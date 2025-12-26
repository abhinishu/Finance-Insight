"""
Differentiate America Trading P&L data by halving values.
This provides a visual "tell" in the UI to prove isolation is working.
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.database import get_database_url

def differentiate_america_trading():
    """Update America Trading P&L facts to be exactly half of current value."""
    db_url = get_database_url()
    engine = create_engine(db_url)
    
    america_trading_id = 'b90f1708-4087-4117-9820-9226ed1115bb'
    
    print("=" * 80)
    print("DIFFERENTIATING AMERICA TRADING P&L DATA")
    print("=" * 80)
    
    with engine.begin() as conn:  # Use transaction
        # Check current state
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as row_count,
                SUM(daily_amount) as total_daily,
                SUM(wtd_amount) as total_wtd,
                SUM(ytd_amount) as total_ytd
            FROM fact_pnl_entries
            WHERE use_case_id = :use_case_id
        """), {"use_case_id": america_trading_id})
        
        before = result.fetchone()
        print(f"\nBEFORE UPDATE (America Trading P&L):")
        print(f"  Row Count: {before[0]}")
        print(f"  Total Daily: ${before[1]:,.2f}" if before[1] else "  Total Daily: $0.00")
        print(f"  Total WTD: ${before[2]:,.2f}" if before[2] else "  Total WTD: $0.00")
        print(f"  Total YTD: ${before[3]:,.2f}" if before[3] else "  Total YTD: $0.00")
        
        # Update to half value
        update_result = conn.execute(text("""
            UPDATE fact_pnl_entries 
            SET 
                daily_amount = daily_amount * 0.5,
                wtd_amount = wtd_amount * 0.5,
                ytd_amount = ytd_amount * 0.5
            WHERE use_case_id = :use_case_id
        """), {"use_case_id": america_trading_id})
        
        print(f"\n[SUCCESS] Updated {update_result.rowcount} rows")
        
        # Check new state
        result2 = conn.execute(text("""
            SELECT 
                COUNT(*) as row_count,
                SUM(daily_amount) as total_daily,
                SUM(wtd_amount) as total_wtd,
                SUM(ytd_amount) as total_ytd
            FROM fact_pnl_entries
            WHERE use_case_id = :use_case_id
        """), {"use_case_id": america_trading_id})
        
        after = result2.fetchone()
        print(f"\nAFTER UPDATE (America Trading P&L):")
        print(f"  Row Count: {after[0]}")
        print(f"  Total Daily: ${after[1]:,.2f}" if after[1] else "  Total Daily: $0.00")
        print(f"  Total WTD: ${after[2]:,.2f}" if after[2] else "  Total WTD: $0.00")
        print(f"  Total YTD: ${after[3]:,.2f}" if after[3] else "  Total YTD: $0.00")
        
        # Verify Project Sterling is unchanged
        sterling_result = conn.execute(text("""
            SELECT 
                COUNT(*) as row_count,
                SUM(daily_amount) as total_daily
            FROM fact_pnl_entries
            WHERE use_case_id != :use_case_id
        """), {"use_case_id": america_trading_id})
        
        sterling = sterling_result.fetchone()
        print(f"\nPROJECT STERLING (Other Use Cases):")
        print(f"  Row Count: {sterling[0]}")
        print(f"  Total Daily: ${sterling[1]:,.2f}" if sterling[1] else "  Total Daily: $0.00")
    
    print("\n" + "=" * 80)
    print("DIFFERENTIATION COMPLETE")
    print("=" * 80)
    print("\nExpected Results:")
    print("  - Project Sterling: ~$9.5M (unchanged)")
    print("  - America Trading: ~$4.75M (half of original)")

if __name__ == "__main__":
    try:
        differentiate_america_trading()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

