"""
SQLAlchemy Models for Finance-Insight
Based on refined database schema with UUIDs, JSONB vectors, and audit fields.
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    TIMESTAMP,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# Enums
class UseCaseStatus(str, PyEnum):
    """Use case status enumeration."""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class RunStatus(str, PyEnum):
    """Run status enumeration."""
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class UseCase(Base):
    """
    Core use case table - each use case is an isolated sandbox.
    
    Phase 5.1: Added input_table_name to support table-per-use-case strategy.
    Phase 5.1: Added measure_mapping to support different column names across use cases.
    """
    __tablename__ = "use_cases"

    use_case_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    owner_id = Column(String, nullable=False)
    atlas_structure_id = Column(String, nullable=False)  # Reference to Atlas tree
    status = Column(Enum(UseCaseStatus), nullable=False, default=UseCaseStatus.DRAFT)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    
    # Phase 5.1: Table-per-use-case strategy
    input_table_name = Column(String(100), nullable=True)  # NULL = use default fact_pnl_gold
    
    # Phase 5.1: Measure mapping for different column names across use cases
    # Format: {"daily": "daily_pnl", "mtd": "mtd_pnl", "ytd": "ytd_pnl"}
    # Example UC 3: {"daily": "pnl_daily", "mtd": "pnl_commission", "ytd": "pnl_trade"}
    measure_mapping = Column(JSONB, nullable=True)

    # Relationships
    rules = relationship("MetadataRule", back_populates="use_case", cascade="all, delete-orphan")
    runs = relationship("UseCaseRun", back_populates="use_case", cascade="all, delete-orphan")
    snapshots = relationship("HistorySnapshot", back_populates="use_case", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<UseCase(id={self.use_case_id}, name='{self.name}', status={self.status}, input_table='{self.input_table_name}')>"


class UseCaseRun(Base):
    """
    Run history - snapshots of calculation runs with version tags.
    Includes audit fields for performance monitoring and traceability.
    """
    __tablename__ = "use_case_runs"

    run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    use_case_id = Column(UUID(as_uuid=True), ForeignKey("use_cases.use_case_id", ondelete="CASCADE"), nullable=False)
    version_tag = Column(String, nullable=False)  # e.g., "Nov_Actuals_v1"
    run_timestamp = Column(TIMESTAMP, nullable=False, server_default=func.now())
    parameters_snapshot = Column(JSONB)  # Snapshots the rules used for this run
    status = Column(Enum(RunStatus), nullable=False, default=RunStatus.IN_PROGRESS)
    triggered_by = Column(String, nullable=False)  # user_id who triggered the calculation
    calculation_duration_ms = Column(Integer)  # Duration in milliseconds for performance monitoring

    # Relationships
    use_case = relationship("UseCase", back_populates="runs")
    results = relationship("FactCalculatedResult", back_populates="run", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<UseCaseRun(id={self.run_id}, version='{self.version_tag}', status={self.status})>"


class DimHierarchy(Base):
    """
    Hierarchy dimension - tree structure imported from Atlas.
    
    Phase 5.1: Added rollup_driver and rollup_value_source for metadata-driven auto-rollup.
    Explicit Mapping: Added mapping_value for explicit fact table key mapping.
    """
    __tablename__ = "dim_hierarchy"

    node_id = Column(String(50), primary_key=True)
    parent_node_id = Column(String(50), ForeignKey("dim_hierarchy.node_id"), nullable=True)
    node_name = Column(String, nullable=False)
    depth = Column(Integer, nullable=False)
    is_leaf = Column(Boolean, nullable=False, default=False)
    atlas_source = Column(String)  # Track which Atlas version this came from
    
    # Phase 5.1: Metadata-driven auto-rollup support
    rollup_driver = Column(String(50), nullable=True)  # Column name in fact table to filter on (e.g., 'cc_id', 'category_code', 'strategy')
    rollup_value_source = Column(String(20), nullable=True, default='node_id')  # Which hierarchy value to use: 'node_id' or 'node_name'
    
    # Explicit Mapping: Explicit value to match in the fact table (overrides node_id)
    mapping_value = Column(String, nullable=True)

    # Self-referential relationship for tree traversal
    parent = relationship("DimHierarchy", remote_side=[node_id], backref="children")

    # Relationships
    rules = relationship("MetadataRule", back_populates="node")
    results = relationship("FactCalculatedResult", back_populates="node")
    bridge_parents = relationship("HierarchyBridge", foreign_keys="HierarchyBridge.parent_node_id", back_populates="parent_node")
    bridge_leaves = relationship("HierarchyBridge", foreign_keys="HierarchyBridge.leaf_node_id", back_populates="leaf_node")

    def __repr__(self):
        return f"<DimHierarchy(id='{self.node_id}', name='{self.node_name}', leaf={self.is_leaf})>"


class HierarchyBridge(Base):
    """
    Flattened parent-to-leaf mappings for performance.
    Stores every parent node linked to all its recursive leaf CCs.
    Enables fast aggregation without recursive queries.
    """
    __tablename__ = "hierarchy_bridge"

    bridge_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    parent_node_id = Column(String(50), ForeignKey("dim_hierarchy.node_id"), nullable=False)
    leaf_node_id = Column(String(50), ForeignKey("dim_hierarchy.node_id"), nullable=False)
    structure_id = Column(String, nullable=False)  # Atlas structure identifier
    path_length = Column(Integer, nullable=False)  # Number of levels between parent and leaf

    # Relationships
    parent_node = relationship("DimHierarchy", foreign_keys=[parent_node_id], back_populates="bridge_parents")
    leaf_node = relationship("DimHierarchy", foreign_keys=[leaf_node_id], back_populates="bridge_leaves")

    # Index for performance
    __table_args__ = (
        {"comment": "Flattened parent-to-leaf mappings for fast aggregation"}
    )

    def __repr__(self):
        return f"<HierarchyBridge(parent='{self.parent_node_id}', leaf='{self.leaf_node_id}', path={self.path_length})>"


class MetadataRule(Base):
    """
    Business rules - override logic for specific nodes in a use case.
    Only one rule per node per use case (enforced by unique constraint).
    
    Phase 5.1: Added support for multiple rule types:
    - FILTER: Type 1/2 (simple/multi-condition filtering)
    - FILTER_ARITHMETIC: Type 2B (arithmetic of multiple queries)
    - NODE_ARITHMETIC: Type 3 (node arithmetic operations)
    """
    __tablename__ = "metadata_rules"

    rule_id = Column(Integer, primary_key=True, autoincrement=True)
    use_case_id = Column(UUID(as_uuid=True), ForeignKey("use_cases.use_case_id", ondelete="CASCADE"), nullable=False)
    node_id = Column(String(50), ForeignKey("dim_hierarchy.node_id"), nullable=False)
    predicate_json = Column(JSONB)  # JSON predicate for UI/GenAI state
    sql_where = Column(Text, nullable=True)  # SQL WHERE clause for execution (nullable for Phase 1 compatibility)
    logic_en = Column(Text)  # Natural language description for auditability
    last_modified_by = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    last_modified_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Phase 5.1: New columns for rule type system
    rule_type = Column(String(20), nullable=True, default='FILTER')  # FILTER, FILTER_ARITHMETIC, NODE_ARITHMETIC
    measure_name = Column(String(50), nullable=True, default='daily_pnl')  # Measure name for rule execution
    rule_expression = Column(Text, nullable=True)  # Arithmetic expression for Type 3 rules (e.g., "NODE_3 - NODE_4")
    rule_dependencies = Column(JSONB, nullable=True)  # JSON array of node IDs this rule depends on (for Type 3)

    # Relationships
    use_case = relationship("UseCase", back_populates="rules")
    node = relationship("DimHierarchy", back_populates="rules")

    # Unique constraint: only one rule per node per use case
    __table_args__ = (
        UniqueConstraint("use_case_id", "node_id", name="uq_use_case_node"),
    )

    def __repr__(self):
        return f"<MetadataRule(id={self.rule_id}, use_case={self.use_case_id}, node='{self.node_id}', type='{self.rule_type}')>"


class FactPnlGold(Base):
    """
    Gold fact table - source P&L data from unified Gold View.
    Dimensions are VARCHAR to support alphanumeric IDs from external systems.
    """
    __tablename__ = "fact_pnl_gold"

    fact_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id = Column(String(50), nullable=False)
    cc_id = Column(String(50), nullable=False)  # Cost Center ID - maps to hierarchy leaf nodes
    book_id = Column(String(50), nullable=False)
    strategy_id = Column(String(50), nullable=False)
    trade_date = Column(Date, nullable=False)
    daily_pnl = Column(Numeric(18, 2), nullable=False)
    mtd_pnl = Column(Numeric(18, 2), nullable=False)
    ytd_pnl = Column(Numeric(18, 2), nullable=False)
    pytd_pnl = Column(Numeric(18, 2), nullable=False)

    def __repr__(self):
        return f"<FactPnlGold(id={self.fact_id}, cc_id='{self.cc_id}', date={self.trade_date})>"


class FactCalculatedResult(Base):
    """
    Calculated results (reporting_results) - output from waterfall engine.
    Each row represents a single node's calculated values for a specific run.
    Step 4.2: Added calculation_run_id for date-anchored temporal versioning.
    """
    __tablename__ = "fact_calculated_results"

    result_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("use_case_runs.run_id", ondelete="CASCADE"), nullable=True)  # Legacy, nullable for transition
    calculation_run_id = Column(UUID(as_uuid=True), ForeignKey("calculation_runs.id", ondelete="CASCADE"), nullable=True)  # Step 4.2: New date-anchored link
    node_id = Column(String(50), ForeignKey("dim_hierarchy.node_id"), nullable=False)
    measure_vector = Column(JSONB, nullable=False)  # {daily: X, mtd: Y, ytd: Z, pytd: W}
    plug_vector = Column(JSONB)  # {daily: X, mtd: Y, ytd: Z, pytd: W} - reconciliation plugs
    is_override = Column(Boolean, nullable=False, default=False)  # True if a rule was applied
    is_reconciled = Column(Boolean, nullable=False, default=True)  # Flag for UI to detect leaks
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    # Relationships
    run = relationship("UseCaseRun", back_populates="results")  # Legacy relationship
    calculation_run = relationship("CalculationRun", back_populates="results")  # Step 4.2: New relationship
    node = relationship("DimHierarchy", back_populates="results")

    def __repr__(self):
        return f"<FactCalculatedResult(id={self.result_id}, calc_run={self.calculation_run_id}, node='{self.node_id}', override={self.is_override})>"


class ReportRegistration(Base):
    """
    Report Registration table - stores report configurations.
    Links report name to Atlas structure and selected measures/dimensions.
    """
    __tablename__ = "report_registrations"

    report_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    report_name = Column(String(200), nullable=False)
    atlas_structure_id = Column(String(200), nullable=False)  # References dim_hierarchy.atlas_source
    selected_measures = Column(JSONB, nullable=False)  # Array: ["daily", "mtd", "ytd"]
    selected_dimensions = Column(JSONB, nullable=True)  # Array: ["region", "product", "desk"]
    measure_scopes = Column(JSONB, nullable=True)  # {"daily": ["input", "rule", "output"], ...}
    dimension_scopes = Column(JSONB, nullable=True)  # {"region": ["input", "rule", "output"], ...}
    owner_id = Column(String(100), nullable=False, default="default_user")
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<ReportRegistration(id={self.report_id}, name='{self.report_name}')>"


class DimDictionary(Base):
    """
    Dictionary dimension - portable metadata for categories like BOOK, STRATEGY, PRODUCT_TYPE, etc.
    Enables environment portability by storing tech_id to display_name mappings.
    """
    __tablename__ = "dim_dictionary"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    category = Column(String(50), nullable=False)  # BOOK, STRATEGY, PRODUCT_TYPE, LEGAL_ENTITY, RISK_OFFICER
    tech_id = Column(String(100), nullable=False)  # Technical identifier (e.g., "EQ_CORE_NYC")
    display_name = Column(String(200), nullable=False)  # Human-readable name
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    # Unique constraint: one tech_id per category
    __table_args__ = (
        UniqueConstraint("category", "tech_id", name="uq_category_tech_id"),
    )

    def __repr__(self):
        return f"<DimDictionary(category='{self.category}', tech_id='{self.tech_id}', display='{self.display_name}')>"


class FactPnlEntries(Base):
    """
    Consolidated P&L fact table - merges PNL_Data and PNL_Prior_Data.
    Uses scenario field to distinguish 'ACTUAL' vs 'PRIOR' data.
    Step 4.2: Added explicit columns for daily, wtd, and ytd measures.
    """
    __tablename__ = "fact_pnl_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    use_case_id = Column(UUID(as_uuid=True), ForeignKey("use_cases.use_case_id", ondelete="CASCADE"), nullable=False)
    pnl_date = Column(Date, nullable=False)
    category_code = Column(String(50), nullable=False)  # Maps to dim_dictionary.tech_id or hierarchy node
    amount = Column(Numeric(18, 2), nullable=False)  # Legacy column, kept for backward compatibility
    daily_amount = Column(Numeric(18, 2), nullable=False)  # Step 4.2: Explicit daily measure
    wtd_amount = Column(Numeric(18, 2), nullable=False)  # Step 4.2: Week-to-date measure
    ytd_amount = Column(Numeric(18, 2), nullable=False)  # Step 4.2: Year-to-date measure
    scenario = Column(String(20), nullable=False)  # 'ACTUAL' or 'PRIOR'
    audit_metadata = Column(JSONB, nullable=True)  # Additional metadata: source, timestamp, etc.

    # Relationships
    use_case = relationship("UseCase")

    def __repr__(self):
        return f"<FactPnlEntries(id={self.id}, use_case={self.use_case_id}, date={self.pnl_date}, scenario={self.scenario})>"


class FactPnlUseCase3(Base):
    """
    Phase 5.1: Dedicated fact table for Use Case 3 (America Cash Equity Trading).
    All PnL columns use NUMERIC(18,2) for Decimal precision (never FLOAT).
    """
    __tablename__ = "fact_pnl_use_case_3"

    entry_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    effective_date = Column(Date, nullable=False)
    
    # Hierarchical Dimensions
    cost_center = Column(String(50), nullable=True)
    division = Column(String(50), nullable=True)
    business_area = Column(String(100), nullable=True)
    product_line = Column(String(100), nullable=True)
    strategy = Column(String(100), nullable=True)
    process_1 = Column(String(100), nullable=True)
    process_2 = Column(String(100), nullable=True)
    book = Column(String(100), nullable=True)
    
    # Financial Measures (CRITICAL: NUMERIC(18,2) for Decimal precision)
    pnl_daily = Column(Numeric(18, 2), nullable=False, default=0)
    pnl_commission = Column(Numeric(18, 2), nullable=False, default=0)
    pnl_trade = Column(Numeric(18, 2), nullable=False, default=0)
    
    # Audit Fields
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    def __repr__(self):
        return f"<FactPnlUseCase3(id={self.entry_id}, date={self.effective_date}, strategy='{self.strategy}')>"


class CalculationRun(Base):
    """
    Calculation Runs (Header) - Temporal versioning pattern for date-anchored reporting.
    Each run represents a snapshot execution for a specific PNL_DATE.
    Supports "Trial Analysis" where users can compare different rule versions for the same date.
    """
    __tablename__ = "calculation_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    pnl_date = Column(Date, nullable=False)  # COB date anchor
    use_case_id = Column(UUID(as_uuid=True), ForeignKey("use_cases.use_case_id", ondelete="CASCADE"), nullable=False)
    run_name = Column(String(200), nullable=False)  # e.g., "Initial Run", "Adjusted v2"
    executed_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    status = Column(String(20), nullable=False, default="IN_PROGRESS")  # IN_PROGRESS, COMPLETED, FAILED
    triggered_by = Column(String(100), nullable=False)  # user_id
    calculation_duration_ms = Column(Integer, nullable=True)  # Performance tracking

    # Relationships
    use_case = relationship("UseCase")
    results = relationship("FactCalculatedResult", back_populates="calculation_run", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CalculationRun(id={self.id}, date={self.pnl_date}, name='{self.run_name}', status={self.status})>"


class HistorySnapshot(Base):
    """
    History snapshots table - locks and archives rule-sets and results.
    Allows users to "freeze" a month-end report so it never changes.
    """
    __tablename__ = "history_snapshots"

    snapshot_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    use_case_id = Column(UUID(as_uuid=True), ForeignKey("use_cases.use_case_id"), nullable=False)
    snapshot_name = Column(String(200), nullable=False)
    snapshot_date = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    created_by = Column(String(100), nullable=False)
    
    # JSONB snapshots
    rules_snapshot = Column(JSONB)  # Array of rule objects: [{node_id, logic_en, sql_where, ...}]
    results_snapshot = Column(JSONB)  # Array of result objects: [{node_id, natural_value, adjusted_value, plug, ...}]
    
    # Metadata
    notes = Column(Text, nullable=True)
    version_tag = Column(String(50), nullable=True)
    
    # Relationships
    use_case = relationship("UseCase", back_populates="snapshots")

    def __repr__(self):
        return f"<HistorySnapshot(id={self.snapshot_id}, use_case={self.use_case_id}, name='{self.snapshot_name}')>"
