"""
Pydantic schemas for Finance-Insight API
"""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


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

