"""
Dependency Resolver Service

Implements topological sort for Type 3 (NODE_ARITHMETIC) rules to determine
execution order based on dependencies.

Phase 5.7: The Math Dependency Engine
"""

import logging
from collections import defaultdict, deque
from typing import Dict, List, Set
from decimal import Decimal

from app.models import MetadataRule, DimHierarchy

logger = logging.getLogger(__name__)


class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected in rule dependencies."""
    pass


class DependencyResolver:
    """
    Resolves execution order for Type 3 (NODE_ARITHMETIC) rules using topological sort.
    """
    
    @staticmethod
    def resolve_execution_order(
        rules: List[MetadataRule],
        hierarchy: Dict[str, DimHierarchy]
    ) -> List[MetadataRule]:
        """
        Resolve execution order for rules using topological sort.
        
        Logic:
        1. Separate SQL rules (Type 1/2) from Math rules (Type 3)
        2. Build dependency graph for Type 3 rules
        3. Perform topological sort
        4. Detect cycles
        
        Args:
            rules: List of all MetadataRule objects
            hierarchy: Dictionary mapping node_id -> DimHierarchy node
            
        Returns:
            List of rules in execution order (SQL rules first, then sorted math rules)
            
        Raises:
            CircularDependencyError: If a circular dependency is detected
        """
        # Step 1: Separate SQL rules from Math rules
        sql_rules = []
        math_rules = []
        
        for rule in rules:
            if rule.rule_type == 'NODE_ARITHMETIC':
                math_rules.append(rule)
            else:
                # Type 1, Type 2, Type 2B are SQL-based (no dependencies)
                sql_rules.append(rule)
        
        logger.info(f"DependencyResolver: Found {len(sql_rules)} SQL rules, {len(math_rules)} Math rules")
        
        if not math_rules:
            # No math rules, return SQL rules only
            return sql_rules
        
        # Step 2: Build dependency graph
        # First, build rule_by_node map for all Type 3 rules
        rule_by_node: Dict[str, MetadataRule] = {}
        for rule in math_rules:
            rule_by_node[rule.node_id] = rule
        
        # Graph structure: {node_id: set of nodes that depend on it}
        # In-degree: number of dependencies for each rule
        graph: Dict[str, Set[str]] = defaultdict(set)  # dependency -> dependents
        in_degree: Dict[str, int] = defaultdict(int)  # node_id -> in-degree count
        
        for rule in math_rules:
            target_node = rule.node_id
            
            # Parse dependencies from rule_dependencies JSONB
            dependencies = []
            if rule.rule_dependencies:
                if isinstance(rule.rule_dependencies, list):
                    dependencies = rule.rule_dependencies
                elif isinstance(rule.rule_dependencies, str):
                    # Handle string representation of JSON array
                    import json
                    try:
                        dependencies = json.loads(rule.rule_dependencies)
                    except:
                        dependencies = []
            
            # Also extract dependencies from rule_expression if not in rule_dependencies
            if not dependencies and rule.rule_expression:
                dependencies = DependencyResolver.extract_dependencies_from_expression(
                    rule.rule_expression,
                    hierarchy
                )
            
            # Build graph edges: dependency -> target
            # Only count dependencies that are ALSO Type 3 rules (not SQL rules or natural rollup)
            for dep_node in dependencies:
                if dep_node in hierarchy:  # Validate dependency exists in hierarchy
                    # Only add edge if dependency is also a Type 3 rule
                    # If dependency is not a Type 3 rule, it's already calculated (SQL/natural)
                    if dep_node in rule_by_node:
                        graph[dep_node].add(target_node)
                        in_degree[target_node] += 1
                    # If dependency is not in rule_by_node, it's from SQL/natural - no edge needed
                else:
                    logger.warning(f"Rule for {target_node} depends on {dep_node} which is not in hierarchy")
            
            # Initialize in-degree for nodes with no dependencies (or only non-Type3 dependencies)
            if target_node not in in_degree:
                in_degree[target_node] = 0
        
        # Step 3: Topological Sort (Kahn's Algorithm)
        sorted_rules = []
        queue = deque()
        
        # Find all nodes with in-degree 0 (no dependencies)
        for node_id in rule_by_node.keys():
            if in_degree[node_id] == 0:
                queue.append(node_id)
        
        # Process queue
        while queue:
            current_node = queue.popleft()
            
            # Add rule to sorted list
            if current_node in rule_by_node:
                sorted_rules.append(rule_by_node[current_node])
            
            # Reduce in-degree for all dependent nodes
            for dependent_node in graph[current_node]:
                in_degree[dependent_node] -= 1
                if in_degree[dependent_node] == 0:
                    queue.append(dependent_node)
        
        # Step 4: Cycle Detection
        # If we didn't process all nodes, there's a cycle
        if len(sorted_rules) < len(math_rules):
            # Find nodes that weren't processed (part of cycle)
            unprocessed = set(rule_by_node.keys()) - {r.node_id for r in sorted_rules}
            cycle_nodes = list(unprocessed)
            
            error_msg = (
                f"Circular dependency detected in Type 3 rules. "
                f"Unprocessed nodes (part of cycle): {cycle_nodes}"
            )
            logger.error(error_msg)
            raise CircularDependencyError(error_msg)
        
        # Step 5: Combine SQL rules (first) with sorted math rules
        final_order = sql_rules + sorted_rules
        
        logger.info(f"DependencyResolver: Execution order resolved: {len(sql_rules)} SQL rules, "
                   f"{len(sorted_rules)} Math rules (topologically sorted)")
        
        return final_order
    
    @staticmethod
    def extract_dependencies_from_expression(
        expression: str,
        hierarchy: Dict[str, DimHierarchy]
    ) -> List[str]:
        """
        Extract node dependencies from a rule expression.
        
        Example: "NODE_3 + NODE_4" -> ["NODE_3", "NODE_4"]
        
        Args:
            expression: Rule expression string (e.g., "NODE_3 - NODE_4")
            hierarchy: Dictionary mapping node_id -> DimHierarchy node
            
        Returns:
            List of node IDs referenced in the expression
        """
        if not expression:
            return []
        
        dependencies = []
        # Simple pattern: Look for "NODE_" followed by alphanumeric/underscore
        import re
        node_pattern = r'NODE_[\w]+'
        matches = re.findall(node_pattern, expression.upper())
        
        # Validate matches exist in hierarchy
        for match in matches:
            # Try exact match first
            if match in hierarchy:
                dependencies.append(match)
            else:
                # Try case-insensitive match
                for node_id in hierarchy.keys():
                    if node_id.upper() == match.upper():
                        dependencies.append(node_id)
                        break
        
        return list(set(dependencies))  # Remove duplicates


def evaluate_type3_expression(
    expression: str,
    node_values: Dict[str, Dict[str, Decimal]],
    measure: str = 'daily'
) -> Dict[str, Decimal]:
    """
    Evaluate a Type 3 arithmetic expression safely using Decimal arithmetic.
    
    Example: "NODE_3 - NODE_4" where NODE_3 has daily=1000, NODE_4 has daily=500
    Returns: {'daily': 500, 'mtd': 500, 'ytd': 500, 'pytd': 0}
    
    Supports: +, -, *, /, parentheses, and numeric constants.
    
    Args:
        expression: Rule expression string (e.g., "NODE_3 - NODE_4" or "NODE_A * 0.10")
        node_values: Dictionary mapping node_id -> {daily: Decimal, mtd: Decimal, ...}
        measure: Which measure to use ('daily', 'mtd', 'ytd', 'pytd')
        
    Returns:
        Dictionary with calculated values for all measures
    """
    if not expression:
        return {
            'daily': Decimal('0'),
            'mtd': Decimal('0'),
            'ytd': Decimal('0'),
            'pytd': Decimal('0'),
        }
    
    # Extract node references from expression
    # Support both NODE_* patterns (e.g., "NODE_3") and actual node IDs (e.g., "CC_AMER_CASH_NY_001")
    import re
    
    # Strategy: Extract all identifiers from expression, then match against known node_ids
    # This is more robust than regex patterns alone
    
    # Get all node_ids from node_values (these are the valid node references)
    valid_node_ids = set(str(node_id).upper() for node_id in node_values.keys())
    
    # Extract all identifiers from expression (alphanumeric + underscores)
    # Pattern matches: CC_AMER_CASH_NY_001, NODE_3, ABC_123, etc.
    all_identifiers = re.findall(r'\b[A-Z_][A-Z0-9_]*\b', expression.upper())
    
    # Filter to only identifiers that match known node_ids
    node_refs = []
    for identifier in all_identifiers:
        # Skip numeric constants (pure numbers)
        if re.match(r'^\d+\.?\d*$', identifier):
            continue
        
        # Skip known operators and keywords
        operators_keywords = {'AND', 'OR', 'NOT', 'TRUE', 'FALSE', 'IF', 'THEN', 'ELSE'}
        if identifier in operators_keywords:
            continue
        
        # Check if identifier matches any node_id (case-insensitive)
        if identifier in valid_node_ids:
            node_refs.append(identifier)
        else:
            # Try case-insensitive match
            for node_id in node_values.keys():
                if str(node_id).upper() == identifier:
                    node_refs.append(identifier)  # Use the identifier as found in expression
                    break
    
    # Remove duplicates while preserving order
    node_refs = list(dict.fromkeys(node_refs))
    
    # Debug logging
    if node_refs:
        logger.debug(f"Extracted node references from expression '{expression}': {node_refs}")
    else:
        logger.warning(f"No node references found in expression '{expression}'. Available node_ids: {list(valid_node_ids)[:10]}")
    
    # Build replacement map for each measure
    replacements = {}
    for measure_name in ['daily', 'mtd', 'ytd', 'pytd']:
        measure_replacements = {}
        for node_ref in node_refs:
            # Find the actual node_id key (case-insensitive match)
            actual_node_id = None
            node_ref_upper = node_ref.upper()
            
            # Try exact match first (case-sensitive)
            if node_ref in node_values:
                actual_node_id = node_ref
            else:
                # Try case-insensitive match
                for node_id in node_values.keys():
                    if str(node_id).upper() == node_ref_upper:
                        actual_node_id = str(node_id)
                        break
            
            if actual_node_id and actual_node_id in node_values:
                value = node_values[actual_node_id].get(measure_name, Decimal('0'))
            else:
                logger.warning(
                    f"Node reference '{node_ref}' not found in node_values. "
                    f"Available keys (sample): {list(node_values.keys())[:10]}"
                )
                value = Decimal('0')
            
            # Replace node_ref with the Decimal value (as string for safe substitution)
            # Store multiple case variations to handle different cases in expression
            measure_replacements[node_ref] = str(value)
            measure_replacements[node_ref.upper()] = str(value)
            measure_replacements[node_ref.lower()] = str(value)
            # Also store the actual node_id key if different
            if actual_node_id and actual_node_id != node_ref:
                measure_replacements[actual_node_id] = str(value)
                measure_replacements[actual_node_id.upper()] = str(value)
                measure_replacements[actual_node_id.lower()] = str(value)
        
        replacements[measure_name] = measure_replacements
    
    # Evaluate expression for each measure
    results = {}
    for measure_name in ['daily', 'mtd', 'ytd', 'pytd']:
        # Start with original expression (preserve case for better matching)
        expr = expression
        
        # Replace node references with values (use word boundaries to avoid partial matches)
        # Sort by length (longest first) to avoid replacing parts of longer node names
        sorted_refs = sorted(replacements[measure_name].keys(), key=len, reverse=True)
        for node_ref in sorted_refs:
            value_str = replacements[measure_name][node_ref]
            # Use word boundary pattern to ensure exact match (case-insensitive)
            import re
            # Escape special regex characters in node_ref
            escaped_ref = re.escape(node_ref)
            # Use case-insensitive pattern with word boundaries
            pattern = r'\b' + escaped_ref + r'\b'
            expr = re.sub(pattern, value_str, expr, flags=re.IGNORECASE)
        
        # Convert to uppercase for final evaluation (to handle any remaining case variations)
        expr = expr.upper()
        
        # Safe evaluation using Decimal arithmetic
        try:
            # Use a restricted environment for eval
            # Only allow Decimal operations and basic math
            from decimal import Decimal as D
            safe_dict = {
                'Decimal': D,
                '__builtins__': {},
            }
            
            # Evaluate the expression
            result = eval(expr, safe_dict)
            
            # Ensure result is Decimal
            if isinstance(result, Decimal):
                results[measure_name] = result
            else:
                results[measure_name] = Decimal(str(result))
                
        except Exception as e:
            logger.error(f"Error evaluating expression '{expression}' for measure '{measure_name}': {e}")
            results[measure_name] = Decimal('0')
    
    return results

