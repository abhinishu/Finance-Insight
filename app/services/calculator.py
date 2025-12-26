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
from app.models import (
    DimHierarchy,
    FactCalculatedResult,
    MetadataRule,
    UseCase,
    UseCaseRun,
    RunStatus,
)

logger = logging.getLogger(__name__)


def apply_rule_to_leaf(
    session: Session, 
    leaf_node_id: str, 
    rule: MetadataRule
) -> Dict[str, Decimal]:
    """
    Stage 1: Apply rule to a leaf node by executing sql_where against fact_pnl_gold.
    
    Args:
        session: Database session
        leaf_node_id: Leaf node ID (for validation)
        rule: MetadataRule with sql_where clause
    
    Returns:
        Dictionary with measure values: {daily: Decimal, mtd: Decimal, ytd: Decimal, pytd: Decimal}
    """
    if not rule.sql_where:
        logger.warning(f"Rule {rule.rule_id} for node {leaf_node_id} has no sql_where clause")
        return {
            'daily': Decimal('0'),
            'mtd': Decimal('0'),
            'ytd': Decimal('0'),
            'pytd': Decimal('0'),
        }
    
    # Execute SQL WHERE clause against fact_pnl_gold
    sql_query = f"""
        SELECT 
            COALESCE(SUM(daily_pnl), 0) as daily_pnl,
            COALESCE(SUM(mtd_pnl), 0) as mtd_pnl,
            COALESCE(SUM(ytd_pnl), 0) as ytd_pnl,
            COALESCE(SUM(pytd_pnl), 0) as pytd_pnl
        FROM fact_pnl_gold
        WHERE {rule.sql_where}
    """
    
    try:
        result = session.execute(text(sql_query)).fetchone()
        
        return {
            'daily': Decimal(str(result[0] or 0)),
            'mtd': Decimal(str(result[1] or 0)),
            'ytd': Decimal(str(result[2] or 0)),
            'pytd': Decimal(str(result[3] or 0)),
        }
    except Exception as e:
        logger.error(f"Error applying rule {rule.rule_id} to leaf {leaf_node_id}: {e}")
        return {
            'daily': Decimal('0'),
            'mtd': Decimal('0'),
            'ytd': Decimal('0'),
            'pytd': Decimal('0'),
        }


