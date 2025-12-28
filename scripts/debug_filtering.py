"""
Debug why TRADE nodes are still appearing.
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

print(f"Total nodes from DB: {len(hierarchy_nodes)}")

# Filter
business_nodes = [
    node for node in hierarchy_nodes 
    if not node.node_id.startswith('TRADE_') 
    and not node.node_id.startswith('STERLING_RULE')
]

print(f"Business nodes after filter: {len(business_nodes)}")
print(f"Filtered out: {len(hierarchy_nodes) - len(business_nodes)} nodes")

hierarchy_dict = {node.node_id: node for node in business_nodes}
print(f"hierarchy_dict size: {len(hierarchy_dict)}")
print(f"TRADE nodes in hierarchy_dict: {[k for k in hierarchy_dict.keys() if k.startswith('TRADE_')]}")
print(f"STERLING_RULE nodes in hierarchy_dict: {[k for k in hierarchy_dict.keys() if k.startswith('STERLING_RULE')]}")

# Build children_dict
children_dict = {}
for node in business_nodes:
    if node.parent_node_id:
        parent_node = hierarchy_dict.get(node.parent_node_id)
        if parent_node and not parent_node.node_id.startswith('TRADE_') and not parent_node.node_id.startswith('STERLING_RULE'):
            if node.parent_node_id not in children_dict:
                children_dict[node.parent_node_id] = []
            children_dict[node.parent_node_id].append(node.node_id)

print(f"\nchildren_dict['ROOT']: {children_dict.get('ROOT', [])}")
print(f"TRADE nodes in children_dict['ROOT']: {[c for c in children_dict.get('ROOT', []) if c.startswith('TRADE_')]}")

session.close()


