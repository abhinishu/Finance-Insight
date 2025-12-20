"""
Mock Data Generation for Finance-Insight
Generates 1,000 P&L fact rows and a ragged hierarchy with 50 leaf nodes.
Uses Decimal for all numeric calculations to ensure precision.
"""

import random
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Tuple
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import DimHierarchy, FactPnlGold, HierarchyBridge


def generate_fact_rows(count: int = 1000, hierarchy: List[Dict] = None) -> List[Dict]:
    """
    Generate mock fact rows for fact_pnl_gold table.
    
    Args:
        count: Number of rows to generate (default: 1000)
        hierarchy: Optional hierarchy list to extract cost center IDs from
    
    Returns:
        List of dictionaries representing fact rows
    """
    facts = []
    
    # Extract cost center IDs from hierarchy if provided
    if hierarchy:
        cost_centers = [h['node_id'] for h in hierarchy if h['is_leaf']]
        if not cost_centers:
            # Fallback if no leaf nodes found
            cost_centers = [f"CC_{i:03d}" for i in range(1, 51)]
    else:
        # Fallback: generate generic cost centers
        cost_centers = [f"CC_{i:03d}" for i in range(1, 51)]  # CC_001 to CC_050 (50 cost centers)
    
    # Dimension ranges
    accounts = [f"ACC_{i:03d}" for i in range(1, 11)]  # ACC_001 to ACC_010 (10 accounts)
    books = [f"BOOK_{i:02d}" for i in range(1, 11)]  # BOOK_01 to BOOK_10 (10 books)
    strategies = [f"STRAT_{i:02d}" for i in range(1, 6)]  # STRAT_01 to STRAT_05 (5 strategies)
    
    # Date range: 2024-01-01 to 2024-12-31
    start_date = date(2024, 1, 1)
    end_date = date(2024, 12, 31)
    date_range = (end_date - start_date).days
    
    for _ in range(count):
        # Generate random trade date
        random_days = random.randint(0, date_range)
        trade_date = start_date + timedelta(days=random_days)
        
        # Generate P&L values using Decimal for precision
        daily_pnl = Decimal(str(random.uniform(-100000, 100000))).quantize(Decimal('0.01'))
        mtd_pnl = Decimal(str(random.uniform(-500000, 500000))).quantize(Decimal('0.01'))
        ytd_pnl = Decimal(str(random.uniform(-2000000, 2000000))).quantize(Decimal('0.01'))
        pytd_pnl = Decimal(str(random.uniform(-1800000, 1800000))).quantize(Decimal('0.01'))
        
        fact_row = {
            'fact_id': uuid4(),
            'account_id': random.choice(accounts),
            'cc_id': random.choice(cost_centers),  # Maps to leaf nodes
            'book_id': random.choice(books),
            'strategy_id': random.choice(strategies),
            'trade_date': trade_date,
            'daily_pnl': daily_pnl,
            'mtd_pnl': mtd_pnl,
            'ytd_pnl': ytd_pnl,
            'pytd_pnl': pytd_pnl,
        }
        facts.append(fact_row)
    
    return facts


