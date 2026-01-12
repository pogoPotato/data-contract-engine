# API Documentation

Complete reference for the Data Contract Engine REST API.

**Base URL**: `http://localhost:8000/api/v1`
**API Documentation**: `/docs` (Swagger) or `/redoc` (ReDoc)

## Authentication

Currently, the API does not require authentication. Future versions will support:
- API key authentication
- JWT tokens
- OAuth 2.0

## Response Format

### Success Response

```json
{
  "status": "PASS",
  "errors": [],
  "validated_at": "2026-01-12T10:00:00Z",
  "execution_time_ms": 12.5
}
```

### Error Response

```json
{
  "error": "ValidationError",
  "message": "Contract not found",
  "detail": "Contract with ID 'abc-123' does not exist",
  "status_code": 404,
  "timestamp": "2026-01-12T10:00:00Z",
  "path": "/api/v1/contracts/abc-123"
}
```

## Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (invalid input) |
| 404 | Not Found |
| 409 | Conflict (duplicate name) |
| 422 | Validation Error |
| 500 | Internal Server Error |

---

## Contracts

### Create Contract

Create a new data contract.

**Endpoint**: `POST /contracts`

**Request Body**:
```json
{
  "name": "user-events",
  "domain": "analytics",
  "yaml_content": "contract_version: \"1.0\"\nschema:\n  user_id:\n    type: string\n    required: true",
  "description": "User signup events"
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "user-events",
  "version": "1.0.0",
  "domain": "analytics",
  "description": "User signup events",
  "yaml_content": "...",
  "is_active": true,
  "created_at": "2026-01-12T10:00:00Z",
  "updated_at": "2026-01-12T10:00:00Z"
}
```

**Errors**:
- `400`: Invalid YAML syntax
- `409`: Contract name already exists

---

### List Contracts

Get all contracts with optional filtering.

**Endpoint**: `GET /contracts`

**Query Parameters**:
- `domain` (optional): Filter by domain
- `limit` (optional, default: 50): Maximum results
- `offset` (optional, default: 0): Pagination offset

**Response** (200 OK):
```json
{
  "contracts": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "user-events",
      "version": "1.0.0",
      "domain": "analytics",
      "is_active": true
    }
  ],
  "total": 1,
  "page": 1
}
```

---

### Get Contract by ID

Get a specific contract by ID.

