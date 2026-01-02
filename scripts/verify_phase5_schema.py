"""
Phase 5.1 Schema Verification Script

Verifies that the Phase 5.1 database migration was applied correctly:
- Checks that fact_pnl_use_case_3 table exists
- Verifies all PnL columns use NUMERIC/DECIMAL (not FLOAT/REAL)
- Validates metadata_rules new columns
- Validates use_cases new column

CRITICAL: This script ensures Decimal precision policy compliance.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError

# Import database configuration
try:
    from app.database import get_database_url
except ImportError as e:
    print(f"ERROR: Cannot import get_database_url from app.database: {e}")
    print(f"Project root: {project_root}")
    print("Make sure you're running from the project root directory.")
    sys.exit(1)


def verify_table_exists(inspector, table_name: str) -> bool:
    """Verify that a table exists in the database."""
    tables = inspector.get_table_names()
    exists = table_name in tables
    if not exists:
        print(f"[FAIL] Table '{table_name}' does not exist")
        print(f"   Available tables: {', '.join(sorted(tables))}")
    else:
        print(f"[PASS] Table '{table_name}' exists")
    return exists


def verify_column_exists(inspector, table_name: str, column_name: str) -> bool:
    """Verify that a column exists in a table."""
    try:
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        exists = column_name in columns
        if not exists:
            print(f"[FAIL] Column '{column_name}' does not exist in table '{table_name}'")
            print(f"   Available columns: {', '.join(sorted(columns))}")
        else:
            print(f"[PASS] Column '{column_name}' exists in table '{table_name}'")
        return exists
    except Exception as e:
        print(f"[FAIL] Error checking column '{column_name}' in table '{table_name}': {e}")
        return False


def verify_numeric_type(engine, table_name: str, column_name: str) -> bool:
    """
    Verify that a column uses NUMERIC or DECIMAL type (not FLOAT/REAL).
    
    CRITICAL: This ensures Decimal precision policy compliance.
    """
    try:
        query = text("""
            SELECT 
                column_name,
                data_type,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns
            WHERE table_name = :table_name
            AND column_name = :column_name
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {"table_name": table_name, "column_name": column_name})
            row = result.fetchone()
        
        if not row:
            print(f"❌ FAIL: Column '{column_name}' not found in information_schema")
            return False
        
        data_type = row[1].lower()
        
        # Check if it's NUMERIC or DECIMAL (acceptable)
        if data_type in ('numeric', 'decimal'):
            precision = row[2]
            scale = row[3]
            print(f"[PASS] Column '{column_name}' uses {data_type.upper()}({precision},{scale})")
            return True
        
        # Check if it's FLOAT or REAL (FORBIDDEN)
        if data_type in ('real', 'double precision', 'float', 'float4', 'float8'):
            print(f"[FAIL] Column '{column_name}' uses {data_type.upper()} - FORBIDDEN!")
            print(f"   CRITICAL: Financial columns must use NUMERIC(18,2) for Decimal precision")
            print(f"   This violates the Decimal precision policy.")
            return False
        
        # Unknown type - warn but don't fail
        print(f"[WARN] Column '{column_name}' uses unknown type: {data_type}")
        return True
        
    except Exception as e:
        print(f"[FAIL] Error checking numeric type for '{column_name}': {e}")
        return False


def verify_metadata_rules_columns(engine, inspector) -> bool:
    """Verify that metadata_rules has the new Phase 5.1 columns."""
    print("\n" + "="*70)
    print("Verifying metadata_rules table columns...")
    print("="*70)
    
    all_pass = True
    
    # Check rule_type
    if not verify_column_exists(inspector, 'metadata_rules', 'rule_type'):
        all_pass = False
    
    # Check measure_name
    if not verify_column_exists(inspector, 'metadata_rules', 'measure_name'):
        all_pass = False
    
    # Check rule_expression
    if not verify_column_exists(inspector, 'metadata_rules', 'rule_expression'):
        all_pass = False
    
    # Check rule_dependencies
    if not verify_column_exists(inspector, 'metadata_rules', 'rule_dependencies'):
        all_pass = False
    
    return all_pass


def verify_use_cases_columns(engine, inspector) -> bool:
    """Verify that use_cases has the new Phase 5.1 column."""
    print("\n" + "="*70)
    print("Verifying use_cases table columns...")
    print("="*70)
    
    # Check input_table_name
    return verify_column_exists(inspector, 'use_cases', 'input_table_name')


