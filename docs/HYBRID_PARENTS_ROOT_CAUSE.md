# Root Cause: Hybrid Parents Causing Reconciliation Break

## 🎯 ROOT CAUSE IDENTIFIED

**Issue:** Reconciliation break of **$131,548.00** at ROOT node (CORE Products)

**Root Cause:** **Hybrid Parents** - Parent nodes that have BOTH:
1. Direct rows in `fact_pnl_use_case_3` table
2. Children in the hierarchy

**The Problem:**
- ROOT Natural includes hybrid parents' direct rows (sum of ALL facts)
- ROOT Adjusted only sums children (excludes parent direct rows)
- Result: Plug = Natural - Adjusted = hybrid parents' direct rows = **$131,548.00**

---

## Hybrid Parents Found

### 1. Core Ex CRB (NODE_3)
- **Direct P&L:** $50,000.00 (3 rows in fact table)
- **Children:** Commissions, Trading
- **Children Direct P&L:** $81,548.00
- **Total (Parent + Children):** $131,548.00

### 2. Commissions (NODE_4)
- **Direct P&L:** $40,769.00 (1 row in fact table)
- **Children:** Commissions (Non Swap), Swap Commission
- **Children Direct P&L:** $71,727.69
- **Total (Parent + Children):** $112,496.69

### 3. Trading (NODE_7)
- **Direct P&L:** $40,779.00 (1 row in fact table)
- **Children:** Facilitations, Inventory Management
- **Children Direct P&L:** $19,999.91
- **Total (Parent + Children):** $60,778.91

**Total Hybrid Parents Direct P&L:** **$131,548.00** ✅ (Matches plug discrepancy exactly!)

---

## How the Break Occurs

### Current Calculation Flow

1. **Natural Rollup (`_calculate_strategy_rollup`):**
   - Matches `strategy = 'Core Ex CRB'` → Returns **$50,000.00** (direct rows)
   - Matches `strategy = 'Commissions'` → Returns **$40,769.00** (direct rows)
   - Matches `strategy = 'Trading'` → Returns **$40,779.00** (direct rows)
   - **ROOT Natural = Sum of ALL facts = $1,203,909.10** (includes hybrid parents' direct rows)

2. **Adjusted Rollup (`waterfall_up`):**
   - For Core Ex CRB: Adjusted = sum of children (Commissions + Trading) = $71,727.81 + $19,999.91 = **$91,727.72**
   - **Does NOT include parent's direct $50,000.00**
   - **ROOT Adjusted = Sum of children = $1,052,361.31** (excludes hybrid parents' direct rows)

3. **Plug Calculation:**
   - Plug = Natural - Adjusted
   - ROOT Plug = $1,203,909.10 - $1,052,361.31 = **$151,547.79**
   - This includes:
     - Commissions (Non Swap) plug: $19,999.79 ✅
     - Hybrid parents' direct rows: $131,548.00 ✅
   - **Total: $151,547.79** ✅

---

## The Mathematical Proof

**ROOT Natural = $1,203,909.10**
- Includes ALL facts, including hybrid parents' direct rows

**ROOT Adjusted = $1,052,361.31**
- Sum of children's adjusted values
- Excludes hybrid parents' direct rows

**ROOT Plug = $151,547.79**
- = Natural - Adjusted
- = $1,203,909.10 - $1,052,361.31
- = $151,547.79 ✅

**Breakdown:**
- Commissions (Non Swap) plug: $19,999.79
- Hybrid parents' direct rows: $131,548.00
- **Total: $151,547.79** ✅

---

## Why This Happens

### Strategy Rollup Logic

**`_calculate_strategy_rollup` matches:**
- `fact.strategy` to `node.node_name` (exact match)

**For hybrid parents:**
- Facts with `strategy = 'Core Ex CRB'` → Match node `'Core Ex CRB'` → Natural = $50,000.00 ✅
- Facts with `strategy = 'Commissions'` → Match node `'Commissions'` → Natural = $40,769.00 ✅
- Facts with `strategy = 'Trading'` → Match node `'Trading'` → Natural = $40,779.00 ✅

**But `waterfall_up` only sums children:**
- Core Ex CRB Adjusted = sum(Commissions, Trading) = $91,727.72
- **Does NOT add parent's direct $50,000.00**

**Result:**
- Natural includes direct rows ✅
- Adjusted excludes direct rows ❌
- Plug = difference = direct rows ✅

---

## Solution Options

### Option 1: Include Direct Rows in Adjusted (Recommended)

**For hybrid parents, Adjusted should = direct + sum(children):**

```python
# In waterfall_up():
if node_id in natural_results:
    # Hybrid parent: has direct value
    direct_value = natural_results[node_id].get('daily', Decimal('0'))
    children_sum = sum(children adjusted)
    adjusted_results[node_id] = direct_value + children_sum
else:
    # Regular parent: no direct value
    adjusted_results[node_id] = sum(children adjusted)
```

**Pros:**
- Adjusted = Natural (no plug for hybrid parents)
- Mathematically correct
- Preserves direct rows

**Cons:**
- Requires code change
- Need to check if direct value exists in natural_results

### Option 2: Exclude Direct Rows from Natural

**For hybrid parents, Natural should = sum(children) only:**

```python
# In _calculate_strategy_rollup():
# Skip direct match for parent nodes, only aggregate from children
if node_id in root_nodes or has_children:
    # Don't match direct rows, only aggregate children
    continue
```

**Pros:**
- Natural = Adjusted (no plug)
- Simpler logic

**Cons:**
- Loses direct row data
- Might not be desired behavior

### Option 3: Mark Hybrid Parents as Leaf Nodes

**If direct rows should be the only value (children are separate):**

```sql
UPDATE dim_hierarchy
SET is_leaf = true
WHERE node_id IN ('NODE_3', 'NODE_4', 'NODE_7')
  AND is_leaf = false;
```

**Pros:**
- Simple fix
- Direct rows preserved

**Cons:**
- Loses parent-child relationship
- Children won't roll up to parent

---

## Recommendation

**Option 1 is recommended** - Include direct rows in Adjusted for hybrid parents.

**Reasoning:**
- Preserves both direct rows and children aggregation
- Mathematically correct: Natural = Adjusted (no plug)
- Maintains parent-child relationships
- Aligns with business logic (parent = direct + children)

---

## Next Steps

1. **Implement Option 1:** Modify `waterfall_up()` to include direct values for hybrid parents
2. **Test:** Re-run calculation and verify ROOT Plug = $19,999.79 (only Commissions Non Swap)
3. **Verify:** Check that hybrid parents' Adjusted = direct + sum(children)

---

## Summary

| Hybrid Parent | Direct P&L | Children Sum | Should Be Adjusted | Current Adjusted | Plug Created |
|---------------|------------|--------------|-------------------|------------------|--------------|
| **Core Ex CRB** | $50,000.00 | $91,727.72 | $141,727.72 | $91,727.72 | $50,000.00 |
| **Commissions** | $40,769.00 | $51,727.90 | $92,496.90 | $51,727.90 | $40,769.00 |
| **Trading** | $40,779.00 | $19,999.91 | $60,778.91 | $19,999.91 | $40,779.00 |
| **TOTAL** | **$131,548.00** | | | | **$131,548.00** ✅ |

**This exactly matches the plug discrepancy!** 🎯

