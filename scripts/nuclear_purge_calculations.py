"""
Nuclear Purge Script
Deletes ALL records from calculation_runs and fact_calculated_results for both use cases.
This forces Tab 3 to fetch fresh baseline from unified_pnl_service.
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.database import get_database_url

def nuclear_purge():
    """Delete all calculation runs and results for Project Sterling and America Trading."""
    db_url = get_database_url()
    engine = create_engine(db_url)
    
    print("=" * 80)
    print("NUCLEAR PURGE: CALCULATION RUNS AND RESULTS".center(80))
    print("=" * 80)
    
    with engine.begin() as conn:  # Use transaction
        # 1. Find UUIDs from use_cases table
        print("\n--- FINDING USE CASE UUIDs ---")
        
        sterling_query = text("""
            SELECT use_case_id, name 
            FROM use_cases 
            WHERE name LIKE '%Sterling%' OR name LIKE '%Project Sterling%'
            LIMIT 1
        """)
        sterling_result = conn.execute(sterling_query).fetchone()
        
        if not sterling_result:
            print("ERROR: Project Sterling use case not found!")
            return
        
        sterling_id = sterling_result[0]
        sterling_name = sterling_result[1]
        print(f"  Project Sterling:")
        print(f"    ID: {sterling_id}")
        print(f"    Name: {sterling_name}")
        
        america_query = text("""
            SELECT use_case_id, name 
            FROM use_cases 
            WHERE name LIKE '%America Trading%' OR name LIKE '%America%'
            LIMIT 1
        """)
        america_result = conn.execute(america_query).fetchone()
        
        if not america_result:
            print("ERROR: America Trading use case not found!")
            return
        
        america_id = america_result[0]
        america_name = america_result[1]
        print(f"  America Trading:")
        print(f"    ID: {america_id}")
        print(f"    Name: {america_name}")
        
        # 2. Count existing calculation runs
        print("\n--- BEFORE PURGE ---")
        count_runs_query = text("""
            SELECT 
                uc.name,
                COUNT(cr.id) as run_count
            FROM use_cases uc
            LEFT JOIN calculation_runs cr ON cr.use_case_id = uc.use_case_id
            WHERE uc.use_case_id IN (:sterling_id, :america_id)
            GROUP BY uc.name
        """)
        before_runs = conn.execute(count_runs_query, {
            "sterling_id": sterling_id,
            "america_id": america_id
        }).fetchall()
        
        print("\nExisting calculation_runs:")
        for row in before_runs:
            print(f"  {row[0]}: {row[1]} runs")
        
        count_results_query = text("""
            SELECT 
                uc.name,
                COUNT(fcr.result_id) as result_count
            FROM use_cases uc
            LEFT JOIN calculation_runs cr ON cr.use_case_id = uc.use_case_id
            LEFT JOIN fact_calculated_results fcr ON fcr.run_id = cr.id
            WHERE uc.use_case_id IN (:sterling_id, :america_id)
            GROUP BY uc.name
        """)
        before_results = conn.execute(count_results_query, {
            "sterling_id": sterling_id,
            "america_id": america_id
        }).fetchall()
        
        print("\nExisting fact_calculated_results:")
        for row in before_results:
            print(f"  {row[0]}: {row[1]} results")
        
        # 3. Delete fact_calculated_results first (foreign key constraint)
        print("\n--- PURGING fact_calculated_results ---")
        delete_results_query = text("""
            DELETE FROM fact_calculated_results
            WHERE run_id IN (
                SELECT id FROM calculation_runs
                WHERE use_case_id IN (:sterling_id, :america_id)
            )
        """)
        results_deleted = conn.execute(delete_results_query, {
            "sterling_id": sterling_id,
            "america_id": america_id
        })
        print(f"  [SUCCESS] Deleted {results_deleted.rowcount} fact_calculated_results records")
        
        # 4. Delete calculation_runs
        print("\n--- PURGING calculation_runs ---")
        delete_runs_query = text("""
            DELETE FROM calculation_runs
            WHERE use_case_id IN (:sterling_id, :america_id)
        """)
        runs_deleted = conn.execute(delete_runs_query, {
            "sterling_id": sterling_id,
            "america_id": america_id
        })
        print(f"  [SUCCESS] Deleted {runs_deleted.rowcount} calculation_runs records")
        
        # 5. Verify purge
        print("\n--- AFTER PURGE ---")
        after_runs = conn.execute(count_runs_query, {
            "sterling_id": sterling_id,
            "america_id": america_id
        }).fetchall()
        
        print("\nRemaining calculation_runs:")
        for row in after_runs:
            print(f"  {row[0]}: {row[1]} runs")
        
        after_results = conn.execute(count_results_query, {
            "sterling_id": sterling_id,
            "america_id": america_id
        }).fetchall()
        
        print("\nRemaining fact_calculated_results:")
        for row in after_results:
            print(f"  {row[0]}: {row[1]} results")
        
        # 6. Verify fact_pnl_entries remain intact
        print("\n--- VERIFYING fact_pnl_entries (should remain intact) ---")
        verify_entries_query = text("""
            SELECT 
                uc.name,
                COUNT(*) as row_count,
                SUM(f.daily_amount) as total_daily
            FROM fact_pnl_entries f
            JOIN use_cases uc ON f.use_case_id = uc.use_case_id
            WHERE f.use_case_id IN (:sterling_id, :america_id) AND f.scenario = 'ACTUAL'
            GROUP BY uc.name
        """)
        entries_check = conn.execute(verify_entries_query, {
            "sterling_id": sterling_id,
            "america_id": america_id
        }).fetchall()
        
        print("\nfact_pnl_entries (should be unchanged):")
        for row in entries_check:
            print(f"  {row[0]}: {row[1]} rows, Total Daily: ${row[2]:,.2f}")
    
    print("\n" + "=" * 80)
    print("NUCLEAR PURGE COMPLETE".center(80))
    print("=" * 80)
    print("\nExpected State:")
    print("  - calculation_runs: 0 records for both use cases")
    print("  - fact_calculated_results: 0 records for both use cases")
    print("  - fact_pnl_entries: UNCHANGED (baseline data intact)")
    print("\n" + "=" * 80)
    print("TAB 3 WILL NOW FETCH BASELINE FROM unified_pnl_service".center(80))
    print("=" * 80 + "\n")

if __name__ == "__main__":
    try:
        nuclear_purge()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

