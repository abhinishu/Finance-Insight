"""
Type 3 Rule Execution Order Resolution
Resolves execution order for node arithmetic rules using topological sort.
Detects circular dependencies and raises specific errors.

Usage:
    python scripts/type3_execution_order.py
"""

from typing import List, Dict, Set, Optional
from collections import defaultdict, deque


class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected in rule dependencies."""
    
    def __init__(self, cycle_nodes: List[int], message: str = None):
        self.cycle_nodes = cycle_nodes
        if message is None:
            message = f"Circular dependency detected involving nodes: {cycle_nodes}"
        super().__init__(message)


def resolve_execution_order(rules: List[Dict]) -> List[int]:
    """
    Resolves execution order for Type 3 rules using topological sort.
    
    Args:
        rules: List of rule dictionaries, each containing:
            - 'node_id': int - The node that this rule calculates
            - 'dependencies': List[int] - List of node IDs this rule depends on
    
    Returns:
        List[int]: Execution order (topological sort) of node IDs
        
    Raises:
        CircularDependencyError: If a circular dependency is detected
        
    Example:
        >>> rules = [
        ...     {'node_id': 7, 'dependencies': [3, 4]},
        ...     {'node_id': 3, 'dependencies': [2, 10]},
        ...     {'node_id': 8, 'dependencies': [7, 9]}
        ... ]
        >>> resolve_execution_order(rules)
        [2, 10, 3, 4, 9, 7, 8]
    """
    # Build directed graph: node -> set of nodes it depends on
    graph: Dict[int, Set[int]] = defaultdict(set)
    # Track all nodes (both rule nodes and dependency nodes)
    all_nodes: Set[int] = set()
    # Track in-degree (number of incoming edges) for each node
    in_degree: Dict[int, int] = defaultdict(int)
    
    # Build graph from rules
    for rule in rules:
        node_id = rule['node_id']
        dependencies = rule.get('dependencies', [])
        
        all_nodes.add(node_id)
        # Initialize in-degree for this node
        if node_id not in in_degree:
            in_degree[node_id] = 0
        
        # Add edges: each dependency points to this node
        for dep in dependencies:
            all_nodes.add(dep)
            graph[dep].add(node_id)
            in_degree[node_id] += 1
    
    # Kahn's Algorithm for Topological Sort
    # Start with nodes that have no dependencies (in-degree = 0)
    queue = deque([node for node in all_nodes if in_degree[node] == 0])
    execution_order: List[int] = []
    processed_count = 0
    
    while queue:
        # Process node with no remaining dependencies
        current = queue.popleft()
        execution_order.append(current)
        processed_count += 1
        
        # Remove this node and reduce in-degree of dependent nodes
        for dependent in graph[current]:
            in_degree[dependent] -= 1
            # If dependent has no more dependencies, add to queue
            if in_degree[dependent] == 0:
                queue.append(dependent)
    
    # If we didn't process all nodes, there's a cycle
    if processed_count != len(all_nodes):
        # Find the cycle for better error message
        cycle = _detect_cycle(graph, all_nodes)
        raise CircularDependencyError(cycle)
    
    return execution_order


def _detect_cycle(graph: Dict[int, Set[int]], all_nodes: Set[int]) -> List[int]:
    """
    Detects a cycle in the dependency graph using DFS.
    
    Args:
        graph: Directed graph (node -> set of dependent nodes)
        all_nodes: Set of all nodes in the graph
    
    Returns:
        List[int]: Nodes involved in the cycle
    """
    # Build reverse graph for DFS (node -> set of nodes it depends on)
    reverse_graph: Dict[int, Set[int]] = defaultdict(set)
    for node, dependents in graph.items():
        for dependent in dependents:
            reverse_graph[dependent].add(node)
    
    # DFS to find cycle
    WHITE = 0  # Unvisited
    GRAY = 1   # Currently in recursion stack
    BLACK = 2  # Fully processed
    
    color: Dict[int, int] = {node: WHITE for node in all_nodes}
    parent: Dict[int, Optional[int]] = {node: None for node in all_nodes}
    cycle_start: Optional[int] = None
    cycle_end: Optional[int] = None
    
    def dfs(node: int) -> bool:
        """DFS helper to detect back edge (cycle)."""
        nonlocal cycle_start, cycle_end
        
        color[node] = GRAY
        
        for neighbor in reverse_graph.get(node, set()):
            if color[neighbor] == WHITE:
                parent[neighbor] = node
                if dfs(neighbor):
                    return True
            elif color[neighbor] == GRAY:
                # Back edge found - cycle detected
                cycle_start = neighbor
                cycle_end = node
                return True
        
        color[node] = BLACK
        return False
    
    # Try DFS from each unvisited node
    for node in all_nodes:
        if color[node] == WHITE:
            if dfs(node):
                # Reconstruct cycle path
                cycle = []
                current = cycle_end
                while current is not None:
                    cycle.append(current)
                    if current == cycle_start:
                        break
                    current = parent.get(current)
                cycle.append(cycle_start)  # Complete the cycle
                return cycle[::-1]  # Reverse to show cycle in order
    
    # Fallback: return nodes that couldn't be processed
    return [node for node in all_nodes if color[node] != BLACK]


# ============================================================================
# TEST CASES
# ============================================================================

def test_valid_dependencies():
    """Test Case 1: Valid dependencies with no cycles."""
    print("=" * 60)
    print("TEST CASE 1: Valid Dependencies (No Cycles)")
    print("=" * 60)
    
    rules = [
        {'node_id': 7, 'dependencies': [3, 4]},
        {'node_id': 3, 'dependencies': [2, 10]},
        {'node_id': 8, 'dependencies': [7, 9]}
    ]
    
    print("\nInput Rules:")
    for rule in rules:
        print(f"  Node {rule['node_id']} depends on: {rule['dependencies']}")
    
    try:
        execution_order = resolve_execution_order(rules)
        print(f"\n[PASS] Execution Order (Topological Sort):")
        print(f"   {execution_order}")
        
        # Verify order constraints
        assert execution_order.index(3) < execution_order.index(7), "Node 3 must come before Node 7"
        assert execution_order.index(4) < execution_order.index(7), "Node 4 must come before Node 7"
        assert execution_order.index(7) < execution_order.index(8), "Node 7 must come before Node 8"
        assert execution_order.index(2) < execution_order.index(3), "Node 2 must come before Node 3"
        assert execution_order.index(10) < execution_order.index(3), "Node 10 must come before Node 3"
        assert execution_order.index(9) < execution_order.index(8), "Node 9 must come before Node 8"
        
        print("\n[PASS] All order constraints satisfied!")
        print("\n" + "=" * 60 + "\n")
        
    except CircularDependencyError as e:
        print(f"\n❌ Unexpected error: {e}")
        raise


def test_circular_dependency():
    """Test Case 2: Circular dependency detection."""
    print("=" * 60)
    print("TEST CASE 2: Circular Dependency Detection")
    print("=" * 60)
    
    rules = [
        {'node_id': 7, 'dependencies': [3, 4]},
        {'node_id': 3, 'dependencies': [2, 10]},
        {'node_id': 8, 'dependencies': [7, 9]},
        {'node_id': 7, 'dependencies': [8]}  # Creates cycle: 7 -> 8 -> 7
    ]
    
    print("\nInput Rules:")
    for rule in rules:
        print(f"  Node {rule['node_id']} depends on: {rule['dependencies']}")
    
    print("\n[WARN] Cycle: Node 7 depends on Node 8, and Node 8 depends on Node 7")
    
    try:
        execution_order = resolve_execution_order(rules)
        print(f"\n[FAIL] ERROR: Should have raised CircularDependencyError!")
        print(f"   Got execution order: {execution_order}")
        raise AssertionError("Should have detected circular dependency")
        
    except CircularDependencyError as e:
        print(f"\n[PASS] Circular Dependency Detected!")
        print(f"   Error Message: {e}")
        print(f"   Cycle Nodes: {e.cycle_nodes}")
        
        # Verify cycle contains both 7 and 8
        assert 7 in e.cycle_nodes, "Cycle should contain Node 7"
        assert 8 in e.cycle_nodes, "Cycle should contain Node 8"
        
        print("\n[PASS] Error correctly identifies cycle nodes!")
        print("\n" + "=" * 60 + "\n")


def test_complex_cycle():
    """Test Case 3: Complex cycle (3-node cycle)."""
    print("=" * 60)
    print("TEST CASE 3: Complex Cycle (3 Nodes)")
    print("=" * 60)
    
    rules = [
        {'node_id': 3, 'dependencies': [4]},  # 3 -> 4
        {'node_id': 4, 'dependencies': [5]},  # 4 -> 5
        {'node_id': 5, 'dependencies': [3]}   # 5 -> 3 (cycle: 3 -> 4 -> 5 -> 3)
    ]
    
    print("\nInput Rules:")
    for rule in rules:
        print(f"  Node {rule['node_id']} depends on: {rule['dependencies']}")
    
    print("\n[WARN] Cycle: Node 3 -> Node 4 -> Node 5 -> Node 3")
    
    try:
        execution_order = resolve_execution_order(rules)
        print(f"\n[FAIL] ERROR: Should have raised CircularDependencyError!")
        raise AssertionError("Should have detected circular dependency")
        
    except CircularDependencyError as e:
        print(f"\n[PASS] Circular Dependency Detected!")
        print(f"   Error Message: {e}")
        print(f"   Cycle Nodes: {e.cycle_nodes}")
        
        # Verify cycle contains all three nodes
        assert 3 in e.cycle_nodes, "Cycle should contain Node 3"
        assert 4 in e.cycle_nodes, "Cycle should contain Node 4"
        assert 5 in e.cycle_nodes, "Cycle should contain Node 5"
        
        print("\n[PASS] Error correctly identifies all cycle nodes!")
        print("\n" + "=" * 60 + "\n")


def test_no_dependencies():
    """Test Case 4: Rules with no dependencies (leaf nodes)."""
    print("=" * 60)
    print("TEST CASE 4: Rules with No Dependencies")
    print("=" * 60)
    
    rules = [
        {'node_id': 2, 'dependencies': []},
        {'node_id': 10, 'dependencies': []},
        {'node_id': 9, 'dependencies': []}
    ]
    
    print("\nInput Rules:")
    for rule in rules:
        print(f"  Node {rule['node_id']} depends on: {rule['dependencies']}")
    
    try:
        execution_order = resolve_execution_order(rules)
        print(f"\n[PASS] Execution Order:")
        print(f"   {execution_order}")
        
        # All nodes should be in execution order (order doesn't matter for independent nodes)
        assert len(execution_order) == 3, "Should have 3 nodes in execution order"
        assert set(execution_order) == {2, 10, 9}, "Should contain all three nodes"
        
        print("\n[PASS] All independent nodes processed!")
        print("\n" + "=" * 60 + "\n")
        
    except CircularDependencyError as e:
        print(f"\n[FAIL] Unexpected error: {e}")
        raise


if __name__ == "__main__":
    """Run all test cases."""
    print("\n" + "=" * 60)
    print("TYPE 3 RULE EXECUTION ORDER RESOLUTION - TEST SUITE")
    print("=" * 60 + "\n")
    
    # Run test cases
    test_valid_dependencies()
    test_circular_dependency()
    test_complex_cycle()
    test_no_dependencies()
    
    print("=" * 60)
    print("[PASS] ALL TESTS PASSED!")
    print("=" * 60 + "\n")

