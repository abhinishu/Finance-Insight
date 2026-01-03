"""
Use Case Management API routes for Finance-Insight
Provides CRUD operations for use cases (Phase 1: Basic create/list)
"""

import io
from typing import List, Optional
from uuid import UUID

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text
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


@router.get("/use-cases/{use_case_id}/schema")
def get_use_case_schema(use_case_id: UUID, db: Session = Depends(get_db)):
    """
    Get available schema fields for a use case based on its input_table_name.
    
    This endpoint returns the correct field names that should be displayed in the
    Rule Editor dropdown based on the use case's table configuration.
    
    Args:
        use_case_id: Use case UUID
    
    Returns:
        Dictionary with 'fields' array containing field objects with:
        - value: Field name to use in rules (frontend name)
        - label: Display label
        - type: Field type (String, Date, Numeric)
    """
    use_case = db.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
    
    if not use_case:
        raise HTTPException(
            status_code=404,
            detail=f"Use case '{use_case_id}' not found"
        )
    
    # Determine fields based on input_table_name
    table_name = use_case.input_table_name or 'fact_pnl_gold'
    
    if table_name == 'fact_pnl_use_case_3':
        # Use Case 3: fact_pnl_use_case_3 uses different column names
        # Phase 5.9: Include ALL dimension fields from the table
        fields = [
            {'value': 'strategy', 'label': 'Strategy', 'type': 'String'},
            {'value': 'book', 'label': 'Book', 'type': 'String'},
            {'value': 'cost_center', 'label': 'Cost Center', 'type': 'String'},
            {'value': 'process_1', 'label': 'Process 1', 'type': 'String'},
            {'value': 'process_2', 'label': 'Process 2', 'type': 'String'},
            {'value': 'division', 'label': 'Division', 'type': 'String'},
            {'value': 'business_area', 'label': 'Business Area', 'type': 'String'},
            {'value': 'product_line', 'label': 'Product Line', 'type': 'String'},
            {'value': 'effective_date', 'label': 'Effective Date', 'type': 'Date'},
        ]
    elif table_name == 'fact_pnl_entries':
        # Use Case 2: fact_pnl_entries
        fields = [
            {'value': 'account_id', 'label': 'Account ID', 'type': 'String'},
            {'value': 'cc_id', 'label': 'Cost Center ID', 'type': 'String'},
            {'value': 'book_id', 'label': 'Book ID', 'type': 'String'},
            {'value': 'strategy_id', 'label': 'Strategy ID', 'type': 'String'},
            {'value': 'pnl_date', 'label': 'P&L Date', 'type': 'Date'},
        ]
    else:
        # Default: fact_pnl_gold (Use Cases 1 & 2)
        fields = [
            {'value': 'account_id', 'label': 'Account ID', 'type': 'String'},
            {'value': 'cc_id', 'label': 'Cost Center ID', 'type': 'String'},
            {'value': 'book_id', 'label': 'Book ID', 'type': 'String'},
            {'value': 'strategy_id', 'label': 'Strategy ID', 'type': 'String'},
            {'value': 'trade_date', 'label': 'Trade Date', 'type': 'Date'},
        ]
    
    return {
        'use_case_id': str(use_case_id),
        'table_name': table_name,
        'fields': fields
    }


@router.get("/use-cases/{use_case_id}/input-data/csv")
def export_input_data_csv(
    use_case_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Export raw input data from the use case's input table as CSV.
    
    This endpoint queries the table specified by the use case's `input_table_name`
    and returns all rows as a CSV file download.
    
    Args:
        use_case_id: Use case UUID
        
    Returns:
        CSV file stream with all data from the input table
        
    Raises:
        HTTPException: If use case not found or table doesn't exist
    """
    # Fetch use case
    use_case = db.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
    
    if not use_case:
        raise HTTPException(
            status_code=404,
            detail=f"Use case '{use_case_id}' not found"
        )
    
    # Determine input table name
    # Default to fact_pnl_gold if not specified (for backward compatibility)
    table_name = use_case.input_table_name or 'fact_pnl_gold'
    
    # Validate table name to prevent SQL injection
    # Only allow alphanumeric and underscore characters
    if not all(c.isalnum() or c == '_' for c in table_name):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid table name: {table_name}"
        )
    
    try:
        # Query all data from the table using raw SQL
        # Use SQLAlchemy's text() with proper identifier quoting for table name
        # Note: Table names cannot be parameterized, but we've validated the table name above
        # SQL injection protection: table_name is validated to only contain alphanumeric and underscore
        
        # Use SQLAlchemy text() with proper quoting (PostgreSQL uses double quotes for identifiers)
        sql_query = text(f'SELECT * FROM "{table_name}"')
        
        # Execute query and load into pandas DataFrame
        result = db.execute(sql_query)
        rows = result.fetchall()
        
        if not rows:
            # Return empty CSV if no data
            df = pd.DataFrame()
        else:
            # Convert to DataFrame
            # Get column names from result keys
            column_names = result.keys()
            df = pd.DataFrame(rows, columns=column_names)
        
        # Convert DataFrame to CSV
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        csv_buffer.close()
        
        # Create filename
        use_case_name_safe = "".join(c for c in use_case.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"raw_input_{use_case_name_safe}_{str(use_case_id)[:8]}.csv"
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(csv_content.encode('utf-8')),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error exporting CSV for use case {use_case_id}: {str(e)}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export CSV: {str(e)}"
        )