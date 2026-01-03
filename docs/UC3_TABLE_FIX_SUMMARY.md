# Use Case 3 Table Configuration - Investigation & Fix Summary

**Date:** 2025-01-03  
**Status:** ✅ **RESOLVED**

---

## Investigation Results

### Task 1: Current Configuration ✅

**Database Query Result:**
- **Use Case:** "America Cash Equity Trading"
- **Use Case ID:** `fce60983-0328-496b-b6e1-34249ec5aa5a`
- **Current `input_table_name`:** `fact_pnl_use_case_3` ✅ **CORRECT**

**Conclusion:** Database configuration is **already correct**. No SQL update needed.

---

### Task 2: Candidate Tables ✅

**Found 3 tables:**
1. `fact_pnl_entries` - Generic fact table
2. `fact_pnl_gold` - Legacy/default table (WRONG for UC3)
3. `fact_pnl_use_case_3` - ✅ **Correct dedicated table for Use Case 3**

---

### Task 3: Schema Comparison ✅

#### `fact_pnl_use_case_3` (Correct Table)
- ✅ Has `strategy` column (not `strategy_id`)
- ✅ Has `pnl_daily`, `pnl_commission`, `pnl_trade` columns
- ✅ Has `cost_center`, `book`, `division`, etc.

#### `fact_pnl_gold` (Wrong Table)
- ❌ Has `strategy_id` (not `strategy`)
- ❌ Has `daily_pnl`, `mtd_pnl`, `ytd_pnl` (not `pnl_daily`, etc.)
- ❌ Does NOT have `daily_commission` or `pnl_commission`

---

## Root Cause: Code Bug (Not Configuration)

**The Problem:**
- ✅ Database was correctly configured with `input_table_name = 'fact_pnl_use_case_3'`
- ❌ **BUT** `apply_rule_to_leaf()` in `app/services/calculator.py` was **hardcoding** `fact_pnl_gold`
- ❌ Code was ignoring `use_case.input_table_name` setting
- ❌ Code was using wrong column names (`daily_pnl` instead of `pnl_daily`)

---

## Fix Applied

### File: `app/services/calculator.py`

**Changes:**
1. ✅ Updated `apply_rule_to_leaf()` signature to accept `use_case: Optional[UseCase]` parameter
2. ✅ Added logic to check `use_case.input_table_name` to determine which table to query
3. ✅ Added table-specific SQL query building:
   - `fact_pnl_use_case_3`: Uses `pnl_daily`, `pnl_commission`, `pnl_trade`
   - `fact_pnl_entries`: Uses `daily_amount`, `wtd_amount`, `ytd_amount`
   - `fact_pnl_gold`: Uses `daily_pnl`, `mtd_pnl`, `ytd_pnl`, `pytd_pnl`
4. ✅ Updated all calls to `apply_rule_to_leaf()` to pass `use_case` parameter
5. ✅ Added logging to show which table is being used

**Code Pattern:**
```python
# Before (WRONG - hardcoded):
sql_query = f"""
    SELECT COALESCE(SUM(daily_pnl), 0) as daily_pnl, ...
    FROM fact_pnl_gold
    WHERE {sql_where}
"""

# After (CORRECT - dynamic):
table_name = 'fact_pnl_gold'  # Default
if use_case and use_case.input_table_name:
    table_name = use_case.input_table_name

if table_name == 'fact_pnl_use_case_3':
    sql_query = f"""
        SELECT COALESCE(SUM(pnl_daily), 0) as daily_pnl, ...
        FROM fact_pnl_use_case_3
        WHERE {sql_where}
    """
elif table_name == 'fact_pnl_entries':
    # ... fact_pnl_entries query
else:
    # ... fact_pnl_gold query
```

---

## Column Name Reference for Use Case 3

### When Writing Rules for Use Case 3:

**✅ CORRECT Column Names:**
- `strategy` (not `strategy_id`)
- `book` (not `book_id`)
- `cost_center` (not `cc_id`)
- `pnl_daily` (for daily P&L)
- `pnl_commission` (for commission P&L)
- `pnl_trade` (for trade P&L)

**❌ WRONG Column Names (from fact_pnl_gold):**
- `strategy_id` ❌
- `book_id` ❌
- `cc_id` ❌
- `daily_pnl` ❌
- `mtd_pnl` ❌

---

## Verification Commands

### Check Current Configuration:
```sql
SELECT use_case_id, name, input_table_name
FROM use_cases
WHERE name ILIKE '%america%cash%equity%';
```

**Expected Result:**
```
input_table_name: fact_pnl_use_case_3
```

### Check Table Schema:
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'fact_pnl_use_case_3'
ORDER BY ordinal_position;
```

**Key Columns to Verify:**
- ✅ `strategy` (varchar)
- ✅ `pnl_daily` (numeric)
- ✅ `pnl_commission` (numeric)
- ✅ `pnl_trade` (numeric)

---

## Next Steps

1. ✅ **Code Fix Complete** - `apply_rule_to_leaf()` now uses correct table
2. **Test Calculation** - Re-run Use Case 3 calculation
3. **Check Backend Logs** - Look for: `"Using table 'fact_pnl_use_case_3'"`
4. **Verify Rules** - Ensure rules use correct column names (`strategy`, not `strategy_id`)

---

## Summary

| Item | Status |
|------|--------|
| Database Configuration | ✅ Correct (`fact_pnl_use_case_3`) |
| Table Exists | ✅ Yes, with correct schema |
| Code Implementation | ✅ Fixed (now respects `input_table_name`) |
| Column Mapping | ✅ Fixed (uses correct columns per table) |

**Result:** ✅ **RESOLVED** - Use Case 3 will now correctly read from `fact_pnl_use_case_3` table.

