"""Quick verification script to check table structure and data."""
from sqlalchemy import inspect
from app.api.dependencies import get_db_engine, get_session_factory
from app.models import DimDictionary, FactPnlEntries

engine = get_db_engine()
inspector = inspect(engine)
tables = inspector.get_table_names()

print("=" * 70)
print("Database Tables Verification")
print("=" * 70)

print(f"\nTotal tables in database: {len(tables)}")

# Check dim_dictionary
print("\n=== dim_dictionary table ===")
if 'dim_dictionary' in tables:
    cols = inspector.get_columns('dim_dictionary')
    print(f"[OK] Table exists with {len(cols)} columns:")
    for col in cols:
        print(f"  - {col['name']}: {col['type']}")
    
    # Check data
    SessionLocal = get_session_factory()
    session = SessionLocal()
    count = session.query(DimDictionary).count()
    categories = session.query(DimDictionary.category).distinct().all()
    print(f"\n[OK] Data populated:")
    print(f"  - Total entries: {count}")
    print(f"  - Categories: {[c[0] for c in categories]}")
    session.close()
else:
    print("[MISSING] Table does not exist")

# Check fact_pnl_entries
print("\n=== fact_pnl_entries table ===")
if 'fact_pnl_entries' in tables:
    cols = inspector.get_columns('fact_pnl_entries')
    print(f"[OK] Table exists with {len(cols)} columns:")
    for col in cols:
        print(f"  - {col['name']}: {col['type']}")
    
    # Check data
    SessionLocal = get_session_factory()
    session = SessionLocal()
    count = session.query(FactPnlEntries).count()
    print(f"\n[OK] Data status:")
    print(f"  - Total entries: {count}")
    session.close()
else:
    print("[MISSING] Table does not exist")

print("\n" + "=" * 70)

