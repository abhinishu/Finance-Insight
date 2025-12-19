"""
Script to create a test use case with sample rules for testing.
"""

import sys
from pathlib import Path
from uuid import uuid4

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_database_url
from app.models import DimHierarchy, MetadataRule, UseCase, UseCaseStatus


def create_test_use_case(session, name: str = "Test Use Case", owner_id: str = "test_user"):
    """
    Create a test use case with sample rules.
    
    Args:
        session: SQLAlchemy session
        name: Use case name
        owner_id: Owner user ID
    
    Returns:
        Use case object
    """
    # Check if hierarchy exists
    hierarchy_count = session.query(DimHierarchy).count()
    if hierarchy_count == 0:
        print("Error: No hierarchy found. Please run generate_mock_data.py first.")
        return None
    
    # Get the atlas_structure_id from existing hierarchy
    sample_node = session.query(DimHierarchy).first()
    atlas_structure_id = sample_node.atlas_source if sample_node else "MOCK_ATLAS_v1"
    
    # Create use case
    use_case = UseCase(
        use_case_id=uuid4(),
        name=name,
        description="Test use case for validation and testing",
        owner_id=owner_id,
        atlas_structure_id=atlas_structure_id,
        status=UseCaseStatus.DRAFT
    )
    session.add(use_case)
    session.commit()
    
    print(f"✓ Created use case: {use_case.use_case_id}")
    print(f"  Name: {use_case.name}")
    print(f"  Atlas Structure: {atlas_structure_id}")
    
    return use_case


def add_sample_rules(session, use_case_id, num_rules: int = 3):
    """
    Add sample rules to a use case for testing.
    
    Args:
        session: SQLAlchemy session
        use_case_id: Use case UUID
        num_rules: Number of sample rules to create
    """
    # Get some leaf nodes
    leaf_nodes = session.query(DimHierarchy).filter(DimHierarchy.is_leaf == True).limit(num_rules).all()
    
    if len(leaf_nodes) < num_rules:
        print(f"Warning: Only {len(leaf_nodes)} leaf nodes available, creating {len(leaf_nodes)} rules")
    
    sample_rules = [
        {
            'node_id': 'CC_001',
            'sql_where': "cc_id = 'CC_001'",
            'logic_en': "Include all transactions for Cost Center CC_001",
        },
        {
            'node_id': 'CC_002',
            'sql_where': "cc_id = 'CC_002' AND strategy_id = 'STRAT_01'",
            'logic_en': "Include CC_002 transactions for Strategy 01 only",
        },
        {
            'node_id': 'CC_003',
            'sql_where': "cc_id IN ('CC_003', 'CC_004', 'CC_005')",
            'logic_en': "Combine CC_003, CC_004, and CC_005",
        },
    ]
    
    rules_created = 0
    for i, rule_data in enumerate(sample_rules[:num_rules]):
        # Check if node exists
        node = session.query(DimHierarchy).filter(DimHierarchy.node_id == rule_data['node_id']).first()
        if not node:
            print(f"Warning: Node {rule_data['node_id']} not found, skipping rule")
            continue
        
        # Check if rule already exists
        existing = session.query(MetadataRule).filter(
            MetadataRule.use_case_id == use_case_id,
            MetadataRule.node_id == rule_data['node_id']
        ).first()
        
        if existing:
            print(f"  Rule for {rule_data['node_id']} already exists, skipping")
            continue
        
        rule = MetadataRule(
            use_case_id=use_case_id,
            node_id=rule_data['node_id'],
            sql_where=rule_data['sql_where'],
            logic_en=rule_data['logic_en'],
            last_modified_by="test_user"
        )
        session.add(rule)
        rules_created += 1
        print(f"  ✓ Created rule for {rule_data['node_id']}: {rule_data['logic_en']}")
    
    session.commit()
    print(f"\n✓ Created {rules_created} sample rules")
    
    return rules_created


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create a test use case with sample rules')
    parser.add_argument('--name', type=str, default='Test Use Case', help='Use case name')
    parser.add_argument('--owner-id', type=str, default='test_user', help='Owner user ID')
    parser.add_argument('--add-rules', action='store_true', help='Add sample rules to use case')
    parser.add_argument('--num-rules', type=int, default=3, help='Number of sample rules to create')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Finance-Insight Test Use Case Creation")
    print("=" * 60)
    
    # Get database URL
    db_url = get_database_url()
    
    # Create engine and session
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create use case
        use_case = create_test_use_case(session, name=args.name, owner_id=args.owner_id)
        
        if not use_case:
            return 1
        
        # Add sample rules if requested
        if args.add_rules:
            print(f"\nAdding {args.num_rules} sample rules...")
            add_sample_rules(session, use_case.use_case_id, num_rules=args.num_rules)
        
        print("\n" + "=" * 60)
        print("Test Use Case Created Successfully!")
        print("=" * 60)
        print(f"\nUse Case ID: {use_case.use_case_id}")
        print(f"Name: {use_case.name}")
        print(f"Owner: {use_case.owner_id}")
        print(f"\nTo run calculation:")
        print(f"  python scripts/run_calculation.py --use-case-id {use_case.use_case_id}")
        
        return 0
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())

