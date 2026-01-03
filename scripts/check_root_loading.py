"""
Check if ROOT is being loaded in hierarchy_nodes.
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from app.api.dependencies import get_session_factory
from app.models import DimHierarchy

session_factory = get_session_factory()
session = session_factory()

structure_id = "Mock Atlas Structure v1"

# Simulate what the API does
hierarchy_nodes = session.query(DimHierarchy).filter(
    DimHierarchy.atlas_source == structure_id
).all()

print(f"Total nodes loaded: {len(hierarchy_nodes)}")

# Check for ROOT
root_in_nodes = [n for n in hierarchy_nodes if n.node_id == 'ROOT']
print(f"ROOT in hierarchy_nodes: {len(root_in_nodes)}")

if root_in_nodes:
    root = root_in_nodes[0]
    print(f"  ROOT node_id: {root.node_id}")
    print(f"  ROOT parent_node_id: {root.parent_node_id}")
    print(f"  ROOT atlas_source: {root.atlas_source}")
else:
    print("  ROOT NOT FOUND in hierarchy_nodes!")
    # Check if ROOT exists in DB
    root_db = session.query(DimHierarchy).filter(
        DimHierarchy.node_id == 'ROOT'
    ).first()
    if root_db:
        print(f"  But ROOT exists in DB with atlas_source: {root_db.atlas_source}")

# Check root nodes
root_nodes = [n for n in hierarchy_nodes if n.parent_node_id is None]
print(f"\nRoot nodes (parent_node_id is None): {len(root_nodes)}")
print(f"  IDs: {[r.node_id for r in root_nodes[:15]]}")

session.close()



