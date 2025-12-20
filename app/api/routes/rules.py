"""
Rules API routes for Finance-Insight Phase 2
Provides endpoints for creating and managing business rules.
"""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.schemas import (
    RuleCreate,
    RuleGenAIRequest,
    RuleGenAIResponse,
    RulePreviewRequest,
    RulePreviewResponse,
    RuleResponse,
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
            
            # Translate natural language to JSON and SQL
            try:
                predicate_json, sql_where, errors, translation_successful = translate_rule(
                    rule_data.logic_en,
                    use_cache=True
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
        elif rule_data.sql_where:
            # Direct SQL mode (advanced, for testing)
            raise HTTPException(
                status_code=501,
                detail="Direct SQL mode not yet implemented. Use 'conditions' for manual rules."
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide either 'conditions' (manual), 'logic_en' (GenAI), or 'sql_where' (direct)"
            )
        
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
            last_modified_at=rule.last_modified_at.isoformat()
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
            last_modified_at=rule.last_modified_at.isoformat()
        ))
    
    return result


@router.post("/rules/preview", response_model=RulePreviewResponse)
def preview_rule(
    request: RulePreviewRequest,
    db: Session = Depends(get_db)
):
    """
    Preview the impact of a rule by counting affected rows.
    
    This endpoint allows users to see how many rows in fact_pnl_gold
    would be affected by a SQL WHERE clause before saving the rule.
    
    Args:
        request: RulePreviewRequest with sql_where
        db: Database session
    
    Returns:
        RulePreviewResponse with affected row count and percentage
    """
    try:
        return preview_rule_impact(request.sql_where, db)
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
    
    try:
        logger.info(f"Translating GenAI rule for use case {use_case_id}: {request.logic_en}")
        
        # Call translator (Stage 1: NL → JSON, Stage 2: Validate, Stage 3: JSON → SQL)
        try:
            predicate_json, sql_where, errors, translation_successful = translate_rule(
                request.logic_en,
                use_cache=True
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

