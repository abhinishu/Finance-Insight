"""
Test script for Discovery API endpoint.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

import requests
import json
from uuid import UUID


def test_discovery_endpoint(base_url: str = "http://localhost:8000", use_case_id: str = None):
    """
    Test the discovery API endpoint.
    
    Args:
        base_url: Base URL of the API
        use_case_id: Use case ID to test (optional)
    """
    print("=" * 60)
    print("Testing Discovery API Endpoint")
    print("=" * 60)
    
    if not use_case_id:
        print("\nError: Use case ID required")
        print("Usage: python scripts/test_discovery_api.py <use_case_id>")
        print("\nTo get a use case ID, first create one:")
        print("  python scripts/create_test_use_case.py")
        return 1
    
    try:
        uuid_obj = UUID(use_case_id)
    except ValueError:
        print(f"\nError: Invalid UUID format: {use_case_id}")
        return 1
    
    endpoint = f"{base_url}/api/v1/use-cases/{use_case_id}/discovery"
    
    print(f"\nTesting endpoint: {endpoint}")
    print(f"Use Case ID: {use_case_id}")
    
    try:
        response = requests.get(endpoint, params={"include_pytd": False})
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✓ Discovery endpoint successful!")
            print(f"\nResponse Summary:")
            print(f"  Use Case ID: {data['use_case_id']}")
            print(f"  Hierarchy Nodes: {len(data['hierarchy'])}")
            
            if data['hierarchy']:
                root = data['hierarchy'][0]
                print(f"\nRoot Node:")
                print(f"  Node ID: {root['node_id']}")
                print(f"  Node Name: {root['node_name']}")
                print(f"  Daily P&L: {root['daily_pnl']}")
                print(f"  MTD P&L: {root['mtd_pnl']}")
                print(f"  YTD P&L: {root['ytd_pnl']}")
                print(f"  Children Count: {len(root.get('children', []))}")
            
            print("\n" + "=" * 60)
            print("✓ Test PASSED")
            print("=" * 60)
            return 0
        else:
            print(f"\n✗ Request failed")
            print(f"Response: {response.text}")
            return 1
            
    except requests.exceptions.ConnectionError:
        print(f"\n✗ Connection error: Could not connect to {base_url}")
        print("Make sure the FastAPI server is running:")
        print("  uvicorn app.main:app --reload")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_discovery_api.py <use_case_id> [base_url]")
        print("\nExample:")
        print("  python scripts/test_discovery_api.py 123e4567-e89b-12d3-a456-426614174000")
        sys.exit(1)
    
    use_case_id = sys.argv[1]
    base_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"
    
    sys.exit(test_discovery_endpoint(base_url, use_case_id))

