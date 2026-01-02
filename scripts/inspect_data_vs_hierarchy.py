"""
Deep Inspection Script: Compare Fact Table Data vs Hierarchy Metadata
Diagnoses why Tab 2 is showing 0.00 for child nodes by comparing:
- Fact table values (strategy, process_2, product_line, cc_id)
- Hierarchy metadata (node_id, node_name, attributes)
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from app.database import SessionLocal
from app.models import (
    FactPnlUseCase3,
    FactPnlGold,
    DimHierarchy,
    UseCase
)

def inspect_use_case_3():
    """Inspect Use Case 3: America Cash Equity Trading Structure"""
    print("=" * 80)
    print("USE CASE 3: America Cash Equity Trading Structure")
    print("=" * 80)
    print()
    
    db: Session = SessionLocal()
    
    try:
        # Step 1: Query fact_pnl_use_case_3
        print("STEP 1: Fact Table Data (fact_pnl_use_case_3)")
        print("-" * 80)
        
        # Get distinct strategy values
        distinct_strategies = db.query(distinct(FactPnlUseCase3.strategy)).filter(
            FactPnlUseCase3.strategy.isnot(None)
        ).all()
        strategies = [s[0] for s in distinct_strategies if s[0]]
        
        # Get distinct process_2 values
        distinct_processes = db.query(distinct(FactPnlUseCase3.process_2)).filter(
            FactPnlUseCase3.process_2.isnot(None)
        ).all()
        processes = [p[0] for p in distinct_processes if p[0]]
        
        # Get distinct product_line values
        distinct_products = db.query(distinct(FactPnlUseCase3.product_line)).filter(
            FactPnlUseCase3.product_line.isnot(None)
        ).all()
        products = [p[0] for p in distinct_products if p[0]]
        
        # Get totals
        totals = db.query(
            func.count(FactPnlUseCase3.entry_id).label('row_count'),
            func.sum(FactPnlUseCase3.pnl_daily).label('sum_daily'),
            func.sum(FactPnlUseCase3.pnl_commission).label('sum_commission'),
            func.sum(FactPnlUseCase3.pnl_trade).label('sum_trade')
        ).first()
        
        print(f"  Total Rows: {totals.row_count}")
        print(f"  SUM(pnl_daily): {totals.sum_daily}")
        print(f"  SUM(pnl_commission): {totals.sum_commission}")
        print(f"  SUM(pnl_trade): {totals.sum_trade}")
        print()
        
        # Flag if MTD/YTD are 0
        if totals.sum_commission == 0 or totals.sum_trade == 0:
            print("  [WARNING] MTD/YTD columns are ZERO!")
            print(f"     - pnl_commission (MTD): {totals.sum_commission}")
            print(f"     - pnl_trade (YTD): {totals.sum_trade}")
            print()
        
        print(f"  Distinct Strategies ({len(strategies)}):")
        for strategy in sorted(strategies)[:20]:  # Show first 20
            # Get count and sum for this strategy
            strategy_stats = db.query(
                func.count(FactPnlUseCase3.entry_id).label('count'),
                func.sum(FactPnlUseCase3.pnl_daily).label('sum_daily')
            ).filter(FactPnlUseCase3.strategy == strategy).first()
            print(f"    - '{strategy}' ({strategy_stats.count} rows, sum={strategy_stats.sum_daily})")
        if len(strategies) > 20:
            print(f"    ... and {len(strategies) - 20} more")
        print()
        
        print(f"  Distinct Process_2 ({len(processes)}):")
        for process in sorted(processes)[:20]:
            process_stats = db.query(
                func.count(FactPnlUseCase3.entry_id).label('count'),
                func.sum(FactPnlUseCase3.pnl_daily).label('sum_daily')
            ).filter(FactPnlUseCase3.process_2 == process).first()
            print(f"    - '{process}' ({process_stats.count} rows, sum={process_stats.sum_daily})")
        if len(processes) > 20:
            print(f"    ... and {len(processes) - 20} more")
        print()
        
        print(f"  Distinct Product_Line ({len(products)}):")
        for product in sorted(products)[:20]:
            product_stats = db.query(
                func.count(FactPnlUseCase3.entry_id).label('count'),
                func.sum(FactPnlUseCase3.pnl_daily).label('sum_daily')
            ).filter(FactPnlUseCase3.product_line == product).first()
            print(f"    - '{product}' ({product_stats.count} rows, sum={product_stats.sum_daily})")
        if len(products) > 20:
            print(f"    ... and {len(products) - 20} more")
        print()
        
        # Step 2: Query dim_hierarchy for Use Case 3
        print("STEP 2: Hierarchy Metadata (dim_hierarchy)")
        print("-" * 80)
        
        # Find Use Case 3
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
        
        # Get hierarchy nodes
        hierarchy_nodes = db.query(DimHierarchy).filter(
            DimHierarchy.atlas_source == atlas_source
        ).order_by(DimHierarchy.depth, DimHierarchy.node_name).all()
        
        print(f"  Total Hierarchy Nodes: {len(hierarchy_nodes)}")
        print()
        
        # Show specific nodes mentioned in requirements
        target_nodes = ['CORE Products', 'Commissions', 'Trading', 'Core Ex CRB']
        print("  Target Nodes (for matching):")
        for target_name in target_nodes:
            matching_nodes = [n for n in hierarchy_nodes if target_name.upper() in n.node_name.upper()]
            if matching_nodes:
                for node in matching_nodes:
                    print(f"    - node_id: '{node.node_id}', node_name: '{node.node_name}', is_leaf: {node.is_leaf}")
            else:
                print(f"    - ❌ NOT FOUND: '{target_name}'")
        print()
        
        # Show all leaf nodes
        leaf_nodes = [n for n in hierarchy_nodes if n.is_leaf]
        print(f"  Leaf Nodes ({len(leaf_nodes)}):")
        for node in leaf_nodes[:30]:  # Show first 30
            print(f"    - node_id: '{node.node_id}', node_name: '{node.node_name}'")
        if len(leaf_nodes) > 30:
            print(f"    ... and {len(leaf_nodes) - 30} more")
        print()
        
        # Step 3: Compare Fact Table vs Hierarchy
        print("STEP 3: Comparison Analysis")
        print("-" * 80)
        
        # Check if strategy values match node_ids
        print("  Strategy Matching:")
        matched_strategies = []
        unmatched_strategies = []
        
        for strategy in strategies:
            # Check if strategy matches any node_id or node_name
            matching_nodes = [
                n for n in hierarchy_nodes 
                if n.node_id == strategy or strategy.upper() in n.node_name.upper()
            ]
            if matching_nodes:
                matched_strategies.append((strategy, [n.node_id for n in matching_nodes]))
            else:
                unmatched_strategies.append(strategy)
        
        print(f"    [MATCHED] {len(matched_strategies)}/{len(strategies)}")
        for strategy, node_ids in matched_strategies[:10]:
            print(f"      '{strategy}' -> {node_ids}")
        if len(matched_strategies) > 10:
            print(f"      ... and {len(matched_strategies) - 10} more")
        
        if unmatched_strategies:
            print(f"    [UNMATCHED] {len(unmatched_strategies)}/{len(strategies)}")
            for strategy in unmatched_strategies[:10]:
                print(f"      '{strategy}'")
            if len(unmatched_strategies) > 10:
                print(f"      ... and {len(unmatched_strategies) - 10} more")
        print()
        
        # Check if product_line values match node_ids
        print("  Product_Line Matching:")
        matched_products = []
        unmatched_products = []
        
        for product in products:
            matching_nodes = [
                n for n in hierarchy_nodes 
                if n.node_id == product or product.upper() in n.node_name.upper()
            ]
            if matching_nodes:
                matched_products.append((product, [n.node_id for n in matching_nodes]))
            else:
                unmatched_products.append(product)
        
        print(f"    [MATCHED] {len(matched_products)}/{len(products)}")
        for product, node_ids in matched_products[:10]:
            print(f"      '{product}' -> {node_ids}")
        if len(matched_products) > 10:
            print(f"      ... and {len(matched_products) - 10} more")
        
        if unmatched_products:
            print(f"    [UNMATCHED] {len(unmatched_products)}/{len(products)}")
            for product in unmatched_products[:10]:
                print(f"      '{product}'")
            if len(unmatched_products) > 10:
                print(f"      ... and {len(unmatched_products) - 10} more")
        print()
        
    except Exception as e:
        print(f"[ERROR] Use Case 3 inspection failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def inspect_use_case_1():
    """Inspect Use Case 1: Mock Atlas Structure v1 (Legacy)"""
    print()
    print("=" * 80)
    print("USE CASE 1: Mock Atlas Structure v1 (Legacy)")
    print("=" * 80)
    print()
    
    db: Session = SessionLocal()
    
    try:
        # Step 1: Query fact_pnl_gold
        print("STEP 1: Fact Table Data (fact_pnl_gold)")
        print("-" * 80)
        
        total_rows = db.query(func.count(FactPnlGold.fact_id)).scalar()
        print(f"  Total Rows: {total_rows}")
        
        # Get top 5 cc_id values
        top_cc_ids = db.query(
            FactPnlGold.cc_id,
            func.count(FactPnlGold.fact_id).label('count'),
            func.sum(FactPnlGold.daily_pnl).label('sum_daily')
        ).group_by(FactPnlGold.cc_id).order_by(func.count(FactPnlGold.fact_id).desc()).limit(5).all()
        
        print(f"  Top 5 cc_id values:")
        for cc_id, count, sum_daily in top_cc_ids:
            print(f"    - '{cc_id}': {count} rows, sum_daily={sum_daily}")
        print()
        
        # Get all distinct cc_ids
        distinct_cc_ids = db.query(distinct(FactPnlGold.cc_id)).all()
        cc_ids = [c[0] for c in distinct_cc_ids if c[0]]
        print(f"  Total Distinct cc_ids: {len(cc_ids)}")
        if len(cc_ids) <= 20:
            print(f"  All cc_ids: {sorted(cc_ids)}")
        else:
            print(f"  First 20 cc_ids: {sorted(cc_ids)[:20]}")
            print(f"  ... and {len(cc_ids) - 20} more")
        print()
        
        # Step 2: Query dim_hierarchy for Use Case 1
        print("STEP 2: Hierarchy Metadata (dim_hierarchy)")
        print("-" * 80)
        
        # Find Use Case 1
        use_case_1 = db.query(UseCase).filter(
            UseCase.name.ilike('%America Trading P&L%')
        ).first()
        
        if not use_case_1:
            # Try alternative name
            use_case_1 = db.query(UseCase).filter(
                UseCase.atlas_structure_id == 'Mock Atlas Structure v1'
            ).first()
        
        if not use_case_1:
            print("  [ERROR] Use Case 1 not found!")
            return
        
        atlas_source = use_case_1.atlas_structure_id
        print(f"  Use Case: {use_case_1.name}")
        print(f"  Atlas Source: {atlas_source}")
        print()
        
        # Get hierarchy nodes
        hierarchy_nodes = db.query(DimHierarchy).filter(
            DimHierarchy.atlas_source == atlas_source
        ).order_by(DimHierarchy.depth, DimHierarchy.node_name).all()
        
        print(f"  Total Hierarchy Nodes: {len(hierarchy_nodes)}")
        print()
        
        # Show specific nodes mentioned in requirements
        target_nodes = ['Americas', 'Cash Equities']
        print("  Target Nodes (for matching):")
        for target_name in target_nodes:
            matching_nodes = [n for n in hierarchy_nodes if target_name.upper() in n.node_name.upper()]
            if matching_nodes:
                for node in matching_nodes:
                    print(f"    - node_id: '{node.node_id}', node_name: '{node.node_name}', is_leaf: {node.is_leaf}")
            else:
                print(f"    - ❌ NOT FOUND: '{target_name}'")
        print()
        
        # Show all leaf nodes
        leaf_nodes = [n for n in hierarchy_nodes if n.is_leaf]
        print(f"  Leaf Nodes ({len(leaf_nodes)}):")
        for node in leaf_nodes[:30]:
            print(f"    - node_id: '{node.node_id}', node_name: '{node.node_name}'")
        if len(leaf_nodes) > 30:
            print(f"    ... and {len(leaf_nodes) - 30} more")
        print()
        
        # Step 3: Compare Fact Table vs Hierarchy
        print("STEP 3: Comparison Analysis")
        print("-" * 80)
        
        # Check if cc_id values match node_ids
        print("  cc_id Matching:")
        matched_cc_ids = []
        unmatched_cc_ids = []
        
        for cc_id in cc_ids:
            # Check if cc_id matches any node_id
            matching_nodes = [n for n in hierarchy_nodes if n.node_id == cc_id]
            if matching_nodes:
                matched_cc_ids.append((cc_id, [n.node_id for n in matching_nodes]))
            else:
                unmatched_cc_ids.append(cc_id)
        
        print(f"    [MATCHED] {len(matched_cc_ids)}/{len(cc_ids)}")
        for cc_id, node_ids in matched_cc_ids[:10]:
            print(f"      '{cc_id}' -> {node_ids}")
        if len(matched_cc_ids) > 10:
            print(f"      ... and {len(matched_cc_ids) - 10} more")
        
        if unmatched_cc_ids:
            print(f"    [UNMATCHED] {len(unmatched_cc_ids)}/{len(cc_ids)}")
            for cc_id in unmatched_cc_ids[:10]:
                print(f"      '{cc_id}'")
            if len(unmatched_cc_ids) > 10:
                print(f"      ... and {len(unmatched_cc_ids) - 10} more")
        print()
        
    except Exception as e:
        print(f"[ERROR] Use Case 1 inspection failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def main():
    """Main inspection function"""
    print("\n" + "=" * 80)
    print("DEEP INSPECTION: Fact Table Data vs Hierarchy Metadata")
    print("=" * 80)
    print()
    
    # Inspect Use Case 3
    inspect_use_case_3()
    
    # Inspect Use Case 1
    inspect_use_case_1()
    
    print()
    print("=" * 80)
    print("INSPECTION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()

