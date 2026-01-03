"""Run migration with IF NOT EXISTS support - handles each statement separately."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine

print("Running Trading Track migration...")
print("=" * 60)

# SQL statements to execute
statements = [
    "-- 1. Fix Fact Table Columns",
    "ALTER TABLE fact_trading_pnl ADD COLUMN IF NOT EXISTS process_1 VARCHAR(100)",
    "ALTER TABLE fact_trading_pnl ADD COLUMN IF NOT EXISTS process_2 VARCHAR(100)",
    "ALTER TABLE fact_trading_pnl ADD COLUMN IF NOT EXISTS pnl_trading_daily NUMERIC(18, 2) DEFAULT 0",
    "ALTER TABLE fact_trading_pnl ADD COLUMN IF NOT EXISTS pnl_trading_ytd NUMERIC(18, 2) DEFAULT 0",
    "ALTER TABLE fact_trading_pnl ADD COLUMN IF NOT EXISTS pnl_commission_daily NUMERIC(18, 2) DEFAULT 0",
    "ALTER TABLE fact_trading_pnl ADD COLUMN IF NOT EXISTS pnl_commission_ytd NUMERIC(18, 2) DEFAULT 0",
    "ALTER TABLE fact_trading_pnl ADD COLUMN IF NOT EXISTS pnl_total_daily NUMERIC(18, 2) DEFAULT 0",
    "ALTER TABLE fact_trading_pnl ADD COLUMN IF NOT EXISTS pnl_total_ytd NUMERIC(18, 2) DEFAULT 0",
    "ALTER TABLE fact_trading_pnl ADD COLUMN IF NOT EXISTS pnl_qtd NUMERIC(18, 2) DEFAULT 0",
    "",
    "-- 2. Fix Use Cases Table",
    "ALTER TABLE use_cases ADD COLUMN IF NOT EXISTS use_case_type VARCHAR(50) DEFAULT 'STANDARD'",
    "",
    "-- 3. Fix Metadata Rules Table",
    "ALTER TABLE metadata_rules ADD COLUMN IF NOT EXISTS rule_type VARCHAR(20) DEFAULT 'DIRECT'",
    "ALTER TABLE metadata_rules ADD COLUMN IF NOT EXISTS target_measure VARCHAR(50)",
]

with engine.connect() as conn:
    trans = conn.begin()
    
    try:
        executed = 0
        skipped = 0
        
        for stmt in statements:
            # Skip comments and empty lines
            stmt = stmt.strip()
            if not stmt or stmt.startswith('--'):
                continue
            
            try:
                print(f"Executing: {stmt[:60]}...")
                conn.execute(text(stmt))
                executed += 1
                print(f"  [OK] Success")
            except Exception as e:
                error_msg = str(e).lower()
                # IF NOT EXISTS might not be supported, or column already exists
                if "already exists" in error_msg or "duplicate" in error_msg:
                    print(f"  [SKIP] Already exists")
                    skipped += 1
                elif "syntax error" in error_msg or "unexpected" in error_msg:
                    # IF NOT EXISTS not supported - try without it
                    print(f"  [WARN] IF NOT EXISTS not supported, trying without...")
                    # Remove IF NOT EXISTS and try again
                    stmt_alt = stmt.replace(" IF NOT EXISTS", "")
                    try:
                        conn.execute(text(stmt_alt))
                        executed += 1
                        print(f"  [OK] Success (without IF NOT EXISTS)")
                    except Exception as e2:
                        error_msg2 = str(e2).lower()
                        if "already exists" in error_msg2:
                            print(f"  [SKIP] Already exists")
                            skipped += 1
                        else:
                            print(f"  [ERROR] Failed: {e2}")
                            raise
                else:
                    print(f"  [ERROR] Failed: {e}")
                    raise
        
        trans.commit()
        
        print("\n" + "=" * 60)
        print(f"[OK] Migration completed!")
        print(f"  Executed: {executed} statements")
        print(f"  Skipped: {skipped} (already exist)")
        print("=" * 60)
        
    except Exception as e:
        trans.rollback()
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)



