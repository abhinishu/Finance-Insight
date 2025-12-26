"""
Improve node names in Project Sterling hierarchy to be more business-friendly.
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from app.api.dependencies import get_session_factory
from app.models import DimHierarchy, UseCase

def improve_node_names():
    """Update node names to be more business-friendly."""
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
        print(f"Improving node names for: {use_case.name}")
        
        # Name mapping for better display
        name_mapping = {
            'UK_LTD': 'UK Limited',
            'US_HOLDINGS': 'US Holdings',
            'AMER': 'Americas',
            'EMEA': 'EMEA',
            'ALGO': 'Algorithmic Trading',
            'MARKET_MAKING': 'Market Making',
            'VOL': 'Volatility Trading',
            'BOOK_001': 'Book 001',
            'BOOK_002': 'Book 002',
            'BOOK_003': 'Book 003'
        }
        
        # Update entity nodes
        entities = session.query(DimHierarchy).filter(
            DimHierarchy.atlas_source == structure_id,
            DimHierarchy.node_id.like('ENTITY_%'),
            DimHierarchy.depth == 1
        ).all()
        
        for entity in entities:
            # Extract entity name from node_id (e.g., ENTITY_UK_LTD -> UK_LTD)
            entity_key = entity.node_id.replace('ENTITY_', '')
            if entity_key in name_mapping:
                entity.node_name = name_mapping[entity_key]
                print(f"  Updated {entity.node_id}: {entity.node_name}")
        
        # Update region nodes
        regions = session.query(DimHierarchy).filter(
            DimHierarchy.atlas_source == structure_id,
            DimHierarchy.node_id.like('ENTITY_%_%'),
            DimHierarchy.depth == 2
        ).all()
        
        for region in regions:
            # Extract region from node_id (e.g., ENTITY_UK_LTD_AMER -> AMER)
            parts = region.node_id.split('_')
            if len(parts) >= 3:
                region_key = parts[-1]  # Last part is the region
                if region_key in name_mapping:
                    region.node_name = name_mapping[region_key]
                    print(f"  Updated {region.node_id}: {region.node_name}")
        
        # Update strategy nodes
        strategies = session.query(DimHierarchy).filter(
            DimHierarchy.atlas_source == structure_id,
            DimHierarchy.depth == 3
        ).all()
        
        for strategy in strategies:
            # Extract strategy from node_id
            parts = strategy.node_id.split('_')
            if len(parts) >= 4:
                strategy_key = parts[-1]  # Last part is the strategy
                if strategy_key in name_mapping:
                    strategy.node_name = name_mapping[strategy_key]
                    print(f"  Updated {strategy.node_id}: {strategy.node_name}")
        
        # Update book nodes
        books = session.query(DimHierarchy).filter(
            DimHierarchy.atlas_source == structure_id,
            DimHierarchy.depth == 4
        ).all()
        
        for book in books:
            # Extract book from node_id
            parts = book.node_id.split('_')
            if len(parts) >= 5:
                book_key = parts[-1]  # Last part is the book
                if book_key in name_mapping:
                    book.node_name = name_mapping[book_key]
                    print(f"  Updated {book.node_id}: {book.node_name}")
        
        session.commit()
        print("\n[SUCCESS] Node names updated successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    improve_node_names()

