"""
Fix Sterling Rules - Clone Working Rules and Purge Stale Results
Clones valid rules from America Trading P&L to Project Sterling.
Purges stale calculation results to force fresh recalculation.
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.database import get_database_url

def fix_sterling_rules():
    """Clone working rules from America Trading to Project Sterling and purge stale results."""
    db_url = get_database_url()
    engine = create_engine(db_url)
    
    print("=" * 80)
    print("RULE CLONING AND STALE RESULTS PURGE".center(80))
    print("=" * 80)
    
    STERLING_ID = "a26121d8-9e01-4e70-9761-588b1854fe06"
    AMERICA_ID = "b90f1708-4087-4117-9820-9226ed1115bb"
    
    with engine.begin() as conn:  # Use transaction
        print("\n--- STARTING RULE CLONE ---")
        
        # 1. Verify Use Cases Exist
        print("\n--- STEP 1: VERIFY USE CASES ---")
        sterling_check = text("""
            SELECT use_case_id, name 
            FROM use_cases 
            WHERE use_case_id = CAST(:uid AS uuid)
        """)
        sterling_result = conn.execute(sterling_check, {"uid": STERLING_ID}).fetchone()
        
        if not sterling_result:
            print(f"ERROR: Project Sterling use case not found (ID: {STERLING_ID})")
            return
        
        america_check = text("""
            SELECT use_case_id, name 
            FROM use_cases 
            WHERE use_case_id = CAST(:uid AS uuid)
        """)
        america_result = conn.execute(america_check, {"uid": AMERICA_ID}).fetchone()
        
        if not america_result:
            print(f"ERROR: America Trading P&L use case not found (ID: {AMERICA_ID})")
            return
        
        print(f"  Project Sterling: {sterling_result[1]} ({sterling_result[0]})")
        print(f"  America Trading: {america_result[1]} ({america_result[0]})")
        
        # 2. Count Existing Rules
        print("\n--- STEP 2: COUNT EXISTING RULES ---")
        sterling_count_query = text("""
            SELECT COUNT(*) 
            FROM metadata_rules 
            WHERE use_case_id = CAST(:uid AS uuid)
        """)
        sterling_count = conn.execute(sterling_count_query, {"uid": STERLING_ID}).scalar()
        print(f"  Existing Project Sterling rules: {sterling_count}")
        
        america_count_query = text("""
            SELECT COUNT(*) 
            FROM metadata_rules 
            WHERE use_case_id = CAST(:uid AS uuid)
        """)
        america_count = conn.execute(america_count_query, {"uid": AMERICA_ID}).scalar()
        print(f"  Existing America Trading rules: {america_count}")
        
        if america_count == 0:
            print("  WARNING: America Trading has no rules to clone!")
            return
        
        # 3. Delete Broken Sterling Rules
        print("\n--- STEP 3: DELETE BROKEN STERLING RULES ---")
        delete_query = text("""
            DELETE FROM metadata_rules 
            WHERE use_case_id = CAST(:uid AS uuid)
        """)
        deleted = conn.execute(delete_query, {"uid": STERLING_ID})
        print(f"  [SUCCESS] Deleted {deleted.rowcount} old broken rules from Project Sterling")
        
        # 4. Clone America Rules -> Sterling
        print("\n--- STEP 4: CLONE AMERICA RULES TO STERLING ---")
        # We copy node_id, sql_where, predicate_json, logic_en, etc. exactly
        # so they attach to the same tree nodes.
        sql_clone = text("""
            INSERT INTO metadata_rules (
                use_case_id, 
                node_id, 
                predicate_json, 
                sql_where, 
                logic_en, 
                last_modified_by,
                created_at,
                last_modified_at
            )
            SELECT 
                CAST(:new_uid AS uuid), 
                node_id, 
                predicate_json, 
                sql_where, 
                logic_en, 
                last_modified_by,
                NOW(),
                NOW()
            FROM metadata_rules 
            WHERE use_case_id = CAST(:source_uid AS uuid)
        """)
        cloned = conn.execute(sql_clone, {
            "new_uid": STERLING_ID, 
            "source_uid": AMERICA_ID
        })
        print(f"  [SUCCESS] Cloned {cloned.rowcount} valid rules from America Trading to Project Sterling")
        
        # 5. Verify Cloned Rules
        print("\n--- STEP 5: VERIFY CLONED RULES ---")
        verify_query = text("""
            SELECT COUNT(*), 
                   COUNT(DISTINCT node_id),
                   COUNT(CASE WHEN sql_where IS NOT NULL THEN 1 END) as rules_with_sql
            FROM metadata_rules 
            WHERE use_case_id = CAST(:uid AS uuid)
        """)
        verify_result = conn.execute(verify_query, {"uid": STERLING_ID}).fetchone()
        print(f"  Project Sterling rules after clone:")
        print(f"    Total rules: {verify_result[0]}")
        print(f"    Unique nodes: {verify_result[1]}")
        print(f"    Rules with SQL: {verify_result[2]}")
        
        # 6. PURGE ZOMBIE RESULTS (The 3.4M Ghost)
        print("\n--- STEP 6: PURGE STALE CALCULATION RESULTS ---")
        print("  This forces Tab 3 to show blanks until you run the Waterfall")
        
        # Count existing results
        count_results_query = text("""
            SELECT COUNT(*) 
            FROM fact_calculated_results 
            WHERE calculation_run_id IN (
                SELECT id FROM calculation_runs WHERE use_case_id = CAST(:uid AS uuid)
            )
        """)
        results_count = conn.execute(count_results_query, {"uid": STERLING_ID}).scalar()
        print(f"  Existing fact_calculated_results: {results_count}")
        
        count_runs_query = text("""
            SELECT COUNT(*) 
            FROM calculation_runs 
            WHERE use_case_id = CAST(:uid AS uuid)
        """)
        runs_count = conn.execute(count_runs_query, {"uid": STERLING_ID}).scalar()
        print(f"  Existing calculation_runs: {runs_count}")
        
        if results_count > 0:
            # Delete calculation results first (foreign key constraint)
            delete_results_query = text("""
                DELETE FROM fact_calculated_results 
                WHERE calculation_run_id IN (
                    SELECT id FROM calculation_runs WHERE use_case_id = CAST(:uid AS uuid)
                )
            """)
            deleted_results = conn.execute(delete_results_query, {"uid": STERLING_ID})
            print(f"  [SUCCESS] Deleted {deleted_results.rowcount} fact_calculated_results records")
        
        if runs_count > 0:
            # Delete calculation runs
            delete_runs_query = text("""
                DELETE FROM calculation_runs 
                WHERE use_case_id = CAST(:uid AS uuid)
            """)
            deleted_runs = conn.execute(delete_runs_query, {"uid": STERLING_ID})
            print(f"  [SUCCESS] Deleted {deleted_runs.rowcount} calculation_runs records")
        
        if results_count == 0 and runs_count == 0:
            print(f"  [INFO] No stale results to purge")
        
        # 7. Final Summary
        print("\n--- STEP 7: FINAL SUMMARY ---")
        print(f"  Project Sterling now has {verify_result[0]} rules (cloned from America Trading)")
        print(f"  All stale calculation results have been purged")
        print(f"  Project Sterling is reset and ready for fresh Waterfall calculation")
    
    print("\n" + "=" * 80)
    print("RULE CLONING AND PURGE COMPLETE".center(80))
    print("=" * 80)
    print("\nExpected Result:")
    print("  - Project Sterling has valid rules attached to visible tree nodes")
    print("  - Tab 3 will show blanks until 'Run Waterfall' is executed")
    print("  - No more $3.4M zombie data")
    print("  - Fresh calculation will produce correct Adjusted P&L")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    try:
        fix_sterling_rules()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

