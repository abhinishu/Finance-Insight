"""
Debug script to inspect database schema and test execution plan queries.
This will help identify why the execution plan endpoint is failing.
"""

from sqlalchemy import text, create_engine, inspect
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from app configuration
try:
    from app.database import get_database_url
    DATABASE_URL = get_database_url()
    print("[OK] Using database URL from app.database.get_database_url()")
except Exception as e:
    print(f"[WARNING] Could not import get_database_url: {e}")
    # Fallback: try to get from environment
    DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if not DATABASE_URL:
        print("[ERROR] No DATABASE_URL found. Please check your .env file.")
        exit(1)

print(f"Database URL: {DATABASE_URL[:50]}...")  # Print partial URL (don't expose password)

try:
    engine = create_engine(DATABASE_URL)
    connection = engine.connect()
    print("[OK] Database Connected Successfully.\n")

    # 2. INSPECT ALL TABLES
    inspector = inspect(engine)
    all_tables = inspector.get_table_names()
    print(f"[INFO] All tables in database ({len(all_tables)} total):")
    for table in sorted(all_tables):
        print(f"  - {table}")
    
    # 3. CHECK business_rules TABLE
    print("\n" + "="*80)
    if "business_rules" in all_tables:
        print("[OK] 'business_rules' table EXISTS.")
        print("\n[INFO] Columns in 'business_rules' table:")
        columns = inspector.get_columns("business_rules")
        column_names = [col['name'] for col in columns]
        for col in columns:
            print(f"  - {col['name']} ({col['type']})")
        
        # Check specifically for is_active
        if "is_active" in column_names:
            print("\n[OK] 'is_active' column EXISTS in business_rules.")
        else:
            print("\n[ERROR] 'is_active' column MISSING in business_rules.")
    else:
        print("[ERROR] 'business_rules' table DOES NOT EXIST.")

    # 4. CHECK metadata_rules TABLE
    print("\n" + "="*80)
    if "metadata_rules" in all_tables:
        print("[OK] 'metadata_rules' table EXISTS.")
        print("\n[INFO] Columns in 'metadata_rules' table:")
        columns = inspector.get_columns("metadata_rules")
        column_names = [col['name'] for col in columns]
        for col in columns:
            print(f"  - {col['name']} ({col['type']})")
        
        # Check specifically for is_active
        if "is_active" in column_names:
            print("\n[OK] 'is_active' column EXISTS in metadata_rules.")
        else:
            print("\n[INFO] 'is_active' column MISSING in metadata_rules (expected - this table doesn't have it).")
    else:
        print("[ERROR] 'metadata_rules' table DOES NOT EXIST.")

    # 5. TEST THE QUERY (The one causing the 500 error)
    print("\n" + "="*80)
    print("[TEST] Testing Execution Plan Query on business_rules...")
    if "business_rules" in all_tables:
        try:
            sql = text("""
                SELECT rule_id, description, node_id, rule_type, strategy, value
                FROM business_rules 
                WHERE is_active = true 
                LIMIT 1
            """)
            result = connection.execute(sql).fetchone()
            if result:
                print(f"[OK] Query Success! Found rule: {result}")
            else:
                print("[WARNING] Query succeeded but returned no rows (table might be empty or no active rules).")
        except Exception as e:
            print(f"[ERROR] Query Failed: {e}")
            print(f"   Error type: {type(e).__name__}")
    else:
        print("[WARNING] Skipping query test - business_rules table doesn't exist.")

    # 6. TEST metadata_rules QUERY (fallback)
    print("\n" + "="*80)
    print("[TEST] Testing Execution Plan Query on metadata_rules (fallback)...")
    if "metadata_rules" in all_tables:
        try:
            sql = text("""
                SELECT rule_id, logic_en as description, node_id
                FROM metadata_rules 
                LIMIT 1
            """)
            result = connection.execute(sql).fetchone()
            if result:
                print(f"[OK] Query Success! Found rule: {result}")
            else:
                print("[WARNING] Query succeeded but returned no rows (table might be empty).")
        except Exception as e:
            print(f"[ERROR] Query Failed: {e}")
            print(f"   Error type: {type(e).__name__}")
    else:
        print("[WARNING] Skipping query test - metadata_rules table doesn't exist.")

    # 7. CHECK FOR USE CASE DATA
    print("\n" + "="*80)
    print("[TEST] Checking for use case data...")
    test_use_case_id = "b90f1708-4087-4117-9820-9226ed1115bb"
    if "metadata_rules" in all_tables:
        try:
            sql = text("""
                SELECT COUNT(*) as rule_count
                FROM metadata_rules 
                WHERE use_case_id = :uc_id::uuid
            """)
            result = connection.execute(sql, {"uc_id": test_use_case_id}).fetchone()
            print(f"[OK] Found {result[0]} rules for use case {test_use_case_id}")
        except Exception as e:
            print(f"[ERROR] Query Failed: {e}")

    connection.close()
    print("\n" + "="*80)
    print("[OK] Debug script completed successfully.")

except Exception as e:
    print(f"\n[FATAL ERROR] Connection failed: {e}")
    import traceback
    print(f"\nFull traceback:")
    print(traceback.format_exc())

