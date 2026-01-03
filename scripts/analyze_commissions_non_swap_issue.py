"""
Analyze why "Commissions (Non Swap)" node shows 0.00 P&L after strategy update.
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
    print("ANALYZING COMMISSIONS (NON SWAP) ZERO P&L ISSUE")
    print("=" * 80)
    print()
    
    uc3_id = 'fce60983-0328-496b-b6e1-34249ec5aa5a'
    
    with engine.connect() as conn:
        # Step 1: Check current strategy values in fact table
        print("Step 1: Current strategy distribution in fact_pnl_use_case_3")
        print("-" * 80)
        result = conn.execute(text("""
            SELECT strategy, COUNT(*) as row_count, SUM(pnl_daily) as total_daily_pnl
            FROM fact_pnl_use_case_3
            GROUP BY strategy
            ORDER BY strategy
        """))
        rows = result.fetchall()
        for row in rows:
            print(f"   Strategy: '{row[0]}' | Rows: {row[1]} | Total Daily P&L: {row[2]}")
        print()
        
        # Step 2: Check if 'Commissions (Non Swap)' strategy still exists
        print("Step 2: Checking for 'Commissions (Non Swap)' strategy")
        print("-" * 80)
        result = conn.execute(text("""
            SELECT COUNT(*) as count, SUM(pnl_daily) as total_pnl
            FROM fact_pnl_use_case_3
            WHERE strategy = 'Commissions (Non Swap)'
        """))
        row = result.fetchone()
        count = row[0] if row else 0
        total_pnl = row[1] if row else 0
        print(f"   Rows with strategy = 'Commissions (Non Swap)': {count}")
        print(f"   Total P&L for 'Commissions (Non Swap)': {total_pnl}")
        print()
        
        # Step 3: Check hierarchy node name for NODE_5
        print("Step 3: Checking hierarchy node name for 'Commissions (Non Swap)'")
        print("-" * 80)
        result = conn.execute(text("""
            SELECT node_id, node_name, is_leaf, parent_node_id
            FROM dim_hierarchy
            WHERE node_name = 'Commissions (Non Swap)'
            AND atlas_source = (
                SELECT atlas_structure_id 
                FROM use_cases 
                WHERE use_case_id = :uc_id
            )
        """), {"uc_id": uc3_id})
        rows = result.fetchall()
        if rows:
            for row in rows:
                print(f"   Node ID: {row[0]}")
                print(f"   Node Name: '{row[1]}'")
                print(f"   Is Leaf: {row[2]}")
                print(f"   Parent Node ID: {row[3]}")
        else:
            print("   [WARNING] No hierarchy node found with name 'Commissions (Non Swap)'")
        print()
        
        # Step 4: Check what strategy values match the node name
        print("Step 4: Strategy values that could match 'Commissions (Non Swap)'")
        print("-" * 80)
        result = conn.execute(text("""
            SELECT DISTINCT strategy
            FROM fact_pnl_use_case_3
            WHERE UPPER(strategy) LIKE UPPER('%Commissions%')
            OR UPPER(strategy) LIKE UPPER('%Non Swap%')
            OR UPPER(strategy) LIKE UPPER('%NON SWAP%')
        """))
        rows = result.fetchall()
        if rows:
            for row in rows:
                print(f"   Found: '{row[0]}'")
        else:
            print("   [WARNING] No strategy values found matching 'Commissions' or 'Non Swap'")
        print()
        
        # Step 5: Check CORE strategy P&L
        print("Step 5: Current 'CORE' strategy P&L")
        print("-" * 80)
        result = conn.execute(text("""
            SELECT COUNT(*) as count, SUM(pnl_daily) as total_pnl
            FROM fact_pnl_use_case_3
            WHERE strategy = 'CORE'
        """))
        row = result.fetchone()
        core_count = row[0] if row else 0
        core_pnl = row[1] if row else 0
        print(f"   Rows with strategy = 'CORE': {core_count}")
        print(f"   Total P&L for 'CORE': {core_pnl}")
        print()
        
        # Step 6: Root Cause Analysis
        print("=" * 80)
        print("ROOT CAUSE ANALYSIS")
        print("=" * 80)
        print()
        print("Matching Logic (from _calculate_strategy_rollup):")
        print("   - Matches fact.strategy to node.node_name (case-insensitive)")
        print("   - For 'Commissions (Non Swap)' node, looks for strategy = 'Commissions (Non Swap)'")
        print()
        print("What Happened:")
        print(f"   1. We updated {count} rows from 'Commissions (Non Swap)' to 'CORE'")
        print(f"   2. Now 0 rows have strategy = 'Commissions (Non Swap)'")
        print(f"   3. The matching logic finds 0 rows, resulting in 0.00 P&L")
        print()
        print("Expected Behavior:")
        print("   - The 'Commissions (Non Swap)' node should match rows where strategy = 'Commissions (Non Swap)'")
        print("   - But we changed all those rows to 'CORE', breaking the match")
        print()
        print("=" * 80)
        print("RECOMMENDED FIX OPTIONS")
        print("=" * 80)
        print()
        print("Option 1: Revert the Strategy Update (Immediate Fix)")
        print("   - Change the 378 rows back from 'CORE' to 'Commissions (Non Swap)'")
        print("   - This restores the original matching behavior")
        print()
        print("Option 2: Update Hierarchy Node Name (If Intentional)")
        print("   - If the data change was intentional, update the hierarchy node name")
        print("   - Change 'Commissions (Non Swap)' node_name to 'CORE'")
        print("   - This aligns the hierarchy with the new data structure")
        print()
        print("Option 3: Use Business Rule Instead (Recommended for Testing)")
        print("   - Keep strategy = 'CORE' in fact table")
        print("   - Create a business rule for 'Commissions (Non Swap)' node")
        print("   - Rule: WHERE strategy = 'CORE' AND [additional filters if needed]")
        print("   - This allows testing data alignment without breaking hierarchy matching")
        print()

if __name__ == "__main__":
    main()

