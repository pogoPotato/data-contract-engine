# Contract Specification

Complete reference for the Data Contract Definition Language (CDL).

## Table of Contents

- [Overview](#overview)
- [Contract Structure](#contract-structure)
- [Field Definitions](#field-definitions)
- [Data Types](#data-types)
- [Validation Rules](#validation-rules)
- [Quality Rules](#quality-rules)
- [Examples](#examples)

## Overview

The Data Contract Definition Language (CDL) is a YAML-based format for defining data expectations. It provides:

- **Schema Definition**: Field types, patterns, and constraints
- **Quality Rules**: Business-level data quality checks
- **Versioning**: Semantic versioning for contract evolution
- **Validation**: Machine-parsable rules for automated validation

## Contract Structure

### Minimal Contract

```yaml
contract_version: "1.0"
domain: "analytics"
schema:
  user_id:
    type: string
    required: true
```

### Complete Contract

```yaml
contract_version: "1.0"
domain: "user-analytics"
description: "User signup events from web application"

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
    max_latency_hours: 2
    description: "Data should not be older than 2 hours"
  
  completeness:
    min_row_count: 1000
    max_null_percentage: 5.0
    description: "Expect at least 1000 records with <5% nulls"
  
  uniqueness:
    fields: ["user_id"]
    description: "No duplicate user IDs allowed"
  
  statistics:
    age:
      mean:
        min: 25
        max: 45
      std_dev:
        max: 15
```

### Contract Sections

| Section | Required | Description |
|---------|-----------|-------------|
| `contract_version` | Yes | Contract version format (e.g., "1.0") |
| `domain` | Yes | Business domain (e.g., "analytics", "finance") |
| `description` | No | Human-readable description |
| `schema` | Yes | Field definitions |
| `quality_rules` | No | Data quality rules |

## Field Definitions

### Basic Field

```yaml
field_name:
  type: string
  required: true
```

### Field with Constraints

```yaml
age:
  type: integer
  required: true
  min: 18
  max: 120
  description: "User age"
```

### Field with Pattern

```yaml
user_id:
  type: string
  required: true
  pattern: "^usr_\\d+$"
  description: "User ID must start with 'usr_' followed by digits"
```

### Field with Format

```yaml
email:
  type: string
  required: true
  format: email
  description: "Valid email address"
```

### Field Properties

| Property | Type | Description | Example |
|----------|--------|-------------|----------|
| `type` | Required | Data type of field | `string`, `integer`, `boolean` |
| `required` | Optional | Whether field is required | `true`, `false` (default: `false`) |
| `pattern` | Optional | Regex pattern for validation | `"^usr_\\d+$"` |
| `format` | Optional | Predefined format | `email`, `url`, `uuid`, `ipv4` |
| `min` | Optional | Minimum value (inclusive) | `18`, `0.0` |
| `max` | Optional | Maximum value (inclusive) | `120`, `100.0` |
| `min_length` | Optional | Minimum string length | `3` |
| `max_length` | Optional | Maximum string length | `50` |
| `description` | Optional | Field description | `"User email address"` |

## Data Types

### Primitive Types

#### String

```yaml
username:
  type: string
  min_length: 3
  max_length: 50
```

**Valid Values**: Any text string

**Constraints**:
- `min_length`: Minimum character count
- `max_length`: Maximum character count
- `pattern`: Regex pattern
- `format`: Email, URL, UUID, IPv4

---

#### Integer

```yaml
age:
  type: integer
  min: 0
  max: 150
```

**Valid Values**: Whole numbers

**Constraints**:
- `min`: Minimum value (inclusive)
- `max`: Maximum value (inclusive)

---

#### Float

```yaml
price:
  type: float
  min: 0.0
  max: 99999.99
```

**Valid Values**: Decimal numbers

**Constraints**:
- `min`: Minimum value (inclusive)
- `max`: Maximum value (inclusive)

---

#### Boolean

```yaml
is_active:
  type: boolean
```

**Valid Values**: `true` or `false`

**Constraints**: None

---

#### Timestamp

```yaml
created_at:
  type: timestamp
  min: "2020-01-01T00:00:00Z"
  max: "2030-12-31T23:59:59Z"
```

**Valid Values**: ISO 8601 datetime string

**Constraints**:
- `min`: Minimum timestamp (inclusive)
- `max`: Maximum timestamp (inclusive)

**Examples**:
- `"2026-01-12T10:00:00Z"`
- `"2026-01-12"`
- `"2026-01-12 10:00:00"`

---

### Complex Types

#### Array

```yaml
tags:
  type: array
  min_items: 1
  max_items: 10
```

**Valid Values**: JSON array

**Constraints**:
- `min_items`: Minimum array length
- `max_items`: Maximum array length

---

#### Object

```yaml
address:
  type: object
  required: true
```

**Valid Values**: JSON object

**Constraints**: None (structure validated separately)

---

## Validation Rules

### Required Field

Field must be present in data:

```yaml
email:
  type: string
  required: true
```

**Validation**:
```json
{"email": "test@example.com"}  // PASS
{}  // FAIL - Missing required field
```

---

### Type Validation

Data type must match field type:

```yaml
age:
  type: integer
```

**Validation**:
```json
{"age": 25}  // PASS
{"age": "25"}  // FAIL - Type mismatch
```

---

### Pattern Validation

Value must match regex pattern:

```yaml
user_id:
  type: string
  pattern: "^usr_\\d+$"
```

**Validation**:
```json
{"user_id": "usr_123"}  // PASS
{"user_id": "user_123"}  // FAIL - Pattern mismatch
{"user_id": "usr_abc"}  // FAIL - Pattern mismatch
```

---

### Format Validation

Value must match predefined format:

```yaml
email:
  type: string
  format: email
```

**Validation**:
```json
{"email": "test@example.com"}  // PASS
{"email": "not-an-email"}  // FAIL - Invalid format
```

**Supported Formats**:
- `email`: RFC 5322 email address
- `url`: HTTP/HTTPS URL
- `uuid`: RFC 4122 UUID
- `ipv4`: IPv4 address

---

### Range Validation

Value must be within range:

```yaml
age:
  type: integer
  min: 18
  max: 120
```

**Validation**:
```json
{"age": 25}  // PASS
{"age": 17}  // FAIL - Too small
{"age": 150}  // FAIL - Too large
```

---

### Length Validation

String length must be within bounds:

```yaml
username:
  type: string
  min_length: 3
  max_length: 20
```

**Validation**:
```json
{"username": "john"}  // PASS
{"username": "ab"}  // FAIL - Too short
{"username": "a" * 21}  // FAIL - Too long
```

---

## Quality Rules

### Freshness

Data should not be too old:

```yaml
quality_rules:
  freshness:
    max_latency_hours: 2
    description: "Data should not be older than 2 hours"
```

**Validation**:
- Checks if data timestamp is within `max_latency_hours` from now
- Fails if data is stale

**Use Case**: Real-time analytics, data freshness monitoring

---

### Completeness

Ensure sufficient data volume and quality:

```yaml
quality_rules:
  completeness:
    min_row_count: 1000
    max_null_percentage: 5.0
    description: "Expect at least 1000 records with <5% nulls"
```

**Validation**:
- `min_row_count`: Minimum number of records
- `max_null_percentage`: Maximum percentage of null values (0-100)

**Use Case**: Detect missing data, data pipeline issues

---

### Uniqueness

Detect duplicate records:

```yaml
quality_rules:
  uniqueness:
    fields: ["user_id", "email"]
    description: "No duplicate user IDs or emails"
```

**Validation**:
- Checks for duplicate values in specified fields
- Fails if duplicates found

**Use Case**: Primary key validation, data deduplication

---

### Statistics

Validate aggregate statistics:

```yaml
quality_rules:
  statistics:
    age:
      mean:
        min: 25
        max: 45
      std_dev:
        max: 15
```

**Validation**:
- `mean`: Average must be within range
- `std_dev`: Standard deviation must be below threshold

**Use Case**: Detect anomalies, data drift

---

## Examples

### User Events Contract

```yaml
contract_version: "1.0"
domain: "user-analytics"
description: "User signup and activity events"

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
    description: "User age"
  
  country:
    type: string
    min_length: 2
    max_length: 2
    required: true
    pattern: "^[A-Z]{2}$"
    description: "Two-letter country code"

quality_rules:
  freshness:
    max_latency_hours: 24
    description: "Events should be less than 24 hours old"
  
  completeness:
    min_row_count: 100
    max_null_percentage: 1.0
```

### Financial Transactions Contract

```yaml
contract_version: "1.0"
domain: "finance"
description: "Payment and transaction events"

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
    description: "Three-letter currency code (e.g., USD, EUR)"
  
  timestamp:
    type: timestamp
    required: true
    min: "2020-01-01"
    description: "Transaction timestamp"

quality_rules:
  uniqueness:
    fields: ["transaction_id"]
    description: "Transaction IDs must be unique"
  
  freshness:
    max_latency_hours: 1
    description: "Transactions should be processed within 1 hour"
```

### API Request Contract

```yaml
contract_version: "1.0"
domain: "api-gateway"
description: "Incoming API request validation"

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
```

## Validation Error Types

| Error Type | Description |
|-------------|-------------|
| `REQUIRED_FIELD_MISSING` | Required field not present |
| `TYPE_MISMATCH` | Value type doesn't match field type |
| `PATTERN_MISMATCH` | Value doesn't match regex pattern |
| `FORMAT_MISMATCH` | Value doesn't match predefined format |
| `VALUE_TOO_SMALL` | Value below minimum threshold |
| `VALUE_TOO_LARGE` | Value above maximum threshold |
| `LENGTH_TOO_SHORT` | String below minimum length |
| `LENGTH_TOO_LONG` | String above maximum length |
| `INVALID_TIMESTAMP` | Timestamp format invalid or out of range |
| `FRESHNESS_FAILED` | Data exceeds max latency |
| `COMPLETENESS_FAILED` | Row count or null percentage out of bounds |
| `UNIQUENESS_FAILED` | Duplicate values detected |
| `STATISTICS_FAILED` | Aggregate statistics out of bounds |

## Best Practices

### Naming Conventions

- **Contract Names**: Use kebab-case (`user-events`, `payment-transactions`)
- **Field Names**: Use snake_case (`user_id`, `email_address`)
- **Domains**: Use lowercase, single word (`analytics`, `finance`, `marketing`)

### Versioning

- Start with `1.0` for initial version
- Bump version on changes:
  - `1.0` → `1.1`: Add optional field
  - `1.1` → `2.0`: Make field required (breaking)
  - `2.0` → `2.0.1`: Update description (patch)

### Documentation

- Always add `description` to fields
- Explain why quality rules exist
- Document business rules in descriptions

### Testing

- Test contract with valid data
- Test with invalid data (negative cases)
- Test edge cases (min/max values)
- Test with missing required fields

---

**Document Version**: 1.0
**Last Updated**: January 12, 2026
