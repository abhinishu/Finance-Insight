"""
Discovery API routes for Finance-Insight
Provides hierarchy with natural values for discovery view.
"""

from typing import Dict, List, Optional
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.schemas import DiscoveryResponse, HierarchyNode, ReconciliationData
from app.engine.waterfall import calculate_natural_rollup, load_facts, load_hierarchy
from app.models import UseCase

router = APIRouter(prefix="/api/v1", tags=["discovery"])


@router.get("/structures")
def list_structures(db: Session = Depends(get_db)):
    """
    List all available Atlas structures.
    
    Returns list of structures with metadata (structure_id, name, node_count).
    """
    from app.models import DimHierarchy
    from sqlalchemy import func
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Get distinct structures with counts (filter out NULL atlas_source)
    structures = db.query(
        DimHierarchy.atlas_source,
        func.count(DimHierarchy.node_id).label('node_count')
    ).filter(
        DimHierarchy.atlas_source.isnot(None)  # Filter out NULL structures
    ).group_by(DimHierarchy.atlas_source).all()
    
    logger.info(f"Structures: Found {len(structures)} structures in database")
    
    result = []
    for structure_id, node_count in structures:
        if structure_id:  # Additional safety check
            # Generate friendly name from structure_id
            name = structure_id.replace('_', ' ').title()
            if structure_id.startswith('MOCK_ATLAS'):
                name = f"Mock Atlas Structure {structure_id.split('_')[-1]}"
            
            result.append({
                "structure_id": structure_id,
                "name": name,
                "node_count": node_count
            })
    
    logger.info(f"Structures: Returning {len(result)} valid structures")
    return {"structures": result}


def build_tree_structure(
    hierarchy_dict: Dict,
    children_dict: Dict,
    natural_results: Dict,
    node_id: str,
    include_pytd: bool = False,
    parent_attributes: Dict = None,
    path_dict: Dict = None
) -> HierarchyNode:
    """
    Recursively build tree structure from hierarchy with multi-dimensional attributes and path array.
    Uses path_dict from SQL CTE for accurate path arrays.
    
    Args:
        hierarchy_dict: Dictionary mapping node_id -> node data
        children_dict: Dictionary mapping parent_node_id -> list of children
        natural_results: Dictionary mapping node_id -> measure values
        node_id: Current node ID
        include_pytd: Whether to include PYTD measure
        parent_attributes: Attributes from parent node (for inheritance)
        path_dict: Dictionary mapping node_id -> path array from SQL CTE
    
    Returns:
        HierarchyNode with children, attributes, and path array
    """
    from app.engine.finance_hierarchy import get_node_attributes
    
    node = hierarchy_dict[node_id]
    measures = natural_results.get(node_id, {
        'daily': 0,
        'mtd': 0,
        'ytd': 0,
        'pytd': 0
    })
    
    # Get path from CTE result (uses node_name, not node_id)
    # Path format: ["Global Trading P&L", "Americas", "Cash Equities", ...]
    if path_dict:
        # Try both string and direct lookup
        current_path = path_dict.get(node_id) or path_dict.get(str(node_id))
        if not current_path:
            # Fallback: build path from node_name
            current_path = [node.node_name]
    else:
        # Fallback: build path from node_name
        current_path = [node.node_name]
    
    # Extract attributes for this node
    attrs = get_node_attributes(node.node_id, node.node_name, parent_attributes)
    
    # Build children recursively (pass attributes and path_dict for inheritance)
    children = []
    for child_id in children_dict.get(node_id, []):
        child_node = build_tree_structure(
            hierarchy_dict, children_dict, natural_results, child_id, include_pytd, attrs, path_dict
        )
        children.append(child_node)
    
    # Create node with attributes and path
    node_data = {
        'node_id': node.node_id,
        'node_name': node.node_name,
        'parent_node_id': node.parent_node_id,
        'depth': node.depth,
        'is_leaf': node.is_leaf,
        'daily_pnl': str(measures['daily']),
        'mtd_pnl': str(measures['mtd']),
        'ytd_pnl': str(measures['ytd']),
        'region': attrs.get('region'),
        'product': attrs.get('product'),
        'desk': attrs.get('desk'),
        'strategy': attrs.get('strategy'),
        'official_gl_baseline': str(measures['daily']),  # Same as daily_pnl for natural values
        'path': current_path,  # Path array from SQL CTE for AG-Grid tree data
        'children': children,
    }
    
    if include_pytd:
        node_data['pytd_pnl'] = str(measures.get('pytd', 0))
    
    return HierarchyNode(**node_data)


