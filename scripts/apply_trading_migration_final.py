"""
Final migration - checks first, then adds (works on all PostgreSQL versions).
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine

def column_exists(conn, table_name: str, column_name: str) -> bool:
    """Quick check using SQL."""
    result = conn.execute(text("""
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = :table_name 
        AND column_name = :column_name
    """), {"table_name": table_name, "column_name": column_name})
    return result.fetchone() is not None

def index_exists(conn, index_name: str) -> bool:
    """Quick check using SQL."""
    result = conn.execute(text("""
        SELECT 1 FROM pg_indexes 
        WHERE schemaname = 'public' AND indexname = :index_name
    """), {"index_name": index_name})
    return result.fetchone() is not None

print("Applying Trading Track migration (final)...")
print("=" * 60)

with engine.connect() as conn:
    trans = conn.begin()
    
    try:
        # 1. Add use_case_type
        print("\n[1/3] Checking use_case_type...")
        if not column_exists(conn, 'use_cases', 'use_case_type'):
            print("  -> Adding use_case_type...")
            conn.execute(text("ALTER TABLE use_cases ADD COLUMN use_case_type VARCHAR(50) DEFAULT 'STANDARD'"))
            print("  [OK] Added")
        else:
            print("  [SKIP] Already exists")
        
        # 2. Add rule columns
        print("\n[2/3] Checking rule columns...")
        if not column_exists(conn, 'metadata_rules', 'rule_type'):
            print("  -> Adding rule_type...")
            conn.execute(text("ALTER TABLE metadata_rules ADD COLUMN rule_type VARCHAR(20) DEFAULT 'DIRECT'"))
            print("  [OK] Added")
        else:
            print("  [SKIP] rule_type already exists")
        
        if not column_exists(conn, 'metadata_rules', 'target_measure'):
            print("  -> Adding target_measure...")
            conn.execute(text("ALTER TABLE metadata_rules ADD COLUMN target_measure VARCHAR(50)"))
            print("  [OK] Added")
        else:
            print("  [SKIP] target_measure already exists")
        
        # 3. Create index
        print("\n[3/3] Checking index...")
        if not index_exists(conn, 'idx_trade_proc2'):
            print("  -> Creating idx_trade_proc2...")
            conn.execute(text("CREATE INDEX idx_trade_proc2 ON fact_trading_pnl(process_2)"))
            print("  [OK] Created")
        else:
            print("  [SKIP] Already exists")
        
        print("\n  -> Committing...")
        trans.commit()
        
        print("\n" + "=" * 60)
        print("[OK] Migration completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        trans.rollback()
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)



