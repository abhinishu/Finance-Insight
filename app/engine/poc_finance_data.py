"""
POC Finance Domain Data Generator - 15-20 Realistic Nodes
Structure: ROOT -> AMER -> CASH_EQUITIES -> HIGH_TOUCH -> [Specific Desks]
Desk Names: AMER_CASH_NY, AMER_PROG_TRADING, EMEA_INDEX_ARB, APAC_ALGO_G1
"""

from typing import Dict, List
from uuid import uuid4
import random
from datetime import date, timedelta
from decimal import Decimal

from app.engine.finance_hierarchy import REGIONS, PRODUCTS


def generate_poc_hierarchy() -> List[Dict]:
    """
    Generate POC hierarchy with 15-20 realistic nodes.
    Structure: ROOT -> AMER -> CASH_EQUITIES -> HIGH_TOUCH -> [Desks]
    
    Returns:
        List of hierarchy node dictionaries
    """
    hierarchy = []
    
    # Root node
    hierarchy.append({
        'node_id': 'ROOT',
        'parent_node_id': None,
        'node_name': 'Global Trading P&L',
        'depth': 0,
        'is_leaf': False,
        'atlas_source': 'MOCK_ATLAS_v1'
    })
    
    # AMER Region (depth 1)
    hierarchy.append({
        'node_id': 'AMER',
        'parent_node_id': 'ROOT',
        'node_name': 'Americas',
        'depth': 1,
        'is_leaf': False,
        'atlas_source': 'MOCK_ATLAS_v1'
    })
    
    # CASH_EQUITIES Product (depth 2)
    hierarchy.append({
        'node_id': 'AMER_CASH_EQUITIES',
        'parent_node_id': 'AMER',
        'node_name': 'Cash Equities',
        'depth': 2,
        'is_leaf': False,
        'atlas_source': 'MOCK_ATLAS_v1'
    })
    
    # HIGH_TOUCH Desk (depth 3)
    hierarchy.append({
        'node_id': 'AMER_CASH_EQUITIES_HIGH_TOUCH',
        'parent_node_id': 'AMER_CASH_EQUITIES',
        'node_name': 'High Touch Trading',
        'depth': 3,
        'is_leaf': False,
        'atlas_source': 'MOCK_ATLAS_v1'
    })
    
    # Specific Desks/Strategies (depth 4)
    desks = [
        {
            'id': 'AMER_CASH_NY',
            'name': 'Americas Cash NY',
            'cc_count': 4  # 4 cost centers per desk
        },
        {
            'id': 'AMER_PROG_TRADING',
            'name': 'Americas Program Trading',
            'cc_count': 3
        },
        {
            'id': 'EMEA_INDEX_ARB',
            'name': 'EMEA Index Arbitrage',
            'cc_count': 3
        },
        {
            'id': 'APAC_ALGO_G1',
            'name': 'APAC Algorithmic G1',
            'cc_count': 3
        }
    ]
    
    cc_counter = 1
    for desk in desks:
        # Desk/Strategy level (depth 4)
        hierarchy.append({
            'node_id': desk['id'],
            'parent_node_id': 'AMER_CASH_EQUITIES_HIGH_TOUCH',
            'node_name': desk['name'],
            'depth': 4,
            'is_leaf': False,
            'atlas_source': 'MOCK_ATLAS_v1'
        })
        
        # Cost Centers (depth 5 - leaf nodes)
        for i in range(desk['cc_count']):
            cc_id = f"CC_{desk['id']}_{cc_counter:03d}"
            hierarchy.append({
                'node_id': cc_id,
                'parent_node_id': desk['id'],
                'node_name': f"Cost Center {cc_counter:03d} - {desk['name']}",
                'depth': 5,
                'is_leaf': True,
                'atlas_source': 'MOCK_ATLAS_v1'
            })
            cc_counter += 1
    
    return hierarchy


def generate_poc_fact_rows(count: int = 1000, hierarchy: List[Dict] = None) -> List[Dict]:
    """
    Generate fact rows mapped to POC cost centers.
    
    Args:
        count: Number of fact rows
        hierarchy: Hierarchy list to extract cost center IDs
    
    Returns:
        List of fact row dictionaries
    """
    facts = []
    
    # Extract cost center IDs from hierarchy
    if hierarchy:
        cost_centers = [h['node_id'] for h in hierarchy if h['is_leaf']]
    else:
        # Fallback
        cost_centers = [f"CC_AMER_CASH_NY_{i:03d}" for i in range(1, 14)]
    
    # Dimension ranges
    accounts = [f"ACC_{i:03d}" for i in range(1, 11)]
    books = [f"BOOK_{i:02d}" for i in range(1, 11)]
    strategies = [f"STRAT_{i:02d}" for i in range(1, 6)]
    
    # Date range: 2024-01-01 to 2024-12-31
    start_date = date(2024, 1, 1)
    end_date = date(2024, 12, 31)
    date_range = (end_date - start_date).days
    
    for _ in range(count):
        random_days = random.randint(0, date_range)
        trade_date = start_date + timedelta(days=random_days)
        
        # Generate P&L values using Decimal
        daily_pnl = Decimal(str(random.uniform(-100000, 100000))).quantize(Decimal('0.01'))
        mtd_pnl = Decimal(str(random.uniform(-500000, 500000))).quantize(Decimal('0.01'))
        ytd_pnl = Decimal(str(random.uniform(-2000000, 2000000))).quantize(Decimal('0.01'))
        pytd_pnl = Decimal(str(random.uniform(-1800000, 1800000))).quantize(Decimal('0.01'))
        
        fact_row = {
            'fact_id': uuid4(),
            'account_id': random.choice(accounts),
            'cc_id': random.choice(cost_centers),
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

