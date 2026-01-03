"""
Minimal migration - only adds what's missing (fast).
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine

print("Applying minimal Trading Track migration...")
print("=" * 60)

with engine.connect() as conn:
    trans = conn.begin()
    
    try:
        # 1. Add use_case_type (missing)
        print("\n[1/3] Adding use_case_type to use_cases...")
        conn.execute(text("ALTER TABLE use_cases ADD COLUMN IF NOT EXISTS use_case_type VARCHAR(50) DEFAULT 'STANDARD'"))
        print("  [OK] Done")
        
        # 2. Add rule columns (missing)
        print("\n[2/3] Adding rule columns to metadata_rules...")
        conn.execute(text("ALTER TABLE metadata_rules ADD COLUMN IF NOT EXISTS rule_type VARCHAR(20) DEFAULT 'DIRECT'"))
        conn.execute(text("ALTER TABLE metadata_rules ADD COLUMN IF NOT EXISTS target_measure VARCHAR(50)"))
        print("  [OK] Done")
        
        # 3. Create missing index
        print("\n[3/3] Creating index idx_trade_proc2...")
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_trade_proc2 ON fact_trading_pnl(process_2)"))
            print("  [OK] Done")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("  [SKIP] Index already exists")
            else:
                raise
        
        trans.commit()
        
        print("\n" + "=" * 60)
        print("[OK] Migration completed!")
        print("=" * 60)
        
    except Exception as e:
        trans.rollback()
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)



