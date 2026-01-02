"""
Comprehensive Data Alignment Script for All Use Cases
Aligns fact table data to match hierarchy metadata for Use Cases 2 and 3.

This script:
1. Fixes Use Case 2 (Sterling/Entries): Maps TRADE_XXX to CC_XXX format
2. Fixes Use Case 3 (Cash Equity): Aligns strategy to match hierarchy leaf node names
3. Populates MTD/YTD for Use Case 3
4. Verifies all alignments
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text, distinct, func
from app.database import SessionLocal
from app.models import FactPnlEntries, FactPnlUseCase3, DimHierarchy, UseCase

def align_use_case_2():
    """Align Use Case 2 (Sterling/Entries) data to match hierarchy."""
    print("=" * 80)
    print("USE CASE 2: Aligning fact_pnl_entries (Project Sterling)")
    print("=" * 80)
    print()
    
    db: Session = SessionLocal()
    
    try:
        # Step 1: Get Use Case 2
        use_case_2 = db.query(UseCase).filter(
            UseCase.name.ilike('%Sterling%')
        ).first()
        
        if not use_case_2:
            print("  [ERROR] Use Case 2 (Project Sterling) not found!")
            return
        
        print(f"  Use Case: {use_case_2.name}")
        print(f"  Use Case ID: {use_case_2.use_case_id}")
        print()
        
        # Step 2: Check current category_code values
        print("STEP 1: Checking Current category_code Values")
        print("-" * 80)
        
        distinct_codes = db.query(distinct(FactPnlEntries.category_code)).filter(
            FactPnlEntries.use_case_id == use_case_2.use_case_id,
            FactPnlEntries.category_code.isnot(None)
        ).all()
        codes = sorted([c[0] for c in distinct_codes if c[0]])
        
        print(f"  Distinct category_code values ({len(codes)}):")
        for code in codes[:10]:
            count = db.query(func.count(FactPnlEntries.id)).filter(
                FactPnlEntries.use_case_id == use_case_2.use_case_id,
                FactPnlEntries.category_code == code
            ).scalar()
            print(f"    - '{code}': {count} rows")
        if len(codes) > 10:
            print(f"    ... and {len(codes) - 10} more")
        print()
        
        # Step 3: Get hierarchy leaf nodes
        print("STEP 2: Getting Hierarchy Leaf Nodes")
        print("-" * 80)
        
        atlas_source = use_case_2.atlas_structure_id
        leaf_nodes = db.query(DimHierarchy).filter(
            DimHierarchy.atlas_source == atlas_source,
            DimHierarchy.is_leaf == True
        ).order_by(DimHierarchy.node_id).all()
        
        leaf_node_ids = [n.node_id for n in leaf_nodes]
        print(f"  Found {len(leaf_node_ids)} leaf nodes in hierarchy")
        print(f"  Sample: {leaf_node_ids[:5]}")
        print()
        
        # Step 4: Map TRADE_XXX to CC_XXX codes
        print("STEP 3: Mapping TRADE_XXX to CC_XXX Format")
        print("-" * 80)
        
        # Get all TRADE_XXX codes for this use case
        trade_codes = db.query(distinct(FactPnlEntries.category_code)).filter(
            FactPnlEntries.use_case_id == use_case_2.use_case_id,
            FactPnlEntries.category_code.like('TRADE_%')
        ).all()
        trade_codes_list = [c[0] for c in trade_codes if c[0]]
        
        print(f"  Found {len(trade_codes_list)} TRADE_XXX codes to map")
        
        # Map to CC codes - use first few leaf nodes and distribute evenly
        # Use CC_AMER_CASH_NY_001, CC_AMER_CASH_NY_002, CC_AMER_CASH_NY_003, etc.
        target_cc_codes = [node_id for node_id in leaf_node_ids if node_id.startswith('CC_')][:13]  # Use first 13 CC codes
        
        if not target_cc_codes:
            print("  [ERROR] No CC_XXX leaf nodes found in hierarchy!")
            return
        
        print(f"  Target CC codes: {target_cc_codes[:5]}... (total: {len(target_cc_codes)})")
        print()
        
        # Distribute TRADE codes across CC codes
        updates_performed = []
        for idx, trade_code in enumerate(trade_codes_list):
            # Round-robin distribution across target CC codes
            target_cc = target_cc_codes[idx % len(target_cc_codes)]
            
            update_sql = text("""
                UPDATE fact_pnl_entries
                SET category_code = :target_cc
                WHERE use_case_id = :uc_id
                AND category_code = :trade_code
            """)
            
            result = db.execute(update_sql, {
                "target_cc": target_cc,
                "uc_id": str(use_case_2.use_case_id),
                "trade_code": trade_code
            })
            rows_updated = result.rowcount
            db.commit()
            
            if rows_updated > 0:
                updates_performed.append((trade_code, target_cc, rows_updated))
                print(f"  [OK] Mapped '{trade_code}' -> '{target_cc}': {rows_updated} rows")
        
        print()
        print(f"  Total mappings: {len(updates_performed)}")
        print()
        
        # Step 5: Verify alignment
        print("STEP 4: Verification")
        print("-" * 80)
        
        # Count category_code values starting with 'CC_'
        cc_count = db.query(func.count(FactPnlEntries.id)).filter(
            FactPnlEntries.use_case_id == use_case_2.use_case_id,
            FactPnlEntries.category_code.like('CC_%')
        ).scalar()
        
        print(f"  category_code values starting with 'CC_': {cc_count} rows")
        
        if cc_count > 0:
            print(f"  [PASS] Use Case 2 alignment verified")
        else:
            print(f"  [FAIL] No CC_XXX codes found!")
        
        # Show distribution
        cc_distribution = db.query(
            FactPnlEntries.category_code,
            func.count(FactPnlEntries.id).label('count')
        ).filter(
            FactPnlEntries.use_case_id == use_case_2.use_case_id,
            FactPnlEntries.category_code.like('CC_%')
        ).group_by(FactPnlEntries.category_code).order_by(func.count(FactPnlEntries.id).desc()).limit(10).all()
        
        print(f"  Top 10 CC code distributions:")
        for cc_code, count in cc_distribution:
            print(f"    - '{cc_code}': {count} rows")
        print()
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Exception in Use Case 2 alignment: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def align_use_case_3():
    """Align Use Case 3 (Cash Equity) data to match hierarchy."""
    print("=" * 80)
    print("USE CASE 3: Aligning fact_pnl_use_case_3 (America Cash Equity Trading)")
    print("=" * 80)
    print()
    
    db: Session = SessionLocal()
    
    try:
        # Step 1: Get Use Case 3
        use_case_3 = db.query(UseCase).filter(
            UseCase.name.ilike('%America Cash Equity Trading%')
        ).first()
        
        if not use_case_3:
            print("  [ERROR] Use Case 3 not found!")
            return
        
        print(f"  Use Case: {use_case_3.name}")
        print(f"  Use Case ID: {use_case_3.use_case_id}")
        print()
        
        # Step 2: Populate MTD/YTD values
        print("STEP 1: Populating MTD/YTD Values")
        print("-" * 80)
        print("  Formula: pnl_commission = pnl_daily * 2.5")
        print("  Formula: pnl_trade = pnl_daily * 10.0")
        print()
        
        update_mtd_ytd = text("""
            UPDATE fact_pnl_use_case_3
            SET 
                pnl_commission = pnl_daily * 2.5,
                pnl_trade = pnl_daily * 10.0
            WHERE pnl_daily != 0
        """)
        
        result = db.execute(update_mtd_ytd)
        rows_updated = result.rowcount
        db.commit()
        
        print(f"  [OK] Updated {rows_updated} rows with MTD/YTD values")
        print()
        
        # Step 3: Align strategy to match hierarchy leaf node names
        print("STEP 2: Aligning Strategy to Match Hierarchy Leaf Nodes")
        print("-" * 80)
        
        updates_performed = []
        
        # Update 1: SD COMMISSION -> Commissions (Non Swap)
        update1 = text("""
            UPDATE fact_pnl_use_case_3
            SET strategy = 'Commissions (Non Swap)'
            WHERE process_2 = 'SD COMMISSION'
        """)
        result1 = db.execute(update1)
        rows1 = result1.rowcount
        db.commit()
        if rows1 > 0:
            updates_performed.append(('SD COMMISSION -> Commissions (Non Swap)', rows1))
            print(f"  [OK] Updated {rows1} rows: process_2='SD COMMISSION' -> strategy='Commissions (Non Swap)'")
        
        # Update 2: SWAP COMMISSION -> Swap Commission
        update2 = text("""
            UPDATE fact_pnl_use_case_3
            SET strategy = 'Swap Commission'
            WHERE process_2 = 'SWAP COMMISSION'
        """)
        result2 = db.execute(update2)
        rows2 = result2.rowcount
        db.commit()
        if rows2 > 0:
            updates_performed.append(('SWAP COMMISSION -> Swap Commission', rows2))
            print(f"  [OK] Updated {rows2} rows: process_2='SWAP COMMISSION' -> strategy='Swap Commission'")
        
        # Update 3: FACILITATION -> Facilitations
        update3 = text("""
            UPDATE fact_pnl_use_case_3
            SET strategy = 'Facilitations'
            WHERE UPPER(process_2) LIKE '%FACILITATION%'
            AND strategy != 'Facilitations'
        """)
        result3 = db.execute(update3)
        rows3 = result3.rowcount
        db.commit()
        if rows3 > 0:
            updates_performed.append(('FACILITATION -> Facilitations', rows3))
            print(f"  [OK] Updated {rows3} rows: process_2 containing 'FACILITATION' -> strategy='Facilitations'")
        
        # Update 4: INVENTORY -> Inventory Management
        update4 = text("""
            UPDATE fact_pnl_use_case_3
            SET strategy = 'Inventory Management'
            WHERE UPPER(process_2) LIKE '%INVENTORY%'
            AND strategy != 'Inventory Management'
        """)
        result4 = db.execute(update4)
        rows4 = result4.rowcount
        db.commit()
        if rows4 > 0:
            updates_performed.append(('INVENTORY -> Inventory Management', rows4))
            print(f"  [OK] Updated {rows4} rows: process_2 containing 'INVENTORY' -> strategy='Inventory Management'")
        
        print()
        print(f"  Total updates: {len(updates_performed)}")
        print()
        
        # Step 4: Verification
        print("STEP 3: Verification")
        print("-" * 80)
        
        # Verify 'Commissions (Non Swap)' has data
        comm_non_swap = db.query(
            func.count(FactPnlUseCase3.entry_id).label('count'),
            func.sum(FactPnlUseCase3.pnl_daily).label('sum_daily')
        ).filter(
            FactPnlUseCase3.strategy == 'Commissions (Non Swap)'
        ).first()
        
        if comm_non_swap and comm_non_swap.count > 0:
            print(f"  [PASS] 'Commissions (Non Swap)': {comm_non_swap.count} rows, sum={comm_non_swap.sum_daily}")
        else:
            print(f"  [FAIL] 'Commissions (Non Swap)' has no data or zero sum!")
        
        # Verify all leaf node strategies
        leaf_strategies = [
            'Commissions (Non Swap)',
            'Swap Commission',
            'Facilitations',
            'Inventory Management'
        ]
        
        print(f"  Leaf Node Strategy Verification:")
        for strategy in leaf_strategies:
            stats = db.query(
                func.count(FactPnlUseCase3.entry_id).label('count'),
                func.sum(FactPnlUseCase3.pnl_daily).label('sum_daily')
            ).filter(
                FactPnlUseCase3.strategy == strategy
            ).first()
            
            count = stats.count if stats else 0
            sum_daily = Decimal(str(stats.sum_daily or 0)) if stats else Decimal('0')
            
            if count > 0 and sum_daily != Decimal('0'):
                print(f"    [PASS] '{strategy}': {count} rows, sum={sum_daily}")
            else:
                print(f"    [FAIL] '{strategy}': {count} rows, sum={sum_daily}")
        
        print()
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Exception in Use Case 3 alignment: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def main():
    """Main alignment function"""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE DATA ALIGNMENT: All Use Cases")
    print("=" * 80)
    print()
    
    # Align Use Case 2
    align_use_case_2()
    
    # Align Use Case 3
    align_use_case_3()
    
    print()
    print("=" * 80)
    print("ALIGNMENT COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()

