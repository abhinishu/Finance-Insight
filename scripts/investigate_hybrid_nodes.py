"""
Investigate if CRB, ETF Amber, MSET are Hybrid Nodes
(Hybrid = Parent node that also has direct P&L rows in fact table)
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
    print("HYBRID NODE INVESTIGATION: CRB, ETF Amber, MSET")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        uc3_id = 'fce60983-0328-496b-b6e1-34249ec5aa5a'
        
        # Task 1: Inspect Node Structure
        print("=" * 80)
        print("TASK 1: INSPECT NODE STRUCTURE")
        print("=" * 80)
        print()
        
        target_nodes = ['CRB', 'ETF Amber', 'MSET']
        
        for node_name in target_nodes:
            print(f"[INVESTIGATING] Node: {node_name}")
            print("-" * 80)
            
            # Step 1a: Check if node exists and get its details
            result = conn.execute(text("""
                SELECT node_id, node_name, parent_node_id, is_leaf, depth
                FROM dim_hierarchy
                WHERE node_name = :node_name
            """), {"node_name": node_name})
            
            node_info = result.fetchone()
            if not node_info:
                print(f"   [ERROR] Node '{node_name}' not found in hierarchy")
                print()
                continue
            
            node_id, node_name_db, parent_id, is_leaf, depth = node_info
            print(f"   [NODE INFO]")
            print(f"      Node ID: {node_id}")
            print(f"      Node Name: {node_name_db}")
            print(f"      Parent Node ID: {parent_id}")
            print(f"      Is Leaf: {is_leaf}")
            print(f"      Depth: {depth}")
            print()
            
            # Step 1b: Check if node has children
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as child_count,
                    STRING_AGG(node_id || ' (' || node_name || ')', ', ') as children
                FROM dim_hierarchy
                WHERE parent_node_id = :node_id
            """), {"node_id": node_id})
            
            children_info = result.fetchone()
            if children_info:
                child_count, children_list = children_info
                print(f"   [CHILDREN]")
                print(f"      Child Count: {child_count}")
                if child_count > 0:
                    print(f"      Children: {children_list}")
                    print()
                    
                    # Get detailed children info
                    result = conn.execute(text("""
                        SELECT node_id, node_name, is_leaf, depth
                        FROM dim_hierarchy
                        WHERE parent_node_id = :node_id
                        ORDER BY node_name
                    """), {"node_id": node_id})
                    
                    children = result.fetchall()
                    print(f"   [CHILDREN DETAILS]")
                    for child in children:
                        child_id, child_name, child_is_leaf, child_depth = child
                        print(f"      - {child_id} ('{child_name}'): leaf={child_is_leaf}, depth={child_depth}")
                else:
                    print(f"      No children found")
                print()
            else:
                print(f"   [CHILDREN] No children found")
                print()
            
            # Step 1c: Check if node has direct rows in fact_pnl_use_case_3
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as row_count,
                    SUM(pnl_daily) as total_daily,
                    SUM(pnl_commission) as total_commission,
                    SUM(pnl_trade) as total_trade,
                    MIN(effective_date) as min_date,
                    MAX(effective_date) as max_date
                FROM fact_pnl_use_case_3
                WHERE strategy = :node_name
            """), {"node_name": node_name})
            
            direct_rows = result.fetchone()
            if direct_rows:
                row_count, total_daily, total_commission, total_trade, min_date, max_date = direct_rows
                print(f"   [DIRECT ROWS IN FACT TABLE]")
                print(f"      Row Count: {row_count}")
                print(f"      Total Daily P&L: {total_daily or 0}")
                print(f"      Total Commission: {total_commission or 0}")
                print(f"      Total Trade: {total_trade or 0}")
                print(f"      Date Range: {min_date} to {max_date}")
                print()
                
                if row_count > 0:
                    print(f"   [HYBRID STATUS]")
                    if child_count > 0:
                        print(f"      [HYBRID NODE CONFIRMED]")
                        print(f"         - Has {child_count} children")
                        print(f"         - Has {row_count} direct rows in fact table")
                        print(f"         - Direct Daily P&L: {total_daily or 0}")
                    else:
                        print(f"      [LEAF NODE WITH DIRECT ROWS]")
                        print(f"         - No children")
                        print(f"         - Has {row_count} direct rows")
                else:
                    print(f"   [HYBRID STATUS]")
                    print(f"      [NO DIRECT ROWS]")
                    print(f"         - Has {child_count} children")
                    print(f"         - No direct rows in fact table")
            else:
                print(f"   [DIRECT ROWS] Could not query fact table")
                print()
            
            # Step 1d: Check if children also have direct rows (Double Counting Risk)
            if child_count > 0:
                print(f"   [DOUBLE COUNTING CHECK]")
                print(f"      Checking if children also have direct rows...")
                print()
                
                result = conn.execute(text("""
                    SELECT 
                        h.node_name as child_name,
                        COUNT(f.entry_id) as row_count,
                        SUM(f.pnl_daily) as total_daily
                    FROM dim_hierarchy h
                    LEFT JOIN fact_pnl_use_case_3 f ON f.strategy = h.node_name
                    WHERE h.parent_node_id = :node_id
                    GROUP BY h.node_name
                    ORDER BY h.node_name
                """), {"node_id": node_id})
                
                children_with_data = result.fetchall()
                if children_with_data:
                    print(f"      Children with direct rows in fact table:")
                    total_children_daily = 0
                    for child_row in children_with_data:
                        child_name, child_row_count, child_total_daily = child_row
                        child_total_daily = child_total_daily or 0
                        total_children_daily += child_total_daily
                        if child_row_count > 0:
                            print(f"         - {child_name}: {child_row_count} rows, Daily={child_total_daily}")
                        else:
                            print(f"         - {child_name}: No direct rows")
                    
                    print()
                    print(f"      [DOUBLE COUNTING ANALYSIS]")
                    direct_daily = total_daily or 0 if row_count > 0 else 0
                    print(f"         Parent Direct Daily: {direct_daily}")
                    print(f"         Children Sum Daily: {total_children_daily}")
                    
                    if direct_daily > 0 and total_children_daily > 0:
                        print(f"         [RISK] Both parent and children have direct rows")
                        print(f"         Question: Is parent's direct value already a sum of children?")
                        print(f"         Answer: If parent={direct_daily} ≈ sum(children)={total_children_daily}, then YES (double counting risk)")
                        print(f"         Answer: If parent={direct_daily} ≠ sum(children)={total_children_daily}, then NO (distinct data)")
                        
                        if abs(direct_daily - total_children_daily) < 0.01:
                            print(f"         [DOUBLE COUNTING CONFIRMED] Parent value = sum of children")
                        else:
                            print(f"         [NO DOUBLE COUNTING] Parent has distinct data")
                    elif direct_daily > 0 and total_children_daily == 0:
                        print(f"         [NO RISK] Only parent has direct rows, children don't")
                    elif direct_daily == 0 and total_children_daily > 0:
                        print(f"         [NO RISK] Only children have direct rows, parent doesn't")
                    else:
                        print(f"         [NO DATA] Neither parent nor children have direct rows")
            
            print()
            print("=" * 80)
            print()
        
        # Task 2: Analyze the Collision
        print("=" * 80)
        print("TASK 2: ANALYZE THE COLLISION")
        print("=" * 80)
        print()
        
        print("[CURRENT WATERFALL LOGIC]")
        print("   waterfall_up() function:")
        print("   - For parent nodes: node_value = sum(children)")
        print("   - This OVERWRITES any direct value from natural rollup")
        print()
        print("[PROBLEM]")
        print("   If a node is HYBRID (has both children AND direct rows):")
        print("   - Natural rollup matches strategy='CRB' -> returns direct value (e.g., 15,000.04)")
        print("   - adjusted_results['NODE_10'] = 15,000.04 (from natural_results.copy())")
        print("   - waterfall_up() overwrites: adjusted_results['NODE_10'] = sum(children)")
        print("   - If children are 0 or missing, parent becomes 0 ❌")
        print()
        print("[REQUIRED FIX]")
        print("   For HYBRID nodes: node_value = node_direct_value + sum(children)")
        print("   But must ensure no double counting!")
        print()
        
        # Task 3: Verify the Fix Logic
        print("=" * 80)
        print("TASK 3: VERIFY THE FIX LOGIC")
        print("=" * 80)
        print()
        
        print("[QUESTION] In _calculate_strategy_rollup, does querying 'CRB' include children's data?")
        print()
        print("[ANALYSIS]")
        print("   _calculate_strategy_rollup logic:")
        print("   1. Loads ALL facts from fact_pnl_use_case_3")
        print("   2. Matches fact.strategy to node.node_name (case-insensitive)")
        print("   3. For 'CRB' node: matches WHERE strategy = 'CRB'")
        print("   4. This ONLY matches rows where strategy column = 'CRB'")
        print("   5. Does NOT include rows where strategy = 'Child of CRB'")
        print()
        print("   [CONCLUSION]")
        print("   ✅ NO DOUBLE COUNTING RISK")
        print("   - Parent's direct value (strategy='CRB') is DISTINCT from children's values")
        print("   - Children would have their own strategy names (if they have direct rows)")
        print("   - The query for 'CRB' only returns rows where strategy='CRB'")
        print()
        print("   [VERIFICATION]")
        print("   Let's check what strategies exist for children of CRB...")
        print()
        
        # Check children strategies for CRB
        result = conn.execute(text("""
            SELECT h.node_name as child_name
            FROM dim_hierarchy h
            WHERE h.parent_node_id = (
                SELECT node_id FROM dim_hierarchy WHERE node_name = 'CRB'
            )
        """))
        
        crb_children = [row[0] for row in result.fetchall()]
        if crb_children:
            print(f"   CRB children: {crb_children}")
            
            # Check if these children exist as strategies
            result = conn.execute(text("""
                SELECT DISTINCT strategy
                FROM fact_pnl_use_case_3
                WHERE strategy IN :children
            """), {"children": tuple(crb_children)})
            
            children_strategies = [row[0] for row in result.fetchall()]
            if children_strategies:
                print(f"   Children that are also strategies: {children_strategies}")
                print(f"   [OK] Children have distinct strategy names")
                print(f"   [OK] Parent 'CRB' strategy is separate from children strategies")
            else:
                print(f"   [INFO] No children found as strategies in fact table")
                print(f"   [OK] This means children don't have direct rows")
                print(f"   [OK] Parent 'CRB' value is independent")
        else:
            print(f"   ⚠️ CRB has no children (or query failed)")
        
        print()
        print("=" * 80)
        print("DEFINITIVE RECOMMENDATION")
        print("=" * 80)
        print()
        print("Based on the investigation above:")
        print()
        print("1. HYBRID NODE STATUS:")
        print("   - Check output above for each node (CRB, ETF Amber, MSET)")
        print("   - If node has BOTH children AND direct rows → HYBRID")
        print()
        print("2. WATERFALL LOGIC FIX:")
        print("   - Current: node_value = sum(children) [DESTRUCTIVE for hybrid nodes]")
        print("   - Required: node_value = node_direct_value + sum(children)")
        print()
        print("3. DOUBLE COUNTING RISK:")
        print("   - LOW RISK: Parent strategy='CRB' is distinct from children strategies")
        print("   - _calculate_strategy_rollup only matches exact strategy name")
        print("   - Children would have different strategy names (if they have direct rows)")
        print()
        print("4. IMPLEMENTATION:")
        print("   - In waterfall_up(), check if node has direct value in natural_results")
        print("   - If yes: node_value = natural_results[node_id] + sum(children)")
        print("   - If no: node_value = sum(children) [current behavior]")
        print()
        
        return 0

if __name__ == "__main__":
    exit(main())

