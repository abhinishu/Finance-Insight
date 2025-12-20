"""
Pydantic schemas for Finance-Insight API
"""

from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class HierarchyNode(BaseModel):
    """Hierarchy node with natural values for discovery view."""
    node_id: str
    node_name: str
    parent_node_id: Optional[str]
    depth: int
    is_leaf: bool
    daily_pnl: str
    mtd_pnl: str
    ytd_pnl: str
    pytd_pnl: Optional[str] = None
    # Multi-dimensional attributes
    region: Optional[str] = None
    product: Optional[str] = None
    desk: Optional[str] = None
    strategy: Optional[str] = None
    # Official GL Baseline (same as daily_pnl for natural values)
    official_gl_baseline: Optional[str] = None
    # Path array for AG-Grid tree data (e.g., ["Global Trading P&L", "Americas", "Cash Equities"])
    path: Optional[List[str]] = None
    children: List['HierarchyNode'] = []

    class Config:
        json_schema_extra = {
            "example": {
                "node_id": "ROOT",
                "node_name": "Root",
                "parent_node_id": None,
                "depth": 0,
                "is_leaf": False,
                "daily_pnl": "1234567.89",
                "mtd_pnl": "12345678.90",
                "ytd_pnl": "123456789.01",
                "pytd_pnl": "1234567890.12",
                "children": []
            }
        }


# Allow forward references
HierarchyNode.model_rebuild()


class ReconciliationData(BaseModel):
    """Reconciliation totals for baseline validation."""
    fact_table_sum: dict
    leaf_nodes_sum: dict


class DiscoveryResponse(BaseModel):
    """Response for discovery endpoint."""
    structure_id: str
    hierarchy: List[HierarchyNode]
    reconciliation: Optional[ReconciliationData] = None

    class Config:
        json_schema_extra = {
            "example": {
                "structure_id": "MOCK_ATLAS_v1",
                "hierarchy": [
                    {
                        "node_id": "ROOT",
                        "node_name": "Root",
                        "parent_node_id": None,
                        "depth": 0,
                        "is_leaf": False,
                        "daily_pnl": "1234567.89",
                        "mtd_pnl": "12345678.90",
                        "ytd_pnl": "123456789.01",
                        "children": []
                    }
                ],
                "reconciliation": {
                    "fact_table_sum": {"daily": "1234567.89", "mtd": "12345678.90", "ytd": "123456789.01"},
                    "leaf_nodes_sum": {"daily": "1234567.89", "mtd": "12345678.90", "ytd": "123456789.01"}
                }
            }
        }


# ============================================================================
# Phase 2: Rule Engine Schemas
# ============================================================================

class RuleCondition(BaseModel):
    """
    A single condition in a rule (e.g., strategy_id equals 'EQUITY').
    Used for manual rule creation via dropdowns.
    """
    field: str = Field(..., description="Field name from fact_pnl_gold (e.g., 'strategy_id', 'book_id')")
    operator: str = Field(..., description="Operator: 'equals', 'not_equals', 'in', 'not_in', 'greater_than', 'less_than'")
    value: Any = Field(..., description="Value to compare against (string, number, or list for 'in'/'not_in')")

    @field_validator('operator')
    @classmethod
    def validate_operator(cls, v: str) -> str:
        """Validate operator is supported."""
        allowed = ['equals', 'not_equals', 'in', 'not_in', 'greater_than', 'less_than']
        if v not in allowed:
            raise ValueError(f"Operator must be one of: {allowed}")
        return v

    @field_validator('value')
    @classmethod
    def validate_value(cls, v: Any, info) -> Any:
        """Validate value matches operator requirements."""
        operator = info.data.get('operator')
        if operator in ['in', 'not_in']:
            if not isinstance(v, list):
                raise ValueError(f"Operator '{operator}' requires a list value")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "field": "strategy_id",
                "operator": "equals",
                "value": "EQUITY"
            }
        }


