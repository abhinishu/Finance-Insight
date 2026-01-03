# Reconciliation Plug Calculation Analysis

## Problem Statement

**Issue:** Top-level plug (CORE Products) shows **151,547.79** but should be **19,999.79** (same as child plugs).

**Expected Behavior:**
- Commissions (Non Swap): Plug = 19,999.79 ✅
- Commissions (parent): Plug = 19,999.79 ✅
- Core Ex CRB (parent): Plug = 19,999.79 ✅
- **CORE Products (root): Plug = 19,999.79** ❌ (Actually shows 151,547.79)

---

## How Plug is Calculated

**Formula:** `Plug = Natural - Adjusted`

**Code Location:** `app/services/calculator.py` - `calculate_plugs()`

```python
plug_results[node_id] = {
    'daily': natural['daily'] - adjusted['daily'],
    ...
}
```

**Key Point:** Plug is calculated **independently for each node** using:
- `Natural` = Value from natural rollup (strategy matching)
- `Adjusted` = Value after rules and waterfall aggregation

---

## Root Cause Hypothesis

### Hypothesis 1: Natural Value Mismatch

**For parent nodes, Natural might be calculated differently than sum of children:**

1. **Natural Rollup (`_calculate_strategy_rollup`):**
   - For leaf nodes: Matches `strategy = 'node_name'` → Returns direct value
   - For parent nodes: **ROOT node uses direct sum of ALL facts** (not sum of children)

2. **Adjusted Rollup (`waterfall_up`):**
   - For leaf nodes: Uses rule-adjusted value (or natural if no rule)
   - For parent nodes: **Sums children's adjusted values**

3. **Plug Calculation:**
   - Plug = Natural - Adjusted
   - For ROOT: Plug = (sum of ALL facts) - (sum of children adjusted)
   - If Natural includes facts that don't match any child, plug will be larger

**Evidence from Code:**
```python
# In _calculate_strategy_rollup (line 515-547):
# Step 3: Handle ROOT node - use DIRECT SUM of ALL facts
for root_id in root_nodes:
    daily_sum = Decimal(str(facts_df['pnl_daily'].sum()))  # Sum ALL facts
    results[root_id] = {
        'daily': daily_sum,  # Direct sum, not sum of children
        ...
    }
```

**This means:**
- ROOT Natural = Sum of ALL facts in table (1,203,909.10)
- ROOT Adjusted = Sum of children adjusted values (1,052,361.31)
- ROOT Plug = 1,203,909.10 - 1,052,361.31 = **151,547.79** ✅ (Matches!)

**But the question is:** Why is Adjusted only 1,052,361.31 when Natural is 1,203,909.10?

---

## Analysis: Why Adjusted < Natural

**Natural (Original) = 1,203,909.10** (sum of ALL facts)

**Adjusted = 1,052,361.31** (sum of children adjusted values)

**Difference = 151,547.79** (this is the plug)

**Possible Reasons:**

### Reason 1: Missing Children in Adjusted

If some children are missing from `adjusted_results`, their values won't be included in the sum.

**Check:** Are all children of CORE Products present in `adjusted_results`?

### Reason 2: Children Have Zero Adjusted Values

If some children have `adjusted = 0` (due to rules or calculation issues), they won't contribute to the sum.

**From the image:**
- Core Ex CRB: Adjusted = 71,727.81
- Trading: Adjusted = 19,999.91
- CRB: Adjusted = 15,000.04 ✅ (now fixed!)
- ETF Amber: Adjusted = 346,858.60 ✅ (now fixed!)
- MSET: Adjusted = 618,774.86 ✅ (now fixed!)

**Sum of visible children:**
71,727.81 + 19,999.91 + 15,000.04 + 346,858.60 + 618,774.86 = **1,072,361.22**

**But Adjusted shows: 1,052,361.31**

**Difference: 1,072,361.22 - 1,052,361.31 = 20,000.00** (approximately)

