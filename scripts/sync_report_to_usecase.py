"""
Migration script to sync existing ReportRegistration records to UseCase table.
This ensures all tabs use the same data source.

Run this script once to migrate existing data:
    python scripts/sync_report_to_usecase.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import get_session_factory
from app.models import ReportRegistration, UseCase, UseCaseStatus, DimHierarchy

def sync_reports_to_usecases():
    """
    Create UseCase records for all existing ReportRegistration records.
    """
    SessionLocal = get_session_factory()
    db: Session = SessionLocal()
    
    try:
        # Get all report registrations
        reports = db.query(ReportRegistration).all()
        print(f"Found {len(reports)} report registrations to sync")
        
        created_count = 0
        skipped_count = 0
        
        for report in reports:
            # Check if UseCase already exists with same name and structure
            existing_use_case = db.query(UseCase).filter(
                UseCase.name == report.report_name,
                UseCase.atlas_structure_id == report.atlas_structure_id
            ).first()
            
            if existing_use_case:
                print(f"  ✓ UseCase already exists for '{report.report_name}' - skipping")
                skipped_count += 1
                continue
            
            # Verify structure exists
            structure_exists = db.query(DimHierarchy).filter(
                DimHierarchy.atlas_source == report.atlas_structure_id
            ).first()
            
            if not structure_exists:
                print(f"  ⚠ Structure '{report.atlas_structure_id}' not found for '{report.report_name}' - skipping")
                skipped_count += 1
                continue
            
            # Create UseCase
            use_case = UseCase(
                name=report.report_name,
                description=f"Use case for {report.report_name}",
                owner_id=report.owner_id,
                atlas_structure_id=report.atlas_structure_id,
                status=UseCaseStatus.ACTIVE
            )
            
            db.add(use_case)
            created_count += 1
            print(f"  ✓ Created UseCase for '{report.report_name}'")
        
        db.commit()
        print(f"\n✅ Migration complete!")
        print(f"   Created: {created_count} UseCase records")
        print(f"   Skipped: {skipped_count} (already exist or invalid)")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error during migration: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting ReportRegistration → UseCase migration...")
    sync_reports_to_usecases()

