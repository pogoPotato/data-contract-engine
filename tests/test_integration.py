import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.database import Base, Contract, ValidationResult
from app.models.schemas import ContractCreate, ContractResponse


@pytest.fixture(scope="function")
def integration_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()
    engine.dispose()


@pytest.fixture(scope="function")
def test_client(integration_db):
    def override_get_db():
        yield integration_db
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestContractIntegration:
    """Integration tests for contract management workflows."""
    
    def test_full_contract_lifecycle(self, test_client):
        """Test complete contract lifecycle from creation to deletion."""
        
        create_response = test_client.post("/api/v1/contracts", json={
            "name": "integration-test-contract",
            "domain": "test",
            "yaml_content": """contract_version: "1.0"
schema:
  user_id:
    type: string
    required: true
""",
            "description": "Integration test contract",
        })
        
        assert create_response.status_code == 201
        contract_data = create_response.json()
        contract_id = contract_data["id"]
        
        get_response = test_client.get(f"/api/v1/contracts/{contract_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "integration-test-contract"
        
        list_response = test_client.get("/api/v1/contracts?domain=test")
        assert list_response.status_code == 200
        contracts = list_response.json()["contracts"]
        assert len(contracts) == 1
        
        delete_response = test_client.delete(f"/api/v1/contracts/{contract_id}?hard_delete=true")
        assert delete_response.status_code == 200
        
        verify_response = test_client.get(f"/api/v1/contracts/{contract_id}")
        assert verify_response.status_code == 404
    
    def test_contract_update_creates_version(self, test_client):
        """Test that updating contract creates new version."""
        
        create_response = test_client.post("/api/v1/contracts", json={
            "name": "version-test-contract",
            "domain": "test",
            "yaml_content": """contract_version: "1.0"
schema:
  user_id:
    type: string
    required: true
""",
        })
        
        contract_id = create_response.json()["id"]
        assert create_response.json()["version"] == "1.0.0"
        
        update_response = test_client.put(f"/api/v1/contracts/{contract_id}", json={
            "yaml_content": """contract_version: "1.0"
schema:
  user_id:
    type: string
    required: true
  email:
    type: string
    format: email
    required: false
""",
        })
        
        assert update_response.status_code == 200
        updated_data = update_response.json()
        assert updated_data["version"] == "1.1.0"
        assert "new_version" in updated_data["changes"]
    
    def test_multiple_contracts_domain_filtering(self, test_client):
        """Test creating multiple contracts and filtering by domain."""
        
        domains = ["analytics", "finance", "marketing"]
        for domain in domains:
            test_client.post("/api/v1/contracts", json={
                "name": f"{domain}-contract",
                "domain": domain,
                "yaml_content": f'contract_version: "1.0"\nschema:\n  field:\n    type: string\n    required: true\n',
            })
        
        analytics_response = test_client.get("/api/v1/contracts?domain=analytics")
        assert analytics_response.status_code == 200
        assert len(analytics_response.json()["contracts"]) == 1
        
        all_response = test_client.get("/api/v1/contracts")
        assert all_response.status_code == 200
        assert len(all_response.json()["contracts"]) == 3
    
    def test_contract_soft_delete_and_restore(self, test_client):
        """Test soft delete and restore contract."""
        
        create_response = test_client.post("/api/v1/contracts", json={
            "name": "delete-restore-contract",
            "domain": "test",
            "yaml_content": 'contract_version: "1.0"\nschema:\n  field:\n    type: string\n',
        })
        
        contract_id = create_response.json()["id"]
        
        delete_response = test_client.delete(f"/api/v1/contracts/{contract_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["hard_delete"] is False
        
        get_response = test_client.get(f"/api/v1/contracts/{contract_id}")
        assert get_response.status_code == 200
        assert get_response.json()["is_active"] is False
        
        activate_response = test_client.post(f"/api/v1/contracts/{contract_id}/activate")
        assert activate_response.status_code == 200
        assert activate_response.json()["is_active"] is True


class TestValidationIntegration:
    """Integration tests for validation workflows."""
    
    def test_validation_stores_result(self, test_client, integration_db):
        """Test that validation results are stored in database."""
        
        contract_response = test_client.post("/api/v1/contracts", json={
            "name": "validation-storage-contract",
            "domain": "test",
            "yaml_content": 'contract_version: "1.0"\nschema:\n  user_id:\n    type: string\n    required: true\n',
        })
        
        contract_id = contract_response.json()["id"]
        
        validation_response = test_client.post(f"/api/v1/validate/{contract_id}", json={
            "data": {"user_id": "test_user"}
        })
        
        assert validation_response.status_code == 200
        assert validation_response.json()["status"] == "PASS"
        
        results = integration_db.query(ValidationResult).filter(
            ValidationResult.contract_id == contract_id
        ).all()
        
        assert len(results) == 1
        assert results[0].status == "PASS"
    
    def test_batch_validation_workflow(self, test_client):
        """Test complete batch validation workflow."""
        
        contract_response = test_client.post("/api/v1/contracts", json={
            "name": "batch-validation-contract",
            "domain": "test",
            "yaml_content": 'contract_version: "1.0"\nschema:\n  user_id:\n    type: string\n    required: true\n',
        })
        
        contract_id = contract_response.json()["id"]
        
        batch_response = test_client.post(f"/api/v1/validate/{contract_id}/batch", json={
            "records": [
                {"user_id": "user_001"},
                {"user_id": "user_002"},
                {"user_id": "user_003"},
            ]
        })
        
        assert batch_response.status_code == 200
        batch_data = batch_response.json()
        assert batch_data["total_records"] == 3
        assert batch_data["passed"] == 3
        assert batch_data["failed"] == 0
        assert batch_data["pass_rate"] == 100.0
    
    def test_validation_with_multiple_errors(self, test_client):
        """Test validation that produces multiple errors."""
        
        contract_response = test_client.post("/api/v1/contracts", json={
            "name": "multi-error-contract",
            "domain": "test",
            "yaml_content": """contract_version: "1.0"
schema:
  user_id:
    type: string
    required: true
    pattern: "^usr_\\d+$"
  email:
    type: string
    format: email
    required: true
  age:
    type: integer
    required: true
    min: 18
    max: 120
""",
        })
        
        contract_id = contract_response.json()["id"]
        
        validation_response = test_client.post(f"/api/v1/validate/{contract_id}", json={
            "data": {
                "user_id": "invalid_id",
                "email": "not-an-email",
                "age": 15,
            }
        })
        
        assert validation_response.status_code == 200
        result = validation_response.json()
        assert result["status"] == "FAIL"
        assert len(result["errors"]) == 3


class TestVersionIntegration:
    """Integration tests for version control workflows."""
    
    def test_version_history_workflow(self, test_client):
        """Test complete version history workflow."""
        
        create_response = test_client.post("/api/v1/contracts", json={
            "name": "version-history-contract",
            "domain": "test",
            "yaml_content": 'contract_version: "1.0"\nschema:\n  field:\n    type: string\n',
        })
        
        contract_id = create_response.json()["id"]
        
        test_client.put(f"/api/v1/contracts/{contract_id}", json={
            "yaml_content": """contract_version: "1.0"
schema:
  field:
    type: string
  new_field:
    type: string
    required: false
""",
        })
        
        test_client.put(f"/api/v1/contracts/{contract_id}", json={
            "yaml_content": """contract_version: "1.0"
schema:
  field:
    type: string
  another_field:
    type: string
    required: true
""",
        })
        
        history_response = test_client.get(f"/api/v1/contract-versions/{contract_id}/versions")
        assert history_response.status_code == 200
        versions = history_response.json()["versions"]
        
        assert len(versions) == 3
        assert versions[0]["version"] == "2.0.0"
        assert versions[1]["version"] == "1.1.0"
        assert versions[2]["version"] == "1.0.0"
    
    def test_version_comparison_workflow(self, test_client):
        """Test version comparison workflow."""
        
        create_response = test_client.post("/api/v1/contracts", json={
            "name": "version-compare-contract",
            "domain": "test",
            "yaml_content": 'contract_version: "1.0"\nschema:\n  field:\n    type: string\n',
        })
        
        contract_id = create_response.json()["id"]
        
        test_client.put(f"/api/v1/contracts/{contract_id}", json={
            "yaml_content": """contract_version: "1.0"
schema:
  field:
    type: integer
  required: true
""",
        })
        
        diff_response = test_client.get(f"/api/v1/contract-versions/{contract_id}/diff/1.0.0/2.0.0")
        assert diff_response.status_code == 200
        diff_data = diff_response.json()
        
        assert len(diff_data["breaking_changes"]) > 0
        assert "TYPE_CHANGED" in [c["type"] for c in diff_data["breaking_changes"]]
        assert "risk_score" in diff_data
    
    def test_rollback_workflow(self, test_client):
        """Test contract rollback workflow."""
        
        create_response = test_client.post("/api/v1/contracts", json={
            "name": "rollback-contract",
            "domain": "test",
            "yaml_content": """contract_version: "1.0"
schema:
  field:
    type: string
    required: true
""",
        })
        
        contract_id = create_response.json()["id"]
        
        test_client.put(f"/api/v1/contracts/{contract_id}", json={
            "yaml_content": """contract_version: "1.0"
schema:
  field:
    type: string
    required: false
""",
        })
        
        rollback_response = test_client.post(f"/api/v1/contract-versions/{contract_id}/rollback", json={
            "version": "1.0.0"
        })
        
        assert rollback_response.status_code == 200
        rollback_data = rollback_response.json()
        assert "previous_version" in rollback_data
        assert rollback_data["previous_version"] == "1.0.0"


class TestMetricsIntegration:
    """Integration tests for metrics workflows."""
    
    def test_metrics_aggregation_workflow(self, test_client, integration_db):
        """Test metrics aggregation and retrieval."""
        
        contract_response = test_client.post("/api/v1/contracts", json={
            "name": "metrics-contract",
            "domain": "test",
            "yaml_content": 'contract_version: "1.0"\nschema:\n  field:\n    type: string\n',
        })
        
        contract_id = contract_response.json()["id"]
        
        for i in range(10):
            test_client.post(f"/api/v1/validate/{contract_id}", json={
                "data": {"field": "value"}
            })
        
        test_client.post("/api/v1/metrics/aggregate")
        
        history_response = test_client.get(f"/api/v1/validate/{contract_id}/results")
        assert history_response.status_code == 200
        results = history_response.json()["results"]
        assert len(results) >= 10
    
    def test_dashboard_endpoint(self, test_client):
        """Test consolidated dashboard endpoint."""
        
        contract_response = test_client.post("/api/v1/contracts", json={
            "name": "dashboard-contract",
            "domain": "test",
            "yaml_content": 'contract_version: "1.0"\nschema:\n  field:\n    type: string\n',
        })
        
        contract_id = contract_response.json()["id"]
        
        for i in range(5):
            test_client.post(f"/api/v1/validate/{contract_id}", json={
                "data": {"field": "value"}
            })
        
        dashboard_response = test_client.get(f"/api/v1/metrics/{contract_id}/dashboard")
        assert dashboard_response.status_code == 200
        dashboard_data = dashboard_response.json()
        
        assert "daily_metrics" in dashboard_data
        assert "trend" in dashboard_data
        assert "top_errors" in dashboard_data
        assert "quality_score" in dashboard_data
    
    def test_platform_summary(self, test_client):
        """Test platform summary endpoint."""
        
        for i in range(3):
            test_client.post("/api/v1/contracts", json={
                "name": f"summary-contract-{i}",
                "domain": "test",
                "yaml_content": 'contract_version: "1.0"\nschema:\n  field:\n    type: string\n',
            })
        
        summary_response = test_client.get("/api/v1/metrics/summary")
        assert summary_response.status_code == 200
        summary_data = summary_response.json()
        
        assert summary_data["total_contracts"] >= 3
        assert summary_data["active_contracts"] >= 3
        assert "top_performing_contracts" in summary_data
