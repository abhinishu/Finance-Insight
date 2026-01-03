"""
Fix ROOT node for Project Sterling structure.
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from app.api.dependencies import get_session_factory
from app.models import DimHierarchy, UseCase

session_factory = get_session_factory()
session = session_factory()

try:
    # Get Project Sterling use case
    use_case = session.query(UseCase).filter(
        UseCase.name == "Project Sterling - Multi-Dimensional Facts"
    ).first()
    
    if not use_case:
        print("Project Sterling use case not found!")
        exit(1)
    
    structure_id = use_case.atlas_structure_id
    print(f"Project Sterling Structure ID: {structure_id}")
    
    # Check if ROOT exists globally
    root_global = session.query(DimHierarchy).filter(
        DimHierarchy.node_id == 'ROOT'
    ).first()
    
    if root_global:
        print(f"ROOT exists with atlas_source: {root_global.atlas_source}")
        if root_global.atlas_source != structure_id:
            print(f"Updating ROOT atlas_source from '{root_global.atlas_source}' to '{structure_id}'")
            root_global.atlas_source = structure_id
            session.commit()
            print("ROOT updated successfully!")
        else:
            print("ROOT already has correct atlas_source")
    else:
        print("Creating ROOT node...")
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
        print("ROOT created successfully!")
    
    # Verify
    root_check = session.query(DimHierarchy).filter(
        DimHierarchy.atlas_source == structure_id,
        DimHierarchy.node_id == 'ROOT'
    ).first()
    
    if root_check:
        print(f"\nVerification: ROOT exists for '{structure_id}'")
        print(f"  Node ID: {root_check.node_id}")
        print(f"  Node Name: {root_check.node_name}")
        print(f"  Atlas Source: {root_check.atlas_source}")
    else:
        print("\nERROR: ROOT not found after creation/update!")
        
except Exception as e:
    session.rollback()
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()



