"""
Runs API routes for Finance-Insight
Provides date-anchored run selection for UI.
Step 4.2: Supports "Trial Analysis" by allowing users to select runs by PNL_DATE.
"""

from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models import CalculationRun, UseCase

router = APIRouter(prefix="/api/v1", tags=["runs"])


@router.get("/runs")
def get_runs(
    pnl_date: Optional[date] = Query(None, description="P&L date (COB date)"),
    use_case_id: Optional[UUID] = Query(None, description="Use case UUID"),
    db: Session = Depends(get_db)
):
    """
    Get calculation runs for UI date selection.
    
    This endpoint allows the UI to:
    1. User selects Date (e.g., 2025-12-24)
    2. API returns Runs: [Run 1: 09:00 AM, Run 2: 10:30 AM (Adjusted)]
    3. User selects Run 2, and the dashboard populates
    
    Args:
        pnl_date: Optional P&L date filter (required if use_case_id is provided)
        use_case_id: Optional use case UUID filter (required if pnl_date is provided)
        db: Database session
    
    Returns:
        List of calculation runs with metadata:
        {
            "runs": [
                {
                    "id": UUID,
                    "pnl_date": "2025-12-24",
                    "run_name": "Initial Run",
                    "executed_at": "2025-12-24T09:00:00",
                    "status": "COMPLETED",
                    "triggered_by": "user123",
                    "duration_ms": 1250
                },
                ...
            ],
            "total": 2
        }
    """
    query = db.query(CalculationRun)
    
    # Build query filters
    if pnl_date and use_case_id:
        # Both filters provided - get runs for specific date and use case
        query = query.filter(
            CalculationRun.pnl_date == pnl_date,
            CalculationRun.use_case_id == use_case_id
        )
    elif pnl_date:
        # Only date provided - get all runs for that date
        query = query.filter(CalculationRun.pnl_date == pnl_date)
    elif use_case_id:
        # Only use case provided - get all runs for that use case
        query = query.filter(CalculationRun.use_case_id == use_case_id)
    else:
        # No filters - return all runs (with limit for performance)
        query = query.limit(100)
    
    # Order by execution time (most recent first)
    runs = query.order_by(CalculationRun.executed_at.desc()).all()
    
    # Validate use case exists if provided
    if use_case_id:
        use_case = db.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
        if not use_case:
            raise HTTPException(
                status_code=404,
                detail=f"Use case '{use_case_id}' not found"
            )
    
    # Format response
    runs_data = []
    for run in runs:
        runs_data.append({
            "id": str(run.id),
            "pnl_date": run.pnl_date.isoformat(),
            "use_case_id": str(run.use_case_id),
            "run_name": run.run_name,
            "executed_at": run.executed_at.isoformat(),
            "status": run.status,
            "triggered_by": run.triggered_by,
            "duration_ms": run.calculation_duration_ms,
        })
    
    return {
        "runs": runs_data,
        "total": len(runs_data),
        "filters": {
            "pnl_date": pnl_date.isoformat() if pnl_date else None,
            "use_case_id": str(use_case_id) if use_case_id else None
        }
    }


@router.get("/runs/{run_id}")
def get_run_details(run_id: UUID, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific calculation run.
    
    Args:
        run_id: Calculation run UUID
        db: Database session
    
    Returns:
        Run details with associated results count
    """
    run = db.query(CalculationRun).filter(CalculationRun.id == run_id).first()
    
    if not run:
        raise HTTPException(
            status_code=404,
            detail=f"Calculation run '{run_id}' not found"
        )
    
    # Get results count
    from app.models import FactCalculatedResult
    results_count = db.query(FactCalculatedResult).filter(
        FactCalculatedResult.calculation_run_id == run_id
    ).count()
    
    return {
        "id": str(run.id),
        "pnl_date": run.pnl_date.isoformat(),
        "use_case_id": str(run.use_case_id),
        "run_name": run.run_name,
        "executed_at": run.executed_at.isoformat(),
        "status": run.status,
        "triggered_by": run.triggered_by,
        "duration_ms": run.calculation_duration_ms,
        "results_count": results_count
    }


@router.get("/runs/latest/defaults")
def get_latest_defaults(
    use_case_id: Optional[UUID] = Query(None, description="Use case UUID (optional)"),
    db: Session = Depends(get_db)
):
    """
    Get the latest PNL date and run_id for defaulting on app load.
    Step 4.3: Returns MAX(pnl_date) and the latest run_id for that date.
    
    Args:
        use_case_id: Optional use case UUID filter
        db: Database session
    
    Returns:
        {
            "pnl_date": "2025-12-24",
            "run_id": "uuid",
            "run_name": "Initial Run",
            "use_case_id": "uuid" (if filtered)
        }
    """
    from sqlalchemy import func
    
    # Build query
    query = db.query(CalculationRun)
    
    if use_case_id:
        query = query.filter(CalculationRun.use_case_id == use_case_id)
    
    # Get MAX(pnl_date)
    max_date_result = query.with_entities(func.max(CalculationRun.pnl_date)).scalar()
    
    if not max_date_result:
        # No runs found - return null
        return {
            "pnl_date": None,
            "run_id": None,
            "run_name": None,
            "use_case_id": str(use_case_id) if use_case_id else None
        }
    
    # Get latest run for that date
    latest_run = query.filter(
        CalculationRun.pnl_date == max_date_result
    ).order_by(CalculationRun.executed_at.desc()).first()
    
    if not latest_run:
        return {
            "pnl_date": max_date_result.isoformat(),
            "run_id": None,
            "run_name": None,
            "use_case_id": str(use_case_id) if use_case_id else None
        }
    
    return {
        "pnl_date": max_date_result.isoformat(),
        "run_id": str(latest_run.id),
        "run_name": latest_run.run_name,
        "executed_at": latest_run.executed_at.isoformat(),
        "use_case_id": str(latest_run.use_case_id)
    }


