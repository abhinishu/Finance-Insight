"""
Migration 008 Runner: Phase 5.1 Unified Hybrid Engine Schema
Executes the SQL migration and verifies the results.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import SessionLocal
from app.models import DimHierarchy, UseCase
from decimal import Decimal

def run_migration_008():
    """
    Execute Migration 008 and verify results.
    """
    print("=" * 80)
    print("MIGRATION 008: Phase 5.1 Unified Hybrid Engine Schema")
    print("=" * 80)
    print()
    
    db = SessionLocal()
    
    try:
        # Step 1: Read migration SQL file
        print("STEP 1: Reading Migration SQL File")
        print("-" * 80)
        migration_file = project_root / "migration_008_phase5_1_hybrid_engine.sql"
        
        if not migration_file.exists():
            print(f"[ERROR] Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print(f"[OK] Migration file loaded: {migration_file}")
        print()
        
        # Step 2: Execute migration
        print("STEP 2: Executing Migration SQL")
        print("-" * 80)
        
        # Split SQL by semicolons and execute each statement
        # Note: PostgreSQL DO blocks contain semicolons, so we need to be careful
        # For safety, execute the entire file as one transaction
        try:
            db.execute(text(migration_sql))
            db.commit()
            print("[OK] Migration executed successfully")
            print()
        except Exception as e:
            db.rollback()
            print(f"[ERROR] Migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Step 3: Verify Schema Changes
        print("STEP 3: Verifying Schema Changes")
        print("-" * 80)
        
        # Check dim_hierarchy columns
        from sqlalchemy import inspect
        inspector = inspect(db.bind)
        dim_hierarchy_columns = [col['name'] for col in inspector.get_columns('dim_hierarchy')]
        
        required_columns = ['rollup_driver', 'rollup_value_source']
        for col in required_columns:
            if col in dim_hierarchy_columns:
                print(f"  [OK] dim_hierarchy.{col} exists")
            else:
                print(f"  [ERROR] dim_hierarchy.{col} missing!")
                return False
        
        # Check use_cases columns
        use_cases_columns = [col['name'] for col in inspector.get_columns('use_cases')]
        if 'measure_mapping' in use_cases_columns:
            print(f"  [OK] use_cases.measure_mapping exists")
        else:
            print(f"  [ERROR] use_cases.measure_mapping missing!")
            return False
        
        print()
        
        # Step 4: Verify Data Migration
        print("STEP 4: Verifying Data Migration")
        print("-" * 80)
        
        # Use Case 1 (America Trading P&L)
        uc1_nodes = db.query(DimHierarchy).filter(
            DimHierarchy.atlas_source == 'MOCK_ATLAS_v1',
            DimHierarchy.rollup_driver == 'cc_id',
            DimHierarchy.rollup_value_source == 'node_id'
        ).count()
        
        print(f"  Use Case 1 (America Trading): {uc1_nodes} nodes with rollup_driver='cc_id'")
        
        uc1 = db.query(UseCase).filter(
            UseCase.name.ilike('%America Trading%')
        ).first()
        
        if uc1 and uc1.measure_mapping:
            print(f"  Use Case 1 measure_mapping: {uc1.measure_mapping}")
        else:
            print(f"  [WARNING] Use Case 1 measure_mapping is NULL")
        
        print()
        
        # Use Case 2 (Project Sterling)
        uc2_structure_ids = db.query(UseCase.atlas_structure_id).filter(
            (UseCase.name.ilike('%Sterling%')) | (UseCase.name.ilike('%Project%'))
        ).distinct().all()
        
        uc2_structure_ids = [sid[0] for sid in uc2_structure_ids]
        
        if uc2_structure_ids:
            uc2_nodes = db.query(DimHierarchy).filter(
                DimHierarchy.atlas_source.in_(uc2_structure_ids),
                DimHierarchy.rollup_driver == 'category_code',
                DimHierarchy.rollup_value_source == 'node_id'
            ).count()
            
            print(f"  Use Case 2 (Sterling): {uc2_nodes} nodes with rollup_driver='category_code'")
            
            uc2 = db.query(UseCase).filter(
                (UseCase.name.ilike('%Sterling%')) | (UseCase.name.ilike('%Project%'))
            ).first()
            
            if uc2 and uc2.measure_mapping:
                print(f"  Use Case 2 measure_mapping: {uc2.measure_mapping}")
            else:
                print(f"  [WARNING] Use Case 2 measure_mapping is NULL")
        else:
            print(f"  [INFO] Use Case 2 not found (may not exist yet)")
        
        print()
        
        # Use Case 3 (Cash Equity Trading)
        uc3_structure_ids = db.query(UseCase.atlas_structure_id).filter(
            (UseCase.input_table_name == 'fact_pnl_use_case_3') |
            (UseCase.name.ilike('%Cash Equity%')) |
            (UseCase.name.ilike('%America Cash Equity%'))
        ).distinct().all()
        
        uc3_structure_ids = [sid[0] for sid in uc3_structure_ids]
        
        if uc3_structure_ids:
            uc3_leaf_nodes = db.query(DimHierarchy).filter(
                DimHierarchy.atlas_source.in_(uc3_structure_ids),
                DimHierarchy.is_leaf == True,
                DimHierarchy.rollup_driver == 'strategy',
                DimHierarchy.rollup_value_source == 'node_name'
            ).count()
            
            print(f"  Use Case 3 (Cash Equity): {uc3_leaf_nodes} leaf nodes with rollup_driver='strategy'")
            
            uc3 = db.query(UseCase).filter(
                (UseCase.input_table_name == 'fact_pnl_use_case_3') |
                (UseCase.name.ilike('%Cash Equity%'))
            ).first()
            
            if uc3 and uc3.measure_mapping:
                print(f"  Use Case 3 measure_mapping: {uc3.measure_mapping}")
            else:
                print(f"  [WARNING] Use Case 3 measure_mapping is NULL")
        else:
            print(f"  [INFO] Use Case 3 not found (may not exist yet)")
        
        print()
        
        # Step 5: Summary
        print("=" * 80)
        print("MIGRATION 008 COMPLETE")
        print("=" * 80)
        print()
        print("Summary:")
        print(f"  [OK] Schema changes applied")
        print(f"  [OK] Use Case 1: {uc1_nodes} nodes migrated")
        if uc2_structure_ids:
            print(f"  [OK] Use Case 2: {uc2_nodes} nodes migrated")
        if uc3_structure_ids:
            print(f"  [OK] Use Case 3: {uc3_leaf_nodes} leaf nodes migrated")
        print()
        print("Next Steps:")
        print("  1. Verify migration results in database")
        print("  2. Proceed with Step 2: RuleResolver Service")
        print()
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = run_migration_008()
    sys.exit(0 if success else 1)