def generate_hierarchy() -> List[Dict]:
    """
    Generate hierarchy - uses POC finance domain structure (15-20 nodes).
    Structure: ROOT -> AMER -> CASH_EQUITIES -> HIGH_TOUCH -> [Desks]
    For POC structure, see app/engine/poc_finance_data.py
    """
    # Use POC finance data generator (15-20 nodes)
    try:
        from app.engine.poc_finance_data import generate_poc_hierarchy
        return generate_poc_hierarchy()
    except ImportError:
        # Fallback to realistic finance data generator
        try:
            from app.engine.realistic_finance_data import generate_realistic_hierarchy
            return generate_realistic_hierarchy()
        except ImportError:
            # Fallback to original generic structure
            pass
    
    # Original generic hierarchy (fallback)
    """
    Generate a ragged hierarchy with 50 leaf nodes.
    Hierarchy structure varies in depth (2-5 levels).
    
    Returns:
        List of dictionaries representing hierarchy nodes
    """
    hierarchy = []
    
    # Root node
    hierarchy.append({
        'node_id': 'ROOT',
        'parent_node_id': None,
        'node_name': 'Root',
        'depth': 0,
        'is_leaf': False,
        'atlas_source': 'MOCK_ATLAS_v1'
    })
    
    # Region level (depth 1)
    regions = ['Region_A', 'Region_B', 'Region_C', 'Region_D']
    for region in regions:
        hierarchy.append({
            'node_id': region,
            'parent_node_id': 'ROOT',
            'node_name': region.replace('_', ' '),
            'depth': 1,
            'is_leaf': False,
            'atlas_source': 'MOCK_ATLAS_v1'
        })
    
    # Division level (depth 2) - varies by region
    divisions = {
        'Region_A': ['Division_1', 'Division_2'],
        'Region_B': ['Division_3', 'Division_4', 'Division_5'],
        'Region_C': ['Division_6'],
        'Region_D': ['Division_7', 'Division_8']
    }
    
    for region, divs in divisions.items():
        for div in divs:
            hierarchy.append({
                'node_id': div,
                'parent_node_id': region,
                'node_name': div.replace('_', ' '),
                'depth': 2,
                'is_leaf': False,
                'atlas_source': 'MOCK_ATLAS_v1'
            })
    
    # Department level (depth 3) - only for some divisions
    departments = {
        'Division_1': ['Dept_X', 'Dept_Y'],
        'Division_3': ['Dept_Z'],
        'Division_5': ['Dept_W'],
        'Division_7': ['Dept_V']
    }
    
    for div, depts in departments.items():
        for dept in depts:
            hierarchy.append({
                'node_id': dept,
                'parent_node_id': div,
                'node_name': dept.replace('_', ' '),
                'depth': 3,
                'is_leaf': False,
                'atlas_source': 'MOCK_ATLAS_v1'
            })
    
    # Sub-department level (depth 4) - only for some departments
    sub_depts = {
        'Dept_X': ['SubDept_1'],
        'Dept_Z': ['SubDept_2']
    }
    
    for dept, sub_dept_list in sub_depts.items():
        for sub_dept in sub_dept_list:
            hierarchy.append({
                'node_id': sub_dept,
                'parent_node_id': dept,
                'node_name': sub_dept.replace('_', ' '),
                'depth': 4,
                'is_leaf': False,
                'atlas_source': 'MOCK_ATLAS_v1'
            })
    
    # Leaf nodes (CC_001 through CC_050) - map to cost centers
    # Distribute across different parent nodes to create ragged structure
    leaf_distribution = [
        # Direct children of divisions (depth 3)
        ('Division_2', 5),  # CC_001 to CC_005
        ('Division_4', 4),  # CC_006 to CC_009
        ('Division_6', 6),  # CC_010 to CC_015
        ('Division_8', 5),  # CC_016 to CC_020
        
        # Children of departments (depth 4)
        ('Dept_Y', 4),     # CC_021 to CC_024
        ('Dept_W', 3),     # CC_025 to CC_027
        ('Dept_V', 4),     # CC_028 to CC_031
        
        # Children of sub-departments (depth 5)
        ('SubDept_1', 5),  # CC_032 to CC_036
        ('SubDept_2', 4),  # CC_037 to CC_040
        
        # Direct children of Region_C (depth 2) - creates ragged structure
        ('Region_C', 10),  # CC_041 to CC_050
    ]
    
    cc_counter = 1
    for parent_id, count in leaf_distribution:
        for i in range(count):
            cc_id = f"CC_{cc_counter:03d}"
            parent_depth = next((h['depth'] for h in hierarchy if h['node_id'] == parent_id), 2)
            
            hierarchy.append({
                'node_id': cc_id,
                'parent_node_id': parent_id,
                'node_name': f"Cost Center {cc_counter}",
                'depth': parent_depth + 1,
                'is_leaf': True,
                'atlas_source': 'MOCK_ATLAS_v1'
            })
            cc_counter += 1
    
    return hierarchy


def load_facts_to_db(session: Session, facts: List[Dict], clear_existing: bool = False) -> int:
    """
    Load fact rows into the database.
    
    Args:
        session: SQLAlchemy session
        facts: List of fact dictionaries
        clear_existing: If True, delete existing facts before loading
    
    Returns:
        Number of rows inserted
    """
    if clear_existing:
        session.query(FactPnlGold).delete()
        session.commit()
    
    fact_objects = [FactPnlGold(**fact) for fact in facts]
    session.bulk_save_objects(fact_objects)
    session.commit()
    
    return len(fact_objects)


def load_hierarchy_to_db(session: Session, hierarchy: List[Dict], clear_existing: bool = False) -> int:
    """
    Load hierarchy nodes into the database.
    
    Args:
        session: SQLAlchemy session
        hierarchy: List of hierarchy dictionaries
        clear_existing: If True, delete existing hierarchy before loading
    
    Returns:
        Number of nodes inserted
    """
    if clear_existing:
        # Delete in reverse order to handle foreign key constraints
        session.query(DimHierarchy).delete()
        session.commit()
    
    hierarchy_objects = [DimHierarchy(**node) for node in hierarchy]
    session.bulk_save_objects(hierarchy_objects)
    session.commit()
    
    return len(hierarchy_objects)


