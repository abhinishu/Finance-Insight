"""
Phase 5.5: Type 2B Rule Engine Verification

Verifies that Type 2B (FILTER_ARITHMETIC) rules are correctly executed.
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
from app.engine.type2b_processor import execute_type_2b_rule, execute_single_query, evaluate_expression


def test_single_query_execution():
    """
    Test 1: Verify single query execution works correctly.
    """
    print("="*70)
    print("Test 1: Single Query Execution")
    print("-"*70)
    
    # Create test DataFrame
    test_data = {
        'strategy': ['CORE', 'CORE', 'OTHER', 'CORE'],
        'process_2': ['A', 'B', 'A', 'A'],
        'pnl_daily': [Decimal('10'), Decimal('20'), Decimal('30'), Decimal('40')],
        'pnl_commission': [Decimal('5'), Decimal('15'), Decimal('25'), Decimal('35')],
    }
    test_df = pd.DataFrame(test_data)
    
    print(f"Test DataFrame: {len(test_df)} rows")
    print(f"  pnl_daily sum: {test_df['pnl_daily'].sum()}")
    print(f"  pnl_commission sum: {test_df['pnl_commission'].sum()}")
    
    # Test query: SUM(pnl_commission) WHERE strategy='CORE'
    query_def = {
        'query_id': 'test_query_1',
        'measure': 'daily_commission',
        'aggregation': 'SUM',
        'filters': [
            {'field': 'strategy', 'operator': '=', 'value': 'CORE'}
        ]
    }
    
    result = execute_single_query(test_df, query_def, 'fact_pnl_use_case_3')
    
    print(f"\n[INFO] Query: SUM(pnl_commission) WHERE strategy='CORE'")
    print(f"  Result: {result} (type: {type(result)})")
    
    # Expected: 5 + 15 + 35 = 55
    expected = Decimal('55')
    if result != expected:
        print(f"[FAIL] Expected {expected}, got {result}")
        return False
    
    if not isinstance(result, Decimal):
        print(f"[FAIL] Result is not Decimal, got {type(result)}")
        return False
    
    print(f"[PASS] Single query execution correct")
    return True


def test_type2b_simple_addition():
    """
    Test 2: Verify Type 2B rule with simple addition (Query1 + Query2).
    """
    print("\n" + "="*70)
    print("Test 2: Type 2B Simple Addition")
    print("-"*70)
    
    # Create test DataFrame
    test_data = {
        'strategy': ['CORE', 'CORE', 'CORE', 'OTHER'],
        'pnl_daily': [Decimal('100'), Decimal('200'), Decimal('300'), Decimal('400')],
        'pnl_commission': [Decimal('50'), Decimal('60'), Decimal('70'), Decimal('80')],
    }
    test_df = pd.DataFrame(test_data)
    
    print(f"Test DataFrame: {len(test_df)} rows")
    print(f"  pnl_daily sum (CORE): {test_df[test_df['strategy'] == 'CORE']['pnl_daily'].sum()}")
    print(f"  pnl_commission sum (CORE): {test_df[test_df['strategy'] == 'CORE']['pnl_commission'].sum()}")
    
    # Create mock rule with Type 2B predicate_json
    class MockRule:
        def __init__(self):
            self.node_id = "TEST_NODE"
            self.rule_type = "FILTER_ARITHMETIC"
            self.predicate_json = {
                "version": "2.0",
                "rule_type": "FILTER_ARITHMETIC",
                "expression": {
                    "operator": "+",
                    "operands": [
                        {"type": "query", "query_id": "query_1"},
                        {"type": "query", "query_id": "query_2"}
                    ]
                },
                "queries": [
                    {
                        "query_id": "query_1",
                        "measure": "daily_pnl",
                        "aggregation": "SUM",
                        "filters": [
                            {"field": "strategy", "operator": "=", "value": "CORE"}
                        ]
                    },
                    {
                        "query_id": "query_2",
                        "measure": "daily_commission",
                        "aggregation": "SUM",
                        "filters": [
                            {"field": "strategy", "operator": "=", "value": "CORE"}
                        ]
                    }
                ]
            }
    
    rule = MockRule()
    
    # Execute Type 2B rule
    result = execute_type_2b_rule(test_df, rule, 'fact_pnl_use_case_3')
    
    print(f"\n[INFO] Rule: SUM(pnl_daily) WHERE strategy='CORE' + SUM(pnl_commission) WHERE strategy='CORE'")
    print(f"  Result: {result} (type: {type(result)})")
    
    # Expected: (100 + 200 + 300) + (50 + 60 + 70) = 600 + 180 = 780
    expected = Decimal('780')
    if result != expected:
        print(f"[FAIL] Expected {expected}, got {result}")
        return False
    
    if not isinstance(result, Decimal):
        print(f"[FAIL] Result is not Decimal, got {type(result)}")
        return False
    
    print(f"[PASS] Type 2B simple addition correct")
    return True


def test_type2b_subtraction():
    """
    Test 3: Verify Type 2B rule with subtraction.
    """
    print("\n" + "="*70)
    print("Test 3: Type 2B Subtraction")
    print("-"*70)
    
    # Create test DataFrame
    test_data = {
        'strategy': ['CORE', 'CORE', 'OTHER'],
        'pnl_daily': [Decimal('100'), Decimal('200'), Decimal('50')],
        'pnl_commission': [Decimal('30'), Decimal('40'), Decimal('10')],
    }
    test_df = pd.DataFrame(test_data)
    
    # Create mock rule: Query1 - Query2
    class MockRule:
        def __init__(self):
            self.node_id = "TEST_NODE"
            self.rule_type = "FILTER_ARITHMETIC"
            self.predicate_json = {
                "version": "2.0",
                "rule_type": "FILTER_ARITHMETIC",
                "expression": {
                    "operator": "-",
                    "operands": [
                        {"type": "query", "query_id": "query_1"},
                        {"type": "query", "query_id": "query_2"}
                    ]
                },
                "queries": [
                    {
                        "query_id": "query_1",
                        "measure": "daily_pnl",
                        "aggregation": "SUM",
                        "filters": [{"field": "strategy", "operator": "=", "value": "CORE"}]
                    },
                    {
                        "query_id": "query_2",
                        "measure": "daily_commission",
                        "aggregation": "SUM",
                        "filters": [{"field": "strategy", "operator": "=", "value": "CORE"}]
                    }
                ]
            }
    
    rule = MockRule()
    result = execute_type_2b_rule(test_df, rule, 'fact_pnl_use_case_3')
    
    print(f"[INFO] Rule: SUM(pnl_daily) - SUM(pnl_commission) WHERE strategy='CORE'")
    print(f"  Result: {result}")
    
    # Expected: (100 + 200) - (30 + 40) = 300 - 70 = 230
    expected = Decimal('230')
    if result != expected:
        print(f"[FAIL] Expected {expected}, got {result}")
        return False
    
    print(f"[PASS] Type 2B subtraction correct")
    return True


def test_type2b_with_in_filter():
    """
    Test 4: Verify Type 2B rule with IN filter (like NODE_4).
    """
    print("\n" + "="*70)
    print("Test 4: Type 2B with IN Filter")
    print("-"*70)
    
    # Create test DataFrame matching NODE_4 scenario
    test_data = {
        'strategy': ['CORE', 'CORE', 'CORE', 'CORE', 'OTHER'],
        'process_2': ['SWAP COMMISSION', 'SD COMMISSION', 'OTHER', 'SWAP COMMISSION', 'SWAP COMMISSION'],
        'pnl_commission': [Decimal('100'), Decimal('200'), Decimal('50'), Decimal('150'), Decimal('300')],
        'pnl_trade': [Decimal('500'), Decimal('600'), Decimal('700'), Decimal('800'), Decimal('900')],
    }
    test_df = pd.DataFrame(test_data)
    
    # Create mock rule matching NODE_4: SUM(commission) WHERE CORE + SUM(trade) WHERE CORE AND process_2 IN (...)
    class MockRule:
        def __init__(self):
            self.node_id = "NODE_4"
            self.rule_type = "FILTER_ARITHMETIC"
            self.predicate_json = {
                "version": "2.0",
                "rule_type": "FILTER_ARITHMETIC",
                "expression": {
                    "operator": "+",
                    "operands": [
                        {"type": "query", "query_id": "query_1"},
                        {"type": "query", "query_id": "query_2"}
                    ]
                },
                "queries": [
                    {
                        "query_id": "query_1",
                        "measure": "daily_commission",
                        "aggregation": "SUM",
                        "filters": [
                            {"field": "strategy", "operator": "=", "value": "CORE"}
                        ]
                    },
                    {
                        "query_id": "query_2",
                        "measure": "daily_trade",
                        "aggregation": "SUM",
                        "filters": [
                            {"field": "strategy", "operator": "=", "value": "CORE"},
                            {"field": "process_2", "operator": "IN", "values": ["SWAP COMMISSION", "SD COMMISSION"]}
                        ]
                    }
                ]
            }
    
    rule = MockRule()
    result = execute_type_2b_rule(test_df, rule, 'fact_pnl_use_case_3')
    
    print(f"[INFO] Rule: SUM(commission) WHERE CORE + SUM(trade) WHERE CORE AND process_2 IN (...)")
    query1_manual = test_df[test_df['strategy'] == 'CORE']['pnl_commission'].sum()
    query2_manual = test_df[(test_df['strategy'] == 'CORE') & (test_df['process_2'].isin(['SWAP COMMISSION', 'SD COMMISSION']))]['pnl_trade'].sum()
    print(f"  Query 1 (commission, CORE): {query1_manual}")
    print(f"  Query 2 (trade, CORE AND IN): {query2_manual}")
    print(f"  Result: {result}")
    
    # Expected: (100 + 200 + 50 + 150) + (500 + 600 + 800) = 500 + 1900 = 2400
    # Note: Row 3 has strategy='CORE' and process_2='SWAP COMMISSION', so it's included in Query 2
    expected = Decimal('2400')
    if result != expected:
        print(f"[FAIL] Expected {expected}, got {result}")
        return False
    
    print(f"[PASS] Type 2B with IN filter correct")
    return True


def test_real_database_rule(session: Session):
    """
    Test 5: Verify with a real Type 2B rule from the database.
    """
    print("\n" + "="*70)
    print("Test 5: Real Database Type 2B Rule")
    print("-"*70)
    
    try:
        # Get Use Case 3
        use_case = session.query(UseCase).filter(
            UseCase.name == "America Cash Equity Trading"
        ).first()
        
        if not use_case:
            print("[SKIP] Use Case 3 not found")
            return True
        
        # Get Type 2B rule (NODE_4)
        rule = session.query(MetadataRule).filter(
            MetadataRule.use_case_id == use_case.use_case_id,
            MetadataRule.node_id == 'NODE_4',
            MetadataRule.rule_type == 'FILTER_ARITHMETIC'
        ).first()
        
        if not rule:
            print("[SKIP] NODE_4 Type 2B rule not found")
            return True
        
        print(f"[OK] Found Type 2B rule for NODE_4")
        print(f"  rule_type: {rule.rule_type}")
        print(f"  predicate_json version: {rule.predicate_json.get('version') if rule.predicate_json else None}")
        
        # Load facts
        from app.engine.waterfall import load_facts_from_use_case_3
        facts_df = load_facts_from_use_case_3(session, use_case.use_case_id)
        
        if facts_df.empty:
            print("[SKIP] No data in fact_pnl_use_case_3")
            return True
        
        print(f"[OK] Loaded {len(facts_df)} rows from fact_pnl_use_case_3")
        
        # Execute Type 2B rule
        result = execute_type_2b_rule(facts_df, rule, 'fact_pnl_use_case_3')
        
        print(f"[INFO] Type 2B rule execution result: {result} (type: {type(result)})")
        
        if not isinstance(result, Decimal):
            print(f"[FAIL] Result is not Decimal, got {type(result)}")
            return False
        
        if result == Decimal('0'):
            print(f"[WARN] Result is zero - may indicate data/rule mismatch")
        
        print(f"[PASS] Real database Type 2B rule executed successfully")
        return True
        
    except Exception as e:
        print(f"[FAIL] Error testing real database rule: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main verification function."""
    print("="*70)
    print("Phase 5.5: Type 2B Rule Engine Verification")
    print("="*70)
    print("Verifying Type 2B (FILTER_ARITHMETIC) rule execution...")
    print()
    
    results = []
    
    # Test 1: Single query execution
    results.append(test_single_query_execution())
    
    # Test 2: Simple addition
    results.append(test_type2b_simple_addition())
    
    # Test 3: Subtraction
    results.append(test_type2b_subtraction())
    
    # Test 4: IN filter
    results.append(test_type2b_with_in_filter())
    
    # Test 5: Real database rule
    session_factory = get_session_factory()
    session = session_factory()
    try:
        results.append(test_real_database_rule(session))
    finally:
        session.close()
    
    # Summary
    print("\n" + "="*70)
    print("Verification Summary")
    print("="*70)
    
    if all(results):
        print("[PASS] All Type 2B rule engine tests passed")
        print("\nThe Type 2B engine correctly executes FILTER_ARITHMETIC rules.")
        print("Ready for Phase 5.6 (Type 3 Engine).")
        return 0
    else:
        print("[FAIL] One or more tests failed")
        print("\nPlease review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

