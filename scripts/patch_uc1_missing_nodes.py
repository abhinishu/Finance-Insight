"""
Data Patch Script for Use Case 1 - Fill Missing Nodes
Inserts mock data into fact_pnl_gold for specific CC IDs that match hierarchy nodes.

This script:
1. Inserts mock data for specific cc_id values
2. Sets MTD/YTD based on daily_pnl formulas
3. Verifies the inserts
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from decimal import Decimal
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from app.database import SessionLocal
from app.models import FactPnlGold
from uuid import uuid4

def patch_uc1_missing_nodes():
    """
    Patch missing nodes for Use Case 1 by inserting mock data.
    """
    print("=" * 80)
    print("PATCH: Use Case 1 - Fill Missing Nodes")
    print("=" * 80)
    print()
    
    db: Session = SessionLocal()
    
    try:
        # Step 1: Check current state
        print("STEP 1: Checking Current State")
        print("-" * 80)
        
        target_cc_ids = [
            'CC_AMER_PROG_TRADING_005',
            'CC_EMEA_INDEX_ARB_010',
            'CC_APAC_ALGO_G1_011'
        ]
        
        for cc_id in target_cc_ids:
            count = db.query(FactPnlGold).filter(
                FactPnlGold.cc_id == cc_id
            ).count()
            print(f"  Current rows for '{cc_id}': {count}")
        print()
        
        # Step 2: Insert Mock Data
        print("STEP 2: Inserting Mock Data")
        print("-" * 80)
        
        # Data to insert: (cc_id, daily_pnl, description)
        mock_data = [
            ('CC_AMER_PROG_TRADING_005', Decimal('15000.00'), 'Americas Program Trading'),
            ('CC_EMEA_INDEX_ARB_010', Decimal('22000.00'), 'EMEA Index Arbitrage'),
            ('CC_APAC_ALGO_G1_011', Decimal('35000.00'), 'APAC Algorithmic G1'),
        ]
        
        inserted_count = 0
        
        for cc_id, daily_pnl, description in mock_data:
            # Calculate MTD and YTD
            mtd_pnl = daily_pnl * Decimal('5')
            ytd_pnl = daily_pnl * Decimal('20')
            
            # Check current sum for this CC ID
            current_sum = db.query(func.sum(FactPnlGold.daily_pnl)).filter(
                FactPnlGold.cc_id == cc_id
            ).scalar()
            current_sum = Decimal(str(current_sum or 0))
            
            # Insert new row regardless (to ensure data exists and add to totals)
            # Note: fact_pnl_gold requires: fact_id, account_id, cc_id, book_id, strategy_id, trade_date, daily_pnl, mtd_pnl, ytd_pnl, pytd_pnl
            new_fact = FactPnlGold(
                fact_id=uuid4(),
                account_id=f"ACC_{cc_id}",
                cc_id=cc_id,
                book_id=f"BOOK_{cc_id[-3:]}",  # Use last 3 chars of cc_id
                strategy_id=f"STRAT_{cc_id[-3:]}",
                trade_date=date.today(),
                daily_pnl=daily_pnl,
                mtd_pnl=mtd_pnl,
                ytd_pnl=ytd_pnl,
                pytd_pnl=Decimal('0')  # Set to 0 for now
            )
            
            db.add(new_fact)
            inserted_count += 1
            
            if current_sum == Decimal('0'):
                print(f"  [OK] Inserted '{cc_id}' ({description}) - was zero, now has data:")
            else:
                print(f"  [OK] Inserted additional row for '{cc_id}' ({description}):")
            print(f"        daily_pnl={daily_pnl}, mtd_pnl={mtd_pnl}, ytd_pnl={ytd_pnl}")
            print(f"        Previous SUM: {current_sum}, New row adds: {daily_pnl}")
        
        db.commit()
        print(f"\n  Total rows inserted: {inserted_count}")
        print()
        
        # Step 3: Verification
        print("STEP 3: Verification")
        print("-" * 80)
        
        for cc_id, expected_daily, description in mock_data:
            facts = db.query(FactPnlGold).filter(
                FactPnlGold.cc_id == cc_id
            ).all()
            
            if facts:
                total_daily = sum(Decimal(str(f.daily_pnl)) for f in facts)
                total_mtd = sum(Decimal(str(f.mtd_pnl)) for f in facts)
                total_ytd = sum(Decimal(str(f.ytd_pnl)) for f in facts)
                
                print(f"  '{cc_id}' ({description}):")
                print(f"    Row count: {len(facts)}")
                print(f"    SUM(daily_pnl): {total_daily}")
                print(f"    SUM(mtd_pnl): {total_mtd}")
                print(f"    SUM(ytd_pnl): {total_ytd}")
                
                # Verify that data exists (formulas may not match if existing data had different formulas)
                if total_daily != Decimal('0'):
                    print(f"    [PASS] Data exists: SUM(daily_pnl)={total_daily} (non-zero)")
                else:
                    print(f"    [WARNING] SUM(daily_pnl) is still zero after insert")
                
                # Note: MTD/YTD formulas may not match if existing data had different formulas
                # The new row follows: mtd = daily * 5, ytd = daily * 20
                print(f"    [INFO] New row formulas: mtd=daily*5, ytd=daily*20")
            else:
                print(f"  [WARNING] '{cc_id}' has no data after insert")
            print()
        
        print("=" * 80)
        print("PATCH COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    patch_uc1_missing_nodes()

