"""
Find any rule with 'CORE' in sql_where - might be in a different use case
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
    print("SEARCHING FOR RULE WITH 'CORE' IN SQL WHERE")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        # Search ALL rules for 'CORE' in sql_where
        print("Searching all rules for 'CORE' in sql_where...")
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
            WHERE r.sql_where ILIKE '%CORE%'
            ORDER BY r.rule_id
        """))
        
        rules = result.fetchall()
        
        if not rules:
            print("[NOT FOUND] No rules found with 'CORE' in sql_where")
            print()
            print("Searching for 'strategy_id' in any rule...")
            result = conn.execute(text("""
                SELECT 
                    r.rule_id,
                    r.node_id,
                    r.sql_where,
                    r.use_case_id,
                    uc.name as use_case_name
                FROM metadata_rules r
                LEFT JOIN use_cases uc ON r.use_case_id = uc.use_case_id
                WHERE r.sql_where ILIKE '%strategy_id%'
                ORDER BY r.rule_id
            """))
            
            strategy_id_rules = result.fetchall()
            if strategy_id_rules:
                print(f"[FOUND] {len(strategy_id_rules)} rule(s) with 'strategy_id':")
                for rule in strategy_id_rules:
                    rule_id, node_id, sql_where, uc_id, uc_name = rule
                    print(f"   Rule {rule_id} (node {node_id}, use case: {uc_name or 'N/A'}):")
                    print(f"      sql_where: {sql_where}")
            else:
                print("[NOT FOUND] No rules found with 'strategy_id'")
            
            return 0
        
        print(f"[FOUND] {len(rules)} rule(s) with 'CORE' in sql_where:")
        print()
        
        for rule in rules:
            rule_id, node_id, rule_type, measure_name, sql_where, logic_en, uc_id, uc_name = rule
            print(f"Rule {rule_id}:")
            print(f"   Use Case: {uc_name or 'N/A'} ({uc_id})")
            print(f"   Node ID: {node_id}")
            print(f"   Rule Type: {rule_type}")
            print(f"   Measure: {measure_name}")
            print(f"   sql_where: {sql_where}")
            print(f"   logic_en: {logic_en}")
            print()
            
            # Check if it has strategy_id
            if sql_where and 'strategy_id' in sql_where.lower():
                print(f"   [PROBLEM] Contains 'strategy_id' - needs to be fixed!")
                print()
                
                # Generate fix
                new_sql_where = sql_where.replace('strategy_id', 'strategy').replace('STRATEGY_ID', 'strategy')
                new_logic_en = logic_en.replace('strategy_id', 'strategy').replace('STRATEGY_ID', 'strategy') if logic_en else None
                
                print(f"   Fix SQL:")
                print(f"   UPDATE metadata_rules")
                print(f"   SET sql_where = {repr(new_sql_where)}")
                if new_logic_en and new_logic_en != logic_en:
                    print(f"   , logic_en = {repr(new_logic_en)}")
                print(f"   WHERE rule_id = {rule_id};")
                print()
                
                # Ask if we should fix it
                print(f"   Execute fix? (This will update rule {rule_id})")
                print()
                
                # Auto-fix if it's for Use Case 3
                if uc_name and 'america' in uc_name.lower() and 'cash' in uc_name.lower():
                    print(f"   [AUTO-FIXING] This rule belongs to Use Case 3, applying fix...")
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
                        print(f"   [SUCCESS] Rule {rule_id} has been fixed!")
                        
                        # Verify
                        result = conn.execute(text("""
                            SELECT sql_where, logic_en
                            FROM metadata_rules
                            WHERE rule_id = :rule_id
                        """), {"rule_id": rule_id})
                        
                        updated = result.fetchone()
                        if updated:
                            print(f"   [VERIFIED] Updated sql_where: {updated[0]}")
                            if updated[1]:
                                print(f"   [VERIFIED] Updated logic_en: {updated[1]}")
                    except Exception as e:
                        conn.rollback()
                        print(f"   [ERROR] Fix failed: {e}")
                        return 1
        
        return 0

if __name__ == "__main__":
    exit(main())

