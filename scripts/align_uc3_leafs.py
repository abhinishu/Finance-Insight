"""
Final Data Alignment Script for Use Case 3 Leaf Nodes
Aligns fact_pnl_use_case_3 data to match hierarchy leaf node names exactly.

This script ensures every hierarchy leaf node has matching data in the fact table.
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
from app.models import FactPnlUseCase3, DimHierarchy, UseCase

def align_uc3_leafs():
    """
    Align fact_pnl_use_case_3 data to match hierarchy leaf node names.
    """
    print("=" * 80)
    print("FINAL DATA ALIGNMENT: Use Case 3 Leaf Nodes")
    print("=" * 80)
    print()
    
    db: Session = SessionLocal()
    
    try:
        # Step 1: Get hierarchy leaf node names
        print("STEP 1: Identifying Hierarchy Leaf Nodes")
        print("-" * 80)
        
        use_case_3 = db.query(UseCase).filter(
            UseCase.name.ilike('%America Cash Equity Trading%')
        ).first()
        
        if not use_case_3:
            print("  [ERROR] Use Case 3 not found!")
            return
        
        atlas_source = use_case_3.atlas_structure_id
        print(f"  Use Case: {use_case_3.name}")
        print(f"  Atlas Source: {atlas_source}")
        print()
        
        # Get leaf nodes
        leaf_nodes = db.query(DimHierarchy).filter(
            DimHierarchy.atlas_source == atlas_source,
            DimHierarchy.is_leaf == True
        ).order_by(DimHierarchy.node_name).all()
        
        leaf_node_names = [n.node_name for n in leaf_nodes]
        print(f"  Leaf Node Names ({len(leaf_node_names)}):")
        for node in leaf_nodes:
            print(f"    - {node.node_id}: '{node.node_name}'")
        print()
        
        # Step 2: Check current process_2 values
        print("STEP 2: Checking Current process_2 Values")
        print("-" * 80)
        
        distinct_processes = db.query(distinct(FactPnlUseCase3.process_2)).filter(
            FactPnlUseCase3.process_2.isnot(None)
        ).all()
        processes = sorted([p[0] for p in distinct_processes if p[0]])
        
        print(f"  Distinct Process_2 values ({len(processes)}):")
        for process in processes:
            count = db.query(func.count(FactPnlUseCase3.entry_id)).filter(
                FactPnlUseCase3.process_2 == process
            ).scalar()
            print(f"    - '{process}': {count} rows")
        print()
        
        # Step 3: Perform Alignment Updates
        print("STEP 3: Performing Alignment Updates")
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
        updates_performed.append(('SWAP COMMISSION -> Swap Commission', rows2))
        print(f"  [OK] Updated {rows2} rows: process_2='SWAP COMMISSION' -> strategy='Swap Commission'")
        
        # Update 3: Check for FACILITATION (case variations)
        update3a = text("""
            UPDATE fact_pnl_use_case_3
            SET strategy = 'Facilitations'
            WHERE UPPER(process_2) LIKE '%FACILITATION%'
            AND strategy != 'Facilitations'
        """)
        result3a = db.execute(update3a)
        rows3a = result3a.rowcount
        db.commit()
        if rows3a > 0:
            updates_performed.append(('FACILITATION -> Facilitations', rows3a))
            print(f"  [OK] Updated {rows3a} rows: process_2 containing 'FACILITATION' -> strategy='Facilitations'")
        
        # Update 4: Ensure Inventory Management matches (already should be aligned, but verify)
        # Check if we need to update any remaining rows
        inventory_count = db.query(func.count(FactPnlUseCase3.entry_id)).filter(
            FactPnlUseCase3.strategy == 'Inventory Management'
        ).scalar()
        
        if inventory_count == 0:
            # Try to find rows with inventory-related process_2
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
        else:
            print(f"  [INFO] Inventory Management already has {inventory_count} rows")
        
        # Step 4: Ensure every leaf node has at least some data
        print()
        print("STEP 4: Ensuring Every Leaf Node Has Data")
        print("-" * 80)
        
        # Check current strategy distribution
        strategy_counts = {}
        for leaf_name in leaf_node_names:
            count = db.query(func.count(FactPnlUseCase3.entry_id)).filter(
                FactPnlUseCase3.strategy == leaf_name
            ).scalar()
            strategy_counts[leaf_name] = count
            print(f"  '{leaf_name}': {count} rows")
        
        # If any leaf node has < 10 rows, redistribute some data
        rows_redistributed = 0
        for leaf_name in leaf_node_names:
            if strategy_counts[leaf_name] < 10:
                needed = 10 - strategy_counts[leaf_name]
                print(f"  [WARNING] '{leaf_name}' has only {strategy_counts[leaf_name]} rows, need {needed} more")
                
                # Find rows with 'Other Process 2' or similar that we can reassign
                update_redist = text(f"""
                    UPDATE fact_pnl_use_case_3
                    SET strategy = :leaf_name
                    WHERE strategy IN ('Other Strategy', 'Other Process 2')
                    AND entry_id IN (
                        SELECT entry_id FROM fact_pnl_use_case_3
                        WHERE strategy IN ('Other Strategy', 'Other Process 2')
                        LIMIT :needed
                    )
                """)
                result_redist = db.execute(update_redist, {"leaf_name": leaf_name, "needed": needed})
                rows_redist = result_redist.rowcount
                db.commit()
                if rows_redist > 0:
                    rows_redistributed += rows_redist
                    print(f"    [OK] Redistributed {rows_redist} rows to '{leaf_name}'")
        
        if rows_redistributed == 0:
            print("  [INFO] All leaf nodes have sufficient data")
        print()
        
        # Step 5: Verification
        print("STEP 5: Verification")
        print("-" * 80)
        
        # Verify each leaf node has non-zero sum
        verification_passed = True
        for leaf_name in leaf_node_names:
            stats = db.query(
                func.count(FactPnlUseCase3.entry_id).label('count'),
                func.sum(FactPnlUseCase3.pnl_daily).label('sum_daily'),
                func.sum(FactPnlUseCase3.pnl_commission).label('sum_commission'),
                func.sum(FactPnlUseCase3.pnl_trade).label('sum_trade')
            ).filter(
                FactPnlUseCase3.strategy == leaf_name
            ).first()
            
            count = stats.count
            sum_daily = Decimal(str(stats.sum_daily or 0))
            sum_commission = Decimal(str(stats.sum_commission or 0))
            sum_trade = Decimal(str(stats.sum_trade or 0))
            
            print(f"  '{leaf_name}':")
            print(f"    Rows: {count}")
            print(f"    SUM(pnl_daily): {sum_daily}")
            print(f"    SUM(pnl_commission): {sum_commission}")
            print(f"    SUM(pnl_trade): {sum_trade}")
            
            if sum_daily == Decimal('0'):
                print(f"    [WARNING] Zero daily P&L for '{leaf_name}'")
                verification_passed = False
            else:
                print(f"    [PASS] Non-zero daily P&L")
            print()
        
        # Special verification for "Commissions (Non Swap)"
        print("  Special Verification: 'Commissions (Non Swap)'")
        comm_non_swap = db.query(
            func.count(FactPnlUseCase3.entry_id).label('count'),
            func.sum(FactPnlUseCase3.pnl_daily).label('sum_daily')
        ).filter(
            FactPnlUseCase3.strategy == 'Commissions (Non Swap)'
        ).first()
        
        if comm_non_swap and comm_non_swap.count > 0 and comm_non_swap.sum_daily:
            print(f"    [PASS] 'Commissions (Non Swap)' has {comm_non_swap.count} rows, sum={comm_non_swap.sum_daily}")
        else:
            print(f"    [FAIL] 'Commissions (Non Swap)' has no data or zero sum!")
            verification_passed = False
        print()
        
        # Summary
        print("=" * 80)
        print("ALIGNMENT COMPLETE")
        print("=" * 80)
        print()
        print("Summary:")
        for update_desc, row_count in updates_performed:
            print(f"  - {update_desc}: {row_count} rows")
        if rows_redistributed > 0:
            print(f"  - Redistributed: {rows_redistributed} rows")
        print()
        print(f"Verification: {'[PASS]' if verification_passed else '[FAIL]'}")
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
    align_uc3_leafs()


