"""
Discovery API routes for Finance-Insight
Provides hierarchy with natural values for discovery view.
"""

from typing import Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.schemas import DiscoveryResponse, HierarchyNode
from app.engine.waterfall import calculate_natural_rollup, load_facts, load_hierarchy
from app.models import UseCase

router = APIRouter(prefix="/api/v1", tags=["discovery"])


def build_tree_structure(
    hierarchy_dict: Dict,
    children_dict: Dict,
    natural_results: Dict,
    node_id: str,
    include_pytd: bool = False
) -> HierarchyNode:
    """
    Recursively build tree structure from hierarchy.
    
    Args:
        hierarchy_dict: Dictionary mapping node_id -> node data
        children_dict: Dictionary mapping parent_node_id -> list of children
        natural_results: Dictionary mapping node_id -> measure values
        node_id: Current node ID
        include_pytd: Whether to include PYTD measure
    
    Returns:
        HierarchyNode with children
    """
    node = hierarchy_dict[node_id]
    measures = natural_results.get(node_id, {
        'daily': 0,
        'mtd': 0,
        'ytd': 0,
        'pytd': 0
    })
    
    # Build children recursively
    children = []
    for child_id in children_dict.get(node_id, []):
        child_node = build_tree_structure(
            hierarchy_dict, children_dict, natural_results, child_id, include_pytd
        )
        children.append(child_node)
    
    # Create node
    node_data = {
        'node_id': node.node_id,
        'node_name': node.node_name,
        'parent_node_id': node.parent_node_id,
        'depth': node.depth,
        'is_leaf': node.is_leaf,
        'daily_pnl': str(measures['daily']),
        'mtd_pnl': str(measures['mtd']),
        'ytd_pnl': str(measures['ytd']),
        'children': children,
    }
    
    if include_pytd:
        node_data['pytd_pnl'] = str(measures.get('pytd', 0))
    
    return HierarchyNode(**node_data)


@router.get("/discovery", response_model=DiscoveryResponse)
def get_discovery_view(
    structure_id: str,
    db: Session = Depends(get_db)
):
    """
    Get hierarchy with natural values for discovery view.
    
    This endpoint provides a live discovery view with natural rollups only.
    No rules are applied - pure bottom-up aggregation.
    Uses structure_id directly (no use case required for discovery).
    
    Args:
        structure_id: Atlas structure identifier
        db: Database session
    
    Returns:
        DiscoveryResponse with hierarchy tree and natural values
    """
    from app.models import DimHierarchy
    
    # Load hierarchy by structure_id
    hierarchy_nodes = db.query(DimHierarchy).filter(
        DimHierarchy.atlas_source == structure_id
    ).all()
    
    if not hierarchy_nodes:
        raise HTTPException(
            status_code=404,
            detail=f"No hierarchy found for structure_id: {structure_id}"
        )
    
    # Build hierarchy dictionaries
    hierarchy_dict = {node.node_id: node for node in hierarchy_nodes}
    children_dict = {}
    leaf_nodes = []
    
    for node in hierarchy_nodes:
        if node.parent_node_id:
            if node.parent_node_id not in children_dict:
                children_dict[node.parent_node_id] = []
            children_dict[node.parent_node_id].append(node.node_id)
        if node.is_leaf:
            leaf_nodes.append(node.node_id)
    
    # Find root node
    root_nodes = [node_id for node_id, node in hierarchy_dict.items() if node.parent_node_id is None]
    if not root_nodes:
        raise HTTPException(
            status_code=500,
            detail="No root node found in hierarchy"
        )
    
    root_id = root_nodes[0]
    
    # Load facts
    facts_df = load_facts(db)
    
    # Calculate natural rollups (no rules)
    natural_results = calculate_natural_rollup(
        hierarchy_dict, children_dict, leaf_nodes, facts_df
    )
    
    # Build tree structure starting from root
    root_node = build_tree_structure(
        hierarchy_dict, children_dict, natural_results, root_id, include_pytd=False
    )
    
    return DiscoveryResponse(
        structure_id=structure_id,
        hierarchy=[root_node]
    )

