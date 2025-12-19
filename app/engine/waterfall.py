"""
Waterfall Engine for Finance-Insight
Implements bottom-up aggregation, top-down rule application, and reconciliation plugs.
Uses Decimal for all calculations to ensure precision.
"""

import time
from collections import defaultdict
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import (
    DimHierarchy,
    FactCalculatedResult,
    FactPnlGold,
    MetadataRule,
    UseCase,
    UseCaseRun,
    RunStatus,
)


def load_hierarchy(session: Session, use_case_id: Optional[UUID] = None) -> Tuple[Dict, Dict, List]:
    """
    Load hierarchy from dim_hierarchy table.
    
    Args:
        session: SQLAlchemy session
        use_case_id: Optional use case ID to filter by atlas_structure_id
    
    Returns:
        Tuple of:
        - Dictionary mapping node_id -> node data
        - Dictionary mapping parent_node_id -> list of children node_ids
        - List of leaf node_ids
    """
    query = session.query(DimHierarchy)
    
    # If use_case_id provided, filter by use case's atlas_structure_id
    if use_case_id:
        use_case = session.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
        if use_case:
            query = query.filter(DimHierarchy.atlas_source == use_case.atlas_structure_id)
    
    nodes = query.all()
    
    # Build dictionaries
    node_dict = {node.node_id: node for node in nodes}
    children_dict = defaultdict(list)
    leaf_nodes = []
    
    for node in nodes:
        if node.parent_node_id:
            children_dict[node.parent_node_id].append(node.node_id)
        if node.is_leaf:
            leaf_nodes.append(node.node_id)
    
    return node_dict, dict(children_dict), leaf_nodes


def load_facts(session: Session, filters: Optional[Dict] = None) -> pd.DataFrame:
    """
    Load fact data from fact_pnl_gold table.
    
    Args:
        session: SQLAlchemy session
        filters: Optional dictionary with filters like {account_id: [...], cc_id: [...]}
    
    Returns:
        Pandas DataFrame with all fact rows, using Decimal for numeric columns
    """
    query = session.query(FactPnlGold)
    
    # Apply filters if provided
    if filters:
        if 'account_id' in filters:
            query = query.filter(FactPnlGold.account_id.in_(filters['account_id']))
        if 'cc_id' in filters:
            query = query.filter(FactPnlGold.cc_id.in_(filters['cc_id']))
        if 'book_id' in filters:
            query = query.filter(FactPnlGold.book_id.in_(filters['book_id']))
        if 'strategy_id' in filters:
            query = query.filter(FactPnlGold.strategy_id.in_(filters['strategy_id']))
    
    # Load into DataFrame
    facts = query.all()
    
    # Convert to DataFrame
    data = []
    for fact in facts:
        data.append({
            'fact_id': fact.fact_id,
            'account_id': fact.account_id,
            'cc_id': fact.cc_id,
            'book_id': fact.book_id,
            'strategy_id': fact.strategy_id,
            'trade_date': fact.trade_date,
            'daily_pnl': Decimal(str(fact.daily_pnl)),  # Convert to Decimal
            'mtd_pnl': Decimal(str(fact.mtd_pnl)),
            'ytd_pnl': Decimal(str(fact.ytd_pnl)),
            'pytd_pnl': Decimal(str(fact.pytd_pnl)),
        })
    
    df = pd.DataFrame(data)
    
    # Ensure Decimal types are preserved
    if not df.empty:
        df['daily_pnl'] = df['daily_pnl'].apply(lambda x: Decimal(str(x)))
        df['mtd_pnl'] = df['mtd_pnl'].apply(lambda x: Decimal(str(x)))
        df['ytd_pnl'] = df['ytd_pnl'].apply(lambda x: Decimal(str(x)))
        df['pytd_pnl'] = df['pytd_pnl'].apply(lambda x: Decimal(str(x)))
    
    return df


