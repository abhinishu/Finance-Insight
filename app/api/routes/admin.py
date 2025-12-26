"""
Admin API routes for Finance-Insight
Provides administrative functions for metadata management and use case deletion.
"""

from pathlib import Path
from typing import Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models import (
    CalculationRun,
    FactPnlEntries,
    MetadataRule,
    UseCase,
    UseCaseRun,
)
from scripts.seed_manager import export_to_json, import_from_json

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/export-metadata")
def export_metadata(db: Session = Depends(get_db)):
    """
    Export current dim_dictionary metadata to JSON backup file.
    
    Returns:
        JSON response with export path and statistics
    """
    try:
        output_path = export_to_json(session=db)
        
        # Read the exported file to get statistics
        import json
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            "status": "success",
            "message": "Metadata exported successfully",
            "export_path": str(output_path),
            "total_entries": data.get("total_entries", 0),
            "exported_at": data.get("exported_at")
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export metadata: {str(e)}"
        )


@router.post("/import-metadata")
def import_metadata(file_path: str = None, db: Session = Depends(get_db)):
    """
    Import dictionary definitions from JSON file.
    
    Args:
        file_path: Optional path to JSON file. If None, uses default seed file.
    
    Returns:
        JSON response with import statistics
    """
    try:
        path = Path(file_path) if file_path else None
        result = import_from_json(session=db, file_path=path)
        
        return {
            "status": "success",
            "message": "Metadata imported successfully",
            "statistics": result
        }
    
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Seed file not found: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import metadata: {str(e)}"
        )


@router.delete("/use-case/{use_case_id}")
def delete_use_case(use_case_id: UUID, db: Session = Depends(get_db)):
    """
    Delete a use case and return summary report of purged data.
    
    Step 4.2: Enhanced to count Runs (both legacy and calculation_runs), Rules, and Facts
    before executing the cascade deletion.
    
    Args:
        use_case_id: UUID of the use case to delete
    
    Returns:
        JSON summary:
        {
            "deleted_use_case": id,
            "rules_purged": X,
            "legacy_runs_purged": Y,
            "calculation_runs_purged": Z,
            "facts_purged": W,
            "message": "..."
        }
    """
    # Find the use case
    use_case = db.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
    
    if not use_case:
        raise HTTPException(
            status_code=404,
            detail=f"Use case '{use_case_id}' not found"
        )
    
    # Count related records before deletion (for summary report)
    rules_count = db.query(MetadataRule).filter(
        MetadataRule.use_case_id == use_case_id
    ).count()
    
    # Legacy runs (use_case_runs)
    legacy_runs_count = db.query(UseCaseRun).filter(
        UseCaseRun.use_case_id == use_case_id
    ).count()
    
    # Step 4.2: Calculation runs (calculation_runs)
    calculation_runs_count = db.query(CalculationRun).filter(
        CalculationRun.use_case_id == use_case_id
    ).count()
    
    # Step 4.2: Facts (fact_pnl_entries)
    facts_count = db.query(FactPnlEntries).filter(
        FactPnlEntries.use_case_id == use_case_id
    ).count()
    
    # Delete the use case (CASCADE will handle related records)
    db.delete(use_case)
    db.commit()
    
    return {
        "deleted_use_case": str(use_case_id),
        "rules_purged": rules_count,
        "legacy_runs_purged": legacy_runs_count,
        "calculation_runs_purged": calculation_runs_count,
        "facts_purged": facts_count,
        "total_items_deleted": rules_count + legacy_runs_count + calculation_runs_count + facts_count,
        "message": f"Use case '{use_case.name}' and all related data deleted successfully"
    }

