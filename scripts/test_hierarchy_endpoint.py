"""
Test script to verify hierarchy endpoint works correctly.
Tests both the discovery endpoint and use-case hierarchy endpoint.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

import requests
from uuid import UUID

def test_use_case_hierarchy(use_case_id: str, base_url: str = "http://localhost:8000"):
    """Test the use-case hierarchy endpoint."""
    print("=" * 60)
    print(f"Testing Use Case Hierarchy Endpoint")
    print("=" * 60)
    print(f"Use Case ID: {use_case_id}")
    print(f"Endpoint: {base_url}/api/v1/use-cases/{use_case_id}/hierarchy")
    print()
    
    try:
        response = requests.get(
            f"{base_url}/api/v1/use-cases/{use_case_id}/hierarchy",
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n[OK] SUCCESS!")
            print(f"\nResponse Summary:")
            print(f"  Structure ID: {data.get('structure_id')}")
            print(f"  Hierarchy Root Nodes: {len(data.get('hierarchy', []))}")
            
            if data.get('hierarchy'):
                root = data['hierarchy'][0]
                print(f"\nRoot Node:")
                print(f"  Node ID: {root.get('node_id')}")
                print(f"  Node Name: {root.get('node_name')}")
                print(f"  Parent Node ID: {root.get('parent_node_id')}")
                print(f"  Depth: {root.get('depth')}")
                print(f"  Is Leaf: {root.get('is_leaf')}")
                print(f"  Children Count: {len(root.get('children', []))}")
                
                if root.get('children'):
                    print(f"\nFirst Child:")
                    first_child = root['children'][0]
                    print(f"  Node ID: {first_child.get('node_id')}")
                    print(f"  Node Name: {first_child.get('node_name')}")
                    print(f"  Parent Node ID: {first_child.get('parent_node_id')}")
            
            print("\n" + "=" * 60)
            print("[OK] Test PASSED")
            print("=" * 60)
            return True
        else:
            print(f"\n[FAIL] FAILED")
            try:
                error_data = response.json()
                print(f"Error Detail: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"Response Text: {response.text[:500]}")
            print("\n" + "=" * 60)
            print("[FAILED] Test FAILED")
            print("=" * 60)
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n[ERROR] Connection Error: Could not connect to {base_url}")
        print("Make sure the FastAPI server is running:")
        print("  uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_discovery_endpoint(structure_id: str, base_url: str = "http://localhost:8000"):
    """Test the discovery endpoint directly."""
    print("=" * 60)
    print(f"Testing Discovery Endpoint")
    print("=" * 60)
    print(f"Structure ID: {structure_id}")
    print(f"Endpoint: {base_url}/api/v1/discovery?structure_id={structure_id}")
    print()
    
    try:
        response = requests.get(
            f"{base_url}/api/v1/discovery",
            params={"structure_id": structure_id},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n[OK] SUCCESS!")
            print(f"\nResponse Summary:")
            print(f"  Structure ID: {data.get('structure_id')}")
            print(f"  Hierarchy Root Nodes: {len(data.get('hierarchy', []))}")
            
            if data.get('hierarchy'):
                root = data['hierarchy'][0]
                print(f"\nRoot Node:")
                print(f"  Node ID: {root.get('node_id')}")
                print(f"  Node Name: {root.get('node_name')}")
                print(f"  Parent Node ID: {root.get('parent_node_id')}")
            
            print("\n" + "=" * 60)
            print("[OK] Test PASSED")
            print("=" * 60)
            return True
        else:
            print(f"\n[FAIL] FAILED")
            try:
                error_data = response.json()
                print(f"Error Detail: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"Response Text: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def list_use_cases(base_url: str = "http://localhost:8000"):
    """List all use cases to help identify test cases."""
    print("=" * 60)
    print("Listing Use Cases")
    print("=" * 60)
    
    try:
        response = requests.get(f"{base_url}/api/v1/use-cases", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            use_cases = data.get('use_cases', [])
            
            if use_cases:
                print(f"\nFound {len(use_cases)} use case(s):\n")
                for uc in use_cases:
                    print(f"  ID: {uc.get('use_case_id')}")
                    print(f"  Name: {uc.get('name')}")
                    print(f"  Structure ID: {uc.get('atlas_structure_id')}")
                    print()
                return use_cases
            else:
                print("\nNo use cases found.")
                return []
        else:
            print(f"Failed to list use cases: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error listing use cases: {e}")
        return []


if __name__ == "__main__":
    if len(sys.argv) > 1:
        use_case_id = sys.argv[1]
        test_use_case_hierarchy(use_case_id)
    else:
        # List use cases and test them
        use_cases = list_use_cases()
        
        if use_cases:
            print("\n" + "=" * 60)
            print("Testing All Use Cases")
            print("=" * 60)
            
            for uc in use_cases:
                print(f"\nTesting: {uc.get('name')} ({uc.get('use_case_id')})")
                print("-" * 60)
                test_use_case_hierarchy(uc.get('use_case_id'))
                
                # Also test discovery endpoint with structure_id
                structure_id = uc.get('atlas_structure_id')
                if structure_id:
                    print(f"\nTesting Discovery Endpoint for structure: {structure_id}")
                    print("-" * 60)
                    test_discovery_endpoint(structure_id)
        else:
            print("\nNo use cases found. Please create a use case first.")
            print("\nUsage:")
            print("  python scripts/test_hierarchy_endpoint.py <use_case_id>")
            print("\nOr run without arguments to test all use cases.")

