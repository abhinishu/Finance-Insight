"""
Quick check: What columns/indexes already exist?
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine

print("Checking current migration status...")
print("=" * 60)

with engine.connect() as conn:
    # Check fact_trading_pnl columns
    print("\nfact_trading_pnl columns:")
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'fact_trading_pnl'
        ORDER BY column_name
    """))
    cols = [row[0] for row in result]
    print(f"  Found {len(cols)} columns")
    for col in cols:
        print(f"    - {col}")
    
    # Check use_cases columns
    print("\nuse_cases columns:")
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'use_cases'
        ORDER BY column_name
    """))
    cols = [row[0] for row in result]
    print(f"  Found {len(cols)} columns")
    for col in cols:
        print(f"    - {col}")
    
    # Check metadata_rules columns
    print("\nmetadata_rules columns:")
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'metadata_rules'
        ORDER BY column_name
    """))
    cols = [row[0] for row in result]
    print(f"  Found {len(cols)} columns")
    for col in cols:
        print(f"    - {col}")
    
    # Check indexes
    print("\nIndexes on fact_trading_pnl:")
    result = conn.execute(text("""
        SELECT indexname FROM pg_indexes 
        WHERE schemaname = 'public' AND tablename = 'fact_trading_pnl'
    """))
    indexes = [row[0] for row in result]
    for idx in indexes:
        print(f"    - {idx}")

print("\n" + "=" * 60)
print("Check complete!")



