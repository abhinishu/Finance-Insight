"""
Test script to diagnose backend issues and verify Phase 1 functionality.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

import requests
from sqlalchemy import create_engine, text
from app.database import get_database_url


def test_database_connection():
    """Test if database connection works."""
    print("=" * 60)
    print("TEST 1: Database Connection")
    print("=" * 60)
    
    try:
        db_url = get_database_url()
        print(f"Database URL: {db_url.split('@')[0]}@***")
        
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("[OK] Database connection: SUCCESS")
        return True
    except Exception as e:
        print(f"[FAIL] Database connection: FAILED")
        print(f"   Error: {e}")
        return False


def test_database_tables():
    """Test if required tables exist."""
    print("\n" + "=" * 60)
    print("TEST 2: Database Tables")
    print("=" * 60)
    
    try:
        db_url = get_database_url()
        engine = create_engine(db_url)
        
        required_tables = [
            "use_cases",
            "use_case_runs",
            "dim_hierarchy",
            "metadata_rules",
            "fact_pnl_gold",
            "fact_calculated_results"
        ]
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            existing_tables = [row[0] for row in result]
        
        missing_tables = []
        for table in required_tables:
            if table in existing_tables:
                print(f"  [OK] {table}")
            else:
                print(f"  [FAIL] {table} - MISSING")
                missing_tables.append(table)
        
        if missing_tables:
            print(f"\n[FAIL] Missing tables: {', '.join(missing_tables)}")
            return False
        else:
            print("\n[OK] All required tables exist")
            return True
            
    except Exception as e:
        print(f"[FAIL] Error checking tables: {e}")
        return False


def test_mock_data():
    """Test if mock data exists."""
    print("\n" + "=" * 60)
    print("TEST 3: Mock Data")
    print("=" * 60)
    
    try:
        db_url = get_database_url()
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Check fact rows
            result = conn.execute(text("SELECT COUNT(*) FROM fact_pnl_gold"))
            fact_count = result.scalar()
            print(f"  Fact rows: {fact_count}")
            
            # Check hierarchy nodes
            result = conn.execute(text("SELECT COUNT(*) FROM dim_hierarchy"))
            hierarchy_count = result.scalar()
            print(f"  Hierarchy nodes: {hierarchy_count}")
            
            # Check for MOCK_ATLAS_v1 structure
            result = conn.execute(text("""
                SELECT COUNT(*) FROM dim_hierarchy 
                WHERE atlas_source = 'MOCK_ATLAS_v1'
            """))
            mock_structure_count = result.scalar()
            print(f"  MOCK_ATLAS_v1 nodes: {mock_structure_count}")
        
        if fact_count > 0 and hierarchy_count > 0 and mock_structure_count > 0:
            print("\n[OK] Mock data exists")
            return True
        else:
            print("\n[FAIL] Mock data missing or incomplete")
            if fact_count == 0:
                print("   - No fact rows found")
            if hierarchy_count == 0:
                print("   - No hierarchy nodes found")
            if mock_structure_count == 0:
                print("   - No MOCK_ATLAS_v1 structure found")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error checking mock data: {e}")
        return False


def test_backend_health():
    """Test backend health endpoint."""
    print("\n" + "=" * 60)
    print("TEST 4: Backend Health")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print(f"[OK] Backend health: SUCCESS")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"[FAIL] Backend health: FAILED (Status: {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print("[FAIL] Backend health: FAILED (Backend not running)")
        return False
    except Exception as e:
        print(f"[FAIL] Backend health: FAILED ({e})")
        return False


def test_discovery_api():
    """Test discovery API endpoint."""
    print("\n" + "=" * 60)
    print("TEST 5: Discovery API")
    print("=" * 60)
    
    try:
        url = "http://localhost:8000/api/v1/discovery"
        params = {"structure_id": "MOCK_ATLAS_v1"}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Discovery API: SUCCESS")
            print(f"   Structure ID: {data.get('structure_id')}")
            print(f"   Hierarchy nodes: {len(data.get('hierarchy', []))}")
            return True
        else:
            print(f"[FAIL] Discovery API: FAILED (Status: {response.status_code})")
            try:
                error_detail = response.json()
                print(f"   Error: {error_detail.get('detail', 'Unknown error')}")
            except:
                print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("[FAIL] Discovery API: FAILED (Backend not running)")
        return False
    except Exception as e:
        print(f"[FAIL] Discovery API: FAILED ({e})")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Finance-Insight Phase 1 Backend Testing")
    print("=" * 60)
    
    results = []
    
    # Test database connection
    db_connected = test_database_connection()
    results.append(("Database Connection", db_connected))
    
    if db_connected:
        # Test tables
        tables_exist = test_database_tables()
        results.append(("Database Tables", tables_exist))
        
        if tables_exist:
            # Test mock data
            data_exists = test_mock_data()
            results.append(("Mock Data", data_exists))
    
    # Test backend
    backend_ok = test_backend_health()
    results.append(("Backend Health", backend_ok))
    
    if backend_ok:
        # Test discovery API
        api_ok = test_discovery_api()
        results.append(("Discovery API", api_ok))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "[OK] PASS" if passed else "[FAIL] FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n[SUCCESS] All tests passed! Phase 1 is working correctly.")
    else:
        print("\n[WARNING]  Some tests failed. See details above.")
        print("\nNext steps:")
        if not db_connected:
            print("  1. Install and start PostgreSQL")
            print("  2. Update DATABASE_URL in app/database.py or .env file")
        elif not any(r[0] == "Database Tables" and r[1] for r in results):
            print("  1. Run: python scripts/init_db.py")
        elif not any(r[0] == "Mock Data" and r[1] for r in results):
            print("  1. Run: python scripts/generate_mock_data.py")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

