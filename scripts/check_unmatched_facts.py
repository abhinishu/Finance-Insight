"""
Check for unmatched facts that might explain the plug discrepancy
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine

def main():
    print("=" * 80)
    print("CHECKING FOR UNMATCHED FACTS")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        # Get all strategies in fact table
        print("Step 1: All strategies in fact_pnl_use_case_3...")
        result = conn.execute(text("""
            SELECT 
                strategy,
                COUNT(*) as row_count,
                SUM(pnl_daily) as total_daily
            FROM fact_pnl_use_case_3
            GROUP BY strategy
            ORDER BY strategy
        """))
        
        fact_strategies = result.fetchall()
        print(f"[FACT STRATEGIES] Found {len(fact_strategies)} strategies:")
        total_fact_daily = 0
        for row in fact_strategies:
            strategy, row_count, total_daily = row
            total_daily = total_daily or 0
            total_fact_daily += total_daily
            print(f"   {strategy}: {row_count} rows, Daily={total_daily:,.2f}")
        print(f"   [TOTAL] Sum of all strategies: {total_fact_daily:,.2f}")
        print()
        
        # Get all node names in hierarchy
        print("Step 2: All node names in hierarchy...")
        result = conn.execute(text("""
            SELECT DISTINCT node_name
            FROM dim_hierarchy
            ORDER BY node_name
        """))
        
        hierarchy_nodes = [row[0] for row in result.fetchall()]
        print(f"[HIERARCHY NODES] Found {len(hierarchy_nodes)} distinct node names:")
        for node_name in hierarchy_nodes[:20]:  # Show first 20
            print(f"   {node_name}")
        if len(hierarchy_nodes) > 20:
            print(f"   ... and {len(hierarchy_nodes) - 20} more")
        print()
        
        # Find unmatched strategies
        print("Step 3: Finding unmatched strategies...")
        fact_strategy_names = [row[0] for row in fact_strategies]
        unmatched = [s for s in fact_strategy_names if s not in hierarchy_nodes]
        
        if unmatched:
            print(f"[UNMATCHED] Found {len(unmatched)} strategies without matching nodes:")
            unmatched_total = 0
            for strategy in unmatched:
                # Get total for this strategy
                for row in fact_strategies:
                    if row[0] == strategy:
                        total_daily = row[2] or 0
                        unmatched_total += total_daily
                        print(f"   {strategy}: Daily={total_daily:,.2f}")
            print(f"   [TOTAL UNMATCHED] Daily={unmatched_total:,.2f}")
            print()
            print(f"[HYPOTHESIS] These unmatched facts ({unmatched_total:,.2f}) are:")
            print(f"   - Included in ROOT Natural (sum of all facts)")
            print(f"   - NOT included in any child's Adjusted value")
            print(f"   - Create plug = {unmatched_total:,.2f}")
        else:
            print("[OK] All strategies have matching nodes")
            print()
        
        # Check if there's a discrepancy
        print("Step 4: Analyzing the discrepancy...")
        print(f"   Total Facts Daily: {total_fact_daily:,.2f}")
        print(f"   Expected Plug: 19,999.79")
        print(f"   Actual Plug: 151,547.79")
        print(f"   Difference: {151547.79 - 19999.79:,.2f}")
        print()
        
        if unmatched:
            print(f"[ROOT CAUSE]")
            print(f"   Unmatched facts total: {unmatched_total:,.2f}")
            print(f"   Plug discrepancy: {151547.79 - 19999.79:,.2f}")
            if abs(unmatched_total - (151547.79 - 19999.79)) < 1.0:
                print(f"   [MATCH] Unmatched facts explain the plug discrepancy!")
            else:
                print(f"   [PARTIAL] Unmatched facts explain part of the discrepancy")
                print(f"   Remaining: {abs(unmatched_total - (151547.79 - 19999.79)):,.2f}")
        
        return 0

if __name__ == "__main__":
    exit(main())

