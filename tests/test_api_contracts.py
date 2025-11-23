import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_contract_api():
    unique_name = f"api-test-contract-{uuid.uuid4().hex[:8]}"
    response = client.post(
        "/api/v1/contracts",
        json={
            "name": unique_name,
            "domain": "test",
            "yaml_content": """
contract_version: "1.0"
domain: "test"
schema:
  user_id:
    type: string
    required: true
"""
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == unique_name
    assert data["version"] == "1.0.0"


def test_list_contracts_api():
    response = client.get("/api/v1/contracts")
    
    assert response.status_code == 200
    data = response.json()
    assert "contracts" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data


def test_get_contract_by_id_api():
    unique_name = f"get-test-contract-{uuid.uuid4().hex[:8]}"
    create_response = client.post(
        "/api/v1/contracts",
        json={
            "name": unique_name,
            "domain": "test",
            "yaml_content": """
contract_version: "1.0"
domain: "test"
schema:
  user_id:
    type: string
    required: true
"""
        }
    )
    
    assert create_response.status_code == 201
    contract_id = create_response.json()["id"]
    
    response = client.get(f"/api/v1/contracts/{contract_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == contract_id


def test_get_contract_by_name_api():
    unique_name = f"name-test-contract-{uuid.uuid4().hex[:8]}"
    create_response = client.post(
        "/api/v1/contracts",
        json={
            "name": unique_name,
            "domain": "test",
            "yaml_content": """
contract_version: "1.0"
domain: "test"
schema:
  user_id:
    type: string
    required: true
"""
        }
    )
    
    assert create_response.status_code == 201
    
    response = client.get(f"/api/v1/contracts/by-name/{unique_name}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == unique_name


def test_update_contract_api():
    unique_name = f"update-test-contract-{uuid.uuid4().hex[:8]}"
    create_response = client.post(
        "/api/v1/contracts",
        json={
            "name": unique_name,
            "domain": "test",
            "yaml_content": """
contract_version: "1.0"
domain: "test"
schema:
  user_id:
    type: string
    required: true
"""
        }
    )
    
    assert create_response.status_code == 201
    contract_id = create_response.json()["id"]
    
    response = client.put(
        f"/api/v1/contracts/{contract_id}",
        json={
            "yaml_content": """
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
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.0.1"


def test_delete_contract_api():
    unique_name = f"delete-test-contract-{uuid.uuid4().hex[:8]}"
    create_response = client.post(
        "/api/v1/contracts",
        json={
            "name": unique_name,
            "domain": "test",
            "yaml_content": """
contract_version: "1.0"
domain: "test"
schema:
  user_id:
    type: string
    required: true
"""
        }
    )
    
    assert create_response.status_code == 201
    contract_id = create_response.json()["id"]
    
    response = client.delete(f"/api/v1/contracts/{contract_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert contract_id in data["contract_id"]


def test_activate_contract_api():
    unique_name = f"activate-test-contract-{uuid.uuid4().hex[:8]}"
    create_response = client.post(
        "/api/v1/contracts",
        json={
            "name": unique_name,
            "domain": "test",
            "yaml_content": """
contract_version: "1.0"
domain: "test"
schema:
  user_id:
    type: string
    required: true
"""
        }
    )
    
    assert create_response.status_code == 201
    contract_id = create_response.json()["id"]
    
    client.delete(f"/api/v1/contracts/{contract_id}")
    
    response = client.post(f"/api/v1/contracts/{contract_id}/activate")
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] == True


def test_list_domains_api():
    unique_name = f"domain-test-contract-{uuid.uuid4().hex[:8]}"
    client.post(
        "/api/v1/contracts",
        json={
            "name": unique_name,
            "domain": "analytics",
            "yaml_content": """
contract_version: "1.0"
domain: "analytics"
schema:
  user_id:
    type: string
    required: true
"""
        }
    )
    
    response = client.get("/api/v1/contracts/domains/list")
    
    assert response.status_code == 200
    data = response.json()
    assert "domains" in data
    assert "total" in data


def test_invalid_yaml_api():
    unique_name = f"invalid-yaml-contract-{uuid.uuid4().hex[:8]}"
    response = client.post(
        "/api/v1/contracts",
        json={
            "name": unique_name,
            "domain": "test",
            "yaml_content": """
contract_version: "1.0
domain: test
"""
        }
    )
    
    assert response.status_code == 422


def test_duplicate_contract_api():
    unique_name = f"duplicate-api-contract-{uuid.uuid4().hex[:8]}"
    
    client.post(
        "/api/v1/contracts",
        json={
            "name": unique_name,
            "domain": "test",
            "yaml_content": """
contract_version: "1.0"
domain: "test"
schema:
  user_id:
    type: string
    required: true
"""
        }
    )
    
    response = client.post(
        "/api/v1/contracts",
        json={
            "name": unique_name,
            "domain": "test",
            "yaml_content": """
contract_version: "1.0"
domain: "test"
schema:
  user_id:
    type: string
    required: true
"""
        }
    )
    
    assert response.status_code == 409