def generate_hierarchy_bridge(hierarchy: List[Dict], structure_id: str = "MOCK_ATLAS_v1") -> List[Dict]:
    """
    Generate flattened parent-to-leaf mappings for HierarchyBridge table.
    For each parent node, creates mappings to all its recursive leaf descendants.
    
    Args:
        hierarchy: List of hierarchy dictionaries
        structure_id: Atlas structure identifier
    
    Returns:
        List of bridge dictionaries
    """
    from collections import defaultdict
    
    # Build children dictionary
    children_dict = defaultdict(list)
    node_dict = {node['node_id']: node for node in hierarchy}
    leaf_nodes = [node['node_id'] for node in hierarchy if node['is_leaf']]
    
    for node in hierarchy:
        if node['parent_node_id']:
            children_dict[node['parent_node_id']].append(node['node_id'])
    
    # Recursive function to find all leaf descendants
    def get_leaf_descendants(node_id: str, visited: set = None) -> List[str]:
        """Get all leaf node IDs that are descendants of the given node."""
        if visited is None:
            visited = set()
        
        if node_id in visited:
            return []
        visited.add(node_id)
        
        node = node_dict.get(node_id)
        if not node:
            return []
        
        # If this is a leaf, return itself
        if node['is_leaf']:
            return [node_id]
        
        # Otherwise, get all leaf descendants of children
        leaves = []
        for child_id in children_dict.get(node_id, []):
            leaves.extend(get_leaf_descendants(child_id, visited))
        
        return leaves
    
    # Generate bridge entries: every parent -> all its leaf descendants
    bridge_entries = []
    
    for node in hierarchy:
        if not node['is_leaf']:  # Only create bridges for non-leaf nodes
            leaf_descendants = get_leaf_descendants(node['node_id'])
            
            for leaf_id in leaf_descendants:
                # Calculate path length (depth difference)
                parent_depth = node['depth']
                leaf_node = node_dict.get(leaf_id, {})
                leaf_depth = leaf_node.get('depth', parent_depth)
                path_length = leaf_depth - parent_depth
                
                bridge_entries.append({
                    'parent_node_id': node['node_id'],
                    'leaf_node_id': leaf_id,
                    'structure_id': structure_id,
                    'path_length': path_length
                })
    
    return bridge_entries


def load_hierarchy_bridge_to_db(session: Session, bridge_entries: List[Dict], clear_existing: bool = False) -> int:
    """
    Load hierarchy bridge entries into the database.
    
    Args:
        session: SQLAlchemy session
        bridge_entries: List of bridge dictionaries
        clear_existing: If True, delete existing bridge entries before loading
    
    Returns:
        Number of bridge entries inserted
    """
    if clear_existing:
        session.query(HierarchyBridge).delete()
        session.commit()
    
    bridge_objects = [HierarchyBridge(**entry) for entry in bridge_entries]
    session.bulk_save_objects(bridge_objects)
    session.commit()
    
    return len(bridge_objects)


def generate_and_load_mock_data(session: Session, clear_existing: bool = True) -> Dict:
    """
    Generate and load all mock data into the database.
    
    Args:
        session: SQLAlchemy session
        clear_existing: If True, clear existing data before loading
    
    Returns:
        Dictionary with summary statistics
    """
    print("Generating mock data...")
    
    # Generate hierarchy first (needed for fact row mapping to cost centers)
    hierarchy = generate_hierarchy()
    
    # Generate facts mapped to hierarchy cost centers
    # Use POC fact generator if available
    try:
        from app.engine.poc_finance_data import generate_poc_fact_rows
        facts = generate_poc_fact_rows(1000, hierarchy)
    except ImportError:
        facts = generate_fact_rows(1000, hierarchy)
    
    # Load to database
    print("Loading fact data...")
    fact_count = load_facts_to_db(session, facts, clear_existing)
    
    # Clear hierarchy_bridge first (before hierarchy) to avoid FK constraint issues
    if clear_existing:
        from app.models import HierarchyBridge
        session.query(HierarchyBridge).delete()
        session.commit()
    
    print("Loading hierarchy data...")
    hierarchy_count = load_hierarchy_to_db(session, hierarchy, clear_existing)
    
    # Generate and load hierarchy bridge
    print("Generating hierarchy bridge (parent-to-leaf mappings)...")
    structure_id = hierarchy[0]['atlas_source'] if hierarchy else "MOCK_ATLAS_v1"
    bridge_entries = generate_hierarchy_bridge(hierarchy, structure_id)
    bridge_count = load_hierarchy_bridge_to_db(session, bridge_entries, False)  # Don't clear again
    print(f"[OK] Generated {bridge_count} parent-to-leaf mappings")
    
    # Calculate summary statistics
    leaf_nodes = [h for h in hierarchy if h['is_leaf']]
    leaf_count = len(leaf_nodes)
    
    # Get value ranges from facts
    daily_values = [f['daily_pnl'] for f in facts]
    mtd_values = [f['mtd_pnl'] for f in facts]
    ytd_values = [f['ytd_pnl'] for f in facts]
    
    summary = {
        'fact_rows': fact_count,
        'hierarchy_nodes': hierarchy_count,
        'leaf_nodes': leaf_count,
        'bridge_entries': bridge_count,
        'date_range': {
            'start': min(f['trade_date'] for f in facts),
            'end': max(f['trade_date'] for f in facts)
        },
        'value_ranges': {
            'daily_pnl': {
                'min': min(daily_values),
                'max': max(daily_values)
            },
            'mtd_pnl': {
                'min': min(mtd_values),
                'max': max(mtd_values)
            },
            'ytd_pnl': {
                'min': min(ytd_values),
                'max': max(ytd_values)
            }
        }
    }
    
    return summary


