"""
Verify that the Math rule data exists in the database
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine

def main():
    print("=" * 80)
    print("VERIFYING MATH RULE DATA IN DATABASE")
    print("=" * 80)
    print()
    
    uc3_id = 'fce60983-0328-496b-b6e1-34249ec5aa5a'
    
    with engine.connect() as conn:
        # Query for Math rule (NODE_4)
        result = conn.execute(text("""
            SELECT 
                rule_id,
                node_id,
                rule_type,
                rule_expression,
                rule_dependencies,
                logic_en,
                sql_where
            FROM metadata_rules
            WHERE use_case_id = :uc_id
            AND node_id = 'NODE_4'
        """), {"uc_id": uc3_id})
        
        rows = result.fetchall()
        
        if not rows:
            print("[ERROR] No rule found for NODE_4")
            return
        
        print(f"[OK] Found {len(rows)} rule(s) for NODE_4")
        print()
        
        for row in rows:
            print(f"Rule ID: {row[0]}")
            print(f"Node ID: {row[1]}")
            print(f"Rule Type: {row[2]}")
            print(f"Rule Expression: {row[3]}")
            print(f"Rule Dependencies: {row[4]}")
            print(f"Logic EN: {row[5]}")
            print(f"SQL Where: {row[6]}")
            print()
            
            # Check if Row object supports _mapping
            print("Row object attributes:")
            print(f"  Type: {type(row)}")
            print(f"  Has _mapping: {hasattr(row, '_mapping')}")
            print(f"  Has _asdict: {hasattr(row, '_asdict')}")
            
            if hasattr(row, '_mapping'):
                print(f"  _mapping type: {type(row._mapping)}")
                print(f"  _mapping keys: {list(row._mapping.keys())}")
                print(f"  _mapping['rule_type']: {row._mapping.get('rule_type')}")
                print(f"  _mapping['rule_expression']: {row._mapping.get('rule_expression')}")
            
            # Try attribute access
            try:
                print(f"  row.rule_type (attribute): {row.rule_type}")
                print(f"  row.rule_expression (attribute): {row.rule_expression}")
            except Exception as e:
                print(f"  Attribute access failed: {e}")

if __name__ == "__main__":
    main()

