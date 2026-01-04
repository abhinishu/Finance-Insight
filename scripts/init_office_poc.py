import os
import json
import argparse
import random
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4
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
            # Try YYYY-MM-DD format first
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            try:
                # Try datetime format (YYYY-MM-DDTHH:MM:SS) - return as datetime for TIMESTAMP columns
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
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
        date_columns = ['effective_date', 'trade_date', 'pnl_date', 'created_at', 'last_modified_at']
        for col in date_columns:
            if col in row_data and row_data[col] and isinstance(row_data[col], str):
                row_data[col] = parse_date(row_data[col])
        
        session.merge(model_class(**row_data))
        count += 1

    try:
        session.commit()
        print(f"   ✅ Loaded {count} rows.")
    except Exception as e:
        session.rollback()
        print(f"   ❌ Error loading {filename}: {str(e)}")
        raise e  # Stop execution on error

def seed_use_case_1(session):
    """
    Seed Use Case 1 (America Trading P&L) with fact_pnl_gold data.
    Generates ~50 rows if the table is empty.
    """
    print("\n🌱 Checking Use Case 1 data (fact_pnl_gold)...")
    
    # Check if table is empty
    count = session.query(FactPnlGold).count()
    
    if count > 0:
        print(f"   ✅ fact_pnl_gold already has {count} rows. Skipping seed.")
        return
    
    print("   ⚠️  fact_pnl_gold is empty. Generating seed data...")
    
    # Find Use Case 1
    use_case_1 = session.query(UseCase).filter(
        UseCase.name == "America Trading P&L"
    ).first()
    
    if not use_case_1:
        print("   ⚠️  Use Case 1 not found. Cannot seed data.")
        return
    
    # Get leaf nodes from hierarchy for Use Case 1
    leaf_nodes = session.query(DimHierarchy).filter(
        DimHierarchy.atlas_source == use_case_1.atlas_structure_id,
        DimHierarchy.is_leaf == True
    ).all()
    
    if not leaf_nodes:
        print("   ⚠️  No leaf nodes found in hierarchy. Using generic CC_001 to CC_050.")
        cc_ids = [f"CC_{i:03d}" for i in range(1, 51)]
    else:
        cc_ids = [node.node_id for node in leaf_nodes]
        print(f"   Found {len(cc_ids)} leaf nodes in hierarchy.")
    
    # Generate ~50 rows
    num_rows = 50
    accounts = [f"ACC_{i:03d}" for i in range(1, 11)]
    books = [f"BOOK_{i:02d}" for i in range(1, 11)]
    strategies = [f"STRAT_{i:02d}" for i in range(1, 6)]
    
    # Date range: Last 30 days
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    rows_generated = 0
    for i in range(num_rows):
        # Random trade date in last 30 days
        random_days = random.randint(0, 30)
        trade_date = end_date - timedelta(days=random_days)
        
        # Generate P&L values (random between -10k and +50k as requested)
        daily_pnl = Decimal(str(random.uniform(-10000, 50000))).quantize(Decimal('0.01'))
        mtd_pnl = daily_pnl * Decimal(str(random.uniform(5, 20)))  # MTD is multiple of daily
        ytd_pnl = daily_pnl * Decimal(str(random.uniform(50, 200)))  # YTD is multiple of daily
        pytd_pnl = ytd_pnl * Decimal(str(random.uniform(0.8, 1.2)))  # PYTD similar to YTD
        
        fact_row = FactPnlGold(
            fact_id=uuid4(),
            account_id=random.choice(accounts),
            cc_id=random.choice(cc_ids),  # Match to hierarchy leaf nodes
            book_id=random.choice(books),
            strategy_id=random.choice(strategies),
            trade_date=trade_date,
            daily_pnl=daily_pnl,
            mtd_pnl=mtd_pnl,
            ytd_pnl=ytd_pnl,
            pytd_pnl=pytd_pnl
        )
        
        session.add(fact_row)
        rows_generated += 1
    
    try:
        session.commit()
        print(f"   ✅ Generated and inserted {rows_generated} rows into fact_pnl_gold.")
    except Exception as e:
        session.rollback()
        print(f"   ❌ Error seeding Use Case 1: {str(e)}")
        raise e

