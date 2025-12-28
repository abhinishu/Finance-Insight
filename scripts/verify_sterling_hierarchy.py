"""
Verify Project Sterling hierarchy structure in API response.
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

import requests
import json

use_case_id = "a26121d8-9e01-4e70-9761-588b1854fe06"
response = requests.get(f"http://localhost:8000/api/v1/use-cases/{use_case_id}/hierarchy")

print(f"Status: {response.status_code}\n")

if response.status_code == 200:
    data = response.json()
    print(f"Structure ID: {data.get('structure_id')}")
    print(f"Root nodes: {len(data.get('hierarchy', []))}\n")
    
    def print_node(node, indent=0):
        prefix = "  " * indent
        print(f"{prefix}- {node.get('node_name')} ({node.get('node_id')})")
        if node.get('children'):
            for child in node.get('children', []):
                print_node(child, indent + 1)
    
    for root in data.get('hierarchy', []):
        print("Hierarchy Tree:")
        print_node(root)
        print(f"\nTotal children: {len(root.get('children', []))}")
        
        # Show business entities specifically
        business_entities = [c for c in root.get('children', []) if c.get('node_id', '').startswith('ENTITY_')]
        print(f"Business entities: {len(business_entities)}")
        for entity in business_entities:
            print(f"  - {entity.get('node_name')} ({len(entity.get('children', []))} children)")
else:
    print(f"Error: {response.text}")


