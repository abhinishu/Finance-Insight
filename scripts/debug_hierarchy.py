"""
Debug script to check hierarchy state in database.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from app.api.dependencies import get_session_factory
from app.models import DimHierarchy, UseCase

def debug_hierarchy(structure_id: str):
    """Debug hierarchy for a given structure_id."""
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        print("=" * 60)
        print(f"Debugging Hierarchy for Structure ID: {structure_id}")
        print("=" * 60)
        
        # Check all nodes for this structure
        nodes = session.query(DimHierarchy).filter(
            DimHierarchy.atlas_source == structure_id
        ).all()
        
        print(f"\nTotal nodes found: {len(nodes)}")
        
        if nodes:
            print("\nAll nodes:")
            for node in nodes:
                print(f"  - {node.node_id} (parent: {node.parent_node_id}, depth: {node.depth}, leaf: {node.is_leaf})")
            
        # Check for root nodes
        root_nodes = [n for n in nodes if n.parent_node_id is None]
        print(f"\nRoot nodes: {len(root_nodes)}")
        for root in root_nodes:
            print(f"  - {root.node_id}: {root.node_name}")
        
        # Check if ROOT node exists with different atlas_source
        root_anywhere = session.query(DimHierarchy).filter(
            DimHierarchy.node_id == 'ROOT'
        ).all()
        if root_anywhere:
            print(f"\nROOT nodes found in database (any structure): {len(root_anywhere)}")
            for r in root_anywhere:
                print(f"  - ROOT (atlas_source: {r.atlas_source})")
        
        # Check which nodes reference ROOT as parent
        nodes_with_root_parent = [n for n in nodes if n.parent_node_id == 'ROOT']
        print(f"\nNodes with ROOT as parent: {len(nodes_with_root_parent)}")
        if nodes_with_root_parent:
            print("  These nodes expect a ROOT node to exist!")
        else:
            print("\n[WARNING] No nodes found for this structure_id!")
            print("This structure needs a template to be created.")
        
        # Check use cases with this structure
        use_cases = session.query(UseCase).filter(
            UseCase.atlas_structure_id == structure_id
        ).all()
        
        print(f"\nUse cases with this structure: {len(use_cases)}")
        for uc in use_cases:
            print(f"  - {uc.name} ({uc.use_case_id})")
        
    finally:
        session.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        structure_id = sys.argv[1]
        debug_hierarchy(structure_id)
    else:
        print("Usage: python scripts/debug_hierarchy.py <structure_id>")
        print("\nExample:")
        print("  python scripts/debug_hierarchy.py MOCK_ATLAS_v1")

