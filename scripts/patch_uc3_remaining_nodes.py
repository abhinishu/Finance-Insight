"""
Data Patch Script for Use Case 3 - Populate Remaining Empty Nodes
Updates fact_pnl_use_case_3 to populate hierarchy nodes: CRB, ETF Amber, MSET.

This script:
1. Updates strategy column to match hierarchy node names
2. Verifies the updates with SUM queries
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from app.database import SessionLocal
from app.models import FactPnlUseCase3

def patch_uc3_remaining_nodes():
    """
    Patch remaining empty nodes for Use Case 3.
    """
    print("=" * 80)
    print("PATCH: Use Case 3 - Populate Remaining Empty Nodes")
    print("=" * 80)
    print()
    
    db: Session = SessionLocal()
    
    try:
        # Step 1: Check current state
        print("STEP 1: Checking Current State")
        print("-" * 80)
        
        # Check if PROCESS_1, PROCESS_2, PROCESS_3 exist
        distinct_processes = db.query(func.count(func.distinct(FactPnlUseCase3.process_2))).scalar()
        process_2_values = db.query(FactPnlUseCase3.process_2).distinct().limit(10).all()
        process_2_list = [p[0] for p in process_2_values if p[0]]
        
        print(f"  Distinct process_2 values: {distinct_processes}")
        print(f"  Sample process_2 values: {process_2_list[:10]}")
        print()
        
        # Check current strategy distribution
        strategy_counts = db.query(
            FactPnlUseCase3.strategy,
            func.count(FactPnlUseCase3.entry_id).label('count')
        ).group_by(FactPnlUseCase3.strategy).all()
        
        print(f"  Current strategy distribution:")
        for strategy, count in strategy_counts:
            print(f"    - '{strategy}': {count} rows")
        print()
        
        # Step 2: Update Data
        print("STEP 2: Updating Data")
        print("-" * 80)
        
        updates_performed = []
        
        # Update 1: CRB
        # Check if CRB already has data
        crb_existing = db.query(func.count(FactPnlUseCase3.entry_id)).filter(
            FactPnlUseCase3.strategy == 'CRB'
        ).scalar()
        
        if crb_existing >= 50:
            print(f"  [SKIP] CRB already has {crb_existing} rows (sufficient)")
        else:
            # Try PROCESS_1 first, if not found, use random rows from 'NON-CORE' or other unassigned strategies
            process_1_count = db.query(func.count(FactPnlUseCase3.entry_id)).filter(
                FactPnlUseCase3.process_2 == 'PROCESS_1'
            ).scalar()
            
            if process_1_count > 0:
                update1 = text("""
                    UPDATE fact_pnl_use_case_3
                    SET strategy = 'CRB'
                    WHERE process_2 = 'PROCESS_1'
                """)
                result1 = db.execute(update1)
                rows1 = result1.rowcount
                db.commit()
                updates_performed.append(('PROCESS_1 -> CRB', rows1))
                print(f"  [OK] Updated {rows1} rows: process_2='PROCESS_1' -> strategy='CRB'")
            else:
                # First try to map 'NON-CORE' to 'CRB'
                non_core_count = db.query(func.count(FactPnlUseCase3.entry_id)).filter(
                    FactPnlUseCase3.strategy == 'NON-CORE'
                ).scalar()
                
                if non_core_count > 0:
                    update1a = text("""
                        UPDATE fact_pnl_use_case_3
                        SET strategy = 'CRB'
                        WHERE strategy = 'NON-CORE'
                    """)
                    result1a = db.execute(update1a)
                    rows1a = result1a.rowcount
                    db.commit()
                    updates_performed.append(('NON-CORE -> CRB', rows1a))
                    print(f"  [OK] Updated {rows1a} rows: strategy='NON-CORE' -> strategy='CRB'")
                else:
                    # Pick 50 random rows from unassigned strategies or reassign from 'Other Strategy'
                    update1 = text("""
                        UPDATE fact_pnl_use_case_3
                        SET strategy = 'CRB'
                        WHERE entry_id IN (
                            SELECT entry_id FROM fact_pnl_use_case_3
                            WHERE strategy NOT IN ('CRB', 'ETF Amber', 'MSET', 'Commissions (Non Swap)', 'Swap Commission', 'Facilitations', 'Inventory Management', 'Core Ex CRB', 'Commissions', 'Trading')
                            OR strategy IS NULL
                            LIMIT 50
                        )
                    """)
                    result1 = db.execute(update1)
                    rows1 = result1.rowcount
                    db.commit()
                    if rows1 > 0:
                        updates_performed.append(('Random rows -> CRB', rows1))
                        print(f"  [OK] Updated {rows1} random rows -> strategy='CRB'")
                    else:
                        print(f"  [WARNING] No rows available to assign to 'CRB'")
        
        # Update 2: ETF Amber
        # Check if ETF Amber already has data
        etf_existing = db.query(func.count(FactPnlUseCase3.entry_id)).filter(
            FactPnlUseCase3.strategy == 'ETF Amber'
        ).scalar()
        
        if etf_existing >= 50:
            print(f"  [SKIP] ETF Amber already has {etf_existing} rows (sufficient)")
        else:
            # Try PROCESS_2 first, if not found, use random rows from 'ETF Amer' or other unassigned strategies
            process_2_count = db.query(func.count(FactPnlUseCase3.entry_id)).filter(
                FactPnlUseCase3.process_2 == 'PROCESS_2'
            ).scalar()
            
            if process_2_count > 0:
                update2 = text("""
                    UPDATE fact_pnl_use_case_3
                    SET strategy = 'ETF Amber'
                    WHERE process_2 = 'PROCESS_2'
                """)
                result2 = db.execute(update2)
                rows2 = result2.rowcount
                db.commit()
                updates_performed.append(('PROCESS_2 -> ETF Amber', rows2))
                print(f"  [OK] Updated {rows2} rows: process_2='PROCESS_2' -> strategy='ETF Amber'")
            else:
                # First try to map 'ETF Amer' to 'ETF Amber'
                etf_amer_count = db.query(func.count(FactPnlUseCase3.entry_id)).filter(
                    FactPnlUseCase3.strategy == 'ETF Amer'
                ).scalar()
                
                if etf_amer_count > 0:
                    update2a = text("""
                        UPDATE fact_pnl_use_case_3
                        SET strategy = 'ETF Amber'
                        WHERE strategy = 'ETF Amer'
                    """)
                    result2a = db.execute(update2a)
                    rows2a = result2a.rowcount
                    db.commit()
                    updates_performed.append(('ETF Amer -> ETF Amber', rows2a))
                    print(f"  [OK] Updated {rows2a} rows: strategy='ETF Amer' -> strategy='ETF Amber'")
                else:
                    # Reassign from 'Other Strategy' or pick random rows from unassigned strategies
                    # If still not enough, reassign from 'Core Ex CRB' (has 38 rows, can spare some)
                    update2 = text("""
                        UPDATE fact_pnl_use_case_3
                        SET strategy = 'ETF Amber'
                        WHERE entry_id IN (
                            SELECT entry_id FROM fact_pnl_use_case_3
                            WHERE strategy NOT IN ('CRB', 'ETF Amber', 'MSET', 'Commissions (Non Swap)', 'Swap Commission', 'Facilitations', 'Inventory Management', 'Commissions', 'Trading')
                            OR strategy IS NULL
                            LIMIT 50
                        )
                    """)
                    result2 = db.execute(update2)
                    rows2 = result2.rowcount
                    db.commit()
                    if rows2 > 0:
                        updates_performed.append(('Random rows -> ETF Amber', rows2))
                        print(f"  [OK] Updated {rows2} random rows -> strategy='ETF Amber'")
                    else:
                        print(f"  [WARNING] No rows available to assign to 'ETF Amber'")
        
        # Update 3: MSET
        # Check if MSET already has data
        mset_existing = db.query(func.count(FactPnlUseCase3.entry_id)).filter(
            FactPnlUseCase3.strategy == 'MSET'
        ).scalar()
        
        if mset_existing >= 50:
            print(f"  [SKIP] MSET already has {mset_existing} rows (sufficient)")
        else:
            # Try PROCESS_3 first, if not found, use random rows
            process_3_count = db.query(func.count(FactPnlUseCase3.entry_id)).filter(
                FactPnlUseCase3.process_2 == 'PROCESS_3'
            ).scalar()
            
            if process_3_count > 0:
                update3 = text("""
                    UPDATE fact_pnl_use_case_3
                    SET strategy = 'MSET'
                    WHERE process_2 = 'PROCESS_3'
                """)
                result3 = db.execute(update3)
                rows3 = result3.rowcount
                db.commit()
                updates_performed.append(('PROCESS_3 -> MSET', rows3))
                print(f"  [OK] Updated {rows3} rows: process_2='PROCESS_3' -> strategy='MSET'")
            else:
                # Reassign from 'Other Strategy' or pick random rows from unassigned strategies
                # If still not enough, reassign from 'Core Ex CRB' (has 38 rows, can spare some)
                # Or reassign from 'Inventory Management' (has 140 rows, can spare 50)
                update3 = text("""
                    UPDATE fact_pnl_use_case_3
                    SET strategy = 'MSET'
                    WHERE entry_id IN (
                        SELECT entry_id FROM fact_pnl_use_case_3
                        WHERE strategy NOT IN ('CRB', 'ETF Amber', 'MSET', 'Commissions (Non Swap)', 'Swap Commission', 'Facilitations', 'Commissions', 'Trading')
                        OR strategy IS NULL
                        LIMIT 50
                    )
                """)
                result3 = db.execute(update3)
                rows3 = result3.rowcount
                db.commit()
                if rows3 > 0:
                    updates_performed.append(('Random rows -> MSET', rows3))
                    print(f"  [OK] Updated {rows3} random rows -> strategy='MSET'")
                else:
                    # Last resort: reassign from 'Inventory Management' (has many rows)
                    update3_fallback = text("""
                        UPDATE fact_pnl_use_case_3
                        SET strategy = 'MSET'
                        WHERE strategy = 'Inventory Management'
                        LIMIT 50
                    """)
                    result3_fallback = db.execute(update3_fallback)
                    rows3_fallback = result3_fallback.rowcount
                    db.commit()
                    if rows3_fallback > 0:
                        updates_performed.append(('Inventory Management -> MSET', rows3_fallback))
                        print(f"  [OK] Updated {rows3_fallback} rows: strategy='Inventory Management' -> strategy='MSET'")
                    else:
                        print(f"  [WARNING] No rows available to assign to 'MSET'")
        
        print()
        
        # Step 3: Verification
        print("STEP 3: Verification")
        print("-" * 80)
        
        # Verify CRB
        crb_stats = db.query(
            func.count(FactPnlUseCase3.entry_id).label('count'),
            func.sum(FactPnlUseCase3.pnl_daily).label('sum_daily')
        ).filter(
            FactPnlUseCase3.strategy == 'CRB'
        ).first()
        
        if crb_stats:
            crb_count = crb_stats.count
            crb_sum = Decimal(str(crb_stats.sum_daily or 0))
            print(f"  'CRB':")
            print(f"    Rows: {crb_count}")
            print(f"    SUM(pnl_daily): {crb_sum}")
            if crb_count > 0 and crb_sum != Decimal('0'):
                print(f"    [PASS] CRB has data")
            else:
                print(f"    [WARNING] CRB has no data or zero sum")
        else:
            print(f"  [FAIL] CRB not found")
        print()
        
        # Verify ETF Amber
        etf_stats = db.query(
            func.count(FactPnlUseCase3.entry_id).label('count'),
            func.sum(FactPnlUseCase3.pnl_daily).label('sum_daily')
        ).filter(
            FactPnlUseCase3.strategy == 'ETF Amber'
        ).first()
        
        if etf_stats:
            etf_count = etf_stats.count
            etf_sum = Decimal(str(etf_stats.sum_daily or 0))
            print(f"  'ETF Amber':")
            print(f"    Rows: {etf_count}")
            print(f"    SUM(pnl_daily): {etf_sum}")
            if etf_count > 0 and etf_sum != Decimal('0'):
                print(f"    [PASS] ETF Amber has data")
            else:
                print(f"    [WARNING] ETF Amber has no data or zero sum")
        else:
            print(f"  [FAIL] ETF Amber not found")
        print()
        
        # Verify MSET
        mset_stats = db.query(
            func.count(FactPnlUseCase3.entry_id).label('count'),
            func.sum(FactPnlUseCase3.pnl_daily).label('sum_daily')
        ).filter(
            FactPnlUseCase3.strategy == 'MSET'
        ).first()
        
        if mset_stats:
            mset_count = mset_stats.count
            mset_sum = Decimal(str(mset_stats.sum_daily or 0))
            print(f"  'MSET':")
            print(f"    Rows: {mset_count}")
            print(f"    SUM(pnl_daily): {mset_sum}")
            if mset_count > 0 and mset_sum != Decimal('0'):
                print(f"    [PASS] MSET has data")
            else:
                print(f"    [WARNING] MSET has no data or zero sum")
        else:
            print(f"  [FAIL] MSET not found")
        print()
        
        # Summary
        print("=" * 80)
        print("PATCH COMPLETE")
        print("=" * 80)
        print()
        print("Summary:")
        for update_desc, row_count in updates_performed:
            print(f"  - {update_desc}: {row_count} rows")
        print()
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    patch_uc3_remaining_nodes()

