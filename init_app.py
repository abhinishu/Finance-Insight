"""
Database Initialization Script

Ensures database schema integrity on application startup.
Creates all tables if they don't exist (does not modify existing tables).
"""

import logging
from app.database import create_db_engine, get_database_url
from app.models import Base

# Import ALL models so they are registered with Base.metadata
# This ensures all table definitions are loaded before create_all()
from app.models import (
    UseCase,
    UseCaseRun,
    DimHierarchy,
    HierarchyBridge,
    MetadataRule,
    FactPnlGold,
    FactCalculatedResult,
    ReportRegistration,
    DimDictionary,
    FactPnlEntries,
    CalculationRun,
    HistorySnapshot
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db():
    """
    Initialize database schema.
    Creates all tables if they don't exist.
    Note: This does NOT update columns in existing tables (SQLAlchemy limitation),
    but it ensures the baseline schema is present.
    """
    logger.info("🛠️ STARTUP: Checking Database Schema...")
    
    try:
        # Get database URL and create engine
        database_url = get_database_url()
        engine = create_db_engine(database_url)
        
        # This creates tables if they don't exist.
        # It does NOT update columns in existing tables (SQLAlchemy limitation),
        # but it ensures the baseline is there.
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ STARTUP: Database Tables Verified/Created.")
        
        # Clean up engine
        engine.dispose()
        
    except Exception as e:
        logger.error(f"❌ STARTUP FAILED: {e}")
        raise e


if __name__ == "__main__":
    init_db()



