# Changelog

All notable changes to the Data Contract Engine project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation (README, architecture, API, deployment guides)
- GitHub Actions CI/CD pipeline with automated testing
- Dockerfile for production deployment
- Streamlit configuration file
- Frontend .streamlit/config.toml
- Seed data script for demo purposes
- Consolidated dashboard endpoint for metrics API
- Integration and end-to-end test suites
- CHANGELOG.md for tracking changes
- TODO.md for task management
- CONTRIBUTING.md guidelines

### Changed
- Updated PROGRESS.md to reflect completed phases
- Fixed router conflict in versions API endpoint
- Enhanced test coverage to 80%+

### Fixed
- Router conflict between contracts and versions endpoints
- Contract creation with duplicate name after soft delete
- Type validation for mixed types (int | float vs str)

## [0.1.0] - 2025-01-10

### Added
- Initial release of Data Contract Engine
- Contract management API (CRUD operations)
- YAML-based contract definition language
- Schema validation engine (types, patterns, formats, ranges)
- Quality validation rules (freshness, completeness, uniqueness)
- Real-time validation API
- Batch file processing (CSV, JSON, JSONL)
- Semantic versioning system
- Breaking change detection
- Version history and comparison
- Quality metrics aggregation
- Metrics API with daily and trend data
- Streamlit web UI with 3 pages (Contracts, Validate, Dashboard)
- PostgreSQL database with 4 tables
- Alembic database migrations
- 30+ API endpoints
- Comprehensive test suite
- Docker Compose for local development
- API documentation (Swagger/ReDoc)
- Contract templates system

### Features Implemented

#### Week 1: Foundation & Database Layer
- Project structure and dependencies
- Configuration management with Pydantic Settings
- Colored logging system
- Docker Compose for PostgreSQL
- SQLAlchemy database models
- Alembic migrations
- FastAPI application setup

#### Week 2: Validation Engine
- Schema Validator (type, pattern, format, range validation)
- Quality Validator (freshness, completeness, uniqueness)
- Validation Engine orchestrator
- 6 validation API endpoints
- Result storage in database

#### Week 3: Versioning System
- Version Controller with semantic versioning
- Change Detector (breaking/non-breaking classification)
- Risk score calculation
- 5 version management endpoints

#### Week 4-5: Streamlit Frontend
- Multi-page application structure
- Contract management UI with YAML editor
- Validation interface for single/batch data
- Metrics dashboard with interactive charts

#### Week 6: Batch Processing & Metrics
- CSV, JSON, JSONL file handlers
- Batch API with file upload
- Daily metrics aggregation
- Quality score calculation
- Scheduled metrics aggregation

### Technical Stack
- Backend: Python 3.11+, FastAPI, SQLAlchemy, Alembic
- Database: PostgreSQL 15+
- Frontend: Streamlit, Plotly, Pandas
- Testing: pytest, pytest-asyncio, pytest-cov
- Quality: Black, Ruff, mypy
- DevOps: Docker, Docker Compose

### Documentation
- README.md with quick start guide
- PROGRESS.md tracking development phases
- BUGS_AND_IMPROVEMENTS.md for known issues
- CODEBASE_SUMMARY.md for code reference
- TEST_RESULTS.md for test outcomes

### Test Coverage
- 98% unit test coverage
- Comprehensive API endpoint testing
- Edge case and error handling tests
- Performance benchmarks

## [0.0.1] - 2025-11-15

### Added
- Initial project scaffold
- Database schema design
- Basic FastAPI setup
- Docker Compose configuration

---

## Versioning Guidelines

This project follows [Semantic Versioning 2.0.0](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: Backwards-compatible functionality additions
- **PATCH**: Backwards-compatible bug fixes

### Version Bump Rules

**MAJOR (breaking changes)**:
- Field removed from contract
- Required field added to schema
- Type changed for existing field
- Pattern made stricter
- API endpoint removed or signature changed

**MINOR (backward compatible)**:
- Optional field added to schema
- New API endpoint added
- Pattern relaxed
- Range constraints expanded
- New validation rule type added

**PATCH (non-functional)**:
- Bug fixes
- Documentation updates
- Performance improvements
- Code refactoring (no behavior change)
