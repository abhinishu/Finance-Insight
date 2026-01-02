"""
Verification Script: Math Dependency Engine (Type 3 Rules)

Tests the Type 3 rule execution with dependency resolution:
1. Mock a Hierarchy: Node A, Node B
2. Mock Data: Node A = 1,000 (Simulating a SQL result)
3. Create a Rule: "Node B = Node A * 0.10" (10% Allocation)
4. Run the Engine
5. Assert: Node B should equal 100
6. Assert: If Node A changes to 2,000, Node B becomes 200
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from decimal import Decimal
from typing import Dict
from app.services.dependency_resolver import (
    DependencyResolver,
    CircularDependencyError,
    evaluate_type3_expression
)
from app.models import MetadataRule, DimHierarchy
import json

def create_mock_rule(node_id: str, expression: str, dependencies: list) -> MetadataRule:
    """Create a mock MetadataRule for testing."""
    rule = MetadataRule()
    rule.rule_id = hash(node_id)  # Mock ID
    rule.node_id = node_id
    rule.rule_type = 'NODE_ARITHMETIC'
    rule.rule_expression = expression
    rule.rule_dependencies = dependencies
    rule.measure_name = 'daily_pnl'
    rule.sql_where = None  # Type 3 rules don't use SQL
    return rule


def create_mock_hierarchy() -> Dict[str, DimHierarchy]:
    """Create a mock hierarchy with Node A and Node B."""
    node_a = DimHierarchy()
    node_a.node_id = 'NODE_A'
    node_a.node_name = 'Node A'
    node_a.depth = 0
    node_a.is_leaf = True
    
    node_b = DimHierarchy()
    node_b.node_id = 'NODE_B'
    node_b.node_name = 'Node B'
    node_b.depth = 0
    node_b.is_leaf = True
    
    return {
        'NODE_A': node_a,
        'NODE_B': node_b
    }


def test_basic_allocation():
    """
    Test 1: Basic 10% Allocation
    Node A = 1,000
    Node B = Node A * 0.10
    Expected: Node B = 100
    """
    print("=" * 80)
    print("TEST 1: Basic 10% Allocation")
    print("=" * 80)
    print()
    
    # Mock hierarchy
    hierarchy = create_mock_hierarchy()
    
    # Mock data: Node A = 1,000
    node_values = {
        'NODE_A': {
            'daily': Decimal('1000'),
            'mtd': Decimal('1000'),
            'ytd': Decimal('1000'),
            'pytd': Decimal('0')
        }
    }
    
    # Create rule: Node B = Node A * 0.10
    rule = create_mock_rule('NODE_B', 'NODE_A * 0.10', ['NODE_A'])
    
    # Evaluate expression
    result = evaluate_type3_expression(
        rule.rule_expression,
        node_values,
        measure='daily'
    )
    
    print(f"  Node A value: {node_values['NODE_A']['daily']}")
    print(f"  Rule expression: {rule.rule_expression}")
    print(f"  Calculated Node B: {result['daily']}")
    print()
    
    # Assert
    expected = Decimal('100')
    assert result['daily'] == expected, f"Expected {expected}, got {result['daily']}"
    print(f"  [PASS] Node B = {result['daily']} (expected: {expected})")
    print()
    
    return result


def test_changed_source():
    """
    Test 2: Changed Source Value
    Node A = 2,000 (changed from 1,000)
    Node B = Node A * 0.10
    Expected: Node B = 200
    """
    print("=" * 80)
    print("TEST 2: Changed Source Value")
    print("=" * 80)
    print()
    
    # Mock hierarchy
    hierarchy = create_mock_hierarchy()
    
    # Mock data: Node A = 2,000 (changed)
    node_values = {
        'NODE_A': {
            'daily': Decimal('2000'),
            'mtd': Decimal('2000'),
            'ytd': Decimal('2000'),
            'pytd': Decimal('0')
        }
    }
    
    # Create rule: Node B = Node A * 0.10
    rule = create_mock_rule('NODE_B', 'NODE_A * 0.10', ['NODE_A'])
    
    # Evaluate expression
    result = evaluate_type3_expression(
        rule.rule_expression,
        node_values,
        measure='daily'
    )
    
    print(f"  Node A value: {node_values['NODE_A']['daily']}")
    print(f"  Rule expression: {rule.rule_expression}")
    print(f"  Calculated Node B: {result['daily']}")
    print()
    
    # Assert
    expected = Decimal('200')
    assert result['daily'] == expected, f"Expected {expected}, got {result['daily']}"
    print(f"  [PASS] Node B = {result['daily']} (expected: {expected})")
    print()
    
    return result


def test_dependency_resolution():
    """
    Test 3: Dependency Resolution (Topological Sort)
    Rule 1: Node B = Node A * 0.10 (depends on Node A)
    Rule 2: Node C = Node B + 50 (depends on Node B)
    Expected execution order: [Rule 1, Rule 2]
    """
    print("=" * 80)
    print("TEST 3: Dependency Resolution")
    print("=" * 80)
    print()
    
    # Mock hierarchy
    node_a = DimHierarchy()
    node_a.node_id = 'NODE_A'
    node_a.node_name = 'Node A'
    node_a.is_leaf = True
    
    node_b = DimHierarchy()
    node_b.node_id = 'NODE_B'
    node_b.node_name = 'Node B'
    node_b.is_leaf = True
    
    node_c = DimHierarchy()
    node_c.node_id = 'NODE_C'
    node_c.node_name = 'Node C'
    node_c.is_leaf = True
    
    hierarchy = {
        'NODE_A': node_a,
        'NODE_B': node_b,
        'NODE_C': node_c
    }
    
    # Create rules
    rule1 = create_mock_rule('NODE_B', 'NODE_A * 0.10', ['NODE_A'])
    rule2 = create_mock_rule('NODE_C', 'NODE_B + 50', ['NODE_B'])
    
    rules = [rule1, rule2]
    
    # Resolve execution order
    sorted_rules = DependencyResolver.resolve_execution_order(rules, hierarchy)
    
    print(f"  Rules: {[r.node_id for r in rules]}")
    print(f"  Sorted order: {[r.node_id for r in sorted_rules]}")
    print()
    
    # Assert execution order
    assert sorted_rules[0].node_id == 'NODE_B', "Rule 1 (NODE_B) should execute first"
    assert sorted_rules[1].node_id == 'NODE_C', "Rule 2 (NODE_C) should execute second"
    print(f"  [PASS] Execution order is correct: {[r.node_id for r in sorted_rules]}")
    print()
    
    # Simulate execution
    node_values = {
        'NODE_A': {
            'daily': Decimal('1000'),
            'mtd': Decimal('1000'),
            'ytd': Decimal('1000'),
            'pytd': Decimal('0')
        }
    }
    
    # Execute Rule 1: Node B = Node A * 0.10
    result_b = evaluate_type3_expression(rule1.rule_expression, node_values)
    node_values['NODE_B'] = result_b
    print(f"  After Rule 1: Node B = {result_b['daily']}")
    
    # Execute Rule 2: Node C = Node B + 50
    result_c = evaluate_type3_expression(rule2.rule_expression, node_values)
    node_values['NODE_C'] = result_c
    print(f"  After Rule 2: Node C = {result_c['daily']}")
    print()
    
    # Assert final values
    assert node_values['NODE_B']['daily'] == Decimal('100'), "Node B should be 100"
    assert node_values['NODE_C']['daily'] == Decimal('150'), "Node C should be 150"
    print(f"  [PASS] Node B = {node_values['NODE_B']['daily']}, Node C = {node_values['NODE_C']['daily']}")
    print()
    
    return sorted_rules


def test_circular_dependency():
    """
    Test 4: Circular Dependency Detection
    Rule 1: Node A = Node B + 10
    Rule 2: Node B = Node A + 20
    Expected: CircularDependencyError
    """
    print("=" * 80)
    print("TEST 4: Circular Dependency Detection")
    print("=" * 80)
    print()
    
    # Mock hierarchy
    node_a = DimHierarchy()
    node_a.node_id = 'NODE_A'
    node_a.node_name = 'Node A'
    node_a.is_leaf = True
    
    node_b = DimHierarchy()
    node_b.node_id = 'NODE_B'
    node_b.node_name = 'Node B'
    node_b.is_leaf = True
    
    hierarchy = {
        'NODE_A': node_a,
        'NODE_B': node_b
    }
    
    # Create circular rules
    rule1 = create_mock_rule('NODE_A', 'NODE_B + 10', ['NODE_B'])
    rule2 = create_mock_rule('NODE_B', 'NODE_A + 20', ['NODE_A'])
    
    rules = [rule1, rule2]
    
    # Attempt to resolve (should raise CircularDependencyError)
    try:
        sorted_rules = DependencyResolver.resolve_execution_order(rules, hierarchy)
        print(f"  [FAIL] Expected CircularDependencyError, but got: {[r.node_id for r in sorted_rules]}")
        assert False, "Should have raised CircularDependencyError"
    except CircularDependencyError as e:
        print(f"  [PASS] Circular dependency detected: {e}")
    except Exception as e:
        print(f"  [FAIL] Expected CircularDependencyError, got: {type(e).__name__}: {e}")
        assert False, f"Wrong exception type: {type(e).__name__}"
    print()


def run_all_tests():
    """Run all verification tests."""
    print("=" * 80)
    print("MATH DEPENDENCY ENGINE VERIFICATION")
    print("=" * 80)
    print()
    
    try:
        test_basic_allocation()
        test_changed_source()
        test_dependency_resolution()
        test_circular_dependency()
        
        print("=" * 80)
        print("ALL TESTS PASSED")
        print("=" * 80)
        
    except AssertionError as e:
        print(f"[FAIL] Assertion failed: {e}")
        raise
    except Exception as e:
        print(f"[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    run_all_tests()

