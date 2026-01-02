"""
Diagnostic Script for Use Case 1 - Parent Node Aggregation Issue
Checks why parent nodes like "Americas Program Trading", "EMEA Index Arbitrage", 
and "APAC Algorithmic G1" are showing 0.00 despite having leaf children with data.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import SessionLocal
from app.models import FactPnlGold, DimHierarchy, UseCase
from app.services.unified_pnl_service import _calculate_legacy_rollup
from app.engine.waterfall import load_hierarchy

def diagnose_uc1_parent_aggregation():
    """
    Diagnose why parent nodes are showing 0.00.
    """
    print("=" * 80)
    print("DIAGNOSTIC: Use Case 1 - Parent Node Aggregation")
    print("=" * 80)
    print()
    
    db: Session = SessionLocal()
    
    try:
        # Step 1: Find Use Case 1
        print("STEP 1: Finding Use Case 1")
        print("-" * 80)
        
        use_case = db.query(UseCase).filter(
            UseCase.name.ilike('%America Trading%')
        ).first()
        
        if not use_case:
            print("  [ERROR] Use Case 1 (America Trading P&L) not found!")
            return
        
        print(f"  Use Case: {use_case.name}")
        print(f"  Use Case ID: {use_case.use_case_id}")
        print(f"  Atlas Source: {use_case.atlas_structure_id}")
        print()
        
        # Step 2: Load Hierarchy
        print("STEP 2: Loading Hierarchy")
        print("-" * 80)
        
        hierarchy_dict, children_dict, leaf_nodes = load_hierarchy(db, use_case.use_case_id)
        
        print(f"  Total nodes: {len(hierarchy_dict)}")
        print(f"  Leaf nodes: {len(leaf_nodes)}")
        print()
        
        # Step 3: Check Target Parent Nodes
        print("STEP 3: Checking Target Parent Nodes")
        print("-" * 80)
        
        target_parent_names = [
            'Americas Program Trading',
            'EMEA Index Arbitrage',
            'APAC Algorithmic G1'
        ]
        
        target_parents = {}
        for node_id, node in hierarchy_dict.items():
            if node.node_name in target_parent_names:
                target_parents[node_id] = node
                print(f"  Found: {node_id} ({node.node_name})")
                print(f"    is_leaf: {node.is_leaf}")
                print(f"    depth: {node.depth}")
                print(f"    parent_node_id: {node.parent_node_id}")
        
        print()
        
        # Step 4: Check Children of Target Parents
        print("STEP 4: Checking Children of Target Parents")
        print("-" * 80)
        
        for parent_id, parent_node in target_parents.items():
            children = children_dict.get(parent_id, [])
            print(f"  {parent_node.node_name} ({parent_id}):")
            print(f"    Number of children: {len(children)}")
            
            for child_id in children:
                child_node = hierarchy_dict.get(child_id)
                if child_node:
                    print(f"      - {child_id} ({child_node.node_name}) - is_leaf={child_node.is_leaf}")
                    
                    # Check if this child has data in fact_pnl_gold
                    if child_node.is_leaf:
                        fact_sum = db.query(func.sum(FactPnlGold.daily_pnl)).filter(
                            FactPnlGold.cc_id == child_id
                        ).scalar()
                        fact_sum = Decimal(str(fact_sum or 0))
                        fact_count = db.query(func.count(FactPnlGold.fact_id)).filter(
                            FactPnlGold.cc_id == child_id
                        ).scalar()
                        print(f"        fact_pnl_gold: {fact_count} rows, SUM(daily_pnl)={fact_sum}")
            print()
        
        # Step 5: Run Legacy Rollup and Check Results
        print("STEP 5: Running Legacy Rollup")
        print("-" * 80)
        
        rollup_results = _calculate_legacy_rollup(
            db, use_case.use_case_id, hierarchy_dict, children_dict, leaf_nodes
        )
        
        print()
        print("STEP 6: Checking Rollup Results for Target Parents")
        print("-" * 80)
        
        for parent_id, parent_node in target_parents.items():
            result = rollup_results.get(parent_id, {})
            daily = result.get('daily', Decimal('0'))
            mtd = result.get('mtd', Decimal('0'))
            ytd = result.get('ytd', Decimal('0'))
            
            print(f"  {parent_node.node_name} ({parent_id}):")
            print(f"    daily: {daily}")
            print(f"    mtd: {mtd}")
            print(f"    ytd: {ytd}")
            
            # Check children's values
            children = children_dict.get(parent_id, [])
            if children:
                child_daily_sum = sum(rollup_results.get(child_id, {}).get('daily', Decimal('0')) for child_id in children)
                child_mtd_sum = sum(rollup_results.get(child_id, {}).get('mtd', Decimal('0')) for child_id in children)
                child_ytd_sum = sum(rollup_results.get(child_id, {}).get('ytd', Decimal('0')) for child_id in children)
                
                print(f"    Sum of children:")
                print(f"      daily: {child_daily_sum}")
                print(f"      mtd: {child_mtd_sum}")
                print(f"      ytd: {child_ytd_sum}")
                
                if daily == Decimal('0') and child_daily_sum != Decimal('0'):
                    print(f"    [ISSUE] Parent shows 0.00 but children sum to {child_daily_sum}")
                elif daily == child_daily_sum:
                    print(f"    [OK] Parent correctly aggregates from children")
                else:
                    print(f"    [WARNING] Parent value ({daily}) doesn't match children sum ({child_daily_sum})")
            print()
        
        print("=" * 80)
        print("DIAGNOSTIC COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    diagnose_uc1_parent_aggregation()

