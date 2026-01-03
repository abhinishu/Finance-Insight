"""
Phase 5.3: Model Verification Script

Verifies that SQLAlchemy models correctly map to database columns:
- FactPnlUseCase3 model exists and works
- MetadataRule model has new columns
- PnL columns return Decimal type (not float)
"""

import sys
from pathlib import Path
from decimal import Decimal

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.api.dependencies import get_session_factory
from app.models import FactPnlUseCase3, MetadataRule


def verify_fact_pnl_use_case_3(session: Session) -> bool:
    """Verify FactPnlUseCase3 model works and returns Decimal types."""
    print("="*70)
    print("Verifying FactPnlUseCase3 Model")
    print("="*70)
    
    try:
        # Query one row
        row = session.query(FactPnlUseCase3).first()
        
        if not row:
            print("[FAIL] No rows found in fact_pnl_use_case_3")
            return False
        
        print(f"[OK] Retrieved row: entry_id={row.entry_id}, effective_date={row.effective_date}")
        print(f"     strategy={row.strategy}, product_line={row.product_line}")
        
        # CRITICAL: Verify PnL columns are Decimal type
        print("\n[INFO] Checking PnL column types...")
        
        pnl_daily_type = type(row.pnl_daily)
        pnl_commission_type = type(row.pnl_commission)
        pnl_trade_type = type(row.pnl_trade)
        
        print(f"  pnl_daily type: {pnl_daily_type.__name__}")
        print(f"  pnl_commission type: {pnl_commission_type.__name__}")
        print(f"  pnl_trade type: {pnl_trade_type.__name__}")
        
        # Check values
        print(f"\n[INFO] Sample values:")
        print(f"  pnl_daily: {row.pnl_daily} (type: {pnl_daily_type.__name__})")
        print(f"  pnl_commission: {row.pnl_commission} (type: {pnl_commission_type.__name__})")
        print(f"  pnl_trade: {row.pnl_trade} (type: {pnl_trade_type.__name__})")
        
        # Verify all are Decimal
        if pnl_daily_type != Decimal:
            print(f"[FAIL] pnl_daily is {pnl_daily_type.__name__}, expected Decimal")
            return False
        
        if pnl_commission_type != Decimal:
            print(f"[FAIL] pnl_commission is {pnl_commission_type.__name__}, expected Decimal")
            return False
        
        if pnl_trade_type != Decimal:
            print(f"[FAIL] pnl_trade is {pnl_trade_type.__name__}, expected Decimal")
            return False
        
        print("\n[PASS] All PnL columns return Decimal type")
        return True
        
    except Exception as e:
        print(f"[FAIL] Error verifying FactPnlUseCase3: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_metadata_rule(session: Session) -> bool:
    """Verify MetadataRule model has new columns and Type 3 rule works."""
    print("\n" + "="*70)
    print("Verifying MetadataRule Model (New Columns)")
    print("="*70)
    
    try:
        # Query a Type 3 rule
        type3_rule = session.query(MetadataRule).filter(
            MetadataRule.rule_type == 'NODE_ARITHMETIC'
        ).first()
        
        if not type3_rule:
            print("[WARN] No Type 3 (NODE_ARITHMETIC) rules found")
            # Try to find any rule
            any_rule = session.query(MetadataRule).first()
            if not any_rule:
                print("[FAIL] No rules found in metadata_rules table")
                return False
            type3_rule = any_rule
            print(f"[INFO] Using rule {type3_rule.rule_id} for verification")
        
        print(f"[OK] Retrieved rule: rule_id={type3_rule.rule_id}, node_id={type3_rule.node_id}")
        
        # Check new columns exist
        print("\n[INFO] Checking new columns...")
        
        has_rule_type = hasattr(type3_rule, 'rule_type')
        has_measure_name = hasattr(type3_rule, 'measure_name')
        has_rule_expression = hasattr(type3_rule, 'rule_expression')
        has_rule_dependencies = hasattr(type3_rule, 'rule_dependencies')
        
        print(f"  rule_type: {'[OK]' if has_rule_type else '[FAIL]'} = {getattr(type3_rule, 'rule_type', 'N/A')}")
        print(f"  measure_name: {'[OK]' if has_measure_name else '[FAIL]'} = {getattr(type3_rule, 'measure_name', 'N/A')}")
        print(f"  rule_expression: {'[OK]' if has_rule_expression else '[FAIL]'} = {getattr(type3_rule, 'rule_expression', 'N/A')}")
        print(f"  rule_dependencies: {'[OK]' if has_rule_dependencies else '[FAIL]'} = {getattr(type3_rule, 'rule_dependencies', 'N/A')}")
        
        if not all([has_rule_type, has_measure_name, has_rule_expression, has_rule_dependencies]):
            print("\n[FAIL] Not all new columns are accessible")
            return False
        
        # Verify Type 3 rule has expression
        if type3_rule.rule_type == 'NODE_ARITHMETIC':
            if not type3_rule.rule_expression:
                print("[FAIL] Type 3 rule missing rule_expression")
                return False
            print(f"\n[OK] Type 3 rule has expression: {type3_rule.rule_expression}")
            if type3_rule.rule_dependencies:
                print(f"[OK] Type 3 rule has dependencies: {type3_rule.rule_dependencies}")
        
        print("\n[PASS] All new columns accessible and working")
        return True
        
    except Exception as e:
        print(f"[FAIL] Error verifying MetadataRule: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_use_case(session: Session) -> bool:
    """Verify UseCase model has input_table_name column."""
    print("\n" + "="*70)
    print("Verifying UseCase Model (New Column)")
    print("="*70)
    
    try:
        from app.models import UseCase
        
        # Query Use Case 3
        use_case = session.query(UseCase).filter(
            UseCase.name == "America Cash Equity Trading"
        ).first()
        
        if not use_case:
            print("[WARN] Use Case 3 not found, checking any use case...")
            use_case = session.query(UseCase).first()
            if not use_case:
                print("[FAIL] No use cases found")
                return False
        
        print(f"[OK] Retrieved use case: {use_case.name} (ID: {use_case.use_case_id})")
        
        # Check new column
        has_input_table_name = hasattr(use_case, 'input_table_name')
        print(f"\n[INFO] Checking input_table_name column...")
        print(f"  input_table_name: {'[OK]' if has_input_table_name else '[FAIL]'} = {getattr(use_case, 'input_table_name', 'N/A')}")
        
        if not has_input_table_name:
            print("[FAIL] input_table_name column not accessible")
            return False
        
        print("\n[PASS] input_table_name column accessible")
        return True
        
    except Exception as e:
        print(f"[FAIL] Error verifying UseCase: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main verification function."""
    print("="*70)
    print("Phase 5.3: Model Verification")
    print("="*70)
    print("Verifying SQLAlchemy models after Phase 5.1 schema changes...")
    print()
    
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        results = []
        
        # 1. Verify FactPnlUseCase3
        results.append(verify_fact_pnl_use_case_3(session))
        
        # 2. Verify MetadataRule
        results.append(verify_metadata_rule(session))
        
        # 3. Verify UseCase
        results.append(verify_use_case(session))
        
        # Summary
        print("\n" + "="*70)
        print("Verification Summary")
        print("="*70)
        
        if all(results):
            print("[PASS] All model verifications passed")
            print("\nModels are correctly updated and working.")
            print("Ready for Phase 5.4 (Multiple Measures Support).")
            return 0
        else:
            print("[FAIL] One or more verifications failed")
            print("\nPlease review the errors above.")
            return 1
            
    except Exception as e:
        print(f"\n[FAIL] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())


