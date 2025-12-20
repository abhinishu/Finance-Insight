"""
Report Registration API routes for Finance-Insight
Provides CRUD operations for report registrations (Tab 1)
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.dependencies import get_db
from app.models import ReportRegistration

router = APIRouter(prefix="/api/v1", tags=["reports"])


# Request/Response schemas
class ReportRegistrationCreate(BaseModel):
    report_name: str
    atlas_structure_id: str
    selected_measures: List[str]  # ["daily", "mtd", "ytd"]
    selected_dimensions: Optional[List[str]] = None  # ["region", "product", "desk"]
    measure_scopes: Optional[dict] = None  # {"daily": ["input", "rule", "output"], ...}
    dimension_scopes: Optional[dict] = None  # {"region": ["input", "rule", "output"], ...}
    owner_id: str = "default_user"


class ReportRegistrationUpdate(BaseModel):
    report_name: Optional[str] = None
    atlas_structure_id: Optional[str] = None
    selected_measures: Optional[List[str]] = None
    selected_dimensions: Optional[List[str]] = None
    measure_scopes: Optional[dict] = None
    dimension_scopes: Optional[dict] = None


class ReportRegistrationResponse(BaseModel):
    report_id: str
    report_name: str
    atlas_structure_id: str
    selected_measures: List[str]
    selected_dimensions: Optional[List[str]]
    measure_scopes: Optional[dict] = None
    dimension_scopes: Optional[dict] = None
    owner_id: str
    created_at: str
    updated_at: str
    status: str = "ACTIVE"


@router.post("/reports", response_model=ReportRegistrationResponse)
def create_report(
    report: ReportRegistrationCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new report registration.
    
    Args:
        report: Report registration data
        db: Database session
    
    Returns:
        Created report registration
    """
    # Verify structure exists
    from app.models import DimHierarchy
    structure_exists = db.query(DimHierarchy).filter(
        DimHierarchy.atlas_source == report.atlas_structure_id
    ).first()
    
    if not structure_exists:
        raise HTTPException(
            status_code=404,
            detail=f"Structure '{report.atlas_structure_id}' not found"
        )
    
    # Create report registration
    db_report = ReportRegistration(
        report_name=report.report_name,
        atlas_structure_id=report.atlas_structure_id,
        selected_measures=report.selected_measures,
        selected_dimensions=report.selected_dimensions or [],
        measure_scopes=report.measure_scopes or {},
        dimension_scopes=report.dimension_scopes or {},
        owner_id=report.owner_id
    )
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    return ReportRegistrationResponse(
        report_id=str(db_report.report_id),
        report_name=db_report.report_name,
        atlas_structure_id=db_report.atlas_structure_id,
        selected_measures=db_report.selected_measures,
        selected_dimensions=db_report.selected_dimensions,
        measure_scopes=db_report.measure_scopes,
        dimension_scopes=db_report.dimension_scopes,
        owner_id=db_report.owner_id,
        created_at=db_report.created_at.isoformat(),
        updated_at=db_report.updated_at.isoformat()
    )


@router.get("/reports", response_model=List[ReportRegistrationResponse])
def list_reports(
    owner_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all report registrations.
    
    Args:
        owner_id: Filter by owner (optional)
        db: Database session
    
    Returns:
        List of report registrations
    """
    query = db.query(ReportRegistration)
    
    if owner_id:
        query = query.filter(ReportRegistration.owner_id == owner_id)
    
    reports = query.order_by(ReportRegistration.created_at.desc()).all()
    
    return [
        ReportRegistrationResponse(
            report_id=str(r.report_id),
            report_name=r.report_name,
            atlas_structure_id=r.atlas_structure_id,
            selected_measures=r.selected_measures,
            selected_dimensions=r.selected_dimensions,
            measure_scopes=r.measure_scopes or {},
            dimension_scopes=r.dimension_scopes or {},
            owner_id=r.owner_id,
            created_at=r.created_at.isoformat(),
            updated_at=r.updated_at.isoformat()
        )
        for r in reports
    ]


@router.get("/reports/{report_id}", response_model=ReportRegistrationResponse)
def get_report(report_id: UUID, db: Session = Depends(get_db)):
    """
    Get report registration details.
    
    Args:
        report_id: Report UUID
        db: Database session
    
    Returns:
        Report registration details
    """
    report = db.query(ReportRegistration).filter(
        ReportRegistration.report_id == report_id
    ).first()
    
    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"Report '{report_id}' not found"
        )
    
    return ReportRegistrationResponse(
        report_id=str(report.report_id),
        report_name=report.report_name,
        atlas_structure_id=report.atlas_structure_id,
        selected_measures=report.selected_measures,
        selected_dimensions=report.selected_dimensions,
        measure_scopes=report.measure_scopes or {},
        dimension_scopes=report.dimension_scopes or {},
        owner_id=report.owner_id,
        created_at=report.created_at.isoformat(),
        updated_at=report.updated_at.isoformat()
    )


@router.put("/reports/{report_id}", response_model=ReportRegistrationResponse)
def update_report(
    report_id: UUID,
    report_update: ReportRegistrationUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing report registration.
    
    Args:
        report_id: Report UUID
        report_update: Updated report data
        db: Database session
    
    Returns:
        Updated report registration
    """
    report = db.query(ReportRegistration).filter(
        ReportRegistration.report_id == report_id
    ).first()
    
    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"Report '{report_id}' not found"
        )
    
    # Update fields if provided
    if report_update.report_name is not None:
        report.report_name = report_update.report_name
    
    if report_update.atlas_structure_id is not None:
        # Verify structure exists
        from app.models import DimHierarchy
        structure_exists = db.query(DimHierarchy).filter(
            DimHierarchy.atlas_source == report_update.atlas_structure_id
        ).first()
        
        if not structure_exists:
            raise HTTPException(
                status_code=404,
                detail=f"Structure '{report_update.atlas_structure_id}' not found"
            )
        report.atlas_structure_id = report_update.atlas_structure_id
    
    if report_update.selected_measures is not None:
        report.selected_measures = report_update.selected_measures
    
    if report_update.selected_dimensions is not None:
        report.selected_dimensions = report_update.selected_dimensions
    
    if report_update.measure_scopes is not None:
        report.measure_scopes = report_update.measure_scopes
    
    if report_update.dimension_scopes is not None:
        report.dimension_scopes = report_update.dimension_scopes
    
    db.commit()
    db.refresh(report)
    
    return ReportRegistrationResponse(
        report_id=str(report.report_id),
        report_name=report.report_name,
        atlas_structure_id=report.atlas_structure_id,
        selected_measures=report.selected_measures,
        selected_dimensions=report.selected_dimensions,
        measure_scopes=report.measure_scopes or {},
        dimension_scopes=report.dimension_scopes or {},
        owner_id=report.owner_id,
        created_at=report.created_at.isoformat(),
        updated_at=report.updated_at.isoformat()
    )

