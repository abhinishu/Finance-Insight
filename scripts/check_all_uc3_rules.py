"""
Check all Use Case 3 rules - including sql_where from predicate_json conversion
"""

import sys
import json
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine
from app.services.rules import convert_json_to_sql

def main():
    print("=" * 80)
    print("COMPREHENSIVE USE CASE 3 RULES CHECK")
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
        
        # Get ALL rules for Use Case 3
        print("Step 1: Fetching all rules for Use Case 3...")
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
            ORDER BY rule_id
        """), {"uc3_id": str(uc3_id)})
        
        rules = result.fetchall()
        print(f"Found {len(rules)} total rules")
        print()
        
        problematic_rules = []
        
        for rule in rules:
            rule_id, node_id, rule_type, measure_name, sql_where, logic_en, predicate_json = rule
            
            print(f"Rule {rule_id} (node {node_id}):")
            print(f"   Type: {rule_type}, Measure: {measure_name}")
            
            # Check direct sql_where
            effective_sql_where = sql_where
            
            # If sql_where is empty/null, try to generate from predicate_json
            if not sql_where and predicate_json:
                try:
                    pred_dict = predicate_json if isinstance(predicate_json, dict) else json.loads(predicate_json)
                    generated_sql = convert_json_to_sql(pred_dict)
                    effective_sql_where = generated_sql
                    print(f"   [NOTE] sql_where is empty, generated from predicate_json: {generated_sql}")
                except Exception as e:
                    print(f"   [NOTE] Could not generate sql_where from predicate_json: {e}")
            
            if effective_sql_where:
                print(f"   sql_where: {effective_sql_where}")
                
                # Check for problematic column names
                sql_upper = effective_sql_where.upper()
                issues = []
                
                if 'STRATEGY_ID' in sql_upper:
                    issues.append("Contains 'strategy_id' (should be 'strategy')")
                if 'BOOK_ID' in sql_upper:
                    issues.append("Contains 'book_id' (should be 'book')")
                if 'CC_ID' in sql_upper:
                    issues.append("Contains 'cc_id' (should be 'cost_center')")
                
                if issues:
                    print(f"   [PROBLEM] Issues found:")
                    for issue in issues:
                        print(f"      - {issue}")
                    problematic_rules.append({
                        'rule_id': rule_id,
                        'node_id': node_id,
                        'sql_where': effective_sql_where,
                        'predicate_json': predicate_json,
                        'issues': issues
                    })
                else:
                    print(f"   [OK] No column name issues")
            else:
                print(f"   [NOTE] No sql_where (empty or null)")
            
            if logic_en:
                print(f"   logic_en: {logic_en}")
            print()
        
        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print()
        
        if problematic_rules:
            print(f"[FOUND] {len(problematic_rules)} rule(s) with column name issues:")
            for rule in problematic_rules:
                print(f"\nRule {rule['rule_id']} (node {rule['node_id']}):")
                print(f"   sql_where: {rule['sql_where']}")
                print(f"   Issues: {', '.join(rule['issues'])}")
                
                # Generate fix
                fixed_sql = rule['sql_where']
                fixed_sql = fixed_sql.replace('strategy_id', 'strategy')
                fixed_sql = fixed_sql.replace('STRATEGY_ID', 'strategy')
                fixed_sql = fixed_sql.replace('book_id', 'book')
                fixed_sql = fixed_sql.replace('BOOK_ID', 'book')
                fixed_sql = fixed_sql.replace('cc_id', 'cost_center')
                fixed_sql = fixed_sql.replace('CC_ID', 'cost_center')
                
                print(f"\n   Fix SQL:")
                print(f"   UPDATE metadata_rules")
                print(f"   SET sql_where = {repr(fixed_sql)}")
                print(f"   WHERE rule_id = {rule['rule_id']};")
        else:
            print("[OK] No rules found with column name issues")
            print("   The error might be coming from a different source, or")
            print("   the rule might be generated dynamically from predicate_json")
        
        return 0

if __name__ == "__main__":
    exit(main())

