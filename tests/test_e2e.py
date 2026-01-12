import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.main import app
from app.models.database import Base, Contract, ContractVersion, ValidationResult, QualityMetric


@pytest.fixture(scope="session")
def e2e_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()
    engine.dispose()


@pytest.fixture(scope="function")
def e2e_client(e2e_db):
    def override_get_db():
        yield e2e_db
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestE2EContractLifecycle:
    """End-to-end tests for complete contract lifecycle."""
    
    def test_complete_contract_workflow_from_creation_to_deletion(self, e2e_client, e2e_db):
        """Test complete workflow: create → validate → update → version → delete."""
        
        step1_response = e2e_client.post("/api/v1/contracts", json={
            "name": "e2e-lifecycle-contract",
            "domain": "test",
            "yaml_content": """contract_version: "1.0"
schema:
  user_id:
    type: string
    required: true
  email:
    type: string
    format: email
    required: true
""",
        })
        
        assert step1_response.status_code == 201
        contract_id = step1_response.json()["id"]
        
        step2_response = e2e_client.post(f"/api/v1/validate/{contract_id}", json={
            "data": {"user_id": "test_user", "email": "test@example.com"}
        })
        
        assert step2_response.status_code == 200
        assert step2_response.json()["status"] == "PASS"
        
        step3_response = e2e_client.put(f"/api/v1/contracts/{contract_id}", json={
            "yaml_content": """contract_version: "1.0"
schema:
  user_id:
    type: string
    required: true
  email:
    type: string
    format: email
    required: true
  age:
    type: integer
    required: false
    min: 18
    max: 120
""",
        })
        
        assert step3_response.status_code == 200
        assert step3_response.json()["version"] == "1.1.0"
        
        step4_response = e2e_client.get(f"/api/v1/contract-versions/{contract_id}/versions")
        
        assert step4_response.status_code == 200
        versions = step4_response.json()["versions"]
        assert len(versions) == 2
        
        step5_response = e2e_client.delete(f"/api/v1/contracts/{contract_id}")
        
        assert step5_response.status_code == 200
        
        verify_response = e2e_client.get(f"/api/v1/contracts/{contract_id}")
        assert verify_response.status_code == 404
    
    def test_contract_with_breaking_changes(self, e2e_client):
        """Test contract update with breaking changes."""
        
        create_response = e2e_client.post("/api/v1/contracts", json={
            "name": "e2e-breaking-contract",
            "domain": "test",
            "yaml_content": """contract_version: "1.0"
schema:
  user_id:
    type: string
    required: true
  optional_field:
    type: string
    required: false
""",
        })
        
        contract_id = create_response.json()["id"]
        assert create_response.json()["version"] == "1.0.0"
        
        update_response = e2e_client.put(f"/api/v1/contracts/{contract_id}", json={
            "yaml_content": """contract_version: "1.0"
schema:
  user_id:
    type: string
    required: true
  required_field:
    type: string
    required: true
""",
        })
        
        assert update_response.status_code == 200
        update_data = update_response.json()
        assert update_data["version"] == "2.0.0"
        assert update_data["changes"]["new_version"] == "2.0.0"
        assert update_data["changes"]["version_bump"] == "MAJOR"
        assert update_data["changes"]["change_type"] == "BREAKING"


