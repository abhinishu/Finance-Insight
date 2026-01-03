"""
Find rule for NODE_5 (Commissions) in Use Case 3 - might have different rule_id
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
    print("FINDING RULE FOR NODE_5 (COMMISSIONS) IN USE CASE 3")
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
        
        # Find rule for NODE_5
        print("Searching for rule with node_id = 'NODE_5'...")
        result = conn.execute(text("""
            SELECT 
                rule_id,
                node_id,
                rule_type,
                measure_name,
                sql_where,
                logic_en,
                predicate_json
            FROM metadata_rules
            WHERE use_case_id = :uc3_id
              AND node_id = 'NODE_5'
        """), {"uc3_id": str(uc3_id)})
        
        node5_rules = result.fetchall()
        
        if not node5_rules:
            print("[NOT FOUND] No rule found for NODE_5 in Use Case 3")
            print()
            print("Searching for any rule with 'commission' in measure_name or logic_en...")
            result = conn.execute(text("""
                SELECT 
                    rule_id,
                    node_id,
                    measure_name,
                    sql_where,
                    logic_en
                FROM metadata_rules
                WHERE use_case_id = :uc3_id
                  AND (
                    measure_name ILIKE '%commission%'
                    OR logic_en ILIKE '%commission%'
                  )
            """), {"uc3_id": str(uc3_id)})
            
            commission_rules = result.fetchall()
            if commission_rules:
                print(f"[FOUND] {len(commission_rules)} rule(s) with 'commission':")
                for rule in commission_rules:
                    print(f"   Rule {rule[0]} (node {rule[1]}):")
                    print(f"      measure_name: {rule[2]}")
                    print(f"      sql_where: {rule[3]}")
                    print(f"      logic_en: {rule[4]}")
            else:
                print("[NOT FOUND] No rules with 'commission' found")
            
            print()
            print("Listing ALL rules for Use Case 3:")
            result = conn.execute(text("""
                SELECT rule_id, node_id, measure_name, sql_where
                FROM metadata_rules
                WHERE use_case_id = :uc3_id
                ORDER BY rule_id
            """), {"uc3_id": str(uc3_id)})
            
            all_rules = result.fetchall()
            for rule in all_rules:
                print(f"   Rule {rule[0]} (node {rule[1]}, measure: {rule[2]}): {rule[3] or '(empty)'}")
            
            return 0
        
        print(f"[FOUND] {len(node5_rules)} rule(s) for NODE_5:")
        print()
        
        for rule in node5_rules:
            rule_id, node_id, rule_type, measure_name, sql_where, logic_en, predicate_json = rule
            print(f"Rule {rule_id}:")
            print(f"   Node ID: {node_id}")
            print(f"   Rule Type: {rule_type}")
            print(f"   Measure: {measure_name}")
            print(f"   sql_where: {sql_where or '(empty)'}")
            print(f"   logic_en: {logic_en or '(empty)'}")
            
            if sql_where and 'strategy_id' in sql_where.lower():
                print()
                print(f"   [PROBLEM] Contains 'strategy_id' - needs to be fixed!")
                
                new_sql_where = sql_where.replace('strategy_id', 'strategy').replace('STRATEGY_ID', 'strategy')
                new_logic_en = logic_en.replace('strategy_id', 'strategy').replace('STRATEGY_ID', 'strategy') if logic_en else None
                
                print(f"   Fix SQL:")
                print(f"   UPDATE metadata_rules")
                print(f"   SET sql_where = {repr(new_sql_where)}")
                if new_logic_en and new_logic_en != logic_en:
                    print(f"   , logic_en = {repr(new_logic_en)}")
                print(f"   WHERE rule_id = {rule_id};")
        
        return 0

if __name__ == "__main__":
    exit(main())

