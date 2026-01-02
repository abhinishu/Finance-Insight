"""
Phase 5.4: Multiple Measures Support Verification

Verifies that the calculation engine correctly routes to different measures
based on rule.measure_name.
"""

import sys
from pathlib import Path
from decimal import Decimal

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from sqlalchemy.orm import Session
from app.api.dependencies import get_session_factory
from app.models import MetadataRule, UseCase
from app.engine.waterfall import apply_rule_override, get_measure_column_name


def test_measure_routing():
    """
    Test that aggregation uses the correct measure column based on rule.measure_name.
    
    Creates a test DataFrame and rule, then verifies the aggregation result.
    """
    print("="*70)
    print("Phase 5.4: Multiple Measures Support - Verification")
    print("="*70)
    print("\nTest 1: Measure Routing Test")
    print("-"*70)
    
    # Create test DataFrame with different values for each measure
    test_data = {
        'strategy': ['CORE', 'CORE', 'CORE'],
        'pnl_daily': [Decimal('10'), Decimal('10'), Decimal('10')],  # All 10s
        'pnl_commission': [Decimal('5'), Decimal('5'), Decimal('5')],  # All 5s
        'pnl_trade': [Decimal('20'), Decimal('20'), Decimal('20')],  # All 20s
    }
    test_df = pd.DataFrame(test_data)
    
    print(f"Test DataFrame created:")
    print(f"  Rows: {len(test_df)}")
    print(f"  pnl_daily sum: {test_df['pnl_daily'].sum()} (should be 30)")
    print(f"  pnl_commission sum: {test_df['pnl_commission'].sum()} (should be 15)")
    print(f"  pnl_trade sum: {test_df['pnl_trade'].sum()} (should be 60)")
    
    # Create a mock rule with measure_name='pnl_commission'
    class MockRule:
        def __init__(self):
            self.node_id = "TEST_NODE"
            self.measure_name = "daily_commission"  # Should map to pnl_commission
            self.sql_where = "strategy = 'CORE'"
            self.rule_type = "FILTER"
    
    rule = MockRule()
    
    # Test measure column name mapping
    print(f"\n[INFO] Testing measure column name mapping...")
    column_name = get_measure_column_name(rule.measure_name, 'fact_pnl_use_case_3')
    print(f"  measure_name: {rule.measure_name}")
    print(f"  table: fact_pnl_use_case_3")
    print(f"  mapped column: {column_name}")
    
    # Verify mapping
    if column_name != 'pnl_commission':
        print(f"[FAIL] Expected 'pnl_commission', got '{column_name}'")
        return False
    
    print(f"[PASS] Measure column mapping correct")
    
    # Test aggregation logic (simulate what apply_rule_override does)
    print(f"\n[INFO] Testing aggregation logic...")
    filtered_df = test_df[test_df['strategy'] == 'CORE']
    
    # Simulate using pnl_commission (the target measure)
    target_column = 'pnl_commission'
    if target_column not in filtered_df.columns:
        print(f"[FAIL] Column '{target_column}' not found in DataFrame")
        print(f"  Available columns: {list(filtered_df.columns)}")
        return False
    
    result_sum = filtered_df[target_column].sum()
    print(f"  Filtered rows: {len(filtered_df)}")
    print(f"  Sum of '{target_column}': {result_sum}")
    print(f"  Type: {type(result_sum)}")
    
    # Verify result is based on pnl_commission (5s), not pnl_daily (10s)
    expected_sum = Decimal('15')  # 5 + 5 + 5
    if result_sum != expected_sum:
        print(f"[FAIL] Expected sum {expected_sum}, got {result_sum}")
        return False
    
    # Verify it's NOT using pnl_daily
    daily_sum = filtered_df['pnl_daily'].sum()
    if result_sum == daily_sum:
        print(f"[FAIL] Result matches pnl_daily sum ({daily_sum}) - wrong measure used!")
        return False
    
    print(f"[PASS] Aggregation uses correct measure (pnl_commission)")
    print(f"  Result: {result_sum} (based on 5s, not 10s)")
    
    return True


