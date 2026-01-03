"""
Robust Schema Fix Script - Fast version using direct SQL queries.
Fixes Trading Track Foundation schema by adding missing columns safely.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine


# Define required schema changes
REQUIRED_CHANGES = {
    'fact_trading_pnl': [
        ('process_1', 'VARCHAR(100)', None),
        ('process_2', 'VARCHAR(100)', None),
        ('pnl_trading_daily', 'NUMERIC(18, 2)', 'DEFAULT 0'),
        ('pnl_trading_ytd', 'NUMERIC(18, 2)', 'DEFAULT 0'),
        ('pnl_commission_daily', 'NUMERIC(18, 2)', 'DEFAULT 0'),
        ('pnl_commission_ytd', 'NUMERIC(18, 2)', 'DEFAULT 0'),
        ('pnl_total_daily', 'NUMERIC(18, 2)', 'DEFAULT 0'),
        ('pnl_total_ytd', 'NUMERIC(18, 2)', 'DEFAULT 0'),
        ('pnl_qtd', 'NUMERIC(18, 2)', 'DEFAULT 0'),
    ],
    'use_cases': [
        ('use_case_type', 'VARCHAR(50)', "DEFAULT 'STANDARD'"),
    ],
    'metadata_rules': [
        ('rule_type', 'VARCHAR(20)', "DEFAULT 'DIRECT'"),
        ('target_measure', 'VARCHAR(50)', None),
    ],
}


def get_existing_columns_fast(conn, table_name: str) -> set:
    """
    Get set of existing column names using direct SQL query (faster than inspect).
    
    Args:
        conn: Database connection
        table_name: Name of the table to inspect
    
    Returns:
        Set of column names
    """
    try:
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = :table_name
        """), {"table_name": table_name})
        return {row[0] for row in result}
    except Exception as e:
        print(f"[WARN] Could not inspect table '{table_name}': {e}")
        return set()


def add_column(conn, table_name: str, column_name: str, column_type: str, default_clause: str = None):
    """
    Add a column to a table.
    
    Args:
        conn: Database connection
        table_name: Name of the table
        column_name: Name of the column to add
        column_type: SQL type definition (e.g., 'VARCHAR(100)')
        default_clause: Optional default clause (e.g., "DEFAULT 'STANDARD'")
    """
    sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
    if default_clause:
        sql += f" {default_clause}"
    
    conn.execute(text(sql))


def fix_schema():
    """
    Main function to fix the schema by adding missing columns.
    """
    print("=" * 60)
    print("Schema Fix Script - Trading Track Foundation (Fast Version)")
    print("=" * 60)
    print()
    
    # Track statistics
    added_count = 0
    skipped_count = 0
    error_count = 0
    
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            # Process each table
            for table_name, required_columns in REQUIRED_CHANGES.items():
                print(f"\n[INFO] Processing table: {table_name}")
                print("-" * 60)
                
                # Get existing columns using fast SQL query
                existing_columns = get_existing_columns_fast(conn, table_name)
                
                if not existing_columns:
                    print(f"[WARN] Table '{table_name}' not found or cannot be inspected. Skipping...")
                    error_count += 1
                    continue
                
                # Process each required column
                for column_name, column_type, default_clause in required_columns:
                    if column_name in existing_columns:
                        print(f"[SKIP] Column '{column_name}' already exists in '{table_name}'")
                        skipped_count += 1
                    else:
                        try:
                            print(f"[ADD] Adding column '{column_name}' to '{table_name}'...")
                            add_column(conn, table_name, column_name, column_type, default_clause)
                            print(f"[OK] Added column '{column_name}' to '{table_name}'")
                            added_count += 1
                            
                            # Refresh column list for this table
                            existing_columns.add(column_name)
                        except Exception as e:
                            error_msg = str(e).lower()
                            if "already exists" in error_msg or "duplicate" in error_msg:
                                print(f"[SKIP] Column '{column_name}' already exists (detected during add)")
                                skipped_count += 1
                            else:
                                print(f"[ERROR] Error adding column '{column_name}': {e}")
                                error_count += 1
                                # Continue with other columns even if one fails
                                continue
            
            # Commit transaction
            print("\n" + "=" * 60)
            print("Committing changes...")
            trans.commit()
            print("[OK] Transaction committed successfully")
            
        except Exception as e:
            print(f"\n[ERROR] Error during migration: {e}")
            print("Rolling back transaction...")
            trans.rollback()
            print("[WARN] Transaction rolled back")
            import traceback
            traceback.print_exc()
            return 1
    
    # Print summary
    print("\n" + "=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"[OK] Columns added: {added_count}")
    print(f"[SKIP] Columns skipped (already exist): {skipped_count}")
    print(f"[ERROR] Errors: {error_count}")
    print("=" * 60)
    
    if error_count > 0:
        print("\n[WARN] Some errors occurred. Please review the output above.")
        return 1
    else:
        print("\n[SUCCESS] Schema fix completed successfully!")
        return 0


if __name__ == "__main__":
    sys.exit(fix_schema())



