"""
Diagnostic Script: Inspect Data Mismatch between Hierarchy and Facts

This script diagnoses "Join Failure" issues by comparing:
- Fact Keys (category_code from fact_pnl_entries)
- Hierarchy Node IDs (leaf nodes from dim_hierarchy)

For Use Case 1 (America Trading P&L).
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from sqlalchemy import distinct
from app.database import SessionLocal
from app.models import (
    UseCase,
    FactPnlEntries,
    DimHierarchy
)

def inspect_data_mismatch():
    """
    Diagnose join failure by comparing fact keys vs hierarchy node IDs.
    """
    print("=" * 80)
    print("DATA MISMATCH DIAGNOSTIC: Use Case 1 (America Trading P&L)")
    print("=" * 80)
    print()
    
    db: Session = SessionLocal()
    
    try:
        # Step 1: Load Use Case 1 (America Trading)
        print("STEP 1: Loading Use Case 1")
        print("-" * 80)
        
        use_case_1 = db.query(UseCase).filter(
            UseCase.name.ilike('%America Trading%')
        ).first()
        
        if not use_case_1:
            print("  [ERROR] Use Case 1 (America Trading P&L) not found!")
            return
        
        print(f"  Use Case: {use_case_1.name}")
        print(f"  Use Case ID: {use_case_1.use_case_id}")
        print(f"  Atlas Structure ID: {use_case_1.atlas_structure_id}")
        print()
        
        # Step 2: Fetch Fact Keys from fact_pnl_entries
        print("STEP 2: Fetching Fact Keys (category_code from fact_pnl_entries)")
        print("-" * 80)
        
        distinct_codes = db.query(distinct(FactPnlEntries.category_code)).filter(
            FactPnlEntries.use_case_id == use_case_1.use_case_id,
            FactPnlEntries.category_code.isnot(None)
        ).all()
        
        fact_keys = sorted([c[0] for c in distinct_codes if c[0]])
        
        print(f"  Found {len(fact_keys)} distinct category_code values")
        print()
        
        # Step 3: Fetch Hierarchy Leaf Node IDs
        print("STEP 3: Fetching Hierarchy Leaf Node IDs")
        print("-" * 80)
        
        atlas_source = use_case_1.atlas_structure_id
        leaf_nodes = db.query(DimHierarchy).filter(
            DimHierarchy.atlas_source == atlas_source,
            DimHierarchy.is_leaf == True
        ).order_by(DimHierarchy.node_id).all()
        
        node_ids = sorted([n.node_id for n in leaf_nodes])
        
        print(f"  Found {len(node_ids)} leaf nodes in hierarchy")
        print()
        
        # Step 4: Compare and Display
        print("STEP 4: Comparison")
        print("-" * 80)
        print()
        
        print("Fact Keys (Available in DB):")
        print(f"  Count: {len(fact_keys)}")
        if fact_keys:
            print("  Values:")
            for key in fact_keys:
                print(f"    - '{key}'")
        else:
            print("  [WARNING] No fact keys found!")
        print()
        
        print("Node IDs (Expecting Data):")
        print(f"  Count: {len(node_ids)}")
        if node_ids:
            print("  Values:")
            for node_id in node_ids:
                print(f"    - '{node_id}'")
        else:
            print("  [WARNING] No leaf nodes found!")
        print()
        
        # Step 5: Analyze Mismatch
        print("STEP 5: Mismatch Analysis")
        print("-" * 80)
        print()
        
        # Find matches
        matches = set(fact_keys) & set(node_ids)
        fact_only = set(fact_keys) - set(node_ids)
        node_only = set(node_ids) - set(fact_keys)
        
        print(f"  Exact Matches: {len(matches)}")
        if matches:
            print("    Matched keys:")
            for key in sorted(matches):
                print(f"      - '{key}'")
        print()
        
        print(f"  Fact Keys Only (not in hierarchy): {len(fact_only)}")
        if fact_only:
            print("    Unmatched fact keys:")
            for key in sorted(fact_only):
                print(f"      - '{key}'")
        print()
        
        print(f"  Node IDs Only (no fact data): {len(node_only)}")
        if node_only:
            print("    Unmatched node IDs:")
            for node_id in sorted(node_only):
                print(f"      - '{node_id}'")
        print()
        
        # Step 6: Pattern Analysis
        print("STEP 6: Pattern Analysis")
        print("-" * 80)
        print()
        
        # Check if fact keys follow TRADE_XXX pattern
        trade_keys = [k for k in fact_keys if k.startswith('TRADE_')]
        cc_keys = [k for k in fact_keys if k.startswith('CC_')]
        other_keys = [k for k in fact_keys if not k.startswith('TRADE_') and not k.startswith('CC_')]
        
        print(f"  Fact Keys Pattern Breakdown:")
        print(f"    TRADE_XXX pattern: {len(trade_keys)} keys")
        print(f"    CC_XXX pattern: {len(cc_keys)} keys")
        print(f"    Other patterns: {len(other_keys)} keys")
        print()
        
        # Check if node IDs follow CC_XXX pattern
        cc_node_ids = [n for n in node_ids if n.startswith('CC_')]
        other_node_ids = [n for n in node_ids if not n.startswith('CC_')]
        
        print(f"  Node IDs Pattern Breakdown:")
        print(f"    CC_XXX pattern: {len(cc_node_ids)} nodes")
        print(f"    Other patterns: {len(other_node_ids)} nodes")
        print()
        
        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print()
        print(f"  Total Fact Keys: {len(fact_keys)}")
        print(f"  Total Node IDs: {len(node_ids)}")
        print(f"  Exact Matches: {len(matches)}")
        print(f"  Mismatches: {len(fact_only) + len(node_only)}")
        print()
        
        if len(matches) == 0:
            print("  [CRITICAL] No exact matches found!")
            print("  This indicates a complete join failure.")
            print("  Bridge mapping is REQUIRED for all nodes.")
        elif len(matches) < len(node_ids):
            print(f"  [WARNING] Only {len(matches)}/{len(node_ids)} nodes have exact matches.")
            print("  Bridge mapping is needed for remaining nodes.")
        else:
            print("  [OK] All nodes have exact matches.")
        print()
        
    except Exception as e:
        print(f"[ERROR] Exception during inspection: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()
        print("=" * 80)
        print("DIAGNOSTIC COMPLETE")
        print("=" * 80)


if __name__ == "__main__":
    inspect_data_mismatch()


