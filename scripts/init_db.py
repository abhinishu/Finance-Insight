"""
Database Initialization Script for Finance-Insight
Creates database if it doesn't exist and runs Alembic migrations.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from app.database import get_database_url


def create_database_if_not_exists(db_url: str, db_name: str = "finance_insight"):
    """
    Create PostgreSQL database if it doesn't exist.
    
    Args:
        db_url: Full database URL
        db_name: Name of the database to create
    """
    # Extract connection details for creating database
    # Format: postgresql://user:pass@host:port/dbname
    parts = db_url.replace("postgresql://", "").split("@")
    if len(parts) != 2:
        print(f"Error: Invalid database URL format: {db_url}")
        return False
    
    auth, host_port_db = parts
    user, password = auth.split(":")
    host_port, _ = host_port_db.split("/")
    
    # Connect to postgres database to create our database
    admin_url = f"postgresql://{user}:{password}@{host_port}/postgres"
    
    try:
        conn = psycopg2.connect(admin_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
            (db_name,)
        )
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Creating database '{db_name}'...")
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            print(f"Database '{db_name}' created successfully.")
        else:
            print(f"Database '{db_name}' already exists.")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"Error creating database: {e}")
        return False


def verify_schema(engine):
    """
    Verify that all required tables exist.
    
    Args:
        engine: SQLAlchemy engine
    """
    from app.models import Base
    
    required_tables = [
        "use_cases",
        "use_case_runs",
        "dim_hierarchy",
        "metadata_rules",
        "fact_pnl_gold",
        "fact_calculated_results"
    ]
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """))
        existing_tables = [row[0] for row in result]
    
    print("\nVerifying schema...")
    all_exist = True
    for table in required_tables:
        if table in existing_tables:
            print(f"  ✓ {table}")
        else:
            print(f"  ✗ {table} - MISSING")
            all_exist = False
    
    return all_exist


def main():
    """Main initialization function."""
    print("=" * 60)
    print("Finance-Insight Database Initialization")
    print("=" * 60)
    
    # Get database URL
    db_url = get_database_url()
    print(f"\nDatabase URL: {db_url.replace(get_database_url().split('@')[0].split(':')[-1], '***')}")
    
    # Extract database name
    db_name = db_url.split("/")[-1]
    
    # Step 1: Create database if it doesn't exist
    print("\nStep 1: Checking database existence...")
    if not create_database_if_not_exists(db_url, db_name):
        print("Failed to create database. Exiting.")
        return 1
    
    # Step 2: Run Alembic migrations
    print("\nStep 2: Running Alembic migrations...")
    try:
        from alembic.config import Config
        from alembic import command
        
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        print("Migrations completed successfully.")
    except Exception as e:
        print(f"Error running migrations: {e}")
        return 1
    
    # Step 3: Verify schema
    print("\nStep 3: Verifying schema...")
    engine = create_engine(db_url)
    if not verify_schema(engine):
        print("\nSchema verification failed. Some tables are missing.")
        return 1
    
    print("\n" + "=" * 60)
    print("Database initialization completed successfully!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())

