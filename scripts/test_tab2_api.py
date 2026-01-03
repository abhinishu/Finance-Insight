"""
Test Tab 2 API endpoint and hierarchy structure.
"""

import requests
import json

structure_id = "Mock Atlas Structure v1"
url = f"http://localhost:8000/api/v1/discovery"
params = {"structure_id": structure_id}

print(f"Testing Tab 2 API endpoint:")
print(f"  URL: {url}")
print(f"  Params: {params}")
print()

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    
    print(f"Status: {response.status_code}")
    print(f"Structure ID: {data.get('structure_id')}")
    print(f"Hierarchy array length: {len(data.get('hierarchy', []))}")
    print()
    
    if data.get('hierarchy'):
        root = data['hierarchy'][0]
        print(f"Root node:")
        print(f"  node_id: {root.get('node_id')}")
        print(f"  node_name: {root.get('node_name')}")
        print(f"  depth: {root.get('depth')}")
        print(f"  is_leaf: {root.get('is_leaf')}")
        print(f"  children count: {len(root.get('children', []))}")
        print()
        
        print("Root's direct children:")
        for i, child in enumerate(root.get('children', [])[:10]):
            print(f"  {i+1}. {child.get('node_name')} (node_id: {child.get('node_id')}, depth: {child.get('depth')}, children: {len(child.get('children', []))})")
        
        print()
        print("Checking nested structure:")
        def check_children(node, indent=0):
            prefix = "  " * indent
            print(f"{prefix}- {node.get('node_name')} (depth: {node.get('depth')}, children: {len(node.get('children', []))})")
            for child in node.get('children', [])[:3]:  # Show first 3 children
                check_children(child, indent + 1)
        
        print("Full hierarchy tree (first 3 levels):")
        check_children(root)
        
        print()
        print("Checking if hierarchy is properly nested:")
        has_nested = any(len(child.get('children', [])) > 0 for child in root.get('children', []))
        print(f"  Has nested children: {has_nested}")
        
        # Check UK Limited specifically
        uk_limited = None
        for child in root.get('children', []):
            if child.get('node_id') == 'ENTITY_UK_LTD':
                uk_limited = child
                break
        
        if uk_limited:
            print()
            print(f"UK Limited node found:")
            print(f"  node_name: {uk_limited.get('node_name')}")
            print(f"  children: {len(uk_limited.get('children', []))}")
            for child in uk_limited.get('children', []):
                print(f"    - {child.get('node_name')} (children: {len(child.get('children', []))})")
        else:
            print()
            print("UK Limited node NOT FOUND in root's children!")
else:
    print(f"Error: {response.status_code}")
    print(response.text)



