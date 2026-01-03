"""
Delete "poisoned" rules for Use Case 3 that contain 'strategy_id' in sql_where.
These rules target a non-existent column and cause calculation crashes.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine

def main():
    print("=" * 80)
    print("DELETING POISONED RULES FOR USE CASE 3")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        # Step 1: Find Use Case 3 ID
        print("Step 1: Finding Use Case 'America Cash Equity Trading'...")
        uc_result = conn.execute(text("""
            SELECT use_case_id, name, input_table_name
            FROM use_cases
            WHERE name = 'America Cash Equity Trading'
        """))
        
        uc_row = uc_result.fetchone()
        if not uc_row:
            print("[ERROR] Use Case 'America Cash Equity Trading' not found!")
            return 1
        
        uc_id, uc_name, input_table = uc_row
        print(f"[OK] Found Use Case: {uc_name}")
        print(f"   Use Case ID: {uc_id}")
        print(f"   Input Table: {input_table}")
        print()
        
        # Step 2: Find poisoned rules
        print("Step 2: Finding rules with 'strategy_id' in sql_where...")
        poisoned_rules = conn.execute(text("""
            SELECT 
                r.rule_id,
                r.node_id,
                h.node_name,
                r.sql_where,
                r.logic_en,
                r.rule_type,
                r.created_at,
                r.last_modified_at
            FROM metadata_rules r
            JOIN dim_hierarchy h ON r.node_id = h.node_id
            WHERE r.use_case_id = :uc_id
              AND r.sql_where IS NOT NULL
              AND r.sql_where ILIKE '%strategy_id%'
            ORDER BY r.rule_id
        """), {"uc_id": str(uc_id)})
        
        rules = poisoned_rules.fetchall()
        
        if not rules:
            print("[OK] No poisoned rules found. All rules are clean!")
            return 0
        
        print(f"[WARNING] Found {len(rules)} poisoned rule(s):")
        print()
        for rule in rules:
            rule_id, node_id, node_name, sql_where, logic_en, rule_type, created_at, last_modified = rule
            print(f"  Rule ID: {rule_id}")
            print(f"  Node: {node_name} ({node_id})")
            print(f"  Type: {rule_type}")
            print(f"  SQL WHERE: {sql_where[:100]}..." if len(sql_where) > 100 else f"  SQL WHERE: {sql_where}")
            print(f"  Logic: {logic_en[:80]}..." if logic_en and len(logic_en) > 80 else f"  Logic: {logic_en or 'N/A'}")
            print(f"  Created: {created_at}")
            print(f"  Last Modified: {last_modified}")
            print()
        
        # Step 3: Confirm deletion
        print("=" * 80)
        print(f"DELETING {len(rules)} POISONED RULE(S)...")
        print("=" * 80)
        print()
        
        # Step 4: Delete the rules
        delete_result = conn.execute(text("""
            DELETE FROM metadata_rules
            WHERE use_case_id = :uc_id
              AND sql_where IS NOT NULL
              AND sql_where ILIKE '%strategy_id%'
        """), {"uc_id": str(uc_id)})
        
        deleted_count = delete_result.rowcount
        conn.commit()
        
        print(f"[OK] Successfully deleted {deleted_count} rule(s)")
        print()
        
        # Step 5: Verify deletion
        print("Step 5: Verifying deletion...")
        verify_result = conn.execute(text("""
            SELECT COUNT(*) as remaining_count
            FROM metadata_rules
            WHERE use_case_id = :uc_id
              AND sql_where IS NOT NULL
              AND sql_where ILIKE '%strategy_id%'
        """), {"uc_id": str(uc_id)})
        
        remaining = verify_result.fetchone()[0]
        
        if remaining == 0:
            print("[OK] Verification: No poisoned rules remain")
        else:
            print(f"[WARNING] {remaining} poisoned rule(s) still exist!")
            return 1
        
        print()
        print("=" * 80)
        print("DELETION COMPLETE")
        print("=" * 80)
        print()
        print("Summary:")
        print(f"  - Use Case: {uc_name}")
        print(f"  - Deleted: {deleted_count} rule(s)")
        print(f"  - Remaining poisoned rules: 0")
        print()
        
        return 0

if __name__ == "__main__":
    exit(main())

