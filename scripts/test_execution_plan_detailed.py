"""
Detailed test script to diagnose execution plan endpoint errors
Shows both the HTTP response and attempts to capture backend logs
"""
import requests
import json
import sys

API_BASE = "http://localhost:8000"
USE_CASE_ID = "b90f1708-4087-4117-9820-9226ed1115bb"
ENDPOINT = f"{API_BASE}/api/v1/use-cases/{USE_CASE_ID}/execution-plan"

print("=" * 80)
print("DETAILED EXECUTION PLAN ENDPOINT TEST")
print("=" * 80)
print(f"Use Case ID: {USE_CASE_ID}")
print(f"URL: {ENDPOINT}")
print()

# Test 1: Health check
print("Step 1: Testing backend health...")
try:
    health_response = requests.get(f"{API_BASE}/health", timeout=5)
    if health_response.status_code == 200:
        print(f"  [OK] Backend is running (HTTP {health_response.status_code})")
    else:
        print(f"  [WARNING] Backend returned HTTP {health_response.status_code}")
except Exception as e:
    print(f"  [ERROR] Backend not reachable: {e}")
    print("  Make sure the backend is running on port 8000")
    sys.exit(1)

print()

# Test 2: Execution plan endpoint
print("Step 2: Testing execution plan endpoint...")
try:
    response = requests.get(ENDPOINT, timeout=10)
    
    print(f"  Status Code: {response.status_code}")
    print(f"  Content-Type: {response.headers.get('content-type', 'N/A')}")
    print(f"  Content-Length: {response.headers.get('content-length', 'N/A')}")
    print()
    
    if response.status_code == 200:
        print("  [SUCCESS] Endpoint returned 200 OK")
        try:
            data = response.json()
            print("  Response JSON:")
            print(json.dumps(data, indent=2))
        except Exception as json_error:
            print(f"  [WARNING] Could not parse as JSON: {json_error}")
            print(f"  Raw response: {response.text[:500]}")
    else:
        print(f"  [ERROR] Endpoint returned HTTP {response.status_code}")
        print(f"  Response Headers: {dict(response.headers)}")
        print()
        print("  Response Body:")
        print("  " + "-" * 76)
        try:
            # Try to parse as JSON first
            error_data = response.json()
            print(json.dumps(error_data, indent=2))
        except:
            # If not JSON, show raw text
            print(response.text)
        print("  " + "-" * 76)
        
except requests.exceptions.Timeout:
    print("  [ERROR] Request timed out after 10 seconds")
    print("  The backend may be hanging or processing slowly")
except requests.exceptions.ConnectionError as e:
    print(f"  [ERROR] Connection failed: {e}")
    print("  Make sure the backend is running on port 8000")
except Exception as e:
    print(f"  [ERROR] Unexpected error: {e}")
    print(f"  Error type: {type(e).__name__}")

print()
print("=" * 80)
print("NEXT STEPS:")
print("=" * 80)
print("1. If you see HTTP 500, check the BACKEND TERMINAL (where uvicorn is running)")
print("2. Look for error messages starting with:")
print("   - 'Execution plan: Starting for use_case_id=...'")
print("   - 'CRITICAL ERROR generating execution plan...'")
print("   - Any Python traceback/stack trace")
print("3. Copy the FULL error message from the backend terminal and share it")
print("=" * 80)



