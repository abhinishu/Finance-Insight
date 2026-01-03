"""
Rule Service - Business logic for rule creation and validation.
Handles both Manual (dropdown) and GenAI (natural language) rule creation.
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.api.schemas import RuleCondition, RuleCreate, RulePreviewResponse
from app.models import FactPnlGold, MetadataRule, UseCase

logger = logging.getLogger(__name__)

# Fact table schema - allowed fields for rule conditions
# Schema for fact_pnl_gold (Use Cases 1 & 2)
FACT_PNL_GOLD_FIELDS = {
    'account_id': 'String',
    'cc_id': 'String',
    'book_id': 'String',
    'strategy_id': 'String',
    'trade_date': 'Date',
    'daily_pnl': 'Numeric',
    'mtd_pnl': 'Numeric',
    'ytd_pnl': 'Numeric',
    'pytd_pnl': 'Numeric',
}

# Schema for fact_pnl_use_case_3 (Use Case 3)
FACT_PNL_UC3_FIELDS = {
    'strategy': 'String',  # Mapped from 'strategy_id'
    'book': 'String',  # Mapped from 'book_id'
    'cost_center': 'String',  # Mapped from 'cc_id'
    'effective_date': 'Date',  # Mapped from 'trade_date'
    'division': 'String',
    'business_area': 'String',
    'product_line': 'String',
    'process_1': 'String',
    'process_2': 'String',
    'pnl_daily': 'Numeric',
    'pnl_commission': 'Numeric',
    'pnl_trade': 'Numeric',
}

# Schema for fact_pnl_entries (Use Case 2 - Project Sterling)
FACT_PNL_ENTRIES_FIELDS = {
    'account_id': 'String',
    'cc_id': 'String',
    'book_id': 'String',
    'strategy_id': 'String',
    'pnl_date': 'Date',  # Mapped from 'trade_date'
    'daily_amount': 'Numeric',
    'wtd_amount': 'Numeric',
    'ytd_amount': 'Numeric',
}

# Legacy: Keep for backward compatibility
FACT_TABLE_FIELDS = FACT_PNL_GOLD_FIELDS

# Supported operators for manual rules
SUPPORTED_OPERATORS = {
    'equals': '=',
    'not_equals': '!=',
    'in': 'IN',
    'not_in': 'NOT IN',
    'greater_than': '>',
    'less_than': '<',
}


def get_column_mapping(table_name: str) -> Dict[str, str]:
    """
    Get column mapping from frontend field names to actual database column names.
    
    This function maps the standard field names (used in the UI) to the actual
    column names in each table. For fact_pnl_gold, the mapping is identity (no change).
    For fact_pnl_use_case_3, fields are mapped to match the table schema.
    
    Args:
        table_name: Target table name (e.g., 'fact_pnl_gold', 'fact_pnl_use_case_3')
    
    Returns:
        Dictionary mapping frontend field names to database column names.
        Empty dict means identity mapping (field name = column name).
    """
    if table_name == 'fact_pnl_use_case_3':
        return {
            'strategy_id': 'strategy',
            'book_id': 'book',
            'cc_id': 'cost_center',
            'trade_date': 'effective_date',
        }
    elif table_name == 'fact_pnl_entries':
        return {
            'trade_date': 'pnl_date',
        }
    else:
        # fact_pnl_gold: identity mapping (no change)
        return {}


def get_table_fields(table_name: str) -> Dict[str, str]:
    """
    Get allowed fields for a specific table.
    
    Args:
        table_name: Target table name
    
    Returns:
        Dictionary of allowed field names and their types
    """
    if table_name == 'fact_pnl_use_case_3':
        return FACT_PNL_UC3_FIELDS
    elif table_name == 'fact_pnl_entries':
        return FACT_PNL_ENTRIES_FIELDS
    else:
        # Default: fact_pnl_gold
        return FACT_PNL_GOLD_FIELDS


def validate_field_exists(field: str, table_name: str = 'fact_pnl_gold') -> bool:
    """
    Validate that a field exists in the specified table schema.
    
    This function checks if a field (frontend name) is valid for the given table.
    It considers both the direct field name and any mapped column names.
    
    Args:
        field: Field name to validate (frontend field name, e.g., 'strategy_id')
        table_name: Target table name (default: 'fact_pnl_gold')
    
    Returns:
        True if field exists (either directly or via mapping), False otherwise
    """
    # Get the mapping for this table
    mapping = get_column_mapping(table_name)
    
    # Check if field maps to a valid column
    mapped_column = mapping.get(field, field)
    
    # Get allowed fields for this table
    allowed_fields = get_table_fields(table_name)
    
    # Check if the mapped column exists in the table schema
    return mapped_column in allowed_fields


def validate_conditions(conditions: List[RuleCondition], table_name: str = 'fact_pnl_gold') -> List[str]:
    """
    Validate a list of conditions against the fact table schema.
    
    Args:
        conditions: List of RuleCondition objects
        table_name: Target table name (default: 'fact_pnl_gold')
    
    Returns:
        List of error messages (empty if validation passes)
    """
    errors = []
    
    # Get allowed fields for this table
    allowed_fields = get_table_fields(table_name)
    
    for idx, condition in enumerate(conditions):
        # Validate field exists
        if not validate_field_exists(condition.field, table_name):
            errors.append(
                f"Condition {idx + 1}: Field '{condition.field}' does not exist in {table_name}. "
                f"Allowed fields: {list(allowed_fields.keys())}"
            )
        
        # Validate operator is supported
        if condition.operator not in SUPPORTED_OPERATORS:
            errors.append(
                f"Condition {idx + 1}: Operator '{condition.operator}' is not supported. "
                f"Supported operators: {list(SUPPORTED_OPERATORS.keys())}"
            )
        
        # Validate value type matches operator
        if condition.operator in ['in', 'not_in']:
            if not isinstance(condition.value, list):
                errors.append(
                    f"Condition {idx + 1}: Operator '{condition.operator}' requires a list value"
                )
        elif condition.operator in ['greater_than', 'less_than']:
            # For numeric comparisons, value should be numeric
            # CRITICAL: Prefer Decimal for financial values, but accept float/int for validation
            if not isinstance(condition.value, (int, float, Decimal)):
                try:
                    # Try to convert to Decimal first (maintains precision)
                    Decimal(str(condition.value))
                except (ValueError, TypeError):
                    errors.append(
                        f"Condition {idx + 1}: Operator '{condition.operator}' requires a numeric value"
                    )
    
    return errors


def convert_conditions_to_json(conditions: List[RuleCondition]) -> Dict[str, Any]:
    """
    Convert list of RuleCondition objects to JSON predicate format.
    
    Args:
        conditions: List of RuleCondition objects
    
    Returns:
        JSON predicate dictionary
    """
    return {
        'conditions': [
            {
                'field': cond.field,
                'operator': cond.operator,
                'value': cond.value
            }
            for cond in conditions
        ],
        'conjunction': 'AND'  # Default to AND for manual rules
    }


def convert_json_to_sql(predicate_json: Dict[str, Any], table_name: str = 'fact_pnl_gold') -> str:
    """
    Convert JSON predicate to safe, parameterized SQL WHERE clause.
    
    This function maps frontend field names to actual database column names
    based on the target table. For example, 'strategy_id' maps to 'strategy'
    for fact_pnl_use_case_3.
    
    Args:
        predicate_json: JSON predicate dictionary
        table_name: Target table name (default: 'fact_pnl_gold')
    
    Returns:
        SQL WHERE clause string with mapped column names
    """
    conditions = predicate_json.get('conditions', [])
    conjunction = predicate_json.get('conjunction', 'AND')
    
    if not conditions:
        raise ValueError("No conditions provided in predicate_json")
    
    # Get column mapping for this table
    mapping = get_column_mapping(table_name)
    
    sql_parts = []
    
    for cond in conditions:
        field = cond['field']
        operator = cond['operator']
        value = cond['value']
        
        # Map field name to actual database column name
        db_column = mapping.get(field, field)
        
        # Validate field exists
        if not validate_field_exists(field, table_name):
            raise ValueError(f"Field '{field}' does not exist in {table_name}")
        
        # Convert operator to SQL
        sql_operator = SUPPORTED_OPERATORS.get(operator)
        if not sql_operator:
            raise ValueError(f"Unsupported operator: {operator}")
        
        # Build SQL condition using mapped column name
        if operator in ['in', 'not_in']:
            # Handle list values
            if not isinstance(value, list):
                raise ValueError(f"Operator '{operator}' requires a list value")
            # Escape and quote string values
            quoted_values = [f'\'{str(v).replace("'", "''")}\'' for v in value]
            sql_parts.append(f"{db_column} {sql_operator} ({', '.join(quoted_values)})")
        elif operator in ['equals', 'not_equals']:
            # String comparison - quote the value
            if isinstance(value, str):
                escaped_value = value.replace("'", "''")
                sql_parts.append(f"{db_column} {sql_operator} '{escaped_value}'")
            else:
                sql_parts.append(f"{db_column} {sql_operator} {value}")
        else:
            # Numeric comparison
            sql_parts.append(f"{db_column} {sql_operator} {value}")
    
    # Join with conjunction
    sql_where = f" {conjunction} ".join(sql_parts)
    
    return sql_where


def generate_logic_en_from_conditions(conditions: List[RuleCondition]) -> str:
    """
    Generate natural language description from conditions.
    Used for auditability when creating manual rules.
    
    Args:
        conditions: List of RuleCondition objects
    
    Returns:
        Natural language description
    """
    if not conditions:
        return "No conditions specified"
    
    descriptions = []
    for cond in conditions:
        field = cond.field
        operator = cond.operator
        value = cond.value
        
        if operator == 'equals':
            descriptions.append(f"{field} equals '{value}'")
        elif operator == 'not_equals':
            descriptions.append(f"{field} not equals '{value}'")
        elif operator == 'in':
            value_str = ', '.join(str(v) for v in value)
            descriptions.append(f"{field} in ({value_str})")
        elif operator == 'not_in':
            value_str = ', '.join(str(v) for v in value)
            descriptions.append(f"{field} not in ({value_str})")
        elif operator == 'greater_than':
            descriptions.append(f"{field} greater than {value}")
        elif operator == 'less_than':
            descriptions.append(f"{field} less than {value}")
    
    return " AND ".join(descriptions)


def create_manual_rule(
    use_case_id: UUID,
    rule_data: RuleCreate,
    session: Session
) -> MetadataRule:
    """
    Create a manual rule from a list of conditions.
    
    Process:
    1. Validate conditions against fact table schema
    2. Convert conditions to JSON predicate
    3. Generate SQL WHERE clause
    4. Generate natural language description
    5. Save to database (overwrite if rule exists for node)
    
    Args:
        use_case_id: Use case UUID
        rule_data: RuleCreate object with conditions
        session: Database session
    
    Returns:
        Created/updated MetadataRule object
    
    Raises:
        ValueError: If validation fails
    """
    # Validate use case exists
    use_case = session.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
    if not use_case:
        raise ValueError(f"Use case '{use_case_id}' not found")
    
    # Determine table name from use case
    table_name = 'fact_pnl_gold'  # Default
    if use_case and use_case.input_table_name:
        table_name = use_case.input_table_name
        logger.info(f"[create_manual_rule] Using table '{table_name}' for use case {use_case_id}")
    
    # Validate conditions
    if not rule_data.conditions:
        raise ValueError("No conditions provided for manual rule")
    
    validation_errors = validate_conditions(rule_data.conditions, table_name)
    if validation_errors:
        raise ValueError(f"Validation failed: {'; '.join(validation_errors)}")
    
    # Convert to JSON predicate
    predicate_json = convert_conditions_to_json(rule_data.conditions)
    
    # Generate SQL WHERE clause with table-specific column mapping
    sql_where = convert_json_to_sql(predicate_json, table_name)
    
    # Generate natural language description
    logic_en = generate_logic_en_from_conditions(rule_data.conditions)
    
    # Check if rule already exists for this node
    existing_rule = session.query(MetadataRule).filter(
        MetadataRule.use_case_id == use_case_id,
        MetadataRule.node_id == rule_data.node_id
    ).first()
    
    # Phase 5.1: Validate rule type requirements
    rule_type = rule_data.rule_type or 'FILTER'
    measure_name = rule_data.measure_name or 'daily_pnl'
    
    # Validation: Type 3 (NODE_ARITHMETIC) requires rule_expression
    if rule_type == 'NODE_ARITHMETIC':
        if not rule_data.rule_expression:
            raise ValueError("rule_expression is required for NODE_ARITHMETIC rule type")
    
    # Validation: FILTER and FILTER_ARITHMETIC require predicate_json
    if rule_type in ('FILTER', 'FILTER_ARITHMETIC'):
        if not predicate_json:
            raise ValueError(f"predicate_json is required for {rule_type} rule type")
    
    if existing_rule:
        # Update existing rule
        logger.info(f"Updating existing rule {existing_rule.rule_id} for node {rule_data.node_id}")
        existing_rule.predicate_json = predicate_json
        existing_rule.sql_where = sql_where
        existing_rule.logic_en = logic_en
        existing_rule.last_modified_by = rule_data.last_modified_by
        # Phase 5.1: Update new fields
        existing_rule.rule_type = rule_type
        existing_rule.measure_name = measure_name
        existing_rule.rule_expression = rule_data.rule_expression
        existing_rule.rule_dependencies = rule_data.rule_dependencies if rule_data.rule_dependencies else None
        session.commit()
        session.refresh(existing_rule)
        return existing_rule
    else:
        # Create new rule
        logger.info(f"Creating new rule for node {rule_data.node_id}")
        new_rule = MetadataRule(
            use_case_id=use_case_id,
            node_id=rule_data.node_id,
            predicate_json=predicate_json,
            sql_where=sql_where,
            logic_en=logic_en,
            last_modified_by=rule_data.last_modified_by,
            # Phase 5.1: New fields
            rule_type=rule_type,
            measure_name=measure_name,
            rule_expression=rule_data.rule_expression,
            rule_dependencies=rule_data.rule_dependencies if rule_data.rule_dependencies else None
        )
        session.add(new_rule)
        session.commit()
        session.refresh(new_rule)
        return new_rule


def preview_rule_impact(sql_where: str, session: Session, use_case_id: Optional[UUID] = None) -> RulePreviewResponse:
    """
    Preview the impact of a rule by counting affected rows.
    
    Args:
        sql_where: SQL WHERE clause to preview
        session: Database session
        use_case_id: Optional use case ID to determine which fact table to query.
                     If provided, checks use_case.input_table_name to select the correct table.
                     If None or use_case.input_table_name is None, defaults to fact_pnl_gold.
    
    Returns:
        RulePreviewResponse with affected row count
    """
    # Whitelist of allowed fact table names (security: prevent SQL injection)
    ALLOWED_TABLES = {'fact_pnl_gold', 'fact_pnl_entries', 'fact_pnl_use_case_3'}
    
    # Determine which table to query based on use_case_id
    table_name = 'fact_pnl_gold'  # Default table
    
    if use_case_id:
        use_case = session.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
        if use_case and use_case.input_table_name:
            candidate_table = use_case.input_table_name.strip()
            # Security: Validate table name against whitelist
            if candidate_table in ALLOWED_TABLES:
                table_name = candidate_table
                logger.info(f"[Rule Preview] Using table '{table_name}' for use case {use_case_id} (from input_table_name)")
            else:
                logger.warning(f"[Rule Preview] Invalid table name '{candidate_table}' for use case {use_case_id}, defaulting to fact_pnl_gold")
        else:
            logger.info(f"[Rule Preview] Use case {use_case_id} has no input_table_name, defaulting to fact_pnl_gold")
    else:
        logger.info(f"[Rule Preview] No use_case_id provided, defaulting to fact_pnl_gold")
    
    # Get total row count from the determined table
    from sqlalchemy import text
    try:
        count_query = text(f"SELECT COUNT(*) FROM {table_name}")
        total_rows = session.execute(count_query).scalar() or 0
    except Exception as e:
        logger.error(f"Error counting total rows in {table_name}: {e}")
        raise ValueError(f"Failed to count rows in table '{table_name}': {str(e)}")
    
    # Count affected rows (safely execute SQL)
    try:
        # Use parameterized query for safety
        query = text(f"SELECT COUNT(*) FROM {table_name} WHERE {sql_where}")
        result = session.execute(query).scalar()
        affected_rows = result or 0
    except Exception as e:
        logger.error(f"Error previewing rule on table {table_name}: {e}")
        raise ValueError(f"Invalid SQL WHERE clause for table '{table_name}': {str(e)}")
    
    percentage = (affected_rows / total_rows * 100) if total_rows > 0 else 0.0
    
    return RulePreviewResponse(
        affected_rows=affected_rows,
        total_rows=total_rows,
        percentage=round(percentage, 2)
    )

