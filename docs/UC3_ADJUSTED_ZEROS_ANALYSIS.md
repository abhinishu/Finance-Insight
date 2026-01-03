# Root Cause Analysis: Adjusted P&L = 0 for Certain Nodes

## Executive Summary

**Problem:** After fixing the zero results bug, we now see:
1. **Commission (Non Swap)**: Adjusted P&L = 0 (has rule: `strategy = 'CORE'`)
2. **CRB, ETF Amber, MSET**: Adjusted P&L = 0 (no rules, should = Original)

**Root Causes Identified:**
1. **Commission (Non Swap) Rule**: Looking for `strategy = 'CORE'` but **no such strategy exists** in database
2. **CRB, ETF Amber, MSET**: These nodes have **no rules**, so Adjusted should = Original, but it's 0

---

## Investigation Findings

### ✅ Data Availability

**Strategies in `fact_pnl_use_case_3`:**
- `CRB`: 41 rows, Daily = 15,000.04 ✅
- `ETF Amber`: 38 rows, Daily = 346,858.60 ✅
- `MSET`: 50 rows, Daily = 618,774.86 ✅
- `Commissions (Non Swap)`: 378 rows, Daily = 19,999.79 ✅
- **NO strategy called `'CORE'` exists** ❌

**Strategies containing "core" or "commission":**
- `Commissions`
- `Commissions (Non Swap)`
- `Core Ex CRB`
- `Swap Commission`

### ❌ Root Cause #1: Commission (Non Swap) Rule

**Rule 70:**
- Node: `NODE_5` ('Commissions (Non Swap)')
- Type: `FILTER`
- SQL WHERE: `strategy = 'CORE'`
- Measure: `pnl_commission`