class RuleCreate(BaseModel):
    """
    Request schema for creating a rule.
    Supports two modes:
    1. Manual: Provide list of RuleCondition objects
    2. GenAI: Provide logic_en (natural language) - will be implemented later
    """
    node_id: str = Field(..., description="Node ID from dim_hierarchy where rule applies")
    last_modified_by: str = Field(..., min_length=1, description="User ID who created/modified the rule")
    
    # Manual mode: list of conditions
    conditions: Optional[List[RuleCondition]] = Field(None, description="List of conditions for manual rule creation")
    
    # GenAI mode: natural language (will be implemented in next sprint)
    logic_en: Optional[str] = Field(None, description="Natural language description (e.g., 'Exclude all EMEA trades')")
    
    # Direct SQL mode (advanced, for testing)
    sql_where: Optional[str] = Field(None, description="Direct SQL WHERE clause (bypasses validation - use with caution)")

    def model_post_init(self, __context):
        """Validate that exactly one mode is provided."""
        conditions = self.conditions
        logic_en = self.logic_en
        sql_where = self.sql_where
        
        provided = sum([bool(conditions), bool(logic_en), bool(sql_where)])
        if provided == 0:
            raise ValueError("Must provide either 'conditions' (manual), 'logic_en' (GenAI), or 'sql_where' (direct)")
        if provided > 1:
            raise ValueError("Cannot provide multiple modes. Choose one: 'conditions', 'logic_en', or 'sql_where'")

    class Config:
        json_schema_extra = {
            "example": {
                "node_id": "AMER_CASH_NY",
                "last_modified_by": "user123",
                "conditions": [
                    {
                        "field": "strategy_id",
                        "operator": "equals",
                        "value": "EQUITY"
                    },
                    {
                        "field": "book_id",
                        "operator": "not_in",
                        "value": ["B01", "B02"]
                    }
                ]
            }
        }


class RuleResponse(BaseModel):
    """
    Response schema for a rule.
    Includes all three stages for auditability:
    1. logic_en: Original natural language (or generated from conditions)
    2. predicate_json: Intermediate JSON predicate
    3. sql_where: Final SQL WHERE clause
    
    Note: All fields are Optional to support Phase 1 reports that don't have rules yet.
    """
    rule_id: int
    use_case_id: UUID
    node_id: str
    node_name: Optional[str] = None  # Populated from dim_hierarchy
    logic_en: Optional[str] = Field(None, description="Natural language description")
    predicate_json: Optional[Dict[str, Any]] = Field(None, description="Intermediate JSON predicate")
    sql_where: Optional[str] = Field(None, description="Final SQL WHERE clause")
    last_modified_by: str
    created_at: str
    last_modified_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "rule_id": 1,
                "use_case_id": "123e4567-e89b-12d3-a456-426614174000",
                "node_id": "AMER_CASH_NY",
                "node_name": "Americas Cash NY",
                "logic_en": "Exclude books B01 and B02",
                "predicate_json": {
                    "conditions": [
                        {"field": "book_id", "operator": "not_in", "value": ["B01", "B02"]}
                    ],
                    "conjunction": "AND"
                },
                "sql_where": "book_id NOT IN ('B01', 'B02')",
                "last_modified_by": "user123",
                "created_at": "2024-01-01T00:00:00",
                "last_modified_at": "2024-01-01T00:00:00"
            }
        }


class RulePreviewRequest(BaseModel):
    """Request schema for previewing rule impact."""
    sql_where: str = Field(..., description="SQL WHERE clause to preview")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sql_where": "book_id NOT IN ('B01', 'B02')"
            }
        }


class RulePreviewResponse(BaseModel):
    """Response schema for rule preview."""
    affected_rows: int = Field(..., description="Number of rows in fact_pnl_gold that match the rule")
    total_rows: int = Field(..., description="Total rows in fact_pnl_gold")
    percentage: float = Field(..., description="Percentage of rows affected")
    
    class Config:
        json_schema_extra = {
            "example": {
                "affected_rows": 150,
                "total_rows": 1000,
                "percentage": 15.0
            }
        }


# ============================================================================
# Phase 2: GenAI Translation Schemas
# ============================================================================

class RuleGenAIRequest(BaseModel):
    """Request schema for GenAI rule translation."""
    node_id: str = Field(..., description="Node ID from dim_hierarchy where rule applies")
    logic_en: str = Field(..., min_length=1, description="Natural language description (e.g., 'Exclude books B01 and B02')")
    last_modified_by: str = Field(..., min_length=1, description="User ID who created/modified the rule")
    
    class Config:
        json_schema_extra = {
            "example": {
                "node_id": "AMER_CASH_NY",
                "logic_en": "Exclude books B01 and B02",
                "last_modified_by": "user123"
            }
        }


