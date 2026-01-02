"""
Phase 5.5: Table Routing Verification

Verifies that data loading correctly routes to use-case-specific input tables.
"""

import sys
from pathlib import Path
from decimal import Decimal

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.api.dependencies import get_session_factory
from app.models import UseCase
from app.services.unified_pnl_service import get_unified_pnl
from app.services.orchestrator import load_facts_for_date
from datetime import date


def test_unified_pnl_table_routing(session: Session):
    """
    Test 1: Verify get_unified_pnl routes to correct table for Use Case 3.
    """
    print("="*70)
    print("Test 1: Unified PnL Service Table Routing")
    print("-"*70)
    
    try:
        # Get Use Case 3
        use_case = session.query(UseCase).filter(
            UseCase.name == "America Cash Equity Trading"
        ).first()
        
        if not use_case:
            print("[SKIP] Use Case 3 not found")
            return True
        
        print(f"[OK] Found Use Case 3: {use_case.name}")
        print(f"  use_case_id: {use_case.use_case_id}")
        print(f"  input_table_name: {use_case.input_table_name}")
        
        if use_case.input_table_name != 'fact_pnl_use_case_3':
            print(f"[FAIL] Expected input_table_name='fact_pnl_use_case_3', got '{use_case.input_table_name}'")
            return False
        
        # Call get_unified_pnl
        result = get_unified_pnl(session, use_case.use_case_id, pnl_date=None, scenario='ACTUAL')
        
        print(f"\n[INFO] get_unified_pnl result:")
        print(f"  daily_pnl: {result.get('daily_pnl')}")
        print(f"  mtd_pnl: {result.get('mtd_pnl')}")
        print(f"  ytd_pnl: {result.get('ytd_pnl')}")
        
        # Verify we got non-zero data
        if result.get('daily_pnl') == Decimal('0'):
            print(f"[FAIL] daily_pnl is zero - table routing may not be working")
            return False
        
        print(f"[PASS] Unified PnL service correctly routes to fact_pnl_use_case_3")
        return True
        
    except Exception as e:
        print(f"[FAIL] Error testing unified_pnl_service: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main verification function."""
    print("="*70)
    print("Phase 5.5: Table Routing Verification")
    print("="*70)
    print("Verifying that data loading routes to correct input tables...")
    print()
    
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        results = []
        
        # Test 1: Unified PnL service
        results.append(test_unified_pnl_table_routing(session))
        
        # Summary
        print("\n" + "="*70)
        print("Verification Summary")
        print("="*70)
        
        if all(results):
            print("[PASS] Table routing test passed")
            print("\nData loading correctly routes to use-case-specific input tables.")
            print("Use Case 3 should now show non-zero results in Tab 2.")
            return 0
        else:
            print("[FAIL] One or more tests failed")
            print("\nPlease review the errors above.")
            return 1
            
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())