def validate_mock_data(session: Session) -> Dict:
    """
    Validate that mock data meets requirements.
    
    Args:
        session: SQLAlchemy session
    
    Returns:
        Dictionary with validation results
    """
    results = {
        'passed': True,
        'checks': {}
    }
    
    # Check 1: Fact row count
    fact_count = session.query(FactPnlGold).count()
    results['checks']['fact_count'] = {
        'expected': 1000,
        'actual': fact_count,
        'passed': fact_count == 1000
    }
    if fact_count != 1000:
        results['passed'] = False
    
    # Check 2: Hierarchy node count
    hierarchy_count = session.query(DimHierarchy).count()
    results['checks']['hierarchy_count'] = {
        'expected': '~30-40',
        'actual': hierarchy_count,
        'passed': 30 <= hierarchy_count <= 40
    }
    if not (30 <= hierarchy_count <= 40):
        results['passed'] = False
    
    # Check 3: Leaf node count (must be exactly 50)
    leaf_count = session.query(DimHierarchy).filter(DimHierarchy.is_leaf == True).count()
    results['checks']['leaf_count'] = {
        'expected': 50,
        'actual': leaf_count,
        'passed': leaf_count == 50
    }
    if leaf_count != 50:
        results['passed'] = False
    
    # Check 4: All cc_id values in facts map to leaf nodes
    all_cc_ids = set(session.query(FactPnlGold.cc_id).distinct().all())
    all_cc_ids = {cc_id[0] for cc_id in all_cc_ids}
    
    all_leaf_node_ids = set(session.query(DimHierarchy.node_id)
                           .filter(DimHierarchy.is_leaf == True).all())
    all_leaf_node_ids = {node_id[0] for node_id in all_leaf_node_ids}
    
    unmapped_cc_ids = all_cc_ids - all_leaf_node_ids
    results['checks']['cc_id_mapping'] = {
        'expected': 'All cc_id map to leaf nodes',
        'unmapped': list(unmapped_cc_ids),
        'passed': len(unmapped_cc_ids) == 0
    }
    if len(unmapped_cc_ids) > 0:
        results['passed'] = False
    
    # Check 5: Hierarchy is valid tree (single root, no cycles)
    root_count = session.query(DimHierarchy).filter(DimHierarchy.parent_node_id == None).count()
    results['checks']['single_root'] = {
        'expected': 1,
        'actual': root_count,
        'passed': root_count == 1
    }
    if root_count != 1:
        results['passed'] = False
    
    # Check 6: All measures are within expected ranges
    facts = session.query(FactPnlGold).all()
    daily_out_of_range = sum(1 for f in facts if not (-100000 <= float(f.daily_pnl) <= 100000))
    mtd_out_of_range = sum(1 for f in facts if not (-500000 <= float(f.mtd_pnl) <= 500000))
    ytd_out_of_range = sum(1 for f in facts if not (-2000000 <= float(f.ytd_pnl) <= 2000000))
    
    results['checks']['measure_ranges'] = {
        'daily_out_of_range': daily_out_of_range,
        'mtd_out_of_range': mtd_out_of_range,
        'ytd_out_of_range': ytd_out_of_range,
        'passed': daily_out_of_range == 0 and mtd_out_of_range == 0 and ytd_out_of_range == 0
    }
    if not results['checks']['measure_ranges']['passed']:
        results['passed'] = False
    
    return results