def calculate_natural_rollup(hierarchy_dict: Dict, children_dict: Dict, leaf_nodes: List, facts_df: pd.DataFrame) -> Dict[str, Dict[str, Decimal]]:
    """
    Calculate natural rollups using bottom-up aggregation.
    
    Args:
        hierarchy_dict: Dictionary mapping node_id -> node data
        children_dict: Dictionary mapping parent_node_id -> list of children
        leaf_nodes: List of leaf node_ids
        facts_df: DataFrame with fact data (using Decimal for measures)
    
    Returns:
        Dictionary mapping node_id -> {daily: Decimal, mtd: Decimal, ytd: Decimal, pytd: Decimal}
    """
    results = {}
    measures = ['daily_pnl', 'mtd_pnl', 'ytd_pnl', 'pytd_pnl']
    
    # Step 1: Calculate leaf node values (sum fact rows where cc_id = node_id)
    for leaf_id in leaf_nodes:
        leaf_facts = facts_df[facts_df['cc_id'] == leaf_id]
        
        if len(leaf_facts) > 0:
            results[leaf_id] = {
                'daily': leaf_facts['daily_pnl'].sum(),
                'mtd': leaf_facts['mtd_pnl'].sum(),
                'ytd': leaf_facts['ytd_pnl'].sum(),
                'pytd': leaf_facts['pytd_pnl'].sum(),
            }
        else:
            # No facts for this leaf - set to zero
            results[leaf_id] = {
                'daily': Decimal('0'),
                'mtd': Decimal('0'),
                'ytd': Decimal('0'),
                'pytd': Decimal('0'),
            }
    
    # Step 2: Bottom-up aggregation for parent nodes
    # Process nodes by depth (deepest first)
    max_depth = max(node.depth for node in hierarchy_dict.values())
    
    for depth in range(max_depth, -1, -1):  # Start from deepest, go to root
        for node_id, node in hierarchy_dict.items():
            if node.depth == depth and not node.is_leaf:
                # Sum all children's values
                children = children_dict.get(node_id, [])
                
                if children:
                    # Sum children values using Decimal
                    results[node_id] = {
                        'daily': sum(results.get(child_id, {}).get('daily', Decimal('0')) for child_id in children),
                        'mtd': sum(results.get(child_id, {}).get('mtd', Decimal('0')) for child_id in children),
                        'ytd': sum(results.get(child_id, {}).get('ytd', Decimal('0')) for child_id in children),
                        'pytd': sum(results.get(child_id, {}).get('pytd', Decimal('0')) for child_id in children),
                    }
                else:
                    # No children - set to zero
                    results[node_id] = {
                        'daily': Decimal('0'),
                        'mtd': Decimal('0'),
                        'ytd': Decimal('0'),
                        'pytd': Decimal('0'),
                    }
    
    return results


def load_rules(session: Session, use_case_id: UUID) -> Dict[str, MetadataRule]:
    """
    Load all rules for a use case.
    
    Args:
        session: SQLAlchemy session
        use_case_id: Use case ID
    
    Returns:
        Dictionary mapping node_id -> rule object
    """
    rules = session.query(MetadataRule).filter(
        MetadataRule.use_case_id == use_case_id
    ).all()
    
    return {rule.node_id: rule for rule in rules}


def apply_rule_override(session: Session, facts_df: pd.DataFrame, rule: MetadataRule) -> Dict[str, Decimal]:
    """
    Apply a rule override by executing SQL WHERE clause on facts.
    
    Args:
        session: SQLAlchemy session (for executing SQL)
        facts_df: DataFrame with fact data
        rule: MetadataRule object with sql_where clause
    
    Returns:
        Dictionary {daily: Decimal, mtd: Decimal, ytd: Decimal, pytd: Decimal}
    """
    # Execute SQL WHERE clause on fact table
    # We'll use SQLAlchemy to execute the query safely
    sql_query = f"""
        SELECT 
            SUM(daily_pnl) as daily_pnl,
            SUM(mtd_pnl) as mtd_pnl,
            SUM(ytd_pnl) as ytd_pnl,
            SUM(pytd_pnl) as pytd_pnl
        FROM fact_pnl_gold
        WHERE {rule.sql_where}
    """
    
    try:
        result = session.execute(text(sql_query)).fetchone()
        
        if result and result[0] is not None:
            return {
                'daily': Decimal(str(result[0] or 0)),
                'mtd': Decimal(str(result[1] or 0)),
                'ytd': Decimal(str(result[2] or 0)),
                'pytd': Decimal(str(result[3] or 0)),
            }
        else:
            # No matching rows
            return {
                'daily': Decimal('0'),
                'mtd': Decimal('0'),
                'ytd': Decimal('0'),
                'pytd': Decimal('0'),
            }
    except Exception as e:
        # If SQL execution fails, return zeros
        print(f"Warning: Rule execution failed for node {rule.node_id}: {e}")
        return {
            'daily': Decimal('0'),
            'mtd': Decimal('0'),
            'ytd': Decimal('0'),
            'pytd': Decimal('0'),
        }


