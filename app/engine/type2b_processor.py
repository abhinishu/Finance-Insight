"""
Phase 5.5: Type 2B (FILTER_ARITHMETIC) Rule Processor

Handles execution of rules that combine multiple independent queries with arithmetic operators.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Any
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def apply_filter_to_dataframe(df: pd.DataFrame, filter_def: Dict[str, Any]) -> pd.DataFrame:
    """
    Apply a single filter condition to a DataFrame.
    
    Args:
        df: Input DataFrame
        filter_def: Filter definition with 'field', 'operator', 'value'/'values'
    
    Returns:
        Filtered DataFrame
    """
    field = filter_def.get('field')
    operator = filter_def.get('operator')
    
    if field not in df.columns:
        logger.warning(f"Filter field '{field}' not found in DataFrame columns: {list(df.columns)}")
        return pd.DataFrame()  # Return empty DataFrame if field doesn't exist
    
    if operator == '=':
        value = filter_def.get('value')
        return df[df[field] == value]
    
    elif operator == '!=':
        value = filter_def.get('value')
        return df[df[field] != value]
    
    elif operator == 'IN':
        values = filter_def.get('values', [])
        return df[df[field].isin(values)]
    
    elif operator == 'NOT IN':
        values = filter_def.get('values', [])
        return df[~df[field].isin(values)]
    
    elif operator == '>':
        value = filter_def.get('value')
        return df[df[field] > value]
    
    elif operator == '<':
        value = filter_def.get('value')
        return df[df[field] < value]
    
    elif operator == '>=':
        value = filter_def.get('value')
        return df[df[field] >= value]
    
    elif operator == '<=':
        value = filter_def.get('value')
        return df[df[field] <= value]
    
    elif operator == 'LIKE':
        value = filter_def.get('value')
        return df[df[field].str.contains(value, case=False, na=False)]
    
    elif operator == 'IS NULL':
        return df[df[field].isna()]
    
    elif operator == 'IS NOT NULL':
        return df[df[field].notna()]
    
    else:
        logger.warning(f"Unsupported filter operator: {operator}")
        return pd.DataFrame()


def execute_single_query(df: pd.DataFrame, query_def: Dict[str, Any], table_name: str) -> Decimal:
    """
    Execute a single query from Type 2B rule.
    
    Args:
        df: Input DataFrame with fact data
        query_def: Query definition with 'query_id', 'measure', 'aggregation', 'filters'
        table_name: Table name for measure column mapping
    
    Returns:
        Aggregated result as Decimal
    """
    from app.engine.waterfall import get_measure_column_name
    
    # Get measure and aggregation
    measure_name = query_def.get('measure', 'daily_pnl')
    aggregation = query_def.get('aggregation', 'SUM')
    filters = query_def.get('filters', [])
    
    # Map measure name to actual column name
    measure_column = get_measure_column_name(measure_name, table_name)
    
    if measure_column not in df.columns:
        logger.warning(f"Measure column '{measure_column}' not found in DataFrame. Available: {list(df.columns)}")
        return Decimal('0')
    
    # Apply all filters sequentially
    filtered_df = df.copy()
    for filter_def in filters:
        filtered_df = apply_filter_to_dataframe(filtered_df, filter_def)
        if filtered_df.empty:
            logger.debug(f"Query {query_def.get('query_id')} returned empty after filter: {filter_def}")
            return Decimal('0')
    
    # Apply aggregation
    if aggregation == 'SUM':
        result = filtered_df[measure_column].sum()
    elif aggregation == 'AVG':
        result = filtered_df[measure_column].mean()
    elif aggregation == 'COUNT':
        result = Decimal(len(filtered_df))
    elif aggregation == 'MAX':
        result = filtered_df[measure_column].max()
    elif aggregation == 'MIN':
        result = filtered_df[measure_column].min()
    else:
        logger.warning(f"Unsupported aggregation: {aggregation}, defaulting to SUM")
        result = filtered_df[measure_column].sum()
    
    # Ensure result is Decimal
    if pd.isna(result):
        return Decimal('0')
    
    return Decimal(str(result))


def evaluate_operand(operand: Dict[str, Any], query_results: Dict[str, Decimal]) -> Decimal:
    """
    Get value for an operand in an arithmetic expression.
    
    Args:
        operand: Operand definition with 'type' and optional 'query_id', 'value', or 'expression'
        query_results: Dictionary mapping query_id -> Decimal result
    
    Returns:
        Operand value as Decimal
    """
    operand_type = operand.get('type')
    
    if operand_type == 'query':
        query_id = operand.get('query_id')
        if query_id not in query_results:
            logger.warning(f"Query ID '{query_id}' not found in query results")
            return Decimal('0')
        return query_results[query_id]
    
    elif operand_type == 'constant':
        value = operand.get('value', 0)
        return Decimal(str(value))
    
    elif operand_type == 'expression':
        expression = operand.get('expression')
        if not expression:
            logger.warning("Operand type 'expression' but no 'expression' field found")
            return Decimal('0')
        return evaluate_expression(expression, query_results)
    
    else:
        logger.warning(f"Unknown operand type: {operand_type}")
        return Decimal('0')


def evaluate_expression(expression: Dict[str, Any], query_results: Dict[str, Decimal]) -> Decimal:
    """
    Evaluate an arithmetic expression using query results.
    
    Supports nested expressions and multiple operands.
    
    Args:
        expression: Expression definition with 'operator' and 'operands'
        query_results: Dictionary mapping query_id -> Decimal result
    
    Returns:
        Evaluated result as Decimal
    """
    operator = expression.get('operator')
    operands = expression.get('operands', [])
    
    if len(operands) < 2:
        logger.warning(f"Expression requires at least 2 operands, got {len(operands)}")
        return Decimal('0')
    
    # Get all operand values
    values = [evaluate_operand(op, query_results) for op in operands]
    
    if operator == '+':
        result = sum(values)
    
    elif operator == '-':
        result = values[0]
        for v in values[1:]:
            result -= v
    
    elif operator == '*':
        result = Decimal('1')
        for v in values:
            result *= v
    
    elif operator == '/':
        result = values[0]
        for v in values[1:]:
            if v == Decimal('0'):
                logger.error("Division by zero detected in Type 2B expression")
                raise ValueError("Division by zero")
            result /= v
    
    else:
        logger.warning(f"Unsupported operator: {operator}")
        return Decimal('0')
    
    return result


def execute_type_2b_rule(
    df: pd.DataFrame,
    rule: Any,
    table_name: str = 'fact_pnl_use_case_3'
) -> Decimal:
    """
    Execute a Type 2B (FILTER_ARITHMETIC) rule.
    
    Phase 5.5: Processes rules that combine multiple queries with arithmetic operators.
    
    Args:
        df: Input DataFrame with fact data
        rule: MetadataRule object with predicate_json containing queries and expression
        table_name: Table name for measure column mapping
    
    Returns:
        Final calculated result as Decimal
    """
    if not rule.predicate_json:
        logger.warning(f"Type 2B rule {rule.node_id} has no predicate_json")
        return Decimal('0')
    
    predicate = rule.predicate_json
    
    # Validate schema version
    version = predicate.get('version')
    if version != '2.0':
        logger.warning(f"Type 2B rule {rule.node_id} has unsupported version: {version}")
        return Decimal('0')
    
    # Extract queries and expression
    queries = predicate.get('queries', [])
    expression = predicate.get('expression')
    
    if not queries:
        logger.warning(f"Type 2B rule {rule.node_id} has no queries")
        return Decimal('0')
    
    if not expression:
        logger.warning(f"Type 2B rule {rule.node_id} has no expression")
        return Decimal('0')
    
    # Step 1: Execute each query independently
    query_results = {}
    for query_def in queries:
        query_id = query_def.get('query_id')
        if not query_id:
            logger.warning(f"Query missing query_id: {query_def}")
            continue
        
        try:
            result = execute_single_query(df, query_def, table_name)
            query_results[query_id] = result
            logger.debug(f"Type 2B query {query_id}: {result}")
        except Exception as e:
            logger.error(f"Error executing query {query_id}: {e}", exc_info=True)
            query_results[query_id] = Decimal('0')
    
    # Step 2: Evaluate the arithmetic expression
    try:
        final_result = evaluate_expression(expression, query_results)
        logger.info(f"Type 2B rule {rule.node_id} final result: {final_result}")
        return final_result
    except Exception as e:
        logger.error(f"Error evaluating expression for rule {rule.node_id}: {e}", exc_info=True)
        return Decimal('0')