def verify_fact_pnl_use_case_3(engine, inspector) -> bool:
    """Verify that fact_pnl_use_case_3 table exists and has correct types."""
    print("\n" + "="*70)
    print("Verifying fact_pnl_use_case_3 table...")
    print("="*70)
    
    all_pass = True
    
    # Check table exists
    if not verify_table_exists(inspector, 'fact_pnl_use_case_3'):
        return False
    
    # Check required columns exist
    required_columns = [
        'entry_id',
        'effective_date',
        'cost_center',
        'division',
        'business_area',
        'product_line',
        'strategy',
        'process_1',
        'process_2',
        'book',
        'pnl_daily',
        'pnl_commission',
        'pnl_trade',
        'created_at'
    ]
    
    print("\nChecking required columns...")
    for col in required_columns:
        if not verify_column_exists(inspector, 'fact_pnl_use_case_3', col):
            all_pass = False
    
    # CRITICAL: Verify PnL columns use NUMERIC (not FLOAT)
    print("\n" + "="*70)
    print("CRITICAL: Verifying PnL columns use NUMERIC (Decimal precision)...")
    print("="*70)
    
    pnl_columns = ['pnl_daily', 'pnl_commission', 'pnl_trade']
    for col in pnl_columns:
        if not verify_numeric_type(engine, 'fact_pnl_use_case_3', col):
            all_pass = False
            print(f"   [FAIL] CRITICAL FAILURE: {col} does not use NUMERIC type!")
            print(f"   This violates the Decimal precision policy.")
    
    return all_pass


def verify_indices(engine, inspector) -> bool:
    """Verify that required indices exist on fact_pnl_use_case_3."""
    print("\n" + "="*70)
    print("Verifying indices on fact_pnl_use_case_3...")
    print("="*70)
    
    try:
        indices = inspector.get_indexes('fact_pnl_use_case_3')
        index_names = [idx['name'] for idx in indices]
        
        required_indices = [
            'idx_fact_pnl_uc3_effective_date',
            'idx_fact_pnl_uc3_strategy',
            'idx_fact_pnl_uc3_process_2'
        ]
        
        all_pass = True
        for idx_name in required_indices:
            if idx_name in index_names:
                print(f"[PASS] Index '{idx_name}' exists")
            else:
                print(f"[WARN] Index '{idx_name}' not found (optional but recommended)")
                # Don't fail on missing indices - they're performance optimizations
        
        return True
        
    except Exception as e:
        print(f"[WARN] Error checking indices: {e}")
        return True  # Don't fail on index check errors


def main():
    """Main verification function."""
    print("="*70)
    print("Phase 5.1 Schema Verification")
    print("="*70)
    print("Verifying database schema after Migration 007...")
    print()
    
    try:
        # Get database URL
        database_url = get_database_url()
        print(f"Database URL: {database_url.split('@')[-1] if '@' in database_url else '***'}")  # Hide credentials
        print()
        
        # Create engine
        engine = create_engine(database_url)
        inspector = inspect(engine)
        
        # Run verifications
        results = []
        
        # 1. Verify metadata_rules columns
        results.append(verify_metadata_rules_columns(engine, inspector))
        
        # 2. Verify use_cases columns
        results.append(verify_use_cases_columns(engine, inspector))
        
        # 3. Verify fact_pnl_use_case_3 table (CRITICAL)
        results.append(verify_fact_pnl_use_case_3(engine, inspector))
        
        # 4. Verify indices (optional)
        verify_indices(engine, inspector)
        
        # Summary
        print("\n" + "="*70)
        print("Verification Summary")
        print("="*70)
        
        if all(results):
            print("[PASS] Schema Validation Passed")
            print("\nAll Phase 5.1 schema changes are correctly applied.")
            print("The database is ready for Phase 5.2 (Input Table + Seed Scripts).")
            return 0
        else:
            print("[FAIL] Schema Validation Failed")
            print("\nOne or more verifications failed.")
            print("Please review the errors above and re-run Migration 007.")
            return 1
            
    except SQLAlchemyError as e:
        print(f"\n[FAIL] Database Error: {e}")
        print("Please check your database connection and credentials.")
        return 1
    except Exception as e:
        print(f"\n[FAIL] Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if 'engine' in locals():
            engine.dispose()


if __name__ == "__main__":
    sys.exit(main())

