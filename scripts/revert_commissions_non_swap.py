"""
Revert the strategy update: Change 378 rows from 'CORE' back to 'Commissions (Non Swap)'.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine

def main():
    print("=" * 80)
    print("REVERTING STRATEGY UPDATE: CORE -> Commissions (Non Swap)")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        # Step 1: Verify current state
        print("Step 1: Verifying current state...")
        print("-" * 80)
        
        # Check CORE rows
        result = conn.execute(text("""
            SELECT COUNT(*) as count, SUM(pnl_daily) as total_pnl
            FROM fact_pnl_use_case_3
            WHERE strategy = 'CORE'
        """))
        row = result.fetchone()
        core_count = row[0] if row else 0
        core_pnl = row[1] if row else 0
        print(f"   Current 'CORE' rows: {core_count}")
        print(f"   Total P&L for 'CORE': {core_pnl}")
        print()
        
        # Check Commissions (Non Swap) rows
        result = conn.execute(text("""
            SELECT COUNT(*) as count, SUM(pnl_daily) as total_pnl
            FROM fact_pnl_use_case_3
            WHERE strategy = 'Commissions (Non Swap)'
        """))
        row = result.fetchone()
        cns_count = row[0] if row else 0
        cns_pnl = row[1] if row else 0
        print(f"   Current 'Commissions (Non Swap)' rows: {cns_count}")
        print(f"   Total P&L for 'Commissions (Non Swap)': {cns_pnl}")
        print()
        
        if core_count == 0:
            print("   [WARNING] No 'CORE' rows found to revert. Nothing to do.")
            return
        
        if core_count != 378:
            print(f"   [WARNING] Expected 378 'CORE' rows, but found {core_count}.")
            print(f"   Proceeding with revert of {core_count} rows anyway.")
            print()
        
        # Step 2: Execute the revert
        print("Step 2: Executing REVERT UPDATE...")
        print("-" * 80)
        update_result = conn.execute(text("""
            UPDATE fact_pnl_use_case_3
            SET strategy = 'Commissions (Non Swap)'
            WHERE strategy = 'CORE'
        """))
        rows_affected = update_result.rowcount
        conn.commit()
        print(f"   Reverted {rows_affected} rows from 'CORE' to 'Commissions (Non Swap)'")
        print()
        
        # Step 3: Verify the revert
        print("Step 3: Verifying the revert...")
        print("-" * 80)
        
        # Check CORE rows after revert
        result = conn.execute(text("""
            SELECT COUNT(*) as count, SUM(pnl_daily) as total_pnl
            FROM fact_pnl_use_case_3
            WHERE strategy = 'CORE'
        """))
        row = result.fetchone()
        core_count_after = row[0] if row else 0
        core_pnl_after = row[1] if row else 0
        print(f"   'CORE' rows after revert: {core_count_after}")
        print(f"   Total P&L for 'CORE' after revert: {core_pnl_after}")
        print()
        
        # Check Commissions (Non Swap) rows after revert
        result = conn.execute(text("""
            SELECT COUNT(*) as count, SUM(pnl_daily) as total_pnl
            FROM fact_pnl_use_case_3
            WHERE strategy = 'Commissions (Non Swap)'
        """))
        row = result.fetchone()
        cns_count_after = row[0] if row else 0
        cns_pnl_after = row[1] if row else 0
        print(f"   'Commissions (Non Swap)' rows after revert: {cns_count_after}")
        print(f"   Total P&L for 'Commissions (Non Swap)' after revert: {cns_pnl_after}")
        print()
        
        # Step 4: Summary
        print("=" * 80)
        print("REVERT SUMMARY")
        print("=" * 80)
        print(f"   Rows reverted: {rows_affected}")
        print(f"   'CORE' rows before: {core_count} | After: {core_count_after}")
        print(f"   'Commissions (Non Swap)' rows before: {cns_count} | After: {cns_count_after}")
        print(f"   'Commissions (Non Swap)' P&L before: {cns_pnl} | After: {cns_pnl_after}")
        print()
        
        if rows_affected == core_count and cns_count_after == core_count:
            print("   [SUCCESS] Revert completed successfully!")
            print("   The 'Commissions (Non Swap)' node should now show P&L correctly in Tab 3.")
        else:
            print("   [WARNING] Revert completed, but row counts don't match expected values.")
        print("=" * 80)

if __name__ == "__main__":
    main()