def seed_use_case_2(session):
    """
    Seed Use Case 2 (Project Sterling) with fact_pnl_entries data.
    Generates ~20 rows if the table is empty for this use case.
    """
    print("\n🌱 Checking Use Case 2 data (fact_pnl_entries)...")
    
    # Find Use Case 2
    use_case_2 = session.query(UseCase).filter(
        UseCase.name == "Project Sterling - Multi-Dimensional Facts"
    ).first()
    
    if not use_case_2:
        print("   ⚠️  Use Case 2 not found. Cannot seed data.")
        return
    
    # Check if table has data for Use Case 2
    count = session.query(FactPnlEntries).filter(
        FactPnlEntries.use_case_id == use_case_2.use_case_id
    ).count()
    
    if count > 0:
        print(f"   ✅ fact_pnl_entries already has {count} rows for Use Case 2. Skipping seed.")
        return
    
    print("   ⚠️  fact_pnl_entries is empty for Use Case 2. Generating seed data...")
    
    # Get leaf nodes from hierarchy for Use Case 2
    leaf_nodes = session.query(DimHierarchy).filter(
        DimHierarchy.atlas_source == use_case_2.atlas_structure_id,
        DimHierarchy.is_leaf == True
    ).all()
    
    if not leaf_nodes:
        print("   ⚠️  No leaf nodes found in hierarchy. Using generic TRADE_001 to TRADE_020.")
        category_codes = [f"TRADE_{i:03d}" for i in range(1, 21)]
    else:
        category_codes = [node.node_id for node in leaf_nodes]
        print(f"   Found {len(category_codes)} leaf nodes in hierarchy.")
    
    # Generate ~20 rows
    num_rows = 20
    
    # Date range: Last 30 days
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    rows_generated = 0
    for i in range(num_rows):
        # Random date in last 30 days
        random_days = random.randint(0, 30)
        pnl_date = end_date - timedelta(days=random_days)
        
        # Generate amounts (random between -10k and +50k as requested)
        daily_amount = Decimal(str(random.uniform(-10000, 50000))).quantize(Decimal('0.01'))
        wtd_amount = daily_amount * Decimal(str(random.uniform(3, 10)))  # WTD is multiple of daily
        ytd_amount = daily_amount * Decimal(str(random.uniform(50, 200)))  # YTD is multiple of daily
        amount = daily_amount  # Legacy column
        
        fact_row = FactPnlEntries(
            id=uuid4(),
            use_case_id=use_case_2.use_case_id,
            pnl_date=pnl_date,
            category_code=random.choice(category_codes),  # Match to hierarchy leaf nodes
            amount=amount,
            daily_amount=daily_amount,
            wtd_amount=wtd_amount,
            ytd_amount=ytd_amount,
            scenario='ACTUAL'  # Use ACTUAL scenario
        )
        
        session.add(fact_row)
        rows_generated += 1
    
    try:
        session.commit()
        print(f"   ✅ Generated and inserted {rows_generated} rows into fact_pnl_entries for Use Case 2.")
    except Exception as e:
        session.rollback()
        print(f"   ❌ Error seeding Use Case 2: {str(e)}")
        raise e

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

    # 3. Auto-Seed Missing Data (Use Cases 1 & 2)
    print("\n🌱 Auto-Seeding Missing Data...")
    seed_use_case_1(session)
    seed_use_case_2(session)

    print("\n========================================")
    print("✅ MIGRATION COMPLETE.")
    print("========================================")

    session.close()
    engine.dispose()

if __name__ == "__main__":
    main()
