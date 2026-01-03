"""
Physical Database Verification Script
Checks fact_pnl_entries table to verify data exists for each use case.
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.database import get_database_url

def check_pnl_data():
    """Print database state for fact_pnl_entries."""
    db_url = get_database_url()
    engine = create_engine(db_url)
    
    print("=" * 80)
    print("PHYSICAL DATABASE VERIFICATION - fact_pnl_entries")
    print("=" * 80)
    
    with engine.connect() as conn:
        # Query 1: Group by use_case_id
        print("\n1. FACT_PNL_ENTRIES BY USE_CASE_ID:")
        print("-" * 80)
        result = conn.execute(text("""
            SELECT 
                use_case_id,
                COUNT(*) as row_count,
                SUM(daily_amount) as total_daily,
                SUM(wtd_amount) as total_wtd,
                SUM(ytd_amount) as total_ytd
            FROM fact_pnl_entries
            GROUP BY use_case_id
            ORDER BY use_case_id
        """))
        
        rows = result.fetchall()
        if rows:
            for row in rows:
                print(f"  Use Case ID: {row[0]}")
                print(f"    Row Count: {row[1]}")
                print(f"    Total Daily: ${row[2]:,.2f}" if row[2] else "    Total Daily: $0.00")
                print(f"    Total WTD: ${row[3]:,.2f}" if row[3] else "    Total WTD: $0.00")
                print(f"    Total YTD: ${row[4]:,.2f}" if row[4] else "    Total YTD: $0.00")
                print()
        else:
            print("  ❌ NO ROWS FOUND in fact_pnl_entries")
        
        # Query 2: Get use case names
        print("\n2. USE CASE NAMES:")
        print("-" * 80)
        result2 = conn.execute(text("""
            SELECT 
                use_case_id,
                name,
                atlas_structure_id
            FROM use_cases
            ORDER BY name
        """))
        
        use_cases = result2.fetchall()
        if use_cases:
            for uc in use_cases:
                print(f"  Use Case ID: {uc[0]}")
                print(f"    Name: {uc[1]}")
                print(f"    Structure ID: {uc[2]}")
                print()
        else:
            print("  ❌ NO USE CASES FOUND")
        
        # Query 3: Total across all use cases
        print("\n3. TOTAL ACROSS ALL USE CASES:")
        print("-" * 80)
        result3 = conn.execute(text("""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT use_case_id) as unique_use_cases,
                SUM(daily_amount) as grand_total_daily,
                SUM(wtd_amount) as grand_total_wtd,
                SUM(ytd_amount) as grand_total_ytd
            FROM fact_pnl_entries
        """))
        
        totals = result3.fetchone()
        if totals:
            print(f"  Total Rows: {totals[0]}")
            print(f"  Unique Use Cases: {totals[1]}")
            print(f"  Grand Total Daily: ${totals[2]:,.2f}" if totals[2] else "  Grand Total Daily: $0.00")
            print(f"  Grand Total WTD: ${totals[3]:,.2f}" if totals[3] else "  Grand Total WTD: $0.00")
            print(f"  Grand Total YTD: ${totals[4]:,.2f}" if totals[4] else "  Grand Total YTD: $0.00")
        
        # Query 4: Sample rows for each use case
        print("\n4. SAMPLE ROWS (first 3 per use_case_id):")
        print("-" * 80)
        result4 = conn.execute(text("""
            SELECT 
                use_case_id,
                category_code,
                daily_amount,
                wtd_amount,
                ytd_amount,
                pnl_date,
                scenario
            FROM fact_pnl_entries
            ORDER BY use_case_id, category_code
            LIMIT 10
        """))
        
        samples = result4.fetchall()
        if samples:
            for sample in samples:
                print(f"  Use Case: {sample[0]}, Category: {sample[1]}, Daily: ${sample[2]:,.2f}, Date: {sample[5]}, Scenario: {sample[6]}")
        else:
            print("  ❌ NO SAMPLE ROWS FOUND")
    
    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    try:
        check_pnl_data()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()



