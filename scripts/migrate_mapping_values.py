"""
Migration Script: Add and Populate mapping_value Column

This script implements the "Explicit Mapping" pattern:
1. Adds mapping_value column to dim_hierarchy table
2. Populates mapping_value for leaf nodes in Use Cases 1 & 2
3. Logic: Extract suffix from node_id and construct TRADE_{suffix}
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from app.database import SessionLocal, engine
from app.models import (
    UseCase,
    DimHierarchy
)

def add_mapping_value_column(db: Session):
    """
    Add mapping_value column to dim_hierarchy table if it doesn't exist.
    """
    print("STEP 1: Adding mapping_value Column")
    print("-" * 80)
    
    # Check if column already exists
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('dim_hierarchy')]
    
    if 'mapping_value' in columns:
        print("  [INFO] Column 'mapping_value' already exists. Skipping creation.")
        return
    
    # Add column using raw SQL
    try:
        db.execute(text("""
            ALTER TABLE dim_hierarchy 
            ADD COLUMN mapping_value VARCHAR NULL
        """))
        db.commit()
        print("  [SUCCESS] Column 'mapping_value' added to dim_hierarchy table")
    except Exception as e:
        db.rollback()
        print(f"  [ERROR] Failed to add column: {e}")
        raise


def populate_mapping_values(db: Session):
    """
    Populate mapping_value for leaf nodes in Use Cases 1 & 2.
    Logic: Extract suffix from node_id and construct TRADE_{suffix}
    """
    print()
    print("STEP 2: Populating mapping_value for Leaf Nodes")
    print("-" * 80)
    
    # Find Use Cases 1 & 2
    use_case_1 = db.query(UseCase).filter(
        UseCase.name.ilike('%America Trading%')
    ).first()
    
    use_case_2 = db.query(UseCase).filter(
        UseCase.name.ilike('%Project Sterling%')
    ).first()
    
    if not use_case_1:
        print("  [ERROR] Use Case 1 (America Trading P&L) not found!")
        return
    
    if not use_case_2:
        print("  [ERROR] Use Case 2 (Project Sterling) not found!")
        return
    
    print(f"  Use Case 1: {use_case_1.name} (ID: {use_case_1.use_case_id})")
    print(f"  Use Case 2: {use_case_2.name} (ID: {use_case_2.use_case_id})")
    print()
    
    # Process Use Case 1
    print("  Processing Use Case 1...")
    atlas_source_1 = use_case_1.atlas_structure_id
    leaf_nodes_1 = db.query(DimHierarchy).filter(
        DimHierarchy.atlas_source == atlas_source_1,
        DimHierarchy.is_leaf == True
    ).all()
    
    updated_count_1 = 0
    for node in leaf_nodes_1:
        # Extract suffix from node_id (e.g., CC_AMER_CASH_NY_001 -> 001)
        parts = node.node_id.split('_')
        if len(parts) > 1:
            suffix = parts[-1]
            
            # If suffix is numeric, construct TRADE_{suffix}
            try:
                # Validate it's numeric
                int(suffix)
                mapping_value = f"TRADE_{suffix}"
                
                # Update the node
                node.mapping_value = mapping_value
                updated_count_1 += 1
                
                if updated_count_1 <= 5:  # Print first 5 as samples
                    print(f"    Updated Node '{node.node_id}' -> Mapping Value: '{mapping_value}'")
            except ValueError:
                # Suffix is not numeric, skip
                print(f"    [SKIP] Node '{node.node_id}' has non-numeric suffix '{suffix}'")
    
    # Process Use Case 2
    print()
    print("  Processing Use Case 2...")
    atlas_source_2 = use_case_2.atlas_structure_id
    leaf_nodes_2 = db.query(DimHierarchy).filter(
        DimHierarchy.atlas_source == atlas_source_2,
        DimHierarchy.is_leaf == True
    ).all()
    
    updated_count_2 = 0
    for node in leaf_nodes_2:
        # Extract suffix from node_id
        parts = node.node_id.split('_')
        if len(parts) > 1:
            suffix = parts[-1]
            
            # If suffix is numeric, construct TRADE_{suffix}
            try:
                int(suffix)
                mapping_value = f"TRADE_{suffix}"
                
                # Update the node
                node.mapping_value = mapping_value
                updated_count_2 += 1
                
                if updated_count_2 <= 5:  # Print first 5 as samples
                    print(f"    Updated Node '{node.node_id}' -> Mapping Value: '{mapping_value}'")
            except ValueError:
                print(f"    [SKIP] Node '{node.node_id}' has non-numeric suffix '{suffix}'")
    
    # Commit all updates
    try:
        db.commit()
        print()
        print(f"  [SUCCESS] Updated {updated_count_1} nodes for Use Case 1")
        print(f"  [SUCCESS] Updated {updated_count_2} nodes for Use Case 2")
        print(f"  [SUCCESS] Total: {updated_count_1 + updated_count_2} nodes updated")
    except Exception as e:
        db.rollback()
        print(f"  [ERROR] Failed to commit updates: {e}")
        raise


def verify_migration(db: Session):
    """
    Verify the migration by checking a sample of updated nodes.
    """
    print()
    print("STEP 3: Verification")
    print("-" * 80)
    
    # Check Use Case 1
    use_case_1 = db.query(UseCase).filter(
        UseCase.name.ilike('%America Trading%')
    ).first()
    
    if use_case_1:
        atlas_source_1 = use_case_1.atlas_structure_id
        sample_nodes = db.query(DimHierarchy).filter(
            DimHierarchy.atlas_source == atlas_source_1,
            DimHierarchy.is_leaf == True,
            DimHierarchy.mapping_value.isnot(None)
        ).limit(5).all()
        
        print(f"  Sample nodes with mapping_value (Use Case 1):")
        for node in sample_nodes:
            print(f"    {node.node_id} -> {node.mapping_value}")
    
    print()
    print("  [SUCCESS] Migration verification complete")


def run_migration():
    """
    Main migration function.
    """
    print("=" * 80)
    print("MIGRATION: Add and Populate mapping_value Column")
    print("=" * 80)
    print()
    
    db: Session = SessionLocal()
    
    try:
        add_mapping_value_column(db)
        populate_mapping_values(db)
        verify_migration(db)
        
        print()
        print("=" * 80)
        print("MIGRATION COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()


