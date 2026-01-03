"""
Test the actual API response to see if rule object is included
"""

import sys
from pathlib import Path
import requests
import json

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

def main():
    print("=" * 80)
    print("TESTING ACTUAL API RESPONSE")
    print("=" * 80)
    print()
    
    uc3_id = 'fce60983-0328-496b-b6e1-34249ec5aa5a'
    api_url = f'http://localhost:8000/api/v1/use-cases/{uc3_id}/results'
    
    print(f"Requesting: {api_url}")
    print()
    
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Find NODE_4 in hierarchy
        def find_node(nodes, target_id='NODE_4'):
            for node in nodes:
                if node.get('node_id') == target_id:
                    return node
                if node.get('children'):
                    found = find_node(node['children'], target_id)
                    if found:
                        return found
            return None
        
        commissions_node = find_node(data.get('hierarchy', []))
        
        if commissions_node:
            print("[OK] Found Commissions node (NODE_4) in API response")
            print(f"   Node ID: {commissions_node.get('node_id')}")
            print(f"   Node Name: {commissions_node.get('node_name')}")
            print()
            
            rule = commissions_node.get('rule')
            if rule:
                print("[OK] Rule object exists in API response:")
                print(json.dumps(rule, indent=2))
                print()
                
                # Check Math rule fields
                if rule.get('rule_type') == 'NODE_ARITHMETIC':
                    print("[OK] rule_type is NODE_ARITHMETIC")
                else:
                    print(f"[WARNING] rule_type is: {rule.get('rule_type')}")
                
                if rule.get('rule_expression'):
                    print(f"[OK] rule_expression is: '{rule.get('rule_expression')}'")
                else:
                    print("[ERROR] rule_expression is missing or empty!")
                
                if rule.get('rule_dependencies'):
                    print(f"[OK] rule_dependencies is: {rule.get('rule_dependencies')}")
                else:
                    print("[INFO] rule_dependencies is missing (OK if not needed)")
            else:
                print("[ERROR] Rule object is NULL or missing in API response!")
                print("   This is the root cause - rule is not being attached to the node.")
                print()
                print("   Checking if node has is_override flag...")
                print(f"   is_override: {commissions_node.get('is_override')}")
        else:
            print("[ERROR] Commissions node (NODE_4) not found in API response!")
            print(f"   Available nodes: {[n.get('node_id') for n in data.get('hierarchy', [])]}")
        
        print()
        print("=" * 80)
        print("DIAGNOSIS COMPLETE")
        print("=" * 80)
        
        return 0
        
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to API. Is the server running?")
        print("   Start server with: uvicorn app.main:app --reload")
        return 1
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())