**Endpoint**: `GET /contracts/{contract_id}`

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "user-events",
  "version": "1.0.0",
  "domain": "analytics",
  "description": "User signup events",
  "yaml_content": "...",
  "is_active": true,
  "created_at": "2026-01-12T10:00:00Z",
  "updated_at": "2026-01-12T10:00:00Z"
}
```

**Errors**:
- `404`: Contract not found

---

### Get Contract by Name

Get a contract by name.

**Endpoint**: `GET /contracts/by-name/{name}`

**Response**: Same as GET by ID

**Errors**:
- `404`: Contract not found

---

### Update Contract

Update a contract (creates new version).

**Endpoint**: `PUT /contracts/{contract_id}`

**Request Body**:
```json
{
  "yaml_content": "contract_version: \"1.0\"\nschema:\n  user_id:\n    type: string\n    required: true\n  email:\n    type: string\n    format: email\n    required: true"
}
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "user-events",
  "version": "1.1.0",
  "updated_at": "2026-01-12T11:00:00Z",
  "changes": {
    "version_bump": "MINOR",
    "new_version": "1.1.0",
    "change_type": "NON_BREAKING",
    "changes_added": ["email"],
    "changes_removed": [],
    "changes_modified": []
  }
}
```

**Errors**:
- `400`: Invalid YAML syntax
- `404`: Contract not found

---

### Delete Contract

Delete a contract (soft or hard delete).

**Endpoint**: `DELETE /contracts/{contract_id}`

**Query Parameters**:
- `hard_delete` (optional, default: false): If true, permanently delete

**Response** (200 OK):
```json
{
  "message": "Contract deactivated",
  "hard_delete": false,
  "contract_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Errors**:
- `404`: Contract not found

---

### Activate Contract

Activate a deactivated contract.

**Endpoint**: `POST /contracts/{contract_id}/activate`

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "user-events",
  "is_active": true
}
```

---

### List Domains

Get all unique contract domains.

**Endpoint**: `GET /contracts/domains/list`

**Response** (200 OK):
```json
{
  "domains": ["analytics", "finance", "marketing"]
}
```

---

## Validation

### Validate Single Record

Validate a single data record against a contract.

**Endpoint**: `POST /validate/{contract_id}`

**Request Body**:
```json
{
  "data": {
    "user_id": "usr_12345",
    "email": "test@example.com",
    "age": 25
  }
}
```

**Response** (200 OK):
```json
{
  "status": "PASS",
  "errors": [],
  "execution_time_ms": 7.6,
  "validated_at": "2026-01-12T10:00:00Z"
}
```

**Response** (FAIL):
```json
{
  "status": "FAIL",
  "errors": [
    {
      "field": "email",
      "error_type": "FORMAT_MISMATCH",
      "message": "Invalid email format",
      "value": "not-an-email"
    },
    {
      "field": "age",
      "error_type": "VALUE_TOO_SMALL",
      "message": "Value 17 is less than minimum 18",
      "value": 17
    }
  ],
  "execution_time_ms": 8.2,
  "validated_at": "2026-01-12T10:00:00Z"
}
```

**Errors**:
- `404`: Contract not found

---

### Validate Batch

Validate multiple records.

**Endpoint**: `POST /validate/{contract_id}/batch`

**Request Body**:
```json
{
  "records": [
    {
      "user_id": "usr_001",
      "email": "user1@example.com",
      "age": 25
    },
    {
      "user_id": "usr_002",
      "email": "user2@example.com",
      "age": 30
    }
  ]
}
```

**Response** (200 OK):
```json
{
  "total_records": 2,
  "passed": 2,
  "failed": 0,
  "pass_rate": 100.0,
  "execution_time_ms": 11.3,
  "errors_summary": {}
}
```

---

### Upload File for Validation

Upload a file for batch validation.

**Endpoint**: `POST /validate/{contract_id}/upload`

**Request**: `multipart/form-data`
- `file`: File to upload (CSV, JSON, or JSONL)

**Response** (200 OK):
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-4466554400001",
  "total_records": 1000,
  "passed": 987,
  "failed": 13,
  "pass_rate": 98.7,
  "execution_time_ms": 1523,
  "errors_summary": {
    "TYPE_MISMATCH": 5,
    "PATTERN_MISMATCH": 3,
    "FORMAT_MISMATCH": 5
  },
  "sample_errors": [
    {
      "record_number": 42,
      "field": "email",
      "error": "Invalid email format",
      "value": "not-an-email"
    }
  ]
}
```

---

### Get Batch Status

Get status of a batch validation.

**Endpoint**: `GET /validate/batch/{batch_id}/status`

**Response** (200 OK):
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-4466554400001",
  "status": "completed",
  "progress": 100,
  "total_records": 1000,
  "processed": 1000
}
```

---

### Get Validation History

Get validation results for a contract.

**Endpoint**: `GET /validate/{contract_id}/results`

**Query Parameters**:
- `limit` (optional, default: 100): Maximum results
- `status` (optional): Filter by status (PASS/FAIL)

**Response** (200 OK):
```json
{
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-4466554400002",
      "status": "PASS",
      "validated_at": "2026-01-12T10:00:00Z",
      "execution_time_ms": 7.6
    }
  ],
  "total": 1
}
```

---

### Get Validation Result

Get a specific validation result.

**Endpoint**: `GET /validate/results/{result_id}`

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-4466554400002",
  "contract_id": "550e8400-e29b-41d4-a716-4466554400000",
  "status": "PASS",
  "data_snapshot": {
    "user_id": "usr_12345",
    "email": "test@example.com"
  },
  "errors": [],
  "execution_time_ms": 7.6,
  "validated_at": "2026-01-12T10:00:00Z"
}
```

---

### Get Errors Summary

Get summary of errors for a contract.

**Endpoint**: `GET /validate/{contract_id}/errors/summary`

**Query Parameters**:
- `days` (optional, default: 7): Number of days to look back

**Response** (200 OK):
```json
{
  "total_errors": 25,
  "error_types": {
    "TYPE_MISMATCH": 8,
    "PATTERN_MISMATCH": 5,
    "FORMAT_MISMATCH": 7,
    "REQUIRED_FIELD_MISSING": 5
  },
  "fields_with_errors": {
    "email": 12,
    "user_id": 8,
    "age": 5
  }
}
```

---

## Versions

### Get Version History

Get all versions of a contract.

**Endpoint**: `GET /contract-versions/{contract_id}/versions`

