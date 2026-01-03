"""
Analyze Reconciliation Plug calculation issue
Top-level plug shows 151,547.79 but should be 19,999.79
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine
from decimal import Decimal

def main():
    print("=" * 80)
    print("ANALYZING RECONCILIATION PLUG CALCULATION")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        uc3_id = 'fce60983-0328-496b-b6e1-34249ec5aa5a'
        
        # Step 1: Get latest calculation results
        print("Step 1: Fetching latest calculation results...")
        result = conn.execute(text("""
            SELECT 
                fcr.node_id,
                h.node_name,
                h.parent_node_id,
                h.depth,
                h.is_leaf,
                fcr.measure_vector->>'daily' as adjusted_daily,
                fcr.plug_vector->>'daily' as plug_daily,
                fcr.is_override,
                ucr.run_timestamp
            FROM fact_calculated_results fcr
            JOIN use_case_runs ucr ON fcr.run_id = ucr.run_id
            JOIN dim_hierarchy h ON fcr.node_id = h.node_id
            WHERE ucr.use_case_id = :uc3_id
              AND ucr.run_timestamp = (
                  SELECT MAX(run_timestamp)
                  FROM use_case_runs
                  WHERE use_case_id = :uc3_id
              )
            ORDER BY h.depth, h.node_name
        """), {"uc3_id": str(uc3_id)})
        
        all_results = result.fetchall()
        print(f"[OK] Found {len(all_results)} result rows from latest calculation")
        print()
        
        # Step 2: Build hierarchy structure and calculate expected values
        print("Step 2: Analyzing plug values by hierarchy level...")
        print()
        
        results_dict = {}
        for row in all_results:
            node_id, node_name, parent_id, depth, is_leaf, adjusted_daily, plug_daily, is_override, run_timestamp = row
            results_dict[node_id] = {
                'node_name': node_name,
                'parent_id': parent_id,
                'depth': depth,
                'is_leaf': is_leaf,
                'adjusted_daily': float(adjusted_daily) if adjusted_daily else 0.0,
                'plug_daily': float(plug_daily) if plug_daily else 0.0,
                'is_override': is_override
            }
        
        # Get children mapping
        result = conn.execute(text("""
            SELECT parent_node_id, node_id, node_name
            FROM dim_hierarchy
            WHERE use_case_id = :uc3_id
            ORDER BY parent_node_id, node_name
        """), {"uc3_id": str(uc3_id)})
        
        children_dict = {}
        for row in result.fetchall():
            parent_id, child_id, child_name = row
            if parent_id not in children_dict:
                children_dict[parent_id] = []
            children_dict[parent_id].append(child_id)
        
        # Step 3: Calculate expected plugs by summing children
        print("[PLUG ANALYSIS]")
        print()
        
        # Find root node (CORE Products)
        root_nodes = [node_id for node_id, data in results_dict.items() if data['parent_id'] is None]
        if not root_nodes:
            # Try to find by name
            for node_id, data in results_dict.items():
                if 'CORE Products' in data['node_name'] or data['depth'] == 0:
                    root_nodes = [node_id]
                    break
        
        if root_nodes:
            root_id = root_nodes[0]
            root_data = results_dict[root_id]
            print(f"[ROOT NODE] {root_id} ('{root_data['node_name']}'):")
            print(f"   Adjusted Daily P&L: {root_data['adjusted_daily']:,.2f}")
            print(f"   Plug Daily: {root_data['plug_daily']:,.2f}")
            print()
            
            # Calculate sum of children plugs
            def sum_children_plugs(node_id):
                children = children_dict.get(node_id, [])
                if not children:
                    return results_dict.get(node_id, {}).get('plug_daily', 0.0)
                
                total = 0.0
                for child_id in children:
                    if child_id in results_dict:
                        child_plug = results_dict[child_id]['plug_daily']
                        total += child_plug
                        print(f"      + {results_dict[child_id]['node_name']} ({child_id}): plug = {child_plug:,.2f}")
                
                return total
            
            print(f"[EXPECTED PLUG] Sum of all child plugs:")
            expected_plug = sum_children_plugs(root_id)
            print(f"   Expected Plug: {expected_plug:,.2f}")
            print(f"   Actual Plug: {root_data['plug_daily']:,.2f}")
            print(f"   Difference: {root_data['plug_daily'] - expected_plug:,.2f}")
            print()
        
        # Step 4: Show all nodes with non-zero plugs
        print("[NODES WITH NON-ZERO PLUGS]")
        nodes_with_plugs = [(node_id, data) for node_id, data in results_dict.items() if abs(data['plug_daily']) > 0.01]
        nodes_with_plugs.sort(key=lambda x: x[1]['depth'])
        
        if nodes_with_plugs:
            total_plug_sum = 0.0
            for node_id, data in nodes_with_plugs:
                print(f"   {node_id} ('{data['node_name']}'):")
                print(f"      Depth: {data['depth']}, Leaf: {data['is_leaf']}")
                print(f"      Adjusted: {data['adjusted_daily']:,.2f}")
                print(f"      Plug: {data['plug_daily']:,.2f}")
                print(f"      Has Rule: {data['is_override']}")
                total_plug_sum += data['plug_daily']
                print()
            
            print(f"[TOTAL PLUG SUM] Sum of all non-zero plugs: {total_plug_sum:,.2f}")
            print()
        else:
            print("   No nodes with non-zero plugs found")
            print()
        
        # Step 5: Check how Original P&L is calculated
        print("[ORIGINAL P&L ANALYSIS]")
        print("   Checking if Original = Adjusted + Plug for each node...")
        print()
        
        # We need to get Original from natural_results or calculate it
        # For now, let's check the relationship: Original = Adjusted + Plug
        mismatches = []
        for node_id, data in results_dict.items():
            # Original should be Adjusted + Plug
            calculated_original = data['adjusted_daily'] + data['plug_daily']
            
            # We don't have Original in the results, but we can verify the relationship
            # If plug is calculated correctly, Original = Adjusted + Plug
            print(f"   {data['node_name']} ({node_id}):")
            print(f"      Adjusted: {data['adjusted_daily']:,.2f}")
            print(f"      Plug: {data['plug_daily']:,.2f}")
            print(f"      Calculated Original (Adjusted + Plug): {calculated_original:,.2f}")
            if abs(data['plug_daily']) > 0.01:
                print(f"      [HAS PLUG]")
            print()
        
        # Step 6: Check parent-child relationships for plugs
        print("[PARENT-CHILD PLUG RELATIONSHIPS]")
        print("   Checking if parent plug = sum of child plugs...")
        print()
        
        # Process by depth (deepest first)
        max_depth = max(data['depth'] for data in results_dict.values())
        for depth in range(max_depth, -1, -1):
            for node_id, data in results_dict.items():
                if data['depth'] == depth and not data['is_leaf']:
                    children = children_dict.get(node_id, [])
                    if children:
                        child_plugs_sum = sum(
                            results_dict.get(child_id, {}).get('plug_daily', 0.0)
                            for child_id in children
                            if child_id in results_dict
                        )
                        parent_plug = data['plug_daily']
                        
                        print(f"   {data['node_name']} ({node_id}):")
                        print(f"      Parent Plug: {parent_plug:,.2f}")
                        print(f"      Sum of Child Plugs: {child_plugs_sum:,.2f}")
                        if abs(parent_plug - child_plugs_sum) > 0.01:
                            print(f"      [MISMATCH] Difference: {parent_plug - child_plugs_sum:,.2f}")
                            mismatches.append((node_id, data['node_name'], parent_plug, child_plugs_sum))
                        else:
                            print(f"      [MATCH]")
                        print()
        
        # Step 7: Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print()
        
        if mismatches:
            print("[ISSUES FOUND]")
            for node_id, node_name, parent_plug, child_sum in mismatches:
                print(f"   {node_name} ({node_id}):")
                print(f"      Parent Plug: {parent_plug:,.2f}")
                print(f"      Sum of Children: {child_sum:,.2f}")
                print(f"      Difference: {parent_plug - child_sum:,.2f}")
                print()
            
            print("[ROOT CAUSE HYPOTHESIS]")
            print("   The plug calculation might be:")
            print("   1. Using Original - Adjusted at each level (correct)")
            print("   2. But Original at parent level might be calculated differently")
            print("   3. OR Adjusted at parent level might not be sum of children")
            print()
            print("   Check:")
            print("   - Is parent Original = sum of child Originals?")
            print("   - Is parent Adjusted = sum of child Adjusted?")
            print("   - If both are true, then parent Plug = sum of child Plugs")
            print("   - If not, there's a calculation mismatch")
        else:
            print("[OK] All parent plugs match sum of child plugs")
        
        return 0

if __name__ == "__main__":
    exit(main())

