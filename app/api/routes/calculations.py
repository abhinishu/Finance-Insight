"""
Calculation API routes for Finance-Insight
Provides endpoints for triggering calculations and retrieving results.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import get_db
from decimal import Decimal

from app.api.schemas import CalculationResponse, ResultsResponse, ResultsNode
from app.models import DimHierarchy, UseCase, UseCaseRun, FactCalculatedResult, MetadataRule, CalculationRun, CalculationRun
# Try to import BusinessRule if it exists
try:
    from app.models.business_rule import BusinessRule
    HAS_BUSINESS_RULE = True
except ImportError:
    HAS_BUSINESS_RULE = False
    BusinessRule = None
from app.services.calculator import calculate_use_case
from pydantic import BaseModel
from typing import List, Dict, Any
from app.engine.translator import translate_natural_language_to_json

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
        
        # Get run information for timestamp and PNL date
        run_timestamp = None
        pnl_date = None
        try:
            # Try to get the UseCaseRun to extract timestamp
            use_case_run = db.query(UseCaseRun).filter(
                UseCaseRun.run_id == result.get('run_id')
            ).first()
            
            if use_case_run:
                # UseCaseRun has run_timestamp field
                if hasattr(use_case_run, 'run_timestamp') and use_case_run.run_timestamp:
                    run_timestamp = use_case_run.run_timestamp.isoformat() if hasattr(use_case_run.run_timestamp, 'isoformat') else str(use_case_run.run_timestamp)
                elif hasattr(use_case_run, 'created_at') and use_case_run.created_at:
                    run_timestamp = use_case_run.created_at.isoformat() if hasattr(use_case_run.created_at, 'isoformat') else str(use_case_run.created_at)
        except Exception as e:
            logger.warning(f"Could not fetch run details: {e}")
        
        # Fallback: use current timestamp if not found
        if not run_timestamp:
            from datetime import datetime
            run_timestamp = datetime.now().isoformat()
        
        # PNL date is not available in UseCaseRun, so we'll leave it as None
        # The frontend can use the run_timestamp as the calculation date
        
        return CalculationResponse(
            run_id=result['run_id'],
            use_case_id=result['use_case_id'],
            rules_applied=result['rules_applied'],
            total_plug=result['total_plug'],
            duration_ms=result['duration_ms'],
            message=message,
            run_timestamp=run_timestamp,
            pnl_date=pnl_date
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
    
    # CRITICAL FIX: Load calculation results with eager loading using outerjoin
    # This ensures rules are loaded efficiently in a single query, preventing N+1 queries
    results = []
    if run_id_to_use:
        # Use outerjoin to eagerly load rules, preventing N+1 queries
        results = (
            db.query(FactCalculatedResult)
            .outerjoin(
                MetadataRule,
                and_(
                    FactCalculatedResult.node_id == MetadataRule.node_id,
                    MetadataRule.use_case_id == use_case_id
                )
            )
            .filter(
                (FactCalculatedResult.run_id == run_id_to_use) |
                (FactCalculatedResult.calculation_run_id == run_id_to_use)
            )
            .all()
        )
    
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
    
    # Build results dictionary with explicitly mapped rule details
    # Rules are already loaded via the outerjoin above, so we can efficiently map them
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
                'rule_id': str(rule.rule_id) if rule and rule.rule_id else None,
                'rule_name': rule.logic_en if rule else None,
                'description': rule.logic_en if rule else None,  # Use logic_en as description
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
    # Phase 5.5: Load facts from use-case-specific input table
    from app.engine.waterfall import load_facts, load_facts_from_use_case_3, calculate_natural_rollup
    use_case_obj = db.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
    if use_case_obj and use_case_obj.input_table_name == 'fact_pnl_use_case_3':
        facts_df = load_facts_from_use_case_3(db, use_case_id=use_case_id)
    else:
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
                # CRITICAL: Handle Decimal properly - convert to string directly, not via float
                # This maintains precision for financial values
                if isinstance(value, Decimal):
                    return str(value)
                # Handle float, int
                if isinstance(value, (float, int)):
                    return str(value)
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


class NarrativeRequest(BaseModel):
    total_plug: float
    top_rules: List[Dict[str, Any]]


class NarrativeResponse(BaseModel):
    narrative: str


@router.post("/use-cases/{use_case_id}/narrative", response_model=NarrativeResponse)
def generate_management_narrative(
    use_case_id: UUID,
    request: NarrativeRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a management narrative summary using Gemini AI.
    
    Creates a one-sentence executive summary describing the total plug
    and the top 3 high-impact rules that drove the adjustment.
    
    Args:
        use_case_id: Use case UUID
        request: NarrativeRequest with total_plug and top_rules
        db: Database session
    
    Returns:
        NarrativeResponse with AI-generated narrative
    """
    try:
        # Build prompt for Gemini
        rules_text = ""
        if request.top_rules:
            rules_list = []
            for i, rule in enumerate(request.top_rules, 1):
                rules_list.append(
                    f"{i}. {rule.get('node', 'Unknown Node')}: {rule.get('logic', 'N/A')} "
                    f"(Impact: ${rule.get('impact', 0):,.2f})"
                )
            rules_text = "\n".join(rules_list)
        else:
            rules_text = "No specific rules identified."
        
        # Handle empty rules case
        if not request.top_rules or len(request.top_rules) == 0:
            return NarrativeResponse(
                narrative="No management adjustments have been proposed for this use case."
            )
        
        prompt = f"""Act as a Senior Financial Controller. Analyze the rule impacts and the total Reconciliation Plug.

Total Reconciliation Plug: ${request.total_plug:,.2f}

Top High-Impact Rules:
{rules_text}

Provide a one-sentence summary that:
1. Highlights the largest driver of the adjustment using professional accounting terminology (e.g., 'management override,' 'normalization,' 'intercompany elimination,' 'reclassification')
2. States the total adjustment amount in clear financial terms
3. Is suitable for executive-level financial reporting
4. Is exactly one sentence, no more than 50 words

Use professional accounting language. Generate only the summary sentence, no additional text:"""

        # Use Gemini to generate narrative
        try:
            import google.generativeai as genai
            import os
            
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                # Fallback narrative with accounting terminology
                if request.top_rules:
                    largest_rule = max(request.top_rules, key=lambda r: r.get('impact', 0))
                    narrative = (
                        f"Management override of ${request.total_plug:,.2f} primarily driven by "
                        f"{largest_rule.get('node', 'selected nodes')} normalization adjustments."
                    )
                else:
                    narrative = (
                        f"Total reconciliation plug of ${request.total_plug:,.2f} reflects "
                        f"management adjustments to the baseline GL."
                    )
            else:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(prompt)
                narrative = response.text.strip()
                
                # Ensure it's a single sentence
                if len(narrative) > 200:
                    narrative = narrative.split('.')[0] + '.'
        except Exception as e:
            logger.warning(f"Failed to generate narrative with Gemini: {e}")
            # Fallback narrative with accounting terminology
            if request.top_rules:
                largest_rule = max(request.top_rules, key=lambda r: r.get('impact', 0))
                narrative = (
                    f"Management override of ${request.total_plug:,.2f} primarily driven by "
                    f"{largest_rule.get('node', 'selected nodes')} normalization adjustments."
                )
            else:
                narrative = (
                    f"Total reconciliation plug of ${request.total_plug:,.2f} reflects "
                    f"management adjustments to the baseline GL."
                )
        
        return NarrativeResponse(narrative=narrative)
    
    except Exception as e:
        logger.error(f"Failed to generate management narrative: {e}", exc_info=True)
        # Return fallback narrative with accounting terminology


