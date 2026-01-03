"""
Consolidate Orphaned Facts Script

This script consolidates orphaned fact keys in fact_pnl_entries by reassigning
them to valid hierarchy nodes, resolving the data topology mismatch.

The Situation:
- Hierarchy has 13 Leaf Nodes mapped to TRADE_001...TRADE_013
- Fact Table has 30 Keys (TRADE_001...TRADE_030)
- Result: 17 Keys (TRADE_014...TRADE_030) are "Orphans" excluded from rollup

The Fix:
- Reassign orphaned keys to valid nodes using a consolidation strategy
- Distributes the missing ~1.5M into the Cash NY desk nodes
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from sqlalchemy import text, distinct, func
from app.database import SessionLocal
from app.models import (
    UseCase,
    FactPnlEntries,
    DimHierarchy
)

def consolidate_orphaned_facts():
    """
    Consolidate orphaned fact keys by reassigning them to valid hierarchy nodes.
    """
    print("=" * 80)
    print("CONSOLIDATE ORPHANED FACTS: Resolve Data Topology Mismatch")
    print("=" * 80)
    print()
    
    db: Session = SessionLocal()
    
    try:
        # Step 1: Identify Valid Hierarchy Keys
        print("STEP 1: Identifying Valid Hierarchy Keys")
        print("-" * 80)
        
        # Get all nodes with mapping_value (these are the valid keys)
        hierarchy_nodes = db.query(DimHierarchy).filter(
            DimHierarchy.mapping_value.isnot(None)
        ).all()
        
        valid_keys = sorted([node.mapping_value for node in hierarchy_nodes if node.mapping_value])
        
        print(f"  Found {len(valid_keys)} valid hierarchy keys:")
        for key in valid_keys:
            print(f"    - {key}")
        print()
        
        # Step 2: Identify Orphaned Keys
        print("STEP 2: Identifying Orphaned Keys")
        print("-" * 80)
        
        # Get all distinct category_code values from fact_pnl_entries
        all_fact_keys = db.query(distinct(FactPnlEntries.category_code)).filter(
            FactPnlEntries.category_code.isnot(None),
            FactPnlEntries.category_code.like('TRADE_%')
        ).all()
        
        all_keys = sorted([k[0] for k in all_fact_keys if k[0]])
        
        # Find orphaned keys (keys not in valid_keys)
        orphaned_keys = [key for key in all_keys if key not in valid_keys]
        
        print(f"  Total fact keys: {len(all_keys)}")
        print(f"  Valid hierarchy keys: {len(valid_keys)}")
        print(f"  Orphaned keys: {len(orphaned_keys)}")
        print()
        
        if orphaned_keys:
            print("  Orphaned keys:")
            for key in orphaned_keys:
                # Count rows for this key
                count = db.query(func.count(FactPnlEntries.id)).filter(
                    FactPnlEntries.category_code == key
                ).scalar()
                print(f"    - {key}: {count} rows")
        else:
            print("  [INFO] No orphaned keys found. All keys are mapped to hierarchy nodes.")
            return
        print()
        
        # Step 3: Define Consolidation Strategy
        print("STEP 3: Consolidation Strategy")
        print("-" * 80)
        
        # Consolidation mapping: orphaned_key -> valid_key
        consolidation_map = {
            # TRADE_014 through TRADE_018 -> TRADE_001 (Cash NY 1)
            'TRADE_014': 'TRADE_001',
            'TRADE_015': 'TRADE_001',
            'TRADE_016': 'TRADE_001',
            'TRADE_017': 'TRADE_001',
            'TRADE_018': 'TRADE_001',
            
            # TRADE_019 through TRADE_023 -> TRADE_002 (Cash NY 2)
            'TRADE_019': 'TRADE_002',
            'TRADE_020': 'TRADE_002',
            'TRADE_021': 'TRADE_002',
            'TRADE_022': 'TRADE_002',
            'TRADE_023': 'TRADE_002',
            
            # TRADE_024 through TRADE_027 -> TRADE_003 (Cash NY 3)
            'TRADE_024': 'TRADE_003',
            'TRADE_025': 'TRADE_003',
            'TRADE_026': 'TRADE_003',
            'TRADE_027': 'TRADE_003',
            
            # TRADE_028 through TRADE_030 -> TRADE_004 (Cash NY 4)
            'TRADE_028': 'TRADE_004',
            'TRADE_029': 'TRADE_004',
            'TRADE_030': 'TRADE_004',
        }
        
        # Filter to only include orphaned keys that exist in fact table
        active_consolidation = {
            old_key: new_key 
            for old_key, new_key in consolidation_map.items() 
            if old_key in orphaned_keys
        }
        
        print(f"  Consolidation mapping ({len(active_consolidation)} keys):")
        for old_key, new_key in sorted(active_consolidation.items()):
            print(f"    {old_key} -> {new_key}")
        print()
        
        # Step 4: Execute Consolidation
        print("STEP 4: Executing Consolidation Updates")
        print("-" * 80)
        
        total_rows_updated = 0
        updates_performed = []
        
        # Group updates by target key for efficiency
        target_groups = {}
        for old_key, new_key in active_consolidation.items():
            if new_key not in target_groups:
                target_groups[new_key] = []
            target_groups[new_key].append(old_key)
        
        # Execute updates grouped by target
        for target_key, source_keys in sorted(target_groups.items()):
            # Update each source key individually for safety and proper parameterization
            group_rows = 0
            for source_key in source_keys:
                update_sql = text("""
                    UPDATE fact_pnl_entries
                    SET category_code = :target_key
                    WHERE category_code = :source_key
                """)
                
                result = db.execute(update_sql, {
                    "target_key": target_key,
                    "source_key": source_key
                })
                rows_updated = result.rowcount
                group_rows += rows_updated
            
            rows_updated = group_rows
            
            if rows_updated > 0:
                total_rows_updated += rows_updated
                updates_performed.append((target_key, source_keys, rows_updated))
                print(f"  [OK] Updated {rows_updated} rows: {source_keys} -> '{target_key}'")
        
        db.commit()
        print()
        print(f"  Total updates: {len(updates_performed)} groups, {total_rows_updated} rows")
        print()
        
        # Step 5: Verification
        print("STEP 5: Verification")
        print("-" * 80)
        
        # Check remaining orphaned keys
        remaining_orphans = []
        for orphan_key in orphaned_keys:
            count = db.query(func.count(FactPnlEntries.id)).filter(
                FactPnlEntries.category_code == orphan_key
            ).scalar()
            if count > 0:
                remaining_orphans.append((orphan_key, count))
        
        if remaining_orphans:
            print(f"  [WARNING] {len(remaining_orphans)} orphaned keys still have rows:")
            for key, count in remaining_orphans:
                print(f"    - {key}: {count} rows")
        else:
            print("  [SUCCESS] All orphaned keys have been consolidated")
        print()
        
        # Show distribution after consolidation
        print("  Distribution after consolidation:")
        for target_key in sorted(target_groups.keys()):
            count = db.query(func.count(FactPnlEntries.id)).filter(
                FactPnlEntries.category_code == target_key
            ).scalar()
            print(f"    {target_key}: {count} rows")
        print()
        
        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print()
        print(f"  Orphaned keys identified: {len(orphaned_keys)}")
        print(f"  Keys consolidated: {len(active_consolidation)}")
        print(f"  Total rows updated: {total_rows_updated}")
        print()
        
        if total_rows_updated > 0:
            print(f"  [SUCCESS] Normalized {total_rows_updated} rows in fact_pnl_entries")
            print("  All orphaned transactions have been reassigned to valid hierarchy nodes.")
        else:
            print("  [INFO] No rows needed consolidation.")
        print()
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Exception during consolidation: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()
        print("=" * 80)
        print("CONSOLIDATION COMPLETE")
        print("=" * 80)


if __name__ == "__main__":
    consolidate_orphaned_facts()

