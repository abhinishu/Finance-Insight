"""
Project Sterling - Multi-Dimensional Fact Hydration
Imports CSV data into fact_pnl_entries table with UPSERT logic.
"""

import csv
import json
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.api.dependencies import get_session_factory
from app.models import FactPnlEntries, UseCase


def get_csv_path() -> Path:
    """Get the path to the sterling_facts.csv file."""
    project_root = Path(__file__).parent.parent
    return project_root / "metadata" / "seed" / "sterling_facts.csv"


def import_sterling_facts(
    session: Optional[Session] = None,
    csv_path: Optional[Path] = None,
    use_case_id: Optional[UUID] = None
) -> Dict:
    """
    Import Sterling facts from CSV and UPSERT into fact_pnl_entries.
    
    Args:
        session: Optional SQLAlchemy session. If None, creates a new one.
        csv_path: Optional path to CSV file. If None, uses default sterling_facts.csv
        use_case_id: Optional use case ID. If None, uses first available use case or creates one.
    
    Returns:
        Dictionary with import statistics: {"imported": count, "updated": count, "skipped": count, "total": count}
    """
    if csv_path is None:
        csv_path = get_csv_path()
    
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    # Use provided session or create new one
    should_close = False
    if session is None:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        should_close = True
    
    try:
        # Get or create use case
        if use_case_id is None:
            # Try to get first available use case
            use_case = session.query(UseCase).first()
            if use_case is None:
                # Create a default use case for Sterling project
                from app.models import UseCaseStatus
                use_case = UseCase(
                    name="Project Sterling - Multi-Dimensional Facts",
                    description="High-complexity dataset for F2B testing",
                    owner_id="sterling_import",
                    atlas_structure_id="Mock Atlas Structure v1",  # Default structure
                    status=UseCaseStatus.ACTIVE
                )
                session.add(use_case)
                session.flush()  # Get the ID without committing
                print(f"Created new use case: {use_case.use_case_id}")
            use_case_id = use_case.use_case_id
        else:
            # Verify use case exists
            use_case = session.query(UseCase).filter(UseCase.use_case_id == use_case_id).first()
            if use_case is None:
                raise ValueError(f"Use case '{use_case_id}' not found")
        
        imported = 0
        updated = 0
        skipped = 0
        total = 0
        
        # Read CSV file
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                total += 1
                
                try:
                    # Parse CSV row
                    pnl_date = date.fromisoformat(row['pnl_date'])
                    category_code = row['category_code']
                    daily_amount = Decimal(row['daily_amount'])
                    wtd_amount = Decimal(row['wtd_amount'])
                    ytd_amount = Decimal(row['ytd_amount'])
                    scenario = row['scenario'].upper()  # ACTUAL or PRIOR
                    amount = Decimal(row.get('amount', row['daily_amount']))  # Legacy column
                    
                    # Build audit_metadata from dimension columns
                    audit_metadata = {
                        'legal_entity': row.get('legal_entity', ''),
                        'region': row.get('region', ''),
                        'strategy': row.get('strategy', ''),
                        'risk_officer': row.get('risk_officer', ''),
                        'source': 'sterling_facts.csv',
                        'import_timestamp': date.today().isoformat()
                    }
                    
                    # Check if entry exists (UPSERT logic)
                    # Match on: use_case_id, pnl_date, category_code, scenario
                    existing = session.query(FactPnlEntries).filter(
                        and_(
                            FactPnlEntries.use_case_id == use_case_id,
                            FactPnlEntries.pnl_date == pnl_date,
                            FactPnlEntries.category_code == category_code,
                            FactPnlEntries.scenario == scenario
                        )
                    ).first()
                    
                    if existing:
                        # Update existing entry
                        existing.daily_amount = daily_amount
                        existing.wtd_amount = wtd_amount
                        existing.ytd_amount = ytd_amount
                        existing.amount = amount
                        existing.audit_metadata = audit_metadata
                        updated += 1
                    else:
                        # Create new entry
                        new_entry = FactPnlEntries(
                            use_case_id=use_case_id,
                            pnl_date=pnl_date,
                            category_code=category_code,
                            daily_amount=daily_amount,
                            wtd_amount=wtd_amount,
                            ytd_amount=ytd_amount,
                            amount=amount,
                            scenario=scenario,
                            audit_metadata=audit_metadata
                        )
                        session.add(new_entry)
                        imported += 1
                
                except Exception as e:
                    print(f"Error processing row {total}: {e}")
                    skipped += 1
                    continue
        
        session.commit()
        
        # Get final count
        final_count = session.query(FactPnlEntries).filter(
            FactPnlEntries.use_case_id == use_case_id
        ).count()
        
        return {
            "imported": imported,
            "updated": updated,
            "skipped": skipped,
            "total_processed": total,
            "final_row_count": final_count,
            "use_case_id": str(use_case_id)
        }
    
    except Exception as e:
        session.rollback()
        raise e
    
    finally:
        if should_close:
            session.close()


if __name__ == "__main__":
    """
    CLI interface for Sterling facts import.
    Usage:
        python scripts/import_sterling_facts.py                    # Import with auto use case
        python scripts/import_sterling_facts.py <use_case_id>     # Import to specific use case
    """
    import sys
    
    use_case_id_arg = None
    if len(sys.argv) > 1:
        try:
            use_case_id_arg = UUID(sys.argv[1])
        except ValueError:
            print(f"Invalid UUID format: {sys.argv[1]}")
            sys.exit(1)
    
    print("=" * 60)
    print("Project Sterling - Multi-Dimensional Fact Hydration")
    print("=" * 60)
    print("Importing Sterling facts from CSV...")
    print()
    
    try:
        result = import_sterling_facts(use_case_id=use_case_id_arg)
        
        print("[SUCCESS] Import complete:")
        print(f"   - Imported: {result['imported']}")
        print(f"   - Updated: {result['updated']}")
        print(f"   - Skipped: {result['skipped']}")
        print(f"   - Total Processed: {result['total_processed']}")
        print(f"   - Final Row Count in DB: {result['final_row_count']}")
        print(f"   - Use Case ID: {result['use_case_id']}")
        print()
        print("=" * 60)
        print(f"[RESULT] Total rows injected: {result['final_row_count']}")
        print("=" * 60)
    
    except Exception as e:
        print(f"[ERROR] Import failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

