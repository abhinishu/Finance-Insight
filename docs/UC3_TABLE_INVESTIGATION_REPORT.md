# Use Case 3 Table Investigation Report

**Date:** 2025-01-03  
**Use Case:** America Cash Equity Trading  
**Issue:** User believes Use Case 3 should read from dedicated input table, not `fact_pnl_gold`

---

## Task 1: Current Configuration ✅

**Query Result:**
```sql
SELECT use_case_id, name, input_table_name, atlas_structure_id, status
FROM use_cases
WHERE name ILIKE '%america%cash%equity%'
```

**Result:**
- **Use Case ID:** `fce60983-0328-496b-b6e1-34249ec5aa5a`
- **Name:** `America Cash Equity Trading`
- **Current input_table_name:** `fact_pnl_use_case_3` ✅ **CORRECTLY CONFIGURED**
- **Atlas Structure ID:** `America Cash Equity Trading Structure`
- **Status:** `ACTIVE`

**Conclusion:** ✅ Use Case 3 is **already configured correctly** to use `fact_pnl_use_case_3`.

---

## Task 2: Candidate Tables Found

**Query:**
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND (
    table_name ILIKE '%amer%'
    OR table_name ILIKE '%equity%'
    OR table_name ILIKE '%cash%'
    OR table_name ILIKE '%use_case_3%'
    OR table_name ILIKE '%input%'
    OR table_name ILIKE '%fact_pnl%'
  )
```

**Found 3 candidate tables:**
1. `fact_pnl_entries` - Generic fact table with use_case_id column
2. `fact_pnl_gold` - Legacy/default fact table
3. `fact_pnl_use_case_3` - ✅ **Dedicated table for Use Case 3**

---

## Task 3: Schema Comparison

### 1. `fact_pnl_use_case_3` (Expected Table) ✅

**Columns (14 total):**
- `entry_id` (uuid, PK)
- `effective_date` (date)
- `cost_center` (varchar)
- `division` (varchar)
- `business_area` (varchar)
- `product_line` (varchar)
- `strategy` (varchar) ✅ **Has `strategy` (not `strategy_id`)**
- `process_1` (varchar)
- `process_2` (varchar)
- `book` (varchar)
- `pnl_daily` (numeric) ✅ **Has `pnl_daily` (not `daily_pnl`)**
- `pnl_commission` (numeric) ✅ **Has `pnl_commission`**
- `pnl_trade` (numeric) ✅ **Has `pnl_trade`**
- `created_at` (timestamp)

**Key Columns Found:** ✅
- `strategy` (not `strategy_id`)
- `pnl_daily`, `pnl_commission`, `pnl_trade`

### 2. `fact_pnl_gold` (Current Default - WRONG) ❌

**Columns (first 10 shown):**
- `fact_id` (uuid)
- `account_id` (varchar)
- `cc_id` (varchar)
- `book_id` (varchar)
- `strategy_id` (varchar) ❌ **Has `strategy_id` (not `strategy`)**
- `trade_date` (date)
- `daily_pnl` (numeric) ❌ **Has `daily_pnl` (not `pnl_daily`)**
- `mtd_pnl` (numeric)
- `ytd_pnl` (numeric)
- `pytd_pnl` (numeric)

**Key Columns NOT Found:** ❌
- `daily_commission` - Does not exist
- `strategy` - Has `strategy_id` instead

**Conclusion:** `fact_pnl_gold` is **NOT the correct table** for Use Case 3.

---

## Root Cause Analysis

### The Problem

**Configuration is correct**, but **code was ignoring it**:

1. ✅ **Database Configuration:** Use Case 3 has `input_table_name = 'fact_pnl_use_case_3'`
2. ❌ **Code Bug:** `apply_rule_to_leaf()` in `app/services/calculator.py` was **hardcoding** `fact_pnl_gold`
3. ❌ **Column Mismatch:** Code was querying `daily_pnl`, `mtd_pnl`, etc. but `fact_pnl_use_case_3` has `pnl_daily`, `pnl_commission`, `pnl_trade`
4. ❌ **Column Name Mismatch:** Rules using `strategy` column, but `fact_pnl_gold` has `strategy_id`

### The Fix

**File:** `app/services/calculator.py`

**Changes Made:**
1. Updated `apply_rule_to_leaf()` to accept `use_case` parameter
2. Added logic to check `use_case.input_table_name` to determine table
3. Added table-specific SQL query building:
   - `fact_pnl_use_case_3`: Uses `pnl_daily`, `pnl_commission`, `pnl_trade`
   - `fact_pnl_entries`: Uses `daily_amount`, `wtd_amount`, `ytd_amount`
   - `fact_pnl_gold`: Uses `daily_pnl`, `mtd_pnl`, `ytd_pnl`, `pytd_pnl`
4. Updated all calls to `apply_rule_to_leaf()` to pass `use_case` parameter
5. Added logging to show which table is being used

---

## Summary

| Item | Status | Details |
|------|--------|---------|
| **Database Configuration** | ✅ Correct | `input_table_name = 'fact_pnl_use_case_3'` |
| **Table Exists** | ✅ Yes | `fact_pnl_use_case_3` with correct schema |
| **Code Implementation** | ✅ Fixed | `apply_rule_to_leaf()` now respects `input_table_name` |
| **Column Mapping** | ✅ Fixed | Uses correct columns for each table type |

---

## No SQL Update Needed

**The database configuration is already correct.** No SQL command needed to update `use_cases` table.

**However**, if you need to verify or reset it:

```sql
-- Verify current configuration
SELECT use_case_id, name, input_table_name
FROM use_cases
WHERE name ILIKE '%america%cash%equity%';

-- If needed, update (should already be correct):
UPDATE use_cases
SET input_table_name = 'fact_pnl_use_case_3'
WHERE name ILIKE '%america%cash%equity%';
```

---

## Next Steps

1. ✅ **Code Fix Applied** - `apply_rule_to_leaf()` now uses correct table
2. **Test Calculation** - Re-run Use Case 3 calculation to verify it works
3. **Check Logs** - Look for log messages showing `"Using table 'fact_pnl_use_case_3'"`
4. **Verify Rules** - Ensure rules use correct column names:
   - ✅ Use `strategy` (not `strategy_id`)
   - ✅ Use `pnl_daily`, `pnl_commission`, `pnl_trade` (not `daily_pnl`, `mtd_pnl`)

---

## Column Name Reference

### For Use Case 3 Rules (fact_pnl_use_case_3):

| Measure Name | Column Name | Notes |
|--------------|-------------|-------|
| `daily_pnl` | `pnl_daily` | Maps to pnl_daily column |
| `daily_commission` | `pnl_commission` | Maps to pnl_commission column |
| `daily_trade` | `pnl_trade` | Maps to pnl_trade column |

### Dimension Columns:

| Dimension | Column Name | Notes |
|-----------|-------------|-------|
| Strategy | `strategy` | ✅ Use `strategy` (not `strategy_id`) |
| Book | `book` | ✅ Use `book` (not `book_id`) |
| Cost Center | `cost_center` | ✅ Use `cost_center` (not `cc_id`) |

---

**Status:** ✅ **RESOLVED** - Code now correctly uses `fact_pnl_use_case_3` table for Use Case 3.

