"""
Analyze why the business rule is using pnl_daily instead of pnl_commission.
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
    print("ANALYZING MEASURE NAME ISSUE")
    print("=" * 80)
    print()
    
    uc3_id = 'fce60983-0328-496b-b6e1-34249ec5aa5a'
    node_id = 'NODE_5'  # Commissions (Non Swap)
    
    with engine.connect() as conn:
        # Step 1: Check the rule's measure_name
        print("Step 1: Checking rule configuration for NODE_5")
        print("-" * 80)
        result = conn.execute(text("""
            SELECT 
                rule_id,
                node_id,
                measure_name,
                rule_type,
                sql_where,
                logic_en
            FROM metadata_rules
            WHERE use_case_id = :uc_id
            AND node_id = :node_id
        """), {"uc_id": uc3_id, "node_id": node_id})
        
        rows = result.fetchall()
        if not rows:
            print("   [ERROR] No rule found for NODE_5")
            return
        
        for row in rows:
            print(f"   Rule ID: {row[0]}")
            print(f"   Node ID: {row[1]}")
            print(f"   Measure Name: '{row[2]}'")
            print(f"   Rule Type: '{row[3]}'")
            print(f"   SQL WHERE: '{row[4]}'")
            print(f"   Logic EN: '{row[5]}'")
            print()
        
        # Step 2: Check actual data values
        print("Step 2: Checking actual data values in fact_pnl_use_case_3")
        print("-" * 80)
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as row_count,
                SUM(pnl_daily) as total_daily_pnl,
                SUM(pnl_commission) as total_commission_pnl,
                SUM(pnl_trade) as total_trade_pnl
            FROM fact_pnl_use_case_3
            WHERE strategy = 'Commissions (Non Swap)'
        """))
        row = result.fetchone()
        print(f"   Rows matching strategy = 'Commissions (Non Swap)': {row[0]}")
        print(f"   SUM(pnl_daily): {row[1]}")
        print(f"   SUM(pnl_commission): {row[2]}")
        print(f"   SUM(pnl_trade): {row[3]}")
        print()
        
        # Step 3: Root Cause Analysis
        print("=" * 80)
        print("ROOT CAUSE ANALYSIS")
        print("=" * 80)
        print()
        print("Issue in apply_rule_to_leaf (app/services/calculator.py):")
        print("   Line 99: target_column = get_measure_column_name(measure_name, table_name)")
        print("   - This correctly maps 'daily_commission' -> 'pnl_commission'")
        print()
        print("   Line 110: BUT the SQL query HARDCODES 'pnl_daily':")
        print("   - SELECT COALESCE(SUM(pnl_daily), 0) as daily_pnl")
        print("   - The target_column variable is IGNORED!")
        print()
        print("   There's even a TODO comment:")
        print("   - 'For now, we only support daily measure (pnl_daily)'")
        print("   - 'TODO: Support multiple measures (pnl_commission, pnl_trade) in future'")
        print()
        print("=" * 80)
        print("RECOMMENDED FIX")
        print("=" * 80)
        print()
        print("Update the SQL query to use target_column instead of hardcoding pnl_daily:")
        print()
        print("   OLD (WRONG):")
        print("   sql_query = f\"\"\"")
        print("       SELECT COALESCE(SUM(pnl_daily), 0) as daily_pnl,")
        print("   \"\"\"")
        print()
        print("   NEW (CORRECT):")
        print("   sql_query = f\"\"\"")
        print("       SELECT COALESCE(SUM({target_column}), 0) as daily_pnl,")
        print("   \"\"\"")
        print()
        print("Also need to map the result to the correct measure key:")
        print("   - If measure_name = 'daily_commission', result should go to 'mtd'")
        print("   - If measure_name = 'daily_trade', result should go to 'ytd'")
        print("   - If measure_name = 'daily_pnl', result should go to 'daily'")
        print()

if __name__ == "__main__":
    main()

