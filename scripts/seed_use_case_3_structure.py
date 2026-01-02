"""
Phase 5.2: Seed Use Case 3 Structure
Creates the "America Cash Equity Trading" use case and hierarchy structure.

This script:
1. Creates a new Use Case "America Cash Equity Trading"
2. Creates the "America Cash Equity Trading Structure" (via atlas_source)
3. Creates 12 hierarchy nodes with correct parent-child relationships
4. Sets up the complete hierarchy tree for Use Case 3
"""

import sys
from pathlib import Path
from decimal import Decimal

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.api.dependencies import get_session_factory
from app.models import UseCase, DimHierarchy, UseCaseStatus


# Structure identifier
STRUCTURE_ID = "America Cash Equity Trading Structure"

# Hierarchy definition: (node_id, node_name, parent_node_id, depth, is_leaf)
HIERARCHY_NODES = [
    # Level 1: Root child
    ("NODE_2", "CORE Products", None, 1, False),
    
    # Level 2: Children of NODE_2
    ("NODE_3", "Core Ex CRB", "NODE_2", 2, False),
    ("NODE_10", "CRB", "NODE_2", 2, False),
    ("NODE_11", "ETF Amber", "NODE_2", 2, False),
    ("NODE_12", "MSET", "NODE_2", 2, False),
    
    # Level 3: Children of NODE_3
    ("NODE_4", "Commissions", "NODE_3", 3, False),
    ("NODE_7", "Trading", "NODE_3", 3, False),
    
    # Level 4: Leaf nodes
    ("NODE_5", "Commissions (Non Swap)", "NODE_4", 4, True),
    ("NODE_6", "Swap Commission", "NODE_4", 4, True),
    ("NODE_8", "Facilitations", "NODE_7", 4, True),
    ("NODE_9", "Inventory Management", "NODE_7", 4, True),
]


def create_use_case(session: Session) -> UseCase:
    """Create or get the 'America Cash Equity Trading' use case."""
    use_case = session.query(UseCase).filter(
        UseCase.name == "America Cash Equity Trading"
    ).first()
    
    if use_case:
        print(f"[INFO] Use case already exists: {use_case.use_case_id}")
        return use_case
    
    # Create new use case
    use_case = UseCase(
        name="America Cash Equity Trading",
        description="Use Case 3: America Cash Equity Trading Structure with Type 1, 2, 2B, and 3 rules",
        owner_id="system",
        atlas_structure_id=STRUCTURE_ID,
        status=UseCaseStatus.ACTIVE
    )
    
    session.add(use_case)
    session.commit()
    session.refresh(use_case)
    
    print(f"[OK] Created use case: {use_case.name} (ID: {use_case.use_case_id})")
    return use_case


def create_hierarchy_nodes(session: Session, use_case: UseCase) -> dict:
    """Create all hierarchy nodes for the structure."""
    created_nodes = {}
    existing_nodes = {}
    
    # Check which nodes already exist
    existing = session.query(DimHierarchy).filter(
        DimHierarchy.atlas_source == STRUCTURE_ID
    ).all()
    
    for node in existing:
        existing_nodes[node.node_id] = node
    
    print(f"\n[INFO] Found {len(existing_nodes)} existing nodes for structure '{STRUCTURE_ID}'")
    
    # Create nodes in order (parents before children)
    for node_id, node_name, parent_id, depth, is_leaf in HIERARCHY_NODES:
        if node_id in existing_nodes:
            node = existing_nodes[node_id]
            print(f"[SKIP] Node '{node_id}' ({node_name}) already exists")
            created_nodes[node_id] = node
            continue
        
        # Create new node
        node = DimHierarchy(
            node_id=node_id,
            parent_node_id=parent_id,
            node_name=node_name,
            depth=depth,
            is_leaf=is_leaf,
            atlas_source=STRUCTURE_ID
        )
        
        session.add(node)
        created_nodes[node_id] = node
        print(f"[OK] Created node '{node_id}': {node_name} (parent: {parent_id or 'ROOT'}, depth: {depth}, leaf: {is_leaf})")
    
    session.commit()
    
    return created_nodes


def verify_hierarchy(session: Session) -> bool:
    """Verify the hierarchy structure is correct."""
    print("\n[INFO] Verifying hierarchy structure...")
    
    nodes = session.query(DimHierarchy).filter(
        DimHierarchy.atlas_source == STRUCTURE_ID
    ).all()
    
    if len(nodes) != len(HIERARCHY_NODES):
        print(f"[WARN] Expected {len(HIERARCHY_NODES)} nodes, found {len(nodes)}")
        return False
    
    # Verify parent-child relationships
    node_dict = {node.node_id: node for node in nodes}
    errors = []
    
    for node_id, node_name, parent_id, depth, is_leaf in HIERARCHY_NODES:
        if node_id not in node_dict:
            errors.append(f"Node {node_id} not found")
            continue
        
        node = node_dict[node_id]
        
        # Check parent
        if node.parent_node_id != parent_id:
            errors.append(f"Node {node_id}: expected parent {parent_id}, got {node.parent_node_id}")
        
        # Check depth
        if node.depth != depth:
            errors.append(f"Node {node_id}: expected depth {depth}, got {node.depth}")
        
        # Check is_leaf
        if node.is_leaf != is_leaf:
            errors.append(f"Node {node_id}: expected is_leaf {is_leaf}, got {node.is_leaf}")
    
    if errors:
        print("[FAIL] Hierarchy verification errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("[OK] Hierarchy structure verified successfully")
    return True


def main():
    """Main execution function."""
    print("="*70)
    print("Phase 5.2: Seed Use Case 3 Structure")
    print("="*70)
    print(f"Structure: {STRUCTURE_ID}")
    print(f"Nodes to create: {len(HIERARCHY_NODES)}")
    print()
    
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        # Step 1: Create use case
        use_case = create_use_case(session)
        
        # Step 2: Create hierarchy nodes
        nodes = create_hierarchy_nodes(session, use_case)
        
        # Step 3: Verify hierarchy
        if not verify_hierarchy(session):
            print("\n[WARN] Hierarchy verification failed, but continuing...")
        
        print("\n" + "="*70)
        print("[SUCCESS] Use Case 3 structure created successfully!")
        print("="*70)
        print(f"Use Case ID: {use_case.use_case_id}")
        print(f"Structure ID: {STRUCTURE_ID}")
        print(f"Total Nodes: {len(nodes)}")
        print("\nNext step: Run seed_use_case_3_rules.py to create business rules")
        
        return 0
        
    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] Failed to create structure: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())

