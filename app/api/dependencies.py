"""
FastAPI dependencies for Finance-Insight
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import get_database_url

# Create engine and session factory
_engine = None
_SessionLocal = None


def get_db_engine():
    """Get or create database engine."""
    global _engine
    if _engine is None:
        db_url = get_database_url()
        _engine = create_engine(db_url, pool_pre_ping=True)
    return _engine


def get_session_factory():
    """Get or create session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_db_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


def get_db() -> Session:
    """
    Dependency for getting database session.
    Used in FastAPI route dependencies.
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

