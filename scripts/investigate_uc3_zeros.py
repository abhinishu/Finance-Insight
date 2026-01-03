"""
Deep RCA: Why Use Case 3 shows all zeros in Executive Dashboard
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
    print("ROOT CAUSE ANALYSIS: USE CASE 3 ZERO VALUES")
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
        print(f"[OK] Use Case 3:")
        print(f"   ID: {uc3_id}")
        print(f"   Name: {uc3_name}")
        print(f"   Input Table: {input_table}")
        print()
        
        # Step 2: Check if fact_pnl_use_case_3 has data
        print("Step 2: Checking if fact_pnl_use_case_3 has data...")
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT strategy) as distinct_strategies,
                MIN(effective_date) as min_date,
                MAX(effective_date) as max_date,
                SUM(pnl_daily) as total_daily,
                SUM(pnl_commission) as total_commission,
                SUM(pnl_trade) as total_trade
            FROM fact_pnl_use_case_3
        """))
        
        data_stats = result.fetchone()
        if data_stats:
            total_rows, distinct_strategies, min_date, max_date, total_daily, total_commission, total_trade = data_stats
            print(f"[DATA CHECK] fact_pnl_use_case_3:")
            print(f"   Total Rows: {total_rows}")
            print(f"   Distinct Strategies: {distinct_strategies}")
            print(f"   Date Range: {min_date} to {max_date}")
            print(f"   Total Daily P&L: {total_daily or 0}")
            print(f"   Total Commission: {total_commission or 0}")
            print(f"   Total Trade: {total_trade or 0}")
            
            if total_rows == 0:
                print()
                print("[ROOT CAUSE #1] fact_pnl_use_case_3 table is EMPTY!")
                print("   This explains why all values are zero.")
                print("   Solution: Populate fact_pnl_use_case_3 with test data.")
            else:
                print()
                print("[OK] fact_pnl_use_case_3 has data")
        else:
            print("[ERROR] Could not query fact_pnl_use_case_3")
        print()
        
        # Step 3: Check if there are any saved calculation results
        print("Step 3: Checking for saved calculation results...")
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as result_count,
                MAX(created_at) as latest_result
            FROM fact_calculated_results fcr
            JOIN use_case_runs ucr ON fcr.run_id = ucr.run_id
            WHERE ucr.use_case_id = :uc3_id
        """), {"uc3_id": str(uc3_id)})
        
        saved_results = result.fetchone()
        if saved_results:
            result_count, latest_result = saved_results
            print(f"[SAVED RESULTS] fact_calculated_results:")
            print(f"   Total Result Rows: {result_count}")
            print(f"   Latest Result: {latest_result or 'None'}")
            
            if result_count == 0:
                print()
                print("[ROOT CAUSE #2] No calculation results saved for Use Case 3!")
                print("   This means either:")
                print("   a) No calculation has been run, OR")
                print("   b) Calculation ran but failed to save results")
            else:
                print()
                print("[OK] Found saved results - checking sample...")
                result = conn.execute(text("""
                    SELECT 
                        fcr.node_id,
                        fcr.measure_vector->>'daily' as daily_value,
                        fcr.measure_vector->>'mtd' as mtd_value,
                        fcr.is_override
                    FROM fact_calculated_results fcr
                    JOIN use_case_runs ucr ON fcr.run_id = ucr.run_id
                    WHERE ucr.use_case_id = :uc3_id
                    ORDER BY fcr.created_at DESC
                    LIMIT 10
                """), {"uc3_id": str(uc3_id)})
                
                sample_results = result.fetchall()
                print(f"   Sample of latest results:")
                for row in sample_results:
                    node_id, daily, mtd, is_override = row
                    print(f"      Node {node_id}: daily={daily}, mtd={mtd}, override={is_override}")
        else:
            print("[ERROR] Could not query saved results")
        print()
        
        # Step 4: Check calculation runs
        print("Step 4: Checking calculation run history...")
        result = conn.execute(text("""
            SELECT 
                run_id,
                run_timestamp,
                status,
                calculation_duration_ms,
                triggered_by
            FROM use_case_runs
            WHERE use_case_id = :uc3_id
            ORDER BY run_timestamp DESC
            LIMIT 5
        """), {"uc3_id": str(uc3_id)})
        
        runs = result.fetchall()
        if runs:
            print(f"[RUN HISTORY] Found {len(runs)} recent runs:")
            for run in runs:
                run_id, timestamp, status, duration, triggered_by = run
                print(f"   Run {run_id}:")
                print(f"      Timestamp: {timestamp}")
                print(f"      Status: {status}")
                print(f"      Duration: {duration}ms" if duration else "      Duration: N/A")
                print(f"      Triggered By: {triggered_by}")
        else:
            print("[ROOT CAUSE #3] No calculation runs found for Use Case 3!")
            print("   This means 'Run Calculation' has never been executed.")
        print()
        
        # Step 5: Check hierarchy nodes
        print("Step 5: Checking hierarchy structure...")
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as node_count,
                COUNT(CASE WHEN is_leaf = true THEN 1 END) as leaf_count
            FROM dim_hierarchy
            WHERE use_case_id = :uc3_id
        """), {"uc3_id": str(uc3_id)})
        
        hierarchy_stats = result.fetchone()
        if hierarchy_stats:
            node_count, leaf_count = hierarchy_stats
            print(f"[HIERARCHY] dim_hierarchy:")
            print(f"   Total Nodes: {node_count}")
            print(f"   Leaf Nodes: {leaf_count}")
            
            if node_count == 0:
                print()
                print("[ROOT CAUSE #4] No hierarchy nodes found for Use Case 3!")
                print("   This means the hierarchy was never imported/created.")
        else:
            print("[ERROR] Could not query hierarchy")
        print()
        
        # Step 6: Check if strategy rollup would work
        print("Step 6: Testing strategy rollup query...")
        result = conn.execute(text("""
            SELECT 
                strategy,
                COUNT(*) as row_count,
                SUM(pnl_daily) as total_daily,
                SUM(pnl_commission) as total_commission
            FROM fact_pnl_use_case_3
            GROUP BY strategy
            ORDER BY strategy
        """))
        
        strategy_data = result.fetchall()
        if strategy_data:
            print(f"[STRATEGY DATA] Found {len(strategy_data)} strategies:")
            for row in strategy_data:
                strategy, row_count, total_daily, total_commission = row
                print(f"   {strategy}: {row_count} rows, daily={total_daily or 0}, commission={total_commission or 0}")
        else:
            print("[WARNING] No strategy data found (table might be empty)")
        print()
        
        # Step 7: Compare with Use Case 1
        print("Step 7: Comparing with Use Case 1 (working case)...")
        result = conn.execute(text("""
            SELECT use_case_id, name, input_table_name
            FROM use_cases
            WHERE name ILIKE '%trading%pnl%'
            LIMIT 1
        """))
        
        uc1 = result.fetchone()
        if uc1:
            uc1_id, uc1_name, uc1_table = uc1
            print(f"[COMPARISON] Use Case 1:")
            print(f"   ID: {uc1_id}")
            print(f"   Name: {uc1_name}")
            print(f"   Input Table: {uc1_table}")
            
            # Check UC1 results
            result = conn.execute(text("""
                SELECT COUNT(*) as result_count
                FROM fact_calculated_results fcr
                JOIN use_case_runs ucr ON fcr.run_id = ucr.run_id
                WHERE ucr.use_case_id = :uc1_id
            """), {"uc1_id": str(uc1_id)})
            
            uc1_results = result.fetchone()
            if uc1_results:
                uc1_count = uc1_results[0]
                print(f"   Saved Results: {uc1_count} rows")
        print()
        
        # Summary
        print("=" * 80)
        print("ROOT CAUSE SUMMARY")
        print("=" * 80)
        print()
        print("Potential Root Causes:")
        print()
        print("1. [DATA] fact_pnl_use_case_3 table is empty")
        print("   → Solution: Populate with test data")
        print()
        print("2. [CALCULATION] No calculation runs executed")
        print("   → Solution: Click 'Run Calculation' button in Tab 4")
        print()
        print("3. [RESULTS] Calculation ran but results not saved")
        print("   → Solution: Check calculation logs for errors")
        print()
        print("4. [HIERARCHY] No hierarchy nodes imported")
        print("   → Solution: Import hierarchy structure in Tab 1")
        print()
        print("5. [ROLLUP] Strategy rollup function failing silently")
        print("   → Solution: Check _calculate_strategy_rollup implementation")
        print()
        
        return 0

if __name__ == "__main__":
    exit(main())

