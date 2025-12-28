"""
Test script to diagnose execution plan endpoint errors
"""
import requests
import json

API_BASE = "http://localhost:8000"
USE_CASE_ID = "b90f1708-4087-4117-9820-9226ed1115bb"

print("=" * 80)
print("TESTING EXECUTION PLAN ENDPOINT")
print("=" * 80)
print(f"Use Case ID: {USE_CASE_ID}")
print(f"URL: {API_BASE}/api/v1/use-cases/{USE_CASE_ID}/execution-plan")
print()

try:
    response = requests.get(
        f"{API_BASE}/api/v1/use-cases/{USE_CASE_ID}/execution-plan",
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print()
    
    if response.status_code == 200:
        print("SUCCESS!")
        print(json.dumps(response.json(), indent=2))
    else:
        print("ERROR!")
        print(f"Response Text: {response.text}")
        try:
            error_detail = response.json()
            print(f"Error Detail: {json.dumps(error_detail, indent=2)}")
        except:
            print("Could not parse error as JSON")
            
except requests.exceptions.RequestException as e:
    print(f"❌ REQUEST FAILED: {e}")
    print(f"Error Type: {type(e).__name__}")

print()
print("=" * 80)

