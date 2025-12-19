"""
Realistic Finance Domain Hierarchy Generator
Creates hierarchy following: Region → Product → Desk → Strategy → Cost Center
"""

from typing import Dict, List, Optional, Tuple


# Finance Domain Constants
REGIONS = {
    'AMER': 'Americas',
    'EMEA': 'Europe, Middle East & Africa',
    'APAC': 'Asia-Pacific'
}

PRODUCTS = {
    'CASH_EQUITIES': 'Cash Equities',
    'EQUITY_DERIVATIVES': 'Equity Derivatives',
    'FIXED_INCOME': 'Fixed Income',
    'FX_SPOT': 'FX Spot'
}

DESKS = {
    'HIGH_TOUCH': 'High Touch Trading',
    'LOW_TOUCH': 'Low Touch Trading',
    'ALGO': 'Algorithmic Trading',
    'ARB': 'Arbitrage',
    'PROP': 'Proprietary Trading'
}

STRATEGIES = {
    'AMER_CASH_HIGH_TOUCH': 'Americas Cash High Touch',
    'AMER_CASH_LOW_TOUCH': 'Americas Cash Low Touch',
    'EMEA_INDEX_ARB': 'EMEA Index Arbitrage',
    'APAC_ALGO_TRADING': 'APAC Algorithmic Trading',
    'GLOBAL_PROP_TRADING': 'Global Proprietary Trading',
    'AMER_FI_GOVT': 'Americas Fixed Income Government',
    'AMER_FI_CORP': 'Americas Fixed Income Corporate',
    'EMEA_EQUITY_DERIV': 'EMEA Equity Derivatives',
    'APAC_FX_SPOT': 'APAC FX Spot'
}


def parse_cost_center_id(cc_id: str) -> Dict[str, Optional[str]]:
    """
    Parse cost center ID to extract attributes.
    Format: CC_{REGION}_{PRODUCT}_{DESK}_{NUMBER}
    Example: CC_AMER_CASH_EQUITIES_HIGH_TOUCH_001
    
    Returns dict with region, product, desk, strategy
    """
    if not cc_id.startswith('CC_'):
        return {'region': None, 'product': None, 'desk': None, 'strategy': None}
    
    parts = cc_id.replace('CC_', '').split('_')
    
    # Try to extract attributes
    region = None
    product = None
    desk = None
    strategy = None
    
    # Check for known regions
    for reg in REGIONS.keys():
        if reg in parts:
            region = reg
            break
    
    # Check for known products
    for prod in PRODUCTS.keys():
        if prod in parts:
            product = prod
            break
    
    # Check for known desks
    for d in DESKS.keys():
        if d in parts:
            desk = d
            break
    
    # Strategy is typically the combination
    if len(parts) >= 3:
        strategy_parts = parts[:-1]  # Everything except the number
        strategy = '_'.join(strategy_parts)
    
    return {
        'region': region,
        'product': product,
        'desk': desk,
        'strategy': strategy
    }


def get_node_attributes(node_id: str, node_name: str, parent_attributes: Optional[Dict] = None) -> Dict[str, Optional[str]]:
    """
    Extract or infer attributes for a hierarchy node.
    
    Args:
        node_id: Node identifier
        node_name: Node display name
        parent_attributes: Attributes from parent node (for inheritance)
    
    Returns:
        Dict with region, product, desk, strategy
    """
    # If it's a cost center, parse it
    if node_id.startswith('CC_'):
        return parse_cost_center_id(node_id)
    
    # Check if node_id matches known patterns
    attrs = {'region': None, 'product': None, 'desk': None, 'strategy': None}
    
    # Check for regions
    for reg_key, reg_name in REGIONS.items():
        if reg_key in node_id.upper() or reg_name in node_name:
            attrs['region'] = reg_key
            break
    
    # Check for products
    for prod_key, prod_name in PRODUCTS.items():
        if prod_key in node_id.upper() or prod_name in node_name:
            attrs['product'] = prod_key
            break
    
    # Check for desks
    for desk_key, desk_name in DESKS.items():
        if desk_key in node_id.upper() or desk_name in node_name:
            attrs['desk'] = desk_key
            break
    
    # Check for strategies
    for strat_key, strat_name in STRATEGIES.items():
        if strat_key in node_id.upper() or strat_name in node_name:
            attrs['strategy'] = strat_key
            break
    
    # Inherit from parent if not found
    if parent_attributes:
        if not attrs['region'] and parent_attributes.get('region'):
            attrs['region'] = parent_attributes['region']
        if not attrs['product'] and parent_attributes.get('product'):
            attrs['product'] = parent_attributes['product']
        if not attrs['desk'] and parent_attributes.get('desk'):
            attrs['desk'] = parent_attributes['desk']
        if not attrs['strategy'] and parent_attributes.get('strategy'):
            attrs['strategy'] = parent_attributes['strategy']
    
    return attrs

