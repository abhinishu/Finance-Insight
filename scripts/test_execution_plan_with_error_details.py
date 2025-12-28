"""
Test script to call execution plan endpoint and show detailed error information.
This will help identify why the endpoint is returning 500.
"""

import requests
import json
import sys

USE_CASE_ID = "b90f1708-4087-4117-9820-9226ed1115bb"
API_URL = f"http://localhost:8000/api/v1/use-cases/{USE_CASE_ID}/execution-plan"
HEALTH_URL = "http://localhost:8000/health"

print("=" * 80)
print("EXECUTION PLAN ENDPOINT TEST WITH ERROR DETAILS")
print("=" * 80)
print(f"Use Case ID: {USE_CASE_ID}")
print(f"URL: {API_URL}\n")

# Step 1: Test backend health
print("Step 1: Testing backend health...")
try:
    health_response = requests.get(HEALTH_URL, timeout=5)
    if health_response.status_code == 200:
        print("  [OK] Backend is running (HTTP 200)\n")
    else:
        print(f"  [ERROR] Backend health check failed: HTTP {health_response.status_code}\n")
        sys.exit(1)
except requests.exceptions.ConnectionError:
    print("  [ERROR] Backend is not running. Please start the backend server.\n")
    print("  To start backend:")
    print("    1. Open PowerShell")
    print("    2. cd C:\\Program1\\Finance-Insight")
    print("    3. .\\.venv\\Scripts\\Activate.ps1")
    print("    4. uvicorn app.main:app --reload --host 127.0.0.1 --port 8000\n")
    sys.exit(1)
except Exception as e:
    print(f"  [ERROR] An unexpected error occurred during health check: {e}\n")
    sys.exit(1)

# Step 2: Test execution plan endpoint with detailed error capture
print("Step 2: Testing execution plan endpoint...")
try:
    response = requests.get(API_URL, timeout=10)
    print(f"  Status Code: {response.status_code}")
    print(f"  Content-Type: {response.headers.get('Content-Type')}")
    print(f"  Content-Length: {response.headers.get('Content-Length')}\n")

    if response.status_code == 200:
        print("  [OK] Endpoint returned HTTP 200")
        try:
            json_response = response.json()
            print("  Response JSON:")
            print("-" * 80)
            print(json.dumps(json_response, indent=2))
            print("-" * 80)
        except json.JSONDecodeError:
            print("  [WARNING] Could not parse response as JSON.")
            print("  Raw Response Text:")
            print("-" * 80)
            print(response.text)
            print("-" * 80)
    else:
        print(f"  [ERROR] Endpoint returned HTTP {response.status_code}")
        print(f"  Response Headers: {dict(response.headers)}")
        print("\n  Response Body:")
        print("-" * 80)
        print(response.text)
        print("-" * 80)
        
        # Try to extract error details if it's JSON
        try:
            error_json = response.json()
            print("\n  Error Details (JSON):")
            print("-" * 80)
            print(json.dumps(error_json, indent=2))
            print("-" * 80)
        except:
            pass
        
        print("\n" + "=" * 80)
        print("NEXT STEPS:")
        print("=" * 80)
        print("1. Check the BACKEND TERMINAL (where uvicorn is running)")
        print("2. Look for error messages starting with:")
        print("   - '[EXECUTION PLAN] Starting for use_case_id=...'")
        print("   - '[EXECUTION PLAN] CRITICAL ERROR...'")
        print("   - Any Python traceback/stack trace")
        print("3. If you don't see a backend terminal, run:")
        print("   .\\scripts\\view_backend_logs.ps1")
        print("   OR")
        print("   Open a new PowerShell window and run:")
        print("   cd C:\\Program1\\Finance-Insight")
        print("   .\\.venv\\Scripts\\Activate.ps1")
        print("   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000")
        print("=" * 80)
        sys.exit(1)

except requests.exceptions.ConnectionError:
    print("  [ERROR] Could not connect to backend. Is the server running?\n")
    sys.exit(1)
except requests.exceptions.Timeout:
    print("  [ERROR] Request timed out. Backend might be slow or unresponsive.\n")
    sys.exit(1)
except Exception as e:
    print(f"  [ERROR] An unexpected error occurred: {e}\n")
    import traceback
    print("  Full traceback:")
    print("-" * 80)
    print(traceback.format_exc())
    print("-" * 80)
    sys.exit(1)

print("\n" + "=" * 80)
print("TEST COMPLETED SUCCESSFULLY")
print("=" * 80)