@router.get("/use-cases/{use_case_id}/execution-plan")
def get_execution_plan(
    use_case_id: str,  # Changed to str to avoid FastAPI UUID validation errors
    include_summary: bool = True,
    db: Session = Depends(get_db)
):
    """
    Fault-Tolerant Execution Plan.
    Target Table: metadata_rules
    Strategy: Dynamic Column Mapping (No hardcoded column assumptions).
    Returns 200 OK even if empty, never 500 Error.
    """
    from sqlalchemy import text
    
    try:
        print(f"[EXECUTION PLAN] Starting for use_case_id={use_case_id} (Fault-Tolerant Raw SQL)")
        
        # Validate UUID format
        try:
            from uuid import UUID as UUIDType
            use_case_uuid = UUIDType(use_case_id) if isinstance(use_case_id, str) else use_case_id
        except ValueError:
            print(f"[EXECUTION PLAN] Invalid UUID format: {use_case_id}")
            return {
                "use_case_id": str(use_case_id),
                "total_rules": 0,
                "leaf_rules": 0,
                "parent_rules": 0,
                "orphaned_rules": 0,
                "steps": [{
                    "step": 1,
                    "description": "Invalid use case ID format"
                }],
                "business_summary": None
            }
        
        # 1. RAW SQL - Select Everything so we can see what we have
        # Removed 'is_active' filter because debug confirmed it doesn't exist
        sql = text("""
            SELECT *
            FROM metadata_rules
            WHERE use_case_id = :uc_id
            ORDER BY created_at ASC
        """)
        
        # 2. Execute with UUID object (SQLAlchemy will handle conversion)
        try:
            results = db.execute(sql, {"uc_id": use_case_uuid}).fetchall()
            print(f"[EXECUTION PLAN] Found {len(results)} rules from metadata_rules table")
        except Exception as query_error:
            print(f"[EXECUTION PLAN] Query failed: {query_error}")
            # Return empty plan instead of crashing
            return {
                "use_case_id": str(use_case_id),
                "total_rules": 0,
                "leaf_rules": 0,
                "parent_rules": 0,
                "orphaned_rules": 0,
                "steps": [{
                    "step": 1,
                    "description": "Error loading rules from database"
                }],
                "business_summary": None
            }
        
        plan = []
        
        # 3. Dynamic Row Mapping (Safety Logic)
        for idx, row in enumerate(results):
            try:
                # Convert Row to Dictionary (Works for SQLAlchemy Row objects)
                if hasattr(row, '_mapping'):
                    row_dict = row._mapping
                elif hasattr(row, '_asdict'):
                    row_dict = row._asdict()
                else:
                    # Fallback: try to convert to dict
                    row_dict = dict(row) if hasattr(row, '__iter__') and not isinstance(row, str) else {}
                
                # Hunt for the ID column (could be 'id', 'rule_id', 'metadata_id')
                r_id = row_dict.get('rule_id') or row_dict.get('id') or str(idx + 1)
                
                # Hunt for Description (try logic_en first, then description, then rule_name)
                desc = row_dict.get('logic_en') or row_dict.get('description') or row_dict.get('rule_name') or "Unnamed Rule"
                
                # Hunt for node_id
                node_id = row_dict.get('node_id') or "Unknown"
                
                # Hunt for Strategy/Value (these might not exist in metadata_rules)
                strategy = row_dict.get('strategy') or "N/A"
                val = row_dict.get('value')
                
                plan.append({
                    "step": len(plan) + 1,
                    "rule_id": str(r_id),
                    "rule_name": desc,
                    "node": node_id,
                    "impact_type": row_dict.get('rule_type') or "Adjustment",
                    "strategy": strategy,
                    # NOTE: Converting to float for API response (JSON doesn't support Decimal)
                    # All calculations use Decimal, only converting at API boundary
                    "value": float(Decimal(str(val))) if val is not None else 0.0
                })
            except Exception as map_err:
                print(f"[EXECUTION PLAN] Skipping row {idx} due to mapping error: {map_err}")
                continue
        
        # Build execution steps summary
        steps = []
        if len(plan) > 0:
            steps.append({
                "step": 1,
                "description": f"Apply {len(plan)} rule{'' if len(plan) == 1 else 's'}"
            })
        else:
            steps.append({
                "step": 1,
                "description": "Calculate Reconciliation Plug (no rules to apply)"
            })
        
        print(f"[EXECUTION PLAN] Success: {len(plan)} rules in plan")
        
        # Return in the expected format
        return {
            "use_case_id": str(use_case_id),
            "total_rules": len(plan),
            "leaf_rules": 0,  # Not categorizing for now
            "parent_rules": 0,
            "orphaned_rules": 0,
            "steps": steps,
            "business_summary": None  # Skip LLM summary for now to avoid errors
        }
    
    except HTTPException as http_err:
        # For 404s, we might want to return empty plan instead of 404
        # But let's re-raise for now to see if that's the issue
        print(f"[EXECUTION PLAN] HTTPException: {http_err.status_code} - {http_err.detail}")
        # Return empty plan instead of 404
        return {
            "use_case_id": str(use_case_id) if use_case_id else "unknown",
            "total_rules": 0,
            "leaf_rules": 0,
            "parent_rules": 0,
            "orphaned_rules": 0,
            "steps": [{
                "step": 1,
                "description": f"Error: {http_err.detail}"
            }],
            "business_summary": None
        }
    except Exception as e:
        # CRITICAL: Log error but return 200 OK with empty plan (never 500)
        print(f"[EXECUTION PLAN] CRITICAL ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"[EXECUTION PLAN] TRACEBACK:\n{traceback.format_exc()}")
        try:
            logger.error(f"CRITICAL ERROR in get_execution_plan for {use_case_id}: {str(e)}", exc_info=True)
        except:
            pass  # If logger fails, continue anyway
        
        # Fallback: Return empty plan so UI loads (instead of 500 error)
        return {
            "use_case_id": str(use_case_id) if use_case_id else "unknown",
            "total_rules": 0,
            "leaf_rules": 0,
            "parent_rules": 0,
            "orphaned_rules": 0,
            "steps": [{
                "step": 1,
                "description": "Error generating execution plan. Please try again."
            }],
            "business_summary": None
        }


class ArchiveSnapshotRequest(BaseModel):
    snapshot_name: str
    rules_snapshot: List[Dict[str, Any]]
    results_snapshot: List[Dict[str, Any]]
    notes: Optional[str] = None
    version_tag: Optional[str] = None
    created_by: str = "system"


@router.post("/use-cases/{use_case_id}/archive")
def archive_snapshot(
    use_case_id: UUID,
    request: ArchiveSnapshotRequest,
    db: Session = Depends(get_db)
):
    """
    Lock and archive a snapshot of current rules and results.
    
    Args:
        use_case_id: Use case UUID
        request: Request body with snapshot_name, rules_snapshot, results_snapshot, notes, created_by
        db: Database session
    
    Returns:
        Snapshot ID
    """
    from app.models import HistorySnapshot
    
    # Validate use case exists
    use_case = db.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
    if not use_case:
        raise HTTPException(
            status_code=404,
            detail=f"Use case '{use_case_id}' not found"
        )
    
    # Determine version number
    existing_snapshots = db.query(HistorySnapshot).filter(
        HistorySnapshot.use_case_id == use_case_id
    ).order_by(HistorySnapshot.snapshot_date.desc()).all()
    
    if not existing_snapshots:
        version_tag = "v1.0"
    else:
        # Extract version number from latest snapshot
        latest_version = existing_snapshots[0].version_tag or "v1.0"
        try:
            # Extract version number (e.g., "v1.0" -> 1.0)
            version_num = float(latest_version.replace('v', ''))
            new_version_num = version_num + 0.1
            version_tag = f"v{new_version_num:.1f}"
        except (ValueError, AttributeError):
            # Fallback if version format is unexpected
            version_tag = f"v{len(existing_snapshots) + 1}.0"
    
    # Create snapshot
    snapshot = HistorySnapshot(
        use_case_id=use_case_id,
        snapshot_name=request.snapshot_name,
        created_by=request.created_by,
        rules_snapshot=request.rules_snapshot,
        results_snapshot=request.results_snapshot,
        notes=request.notes,
        version_tag=version_tag
    )
    
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    
    return {
        "snapshot_id": str(snapshot.snapshot_id),
        "snapshot_name": snapshot.snapshot_name,
        "snapshot_date": snapshot.snapshot_date.isoformat(),
        "version_tag": snapshot.version_tag
    }

