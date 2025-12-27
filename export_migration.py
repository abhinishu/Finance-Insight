"""
Data Export Script for Database Migration Snapshot

This script exports all critical tables from the Finance-Insight database
to JSON files for backup and migration purposes.
"""

import json
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.database import get_database_url, create_db_engine
from app.models import Base


def serialize_date(obj):
    """
    Helper function to serialize datetime objects to ISO format strings.
    
    Args:
        obj: Object that might be a datetime
        
    Returns:
        ISO format string if obj is datetime, otherwise returns obj
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def export_table(session: Session, table_name: str, output_dir: str) -> int:
    """
    Export all rows from a table to a JSON file.
    
    Args:
        session: SQLAlchemy session
        table_name: Name of the table to export
        output_dir: Directory to save the JSON file
        
    Returns:
        Number of rows exported
    """
    try:
        # Rollback any previous failed transaction
        session.rollback()
        
        # Use raw SQL to fetch all rows
        query = text(f"SELECT * FROM {table_name}")
        result = session.execute(query)
        
        # Get column names
        columns = result.keys()
        
        # Convert rows to dictionaries
        rows = []
        for row in result:
            row_dict = {}
            for col in columns:
                value = getattr(row, col)
                # Serialize dates
                if isinstance(value, datetime):
                    value = serialize_date(value)
                row_dict[col] = value
            rows.append(row_dict)
        
        # Save to JSON file
        output_file = os.path.join(output_dir, f"{table_name}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(rows, f, indent=2, default=str, ensure_ascii=False)
        
        row_count = len(rows)
        print(f"[SUCCESS] Saved {row_count} rows to {output_file}")
        return row_count
        
    except Exception as e:
        # Rollback on error to clear transaction state
        session.rollback()
        print(f"[ERROR] Error exporting {table_name}: {str(e)}")
        return 0


def main():
    """
    Main execution flow:
    1. Connect to database
    2. Create migration_payload directory
    3. Export use_cases
    4. Export data_records
    5. Export metadata_rules (with fallback to business_rules)
    """
    print("=" * 80)
    print("Database Migration Export Script")
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
        # Create migration_payload directory
        output_dir = "migration_payload"
        os.makedirs(output_dir, exist_ok=True)
        print(f"[INFO] Created output directory: {output_dir}")
        print()
        
        # Export use_cases
        print("Exporting use_cases...")
        export_table(session, "use_cases", output_dir)
        print()
        
        # Export fact_pnl_entries (instead of data_records which doesn't exist)
        print("Exporting fact_pnl_entries...")
        export_table(session, "fact_pnl_entries", output_dir)
        print()
        
        # Export metadata_rules (with fallback to business_rules)
        print("Exporting metadata_rules...")
        metadata_count = export_table(session, "metadata_rules", output_dir)
        if metadata_count == 0:
            print("Trying fallback: business_rules...")
            export_table(session, "business_rules", output_dir)
        print()
        
        print("=" * 80)
        print("[SUCCESS] Export completed successfully!")
        print(f"[INFO] Files saved in: {os.path.abspath(output_dir)}")
        print("=" * 80)
        
    except Exception as e:
        print(f"[ERROR] Fatal error during export: {str(e)}")
        raise
        
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    main()