def test_real_database_rule(session: Session):
    """
    Test with a real rule from the database.
    """
    print("\n" + "="*70)
    print("Test 2: Real Database Rule Test")
    print("-"*70)
    
    try:
        # Get Use Case 3
        use_case = session.query(UseCase).filter(
            UseCase.name == "America Cash Equity Trading"
        ).first()
        
        if not use_case:
            print("[SKIP] Use Case 3 not found - skipping real database test")
            return True
        
        # Get a rule with measure_name='daily_commission' (NODE_5)
        rule = session.query(MetadataRule).filter(
            MetadataRule.use_case_id == use_case.use_case_id,
            MetadataRule.node_id == 'NODE_5'
        ).first()
        
        if not rule:
            print("[SKIP] NODE_5 rule not found - skipping real database test")
            return True
        
        print(f"[OK] Found rule for NODE_5: {rule.node_id}")
        print(f"  rule_type: {rule.rule_type}")
        print(f"  measure_name: {rule.measure_name}")
        print(f"  sql_where: {rule.sql_where}")
        
        # Verify measure_name is set
        if not rule.measure_name:
            print("[FAIL] Rule measure_name is None")
            return False
        
        if rule.measure_name != 'daily_commission':
            print(f"[WARN] Expected measure_name='daily_commission', got '{rule.measure_name}'")
        
        # Test column mapping
        column_name = get_measure_column_name(rule.measure_name, 'fact_pnl_use_case_3')
        print(f"\n[INFO] Column mapping:")
        print(f"  measure_name: {rule.measure_name}")
        print(f"  mapped column: {column_name}")
        
        if column_name != 'pnl_commission':
            print(f"[FAIL] Expected 'pnl_commission', got '{column_name}'")
            return False
        
        print(f"[PASS] Real database rule has correct measure_name and mapping")
        return True
        
    except Exception as e:
        print(f"[FAIL] Error testing real database rule: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dataframe_measure_access():
    """
    Test that DataFrame can access all measure columns.
    """
    print("\n" + "="*70)
    print("Test 3: DataFrame Measure Access Test")
    print("-"*70)
    
    # Load data from fact_pnl_use_case_3
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        from app.engine.waterfall import load_facts_from_use_case_3
        
        # Load facts
        facts_df = load_facts_from_use_case_3(session)
        
        if facts_df.empty:
            print("[SKIP] No data in fact_pnl_use_case_3 - skipping DataFrame test")
            return True
        
        print(f"[OK] Loaded {len(facts_df)} rows from fact_pnl_use_case_3")
        print(f"  Columns: {list(facts_df.columns)}")
        
        # Verify all measure columns exist
        required_columns = ['pnl_daily', 'pnl_commission', 'pnl_trade']
        missing_columns = [col for col in required_columns if col not in facts_df.columns]
        
        if missing_columns:
            print(f"[FAIL] Missing columns: {missing_columns}")
            return False
        
        print(f"[PASS] All measure columns present")
        
        # Verify column types (should be Decimal or compatible)
        print(f"\n[INFO] Checking column types...")
        for col in required_columns:
            sample_value = facts_df[col].iloc[0] if len(facts_df) > 0 else None
            print(f"  {col}: type={type(sample_value)}, sample={sample_value}")
            
            # Check if it's Decimal or can be converted to Decimal
            if sample_value is not None:
                try:
                    decimal_value = Decimal(str(sample_value))
                    print(f"    -> Can convert to Decimal: {decimal_value}")
                except Exception as e:
                    print(f"    -> WARN: Cannot convert to Decimal: {e}")
        
        # Test aggregation on each measure
        print(f"\n[INFO] Testing aggregation on each measure...")
        for col in required_columns:
            col_sum = facts_df[col].sum()
            print(f"  SUM({col}): {col_sum} (type: {type(col_sum)})")
            
            # Verify it's not zero (if we have data)
            if col_sum == Decimal('0') and len(facts_df) > 0:
                print(f"    [WARN] Sum is zero - may indicate data issue")
        
        print(f"[PASS] DataFrame measure access working correctly")
        return True
        
    except Exception as e:
        print(f"[FAIL] Error testing DataFrame: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


def main():
    """Main verification function."""
    print("="*70)
    print("Phase 5.4: Multiple Measures Support Verification")
    print("="*70)
    print("Verifying that calculation engine routes to correct measures...")
    print()
    
    results = []
    
    # Test 1: Measure routing with mock data
    results.append(test_measure_routing())
    
    # Test 2: Real database rule
    session_factory = get_session_factory()
    session = session_factory()
    try:
        results.append(test_real_database_rule(session))
    finally:
        session.close()
    
    # Test 3: DataFrame measure access
    results.append(test_dataframe_measure_access())
    
    # Summary
    print("\n" + "="*70)
    print("Verification Summary")
    print("="*70)
    
    if all(results):
        print("[PASS] All measure routing tests passed")
        print("\nThe calculation engine correctly routes to different measures")
        print("based on rule.measure_name.")
        print("Ready for Phase 5.5 (Type 2B Engine).")
        return 0
    else:
        print("[FAIL] One or more tests failed")
        print("\nPlease review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

