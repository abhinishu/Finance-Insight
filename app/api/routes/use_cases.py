"""
Use Case Management API routes for Finance-Insight
Provides CRUD operations for use cases (Phase 1: Basic create/list)
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models import UseCase, UseCaseStatus

router = APIRouter(prefix="/api/v1", tags=["use-cases"])


@router.post("/use-cases")
def create_use_case(
    name: str,
    description: Optional[str] = None,
    owner_id: str = "default_user",
    atlas_structure_id: str = None,
    db: Session = Depends(get_db)
):
    """
    Create a new use case.
    
    Args:
        name: Use case name (e.g., "America Trading P&L")
        description: Optional description
        owner_id: Owner user ID
        atlas_structure_id: Atlas structure identifier (required)
    
    Returns:
        Created use case with UUID
    """
    if not atlas_structure_id:
        raise HTTPException(
            status_code=400,
            detail="atlas_structure_id is required"
        )
    
    # Verify structure exists
    from app.models import DimHierarchy
    structure_exists = db.query(DimHierarchy).filter(
        DimHierarchy.atlas_source == atlas_structure_id
    ).first()
    
    if not structure_exists:
        raise HTTPException(
            status_code=404,
            detail=f"Structure '{atlas_structure_id}' not found"
        )
    
    # Create use case
    use_case = UseCase(
        name=name,
        description=description,
        owner_id=owner_id,
        atlas_structure_id=atlas_structure_id,
        status=UseCaseStatus.DRAFT
    )
    
    db.add(use_case)
    db.commit()
    db.refresh(use_case)
    
    return {
        "use_case_id": str(use_case.use_case_id),
        "name": use_case.name,
        "description": use_case.description,
        "owner_id": use_case.owner_id,
        "atlas_structure_id": use_case.atlas_structure_id,
        "status": use_case.status.value,
        "created_at": use_case.created_at.isoformat()
    }


@router.get("/use-cases")
def list_use_cases(
    owner_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all use cases with optional filters.
    
    Args:
        owner_id: Filter by owner
        status: Filter by status (DRAFT, ACTIVE, ARCHIVED)
    
    Returns:
        List of use cases
    """
    query = db.query(UseCase)
    
    if owner_id:
        query = query.filter(UseCase.owner_id == owner_id)
    
    if status:
        try:
            status_enum = UseCaseStatus(status.upper())
            query = query.filter(UseCase.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}. Must be one of: DRAFT, ACTIVE, ARCHIVED"
            )
    
    # Order by name alphabetically for consistent display across tabs
    use_cases = query.order_by(UseCase.name.asc()).all()
    
    return {
        "use_cases": [
            {
                "use_case_id": str(uc.use_case_id),
                "name": uc.name,
                "description": uc.description,
                "owner_id": uc.owner_id,
                "atlas_structure_id": uc.atlas_structure_id,
                "status": uc.status.value,
                "created_at": uc.created_at.isoformat()
            }
            for uc in use_cases
        ]
    }


@router.get("/use-cases/{use_case_id}")
def get_use_case(use_case_id: UUID, db: Session = Depends(get_db)):
    """
    Get use case details.
    
    Args:
        use_case_id: Use case UUID
    
    Returns:
        Use case details
    """
    use_case = db.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
    
    if not use_case:
        raise HTTPException(
            status_code=404,
            detail=f"Use case '{use_case_id}' not found"
        )
    
    # Get rule count and run count
    rule_count = len(use_case.rules) if use_case.rules else 0
    run_count = len(use_case.runs) if use_case.runs else 0
    
    return {
        "use_case_id": str(use_case.use_case_id),
        "name": use_case.name,
        "description": use_case.description,
        "owner_id": use_case.owner_id,
        "atlas_structure_id": use_case.atlas_structure_id,
        "status": use_case.status.value,
        "created_at": use_case.created_at.isoformat(),
        "rule_count": rule_count,
        "run_count": run_count
    }


@router.put("/use-cases/{use_case_id}")
def update_use_case(
    use_case_id: UUID,
    name: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Update a use case (name and description only).
    
    Step 4.4: Prevents editing of atlas_structure_id to maintain data integrity.
    
    Args:
        use_case_id: Use case UUID
        name: Updated use case name (optional)
        description: Updated description (optional)
    
    Returns:
        Updated use case details
    """
    use_case = db.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
    
    if not use_case:
        raise HTTPException(
            status_code=404,
            detail=f"Use case '{use_case_id}' not found"
        )
    
    # Update only name and description (atlas_structure_id is immutable)
    if name is not None:
        if not name.strip():
            raise HTTPException(
                status_code=400,
                detail="Use case name cannot be empty"
            )
        use_case.name = name.strip()
    
    if description is not None:
        use_case.description = description.strip() if description else None
    
    db.commit()
    db.refresh(use_case)
    
    # Get rule count and run count
    rule_count = len(use_case.rules) if use_case.rules else 0
    run_count = len(use_case.runs) if use_case.runs else 0
    
    return {
        "use_case_id": str(use_case.use_case_id),
        "name": use_case.name,
        "description": use_case.description,
        "owner_id": use_case.owner_id,
        "atlas_structure_id": use_case.atlas_structure_id,
        "status": use_case.status.value,
        "created_at": use_case.created_at.isoformat(),
        "rule_count": rule_count,
        "run_count": run_count,
        "message": "Use case updated successfully"
    }


@router.get("/use-cases/{use_case_id}/hierarchy")
def get_use_case_hierarchy(
    use_case_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get hierarchy for a use case by automatically using its atlas_structure_id.
    This endpoint returns the base Atlas structure even if no calculation_run exists.
    If a calculation run exists, uses calculated results; otherwise uses natural rollups.
    
    Args:
        use_case_id: Use case UUID
    
    Returns:
        DiscoveryResponse with hierarchy tree (same format as /api/v1/discovery)
    """
    use_case = db.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
    
    if not use_case:
        raise HTTPException(
            status_code=404,
            detail=f"Use case '{use_case_id}' not found"
        )
    
    # Check if there's a latest calculation run with results
    from app.models import CalculationRun, FactCalculatedResult
    from sqlalchemy import desc
    
    latest_run = db.query(CalculationRun).filter(
        CalculationRun.use_case_id == use_case_id
    ).order_by(desc(CalculationRun.executed_at)).first()
    
    # If we have calculated results, use them; otherwise use discovery endpoint (natural rollups)
    if latest_run:
        # Check if results exist for this run
        results_count = db.query(FactCalculatedResult).filter(
            (FactCalculatedResult.calculation_run_id == latest_run.calculation_run_id) |
            (FactCalculatedResult.run_id == latest_run.calculation_run_id)
        ).count()
        
        if results_count > 0:
            # Use calculated results - delegate to discovery endpoint but it will use natural rollups
            # The discovery endpoint always uses natural rollups, so we'll use it as-is
            # (The calculated results are shown in the /results endpoint, not /hierarchy)
            pass
    
    # Always return the base Atlas structure via discovery endpoint
    # This ensures the hierarchy is always visible even without calculation runs
    from app.api.routes.discovery import get_discovery_view
    return get_discovery_view(
        structure_id=use_case.atlas_structure_id,
        report_id=None,
        db=db
    )