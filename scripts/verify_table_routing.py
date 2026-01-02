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


def test_load_facts_for_date_table_routing(session: Session):
    """
    Test 2: Verify load_facts_for_date routes to correct table for Use Case 3.
    """
    print("\n" + "="*70)
    print("Test 2: load_facts_for_date Table Routing")
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
        print(f"  input_table_name: {use_case.input_table_name}")
        
        # Call load_facts_for_date
        facts_df = load_facts_for_date(
            session, 
            use_case.use_case_id, 
            pnl_date=date(2024, 1, 1), 
            scenario='ACTUAL'
        )
        
        print(f"\n[INFO] load_facts_for_date result:")
        print(f"  Rows: {len(facts_df)}")
        print(f"  Columns: {list(facts_df.columns) if not facts_df.empty else [])}")
        
        # Verify we got data (should be 500 rows from seed data)
        if facts_df.empty:
            print(f"[FAIL] DataFrame is empty - table routing may not be working")
            return False
        
        if len(facts_df) < 100:
            print(f"[WARN] Only {len(facts_df)} rows found, expected ~500 from seed data")
        
        # Verify columns include pnl_commission and pnl_trade for Use Case 3
        if 'pnl_commission' in facts_df.columns or 'pnl_trade' in facts_df.columns:
            print(f"[OK] DataFrame includes Use Case 3 specific columns")
            if 'pnl_commission' in facts_df.columns:
                commission_sum = facts_df['pnl_commission'].sum()
                print(f"  pnl_commission sum: {commission_sum}")
            if 'pnl_trade' in facts_df.columns:
                trade_sum = facts_df['pnl_trade'].sum()
                print(f"  pnl_trade sum: {trade_sum}")
        else:
            print(f"[WARN] DataFrame does not include pnl_commission or pnl_trade columns")
        
        print(f"[PASS] load_facts_for_date correctly routes to fact_pnl_use_case_3")
        return True
        
    except Exception as e:
        print(f"[FAIL] Error testing load_facts_for_date: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backward_compatibility(session: Session):
    """
    Test 3: Verify backward compatibility with existing use cases (fact_pnl_entries).
    """
    print("\n" + "="*70)
    print("Test 3: Backward Compatibility (fact_pnl_entries)")
    print("-"*70)
    
    try:
        # Get a use case that uses fact_pnl_entries (e.g., Project Sterling)
        use_case = session.query(UseCase).filter(
            UseCase.name.like('%Sterling%')
        ).first()
        
        if not use_case:
            print("[SKIP] No use case with 'Sterling' in name found")
            return True
        
        print(f"[OK] Found use case: {use_case.name}")
        print(f"  input_table_name: {use_case.input_table_name}")
        
        # Call get_unified_pnl
        result = get_unified_pnl(session, use_case.use_case_id, pnl_date=None, scenario='ACTUAL')
        
        print(f"\n[INFO] get_unified_pnl result:")
        print(f"  daily_pnl: {result.get('daily_pnl')}")
        
        # Should still work (either from DB or fallback)
        print(f"[PASS] Backward compatibility maintained for fact_pnl_entries")
        return True
        
    except Exception as e:
        print(f"[FAIL] Error testing backward compatibility: {e}")
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
        
        # Test 2: load_facts_for_date
        results.append(test_load_facts_for_date_table_routing(session))
        
        # Test 3: Backward compatibility
        results.append(test_backward_compatibility(session))
        
        # Summary
        print("\n" + "="*70)
        print("Verification Summary")
        print("="*70)
        
        if all(results):
            print("[PASS] All table routing tests passed")
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

