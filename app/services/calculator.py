"""
Calculation Service - Waterfall Calculation Engine
Implements the three-stage waterfall: Leaf Application, Waterfall Up, and Reconciliation Plug.
"""

import logging
import time
from collections import defaultdict
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.engine.waterfall import (
    calculate_natural_rollup,
    load_facts,
    load_hierarchy,
    load_rules,
)
from app.services.unified_pnl_service import (
    _calculate_strategy_rollup,
    _calculate_legacy_rollup,
)
from app.models import (
    DimHierarchy,
    FactCalculatedResult,
    MetadataRule,
    UseCase,
    UseCaseRun,
    RunStatus,
)
from app.services.dependency_resolver import (
    DependencyResolver,
    CircularDependencyError,
    evaluate_type3_expression
)

logger = logging.getLogger(__name__)


def apply_rule_to_leaf(
    session: Session, 
    leaf_node_id: str, 
    rule: MetadataRule,
    use_case: Optional[UseCase] = None
) -> Dict[str, Decimal]:
    """
    Stage 1: Apply rule to a leaf node by executing sql_where against the appropriate fact table.
    
    Phase 5.5: Updated to support table-per-use-case strategy via use_case.input_table_name.
    
    Args:
        session: Database session
        leaf_node_id: Leaf node ID (for validation)
        rule: MetadataRule with sql_where clause
        use_case: Optional UseCase object to determine input table (if None, defaults to fact_pnl_gold)
    
    Returns:
        Dictionary with measure values: {daily: Decimal, mtd: Decimal, ytd: Decimal, pytd: Decimal}
    
    Raises:
        Exception: If SQL execution fails (transaction will be rolled back by caller)
    """
    if not rule.sql_where:
        logger.warning(f"Rule {rule.rule_id} for node {leaf_node_id} has no sql_where clause")
        return {
            'daily': Decimal('0'),
            'mtd': Decimal('0'),
            'ytd': Decimal('0'),
            'pytd': Decimal('0'),
        }
    
    # Validate and sanitize SQL WHERE clause
    sql_where = rule.sql_where.strip()
    
    # Basic validation: Check for dangerous patterns
    dangerous_patterns = [';', '--', '/*', '*/', 'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
    sql_where_upper = sql_where.upper()
    for pattern in dangerous_patterns:
        if pattern in sql_where_upper:
            error_msg = f"Rule {rule.rule_id} for node {leaf_node_id} contains dangerous SQL pattern: {pattern}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    # Phase 5.5: Determine which table to query based on use_case.input_table_name
    table_name = 'fact_pnl_gold'  # Default
    if use_case and use_case.input_table_name:
        table_name = use_case.input_table_name
        logger.info(f"apply_rule_to_leaf: Using table '{table_name}' for use case {use_case.use_case_id}")
    else:
        logger.info(f"apply_rule_to_leaf: No use_case or input_table_name provided, defaulting to 'fact_pnl_gold'")
    
    # Phase 5.5: Get measure column name based on table and rule.measure_name
    from app.engine.waterfall import get_measure_column_name
    measure_name = rule.measure_name or 'daily_pnl'
    target_column = get_measure_column_name(measure_name, table_name)
    
    logger.info(f"apply_rule_to_leaf: Node {leaf_node_id}, measure_name={measure_name}, table={table_name}, target_column={target_column}")
    
    # Build SQL query based on table structure
    if table_name == 'fact_pnl_use_case_3':
        # Phase 5.9: Use target_column instead of hardcoding pnl_daily
        # This supports all measures: pnl_daily, pnl_commission, pnl_trade
        sql_query = f"""
            SELECT 
                COALESCE(SUM({target_column}), 0) as measure_value,
                0 as mtd_pnl,
                0 as ytd_pnl,
                0 as pytd_pnl
            FROM fact_pnl_use_case_3
            WHERE {sql_where}
        """
    elif table_name == 'fact_pnl_entries':
        # fact_pnl_entries uses daily_amount, wtd_amount, ytd_amount
        sql_query = f"""
            SELECT 
                COALESCE(SUM(daily_amount), 0) as daily_pnl,
                COALESCE(SUM(wtd_amount), 0) as mtd_pnl,
                COALESCE(SUM(ytd_amount), 0) as ytd_pnl,
                0 as pytd_pnl
            FROM fact_pnl_entries
            WHERE {sql_where}
        """
    else:
        # Default: fact_pnl_gold uses daily_pnl, mtd_pnl, ytd_pnl, pytd_pnl
        sql_query = f"""
            SELECT 
                COALESCE(SUM(daily_pnl), 0) as daily_pnl,
                COALESCE(SUM(mtd_pnl), 0) as mtd_pnl,
                COALESCE(SUM(ytd_pnl), 0) as ytd_pnl,
                COALESCE(SUM(pytd_pnl), 0) as pytd_pnl
            FROM fact_pnl_gold
            WHERE {sql_where}
        """
    
    try:
        result = session.execute(text(sql_query)).fetchone()
        
        # Phase 5.9: Map measure_value to 'daily' key so it appears in "Adjusted Daily P&L" column
        # The measure_value is the sum of the target_column (pnl_daily, pnl_commission, or pnl_trade)
        measure_value = Decimal(str(result[0] or 0))
        
        return {
            'daily': measure_value,  # Map to 'daily' key for display in Adjusted Daily P&L column
            'mtd': Decimal(str(result[1] or 0)),
            'ytd': Decimal(str(result[2] or 0)),
            'pytd': Decimal(str(result[3] or 0)),
        }
    except Exception as e:
        # CRITICAL: Log the original exception with full traceback
        logger.error(
            f"SQL execution failed for rule {rule.rule_id} (node {leaf_node_id}). "
            f"Table: {table_name}, SQL WHERE clause: {sql_where}. "
            f"Error: {e}",
            exc_info=True
        )
        # Re-raise the exception so caller can handle transaction rollback
        raise


def waterfall_up(
    hierarchy_dict: Dict,
    children_dict: Dict,
    adjusted_results: Dict[str, Dict[str, Decimal]],
    max_depth: int,
    natural_results: Optional[Dict[str, Dict[str, Decimal]]] = None,
    children_natural_sum: Optional[Dict[str, Dict[str, Decimal]]] = None,
    skip_nodes: Optional[set] = None
) -> Dict[str, Dict[str, Decimal]]:
    """
    Stage 2: Waterfall up - bottom-up aggregation.
    Parent nodes sum the rule-adjusted values of their children.
    
    Phase 5.8: Support for Hybrid Parents - Parent nodes that have both:
    - Direct rows in fact table (captured in natural_results)
    - Children in hierarchy (summed from adjusted_results)
    
    For hybrid parents: Adjusted = Direct (from natural) + Sum(Children)
    For regular parents: Adjusted = Sum(Children)
    
    Phase 5.9: Support for Math Rules - Nodes with Math rules are skipped
    - Math rules are the final authority for a node's value
    - waterfall_up must not overwrite Math rule results
    
    Args:
        hierarchy_dict: Dictionary mapping node_id -> node data
        children_dict: Dictionary mapping parent_node_id -> list of children
        adjusted_results: Dictionary with leaf node adjusted values (from Stage 1)
        max_depth: Maximum depth in hierarchy
        natural_results: Optional dictionary with natural values (for hybrid parent support)
        children_natural_sum: Optional pre-calculated children natural sums
        skip_nodes: Optional set of node IDs to skip (nodes with Math rules)
    
    Returns:
        Updated adjusted_results with all parent nodes calculated
    """
    # Process nodes by depth (deepest first, bottom-up)
    for depth in range(max_depth, -1, -1):
        for node_id, node in hierarchy_dict.items():
            if node.depth == depth and not node.is_leaf:
                # Phase 5.9: Skip nodes with Math rules (Math rules are the final authority)
                if skip_nodes and node_id in skip_nodes:
                    logger.info(
                        f"Skipping waterfall aggregation for {node_id} ('{node.node_name}') - "
                        f"Math Rule already calculated this node"
                    )
                    continue
                # Sum children's adjusted values
                children = children_dict.get(node_id, [])
                
                # Calculate children sum
                children_sum_daily = sum(
                    adjusted_results.get(child_id, {}).get('daily', Decimal('0'))
                    for child_id in children
                )
                children_sum_mtd = sum(
                    adjusted_results.get(child_id, {}).get('mtd', Decimal('0'))
                    for child_id in children
                )
                children_sum_ytd = sum(
                    adjusted_results.get(child_id, {}).get('ytd', Decimal('0'))
                    for child_id in children
                )
                children_sum_pytd = sum(
                    adjusted_results.get(child_id, {}).get('pytd', Decimal('0'))
                    for child_id in children
                )
                
                # Phase 5.8: Get parent's direct value from natural_results (for hybrid parents)
                # This captures direct P&L rows for parent nodes that also have children
                direct_daily = Decimal('0')
                direct_mtd = Decimal('0')
                direct_ytd = Decimal('0')
                direct_pytd = Decimal('0')
                
                # Phase 5.8: Extract direct value for hybrid parents
                # natural_results[node_id] contains: Direct + Children Natural (for hybrid parents)
                # We need: Direct = Natural - Children Natural
                if natural_results and node_id in natural_results:
                    natural_node = natural_results[node_id]
                    natural_daily = natural_node.get('daily', Decimal('0'))
                    natural_mtd = natural_node.get('mtd', Decimal('0'))
                    natural_ytd = natural_node.get('ytd', Decimal('0'))
                    natural_pytd = natural_node.get('pytd', Decimal('0'))
                    
                    # Calculate children natural sum (if available)
                    children_natural_daily = Decimal('0')
                    children_natural_mtd = Decimal('0')
                    children_natural_ytd = Decimal('0')
                    children_natural_pytd = Decimal('0')
                    
                    if children_natural_sum and node_id in children_natural_sum:
                        children_natural_daily = children_natural_sum[node_id].get('daily', Decimal('0'))
                        children_natural_mtd = children_natural_sum[node_id].get('mtd', Decimal('0'))
                        children_natural_ytd = children_natural_sum[node_id].get('ytd', Decimal('0'))
                        children_natural_pytd = children_natural_sum[node_id].get('pytd', Decimal('0'))
                    else:
                        # Fallback: Calculate children natural sum from natural_results
                        for child_id in children:
                            if natural_results and child_id in natural_results:
                                child_natural = natural_results[child_id]
                                children_natural_daily += child_natural.get('daily', Decimal('0'))
                                children_natural_mtd += child_natural.get('mtd', Decimal('0'))
                                children_natural_ytd += child_natural.get('ytd', Decimal('0'))
                                children_natural_pytd += child_natural.get('pytd', Decimal('0'))
                    
                    # Extract direct value: Direct = Natural - Children Natural
                    direct_daily = natural_daily - children_natural_daily
                    direct_mtd = natural_mtd - children_natural_mtd
                    direct_ytd = natural_ytd - children_natural_ytd
                    direct_pytd = natural_pytd - children_natural_pytd
                    
                    # Only use direct value if it's positive (indicates direct rows exist)
                    # Negative values indicate calculation error or data inconsistency
                    if direct_daily < Decimal('0'):
                        direct_daily = Decimal('0')
                    if direct_mtd < Decimal('0'):
                        direct_mtd = Decimal('0')
                    if direct_ytd < Decimal('0'):
                        direct_ytd = Decimal('0')
                    if direct_pytd < Decimal('0'):
                        direct_pytd = Decimal('0')
                
                # Combine: Direct value (from natural) + Sum of children (from adjusted)
                # For hybrid parents: Adjusted = Direct + Children
                # For regular parents: Adjusted = Children (direct = 0)
                adjusted_results[node_id] = {
                    'daily': direct_daily + children_sum_daily,
                    'mtd': direct_mtd + children_sum_mtd,
                    'ytd': direct_ytd + children_sum_ytd,
                    'pytd': direct_pytd + children_sum_pytd,
                }
                
                # Log hybrid parent detection for debugging
                if direct_daily > Decimal('0') or direct_mtd > Decimal('0') or direct_ytd > Decimal('0'):
                    logger.info(
                        f"Hybrid Parent detected: {node_id} ('{node.node_name}') - "
                        f"Direct: daily={direct_daily}, Children Sum: daily={children_sum_daily}, "
                        f"Combined Adjusted: daily={adjusted_results[node_id]['daily']}"
                    )
    
    return adjusted_results


def calculate_plugs(
    natural_results: Dict[str, Dict[str, Decimal]],
    adjusted_results: Dict[str, Dict[str, Decimal]]
) -> Dict[str, Dict[str, Decimal]]:
    """
    Stage 3: Calculate Reconciliation Plug for every node.
    
    GOLDEN EQUATION: Natural GL Baseline = Adjusted P&L + Reconciliation Plug
    Therefore: Plug = Natural_Value - Adjusted_Value
    
    This ensures mathematical integrity: every P&L dollar is accounted for.
    All calculations use Decimal precision to avoid rounding errors.
    
    Args:
        natural_results: Natural GL values (from bottom-up aggregation without rules)
        adjusted_results: Rule-adjusted values (from Stage 1 & 2)
    
    Returns:
        Dictionary mapping node_id -> {daily: Decimal, mtd: Decimal, ytd: Decimal, pytd: Decimal}
    """
    plug_results = {}
    
    for node_id in natural_results.keys():
        natural = natural_results.get(node_id, {
            'daily': Decimal('0'),
            'mtd': Decimal('0'),
            'ytd': Decimal('0'),
            'pytd': Decimal('0'),
        })
        adjusted = adjusted_results.get(node_id, {
            'daily': Decimal('0'),
            'mtd': Decimal('0'),
            'ytd': Decimal('0'),
            'pytd': Decimal('0'),
        })
        
        plug_results[node_id] = {
            'daily': natural['daily'] - adjusted['daily'],
            'mtd': natural['mtd'] - adjusted['mtd'],
            'ytd': natural['ytd'] - adjusted['ytd'],
            'pytd': natural['pytd'] - adjusted['pytd'],
        }
    
    return plug_results


def calculate_use_case(
    use_case_id: UUID,
    session: Session,
    triggered_by: str = "system",
    version_tag: Optional[str] = None
) -> Dict:
    """
    Main calculation function for a use case.
    
    Implements the three-stage waterfall:
    1. Stage 1 (Leaf Application): Apply rules to leaf nodes
    2. Stage 2 (Waterfall Up): Bottom-up aggregation of rule-adjusted values
    3. Stage 3 (The Plug): Calculate Reconciliation Plug = Natural - Adjusted
    
    Args:
        use_case_id: Use case UUID
        session: Database session
        triggered_by: User ID who triggered the calculation
        version_tag: Optional version tag for the run (e.g., "Nov_Actuals_v1")
    
    Returns:
        Dictionary with calculation results:
        {
            'run_id': UUID,
            'use_case_id': UUID,
            'natural_results': Dict[node_id -> measures],
            'adjusted_results': Dict[node_id -> measures],
            'plug_results': Dict[node_id -> measures],
            'rules_applied': int,
            'total_plug': Dict[measure -> Decimal],
            'duration_ms': int
        }
    """
    start_time = time.time()
    
    # Validate use case exists
    use_case = session.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
    if not use_case:
        raise ValueError(f"Use case '{use_case_id}' not found")
    
    # Create run record
    if not version_tag:
        version_tag = f"run_{int(time.time())}"
    
    run = UseCaseRun(
        use_case_id=use_case_id,
        version_tag=version_tag,
        status=RunStatus.IN_PROGRESS,
        triggered_by=triggered_by,
        parameters_snapshot={}  # Will be populated with rule IDs
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    
    # CRITICAL: Wrap entire calculation logic in try/except with proper transaction management
    try:
        # Load hierarchy for the use case's structure
        hierarchy_dict, children_dict, leaf_nodes = load_hierarchy(session, use_case_id)
        
        if not hierarchy_dict:
            raise ValueError(f"No hierarchy found for use case '{use_case_id}'")
        
        # Phase 5.1: Convert hierarchy_dict to list of nodes for RuleResolver compatibility
        # This ensures hierarchy_nodes is available if RuleResolver needs to be called
        hierarchy_nodes = list(hierarchy_dict.values())
        
        max_depth = max(node.depth for node in hierarchy_dict.values())
        
        # Phase 5.6: Dual-Path Rollup Logic (same as GET /results endpoint)
        # Get use case to determine which rollup to use
        use_case = session.query(UseCase).filter(
            UseCase.use_case_id == use_case_id
        ).first()
        
        if use_case and use_case.input_table_name == 'fact_pnl_use_case_3':
            # Use Case 3: Strategy rollup (queries fact_pnl_use_case_3)
            logger.info(f"[Calculator] Using strategy rollup for Use Case 3 (Table: {use_case.input_table_name})")
            natural_results = _calculate_strategy_rollup(
                session, use_case_id, hierarchy_dict, children_dict, leaf_nodes
            )
        else:
            # Use Cases 1 & 2: Legacy rollup (queries fact_pnl_gold)
            logger.info(f"[Calculator] Using legacy rollup for Use Cases 1 & 2")
            natural_results = _calculate_legacy_rollup(
                session, use_case_id, hierarchy_dict, children_dict, leaf_nodes
            )
        
        # Load all rules for use case
        rules_dict = load_rules(session, use_case_id)
        all_rules = list(rules_dict.values())
        
        # Separate SQL rules (Type 1/2) from Math rules (Type 3)
        sql_rules = {
            node_id: rule
            for node_id, rule in rules_dict.items()
            if rule.rule_type != 'NODE_ARITHMETIC' and rule.sql_where
        }
        
        type3_rules = [
            rule for rule in all_rules
            if rule.rule_type == 'NODE_ARITHMETIC' and rule.rule_expression
        ]
        
        # Phase 5.7: Resolve execution order for Type 3 rules
        sorted_type3_rules = []
        if type3_rules:
            try:
                sorted_type3_rules = DependencyResolver.resolve_execution_order(
                    type3_rules,
                    hierarchy_dict
                )
                logger.info(f"Resolved execution order for {len(sorted_type3_rules)} Type 3 rules")
            except CircularDependencyError as e:
                logger.error(f"Circular dependency detected in Type 3 rules: {e}")
                raise ValueError(f"Cannot execute Type 3 rules: {e}")
        
        # Stage 1: Execute SQL Rules (Type 1/2) - Keep existing logic
        adjusted_results = natural_results.copy()
        rules_applied = 0
        
        # Stage 1a: Execute SQL Rules (Type 1/2) with "Most Specific Wins" Policy
        # Helper function to check if any descendant has a rule
        def has_descendant_rule(node_id: str, rules_dict: Dict) -> bool:
            """Check if any descendant (child, grandchild, etc.) has a rule."""
            children = children_dict.get(node_id, [])
            for child_id in children:
                if child_id in rules_dict:
                    return True
                if has_descendant_rule(child_id, rules_dict):
                    return True
            return False
        
        # Apply SQL rules bottom-up (deepest first), but only if no descendant has a rule
        # Process nodes by depth (deepest first)
        for depth in range(max_depth, -1, -1):
            for node_id, node in hierarchy_dict.items():
                if node.depth == depth and node_id in sql_rules:
                    # Check if any descendant has a rule
                    if not has_descendant_rule(node_id, sql_rules):
                        # No descendant has a rule, so apply this rule
                        rule = sql_rules[node_id]
                        
                        # Apply rule (works for both leaf and non-leaf nodes)
                        rule_adjusted = apply_rule_to_leaf(session, node_id, rule, use_case)
                        adjusted_results[node_id] = rule_adjusted
                        
                        rules_applied += 1
                        logger.info(f"Applied SQL rule {rule.rule_id} to node {node_id} (Most Specific Wins)")
                    else:
                        # Descendant has a rule, so skip this parent rule
                        logger.info(f"Skipping SQL rule for node {node_id} - descendant has more specific rule")
        
        # Stage 1b: Execute Type 3 Rules (Math/Allocation Rules) in dependency order
        # Phase 5.7: The Math Dependency Engine
        # Track nodes with Math rules to prevent waterfall_up from overwriting them
        nodes_with_math_rules = set()
        
        for rule in sorted_type3_rules:
            if rule.rule_type != 'NODE_ARITHMETIC':
                continue  # Skip non-Type 3 rules (already handled above)
            
            target_node = rule.node_id
            nodes_with_math_rules.add(target_node)  # Track this node
            
            # Capture original value for Flight Recorder logging
            original_val = adjusted_results.get(target_node, {}).get('daily', Decimal('0'))
            
            # Evaluate the arithmetic expression
            try:
                # Get measure name (default to 'daily')
                measure_name = rule.measure_name or 'daily_pnl'
                # Map measure_name to our internal measure key
                measure_key = 'daily'  # Default
                if 'mtd' in measure_name.lower() or 'commission' in measure_name.lower():
                    measure_key = 'mtd'
                elif 'ytd' in measure_name.lower() or 'trade' in measure_name.lower():
                    measure_key = 'ytd'
                elif 'pytd' in measure_name.lower():
                    measure_key = 'pytd'
                
                # CRITICAL FIX: Build complete calculation_context map with ALL hierarchy nodes
                # Ensure every node in the hierarchy has an entry in the context
                # Use STRING node_id keys to match expression references exactly
                # This prevents "name 'CC_AMER_CASH_NY_001' is not defined" errors
                calculation_context = {}
                
                # Step 1: Normalize all result dictionaries to use string keys
                # This ensures consistent key matching regardless of original key type
                adjusted_results_str_keys = {}
                for key, value in adjusted_results.items():
                    key_str = str(key)
                    adjusted_results_str_keys[key_str] = value
                
                natural_results_str_keys = {}
                for key, value in natural_results.items():
                    key_str = str(key)
                    natural_results_str_keys[key_str] = value
                
                # Step 2: Build context from hierarchy_dict (primary source of truth for node IDs)
                # Use the actual node_id from hierarchy as the key (ensure it's a string)
                for node_id, node in hierarchy_dict.items():
                    # Get the actual node_id string (this is what formulas reference)
                    node_id_str = str(node_id)
                    
                    # Priority 1: Use adjusted value if available
                    if node_id_str in adjusted_results_str_keys:
                        calculation_context[node_id_str] = adjusted_results_str_keys[node_id_str]
                    # Priority 2: Fall back to natural value
                    elif node_id_str in natural_results_str_keys:
                        calculation_context[node_id_str] = natural_results_str_keys[node_id_str]
                    # Priority 3: Ensure all nodes have at least zero values
                    else:
                        calculation_context[node_id_str] = {
                            'daily': Decimal('0'),
                            'mtd': Decimal('0'),
                            'ytd': Decimal('0'),
                            'pytd': Decimal('0'),
                        }
                
                # Step 3: Include any additional keys from adjusted_results that might not be in hierarchy
                # (e.g., intermediate calculated values from previous math rules)
                for node_id_str, values in adjusted_results_str_keys.items():
                    if node_id_str not in calculation_context:
                        calculation_context[node_id_str] = values
                
                # Step 4: Include keys from natural_results that might be missing
                for node_id_str, values in natural_results_str_keys.items():
                    if node_id_str not in calculation_context:
                        calculation_context[node_id_str] = values
                
                # Step 5: Extract node references from expression for validation
                import re
                expression_upper = rule.rule_expression.upper() if rule.rule_expression else ''
                # Extract all identifiers that could be node references
                potential_refs = re.findall(r'\b[A-Z_][A-Z0-9_]*\b', expression_upper)
                # Filter out numeric constants
                node_refs_in_expression = [
                    ref for ref in potential_refs 
                    if not re.match(r'^\d+\.?\d*$', ref)
                    and ref not in ['AND', 'OR', 'NOT', 'TRUE', 'FALSE', 'IF', 'THEN', 'ELSE']
                ]
                
                # Step 6: Debug logging - Show context keys, expression, and validation
                missing_refs = [ref for ref in node_refs_in_expression if ref not in [k.upper() for k in calculation_context.keys()]]
                logger.info(
                    f"🔎 MATH ENGINE CONTEXT: Expression='{rule.rule_expression}' | "
                    f"Node Refs in Expression: {node_refs_in_expression} | "
                    f"Context Keys Sample: {list(calculation_context.keys())[:10]} | "
                    f"Total Context Nodes: {len(calculation_context)} | "
                    f"Missing Refs: {missing_refs if missing_refs else 'None'}"
                )
                
                if missing_refs:
                    logger.warning(
                        f"⚠️ MATH ENGINE: Expression references nodes not in context: {missing_refs}. "
                        f"These will default to 0."
                    )
                
                # Step 7: Evaluate expression using calculation_context
                calculated_values = evaluate_type3_expression(
                    rule.rule_expression,
                    calculation_context,
                    measure=measure_key
                )
                
                # Update adjusted_results with calculated values
                # CRITICAL: Ensure all values are Decimal
                adjusted_results[target_node] = {
                    'daily': Decimal(str(calculated_values.get('daily', Decimal('0')))),
                    'mtd': Decimal(str(calculated_values.get('mtd', Decimal('0')))),
                    'ytd': Decimal(str(calculated_values.get('ytd', Decimal('0')))),
                    'pytd': Decimal(str(calculated_values.get('pytd', Decimal('0')))),
                }
                
                new_val = adjusted_results[target_node]['daily']
                
                rules_applied += 1
                
                # Flight Recorder Logging (High-Visibility)
                logger.info(
                    f"🧮 MATH ENGINE: Node {target_node} | "
                    f"SQL Value: {original_val} | Rule: {rule.rule_expression} | "
                    f"➡️ New Value: {new_val}"
                )
                
            except Exception as e:
                logger.error(f"Error executing Type 3 rule {rule.rule_id} for node {target_node}: {e}")
                # Set to zero on error
                adjusted_results[target_node] = {
                    'daily': Decimal('0'),
                    'mtd': Decimal('0'),
                    'ytd': Decimal('0'),
                    'pytd': Decimal('0'),
                }
        
        # Stage 2: Waterfall Up
        # Perform bottom-up aggregation: parents sum rule-adjusted children
        # Phase 5.8: Pass natural_results to support hybrid parents (direct + children)
        # Phase 5.9: Skip nodes with Math rules (they are the final authority)
        adjusted_results = waterfall_up(
            hierarchy_dict, children_dict, adjusted_results, max_depth, natural_results, None,
            skip_nodes=nodes_with_math_rules
        )
        
        # Stage 3: The Plug
        # Calculate Reconciliation Plug for every node: Plug = Natural - Adjusted
        plug_results = calculate_plugs(natural_results, adjusted_results)
        
        # Calculate total plug across all measures
        total_plug = {
            'daily': sum(plug.get('daily', Decimal('0')) for plug in plug_results.values()),
            'mtd': sum(plug.get('mtd', Decimal('0')) for plug in plug_results.values()),
            'ytd': sum(plug.get('ytd', Decimal('0')) for plug in plug_results.values()),
            'pytd': sum(plug.get('pytd', Decimal('0')) for plug in plug_results.values()),
        }
        
        # Combine SQL and Type 3 rules for saving
        all_active_rules = {**sql_rules}
        for rule in sorted_type3_rules:
            if rule.rule_type == 'NODE_ARITHMETIC':
                all_active_rules[rule.node_id] = rule
        
        # Save results to database
        num_results = save_calculation_results(
            run.run_id,
            hierarchy_dict,
            natural_results,
            adjusted_results,
            plug_results,
            all_active_rules,
            session
        )
        
        # Update run status
        end_time = time.time()
        duration_ms = int((end_time - start_time) * 1000)
        
        run.status = RunStatus.COMPLETED
        run.calculation_duration_ms = duration_ms
        run.parameters_snapshot = {
            'rules_applied': rules_applied,
            'rule_ids': [rule.rule_id for rule in all_active_rules.values()],
            'num_nodes': len(hierarchy_dict),
            'num_results': num_results
        }
        session.commit()
        
        logger.info(
            f"Calculation complete for use case {use_case_id}. "
            f"Rules applied: {rules_applied}, Duration: {duration_ms}ms"
        )
        
        return {
            'run_id': str(run.run_id),
            'use_case_id': str(use_case_id),
            'natural_results': {
                node_id: {
                    'daily': str(measures['daily']),
                    'mtd': str(measures['mtd']),
                    'ytd': str(measures['ytd']),
                    'pytd': str(measures['pytd']),
                }
                for node_id, measures in natural_results.items()
            },
            'adjusted_results': {
                node_id: {
                    'daily': str(measures['daily']),
                    'mtd': str(measures['mtd']),
                    'ytd': str(measures['ytd']),
                    'pytd': str(measures['pytd']),
                }
                for node_id, measures in adjusted_results.items()
            },
            'plug_results': {
                node_id: {
                    'daily': str(measures['daily']),
                    'mtd': str(measures['mtd']),
                    'ytd': str(measures['ytd']),
                    'pytd': str(measures['pytd']),
                }
                for node_id, measures in plug_results.items()
            },
            'rules_applied': rules_applied,
            'total_plug': {
                'daily': str(total_plug['daily']),
                'mtd': str(total_plug['mtd']),
                'ytd': str(total_plug['ytd']),
                'pytd': str(total_plug['pytd']),
            },
            'duration_ms': duration_ms,
        }
    
    except Exception as e:
        # CRITICAL: Log the ORIGINAL exception immediately with full traceback
        logger.error(
            f"Calculation failed for use case {use_case_id}. "
            f"Original error: {e}",
            exc_info=True
        )
        
        # CRITICAL: Explicitly rollback the transaction to reset the connection
        # This prevents InFailedSqlTransaction errors in subsequent operations
        try:
            session.rollback()
            logger.info(f"Transaction rolled back after calculation failure for use case {use_case_id}")
        except Exception as rollback_error:
            logger.error(
                f"Failed to rollback transaction after calculation error: {rollback_error}",
                exc_info=True
            )
            # Try to close and recreate session if rollback fails
            try:
                session.close()
                logger.warning("Closed session after rollback failure")
            except Exception as close_error:
                logger.error(f"Failed to close session: {close_error}", exc_info=True)
        
        # Update run status to failed (in a fresh transaction)
        try:
            # Start a new transaction for updating run status
            run.status = RunStatus.FAILED
            session.commit()
            logger.info(f"Run status updated to FAILED for use case {use_case_id}")
        except Exception as status_error:
            logger.error(
                f"Failed to update run status to FAILED: {status_error}",
                exc_info=True
            )
            # Rollback the status update attempt
            try:
                session.rollback()
            except Exception:
                pass
        
        # Re-raise the original exception so the UI knows it failed
        raise


def save_calculation_results(
    run_id: UUID,
    hierarchy_dict: Dict,
    natural_results: Dict[str, Dict[str, Decimal]],
    adjusted_results: Dict[str, Dict[str, Decimal]],
    plug_results: Dict[str, Dict[str, Decimal]],
    active_rules: Dict[str, MetadataRule],
    session: Session
) -> int:
    """
    Save calculation results to fact_calculated_results table.
    
    Args:
        run_id: Run ID
        hierarchy_dict: Dictionary mapping node_id -> node data
        natural_results: Natural GL values
        adjusted_results: Rule-adjusted values
        plug_results: Reconciliation plug values
        active_rules: Dictionary mapping node_id -> rule (for nodes with rules)
        session: Database session
    
    Returns:
        Number of result rows inserted
    """
    result_objects = []
    
    for node_id in hierarchy_dict.keys():
        # Get natural values
        natural = natural_results.get(node_id, {
            'daily': Decimal('0'),
            'mtd': Decimal('0'),
            'ytd': Decimal('0'),
            'pytd': Decimal('0'),
        })
        
        # Get adjusted values
        adjusted = adjusted_results.get(node_id, {
            'daily': Decimal('0'),
            'mtd': Decimal('0'),
            'ytd': Decimal('0'),
            'pytd': Decimal('0'),
        })
        
        # Get plug values
        plug = plug_results.get(node_id, {
            'daily': Decimal('0'),
            'mtd': Decimal('0'),
            'ytd': Decimal('0'),
            'pytd': Decimal('0'),
        })
        
        # Format measure_vector (adjusted values)
        # CRITICAL FIX: Convert to float with rounding, not string, to prevent InFailedSqlTransaction
        # Use round(float(val), 4) to ensure clean numeric data for PostgreSQL JSONB
        measure_vector = {
            'daily': round(float(adjusted['daily']), 4),
            'mtd': round(float(adjusted['mtd']), 4),
            'ytd': round(float(adjusted['ytd']), 4),
            'pytd': round(float(adjusted['pytd']), 4),
        }
        
        # Format plug_vector
        # CRITICAL FIX: Convert to float with rounding, not string
        plug_vector = {
            'daily': round(float(plug['daily']), 4),
            'mtd': round(float(plug['mtd']), 4),
            'ytd': round(float(plug['ytd']), 4),
            'pytd': round(float(plug['pytd']), 4),
        }
        
        # Check if node has override
        is_override = node_id in active_rules
        
        # Check if reconciled (plug is zero within tolerance)
        tolerance = Decimal('0.01')
        is_reconciled = all(
            abs(plug[measure]) <= tolerance
            for measure in ['daily', 'mtd', 'ytd', 'pytd']
        )
        
        result_obj = FactCalculatedResult(
            run_id=run_id,
            node_id=node_id,
            measure_vector=measure_vector,
            plug_vector=plug_vector,
            is_override=is_override,
            is_reconciled=is_reconciled,
        )
        result_objects.append(result_obj)
    
    # Bulk insert with error handling
    try:
        session.bulk_save_objects(result_objects)
        session.commit()
        return len(result_objects)
    except Exception as e:
        # CRITICAL: Rollback on any error during bulk insert
        session.rollback()
        raise RuntimeError(f"Failed to save calculation results: {e}") from e

