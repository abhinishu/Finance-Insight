"""
Analyze why Tab 3 shows 0 for Commissions (Non Swap) while Tab 4 shows 19,999.79
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine

def main():
    print("=" * 80)
    print("ANALYZING TAB 3 vs TAB 4 DATA DISCREPANCY")
    print("=" * 80)
    print()
    print("Issue: Tab 3 shows Daily P&L = 0 for Commissions (Non Swap)")
    print("       Tab 4 shows Original Daily P&L = 19,999.79")
    print()
    
    with engine.connect() as conn:
        uc3_id = 'fce60983-0328-496b-b6e1-34249ec5aa5a'
        
        # Step 1: Check what the results endpoint returns
        print("Step 1: Checking latest calculation results...")
        result = conn.execute(text("""
            SELECT 
                fcr.node_id,
                h.node_name,
                fcr.measure_vector->>'daily' as adjusted_daily,
                fcr.plug_vector->>'daily' as plug_daily,
                fcr.is_override,
                ucr.run_timestamp
            FROM fact_calculated_results fcr
            JOIN use_case_runs ucr ON fcr.run_id = ucr.run_id
            JOIN dim_hierarchy h ON fcr.node_id = h.node_id
            WHERE ucr.use_case_id = :uc3_id
              AND ucr.run_timestamp = (
                  SELECT MAX(run_timestamp)
                  FROM use_case_runs
                  WHERE use_case_id = :uc3_id
              )
              AND h.node_name = 'Commissions (Non Swap)'
        """), {"uc3_id": str(uc3_id)})
        
        calc_result = result.fetchone()
        if calc_result:
            node_id, node_name, adjusted_daily, plug_daily, is_override, run_timestamp = calc_result
            adjusted_daily = float(adjusted_daily) if adjusted_daily else 0.0
            plug_daily = float(plug_daily) if plug_daily else 0.0
            
            print(f"[CALCULATION RESULTS] {node_name} ({node_id}):")
            print(f"   Adjusted Daily P&L: {adjusted_daily:,.2f}")
            print(f"   Plug Daily: {plug_daily:,.2f}")
            print(f"   Has Rule (override): {is_override}")
            print(f"   Run Timestamp: {run_timestamp}")
            print()
            
            # Calculate natural from adjusted + plug
            natural_daily = adjusted_daily + plug_daily
            print(f"   Calculated Natural (Adjusted + Plug): {natural_daily:,.2f}")
            print()
        else:
            print("[INFO] No calculation results found for Commissions (Non Swap)")
            print()
        
        # Step 2: Check what natural rollup would return
        print("Step 2: Checking what natural rollup returns...")
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as row_count,
                SUM(pnl_daily) as total_daily,
                SUM(pnl_commission) as total_commission,
                SUM(pnl_trade) as total_trade
            FROM fact_pnl_use_case_3
            WHERE strategy = 'Commissions (Non Swap)'
        """))
        
        natural_data = result.fetchone()
        if natural_data:
            row_count, total_daily, total_commission, total_trade = natural_data
            total_daily = total_daily or 0
            print(f"[NATURAL ROLLUP] Strategy 'Commissions (Non Swap)':")
            print(f"   Rows: {row_count}")
            print(f"   Total Daily P&L: {total_daily:,.2f}")
            print(f"   Total Commission: {total_commission or 0:,.2f}")
            print(f"   Total Trade: {total_trade or 0:,.2f}")
            print()
        
        # Step 3: Analyze the issue
        print("Step 3: Root Cause Analysis...")
        print()
        print("[TAB 3 LOGIC]")
        print("   Tab 3 uses: adjusted_value?.daily || natural_value?.daily || '0'")
        print("   Problem: When adjusted_value.daily = 0, it becomes string '0'")
        print("   String '0' is truthy in JavaScript, so fallback never happens!")
        print()
        print("[TAB 4 LOGIC]")
        print("   Tab 4 uses: natural_value.daily (Original Daily P&L)")
        print("   This shows the correct value: 19,999.79")
        print()
        print("[THE BUG]")
        print("   Line 920 in RuleEditor.tsx:")
        print("   daily_pnl: node.adjusted_value?.daily?.toString() || node.natural_value?.daily?.toString() || '0'")
        print()
        print("   When adjusted_value.daily = 0:")
        print("   - adjusted_value?.daily?.toString() = '0' (truthy)")
        print("   - Fallback to natural_value never executes")
        print("   - Result: daily_pnl = '0' ❌")
        print()
        print("   Should be:")
        print("   - Check if adjusted_value exists AND is meaningful")
        print("   - OR always use natural_value for Tab 3 (since it shows 'Original' values)")
        print()
        
        # Step 4: Check what the API actually returns
        print("Step 4: What the API returns...")
        if calc_result:
            print(f"   API returns for Commissions (Non Swap):")
            print(f"   - adjusted_value.daily: {adjusted_daily:,.2f} (from calculation)")
            print(f"   - natural_value.daily: {natural_daily:,.2f} (calculated: adjusted + plug)")
            print()
            print(f"   Tab 3 uses: adjusted_value ({adjusted_daily:,.2f}) = 0 ❌")
            print(f"   Tab 4 uses: natural_value ({natural_daily:,.2f}) = 19,999.79 ✅")
        print()
        
        # Step 5: Recommendation
        print("=" * 80)
        print("RECOMMENDATION")
        print("=" * 80)
        print()
        print("Tab 3 should show NATURAL values (Original P&L), not Adjusted values.")
        print()
        print("Fix Option 1: Always use natural_value for Tab 3")
        print("   daily_pnl: node.natural_value?.daily?.toString() || '0'")
        print()
        print("Fix Option 2: Check if adjusted is meaningful before using it")
        print("   const adjusted = parseFloat(node.adjusted_value?.daily || '0')")
        print("   const natural = parseFloat(node.natural_value?.daily || '0')")
        print("   daily_pnl: (adjusted > 0 ? adjusted : natural).toString()")
        print()
        print("Fix Option 3: Use natural_value when adjusted is zero")
        print("   const adjusted = node.adjusted_value?.daily")
        print("   const natural = node.natural_value?.daily")
        print("   daily_pnl: (adjusted && parseFloat(adjusted) !== 0 ? adjusted : natural)?.toString() || '0'")
        print()
        
        return 0

if __name__ == "__main__":
    exit(main())

