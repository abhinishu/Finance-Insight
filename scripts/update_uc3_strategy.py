"""
Update strategy column in fact_pnl_use_case_3 table for Use Case 3 data alignment testing.
Changes 'Commissions (Non Swap)' to 'CORE'.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("=" * 80)
    print("UPDATING STRATEGY IN fact_pnl_use_case_3")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        # Step 1: Verify the count (Should be 376)
        print("Step 1: Verifying row count for 'Commissions (Non Swap)'...")
        result = conn.execute(text("""
            SELECT COUNT(*) as row_count 
            FROM fact_pnl_use_case_3 
            WHERE strategy = 'Commissions (Non Swap)'
        """))
        row = result.fetchone()
        count_before = row[0] if row else 0
        print(f"   Found {count_before} rows with strategy = 'Commissions (Non Swap)'")
        print()
        
        if count_before == 0:
            print("   [WARNING] No rows found to update. Exiting.")
            return
        
        if count_before != 376:
            print(f"   [WARNING] Expected 376 rows, but found {count_before} rows.")
            print(f"   Proceeding with update anyway (difference: {count_before - 376} rows)")
        
        # Step 2: Execute the Update
        print("Step 2: Executing UPDATE...")
        update_result = conn.execute(text("""
            UPDATE fact_pnl_use_case_3
            SET strategy = 'CORE'
            WHERE strategy = 'Commissions (Non Swap)'
        """))
        rows_affected = update_result.rowcount
        conn.commit()
        print(f"   Updated {rows_affected} rows")
        print()
        
        # Step 3: Verify the update
        print("Step 3: Verifying the update...")
        result = conn.execute(text("""
            SELECT COUNT(*) as new_core_count 
            FROM fact_pnl_use_case_3 
            WHERE strategy = 'CORE'
        """))
        row = result.fetchone()
        count_after = row[0] if row else 0
        print(f"   Total rows with strategy = 'CORE': {count_after}")
        print()
        
        # Additional verification: Check if any 'Commissions (Non Swap)' remain
        result = conn.execute(text("""
            SELECT COUNT(*) as remaining_count 
            FROM fact_pnl_use_case_3 
            WHERE strategy = 'Commissions (Non Swap)'
        """))
        row = result.fetchone()
        remaining = row[0] if row else 0
        print(f"   Remaining rows with strategy = 'Commissions (Non Swap)': {remaining}")
        print()
        
        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"   Rows before update: {count_before}")
        print(f"   Rows updated: {rows_affected}")
        print(f"   Total 'CORE' rows after update: {count_after}")
        print(f"   Remaining 'Commissions (Non Swap)' rows: {remaining}")
        
        if rows_affected == count_before and remaining == 0:
            print()
            print("   [SUCCESS] Update completed successfully!")
        else:
            print()
            print("   [WARNING] Update completed, but row counts don't match expected values.")
        print("=" * 80)

if __name__ == "__main__":
    main()

