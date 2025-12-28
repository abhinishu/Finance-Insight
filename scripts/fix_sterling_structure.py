"""
Fix Broken Hierarchy Link for Project Sterling
Transplants the working atlas_structure_id from America Trading P&L to Project Sterling.
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.database import get_database_url

def fix_sterling_structure():
    """Fix Project Sterling hierarchy by using America Trading's working structure."""
    db_url = get_database_url()
    engine = create_engine(db_url)
    
    print("=" * 80)
    print("FIX PROJECT STERLING HIERARCHY LINK".center(80))
    print("=" * 80)
    
    with engine.begin() as conn:  # Use transaction
        # 1. Identify the Working Structure (America Trading P&L)
        print("\n--- STEP 1: IDENTIFY WORKING STRUCTURE ---")
        
        america_query = text("""
            SELECT use_case_id, name, atlas_structure_id 
            FROM use_cases 
            WHERE name = 'America Trading P&L' 
            LIMIT 1
        """)
        america_result = conn.execute(america_query).fetchone()
        
        if not america_result:
            print("ERROR: 'America Trading P&L' use case not found!")
            return
        
        america_id = america_result[0]
        america_name = america_result[1]
        working_structure_id = america_result[2]
        
        print(f"  America Trading P&L:")
        print(f"    Use Case ID: {america_id}")
        print(f"    Name: {america_name}")
        print(f"    Atlas Structure ID: {working_structure_id}")
        
        # 2. Check Current Project Sterling Structure
        print("\n--- STEP 2: CHECK CURRENT PROJECT STERLING STRUCTURE ---")
        
        sterling_before_query = text("""
            SELECT use_case_id, name, atlas_structure_id 
            FROM use_cases 
            WHERE name LIKE 'Project Sterling%' 
            LIMIT 1
        """)
        sterling_before = conn.execute(sterling_before_query).fetchone()
        
        if not sterling_before:
            print("ERROR: 'Project Sterling' use case not found!")
            return
        
        sterling_id = sterling_before[0]
        sterling_name = sterling_before[1]
        old_structure_id = sterling_before[2]
        
        print(f"  Project Sterling (BEFORE):")
        print(f"    Use Case ID: {sterling_id}")
        print(f"    Name: {sterling_name}")
        print(f"    Current Atlas Structure ID: {old_structure_id}")
        
        # 3. Perform the Transplant
        print("\n--- STEP 3: PERFORM STRUCTURE TRANSPLANT ---")
        
        update_query = text("""
            UPDATE use_cases
            SET atlas_structure_id = :structure_id
            WHERE name LIKE 'Project Sterling%'
        """)
        
        result = conn.execute(update_query, {"structure_id": working_structure_id})
        print(f"  [SUCCESS] Updated {result.rowcount} Project Sterling record(s)")
        
        # 4. Verify the Update
        print("\n--- STEP 4: VERIFY UPDATE ---")
        
        sterling_after_query = text("""
            SELECT use_case_id, name, atlas_structure_id 
            FROM use_cases 
            WHERE name LIKE 'Project Sterling%' 
            LIMIT 1
        """)
        sterling_after = conn.execute(sterling_after_query).fetchone()
        
        new_structure_id = sterling_after[2]
        print(f"  Project Sterling (AFTER):")
        print(f"    Use Case ID: {sterling_after[0]}")
        print(f"    Name: {sterling_after[1]}")
        print(f"    New Atlas Structure ID: {new_structure_id}")
        
        if new_structure_id == working_structure_id:
            print(f"  [SUCCESS] Structure transplant confirmed!")
        else:
            print(f"  [ERROR] Structure transplant failed!")
            return
        
        # 5. Cleanup Orphaned Data (Delete calculation_runs for Project Sterling)
        print("\n--- STEP 5: CLEANUP ORPHANED CALCULATION RUNS ---")
        
        # Count existing runs
        count_runs_query = text("""
            SELECT COUNT(*) 
            FROM calculation_runs 
            WHERE use_case_id = :sterling_id
        """)
        run_count = conn.execute(count_runs_query, {"sterling_id": sterling_id}).scalar()
        print(f"  Existing calculation_runs for Project Sterling: {run_count}")
        
        if run_count > 0:
            # Delete calculation results first (foreign key constraint)
            delete_results_query = text("""
                DELETE FROM fact_calculated_results
                WHERE calculation_run_id IN (
                    SELECT id FROM calculation_runs WHERE use_case_id = :sterling_id
                )
            """)
            deleted_results = conn.execute(delete_results_query, {"sterling_id": sterling_id})
            print(f"  [SUCCESS] Deleted {deleted_results.rowcount} fact_calculated_results records")
            
            # Delete calculation runs
            delete_runs_query = text("""
                DELETE FROM calculation_runs
                WHERE use_case_id = :sterling_id
            """)
            deleted_runs = conn.execute(delete_runs_query, {"sterling_id": sterling_id})
            print(f"  [SUCCESS] Deleted {deleted_runs.rowcount} calculation_runs records")
        else:
            print(f"  [INFO] No calculation_runs to delete")
        
        # 6. Verification Log
        print("\n--- STEP 6: FINAL VERIFICATION ---")
        print(f"  Project Sterling now uses Atlas Structure: {new_structure_id}")
        print(f"  This is the SAME structure as America Trading P&L")
        print(f"  Project Sterling should now display the full 'Global Trading P&L' hierarchy")
    
    print("\n" + "=" * 80)
    print("STRUCTURE TRANSPLANT COMPLETE".center(80))
    print("=" * 80)
    print("\nExpected Result:")
    print("  - Project Sterling will use the same hierarchy as America Trading P&L")
    print("  - Tab 3 should display the full 'Global Trading P&L' tree")
    print("  - Waterfall should process the $9.5M facts correctly")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    try:
        fix_sterling_structure()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


