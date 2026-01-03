# Hybrid Parents Fix Implementation

## Summary

**Issue:** Hybrid parents (parent nodes with direct fact rows) were causing a $131,548.00 reconciliation break because:
- Natural included direct rows ✅
- Adjusted only summed children (excluded direct rows) ❌
- Plug = Natural - Adjusted = direct rows = $131,548.00

**Fix:** Modified `waterfall_up()` to include direct values for hybrid parents:
- Adjusted = Direct (from natural) + Sum(Children Adjusted)

---

## Changes Made

### 1. `app/services/unified_pnl_service.py` - `_calculate_strategy_rollup()`

**Change:** Preserve direct values for hybrid parents when aggregating from children.

**Before:**
```python
# Step 2: Always overwrite parent with sum of children
results[node_id] = {
    'daily': child_daily,  # Lost direct value!
    ...
}
```

**After:**
```python
# Step 2: For hybrid parents, combine direct + children
direct_value = direct_values.get(node_id, {})
if is_hybrid:
    results[node_id] = {
        'daily': direct_daily + child_daily,  # Preserve direct!
        ...
    }
```

**Result:** `natural_results` now correctly contains Direct + Children for hybrid parents.

### 2. `app/services/calculator.py` - `waterfall_up()`

**Change:** Extract direct value from `natural_results` and add it to children adjusted sum.

**Before:**
```python
# Only sum children
adjusted_results[node_id] = {
    'daily': sum(children adjusted),  # Missing direct value!
    ...
}
```

**After:**
```python
# Extract direct from natural, then combine with children adjusted
direct_daily = natural_daily - children_natural_daily  # Extract direct part
adjusted_results[node_id] = {
    'daily': direct_daily + children_sum_daily,  # Include direct!
    ...
}
```

**Result:** `adjusted_results` now correctly contains Direct + Children Adjusted for hybrid parents.

---

## How It Works

### For Hybrid Parents (e.g., Core Ex CRB):

1. **Natural Rollup:**
   - Direct match: `strategy = 'Core Ex CRB'` → $50,000.00
   - Children Natural: Commissions + Trading = $91,727.72
   - **Natural = Direct + Children = $141,727.72** ✅

2. **Adjusted Rollup:**
   - Direct (from natural, no rules): $50,000.00
   - Children Adjusted: Commissions Adjusted + Trading Adjusted = $91,727.72
   - **Adjusted = Direct + Children = $141,727.72** ✅

3. **Plug:**
   - Plug = Natural - Adjusted = $141,727.72 - $141,727.72 = **$0.00** ✅

### For Regular Parents (no direct rows):

1. **Natural Rollup:**
   - No direct match
   - Children Natural: Sum of children
   - **Natural = Children** ✅

2. **Adjusted Rollup:**
   - No direct value
   - Children Adjusted: Sum of children
   - **Adjusted = Children** ✅

3. **Plug:**
   - Plug = Natural - Adjusted = **$0.00** (if no rules) ✅

---

## Expected Impact

**Before Fix:**
- Core Ex CRB: Natural = $141,727.72, Adjusted = $91,727.72, Plug = $50,000.00
- Commissions: Natural = $92,496.90, Adjusted = $51,727.90, Plug = $40,769.00
- Trading: Natural = $60,778.91, Adjusted = $19,999.91, Plug = $40,779.00
- **ROOT Plug = $151,547.79** ❌

**After Fix:**
- Core Ex CRB: Natural = $141,727.72, Adjusted = $141,727.72, Plug = $0.00 ✅
- Commissions: Natural = $92,496.90, Adjusted = $92,496.90, Plug = $0.00 ✅ (if no rules)
- Trading: Natural = $60,778.91, Adjusted = $60,778.91, Plug = $0.00 ✅
- **ROOT Plug = $19,999.79** ✅ (only Commissions Non Swap rule plug)

---

## Testing

1. **Re-run calculation for Use Case 3**
2. **Verify hybrid parents:**
   - Core Ex CRB: Adjusted should = Natural (no plug)
   - Commissions: Adjusted should = Natural (no plug, unless rules apply)
   - Trading: Adjusted should = Natural (no plug)
3. **Verify ROOT plug:**
   - Should equal only the Commissions (Non Swap) rule plug = $19,999.79
   - Should NOT include hybrid parents' direct rows = $131,548.00

---

## Code Locations

- **File:** `app/services/unified_pnl_service.py`
- **Function:** `_calculate_strategy_rollup()`
- **Lines:** ~494-533 (Step 2 aggregation)

- **File:** `app/services/calculator.py`
- **Function:** `waterfall_up()`
- **Lines:** ~214-255 (Direct value extraction and combination)
- **Call Site:** Line ~559 (Passes `natural_results`)

---

## Status

✅ **IMPLEMENTED** - Ready for testing

