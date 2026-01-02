"""
Discovery API routes for Finance-Insight
Provides hierarchy with natural values for discovery view.
"""

from typing import Dict, List, Optional
from uuid import UUID
from decimal import Decimal
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.schemas import DiscoveryResponse, HierarchyNode, ReconciliationData
from app.engine.waterfall import calculate_natural_rollup, load_facts, load_facts_from_entries, load_hierarchy, load_facts_from_use_case_3
from app.services.fact_service import load_facts_for_use_case, load_facts_gold_for_structure, verify_reconciliation
from app.services.unified_pnl_service import get_unified_pnl, _calculate_legacy_rollup, _calculate_strategy_rollup, _calculate_legacy_rollup, _calculate_strategy_rollup
from app.models import UseCase

router = APIRouter(prefix="/api/v1", tags=["discovery"])


def _create_empty_atlas_template(db: Session, structure_id: str) -> List:
    """
    Create an Empty Atlas Template hierarchy when no hierarchy exists.
    Structure: Legal Entity > Region > Strategy > Book (4-tier hierarchy)
    
    Uses dim_dictionary to get available values for each tier, or creates default structure.
    """
    from app.models import DimHierarchy, DimDictionary
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"Creating Empty Atlas Template for structure_id: {structure_id}")
    
    # Get available values from dim_dictionary
    legal_entities = db.query(DimDictionary).filter(
        DimDictionary.category == 'LEGAL_ENTITY'
    ).all()
    regions = db.query(DimDictionary).filter(
        DimDictionary.category == 'REGION'
    ).all()
    strategies = db.query(DimDictionary).filter(
        DimDictionary.category == 'STRATEGY'
    ).all()
    books = db.query(DimDictionary).filter(
        DimDictionary.category == 'BOOK'
    ).all()
    
    # If no dictionary entries, use default structure
    class DictEntry:
        def __init__(self, tech_id, display_name):
            self.tech_id = tech_id
            self.display_name = display_name
    
    if not legal_entities:
        legal_entities = [DictEntry('GLOBAL_ENTITY', 'Global Trading P&L')]
    if not regions:
        regions = [
            DictEntry('AMER', 'Americas'),
            DictEntry('EMEA', 'EMEA'),
            DictEntry('APAC', 'APAC')
        ]
    if not strategies:
        strategies = [
            DictEntry('CASH_EQUITIES', 'Cash Equities'),
            DictEntry('DERIVATIVES', 'Derivatives'),
            DictEntry('FIXED_INCOME', 'Fixed Income')
        ]
    if not books:
        books = [
            DictEntry('BOOK_001', 'Book 001'),
            DictEntry('BOOK_002', 'Book 002')
        ]
    
    template_nodes = []
    
    # Root node - check if it already exists for this structure
    existing_root = db.query(DimHierarchy).filter(
        DimHierarchy.atlas_source == structure_id,
        DimHierarchy.parent_node_id.is_(None)
    ).first()
    
    root_node_id = 'ROOT'
    if not existing_root:
        root_node = DimHierarchy(
            node_id=root_node_id,
            parent_node_id=None,
            node_name='Global Trading P&L',
            depth=0,
            is_leaf=False,
            atlas_source=structure_id
        )
        template_nodes.append(root_node)
        logger.info(f"Creating new root node: {root_node_id} for structure_id: {structure_id}")
    else:
        # Use existing root - don't add to template_nodes (it's already in DB)
        root_node_id = existing_root.node_id
        logger.info(f"Using existing root node: {root_node_id} for structure_id: {structure_id}")
    
    # Legal Entity level (depth 1)
    for entity in legal_entities[:3]:  # Limit to 3 for template
        entity_id = f"ENTITY_{entity.tech_id}"
        entity_node = DimHierarchy(
            node_id=entity_id,
            parent_node_id=root_node_id,  # Use the root_node_id variable
            node_name=entity.display_name if hasattr(entity, 'display_name') else entity.tech_id,
            depth=1,
            is_leaf=False,
            atlas_source=structure_id
        )
        template_nodes.append(entity_node)
        
        # Region level (depth 2) - under first entity only for template
        if entity == legal_entities[0]:
            for region in regions[:3]:  # Limit to 3 regions
                region_id = f"{entity_id}_{region.tech_id}"
                region_node = DimHierarchy(
                    node_id=region_id,
                    parent_node_id=entity_id,
                    node_name=region.display_name if hasattr(region, 'display_name') else region.tech_id,
                    depth=2,
                    is_leaf=False,
                    atlas_source=structure_id
                )
                template_nodes.append(region_node)
                
                # Strategy level (depth 3) - under first region only
                if region == regions[0]:
                    for strategy in strategies[:2]:  # Limit to 2 strategies
                        strategy_id = f"{region_id}_{strategy.tech_id}"
                        strategy_node = DimHierarchy(
                            node_id=strategy_id,
                            parent_node_id=region_id,
                            node_name=strategy.display_name if hasattr(strategy, 'display_name') else strategy.tech_id,
                            depth=3,
                            is_leaf=False,
                            atlas_source=structure_id
                        )
                        template_nodes.append(strategy_node)
                        
                        # Book level (depth 4 - leaf nodes)
                        for book in books[:2]:  # Limit to 2 books
                            book_id = f"{strategy_id}_{book.tech_id}"
                            book_node = DimHierarchy(
                                node_id=book_id,
                                parent_node_id=strategy_id,
                                node_name=book.display_name if hasattr(book, 'display_name') else book.tech_id,
                                depth=4,
                                is_leaf=True,
                                atlas_source=structure_id
                            )
                            template_nodes.append(book_node)
    
    # Save template nodes to database
    try:
        nodes_added = 0
        for node in template_nodes:
            # Check if node already exists (skip if it's already in DB)
            existing = db.query(DimHierarchy).filter(
                DimHierarchy.node_id == node.node_id,
                DimHierarchy.atlas_source == structure_id
            ).first()
            if not existing:
                db.add(node)
                nodes_added += 1
            else:
                # Node already exists, refresh it to ensure it's attached to session
                db.refresh(existing)
        
        if nodes_added > 0:
            db.commit()
            logger.info(f"Created {nodes_added} new template nodes for structure_id: {structure_id}")
        else:
            logger.info(f"All {len(template_nodes)} template nodes already exist for structure_id: {structure_id}")
        
        # Always return the template_nodes list (even if they already existed)
        return template_nodes
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create template nodes: {e}", exc_info=True)
        return []


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
    import logging
    logger = logging.getLogger(__name__)
    
    # CRITICAL: Ensure node_id exists in hierarchy_dict (prevent null/None errors)
    if node_id not in hierarchy_dict:
        logger.error(f"build_tree_structure: node_id '{node_id}' not found in hierarchy_dict. Available keys: {list(hierarchy_dict.keys())[:10]}")
        raise ValueError(f"node_id '{node_id}' not found in hierarchy_dict")
    
    node = hierarchy_dict[node_id]
    # CRITICAL: Explicitly map daily_amount -> daily_pnl, wtd_amount -> mtd_pnl, ytd_amount -> ytd_pnl
    # Ensure measures are Decimal, not int/float
    measures = natural_results.get(node_id, {
        'daily': Decimal('0'),  # Maps to daily_pnl in response (from daily_amount)
        'mtd': Decimal('0'),    # Maps to mtd_pnl in response (from wtd_amount)
        'ytd': Decimal('0'),    # Maps to ytd_pnl in response (from ytd_amount)
        'pytd': Decimal('0')
    })
    
    # Ensure all measures are Decimal type
    if not isinstance(measures.get('daily'), Decimal):
        measures['daily'] = Decimal(str(measures.get('daily', 0)))
    if not isinstance(measures.get('mtd'), Decimal):
        measures['mtd'] = Decimal(str(measures.get('mtd', 0)))
    if not isinstance(measures.get('ytd'), Decimal):
        measures['ytd'] = Decimal(str(measures.get('ytd', 0)))
    
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
    # Filter out any child_id that's not in hierarchy_dict (e.g., TRADE or STERLING_RULE nodes)
    children = []
    for child_id in children_dict.get(node_id, []):
        # Skip nodes that aren't in hierarchy_dict (filtered out TRADE/STERLING_RULE nodes)
        if child_id not in hierarchy_dict:
            continue
        # Skip TRADE and STERLING_RULE nodes explicitly
        if child_id.startswith('TRADE_') or child_id.startswith('STERLING_RULE'):
            continue
        child_node = build_tree_structure(
            hierarchy_dict, children_dict, natural_results, child_id, include_pytd, attrs, path_dict
        )
        children.append(child_node)
    
    # Create node with attributes and path
    # CRITICAL: Explicitly map daily_amount -> daily_pnl, wtd_amount -> mtd_pnl, ytd_amount -> ytd_pnl
    # Ensure node_id is never null
    node_data = {
        'node_id': str(node.node_id) if node.node_id else 'UNKNOWN',  # Prevent null node_id
        'node_name': str(node.node_name) if node.node_name else 'Unknown',
        'parent_node_id': str(node.parent_node_id) if node.parent_node_id else None,
        'depth': int(node.depth) if node.depth is not None else 0,
        'is_leaf': bool(node.is_leaf) if node.is_leaf is not None else False,
        'daily_pnl': str(measures['daily']),  # Explicitly mapped from daily_amount
        'mtd_pnl': str(measures['mtd']),      # Explicitly mapped from wtd_amount (pre-calculated)
        'ytd_pnl': str(measures['ytd']),      # Explicitly mapped from ytd_amount
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
    use_case_id: Optional[UUID] = None,
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
    import logging
    logger = logging.getLogger(__name__)
    
    # CRITICAL: Force session refresh - drop SQLAlchemy cache and talk to physical DB
    # Also flush any pending changes to clear "poisoned" transaction state
    try:
        db.expire_all()
        db.flush()  # Flush any pending changes
        logger.info(f"Discovery: Forced session refresh (expire_all + flush) for structure_id: {structure_id}, use_case_id: {use_case_id}")
    except Exception as flush_error:
        logger.warning(f"Discovery: Flush failed (may be expected): {flush_error}")
        # Continue anyway - expire_all is the critical part
    
    try:
        from app.models import DimHierarchy, ReportRegistration
        from sqlalchemy import text
        
        # Load hierarchy by structure_id (NO JOIN with rules - pure Phase 1 functionality)
        hierarchy_nodes = db.query(DimHierarchy).filter(
            DimHierarchy.atlas_source == structure_id
        ).all()

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

        # Check if we have nodes but no root node (orphaned hierarchy)
        if hierarchy_nodes:
            root_nodes_check = [n for n in hierarchy_nodes if n.parent_node_id is None]
        if not root_nodes_check:
            # We have nodes but no root - create the missing ROOT node
            logger.warning(f"Discovery: Found {len(hierarchy_nodes)} nodes but no root node for structure_id: {structure_id}. Creating missing ROOT node.")
            # Check if ROOT already exists (might be for different structure)
            existing_root = db.query(DimHierarchy).filter(
                DimHierarchy.atlas_source == structure_id,
                DimHierarchy.parent_node_id.is_(None)
            ).first()
            
            if not existing_root:
                # Check if ROOT exists with different atlas_source (unique constraint issue)
                root_anywhere = db.query(DimHierarchy).filter(
                    DimHierarchy.node_id == 'ROOT'
                ).first()
                
                if root_anywhere:
                    # ROOT exists but for different structure - update its atlas_source
                    # This handles the unique constraint on node_id='ROOT'
                    logger.warning(f"Discovery: ROOT node exists for structure '{root_anywhere.atlas_source}', updating to '{structure_id}'")
                    root_anywhere.atlas_source = structure_id
                    db.commit()
                    logger.info(f"Discovery: Updated existing ROOT node to use structure_id: {structure_id}")
                else:
                    # Create ROOT node (shouldn't happen due to unique constraint, but just in case)
                    root_node = DimHierarchy(
                        node_id='ROOT',
                        parent_node_id=None,
                        node_name='Global Trading P&L',
                        depth=0,
                        is_leaf=False,
                        atlas_source=structure_id
                    )
                    db.add(root_node)
                    db.commit()
                    logger.info(f"Discovery: Created missing ROOT node for structure_id: {structure_id}")
                
                # Reload hierarchy to include the ROOT node
                hierarchy_nodes = db.query(DimHierarchy).filter(
                    DimHierarchy.atlas_source == structure_id
                ).all()
                logger.info(f"Discovery: Reloaded {len(hierarchy_nodes)} nodes after fixing ROOT")

        if not hierarchy_nodes:
            logger.warning(f"Discovery: No hierarchy found for structure_id: {structure_id}. Creating Empty Atlas Template.")
            # Create Empty Atlas Template: Legal Entity > Region > Strategy > Book
            template_nodes = _create_empty_atlas_template(db, structure_id)
            if not template_nodes:
                # If template creation fails, return a minimal structure
                logger.error(f"Discovery: Failed to create template for structure_id: {structure_id}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create hierarchy template for structure_id: {structure_id}"
                )
            # CRITICAL: Reload hierarchy_nodes from database after template creation
            # This ensures we have the actual persisted nodes, not just in-memory objects
            db.commit()  # Ensure any pending changes are committed
            hierarchy_nodes = db.query(DimHierarchy).filter(
                DimHierarchy.atlas_source == structure_id
            ).all()
            logger.info(f"Discovery: Reloaded {len(hierarchy_nodes)} nodes from database after template creation")
            
            # Verify we have nodes after reload
            if not hierarchy_nodes:
                logger.error(f"Discovery: Template creation succeeded but no nodes found after reload for structure_id: {structure_id}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Template created but nodes not found for structure_id: {structure_id}. Please check database connection."
                )
        
        # Final verification: ensure we have a root node
        root_nodes_final = [n for n in hierarchy_nodes if n.parent_node_id is None]
        if not root_nodes_final:
            logger.error(f"Discovery: No root node found in hierarchy for structure_id: {structure_id}")
            logger.error(f"  Total nodes: {len(hierarchy_nodes)}")
            logger.error(f"  Node IDs: {[n.node_id for n in hierarchy_nodes[:10]]}")
            logger.error(f"  Parent IDs: {[n.parent_node_id for n in hierarchy_nodes[:10]]}")
            raise HTTPException(
                status_code=500,
                detail=f"No root node found in hierarchy for structure_id: {structure_id}. Please check database."
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
        
        # FIRST: Ensure ROOT exists and is loaded before filtering
        # Check if ROOT exists in DB for this structure
        root_check = db.query(DimHierarchy).filter(
            DimHierarchy.atlas_source == structure_id,
            DimHierarchy.node_id == 'ROOT'
        ).first()
        
        # Also check if ROOT exists globally (might need to update atlas_source)
        if not root_check:
            root_global = db.query(DimHierarchy).filter(
                DimHierarchy.node_id == 'ROOT'
            ).first()
            if root_global:
                # Update ROOT's atlas_source to match this structure
                root_global.atlas_source = structure_id
                db.commit()
                root_check = root_global
                logger.info(f"Discovery: Updated ROOT atlas_source to '{structure_id}'")
        
        # Build hierarchy dictionaries
        # Filter out TRADE nodes and STERLING_RULE nodes - only keep business hierarchy
        # BUT: Always include ROOT if it exists
        business_nodes = [
            node for node in hierarchy_nodes 
            if not node.node_id.startswith('TRADE_') 
            and not node.node_id.startswith('STERLING_RULE')
        ]
        
        # Ensure ROOT is included if it exists
        if root_check and root_check not in business_nodes:
            business_nodes.append(root_check)
            logger.info(f"Discovery: Added ROOT node to business_nodes")
        
        hierarchy_dict = {node.node_id: node for node in business_nodes}
        children_dict = {}
        leaf_nodes = []
        
        # Build children_dict only for business nodes (filtered)
        for node in business_nodes:
            if node.parent_node_id:
                # Only add to children_dict if parent is also a business node (not TRADE or STERLING_RULE)
                parent_node = hierarchy_dict.get(node.parent_node_id)
                if parent_node and not parent_node.node_id.startswith('TRADE_') and not parent_node.node_id.startswith('STERLING_RULE'):
                    if node.parent_node_id not in children_dict:
                        children_dict[node.parent_node_id] = []
                    children_dict[node.parent_node_id].append(node.node_id)
            if node.is_leaf:
                leaf_nodes.append(node.node_id)
        
        logger.info(f"Discovery: Filtered to {len(business_nodes)} business nodes (excluded {len(hierarchy_nodes) - len(business_nodes)} TRADE/STERLING_RULE nodes)")
        
        # Find ALL root nodes (support multiple roots)
        root_nodes = [node_id for node_id, node in hierarchy_dict.items() if node.parent_node_id is None]
        logger.info(f"Discovery: Found {len(root_nodes)} root node(s): {root_nodes[:10]}")  # Log first 10
        
        # ALWAYS filter out STERLING_RULE placeholder nodes if ROOT exists
        has_rule_nodes = any(nid.startswith('STERLING_RULE') for nid in root_nodes)
        has_root = 'ROOT' in root_nodes
        
        if has_root and has_rule_nodes:
            # Filter out ALL STERLING_RULE nodes - business hierarchy takes precedence
            rule_nodes = [nid for nid in root_nodes if nid.startswith('STERLING_RULE')]
            if rule_nodes:
                logger.info(f"Discovery: Filtering out {len(rule_nodes)} STERLING_RULE placeholder nodes (business hierarchy exists)")
                root_nodes = ['ROOT']  # Use only ROOT, filter out all rule nodes
                logger.info(f"Discovery: Using ROOT as business hierarchy root node")
        
        if not root_nodes:
            # Last attempt: check if ROOT exists but wasn't loaded (edge case)
            root_check = db.query(DimHierarchy).filter(
                DimHierarchy.atlas_source == structure_id,
                DimHierarchy.parent_node_id.is_(None)
            ).first()
            if root_check:
                # Add ROOT to hierarchy_dict and retry
                hierarchy_dict[root_check.node_id] = root_check
                root_nodes = [root_check.node_id]
                logger.warning(f"Discovery: Found ROOT node on second attempt: {root_check.node_id}")
            else:
                logger.error(f"Discovery: No root node found. Total nodes: {len(hierarchy_dict)}, Node IDs: {list(hierarchy_dict.keys())[:10]}")
                raise HTTPException(
                    status_code=500,
                    detail=f"No root node found in hierarchy for structure_id: {structure_id}. Please check database."
                )
        
        # Check if we should use calculated results (if use_case_id is provided via report_id or structure lookup)
        # For now, we'll check if there's a use case with this structure_id that has calculated results
        from app.models import UseCase, CalculationRun, FactCalculatedResult, FactPnlEntries
        from sqlalchemy import desc
        
        use_case = None
        latest_run = None
        calculated_results_dict = {}
        
        # Try to find a use case - prioritize use_case_id if provided, otherwise lookup by structure_id
        try:
            if use_case_id:
                # CRITICAL: If use_case_id is provided, use it directly (most reliable)
                use_case = db.query(UseCase).filter(
                    UseCase.use_case_id == use_case_id
                ).first()
                if use_case:
                    logger.info(f"Discovery: Using provided use_case_id {use_case_id} - '{use_case.name}' (structure_id: {use_case.atlas_structure_id})")
                    # Verify structure_id matches
                    if use_case.atlas_structure_id != structure_id:
                        logger.warning(f"Discovery: use_case_id structure_id mismatch! use_case has '{use_case.atlas_structure_id}', request has '{structure_id}'")
                else:
                    logger.warning(f"Discovery: use_case_id {use_case_id} not found in database")
                    use_case = None
            else:
                # Fallback: lookup by structure_id (may return wrong use case if multiple share structure_id)
                use_case = db.query(UseCase).filter(
                    UseCase.atlas_structure_id == structure_id
                ).first()
                
                if use_case:
                    logger.info(f"Discovery: Found use case '{use_case.name}' (ID: {use_case.use_case_id}) for structure_id: {structure_id}")
                    # Check if multiple use cases share this structure_id
                    use_case_count = db.query(UseCase).filter(
                        UseCase.atlas_structure_id == structure_id
                    ).count()
                    if use_case_count > 1:
                        logger.warning(f"Discovery: WARNING - {use_case_count} use cases share structure_id '{structure_id}'. Using first one: '{use_case.name}'. Consider passing use_case_id explicitly.")
                else:
                    logger.warning(f"Discovery: No use case found for structure_id: {structure_id}")
            
            # CRITICAL FIX: Check fact_pnl_entries FIRST, only fallback to fact_pnl_gold if zero rows
            # This ensures "Project Sterling" (Dynamic) doesn't get blocked by "Gold" (Static) logic
            facts_df = None
            source_table = None
            debug_info = {}
            
            if use_case:
                # Phase 5.5: Check input_table_name FIRST to route to correct table
                input_table_name = use_case.input_table_name
                facts_df = None
                
                if input_table_name == 'fact_pnl_use_case_3':
                    # Use Case 3: Load from fact_pnl_use_case_3
                    logger.info(f"Discovery: Loading facts from fact_pnl_use_case_3 for use case {use_case.use_case_id}")
                    try:
                        facts_df = load_facts_from_use_case_3(db, use_case_id=use_case.use_case_id)
                        source_table = "fact_pnl_use_case_3"
                        debug_info = {
                            "source_table": source_table,
                            "row_count": len(facts_df),
                            "use_case_id": str(use_case.use_case_id),
                            "use_case_name": use_case.name
                        }
                        logger.info(f"Discovery: Loaded {len(facts_df)} fact rows from fact_pnl_use_case_3")
                        if not facts_df.empty:
                            # Use Case 3 has pnl_daily column
                            total_daily = facts_df['pnl_daily'].sum() if 'pnl_daily' in facts_df.columns else (facts_df['daily_pnl'].sum() if 'daily_pnl' in facts_df.columns else Decimal('0'))
                            logger.info(f"Discovery: Total daily_pnl in loaded facts: {total_daily}")
                        else:
                            logger.warning(f"Discovery: load_facts_from_use_case_3 returned empty DataFrame!")
                            # DO NOT fall through - keep facts_df as empty DataFrame, but don't set to None
                            # This ensures we don't fall back to fact_pnl_gold
                    except Exception as e:
                        logger.error(f"Discovery: Error loading facts from fact_pnl_use_case_3: {e}", exc_info=True)
                        try:
                            db.rollback()
                        except Exception as rollback_error:
                            logger.error(f"Discovery: Failed to rollback: {rollback_error}")
                        # Set to empty DataFrame instead of None to prevent fallback
                        import pandas as pd
                        facts_df = pd.DataFrame()
                        source_table = "fact_pnl_use_case_3"
                        debug_info = {
                            "source_table": source_table,
                            "row_count": 0,
                            "use_case_id": str(use_case.use_case_id),
                            "use_case_name": use_case.name,
                            "error": str(e)
                        }
                
                # MANDATORY: Check fact_pnl_entries if no custom table was set OR if custom table check failed
                # CRITICAL: For Use Case 3, if we already loaded from fact_pnl_use_case_3, DO NOT fall back
                if input_table_name != 'fact_pnl_use_case_3' and (facts_df is None or (facts_df.empty if facts_df is not None else True)):
                    entries_count = db.query(FactPnlEntries).filter(
                        FactPnlEntries.use_case_id == use_case.use_case_id
                    ).count()
                    
                    logger.info(f"Discovery: fact_pnl_entries count for use_case_id {use_case.use_case_id}: {entries_count}")
                    
                    if entries_count > 0:
                        # Use fact_pnl_entries (Project Sterling and similar)
                        # CRITICAL: Use fact_service with strict use_case_id filtering
                        logger.info(f"Discovery: Loading facts from fact_pnl_entries for use case {use_case.use_case_id} ({entries_count} rows)")
                        try:
                            facts_df = load_facts_for_use_case(db, use_case_id=use_case.use_case_id)
                            source_table = "fact_pnl_entries"
                            debug_info = {
                                "source_table": source_table,
                                "row_count": len(facts_df),
                                "use_case_id": str(use_case.use_case_id),
                                "use_case_name": use_case.name
                            }
                            logger.info(f"Discovery: Loaded {len(facts_df)} fact rows from fact_pnl_entries via fact_service")
                            
                            # Verification: Check total P&L
                            if not facts_df.empty:
                                total_daily = facts_df['daily_pnl'].sum()
                                logger.info(f"Discovery: Total daily_pnl in loaded facts: {total_daily}")
                                # Also check if we should filter by category_code from hierarchy
                                if 'category_code' in facts_df.columns:
                                    unique_categories = facts_df['category_code'].unique()[:10]
                                    logger.info(f"Discovery: Sample category_codes in loaded facts: {list(unique_categories)}")
                        except Exception as e:
                            logger.error(f"Discovery: Error loading facts via fact_service: {e}", exc_info=True)
                            try:
                                db.rollback()
                            except Exception as rollback_error:
                                logger.error(f"Discovery: Failed to rollback: {rollback_error}")
                            # Fallback to old method (should not happen, but for safety)
                            logger.warning(f"Discovery: Falling back to load_facts_from_entries")
                            facts_df = load_facts_from_entries(db, use_case_id=use_case.use_case_id)
                            source_table = "fact_pnl_entries"
                            debug_info = {
                                "source_table": source_table,
                                "row_count": len(facts_df),
                                "use_case_id": str(use_case.use_case_id),
                                "use_case_name": use_case.name,
                                "fallback": True
                            }
                else:
                    # ONLY fall back to fact_pnl_gold if fact_pnl_entries returns zero rows
                    logger.info(f"Discovery: fact_pnl_entries returned zero rows, falling back to fact_pnl_gold")
                    # Get leaf node IDs (cc_ids) from the hierarchy for this structure
                    leaf_cc_ids = [node.node_id for node in hierarchy_dict.values() if node.is_leaf]
                    logger.info(f"Discovery: Found {len(leaf_cc_ids)} leaf nodes in hierarchy. Sample: {leaf_cc_ids[:5]}")
                    if leaf_cc_ids:
                        logger.info(f"Discovery: Filtering fact_pnl_gold by {len(leaf_cc_ids)} leaf cc_ids")
                        try:
                            facts_df = load_facts_gold_for_structure(db, structure_id=structure_id, leaf_cc_ids=leaf_cc_ids)
                            source_table = "fact_pnl_gold"
                            debug_info = {
                                "source_table": source_table,
                                "row_count": len(facts_df),
                                "use_case_id": str(use_case.use_case_id),
                                "use_case_name": use_case.name,
                                "filtered_by_cc_ids": True,
                                "leaf_cc_ids_count": len(leaf_cc_ids)
                            }
                            logger.info(f"Discovery: Loaded {len(facts_df)} fact rows from fact_pnl_gold via fact_service")
                            if not facts_df.empty:
                                total_daily = facts_df['daily_pnl'].sum()
                                logger.info(f"Discovery: Total daily_pnl in loaded facts: {total_daily}")
                        except Exception as e:
                            logger.error(f"Discovery: Error loading facts_gold via fact_service: {e}", exc_info=True)
                            try:
                                db.rollback()
                            except Exception as rollback_error:
                                logger.error(f"Discovery: Failed to rollback: {rollback_error}")
                            # Fallback to old method
                            logger.warning(f"Discovery: Falling back to load_facts")
                            facts_df = load_facts(db, filters={'cc_id': leaf_cc_ids})
                            source_table = "fact_pnl_gold"
                            debug_info = {
                                "source_table": source_table,
                                "row_count": len(facts_df),
                                "use_case_id": str(use_case.use_case_id),
                                "use_case_name": use_case.name,
                                "fallback": True
                            }
                    else:
                        logger.warning(f"Discovery: No leaf nodes found in hierarchy, loading all fact_pnl_gold")
                        try:
                            facts_df = load_facts_gold_for_structure(db, structure_id=structure_id, leaf_cc_ids=[])
                            source_table = "fact_pnl_gold"
                            debug_info = {
                                "source_table": source_table,
                                "row_count": len(facts_df),
                                "use_case_id": str(use_case.use_case_id),
                                "use_case_name": use_case.name,
                                "unfiltered": True
                            }
                        except Exception as e:
                            logger.error(f"Discovery: Error loading facts_gold: {e}", exc_info=True)
                            try:
                                db.rollback()
                            except Exception as rollback_error:
                                logger.error(f"Discovery: Failed to rollback: {rollback_error}")
                            facts_df = load_facts(db)
                            source_table = "fact_pnl_gold"
                            debug_info = {
                                "source_table": source_table,
                                "row_count": len(facts_df),
                                "use_case_id": str(use_case.use_case_id),
                                "use_case_name": use_case.name,
                                "fallback": True,
                                "unfiltered": True
                            }
                        logger.info(f"Discovery: Loaded {len(facts_df)} fact rows from fact_pnl_gold (unfiltered)")
            else:
                # No use case found - use fact_pnl_gold as default
                # CRITICAL: Still filter by hierarchy leaf nodes to avoid cross-use-case contamination
                logger.info(f"Discovery: No use case found for structure_id {structure_id}, using fact_pnl_gold")
                leaf_cc_ids = [node.node_id for node in hierarchy_dict.values() if node.is_leaf]
                logger.info(f"Discovery: Found {len(leaf_cc_ids)} leaf nodes in hierarchy. Sample: {leaf_cc_ids[:5]}")
                if leaf_cc_ids:
                    logger.info(f"Discovery: Filtering fact_pnl_gold by {len(leaf_cc_ids)} leaf cc_ids")
                    try:
                        facts_df = load_facts_gold_for_structure(db, structure_id=structure_id, leaf_cc_ids=leaf_cc_ids)
                        source_table = "fact_pnl_gold"
                        debug_info = {
                            "source_table": source_table,
                            "row_count": len(facts_df),
                            "use_case_id": None,
                            "structure_id": structure_id,
                            "filtered_by_cc_ids": True,
                            "leaf_cc_ids_count": len(leaf_cc_ids)
                        }
                        logger.info(f"Discovery: Loaded {len(facts_df)} fact rows from fact_pnl_gold via fact_service")
                    except Exception as e:
                        logger.error(f"Discovery: Error loading facts_gold via fact_service: {e}", exc_info=True)
                        try:
                            db.rollback()
                        except Exception as rollback_error:
                            logger.error(f"Discovery: Failed to rollback: {rollback_error}")
                        facts_df = load_facts(db, filters={'cc_id': leaf_cc_ids})
                        source_table = "fact_pnl_gold"
                        debug_info = {
                            "source_table": source_table,
                            "row_count": len(facts_df),
                            "use_case_id": None,
                            "structure_id": structure_id,
                            "fallback": True
                        }
                else:
                    logger.warning(f"Discovery: No leaf nodes found in hierarchy, loading all fact_pnl_gold")
                    try:
                        facts_df = load_facts_gold_for_structure(db, structure_id=structure_id, leaf_cc_ids=[])
                        source_table = "fact_pnl_gold"
                        debug_info = {
                            "source_table": source_table,
                            "row_count": len(facts_df),
                            "use_case_id": None,
                            "structure_id": structure_id,
                            "unfiltered": True
                        }
                    except Exception as e:
                        logger.error(f"Discovery: Error loading facts_gold: {e}", exc_info=True)
                        try:
                            db.rollback()
                        except Exception as rollback_error:
                            logger.error(f"Discovery: Failed to rollback: {rollback_error}")
                        facts_df = load_facts(db)
                        source_table = "fact_pnl_gold"
                        debug_info = {
                            "source_table": source_table,
                            "row_count": len(facts_df),
                            "use_case_id": None,
                            "structure_id": structure_id,
                            "fallback": True,
                            "unfiltered": True
                        }
                    logger.info(f"Discovery: Loaded {len(facts_df)} fact rows from fact_pnl_gold (unfiltered)")
            
            # Ensure facts_df is initialized
            if facts_df is None:
                logger.warning(f"Discovery: facts_df is None, initializing empty DataFrame")
                import pandas as pd
                facts_df = pd.DataFrame()
                source_table = "none"
                debug_info = {
                    "source_table": source_table,
                    "row_count": 0,
                    "use_case_id": str(use_case.use_case_id) if use_case else None,
                    "error": "facts_df was None"
                }
            
            if use_case:
                # Check for latest calculation run
                latest_run = db.query(CalculationRun).filter(
                    CalculationRun.use_case_id == use_case.use_case_id
                ).order_by(desc(CalculationRun.executed_at)).first()
                
                if latest_run:
                    # Load calculated results for this run
                    calculated_results = db.query(FactCalculatedResult).filter(
                        (FactCalculatedResult.calculation_run_id == latest_run.calculation_run_id) |
                        (FactCalculatedResult.run_id == latest_run.calculation_run_id)
                    ).all()
                    
                    # Build dictionary: node_id -> {daily, mtd, ytd} from measure_vector
                    # measure_vector uses keys: 'daily', 'mtd' (or 'wtd'), 'ytd'
                    for result in calculated_results:
                        try:
                            measure_vector = result.measure_vector or {}
                            # Handle both 'mtd' and 'wtd' keys (wtd is used in fact_pnl_entries)
                            mtd_value = measure_vector.get('mtd') or measure_vector.get('wtd') or 0
                            calculated_results_dict[result.node_id] = {
                                'daily': Decimal(str(measure_vector.get('daily', 0))),
                                'mtd': Decimal(str(mtd_value)),
                                'ytd': Decimal(str(measure_vector.get('ytd', 0))),
                            }
                        except Exception as e:
                            logger.warning(f"Discovery: Error processing calculated result for node {result.node_id}: {e}")
                            continue
                    
                    if calculated_results_dict:
                        logger.info(f"Discovery: Using calculated results from run {latest_run.calculation_run_id} ({len(calculated_results_dict)} nodes)")
        except Exception as e:
            logger.warning(f"Discovery: Error checking for calculated results, will use natural rollups: {e}")
            calculated_results_dict = {}
        
        # If we have calculated results, use them; otherwise calculate natural rollups
        try:
            if calculated_results_dict and len(calculated_results_dict) > 0:
                # Use calculated results, but aggregate parent nodes bottom-up
                natural_results = {}
                
                # First, populate leaf nodes from calculated results
                for node_id in leaf_nodes:
                    if node_id in calculated_results_dict:
                        natural_results[node_id] = calculated_results_dict[node_id]
                    else:
                        natural_results[node_id] = {
                            'daily': Decimal('0'),
                            'mtd': Decimal('0'),
                            'ytd': Decimal('0'),
                        }
                
                # Then aggregate parent nodes bottom-up
                if hierarchy_dict:
                    try:
                        max_depth = max(node.depth for node in hierarchy_dict.values())
                    except (ValueError, AttributeError):
                        # Fallback if depth calculation fails
                        max_depth = 0
                        logger.warning("Discovery: Failed to calculate max_depth, using 0")
                    
                    for depth in range(max_depth, -1, -1):
                        for node_id, node in hierarchy_dict.items():
                            if node.depth == depth and not node.is_leaf:
                                # CRITICAL: Skip ROOT node(s) - they will be overridden by unified_pnl_service
                                if node_id in root_nodes:
                                    logger.debug(f"Discovery: Skipping bottom-up aggregation for ROOT node {node_id} (will use unified_pnl_service)")
                                    continue
                                
                                children = children_dict.get(node_id, [])
                                if children:
                                    natural_results[node_id] = {
                                        'daily': sum(natural_results.get(child_id, {}).get('daily', Decimal('0')) for child_id in children),
                                        'mtd': sum(natural_results.get(child_id, {}).get('mtd', Decimal('0')) for child_id in children),
                                        'ytd': sum(natural_results.get(child_id, {}).get('ytd', Decimal('0')) for child_id in children),
                                    }
                                elif node_id in calculated_results_dict:
                                    # Parent node with calculated result but no children in hierarchy
                                    natural_results[node_id] = calculated_results_dict[node_id]
                                else:
                                    natural_results[node_id] = {
                                        'daily': Decimal('0'),
                                        'mtd': Decimal('0'),
                                        'ytd': Decimal('0'),
                                    }
                else:
                    # No hierarchy_dict - use calculated results as-is
                    natural_results = calculated_results_dict
                    logger.warning("Discovery: No hierarchy_dict available, using calculated results directly")
            else:
                # No calculated results - use dual-path rollup logic
                logger.info(f"Discovery: Calculating rollups using dual-path logic")
                
                # Phase 5.6: Use dual-path rollup based on input_table_name
                if use_case and use_case.input_table_name == 'fact_pnl_use_case_3':
                    # Use Case 3: Strategy Path
                    logger.info(f"Discovery: Using Strategy Path rollup for Use Case 3")
                    print(f"[Discovery] Strategy Path Selected for Use Case 3")
                    natural_results = _calculate_strategy_rollup(
                        db, use_case_id, hierarchy_dict, children_dict, leaf_nodes
                    )
                else:
                    # Use Cases 1 & 2: Legacy Path
                    logger.info(f"Discovery: Using Legacy Path rollup for Use Cases 1 & 2")
                    print(f"[Discovery] Legacy Path Selected for Use Cases 1 & 2")
                    if use_case_id:
                        natural_results = _calculate_legacy_rollup(
                            db, use_case_id, hierarchy_dict, children_dict, leaf_nodes
                        )
                    else:
                        # Fallback to old calculate_natural_rollup if no use_case_id
                        logger.warning(f"Discovery: No use_case_id, falling back to calculate_natural_rollup")
                        if facts_df.empty:
                            logger.warning(f"Discovery: facts_df is empty! Cannot calculate natural rollups.")
                            natural_results = {node_id: {'daily': Decimal('0'), 'mtd': Decimal('0'), 'ytd': Decimal('0')} for node_id in hierarchy_dict.keys()}
                        else:
                            natural_results = calculate_natural_rollup(
                                hierarchy_dict, children_dict, leaf_nodes, facts_df
                            )
                
                # Debug: Log total aggregated values
                total_daily = sum(r.get('daily', Decimal('0')) for r in natural_results.values())
                logger.info(f"Discovery: Rollup total daily: {total_daily}")
        except Exception as e:
            # Fallback to natural rollups if calculated results processing fails
            logger.error(f"Discovery: Error processing calculated results, falling back to rollups: {e}", exc_info=True)
            # Try dual-path rollup first
            if use_case and use_case.input_table_name == 'fact_pnl_use_case_3' and use_case_id:
                try:
                    natural_results = _calculate_strategy_rollup(
                        db, use_case_id, hierarchy_dict, children_dict, leaf_nodes
                    )
                except Exception as e2:
                    logger.error(f"Discovery: Strategy rollup failed, falling back to calculate_natural_rollup: {e2}", exc_info=True)
                    natural_results = calculate_natural_rollup(
                        hierarchy_dict, children_dict, leaf_nodes, facts_df
                    )
            elif use_case_id:
                try:
                    natural_results = _calculate_legacy_rollup(
                        db, use_case_id, hierarchy_dict, children_dict, leaf_nodes
                    )
                except Exception as e2:
                    logger.error(f"Discovery: Legacy rollup failed, falling back to calculate_natural_rollup: {e2}", exc_info=True)
                    natural_results = calculate_natural_rollup(
                        hierarchy_dict, children_dict, leaf_nodes, facts_df
                    )
            else:
                # Last resort: use old calculate_natural_rollup
                natural_results = calculate_natural_rollup(
                    hierarchy_dict, children_dict, leaf_nodes, facts_df
                )
        
        # CRITICAL: Get baseline (Original) P&L totals using unified_pnl_service
        # This is the SINGLE SOURCE OF TRUTH for P&L data (Tab 2 and Tab 3)
        baseline_pnl = None
        if use_case_id:
            print(f"\n[API] {'='*70}")
            print(f"[API] Received Request for Use Case: {use_case_id} - Calling get_unified_pnl")
            print(f"[API] {'='*70}")
            try:
                baseline_pnl = get_unified_pnl(db, use_case_id, pnl_date=None, scenario='ACTUAL')
                print(f"[API] get_unified_pnl returned: {baseline_pnl}")
                if '_debug_info' in baseline_pnl:
                    debug_info_from_service = baseline_pnl.pop('_debug_info')
                    print(f"[API] Service Debug Info: {debug_info_from_service}")
                logger.info(f"Discovery: Baseline (Original) P&L from unified_pnl_service for use_case_id {use_case_id}: {baseline_pnl}")
            except Exception as pnl_error:
                print(f"[API] [ERROR] Failed to get baseline P&L: {pnl_error}")
                logger.warning(f"Discovery: Failed to get baseline P&L from unified_pnl_service (non-fatal): {pnl_error}")
        
        # CRITICAL FIX: Override ROOT node(s) with unified_pnl_service total AFTER all aggregations
        # This ensures the root node shows the correct total even if leaf matching or bottom-up aggregation fails
        if use_case_id and baseline_pnl:
            print(f"[API] Overriding ROOT nodes with unified_pnl_service values...")
            print(f"[API] baseline_pnl: {baseline_pnl}")
            print(f"[API] root_nodes: {root_nodes}")
            for root_id in root_nodes:
                if root_id in natural_results:
                    # Override root node with unified service total (this is the SINGLE SOURCE OF TRUTH)
                    old_daily = natural_results[root_id].get('daily', Decimal('0'))
                    new_daily = baseline_pnl['daily_pnl']
                    natural_results[root_id] = {
                        'daily': new_daily,
                        'mtd': baseline_pnl['mtd_pnl'],
                        'ytd': baseline_pnl['ytd_pnl'],
                        'pytd': Decimal('0'),
                    }
                    print(f"[API] ROOT node {root_id}: Overrode {old_daily} -> {new_daily}")
                    logger.info(
                        f"Discovery: Overrode ROOT node {root_id} with unified_pnl_service total. "
                        f"Old: {old_daily}, New: {new_daily}"
                    )
                else:
                    print(f"[API] [WARNING] ROOT node {root_id} not found in natural_results!")
        
        # Build tree structure for ALL root nodes (support multiple roots)
        root_node_trees = []
        for root_id in root_nodes:
            root_node = build_tree_structure(
                hierarchy_dict, children_dict, natural_results, root_id, include_pytd=False, parent_attributes=None, path_dict=path_dict
            )
            root_node_trees.append(root_node)
        
        logger.info(f"Discovery: Built {len(root_node_trees)} root node tree(s)")
        
        # CRITICAL: Verify the ROOT node has the correct unified_pnl_service total
        if use_case_id and baseline_pnl:
            for root_node in root_node_trees:
                root_daily = Decimal(str(root_node.daily_pnl)) if root_node.daily_pnl else Decimal('0')
                expected_daily = baseline_pnl['daily_pnl']
                if abs(root_daily - expected_daily) > Decimal('0.01'):
                    logger.warning(
                        f"Discovery: ROOT node daily_pnl ({root_daily}) doesn't match unified_pnl_service ({expected_daily}). "
                        f"This may indicate a hierarchy aggregation issue."
                    )
        
        # Calculate reconciliation totals: sum of leaf nodes vs fact table sum
        # Wrap in try-except to make it optional if it fails
        # Phase 5.5: Use unified_pnl_service for fact table sum (respects table routing)
        reconciliation_data = None
        try:
            from sqlalchemy import func
            
            # Phase 5.5: Get fact table sum from unified_pnl_service (respects table routing)
            # This ensures reconciliation uses the correct source table
            fact_table_sum = None
            if use_case_id and baseline_pnl:
                # Use the values from unified_pnl_service (already routed to correct table)
                fact_table_sum = {
                    'daily': baseline_pnl['daily_pnl'],
                    'mtd': baseline_pnl['mtd_pnl'],
                    'ytd': baseline_pnl['ytd_pnl']
                }
                print(f"[API] Reconciliation: Using unified_pnl_service values for fact_table_sum: {fact_table_sum}")
            else:
                # Fallback: Query fact_pnl_gold (legacy behavior)
                from app.models import FactPnlGold
                fact_totals = db.query(
                    func.sum(FactPnlGold.daily_pnl).label('daily_total'),
                    func.sum(FactPnlGold.mtd_pnl).label('mtd_total'),
                    func.sum(FactPnlGold.ytd_pnl).label('ytd_total')
                ).first()
                fact_table_sum = {
                    'daily': Decimal(str(fact_totals.daily_total or 0)),
                    'mtd': Decimal(str(fact_totals.mtd_total or 0)),
                    'ytd': Decimal(str(fact_totals.ytd_total or 0))
                }
                print(f"[API] Reconciliation: Using fact_pnl_gold fallback: {fact_table_sum}")
            
            if fact_table_sum:
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
                        'daily': str(fact_table_sum['daily']),
                        'mtd': str(fact_table_sum['mtd']),
                        'ytd': str(fact_table_sum['ytd'])
                    },
                    leaf_nodes_sum={
                        'daily': str(leaf_totals['daily']),
                        'mtd': str(leaf_totals['mtd']),
                        'ytd': str(leaf_totals['ytd'])
                    }
                )
                print(f"[API] Reconciliation data built: fact_table_sum={reconciliation_data.fact_table_sum}, leaf_nodes_sum={reconciliation_data.leaf_nodes_sum}")
        except Exception as e:
            # Log error but don't fail the request
            logger.warning(f"Failed to calculate reconciliation data: {e}")
            reconciliation_data = None
        
        # CRITICAL: Verify reconciliation before returning response
        # Financial Guardrail: If the sum of fact_pnl_entries (Raw) does not match the sum of
        # fact_calculated_results (Adjusted) before rules are applied, log a RECONCILIATION_ERROR.
        if use_case_id:
            try:
                reconciliation_status = verify_reconciliation(db, use_case_id)
                if not reconciliation_status['is_reconciled']:
                    logger.error(
                        f"RECONCILIATION_ERROR in discovery endpoint: Use Case {use_case_id} - "
                        f"Raw Daily: {reconciliation_status['raw_totals']['daily_pnl']}, "
                        f"Adjusted Daily: {reconciliation_status['adjusted_totals']['daily_pnl']}, "
                        f"Difference: {reconciliation_status['differences']['daily']}"
                    )
                else:
                    logger.info(f"Discovery: Reconciliation verified for use_case_id: {use_case_id}")
            except Exception as recon_error:
                logger.warning(f"Discovery: Reconciliation check failed (non-fatal): {recon_error}")
        
        # Build response with ALL root nodes (support multiple roots)
        logger.info(f"Discovery: Returning hierarchy with {len(root_node_trees)} root node(s)")
        logger.debug(f"Discovery: Debug info: {debug_info}")
        
        # Print final response summary for debugging
        print(f"[API] Building response...")
        if root_node_trees:
            first_root = root_node_trees[0]
            print(f"[API] First ROOT node: {first_root.node_name} (ID: {first_root.node_id})")
            print(f"[API] First ROOT daily_pnl: {first_root.daily_pnl}")
            if reconciliation_data:
                print(f"[API] Reconciliation fact_table_sum['daily']: {reconciliation_data.fact_table_sum.get('daily')}")
        
        response = DiscoveryResponse(
            structure_id=structure_id,
            hierarchy=root_node_trees,  # Return all root nodes, not just the first one
            reconciliation=reconciliation_data,
            debug_info=debug_info  # Include debug information for data sanity verification
        )
        logger.info(f"Discovery: Response built successfully, hierarchy has {len(response.hierarchy)} root nodes")
        print(f"[API] Response built and returning. ROOT node daily_pnl should be: {baseline_pnl['daily_pnl'] if baseline_pnl else 'N/A'}")
        print(f"[API] {'='*70}\n")
        return response
    
    except Exception as e:
        # CRITICAL: Rollback session on any error to prevent InFailedSqlTransaction
        try:
            db.rollback()
            logger.error(f"Discovery: Error occurred, rolled back transaction: {e}", exc_info=True)
        except Exception as rollback_error:
            logger.error(f"Discovery: Failed to rollback transaction: {rollback_error}", exc_info=True)
        
        # Re-raise the original exception
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load discovery view: {str(e)}"
        ) from e

