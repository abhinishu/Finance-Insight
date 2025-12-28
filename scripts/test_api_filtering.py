"""
Test if API filtering is working.
"""

import requests
import json

use_case_id = "a26121d8-9e01-4e70-9761-588b1854fe06"
response = requests.get(f"http://localhost:8000/api/v1/use-cases/{use_case_id}/hierarchy")

if response.status_code == 200:
    data = response.json()
    root = data['hierarchy'][0]
    children = root.get('children', [])
    
    print(f"Total children of ROOT: {len(children)}")
    
    trade_nodes = [c for c in children if c['node_id'].startswith('TRADE_')]
    sterling_rule_nodes = [c for c in children if c['node_id'].startswith('STERLING_RULE')]
    business_nodes = [c for c in children if not c['node_id'].startswith('TRADE_') and not c['node_id'].startswith('STERLING_RULE')]
    
    print(f"TRADE nodes: {len(trade_nodes)}")
    print(f"STERLING_RULE nodes: {len(sterling_rule_nodes)}")
    print(f"Business nodes: {len(business_nodes)}")
    
    if trade_nodes or sterling_rule_nodes:
        print("\n[FAIL] Filtering not working - TRADE/STERLING_RULE nodes still present!")
        if trade_nodes:
            print(f"  First 3 TRADE nodes: {[c['node_name'] for c in trade_nodes[:3]]}")
    else:
        print("\n[OK] Filtering working - only business nodes present!")
        print(f"  Business entities: {[c['node_name'] for c in business_nodes]}")
else:
    print(f"Error: {response.status_code} - {response.text}")


