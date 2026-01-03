"""
Diagnostic script to check why Tab 4 isn't showing Math rules
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine
import json

def main():
    print("=" * 80)
    print("TAB 4 MATH RULE DIAGNOSTIC")
    print("=" * 80)
    print()
    
    uc3_id = 'fce60983-0328-496b-b6e1-34249ec5aa5a'
    node_id = 'NODE_4'  # Commissions
    
    with engine.connect() as conn:
        # Step 1: Check if rule exists in database
        print("Step 1: Checking rule in metadata_rules table...")
        rule_result = conn.execute(text("""
            SELECT 
                rule_id,
                node_id,
                rule_type,
                rule_expression,
                rule_dependencies,
                logic_en,
                sql_where
            FROM metadata_rules
            WHERE use_case_id = :uc3_id
              AND node_id = :node_id
        """), {"uc3_id": str(uc3_id), "node_id": node_id})
        
        rule = rule_result.fetchone()
        if rule:
            rule_id, node_id_db, rule_type, rule_expression, rule_dependencies, logic_en, sql_where = rule
            print(f"[OK] Rule found:")
            print(f"   Rule ID: {rule_id}")
            print(f"   Node ID: {node_id_db}")
            print(f"   Rule Type: {rule_type}")
            print(f"   Rule Expression: {rule_expression}")
            print(f"   Rule Dependencies: {rule_dependencies}")
            print(f"   Logic EN: {logic_en}")
            print(f"   SQL Where: {sql_where}")
            print()
        else:
            print("[ERROR] No rule found for NODE_4!")
            return 1
        
        # Step 2: Check latest calculation results
        print("Step 2: Checking latest calculation results...")
        calc_result = conn.execute(text("""
            SELECT 
                fcr.node_id,
                fcr.run_id,
                fcr.is_override,
                ucr.run_timestamp
            FROM fact_calculated_results fcr
            JOIN use_case_runs ucr ON fcr.run_id = ucr.run_id
            WHERE ucr.use_case_id = :uc3_id
              AND fcr.node_id = :node_id
              AND ucr.run_timestamp = (
                  SELECT MAX(run_timestamp)
                  FROM use_case_runs
                  WHERE use_case_id = :uc3_id
              )
        """), {"uc3_id": str(uc3_id), "node_id": node_id})
        
        calc_data = calc_result.fetchone()
        if calc_data:
            node_id_calc, run_id, is_override, run_timestamp = calc_data
            print(f"[OK] Calculation result found:")
            print(f"   Node ID: {node_id_calc}")
            print(f"   Run ID: {run_id}")
            print(f"   Is Override: {is_override}")
            print(f"   Run Timestamp: {run_timestamp}")
            print()
        else:
            print("[WARNING] No calculation result found for NODE_4!")
            print()
        
        # Step 3: Simulate what the API does - check rules_dict lookup
        print("Step 3: Simulating API rules_dict lookup...")
        all_rules_result = conn.execute(text("""
            SELECT 
                node_id,
                rule_id,
                rule_type,
                rule_expression,
                rule_dependencies,
                logic_en,
                sql_where
            FROM metadata_rules
            WHERE use_case_id = :uc3_id
        """), {"uc3_id": str(uc3_id)})
        
        all_rules = all_rules_result.fetchall()
        rules_dict = {rule[0]: rule for rule in all_rules}  # node_id -> rule tuple
        
        print(f"[OK] Loaded {len(rules_dict)} rules for use case")
        print(f"   Rules for nodes: {list(rules_dict.keys())}")
        print()
        
        # Check if NODE_4 is in the dict
        if node_id in rules_dict:
            rule_tuple = rules_dict[node_id]
            print(f"[OK] NODE_4 found in rules_dict:")
            print(f"   Node ID: {rule_tuple[0]}")
            print(f"   Rule ID: {rule_tuple[1]}")
            print(f"   Rule Type: {rule_tuple[2]}")
            print(f"   Rule Expression: {rule_tuple[3]}")
            print(f"   Rule Dependencies: {rule_tuple[4]}")
            print(f"   Logic EN: {rule_tuple[5]}")
            print()
            
            # Step 4: Check what the API would return
            print("Step 4: Simulating API response construction...")
            rule_obj = {
                'rule_id': str(rule_tuple[1]) if rule_tuple[1] else None,
                'rule_name': rule_tuple[5] if rule_tuple[5] else None,
                'description': rule_tuple[5] if rule_tuple[5] else None,
                'logic_en': rule_tuple[5] if rule_tuple[5] else None,
                'sql_where': rule_tuple[6] if rule_tuple[6] else None,
                'rule_type': rule_tuple[2] if rule_tuple[2] else None,
                'rule_expression': rule_tuple[3] if rule_tuple[3] else None,
                'rule_dependencies': rule_tuple[4] if rule_tuple[4] else None,
            }
            
            print(f"[OK] API would return rule object:")
            print(json.dumps(rule_obj, indent=2))
            print()
            
            # Step 5: Check if rule_expression is None or empty
            if not rule_obj['rule_expression']:
                print("[ERROR] rule_expression is None or empty!")
                print("   This would cause the frontend to not detect it as a Math rule.")
            else:
                print(f"[OK] rule_expression is populated: '{rule_obj['rule_expression']}'")
            
            if not rule_obj['rule_type']:
                print("[WARNING] rule_type is None!")
                print("   Frontend fallback should still work (checks rule_expression)")
            else:
                print(f"[OK] rule_type is populated: '{rule_obj['rule_type']}'")
        else:
            print(f"[ERROR] NODE_4 NOT found in rules_dict!")
            print(f"   Available node_ids: {list(rules_dict.keys())}")
            return 1
        
        # Step 6: Check JSONB field handling
        print()
        print("Step 6: Checking JSONB field (rule_dependencies)...")
        if rule_dependencies:
            print(f"   Type: {type(rule_dependencies)}")
            print(f"   Value: {rule_dependencies}")
            if isinstance(rule_dependencies, dict):
                print("   [OK] JSONB is dict (correct)")
            elif isinstance(rule_dependencies, list):
                print("   [OK] JSONB is list (correct)")
            else:
                print(f"   [WARNING] JSONB is {type(rule_dependencies)} (might need conversion)")
        else:
            print("   [INFO] rule_dependencies is None (OK for this rule)")
        
        print()
        print("=" * 80)
        print("DIAGNOSIS COMPLETE")
        print("=" * 80)
        
        return 0

if __name__ == "__main__":
    exit(main())