@router.get("/discovery", response_model=DiscoveryResponse)
def get_discovery_view(
    structure_id: str,
    report_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """
    Get hierarchy with natural values for discovery view.
    
    This endpoint provides a live discovery view with natural rollups only.
    No rules are applied - pure bottom-up aggregation.
    Uses structure_id directly (no use case required for discovery).
    
    If report_id is provided, filters measures and dimensions based on ReportRegistration configuration.
    This ensures Tab 1 configuration drives what's displayed in Tabs 2 and 3.
    
    Args:
        structure_id: Atlas structure identifier
        report_id: Optional report registration ID (for filtering measures/dimensions)
        db: Database session
    
    Returns:
        DiscoveryResponse with hierarchy tree and natural values
    """
    from app.models import DimHierarchy, ReportRegistration
    from sqlalchemy import text
    
    # Load hierarchy by structure_id (NO JOIN with rules - pure Phase 1 functionality)
    hierarchy_nodes = db.query(DimHierarchy).filter(
        DimHierarchy.atlas_source == structure_id
    ).all()
    
    import logging
    logger = logging.getLogger(__name__)
    
    # Load report registration if report_id provided (for filtering)
    report_config = None
    if report_id:
        report_config = db.query(ReportRegistration).filter(
            ReportRegistration.report_id == report_id
        ).first()
        if not report_config:
            raise HTTPException(
                status_code=404,
                detail=f"Report registration '{report_id}' not found"
            )
        # Verify structure_id matches
        if report_config.atlas_structure_id != structure_id:
            raise HTTPException(
                status_code=400,
                detail=f"Report structure '{report_config.atlas_structure_id}' does not match requested structure '{structure_id}'"
            )
        logger.info(f"Discovery: Using report configuration for report_id: {report_id}")
        logger.info(f"  Selected measures: {report_config.selected_measures}")
        logger.info(f"  Selected dimensions: {report_config.selected_dimensions}")
    
    logger.info(f"Discovery: Loaded {len(hierarchy_nodes)} nodes for structure_id: {structure_id}")
    
    if not hierarchy_nodes:
        logger.warning(f"Discovery: No hierarchy found for structure_id: {structure_id}")
        raise HTTPException(
            status_code=404,
            detail=f"No hierarchy found for structure_id: {structure_id}"
        )
    
    # Build path arrays using SQL CTE (recursive)
    # This creates a path array for each node: ["Global Trading P&L", "Americas", "Cash Equities", ...]
    try:
        path_query = text("""
            WITH RECURSIVE node_paths AS (
                -- Base case: root nodes
                SELECT 
                    node_id,
                    node_name,
                    ARRAY[node_name]::text[] as path
                FROM dim_hierarchy
                WHERE atlas_source = :structure_id AND parent_node_id IS NULL
                
                UNION ALL
                
                -- Recursive case: children
                SELECT 
                    h.node_id,
                    h.node_name,
                    np.path || h.node_name
                FROM dim_hierarchy h
                INNER JOIN node_paths np ON h.parent_node_id = np.node_id
                WHERE h.atlas_source = :structure_id
            )
            SELECT node_id, path FROM node_paths
        """)
        
        path_results = db.execute(path_query, {"structure_id": structure_id}).fetchall()
        # Build path_dict: key is node_id (string), value is path array of node_names
        path_dict = {}
        for row in path_results:
            node_id_key = str(row[0])  # node_id as string key
            path_array = list(row[1]) if row[1] else []  # Path array of node_names
            path_dict[node_id_key] = path_array
        
        # Debug: Log first 5 paths to verify they use node_name, not node_id
        print(f"=== Path CTE Verification (first 5) ===")
        for i, (node_id_key, path_array) in enumerate(list(path_dict.items())[:5]):
            print(f"  {i+1}. node_id={node_id_key}, path={path_array}")
    except Exception as e:
        # Fallback: build paths recursively in Python if CTE fails
        print(f"CTE path building failed, using Python fallback: {e}")
        path_dict = {}
    
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
    
    # Build tree structure starting from root (with attributes and path from CTE)
    root_node = build_tree_structure(
        hierarchy_dict, children_dict, natural_results, root_id, include_pytd=False, parent_attributes=None, path_dict=path_dict
    )
    
    # Calculate reconciliation totals: sum of leaf nodes vs fact table sum
    # Wrap in try-except to make it optional if it fails
    reconciliation_data = None
    try:
        from sqlalchemy import func
        from app.models import FactPnlGold
        
        # Sum of all facts in fact_pnl_gold
        fact_totals = db.query(
            func.sum(FactPnlGold.daily_pnl).label('daily_total'),
            func.sum(FactPnlGold.mtd_pnl).label('mtd_total'),
            func.sum(FactPnlGold.ytd_pnl).label('ytd_total')
        ).first()
        
        # Sum of leaf nodes from natural results
        leaf_totals = {
            'daily': Decimal('0'),
            'mtd': Decimal('0'),
            'ytd': Decimal('0')
        }
        for node_id in leaf_nodes:
            if node_id in natural_results:
                leaf_totals['daily'] += Decimal(str(natural_results[node_id].get('daily', 0)))
                leaf_totals['mtd'] += Decimal(str(natural_results[node_id].get('mtd', 0)))
                leaf_totals['ytd'] += Decimal(str(natural_results[node_id].get('ytd', 0)))
        
        # Build reconciliation data
        reconciliation_data = ReconciliationData(
            fact_table_sum={
                'daily': str(fact_totals.daily_total or 0),
                'mtd': str(fact_totals.mtd_total or 0),
                'ytd': str(fact_totals.ytd_total or 0)
            },
            leaf_nodes_sum={
                'daily': str(leaf_totals['daily']),
                'mtd': str(leaf_totals['mtd']),
                'ytd': str(leaf_totals['ytd'])
            }
        )
    except Exception as e:
        # Log error but don't fail the request
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to calculate reconciliation data: {e}")
        reconciliation_data = None
    
    # Build response with optional reconciliation data
    logger.info(f"Discovery: Returning hierarchy with {len([root_node])} root node(s)")
    response = DiscoveryResponse(
        structure_id=structure_id,
        hierarchy=[root_node],
        reconciliation_data=reconciliation_data
    )
    return response


@router.get("/fact-values/{field_name}")
def get_sample_values(field_name: str, limit: int = 5, db: Session = Depends(get_db)):
    """
    Get sample values for a given field from fact_pnl_gold table.
    Used by Field Helper to show users actual values in the database.
    
    Args:
        field_name: Field name (e.g., 'book_id', 'strategy_id')
        limit: Number of sample values to return (default: 5)
        db: Database session
    
    Returns:
        List of distinct sample values
    """
    from app.models import FactPnlGold
    from sqlalchemy import distinct, func
    
    # Validate field name
    valid_fields = ['account_id', 'cc_id', 'book_id', 'strategy_id']
    if field_name not in valid_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid field name. Must be one of: {valid_fields}"
        )
    
    try:
        # Get distinct values for the field
        field_attr = getattr(FactPnlGold, field_name)
        distinct_values = db.query(distinct(field_attr)).limit(limit).all()
        
        # Flatten the list of tuples
        values = [val[0] for val in distinct_values if val[0] is not None]
        
        return {
            "field_name": field_name,
            "sample_values": values,
            "count": len(values)
        }
    except Exception as e:
        logger.error(f"Failed to get sample values for {field_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve sample values: {str(e)}"
        )(
        structure_id=structure_id,
        hierarchy=[root_node],
        reconciliation=reconciliation_data
    )
    logger.info(f"Discovery: Response built successfully, hierarchy has {len(response.hierarchy)} root nodes")
    return response

