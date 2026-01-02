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
    FactPnlEntries,
    FactPnlUseCase3,
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


def load_facts_from_entries(session: Session, use_case_id: Optional[UUID] = None, filters: Optional[Dict] = None) -> pd.DataFrame:
    """
    Load fact data from fact_pnl_entries table (for Project Sterling and similar use cases).
    
    Args:
        session: SQLAlchemy session
        use_case_id: Optional use case ID to filter by
        filters: Optional dictionary with filters like {category_code: [...], pnl_date: [...]}
    
    Returns:
        Pandas DataFrame with all fact rows, using Decimal for numeric columns
        Columns: category_code, daily_amount, wtd_amount, ytd_amount
    """
    query = session.query(FactPnlEntries)
    
    # Filter by use_case_id if provided
    if use_case_id:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"load_facts_from_entries: Filtering by use_case_id: {use_case_id}")
        query = query.filter(FactPnlEntries.use_case_id == use_case_id)
        # Verify the filter is applied
        count_before = session.query(FactPnlEntries).count()
        count_after = query.count()
        logger.info(f"load_facts_from_entries: Total facts before filter: {count_before}, after filter: {count_after}")
    
    # Apply additional filters if provided
    if filters:
        if 'category_code' in filters:
            query = query.filter(FactPnlEntries.category_code.in_(filters['category_code']))
        if 'pnl_date' in filters:
            query = query.filter(FactPnlEntries.pnl_date == filters['pnl_date'])
        if 'scenario' in filters:
            query = query.filter(FactPnlEntries.scenario == filters['scenario'])
    
    # Load into DataFrame
    facts = query.all()
    
    # Convert to DataFrame with correct column mapping
    data = []
    for fact in facts:
        data.append({
            'fact_id': fact.id,
            'category_code': fact.category_code,
            'pnl_date': fact.pnl_date,
            'use_case_id': fact.use_case_id,
            'scenario': fact.scenario,
            # CRITICAL: Map fact_pnl_entries columns to standard names
            'daily_amount': Decimal(str(fact.daily_amount)),
            'wtd_amount': Decimal(str(fact.wtd_amount)),
            'ytd_amount': Decimal(str(fact.ytd_amount)),
            # Map to daily_pnl, mtd_pnl, ytd_pnl for compatibility with calculate_natural_rollup
            'daily_pnl': Decimal(str(fact.daily_amount)),  # daily_amount -> daily_pnl
            'mtd_pnl': Decimal(str(fact.wtd_amount)),      # wtd_amount -> mtd_pnl
            'ytd_pnl': Decimal(str(fact.ytd_amount)),       # ytd_amount -> ytd_pnl
            'pytd_pnl': Decimal('0'),  # Not available in fact_pnl_entries
        })
    
    df = pd.DataFrame(data)
    
    # Ensure Decimal types are preserved
    if not df.empty:
        df['daily_amount'] = df['daily_amount'].apply(lambda x: Decimal(str(x)))
        df['wtd_amount'] = df['wtd_amount'].apply(lambda x: Decimal(str(x)))
        df['ytd_amount'] = df['ytd_amount'].apply(lambda x: Decimal(str(x)))
        df['daily_pnl'] = df['daily_pnl'].apply(lambda x: Decimal(str(x)))
        df['mtd_pnl'] = df['mtd_pnl'].apply(lambda x: Decimal(str(x)))
        df['ytd_pnl'] = df['ytd_pnl'].apply(lambda x: Decimal(str(x)))
    
    return df