**This suggests:** There might be another child node that's not visible or has a different value.

### Reason 3: Natural Includes Unmatched Facts

**The ROOT node's Natural value includes ALL facts in the table**, even if they don't match any child node's strategy name.

**Example:**
- If there are facts with `strategy = 'Other'` that don't match any child node
- These facts are included in ROOT Natural (1,203,909.10)
- But they're NOT included in any child's Adjusted value
- So ROOT Adjusted = sum of children < ROOT Natural
- Result: Plug = difference = unmatched facts

---

## Expected Behavior

**If the Golden Equation holds:**
- `Natural = Adjusted + Plug`
- For ROOT: `1,203,909.10 = 1,052,361.31 + 151,547.79` ✅

**But the user expects:**
- Plug should equal the sum of child plugs = 19,999.79

**This would require:**
- `Natural = Adjusted + 19,999.79`
- `1,203,909.10 = Adjusted + 19,999.79`
- `Adjusted = 1,183,909.31`

**But actual Adjusted = 1,052,361.31**

**Difference: 1,183,909.31 - 1,052,361.31 = 131,548.00**

**This suggests:** There are **131,548.00 worth of facts** that:
1. Are included in ROOT Natural (sum of all facts)
2. Are NOT included in any child's Adjusted value
3. Create the extra plug of 131,548.00

---

## Root Cause Conclusion

**The issue is NOT with the plug calculation logic** - it's mathematically correct:
- Plug = Natural - Adjusted = 1,203,909.10 - 1,052,361.31 = 151,547.79 ✅

**The issue is with the EXPECTATION:**
- User expects: Plug = sum of child plugs = 19,999.79
- Actual: Plug = Natural - Adjusted = 151,547.79

**Why the difference?**

1. **ROOT Natural includes ALL facts** (even unmatched ones)
2. **ROOT Adjusted = sum of children** (only matched children)
3. **If there are unmatched facts**, they create additional plug

**The 131,548.00 difference suggests:**
- There are facts in the table that don't match any child node's strategy name
- OR some children are missing from the hierarchy
- OR some children have zero adjusted values

---

## Recommended Investigation

1. **Check for unmatched facts:**
   - Query: What strategies exist in `fact_pnl_use_case_3`?
   - Query: What node names exist in hierarchy?
   - Compare: Are there strategies without matching nodes?

2. **Check for missing children:**
   - Verify all children of CORE Products are in `adjusted_results`
   - Check if any children have `adjusted = 0` when they shouldn't

3. **Verify Natural calculation:**
   - Does ROOT Natural = sum of ALL facts? (Yes, per code)
   - Should ROOT Natural = sum of child Naturals? (Maybe, if no unmatched facts)

---

## Potential Fix

**Option 1: Change ROOT Natural Calculation**

Instead of summing ALL facts, sum only the child Naturals:

```python
# In _calculate_strategy_rollup:
# Instead of: daily_sum = facts_df['pnl_daily'].sum()  # All facts
# Use: daily_sum = sum(child_naturals)  # Sum of children
```

**Pros:** Plug will equal sum of child plugs
**Cons:** Might miss unmatched facts (data quality issue)

**Option 2: Keep Current Logic (Recommended)**

The current logic is correct - it identifies unmatched facts as plug.

**Action:** Investigate what the 131,548.00 represents:
- Unmatched strategies?
- Missing children?
- Data quality issue?

---

## Next Steps

1. **Query unmatched facts:**
   ```sql
   SELECT strategy, COUNT(*), SUM(pnl_daily)
   FROM fact_pnl_use_case_3
   WHERE strategy NOT IN (
       SELECT node_name FROM dim_hierarchy
   )
   GROUP BY strategy
   ```

2. **Verify all children are included:**
   - Check if all children of CORE Products have values in `adjusted_results`

3. **Check if expectation is correct:**
   - Should ROOT Plug = sum of child plugs?
   - Or should ROOT Plug = Natural - Adjusted (current behavior)?

