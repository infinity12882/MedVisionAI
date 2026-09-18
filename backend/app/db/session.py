"""
Database engine + session factory.

Works with both MySQL (production, per spec — `mysql+pymysql://...`) and
SQLite (zero-setup local dev / CI — `sqlite:///./file.db`). The ORM models
use only cross-compatible column types, so no code changes are needed when
switching between the two; only DATABASE_URL in `.env` changes.
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base


def _build_engine():
    database_url = settings.DATABASE_URL
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}

    try:
        engine = create_engine(
            database_url,
            connect_args=connect_args,
            pool_pre_ping=True,
            pool_recycle=280 if not database_url.startswith("sqlite") else -1,
        )
        with engine.connect():
            pass
        return engine
    except OperationalError:
        if database_url.startswith("sqlite"):
            raise

        fallback_url = "sqlite:///./medvision_dev.db"
        print(
            f"Warning: unable to connect to {database_url!r}; falling back to {fallback_url!r} for local runtime."
        )
        engine = create_engine(
            fallback_url,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
            pool_recycle=-1,
        )
        import app.models  # noqa: F401
        Base.metadata.create_all(engine)
        return engine


engine = _build_engine()

if settings.is_sqlite:
    import app.models  # noqa: F401
    Base.metadata.create_all(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
