"""
Apply Trading Track Foundation migration - handles existing tables gracefully.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import text, inspect
from app.database import engine


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns


def index_exists(index_name: str) -> bool:
    """Check if an index exists."""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 1 FROM pg_indexes 
            WHERE indexname = :index_name
        """), {"index_name": index_name})
        return result.fetchone() is not None


def apply_migration():
    """Apply the Trading Track Foundation migration."""
    print("Applying Trading Track Foundation Migration")
    print("=" * 60)
    
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            # 1. Add missing dimension columns to fact_trading_pnl
            print("\n1. Adding dimension columns to fact_trading_pnl...")
            if not column_exists('fact_trading_pnl', 'process_1'):
                conn.execute(text("ALTER TABLE fact_trading_pnl ADD COLUMN process_1 VARCHAR(100)"))
                print("  [OK] Added process_1")
            else:
                print("  [SKIP] process_1 already exists")
            
            if not column_exists('fact_trading_pnl', 'process_2'):
                conn.execute(text("ALTER TABLE fact_trading_pnl ADD COLUMN process_2 VARCHAR(100)"))
                print("  [OK] Added process_2")
            else:
                print("  [SKIP] process_2 already exists")
            
            # 2. Add new measure columns
            print("\n2. Adding measure columns to fact_trading_pnl...")
            new_measures = [
                'pnl_trading_daily', 'pnl_trading_ytd',
                'pnl_commission_daily', 'pnl_commission_ytd',
                'pnl_total_daily', 'pnl_total_ytd'
            ]
            
            for measure in new_measures:
                if not column_exists('fact_trading_pnl', measure):
                    conn.execute(text(f"""
                        ALTER TABLE fact_trading_pnl 
                        ADD COLUMN {measure} NUMERIC(18, 2) DEFAULT 0
                    """))
                    print(f"  [OK] Added {measure}")
                else:
                    print(f"  [SKIP] {measure} already exists")
            
            # 3. Create indexes
            print("\n3. Creating indexes...")
            if not index_exists('idx_trade_proc2'):
                conn.execute(text("CREATE INDEX idx_trade_proc2 ON fact_trading_pnl(process_2)"))
                print("  [OK] Created idx_trade_proc2")
            else:
                print("  [SKIP] idx_trade_proc2 already exists")
            
            # 4. Add use_case_type to use_cases
            print("\n4. Adding use_case_type to use_cases...")
            if not column_exists('use_cases', 'use_case_type'):
                conn.execute(text("ALTER TABLE use_cases ADD COLUMN use_case_type VARCHAR(50) DEFAULT 'STANDARD'"))
                print("  [OK] Added use_case_type")
            else:
                print("  [SKIP] use_case_type already exists")
            
            # 5. Add rule_type and target_measure to metadata_rules
            print("\n5. Adding rule columns to metadata_rules...")
            if not column_exists('metadata_rules', 'rule_type'):
                conn.execute(text("ALTER TABLE metadata_rules ADD COLUMN rule_type VARCHAR(20) DEFAULT 'DIRECT'"))
                print("  [OK] Added rule_type")
            else:
                print("  [SKIP] rule_type already exists")
            
            if not column_exists('metadata_rules', 'target_measure'):
                conn.execute(text("ALTER TABLE metadata_rules ADD COLUMN target_measure VARCHAR(50)"))
                print("  [OK] Added target_measure")
            else:
                print("  [SKIP] target_measure already exists")
            
            trans.commit()
            
            print("\n" + "=" * 60)
            print("[OK] Migration completed successfully!")
            print("=" * 60)
            return 0
            
        except Exception as e:
            trans.rollback()
            print(f"\n[ERROR] Migration failed: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == "__main__":
    sys.exit(apply_migration())



