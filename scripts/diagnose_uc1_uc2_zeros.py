"""
Diagnostic Script: Use Case 1 & 2 Zero P&L Issue
================================================

Investigates why Use Cases 1 & 2 are showing 0 P&L values in Tab 3 and Tab 4.

Checks:
1. Data existence in fact_pnl_gold and fact_pnl_entries
2. Use case configuration
3. Hierarchy node matching
4. Legacy rollup function behavior
"""

import sys
from pathlib import Path
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import create_db_engine, get_database_url
from app.models import (
    UseCase,
    FactPnlGold,
    FactPnlEntries,
    DimHierarchy
)

def diagnose_use_cases():
    """Diagnose Use Cases 1 & 2 zero P&L issue."""
    
    print("=" * 80)
    print("DIAGNOSTIC: Use Case 1 & 2 Zero P&L Issue")
    print("=" * 80)
    
    engine = create_db_engine(get_database_url())
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Step 1: Find Use Cases 1 & 2
        print("\n[STEP 1] Finding Use Cases 1 & 2...")
        
        use_case_1 = session.query(UseCase).filter(
            UseCase.name == "America Trading P&L"
        ).first()
        
        use_case_2 = session.query(UseCase).filter(
            UseCase.name == "Project Sterling - Multi-Dimensional Facts"
        ).first()
        
        if not use_case_1:
            print("  ❌ Use Case 1 (America Trading P&L) NOT FOUND!")
            return
        
        if not use_case_2:
            print("  ❌ Use Case 2 (Project Sterling) NOT FOUND!")
            return
        
        print(f"  ✅ Use Case 1: {use_case_1.name}")
        print(f"     ID: {use_case_1.use_case_id}")
        print(f"     input_table_name: {use_case_1.input_table_name}")
        print(f"     Status: {use_case_1.status}")
        
        print(f"  ✅ Use Case 2: {use_case_2.name}")
        print(f"     ID: {use_case_2.use_case_id}")
        print(f"     input_table_name: {use_case_2.input_table_name}")
        print(f"     Status: {use_case_2.status}")
        
        # Step 2: Check fact_pnl_gold data (Use Case 1)
        print("\n[STEP 2] Checking fact_pnl_gold data (Use Case 1)...")
        
        total_gold_rows = session.query(FactPnlGold).count()
        print(f"  Total rows in fact_pnl_gold: {total_gold_rows}")
        
        if total_gold_rows > 0:
            # Sample some rows
            sample_gold = session.query(FactPnlGold).limit(5).all()
            print(f"  Sample rows:")
            for row in sample_gold:
                print(f"    cc_id: {row.cc_id}, daily_pnl: {row.daily_pnl}, trade_date: {row.trade_date}")
            
            # Check if there's any data
            total_daily = session.query(func.sum(FactPnlGold.daily_pnl)).scalar()
            print(f"  Total daily_pnl sum: {total_daily}")
            
            # Get unique cc_ids
            unique_cc_ids = session.query(FactPnlGold.cc_id).distinct().limit(10).all()
            print(f"  Sample cc_ids (first 10): {[r[0] for r in unique_cc_ids]}")
        else:
            print("  ❌ NO DATA in fact_pnl_gold!")
        
        # Step 3: Check fact_pnl_entries data (Use Case 2)
        print("\n[STEP 3] Checking fact_pnl_entries data (Use Case 2)...")
        
        entries_count_uc2 = session.query(FactPnlEntries).filter(
            FactPnlEntries.use_case_id == use_case_2.use_case_id
        ).count()
        
        print(f"  Rows in fact_pnl_entries for Use Case 2: {entries_count_uc2}")
        
        if entries_count_uc2 > 0:
            # Sample some rows
            sample_entries = session.query(FactPnlEntries).filter(
                FactPnlEntries.use_case_id == use_case_2.use_case_id
            ).limit(5).all()
            
            print(f"  Sample rows:")
            for row in sample_entries:
                print(f"    category_code: {row.category_code}, daily_amount: {row.daily_amount}, scenario: {row.scenario}")
            
            # Check ACTUAL scenario
            actual_count = session.query(FactPnlEntries).filter(
                FactPnlEntries.use_case_id == use_case_2.use_case_id,
                FactPnlEntries.scenario == 'ACTUAL'
            ).count()
            print(f"  Rows with scenario='ACTUAL': {actual_count}")
            
            # Get unique category_codes
            unique_codes = session.query(FactPnlEntries.category_code).filter(
                FactPnlEntries.use_case_id == use_case_2.use_case_id
            ).distinct().limit(10).all()
            print(f"  Sample category_codes (first 10): {[r[0] for r in unique_codes]}")
        else:
            print("  ❌ NO DATA in fact_pnl_entries for Use Case 2!")
        
        # Step 4: Check hierarchy nodes for Use Case 1
        print("\n[STEP 4] Checking hierarchy nodes for Use Case 1...")
        
        hierarchy_uc1 = session.query(DimHierarchy).filter(
            DimHierarchy.atlas_source == use_case_1.atlas_structure_id
        ).all()
        
        print(f"  Total hierarchy nodes: {len(hierarchy_uc1)}")
        
        if hierarchy_uc1:
            leaf_nodes = [h for h in hierarchy_uc1 if h.is_leaf]
            print(f"  Leaf nodes: {len(leaf_nodes)}")
            
            # Sample leaf node_ids
            sample_leaf_ids = [h.node_id for h in leaf_nodes[:10]]
            print(f"  Sample leaf node_ids (first 10): {sample_leaf_ids}")
            
            # Check if any leaf node_ids match cc_ids in fact_pnl_gold
            if total_gold_rows > 0:
                matching_count = 0
                for leaf in leaf_nodes[:20]:  # Check first 20
                    match = session.query(FactPnlGold).filter(
                        FactPnlGold.cc_id == leaf.node_id
                    ).first()
                    if match:
                        matching_count += 1
                
                print(f"  Matching leaf nodes (first 20 checked): {matching_count}/20")
                if matching_count == 0:
                    print("  ⚠️  WARNING: No matching cc_ids found between hierarchy and fact_pnl_gold!")
        
        # Step 5: Check hierarchy nodes for Use Case 2
        print("\n[STEP 5] Checking hierarchy nodes for Use Case 2...")
        
        hierarchy_uc2 = session.query(DimHierarchy).filter(
            DimHierarchy.atlas_source == use_case_2.atlas_structure_id
        ).all()
        
        print(f"  Total hierarchy nodes: {len(hierarchy_uc2)}")
        
        if hierarchy_uc2:
            leaf_nodes = [h for h in hierarchy_uc2 if h.is_leaf]
            print(f"  Leaf nodes: {len(leaf_nodes)}")
            
            # Sample leaf node_ids
            sample_leaf_ids = [h.node_id for h in leaf_nodes[:10]]
            print(f"  Sample leaf node_ids (first 10): {sample_leaf_ids}")
            
            # Check if any leaf node_ids match category_codes in fact_pnl_entries
            if entries_count_uc2 > 0:
                matching_count = 0
                for leaf in leaf_nodes[:20]:  # Check first 20
                    match = session.query(FactPnlEntries).filter(
                        FactPnlEntries.use_case_id == use_case_2.use_case_id,
                        FactPnlEntries.category_code == leaf.node_id
                    ).first()
                    if match:
                        matching_count += 1
                
                print(f"  Matching leaf nodes (first 20 checked): {matching_count}/20")
                if matching_count == 0:
                    print("  ⚠️  WARNING: No matching category_codes found between hierarchy and fact_pnl_entries!")
        
        # Step 6: Check if migration scripts affected data
        print("\n[STEP 6] Checking for migration-related issues...")
        print("  Checking if export/import scripts might have affected data...")
        
        # Check if fact_pnl_gold has any recent data
        if total_gold_rows > 0:
            latest_date = session.query(func.max(FactPnlGold.trade_date)).scalar()
            print(f"  Latest trade_date in fact_pnl_gold: {latest_date}")
        
        if entries_count_uc2 > 0:
            latest_date = session.query(func.max(FactPnlEntries.pnl_date)).filter(
                FactPnlEntries.use_case_id == use_case_2.use_case_id
            ).scalar()
            print(f"  Latest pnl_date in fact_pnl_entries (UC2): {latest_date}")
        
        print("\n" + "=" * 80)
        print("DIAGNOSTIC COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
        engine.dispose()

if __name__ == "__main__":
    diagnose_use_cases()

