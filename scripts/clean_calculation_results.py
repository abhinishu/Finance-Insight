"""
Clean calculation results for Project Sterling and America Trading.
This clears stale results to ensure fresh data sync.
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.database import get_database_url

def clean_calculation_results():
    """Delete calculation_runs and fact_calculated_results for both use cases."""
    db_url = get_database_url()
    engine = create_engine(db_url)
    
    project_sterling_id = 'a26121d8-9e01-4e70-9761-588b1854fe06'
    america_trading_id = 'b90f1708-4087-4117-9820-9226ed1115bb'
    
    print("=" * 80)
    print("CLEANING CALCULATION RESULTS")
    print("=" * 80)
    
    with engine.begin() as conn:  # Use transaction
        # 1. Check current state
        print("\n--- BEFORE CLEANUP ---")
        
        # Check calculation_runs
        runs_query = text("""
            SELECT use_case_id, COUNT(*) as count, MAX(executed_at) as latest_run
            FROM calculation_runs
            WHERE use_case_id IN (:id1, :id2)
            GROUP BY use_case_id
        """)
        runs_result = conn.execute(runs_query, {"id1": project_sterling_id, "id2": america_trading_id})
        runs_before = runs_result.fetchall()
        
        print("\nCalculation Runs:")
        if runs_before:
            for row in runs_before:
                print(f"  Use Case ID: {row[0]}")
                print(f"    Count: {row[1]}")
                print(f"    Latest: {row[2]}")
        else:
            print("  No calculation runs found")
        
        # Check fact_calculated_results (via calculation_runs join)
        results_query = text("""
            SELECT cr.use_case_id, COUNT(*) as count, SUM((fcr.measure_vector->>'daily')::numeric) as total_daily
            FROM fact_calculated_results fcr
            JOIN calculation_runs cr ON fcr.calculation_run_id = cr.id
            WHERE cr.use_case_id IN (:id1, :id2)
            GROUP BY cr.use_case_id
        """)
        results_result = conn.execute(results_query, {"id1": project_sterling_id, "id2": america_trading_id})
        results_before = results_result.fetchall()
        
        print("\nFact Calculated Results:")
        if results_before:
            for row in results_before:
                print(f"  Use Case ID: {row[0]}")
                print(f"    Count: {row[1]}")
                print(f"    Total Daily: ${row[2]:,.2f}" if row[2] else "    Total Daily: $0.00")
        else:
            print("  No calculated results found")
        
        # 2. Delete fact_calculated_results first (foreign key constraint)
        print("\n--- DELETING FACT_CALCULATED_RESULTS ---")
        delete_results = text("""
            DELETE FROM fact_calculated_results
            WHERE calculation_run_id IN (
                SELECT id FROM calculation_runs
                WHERE use_case_id IN (:id1, :id2)
            )
        """)
        results_deleted = conn.execute(delete_results, {"id1": project_sterling_id, "id2": america_trading_id})
        print(f"[SUCCESS] Deleted {results_deleted.rowcount} rows from fact_calculated_results")
        
        # 3. Delete calculation_runs
        print("\n--- DELETING CALCULATION_RUNS ---")
        delete_runs = text("""
            DELETE FROM calculation_runs
            WHERE use_case_id IN (:id1, :id2)
        """)
        runs_deleted = conn.execute(delete_runs, {"id1": project_sterling_id, "id2": america_trading_id})
        print(f"[SUCCESS] Deleted {runs_deleted.rowcount} rows from calculation_runs")
        
        # 4. Verify fact_pnl_entries remain intact
        print("\n--- VERIFYING FACT_PNL_ENTRIES (Should Remain Unchanged) ---")
        verify_query = text("""
            SELECT 
                use_case_id,
                COUNT(*) as row_count,
                SUM(daily_amount) as total_daily,
                SUM(wtd_amount) as total_wtd,
                SUM(ytd_amount) as total_ytd
            FROM fact_pnl_entries
            WHERE use_case_id IN (:id1, :id2)
            GROUP BY use_case_id
        """)
        verify_result = conn.execute(verify_query, {"id1": project_sterling_id, "id2": america_trading_id})
        verify_data = verify_result.fetchall()
        
        print("\nFact P&L Entries (Raw Data):")
        for row in verify_data:
            print(f"  Use Case ID: {row[0]}")
            print(f"    Row Count: {row[1]}")
            print(f"    Total Daily: ${row[2]:,.2f}" if row[2] else "    Total Daily: $0.00")
            print(f"    Total WTD: ${row[3]:,.2f}" if row[3] else "    Total WTD: $0.00")
            print(f"    Total YTD: ${row[4]:,.2f}" if row[4] else "    Total YTD: $0.00")
        
        # 5. Verify cleanup
        print("\n--- AFTER CLEANUP VERIFICATION ---")
        runs_after = conn.execute(runs_query, {"id1": project_sterling_id, "id2": america_trading_id}).fetchall()
        # Use same query as before for results
        results_after = conn.execute(results_query, {"id1": project_sterling_id, "id2": america_trading_id}).fetchall()
        
        print("\nCalculation Runs Remaining:")
        if runs_after:
            for row in runs_after:
                print(f"  Use Case ID: {row[0]}, Count: {row[1]}")
        else:
            print("  [SUCCESS] All calculation runs deleted")
        
        print("\nFact Calculated Results Remaining:")
        if results_after:
            for row in results_after:
                print(f"  Use Case ID: {row[0]}, Count: {row[1]}")
        else:
            print("  [SUCCESS] All calculated results deleted")
    
    print("\n" + "=" * 80)
    print("CLEANUP COMPLETE")
    print("=" * 80)
    print("\nExpected State:")
    print("  - Project Sterling: ~$9.5M in fact_pnl_entries (unchanged)")
    print("  - America Trading: ~$4.75M in fact_pnl_entries (unchanged)")
    print("  - No calculation_runs or fact_calculated_results for these use cases")

if __name__ == "__main__":
    try:
        clean_calculation_results()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

