"""
Analyze Commissions parent value discrepancy and Math rule execution
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine
from decimal import Decimal

def main():
    print("=" * 80)
    print("COMMISSIONS VALUE DISCREPANCY ANALYSIS")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        uc3_id = 'fce60983-0328-496b-b6e1-34249ec5aa5a'
        
        # Step 1: Find Commissions node
        print("Step 1: Finding Commissions node...")
        node_result = conn.execute(text("""
            SELECT node_id, node_name, parent_node_id, is_leaf, depth
            FROM dim_hierarchy
            WHERE node_name = 'Commissions'
              AND atlas_source = (
                  SELECT atlas_structure_id FROM use_cases WHERE use_case_id = :uc3_id
              )
        """), {"uc3_id": str(uc3_id)})
        
        comm_node = node_result.fetchone()
        if not comm_node:
            print("[ERROR] Commissions node not found!")
            return 1
        
        comm_node_id, comm_node_name, parent_id, is_leaf, depth = comm_node
        print(f"[OK] Found: {comm_node_name} ({comm_node_id})")
        print(f"   Parent: {parent_id}")
        print(f"   Is Leaf: {is_leaf}")
        print(f"   Depth: {depth}")
        print()
        
        # Step 2: Find children of Commissions
        print("Step 2: Finding children of Commissions...")
        children_result = conn.execute(text("""
            SELECT node_id, node_name, is_leaf
            FROM dim_hierarchy
            WHERE parent_node_id = :comm_node_id
            ORDER BY node_name
        """), {"comm_node_id": comm_node_id})
        
        children = children_result.fetchall()
        print(f"[OK] Found {len(children)} child(ren):")
        for child_id, child_name, child_is_leaf in children:
            print(f"   - {child_name} ({child_id}), is_leaf={child_is_leaf}")
        print()
        
        # Step 3: Check direct fact rows for Commissions
        print("Step 3: Checking direct fact rows for 'Commissions' strategy...")
        direct_result = conn.execute(text("""
            SELECT 
                COUNT(*) as row_count,
                SUM(pnl_daily) as total_daily,
                SUM(pnl_commission) as total_commission,
                SUM(pnl_trade) as total_trade
            FROM fact_pnl_use_case_3
            WHERE strategy = 'Commissions'
        """))
        
        direct_data = direct_result.fetchone()
        direct_daily = Decimal('0')
        if direct_data:
            row_count, total_daily, total_commission, total_trade = direct_data
            direct_daily = Decimal(str(total_daily)) if total_daily else Decimal('0')
            print(f"[OK] Direct fact rows for 'Commissions':")
            print(f"   Rows: {row_count}")
            print(f"   Total Daily P&L: {direct_daily:,.2f}")
            print(f"   Total Commission: {total_commission or 0:,.2f}")
            print(f"   Total Trade: {total_trade or 0:,.2f}")
            print()
        
        # Step 4: Check children's fact rows
        print("Step 4: Checking children's fact rows...")
        child_values = {}
        for child_id, child_name, child_is_leaf in children:
            child_result = conn.execute(text("""
                SELECT 
                    COUNT(*) as row_count,
                    SUM(pnl_daily) as total_daily
                FROM fact_pnl_use_case_3
                WHERE strategy = :child_name
            """), {"child_name": child_name})
            
            child_data = child_result.fetchone()
            if child_data:
                row_count, total_daily = child_data
                total_daily = total_daily or Decimal('0')
                child_values[child_name] = total_daily
                print(f"   {child_name}: {total_daily:,.2f} ({row_count} rows)")
        
        # Calculate sum of children
        children_sum = sum(child_values.values())
        print(f"   Sum of Children: {children_sum:,.2f}")
        print()
        
        # Step 5: Calculate expected vs actual
        print("Step 5: Value Analysis...")
        print(f"   Direct 'Commissions' rows: {direct_daily:,.2f}")
        print(f"   Sum of Children: {children_sum:,.2f}")
        print(f"   Expected Natural (Direct + Children): {direct_daily + children_sum:,.2f}")
        print(f"   Actual Tab 3 Value: 112,496.69")
        print()
        
        expected_natural = direct_daily + children_sum
        discrepancy = Decimal('112496.69') - expected_natural
        print(f"   Discrepancy: {discrepancy:,.2f}")
        if abs(discrepancy) < Decimal('0.01'):
            print(f"   [OK] Natural value matches expected (Hybrid Parent behavior)")
        print()
        
        # Step 6: Check Math rule
        print("Step 6: Checking Math rule for Commissions...")
        rule_result = conn.execute(text("""
            SELECT 
                r.rule_id,
                r.rule_type,
                r.rule_expression,
                r.rule_dependencies,
                r.measure_name
            FROM metadata_rules r
            WHERE r.use_case_id = :uc3_id
              AND r.node_id = :comm_node_id
        """), {"uc3_id": str(uc3_id), "comm_node_id": comm_node_id})
        
        rule = rule_result.fetchone()
        if rule:
            rule_id, rule_type, rule_expr, rule_deps, measure_name = rule
            print(f"[OK] Found Math rule:")
            print(f"   Rule ID: {rule_id}")
            print(f"   Type: {rule_type}")
            print(f"   Expression: {rule_expr}")
            print(f"   Dependencies: {rule_deps}")
            print(f"   Measure: {measure_name}")
            print()
            
            # Step 7: Check if NODE_5 and NODE_6 exist and their values
            print("Step 7: Checking NODE_5 and NODE_6...")
            node5_result = conn.execute(text("""
                SELECT node_id, node_name
                FROM dim_hierarchy
                WHERE node_id = 'NODE_5'
                  AND atlas_source = (
                      SELECT atlas_structure_id FROM use_cases WHERE use_case_id = :uc3_id
                  )
            """), {"uc3_id": str(uc3_id)})
            
            node5 = node5_result.fetchone()
            if node5:
                node5_id, node5_name = node5
                print(f"   NODE_5: {node5_name} ({node5_id})")
                
                # Get NODE_5 value from fact table
                node5_fact = conn.execute(text("""
                    SELECT SUM(pnl_daily) as total_daily
                    FROM fact_pnl_use_case_3
                    WHERE strategy = :node5_name
                """), {"node5_name": node5_name})
                node5_value = node5_fact.fetchone()[0] or Decimal('0')
                print(f"   NODE_5 Value: {node5_value:,.2f}")
            
            node6_result = conn.execute(text("""
                SELECT node_id, node_name
                FROM dim_hierarchy
                WHERE node_id = 'NODE_6'
                  AND atlas_source = (
                      SELECT atlas_structure_id FROM use_cases WHERE use_case_id = :uc3_id
                  )
            """), {"uc3_id": str(uc3_id)})
            
            node6 = node6_result.fetchone()
            if node6:
                node6_id, node6_name = node6
                print(f"   NODE_6: {node6_name} ({node6_id})")
                
                # Get NODE_6 value from fact table
                node6_fact = conn.execute(text("""
                    SELECT SUM(pnl_daily) as total_daily
                    FROM fact_pnl_use_case_3
                    WHERE strategy = :node6_name
                """), {"node6_name": node6_name})
                node6_value = node6_fact.fetchone()[0] or Decimal('0')
                print(f"   NODE_6 Value: {node6_value:,.2f}")
                
                if node5:
                    expected_math = node5_value + node6_value
                    print(f"   Expected Math Result (NODE_5 + NODE_6): {expected_math:,.2f}")
                    print(f"   Actual Tab 3 Value: 112,496.69")
                    print(f"   Difference: {Decimal('112496.69') - expected_math:,.2f}")
        else:
            print("[WARNING] No Math rule found for Commissions!")
        print()
        
        # Step 8: Check latest calculation results
        print("Step 8: Checking latest calculation results...")
        calc_result = conn.execute(text("""
            SELECT 
                fcr.node_id,
                h.node_name,
                fcr.measure_vector->>'daily' as adjusted_daily,
                fcr.plug_vector->>'daily' as plug_daily,
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
              AND h.node_name IN ('Commissions', 'Commissions (Non Swap)', 'Swap Commission')
            ORDER BY h.node_name
        """), {"uc3_id": str(uc3_id)})
        
        calc_data = calc_result.fetchall()
        if calc_data:
            print("[OK] Latest calculation results:")
            for node_id, node_name, adjusted_daily, plug_daily, run_timestamp in calc_data:
                adjusted_daily = float(adjusted_daily) if adjusted_daily else 0.0
                plug_daily = float(plug_daily) if plug_daily else 0.0
                natural_daily = adjusted_daily + plug_daily
                print(f"   {node_name} ({node_id}):")
                print(f"      Natural (Adjusted + Plug): {natural_daily:,.2f}")
                print(f"      Adjusted: {adjusted_daily:,.2f}")
                print(f"      Plug: {plug_daily:,.2f}")
        else:
            print("[WARNING] No calculation results found")
        print()
        
        # Step 9: Root Cause Analysis
        print("=" * 80)
        print("ROOT CAUSE ANALYSIS")
        print("=" * 80)
        print()
        print("Issue 1: Natural Value (112,496.69) doesn't match sum of children")
        print(f"   - Children Sum: {children_sum:,.2f}")
        print(f"   - Direct 'Commissions' rows: {total_daily:,.2f}")
        print(f"   - Expected: {total_daily + children_sum:,.2f}")
        print(f"   - Actual: 112,496.69")
        print(f"   - Discrepancy: {discrepancy:,.2f}")
        print()
        print("Possible Causes:")
        print("   1. 'Commissions' is a Hybrid Parent (has direct rows + children)")
        print("   2. Natural rollup includes direct rows in parent value")
        print("   3. Children sum calculation might be wrong")
        print()
        print("Issue 2: Math Rule Not Applied")
        print("   - Rule exists: NODE_5 + NODE_6")
        if node5 and node6:
            print(f"   - Expected Adjusted: {expected_math:,.2f}")
            print(f"   - Actual Adjusted: (check calculation results above)")
        print()
        print("Possible Causes:")
        print("   1. Math rule executed but overwritten by waterfall_up")
        print("   2. Math rule not executed in correct order")
        print("   3. waterfall_up runs after Math rule and overwrites it")
        print()
        
        return 0

if __name__ == "__main__":
    exit(main())

