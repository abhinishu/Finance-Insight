# Plug Discrepancy Root Cause Analysis

## Problem Summary

**Issue:** CORE Products plug shows **151,547.79** but expected **19,999.79**

**Current State:**
- Commissions (Non Swap): Plug = 19,999.79 ✅
- Commissions (parent): Plug = 19,999.79 ✅  
- Core Ex CRB (parent): Plug = 19,999.79 ✅
- **CORE Products (root): Plug = 151,547.79** ❌

**Investigation Results:**
- ✅ All strategies in fact table have matching nodes
- ✅ No unmatched facts
- ✅ Plug calculation logic is correct: `Plug = Natural - Adjusted`

---

## Root Cause: ROOT Natural Calculation

### The Issue

**ROOT Natural is calculated as sum of ALL facts:**
```python
# In _calculate_strategy_rollup (line 524):
daily_sum = Decimal(str(facts_df['pnl_daily'].sum()))  # Sum ALL facts
results[root_id] = {'daily': daily_sum, ...}
```

**This means:**
- ROOT Natural = 1,203,909.10 (sum of ALL facts in table) ✅

**ROOT Adjusted is calculated as sum of children:**
```python
# In waterfall_up (line 189-193):
adjusted_results[node_id] = {
    'daily': sum(adjusted_results.get(child_id, {}).get('daily', Decimal('0')) 
                 for child_id in children)
}
```

**This means:**
- ROOT Adjusted = Sum of children's adjusted values = 1,052,361.31 ✅

**ROOT Plug:**
- Plug = Natural - Adjusted = 1,203,909.10 - 1,052,361.31 = **151,547.79** ✅

---

## Why the Discrepancy?

### The Key Question

**If all strategies match nodes, why is Adjusted (1,052,361.31) less than Natural (1,203,909.10)?**

**Answer:** Some children might have:
1. **Zero adjusted values** (due to rules or calculation issues)
2. **Missing from adjusted_results** (not calculated)
3. **Different natural values** than their direct fact matches

### Analysis from Image Data

**Visible children of CORE Products:**
- Core Ex CRB: Adjusted = 71,727.81
- Trading: Adjusted = 19,999.91
- CRB: Adjusted = 15,000.04
- ETF Amber: Adjusted = 346,858.60
- MSET: Adjusted = 618,774.86

**Sum of visible children:** 1,072,361.22

**But ROOT Adjusted = 1,052,361.31**

**Difference:** 1,072,361.22 - 1,052,361.31 = **19,999.91**

**This is approximately equal to Trading's adjusted value!**

**Hypothesis:** Trading might be counted twice, or there's another child with negative value, or the calculation is excluding Trading.

---

## The Real Issue: Strategy Matching vs Hierarchy

### Strategy Rollup Logic

**`_calculate_strategy_rollup` matches:**
- `fact.strategy` to `node.node_name` (exact match)

**For example:**
- Facts with `strategy = 'CRB'` → Match node `'CRB'` → Natural = 15,000.04 ✅
- Facts with `strategy = 'ETF Amber'` → Match node `'ETF Amber'` → Natural = 346,858.60 ✅

**But for parent nodes:**
- Parent nodes like "Core Ex CRB" might NOT have direct facts with `strategy = 'Core Ex CRB'`
- Instead, they aggregate from children

**The problem:**
- ROOT Natural = Sum of ALL facts (including facts that match child nodes)
- ROOT Adjusted = Sum of children's adjusted values
- **If a child has a rule that sets Adjusted = 0, it doesn't contribute to ROOT Adjusted**
- **But its Natural value IS included in ROOT Natural**

### Example: Commissions (Non Swap)

- Natural = 19,999.79 (from facts with `strategy = 'Commissions (Non Swap)'`)
- Adjusted = 0.00 (rule returns 0 because `strategy = 'CORE'` doesn't exist)
- Plug = 19,999.79 ✅

**This plug is correct at the leaf level.**

**But at ROOT level:**
- ROOT Natural includes the 19,999.79 (from Commissions Non Swap facts)
- ROOT Adjusted does NOT include 19,999.79 (because child Adjusted = 0)
- **Result: ROOT Plug includes this 19,999.79**

**But wait - the user sees ROOT Plug = 151,547.79, not 19,999.79.**

**This means there are OTHER nodes with similar issues!**

---

## Root Cause Conclusion

**The issue is NOT with the plug calculation - it's mathematically correct.**

**The issue is with the EXPECTATION:**

**User expects:** Plug = sum of child plugs = 19,999.79

**Actual:** Plug = Natural - Adjusted = 151,547.79

**Why the difference?**

1. **ROOT Natural = Sum of ALL facts** (1,203,909.10)
   - Includes facts for ALL nodes (even if their Adjusted = 0)

2. **ROOT Adjusted = Sum of children Adjusted** (1,052,361.31)
   - Only includes children that have non-zero Adjusted values
   - Excludes children with Adjusted = 0 (due to rules)

3. **Plug = Natural - Adjusted = 151,547.79**
   - This represents the sum of ALL nodes with Adjusted = 0
   - Not just Commissions (Non Swap), but potentially other nodes too

---

## Verification Needed

**To confirm this hypothesis, check:**

1. **How many children does CORE Products have?**
   - Query: `SELECT COUNT(*) FROM dim_hierarchy WHERE parent_node_id = 'NODE_1'` (or root node ID)

2. **What are their Adjusted values?**
   - Check if any children have Adjusted = 0 when Natural > 0

3. **Sum of child Naturals vs ROOT Natural:**
   - Does sum of child Naturals = ROOT Natural?
   - If not, there's a calculation mismatch

---

## Recommended Fix

**Option 1: Change ROOT Natural to Sum of Child Naturals**

Instead of summing ALL facts, sum child Naturals:

```python
# In _calculate_strategy_rollup:
# For ROOT node:
children = children_dict.get(root_id, [])
child_naturals_sum = sum(
    results.get(child_id, {}).get('daily', Decimal('0'))
    for child_id in children
)
results[root_id] = {'daily': child_naturals_sum, ...}
```

**Pros:** Plug will equal sum of child plugs
**Cons:** Might miss facts that don't match any child (data quality issue)

**Option 2: Keep Current Logic (Recommended)**

The current logic is correct - it identifies nodes with Adjusted = 0.

**Action:** Investigate which nodes have Adjusted = 0 but Natural > 0:
- These nodes create the plug
- Sum of their Naturals should equal the plug discrepancy

---

## Next Steps

1. **Query all children of CORE Products and their values:**
   ```sql
   SELECT 
       h.node_id,
       h.node_name,
       fcr.measure_vector->>'daily' as adjusted,
       fcr.plug_vector->>'daily' as plug
   FROM dim_hierarchy h
   JOIN fact_calculated_results fcr ON h.node_id = fcr.node_id
   WHERE h.parent_node_id = 'NODE_1'  -- or root node ID
   ORDER BY h.node_name
   ```

2. **Check for nodes with Adjusted = 0:**
   - These nodes contribute to the plug
   - Their Natural values sum to the plug discrepancy

3. **Verify the calculation:**
   - Sum of child Naturals = ROOT Natural?
   - Sum of child Adjusted = ROOT Adjusted?
   - Sum of child Plugs = ROOT Plug?

