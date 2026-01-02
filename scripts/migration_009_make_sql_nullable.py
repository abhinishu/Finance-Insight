"""
Migration 009: Make sql_where and logic_en Columns Nullable in metadata_rules
This migration allows NODE_ARITHMETIC (math) rules to be created without requiring sql_where or logic_en.

Phase 5.7: Math Rules Support
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text, inspect
from app.database import SessionLocal

def run_migration_009():
    """
    Execute Migration 009: Make sql_where and logic_en nullable in metadata_rules table.
    """
    print("=" * 80)
    print("MIGRATION 009: Make sql_where and logic_en Columns Nullable")
    print("=" * 80)
    print()
    print("This migration allows NODE_ARITHMETIC (math) rules to be created")
    print("without requiring the sql_where or logic_en fields.")
    print()
    
    db = SessionLocal()
    
    try:
        # Step 1: Check current column definitions
        print("STEP 1: Checking Current Column Definitions")
        print("-" * 80)
        
        inspector = inspect(db.bind)
        columns = inspector.get_columns('metadata_rules')
        
        sql_where_column = next((col for col in columns if col['name'] == 'sql_where'), None)
        logic_en_column = next((col for col in columns if col['name'] == 'logic_en'), None)
        
        if not sql_where_column:
            print("[ERROR] Column 'sql_where' not found in metadata_rules table!")
            return False
        if not logic_en_column:
            print("[ERROR] Column 'logic_en' not found in metadata_rules table!")
            return False
        
        sql_where_nullable = sql_where_column.get('nullable', False)
        logic_en_nullable = logic_en_column.get('nullable', False)
        
        print(f"  Column: sql_where")
        print(f"    Current nullable: {sql_where_nullable}")
        print(f"    Type: {sql_where_column.get('type', 'Unknown')}")
        print()
        print(f"  Column: logic_en")
        print(f"    Current nullable: {logic_en_nullable}")
        print(f"    Type: {logic_en_column.get('type', 'Unknown')}")
        print()
        
        if sql_where_nullable and logic_en_nullable:
            print("[INFO] Both columns are already nullable. No migration needed.")
            return True
        
        # Step 2: Execute migration
        print("STEP 2: Executing Migration")
        print("-" * 80)
        
        migration_statements = []
        
        if not sql_where_nullable:
            migration_statements.append("ALTER TABLE metadata_rules ALTER COLUMN sql_where DROP NOT NULL;")
        
        if not logic_en_nullable:
            migration_statements.append("ALTER TABLE metadata_rules ALTER COLUMN logic_en DROP NOT NULL;")
        
        if not migration_statements:
            print("[INFO] No migrations needed - all columns are already nullable.")
            return True
        
        print("  Executing SQL statements:")
        for stmt in migration_statements:
            print(f"    {stmt.strip()}")
        print()
        
        # Execute all statements in a single transaction
        for stmt in migration_statements:
            db.execute(text(stmt))
        
        db.commit()
        
        print("[OK] Migration executed successfully")
        print()
        
        # Step 3: Verify migration
        print("STEP 3: Verifying Migration")
        print("-" * 80)
        
        # Refresh inspector to get updated column info
        inspector = inspect(db.bind)
        columns = inspector.get_columns('metadata_rules')
        sql_where_column = next((col for col in columns if col['name'] == 'sql_where'), None)
        logic_en_column = next((col for col in columns if col['name'] == 'logic_en'), None)
        
        if not sql_where_column or not logic_en_column:
            print("[ERROR] Columns not found after migration!")
            return False
        
        sql_where_nullable_after = sql_where_column.get('nullable', False)
        logic_en_nullable_after = logic_en_column.get('nullable', False)
        
        print(f"  Column: sql_where")
        print(f"    Nullable after migration: {sql_where_nullable_after}")
        print()
        print(f"  Column: logic_en")
        print(f"    Nullable after migration: {logic_en_nullable_after}")
        print()
        
        if sql_where_nullable_after and logic_en_nullable_after:
            print("[SUCCESS] Migration completed successfully!")
            print("  Both sql_where and logic_en columns are now nullable.")
            print("  Math rules (NODE_ARITHMETIC) can now be created without sql_where or logic_en.")
            return True
        else:
            print("[ERROR] Migration failed - some columns are still NOT NULL")
            if not sql_where_nullable_after:
                print("  - sql_where is still NOT NULL")
            if not logic_en_nullable_after:
                print("  - logic_en is still NOT NULL")
            return False
            
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = run_migration_009()
    sys.exit(0 if success else 1)