**Response** (200 OK):
```json
{
  "contract_id": "550e8400-e29b-41d4-a716-4466554400000",
  "versions": [
    {
      "id": "550e8400-e29b-41d4-a716-4466554400010",
      "version": "2.0.0",
      "change_type": "BREAKING",
      "created_at": "2026-01-12T11:00:00Z",
      "created_by": "system"
    },
    {
      "id": "550e8400-e29b-41d4-a716-4466554400011",
      "version": "1.1.0",
      "change_type": "NON_BREAKING",
      "created_at": "2026-01-12T10:00:00Z",
      "created_by": "system"
    },
    {
      "id": "550e8400-e29b-41d4-a716-4466554400012",
      "version": "1.0.0",
      "change_type": "INITIAL",
      "created_at": "2026-01-12T09:00:00Z",
      "created_by": "system"
    }
  ]
}
```

---

### Get Latest Version

Get the latest version of a contract.

**Endpoint**: `GET /contract-versions/{contract_id}/versions/latest`

**Response**: Same as version in list

---

### Get Specific Version

Get a specific version of a contract.

**Endpoint**: `GET /contract-versions/{contract_id}/versions/{version}`

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-4466554400011",
  "contract_id": "550e8400-e29b-41d4-a716-4466554400000",
  "version": "1.1.0",
  "yaml_content": "...",
  "change_type": "NON_BREAKING",
  "change_summary": {
    "breaking_changes": [],
    "non_breaking_changes": [
      {
        "type": "FIELD_ADDED_OPTIONAL",
        "field": "email"
      }
    ],
    "risk_score": 3
  },
  "created_at": "2026-01-12T10:00:00Z",
  "created_by": "system"
}
```

---

### Compare Versions

Compare two versions of a contract.

**Endpoint**: `GET /contract-versions/{contract_id}/diff/{version1}/{version2}`

**Response** (200 OK):
```json
{
  "version1": "1.0.0",
  "version2": "2.0.0",
  "breaking_changes": [
    {
      "type": "FIELD_MADE_REQUIRED",
      "field": "email",
      "description": "Field 'email' changed from optional to required",
      "impact": "Consumers not providing 'email' will fail validation"
    }
  ],
  "non_breaking_changes": [
    {
      "type": "FIELD_ADDED_OPTIONAL",
      "field": "country",
      "description": "Optional field 'country' was added",
      "impact": "No impact on existing consumers"
    }
  ],
  "risk_score": 18,
  "risk_level": "LOW"
}
```

---

### Rollback Version

Rollback to a previous version.

**Endpoint**: `POST /contract-versions/{contract_id}/rollback`

**Request Body**:
```json
{
  "version": "1.1.0"
}
```

**Response** (200 OK):
```json
{
  "message": "Rolled back to version 1.1.0",
  "current_version": "1.2.1",
  "previous_version": "1.1.0",
  "rollback_time": "2026-01-12T12:00:00Z"
}
```

---

## Metrics

### Get Daily Metrics

Get daily metrics for a contract.

**Endpoint**: `GET /metrics/{contract_id}/daily`

**Query Parameters**:
- `days` (optional, default: 30): Number of days

**Response** (200 OK):
```json
{
  "metrics": [
    {
      "date": "2026-01-12",
      "total_validations": 1523,
      "passed": 1498,
      "failed": 25,
      "pass_rate": 98.4,
      "avg_execution_time_ms": 8.2,
      "quality_score": 96.2
    }
  ]
}
```

---

### Get Trend Data

Get trend data for a contract.

**Endpoint**: `GET /metrics/{contract_id}/trend`

**Query Parameters**:
- `days` (optional, default: 90): Number of days

**Response** (200 OK):
```json
{
  "pass_rate_trend": [
    {"date": "2026-01-10", "value": 97.5},
    {"date": "2026-01-11", "value": 98.2},
    {"date": "2026-01-12", "value": 98.4}
  ],
  "volume_trend": [
    {"date": "2026-01-10", "value": 1450},
    {"date": "2026-01-11", "value": 1510},
    {"date": "2026-01-12", "value": 1523}
  ],
  "quality_score_trend": [
    {"date": "2026-01-10", "value": 95.8},
    {"date": "2026-01-11", "value": 96.0},
    {"date": "2026-01-12", "value": 96.2}
  ]
}
```

---

### Get Top Errors

Get most frequent errors.

**Endpoint**: `GET /metrics/{contract_id}/errors/top`

**Query Parameters**:
- `days` (optional, default: 7): Number of days
- `limit` (optional, default: 10): Maximum errors to return

**Response** (200 OK):
```json
{
  "top_errors": [
    {
      "error_type": "FORMAT_MISMATCH",
      "field": "email",
      "count": 12,
      "percentage": 48.0,
      "sample_message": "Invalid email format"
    },
    {
      "error_type": "TYPE_MISMATCH",
      "field": "age",
      "count": 8,
      "percentage": 32.0,
      "sample_message": "Expected integer, got string"
    }
  ]
}
```

---

### Get Quality Score

Get quality score for a contract.

**Endpoint**: `GET /metrics/{contract_id}/quality-score`

**Query Parameters**:
- `days` (optional, default: 7): Number of days

**Response** (200 OK):
```json
{
  "contract_id": "550e8400-e29b-41d4-a716-4466554400000",
  "days": 7,
  "quality_score": 96.2,
  "components": {
    "pass_rate_score": 98.4,
    "consistency_score": 95.0,
    "freshness_score": 90.0
  },
  "trend": "STABLE",
  "calculated_at": "2026-01-12T10:00:00Z"
}
```

---

### Get Platform Summary

Get platform-wide metrics.

**Endpoint**: `GET /metrics/summary`

**Response** (200 OK):
```json
{
  "total_contracts": 25,
  "active_contracts": 23,
  "total_validations_today": 5432,
  "avg_pass_rate": 97.3,
  "top_contracts": [
    {
      "name": "user-events",
      "validations": 1200,
      "pass_rate": 99.1
    }
  ],
  "contracts_needing_attention": [
    {
      "name": "payment-events",
      "pass_rate": 85.0,
      "issue": "High failure rate"
    }
  ]
}
```

---

### Get Dashboard

Get consolidated dashboard data.

**Endpoint**: `GET /metrics/{contract_id}/dashboard`

**Query Parameters**:
- `days` (optional, default: 7): Number of days

**Response** (200 OK):
```json
{
  "daily_metrics": [...],
  "trend": {...},
  "top_errors": [...],
  "quality_score": {...}
}
```

---

### Aggregate Metrics

Trigger manual metrics aggregation.

**Endpoint**: `POST /metrics/aggregate`

**Request Body**:
```json
{
  "contract_id": "550e8400-e29b-41d4-a716-4466554400000",
  "days": 30
}
```

**Response** (200 OK):
```json
{
  "message": "Metrics aggregated successfully",
  "contract_id": "550e8400-e29b-41d4-a716-4466554400000",
  "days_processed": 30,
  "records_aggregated": 1523
}
```

---

## Templates

### List Templates

Get all contract templates.

**Endpoint**: `GET /templates`

**Response** (200 OK):
```json
{
  "templates": [
    {
      "name": "user-events",
      "domain": "analytics",
      "description": "User signup event template",
      "yaml_content": "..."
    }
  ]
}
```

---

### Get Template

Get a specific contract template.

**Endpoint**: `GET /templates/{template_name}`

**Response** (200 OK):
```json
{
  "name": "user-events",
  "domain": "analytics",
  "description": "User signup event template",
  "yaml_content": "contract_version: \"1.0\"\nschema:\n  user_id:\n    type: string\n    required: true"
}
```

---

## Health Check

### Health Status

Check API and database health.

**Endpoint**: `GET /health`

**Response** (200 OK):
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

---

## Rate Limiting

Currently, there are no rate limits. Future versions will implement rate limiting per API key.

## Pagination

Endpoints that return lists support pagination via `limit` and `offset` parameters:

- `limit`: Maximum number of results (default: 50, max: 1000)
- `offset`: Number of results to skip (default: 0)

Example:
```
GET /contracts?limit=10&offset=20
```

## Error Handling

All errors follow a consistent format:

```json
{
  "error": "ErrorCode",
  "message": "Human-readable error message",
  "detail": "Additional details",
  "status_code": 400,
  "timestamp": "2026-01-12T10:00:00Z",
  "path": "/api/v1/endpoint"
}
```

Common error types:
- `ValidationError`: Invalid input data
- `NotFoundError`: Resource not found
- `DuplicateError`: Resource already exists
- `ContractError`: Contract-related errors
- `ParseError`: YAML parsing errors

---

**Document Version**: 1.0
**Last Updated**: January 12, 2026
