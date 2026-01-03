"""
Investigate Use Case 3 table configuration
Check current input_table_name and find candidate tables
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text, inspect
from app.database import engine

def main():
    print("=" * 80)
    print("USE CASE 3 TABLE INVESTIGATION")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        # Task 1: Check current configuration
        print("TASK 1: Current Configuration")
        print("-" * 80)
        result = conn.execute(text("""
            SELECT 
                use_case_id,
                name,
                input_table_name,
                atlas_structure_id,
                status
            FROM use_cases
            WHERE name ILIKE '%america%cash%equity%'
               OR name ILIKE '%amer%equity%'
               OR name ILIKE '%cash%equity%'
            ORDER BY name
        """))
        
        rows = result.fetchall()
        if not rows:
            print("[ERROR] No use case found matching 'America Cash Equity Trading'")
            print("\nChecking all use cases...")
            result = conn.execute(text("SELECT use_case_id, name, input_table_name FROM use_cases"))
            all_rows = result.fetchall()
            print(f"\nFound {len(all_rows)} use cases:")
            for row in all_rows:
                print(f"  - {row[1]} (input_table: {row[2] or 'NULL'})")
        else:
            for row in rows:
                use_case_id, name, input_table_name, atlas_structure_id, status = row
                print(f"Use Case ID: {use_case_id}")
                print(f"Name: {name}")
                print(f"Current input_table_name: {input_table_name or 'NULL (defaults to fact_pnl_gold)'}")
                print(f"Atlas Structure ID: {atlas_structure_id}")
                print(f"Status: {status}")
                print()
        
        # Task 2: Find candidate tables
        print("\n" + "=" * 80)
        print("TASK 2: Finding Candidate Tables")
        print("-" * 80)
        
        # Search for tables with 'amer', 'equity', 'cash', 'use_case_3', or 'input' in name
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND (
                table_name ILIKE '%amer%'
                OR table_name ILIKE '%equity%'
                OR table_name ILIKE '%cash%'
                OR table_name ILIKE '%use_case_3%'
                OR table_name ILIKE '%input%'
                OR table_name ILIKE '%fact_pnl%'
              )
            ORDER BY table_name
        """))
        
        candidate_tables = result.fetchall()
        print(f"\nFound {len(candidate_tables)} candidate tables:")
        for row in candidate_tables:
            print(f"  - {row[0]}")
        
        # Task 3: Compare schemas of candidate tables
        print("\n" + "=" * 80)
        print("TASK 3: Schema Comparison")
        print("-" * 80)
        
        # Check fact_pnl_use_case_3 (expected table)
        print("\n1. Checking 'fact_pnl_use_case_3' (expected table):")
        try:
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'fact_pnl_use_case_3'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            if columns:
                print(f"   [OK] Table exists with {len(columns)} columns:")
                for col in columns:
                    print(f"      - {col[0]} ({col[1]}, nullable: {col[2]})")
                
                # Check for key columns
                col_names = [col[0] for col in columns]
                key_columns = ['daily_commission', 'strategy', 'pnl_daily', 'pnl_commission', 'pnl_trade']
                found_keys = [col for col in key_columns if col in col_names]
                if found_keys:
                    print(f"\n   [OK] Found key columns: {', '.join(found_keys)}")
                else:
                    print(f"\n   [WARN] Key columns not found: {', '.join(key_columns)}")
            else:
                print("   [ERROR] Table does not exist")
        except Exception as e:
            print(f"   [ERROR] Error checking table: {e}")
        
        # Check fact_pnl_gold (current default)
        print("\n2. Checking 'fact_pnl_gold' (current default):")
        try:
            result = conn.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'fact_pnl_gold'
                ORDER BY ordinal_position
                LIMIT 20
            """))
            columns = result.fetchall()
            if columns:
                print(f"   [OK] Table exists with columns (showing first 20):")
                col_names = [col[0] for col in columns]
                for col in columns[:10]:
                    print(f"      - {col[0]} ({col[1]})")
                if len(columns) > 10:
                    print(f"      ... and {len(columns) - 10} more")
                
                # Check for key columns
                key_columns = ['daily_commission', 'strategy']
                found_keys = [col for col in key_columns if col in col_names]
                if found_keys:
                    print(f"\n   [OK] Found key columns: {', '.join(found_keys)}")
                else:
                    print(f"\n   [WARN] Key columns NOT found: {', '.join(key_columns)}")
                    print(f"      (This suggests fact_pnl_gold is NOT the correct table)")
            else:
                print("   [ERROR] Table does not exist")
        except Exception as e:
            print(f"   [ERROR] Error checking table: {e}")
        
        # Check other candidate tables
        print("\n3. Checking other candidate tables:")
        for table_row in candidate_tables:
            table_name = table_row[0]
            if table_name in ['fact_pnl_use_case_3', 'fact_pnl_gold']:
                continue  # Already checked
            
            try:
                result = conn.execute(text(f"""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = '{table_name}'
                    ORDER BY ordinal_position
                    LIMIT 15
                """))
                columns = result.fetchall()
                if columns:
                    print(f"\n   Table: {table_name}")
                    print(f"   Columns ({len(columns)} total, showing first 15):")
                    for col in columns[:15]:
                        print(f"      - {col[0]} ({col[1]})")
            except Exception as e:
                print(f"   [ERROR] Error checking {table_name}: {e}")
        
        # Summary and recommendation
        print("\n" + "=" * 80)
        print("SUMMARY & RECOMMENDATION")
        print("-" * 80)
        
        if rows:
            use_case_id, name, input_table_name, _, _ = rows[0]
            print(f"\nUse Case: {name}")
            print(f"Current input_table_name: {input_table_name or 'NULL'}")
            
            if not input_table_name or input_table_name == 'fact_pnl_gold':
                print("\n[PROBLEM] Use Case 3 is configured to use fact_pnl_gold (or NULL)")
                print("   This is likely WRONG - it should use a dedicated input table")
                
                # Check if fact_pnl_use_case_3 exists
                result = conn.execute(text("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                      AND table_name = 'fact_pnl_use_case_3'
                """))
                exists = result.fetchone()[0] > 0
                
                if exists:
                    print("\n[SOLUTION] Update use_cases table to point to 'fact_pnl_use_case_3'")
                    print(f"\nSQL Command to fix:")
                    print(f"UPDATE use_cases")
                    print(f"SET input_table_name = 'fact_pnl_use_case_3'")
                    print(f"WHERE use_case_id = '{use_case_id}';")
                    print(f"\nOr by name:")
                    print(f"UPDATE use_cases")
                    print(f"SET input_table_name = 'fact_pnl_use_case_3'")
                    print(f"WHERE name ILIKE '%america%cash%equity%';")
                else:
                    print("\n[WARNING] fact_pnl_use_case_3 table does not exist!")
                    print("   You may need to create it or use a different table name")
            else:
                print(f"\n[OK] Use Case 3 is configured to use: {input_table_name}")
                print("   Verify this is the correct table by checking its schema above")

if __name__ == "__main__":
    main()

