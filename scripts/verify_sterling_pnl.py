"""
Verification script to test fact_pnl_entries data for Project Sterling.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Get database URL from environment or use default
database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/finance_insight')

# Create database connection
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Test query: Sum of daily_amount from fact_pnl_entries
    # First, find Project Sterling use case ID
    result = session.execute(text("""
        SELECT use_case_id, name 
        FROM use_cases 
        WHERE name LIKE '%Sterling%' OR name LIKE '%sterling%'
        LIMIT 1
    """)).fetchone()
    
    if result:
        use_case_id = result[0]
        use_case_name = result[1]
        print(f"Found Use Case: {use_case_name} (ID: {use_case_id})")
        
        # Sum daily_amount for this use case
        sum_result = session.execute(text("""
            SELECT 
                COUNT(*) as row_count,
                SUM(daily_amount) as total_daily,
                SUM(wtd_amount) as total_wtd,
                SUM(ytd_amount) as total_ytd
            FROM fact_pnl_entries
            WHERE use_case_id = :use_case_id
        """), {"use_case_id": use_case_id}).fetchone()
        
        print(f"\n=== Fact P&L Entries Summary ===")
        print(f"Row Count: {sum_result[0]}")
        print(f"Total Daily Amount: ${sum_result[1]:,.2f}" if sum_result[1] else "Total Daily Amount: $0.00")
        print(f"Total WTD Amount: ${sum_result[2]:,.2f}" if sum_result[2] else "Total WTD Amount: $0.00")
        print(f"Total YTD Amount: ${sum_result[3]:,.2f}" if sum_result[3] else "Total YTD Amount: $0.00")
        
        if sum_result[1] and float(sum_result[1]) > 0:
            print(f"\n✅ SUCCESS: Found ${sum_result[1]:,.2f} in daily_amount for Project Sterling")
        else:
            print(f"\n❌ WARNING: No daily_amount found for Project Sterling")
    else:
        print("❌ ERROR: Project Sterling use case not found")
        
        # Show all use cases
        all_use_cases = session.execute(text("SELECT use_case_id, name FROM use_cases")).fetchall()
        print(f"\nAvailable Use Cases:")
        for uc in all_use_cases:
            print(f"  - {uc[1]} (ID: {uc[0]})")
    
    # Also check total across all use cases
    total_result = session.execute(text("""
        SELECT 
            COUNT(*) as row_count,
            SUM(daily_amount) as total_daily
        FROM fact_pnl_entries
    """)).fetchone()
    
    print(f"\n=== Overall fact_pnl_entries Summary ===")
    print(f"Total Rows: {total_result[0]}")
    print(f"Total Daily Amount (All): ${total_result[1]:,.2f}" if total_result[1] else "Total Daily Amount: $0.00")
    
finally:
    session.close()

