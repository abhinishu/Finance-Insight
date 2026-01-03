"""
Direct SQL UPDATE for Rule 69 as requested by user
If rule doesn't exist, this will be a no-op
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine

def main():
    print("=" * 80)
    print("UPDATING RULE 69 (DIRECT SQL AS REQUESTED)")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        # First check if Rule 69 exists
        print("Step 1: Checking if Rule 69 exists...")
        result = conn.execute(text("""
            SELECT rule_id, node_id, sql_where, use_case_id
            FROM metadata_rules
            WHERE rule_id = 69
        """))
        
        rule = result.fetchone()
        
        if not rule:
            print("[WARNING] Rule 69 does not exist in the database")
            print()
            print("Attempting UPDATE anyway (will be a no-op if rule doesn't exist)...")
        else:
            rule_id, node_id, sql_where, uc_id = rule
            print(f"[OK] Rule 69 found:")
            print(f"   Node ID: {node_id}")
            print(f"   Current sql_where: {sql_where or '(empty)'}")
            print(f"   Use Case ID: {uc_id}")
            print()
        
        # Execute the UPDATE as requested
        print("Step 2: Executing UPDATE...")
        print("   SQL: UPDATE metadata_rules")
        print("        SET sql_where = 'strategy = ''CORE'''")
        print("        WHERE rule_id = 69;")
        print()
        
        try:
            result = conn.execute(text("""
                UPDATE metadata_rules
                SET sql_where = 'strategy = ''CORE'''
                WHERE rule_id = 69
            """))
            
            rows_affected = result.rowcount
            conn.commit()
            
            if rows_affected == 0:
                print(f"[INFO] UPDATE executed, but 0 rows affected")
                print(f"   This means Rule 69 does not exist (or already has this value)")
                print()
                print("Checking if there's a rule for NODE_5 in Use Case 3...")
                
                # Get Use Case 3
                result = conn.execute(text("""
                    SELECT use_case_id
                    FROM use_cases
                    WHERE name ILIKE '%america%cash%equity%'
                """))
                uc3 = result.fetchone()
                
                if uc3:
                    uc3_id = uc3[0]
                    result = conn.execute(text("""
                        SELECT rule_id, node_id, sql_where
                        FROM metadata_rules
                        WHERE use_case_id = :uc3_id
                          AND node_id = 'NODE_5'
                    """), {"uc3_id": str(uc3_id)})
                    
                    node5_rule = result.fetchone()
                    if node5_rule:
                        print(f"[FOUND] Rule {node5_rule[0]} for NODE_5 in Use Case 3")
                        print(f"   Current sql_where: {node5_rule[2] or '(empty)'}")
                        print()
                        print("Would you like to update this rule instead?")
                    else:
                        print("[NOT FOUND] No rule exists for NODE_5 in Use Case 3")
                        print("   A rule may need to be created first")
            else:
                print(f"[SUCCESS] UPDATE successful - {rows_affected} row(s) affected")
                
                # Verify
                result = conn.execute(text("""
                    SELECT sql_where
                    FROM metadata_rules
                    WHERE rule_id = 69
                """))
                
                updated = result.fetchone()
                if updated:
                    print(f"[VERIFIED] Updated sql_where: {updated[0]}")
            
            return 0
            
        except Exception as e:
            conn.rollback()
            print(f"[ERROR] UPDATE failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

if __name__ == "__main__":
    exit(main())

