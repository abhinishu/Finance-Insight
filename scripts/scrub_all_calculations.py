"""
Scrub ALL calculation results from the database.
This removes any "poisoned" or stale calculation state.
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.database import get_database_url

def scrub_all_calculations():
    """Delete ALL rows from calculation_runs and fact_calculated_results."""
    db_url = get_database_url()
    engine = create_engine(db_url)
    
    print("=" * 80)
    print("SCRUBBING ALL CALCULATION RESULTS")
    print("=" * 80)
    
    with engine.begin() as conn:  # Use transaction
        # 1. Check current state
        print("\n--- BEFORE SCRUB ---")
        
        # Check calculation_runs
        runs_count = conn.execute(text("SELECT COUNT(*) FROM calculation_runs")).scalar()
        print(f"\nCalculation Runs: {runs_count} rows")
        
        # Check fact_calculated_results
        results_count = conn.execute(text("SELECT COUNT(*) FROM fact_calculated_results")).scalar()
        print(f"Fact Calculated Results: {results_count} rows")
        
        # 2. Delete fact_calculated_results first (foreign key constraint)
        print("\n--- DELETING ALL FACT_CALCULATED_RESULTS ---")
        delete_results = text("DELETE FROM fact_calculated_results")
        results_deleted = conn.execute(delete_results)
        print(f"[SUCCESS] Deleted {results_deleted.rowcount} rows from fact_calculated_results")
        
        # 3. Delete calculation_runs
        print("\n--- DELETING ALL CALCULATION_RUNS ---")
        delete_runs = text("DELETE FROM calculation_runs")
        runs_deleted = conn.execute(delete_runs)
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
            GROUP BY use_case_id
        """)
        verify_result = conn.execute(verify_query)
        verify_data = verify_result.fetchall()
        
        print("\nFact P&L Entries (Raw Data):")
        for row in verify_data:
            print(f"  Use Case ID: {row[0]}")
            print(f"    Row Count: {row[1]}")
            print(f"    Total Daily: ${row[2]:,.2f}" if row[2] else "    Total Daily: $0.00")
            print(f"    Total WTD: ${row[3]:,.2f}" if row[3] else "    Total WTD: $0.00")
            print(f"    Total YTD: ${row[4]:,.2f}" if row[4] else "    Total YTD: $0.00")
        
        # 5. Verify cleanup
        print("\n--- AFTER SCRUB VERIFICATION ---")
        runs_after = conn.execute(text("SELECT COUNT(*) FROM calculation_runs")).scalar()
        results_after = conn.execute(text("SELECT COUNT(*) FROM fact_calculated_results")).scalar()
        
        print(f"\nCalculation Runs Remaining: {runs_after}")
        print(f"Fact Calculated Results Remaining: {results_after}")
        
        if runs_after == 0 and results_after == 0:
            print("\n[SUCCESS] All calculation results scrubbed successfully")
        else:
            print("\n[WARNING] Some calculation results remain")
    
    print("\n" + "=" * 80)
    print("SCRUB COMPLETE")
    print("=" * 80)
    print("\nExpected State:")
    print("  - Project Sterling: ~$9.5M in fact_pnl_entries (unchanged)")
    print("  - America Trading: ~$4.75M in fact_pnl_entries (unchanged)")
    print("  - No calculation_runs or fact_calculated_results in database")

if __name__ == "__main__":
    try:
        scrub_all_calculations()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


