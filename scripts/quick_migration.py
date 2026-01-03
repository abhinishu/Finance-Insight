"""Quick migration - executes each statement individually with error handling."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine

print("Running quick migration...")
print("=" * 60)

with engine.connect() as conn:
    trans = conn.begin()
    
    statements = [
        ("Adding use_case_type", "ALTER TABLE use_cases ADD COLUMN use_case_type VARCHAR(50) DEFAULT 'STANDARD'"),
        ("Adding rule_type", "ALTER TABLE metadata_rules ADD COLUMN rule_type VARCHAR(20) DEFAULT 'DIRECT'"),
        ("Adding target_measure", "ALTER TABLE metadata_rules ADD COLUMN target_measure VARCHAR(50)"),
        ("Creating index", "CREATE INDEX IF NOT EXISTS idx_trade_proc2 ON fact_trading_pnl(process_2)"),
    ]
    
    for desc, sql in statements:
        try:
            print(f"\n{desc}...")
            conn.execute(text(sql))
            print(f"  [OK] {desc} completed")
        except Exception as e:
            error_msg = str(e).lower()
            if "already exists" in error_msg or "duplicate" in error_msg:
                print(f"  [SKIP] {desc} - already exists")
            else:
                print(f"  [ERROR] {desc} failed: {e}")
                raise
    
    trans.commit()
    print("\n" + "=" * 60)
    print("[OK] Migration completed!")
    print("=" * 60)

