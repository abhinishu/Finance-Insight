"""
Find orphan strategies: Strategies in fact_pnl_use_case_3 that don't have matching nodes in hierarchy
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
    print("FINDING ORPHAN STRATEGIES")
    print("=" * 80)
    print()
    print("Orphan = Strategy in fact table that doesn't match any node_name in hierarchy")
    print()
    
    with engine.connect() as conn:
        # Step 1: Get Use Case 3 ID
        print("Step 1: Getting Use Case 3 ID...")
        result = conn.execute(text("""
            SELECT use_case_id, name
            FROM use_cases
            WHERE name ILIKE '%america%cash%equity%'
        """))
        
        uc3 = result.fetchone()
        if not uc3:
            print("[ERROR] Use Case 3 not found!")
            return 1
        
        uc3_id, uc3_name = uc3
        print(f"[OK] Use Case: {uc3_name}")
        print(f"   ID: {uc3_id}")
        print()
        
        # Step 2: Get all strategies from fact table
        print("Step 2: Getting all strategies from fact_pnl_use_case_3...")
        result = conn.execute(text("""
            SELECT 
                strategy,
                COUNT(*) as row_count,
                SUM(pnl_daily) as total_pnl,
                SUM(pnl_commission) as total_commission,
                SUM(pnl_trade) as total_trade
            FROM fact_pnl_use_case_3
            GROUP BY strategy
            ORDER BY strategy
        """))
        
        fact_strategies = result.fetchall()
        print(f"[FACT STRATEGIES] Found {len(fact_strategies)} distinct strategies:")
        fact_strategy_names = []
        total_fact_pnl = 0
        for row in fact_strategies:
            strategy, row_count, total_pnl, total_commission, total_trade = row
            total_pnl = total_pnl or 0
            fact_strategy_names.append(strategy)
            total_fact_pnl += total_pnl
            print(f"   {strategy}: {row_count} rows, Daily P&L={total_pnl:,.2f}")
        print(f"   [TOTAL] Sum of all strategies: {total_fact_pnl:,.2f}")
        print()
        
        # Step 3: Get all node names from hierarchy
        print("Step 3: Getting all node names from dim_hierarchy...")
        result = conn.execute(text("""
            SELECT DISTINCT node_name
            FROM dim_hierarchy
            ORDER BY node_name
        """))
        
        hierarchy_nodes = [row[0] for row in result.fetchall()]
        print(f"[HIERARCHY NODES] Found {len(hierarchy_nodes)} distinct node names")
        print(f"   (Showing first 20):")
        for node_name in hierarchy_nodes[:20]:
            print(f"   - {node_name}")
        if len(hierarchy_nodes) > 20:
            print(f"   ... and {len(hierarchy_nodes) - 20} more")
        print()
        
        # Step 4: Find orphan strategies
        print("Step 4: Identifying orphan strategies...")
        print("   (Strategies in fact table that don't exist in hierarchy)")
        print()
        
        orphan_strategies = []
        for strategy in fact_strategy_names:
            if strategy not in hierarchy_nodes:
                orphan_strategies.append(strategy)
        
        if orphan_strategies:
            print(f"[ORPHANS FOUND] {len(orphan_strategies)} orphan strategy(ies):")
            print()
            
            total_orphan_pnl = 0
            for strategy in orphan_strategies:
                # Get details for this orphan
                for row in fact_strategies:
                    if row[0] == strategy:
                        strategy_name, row_count, total_pnl, total_commission, total_trade = row
                        total_pnl = total_pnl or 0
                        total_orphan_pnl += total_pnl
                        print(f"   [ORPHAN] {strategy_name}:")
                        print(f"      Rows: {row_count}")
                        print(f"      Daily P&L: {total_pnl:,.2f}")
                        print(f"      Commission: {total_commission or 0:,.2f}")
                        print(f"      Trade: {total_trade or 0:,.2f}")
                        print()
            
            print(f"[TOTAL ORPHAN P&L] Sum of orphan strategies: {total_orphan_pnl:,.2f}")
            print()
            
            # Step 5: Compare with plug discrepancy
            print("Step 5: Comparing with plug discrepancy...")
            expected_plug = 19999.79
            actual_plug = 151547.79
            plug_discrepancy = actual_plug - expected_plug
            print(f"   Expected Plug: {expected_plug:,.2f}")
            print(f"   Actual Plug: {actual_plug:,.2f}")
            print(f"   Discrepancy: {plug_discrepancy:,.2f}")
            print()
            print(f"   Orphan P&L Total: {total_orphan_pnl:,.2f}")
            
            if abs(total_orphan_pnl - plug_discrepancy) < 1.0:
                print(f"   [MATCH] Orphan P&L matches plug discrepancy!")
                print(f"   [ROOT CAUSE] Orphan strategies explain the plug discrepancy")
            elif total_orphan_pnl > 0:
                print(f"   [PARTIAL] Orphan P&L explains {total_orphan_pnl:,.2f} of {plug_discrepancy:,.2f}")
                print(f"   Remaining: {plug_discrepancy - total_orphan_pnl:,.2f}")
            else:
                print(f"   [NO MATCH] Orphan P&L doesn't explain the discrepancy")
            
            print()
            
            # Step 6: SQL query for user
            print("=" * 80)
            print("SQL QUERY FOR ORPHAN STRATEGIES")
            print("=" * 80)
            print()
            print("-- Fixed query (using correct table name):")
            print("SELECT")
            print("    strategy,")
            print("    COUNT(*) as row_count,")
            print("    SUM(pnl_daily) as total_pnl,")
            print("    SUM(pnl_commission) as total_commission,")
            print("    SUM(pnl_trade) as total_trade")
            print("FROM fact_pnl_use_case_3")
            print("WHERE strategy NOT IN (")
            print("    SELECT DISTINCT node_name")
            print("    FROM dim_hierarchy")
            print(")")
            print("GROUP BY strategy")
            print("ORDER BY strategy;")
            print()
            
        else:
            print("[OK] No orphan strategies found")
            print("   All strategies in fact table have matching nodes in hierarchy")
            print()
            print("[IMPLICATION]")
            print("   The plug discrepancy (131,548.00) is NOT caused by orphan strategies")
            print("   The issue must be elsewhere:")
            print("   - Nodes with Adjusted = 0 (due to rules)")
            print("   - Calculation mismatch between Natural and Adjusted")
            print("   - Missing children in hierarchy")
            print()
        
        # Step 7: Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print()
        print(f"Total Strategies in Fact Table: {len(fact_strategies)}")
        print(f"Total Node Names in Hierarchy: {len(hierarchy_nodes)}")
        print(f"Orphan Strategies: {len(orphan_strategies)}")
        if orphan_strategies:
            print(f"Total Orphan P&L: {total_orphan_pnl:,.2f}")
            print()
            print("[RECOMMENDATION]")
            print("   1. Add missing nodes to hierarchy for orphan strategies")
            print("   2. OR exclude orphan strategies from ROOT Natural calculation")
            print("   3. Re-run calculation to verify plug matches expected value")
        else:
            print()
            print("[RECOMMENDATION]")
            print("   Investigate other causes:")
            print("   1. Check for nodes with Adjusted = 0")
            print("   2. Verify Natural calculation for all nodes")
            print("   3. Check if all children are included in Adjusted sum")
        
        return 0

if __name__ == "__main__":
    exit(main())

