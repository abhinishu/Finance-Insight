"""
Test script to check Project Sterling hierarchy response.
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

import requests
import json

use_case_id = "a26121d8-9e01-4e70-9761-588b1854fe06"
response = requests.get(f"http://localhost:8000/api/v1/use-cases/{use_case_id}/hierarchy")

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"\nStructure ID: {data.get('structure_id')}")
    print(f"Number of root nodes: {len(data.get('hierarchy', []))}")
    print("\nAll root nodes:")
    for i, root in enumerate(data.get('hierarchy', []), 1):
        print(f"  {i}. {root.get('node_id')}: {root.get('node_name')} (children: {len(root.get('children', []))})")
else:
    print(f"Error: {response.text}")

