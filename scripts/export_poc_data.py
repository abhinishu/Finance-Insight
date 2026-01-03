"""
Export POC Data Script
======================

Exports current database state to portable JSON files for migration to Office POC Environment.

Tables Exported:
- use_cases
- dim_hierarchy
- fact_pnl_use_case_3
- metadata_rules (with predicate_json JSONB column)

Output: JSON files saved to app/data_seed/ directory.
"""

import json
import logging
import sys
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session, sessionmaker
from app.database import create_db_engine, get_database_url
from app.models import (
    Base,
    UseCase,
    DimHierarchy,
    FactPnlUseCase3,
    MetadataRule
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for UUID, Decimal, datetime, and other types."""
    
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        # FIX: Add this check for Date and DateTime objects
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()  # Converts date to "YYYY-MM-DD" string
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


def row_to_dict(row):
    """
    Convert SQLAlchemy row to dictionary, handling all column types.
    
    Args:
        row: SQLAlchemy model instance
        
    Returns:
        dict: Dictionary representation of the row
    """
    result = {}
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        
        # Handle None values
        if value is None:
            result[column.name] = None
        # Handle JSONB columns (already dict/list)
        elif isinstance(value, (dict, list)):
            result[column.name] = value
        # Handle Enum types
        elif hasattr(value, 'value'):
            result[column.name] = value.value
        # Handle other types (UUID, Decimal, datetime handled by JSONEncoder)
        else:
            result[column.name] = value
    
    return result


def export_table(session: Session, model_class, table_name: str, output_dir: Path):
    """
    Export a table to JSON file.
    
    Args:
        session: SQLAlchemy session
        model_class: SQLAlchemy model class
        table_name: Name of the table (for filename)
        output_dir: Directory to save JSON file
        
    Returns:
        int: Number of rows exported
    """
    logger.info(f"Exporting {table_name}...")
    
    try:
        # Query all rows
        rows = session.query(model_class).all()
        logger.info(f"  Found {len(rows)} rows")
        
        # Convert to dictionaries
        data = [row_to_dict(row) for row in rows]
        
        # Write to JSON file
        output_file = output_dir / f"{table_name}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, cls=JSONEncoder, ensure_ascii=False)
        
        logger.info(f"  ✅ Exported to {output_file}")
        return len(rows)
        
    except Exception as e:
        logger.error(f"  ❌ Error exporting {table_name}: {e}", exc_info=True)
        raise


def main():
    """Main export function."""
    logger.info("=" * 60)
    logger.info("POC Data Export Script")
    logger.info("=" * 60)
    
    # Create output directory
    output_dir = project_root / "app" / "data_seed"
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")
    
    # Connect to database
    database_url = get_database_url()
    logger.info(f"Connecting to database: {database_url.split('@')[-1] if '@' in database_url else 'localhost'}")
    
    engine = create_db_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        total_rows = 0
        
        # Export tables in dependency order
        # 1. use_cases (no dependencies)
        total_rows += export_table(session, UseCase, "use_cases", output_dir)
        
        # 2. dim_hierarchy (no dependencies on exported tables)
        total_rows += export_table(session, DimHierarchy, "dim_hierarchy", output_dir)
        
        # 3. fact_pnl_use_case_3 (no dependencies on exported tables)
        total_rows += export_table(session, FactPnlUseCase3, "fact_pnl_use_case_3", output_dir)
        
        # 4. metadata_rules (depends on use_cases and dim_hierarchy, but we export after)
        total_rows += export_table(session, MetadataRule, "metadata_rules", output_dir)
        
        logger.info("=" * 60)
        logger.info(f"✅ Export Complete! Total rows exported: {total_rows}")
        logger.info(f"📁 Files saved to: {output_dir}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Export failed: {e}", exc_info=True)
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    main()

