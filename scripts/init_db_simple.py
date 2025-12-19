"""
Simplified database initialization - skips database creation, just runs migrations.
Use this if database and user already exist.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.database import get_database_url


def verify_schema(engine):
    """Verify that all required tables exist."""
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
            print(f"  [OK] {table}")
        else:
            print(f"  [MISSING] {table}")
            all_exist = False
    
    return all_exist


def main():
    """Main initialization function."""
    print("=" * 60)
    print("Finance-Insight Database Initialization (Simple)")
    print("=" * 60)
    
    # Get database URL
    db_url = get_database_url()
    print(f"\nDatabase URL: {db_url.split('@')[0]}@***")
    
    # Test connection first
    print("\nStep 1: Testing database connection...")
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("[OK] Database connection successful!")
    except Exception as e:
        print(f"[FAIL] Database connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Verify user 'finance_user' exists: Run in pgAdmin: SELECT * FROM pg_user WHERE usename = 'finance_user';")
        print("2. Verify password is 'finance_pass'")
        print("3. Check .env file has correct DATABASE_URL")
        return 1
    
    # Step 2: Run Alembic migrations
    print("\nStep 2: Running Alembic migrations...")
    try:
        from alembic.config import Config
        from alembic import command
        
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        print("[OK] Migrations completed successfully.")
    except Exception as e:
        print(f"[FAIL] Error running migrations: {e}")
        return 1
    
    # Step 3: Verify schema
    print("\nStep 3: Verifying schema...")
    if not verify_schema(engine):
        print("\n[WARNING] Some tables are missing, but migrations completed.")
        print("This might be normal if tables are created on first use.")
    else:
        print("\n[OK] All required tables exist!")
    
    print("\n" + "=" * 60)
    print("Database initialization completed!")
    print("=" * 60)
    print("\nNext step: Run 'python scripts/generate_mock_data.py'")
    return 0


if __name__ == "__main__":
    sys.exit(main())

