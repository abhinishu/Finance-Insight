"""
Seed Manager for Finance-Insight
Handles portable metadata import/export for environment synchronization.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.api.dependencies import get_session_factory
from app.models import DimDictionary


def get_seed_path() -> Path:
    """Get the path to the metadata/seed directory."""
    project_root = Path(__file__).parent.parent
    return project_root / "metadata" / "seed"


def get_backup_path() -> Path:
    """Get the path to the metadata/backups directory."""
    project_root = Path(__file__).parent.parent
    backup_dir = project_root / "metadata" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def import_from_json(session: Optional[Session] = None, file_path: Optional[Path] = None) -> Dict:
    """
    Import dictionary definitions from JSON file and UPSERT into dim_dictionary.
    
    Args:
        session: Optional SQLAlchemy session. If None, creates a new one.
        file_path: Optional path to JSON file. If None, uses default dictionary_definitions.json
    
    Returns:
        Dictionary with import statistics: {"imported": count, "updated": count, "skipped": count}
    """
    if file_path is None:
        file_path = get_seed_path() / "dictionary_definitions.json"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Seed file not found: {file_path}")
    
    # Read JSON file
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if 'definitions' not in data:
        raise ValueError("JSON file must contain a 'definitions' array")
    
    # Use provided session or create new one
    should_close = False
    if session is None:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        should_close = True
    
    try:
        imported = 0
        updated = 0
        skipped = 0
        
        for entry in data['definitions']:
            category = entry.get('category')
            tech_id = entry.get('tech_id')
            display_name = entry.get('display_name')
            
            if not all([category, tech_id, display_name]):
                skipped += 1
                continue
            
            # Check if entry exists
            existing = session.query(DimDictionary).filter(
                DimDictionary.category == category,
                DimDictionary.tech_id == tech_id
            ).first()
            
            if existing:
                # Update existing entry
                existing.display_name = display_name
                updated += 1
            else:
                # Create new entry
                new_entry = DimDictionary(
                    id=uuid4(),
                    category=category,
                    tech_id=tech_id,
                    display_name=display_name
                )
                session.add(new_entry)
                imported += 1
        
        session.commit()
        
        return {
            "imported": imported,
            "updated": updated,
            "skipped": skipped,
            "total": len(data['definitions'])
        }
    
    except Exception as e:
        session.rollback()
        raise e
    
    finally:
        if should_close:
            session.close()


def export_to_json(session: Optional[Session] = None, output_path: Optional[Path] = None) -> Path:
    """
    Export current dim_dictionary data to JSON file in metadata/backups/.
    
    Args:
        session: Optional SQLAlchemy session. If None, creates a new one.
        output_path: Optional output path. If None, creates timestamped file in backups/
    
    Returns:
        Path to the exported JSON file
    """
    # Use provided session or create new one
    should_close = False
    if session is None:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        should_close = True
    
    try:
        # Query all dictionary entries
        entries = session.query(DimDictionary).order_by(
            DimDictionary.category,
            DimDictionary.tech_id
        ).all()
        
        # Build JSON structure
        definitions = []
        for entry in entries:
            definitions.append({
                "category": entry.category,
                "tech_id": entry.tech_id,
                "display_name": entry.display_name
            })
        
        data = {
            "exported_at": datetime.utcnow().isoformat(),
            "total_entries": len(definitions),
            "definitions": definitions
        }
        
        # Determine output path
        if output_path is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_path = get_backup_path() / f"dictionary_backup_{timestamp}.json"
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    finally:
        if should_close:
            session.close()


if __name__ == "__main__":
    """
    CLI interface for seed manager.
    Usage:
        python scripts/seed_manager.py import    # Import from seed file
        python scripts/seed_manager.py export     # Export to backup file
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python scripts/seed_manager.py [import|export]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "import":
        print("Importing dictionary definitions from seed file...")
        result = import_from_json()
        print(f"✅ Import complete:")
        print(f"   - Imported: {result['imported']}")
        print(f"   - Updated: {result['updated']}")
        print(f"   - Skipped: {result['skipped']}")
        print(f"   - Total: {result['total']}")
    
    elif command == "export":
        print("Exporting dictionary definitions to backup file...")
        output_path = export_to_json()
        print(f"✅ Export complete: {output_path}")
    
    else:
        print(f"Unknown command: {command}")
        print("Usage: python scripts/seed_manager.py [import|export]")
        sys.exit(1)
