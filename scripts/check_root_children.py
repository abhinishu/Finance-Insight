"""
Check ROOT node's children to verify business hierarchy structure.
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from app.api.dependencies import get_session_factory
from app.models import DimHierarchy, UseCase

session_factory = get_session_factory()
session = session_factory()

use_case = session.query(UseCase).filter(
    UseCase.name == "Project Sterling - Multi-Dimensional Facts"
).first()

structure_id = use_case.atlas_structure_id

root = session.query(DimHierarchy).filter(
    DimHierarchy.atlas_source == structure_id,
    DimHierarchy.node_id == 'ROOT'
).first()

if root:
    print(f"ROOT Node: {root.node_name}")
    print(f"Children (direct):")
    
    children = session.query(DimHierarchy).filter(
        DimHierarchy.atlas_source == structure_id,
        DimHierarchy.parent_node_id == 'ROOT'
    ).all()
    
    print(f"  Total: {len(children)}")
    for child in sorted(children, key=lambda x: x.node_name):
        print(f"    - {child.node_name} ({child.node_id}, depth: {child.depth})")
        
        # Show grandchildren for entities
        if child.depth == 1:
            grandchildren = session.query(DimHierarchy).filter(
                DimHierarchy.atlas_source == structure_id,
                DimHierarchy.parent_node_id == child.node_id
            ).all()
            for grandchild in sorted(grandchildren, key=lambda x: x.node_name):
                print(f"      - {grandchild.node_name} ({grandchild.node_id}, depth: {grandchild.depth})")
else:
    print("ROOT node not found!")

session.close()

