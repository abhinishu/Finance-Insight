# Root Cause Analysis: Use Case 3 Showing All Zeros

## Executive Summary

**Problem:** Use Case 3 ("America Cash Equity Trading") shows all zeros (0.00) for Original Daily P&L, Adjusted Daily P&L, and Reconciliation Plug in Tab 4 (Executive Dashboard), while Use Cases 1 and 2 show populated values.

**Root Cause:** The `calculate_use_case()` function in `app/services/calculator.py` is using the **WRONG rollup function** for Use Case 3. It calls `calculate_natural_rollup()` (which queries `fact_pnl_gold`) instead of `_calculate_strategy_rollup()` (which queries `fact_pnl_use_case_3`).

---

## Investigation Findings

### ✅ Data Availability
- **fact_pnl_use_case_3 HAS DATA:**
  - 776 rows
  - 10 distinct strategies
  - Date range: 2024-01-01 to 2026-01-02
  - Total Daily P&L: **1,203,909.10**
  - Total Commission: 3,009,774.02
  - Total Trade: 12,039,093.89

### ✅ Calculation Runs
- **Calculations ARE running:**
  - Latest run: 2026-01-03 14:14:49 (Status: COMPLETED, Duration: 73ms)
  - Multiple successful runs exist

### ❌ Saved Results
- **Results ARE being saved, but ALL ZEROS:**
  - 33 result rows in `fact_calculated_results`
  - All show `daily=0.0, mtd=0.0`
  - Example: Node NODE_5 (Commissions): `daily=0.0, mtd=0.0, override=True`

### ❌ Root Cause Identified
**The `calculate_use_case()` function does NOT use the dual-path rollup logic!**

---

## Code Analysis

### Current Implementation (WRONG)

**File:** `app/services/calculator.py`  
**Function:** `calculate_use_case()`  
**Line:** ~334

```python
# CURRENT CODE (WRONG):
natural_results = calculate_natural_rollup(
    hierarchy_dict, children_dict, leaf_nodes, facts_df
)
```

**Problem:**
1. `calculate_natural_rollup()` expects `facts_df` from `fact_pnl_gold` (Use Cases 1 & 2)
2. It does NOT work with `fact_pnl_use_case_3` schema (different column names)
3. It's called regardless of which use case is being calculated

### Correct Implementation (What Tab 2 & Tab 4 GET endpoint use)

**File:** `app/api/routes/calculations.py`  
**Function:** `get_calculation_results()`  
**Line:** ~344-355

```python
# CORRECT CODE (used by GET /results):
if input_table_name and input_table_name.strip() == 'fact_pnl_use_case_3':
    # Use Case 3: Strategy rollup
    natural_results = _calculate_strategy_rollup(
        db, use_case_id, hierarchy_dict, children_dict, leaf_nodes
    )
else:
    # Use Cases 1 & 2: Legacy rollup
    natural_results = _calculate_legacy_rollup(
        db, use_case_id, hierarchy_dict, children_dict, leaf_nodes
    )
```

**Why This Works:**
- Checks `use_case.input_table_name` to determine which rollup to use
- Uses `_calculate_strategy_rollup()` for Use Case 3 (queries `fact_pnl_use_case_3`)
- Uses `_calculate_legacy_rollup()` for Use Cases 1 & 2 (queries `fact_pnl_gold`)

---

## Why Tab 2 Shows Data But Tab 4 Doesn't

### Tab 2 (Discovery Screen)
- **Endpoint:** `GET /api/v1/discovery`
- **Uses:** `_calculate_strategy_rollup()` for Use Case 3 ✅
- **Result:** Shows populated values ✅

### Tab 4 (Executive Dashboard)
- **When viewing without calculation:**
  - **Endpoint:** `GET /api/v1/use-cases/{id}/results`
  - **Uses:** `_calculate_strategy_rollup()` for Use Case 3 ✅
  - **Result:** Shows populated values ✅

- **After running calculation:**
  - **Calculation:** `POST /api/v1/use-cases/{id}/calculate`
  - **Uses:** `calculate_natural_rollup()` (WRONG) ❌
  - **Saves:** All zeros to `fact_calculated_results` ❌
  - **GET /results then returns:** Saved zeros instead of recalculating ❌

---

## The Mismatch

| Component | Use Case 3 Rollup Function | Status |
|-----------|---------------------------|--------|
| **Tab 2 (Discovery)** | `_calculate_strategy_rollup()` | ✅ Works |
| **Tab 4 GET /results** | `_calculate_strategy_rollup()` | ✅ Works |
| **Tab 4 POST /calculate** | `calculate_natural_rollup()` | ❌ **WRONG** |

---

## Impact

1. **User clicks "Run Calculation" in Tab 4:**
   - Calculation runs successfully (no errors)
   - But uses wrong rollup function
   - Saves all zeros to database
   - Tab 4 then shows zeros (from saved results)

2. **User refreshes Tab 4:**
   - GET /results returns saved zeros
   - Even though Tab 2 shows correct values

3. **User views Tab 2:**
   - Always shows correct values (recalculates on-the-fly)

---

## Solution

### Fix Required

**File:** `app/services/calculator.py`  
**Function:** `calculate_use_case()`  
**Location:** Around line 300-350

