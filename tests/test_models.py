import pytest
from datetime import datetime, date
from app.models.database import Contract, ContractVersion, ValidationResult, QualityMetric


def test_create_contract(test_db, sample_contract_data):
    contract = Contract(**sample_contract_data)
    test_db.add(contract)
    test_db.commit()
    
    assert contract.id is not None
    assert contract.name == sample_contract_data["name"]
    assert contract.version == sample_contract_data["version"]
    assert contract.created_at is not None


def test_contract_to_dict(test_db, sample_contract_data):
    contract = Contract(**sample_contract_data)
    test_db.add(contract)
    test_db.commit()
    
    contract_dict = contract.to_dict()
    assert "id" in contract_dict
    assert contract_dict["name"] == sample_contract_data["name"]
    assert contract_dict["version"] == sample_contract_data["version"]


def test_contract_unique_name(test_db, sample_contract_data):
    contract1 = Contract(**sample_contract_data)
    test_db.add(contract1)
    test_db.commit()
    
    
    contract2 = Contract(**sample_contract_data)
    test_db.add(contract2)
    
    with pytest.raises(Exception):  
        test_db.commit()


def test_create_contract_version(test_db, sample_contract_data):
    contract = Contract(**sample_contract_data)
    test_db.add(contract)
    test_db.commit()
    
    
    version = ContractVersion(
        contract_id=contract.id,
        version="1.0.0",
        yaml_content=sample_contract_data["yaml_content"],
        change_type="INITIAL",
        created_by="test_user"
    )
    test_db.add(version)
    test_db.commit()
    
    assert version.id is not None
    assert version.contract_id == contract.id
    assert version.version == "1.0.0"


def test_contract_version_relationship(test_db, sample_contract_data):
    contract = Contract(**sample_contract_data)
    test_db.add(contract)
    test_db.commit()
    
    version = ContractVersion(
        contract_id=contract.id,
        version="1.0.0",
        yaml_content=sample_contract_data["yaml_content"]
    )
    test_db.add(version)
    test_db.commit()
    
    
    assert len(contract.versions) == 1
    assert contract.versions[0].version == "1.0.0"
    assert version.contract.name == contract.name


def test_create_validation_result(test_db, sample_contract_data):
    contract = Contract(**sample_contract_data)
    test_db.add(contract)
    test_db.commit()
    
    result = ValidationResult(
        contract_id=contract.id,
        status="PASS",
        data_snapshot={"user_id": "usr_123"},
        errors=None,
        execution_time_ms=12.5
    )
    test_db.add(result)
    test_db.commit()
    
    assert result.id is not None
    assert result.status == "PASS"
    assert result.is_pass() is True
    assert result.error_count() == 0


def test_validation_result_with_errors(test_db, sample_contract_data):
    contract = Contract(**sample_contract_data)
    test_db.add(contract)
    test_db.commit()
    
    errors = [
        {"field": "email", "error_type": "FORMAT_INVALID", "message": "Invalid email"}
    ]
    
    result = ValidationResult(
        contract_id=contract.id,
        status="FAIL",
        data_snapshot={"email": "not-an-email"},
        errors=errors,
        execution_time_ms=10.2
    )
    test_db.add(result)
    test_db.commit()
    
    assert result.is_pass() is False
    assert result.error_count() == 1
    assert result.errors[0]["field"] == "email"


def test_create_quality_metric(test_db, sample_contract_data):
    contract = Contract(**sample_contract_data)
    test_db.add(contract)
    test_db.commit()
    
    metric = QualityMetric(
        contract_id=contract.id,
        metric_date=date.today(),
        total_validations=100,
        passed=95,
        failed=5,
        pass_rate=95.0,
        quality_score=94.5
    )
    test_db.add(metric)
    test_db.commit()
    
    assert metric.id is not None
    assert metric.pass_rate == 95.0
    assert metric.calculate_pass_rate() == 95.0


def test_quality_metric_calculate_pass_rate(test_db, sample_contract_data):
    contract = Contract(**sample_contract_data)
    test_db.add(contract)
    test_db.commit()
    
    metric = QualityMetric(
        contract_id=contract.id,
        metric_date=date.today(),
        total_validations=100,
        passed=87,
        failed=13
    )
    
    calculated_rate = metric.calculate_pass_rate()
    assert calculated_rate == 87.0


def test_cascade_delete_contract(test_db, sample_contract_data):
    
    contract = Contract(**sample_contract_data)
    test_db.add(contract)
    test_db.commit()
    
    version = ContractVersion(
        contract_id=contract.id,
        version="1.0.0",
        yaml_content="test"
    )
    result = ValidationResult(
        contract_id=contract.id,
        status="PASS",
        execution_time_ms=10.0
    )
    metric = QualityMetric(
        contract_id=contract.id,
        metric_date=date.today(),
        total_validations=10
    )

    test_db.add_all([version, result, metric])
    test_db.commit()
    
    test_db.delete(contract)
    test_db.commit()
    
    assert test_db.query(ContractVersion).filter_by(contract_id=contract.id).count() == 0
    assert test_db.query(ValidationResult).filter_by(contract_id=contract.id).count() == 0
    assert test_db.query(QualityMetric).filter_by(contract_id=contract.id).count() == 0