"""
Data Alignment Script for Use Case 3
Aligns fact_pnl_use_case_3 data to match hierarchy metadata so rollup logic can match nodes.

This script:
1. Populates MTD/YTD values (pnl_commission, pnl_trade)
2. Aligns text values (strategy, product_line) to match hierarchy node names
3. Verifies the alignment
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

def align_uc3_data():
    """
    Align fact_pnl_use_case_3 data to match hierarchy metadata.
    """
    print("=" * 80)
    print("DATA ALIGNMENT: Use Case 3 Fact Table")
    print("=" * 80)
    print()
    
    db: Session = SessionLocal()
    
    try:
        # Step 1: Populate MTD/YTD values
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
        
        # Step 2: Align Text Values to Match Hierarchy Node Names
        print("STEP 2: Aligning Text Values to Match Hierarchy Node Names")
        print("-" * 80)
        
        # Get hierarchy node names for reference
        use_case_3 = db.query(UseCase).filter(
            UseCase.name.ilike('%America Cash Equity Trading%')
        ).first()
        
        if use_case_3:
            atlas_source = use_case_3.atlas_structure_id
            hierarchy_nodes = db.query(DimHierarchy).filter(
                DimHierarchy.atlas_source == atlas_source
            ).all()
            
            node_names = [n.node_name for n in hierarchy_nodes]
            print(f"  Hierarchy Node Names: {sorted(node_names)}")
            print()
        
        # Alignment Rule 1: Map process_2 to strategy for Commission nodes
        print("  Alignment Rule 1: Map process_2 -> strategy for Commissions")
        update_commissions = text("""
            UPDATE fact_pnl_use_case_3
            SET strategy = 'Commissions'
            WHERE process_2 IN ('SD COMMISSION', 'SWAP COMMISSION')
        """)
        result = db.execute(update_commissions)
        rows_commissions = result.rowcount
        db.commit()
        print(f"    [OK] Updated {rows_commissions} rows: process_2 (SD COMMISSION, SWAP COMMISSION) -> strategy='Commissions'")
        
        # Alignment Rule 2: Map process_2 to strategy for Trading nodes
        print("  Alignment Rule 2: Map process_2 -> strategy for Trading")
        update_trading = text("""
            UPDATE fact_pnl_use_case_3
            SET strategy = 'Trading'
            WHERE process_2 = 'Inventory Management'
        """)
        result = db.execute(update_trading)
        rows_trading = result.rowcount
        db.commit()
        print(f"    [OK] Updated {rows_trading} rows: process_2='Inventory Management' -> strategy='Trading'")
        
        # Alignment Rule 3: Map strategy 'CORE' to 'Core Ex CRB' (matches hierarchy node)
        print("  Alignment Rule 3: Map strategy 'CORE' -> 'Core Ex CRB'")
        update_core = text("""
            UPDATE fact_pnl_use_case_3
            SET strategy = 'Core Ex CRB'
            WHERE strategy = 'CORE'
        """)
        result = db.execute(update_core)
        rows_core = result.rowcount
        db.commit()
        print(f"    [OK] Updated {rows_core} rows: strategy='CORE' -> strategy='Core Ex CRB'")
        
        # Alignment Rule 4: Map product_line to match hierarchy node names
        # 'CORE Products' already matches 'NODE_2' (CORE Products), so keep it
        # But we can map other product lines to match if needed
        print("  Alignment Rule 4: Verify product_line alignment")
        print("    [INFO] 'CORE Products' already matches hierarchy node 'CORE Products'")
        print("    [INFO] Other product lines will be handled by rollup logic")
        print()
        
        # Step 3: Verify Alignment
        print("STEP 3: Verification")
        print("-" * 80)
        
        # Check distinct strategy values
        distinct_strategies = db.query(distinct(FactPnlUseCase3.strategy)).filter(
            FactPnlUseCase3.strategy.isnot(None)
        ).all()
        strategies = sorted([s[0] for s in distinct_strategies if s[0]])
        
        print(f"  Distinct Strategies ({len(strategies)}):")
        for strategy in strategies:
            count = db.query(func.count(FactPnlUseCase3.entry_id)).filter(
                FactPnlUseCase3.strategy == strategy
            ).scalar()
            sum_daily = db.query(func.sum(FactPnlUseCase3.pnl_daily)).filter(
                FactPnlUseCase3.strategy == strategy
            ).scalar()
            print(f"    - '{strategy}': {count} rows, sum_daily={sum_daily}")
        print()
        
        # Check distinct process_2 values
        distinct_processes = db.query(distinct(FactPnlUseCase3.process_2)).filter(
            FactPnlUseCase3.process_2.isnot(None)
        ).all()
        processes = sorted([p[0] for p in distinct_processes if p[0]])
        
        print(f"  Distinct Process_2 ({len(processes)}):")
        for process in processes:
            count = db.query(func.count(FactPnlUseCase3.entry_id)).filter(
                FactPnlUseCase3.process_2 == process
            ).scalar()
            print(f"    - '{process}': {count} rows")
        print()
        
        # Check distinct product_line values
        distinct_products = db.query(distinct(FactPnlUseCase3.product_line)).filter(
            FactPnlUseCase3.product_line.isnot(None)
        ).all()
        products = sorted([p[0] for p in distinct_products if p[0]])
        
        print(f"  Distinct Product_Line ({len(products)}):")
        for product in products:
            count = db.query(func.count(FactPnlUseCase3.entry_id)).filter(
                FactPnlUseCase3.product_line == product
            ).scalar()
            print(f"    - '{product}': {count} rows")
        print()
        
        # Verify MTD/YTD totals
        totals = db.query(
            func.sum(FactPnlUseCase3.pnl_daily).label('sum_daily'),
            func.sum(FactPnlUseCase3.pnl_commission).label('sum_commission'),
            func.sum(FactPnlUseCase3.pnl_trade).label('sum_trade')
        ).first()
        
        print("  MTD/YTD Totals:")
        print(f"    SUM(pnl_daily): {totals.sum_daily}")
        print(f"    SUM(pnl_commission): {totals.sum_commission}")
        print(f"    SUM(pnl_trade): {totals.sum_trade}")
        
        # Verify formulas
        expected_commission = Decimal(str(totals.sum_daily)) * Decimal('2.5')
        expected_trade = Decimal(str(totals.sum_daily)) * Decimal('10.0')
        commission_diff = abs(Decimal(str(totals.sum_commission)) - expected_commission)
        trade_diff = abs(Decimal(str(totals.sum_trade)) - expected_trade)
        
        if commission_diff < Decimal('0.01') and trade_diff < Decimal('0.01'):
            print("    [PASS] MTD/YTD formulas verified")
        else:
            print(f"    [WARNING] Formula verification: commission_diff={commission_diff}, trade_diff={trade_diff}")
        print()
        
        # Step 4: Compare with Hierarchy Node Names
        print("STEP 4: Comparison with Hierarchy Node Names")
        print("-" * 80)
        
        if use_case_3:
            print(f"  Use Case: {use_case_3.name}")
            print(f"  Atlas Source: {atlas_source}")
            print()
            
            # Check which strategies match hierarchy node names
            matching_strategies = []
            unmatched_strategies = []
            
            for strategy in strategies:
                # Check if strategy matches any node name (case-insensitive)
                matching_nodes = [
                    n for n in hierarchy_nodes 
                    if strategy.upper() in n.node_name.upper() or n.node_name.upper() in strategy.upper()
                ]
                if matching_nodes:
                    matching_strategies.append((strategy, [n.node_name for n in matching_nodes]))
                else:
                    unmatched_strategies.append(strategy)
            
            print(f"  Strategy Matching:")
            print(f"    [MATCHED] {len(matching_strategies)}/{len(strategies)}")
            for strategy, node_names in matching_strategies[:10]:
                print(f"      '{strategy}' -> {node_names}")
            if len(matching_strategies) > 10:
                print(f"      ... and {len(matching_strategies) - 10} more")
            
            if unmatched_strategies:
                print(f"    [UNMATCHED] {len(unmatched_strategies)}/{len(strategies)}")
                for strategy in unmatched_strategies[:10]:
                    print(f"      '{strategy}'")
                if len(unmatched_strategies) > 10:
                    print(f"      ... and {len(unmatched_strategies) - 10} more")
            print()
        
        print("=" * 80)
        print("ALIGNMENT COMPLETE")
        print("=" * 80)
        print()
        print("Summary:")
        print(f"  - Updated {rows_updated} rows with MTD/YTD values")
        print(f"  - Aligned {rows_commissions} rows for Commissions")
        print(f"  - Aligned {rows_trading} rows for Trading")
        print(f"  - Aligned {rows_core} rows for Core Ex CRB")
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
    align_uc3_data()