class TestE2EValidationWorkflow:
    """End-to-end tests for complete validation workflows."""
    
    def test_validation_with_all_error_types(self, e2e_client, e2e_db):
        """Test validation that produces all error types."""
        
        create_response = e2e_client.post("/api/v1/contracts", json={
            "name": "e2e-validation-contract",
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
        
        contract_id = create_response.json()["id"]
        
        validation_response = e2e_client.post(f"/api/v1/validate/{contract_id}", json={
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
        
        error_types = {e["error_type"] for e in result["errors"]}
        assert "PATTERN_MISMATCH" in error_types
        assert "FORMAT_MISMATCH" in error_types
        assert "VALUE_TOO_SMALL" in error_types
    
    def test_batch_validation_with_mixed_results(self, e2e_client):
        """Test batch validation with mix of pass and fail."""
        
        create_response = e2e_client.post("/api/v1/contracts", json={
            "name": "e2e-batch-contract",
            "domain": "test",
            "yaml_content": """contract_version: "1.0"
schema:
  user_id:
    type: string
    required: true
""",
        })
        
        contract_id = create_response.json()["id"]
        
        batch_response = e2e_client.post(f"/api/v1/validate/{contract_id}/batch", json={
            "records": [
                {"user_id": "valid_user"},
                {"user_id": "another_valid"},
                {"user_id": ""},
                {"user_id": 123},
            ]
        })
        
        assert batch_response.status_code == 200
        batch_data = batch_response.json()
        assert batch_data["total_records"] == 4
        assert batch_data["passed"] == 2
        assert batch_data["failed"] == 2
        assert batch_data["pass_rate"] == 50.0
        
        history_response = e2e_client.get(f"/api/v1/validate/{contract_id}/results?limit=10")
        
        assert history_response.status_code == 200
        results = history_response.json()["results"]
        assert len(results) == 4


class TestE2EVersioningWorkflow:
    """End-to-end tests for complete versioning workflows."""
    
    def test_version_evolution_and_rollback(self, e2e_client):
        """Test version evolution with breaking and non-breaking changes."""
        
        create_response = e2e_client.post("/api/v1/contracts", json={
            "name": "e2e-versioning-contract",
            "domain": "test",
            "yaml_content": """contract_version: "1.0"
schema:
  field1:
    type: string
    required: true
""",
        })
        
        contract_id = create_response.json()["id"]
        
        update1_response = e2e_client.put(f"/api/v1/contracts/{contract_id}", json={
            "yaml_content": """contract_version: "1.0"
schema:
  field1:
    type: string
    required: true
  field2:
    type: string
    required: false
""",
        })
        
        assert update1_response.json()["version"] == "1.1.0"
        
        update2_response = e2e_client.put(f"/api/v1/contracts/{contract_id}", json={
            "yaml_content": """contract_version: "1.0"
schema:
  field1:
    type: string
    required: true
  field2:
    type: string
    required: true
""",
        })
        
        assert update2_response.json()["version"] == "2.0.0"
        
        diff_response = e2e_client.get(f"/api/v1/contract-versions/{contract_id}/diff/1.0.0/2.0.0")
        
        assert diff_response.status_code == 200
        diff_data = diff_response.json()
        assert len(diff_data["breaking_changes"]) > 0
        
        rollback_response = e2e_client.post(f"/api/v1/contract-versions/{contract_id}/rollback", json={
            "version": "1.1.0"
        })
        
        assert rollback_response.status_code == 200
        assert rollback_response.json()["previous_version"] == "1.1.0"
        
        get_response = e2e_client.get(f"/api/v1/contracts/{contract_id}")
        
        assert get_response.json()["version"] == "1.2.0"


class TestE2EMetricsWorkflow:
    """End-to-end tests for complete metrics workflows."""
    
    def test_metrics_from_validation_to_dashboard(self, e2e_client):
        """Test metrics generation and dashboard aggregation."""
        
        create_response = e2e_client.post("/api/v1/contracts", json={
            "name": "e2e-metrics-contract",
            "domain": "test",
            "yaml_content": """contract_version: "1.0"
schema:
  user_id:
    type: string
    required: true
""",
        })
        
        contract_id = create_response.json()["id"]
        
        for i in range(10):
            e2e_client.post(f"/api/v1/validate/{contract_id}", json={
                "data": {"user_id": f"user_{i}"}
            })
        
        dashboard_response = e2e_client.get(f"/api/v1/metrics/{contract_id}/dashboard?days=7")
        
        assert dashboard_response.status_code == 200
        dashboard_data = dashboard_response.json()
        
        assert "daily_metrics" in dashboard_data
        assert "trend" in dashboard_data
        assert "quality_score" in dashboard_data
        
        quality_score = dashboard_data["quality_score"]["quality_score"]
        assert 0 <= quality_score <= 100
    
    def test_platform_summary_with_multiple_contracts(self, e2e_client):
        """Test platform summary with multiple contracts."""
        
        contract_names = ["e2e-platform-contract-1", "e2e-platform-contract-2", "e2e-platform-contract-3"]
        
        for name in contract_names:
            e2e_client.post("/api/v1/contracts", json={
                "name": name,
                "domain": "test",
                "yaml_content": f"""contract_version: "1.0"
schema:
  field:
    type: string
    required: true
""",
            })
            
            contract_id = e2e_client.post(f"/api/v1/contracts", json={
                "name": name,
                "domain": "test",
                "yaml_content": f"""contract_version: "1.0"
schema:
  field:
    type: string
    required: true
""",
            }).json()["id"]
            
            e2e_client.post(f"/api/v1/validate/{contract_id}", json={
                "data": {"field": "value"}
            })
        
        summary_response = e2e_client.get("/api/v1/metrics/summary")
        
        assert summary_response.status_code == 200
        summary_data = summary_response.json()
        
        assert summary_data["total_contracts"] >= 3
        assert summary_data["active_contracts"] >= 3
        assert summary_data["total_validations_today"] >= 3
        assert "top_performing_contracts" in summary_data
        assert "contracts_needing_attention" in summary_data


class TestE2EErrorHandling:
    """End-to-end tests for error handling across workflows."""
    
    def test_404_scenarios(self, e2e_client):
        """Test various 404 not found scenarios."""
        
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        responses = [
            e2e_client.get(f"/api/v1/contracts/{fake_id}"),
            e2e_client.put(f"/api/v1/contracts/{fake_id}", json={"yaml_content": "test"}),
            e2e_client.delete(f"/api/v1/contracts/{fake_id}"),
            e2e_client.post(f"/api/v1/validate/{fake_id}", json={"data": {}}),
            e2e_client.get(f"/api/v1/contract-versions/{fake_id}/versions"),
            e2e_client.get(f"/api/v1/metrics/{fake_id}/dashboard"),
        ]
        
        for response in responses:
            assert response.status_code in [404, 422]
    
    def test_validation_errors_with_contract(self, e2e_client):
        """Test all validation error scenarios."""
        
        create_response = e2e_client.post("/api/v1/contracts", json={
            "name": "e2e-errors-contract",
            "domain": "test",
            "yaml_content": """contract_version: "1.0"
schema:
  required_field:
    type: string
    required: true
  another_required:
    type: integer
    required: true
    min: 0
  optional_field:
    type: string
    required: false
""",
        })
        
        contract_id = create_response.json()["id"]
        
        error_scenarios = [
            ("missing_required", {"optional_field": "value"}, "REQUIRED_FIELD_MISSING"),
            ("wrong_type", {"required_field": 123}, "TYPE_MISMATCH"),
            ("out_of_range", {"another_required": -1}, "VALUE_TOO_SMALL"),
        ]
        
        for scenario_name, data, expected_error in error_scenarios:
            response = e2e_client.post(f"/api/v1/validate/{contract_id}", json={"data": data})
            
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "FAIL"
            assert expected_error in [e["error_type"] for e in result["errors"]]
    
    def test_invalid_yaml_scenarios(self, e2e_client):
        """Test various invalid YAML scenarios."""
        
        invalid_yamls = [
            ("malformed_yaml", "contract_version: 1.0\nschema: unclosed"),
            ("invalid_version", "contract_version: 'invalid'\nschema:\n  field:\n    type: string"),
            ("empty_schema", "contract_version: '1.0'\nschema: {}"),
            ("missing_version", "schema:\n  field:\n    type: string"),
        ]
        
        for scenario_name, yaml_content in invalid_yamls:
            response = e2e_client.post("/api/v1/contracts", json={
                "name": f"e2e-{scenario_name}-contract",
                "domain": "test",
                "yaml_content": yaml_content,
            })
            
            assert response.status_code in [400, 422]


class TestE2EDataPersistence:
    """End-to-end tests for data persistence across operations."""
    
    def test_validation_results_persisted_correctly(self, e2e_client, e2e_db):
        """Test that validation results are persisted correctly."""
        
        create_response = e2e_client.post("/api/v1/contracts", json={
            "name": "e2e-persistence-contract",
            "domain": "test",
            "yaml_content": """contract_version: "1.0"
schema:
  field:
    type: string
    required: true
""",
        })
        
        contract_id = create_response.json()["id"]
        
        e2e_client.post(f"/api/v1/validate/{contract_id}", json={
            "data": {"field": "valid_value"}
        })
        
        e2e_client.post(f"/api/v1/validate/{contract_id}", json={
            "data": {"field": "valid_value_2"}
        })
        
        e2e_client.post(f"/api/v1/validate/{contract_id}", json={
            "data": {}}
        })
        
        results = e2e_db.query(ValidationResult).filter(
            ValidationResult.contract_id == contract_id
        ).all()
        
        assert len(results) == 3
        statuses = [r.status for r in results]
        assert statuses.count("PASS") == 2
        assert statuses.count("FAIL") == 1
