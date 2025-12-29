import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()  # Load .env file

# DEFAULT: Laptop Creds (Change these to match your local setup)
DEFAULT_URL = "postgresql://postgres:password@localhost:5432/finance_insight"

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_URL)

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Note: Base is defined in app.models.py and imported from there by other modules


# Backward compatibility functions for existing code
def get_database_url() -> str:
    """
    Get database URL from environment variables or use default.
    Format: postgresql://user:password@host:port/database
    """
    return os.getenv("DATABASE_URL", DEFAULT_URL)


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
    
    return create_engine(database_url, pool_pre_ping=True)


def get_session_factory(engine_instance=None):
    """
    Create a session factory for database operations.
    
    Args:
        engine_instance: SQLAlchemy Engine instance. If None, uses the global engine.
    
    Returns:
        SessionMaker instance
    """
    if engine_instance is None:
        engine_instance = engine
    
    return sessionmaker(autocommit=False, autoflush=False, bind=engine_instance)
