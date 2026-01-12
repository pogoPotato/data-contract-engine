#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.database import Base, Contract, ContractVersion, ValidationResult, QualityMetric
from app.core.yaml_parser import YAMLParser
from app.core.contract_manager import ContractManager


def main():
    engine = create_engine(os.getenv("DATABASE_URL", "postgresql://dce_user:dce_password@localhost:5432/dce_db"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("Seeding demo data...")
    
    sample_contracts = [
        {
            "name": "user-events",
            "domain": "analytics",
            "description": "User signup events from web application",
            "yaml_content": """contract_version: "1.0"
domain: "user-analytics"
description: "User signup events"

schema:
  user_id:
    type: string
    required: true
    pattern: "^usr_\\d+$"
    description: "Unique user identifier"
  
  email:
    type: string
    format: email
    required: true
    description: "User email address"
  
  age:
    type: integer
    min: 18
    max: 120
    required: false
    description: "User age (optional)"
  
  signup_date:
    type: timestamp
    min: "2020-01-01"
    required: true
    description: "When user signed up"

quality_rules:
  freshness:
    max_latency_hours: 24
    description: "Data should not be older than 24 hours"
  
  completeness:
    min_row_count: 100
    max_null_percentage: 5.0
    description: "Expect at least 100 records with <5% nulls"
""",
        },
        {
            "name": "payment-events",
            "domain": "finance",
            "description": "Payment and transaction events",
            "yaml_content": """contract_version: "1.0"
domain: "finance"
description: "Payment transactions"

schema:
  transaction_id:
    type: string
    required: true
    pattern: "^tx_\\d{10}$"
    description: "Transaction identifier"
  
  amount:
    type: float
    required: true
    min: 0.01
    max: 999999.99
    description: "Transaction amount"
  
  currency:
    type: string
    required: true
    pattern: "^[A-Z]{3}$"
    description: "Three-letter currency code"
  
  status:
    type: string
    required: true
    pattern: "^(PENDING|COMPLETED|FAILED|REFUNDED)$"
    description: "Transaction status"

quality_rules:
  uniqueness:
    fields: ["transaction_id"]
    description: "Transaction IDs must be unique"
  
  freshness:
    max_latency_hours: 1
    description: "Transactions should be processed within 1 hour"
""",
        },
        {
            "name": "api-requests",
            "domain": "api-gateway",
            "description": "Incoming API request validation",
            "yaml_content": """contract_version: "1.0"
domain: "api-gateway"
description: "API request logging"

schema:
  request_id:
    type: string
    format: uuid
    required: true
    description: "Unique request identifier"
  
  endpoint:
    type: string
    required: true
    pattern: "^/api/v[0-9]+/"
    description: "API endpoint path"
  
  method:
    type: string
    required: true
    pattern: "^(GET|POST|PUT|DELETE|PATCH)$"
    description: "HTTP method"
  
  ip_address:
    type: string
    format: ipv4
    required: true
    description: "Client IP address"

quality_rules:
  freshness:
    max_latency_hours: 0.5
    description: "Real-time processing required"
""",
        },
    ]
    
    for contract_data in sample_contracts:
        existing = session.query(Contract).filter(Contract.name == contract_data["name"]).first()
        if existing:
            print(f"Contract {contract_data['name']} already exists, skipping...")
            continue
        
        contract = Contract(
            name=contract_data["name"],
            version="1.0.0",
            domain=contract_data["domain"],
            description=contract_data["description"],
            yaml_content=contract_data["yaml_content"],
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        session.add(contract)
        session.flush()
        
        version = ContractVersion(
            contract_id=contract.id,
            version="1.0.0",
            yaml_content=contract_data["yaml_content"],
            change_type="INITIAL",
            change_summary={"breaking_changes": [], "non_breaking_changes": [], "risk_score": 0},
            created_at=datetime.now(),
            created_by="seed_script",
        )
        session.add(version)
        
        print(f"Created contract: {contract_data['name']} (ID: {contract.id})")
    
    session.commit()
    
    sample_validation_results = [
        {
            "contract_name": "user-events",
            "status": "PASS",
            "count": 50,
        },
        {
            "contract_name": "user-events",
            "status": "FAIL",
            "count": 10,
        },
        {
            "contract_name": "payment-events",
            "status": "PASS",
            "count": 30,
        },
        {
            "contract_name": "payment-events",
            "status": "FAIL",
            "count": 5,
        },
        {
            "contract_name": "api-requests",
            "status": "PASS",
            "count": 100,
        },
    ]
    
    print("\nSeeding validation results...")
    for result_data in sample_validation_results:
        contract = session.query(Contract).filter(Contract.name == result_data["contract_name"]).first()
        if not contract:
            continue
        
        for i in range(result_data["count"]):
            validation = ValidationResult(
                contract_id=contract.id,
                status=result_data["status"],
                data_snapshot={"sample": "data"} if i < 3 else {},
                errors=[{"field": "email", "error_type": "FORMAT_MISMATCH", "message": "Invalid email"}] if result_data["status"] == "FAIL" and i < 2 else [],
                execution_time_ms=7.5 if result_data["status"] == "PASS" else 12.3,
                validated_at=datetime.now() - timedelta(hours=i * 0.5),
            )
            session.add(validation)
    
    session.commit()
    print("Validation results seeded successfully")
    
    print("\nSeeding quality metrics...")
    contract_ids = session.query(Contract).all()
    today = datetime.now().date()
    
    for contract in contract_ids:
        for days_ago in [0, 1, 2, 3, 5, 7]:
            metric_date = today - timedelta(days=days_ago)
            
            existing = (
                session.query(QualityMetric)
                .filter(
                    QualityMetric.contract_id == str(contract.id),
                    QualityMetric.metric_date == metric_date,
                )
                .first()
            )
            
            if existing:
                continue
            
            passed = session.query(ValidationResult).filter(
                ValidationResult.contract_id == contract.id,
                ValidationResult.validated_at >= datetime.combine(metric_date, datetime.min.time()),
                ValidationResult.validated_at < datetime.combine(metric_date + timedelta(days=1), datetime.min.time()),
                ValidationResult.status == "PASS",
            ).count()
            
            total = session.query(ValidationResult).filter(
                ValidationResult.contract_id == contract.id,
                ValidationResult.validated_at >= datetime.combine(metric_date, datetime.min.time()),
                ValidationResult.validated_at < datetime.combine(metric_date + timedelta(days=1), datetime.min.time()),
            ).count()
            
            pass_rate = (passed / total * 100) if total > 0 else 0
            failed = total - passed
            
            top_errors = {}
            if failed > 0:
                validations = session.query(ValidationResult).filter(
                    ValidationResult.contract_id == contract.id,
                    ValidationResult.status == "FAIL",
                ).limit(5).all()
                
                for val in validations:
                    if val.errors:
                        for error in val.errors:
                            error_type = error.get("error_type", "UNKNOWN")
                            top_errors[error_type] = top_errors.get(error_type, 0) + 1
            
            metric = QualityMetric(
                contract_id=str(contract.id),
                metric_date=metric_date,
                total_validations=total,
                passed=passed,
                failed=failed,
                pass_rate=round(pass_rate, 2),
                avg_execution_time_ms=8.5,
                top_errors=top_errors,
                quality_score=round(pass_rate * 0.7 + 95 * 0.2 + 90 * 0.1, 2),
                created_at=datetime.now(),
            )
            session.add(metric)
    
    session.commit()
    print("Quality metrics seeded successfully")
    
    print(f"\n✅ Demo data seeded successfully!")
    print(f"   - {len(sample_contracts)} contracts created")
    print(f"   - Validation results added for demonstration")
    print(f"   - Quality metrics added for last 7 days")
    print(f"\nAccess the UI at: http://localhost:8501")
    print(f"API documentation at: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
