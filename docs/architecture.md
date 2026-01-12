# Data Contract Engine - Architecture

This document describes the system architecture, design decisions, and component interactions.

## Table of Contents

- [Overview](#overview)
- [High-Level Architecture](#high-level-architecture)
- [Layered Architecture](#layered-architecture)
- [Component Design](#component-design)
- [Data Flow](#data-flow)
- [Database Schema](#database-schema)
- [Design Principles](#design-principles)
- [Technology Choices](#technology-choices)

## Overview

The Data Contract Engine is a 3-tier web application that enforces data quality through contract-based validation. The system follows a layered architecture with clear separation of concerns.

### Key Characteristics

- **Stateless API**: REST endpoints don't maintain session state
- **Layer Separation**: Presentation, Business Logic, Data Access, and Domain layers
- **Event-Driven**: Scheduled metrics aggregation via APScheduler
- **Async I/O**: FastAPI with async database operations
- **Validation-First**: Data validated before entering the system

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Streamlit UI  │  │ REST Clients │  │  External    │ │
│  │              │  │ (cURL, SDK) │  │  Systems     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │ HTTP/REST
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Presentation Layer                         │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              FastAPI Application                        │  │
│  │  - Request routing                                    │  │
│  │  - Request/Response validation (Pydantic)             │  │
│  │  - Error handling                                     │  │
│  │  - CORS, security middleware                           │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Business Logic Layer                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │ Contract     │ │ Validation   │ │ Versioning   │      │
│  │ Manager      │ │ Engine      │ │ Controller   │      │
│  └──────────────┘ └──────────────┘ └──────────────┘      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │ Schema       │ │ Quality      │ │ Metrics      │      │
│  │ Validator    │ │ Validator    │ │ Aggregator   │      │
│  └──────────────┘ └──────────────┘ └──────────────┘      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │ Change       │ │ Batch        │ │ YAML Parser   │      │
│  │ Detector    │ │ Processor    │ │              │      │
│  └──────────────┘ └──────────────┘ └──────────────┘      │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Access Layer                         │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              SQLAlchemy ORM                            │  │
│  │  - Database models (SQLAlchemy Base)                  │  │
│  │  - Session management                                │  │
│  │  - Query abstraction                                │  │
│  │  - Connection pooling                                 │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │ SQL
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                             │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              PostgreSQL Database                       │  │
│  │  - contracts                                        │  │
│  │  - contract_versions                                  │  │
│  │  - validation_results                                │  │
│  │  - quality_metrics                                   │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Layered Architecture

### Layer 1: Presentation (API Layer)

**Location**: `app/api/`

**Responsibilities**:
- HTTP request/response handling
- Request validation (basic Pydantic models)
- Authentication (future)
- Error response formatting
- API documentation (OpenAPI/Swagger)

**Key Components**:
- `contracts.py` - Contract CRUD endpoints
- `validation.py` - Validation endpoints
- `versions.py` - Version management endpoints
- `metrics.py` - Metrics and analytics endpoints
- `templates.py` - Contract template endpoints

**Design Rule**: No business logic in this layer. All validation logic delegated to services.

### Layer 2: Business Logic (Service Layer)

**Location**: `app/core/`

**Responsibilities**:
- Contract lifecycle management
- Validation orchestration
- Version calculation
- Change detection
- File processing
- Metrics calculation

**Key Components**:
- `contract_manager.py` - Contract CRUD operations
- `validation_engine.py` - Validation orchestration
- `schema_validator.py` - Type/pattern/format validation
- `quality_validator.py` - Business rule validation
- `version_controller.py` - Semantic versioning
- `change_detector.py` - Breaking change detection
- `batch_processor.py` - File handling
- `metrics_aggregator.py` - Metrics calculation
- `yaml_parser.py` - Contract parsing
- `file_handlers.py` - File format handlers

**Design Rule**: Framework-agnostic. No FastAPI/HTTP dependencies.

### Layer 3: Data Access (Repository Layer)

**Location**: `app/models/database.py`

**Responsibilities**:
- Database CRUD operations
- Session management
- Transaction handling
- Query optimization

**Key Components**:
- SQLAlchemy ORM models:
  - `Contract` - Contract definitions
  - `ContractVersion` - Version history
  - `ValidationResult` - Validation outcomes
  - `QualityMetric` - Aggregated metrics

**Design Rule**: No business logic. Only database operations.

### Layer 4: Domain Models

**Location**: `app/models/schemas.py`

**Responsibilities**:
- Domain concepts and value objects
- Request/response models (Pydantic)
- Validation rules (Pydantic validators)

**Design Rule**: Pure Python classes, no external dependencies.

## Component Design

### Validation Engine

The validation engine orchestrates multiple validators in sequence:

```
Data Record
    │
    ├─→ Schema Validator (types, patterns, formats)
    │       │
    │       └─→ Fail if schema errors
    │
    ├─→ Quality Validator (freshness, completeness)
    │       │
    │       └─→ Collect all quality errors
    │
    └─→ Result Aggregator
            │
            └─→ Combine errors, calculate pass/fail
```

**Design Pattern**: Chain of Responsibility

### Version Controller

Implements semantic versioning based on change detection:

```
Old Contract → Change Detector → New Contract
                    │
                    ├─→ Breaking changes → MAJOR version bump
                    ├─→ Additions → MINOR version bump
                    └─→ Changes only → PATCH version bump
```

**Design Pattern**: Strategy Pattern

### Batch Processor

Processes large files in chunks for memory efficiency:

```
Large File
    │
    ├─→ Detect format (CSV/JSON/JSONL)
    │
    ├─→ Chunk reader (1000 records/chunk)
    │
    ├─→ Validate each chunk
    │
    └─→ Aggregate results
```

**Design Pattern**: Iterator Pattern

## Data Flow

### Contract Creation Flow

```
1. Client → POST /api/v1/contracts
   ↓
2. API Layer → Validate request
   ↓
3. ContractManager → Parse YAML
   ↓
4. YAMLParser → Extract schema & rules
   ↓
5. ContractManager → Create version 1.0.0
   ↓
6. Database → Insert contract
   ↓
7. Response → Contract object with version
```

### Validation Flow

```
1. Client → POST /api/v1/validate/{contract_id}
   ↓
2. API Layer → Fetch contract
   ↓
3. ValidationEngine → Parse contract
   ↓
4. SchemaValidator → Validate types/patterns
   ↓
5. QualityValidator → Validate business rules
   ↓
6. ValidationResult → Aggregate errors
   ↓
7. Database → Store result
   ↓
8. Response → PASS/FAIL with errors
```

### Version Update Flow

```
1. Client → PUT /api/v1/contracts/{id}
   ↓
2. API Layer → Parse new YAML
   ↓
3. VersionController → Detect changes
   ↓
4. ChangeDetector → Classify (breaking/non-breaking)
   ↓
5. VersionController → Calculate new version
   ↓
6. ContractManager → Create version record
   ↓
7. Database → Update contract
   ↓
8. Response → New version with change report
```

## Database Schema

### Entity Relationship Diagram

```
┌─────────────────┐         ┌─────────────────────┐
│    contracts    │         │ contract_versions   │
├─────────────────┤         ├─────────────────────┤
│ id (PK)        │◄───────│ id (PK)            │
│ name           │         │ contract_id (FK)     │
│ version        │         │ version             │
│ domain         │         │ yaml_content        │
│ yaml_content   │         │ change_type         │
│ is_active      │         │ change_summary      │
│ created_at     │         │ created_at          │
│ updated_at     │         └─────────────────────┘
└─────────────────┘
         │
         │
         ├──────────────────────────┬──────────────────┐
         │                          │                  │
         ▼                          ▼                  ▼
┌─────────────────┐    ┌─────────────────────┐  ┌─────────────────┐
│validation_      │    │ quality_metrics     │  │ contract_      │
│results         │    │                     │  │ versions       │
├─────────────────┤    ├─────────────────────┤  │ (more rows)    │
│ id (PK)        │    │ id (PK)            │  └─────────────────┘
│ contract_id    │    │ contract_id (FK)     │
│ status         │    │ metric_date         │
│ data_snapshot  │    │ total_validations  │
│ errors         │    │ passed             │
│ execution_time │    │ failed             │
│ validated_at   │    │ pass_rate          │
└─────────────────┘    │ quality_score       │
                       └─────────────────────┘
```

### Key Indexes

- `contracts(name, is_active)` - Fast contract lookups
- `contracts(domain)` - Domain filtering
- `contract_versions(contract_id)` - Version history queries
- `validation_results(contract_id, validated_at)` - Result pagination
- `validation_results(status)` - Filtering by status
- `quality_metrics(contract_id, metric_date)` - Daily metrics queries

## Design Principles

### 1. Separation of Concerns

Each layer has a single, well-defined responsibility. Layers communicate via dependency injection.

**Example**: API layer doesn't validate contracts; it delegates to ValidationEngine.

### 2. Dependency Inversion

High-level modules don't depend on low-level modules. Both depend on abstractions.

**Example**: Business logic depends on SQLAlchemy models (abstraction), not raw SQL.

### 3. Single Responsibility

Each class has one reason to change.

**Example**: SchemaValidator only handles schema validation, not quality rules.

### 4. Open/Closed Principle

Open for extension, closed for modification.

**Example**: New file format? Extend `FileHandler` base class, don't modify existing handlers.

### 5. Fail Fast

Validate input early and return clear error messages.

**Example**: Invalid YAML rejected at API layer, not after parsing.

### 6. Idempotency

Same input produces same output; safe to retry.

**Example**: Validating same record twice returns identical results.

## Technology Choices

### Python 3.11+

**Why**:
- Type hints for better code quality
- Performance improvements over 3.8-3.10
- Rich ecosystem for data engineering
- Industry standard for data platforms

### FastAPI

**Why**:
- Automatic API documentation
- Built-in data validation (Pydantic)
- Async support for better performance
- Modern Python patterns
- Growing industry adoption

### PostgreSQL

**Why**:
- JSONB for flexible error storage
- Strong consistency guarantees
- Excellent query performance
- Free hosting options (Render, Supabase)
- Industry standard

### SQLAlchemy 2.0+

**Why**:
- Type-safe ORM with Python 3.11+
- Async support
- Database-agnostic
- Migration support (Alembic)
- Connection pooling

### Streamlit

**Why**:
- Python-native (no JavaScript required)
- Rapid UI development
- Built-in components and state management
- Free hosting (Streamlit Cloud)
- Perfect for data applications

## Scalability Considerations

### Current State

- **Single Instance**: Vertical scaling
- **Stateless API**: Can horizontally scale
- **Connection Pooling**: SQLAlchemy manages connections

### Future Scaling

1. **Horizontal Scaling**:
   - Add load balancer (NGINX)
   - Run multiple API instances
   - Session-based metrics aggregation

2. **Caching Layer**:
   - Redis for contract cache
   - Reduce database queries
   - Faster validation for repeated contracts

3. **Database Scaling**:
   - Read replicas for metrics queries
   - Connection pooling optimization
   - Query optimization with EXPLAIN ANALYZE

4. **Message Queue**:
   - RabbitMQ/Kafka for async batch processing
   - Decouple validation from API response
   - Background job processing

## Security Considerations

### Current Measures

- CORS configuration
- XSRF protection (frontend)
- Input validation (Pydantic)
- SQL injection prevention (SQLAlchemy)
- Error message sanitization

### Future Enhancements

- API authentication (JWT/OAuth)
- Rate limiting per API key
- Request signing
- Webhook secret verification
- File upload validation (size, type)

---

**Document Version**: 1.0
**Last Updated**: January 12, 2026
