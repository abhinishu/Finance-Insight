"""
Calculation API routes for Finance-Insight
Provides endpoints for triggering calculations and retrieving results.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from decimal import Decimal

from app.api.schemas import CalculationResponse, ResultsResponse, ResultsNode
from app.models import DimHierarchy, UseCase, UseCaseRun, FactCalculatedResult, MetadataRule
from app.services.calculator import calculate_use_case

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["calculations"])


@router.post("/use-cases/{use_case_id}/calculate", response_model=CalculationResponse)
def trigger_calculation(
    use_case_id: UUID,
    version_tag: Optional[str] = None,
    triggered_by: str = "system",
    db: Session = Depends(get_db)
):
    """
    Trigger calculation for a use case.
    
    Executes the three-stage waterfall:
    1. Stage 1 (Leaf Application): Apply rules to leaf nodes
    2. Stage 2 (Waterfall Up): Bottom-up aggregation
    3. Stage 3 (The Plug): Calculate Reconciliation Plug
    
    Args:
        use_case_id: Use case UUID
        version_tag: Optional version tag (e.g., "Nov_Actuals_v1")
        triggered_by: User ID who triggered the calculation
        db: Database session
    
    Returns:
        CalculationResponse with summary
    """
    # Validate use case exists
    use_case = db.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
    if not use_case:
        raise HTTPException(
            status_code=404,
            detail=f"Use case '{use_case_id}' not found"
        )
    
    try:
        # Execute calculation
        result = calculate_use_case(
            use_case_id=use_case_id,
            session=db,
            triggered_by=triggered_by,
            version_tag=version_tag
        )
        
        # Build summary message
        total_plug_daily = result['total_plug']['daily']
        message = (
            f"Calculation complete. {result['rules_applied']} rules applied. "
            f"Total Plug: ${total_plug_daily}"
        )
        
        return CalculationResponse(
            run_id=result['run_id'],
            use_case_id=result['use_case_id'],
            rules_applied=result['rules_applied'],
            total_plug=result['total_plug'],
            duration_ms=result['duration_ms'],
            message=message
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Calculation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")


@router.get("/use-cases/{use_case_id}/results", response_model=ResultsResponse)
def get_calculation_results(
    use_case_id: UUID,
    run_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """
    Get calculation results for a use case.
    
    Returns the full hierarchy tree with:
    - natural_value: Natural GL baseline values
    - adjusted_value: Rule-adjusted values
    - plug: Reconciliation plug (Natural - Adjusted)
    
    If run_id is not provided, returns the most recent run.
    
    Args:
        use_case_id: Use case UUID
        run_id: Optional run ID (defaults to most recent)
        db: Database session
    
    Returns:
        ResultsResponse with hierarchy tree and calculation results
    """
    # Validate use case exists
    use_case = db.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
    if not use_case:
        raise HTTPException(
            status_code=404,
            detail=f"Use case '{use_case_id}' not found"
        )
    
    # Get run (most recent if not specified)
    if run_id:
        run = db.query(UseCaseRun).filter(
            UseCaseRun.use_case_id == use_case_id,
            UseCaseRun.run_id == run_id
        ).first()
    else:
        run = db.query(UseCaseRun).filter(
            UseCaseRun.use_case_id == use_case_id
        ).order_by(UseCaseRun.run_timestamp.desc()).first()
    
    if not run:
        raise HTTPException(
            status_code=404,
            detail=f"No calculation runs found for use case '{use_case_id}'"
        )
    
    # Load hierarchy
    from app.engine.waterfall import load_hierarchy
    hierarchy_dict, children_dict, leaf_nodes = load_hierarchy(db, use_case_id)
    
    if not hierarchy_dict:
        raise HTTPException(
            status_code=404,
            detail=f"No hierarchy found for use case '{use_case_id}'"
        )
    
    # Load calculation results
    results = db.query(FactCalculatedResult).filter(
        FactCalculatedResult.run_id == run.run_id
    ).all()
    
    # Load rules for this use case to get rule details
    rules = db.query(MetadataRule).filter(
        MetadataRule.use_case_id == use_case_id
    ).all()
    rules_dict = {rule.node_id: rule for rule in rules}
    
    # Build results dictionary
    results_dict = {}
    for result in results:
        rule = rules_dict.get(result.node_id)
        results_dict[result.node_id] = {
            'natural_value': {},  # Will be calculated from hierarchy
            'adjusted_value': result.measure_vector or {},
            'plug': result.plug_vector or {},
            'is_override': result.is_override,
            'is_reconciled': result.is_reconciled,
            'rule': {
                'rule_id': rule.rule_id if rule else None,
                'logic_en': rule.logic_en if rule else None,
                'sql_where': rule.sql_where if rule else None,
            } if rule else None,
        }
    
    # Recalculate natural values from hierarchy (for accurate comparison)
    # Natural values = sum of facts without rules applied
    from app.engine.waterfall import load_facts, calculate_natural_rollup
    facts_df = load_facts(db)
    natural_results = calculate_natural_rollup(
        hierarchy_dict, children_dict, leaf_nodes, facts_df
    )
    
    # Populate natural values and ensure all nodes have results
    for node_id in hierarchy_dict.keys():
        if node_id in results_dict:
            # Natural value from recalculation
            natural = natural_results.get(node_id, {
                'daily': Decimal('0'),
                'mtd': Decimal('0'),
                'ytd': Decimal('0'),
                'pytd': Decimal('0'),
            })
            results_dict[node_id]['natural_value'] = {
                'daily': str(natural['daily']),
                'mtd': str(natural['mtd']),
                'ytd': str(natural['ytd']),
                'pytd': str(natural['pytd']),
            }
        else:
            # No result for this node - set defaults
            natural = natural_results.get(node_id, {
                'daily': Decimal('0'),
                'mtd': Decimal('0'),
                'ytd': Decimal('0'),
                'pytd': Decimal('0'),
            })
            results_dict[node_id] = {
                'natural_value': {
                    'daily': str(natural['daily']),
                    'mtd': str(natural['mtd']),
                    'ytd': str(natural['ytd']),
                    'pytd': str(natural['pytd']),
                },
                'adjusted_value': {'daily': '0', 'mtd': '0', 'ytd': '0', 'pytd': '0'},
                'plug': {'daily': '0', 'mtd': '0', 'ytd': '0', 'pytd': '0'},
                'is_override': False,
                'is_reconciled': True,
            }
    
    # Build path arrays using SQL CTE (same as discovery endpoint)
    from sqlalchemy import text
    path_dict = {}
    try:
        path_query = text("""
            WITH RECURSIVE node_paths AS (
                -- Base case: root nodes
                SELECT 
                    node_id,
                    node_name,
                    parent_node_id,
                    ARRAY[node_name] as path
                FROM dim_hierarchy
                WHERE parent_node_id IS NULL
                    AND atlas_source = :structure_id
                
                UNION ALL
                
                -- Recursive case: children
                SELECT 
                    h.node_id,
                    h.node_name,
                    h.parent_node_id,
                    np.path || h.node_name
                FROM dim_hierarchy h
                INNER JOIN node_paths np ON h.parent_node_id = np.node_id
                WHERE h.atlas_source = :structure_id
            )
            SELECT node_id, path FROM node_paths
        """)
        
        path_results = db.execute(
            path_query,
            {"structure_id": use_case.atlas_structure_id}
        ).fetchall()
        
        path_dict = {row[0]: row[1] for row in path_results}
    except Exception as e:
        logger.warning(f"Failed to build path arrays: {e}")
        path_dict = {}
    
    # Build tree structure
    def build_results_tree(node_id: str) -> ResultsNode:
        """Recursively build results tree."""
        node = hierarchy_dict[node_id]
        result_data = results_dict.get(node_id, {
            'natural_value': {'daily': '0', 'mtd': '0', 'ytd': '0', 'pytd': '0'},
            'adjusted_value': {'daily': '0', 'mtd': '0', 'ytd': '0', 'pytd': '0'},
            'plug': {'daily': '0', 'mtd': '0', 'ytd': '0', 'pytd': '0'},
            'is_override': False,
            'is_reconciled': True,
            'rule': None,
        })
        
        # Get path
        current_path = path_dict.get(node_id, [node.node_name])
        
        # Build children
        children = []
        for child_id in children_dict.get(node_id, []):
            children.append(build_results_tree(child_id))
        
        return ResultsNode(
            node_id=node.node_id,
            node_name=node.node_name,
            parent_node_id=node.parent_node_id,
            depth=node.depth,
            is_leaf=node.is_leaf,
            natural_value=result_data['natural_value'],
            adjusted_value=result_data['adjusted_value'],
            plug=result_data['plug'],
            is_override=result_data['is_override'],
            is_reconciled=result_data['is_reconciled'],
            rule=result_data.get('rule'),
            path=current_path,
            children=children
        )
    
    # Find root node
    root_nodes = [
        node_id for node_id, node in hierarchy_dict.items()
        if node.parent_node_id is None
    ]
    
    if not root_nodes:
        raise HTTPException(
            status_code=500,
            detail="No root node found in hierarchy"
        )
    
    root_id = root_nodes[0]
    root_node = build_results_tree(root_id)
    
    return ResultsResponse(
        run_id=str(run.run_id),
        use_case_id=str(use_case_id),
        version_tag=run.version_tag,
        run_timestamp=run.run_timestamp.isoformat(),
        hierarchy=[root_node]
    )

