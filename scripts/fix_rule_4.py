"""
Fix Rule 4 - Update sql_where from strategy_id to strategy
This rule has 'strategy_id = CORE' which matches the error pattern
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
    print("FIXING RULE 4 - strategy_id -> strategy")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        # Verify Rule 4 exists
        print("Step 1: Verifying Rule 4...")
        result = conn.execute(text("""
            SELECT 
                r.rule_id,
                r.node_id,
                r.rule_type,
                r.measure_name,
                r.sql_where,
                r.logic_en,
                r.use_case_id,
                uc.name as use_case_name
            FROM metadata_rules r
            LEFT JOIN use_cases uc ON r.use_case_id = uc.use_case_id
            WHERE r.rule_id = 4
        """))
        
        rule = result.fetchone()
        if not rule:
            print("[ERROR] Rule 4 not found!")
            return 1
        
        rule_id, node_id, rule_type, measure_name, sql_where, logic_en, uc_id, uc_name = rule
        
        print(f"[OK] Rule 4 found:")
        print(f"   Use Case: {uc_name or 'N/A'}")
        print(f"   Node ID: {node_id}")
        print(f"   Rule Type: {rule_type}")
        print(f"   Measure: {measure_name}")
        print(f"   Current sql_where: {sql_where}")
        print(f"   Current logic_en: {logic_en}")
        print()
        
        # Check if it needs fixing
        if not sql_where or 'strategy_id' not in sql_where.lower():
            print("[OK] Rule 4 does not contain 'strategy_id' - no fix needed")
            return 0
        
        # Prepare fix
        print("Step 2: Preparing fix...")
        new_sql_where = sql_where.replace('strategy_id', 'strategy').replace('STRATEGY_ID', 'strategy')
        new_logic_en = logic_en.replace('strategy_id', 'strategy').replace('STRATEGY_ID', 'strategy') if logic_en else None
        
        print(f"   OLD sql_where: {sql_where}")
        print(f"   NEW sql_where: {new_sql_where}")
        if logic_en:
            print(f"   OLD logic_en: {logic_en}")
            print(f"   NEW logic_en: {new_logic_en}")
        print()
        
        # Execute update
        print("Step 3: Executing UPDATE...")
        try:
            if new_logic_en and new_logic_en != logic_en:
                conn.execute(text("""
                    UPDATE metadata_rules
                    SET sql_where = :new_sql_where,
                        logic_en = :new_logic_en
                    WHERE rule_id = 4
                """), {
                    "new_sql_where": new_sql_where,
                    "new_logic_en": new_logic_en
                })
            else:
                conn.execute(text("""
                    UPDATE metadata_rules
                    SET sql_where = :new_sql_where
                    WHERE rule_id = 4
                """), {
                    "new_sql_where": new_sql_where
                })
            
            conn.commit()
            print("[OK] Update successful!")
            print()
            
            # Verify
            print("Step 4: Verifying update...")
            result = conn.execute(text("""
                SELECT sql_where, logic_en
                FROM metadata_rules
                WHERE rule_id = 4
            """))
            
            updated = result.fetchone()
            if updated:
                updated_sql, updated_logic = updated
                print(f"[OK] Verified:")
                print(f"   sql_where: {updated_sql}")
                if updated_logic:
                    print(f"   logic_en: {updated_logic}")
                
                if 'strategy_id' in updated_sql.lower():
                    print()
                    print("[WARNING] Rule still contains 'strategy_id'!")
                    return 1
                else:
                    print()
                    print("[SUCCESS] Rule 4 has been fixed!")
                    print("   Column name changed from 'strategy_id' to 'strategy'")
                    return 0
            else:
                print("[ERROR] Could not verify update")
                return 1
                
        except Exception as e:
            conn.rollback()
            print(f"[ERROR] Update failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

if __name__ == "__main__":
    exit(main())