**Change:**
1. Add dual-path rollup logic (same as GET /results endpoint)
2. Check `use_case.input_table_name`
3. Call `_calculate_strategy_rollup()` for Use Case 3
4. Call `_calculate_legacy_rollup()` for Use Cases 1 & 2

**Code Pattern:**
```python
# Get use case to check input_table_name
use_case = session.query(UseCase).filter(
    UseCase.use_case_id == use_case_id
).first()

# Use dual-path rollup logic
from app.services.unified_pnl_service import _calculate_strategy_rollup, _calculate_legacy_rollup

if use_case and use_case.input_table_name == 'fact_pnl_use_case_3':
    # Use Case 3: Strategy rollup
    natural_results = _calculate_strategy_rollup(
        session, use_case_id, hierarchy_dict, children_dict, leaf_nodes
    )
else:
    # Use Cases 1 & 2: Legacy rollup
    natural_results = _calculate_legacy_rollup(
        session, use_case_id, hierarchy_dict, children_dict, leaf_nodes
    )
```

---

## Next Steps

1. **Fix `calculate_use_case()` to use dual-path rollup**
2. **Test calculation for Use Case 3**
3. **Verify saved results are non-zero**
4. **Verify Tab 4 shows populated values after calculation**

---

## Additional Notes

- The GET /results endpoint already has the correct logic
- Tab 2 (Discovery) already works correctly
- The issue is isolated to the POST /calculate endpoint
- This explains why "even without business rules, Original and Adjusted P&L should be populated" - the natural rollup is returning zeros because it's querying the wrong table

---

## Detailed Code Location

### Current Code (Line 330-336 in `app/services/calculator.py`):

```python
# Load facts
facts_df = load_facts(session)  # ❌ Loads from fact_pnl_gold (wrong for UC3)

# Calculate natural rollups (baseline - no rules applied)
natural_results = calculate_natural_rollup(
    hierarchy_dict, children_dict, leaf_nodes, facts_df
)  # ❌ Expects fact_pnl_gold schema
```

### What `load_facts()` Does:

**File:** `app/engine/waterfall.py`  
**Function:** `load_facts(session: Session, filters: Optional[Dict] = None)`

- Queries `fact_pnl_gold` table
- Returns DataFrame with columns: `cc_id`, `book_id`, `strategy_id`, `daily_pnl`, `mtd_pnl`, `ytd_pnl`, `pytd_pnl`
- **Does NOT work with `fact_pnl_use_case_3`** (which has `strategy`, `pnl_daily`, `pnl_commission`, `pnl_trade`)

### What `calculate_natural_rollup()` Expects:

**File:** `app/engine/waterfall.py`  
**Function:** `calculate_natural_rollup(hierarchy_dict, children_dict, leaf_nodes, facts_df)`

- Expects `facts_df` with `fact_pnl_gold` schema
- Matches by `cc_id`, `book_id`, `strategy_id`
- **Cannot match `fact_pnl_use_case_3` data** (different column names)

### Why It Returns Zeros:

1. `load_facts()` loads from `fact_pnl_gold` (empty or wrong data for UC3)
2. `calculate_natural_rollup()` tries to match hierarchy nodes to facts
3. No matches found (wrong table/schema)
4. Returns zeros for all nodes
5. Zeros are saved to `fact_calculated_results`
6. Tab 4 displays saved zeros

---

## Fix Implementation Details

### Required Changes:

1. **Remove `load_facts()` call** (not needed for dual-path rollup)
2. **Get `use_case` object** to check `input_table_name`
3. **Import rollup functions** from `unified_pnl_service`
4. **Call appropriate rollup** based on `input_table_name`

### Code Block to Replace:

**Location:** `app/services/calculator.py`, lines ~330-336

**Replace:**
```python
# Load facts
facts_df = load_facts(session)

# Calculate natural rollups (baseline - no rules applied)
natural_results = calculate_natural_rollup(
    hierarchy_dict, children_dict, leaf_nodes, facts_df
)
```

**With:**
```python
# Get use case to determine which rollup to use
use_case = session.query(UseCase).filter(
    UseCase.use_case_id == use_case_id
).first()

# Phase 5.6: Dual-Path Rollup Logic (same as GET /results endpoint)
from app.services.unified_pnl_service import _calculate_strategy_rollup, _calculate_legacy_rollup

if use_case and use_case.input_table_name == 'fact_pnl_use_case_3':
    # Use Case 3: Strategy rollup (queries fact_pnl_use_case_3)
    logger.info(f"[Calculator] Using strategy rollup for Use Case 3")
    natural_results = _calculate_strategy_rollup(
        session, use_case_id, hierarchy_dict, children_dict, leaf_nodes
    )
else:
    # Use Cases 1 & 2: Legacy rollup (queries fact_pnl_gold)
    logger.info(f"[Calculator] Using legacy rollup for Use Cases 1 & 2")
    natural_results = _calculate_legacy_rollup(
        session, use_case_id, hierarchy_dict, children_dict, leaf_nodes
    )
```

### Additional Considerations:

- **Remove unused import:** `load_facts` from `app.engine.waterfall` (if not used elsewhere)
- **Keep `calculate_natural_rollup` import:** May still be used for other purposes
- **Test both paths:** Verify Use Cases 1, 2, and 3 all work correctly after fix

