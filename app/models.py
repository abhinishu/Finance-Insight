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
    """
    __tablename__ = "use_cases"

    use_case_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    owner_id = Column(String, nullable=False)
    atlas_structure_id = Column(String, nullable=False)  # Reference to Atlas tree
    status = Column(Enum(UseCaseStatus), nullable=False, default=UseCaseStatus.DRAFT)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    # Relationships
    rules = relationship("MetadataRule", back_populates="use_case", cascade="all, delete-orphan")
    runs = relationship("UseCaseRun", back_populates="use_case", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<UseCase(id={self.use_case_id}, name='{self.name}', status={self.status})>"


class UseCaseRun(Base):
    """
    Run history - snapshots of calculation runs with version tags.
    Includes audit fields for performance monitoring and traceability.
    """
    __tablename__ = "use_case_runs"

    run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    use_case_id = Column(UUID(as_uuid=True), ForeignKey("use_cases.use_case_id"), nullable=False)
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
    """
    __tablename__ = "dim_hierarchy"

    node_id = Column(String(50), primary_key=True)
    parent_node_id = Column(String(50), ForeignKey("dim_hierarchy.node_id"), nullable=True)
    node_name = Column(String, nullable=False)
    depth = Column(Integer, nullable=False)
    is_leaf = Column(Boolean, nullable=False, default=False)
    atlas_source = Column(String)  # Track which Atlas version this came from

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
    """
    __tablename__ = "metadata_rules"

    rule_id = Column(Integer, primary_key=True, autoincrement=True)
    use_case_id = Column(UUID(as_uuid=True), ForeignKey("use_cases.use_case_id"), nullable=False)
    node_id = Column(String(50), ForeignKey("dim_hierarchy.node_id"), nullable=False)
    predicate_json = Column(JSONB)  # JSON predicate for UI/GenAI state
    sql_where = Column(Text, nullable=False)  # SQL WHERE clause for execution
    logic_en = Column(Text)  # Natural language description for auditability
    last_modified_by = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    last_modified_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    use_case = relationship("UseCase", back_populates="rules")
    node = relationship("DimHierarchy", back_populates="rules")

    # Unique constraint: only one rule per node per use case
    __table_args__ = (
        UniqueConstraint("use_case_id", "node_id", name="uq_use_case_node"),
    )

    def __repr__(self):
        return f"<MetadataRule(id={self.rule_id}, use_case={self.use_case_id}, node='{self.node_id}')>"


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
    Calculated results - output from waterfall engine.
    Each row represents a single node's calculated values for a specific run.
    """
    __tablename__ = "fact_calculated_results"

    result_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("use_case_runs.run_id"), nullable=False)
    node_id = Column(String(50), ForeignKey("dim_hierarchy.node_id"), nullable=False)
    measure_vector = Column(JSONB, nullable=False)  # {daily: X, mtd: Y, ytd: Z, pytd: W}
    plug_vector = Column(JSONB)  # {daily: X, mtd: Y, ytd: Z, pytd: W} - reconciliation plugs
    is_override = Column(Boolean, nullable=False, default=False)  # True if a rule was applied
    is_reconciled = Column(Boolean, nullable=False, default=True)  # Flag for UI to detect leaks
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    # Relationships
    run = relationship("UseCaseRun", back_populates="results")
    node = relationship("DimHierarchy", back_populates="results")

    def __repr__(self):
        return f"<FactCalculatedResult(id={self.result_id}, run={self.run_id}, node='{self.node_id}', override={self.is_override})>"

