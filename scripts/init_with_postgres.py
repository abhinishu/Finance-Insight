"""
Initialize database using postgres superuser.
This bypasses the URL parsing issues with special characters in passwords.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

import psycopg2
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus


def main():
    """Main initialization function."""
    print("=" * 60)
    print("Finance-Insight Database Initialization (Postgres Superuser)")
    print("=" * 60)
    
    # Use postgres superuser with direct connection parameters
    postgres_password = "Hisv2cstm2010@"
    
    # Test connection with psycopg2 directly
    print("\nStep 1: Testing database connection...")
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="finance_insight",
            user="postgres",
            password=postgres_password
        )
        print("[OK] Database connection successful!")
        conn.close()
    except Exception as e:
        print(f"[FAIL] Database connection failed: {e}")
        print("\nPlease verify:")
        print("1. PostgreSQL is running")
        print("2. Password is correct")
        print("3. Database 'finance_insight' exists")
        return 1
    
    # Create SQLAlchemy engine with properly encoded URL
    encoded_password = quote_plus(postgres_password)
    db_url = f"postgresql://postgres:{encoded_password}@localhost:5432/finance_insight"
    
    print("\nStep 2: Running Alembic migrations...")
    try:
        from alembic.config import Config
        from alembic import command
        
        alembic_cfg = Config("alembic.ini")
        # Set the database URL for alembic
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        command.upgrade(alembic_cfg, "head")
        print("[OK] Migrations completed successfully.")
    except Exception as e:
        print(f"[FAIL] Error running migrations: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Step 3: Verify schema
    print("\nStep 3: Verifying schema...")
    try:
        engine = create_engine(db_url)
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
        
        all_exist = True
        for table in required_tables:
            if table in existing_tables:
                print(f"  [OK] {table}")
            else:
                print(f"  [MISSING] {table}")
                all_exist = False
        
        if all_exist:
            print("\n[OK] All required tables exist!")
        else:
            print("\n[WARNING] Some tables are missing.")
    except Exception as e:
        print(f"[WARNING] Could not verify schema: {e}")
    
    print("\n" + "=" * 60)
    print("Database initialization completed!")
    print("=" * 60)
    print("\nNext step: Run 'python scripts/generate_mock_data.py'")
    print("\nNote: You may want to create finance_user later and update .env")
    return 0


if __name__ == "__main__":
    sys.exit(main())

