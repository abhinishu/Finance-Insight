"""
Realistic Finance Domain Mock Data Generator
Creates hierarchy: Region → Product → Desk → Strategy → Cost Center
Uses finance domain naming: AMER, EMEA, APAC regions, CASH_EQUITIES, etc.
"""

import random
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List
from uuid import uuid4

from app.engine.finance_hierarchy import (
    DESKS, PRODUCTS, REGIONS, STRATEGIES, get_node_attributes
)


def generate_realistic_hierarchy() -> List[Dict]:
    """
    Generate realistic finance domain hierarchy.
    Structure: Region → Product → Desk → Strategy → Cost Center
    
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
    
    # Define realistic hierarchy structure
    # Format: Region → Product → Desk → Strategy → Cost Centers
    # Expanded to generate ~50 cost centers total
    structure = {
        'AMER': {
            'CASH_EQUITIES': {
                'HIGH_TOUCH': {
                    'AMER_CASH_HIGH_TOUCH': 5,  # 5 cost centers
                },
                'LOW_TOUCH': {
                    'AMER_CASH_LOW_TOUCH': 4,
                }
            },
            'EQUITY_DERIVATIVES': {
                'ARB': {
                    'EMEA_INDEX_ARB': 3,  # Shared strategy
                }
            },
            'FIXED_INCOME': {
                'HIGH_TOUCH': {
                    'AMER_FI_GOVT': 3,
                    'AMER_FI_CORP': 3,
                }
            }
        },
        'EMEA': {
            'CASH_EQUITIES': {
                'ALGO': {
                    'APAC_ALGO_TRADING': 4,  # Shared strategy
                }
            },
            'EQUITY_DERIVATIVES': {
                'ARB': {
                    'EMEA_INDEX_ARB': 4,
                },
                'PROP': {
                    'GLOBAL_PROP_TRADING': 3,
                }
            }
        },
        'APAC': {
            'CASH_EQUITIES': {
                'ALGO': {
                    'APAC_ALGO_TRADING': 5,
                }
            },
            'FX_SPOT': {
                'HIGH_TOUCH': {
                    'APAC_FX_SPOT': 3,
                }
            },
            'EQUITY_DERIVATIVES': {
                'PROP': {
                    'GLOBAL_PROP_TRADING': 3,
                }
            }
        }
    }
    
    cc_counter = 1
    depth = 1
    
    # Generate hierarchy following structure
    for region_key, region_name in REGIONS.items():
        if region_key not in structure:
            continue
        
        # Region level (depth 1)
        region_node_id = region_key
        hierarchy.append({
            'node_id': region_node_id,
            'parent_node_id': 'ROOT',
            'node_name': region_name,
            'depth': depth,
            'is_leaf': False,
            'atlas_source': 'MOCK_ATLAS_v1'
        })
        
        depth = 2
        for product_key, product_name in PRODUCTS.items():
            if product_key not in structure[region_key]:
                continue
            
            # Product level (depth 2)
            product_node_id = f"{region_key}_{product_key}"
            hierarchy.append({
                'node_id': product_node_id,
                'parent_node_id': region_node_id,
                'node_name': product_name,
                'depth': depth,
                'is_leaf': False,
                'atlas_source': 'MOCK_ATLAS_v1'
            })
            
            depth = 3
            for desk_key, desk_name in DESKS.items():
                if desk_key not in structure[region_key][product_key]:
                    continue
                
                # Desk level (depth 3)
                desk_node_id = f"{region_key}_{product_key}_{desk_key}"
                hierarchy.append({
                    'node_id': desk_node_id,
                    'parent_node_id': product_node_id,
                    'node_name': desk_name,
                    'depth': depth,
                    'is_leaf': False,
                    'atlas_source': 'MOCK_ATLAS_v1'
                })
                
                depth = 4
                # Get strategies for this desk from structure
                strategies_dict = structure[region_key][product_key][desk_key]
                for strategy_key, num_ccs in strategies_dict.items():
                    # Get strategy name from STRATEGIES dict or use key
                    strategy_name = STRATEGIES.get(strategy_key, strategy_key.replace('_', ' ').title())
                    
                    # Strategy level (depth 4)
                    strategy_node_id = f"{region_key}_{product_key}_{desk_key}_{strategy_key}"
                    hierarchy.append({
                        'node_id': strategy_node_id,
                        'parent_node_id': desk_node_id,
                        'node_name': strategy_name,
                        'depth': depth,
                        'is_leaf': False,
                        'atlas_source': 'MOCK_ATLAS_v1'
                    })
                    
                    # Cost Centers (depth 5 - leaf nodes)
                    for i in range(num_ccs):
                        cc_id = f"CC_{region_key}_{product_key}_{desk_key}_{strategy_key}_{cc_counter:03d}"
                        hierarchy.append({
                            'node_id': cc_id,
                            'parent_node_id': strategy_node_id,
                            'node_name': f"Cost Center {cc_counter:03d} - {strategy_name}",
                            'depth': depth + 1,
                            'is_leaf': True,
                            'atlas_source': 'MOCK_ATLAS_v1'
                        })
                        cc_counter += 1
                    
                    depth = 4
                depth = 3
            depth = 2
        depth = 1
    
    return hierarchy


def generate_realistic_fact_rows(count: int = 1000, hierarchy: List[Dict] = None) -> List[Dict]:
    """
    Generate fact rows mapped to realistic cost centers.
    
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
        # Fallback: generate some cost centers
        cost_centers = [f"CC_AMER_CASH_EQUITIES_HIGH_TOUCH_AMER_CASH_HIGH_TOUCH_{i:03d}" 
                       for i in range(1, 51)]
    
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

