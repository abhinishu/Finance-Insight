"""
Database configuration and session management for Finance-Insight.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from app.models import Base


# Database URL - will be loaded from environment variables
DATABASE_URL = "postgresql://finance_user:finance_pass@localhost:5432/finance_insight"


def get_database_url() -> str:
    """
    Get database URL from environment variables or use default.
    Format: postgresql://user:password@host:port/database
    """
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    return os.getenv("DATABASE_URL", DATABASE_URL)


def create_db_engine(database_url: str = None):
    """
    Create SQLAlchemy engine with appropriate configuration.
    
    Args:
        database_url: PostgreSQL connection string. If None, uses get_database_url()
    
    Returns:
        SQLAlchemy Engine instance
    """
    if database_url is None:
        database_url = get_database_url()
    
    engine = create_engine(
        database_url,
        poolclass=NullPool,  # Use NullPool for development; switch to QueuePool for production
        echo=False,  # Set to True for SQL query logging
        future=True,  # Use SQLAlchemy 2.0 style
    )
    return engine


def get_session_factory(engine=None):
    """
    Create a session factory for database operations.
    
    Args:
        engine: SQLAlchemy Engine instance. If None, creates a new one.
    
    Returns:
        SessionMaker instance
    """
    if engine is None:
        engine = create_db_engine()
    
    return sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


def init_db(engine=None):
    """
    Initialize database by creating all tables.
    This should be called once during setup.
    
    Args:
        engine: SQLAlchemy Engine instance. If None, creates a new one.
    """
    if engine is None:
        engine = create_db_engine()
    
    Base.metadata.create_all(engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    # Allow running this file directly to initialize the database
    init_db()

