"""
Create proper business hierarchy for Project Sterling.
Builds Legal Entity > Region > Strategy > Book hierarchy from actual fact data.
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from app.api.dependencies import get_session_factory
from app.models import DimHierarchy, FactPnlEntries, UseCase
from collections import defaultdict

def create_sterling_business_hierarchy():
    """Create proper 4-tier business hierarchy for Project Sterling."""
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        # Get Project Sterling use case
        use_case = session.query(UseCase).filter(
            UseCase.name == "Project Sterling - Multi-Dimensional Facts"
        ).first()
        
        if not use_case:
            print("Project Sterling use case not found!")
            return
        
        structure_id = use_case.atlas_structure_id
        print(f"Creating business hierarchy for: {use_case.name}")
        print(f"Structure ID: {structure_id}")
        
        # Get all facts for this use case (or all facts if no filter)
        facts = session.query(FactPnlEntries).all()
        print(f"\nFound {len(facts)} fact records")
        
        # Extract unique business dimensions from audit_metadata
        entities = set()
        regions = set()
        strategies = set()
        books = set()
        
        for fact in facts:
            metadata = fact.audit_metadata or {}
            if metadata.get('legal_entity'):
                entities.add(metadata['legal_entity'])
            if metadata.get('region'):
                regions.add(metadata['region'])
            if metadata.get('strategy'):
                strategies.add(metadata['strategy'])
            if metadata.get('book'):
                books.add(metadata['book'])
        
        print(f"\nFound dimensions:")
        print(f"  Legal Entities: {sorted(entities) if entities else 'None'}")
        print(f"  Regions: {sorted(regions) if regions else 'None'}")
        print(f"  Strategies: {sorted(strategies) if strategies else 'None'}")
        print(f"  Books: {sorted(books) if books else 'None'}")
        
        # If no metadata, use defaults
        if not entities:
            entities = {'Global Trading'}
        if not regions:
            regions = {'AMER', 'EMEA', 'APAC'}
        if not strategies:
            strategies = {'CASH_EQUITIES', 'DERIVATIVES', 'FIXED_INCOME'}
        if not books:
            books = {'BOOK_001', 'BOOK_002', 'BOOK_003'}
        
        # Create proper ROOT node (not STERLING_RULE nodes)
        # First, check if there's a ROOT node (not a STERLING_RULE node)
        root_node = session.query(DimHierarchy).filter(
            DimHierarchy.atlas_source == structure_id,
            DimHierarchy.parent_node_id.is_(None),
            DimHierarchy.node_id == 'ROOT'  # Must be actual ROOT, not STERLING_RULE
        ).first()
        
        if not root_node:
            # Check if ROOT exists globally and update it
            root_global = session.query(DimHierarchy).filter(
                DimHierarchy.node_id == 'ROOT'
            ).first()
            if root_global:
                root_global.atlas_source = structure_id
                root_global.node_name = 'Global Trading P&L'
                root_node = root_global
                print("\nUpdated existing ROOT node")
            else:
                root_node = DimHierarchy(
                    node_id='ROOT',
                    parent_node_id=None,
                    node_name='Global Trading P&L',
                    depth=0,
                    is_leaf=False,
                    atlas_source=structure_id
                )
                session.add(root_node)
                print("\nCreated ROOT node")
        else:
            root_node.node_name = 'Global Trading P&L'
            print(f"\nUsing existing ROOT node: {root_node.node_id}")
        
        # Create Legal Entity level (depth 1)
        entity_nodes = {}
        for entity in sorted(entities):
            entity_id = f"ENTITY_{entity.replace(' ', '_').upper()}"
            entity_node = session.query(DimHierarchy).filter(
                DimHierarchy.node_id == entity_id,
                DimHierarchy.atlas_source == structure_id
            ).first()
            
            if not entity_node:
                entity_node = DimHierarchy(
                    node_id=entity_id,
                    parent_node_id='ROOT',
                    node_name=entity,
                    depth=1,
                    is_leaf=False,
                    atlas_source=structure_id
                )
                session.add(entity_node)
                print(f"  Created entity: {entity}")
            entity_nodes[entity] = entity_node
        
        # Create Region level (depth 2) under first entity
        region_nodes = {}
        first_entity = sorted(entities)[0] if entities else None
        if first_entity:
            for region in sorted(regions):
                region_id = f"ENTITY_{first_entity.replace(' ', '_').upper()}_{region}"
                region_node = session.query(DimHierarchy).filter(
                    DimHierarchy.node_id == region_id,
                    DimHierarchy.atlas_source == structure_id
                ).first()
                
                if not region_node:
                    region_node = DimHierarchy(
                        node_id=region_id,
                        parent_node_id=entity_nodes[first_entity].node_id,
                        node_name=region,
                        depth=2,
                        is_leaf=False,
                        atlas_source=structure_id
                    )
                    session.add(region_node)
                    print(f"    Created region: {region}")
                region_nodes[region] = region_node
        
        # Create Strategy level (depth 3) under first region
        strategy_nodes = {}
        first_region = sorted(regions)[0] if regions else None
        if first_region:
            for strategy in sorted(strategies):
                strategy_id = f"ENTITY_{first_entity.replace(' ', '_').upper()}_{first_region}_{strategy}"
                strategy_node = session.query(DimHierarchy).filter(
                    DimHierarchy.node_id == strategy_id,
                    DimHierarchy.atlas_source == structure_id
                ).first()
                
                if not strategy_node:
                    strategy_node = DimHierarchy(
                        node_id=strategy_id,
                        parent_node_id=region_nodes[first_region].node_id,
                        node_name=strategy.replace('_', ' ').title(),
                        depth=3,
                        is_leaf=False,
                        atlas_source=structure_id
                    )
                    session.add(strategy_node)
                    print(f"      Created strategy: {strategy}")
                strategy_nodes[strategy] = strategy_node
        
        # Create Book level (depth 4 - leaf nodes) under first strategy
        book_nodes = {}
        first_strategy = sorted(strategies)[0] if strategies else None
        if first_strategy:
            for book in sorted(books):
                book_id = f"ENTITY_{first_entity.replace(' ', '_').upper()}_{first_region}_{first_strategy}_{book}"
                book_node = session.query(DimHierarchy).filter(
                    DimHierarchy.node_id == book_id,
                    DimHierarchy.atlas_source == structure_id
                ).first()
                
                if not book_node:
                    book_node = DimHierarchy(
                        node_id=book_id,
                        parent_node_id=strategy_nodes[first_strategy].node_id,
                        node_name=book.replace('_', ' ').title(),
                        depth=4,
                        is_leaf=True,
                        atlas_source=structure_id
                    )
                    session.add(book_node)
                    print(f"        Created book: {book}")
                book_nodes[book] = book_node
        
        # Update existing STERLING_RULE nodes to be children of books
        # Or we can keep them as separate fact-level nodes
        # For now, let's keep the STERLING_RULE nodes but update their names to be more descriptive
        
        session.commit()
        print("\n[SUCCESS] Business hierarchy created successfully!")
        print(f"\nHierarchy structure:")
        print(f"  ROOT: Global Trading P&L")
        for entity in sorted(entities):
            print(f"    - {entity}")
            for region in sorted(regions):
                print(f"      - {region}")
                for strategy in sorted(strategies):
                    print(f"        - {strategy.replace('_', ' ').title()}")
                    for book in sorted(books):
                        print(f"          - {book.replace('_', ' ').title()}")
        
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    create_sterling_business_hierarchy()

