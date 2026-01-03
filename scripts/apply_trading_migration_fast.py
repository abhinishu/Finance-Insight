"""
Apply Trading Track Foundation migration - FAST VERSION using direct SQL queries.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine


def column_exists_fast(conn, table_name: str, column_name: str) -> bool:
    """Check if a column exists using direct SQL query (faster than inspect)."""
    result = conn.execute(text("""
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = :table_name 
        AND column_name = :column_name
    """), {"table_name": table_name, "column_name": column_name})
    return result.fetchone() is not None


def index_exists_fast(conn, index_name: str) -> bool:
    """Check if an index exists using direct SQL query."""
    result = conn.execute(text("""
        SELECT 1 FROM pg_indexes 
        WHERE schemaname = 'public' 
        AND indexname = :index_name
    """), {"index_name": index_name})
    return result.fetchone() is not None


def apply_migration():
    """Apply the Trading Track Foundation migration - FAST VERSION."""
    print("Applying Trading Track Foundation Migration (Fast Version)")
    print("=" * 60)
    
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                # 1. Add missing dimension columns to fact_trading_pnl
                print("\n[1/5] Checking dimension columns...")
                if not column_exists_fast(conn, 'fact_trading_pnl', 'process_1'):
                    print("  -> Adding process_1...")
                    conn.execute(text("ALTER TABLE fact_trading_pnl ADD COLUMN process_1 VARCHAR(100)"))
                    print("  [OK] Added process_1")
                else:
                    print("  [SKIP] process_1 already exists")
                
                if not column_exists_fast(conn, 'fact_trading_pnl', 'process_2'):
                    print("  -> Adding process_2...")
                    conn.execute(text("ALTER TABLE fact_trading_pnl ADD COLUMN process_2 VARCHAR(100)"))
                    print("  [OK] Added process_2")
                else:
                    print("  [SKIP] process_2 already exists")
                
                # 2. Add new measure columns
                print("\n[2/5] Checking measure columns...")
                new_measures = [
                    ('pnl_trading_daily', 'NUMERIC(18, 2) DEFAULT 0'),
                    ('pnl_trading_ytd', 'NUMERIC(18, 2) DEFAULT 0'),
                    ('pnl_commission_daily', 'NUMERIC(18, 2) DEFAULT 0'),
                    ('pnl_commission_ytd', 'NUMERIC(18, 2) DEFAULT 0'),
                    ('pnl_total_daily', 'NUMERIC(18, 2) DEFAULT 0'),
                    ('pnl_total_ytd', 'NUMERIC(18, 2) DEFAULT 0')
                ]
                
                for measure, col_type in new_measures:
                    if not column_exists_fast(conn, 'fact_trading_pnl', measure):
                        print(f"  -> Adding {measure}...")
                        conn.execute(text(f"ALTER TABLE fact_trading_pnl ADD COLUMN {measure} {col_type}"))
                        print(f"  [OK] Added {measure}")
                    else:
                        print(f"  [SKIP] {measure} already exists")
                
                # 3. Create indexes
                print("\n[3/5] Checking indexes...")
                if not index_exists_fast(conn, 'idx_trade_proc2'):
                    print("  -> Creating idx_trade_proc2...")
                    conn.execute(text("CREATE INDEX idx_trade_proc2 ON fact_trading_pnl(process_2)"))
                    print("  [OK] Created idx_trade_proc2")
                else:
                    print("  [SKIP] idx_trade_proc2 already exists")
                
                # 4. Add use_case_type to use_cases
                print("\n[4/5] Checking use_cases table...")
                if not column_exists_fast(conn, 'use_cases', 'use_case_type'):
                    print("  -> Adding use_case_type...")
                    conn.execute(text("ALTER TABLE use_cases ADD COLUMN use_case_type VARCHAR(50) DEFAULT 'STANDARD'"))
                    print("  [OK] Added use_case_type")
                else:
                    print("  [SKIP] use_case_type already exists")
                
                # 5. Add rule_type and target_measure to metadata_rules
                print("\n[5/5] Checking metadata_rules table...")
                if not column_exists_fast(conn, 'metadata_rules', 'rule_type'):
                    print("  -> Adding rule_type...")
                    conn.execute(text("ALTER TABLE metadata_rules ADD COLUMN rule_type VARCHAR(20) DEFAULT 'DIRECT'"))
                    print("  [OK] Added rule_type")
                else:
                    print("  [SKIP] rule_type already exists")
                
                if not column_exists_fast(conn, 'metadata_rules', 'target_measure'):
                    print("  -> Adding target_measure...")
                    conn.execute(text("ALTER TABLE metadata_rules ADD COLUMN target_measure VARCHAR(50)"))
                    print("  [OK] Added target_measure")
                else:
                    print("  [SKIP] target_measure already exists")
                
                print("\n  -> Committing transaction...")
                trans.commit()
                
                print("\n" + "=" * 60)
                print("[OK] Migration completed successfully!")
                print("=" * 60)
                return 0
                
            except Exception as e:
                print(f"\n[ERROR] Rolling back transaction...")
                trans.rollback()
                print(f"[ERROR] Migration failed: {e}")
                import traceback
                traceback.print_exc()
                return 1
    
    except Exception as e:
        print(f"[ERROR] Connection error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(apply_migration())