**Problem:**
- The rule queries: `SELECT SUM(pnl_commission) FROM fact_pnl_use_case_3 WHERE strategy = 'CORE'`
- **Result: 0** (no rows match because `'CORE'` strategy doesn't exist)
- The actual strategy name is `'Commissions (Non Swap)'` (378 rows with data)

**Expected Behavior:**
- Rule should probably be: `strategy = 'Commissions (Non Swap)'`
- OR the rule should filter for a different condition that matches the intended data

**Current State:**
- Original Daily P&L: 19,999.79 ✅ (from natural rollup)
- Adjusted Daily P&L: 0.00 ❌ (rule returns 0)
- Reconciliation Plug: 19,999.79 ✅ (Original - Adjusted)

### ❌ Root Cause #2: CRB, ETF Amber, MSET Adjusted = 0

**Nodes:**
- `CRB` (NODE_10): Original = 15,000.04, Adjusted = 0.00, **No rule**
- `ETF Amber` (NODE_11): Original = 346,858.60, Adjusted = 0.00, **No rule**
- `MSET` (NODE_12): Original = 618,774.86, Adjusted = 0.00, **No rule**

**Expected Behavior:**
- For nodes **without rules**, Adjusted P&L should = Original P&L
- Plug should = 0 (Original - Original)

**Actual Behavior:**
- Adjusted P&L = 0.00 ❌
- Plug = Original (Original - 0)

**Hypothesis:**
The `adjusted_results` dictionary is not being properly initialized from `natural_results` for nodes without rules.

**Code Location:**
`app/services/calculator.py` line ~368:
```python
adjusted_results = natural_results.copy()
```

This should work, but something might be overwriting it later, OR the natural_results might not contain these nodes.

---

## Analysis of Calculation Flow

### Expected Flow (for nodes WITHOUT rules):

1. **Natural Rollup** (`_calculate_strategy_rollup`):
   - Matches `fact.strategy` to `node.node_name`
   - For `CRB`: Matches strategy `'CRB'` → Returns 15,000.04 ✅
   - For `ETF Amber`: Matches strategy `'ETF Amber'` → Returns 346,858.60 ✅
   - For `MSET`: Matches strategy `'MSET'` → Returns 618,774.86 ✅

2. **Initialize Adjusted**:
   ```python
   adjusted_results = natural_results.copy()
   ```
   - Should copy all natural values to adjusted ✅

3. **Apply Rules** (none for these nodes):
   - No rules to apply, so adjusted should remain = natural ✅

4. **Waterfall Up**:
   - Aggregates parent nodes from children
   - Should preserve leaf node values ✅

5. **Save Results**:
   - Should save adjusted = natural for nodes without rules ✅

### Actual Flow (What's Happening):

**Hypothesis 1: Natural Rollup Not Populating These Nodes**
- `_calculate_strategy_rollup` might not be matching these nodes correctly
- OR the matching logic has a bug

**Hypothesis 2: Adjusted Results Being Overwritten**
- Something in the calculation flow is setting adjusted_results[node_id] = 0
- OR the results are being saved incorrectly

**Hypothesis 3: Results Not Being Saved Correctly**
- The save logic might be defaulting to 0 for missing values
- OR the measure_vector is not being populated correctly

---

## Next Steps for Investigation

### 1. Verify Natural Rollup Results

Check if `_calculate_strategy_rollup` is actually returning values for CRB, ETF Amber, MSET:

```python
# In _calculate_strategy_rollup, check:
# - Does it match 'CRB' strategy to 'CRB' node?
# - Does it return the correct sum?
# - Is the result being stored in natural_results?
```

### 2. Verify Adjusted Results Initialization

Check if `adjusted_results = natural_results.copy()` is working:

```python
# After initialization, check:
# - Does adjusted_results['NODE_10'] exist?
# - Does it equal natural_results['NODE_10']?
```

### 3. Check Waterfall Up Logic

Verify that `waterfall_up` is not overwriting leaf node values:

```python
# In waterfall_up, check:
# - Does it preserve leaf node values?
# - Or does it overwrite them with parent aggregation?
```

### 4. Check Save Logic

Verify that `save_calculation_results` is using the correct values:

```python
# In save_calculation_results, check:
# - Is it reading from adjusted_results correctly?
# - Is it defaulting to 0 for missing keys?
```

---

## Recommended Fixes

### Fix #1: Commission (Non Swap) Rule

**Option A:** Update the rule to use the correct strategy name:
```sql
UPDATE metadata_rules
SET sql_where = 'strategy = ''Commissions (Non Swap)'''
WHERE rule_id = 70;
```

**Option B:** If the intent is to filter for "Core" products, check what the actual strategy name should be:
- Is it `'Core Ex CRB'`?
- Or should the rule be different?

### Fix #2: CRB, ETF Amber, MSET Adjusted = 0

**Investigation Required:**
1. Add logging to `_calculate_strategy_rollup` to see what it returns
2. Add logging to `calculate_use_case` to see natural_results vs adjusted_results
3. Check if `waterfall_up` is overwriting leaf values
4. Check if `save_calculation_results` is using correct values

**Potential Fix:**
- Ensure `adjusted_results = natural_results.copy()` happens AFTER natural rollup
- Ensure `waterfall_up` doesn't overwrite leaf node values
- Ensure `save_calculation_results` uses adjusted_results, not natural_results

---

## Critical Discovery: CRB, ETF Amber, MSET Are NOT Leaf Nodes

**From Investigation:**
- `NODE_10` ('CRB'): `leaf=False, depth=2` - **Has children**
- `NODE_11` ('ETF Amber'): `leaf=False, depth=2` - **Has children**
- `NODE_12` ('MSET'): `leaf=False, depth=2` - **Has children**

**Implication:**
These nodes are **parent nodes**, not leaf nodes. The `waterfall_up` function aggregates parent nodes from their children:

```python
# waterfall_up logic (line 189-206):
adjusted_results[node_id] = {
    'daily': sum(adjusted_results.get(child_id, {}).get('daily', Decimal('0')) for child_id in children),
    ...
}
```

**Root Cause Hypothesis:**
1. Natural rollup matches `strategy = 'CRB'` to node `'CRB'` and returns 15,000.04 ✅
2. `adjusted_results = natural_results.copy()` copies this value ✅
3. **BUT** `waterfall_up` overwrites parent nodes by summing their children
4. If the children have `adjusted_results[child_id] = 0` (not in natural_results or not copied correctly), the parent becomes 0 ❌

**The Real Question:**
- Do the children of CRB, ETF Amber, MSET have values in `natural_results`?
- Are those children being copied to `adjusted_results`?
- Or are the children missing from `natural_results`, causing the parent to be 0?

---

## Summary

| Node | Original | Adjusted | Rule | Node Type | Issue |
|------|----------|----------|------|-----------|-------|
| **Commission (Non Swap)** | 19,999.79 | 0.00 | ✅ Yes | Leaf | Rule queries `strategy = 'CORE'` but no such strategy exists |
| **CRB** | 15,000.04 | 0.00 | ❌ No | **Parent** | `waterfall_up` overwrites from children (children may be 0) |
| **ETF Amber** | 346,858.60 | 0.00 | ❌ No | **Parent** | `waterfall_up` overwrites from children (children may be 0) |
| **MSET** | 618,774.86 | 0.00 | ❌ No | **Parent** | `waterfall_up` overwrites from children (children may be 0) |

**Next Action:** 
1. Check if children of CRB, ETF Amber, MSET have values in `natural_results`
2. Verify if `_calculate_strategy_rollup` is populating children correctly
3. Check if `waterfall_up` should preserve direct matches for parent nodes

