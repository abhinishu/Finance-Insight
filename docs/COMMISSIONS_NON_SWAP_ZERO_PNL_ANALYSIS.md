# Commissions (Non Swap) Zero P&L Root Cause Analysis

## 🔍 Issue Summary

After updating 378 rows in `fact_pnl_use_case_3` from `strategy = 'Commissions (Non Swap)'` to `strategy = 'CORE'`, the "Commissions (Non Swap)" node in Tab 3 now shows **0.00** for Original P&L.

## 📊 Current Data State

### Strategy Distribution in fact_pnl_use_case_3:
- **'CORE'**: 378 rows, Total Daily P&L: **19,999.79** ✅ (This is the data we moved!)
- **'Commissions (Non Swap)'**: 0 rows ❌ (All rows were updated)
- **'Commissions'**: 1 row, Total Daily P&L: 40,769.00
- Other strategies: Core Ex CRB, CRB, ETF Amber, MSET, etc.

### Hierarchy Node:
- **Node ID**: NODE_5
- **Node Name**: 'Commissions (Non Swap)'
- **Is Leaf**: True
- **Parent**: NODE_4 (Commissions)

## 🔎 Root Cause

### Matching Logic (from `_calculate_strategy_rollup`):

**Location:** `app/services/unified_pnl_service.py` lines 429-434

```python
# Match by strategy first (fact.strategy == node.node_name)
if 'strategy' in facts_df.columns:
    # Case-insensitive matching: fact.strategy == node.node_name
    strategy_match = facts_df[facts_df['strategy'].str.upper() == node_name.upper()]
    if len(strategy_match) > 0:
        matched_facts = strategy_match
```

**The Problem:**
1. The system matches `fact.strategy` to `node.node_name` (case-insensitive)
2. For "Commissions (Non Swap)" node, it looks for rows where `strategy = 'Commissions (Non Swap)'`
3. We updated all 378 rows from `'Commissions (Non Swap)'` to `'CORE'`
4. Now 0 rows match, resulting in **0.00 P&L**

**Evidence:**
- Before update: 378 rows with `strategy = 'Commissions (Non Swap)'` → P&L = 19,999.79
- After update: 0 rows with `strategy = 'Commissions (Non Swap)'` → P&L = 0.00
- The data exists but is now under `strategy = 'CORE'` (378 rows, 19,999.79)

## 💡 Fix Options

### Option 1: Revert the Strategy Update ⭐ (Immediate Fix)

**Action:** Change the 378 rows back from `'CORE'` to `'Commissions (Non Swap)'`

**SQL:**
```sql
UPDATE fact_pnl_use_case_3
SET strategy = 'Commissions (Non Swap)'
WHERE strategy = 'CORE'
AND [add additional filter to identify the 378 specific rows]
```

**Pros:**
- ✅ Restores original matching behavior immediately
- ✅ No code changes needed
- ✅ Original P&L will show correctly

**Cons:**
- ⚠️ Reverses the data alignment test
- ⚠️ Need to identify which 378 rows to revert (if other 'CORE' rows exist)

**When to Use:** If the data update was a mistake or test that should be reverted.

---

### Option 2: Update Hierarchy Node Name (If Intentional)

**Action:** Change the hierarchy node name from `'Commissions (Non Swap)'` to `'CORE'`

**SQL:**
```sql
UPDATE dim_hierarchy
SET node_name = 'CORE'
WHERE node_id = 'NODE_5'
AND atlas_source = (SELECT atlas_structure_id FROM use_cases WHERE use_case_id = 'fce60983-0328-496b-b6e1-34249ec5aa5a')
```

**Pros:**
- ✅ Aligns hierarchy with new data structure
- ✅ No fact table changes needed
- ✅ Matching will work correctly

**Cons:**
- ⚠️ Changes the node name permanently
- ⚠️ May break existing business rules that reference 'Commissions (Non Swap)'
- ⚠️ UI will show 'CORE' instead of 'Commissions (Non Swap)'

**When to Use:** If the data change was intentional and the hierarchy should reflect the new structure.

---

### Option 3: Use Business Rule (Recommended for Testing) ⭐⭐⭐

**Action:** Keep `strategy = 'CORE'` in fact table, create a business rule for the node

**Steps:**
1. Keep the 378 rows as `strategy = 'CORE'`
2. Create a business rule for NODE_5 ("Commissions (Non Swap)"):
   - **Rule Type**: FILTER (Type 1)
   - **SQL WHERE**: `strategy = 'CORE'` (or more specific filter if needed)
   - **Measure**: `pnl_daily` (or `pnl_commission` if using commission measure)

**Pros:**
- ✅ Allows testing data alignment without breaking hierarchy matching
- ✅ Original P&L will show via the business rule
- ✅ Flexible - can add additional filters if needed
- ✅ Doesn't require reverting data or changing hierarchy

**Cons:**
- ⚠️ Requires creating a business rule
- ⚠️ The rule will show in the "Business Rule" column

**When to Use:** If you want to test data alignment while keeping the hierarchy structure intact.

---

## 🎯 Recommended Solution

**For Testing Data Alignment:** **Option 3 (Business Rule)**

This allows you to:
1. Keep the `strategy = 'CORE'` update for testing
2. Restore the P&L display for "Commissions (Non Swap)" node
3. Test the data alignment without breaking the hierarchy matching

**For Production Fix:** **Option 1 (Revert Update)**

If the update was unintended, revert it to restore the original behavior.

---

## 📝 Implementation Notes

### If Using Option 3 (Business Rule):

The rule should be created for:
- **Use Case**: America Cash Equity Trading (fce60983-0328-496b-b6e1-34249ec5aa5a)
- **Node**: NODE_5 (Commissions (Non Swap))
- **Rule Type**: FILTER
- **SQL WHERE**: `strategy = 'CORE'`
- **Measure**: `pnl_daily` (or appropriate measure)

This will ensure the node shows the 19,999.79 P&L from the 378 'CORE' rows.

---

## 🔍 Verification Queries

After applying any fix, verify with:

```sql
-- Check strategy distribution
SELECT strategy, COUNT(*), SUM(pnl_daily) 
FROM fact_pnl_use_case_3 
GROUP BY strategy 
ORDER BY strategy;

-- Check hierarchy node
SELECT node_id, node_name 
FROM dim_hierarchy 
WHERE node_id = 'NODE_5';

-- Check if business rule exists (if using Option 3)
SELECT rule_id, node_id, sql_where, rule_type
FROM metadata_rules
WHERE node_id = 'NODE_5'
AND use_case_id = 'fce60983-0328-496b-b6e1-34249ec5aa5a';
```

