"""
Find and fix the rule with strategy_id column name issue for Use Case 3
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
    print("FINDING AND FIXING USE CASE 3 RULE WITH strategy_id ISSUE")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        # Get Use Case 3 ID
        result = conn.execute(text("""
            SELECT use_case_id, name
            FROM use_cases
            WHERE name ILIKE '%america%cash%equity%'
        """))
        uc3_row = result.fetchone()
        
        if not uc3_row:
            print("[ERROR] Use Case 3 not found")
            return 1
        
        uc3_id, uc3_name = uc3_row
        print(f"Use Case: {uc3_name}")
        print(f"Use Case ID: {uc3_id}")
        print()
        
        # Find rules with strategy_id in sql_where
        print("Step 1: Finding rules with 'strategy_id' in sql_where...")
        result = conn.execute(text("""
            SELECT 
                rule_id,
                node_id,
                rule_type,
                measure_name,
                sql_where,
                logic_en
            FROM metadata_rules
            WHERE use_case_id = :uc3_id
              AND sql_where ILIKE '%strategy_id%'
        """), {"uc3_id": str(uc3_id)})
        
        problematic_rules = result.fetchall()
        
        if not problematic_rules:
            print("[OK] No rules found with 'strategy_id' in sql_where")
            print("   The issue may have already been fixed, or the rule uses a different pattern.")
            print()
            print("Checking all rules for Use Case 3...")
            result = conn.execute(text("""
                SELECT rule_id, node_id, sql_where
                FROM metadata_rules
                WHERE use_case_id = :uc3_id
                  AND sql_where IS NOT NULL
            """), {"uc3_id": str(uc3_id)})
            all_rules = result.fetchall()
            print(f"Found {len(all_rules)} rules with sql_where:")
            for rule in all_rules:
                print(f"   Rule {rule[0]} (node {rule[1]}): {rule[2]}")
            return 0
        
        print(f"[FOUND] {len(problematic_rules)} rule(s) with 'strategy_id':")
        print()
        
        for rule in problematic_rules:
            rule_id, node_id, rule_type, measure_name, sql_where, logic_en = rule
            print(f"Rule ID: {rule_id}")
            print(f"   Node ID: {node_id}")
            print(f"   Rule Type: {rule_type}")
            print(f"   Measure: {measure_name}")
            print(f"   Current sql_where: {sql_where}")
            print(f"   Current logic_en: {logic_en}")
            print()
            
            # Prepare fix
            new_sql_where = sql_where.replace('strategy_id', 'strategy').replace('STRATEGY_ID', 'strategy')
            new_logic_en = logic_en.replace('strategy_id', 'strategy').replace('STRATEGY_ID', 'strategy') if logic_en else None
            
            print(f"   Will update to:")
            print(f"   NEW sql_where: {new_sql_where}")
            if new_logic_en:
                print(f"   NEW logic_en: {new_logic_en}")
            print()
            
            # Execute update
            print(f"Step 2: Updating Rule {rule_id}...")
            try:
                if new_logic_en and new_logic_en != logic_en:
                    conn.execute(text("""
                        UPDATE metadata_rules
                        SET sql_where = :new_sql_where,
                            logic_en = :new_logic_en
                        WHERE rule_id = :rule_id
                    """), {
                        "new_sql_where": new_sql_where,
                        "new_logic_en": new_logic_en,
                        "rule_id": rule_id
                    })
                else:
                    conn.execute(text("""
                        UPDATE metadata_rules
                        SET sql_where = :new_sql_where
                        WHERE rule_id = :rule_id
                    """), {
                        "new_sql_where": new_sql_where,
                        "rule_id": rule_id
                    })
                
                conn.commit()
                print(f"[OK] Rule {rule_id} updated successfully!")
                print()
                
                # Verify
                result = conn.execute(text("""
                    SELECT sql_where, logic_en
                    FROM metadata_rules
                    WHERE rule_id = :rule_id
                """), {"rule_id": rule_id})
                
                updated = result.fetchone()
                if updated:
                    updated_sql, updated_logic = updated
                    print(f"[VERIFIED] Rule {rule_id}:")
                    print(f"   sql_where: {updated_sql}")
                    if updated_logic:
                        print(f"   logic_en: {updated_logic}")
                    
                    if 'strategy_id' in updated_sql.lower():
                        print()
                        print("[WARNING] Rule still contains 'strategy_id'!")
                        return 1
                    else:
                        print()
                        print("[SUCCESS] Rule fixed - no more 'strategy_id' found")
                
            except Exception as e:
                conn.rollback()
                print(f"[ERROR] Update failed: {e}")
                return 1
        
        print("=" * 80)
        print("[SUCCESS] All problematic rules have been fixed!")
        print("=" * 80)
        return 0

if __name__ == "__main__":
    exit(main())