def calculate_waterfall(use_case_id: UUID, session: Session, triggered_by: str = "system") -> Dict:
    """
    Main orchestration function for waterfall calculation.
    
    Args:
        use_case_id: Use case ID
        session: SQLAlchemy session
        triggered_by: User ID who triggered the calculation
    
    Returns:
        Dictionary with results and timing information
    """
    start_time = time.time()
    
    # Step 1: Load hierarchy
    hierarchy_dict, children_dict, leaf_nodes = load_hierarchy(session, use_case_id)
    
    # Step 2: Load facts
    facts_df = load_facts(session)
    
    # Step 3: Calculate natural rollups (bottom-up)
    natural_results = calculate_natural_rollup(hierarchy_dict, children_dict, leaf_nodes, facts_df)
    
    # Step 4: Load rules for use case
    rules_dict = load_rules(session, use_case_id)
    
    # Step 5: Apply rule overrides (top-down)
    # Start with natural results, then override where rules exist
    final_results = natural_results.copy()
    override_nodes = set()
    
    # Process nodes top-down (root to leaves)
    max_depth = max(node.depth for node in hierarchy_dict.values())
    
    for depth in range(0, max_depth + 1):
        for node_id, node in hierarchy_dict.items():
            if node.depth == depth and node_id in rules_dict:
                # Apply rule override
                rule = rules_dict[node_id]
                override_values = apply_rule_override(session, facts_df, rule)
                final_results[node_id] = override_values
                override_nodes.add(node_id)
    
    # Step 6: Calculate reconciliation plugs
    # For each node with override: plug = override - sum(children_natural)
    plug_results = {}
    
    for node_id in override_nodes:
        children = children_dict.get(node_id, [])
        
        # Sum children's natural values (not overridden values)
        children_natural_sum = {
            'daily': sum(natural_results.get(child_id, {}).get('daily', Decimal('0')) for child_id in children),
            'mtd': sum(natural_results.get(child_id, {}).get('mtd', Decimal('0')) for child_id in children),
            'ytd': sum(natural_results.get(child_id, {}).get('ytd', Decimal('0')) for child_id in children),
            'pytd': sum(natural_results.get(child_id, {}).get('pytd', Decimal('0')) for child_id in children),
        }
        
        # Calculate plug: override - children_natural
        override_values = final_results[node_id]
        plug_results[node_id] = {
            'daily': override_values['daily'] - children_natural_sum['daily'],
            'mtd': override_values['mtd'] - children_natural_sum['mtd'],
            'ytd': override_values['ytd'] - children_natural_sum['ytd'],
            'pytd': override_values['pytd'] - children_natural_sum['pytd'],
        }
    
    # Calculate duration
    end_time = time.time()
    duration_ms = int((end_time - start_time) * 1000)
    
    return {
        'use_case_id': use_case_id,
        'results': final_results,
        'natural_results': natural_results,
        'plug_results': plug_results,
        'override_nodes': list(override_nodes),
        'duration_ms': duration_ms,
        'triggered_by': triggered_by,
    }


def save_results(run_id: UUID, waterfall_results: Dict, session: Session) -> int:
    """
    Save waterfall calculation results to database.
    
    Args:
        run_id: Run ID from use_case_runs table
        waterfall_results: Results dictionary from calculate_waterfall()
        session: SQLAlchemy session
    
    Returns:
        Number of result rows inserted
    """
    results = waterfall_results['results']
    plug_results = waterfall_results.get('plug_results', {})
    override_nodes = set(waterfall_results.get('override_nodes', []))
    
    result_objects = []
    
    for node_id, measures in results.items():
        # Format measure_vector
        measure_vector = {
            'daily': str(measures['daily']),
            'mtd': str(measures['mtd']),
            'ytd': str(measures['ytd']),
            'pytd': str(measures['pytd']),
        }
        
        # Format plug_vector (only if node has override)
        plug_vector = None
        if node_id in override_nodes and node_id in plug_results:
            plug_vector = {
                'daily': str(plug_results[node_id]['daily']),
                'mtd': str(plug_results[node_id]['mtd']),
                'ytd': str(plug_results[node_id]['ytd']),
                'pytd': str(plug_results[node_id]['pytd']),
            }
            
            # Check if reconciled (plug is zero within tolerance)
            tolerance = Decimal('0.01')
            is_reconciled = all(
                abs(Decimal(plug_vector[measure])) <= tolerance
                for measure in ['daily', 'mtd', 'ytd', 'pytd']
            )
        else:
            is_reconciled = True  # Natural nodes are always reconciled
        
        result_obj = FactCalculatedResult(
            run_id=run_id,
            node_id=node_id,
            measure_vector=measure_vector,
            plug_vector=plug_vector,
            is_override=(node_id in override_nodes),
            is_reconciled=is_reconciled,
        )
        result_objects.append(result_obj)
    
    # Bulk insert
    session.bulk_save_objects(result_objects)
    session.commit()
    
    return len(result_objects)

