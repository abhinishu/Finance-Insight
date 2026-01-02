"""
Patch Use Case 3 Data - Populate Mock MTD and YTD Values
Updates pnl_commission and pnl_trade columns with calculated values based on pnl_daily.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal
from app.models import FactPnlUseCase3

def patch_uc3_data():
    """
    Update fact_pnl_use_case_3 rows to populate pnl_commission and pnl_trade.
    """
    print("=" * 70)
    print("PATCH: Use Case 3 Data - Populate Mock Values")
    print("=" * 70)
    print()
    
    db: Session = SessionLocal()
    
    try:
        # Step 1: Check current state
        print("Step 1: Checking current data state...")
        print("-" * 70)
        
        current_stats = db.execute(text("""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(CASE WHEN pnl_daily != 0 THEN 1 END) as rows_with_daily,
                SUM(pnl_daily) as sum_daily,
                SUM(pnl_commission) as sum_commission,
                SUM(pnl_trade) as sum_trade
            FROM fact_pnl_use_case_3
        """)).fetchone()
        
        print(f"  Total rows: {current_stats[0]}")
        print(f"  Rows with non-zero pnl_daily: {current_stats[1]}")
        print(f"  Current SUM(pnl_daily): {current_stats[2]}")
        print(f"  Current SUM(pnl_commission): {current_stats[3]}")
        print(f"  Current SUM(pnl_trade): {current_stats[4]}")
        print()
        
        # Step 2: Update rows where pnl_daily is not 0
        print("Step 2: Updating rows...")
        print("-" * 70)
        print("  Formula: pnl_commission = pnl_daily * 2.5")
        print("  Formula: pnl_trade = pnl_daily * 10.0")
        print()
        
        # Use raw SQL for efficient bulk update with Decimal precision
        update_sql = text("""
            UPDATE fact_pnl_use_case_3
            SET 
                pnl_commission = pnl_daily * 2.5,
                pnl_trade = pnl_daily * 10.0
            WHERE pnl_daily != 0
        """)
        
        result = db.execute(update_sql)
        rows_updated = result.rowcount
        db.commit()
        
        print(f"  [OK] Updated {rows_updated} rows")
        print()
        
        # Step 3: Verify the update
        print("Step 3: Verifying updated data...")
        print("-" * 70)
        
        updated_stats = db.execute(text("""
            SELECT 
                COUNT(*) as total_rows,
                SUM(pnl_daily) as sum_daily,
                SUM(pnl_commission) as sum_commission,
                SUM(pnl_trade) as sum_trade
            FROM fact_pnl_use_case_3
        """)).fetchone()
        
        sum_daily = Decimal(str(updated_stats[1] or 0))
        sum_commission = Decimal(str(updated_stats[2] or 0))
        sum_trade = Decimal(str(updated_stats[3] or 0))
        
        print(f"  Total rows: {updated_stats[0]}")
        print(f"  SUM(pnl_daily): {sum_daily}")
        print(f"  SUM(pnl_commission): {sum_commission}")
        print(f"  SUM(pnl_trade): {sum_trade}")
        print()
        
        # Step 4: Verify formulas
        print("Step 4: Verifying formulas...")
        print("-" * 70)
        expected_commission = sum_daily * Decimal('2.5')
        expected_trade = sum_daily * Decimal('10.0')
        
        commission_diff = abs(sum_commission - expected_commission)
        trade_diff = abs(sum_trade - expected_trade)
        
        print(f"  Expected SUM(pnl_commission): {expected_commission}")
        print(f"  Actual SUM(pnl_commission): {sum_commission}")
        print(f"  Difference: {commission_diff}")
        
        if commission_diff < Decimal('0.01'):
            print("  [PASS] pnl_commission formula verified")
        else:
            print(f"  [FAIL] pnl_commission formula mismatch! Expected {expected_commission}, got {sum_commission}")
        
        print()
        print(f"  Expected SUM(pnl_trade): {expected_trade}")
        print(f"  Actual SUM(pnl_trade): {sum_trade}")
        print(f"  Difference: {trade_diff}")
        
        if trade_diff < Decimal('0.01'):
            print("  [PASS] pnl_trade formula verified")
        else:
            print(f"  [FAIL] pnl_trade formula mismatch! Expected {expected_trade}, got {sum_trade}")
        
        print()
        print("=" * 70)
        print("PATCH COMPLETE")
        print("=" * 70)
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    patch_uc3_data()