class RuleGenAIResponse(BaseModel):
    """Response schema for GenAI translation preview."""
    node_id: str
    logic_en: str
    predicate_json: Optional[Dict[str, Any]] = Field(None, description="Generated JSON predicate (intermediate stage)")
    sql_where: Optional[str] = Field(None, description="Generated SQL WHERE clause (final stage)")
    translation_successful: bool = Field(..., description="Whether translation was successful")
    errors: List[str] = Field(default_factory=list, description="List of error messages if translation failed")
    preview_available: bool = Field(False, description="Whether preview is available (requires successful translation)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "node_id": "AMER_CASH_NY",
                "logic_en": "Exclude books B01 and B02",
                "predicate_json": {
                    "conditions": [
                        {"field": "book_id", "operator": "not_in", "value": ["B01", "B02"]}
                    ],
                    "conjunction": "AND"
                },
                "sql_where": "book_id NOT IN ('B01', 'B02')",
                "translation_successful": True,
                "errors": [],
                "preview_available": True
            }
        }


# ============================================================================
# Phase 2: Calculation Engine Schemas
# ============================================================================

class CalculationResponse(BaseModel):
    """Response schema for calculation endpoint."""
    run_id: str = Field(..., description="Run ID for this calculation")
    use_case_id: str = Field(..., description="Use case ID")
    rules_applied: int = Field(..., description="Number of rules applied")
    total_plug: Dict[str, str] = Field(..., description="Total reconciliation plug across all measures")
    duration_ms: int = Field(..., description="Calculation duration in milliseconds")
    message: str = Field(..., description="Summary message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "run_id": "123e4567-e89b-12d3-a456-426614174000",
                "use_case_id": "123e4567-e89b-12d3-a456-426614174001",
                "rules_applied": 5,
                "total_plug": {
                    "daily": "1234.56",
                    "mtd": "5678.90",
                    "ytd": "12345.67",
                    "pytd": "23456.78"
                },
                "duration_ms": 1250,
                "message": "Calculation complete. 5 rules applied. Total Plug: $1234.56"
            }
        }


class ResultsNode(BaseModel):
    """Hierarchy node with calculation results (natural, adjusted, plug)."""
    node_id: str
    node_name: str
    parent_node_id: Optional[str]
    depth: int
    is_leaf: bool
    # Natural GL values (baseline)
    natural_value: Dict[str, str] = Field(..., description="Natural GL values: {daily, mtd, ytd, pytd}")
    # Rule-adjusted values (after applying rules)
    adjusted_value: Dict[str, str] = Field(..., description="Rule-adjusted values: {daily, mtd, ytd, pytd}")
    # Reconciliation plug
    plug: Dict[str, str] = Field(..., description="Reconciliation plug: {daily, mtd, ytd, pytd}")
    # Metadata
    is_override: bool = Field(..., description="True if a rule was applied to this node")
    is_reconciled: bool = Field(..., description="True if plug is zero (within tolerance)")
    # Rule information (for audit trail)
    rule: Optional[Dict[str, Any]] = Field(None, description="Rule details if override exists: {rule_id, logic_en, sql_where}")
    # Path array for tree structure
    path: Optional[List[str]] = None
    children: List['ResultsNode'] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "node_id": "AMER_CASH_NY",
                "node_name": "Americas Cash NY",
                "parent_node_id": "AMER_CASH",
                "depth": 3,
                "is_leaf": True,
                "natural_value": {
                    "daily": "123456.78",
                    "mtd": "1234567.89",
                    "ytd": "12345678.90",
                    "pytd": "123456789.01"
                },
                "adjusted_value": {
                    "daily": "120000.00",
                    "mtd": "1200000.00",
                    "ytd": "12000000.00",
                    "pytd": "120000000.00"
                },
                "plug": {
                    "daily": "3456.78",
                    "mtd": "34567.89",
                    "ytd": "345678.90",
                    "pytd": "3456789.01"
                },
                "is_override": True,
                "is_reconciled": False,
                "path": ["Global Trading P&L", "Americas", "Cash Equities", "Americas Cash NY"],
                "children": []
            }
        }


# Allow forward references
ResultsNode.model_rebuild()


class ResultsResponse(BaseModel):
    """Response schema for results endpoint."""
    run_id: str = Field(..., description="Run ID")
    use_case_id: str = Field(..., description="Use case ID")
    version_tag: str = Field(..., description="Version tag for this run")
    run_timestamp: str = Field(..., description="When the calculation was run")
    hierarchy: List[ResultsNode] = Field(..., description="Hierarchy tree with calculation results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "run_id": "123e4567-e89b-12d3-a456-426614174000",
                "use_case_id": "123e4567-e89b-12d3-a456-426614174001",
                "version_tag": "Nov_Actuals_v1",
                "run_timestamp": "2024-01-01T00:00:00",
                "hierarchy": []
            }
        }