"""
Analyze why Adjusted Daily P&L is 0 for certain nodes in Use Case 3
Focus: CRB, ETF Amber, MSET, and Commission (Non Swap)
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
    print("ANALYSIS: WHY ADJUSTED P&L IS ZERO FOR CERTAIN NODES")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        # Step 1: Get Use Case 3 ID
        print("Step 1: Identifying Use Case 3...")
        result = conn.execute(text("""
            SELECT use_case_id, name, input_table_name
            FROM use_cases
            WHERE name ILIKE '%america%cash%equity%'
        """))
        
        uc3 = result.fetchone()
        if not uc3:
            print("[ERROR] Use Case 3 not found!")
            return 1
        
        uc3_id, uc3_name, input_table = uc3
        print(f"[OK] Use Case: {uc3_name}")
        print(f"   ID: {uc3_id}")
        print(f"   Input Table: {input_table}")
        print()
        
        # Step 2: Check what strategies exist in fact_pnl_use_case_3
        print("Step 2: Analyzing strategies in fact_pnl_use_case_3...")
        result = conn.execute(text("""
            SELECT 
                strategy,
                COUNT(*) as row_count,
                SUM(pnl_daily) as total_daily,
                SUM(pnl_commission) as total_commission,
                SUM(pnl_trade) as total_trade
            FROM fact_pnl_use_case_3
            GROUP BY strategy
            ORDER BY strategy
        """))
        
        strategies = result.fetchall()
        print(f"[STRATEGIES] Found {len(strategies)} distinct strategies:")
        for row in strategies:
            strategy, row_count, total_daily, total_commission, total_trade = row
            print(f"   {strategy}: {row_count} rows, daily={total_daily or 0}, commission={total_commission or 0}, trade={total_trade or 0}")
        print()
        
        # Step 3: Check for 'CORE' strategy specifically
        print("Step 3: Checking 'CORE' strategy data...")
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as row_count,
                SUM(pnl_daily) as total_daily,
                SUM(pnl_commission) as total_commission,
                SUM(pnl_trade) as total_trade,
                MIN(effective_date) as min_date,
                MAX(effective_date) as max_date
            FROM fact_pnl_use_case_3
            WHERE strategy = 'CORE'
        """))
        
        core_data = result.fetchone()
        if core_data:
            row_count, total_daily, total_commission, total_trade, min_date, max_date = core_data
            print(f"[CORE STRATEGY] Data found:")
            print(f"   Rows: {row_count}")
            print(f"   Total Daily P&L: {total_daily or 0}")
            print(f"   Total Commission: {total_commission or 0}")
            print(f"   Total Trade: {total_trade or 0}")
            print(f"   Date Range: {min_date} to {max_date}")
            
            if row_count == 0:
                print()
                print("[ROOT CAUSE #1] No rows found for strategy = 'CORE'!")
                print("   This explains why Commission (Non Swap) Adjusted P&L = 0")
            else:
                print()
                print("[OK] CORE strategy has data - rule should return values")
        else:
            print("[ERROR] Could not query CORE strategy")
        print()
        
        # Step 4: Check hierarchy nodes and their names
        print("Step 4: Checking hierarchy node names...")
        result = conn.execute(text("""
            SELECT node_id, node_name, parent_node_id, is_leaf, depth
            FROM dim_hierarchy
            WHERE node_name IN ('CRB', 'ETF Amber', 'MSET', 'Commissions (Non Swap)', 'Commissions')
            ORDER BY depth, node_name
        """))
        
        nodes = result.fetchall()
        print(f"[NODES] Found {len(nodes)} matching nodes:")
        for node in nodes:
            node_id, node_name, parent_id, is_leaf, depth = node
            print(f"   {node_id} ('{node_name}'): parent={parent_id}, leaf={is_leaf}, depth={depth}")
        print()
        
        # Step 5: Check rules for these nodes
        print("Step 5: Checking business rules for these nodes...")
        result = conn.execute(text("""
            SELECT 
                r.rule_id,
                r.node_id,
                h.node_name,
                r.rule_type,
                r.measure_name,
                r.sql_where,
                r.logic_en
            FROM metadata_rules r
            JOIN dim_hierarchy h ON r.node_id = h.node_id
            WHERE r.use_case_id = :uc3_id
              AND h.node_name IN ('CRB', 'ETF Amber', 'MSET', 'Commissions (Non Swap)', 'Commissions')
        """), {"uc3_id": str(uc3_id)})
        
        rules = result.fetchall()
        if rules:
            print(f"[RULES] Found {len(rules)} rules for these nodes:")
            for rule in rules:
                rule_id, node_id, node_name, rule_type, measure_name, sql_where, logic_en = rule
                print(f"   Rule {rule_id} for {node_id} ('{node_name}'):")
                print(f"      Type: {rule_type}")
                print(f"      Measure: {measure_name}")
                print(f"      SQL WHERE: {sql_where}")
                print(f"      Logic: {logic_en}")
        else:
            print("[INFO] No rules found for these specific nodes")
        print()
        
        # Step 6: Check all rules for Use Case 3
        print("Step 6: Checking ALL rules for Use Case 3...")
        result = conn.execute(text("""
            SELECT 
                r.rule_id,
                r.node_id,
                h.node_name,
                r.rule_type,
                r.measure_name,
                r.sql_where,
                r.logic_en
            FROM metadata_rules r
            JOIN dim_hierarchy h ON r.node_id = h.node_id
            WHERE r.use_case_id = :uc3_id
            ORDER BY r.rule_id
        """), {"uc3_id": str(uc3_id)})
        
        all_rules = result.fetchall()
        print(f"[ALL RULES] Found {len(all_rules)} total rules for Use Case 3:")
        for rule in all_rules:
            rule_id, node_id, node_name, rule_type, measure_name, sql_where, logic_en = rule
            print(f"   Rule {rule_id}: {node_id} ('{node_name}') - {rule_type}")
            if sql_where:
                print(f"      SQL: {sql_where}")
        print()
        
        # Step 7: Check latest calculation results
        print("Step 7: Checking latest calculation results...")
        result = conn.execute(text("""
            SELECT 
                fcr.node_id,
                h.node_name,
                fcr.measure_vector->>'daily' as adjusted_daily,
                fcr.is_override,
                ucr.run_timestamp
            FROM fact_calculated_results fcr
            JOIN use_case_runs ucr ON fcr.run_id = ucr.run_id
            JOIN dim_hierarchy h ON fcr.node_id = h.node_id
            WHERE ucr.use_case_id = :uc3_id
              AND h.node_name IN ('CRB', 'ETF Amber', 'MSET', 'Commissions (Non Swap)', 'Commissions')
            ORDER BY ucr.run_timestamp DESC, h.node_name
            LIMIT 20
        """), {"uc3_id": str(uc3_id)})
        
        results = result.fetchall()
        if results:
            print(f"[RESULTS] Latest calculation results:")
            for row in results:
                node_id, node_name, adjusted_daily, is_override, run_timestamp = row
                print(f"   {node_id} ('{node_name}'): adjusted={adjusted_daily}, override={is_override}, run={run_timestamp}")
        else:
            print("[INFO] No results found for these nodes")
        print()
        
        # Step 8: Test the rule query for Commission (Non Swap)
        print("Step 8: Testing rule query for 'Commissions (Non Swap)'...")
        result = conn.execute(text("""
            SELECT 
                r.rule_id,
                r.node_id,
                r.sql_where,
                r.measure_name
            FROM metadata_rules r
            JOIN dim_hierarchy h ON r.node_id = h.node_id
            WHERE r.use_case_id = :uc3_id
              AND h.node_name = 'Commissions (Non Swap)'
        """), {"uc3_id": str(uc3_id)})
        
        commission_rule = result.fetchone()
        if commission_rule:
            rule_id, node_id, sql_where, measure_name = commission_rule
            print(f"[RULE] Found rule {rule_id} for {node_id}:")
            print(f"   SQL WHERE: {sql_where}")
            print(f"   Measure: {measure_name}")
            print()
            
            # Execute the rule query
            if sql_where:
                print(f"[TEST QUERY] Executing rule query...")
                try:
                    # Build the query based on measure_name
                    if measure_name == 'pnl_commission':
                        query = f"""
                            SELECT 
                                COALESCE(SUM(pnl_commission), 0) as measure_value
                            FROM fact_pnl_use_case_3
                            WHERE {sql_where}
                        """
                    elif measure_name == 'pnl_trade':
                        query = f"""
                            SELECT 
                                COALESCE(SUM(pnl_trade), 0) as measure_value
                            FROM fact_pnl_use_case_3
                            WHERE {sql_where}
                        """
                    else:
                        query = f"""
                            SELECT 
                                COALESCE(SUM(pnl_daily), 0) as measure_value
                            FROM fact_pnl_use_case_3
                            WHERE {sql_where}
                        """
                    
                    result = conn.execute(text(query))
                    rule_result = result.fetchone()
                    if rule_result:
                        measure_value = rule_result[0]
                        print(f"   Query Result: {measure_value}")
                        if measure_value == 0:
                            print()
                            print("[ROOT CAUSE #2] Rule query returns 0!")
                            print("   This means the WHERE clause matches no rows")
                            print(f"   SQL WHERE: {sql_where}")
                        else:
                            print()
                            print("[OK] Rule query returns non-zero value")
                            print(f"   But Adjusted P&L is 0 - check rule application logic")
                except Exception as e:
                    print(f"[ERROR] Query failed: {e}")
        else:
            print("[INFO] No rule found for 'Commissions (Non Swap)'")
        print()
        
        # Step 9: Check if nodes match strategy names
        print("Step 9: Checking if node names match strategy names...")
        result = conn.execute(text("""
            SELECT DISTINCT strategy
            FROM fact_pnl_use_case_3
            ORDER BY strategy
        """))
        
        db_strategies = [row[0] for row in result.fetchall()]
        print(f"[DB STRATEGIES] Strategies in database: {db_strategies}")
        
        result = conn.execute(text("""
            SELECT node_name
            FROM dim_hierarchy
            WHERE node_name IN ('CRB', 'ETF Amber', 'MSET')
        """))
        
        node_names = [row[0] for row in result.fetchall()]
        print(f"[NODE NAMES] Node names in hierarchy: {node_names}")
        
        matches = set(db_strategies) & set(node_names)
        print(f"[MATCHES] Matching strategies/nodes: {matches}")
        
        if not matches:
            print()
            print("[ROOT CAUSE #3] Node names don't match strategy names!")
            print("   This explains why CRB, ETF Amber, MSET have Adjusted = 0")
            print("   The rollup function matches by strategy name, but names don't match")
        print()
        
        # Summary
        print("=" * 80)
        print("ROOT CAUSE SUMMARY")
        print("=" * 80)
        print()
        print("Potential Issues:")
        print()
        print("1. Commission (Non Swap) - Adjusted P&L = 0:")
        print("   - Rule exists: strategy = 'CORE'")
        print("   - Check if CORE strategy has data")
        print("   - Check if rule query returns 0")
        print()
        print("2. CRB, ETF Amber, MSET - Adjusted P&L = 0:")
        print("   - Check if these nodes have rules")
        print("   - Check if node names match strategy names in database")
        print("   - If no rules, Adjusted should = Original (not 0)")
        print()
        
        return 0

if __name__ == "__main__":
    exit(main())

