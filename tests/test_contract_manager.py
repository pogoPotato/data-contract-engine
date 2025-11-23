import pytest
import uuid
from app.core.contract_manager import ContractManager
from app.models.schemas import ContractCreate, ContractUpdate
from app.utils.exceptions import DuplicateContractError, ContractNotFoundError


def test_create_contract_success(test_db):
    manager = ContractManager(test_db)
    
    contract_data = ContractCreate(
        name="test-contract-success",
        domain="test",
        yaml_content="""
contract_version: "1.0"
domain: "test"
schema:
  user_id:
    type: string
    required: true
"""
    )
    
    contract = manager.create_contract(contract_data)
    
    assert contract.name == "test-contract-success"
    assert contract.version == "1.0.0"
    assert contract.is_active == True


def test_create_contract_duplicate_name(test_db):
    manager = ContractManager(test_db)
    
    contract_data = ContractCreate(
        name="duplicate-contract",
        domain="test",
        yaml_content="""
contract_version: "1.0"
domain: "test"
schema:
  user_id:
    type: string
    required: true
"""
    )
    
    manager.create_contract(contract_data)
    
    with pytest.raises(DuplicateContractError):
        manager.create_contract(contract_data)


def test_get_contract_by_id(test_db):
    manager = ContractManager(test_db)
    
    contract_data = ContractCreate(
        name="get-by-id-contract",
        domain="test",
        yaml_content="""
contract_version: "1.0"
domain: "test"
schema:
  user_id:
    type: string
    required: true
"""
    )
    
    contract = manager.create_contract(contract_data)
    contract_uuid = uuid.UUID(contract.id)
    
    retrieved = manager.get_contract_by_id(contract_uuid)
    
    assert retrieved is not None
    assert retrieved.id == contract.id
    assert retrieved.name == contract.name


def test_get_contract_by_name(test_db):
    manager = ContractManager(test_db)
    
    contract_data = ContractCreate(
        name="get-by-name-contract",
        domain="test",
        yaml_content="""
contract_version: "1.0"
domain: "test"
schema:
  user_id:
    type: string
    required: true
"""
    )
    
    contract = manager.create_contract(contract_data)
    
    retrieved = manager.get_contract_by_name("get-by-name-contract")
    
    assert retrieved is not None
    assert retrieved.name == contract.name


def test_list_contracts(test_db):
    manager = ContractManager(test_db)
    
    contract_data = ContractCreate(
        name="list-contract-1",
        domain="test",
        yaml_content="""
contract_version: "1.0"
domain: "test"
schema:
  user_id:
    type: string
    required: true
"""
    )
    
    manager.create_contract(contract_data)
    
    contracts, total = manager.list_contracts()
    
    assert total >= 1
    assert len(contracts) >= 1


def test_list_contracts_with_domain_filter(test_db):
    manager = ContractManager(test_db)
    
    contract_data = ContractCreate(
        name="domain-filter-contract",
        domain="analytics",
        yaml_content="""
contract_version: "1.0"
domain: "analytics"
schema:
  user_id:
    type: string
    required: true
"""
    )
    
    manager.create_contract(contract_data)
    
    contracts, total = manager.list_contracts(domain="analytics")
    
    assert total >= 1
    assert all(c.domain == "analytics" for c in contracts)


def test_update_contract(test_db):
    manager = ContractManager(test_db)
    
    contract_data = ContractCreate(
        name="update-contract",
        domain="test",
        yaml_content="""
contract_version: "1.0"
domain: "test"
schema:
  user_id:
    type: string
    required: true
"""
    )
    
    contract = manager.create_contract(contract_data)
    contract_uuid = uuid.UUID(contract.id)
    
    update_data = ContractUpdate(
        yaml_content="""
contract_version: "1.0"
domain: "test"
schema:
  user_id:
    type: string
    required: true
  email:
    type: string
    required: false
"""
    )
    
    updated = manager.update_contract(contract_uuid, update_data)
    
    assert updated.version == "1.0.1"


def test_delete_contract_soft(test_db):
    manager = ContractManager(test_db)
    
    contract_data = ContractCreate(
        name="soft-delete-contract",
        domain="test",
        yaml_content="""
contract_version: "1.0"
domain: "test"
schema:
  user_id:
    type: string
    required: true
"""
    )
    
    contract = manager.create_contract(contract_data)
    contract_uuid = uuid.UUID(contract.id)
    
    result = manager.delete_contract(contract_uuid, hard_delete=False)
    
    assert result == True
    
    retrieved = manager.get_contract_by_id(contract_uuid)
    assert retrieved.is_active == False


def test_delete_contract_hard(test_db):
    manager = ContractManager(test_db)
    
    contract_data = ContractCreate(
        name="hard-delete-contract",
        domain="test",
        yaml_content="""
contract_version: "1.0"
domain: "test"
schema:
  user_id:
    type: string
    required: true
"""
    )
    
    contract = manager.create_contract(contract_data)
    contract_uuid = uuid.UUID(contract.id)
    
    result = manager.delete_contract(contract_uuid, hard_delete=True)
    
    assert result == True
    
    retrieved = manager.get_contract_by_id(contract_uuid)
    assert retrieved is None


def test_activate_contract(test_db):
    manager = ContractManager(test_db)
    
    contract_data = ContractCreate(
        name="activate-contract",
        domain="test",
        yaml_content="""
contract_version: "1.0"
domain: "test"
schema:
  user_id:
    type: string
    required: true
"""
    )
    
    contract = manager.create_contract(contract_data)
    contract_uuid = uuid.UUID(contract.id)
    
    manager.delete_contract(contract_uuid, hard_delete=False)
    
    activated = manager.activate_contract(contract_uuid)
    
    assert activated.is_active == True