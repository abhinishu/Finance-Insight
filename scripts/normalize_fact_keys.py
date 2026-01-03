"""
Normalize Fact Keys Script

This script normalizes category_code values in fact_pnl_entries to match
the mapping_value from dim_hierarchy, ensuring data consistency.

The Problem:
- Hierarchy expects keys like TRADE_005 (from mapping_value column)
- Fact table contains a mix: some TRADE_005, some legacy CC_AMER_PROG_TRADING_005
- Some keys are missing or mismatched

The Fix:
- Update fact_pnl_entries.category_code to use mapping_value instead of legacy node_id values
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

def normalize_fact_keys():
    """
    Normalize category_code values in fact_pnl_entries to match hierarchy mapping_value.
    """
    print("=" * 80)
    print("NORMALIZE FACT KEYS: Align fact_pnl_entries with Hierarchy Mapping")
    print("=" * 80)
    print()
    
    db: Session = SessionLocal()
    
    try:
        # Step 1: Fetch Hierarchy Mapping
        print("STEP 1: Fetching Hierarchy Mapping")
        print("-" * 80)
        
        # Load all nodes where mapping_value is NOT NULL
        hierarchy_nodes = db.query(DimHierarchy).filter(
            DimHierarchy.mapping_value.isnot(None)
        ).all()
        
        # Create map: { old_key (node_id): new_key (mapping_value) }
        # Example: { 'CC_AMER_PROG_TRADING_005': 'TRADE_005', ... }
        mapping_dict = {}
        for node in hierarchy_nodes:
            if node.node_id and node.mapping_value:
                mapping_dict[node.node_id] = node.mapping_value
        
        print(f"  Found {len(mapping_dict)} nodes with mapping_value")
        print()
        
        if not mapping_dict:
            print("  [WARNING] No mapping values found in hierarchy!")
            print("  Run migrate_mapping_values.py first.")
            return
        
        # Show sample mappings
        print("  Sample mappings:")
        sample_count = 0
        for old_key, new_key in sorted(mapping_dict.items())[:10]:
            print(f"    '{old_key}' -> '{new_key}'")
            sample_count += 1
        if len(mapping_dict) > sample_count:
            print(f"    ... and {len(mapping_dict) - sample_count} more")
        print()
        
        # Step 2: Update Fact Table - Direct Mappings
        print("STEP 2: Updating Fact Table (Direct Mappings)")
        print("-" * 80)
        
        total_rows_updated = 0
        updates_performed = []
        
        # Iterate through the mapping dictionary
        for old_key, new_key in mapping_dict.items():
            # Update fact_pnl_entries where category_code matches the old key
            update_sql = text("""
                UPDATE fact_pnl_entries
                SET category_code = :new_key
                WHERE category_code = :old_key
            """)
            
            result = db.execute(update_sql, {
                "new_key": new_key,
                "old_key": old_key
            })
            rows_updated = result.rowcount
            
            if rows_updated > 0:
                total_rows_updated += rows_updated
                updates_performed.append((old_key, new_key, rows_updated))
                print(f"  [OK] Updated {rows_updated} rows: '{old_key}' -> '{new_key}'")
        
        db.commit()
        print()
        print(f"  Direct mappings: {len(updates_performed)} updates, {total_rows_updated} rows")
        print()
        
        # Step 3: Handle Missing NY Cash Nodes (Pattern-based)
        print("STEP 3: Handling Missing NY Cash Nodes (Pattern-based)")
        print("-" * 80)
        
        # Find nodes that match CC_AMER_CASH_NY_% pattern
        ny_cash_nodes = db.query(DimHierarchy).filter(
            DimHierarchy.node_id.like('CC_AMER_CASH_NY_%'),
            DimHierarchy.mapping_value.isnot(None)
        ).all()
        
        ny_updates = 0
        for node in ny_cash_nodes:
            # Extract suffix from node_id (e.g., CC_AMER_CASH_NY_001 -> 001)
            parts = node.node_id.split('_')
            if len(parts) > 0:
                suffix = parts[-1]
                expected_mapping = f"TRADE_{suffix}"
                
                # Update any rows that match the old pattern
                # This handles cases where category_code might be CC_AMER_CASH_NY_001 instead of TRADE_001
                update_sql = text("""
                    UPDATE fact_pnl_entries
                    SET category_code = :new_key
                    WHERE category_code = :old_key
                """)
                
                result = db.execute(update_sql, {
                    "new_key": expected_mapping,
                    "old_key": node.node_id
                })
                rows_updated = result.rowcount
                
                if rows_updated > 0:
                    ny_updates += rows_updated
                    print(f"  [OK] Updated {rows_updated} rows: '{node.node_id}' -> '{expected_mapping}'")
        
        db.commit()
        total_rows_updated += ny_updates
        print()
        print(f"  NY Cash pattern updates: {ny_updates} rows")
        print()
        
        # Step 4: Handle Other Legacy Patterns
        print("STEP 4: Handling Other Legacy Patterns")
        print("-" * 80)
        
        # Check for any remaining CC_XXX patterns that should be TRADE_XXX
        # This catches any legacy keys we might have missed
        legacy_updates = 0
        
        # Get all distinct category_code values that start with 'CC_' but aren't in our mapping
        legacy_codes = db.query(distinct(FactPnlEntries.category_code)).filter(
            FactPnlEntries.category_code.like('CC_%'),
            ~FactPnlEntries.category_code.in_(list(mapping_dict.keys()))
        ).all()
        
        legacy_codes_list = [c[0] for c in legacy_codes if c[0]]
        
        if legacy_codes_list:
            print(f"  Found {len(legacy_codes_list)} legacy CC_XXX codes not in mapping:")
            for legacy_code in legacy_codes_list[:10]:
                print(f"    - '{legacy_code}'")
            if len(legacy_codes_list) > 10:
                print(f"    ... and {len(legacy_codes_list) - 10} more")
            print()
            
            # Try to map them by extracting suffix
            for legacy_code in legacy_codes_list:
                parts = legacy_code.split('_')
                if len(parts) > 1:
                    suffix = parts[-1]
                    try:
                        # Validate suffix is numeric
                        int(suffix)
                        candidate_mapping = f"TRADE_{suffix}"
                        
                        # Check if this candidate exists in our mapping values
                        if candidate_mapping in mapping_dict.values():
                            # Update to the candidate mapping
                            update_sql = text("""
                                UPDATE fact_pnl_entries
                                SET category_code = :new_key
                                WHERE category_code = :old_key
                            """)
                            
                            result = db.execute(update_sql, {
                                "new_key": candidate_mapping,
                                "old_key": legacy_code
                            })
                            rows_updated = result.rowcount
                            
                            if rows_updated > 0:
                                legacy_updates += rows_updated
                                print(f"  [OK] Updated {rows_updated} rows: '{legacy_code}' -> '{candidate_mapping}'")
                    except ValueError:
                        # Suffix is not numeric, skip
                        pass
        
        db.commit()
        total_rows_updated += legacy_updates
        print()
        print(f"  Legacy pattern updates: {legacy_updates} rows")
        print()
        
        # Step 5: Verification
        print("STEP 5: Verification")
        print("-" * 80)
        
        # Count how many rows now have TRADE_XXX pattern
        trade_pattern_count = db.query(func.count(FactPnlEntries.id)).filter(
            FactPnlEntries.category_code.like('TRADE_%')
        ).scalar()
        
        # Count how many rows still have CC_XXX pattern (should be minimal or zero)
        cc_pattern_count = db.query(func.count(FactPnlEntries.id)).filter(
            FactPnlEntries.category_code.like('CC_%')
        ).scalar()
        
        print(f"  Rows with TRADE_XXX pattern: {trade_pattern_count}")
        print(f"  Rows with CC_XXX pattern: {cc_pattern_count}")
        print()
        
        # Show distribution of category_code values
        distinct_codes = db.query(
            FactPnlEntries.category_code,
            func.count(FactPnlEntries.id).label('count')
        ).group_by(FactPnlEntries.category_code).order_by(func.count(FactPnlEntries.id).desc()).limit(20).all()
        
        print("  Top 20 category_code values:")
        for code, count in distinct_codes:
            print(f"    '{code}': {count} rows")
        print()
        
        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print()
        print(f"  Normalized {total_rows_updated} rows in fact_pnl_entries")
        print(f"  Direct mappings: {len(updates_performed)}")
        print(f"  NY Cash pattern updates: {ny_updates} rows")
        print(f"  Legacy pattern updates: {legacy_updates} rows")
        print()
        
        if cc_pattern_count > 0:
            print(f"  [WARNING] {cc_pattern_count} rows still have CC_XXX pattern")
            print("  These may need manual review or additional mapping rules.")
        else:
            print("  [SUCCESS] All category_code values normalized to TRADE_XXX pattern")
        print()
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Exception during normalization: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()
        print("=" * 80)
        print("NORMALIZATION COMPLETE")
        print("=" * 80)


if __name__ == "__main__":
    normalize_fact_keys()


