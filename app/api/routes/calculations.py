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
from app.models import DimHierarchy, UseCase, UseCaseRun, FactCalculatedResult, MetadataRule, CalculationRun, CalculationRun
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
    # Try CalculationRun first (new system), then fall back to UseCaseRun (legacy)
    run = None
    run_id_to_use = None
    
    if run_id:
        # Try CalculationRun first
        calc_run = db.query(CalculationRun).filter(
            CalculationRun.use_case_id == use_case_id,
            CalculationRun.id == run_id
        ).first()
        
        if calc_run:
            run = calc_run
            run_id_to_use = calc_run.id
        else:
            # Fall back to UseCaseRun
            use_case_run = db.query(UseCaseRun).filter(
                UseCaseRun.use_case_id == use_case_id,
                UseCaseRun.run_id == run_id
            ).first()
            if use_case_run:
                run = use_case_run
                run_id_to_use = use_case_run.run_id
    else:
        # Get most recent - try CalculationRun first
        calc_run = db.query(CalculationRun).filter(
            CalculationRun.use_case_id == use_case_id
        ).order_by(CalculationRun.executed_at.desc()).first()
        
        if calc_run:
            run = calc_run
            run_id_to_use = calc_run.id
        else:
            # Fall back to UseCaseRun
            use_case_run = db.query(UseCaseRun).filter(
                UseCaseRun.use_case_id == use_case_id
            ).order_by(UseCaseRun.run_timestamp.desc()).first()
            if use_case_run:
                run = use_case_run
                run_id_to_use = use_case_run.run_id
    
    # CRITICAL FIX: If no run found, return empty hierarchy to force frontend to use discovery endpoint
    # The discovery endpoint uses unified_pnl_service which is the single source of truth
    if not run:
        logger.info(f"No calculation runs found for use case '{use_case_id}'. Returning empty hierarchy to force fallback to discovery endpoint (unified_pnl_service).")
        # Return empty hierarchy so frontend falls back to discovery endpoint
        return ResultsResponse(
            run_id="N/A",
            use_case_id=str(use_case_id),
            version_tag="No Run",
            run_timestamp="",
            hierarchy=[]  # Empty hierarchy forces frontend to use discovery endpoint
        )
    
    # Load hierarchy
    from app.engine.waterfall import load_hierarchy
    hierarchy_dict, children_dict, leaf_nodes = load_hierarchy(db, use_case_id)
    
    if not hierarchy_dict:
        raise HTTPException(
            status_code=404,
            detail=f"No hierarchy found for use case '{use_case_id}'"
        )
    
    # Load calculation results - check both run_id (legacy) and calculation_run_id (new)
    # Only query if we have a run_id_to_use
    results = []
    if run_id_to_use:
        results = db.query(FactCalculatedResult).filter(
            (FactCalculatedResult.run_id == run_id_to_use) |
            (FactCalculatedResult.calculation_run_id == run_id_to_use)
        ).all()
    
    # If no results found, it might be because the calculation hasn't saved results yet
    # or the run_id doesn't match. Let's check if we have any results at all for this use case
    if not results and run_id_to_use:
        # Try to find any results for this use case to help debug
        all_results = db.query(FactCalculatedResult).join(
            DimHierarchy, FactCalculatedResult.node_id == DimHierarchy.node_id
        ).filter(
            DimHierarchy.atlas_source == use_case.atlas_structure_id
        ).limit(5).all()
        
        if all_results:
            logger.warning(
                f"Found {len(all_results)} results for structure but none for run {run_id_to_use}. "
                f"Results have run_id={[r.run_id for r in all_results]} and calculation_run_id={[r.calculation_run_id for r in all_results]}"
            )
    
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
    
    # INJECT LIVE BASELINE: Get the TRUE baseline from unified_pnl_service (Tab 2's logic)
    # This ensures Tab 4 "Original P&L" matches Tab 2 exactly, not stale zombie data
    from app.services.unified_pnl_service import get_unified_pnl
    baseline_pnl = None
    try:
        baseline_pnl = get_unified_pnl(db, use_case_id, pnl_date=None, scenario='ACTUAL')
        logger.info(f"calculations: Injected live baseline P&L from unified_pnl_service: {baseline_pnl}")
    except Exception as baseline_error:
        logger.warning(f"calculations: Failed to get baseline from unified_pnl_service (non-fatal): {baseline_error}")
    
    # Recalculate natural values from hierarchy (for accurate comparison)
    # Natural values = sum of facts without rules applied
    from app.engine.waterfall import load_facts, calculate_natural_rollup
    facts_df = load_facts(db)
    natural_results = calculate_natural_rollup(
        hierarchy_dict, children_dict, leaf_nodes, facts_df
    )
    
    # Populate natural values and ensure all nodes have results
    # If no results were found in DB, still return hierarchy with natural values (zero adjusted/plug)
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
            # No result for this node - use natural values, zero adjusted/plug
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
                'adjusted_value': {
                    'daily': str(natural['daily']),  # Use natural as adjusted if no rules
                    'mtd': str(natural['mtd']),
                    'ytd': str(natural['ytd']),
                    'pytd': str(natural['pytd']),
                },
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
    
    # Build tree structure with sanitization
    def build_results_tree(node_id: str) -> ResultsNode:
        """Recursively build results tree with data sanitization."""
        node = hierarchy_dict[node_id]
        result_data = results_dict.get(node_id, {
            'natural_value': {'daily': '0', 'mtd': '0', 'ytd': '0', 'pytd': '0'},
            'adjusted_value': {'daily': '0', 'mtd': '0', 'ytd': '0', 'pytd': '0'},
            'plug': {'daily': '0', 'mtd': '0', 'ytd': '0', 'pytd': '0'},
            'is_override': False,
            'is_reconciled': True,
            'rule': None,
        })
        
        # SANITIZATION BLOCK: Force all values to proper types to prevent serialization errors
        def sanitize_value(value, default='0'):
            """Convert value to string, handling Decimal, float, int, None."""
            if value is None:
                return default
            try:
                # Handle Decimal, float, int
                if isinstance(value, (Decimal, float, int)):
                    return str(float(value))
                return str(value)
            except (ValueError, TypeError):
                return default
        
        def sanitize_dict(d: dict, default='0') -> dict:
            """Sanitize a dictionary of values."""
            return {
                'daily': sanitize_value(d.get('daily'), default),
                'mtd': sanitize_value(d.get('mtd', d.get('wtd')), default),  # Handle both mtd and wtd
                'ytd': sanitize_value(d.get('ytd'), default),
                'pytd': sanitize_value(d.get('pytd'), default),
            }
        
        # Sanitize all value dictionaries
        natural_value = sanitize_dict(result_data.get('natural_value', {}))
        adjusted_value = sanitize_dict(result_data.get('adjusted_value', {}))
        plug = sanitize_dict(result_data.get('plug', {}))
        
        # Sanitize rule data
        rule_data = result_data.get('rule')
        sanitized_rule = None
        if rule_data:
            sanitized_rule = {
                'rule_id': int(rule_data['rule_id']) if rule_data.get('rule_id') is not None else None,
                'logic_en': str(rule_data['logic_en']) if rule_data.get('logic_en') else None,
                'sql_where': str(rule_data['sql_where']) if rule_data.get('sql_where') else None,
            }
        
        # Get path
        current_path = path_dict.get(node_id, [str(node.node_name) if node.node_name else 'Unknown'])
        
        # Build children
        children = []
        for child_id in children_dict.get(node_id, []):
            children.append(build_results_tree(child_id))
        
        return ResultsNode(
            node_id=str(node.node_id),
            node_name=str(node.node_name) if node.node_name else "Unknown",
            parent_node_id=str(node.parent_node_id) if node.parent_node_id else None,
            depth=int(node.depth) if node.depth is not None else 0,
            is_leaf=bool(node.is_leaf),
            natural_value=natural_value,
            adjusted_value=adjusted_value,
            plug=plug,
            is_override=bool(result_data.get('is_override', False)),
            is_reconciled=bool(result_data.get('is_reconciled', True)),
            rule=sanitized_rule,
            path=[str(p) for p in current_path] if current_path else [],
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
    
    # INJECT LIVE BASELINE: Overwrite root node's natural_value (Original P&L) with live baseline
    # This ensures Tab 4 "Original P&L" matches Tab 2 exactly ($2.5M and $4.9M)
    if baseline_pnl and root_node:
        # Overwrite natural_value (Original P&L) with live baseline
        root_node.natural_value = {
            'daily': str(baseline_pnl['daily_pnl']),
            'mtd': str(baseline_pnl['mtd_pnl']),
            'ytd': str(baseline_pnl['ytd_pnl']),
            'pytd': '0'  # Not available in baseline
        }
        
        # Recalculate the Plug to be accurate: Adjusted - Original
        # Plug = Natural (Original) - Adjusted
        adjusted_daily = Decimal(str(root_node.adjusted_value.get('daily', '0')))
        original_daily = baseline_pnl['daily_pnl']
        plug_daily = original_daily - adjusted_daily
        
        adjusted_mtd = Decimal(str(root_node.adjusted_value.get('mtd', '0')))
        original_mtd = baseline_pnl['mtd_pnl']
        plug_mtd = original_mtd - adjusted_mtd
        
        adjusted_ytd = Decimal(str(root_node.adjusted_value.get('ytd', '0')))
        original_ytd = baseline_pnl['ytd_pnl']
        plug_ytd = original_ytd - adjusted_ytd
        
        root_node.plug = {
            'daily': str(plug_daily),
            'mtd': str(plug_mtd),
            'ytd': str(plug_ytd),
            'pytd': '0'
        }
        
        logger.info(
            f"calculations: Injected live baseline for root node '{root_node.node_name}'. "
            f"Original Daily: {original_daily}, Adjusted Daily: {adjusted_daily}, Plug: {plug_daily}"
        )
    
    # CRITICAL: Ensure root_node is a pure Pydantic model (not SQLAlchemy object)
    # The build_results_tree function already returns ResultsNode (Pydantic), which FastAPI serializes correctly
    # This extra check ensures all nested values are pure Python types (not Decimal, etc.)
    if root_node:
        try:
            # Pydantic v2 uses model_dump(), v1 uses dict()
            # FastAPI will handle serialization, but we ensure no SQLAlchemy objects leak through
            if hasattr(root_node, 'model_dump'):
                # Pydantic v2 - model_dump() returns pure dict
                root_node_dict = root_node.model_dump(mode='python')  # mode='python' converts Decimal to float
            elif hasattr(root_node, 'dict'):
                # Pydantic v1 - dict() returns pure dict
                root_node_dict = root_node.dict()
            else:
                # Fallback: use JSON serialization round-trip
                import json
                root_node_dict = json.loads(root_node.model_dump_json())
            
            # Reconstruct from dict to ensure pure Python types (no Decimal, no SQLAlchemy objects)
            # ResultsNode is already imported at the top of the file, no need to import again
            root_node = ResultsNode(**root_node_dict)
        except Exception as serialization_error:
            logger.warning(f"Serialization check failed (non-fatal): {serialization_error}")
            # Continue with original root_node - FastAPI should still serialize it correctly
    
    # Build response - handle both CalculationRun and UseCaseRun, or no run
    if run:
        if isinstance(run, CalculationRun):
            run_id_str = str(run.id)
            version_tag = run.run_name or "N/A"
            run_timestamp = run.executed_at
        else:
            run_id_str = str(run.run_id)
            version_tag = getattr(run, 'version_tag', 'N/A')
            run_timestamp = getattr(run, 'run_timestamp', None)
    else:
        # No run found - use placeholder values
        run_id_str = "N/A"
        version_tag = "No Run"
        run_timestamp = None
    
    # Calculate is_outdated flag with grace period (2 seconds) to handle timestamp precision issues
    is_outdated = False
    if run_timestamp:
        try:
            # Get the most recent rule modification time
            latest_rule = db.query(MetadataRule).filter(
                MetadataRule.use_case_id == use_case_id
            ).order_by(MetadataRule.last_modified_at.desc()).first()
            
            if latest_rule and latest_rule.last_modified_at:
                # Fix for Timestamp Race Condition
                # If run_time is within 2 seconds of rule_update_time, consider it VALID.
                from datetime import datetime, timezone
                
                # Ensure both timestamps are timezone-aware for comparison
                if run_timestamp.tzinfo is None:
                    run_timestamp = run_timestamp.replace(tzinfo=timezone.utc)
                if latest_rule.last_modified_at.tzinfo is None:
                    rule_time = latest_rule.last_modified_at.replace(tzinfo=timezone.utc)
                else:
                    rule_time = latest_rule.last_modified_at
                
                time_diff = (rule_time - run_timestamp).total_seconds()
                
                if rule_time > run_timestamp:
                    # Rule was modified after calculation
                    if abs(time_diff) < 2.0:
                        # Close enough (Database precision jitter) - consider it VALID
                        is_outdated = False
                        logger.debug(f"calculations: Grace period applied. Time diff: {time_diff:.3f}s (within 2s threshold)")
                    else:
                        # Rule was modified significantly after calculation
                        is_outdated = True
                        logger.debug(f"calculations: Calculation outdated. Rule modified {time_diff:.3f}s after calculation")
                else:
                    # Rule was modified before or at the same time as calculation
                    is_outdated = False
        except Exception as outdated_error:
            logger.warning(f"calculations: Failed to check outdated status (non-fatal): {outdated_error}")
            is_outdated = False  # Default to not outdated if check fails
    
    # CRITICAL: Session Guard - Remove session to prevent "Transaction Aborted" error
    # This ensures clean session state for the next request
    try:
        db.remove()
        logger.debug(f"calculations: Session removed for use_case_id: {use_case_id}")
    except Exception as remove_error:
        logger.warning(f"calculations: db.remove() failed (non-fatal): {remove_error}")
        # Try rollback as fallback
        try:
            db.rollback()
            logger.debug(f"calculations: Rolled back session as fallback")
        except Exception as rollback_error:
            logger.error(f"calculations: Rollback also failed: {rollback_error}")
    
    return ResultsResponse(
        run_id=run_id_str,
        use_case_id=str(use_case_id),
        version_tag=version_tag,
        run_timestamp=run_timestamp.isoformat() if run_timestamp else "",
        hierarchy=[root_node] if root_node else [],
        is_outdated=is_outdated
    )

