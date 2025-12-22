"""
Script to create "America Trading P&L" use case in Tab 1 (ReportRegistration).
This will automatically create the corresponding UseCase record for all tabs.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import get_session_factory
from app.models import ReportRegistration, UseCase, UseCaseStatus, DimHierarchy

def create_america_trading_usecase():
    """
    Create "America Trading P&L" as a ReportRegistration (Tab 1).
    This will automatically create the UseCase record via the API endpoint.
    """
    SessionLocal = get_session_factory()
    db: Session = SessionLocal()
    
    try:
        # Check if it already exists
        existing_report = db.query(ReportRegistration).filter(
            ReportRegistration.report_name == "America Trading P&L"
        ).first()
        
        if existing_report:
            print("[OK] 'America Trading P&L' already exists in ReportRegistration")
        else:
            # Get the first available structure
            structure = db.query(DimHierarchy).filter(
                DimHierarchy.atlas_source.isnot(None)
            ).first()
            
            if not structure:
                print("[ERROR] No Atlas structure found. Please generate mock data first.")
                return False
            
            atlas_structure_id = structure.atlas_source
            print(f"Using structure: {atlas_structure_id}")
            
            # Create ReportRegistration
            report = ReportRegistration(
                report_name="America Trading P&L",
                atlas_structure_id=atlas_structure_id,
                selected_measures=["daily", "mtd", "ytd"],
                selected_dimensions=["region", "product", "desk", "strategy"],
                measure_scopes={
                    "daily": ["input", "rule", "output"],
                    "mtd": ["input", "rule", "output"],
                    "ytd": ["input", "rule", "output"]
                },
                dimension_scopes={
                    "region": ["input", "rule", "output"],
                    "product": ["input", "rule", "output"],
                    "desk": ["input", "rule", "output"],
                    "strategy": ["input", "rule", "output"]
                },
                owner_id="default_user"
            )
            
            db.add(report)
            db.commit()
            db.refresh(report)
            print(f"[OK] Created ReportRegistration: {report.report_name} (ID: {report.report_id})")
        
        # Now create/update the UseCase record (matching the API logic)
        existing_use_case = db.query(UseCase).filter(
            UseCase.name == "America Trading P&L"
        ).first()
        
        if existing_use_case:
            print("[OK] 'America Trading P&L' already exists in UseCase table")
            # Update it to ensure it's active and linked
            if existing_report:
                existing_use_case.atlas_structure_id = existing_report.atlas_structure_id
                existing_use_case.status = UseCaseStatus.ACTIVE
                existing_use_case.owner_id = existing_report.owner_id
                db.commit()
                print("[OK] Updated existing UseCase to match ReportRegistration")
        else:
            # Get the report to use its structure
            report = db.query(ReportRegistration).filter(
                ReportRegistration.report_name == "America Trading P&L"
            ).first()
            
            if not report:
                print("[ERROR] ReportRegistration not found. Cannot create UseCase.")
                return False
            
            # Create UseCase
            use_case = UseCase(
                name="America Trading P&L",
                description="Use case for America Trading P&L",
                owner_id=report.owner_id,
                atlas_structure_id=report.atlas_structure_id,
                status=UseCaseStatus.ACTIVE
            )
            
            db.add(use_case)
            db.commit()
            db.refresh(use_case)
            print(f"[OK] Created UseCase: {use_case.name} (ID: {use_case.use_case_id})")
        
        print("\n[SUCCESS] 'America Trading P&L' is now available in all tabs.")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Creating 'America Trading P&L' Use Case")
    print("=" * 60)
    print()
    success = create_america_trading_usecase()
    if success:
        print("\n" + "=" * 60)
        print("[SUCCESS] Complete! Refresh Tab 1 to see the new use case.")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("[ERROR] Failed to create use case.")
        print("=" * 60)
        sys.exit(1)

