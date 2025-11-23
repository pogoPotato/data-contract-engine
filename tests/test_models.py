import pytest
from datetime import datetime, timezone, date
from app.models.database import Contract, ContractVersion, ValidationResult, QualityMetric


def test_create_contract(test_db):
    contract = Contract(
        name="test-contract",
        version="1.0.0",
        domain="test",
        yaml_content="contract_version: '1.0'\nschema:\n  user_id:\n    type: string",
        description="Test contract",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    test_db.add(contract)
    test_db.commit()
    
    assert contract.id is not None
    assert contract.name == "test-contract"


def test_contract_to_dict(test_db):
    contract = Contract(
        name="dict-test-contract",
        version="1.0.0",
        domain="test",
        yaml_content="contract_version: '1.0'\nschema:\n  user_id:\n    type: string",
        description="Test contract",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    test_db.add(contract)
    test_db.commit()
    
    contract_dict = contract.to_dict()
    assert "id" in contract_dict
    assert contract_dict["name"] == "dict-test-contract"


def test_contract_unique_name(test_db):
    contract1 = Contract(
        name="unique-contract",
        version="1.0.0",
        domain="test",
        yaml_content="contract_version: '1.0'\nschema:\n  user_id:\n    type: string",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    test_db.add(contract1)
    test_db.commit()
    
    contract2 = Contract(
        name="unique-contract",
        version="1.0.0",
        domain="test",
        yaml_content="contract_version: '1.0'\nschema:\n  user_id:\n    type: string",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    test_db.add(contract2)
    
    with pytest.raises(Exception):
        test_db.commit()


def test_create_contract_version(test_db):
    contract = Contract(
        name="version-test-contract",
        version="1.0.0",
        domain="test",
        yaml_content="contract_version: '1.0'\nschema:\n  user_id:\n    type: string",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    test_db.add(contract)
    test_db.commit()
    
    version = ContractVersion(
        contract_id=contract.id,
        version="1.0.0",
        yaml_content="contract_version: '1.0'\nschema:\n  user_id:\n    type: string",
        change_type="INITIAL",
        created_at=datetime.now(timezone.utc)
    )
    test_db.add(version)
    test_db.commit()
    
    assert version.id is not None
    assert version.contract_id == contract.id


def test_contract_version_relationship(test_db):
    contract = Contract(
        name="relationship-test-contract",
        version="1.0.0",
        domain="test",
        yaml_content="contract_version: '1.0'\nschema:\n  user_id:\n    type: string",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    test_db.add(contract)
    test_db.commit()
    
    version = ContractVersion(
        contract_id=contract.id,
        version="1.0.0",
        yaml_content="contract_version: '1.0'\nschema:\n  user_id:\n    type: string",
        change_type="INITIAL",
        created_at=datetime.now(timezone.utc)
    )
    test_db.add(version)
    test_db.commit()
    
    assert len(contract.versions) == 1
    assert contract.versions[0].version == "1.0.0"


def test_create_validation_result(test_db):
    contract = Contract(
        name="validation-test-contract",
        version="1.0.0",
        domain="test",
        yaml_content="contract_version: '1.0'\nschema:\n  user_id:\n    type: string",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    test_db.add(contract)
    test_db.commit()
    
    result = ValidationResult(
        contract_id=contract.id,
        status="PASS",
        execution_time_ms=10.5,
        validated_at=datetime.now(timezone.utc)
    )
    test_db.add(result)
    test_db.commit()
    
    assert result.id is not None
    assert result.is_pass() == True


def test_validation_result_with_errors(test_db):
    contract = Contract(
        name="error-test-contract",
        version="1.0.0",
        domain="test",
        yaml_content="contract_version: '1.0'\nschema:\n  user_id:\n    type: string",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    test_db.add(contract)
    test_db.commit()
    
    result = ValidationResult(
        contract_id=contract.id,
        status="FAIL",
        errors=[
            {"field": "user_id", "error": "Missing required field"},
            {"field": "email", "error": "Invalid format"}
        ],
        execution_time_ms=15.2,
        validated_at=datetime.now(timezone.utc)
    )
    test_db.add(result)
    test_db.commit()
    
    assert result.is_pass() == False
    assert result.error_count() == 2


def test_create_quality_metric(test_db):
    contract = Contract(
        name="quality-test-contract",
        version="1.0.0",
        domain="test",
        yaml_content="contract_version: '1.0'\nschema:\n  user_id:\n    type: string",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    test_db.add(contract)
    test_db.commit()
    
    metric = QualityMetric(
        contract_id=contract.id,
        metric_date=date.today(),
        total_validations=100,
        passed=95,
        failed=5,
        created_at=datetime.now(timezone.utc)
    )
    test_db.add(metric)
    test_db.commit()
    
    assert metric.id is not None
    assert metric.total_validations == 100


def test_quality_metric_calculate_pass_rate(test_db):
    contract = Contract(
        name="pass-rate-test-contract",
        version="1.0.0",
        domain="test",
        yaml_content="contract_version: '1.0'\nschema:\n  user_id:\n    type: string",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    test_db.add(contract)
    test_db.commit()
    
    metric = QualityMetric(
        contract_id=contract.id,
        metric_date=date.today(),
        total_validations=100,
        passed=95,
        failed=5,
        created_at=datetime.now(timezone.utc)
    )
    
    pass_rate = metric.calculate_pass_rate()
    assert pass_rate == 95.0


def test_cascade_delete_contract(test_db):
    contract = Contract(
        name="cascade-test-contract",
        version="1.0.0",
        domain="test",
        yaml_content="contract_version: '1.0'\nschema:\n  user_id:\n    type: string",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    test_db.add(contract)
    test_db.commit()
    
    version = ContractVersion(
        contract_id=contract.id,
        version="1.0.0",
        yaml_content="contract_version: '1.0'\nschema:\n  user_id:\n    type: string",
        change_type="INITIAL",
        created_at=datetime.now(timezone.utc)
    )
    test_db.add(version)
    
    result = ValidationResult(
        contract_id=contract.id,
        status="PASS",
        execution_time_ms=10.5,
        validated_at=datetime.now(timezone.utc)
    )
    test_db.add(result)
    test_db.commit()
    
    contract_id = contract.id
    
    test_db.delete(contract)
    test_db.commit()
    
    assert test_db.query(Contract).filter_by(id=contract_id).first() is None
    assert test_db.query(ContractVersion).filter_by(contract_id=contract_id).count() == 0
    assert test_db.query(ValidationResult).filter_by(contract_id=contract_id).count() == 0