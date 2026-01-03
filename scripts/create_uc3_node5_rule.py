"""
Create a new business rule for Use Case 3, Node NODE_5 (Commissions)
Rule: Filter for 'CORE' strategies using the correct column name 'strategy'
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
    print("CREATING BUSINESS RULE FOR USE CASE 3 - NODE_5 (COMMISSIONS)")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        # Step 1: Get Use Case 3 ID
        print("Step 1: Fetching Use Case ID for 'America Cash Equity Trading'...")
        result = conn.execute(text("""
            SELECT use_case_id, name
            FROM use_cases
            WHERE name ILIKE '%america%cash%equity%'
        """))
        
        uc3_row = result.fetchone()
        if not uc3_row:
            print("[ERROR] Use Case 'America Cash Equity Trading' not found!")
            return 1
        
        uc3_id, uc3_name = uc3_row
        print(f"[OK] Found Use Case:")
        print(f"   ID: {uc3_id}")
        print(f"   Name: {uc3_name}")
        print()
        
        # Step 2: Verify NODE_5 exists in the hierarchy
        print("Step 2: Verifying NODE_5 exists in hierarchy...")
        result = conn.execute(text("""
            SELECT node_id, node_name
            FROM dim_hierarchy
            WHERE node_id = 'NODE_5'
        """))
        
        node5 = result.fetchone()
        if not node5:
            print("[WARNING] NODE_5 not found in dim_hierarchy")
            print("   The rule will still be created, but it may not work if the node doesn't exist")
        else:
            node_id, node_name = node5
            print(f"[OK] Found node:")
            print(f"   Node ID: {node_id}")
            print(f"   Node Name: {node_name}")
            print()
        
        # Step 3: Check if a rule already exists for NODE_5 in Use Case 3
        print("Step 3: Checking for existing rule...")
        result = conn.execute(text("""
            SELECT rule_id, sql_where, measure_name
            FROM metadata_rules
            WHERE use_case_id = :uc3_id
              AND node_id = 'NODE_5'
        """), {"uc3_id": str(uc3_id)})
        
        existing_rule = result.fetchone()
        if existing_rule:
            print(f"[WARNING] Rule already exists for NODE_5:")
            print(f"   Rule ID: {existing_rule[0]}")
            print(f"   Current sql_where: {existing_rule[1] or '(empty)'}")
            print(f"   Current measure_name: {existing_rule[2] or '(empty)'}")
            print()
            print("Would you like to update the existing rule instead?")
            print("(Skipping insert - rule already exists)")
            return 0
        
        print("[OK] No existing rule found - proceeding with insert")
        print()
        
        # Step 4: Prepare the INSERT statement
        print("Step 4: Preparing INSERT statement...")
        print()
        print("Rule Details:")
        print(f"   use_case_id: {uc3_id}")
        print(f"   node_id: 'NODE_5'")
        print(f"   rule_type: 'FILTER'")
        print(f"   sql_where: \"strategy = 'CORE'\"")
        print(f"   measure_name: 'pnl_commission'")
        print(f"   logic_en: \"strategy equals 'CORE'\"")
        print(f"   last_modified_by: 'system'")
        print()
        
        # Step 5: Execute INSERT
        print("Step 5: Executing INSERT...")
        try:
            result = conn.execute(text("""
                INSERT INTO metadata_rules (
                    use_case_id,
                    node_id,
                    rule_type,
                    sql_where,
                    measure_name,
                    logic_en,
                    last_modified_by
                ) VALUES (
                    :use_case_id,
                    'NODE_5',
                    'FILTER',
                    'strategy = ''CORE''',
                    'pnl_commission',
                    'strategy equals ''CORE''',
                    'system'
                )
                RETURNING rule_id, sql_where, measure_name, logic_en
            """), {
                "use_case_id": str(uc3_id)
            })
            
            new_rule = result.fetchone()
            conn.commit()
            
            if new_rule:
                rule_id, sql_where, measure_name, logic_en = new_rule
                print(f"[SUCCESS] Rule created successfully!")
                print()
                print("Created Rule Details:")
                print(f"   Rule ID: {rule_id}")
                print(f"   Use Case ID: {uc3_id}")
                print(f"   Node ID: NODE_5")
                print(f"   Rule Type: FILTER")
                print(f"   sql_where: {sql_where}")
                print(f"   measure_name: {measure_name}")
                print(f"   logic_en: {logic_en}")
                print()
                
                # Verification: Check column name
                if 'strategy_id' in sql_where.lower():
                    print("[ERROR] Rule contains 'strategy_id' instead of 'strategy'!")
                    print("   This is incorrect for fact_pnl_use_case_3 table")
                    return 1
                elif 'strategy' in sql_where.lower() and 'strategy_id' not in sql_where.lower():
                    print("[VERIFIED] Rule uses correct column name 'strategy'")
                    print("   This matches the fact_pnl_use_case_3 table schema")
                else:
                    print("[WARNING] Could not verify column name correctness")
                
                print()
                print("=" * 80)
                print("RULE CREATION COMPLETE")
                print("=" * 80)
                print()
                print("SQL Command Used:")
                print("""
INSERT INTO metadata_rules (
    use_case_id,
    node_id,
    rule_type,
    sql_where,
    measure_name,
    logic_en,
    last_modified_by
) VALUES (
    :use_case_id,
    'NODE_5',
    'FILTER',
    'strategy = ''CORE''',
    'pnl_commission',
    'strategy equals ''CORE''',
    'system'
)
                """.strip())
                
                return 0
            else:
                print("[ERROR] INSERT executed but no row returned")
                return 1
                
        except Exception as e:
            conn.rollback()
            print(f"[ERROR] INSERT failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

if __name__ == "__main__":
    exit(main())

