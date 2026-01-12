"""
Rules API routes for Finance-Insight Phase 2
Provides endpoints for creating and managing business rules.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.schemas import (
    BulkRuleCreateRequest,
    BulkRuleDeleteRequest,
    BulkRuleResponse,
    RuleCreate,
    RuleGenAIRequest,
    RuleGenAIResponse,
    RulePreviewRequest,
    RulePreviewResponse,
    RuleResponse,
    RuleStackResponse,
)
from app.engine.translator import translate_rule
from app.models import DimHierarchy, MetadataRule, UseCase
from app.services.rules import create_manual_rule, preview_rule_impact

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["rules"])


@router.post("/use-cases/{use_case_id}/rules", response_model=RuleResponse)
def create_rule(
    use_case_id: UUID,
    rule_data: RuleCreate,
    db: Session = Depends(get_db)
):
    """
    Create a rule for a use case.
    
    Supports two modes:
    1. Manual: Provide 'conditions' (list of RuleCondition objects)
    2. GenAI: Provide 'logic_en' (natural language) - will be implemented later
    
    Args:
        use_case_id: Use case UUID
        rule_data: RuleCreate object
        db: Database session
    
    Returns:
        RuleResponse with created rule details
    """
    try:
        # Determine mode
        if rule_data.conditions:
            # Manual mode
            logger.info(f"Creating manual rule for use case {use_case_id}, node {rule_data.node_id}")
            rule = create_manual_rule(use_case_id, rule_data, db)
        elif rule_data.logic_en:
            # GenAI mode - translate and create rule
            logger.info(f"Creating GenAI rule for use case {use_case_id}, node {rule_data.node_id}")
            
            # Get use case to determine table name for column mapping
            use_case = db.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
            if not use_case:
                raise HTTPException(
                    status_code=404,
                    detail=f"Use case '{use_case_id}' not found"
                )
            
            table_name = use_case.input_table_name or 'fact_pnl_gold'
            
            # Translate natural language to JSON and SQL
            try:
                predicate_json, sql_where, errors, translation_successful = translate_rule(
                    rule_data.logic_en,
                    use_cache=True,
                    table_name=table_name
                )
            except Exception as e:
                # Handle quota errors with user-friendly message
                error_str = str(e).lower()
                if "quota" in error_str or "429" in error_str:
                    raise HTTPException(
                        status_code=429,
                        detail="Gemini API quota exceeded. Please wait a few minutes and try again."
                    )
                raise HTTPException(
                    status_code=500,
                    detail=f"Translation error: {str(e)}"
                )
            
            if not translation_successful:
                raise HTTPException(
                    status_code=400,
                    detail=f"Translation failed: {'; '.join(errors)}"
                )
            
            # Create rule with translated data
            # Check if rule already exists for this node
            existing_rule = db.query(MetadataRule).filter(
                MetadataRule.use_case_id == use_case_id,
                MetadataRule.node_id == rule_data.node_id
            ).first()
            
            if existing_rule:
                # Update existing rule
                logger.info(f"Updating existing rule {existing_rule.rule_id} for node {rule_data.node_id}")
                existing_rule.predicate_json = predicate_json
                existing_rule.sql_where = sql_where
                existing_rule.logic_en = rule_data.logic_en
                existing_rule.last_modified_by = rule_data.last_modified_by
                db.commit()
                db.refresh(existing_rule)
                rule = existing_rule
            else:
                # Create new rule
                logger.info(f"Creating new GenAI rule for node {rule_data.node_id}")
                new_rule = MetadataRule(
                    use_case_id=use_case_id,
                    node_id=rule_data.node_id,
                    predicate_json=predicate_json,
                    sql_where=sql_where,
                    logic_en=rule_data.logic_en,
                    last_modified_by=rule_data.last_modified_by
                )
                db.add(new_rule)
                db.commit()
                db.refresh(new_rule)
                rule = new_rule
        elif rule_data.rule_type == 'NODE_ARITHMETIC' and rule_data.rule_expression:
            # Phase 5.7: Math rule mode (Type 3)
            logger.info(f"Creating math rule for use case {use_case_id}, node {rule_data.node_id}")
            
            # Check if rule already exists for this node
            existing_rule = db.query(MetadataRule).filter(
                MetadataRule.use_case_id == use_case_id,
                MetadataRule.node_id == rule_data.node_id
            ).first()
            
            if existing_rule:
                # Update existing rule
                logger.info(f"Updating existing rule {existing_rule.rule_id} for node {rule_data.node_id}")
                existing_rule.rule_type = rule_data.rule_type
                existing_rule.rule_expression = rule_data.rule_expression
                existing_rule.rule_dependencies = rule_data.rule_dependencies
                existing_rule.last_modified_by = rule_data.last_modified_by
                # Clear SQL fields for math rules
                existing_rule.sql_where = None
                existing_rule.predicate_json = None
                db.commit()
                db.refresh(existing_rule)
                rule = existing_rule
            else:
                # Create new math rule
                logger.info(f"Creating new math rule for node {rule_data.node_id}")
                new_rule = MetadataRule(
                    use_case_id=use_case_id,
                    node_id=rule_data.node_id,
                    rule_type=rule_data.rule_type,
                    rule_expression=rule_data.rule_expression,
                    rule_dependencies=rule_data.rule_dependencies,
                    last_modified_by=rule_data.last_modified_by
                )
                db.add(new_rule)
                db.commit()
                db.refresh(new_rule)
                rule = new_rule
        elif rule_data.sql_where:
            # Direct SQL mode (advanced, for testing)
            raise HTTPException(
                status_code=501,
                detail="Direct SQL mode not yet implemented. Use 'conditions' for manual rules."
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide either 'conditions' (manual), 'logic_en' (GenAI), 'rule_expression' (math), or 'sql_where' (direct)"
            )
        
        # PHASE 2C FIX 1: Invalidate rules cache after create/update
        from app.services.rules_cache import invalidate_cache
        invalidate_cache(use_case_id)
        logger.info(f"[Rules] Invalidated rules cache for use case {use_case_id} after create/update")
        
        # Get node name for response
        node = db.query(DimHierarchy).filter(DimHierarchy.node_id == rule.node_id).first()
        node_name = node.node_name if node else None
        
        return RuleResponse(
            rule_id=rule.rule_id,
            use_case_id=rule.use_case_id,
            node_id=rule.node_id,
            node_name=node_name,
            logic_en=rule.logic_en if rule.logic_en else None,
            predicate_json=rule.predicate_json if rule.predicate_json else None,
            sql_where=rule.sql_where if rule.sql_where else None,
            last_modified_by=rule.last_modified_by,
            created_at=rule.created_at.isoformat(),
            last_modified_at=rule.last_modified_at.isoformat(),
            # Phase 5.7: Math Engine fields - explicitly map from database model
            rule_type=rule.rule_type if rule.rule_type else None,
            rule_expression=rule.rule_expression if rule.rule_expression else None,
            measure_name=rule.measure_name if rule.measure_name else None,
            rule_dependencies=rule.rule_dependencies if rule.rule_dependencies else None
        )
        
    except ValueError as e:
        logger.error(f"Validation error creating rule: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create rule: {str(e)}")


@router.get("/use-cases/{use_case_id}/rules", response_model=List[RuleResponse])
def list_rules(
    use_case_id: UUID,
    db: Session = Depends(get_db)
):
    """
    List all active rules for a use case.
    
    Args:
        use_case_id: Use case UUID
        db: Database session
    
    Returns:
        List of RuleResponse objects
    """
    # Validate use case exists
    use_case = db.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
    if not use_case:
        raise HTTPException(
            status_code=404,
            detail=f"Use case '{use_case_id}' not found"
        )
    
    # Get all rules for use case
    rules = db.query(MetadataRule).filter(
        MetadataRule.use_case_id == use_case_id
    ).order_by(MetadataRule.created_at.desc()).all()
    
    # Build response with node names
    result = []
    for rule in rules:
        node = db.query(DimHierarchy).filter(DimHierarchy.node_id == rule.node_id).first()
        node_name = node.node_name if node else None
        
        result.append(RuleResponse(
            rule_id=rule.rule_id,
            use_case_id=rule.use_case_id,
            node_id=rule.node_id,
            node_name=node_name,
            logic_en=rule.logic_en if rule.logic_en else None,
            predicate_json=rule.predicate_json if rule.predicate_json else None,
            sql_where=rule.sql_where if rule.sql_where else None,
            last_modified_by=rule.last_modified_by,
            created_at=rule.created_at.isoformat(),
            last_modified_at=rule.last_modified_at.isoformat(),
            # Phase 5.7: Math Engine fields - explicitly map from database model
            rule_type=rule.rule_type if rule.rule_type else None,
            rule_expression=rule.rule_expression if rule.rule_expression else None,
            measure_name=rule.measure_name if rule.measure_name else None,
            rule_dependencies=rule.rule_dependencies if rule.rule_dependencies else None
        ))
    
    return result


@router.post("/rules/preview", response_model=RulePreviewResponse)
def preview_rule(
    request: RulePreviewRequest,
    db: Session = Depends(get_db)
):
    """
    Preview the impact of a rule by counting affected rows.
    
    This endpoint allows users to see how many rows in the appropriate fact table
    would be affected by a SQL WHERE clause before saving the rule.
    
    The table is determined by:
    - If use_case_id is provided: Uses use_case.input_table_name (e.g., 'fact_pnl_use_case_3')
    - Otherwise: Defaults to 'fact_pnl_gold'
    
    Args:
        request: RulePreviewRequest with sql_where and optional use_case_id
        db: Database session
    
    Returns:
        RulePreviewResponse with affected row count and percentage
    """
    try:
        return preview_rule_impact(request.sql_where, db, use_case_id=request.use_case_id)
    except ValueError as e:
        logger.error(f"Validation error previewing rule: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error previewing rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to preview rule: {str(e)}")


@router.post("/use-cases/{use_case_id}/rules/genai", response_model=RuleGenAIResponse)
def translate_genai_rule(
    use_case_id: UUID,
    request: RuleGenAIRequest,
    db: Session = Depends(get_db)
):
    """
    Translate natural language to rule (GenAI mode).
    
    This endpoint:
    1. Calls Gemini 1.5 Pro to translate natural language to JSON predicate
    2. Validates the JSON against fact table schema
    3. Converts JSON to SQL WHERE clause
    4. Returns translation preview (does NOT save to database)
    
    The user must review the translation and call the preview endpoint
    before saving the rule via POST /use-cases/{id}/rules.
    
    Args:
        use_case_id: Use case UUID
        request: RuleGenAIRequest with logic_en (natural language)
        db: Database session (for validation, not used for translation)
    
    Returns:
        RuleGenAIResponse with predicate_json, sql_where, and success status
    """
    # Validate use case exists
    use_case = db.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
    if not use_case:
        raise HTTPException(
            status_code=404,
            detail=f"Use case '{use_case_id}' not found"
        )
    
    # Get table name for column mapping
    table_name = use_case.input_table_name or 'fact_pnl_gold'
    
    try:
        logger.info(f"Translating GenAI rule for use case {use_case_id}: {request.logic_en}")
        
        # Get table name for column mapping
        table_name = use_case.input_table_name or 'fact_pnl_gold'
        
        # Call translator (Stage 1: NL → JSON, Stage 2: Validate, Stage 3: JSON → SQL)
        try:
            predicate_json, sql_where, errors, translation_successful = translate_rule(
                request.logic_en,
                use_cache=True,
                table_name=table_name
            )
        except Exception as e:
            # Handle quota errors with user-friendly message
            error_str = str(e).lower()
            if "quota" in error_str or "429" in error_str:
                return RuleGenAIResponse(
                    node_id=request.node_id,
                    logic_en=request.logic_en,
                    predicate_json=None,
                    sql_where=None,
                    translation_successful=False,
                    errors=["Gemini API quota exceeded. Please wait a few minutes and try again."],
                    preview_available=False
                )
            raise
        
        # Build response
        response = RuleGenAIResponse(
            node_id=request.node_id,
            logic_en=request.logic_en,
            predicate_json=predicate_json,
            sql_where=sql_where,
            translation_successful=translation_successful,
            errors=errors,
            preview_available=translation_successful and sql_where is not None
        )
        
        if translation_successful:
            logger.info(f"Successfully translated rule: {request.logic_en} → {sql_where}")
        else:
            logger.warning(f"Translation failed: {request.logic_en} - Errors: {errors}")
        
        return response
        
    except ValueError as e:
        # Rate limit or validation errors
        logger.error(f"Translation error: {e}")
        return RuleGenAIResponse(
            node_id=request.node_id,
            logic_en=request.logic_en,
            predicate_json=None,
            sql_where=None,
            translation_successful=False,
            errors=[str(e)],
            preview_available=False
        )
    except Exception as e:
        logger.error(f"Unexpected error in GenAI translation: {e}", exc_info=True)
        return RuleGenAIResponse(
            node_id=request.node_id,
            logic_en=request.logic_en,
            predicate_json=None,
            sql_where=None,
            translation_successful=False,
            errors=[f"Unexpected error: {str(e)}"],
            preview_available=False
        )


@router.post("/use-cases/{use_case_id}/rules/bulk", response_model=BulkRuleResponse)
def bulk_create_rules(
    use_case_id: UUID,
    request: BulkRuleCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create or update rules for multiple nodes simultaneously (batch save).
    
    Args:
        use_case_id: Use case UUID
        request: BulkRuleCreateRequest with node_ids and rule configuration
        db: Database session
    
    Returns:
        BulkRuleResponse with success/failure counts and created rules
    """
    try:
        # Validate use case exists
        use_case = db.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
        if not use_case:
            raise HTTPException(
                status_code=404,
                detail=f"Use case '{use_case_id}' not found"
            )
        
        created_rules = []
        errors = []
        success_count = 0
        failed_count = 0
        
        # Process each node
        for node_id in request.node_ids:
            try:
                # Create RuleCreate object for this node
                # Phase 5.7: Include math rule fields if provided
                rule_data = RuleCreate(
                    node_id=node_id,
                    last_modified_by=request.last_modified_by,
                    conditions=request.conditions,
                    logic_en=request.logic_en,
                    rule_type=request.rule_type,
                    rule_expression=request.rule_expression,
                    rule_dependencies=request.rule_dependencies,
                    sql_where=request.sql_where
                )
                
                # Create rule using existing logic
                if rule_data.rule_type == 'NODE_ARITHMETIC' and rule_data.rule_expression:
                    # Phase 5.7: Math rule mode (Type 3)
                    existing_rule = db.query(MetadataRule).filter(
                        MetadataRule.use_case_id == use_case_id,
                        MetadataRule.node_id == node_id
                    ).first()
                    
                    if existing_rule:
                        existing_rule.rule_type = rule_data.rule_type
                        existing_rule.rule_expression = rule_data.rule_expression
                        existing_rule.rule_dependencies = rule_data.rule_dependencies
                        existing_rule.last_modified_by = rule_data.last_modified_by
                        existing_rule.sql_where = None
                        existing_rule.predicate_json = None
                        db.commit()
                        db.refresh(existing_rule)
                        rule = existing_rule
                    else:
                        rule = MetadataRule(
                            use_case_id=use_case_id,
                            node_id=node_id,
                            rule_type=rule_data.rule_type,
                            rule_expression=rule_data.rule_expression,
                            rule_dependencies=rule_data.rule_dependencies,
                            last_modified_by=rule_data.last_modified_by
                        )
                        db.add(rule)
                        db.commit()
                        db.refresh(rule)
                elif rule_data.conditions:
                    rule = create_manual_rule(use_case_id, rule_data, db)
                elif rule_data.logic_en:
                    # Get use case to determine table name for column mapping
                    use_case = db.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
                    if not use_case:
                        errors.append(f"Use case '{use_case_id}' not found")
                        failed_count += 1
                        continue
                    
                    table_name = use_case.input_table_name or 'fact_pnl_gold'
                    
                    # Translate and create
                    predicate_json, sql_where, translation_errors, translation_successful = translate_rule(
                        rule_data.logic_en,
                        use_cache=True,
                        table_name=table_name
                    )
                    
                    if not translation_successful:
                        errors.append(f"Node {node_id}: Translation failed: {'; '.join(translation_errors)}")
                        failed_count += 1
                        continue
                    
                    # Check if rule exists
                    existing_rule = db.query(MetadataRule).filter(
                        MetadataRule.use_case_id == use_case_id,
                        MetadataRule.node_id == node_id
                    ).first()
                    
                    if existing_rule:
                        existing_rule.predicate_json = predicate_json
                        existing_rule.sql_where = sql_where
                        existing_rule.logic_en = rule_data.logic_en
                        existing_rule.last_modified_by = rule_data.last_modified_by
                        db.commit()
                        db.refresh(existing_rule)
                        rule = existing_rule
                    else:
                        rule = MetadataRule(
                            use_case_id=use_case_id,
                            node_id=node_id,
                            predicate_json=predicate_json,
                            sql_where=sql_where,
                            logic_en=rule_data.logic_en,
                            last_modified_by=rule_data.last_modified_by
                        )
                        db.add(rule)
                        db.commit()
                        db.refresh(rule)
                else:
                    errors.append(f"Node {node_id}: Must provide either 'conditions' or 'logic_en'")
                    failed_count += 1
                    continue
                
                # Get node name for response
                node = db.query(DimHierarchy).filter(DimHierarchy.node_id == rule.node_id).first()
                node_name = node.node_name if node else None
                
                created_rules.append(RuleResponse(
                    rule_id=rule.rule_id,
                    use_case_id=rule.use_case_id,
                    node_id=rule.node_id,
                    node_name=node_name,
                    logic_en=rule.logic_en if rule.logic_en else None,
                    predicate_json=rule.predicate_json if rule.predicate_json else None,
                    sql_where=rule.sql_where if rule.sql_where else None,
                    last_modified_by=rule.last_modified_by,
                    created_at=rule.created_at.isoformat(),
                    last_modified_at=rule.last_modified_at.isoformat(),
                    # Phase 5.7: Math Engine fields - explicitly map from database model
                    rule_type=rule.rule_type if rule.rule_type else None,
                    rule_expression=rule.rule_expression if rule.rule_expression else None,
                    measure_name=rule.measure_name if rule.measure_name else None,
                    rule_dependencies=rule.rule_dependencies if rule.rule_dependencies else None
                ))
                success_count += 1
                
            except Exception as e:
                logger.error(f"Error creating rule for node {node_id}: {e}")
                errors.append(f"Node {node_id}: {str(e)}")
                failed_count += 1
        
        # PHASE 2C FIX 1: Invalidate rules cache after bulk create
        from app.services.rules_cache import invalidate_cache
        invalidate_cache(use_case_id)
        logger.info(f"[Rules] Invalidated rules cache for use case {use_case_id} after bulk create")
        
        return BulkRuleResponse(
            success_count=success_count,
            failed_count=failed_count,
            errors=errors,
            created_rules=created_rules
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk rule creation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create bulk rules: {str(e)}")


@router.delete("/use-cases/{use_case_id}/rules/bulk", response_model=BulkRuleResponse)
def bulk_delete_rules(
    use_case_id: UUID,
    request: BulkRuleDeleteRequest,
    db: Session = Depends(get_db)
):
    """
    Delete rules for multiple nodes in one transaction (Clear Rules).
    
    Args:
        use_case_id: Use case UUID
        request: BulkRuleDeleteRequest with node_ids
        db: Database session
    
    Returns:
        BulkRuleResponse with success/failure counts
    """
    try:
        # Validate use case exists
        use_case = db.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
        if not use_case:
            raise HTTPException(
                status_code=404,
                detail=f"Use case '{use_case_id}' not found"
            )
        
        success_count = 0
        failed_count = 0
        errors = []
        
        # Delete rules in one transaction
        try:
            deleted_count = db.query(MetadataRule).filter(
                MetadataRule.use_case_id == use_case_id,
                MetadataRule.node_id.in_(request.node_ids)
            ).delete(synchronize_session=False)
            
            db.commit()
            success_count = deleted_count
            
            # PHASE 2C FIX 1: Invalidate rules cache after delete
            from app.services.rules_cache import invalidate_cache
            invalidate_cache(use_case_id)
            logger.info(f"[Rules] Invalidated rules cache for use case {use_case_id} after bulk delete")
            
            # Check if any requested nodes didn't have rules
            if deleted_count < len(request.node_ids):
                failed_count = len(request.node_ids) - deleted_count
                errors.append(f"{failed_count} node(s) did not have rules to delete")
                
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting bulk rules: {e}")
            errors.append(f"Transaction failed: {str(e)}")
            failed_count = len(request.node_ids)
            success_count = 0
        
        return BulkRuleResponse(
            success_count=success_count,
            failed_count=failed_count,
            errors=errors,
            created_rules=[]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk rule deletion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete bulk rules: {str(e)}")


@router.get("/use-cases/{use_case_id}/rules/stack/{node_id}", response_model=RuleStackResponse)
def get_rule_stack(
    use_case_id: UUID,
    node_id: str,
    db: Session = Depends(get_db)
):
    """
    Get rule stack for a node: direct rule + parent rules from path.
    
    Args:
        use_case_id: Use case UUID
        node_id: Node ID to get rule stack for
        db: Database session
    
    Returns:
        RuleStackResponse with direct rule and parent rules
    """
    try:
        # Validate use case exists
        use_case = db.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
        if not use_case:
            raise HTTPException(
                status_code=404,
                detail=f"Use case '{use_case_id}' not found"
            )
        
        # Get node
        node = db.query(DimHierarchy).filter(DimHierarchy.node_id == node_id).first()
        if not node:
            raise HTTPException(
                status_code=404,
                detail=f"Node '{node_id}' not found"
            )
        
        # Get direct rule for this node
        direct_rule_obj = db.query(MetadataRule).filter(
            MetadataRule.use_case_id == use_case_id,
            MetadataRule.node_id == node_id
        ).first()
        
        direct_rule = None
        if direct_rule_obj:
            direct_rule = RuleResponse(
                rule_id=direct_rule_obj.rule_id,
                use_case_id=direct_rule_obj.use_case_id,
                node_id=direct_rule_obj.node_id,
                node_name=node.node_name,
                logic_en=direct_rule_obj.logic_en if direct_rule_obj.logic_en else None,
                predicate_json=direct_rule_obj.predicate_json if direct_rule_obj.predicate_json else None,
                sql_where=direct_rule_obj.sql_where if direct_rule_obj.sql_where else None,
                last_modified_by=direct_rule_obj.last_modified_by,
                created_at=direct_rule_obj.created_at.isoformat(),
                last_modified_at=direct_rule_obj.last_modified_at.isoformat(),
                # Phase 5.7: Math Engine fields - explicitly map from database model
                rule_type=direct_rule_obj.rule_type if direct_rule_obj.rule_type else None,
                rule_expression=direct_rule_obj.rule_expression if direct_rule_obj.rule_expression else None,
                measure_name=direct_rule_obj.measure_name if direct_rule_obj.measure_name else None,
                rule_dependencies=direct_rule_obj.rule_dependencies if direct_rule_obj.rule_dependencies else None
            )
        
        # Get path array to find parent nodes (traverse up to root)
        from sqlalchemy import text
        path_query = text("""
            WITH RECURSIVE node_paths AS (
                -- Start with the target node
                SELECT 
                    node_id,
                    node_name,
                    parent_node_id,
                    ARRAY[node_id]::text[] as path_ids
                FROM dim_hierarchy
                WHERE node_id = :node_id
                
                UNION ALL
                
                -- Traverse up to parent
                SELECT 
                    h.node_id,
                    h.node_name,
                    h.parent_node_id,
                    h.node_id || np.path_ids
                FROM dim_hierarchy h
                INNER JOIN node_paths np ON h.node_id = np.parent_node_id
            )
            SELECT path_ids FROM node_paths WHERE parent_node_id IS NULL
        """)
        
        try:
            path_result = db.execute(path_query, {"node_id": node_id}).fetchone()
            path_ids = list(path_result[0]) if path_result and path_result[0] else [node_id]
        except Exception as e:
            logger.warning(f"Failed to get path for node {node_id}: {e}")
            # Fallback: just use the node itself
            path_ids = [node_id]
        
        # Get parent rules (exclude current node)
        parent_rules = []
        if path_ids:
            parent_node_ids = path_ids[:-1]  # All nodes except the current one
            if parent_node_ids:
                parent_rule_objs = db.query(MetadataRule).filter(
                    MetadataRule.use_case_id == use_case_id,
                    MetadataRule.node_id.in_(parent_node_ids)
                ).all()
                
                for parent_rule_obj in parent_rule_objs:
                    parent_node = db.query(DimHierarchy).filter(
                        DimHierarchy.node_id == parent_rule_obj.node_id
                    ).first()
                    
                    parent_rules.append(RuleResponse(
                        rule_id=parent_rule_obj.rule_id,
                        use_case_id=parent_rule_obj.use_case_id,
                        node_id=parent_rule_obj.node_id,
                        node_name=parent_node.node_name if parent_node else None,
                        logic_en=parent_rule_obj.logic_en if parent_rule_obj.logic_en else None,
                        predicate_json=parent_rule_obj.predicate_json if parent_rule_obj.predicate_json else None,
                        sql_where=parent_rule_obj.sql_where if parent_rule_obj.sql_where else None,
                        last_modified_by=parent_rule_obj.last_modified_by,
                        created_at=parent_rule_obj.created_at.isoformat(),
                        last_modified_at=parent_rule_obj.last_modified_at.isoformat(),
                        # Phase 5.7: Math Engine fields - explicitly map from database model
                        rule_type=parent_rule_obj.rule_type if parent_rule_obj.rule_type else None,
                        rule_expression=parent_rule_obj.rule_expression if parent_rule_obj.rule_expression else None,
                        measure_name=parent_rule_obj.measure_name if parent_rule_obj.measure_name else None,
                        rule_dependencies=parent_rule_obj.rule_dependencies if parent_rule_obj.rule_dependencies else None
                    ))
        
        # Check for conflicts: if child has direct rule and parent also has rule
        has_conflict = direct_rule is not None and len(parent_rules) > 0
        
        return RuleStackResponse(
            node_id=node_id,
            node_name=node.node_name,
            direct_rule=direct_rule,
            parent_rules=parent_rules,
            has_conflict=has_conflict
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting rule stack: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get rule stack: {str(e)}")

