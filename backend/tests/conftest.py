from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_medvision.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only-32-characters")
os.environ.setdefault("JWT_REFRESH_SECRET_KEY", "test-refresh-secret-key-for-pytest-32chars")
os.environ.setdefault("GEMINI_API_KEY", "")
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "100000")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app

TEST_DB_PATH = Path(__file__).parent / "test_medvision.db"
engine = create_engine(f"sqlite:///{TEST_DB_PATH}", connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def _setup_database():
    from app import models  # noqa: F401  ensure all models are registered on Base

    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


def _override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db_session():
    session = TestSessionLocal()
    yield session
    session.close()
