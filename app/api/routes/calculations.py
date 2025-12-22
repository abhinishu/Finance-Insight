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
    use_case_id: UUID,
    include_summary: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get execution plan for a use case before running calculation.
    Shows the order of operations: Leaf rules, Parent aggregation, Overrides.
    
    Args:
        use_case_id: Use case UUID
        db: Database session
    
    Returns:
        Execution plan with step-by-step breakdown
    """
    from app.models import MetadataRule, DimHierarchy
    
    # Validate use case exists
    use_case = db.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
    if not use_case:
        raise HTTPException(
            status_code=404,
            detail=f"Use case '{use_case_id}' not found"
        )
    
    # Get all active rules for this use case
    rules = db.query(MetadataRule).filter(
        MetadataRule.use_case_id == use_case_id,
        MetadataRule.is_active == True
    ).all()
    
    # Get hierarchy to determine leaf vs parent nodes
    hierarchy_nodes = db.query(DimHierarchy).filter(
        DimHierarchy.atlas_source == use_case.atlas_structure_id
    ).all()
    
    leaf_node_ids = {node.node_id for node in hierarchy_nodes if node.is_leaf}
    
    # Categorize rules
    leaf_rules = [r for r in rules if r.node_id in leaf_node_ids]
    parent_rules = [r for r in rules if r.node_id not in leaf_node_ids]
    
    # Build execution steps
    steps = []
    if leaf_rules:
        steps.append({
            "step": 1,
            "description": f"Apply {len(leaf_rules)} Leaf-node rule{'' if len(leaf_rules) == 1 else 's'}"
        })
    
    # Count parent nodes that will be aggregated
    parent_node_count = len(set(r.node_id for r in parent_rules))
    if parent_node_count > 0:
        steps.append({
            "step": len(steps) + 1,
            "description": f"Aggregate to {parent_node_count} Parent node{'' if parent_node_count == 1 else 's'}"
        })
    
    if parent_rules:
        steps.append({
            "step": len(steps) + 1,
            "description": f"Apply {len(parent_rules)} Regional override{'' if len(parent_rules) == 1 else 's'}"
        })
    
    if not steps:
        steps.append({
            "step": 1,
            "description": "Calculate Reconciliation Plug (no rules to apply)"
        })
    
    # Generate business rules summary using LLM
    business_summary = None
    if include_summary and rules:
        try:
            from app.engine.translator import generate_business_rules_summary
            # Get node names from hierarchy
            node_name_map = {node.node_id: node.node_name for node in hierarchy_nodes}
            rules_data = [
                {
                    "node_id": r.node_id,
                    "node_name": node_name_map.get(r.node_id, r.node_id),
                    "logic_en": r.logic_en,
                    "is_leaf": r.node_id in leaf_node_ids
                }
                for r in rules
            ]
            business_summary = generate_business_rules_summary(rules_data)
        except Exception as e:
            logger.warning(f"Failed to generate business rules summary: {e}")
            business_summary = None
    
    return {
        "use_case_id": str(use_case_id),
        "total_rules": len(rules),
        "leaf_rules": len(leaf_rules),
        "parent_rules": len(parent_rules),
        "steps": steps,
        "business_summary": business_summary
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

