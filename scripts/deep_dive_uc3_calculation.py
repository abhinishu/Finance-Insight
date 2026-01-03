"""
Deep dive into Use Case 3 calculation logic
Focus: Why Adjusted P&L = 0 for nodes without rules
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
    print("DEEP DIVE: USE CASE 3 CALCULATION LOGIC")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        uc3_id = 'fce60983-0328-496b-b6e1-34249ec5aa5a'
        
        # Step 1: Check what the strategy rollup should return for CRB, ETF Amber, MSET
        print("Step 1: Testing strategy rollup matching logic...")
        print()
        
        test_nodes = ['CRB', 'ETF Amber', 'MSET']
        for node_name in test_nodes:
            print(f"[TEST] Node: {node_name}")
            
            # Check if strategy exists
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as row_count,
                    SUM(pnl_daily) as total_daily,
                    SUM(pnl_commission) as total_commission,
                    SUM(pnl_trade) as total_trade
                FROM fact_pnl_use_case_3
                WHERE strategy = :node_name
            """), {"node_name": node_name})
            
            strategy_data = result.fetchone()
            if strategy_data:
                row_count, total_daily, total_commission, total_trade = strategy_data
                print(f"   Strategy '{node_name}' in DB:")
                print(f"      Rows: {row_count}")
                print(f"      Daily: {total_daily or 0}")
                print(f"      Commission: {total_commission or 0}")
                print(f"      Trade: {total_trade or 0}")
                
                if row_count > 0:
                    print(f"   ✅ Strategy exists and has data")
                    print(f"   ❓ Why is Adjusted P&L = 0?")
                else:
                    print(f"   ⚠️ Strategy exists but has no rows")
            else:
                print(f"   ❌ Strategy not found in database")
            print()
        
        # Step 2: Check the actual strategy name that should be used for Commission rule
        print("Step 2: Finding correct strategy name for Commission rule...")
        print()
        
        # The rule says strategy = 'CORE', but what strategies actually exist?
        result = conn.execute(text("""
            SELECT DISTINCT strategy
            FROM fact_pnl_use_case_3
            WHERE strategy ILIKE '%core%' OR strategy ILIKE '%commission%'
            ORDER BY strategy
        """))
        
        related_strategies = [row[0] for row in result.fetchall()]
        print(f"[STRATEGIES] Strategies containing 'core' or 'commission':")
        for strat in related_strategies:
            print(f"   - {strat}")
        print()
        
        # Check what data exists for 'Commissions (Non Swap)' strategy
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as row_count,
                SUM(pnl_daily) as total_daily,
                SUM(pnl_commission) as total_commission
            FROM fact_pnl_use_case_3
            WHERE strategy = 'Commissions (Non Swap)'
        """))
        
        comm_data = result.fetchone()
        if comm_data:
            row_count, total_daily, total_commission = comm_data
            print(f"[DATA] 'Commissions (Non Swap)' strategy:")
            print(f"   Rows: {row_count}")
            print(f"   Daily: {total_daily or 0}")
            print(f"   Commission: {total_commission or 0}")
            print()
            print(f"[HYPOTHESIS] The rule should probably be:")
            print(f"   strategy = 'Commissions (Non Swap)'")
            print(f"   NOT strategy = 'CORE'")
        print()
        
        # Step 3: Check natural vs adjusted results
        print("Step 3: Comparing Natural vs Adjusted results...")
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
              AND ucr.run_timestamp = (
                  SELECT MAX(run_timestamp)
                  FROM use_case_runs
                  WHERE use_case_id = :uc3_id
              )
              AND h.node_name IN ('CRB', 'ETF Amber', 'MSET', 'Commissions (Non Swap)', 'Commissions')
            ORDER BY h.node_name
        """), {"uc3_id": str(uc3_id)})
        
        latest_results = result.fetchall()
        if latest_results:
            print(f"[LATEST RESULTS] From most recent calculation:")
            for row in latest_results:
                node_id, node_name, adjusted_daily, is_override, run_timestamp = row
                print(f"   {node_name} ({node_id}):")
                print(f"      Adjusted Daily: {adjusted_daily}")
                print(f"      Has Rule (override): {is_override}")
        else:
            print("[INFO] No results found")
        print()
        
        # Step 4: Check if natural rollup is working
        print("Step 4: Understanding natural rollup logic...")
        print()
        print("[INFO] The _calculate_strategy_rollup function:")
        print("   1. Loads all facts from fact_pnl_use_case_3")
        print("   2. Matches fact.strategy to node.node_name (case-insensitive)")
        print("   3. Sums matching rows for each node")
        print("   4. Aggregates parent nodes from children (bottom-up)")
        print()
        print("[QUESTION] If CRB, ETF Amber, MSET have:")
        print("   - Original Daily P&L = non-zero (from natural rollup)")
        print("   - No rules")
        print("   - Adjusted Daily P&L = 0")
        print()
        print("[HYPOTHESIS] The issue might be:")
        print("   - Natural rollup works (Original is populated)")
        print("   - But adjusted_results initialization is wrong")
        print("   - OR adjusted_results is being overwritten incorrectly")
        print()
        
        # Step 5: Check the calculation logic flow
        print("Step 5: Expected calculation flow...")
        print()
        print("[EXPECTED] For nodes WITHOUT rules:")
        print("   1. natural_results[node_id] = calculated from strategy rollup")
        print("   2. adjusted_results[node_id] = natural_results[node_id] (copy)")
        print("   3. plug_results[node_id] = natural - adjusted = 0")
        print()
        print("[ACTUAL] What we see:")
        print("   - Original (natural) = non-zero ✅")
        print("   - Adjusted = 0 ❌ (should = Original)")
        print("   - Plug = Original - 0 = Original ✅")
        print()
        print("[ROOT CAUSE HYPOTHESIS]")
        print("   The adjusted_results might not be initialized from natural_results")
        print("   OR it's being set to 0 somewhere in the calculation")
        print()
        
        return 0

if __name__ == "__main__":
    exit(main())

