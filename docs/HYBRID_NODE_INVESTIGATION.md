# Hybrid Node Investigation: CRB, ETF Amber, MSET

## Executive Summary

**Finding:** CRB, ETF Amber, and MSET are **NOT hybrid nodes**. They are **leaf nodes with direct fact rows**, but they are incorrectly marked as `is_leaf = False` in the hierarchy.

**Root Cause:** The `waterfall_up()` function treats them as parent nodes (because `is_leaf = False`) and overwrites their direct values with `sum(children) = 0` (since they have no children).

---

## Task 1: Node Structure Inspection

### CRB (NODE_10)
- **Node Info:**
  - Node ID: `NODE_10`
  - Node Name: `CRB`
  - Parent: `NODE_2`
  - **Is Leaf: `False`** ❌ (Should be `True`)
  - Depth: 2

- **Children:** 0 (No children found)

- **Direct Rows in `fact_pnl_use_case_3`:**
  - Row Count: **41 rows**
  - Total Daily P&L: **15,000.04**
  - Total Commission: 37,500.02
  - Total Trade: 150,000.00

- **Status:** **LEAF NODE WITH DIRECT ROWS** (but marked as non-leaf)

### ETF Amber (NODE_11)
- **Node Info:**
  - Node ID: `NODE_11`
  - Node Name: `ETF Amber`
  - Parent: `NODE_2`
  - **Is Leaf: `False`** ❌ (Should be `True`)
  - Depth: 2

- **Children:** 0 (No children found)

- **Direct Rows in `fact_pnl_use_case_3`:**
  - Row Count: **38 rows**
  - Total Daily P&L: **346,858.60**
  - Total Commission: 867,146.53
  - Total Trade: 3,468,586.00

- **Status:** **LEAF NODE WITH DIRECT ROWS** (but marked as non-leaf)

### MSET (NODE_12)
- **Node Info:**
  - Node ID: `NODE_12`
  - Node Name: `MSET`
  - Parent: `NODE_2`
  - **Is Leaf: `False`** ❌ (Should be `True`)
  - Depth: 2

- **Children:** 0 (No children found)

- **Direct Rows in `fact_pnl_use_case_3`:**
  - Row Count: **50 rows**
  - Total Daily P&L: **618,774.86**
  - Total Commission: 1,546,937.18
  - Total Trade: 6,187,748.60

- **Status:** **LEAF NODE WITH DIRECT ROWS** (but marked as non-leaf)

---

## Task 2: Collision Analysis

### Current Waterfall Logic

**Function:** `waterfall_up()` in `app/services/calculator.py`

**Logic:**
```python
for depth in range(max_depth, -1, -1):
    for node_id, node in hierarchy_dict.items():
        if node.depth == depth and not node.is_leaf:  # ← Processes non-leaf nodes
            children = children_dict.get(node_id, [])
            if children:
                adjusted_results[node_id] = {
                    'daily': sum(adjusted_results.get(child_id, {}).get('daily', Decimal('0')) 
                                 for child_id in children)
                }
            else:
                # No children - set to zero  ← THIS IS THE PROBLEM
                adjusted_results[node_id] = {
                    'daily': Decimal('0'),
                    ...
                }
```

### The Problem

1. **Natural Rollup Works:**
   - `_calculate_strategy_rollup()` matches `strategy = 'CRB'` to node `'CRB'`
   - Returns direct value: `natural_results['NODE_10'] = {'daily': 15,000.04, ...}` ✅

2. **Adjusted Results Initialized:**
   - `adjusted_results = natural_results.copy()`
   - `adjusted_results['NODE_10'] = {'daily': 15,000.04, ...}` ✅

3. **Waterfall Up Destroys Values:**
   - `waterfall_up()` processes `NODE_10` because `is_leaf = False`
   - Finds no children: `children = []`
   - **Overwrites:** `adjusted_results['NODE_10'] = {'daily': Decimal('0'), ...}` ❌

4. **Result:**
   - Original P&L: 15,000.04 ✅ (from natural rollup)
   - Adjusted P&L: 0.00 ❌ (overwritten by waterfall_up)
   - Plug: 15,000.04 ✅ (Original - Adjusted)

---

## Task 3: Fix Logic Verification

### Double Counting Risk Analysis

**Question:** In `_calculate_strategy_rollup`, does querying 'CRB' include children's data?

**Answer:** **NO - No Double Counting Risk**

**Reasoning:**
1. `_calculate_strategy_rollup()` matches `fact.strategy` to `node.node_name` (exact match)
2. Query for 'CRB' node: `WHERE strategy = 'CRB'`
3. This **ONLY** matches rows where `strategy` column = `'CRB'`
4. Does **NOT** include rows where `strategy = 'Child of CRB'` (if such existed)
5. Since CRB has no children, there's no risk of double counting

