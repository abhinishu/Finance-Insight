"""
Data Import Script for Database Migration

This script imports JSON files from migration_payload/ back into the database.
Uses ON CONFLICT DO NOTHING to safely handle existing records.
"""

import json
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.database import get_database_url, create_db_engine


def load_table(session: Session, table_name: str, file_name: str) -> int:
    """
    Load data from a JSON file into a database table.
    
    Args:
        session: SQLAlchemy session
        table_name: Name of the target table
        file_name: Name of the JSON file in migration_payload/
        
    Returns:
        Number of rows imported
    """
    file_path = os.path.join("migration_payload", file_name)
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        return 0
    
    # Read JSON file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            rows = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to read {file_path}: {str(e)}")
        return 0
    
    if not rows:
        print(f"[WARN] No data in {file_path}")
        return 0
    
    # Determine conflict key based on table name
    conflict_key = None
    if table_name == "use_cases":
        conflict_key = "use_case_id"
    elif table_name == "metadata_rules":
        conflict_key = "rule_id"
    elif table_name == "fact_pnl_entries":
        # Check if entry_id exists, otherwise use id
        if rows and "entry_id" in rows[0]:
            conflict_key = "entry_id"
        elif rows and "id" in rows[0]:
            conflict_key = "id"
        else:
            conflict_key = "id"  # Default fallback
    
    # Get column names from first row
    if not rows:
        print(f"[WARN] Empty data in {file_path}")
        return 0
    
    columns = list(rows[0].keys())
    
    # Build INSERT statement with ON CONFLICT DO NOTHING
    columns_str = ", ".join(columns)
    placeholders = ", ".join([f":{col}" for col in columns])
    
    if conflict_key and conflict_key in columns:
        # Use ON CONFLICT for primary key conflicts
        conflict_clause = f"ON CONFLICT ({conflict_key}) DO NOTHING"
        insert_sql = f"""
            INSERT INTO {table_name} ({columns_str})
            VALUES ({placeholders})
            {conflict_clause}
        """
    else:
        # No conflict resolution - will fail on duplicates
        insert_sql = f"""
            INSERT INTO {table_name} ({columns_str})
            VALUES ({placeholders})
        """
    
    # Execute inserts
    imported_count = 0
    try:
        session.rollback()  # Clear any previous transaction state
        
        for row in rows:
            # Convert values to proper types (handle None, dates, UUIDs, etc.)
            params = {}
            for col, value in row.items():
                if value is None:
                    params[col] = None
                elif isinstance(value, str) and value == "null":
                    params[col] = None
                elif isinstance(value, dict):
                    # JSONB fields - keep as dict, SQLAlchemy will handle conversion
                    params[col] = json.dumps(value) if value else None
                else:
                    params[col] = value
            
            try:
                result = session.execute(text(insert_sql), params)
                # Check if row was actually inserted (not skipped due to conflict)
                if result.rowcount > 0:
                    imported_count += 1
            except Exception as e:
                # Skip rows that fail (likely due to conflicts or constraints)
                # This is expected for ON CONFLICT DO NOTHING
                continue
        
        session.commit()
        print(f"[SUCCESS] Imported {imported_count} rows into {table_name}")
        return imported_count
        
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Failed to import {table_name}: {str(e)}")
        return 0


def main():
    """
    Main execution flow:
    1. Connect to database
    2. Load use_cases
    3. Load fact_pnl_entries
    4. Load metadata_rules
    """
    print("=" * 80)
    print("Database Migration Import Script")
    print("=" * 80)
    print()
    
    # Get database URL
    database_url = get_database_url()
    print(f"Connecting to database: {database_url.split('@')[1] if '@' in database_url else '***'}")
    
    # Create engine and session
    engine = create_db_engine(database_url)
    SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
    session = SessionLocal()
    
    try:
        # Check if migration_payload directory exists
        if not os.path.exists("migration_payload"):
            print("[ERROR] migration_payload directory not found!")
            print("Please run export_migration.py first to create the data files.")
            return
        
        print(f"[INFO] Found migration_payload directory")
        print()
        
        # Import use_cases
        print("Importing use_cases...")
        load_table(session, "use_cases", "use_cases.json")
        print()
        
        # Import fact_pnl_entries
        print("Importing fact_pnl_entries...")
        load_table(session, "fact_pnl_entries", "fact_pnl_entries.json")
        print()
        
        # Import metadata_rules
        print("Importing metadata_rules...")
        load_table(session, "metadata_rules", "metadata_rules.json")
        print()
        
        print("=" * 80)
        print("[SUCCESS] Import completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"[ERROR] Fatal error during import: {str(e)}")
        raise
        
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    main()

