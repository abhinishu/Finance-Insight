"""
Check how many root nodes Project Sterling actually has in the database.
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

# Get all nodes
all_nodes = session.query(DimHierarchy).filter(
    DimHierarchy.atlas_source == structure_id
).all()

print(f"Total nodes for '{structure_id}': {len(all_nodes)}")

# Get root nodes
root_nodes = [n for n in all_nodes if n.parent_node_id is None]

print(f"\nRoot nodes (parent_node_id is None): {len(root_nodes)}")
for i, root in enumerate(root_nodes, 1):
    print(f"  {i}. {root.node_id}: {root.node_name} (depth: {root.depth}, leaf: {root.is_leaf})")

# Check hierarchy_dict that would be built
hierarchy_dict = {node.node_id: node for node in all_nodes}
root_nodes_from_dict = [node_id for node_id, node in hierarchy_dict.items() if node.parent_node_id is None]

print(f"\nRoot nodes from hierarchy_dict: {len(root_nodes_from_dict)}")
print(f"  IDs: {root_nodes_from_dict}")

session.close()

