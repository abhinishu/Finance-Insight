"""
Cleanup Script: Flush Legacy Calculated Results

This script removes "ghost data" from fact_calculated_results for Legacy Use Cases
(Use Case 1: America Trading P&L, Use Case 2: Project Sterling) that is causing
double-counting in Tab 3.

SAFETY: This script ONLY deletes from fact_calculated_results (derived/cached data).
It does NOT touch source fact tables (fact_pnl_entries, fact_pnl_gold, fact_pnl_use_case_3).
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.database import SessionLocal
from app.models import (
    UseCase,
    FactCalculatedResult,
    CalculationRun,
    UseCaseRun
)

def flush_legacy_results():
    """
    Delete all calculated results for Legacy Use Cases (1 & 2).
    """
    print("=" * 80)
    print("FLUSH LEGACY CALCULATED RESULTS")
    print("=" * 80)
    print()
    print("This script will delete all rows from fact_calculated_results for:")
    print("  - Use Case 1: America Trading P&L")
    print("  - Use Case 2: Project Sterling")
    print()
    print("SAFETY: Only deleting from fact_calculated_results (derived data).")
    print("        Source fact tables are NOT touched.")
    print()
    
    db: Session = SessionLocal()
    
    try:
        # Step 1: Find Target Use Cases
        print("STEP 1: Finding Target Use Cases")
        print("-" * 80)
        
        use_case_1 = db.query(UseCase).filter(
            UseCase.name.ilike('%America Trading%')
        ).first()
        
        use_case_2 = db.query(UseCase).filter(
            UseCase.name.ilike('%Project Sterling%')
        ).first()
        
        if not use_case_1:
            print("  [ERROR] Use Case 1 (America Trading P&L) not found!")
            return
        
        if not use_case_2:
            print("  [ERROR] Use Case 2 (Project Sterling) not found!")
            return
        
        print(f"  Use Case 1: {use_case_1.name}")
        print(f"    ID: {use_case_1.use_case_id}")
        print()
        print(f"  Use Case 2: {use_case_2.name}")
        print(f"    ID: {use_case_2.use_case_id}")
        print()
        
        # Step 2: Count existing results (before deletion)
        print("STEP 2: Counting Existing Results")
        print("-" * 80)
        
        # Count via calculation_run_id
        calc_run_ids_uc1 = [r.id for r in db.query(CalculationRun.id).filter(
            CalculationRun.use_case_id == use_case_1.use_case_id
        ).all()]
        calc_run_ids_uc2 = [r.id for r in db.query(CalculationRun.id).filter(
            CalculationRun.use_case_id == use_case_2.use_case_id
        ).all()]
        
        count_via_calc_run_uc1 = 0
        if calc_run_ids_uc1:
            count_via_calc_run_uc1 = db.query(FactCalculatedResult).filter(
                FactCalculatedResult.calculation_run_id.in_(calc_run_ids_uc1)
            ).count()
        
        count_via_calc_run_uc2 = 0
        if calc_run_ids_uc2:
            count_via_calc_run_uc2 = db.query(FactCalculatedResult).filter(
                FactCalculatedResult.calculation_run_id.in_(calc_run_ids_uc2)
            ).count()
        
        # Count via run_id (legacy)
        run_ids_uc1 = [r.run_id for r in db.query(UseCaseRun.run_id).filter(
            UseCaseRun.use_case_id == use_case_1.use_case_id
        ).all()]
        run_ids_uc2 = [r.run_id for r in db.query(UseCaseRun.run_id).filter(
            UseCaseRun.use_case_id == use_case_2.use_case_id
        ).all()]
        
        count_via_run_id_uc1 = 0
        if run_ids_uc1:
            count_via_run_id_uc1 = db.query(FactCalculatedResult).filter(
                FactCalculatedResult.run_id.in_(run_ids_uc1)
            ).count()
        
        count_via_run_id_uc2 = 0
        if run_ids_uc2:
            count_via_run_id_uc2 = db.query(FactCalculatedResult).filter(
                FactCalculatedResult.run_id.in_(run_ids_uc2)
            ).count()
        
        total_uc1 = count_via_calc_run_uc1 + count_via_run_id_uc1
        total_uc2 = count_via_calc_run_uc2 + count_via_run_id_uc2
        
        print(f"  Use Case 1 (via calculation_run_id): {count_via_calc_run_uc1} rows")
        print(f"  Use Case 1 (via run_id): {count_via_run_id_uc1} rows")
        print(f"  Use Case 1 (TOTAL): {total_uc1} rows")
        print()
        print(f"  Use Case 2 (via calculation_run_id): {count_via_calc_run_uc2} rows")
        print(f"  Use Case 2 (via run_id): {count_via_run_id_uc2} rows")
        print(f"  Use Case 2 (TOTAL): {total_uc2} rows")
        print()
        
        if total_uc1 == 0 and total_uc2 == 0:
            print("  [INFO] No results found to delete. Database is already clean.")
            return
        
        # Step 3: Delete Results
        print("STEP 3: Deleting Results")
        print("-" * 80)
        
        # Delete via calculation_run_id
        deleted_calc_run_uc1 = 0
        if calc_run_ids_uc1:
            deleted_calc_run_uc1 = db.query(FactCalculatedResult).filter(
                FactCalculatedResult.calculation_run_id.in_(calc_run_ids_uc1)
            ).delete(synchronize_session=False)
        
        deleted_calc_run_uc2 = 0
        if calc_run_ids_uc2:
            deleted_calc_run_uc2 = db.query(FactCalculatedResult).filter(
                FactCalculatedResult.calculation_run_id.in_(calc_run_ids_uc2)
            ).delete(synchronize_session=False)
        
        # Delete via run_id (legacy)
        deleted_run_id_uc1 = 0
        if run_ids_uc1:
            deleted_run_id_uc1 = db.query(FactCalculatedResult).filter(
                FactCalculatedResult.run_id.in_(run_ids_uc1)
            ).delete(synchronize_session=False)
        
        deleted_run_id_uc2 = 0
        if run_ids_uc2:
            deleted_run_id_uc2 = db.query(FactCalculatedResult).filter(
                FactCalculatedResult.run_id.in_(run_ids_uc2)
            ).delete(synchronize_session=False)
        
        # Commit the deletions
        db.commit()
        
        print(f"  Use Case 1 (via calculation_run_id): {deleted_calc_run_uc1} rows deleted")
        print(f"  Use Case 1 (via run_id): {deleted_run_id_uc1} rows deleted")
        print(f"  Use Case 1 (TOTAL DELETED): {deleted_calc_run_uc1 + deleted_run_id_uc1} rows")
        print()
        print(f"  Use Case 2 (via calculation_run_id): {deleted_calc_run_uc2} rows deleted")
        print(f"  Use Case 2 (via run_id): {deleted_run_id_uc2} rows deleted")
        print(f"  Use Case 2 (TOTAL DELETED): {deleted_calc_run_uc2 + deleted_run_id_uc2} rows")
        print()
        
        total_deleted = (deleted_calc_run_uc1 + deleted_run_id_uc1 + 
                        deleted_calc_run_uc2 + deleted_run_id_uc2)
        
        print(f"  [SUCCESS] Total rows deleted: {total_deleted}")
        print()
        
        # Step 4: Verify Deletion
        print("STEP 4: Verifying Deletion")
        print("-" * 80)
        
        # Re-fetch IDs after deletion (should be same, but safer)
        remaining_calc_run_ids_uc1 = [r.id for r in db.query(CalculationRun.id).filter(
            CalculationRun.use_case_id == use_case_1.use_case_id
        ).all()]
        remaining_run_ids_uc1 = [r.run_id for r in db.query(UseCaseRun.run_id).filter(
            UseCaseRun.use_case_id == use_case_1.use_case_id
        ).all()]
        
        remaining_uc1 = 0
        if remaining_calc_run_ids_uc1 or remaining_run_ids_uc1:
            filters = []
            if remaining_calc_run_ids_uc1:
                filters.append(FactCalculatedResult.calculation_run_id.in_(remaining_calc_run_ids_uc1))
            if remaining_run_ids_uc1:
                filters.append(FactCalculatedResult.run_id.in_(remaining_run_ids_uc1))
            if filters:
                remaining_uc1 = db.query(FactCalculatedResult).filter(or_(*filters)).count()
        
        remaining_calc_run_ids_uc2 = [r.id for r in db.query(CalculationRun.id).filter(
            CalculationRun.use_case_id == use_case_2.use_case_id
        ).all()]
        remaining_run_ids_uc2 = [r.run_id for r in db.query(UseCaseRun.run_id).filter(
            UseCaseRun.use_case_id == use_case_2.use_case_id
        ).all()]
        
        remaining_uc2 = 0
        if remaining_calc_run_ids_uc2 or remaining_run_ids_uc2:
            filters = []
            if remaining_calc_run_ids_uc2:
                filters.append(FactCalculatedResult.calculation_run_id.in_(remaining_calc_run_ids_uc2))
            if remaining_run_ids_uc2:
                filters.append(FactCalculatedResult.run_id.in_(remaining_run_ids_uc2))
            if filters:
                remaining_uc2 = db.query(FactCalculatedResult).filter(or_(*filters)).count()
        
        print(f"  Use Case 1 remaining rows: {remaining_uc1}")
        print(f"  Use Case 2 remaining rows: {remaining_uc2}")
        print()
        
        if remaining_uc1 == 0 and remaining_uc2 == 0:
            print("  [SUCCESS] All legacy results have been flushed.")
        else:
            print(f"  [WARNING] {remaining_uc1 + remaining_uc2} rows still remain.")
            print("           This may indicate orphaned records or a deletion issue.")
        print()
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Exception during cleanup: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()
        print("=" * 80)
        print("CLEANUP COMPLETE")
        print("=" * 80)


if __name__ == "__main__":
    flush_legacy_results()