def waterfall_up(
    hierarchy_dict: Dict,
    children_dict: Dict,
    adjusted_results: Dict[str, Dict[str, Decimal]],
    max_depth: int
) -> Dict[str, Dict[str, Decimal]]:
    """
    Stage 2: Waterfall up - bottom-up aggregation.
    Parent nodes sum the rule-adjusted values of their children.
    
    Args:
        hierarchy_dict: Dictionary mapping node_id -> node data
        children_dict: Dictionary mapping parent_node_id -> list of children
        adjusted_results: Dictionary with leaf node adjusted values (from Stage 1)
        max_depth: Maximum depth in hierarchy
    
    Returns:
        Updated adjusted_results with all parent nodes calculated
    """
    # Process nodes by depth (deepest first, bottom-up)
    for depth in range(max_depth, -1, -1):
        for node_id, node in hierarchy_dict.items():
            if node.depth == depth and not node.is_leaf:
                # Sum children's adjusted values
                children = children_dict.get(node_id, [])
                
                if children:
                    # Sum children's adjusted values
                    adjusted_results[node_id] = {
                        'daily': sum(
                            adjusted_results.get(child_id, {}).get('daily', Decimal('0'))
                            for child_id in children
                        ),
                        'mtd': sum(
                            adjusted_results.get(child_id, {}).get('mtd', Decimal('0'))
                            for child_id in children
                        ),
                        'ytd': sum(
                            adjusted_results.get(child_id, {}).get('ytd', Decimal('0'))
                            for child_id in children
                        ),
                        'pytd': sum(
                            adjusted_results.get(child_id, {}).get('pytd', Decimal('0'))
                            for child_id in children
                        ),
                    }
                else:
                    # No children - set to zero
                    adjusted_results[node_id] = {
                        'daily': Decimal('0'),
                        'mtd': Decimal('0'),
                        'ytd': Decimal('0'),
                        'pytd': Decimal('0'),
                    }
    
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
    
    try:
        # Load hierarchy for the use case's structure
        hierarchy_dict, children_dict, leaf_nodes = load_hierarchy(session, use_case_id)
        
        if not hierarchy_dict:
            raise ValueError(f"No hierarchy found for use case '{use_case_id}'")
        
        max_depth = max(node.depth for node in hierarchy_dict.values())
        
        # Load facts
        facts_df = load_facts(session)
        
        # Calculate natural rollups (baseline - no rules applied)
        natural_results = calculate_natural_rollup(
            hierarchy_dict, children_dict, leaf_nodes, facts_df
        )
        
        # Load active rules for use case (only rules with sql_where)
        rules_dict = load_rules(session, use_case_id)
        active_rules = {
            node_id: rule
            for node_id, rule in rules_dict.items()
            if rule.sql_where  # Only rules with SQL WHERE clause are active
        }
        
        # Stage 1: Rule Application with "Most Specific Wins" Policy
        # Child rules override parent rules. Apply rules bottom-up, skipping parent
        # rules if any child has a rule.
        adjusted_results = natural_results.copy()
        rules_applied = 0
        
        # Helper function to check if any descendant has a rule
        def has_descendant_rule(node_id: str) -> bool:
            """Check if any descendant (child, grandchild, etc.) has a rule."""
            children = children_dict.get(node_id, [])
            for child_id in children:
                if child_id in active_rules:
                    return True
                if has_descendant_rule(child_id):
                    return True
            return False
        
        # Apply rules bottom-up (deepest first), but only if no descendant has a rule
        # Process nodes by depth (deepest first)
        for depth in range(max_depth, -1, -1):
            for node_id, node in hierarchy_dict.items():
                if node.depth == depth and node_id in active_rules:
                    # Check if any descendant has a rule
                    if not has_descendant_rule(node_id):
                        # No descendant has a rule, so apply this rule
                        rule = active_rules[node_id]
                        
                        if node.is_leaf:
                            # For leaf nodes, apply rule directly
                            rule_adjusted = apply_rule_to_leaf(session, node_id, rule)
                            adjusted_results[node_id] = rule_adjusted
                        else:
                            # For non-leaf nodes, apply rule to get aggregated value
                            # This executes the SQL WHERE clause against fact_pnl_gold
                            rule_adjusted = apply_rule_to_leaf(session, node_id, rule)
                            adjusted_results[node_id] = rule_adjusted
                        
                        rules_applied += 1
                        logger.info(f"Applied rule {rule.rule_id} to node {node_id} (Most Specific Wins)")
                    else:
                        # Descendant has a rule, so skip this parent rule
                        logger.info(f"Skipping rule for node {node_id} - descendant has more specific rule")
        
        # Stage 2: Waterfall Up
        # Perform bottom-up aggregation: parents sum rule-adjusted children
        adjusted_results = waterfall_up(
            hierarchy_dict, children_dict, adjusted_results, max_depth
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
        
        # Save results to database
        num_results = save_calculation_results(
            run.run_id,
            hierarchy_dict,
            natural_results,
            adjusted_results,
            plug_results,
            active_rules,
            session
        )
        
        # Update run status
        end_time = time.time()
        duration_ms = int((end_time - start_time) * 1000)
        
        run.status = RunStatus.COMPLETED
        run.calculation_duration_ms = duration_ms
        run.parameters_snapshot = {
            'rules_applied': rules_applied,
            'rule_ids': [rule.rule_id for rule in active_rules.values()],
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
        # Update run status to failed
        run.status = RunStatus.FAILED
        session.commit()
        logger.error(f"Calculation failed for use case {use_case_id}: {e}", exc_info=True)
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