def load_facts_from_use_case_3(session: Session, use_case_id: Optional[UUID] = None) -> pd.DataFrame:
    """
    Phase 5.1: Load fact data from fact_pnl_use_case_3 table.
    
    CRITICAL: Loads ALL PnL columns (pnl_daily, pnl_commission, pnl_trade) for multiple measures support.
    All amounts use Decimal type for precision.
    
    Args:
        session: SQLAlchemy session
        use_case_id: Optional use case ID (for logging)
    
    Returns:
        Pandas DataFrame with all fact rows, using Decimal for numeric columns
        Columns: effective_date, strategy, process_2, product_line, pnl_daily, pnl_commission, pnl_trade
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Load all rows from fact_pnl_use_case_3
    facts = session.query(FactPnlUseCase3).all()
    
    logger.info(f"load_facts_from_use_case_3: Loaded {len(facts)} rows from fact_pnl_use_case_3")
    
    # Convert to DataFrame with ALL PnL columns
    data = []
    for fact in facts:
        data.append({
            'entry_id': fact.entry_id,
            'effective_date': fact.effective_date,
            'cost_center': fact.cost_center,
            'division': fact.division,
            'business_area': fact.business_area,
            'product_line': fact.product_line,
            'strategy': fact.strategy,
            'process_1': fact.process_1,
            'process_2': fact.process_2,
            'book': fact.book,
            # CRITICAL: Load ALL PnL columns (for multiple measures support)
            'pnl_daily': Decimal(str(fact.pnl_daily)),
            'pnl_commission': Decimal(str(fact.pnl_commission)),
            'pnl_trade': Decimal(str(fact.pnl_trade)),
            # Map to standard names for compatibility (daily_pnl = pnl_daily for backward compatibility)
            'daily_pnl': Decimal(str(fact.pnl_daily)),
            'mtd_pnl': Decimal('0'),  # Not available in fact_pnl_use_case_3
            'ytd_pnl': Decimal('0'),  # Not available in fact_pnl_use_case_3
            'pytd_pnl': Decimal('0'),  # Not available in fact_pnl_use_case_3
        })
    
    df = pd.DataFrame(data)
    
    # Ensure Decimal types are preserved
    if not df.empty:
        df['pnl_daily'] = df['pnl_daily'].apply(lambda x: Decimal(str(x)))
        df['pnl_commission'] = df['pnl_commission'].apply(lambda x: Decimal(str(x)))
        df['pnl_trade'] = df['pnl_trade'].apply(lambda x: Decimal(str(x)))
        df['daily_pnl'] = df['daily_pnl'].apply(lambda x: Decimal(str(x)))
        
        logger.info(f"load_facts_from_use_case_3: DataFrame created with {len(df)} rows")
        logger.info(f"load_facts_from_use_case_3: Columns: {list(df.columns)}")
        logger.info(f"load_facts_from_use_case_3: Sample pnl_daily sum: {df['pnl_daily'].sum()}")
        logger.info(f"load_facts_from_use_case_3: Sample pnl_commission sum: {df['pnl_commission'].sum()}")
        logger.info(f"load_facts_from_use_case_3: Sample pnl_trade sum: {df['pnl_trade'].sum()}")
    
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
    
    # Step 1: Calculate leaf node values
    # CRITICAL: Support both fact_pnl_gold (cc_id) and fact_pnl_entries (category_code)
    import logging
    logger = logging.getLogger(__name__)
    
    # Debug: Log fact columns and sample values
    if not facts_df.empty:
        logger.info(f"calculate_natural_rollup: facts_df has {len(facts_df)} rows")
        logger.info(f"calculate_natural_rollup: facts_df columns: {list(facts_df.columns)}")
        if 'category_code' in facts_df.columns:
            unique_codes = facts_df['category_code'].unique()[:10]
            logger.info(f"calculate_natural_rollup: Sample category_codes: {list(unique_codes)}")
        if 'cc_id' in facts_df.columns:
            unique_cc_ids = facts_df['cc_id'].unique()[:10]
            logger.info(f"calculate_natural_rollup: Sample cc_ids: {list(unique_cc_ids)}")
        logger.info(f"calculate_natural_rollup: Leaf nodes count: {len(leaf_nodes)}, Sample: {leaf_nodes[:5]}")
    
    for leaf_id in leaf_nodes:
        # Try cc_id first (fact_pnl_gold), then category_code (fact_pnl_entries)
        if 'cc_id' in facts_df.columns:
            leaf_facts = facts_df[facts_df['cc_id'] == leaf_id]
        elif 'category_code' in facts_df.columns:
            leaf_facts = facts_df[facts_df['category_code'] == leaf_id]
        else:
            # Fallback: if neither column exists, skip this leaf
            leaf_facts = pd.DataFrame()
        
        if len(leaf_facts) > 0:
            # CRITICAL: Use daily_pnl, mtd_pnl, ytd_pnl columns (already mapped in load_facts_from_entries)
            daily_sum = leaf_facts['daily_pnl'].sum() if 'daily_pnl' in leaf_facts.columns else Decimal('0')
            mtd_sum = leaf_facts['mtd_pnl'].sum() if 'mtd_pnl' in leaf_facts.columns else Decimal('0')
            ytd_sum = leaf_facts['ytd_pnl'].sum() if 'ytd_pnl' in leaf_facts.columns else Decimal('0')
            pytd_sum = leaf_facts['pytd_pnl'].sum() if 'pytd_pnl' in leaf_facts.columns else Decimal('0')
            
            logger.debug(f"calculate_natural_rollup: Leaf {leaf_id} matched {len(leaf_facts)} facts, daily={daily_sum}")
            
            results[leaf_id] = {
                'daily': daily_sum,
                'mtd': mtd_sum,
                'ytd': ytd_sum,
                'pytd': pytd_sum,
            }
        else:
            # No facts for this leaf - set to zero
            results[leaf_id] = {
                'daily': Decimal('0'),
                'mtd': Decimal('0'),
                'ytd': Decimal('0'),
                'pytd': Decimal('0'),
            }
    
    # Debug: Log how many leaf nodes got matched
    matched_count = sum(1 for leaf_id in leaf_nodes if results.get(leaf_id, {}).get('daily', Decimal('0')) != Decimal('0'))
    logger.info(f"calculate_natural_rollup: Matched {matched_count}/{len(leaf_nodes)} leaf nodes with non-zero values")
    
    # CRITICAL FIX: If no matches found and we have category_code, try aggregating all facts
    # This handles cases where hierarchy node_ids don't match category_code values
    if matched_count == 0 and 'category_code' in facts_df.columns and not facts_df.empty:
        logger.warning(f"calculate_natural_rollup: No leaf nodes matched! Trying aggregate approach...")
        # Aggregate all facts by category_code
        if 'daily_pnl' in facts_df.columns:
            aggregated = facts_df.groupby('category_code').agg({
                'daily_pnl': 'sum',
                'mtd_pnl': 'sum',
                'ytd_pnl': 'sum',
                'pytd_pnl': 'sum' if 'pytd_pnl' in facts_df.columns else lambda x: Decimal('0')
            }).to_dict('index')
            
            # Try to match aggregated values to leaf nodes
            for leaf_id in leaf_nodes:
                # Try exact match first
                if leaf_id in aggregated:
                    results[leaf_id] = {
                        'daily': Decimal(str(aggregated[leaf_id]['daily_pnl'])),
                        'mtd': Decimal(str(aggregated[leaf_id]['mtd_pnl'])),
                        'ytd': Decimal(str(aggregated[leaf_id]['ytd_pnl'])),
                        'pytd': Decimal(str(aggregated[leaf_id].get('pytd_pnl', Decimal('0')))),
                    }
                else:
                    # Try case-insensitive match or partial match
                    matched = False
                    for cat_code, values in aggregated.items():
                        if cat_code.upper() == leaf_id.upper() or leaf_id.upper() in cat_code.upper() or cat_code.upper() in leaf_id.upper():
                            results[leaf_id] = {
                                'daily': Decimal(str(values['daily_pnl'])),
                                'mtd': Decimal(str(values['mtd_pnl'])),
                                'ytd': Decimal(str(values['ytd_pnl'])),
                                'pytd': Decimal(str(values.get('pytd_pnl', Decimal('0')))),
                            }
                            matched = True
                            logger.info(f"calculate_natural_rollup: Matched {leaf_id} to {cat_code} via fuzzy matching")
                            break
                    
                    if not matched:
                        # Still no match - keep zero
                        logger.debug(f"calculate_natural_rollup: No match found for leaf {leaf_id}")
            
            # Recalculate matched count
            matched_count = sum(1 for leaf_id in leaf_nodes if results.get(leaf_id, {}).get('daily', Decimal('0')) != Decimal('0'))
            logger.info(f"calculate_natural_rollup: After aggregate approach, matched {matched_count}/{len(leaf_nodes)} leaf nodes")
        
        # CRITICAL FIX: If still no matches, DO NOT distribute across leaf nodes
        # The category_code values (TRADE_001, etc.) don't match hierarchy node_ids (ENTITY_UK_LTD, etc.)
        # Instead, leave leaf nodes as zero and let the ROOT node be overridden by unified_pnl_service
        if matched_count == 0 and not facts_df.empty:
            logger.warning(
                f"calculate_natural_rollup: No matches found between category_code and node_id. "
                f"Leaf nodes will remain zero. ROOT node will be set by unified_pnl_service in discovery endpoint."
            )
            # Calculate total for logging only (don't distribute)
            total_daily = facts_df['daily_pnl'].sum() if 'daily_pnl' in facts_df.columns else Decimal('0')
            logger.info(f"calculate_natural_rollup: Total in facts_df: {total_daily}, but NOT distributing to leaf nodes")
    
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
    Load all rules for a use case using RAW SQL.
    
    RAW SQL RULES LOAD: Loads rules strictly by Use Case ID, ignoring Structure ID.
    This ensures "orphaned" rules (rules that exist but might be linked to wrong Structure ID) are found.
    
    Args:
        session: SQLAlchemy session
        use_case_id: Use case ID
    
    Returns:
        Dictionary mapping node_id -> rule object
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # RAW SQL RULES LOAD (Ignoring Structure ID to find "Orphaned" Rules)
    # Phase 5.1: Include new columns (rule_type, measure_name, rule_expression, rule_dependencies)
    sql_rules = text("""
        SELECT 
            rule_id, 
            node_id, 
            predicate_json,
            sql_where, 
            logic_en,
            last_modified_by,
            created_at,
            last_modified_at,
            rule_type,
            measure_name,
            rule_expression,
            rule_dependencies
        FROM metadata_rules
        WHERE use_case_id = :uc_id
    """)
    
    try:
        rule_rows = session.execute(sql_rules, {"uc_id": str(use_case_id)}).fetchall()
        
        active_rules = {}
        for r in rule_rows:
            # Reconstruct MetadataRule object using constructor
            # Note: rule_id is auto-generated, but we set it from raw SQL for consistency
            rule = MetadataRule(
                use_case_id=use_case_id,
                node_id=r[1],
                predicate_json=r[2] if r[2] else None,
                sql_where=r[3] if r[3] else None,
                logic_en=r[4] if r[4] else None,
                last_modified_by=r[5] if r[5] else 'system'
            )
            # Set rule_id and timestamps from raw SQL (not in constructor)
            rule.rule_id = r[0]
            rule.created_at = r[6] if r[6] else None
            rule.last_modified_at = r[7] if r[7] else None
            # Phase 5.1: Set new columns
            rule.rule_type = r[8] if len(r) > 8 and r[8] else 'FILTER'
            rule.measure_name = r[9] if len(r) > 9 and r[9] else 'daily_pnl'
            rule.rule_expression = r[10] if len(r) > 10 and r[10] else None
            rule.rule_dependencies = r[11] if len(r) > 11 and r[11] else None
            
            active_rules[rule.node_id] = rule
        
        logger.debug(f"Rescued {len(active_rules)} Rules via Raw SQL (Ignoring Structure Link) for use_case_id={use_case_id}")
        return active_rules
        
    except Exception as e:
        logger.error(f"ERROR in load_rules (Raw SQL): {str(e)}", exc_info=True)
        # Fallback to ORM if raw SQL fails
        logger.warning("Falling back to ORM for rule loading")
        rules = session.query(MetadataRule).filter(
            MetadataRule.use_case_id == use_case_id
        ).all()
        return {rule.node_id: rule for rule in rules}


def get_measure_column_name(measure_name: Optional[str], table_name: str) -> str:
    """
    Phase 5.4: Map measure_name to actual database column name.
    
    Args:
        measure_name: Measure name from rule (e.g., 'daily_pnl', 'daily_commission', 'daily_trade')
        table_name: Table name to determine column mapping
    
    Returns:
        Actual column name in the database table
    """
    if not measure_name:
        return 'daily_pnl'  # Default
    
    # Map measure_name to column names based on table
    if table_name == 'fact_pnl_use_case_3':
        # Use Case 3 specific mapping
        mapping = {
            'daily_pnl': 'pnl_daily',
            'daily_commission': 'pnl_commission',
            'daily_trade': 'pnl_trade',
        }
        return mapping.get(measure_name, 'pnl_daily')  # Default to pnl_daily
    elif table_name == 'fact_pnl_entries':
        # fact_pnl_entries uses daily_amount, wtd_amount, ytd_amount
        mapping = {
            'daily_pnl': 'daily_amount',
            'daily_commission': 'daily_amount',  # Not available, fallback to daily_amount
            'daily_trade': 'daily_amount',  # Not available, fallback to daily_amount
        }
        return mapping.get(measure_name, 'daily_amount')
    else:
        # fact_pnl_gold uses daily_pnl, mtd_pnl, ytd_pnl
        return measure_name  # Use as-is for fact_pnl_gold


def apply_rule_override(session: Session, facts_df: pd.DataFrame, rule: MetadataRule, use_case: Optional[UseCase] = None) -> Dict[str, Decimal]:
    """
    Apply a rule override by executing SQL WHERE clause on facts.
    
    Phase 5.4: Updated to support multiple measures via rule.measure_name.
    Phase 5.5: Updated to support Type 2B (FILTER_ARITHMETIC) rules.
    
    Note: For Sterling Python rules, this function may not be called since rules
    are applied via Python logic. However, for SQL-based rules, we need to handle
    the fact that sql_where clauses may reference fact_pnl_entries.
    
    Args:
        session: SQLAlchemy session (for executing SQL)
        facts_df: DataFrame with fact data
        rule: MetadataRule object with sql_where clause and measure_name
        use_case: Optional UseCase object to determine input table
    
    Returns:
        Dictionary {daily: Decimal, mtd: Decimal, ytd: Decimal, pytd: Decimal}
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Phase 5.5: Check if this is a Type 2B rule
    rule_type = rule.rule_type or 'FILTER'
    if rule_type == 'FILTER_ARITHMETIC':
        # Execute Type 2B rule using DataFrame operations
        from app.engine.type2b_processor import execute_type_2b_rule
        
        # Determine table name
        table_name = 'fact_pnl_gold'  # Default
        if use_case and use_case.input_table_name:
            table_name = use_case.input_table_name
        elif 'pnl_commission' in facts_df.columns or 'pnl_trade' in facts_df.columns:
            table_name = 'fact_pnl_use_case_3'
        elif 'daily_amount' in facts_df.columns:
            table_name = 'fact_pnl_entries'
        
        logger.info(f"apply_rule_override: Executing Type 2B rule for node {rule.node_id}, table={table_name}")
        
        try:
            # Execute Type 2B rule
            result_value = execute_type_2b_rule(facts_df, rule, table_name)
            
            # Return in standard format (Type 2B only returns 'daily' for now)
            return {
                'daily': result_value,
                'mtd': Decimal('0'),  # Not available for Type 2B
                'ytd': Decimal('0'),  # Not available for Type 2B
                'pytd': Decimal('0'),
            }
        except Exception as e:
            logger.error(f"Error executing Type 2B rule for node {rule.node_id}: {e}", exc_info=True)
            return {
                'daily': Decimal('0'),
                'mtd': Decimal('0'),
                'ytd': Decimal('0'),
                'pytd': Decimal('0'),
            }
    
    # Phase 5.4: Determine target measure column (for Type 1/2 rules)
    measure_name = rule.measure_name or 'daily_pnl'  # Default to daily_pnl
    
    # Determine which table to use
    table_name = 'fact_pnl_gold'  # Default
    if use_case and use_case.input_table_name:
        table_name = use_case.input_table_name
    elif 'pnl_commission' in facts_df.columns or 'pnl_trade' in facts_df.columns:
        # Detect fact_pnl_use_case_3 by presence of pnl_commission or pnl_trade
        table_name = 'fact_pnl_use_case_3'
    elif 'daily_amount' in facts_df.columns:
        table_name = 'fact_pnl_entries'
    
    # Get actual column name for the measure
    target_column = get_measure_column_name(measure_name, table_name)
    
    logger.info(f"apply_rule_override: Node {rule.node_id}, measure_name={measure_name}, table={table_name}, target_column={target_column}")
    
    if not rule.sql_where:
        # No SQL WHERE clause - return zeros
        return {
            'daily': Decimal('0'),
            'mtd': Decimal('0'),
            'ytd': Decimal('0'),
            'pytd': Decimal('0'),
        }
    
    # Try to execute SQL WHERE clause on the appropriate table
    try:
        sql_where = rule.sql_where.strip()
        
        # Phase 5.4: Use target_column instead of hardcoded daily_pnl
        if table_name == 'fact_pnl_use_case_3':
            # Use Case 3: fact_pnl_use_case_3 table
            sql_query = f"""
                SELECT 
                    COALESCE(SUM({target_column}), 0) as measure_value
                FROM fact_pnl_use_case_3
                WHERE {sql_where}
            """
        elif table_name == 'fact_pnl_entries':
            # fact_pnl_entries table
            sql_query = f"""
                SELECT 
                    COALESCE(SUM({target_column}), 0) as daily_amount,
                    COALESCE(SUM(wtd_amount), 0) as wtd_amount,
                    COALESCE(SUM(ytd_amount), 0) as ytd_amount,
                    0 as pytd_amount
                FROM fact_pnl_entries
                WHERE {sql_where}
            """
        else:
            # Default to fact_pnl_gold for legacy rules
            sql_query = f"""
                SELECT 
                    COALESCE(SUM({target_column}), 0) as daily_pnl,
                    COALESCE(SUM(mtd_pnl), 0) as mtd_pnl,
                    COALESCE(SUM(ytd_pnl), 0) as ytd_pnl,
                    COALESCE(SUM(pytd_pnl), 0) as pytd_pnl
                FROM fact_pnl_gold
                WHERE {sql_where}
            """
        
        result = session.execute(text(sql_query)).fetchone()
        
        if result and result[0] is not None:
            # Phase 5.4: For Use Case 3, we only get one value (the target measure)
            if table_name == 'fact_pnl_use_case_3':
                measure_value = Decimal(str(result[0] or 0))
                # Return the measure value in 'daily' slot (for now, other measures are zero)
                return {
                    'daily': measure_value,
                    'mtd': Decimal('0'),  # Not available in fact_pnl_use_case_3
                    'ytd': Decimal('0'),  # Not available in fact_pnl_use_case_3
                    'pytd': Decimal('0'),
                }
            elif table_name == 'fact_pnl_entries':
                return {
                    'daily': Decimal(str(result[0] or 0)),
                    'mtd': Decimal(str(result[1] or 0)),  # wtd_amount maps to mtd
                    'ytd': Decimal(str(result[2] or 0)),
                    'pytd': Decimal(str(result[3] or 0)),
                }
            else:
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
        # CRITICAL: Rollback transaction on SQL error to prevent InFailedSqlTransaction
        try:
            session.rollback()
        except Exception as rollback_error:
            logger.warning(f"apply_rule_override: Failed to rollback after SQL error: {rollback_error}")
        
        # If SQL execution fails, return zeros (this is expected for Sterling Python rules)
        # Only log warning if sql_where exists and looks valid
        if rule.sql_where and rule.sql_where.strip() and rule.sql_where.strip() != '1=1':
            logger.warning(f"apply_rule_override: Rule execution failed for node {rule.node_id}: {e}")
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
    
    # Phase 5.4: Get use_case for table detection (needed early for fact loading)
    use_case = session.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
    
    # Step 1: Load hierarchy
    hierarchy_dict, children_dict, leaf_nodes = load_hierarchy(session, use_case_id)
    
    # Step 2: Load facts
    # Phase 5.5: For Use Case 3, load from fact_pnl_use_case_3 if needed
    if use_case and use_case.input_table_name == 'fact_pnl_use_case_3':
        facts_df = load_facts_from_use_case_3(session, use_case_id)
    else:
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
                override_values = apply_rule_override(session, facts_df, rule, use_case)
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

