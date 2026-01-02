"""
Manual Debug Run - Direct Execution Test
Tests the table routing logic by calling get_unified_pnl directly.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import UseCase
from app.services.unified_pnl_service import get_unified_pnl

def manual_debug_run():
    """
    Direct execution test for table routing logic.
    """
    print("=" * 70)
    print("MANUAL DEBUG RUN: Testing Table Routing Logic")
    print("=" * 70)
    print()
    
    # Setup: Initialize database session
    db: Session = SessionLocal()
    
    try:
        # Step 1: Fetch the "America Cash Equity Trading" Use Case
        use_case_name = "America Cash Equity Trading"
        print(f"Step 1: Fetching Use Case: '{use_case_name}'")
        print("-" * 70)
        
        use_case = db.query(UseCase).filter(UseCase.name == use_case_name).first()
        
        if not use_case:
            print(f"[ERROR] Use Case '{use_case_name}' not found!")
            return
        
        print(f"[OK] Found Use Case:")
        print(f"     ID: {use_case.use_case_id}")
        print(f"     Name: {use_case.name}")
        print(f"     input_table_name (from Python object): {repr(use_case.input_table_name)}")
        print(f"     input_table_name type: {type(use_case.input_table_name)}")
        print()
        
        # Step 2: Call unified_pnl_service.get_unified_pnl()
        print("Step 2: Calling get_unified_pnl()")
        print("-" * 70)
        print(f"     Use Case ID: {use_case.use_case_id}")
        print()
        
        # Call the service function directly
        result = get_unified_pnl(
            session=db,
            use_case_id=use_case.use_case_id,
            pnl_date=None,
            scenario='ACTUAL'
        )
        
        # Step 3: Print Results
        print()
        print("Step 3: Results")
        print("=" * 70)
        print(f"Daily PnL: {result.get('daily_pnl', 'N/A')}")
        print(f"MTD PnL: {result.get('mtd_pnl', 'N/A')}")
        print(f"YTD PnL: {result.get('ytd_pnl', 'N/A')}")
        print()
        
        # Step 4: Print Debug Info
        print("Step 4: Debug Info")
        print("=" * 70)
        debug_info = result.get('_debug_info', {})
        
        if debug_info:
            print("Debug Information:")
            print(f"  use_case_id: {debug_info.get('use_case_id')}")
            print(f"  use_case_name: {debug_info.get('use_case_name')}")
            print(f"  source_table: {debug_info.get('source_table')}")
            print(f"  routing_reason: {debug_info.get('routing_reason')}")
            print(f"  raw_input_table_name: {debug_info.get('raw_input_table_name')}")
            print(f"  processed_input_table_name: {debug_info.get('processed_input_table_name')}")
            print(f"  query_executed: {debug_info.get('query_executed')}")
            print(f"  result_daily: {debug_info.get('result_daily')}")
            print(f"  result_mtd: {debug_info.get('result_mtd')}")
            print(f"  result_ytd: {debug_info.get('result_ytd')}")
            print(f"  fallback_used: {debug_info.get('fallback_used', False)}")
            if debug_info.get('fallback_used'):
                print(f"  fallback_type: {debug_info.get('fallback_type')}")
        else:
            print("[WARNING] No debug_info found in response!")
            print("          This suggests the function may not have been updated with debug logging.")
        print()
        
        # Step 5: Verification
        print("Step 5: Verification")
        print("=" * 70)
        source_table = debug_info.get('source_table') if debug_info else None
        daily_value = result.get('daily_pnl', Decimal('0'))
        expected_wrong_value = Decimal('3482637.13')  # This is from fact_pnl_gold
        
        print(f"Expected Source Table: 'fact_pnl_use_case_3'")
        print(f"Actual Source Table: {repr(source_table)}")
        print()
        
        if source_table == 'fact_pnl_use_case_3':
            print("[PASS] Source table is correct: 'fact_pnl_use_case_3'")
        else:
            print(f"[FAIL] Source table is WRONG! Expected 'fact_pnl_use_case_3', got {repr(source_table)}")
        
        print()
        print(f"Daily PnL Value: {daily_value}")
        print(f"Expected Wrong Value (from fact_pnl_gold): {expected_wrong_value}")
        print()
        
        if abs(daily_value - expected_wrong_value) < Decimal('0.01'):
            print("[WARNING] Daily PnL matches fact_pnl_gold value!")
            print("          This suggests the query may have hit the wrong table.")
        else:
            print("[OK] Daily PnL is DIFFERENT from fact_pnl_gold value.")
            print("     This suggests the query hit the correct table (fact_pnl_use_case_3).")
        
        print()
        print("=" * 70)
        print("MANUAL DEBUG RUN COMPLETE")
        print("=" * 70)
        
    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    from decimal import Decimal
    manual_debug_run()

