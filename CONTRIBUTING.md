# Contributing to Data Contract Engine

Thank you for considering contributing to Data Contract Engine!

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Report issues politely

## Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git
- GitHub account

### Setup Development Environment

```bash
# Fork and clone repository
git clone https://github.com/YOUR_USERNAME/data-contract-engine.git
cd data-contract-engine

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/data-contract-engine.git

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Setup environment
cp .env.example .env
# Edit .env with your local settings

# Start PostgreSQL
docker-compose up -d

# Run migrations
alembic upgrade head

# Run tests
pytest
```

## Development Workflow

### 1. Create a Branch

Create a branch for your work:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

**Branch Naming**:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test improvements

### 2. Make Changes

Follow the [Coding Standards](#coding-standards).

### 3. Write Tests

- Add tests for new functionality
- Update tests for bug fixes
- Ensure all tests pass: `pytest`

### 4. Commit Changes

Write meaningful commit messages:

```bash
git add .
git commit -m "Add batch validation for CSV files"
```

**Commit Message Format**:
```
<type>: <subject>

<body>

<footer>
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Example**:
```
feat: Add Parquet file support for batch validation

- Add parquet file handler
- Update batch processor to detect .parquet extension
- Add unit tests for parquet validation

Closes #123
```

### 5. Sync with Upstream

```bash
git fetch upstream
git rebase upstream/main
```

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Create a pull request on GitHub with:
- Clear description
- Link to related issues
- Screenshots (if UI changes)
- Test results

## Coding Standards

### Python Style

We follow [PEP 8](https://pep8.org/) with these tools:

**Formatting** (Black):
```bash
black app/ tests/
```

**Linting** (Ruff):
```bash
ruff check app/ tests/
```

**Auto-fix Ruff Issues**:
```bash
ruff check --fix app/ tests/
```

**Type Checking** (mypy):
```bash
mypy app/
```

### Code Organization

#### File Structure

```
app/
├── api/           # API endpoints (FastAPI routes)
├── core/          # Business logic (services)
├── models/        # Data models (SQLAlchemy, Pydantic)
└── utils/         # Utilities (logging, exceptions)
```

#### Import Order

1. Standard library
2. Third-party imports
3. Local imports
4. Type imports (if used)

```python
import os
from datetime import datetime

from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.core.validation_engine import ValidationEngine
from app.models.schemas import ContractResponse
from typing import Dict, List
```

### Naming Conventions

**Variables and Functions**: `snake_case`
```python
def validate_contract(contract_id: str) -> bool:
    is_valid = check_contract(contract_id)
    return is_valid
```

**Classes**: `PascalCase`
```python
class ValidationEngine:
    def __init__(self, contract: Contract):
        self.contract = contract
```

**Constants**: `UPPER_SNAKE_CASE`
```python
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT = 30
```

**Private Methods**: Leading underscore
```python
class Validator:
    def _validate_type(self, value):
        pass
```

### Type Hints

All functions must have type hints:

```python
from typing import Dict, List, Optional

def process_data(
    data: List[Dict[str, Any]],
    options: Optional[Dict[str, Any]] = None
) -> ValidationResult:
    if options is None:
        options = {}
    return ValidationResult(...)
```

### Docstrings

Use Google-style docstrings:

```python
def validate_contract(
    contract_id: str,
    db: Session
) -> Optional[Contract]:
    """Validate a contract by ID.

    Args:
        contract_id: The UUID of the contract to validate.
        db: Database session for querying.

    Returns:
        Contract object if found, None otherwise.

    Raises:
        DatabaseError: If database query fails.
    """
    try:
        return db.query(Contract).filter(Contract.id == contract_id).first()
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise DatabaseError(f"Failed to fetch contract: {e}")
```

### Error Handling

Use custom exceptions:

```python
from app.utils.exceptions import ContractNotFoundError, ValidationError

def get_contract(contract_id: str) -> Contract:
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise ContractNotFoundError(f"Contract {contract_id} not found")
    return contract
```

### Logging

Use the configured logger:

```python
import logging

logger = logging.getLogger(__name__)

def process_data(data: Dict) -> ValidationResult:
    logger.info(f"Processing data: {len(data)} records")
    
    try:
        result = validate(data)
        logger.debug(f"Validation result: {result.status}")
        return result
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        raise
```

**Log Levels**:
- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Something unexpected but not error
- `ERROR`: Error occurred but system continues
- `CRITICAL`: Critical error, system may not continue

## Testing

### Test Structure

```
tests/
├── conftest.py              # Pytest fixtures
├── test_contract_manager.py   # Unit tests for contract manager
├── test_validation_engine.py  # Unit tests for validation
└── test_api_contracts.py    # Integration tests for API
```

### Unit Tests

Test individual functions in isolation:

```python
import pytest
from app.core.schema_validator import SchemaValidator
from app.models.schemas import ContractSchema, FieldDefinition

def test_string_type_validation():
    """Test string type validation."""
    schema = ContractSchema(schema={
        "email": FieldDefinition(type="string", required=True)
    })
    validator = SchemaValidator(schema)
    
    errors = validator.validate({"email": "test@example.com"})
    assert len(errors) == 0
```

### Integration Tests

Test component interaction:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_contract():
    """Test contract creation via API."""
    response = client.post("/api/v1/contracts", json={
        "name": "test-contract",
        "domain": "analytics",
        "yaml_content": "contract_version: \"1.0\"\nschema: {}"
    })
    
    assert response.status_code == 201
    assert response.json()["version"] == "1.0.0"
```

### Fixtures

Use `conftest.py` for shared fixtures:

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()

@pytest.fixture
def sample_contract():
    return {
        "name": "test-contract",
        "domain": "analytics",
        "yaml_content": "contract_version: \"1.0\"\nschema:\n  user_id:\n    type: string\n    required: true"
    }
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_validation_engine.py

# Run with verbose output
pytest -v

# Run only unit tests
pytest tests/ -m "not integration"

# Run only integration tests
pytest tests/ -m "integration"
```

### Test Coverage

Maintain minimum 80% coverage:

```bash
# Generate coverage report
pytest --cov=app --cov-report=term-missing

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Pull Request Process

### Before Submitting

1. [ ] All tests pass (`pytest`)
2. [ ] Code is formatted (`black`)
3. [ ] No linting errors (`ruff check`)
4. [ ] Type checking passes (`mypy app`)
5. [ ] New tests added
6. [ ] Documentation updated
7. [ ] Commit messages follow format

### PR Description Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Fixes #123
Related to #456

## How to Test
Steps to test the changes:
1. 
2. 
3. 

## Checklist
- [ ] Tests pass locally
- [ ] Code formatted with Black
- [ ] No linting errors
- [ ] Type checking passes
- [ ] Added/updated tests
- [ ] Updated documentation
```

### Review Guidelines

**Reviewers** should check:
- Code follows style guidelines
- Tests are sufficient
- Documentation is clear
- No security vulnerabilities
- Performance impact considered
- Breaking changes documented

### Merge Process

- Maintainer reviews PR
- Request changes if needed
- Author addresses feedback
- Maintainer merges after approval
- Delete branch after merge

## Project Structure

### Backend (`app/`)

```
app/
├── __init__.py
├── main.py                  # FastAPI application entry point
├── config.py                # Application configuration
├── database.py              # Database connection
├── api/                     # API endpoints
│   ├── __init__.py
│   ├── contracts.py          # Contract CRUD
│   ├── validation.py         # Validation endpoints
│   ├── versions.py          # Version management
│   └── metrics.py           # Metrics endpoints
├── core/                    # Business logic
│   ├── __init__.py
│   ├── contract_manager.py   # Contract operations
│   ├── validation_engine.py  # Validation orchestration
│   ├── schema_validator.py   # Type/pattern validation
│   ├── quality_validator.py  # Quality rules
│   ├── version_controller.py # Version management
│   ├── change_detector.py    # Breaking change detection
│   ├── batch_processor.py    # File handling
│   └── metrics_aggregator.py # Metrics calculation
├── models/                  # Data models
│   ├── __init__.py
│   ├── database.py          # SQLAlchemy models
│   └── schemas.py           # Pydantic schemas
└── utils/                   # Utilities
    ├── __init__.py
    ├── logging.py           # Logging setup
    ├── exceptions.py        # Custom exceptions
    └── helpers.py          # Helper functions
```

### Frontend (`frontend/`)

```
frontend/
├── streamlit_app.py        # Main app entry point
├── .streamlit/
│   └── config.toml        # Streamlit configuration
├── pages/                  # Multi-page app
│   ├── 1_📝_Contracts.py
│   ├── 2_✅_Validate.py
│   └── 3_📊_Dashboard.py
└── components/              # Reusable components
    ├── api_client.py
    ├── contract_editor.py
    ├── metrics_charts.py
    └── validation_display.py
```

## Reporting Issues

### Bug Reports

Include:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Logs/error messages

### Feature Requests

Include:
- Use case description
- Proposed solution
- Alternatives considered
- Examples or mockups

## Documentation

### Updating Documentation

- Update README.md for user-facing changes
- Update docs/ for technical changes
- Update CHANGELOG.md for version changes
- Add examples for new features

### Docstring Comments

Code should be self-documenting. Add docstrings for:
- All public functions
- All classes
- Complex algorithms
- Non-obvious logic

## Questions?

- Open an issue on GitHub
- Contact maintainers via email
- Join community discussions

---

Thank you for contributing! 🎉
