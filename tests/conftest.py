import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.database import Base

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_engine():
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_engine) -> Generator[Session, None, None]:
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture(scope="function")
def sample_contract_data():
    from app.models.schemas import ContractCreate
    
    return ContractCreate(
        name="test-contract",
        domain="test",
        yaml_content="""contract_version: "1.0"
domain: "test"
description: "Test contract"
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
    min: 0
    max: 120
quality_rules:
  freshness:
    max_latency_hours: 24
"""
    )