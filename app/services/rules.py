"""
Rule Service - Business logic for rule creation and validation.
Handles both Manual (dropdown) and GenAI (natural language) rule creation.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.api.schemas import RuleCondition, RuleCreate, RulePreviewResponse
from app.models import FactPnlGold, MetadataRule, UseCase

logger = logging.getLogger(__name__)

# Fact table schema - allowed fields for rule conditions
FACT_TABLE_FIELDS = {
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

# Supported operators for manual rules
SUPPORTED_OPERATORS = {
    'equals': '=',
    'not_equals': '!=',
    'in': 'IN',
    'not_in': 'NOT IN',
    'greater_than': '>',
    'less_than': '<',
}


def validate_field_exists(field: str) -> bool:
    """
    Validate that a field exists in the fact_pnl_gold schema.
    
    Args:
        field: Field name to validate
    
    Returns:
        True if field exists, False otherwise
    """
    return field in FACT_TABLE_FIELDS


def validate_conditions(conditions: List[RuleCondition]) -> List[str]:
    """
    Validate a list of conditions against the fact table schema.
    
    Args:
        conditions: List of RuleCondition objects
    
    Returns:
        List of error messages (empty if validation passes)
    """
    errors = []
    
    for idx, condition in enumerate(conditions):
        # Validate field exists
        if not validate_field_exists(condition.field):
            errors.append(
                f"Condition {idx + 1}: Field '{condition.field}' does not exist in fact_pnl_gold. "
                f"Allowed fields: {list(FACT_TABLE_FIELDS.keys())}"
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
            if not isinstance(condition.value, (int, float)):
                try:
                    float(condition.value)
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


def convert_json_to_sql(predicate_json: Dict[str, Any]) -> str:
    """
    Convert JSON predicate to safe, parameterized SQL WHERE clause.
    
    Args:
        predicate_json: JSON predicate dictionary
    
    Returns:
        SQL WHERE clause string
    """
    conditions = predicate_json.get('conditions', [])
    conjunction = predicate_json.get('conjunction', 'AND')
    
    if not conditions:
        raise ValueError("No conditions provided in predicate_json")
    
    sql_parts = []
    
    for cond in conditions:
        field = cond['field']
        operator = cond['operator']
        value = cond['value']
        
        # Validate field exists
        if not validate_field_exists(field):
            raise ValueError(f"Field '{field}' does not exist in fact_pnl_gold")
        
        # Convert operator to SQL
        sql_operator = SUPPORTED_OPERATORS.get(operator)
        if not sql_operator:
            raise ValueError(f"Unsupported operator: {operator}")
        
        # Build SQL condition
        if operator in ['in', 'not_in']:
            # Handle list values
            if not isinstance(value, list):
                raise ValueError(f"Operator '{operator}' requires a list value")
            # Escape and quote string values
            quoted_values = [f"'{str(v).replace("'", "''")}'" for v in value]
            sql_parts.append(f"{field} {sql_operator} ({', '.join(quoted_values)})")
        elif operator in ['equals', 'not_equals']:
            # String comparison - quote the value
            if isinstance(value, str):
                escaped_value = value.replace("'", "''")
                sql_parts.append(f"{field} {sql_operator} '{escaped_value}'")
            else:
                sql_parts.append(f"{field} {sql_operator} {value}")
        else:
            # Numeric comparison
            sql_parts.append(f"{field} {sql_operator} {value}")
    
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
    
    # Validate conditions
    if not rule_data.conditions:
        raise ValueError("No conditions provided for manual rule")
    
    validation_errors = validate_conditions(rule_data.conditions)
    if validation_errors:
        raise ValueError(f"Validation failed: {'; '.join(validation_errors)}")
    
    # Convert to JSON predicate
    predicate_json = convert_conditions_to_json(rule_data.conditions)
    
    # Generate SQL WHERE clause
    sql_where = convert_json_to_sql(predicate_json)
    
    # Generate natural language description
    logic_en = generate_logic_en_from_conditions(rule_data.conditions)
    
    # Check if rule already exists for this node
    existing_rule = session.query(MetadataRule).filter(
        MetadataRule.use_case_id == use_case_id,
        MetadataRule.node_id == rule_data.node_id
    ).first()
    
    if existing_rule:
        # Update existing rule
        logger.info(f"Updating existing rule {existing_rule.rule_id} for node {rule_data.node_id}")
        existing_rule.predicate_json = predicate_json
        existing_rule.sql_where = sql_where
        existing_rule.logic_en = logic_en
        existing_rule.last_modified_by = rule_data.last_modified_by
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
            last_modified_by=rule_data.last_modified_by
        )
        session.add(new_rule)
        session.commit()
        session.refresh(new_rule)
        return new_rule


def preview_rule_impact(sql_where: str, session: Session) -> RulePreviewResponse:
    """
    Preview the impact of a rule by counting affected rows.
    
    Args:
        sql_where: SQL WHERE clause to preview
        session: Database session
    
    Returns:
        RulePreviewResponse with affected row count
    """
    # Get total row count
    total_rows = session.query(FactPnlGold).count()
    
    # Count affected rows (safely execute SQL)
    try:
        # Use parameterized query for safety
        from sqlalchemy import text
        query = text(f"SELECT COUNT(*) FROM fact_pnl_gold WHERE {sql_where}")
        result = session.execute(query).scalar()
        affected_rows = result or 0
    except Exception as e:
        logger.error(f"Error previewing rule: {e}")
        raise ValueError(f"Invalid SQL WHERE clause: {str(e)}")
    
    percentage = (affected_rows / total_rows * 100) if total_rows > 0 else 0.0
    
    return RulePreviewResponse(
        affected_rows=affected_rows,
        total_rows=total_rows,
        percentage=round(percentage, 2)
    )

