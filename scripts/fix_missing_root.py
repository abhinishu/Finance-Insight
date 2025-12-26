"""
Fix missing ROOT node for a structure.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from app.api.dependencies import get_session_factory
from app.models import DimHierarchy

def fix_missing_root(structure_id: str):
    """Create missing ROOT node for a structure."""
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        print(f"Fixing missing ROOT node for structure: {structure_id}")
        
        # Check if ROOT exists
        existing_root = session.query(DimHierarchy).filter(
            DimHierarchy.atlas_source == structure_id,
            DimHierarchy.parent_node_id.is_(None)
        ).first()
        
        if existing_root:
            print(f"ROOT node already exists: {existing_root.node_id} (atlas_source: {existing_root.atlas_source})")
            if existing_root.atlas_source != structure_id:
                print(f"Updating ROOT node's atlas_source from '{existing_root.atlas_source}' to '{structure_id}'")
                existing_root.atlas_source = structure_id
                session.commit()
                print("ROOT node updated successfully!")
            return
        
        # Check if there are nodes that reference ROOT
        nodes = session.query(DimHierarchy).filter(
            DimHierarchy.atlas_source == structure_id
        ).all()
        
        if not nodes:
            print("No nodes found for this structure. Nothing to fix.")
            return
        
        print(f"Found {len(nodes)} nodes. Creating ROOT node...")
        
        # Check if ROOT exists globally (unique constraint)
        root_global = session.query(DimHierarchy).filter(
            DimHierarchy.node_id == 'ROOT'
        ).first()
        
        if root_global:
            # ROOT exists but for different structure - update it
            print(f"ROOT node exists for structure '{root_global.atlas_source}', updating to '{structure_id}'")
            root_global.atlas_source = structure_id
            session.commit()
            print("ROOT node updated successfully!")
        else:
            # Create ROOT node (shouldn't happen due to unique constraint)
            root_node = DimHierarchy(
                node_id='ROOT',
                parent_node_id=None,
                node_name='Global Trading P&L',
                depth=0,
                is_leaf=False,
                atlas_source=structure_id
            )
            session.add(root_node)
            session.commit()
            print("ROOT node created successfully!")
        
        # Verify
        root_check = session.query(DimHierarchy).filter(
            DimHierarchy.atlas_source == structure_id,
            DimHierarchy.parent_node_id.is_(None)
        ).first()
        
        if root_check:
            print(f"Verification: ROOT node exists: {root_check.node_id}")
        else:
            print("WARNING: ROOT node was not found after creation!")
            
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        structure_id = sys.argv[1]
        fix_missing_root(structure_id)
    else:
        print("Usage: python scripts/fix_missing_root.py <structure_id>")
        print("\nExample:")
        print("  python scripts/fix_missing_root.py MOCK_ATLAS_v1")

