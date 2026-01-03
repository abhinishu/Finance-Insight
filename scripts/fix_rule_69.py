"""
Fix Rule 69 - Update sql_where from strategy_id to strategy
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
    print("FIXING RULE 69 - Column Name Correction")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        # First, verify the rule exists and show current state
        print("Step 1: Verifying Rule 69 exists...")
        result = conn.execute(text("""
            SELECT 
                rule_id,
                node_id,
                rule_type,
                measure_name,
                sql_where,
                logic_en,
                use_case_id
            FROM metadata_rules
            WHERE rule_id = 69
        """))
        
        rule = result.fetchone()
        if not rule:
            print("[ERROR] Rule 69 not found!")
            return 1
        
        rule_id, node_id, rule_type, measure_name, sql_where, logic_en, use_case_id = rule
        
        print(f"[OK] Rule 69 found:")
        print(f"   Node ID: {node_id}")
        print(f"   Rule Type: {rule_type}")
        print(f"   Measure: {measure_name}")
        print(f"   Current sql_where: {sql_where}")
        print(f"   Current logic_en: {logic_en}")
        print()
        
        # Check if it already has the correct column name
        if sql_where and 'strategy =' in sql_where.lower() and 'strategy_id' not in sql_where.lower():
            print("[OK] Rule 69 already has correct column name 'strategy'")
            print("   No update needed.")
            return 0
        
        # Show what will be changed
        print("Step 2: Preparing update...")
        new_sql_where = sql_where.replace('strategy_id', 'strategy').replace('STRATEGY_ID', 'strategy')
        new_logic_en = logic_en.replace('strategy_id', 'strategy').replace('STRATEGY_ID', 'strategy') if logic_en else None
        
        print(f"   OLD sql_where: {sql_where}")
        print(f"   NEW sql_where: {new_sql_where}")
        if logic_en:
            print(f"   OLD logic_en: {logic_en}")
            print(f"   NEW logic_en: {new_logic_en}")
        print()
        
        # Execute the update
        print("Step 3: Executing UPDATE...")
        try:
            if new_logic_en and new_logic_en != logic_en:
                # Update both sql_where and logic_en
                conn.execute(text("""
                    UPDATE metadata_rules
                    SET sql_where = :new_sql_where,
                        logic_en = :new_logic_en
                    WHERE rule_id = 69
                """), {
                    "new_sql_where": new_sql_where,
                    "new_logic_en": new_logic_en
                })
            else:
                # Update only sql_where
                conn.execute(text("""
                    UPDATE metadata_rules
                    SET sql_where = :new_sql_where
                    WHERE rule_id = 69
                """), {
                    "new_sql_where": new_sql_where
                })
            
            conn.commit()
            print("[OK] Update successful!")
            print()
            
            # Verify the update
            print("Step 4: Verifying update...")
            result = conn.execute(text("""
                SELECT sql_where, logic_en
                FROM metadata_rules
                WHERE rule_id = 69
            """))
            
            updated_rule = result.fetchone()
            if updated_rule:
                updated_sql_where, updated_logic_en = updated_rule
                print(f"[OK] Verified:")
                print(f"   sql_where: {updated_sql_where}")
                if updated_logic_en:
                    print(f"   logic_en: {updated_logic_en}")
                
                # Final check
                if 'strategy_id' in updated_sql_where.lower():
                    print()
                    print("[WARNING] Rule still contains 'strategy_id' - update may not have worked correctly")
                    return 1
                else:
                    print()
                    print("[SUCCESS] Rule 69 has been fixed!")
                    print("   Column name changed from 'strategy_id' to 'strategy'")
                    return 0
            else:
                print("[ERROR] Could not verify update - rule not found after update")
                return 1
                
        except Exception as e:
            conn.rollback()
            print(f"[ERROR] Update failed: {e}")
            return 1

if __name__ == "__main__":
    exit(main())

