"""
Analyze Use Case 3 rules to find SQL WHERE clauses using wrong column names
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
    print("USE CASE 3 RULES ANALYSIS - Column Name Issues")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        # Get Use Case 3 ID
        result = conn.execute(text("""
            SELECT use_case_id, name, input_table_name
            FROM use_cases
            WHERE name ILIKE '%america%cash%equity%'
        """))
        uc3_row = result.fetchone()
        
        if not uc3_row:
            print("[ERROR] Use Case 3 not found")
            return
        
        uc3_id, uc3_name, input_table = uc3_row
        print(f"Use Case: {uc3_name}")
        print(f"Use Case ID: {uc3_id}")
        print(f"Input Table: {input_table}")
        print()
        
        # Get all rules for Use Case 3
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
        print(f"Found {len(rules)} rules for Use Case 3")
        print()
        
        # Analyze each rule
        print("=" * 80)
        print("RULE ANALYSIS")
        print("=" * 80)
        print()
        
        problematic_rules = []
        correct_rules = []
        
        for rule in rules:
            rule_id, node_id, rule_type, measure_name, sql_where, logic_en, predicate_json = rule
            
            if not sql_where:
                continue
            
            # Check for wrong column names
            issues = []
            sql_upper = sql_where.upper()
            
            # Check for strategy_id (should be strategy)
            if 'STRATEGY_ID' in sql_upper:
                issues.append("Uses 'strategy_id' (should be 'strategy')")
            
            # Check for book_id (should be book)
            if 'BOOK_ID' in sql_upper:
                issues.append("Uses 'book_id' (should be 'book')")
            
            # Check for cc_id (should be cost_center)
            if 'CC_ID' in sql_upper or 'CC_ID' in sql_upper.replace(' ', ''):
                issues.append("Uses 'cc_id' (should be 'cost_center')")
            
            # Check for daily_pnl (should be pnl_daily for UC3)
            if 'DAILY_PNL' in sql_upper and input_table == 'fact_pnl_use_case_3':
                issues.append("Uses 'daily_pnl' (should be 'pnl_daily' for fact_pnl_use_case_3)")
            
            # Check for mtd_pnl, ytd_pnl (not available in fact_pnl_use_case_3)
            if input_table == 'fact_pnl_use_case_3':
                if 'MTD_PNL' in sql_upper or 'YTD_PNL' in sql_upper:
                    issues.append("Uses 'mtd_pnl' or 'ytd_pnl' (not available in fact_pnl_use_case_3)")
            
            if issues:
                problematic_rules.append({
                    'rule_id': rule_id,
                    'node_id': node_id,
                    'rule_type': rule_type,
                    'measure_name': measure_name,
                    'sql_where': sql_where,
                    'logic_en': logic_en,
                    'issues': issues
                })
            else:
                correct_rules.append({
                    'rule_id': rule_id,
                    'node_id': node_id,
                    'sql_where': sql_where,
                    'logic_en': logic_en
                })
        
        # Report problematic rules
        if problematic_rules:
            print(f"[PROBLEM] Found {len(problematic_rules)} rules with column name issues:")
            print()
            for i, rule in enumerate(problematic_rules, 1):
                print(f"{i}. Rule ID: {rule['rule_id']}")
                print(f"   Node ID: {rule['node_id']}")
                print(f"   Rule Type: {rule['rule_type']}")
                print(f"   Measure: {rule['measure_name']}")
                print(f"   Logic: {rule['logic_en'] or 'N/A'}")
                print(f"   SQL WHERE: {rule['sql_where']}")
                print(f"   Issues:")
                for issue in rule['issues']:
                    print(f"      - {issue}")
                print()
        else:
            print("[OK] No problematic rules found")
        
        # Report correct rules
        if correct_rules:
            print(f"[OK] Found {len(correct_rules)} rules with correct column names:")
            for rule in correct_rules[:5]:  # Show first 5
                print(f"   Rule {rule['rule_id']} (node {rule['node_id']}): {rule['sql_where'][:60]}...")
            if len(correct_rules) > 5:
                print(f"   ... and {len(correct_rules) - 5} more")
            print()
        
        # Summary and recommendations
        print("=" * 80)
        print("SUMMARY & RECOMMENDATIONS")
        print("=" * 80)
        print()
        
        if problematic_rules:
            print(f"Found {len(problematic_rules)} rule(s) that need to be fixed.")
            print()
            print("Column Name Mapping for fact_pnl_use_case_3:")
            print("  OLD (fact_pnl_gold)     ->  NEW (fact_pnl_use_case_3)")
            print("  strategy_id            ->  strategy")
            print("  book_id                ->  book")
            print("  cc_id                  ->  cost_center")
            print("  daily_pnl              ->  pnl_daily")
            print("  mtd_pnl                ->  (not available)")
            print("  ytd_pnl                ->  (not available)")
            print()
            print("SQL Commands to Fix Rules:")
            print()
            for rule in problematic_rules:
                # Generate fix SQL
                fixed_sql = rule['sql_where']
                fixed_sql = fixed_sql.replace('strategy_id', 'strategy')
                fixed_sql = fixed_sql.replace('STRATEGY_ID', 'strategy')
                fixed_sql = fixed_sql.replace('book_id', 'book')
                fixed_sql = fixed_sql.replace('BOOK_ID', 'book')
                fixed_sql = fixed_sql.replace('cc_id', 'cost_center')
                fixed_sql = fixed_sql.replace('CC_ID', 'cost_center')
                
                if fixed_sql != rule['sql_where']:
                    print(f"-- Fix Rule {rule['rule_id']} (node {rule['node_id']}):")
                    print(f"UPDATE metadata_rules")
                    print(f"SET sql_where = {repr(fixed_sql)}")
                    print(f"WHERE rule_id = {rule['rule_id']};")
                    print()
        else:
            print("[OK] All rules appear to have correct column names")
            print("The error might be coming from a different source.")

if __name__ == "__main__":
    main()

