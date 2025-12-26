"""
Force-Sync IDs Script
Force-syncs use_case_id in fact_pnl_entries to match use_cases table.
Sets America Trading daily_amount to exactly $2,500,000.00 for visual differentiation.
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.database import get_database_url
from decimal import Decimal

def force_sync_ids():
    """Force-sync use_case_ids and set America Trading to $2.5M."""
    db_url = get_database_url()
    engine = create_engine(db_url)
    
    print("=" * 80)
    print("FORCE-SYNC IDs AND AMERICA TRADING UPDATE".center(80))
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
        
        # 2. Check current state of fact_pnl_entries
        print("\n--- BEFORE FORCE-SYNC ---")
        before_query = text("""
            SELECT 
                uc.name,
                f.use_case_id,
                COUNT(*) as row_count,
                SUM(f.daily_amount) as total_daily,
                SUM(f.wtd_amount) as total_wtd,
                SUM(f.ytd_amount) as total_ytd
            FROM fact_pnl_entries f
            LEFT JOIN use_cases uc ON f.use_case_id = uc.use_case_id
            WHERE f.use_case_id IN (:sterling_id, :america_id)
            GROUP BY uc.name, f.use_case_id
        """)
        before_result = conn.execute(before_query, {
            "sterling_id": sterling_id,
            "america_id": america_id
        }).fetchall()
        
        print("\nCurrent fact_pnl_entries state:")
        for row in before_result:
            print(f"  Use Case: {row[0] or 'Unknown'}")
            print(f"    ID: {row[1]}")
            print(f"    Row Count: {row[2]}")
            print(f"    Total Daily: ${row[3]:,.2f}" if row[3] else "    Total Daily: $0.00")
            print(f"    Total WTD: ${row[4]:,.2f}" if row[4] else "    Total WTD: $0.00")
            print(f"    Total YTD: ${row[5]:,.2f}" if row[5] else "    Total YTD: $0.00")
        
        # 3. Force-sync Project Sterling rows (all 60 rows should use Sterling UUID)
        print("\n--- FORCE-SYNC PROJECT STERLING ROWS ---")
        # Find all rows that should be Project Sterling (by category_code pattern or current association)
        # We'll update all rows that match Sterling pattern to use the correct UUID
        update_sterling = text("""
            UPDATE fact_pnl_entries
            SET use_case_id = :sterling_id
            WHERE (
                category_code LIKE 'TRADE_%'
                AND use_case_id != :america_id
            )
            OR use_case_id = :sterling_id
        """)
        sterling_updated = conn.execute(update_sterling, {
            "sterling_id": sterling_id,
            "america_id": america_id
        })
        print(f"  [SUCCESS] Force-synced {sterling_updated.rowcount} Project Sterling rows")
        
        # 4. Force-sync America Trading rows and set to exactly $2,500,000.00
        print("\n--- FORCE-SYNC AMERICA TRADING ROWS TO $2.5M ---")
        
        # First, count current America Trading rows (ACTUAL scenario only)
        check_america = text("""
            SELECT COUNT(*), SUM(daily_amount) as current_total
            FROM fact_pnl_entries 
            WHERE use_case_id = :america_id AND scenario = 'ACTUAL'
        """)
        america_check = conn.execute(check_america, {"america_id": america_id}).fetchone()
        current_america_count = america_check[0] or 0
        current_america_total = Decimal(str(america_check[1])) if america_check[1] else Decimal('0')
        
        print(f"  Current America Trading rows (ACTUAL): {current_america_count}")
        print(f"  Current total daily_amount: ${current_america_total:,.2f}")
        
        # Calculate multiplier to reach exactly $2,500,000.00
        target_total = Decimal('2500000.00')
        
        if current_america_count > 0 and current_america_total > Decimal('0'):
            multiplier = float(target_total / current_america_total)
            print(f"  Multiplier to reach $2.5M: {multiplier:.6f}")
            
            # Update America Trading rows (ACTUAL scenario only)
            update_america = text("""
                UPDATE fact_pnl_entries
                SET 
                    use_case_id = :america_id,
                    daily_amount = daily_amount * :multiplier,
                    wtd_amount = wtd_amount * :multiplier,
                    ytd_amount = ytd_amount * :multiplier
                WHERE use_case_id = :america_id AND scenario = 'ACTUAL'
            """)
            america_updated = conn.execute(update_america, {
                "america_id": america_id,
                "multiplier": multiplier
            })
            print(f"  [SUCCESS] Force-synced and updated {america_updated.rowcount} America Trading rows")
        elif current_america_count > 0 and current_america_total == Decimal('0'):
            # If current total is 0 but rows exist, set each daily_amount to target_daily_total / row_count
            per_row_amount = target_total / current_america_count
            update_america = text("""
                UPDATE fact_pnl_entries
                SET
                    use_case_id = :america_id,
                    daily_amount = :per_row_amount,
                    wtd_amount = :per_row_amount,
                    ytd_amount = :per_row_amount
                WHERE use_case_id = :america_id AND scenario = 'ACTUAL'
            """)
            america_updated = conn.execute(update_america, {
                "america_id": america_id,
                "per_row_amount": per_row_amount
            })
            print(f"  [SUCCESS] Set {america_updated.rowcount} America Trading rows to distribute $2.5M")
        else:
            print("  WARNING: No America Trading rows found to update.")
        
        # 5. Verify final state
        print("\n--- AFTER FORCE-SYNC ---")
        after_query = text("""
            SELECT 
                uc.name,
                f.use_case_id,
                COUNT(*) as row_count,
                SUM(f.daily_amount) as total_daily,
                SUM(f.wtd_amount) as total_wtd,
                SUM(f.ytd_amount) as total_ytd
            FROM fact_pnl_entries f
            JOIN use_cases uc ON f.use_case_id = uc.use_case_id
            WHERE f.use_case_id IN (:sterling_id, :america_id) AND f.scenario = 'ACTUAL'
            GROUP BY uc.name, f.use_case_id
        """)
        after_result = conn.execute(after_query, {
            "sterling_id": sterling_id,
            "america_id": america_id
        }).fetchall()
        
        print("\nFinal fact_pnl_entries state (ACTUAL scenario only):")
        for row in after_result:
            print(f"  Use Case: {row[0]}")
            print(f"    ID: {row[1]}")
            print(f"    Row Count: {row[2]}")
            print(f"    Total Daily: ${row[3]:,.2f}" if row[3] else "    Total Daily: $0.00")
            print(f"    Total WTD: ${row[4]:,.2f}" if row[4] else "    Total WTD: $0.00")
            print(f"    Total YTD: ${row[5]:,.2f}" if row[5] else "    Total YTD: $0.00")
    
    print("\n" + "=" * 80)
    print("FORCE-SYNC COMPLETE".center(80))
    print("=" * 80)
    print("\nExpected State:")
    print(f"  - Project Sterling: ~$9.5M in fact_pnl_entries")
    print(f"  - America Trading: Exactly $2,500,000.00 in fact_pnl_entries")
    print("\n" + "=" * 80)
    print("BACKEND AND DATABASE ALIGNED. RESTART SERVER NOW.".center(80))
    print("=" * 80 + "\n")

if __name__ == "__main__":
    try:
        force_sync_ids()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

