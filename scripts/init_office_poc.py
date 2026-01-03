import os
import json
import argparse
from datetime import datetime, date
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Add project root to path
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# --- IMPORT YOUR MODELS HERE ---
from app.database import get_database_url
from app.models import Base
from app.models import (
    UseCase,
    DimHierarchy,
    FactPnlUseCase3,
    MetadataRule
)

# Import ALL models to ensure they're registered with Base.metadata
from app.models import (
    UseCaseRun,
    HierarchyBridge,
    FactPnlGold,
    FactCalculatedResult,
    ReportRegistration,
    DimDictionary,
    FactPnlEntries,
    CalculationRun,
    HistorySnapshot
)

# Configuration
DATA_SEED_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "data_seed")

def get_engine():
    """Create database engine using project config"""
    url = get_database_url()
    return create_engine(url, pool_pre_ping=True)

def parse_date(value):
    """Helper to parse date strings back to Python date objects"""
    if isinstance(value, str):
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            pass
    return value

# FIX: Added sort_key parameter to control insertion order
def load_table(session, model_class, filename, sort_key=None):
    """Generic function to load data from JSON into a table"""
    filepath = os.path.join(DATA_SEED_DIR, filename)
    
    if not os.path.exists(filepath):
        print(f"⚠️  Skipping {filename} (File not found)")
        return

    print(f"📦 Loading {model_class.__tablename__} from {filename}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # CRITICAL FIX: Sort data if a sort_key is provided
    # This ensures Parents (Depth 0) are inserted before Children (Depth 1)
    if sort_key:
        print(f"   Sorting by '{sort_key}' to ensure Parent-Child integrity...")
        data.sort(key=lambda x: x.get(sort_key, 0))

    count = 0
    for row_data in data:
        # DATA FIX: Check for date columns and convert strings to dates
        if 'effective_date' in row_data and row_data['effective_date']:
            row_data['effective_date'] = parse_date(row_data['effective_date'])
        
        session.merge(model_class(**row_data))
        count += 1

    try:
        session.commit()
        print(f"   ✅ Loaded {count} rows.")
    except Exception as e:
        session.rollback()
        print(f"   ❌ Error loading {filename}: {str(e)}")
        raise e  # Stop execution on error

def main():
    parser = argparse.ArgumentParser(description="Initialize Office POC Database")
    parser.add_argument("--reset", action="store_true", help="WIPE database and recreate schema")
    args = parser.parse_args()

    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    print("========================================")
    print("   OFFICE POC INITIALIZATION SCRIPT")
    print("========================================")

    # 1. Schema Reset
    if args.reset:
        print("\n⚠  RESET DETECTED: Dropping all tables...")
        # REFLECTION FIX: Drop ghost tables too
        meta = MetaData()
        meta.reflect(bind=engine)
        meta.drop_all(bind=engine)
        print("   ✅ All tables dropped.")
        
        print("🔨 Recreating Schema from Models...")
        Base.metadata.create_all(bind=engine)
        print("   ✅ Schema created.")
    else:
        print("\nℹ  Running in Append/Update mode (No drop).")
        Base.metadata.create_all(bind=engine)

    # 2. Load Data (Order Matters!)
    print("\n🚀 Starting Data Import...")
    
    load_table(session, UseCase, "use_cases.json")
    
    # CRITICAL FIX: Sort hierarchy by depth so Parents exist before Children
    load_table(session, DimHierarchy, "dim_hierarchy.json", sort_key="depth")
    
    load_table(session, MetadataRule, "metadata_rules.json")
    load_table(session, FactPnlUseCase3, "fact_pnl_use_case_3.json")

    print("\n========================================")
    print("✅ MIGRATION COMPLETE.")
    print("========================================")

    session.close()
    engine.dispose()

if __name__ == "__main__":
    main()