**Conclusion:** The direct value from `strategy = 'CRB'` is **distinct and independent** from any children (if they existed).

---

## Definitive Recommendation

### Option 1: Fix Hierarchy Data (Recommended)

**Update the hierarchy to mark these nodes as leaf nodes:**

```sql
UPDATE dim_hierarchy
SET is_leaf = true
WHERE node_id IN ('NODE_10', 'NODE_11', 'NODE_12')
  AND is_leaf = false;
```

**Why This Works:**
- `waterfall_up()` only processes nodes where `not node.is_leaf`
- If `is_leaf = true`, `waterfall_up()` will skip these nodes
- Their direct values from natural rollup will be preserved

**Pros:**
- Simple fix (one SQL statement)
- Corrects data inconsistency
- No code changes required

**Cons:**
- Requires hierarchy data update
- May need to verify if this is intentional (perhaps children will be added later?)

### Option 2: Fix Waterfall Logic (Alternative)

**Modify `waterfall_up()` to preserve direct values for nodes with no children:**

```python
def waterfall_up(...):
    for depth in range(max_depth, -1, -1):
        for node_id, node in hierarchy_dict.items():
            if node.depth == depth and not node.is_leaf:
                children = children_dict.get(node_id, [])
                
                if children:
                    # Sum children (existing logic)
                    adjusted_results[node_id] = {
                        'daily': sum(...)
                    }
                else:
                    # No children - preserve direct value if it exists
                    # Don't overwrite with zero
                    if node_id not in adjusted_results:
                        # Only set to zero if no value exists
                        adjusted_results[node_id] = {
                            'daily': Decimal('0'),
                            ...
                        }
                    # Otherwise, keep existing value (from natural rollup)
```

**Pros:**
- Handles hybrid nodes correctly (if they exist in future)
- More robust logic

**Cons:**
- Requires code change
- Doesn't fix the data inconsistency

### Option 3: Hybrid Node Support (Future-Proof)

**Modify `waterfall_up()` to support hybrid nodes:**

```python
def waterfall_up(...):
    for depth in range(max_depth, -1, -1):
        for node_id, node in hierarchy_dict.items():
            if node.depth == depth and not node.is_leaf:
                children = children_dict.get(node_id, [])
                
                # Get direct value from natural_results (if exists)
                direct_value = natural_results.get(node_id, {}).get('daily', Decimal('0'))
                
                if children:
                    # Sum children
                    children_sum = sum(
                        adjusted_results.get(child_id, {}).get('daily', Decimal('0'))
                        for child_id in children
                    )
                    # Hybrid: direct + children
                    adjusted_results[node_id] = {
                        'daily': direct_value + children_sum,
                        ...
                    }
                else:
                    # No children - use direct value (or zero if none)
                    adjusted_results[node_id] = {
                        'daily': direct_value,
                        ...
                    }
```

**Pros:**
- Supports true hybrid nodes (parent with both direct rows and children)
- Future-proof
- Handles current case correctly

**Cons:**
- Requires code change
- Need to pass `natural_results` to `waterfall_up()` (signature change)

---

## Final Recommendation

**Immediate Fix:** **Option 1** (Update hierarchy data)

**Reason:**
- CRB, ETF Amber, MSET are **not hybrid nodes** - they have no children
- They should be marked as `is_leaf = true`
- This is a data consistency issue, not a logic issue
- Simple, safe, and correct

**Long-term Enhancement:** **Option 3** (Hybrid node support)

**Reason:**
- If true hybrid nodes are needed in the future, Option 3 provides the correct logic
- It handles both cases: nodes with children only, and nodes with both direct rows and children

---

## Summary

| Node | Has Children | Has Direct Rows | Is Leaf (DB) | Should Be Leaf | Issue |
|------|--------------|-----------------|--------------|----------------|-------|
| **CRB** | ❌ No | ✅ Yes (41 rows) | ❌ False | ✅ True | Marked as non-leaf but has no children |
| **ETF Amber** | ❌ No | ✅ Yes (38 rows) | ❌ False | ✅ True | Marked as non-leaf but has no children |
| **MSET** | ❌ No | ✅ Yes (50 rows) | ❌ False | ✅ True | Marked as non-leaf but has no children |

**Root Cause:** Hierarchy data inconsistency - nodes marked as `is_leaf = False` but have no children.

**Fix:** Update `is_leaf = true` for these nodes, OR modify `waterfall_up()` to preserve direct values when no children exist.

