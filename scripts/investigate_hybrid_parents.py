"""
Investigate Hybrid Parents: Parent nodes that also have direct rows in fact table
Focus: Core Ex CRB, Commissions, Trading, CORE Products
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine

def main():
    print("=" * 80)
    print("INVESTIGATING HYBRID PARENTS")
    print("=" * 80)
    print()
    print("Hybrid Parent = Parent node that also has direct rows in fact table")
    print()
    
    with engine.connect() as conn:
        uc3_id = 'fce60983-0328-496b-b6e1-34249ec5aa5a'
        
        # Step 1: Check direct P&L for suspected parent strategies
        print("Step 1: Checking direct P&L for parent strategies...")
        print()
        
        target_strategies = ['Core Ex CRB', 'Commissions', 'Trading', 'CORE Products']
        
        result = conn.execute(text("""
            SELECT 
                strategy,
                COUNT(*) as row_count,
                SUM(pnl_daily) as direct_pnl,
                SUM(pnl_commission) as direct_commission,
                SUM(pnl_trade) as direct_trade
            FROM fact_pnl_use_case_3
            WHERE strategy IN :strategies
            GROUP BY strategy
            ORDER BY strategy
        """), {"strategies": tuple(target_strategies)})
        
        direct_rows = result.fetchall()
        print(f"[DIRECT ROWS] Found direct rows for {len(direct_rows)} strategies:")
        direct_pnl_dict = {}
        total_direct_pnl = 0
        for row in direct_rows:
            strategy, row_count, direct_pnl, direct_commission, direct_trade = row
            direct_pnl = direct_pnl or 0
            direct_pnl_dict[strategy] = direct_pnl
            total_direct_pnl += direct_pnl
            print(f"   {strategy}:")
            print(f"      Rows: {row_count}")
            print(f"      Direct Daily P&L: {direct_pnl:,.2f}")
            print(f"      Direct Commission: {direct_commission or 0:,.2f}")
            print(f"      Direct Trade: {direct_trade or 0:,.2f}")
            print()
        
        # Check which strategies don't have direct rows
        strategies_without_direct = [s for s in target_strategies if s not in direct_pnl_dict]
        if strategies_without_direct:
            print(f"[NO DIRECT ROWS] These strategies have no direct rows:")
            for strategy in strategies_without_direct:
                print(f"   - {strategy}")
            print()
        
        print(f"[TOTAL DIRECT P&L] Sum of direct P&L for these strategies: {total_direct_pnl:,.2f}")
        print()
        
        # Step 2: Check if these are parent nodes in hierarchy
        print("Step 2: Checking hierarchy structure for these nodes...")
        print()
        
        result = conn.execute(text("""
            SELECT 
                node_id,
                node_name,
                parent_node_id,
                is_leaf,
                depth
            FROM dim_hierarchy
            WHERE node_name IN :strategies
            ORDER BY node_name
        """), {"strategies": tuple(target_strategies)})
        
        hierarchy_nodes = result.fetchall()
        print(f"[HIERARCHY NODES] Found {len(hierarchy_nodes)} nodes in hierarchy:")
        hybrid_parents = []
        for row in hierarchy_nodes:
            node_id, node_name, parent_id, is_leaf, depth = row
            has_direct = node_name in direct_pnl_dict
            is_parent = not is_leaf
            
            print(f"   {node_id} ('{node_name}'):")
            print(f"      Parent: {parent_id}, Leaf: {is_leaf}, Depth: {depth}")
            print(f"      Has Direct Rows: {has_direct}")
            print(f"      Is Parent Node: {is_parent}")
            
            if is_parent and has_direct:
                hybrid_parents.append((node_id, node_name, direct_pnl_dict[node_name]))
                print(f"      [HYBRID PARENT CONFIRMED]")
            print()
        
        # Step 3: Get children for each hybrid parent
        print("Step 3: Analyzing hybrid parents and their children...")
        print()
        
        total_hybrid_direct_pnl = 0
        for node_id, node_name, direct_pnl in hybrid_parents:
            print(f"[HYBRID PARENT] {node_name} ({node_id}):")
            print(f"   Direct P&L: {direct_pnl:,.2f}")
            print()
            
            # Get children
            result = conn.execute(text("""
                SELECT 
                    node_id,
                    node_name,
                    is_leaf,
                    depth
                FROM dim_hierarchy
                WHERE parent_node_id = :node_id
                ORDER BY node_name
            """), {"node_id": node_id})
            
            children = result.fetchall()
            if children:
                print(f"   Children ({len(children)}):")
                for child in children:
                    child_id, child_name, child_is_leaf, child_depth = child
                    print(f"      - {child_id} ('{child_name}'): leaf={child_is_leaf}, depth={child_depth}")
                print()
                
                # Check if children have direct rows
                child_names = [c[1] for c in children]
                result = conn.execute(text("""
                    SELECT 
                        strategy,
                        SUM(pnl_daily) as direct_pnl
                    FROM fact_pnl_use_case_3
                    WHERE strategy IN :child_names
                    GROUP BY strategy
                """), {"child_names": tuple(child_names)})
                
                child_direct = {row[0]: row[1] or 0 for row in result.fetchall()}
                total_child_direct = sum(child_direct.values())
                
                print(f"   Children Direct P&L: {total_child_direct:,.2f}")
                print(f"   Parent Direct P&L: {direct_pnl:,.2f}")
                print(f"   Total (Parent + Children): {direct_pnl + total_child_direct:,.2f}")
                print()
                
                # Check if parent direct + children direct = parent natural
                # This would indicate double counting risk
                if abs(direct_pnl + total_child_direct - direct_pnl) > 0.01:
                    print(f"   [ANALYSIS]")
                    print(f"      If parent Natural = parent direct ({direct_pnl:,.2f})")
                    print(f"      And children Natural = children direct ({total_child_direct:,.2f})")
                    print(f"      Then parent Natural should = {direct_pnl + total_child_direct:,.2f}")
                    print(f"      But if parent Natural only includes direct, children are missing!")
                    print()
            
            total_hybrid_direct_pnl += direct_pnl
        
        print(f"[TOTAL HYBRID DIRECT P&L] Sum: {total_hybrid_direct_pnl:,.2f}")
        print()
        
        # Step 4: Compare with plug discrepancy
        print("Step 4: Comparing with plug discrepancy...")
        print()
        expected_plug = 19999.79
        actual_plug = 151547.79
        plug_discrepancy = actual_plug - expected_plug
        print(f"   Expected Plug: {expected_plug:,.2f}")
        print(f"   Actual Plug: {actual_plug:,.2f}")
        print(f"   Discrepancy: {plug_discrepancy:,.2f}")
        print()
        print(f"   Hybrid Parents Direct P&L: {total_hybrid_direct_pnl:,.2f}")
        
        if abs(float(total_hybrid_direct_pnl) - plug_discrepancy) < 1.0:
            print(f"   [MATCH] Hybrid parents direct P&L matches plug discrepancy!")
            print(f"   [ROOT CAUSE] Hybrid parents' direct rows are included in ROOT Natural")
            print(f"                but NOT in ROOT Adjusted (which only sums children)")
        elif total_hybrid_direct_pnl > 0:
            print(f"   [PARTIAL] Hybrid parents explain {total_hybrid_direct_pnl:,.2f} of {plug_discrepancy:,.2f}")
            print(f"   Remaining: {plug_discrepancy - total_hybrid_direct_pnl:,.2f}")
        else:
            print(f"   [NO MATCH] Hybrid parents don't explain the discrepancy")
        
        print()
        
        # Step 5: Check latest calculation results
        print("Step 5: Checking latest calculation results for these nodes...")
        print()
        
        for node_id, node_name, direct_pnl in hybrid_parents:
            result = conn.execute(text("""
                SELECT 
                    fcr.measure_vector->>'daily' as adjusted_daily,
                    fcr.plug_vector->>'daily' as plug_daily,
                    fcr.is_override,
                    ucr.run_timestamp
                FROM fact_calculated_results fcr
                JOIN use_case_runs ucr ON fcr.run_id = ucr.run_id
                WHERE fcr.node_id = :node_id
                  AND ucr.use_case_id = :uc3_id
                  AND ucr.run_timestamp = (
                      SELECT MAX(run_timestamp)
                      FROM use_case_runs
                      WHERE use_case_id = :uc3_id
                  )
            """), {"node_id": node_id, "uc3_id": str(uc3_id)})
            
            calc_result = result.fetchone()
            if calc_result:
                adjusted_daily, plug_daily, is_override, run_timestamp = calc_result
                adjusted_daily = float(adjusted_daily) if adjusted_daily else 0.0
                plug_daily = float(plug_daily) if plug_daily else 0.0
                
                print(f"   {node_name} ({node_id}):")
                print(f"      Direct P&L (from facts): {direct_pnl:,.2f}")
                print(f"      Adjusted P&L (calculated): {adjusted_daily:,.2f}")
                print(f"      Plug: {plug_daily:,.2f}")
                print(f"      Has Rule: {is_override}")
                
                # Calculate expected natural
                expected_natural = adjusted_daily + plug_daily
                print(f"      Expected Natural (Adjusted + Plug): {expected_natural:,.2f}")
                
                if abs(float(direct_pnl) - expected_natural) < 1.0:
                    print(f"      [MATCH] Direct P&L matches Expected Natural")
                else:
                    print(f"      [MISMATCH] Direct P&L ({direct_pnl:,.2f}) != Expected Natural ({expected_natural:,.2f})")
                    print(f"      Difference: {abs(float(direct_pnl) - expected_natural):,.2f}")
                print()
        
        # Step 6: Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print()
        print(f"Hybrid Parents Found: {len(hybrid_parents)}")
        for node_id, node_name, direct_pnl in hybrid_parents:
            print(f"   - {node_name} ({node_id}): Direct P&L = {direct_pnl:,.2f}")
        print()
        print(f"Total Hybrid Direct P&L: {total_hybrid_direct_pnl:,.2f}")
        print(f"Plug Discrepancy: {plug_discrepancy:,.2f}")
        print()
        
        if total_hybrid_direct_pnl > 0:
            print("[HYPOTHESIS]")
            print("   If hybrid parents have direct rows:")
            print("   1. ROOT Natural includes these direct rows (sum of ALL facts)")
            print("   2. ROOT Adjusted = sum of children (excludes parent direct rows)")
            print("   3. Plug = Natural - Adjusted = parent direct rows")
            print("   4. This creates the reconciliation break")
            print()
            print("[SOLUTION]")
            print("   For hybrid parents, Adjusted should = direct + sum(children)")
            print("   OR Natural should exclude parent direct rows (only sum children)")
        
        return 0

if __name__ == "__main__":
    exit(main())

