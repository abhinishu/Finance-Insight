# Use Case 3 Rule Column Name Analysis

**Date:** 2025-01-03  
**Error:** `column "strategy_id" does not exist`  
**Status:** 🔍 **ANALYSIS COMPLETE** - Awaiting Approval for Fix

---

## Error Details

```
(psycopg2.errors.UndefinedColumn) column "strategy_id" does not exist
LINE 8: WHERE strategy_id = 'CORE'
HINT: Perhaps you meant to reference the column "fact_pnl_use_case_3.strategy".
```

**SQL Query (from error):**
```sql
SELECT COALESCE(SUM(pnl_daily), 0) as daily_pnl, 
       0 as mtd_pnl, 
       0 as ytd_pnl, 
       0 as pytd_pnl 
FROM fact_pnl_use_case_3 
WHERE strategy_id = 'CORE'
```

**Analysis:**
- ✅ Code is now correctly using `fact_pnl_use_case_3` table (fix worked!)
- ❌ **BUT** the rule's SQL WHERE clause uses `strategy_id` (wrong column name)
- ✅ Table has `strategy` column (not `strategy_id`)

---

## Root Cause

**The rule was created with column names from `fact_pnl_gold` table**, but now that the code correctly routes to `fact_pnl_use_case_3`, the column names don't match.

### Column Name Differences

| fact_pnl_gold (OLD) | fact_pnl_use_case_3 (NEW) | Status |
|---------------------|---------------------------|--------|
| `strategy_id` | `strategy` | ❌ **MISMATCH** |
| `book_id` | `book` | ⚠️ Potential issue |
| `cc_id` | `cost_center` | ⚠️ Potential issue |
| `daily_pnl` | `pnl_daily` | ⚠️ Potential issue |
| `mtd_pnl` | *(not available)* | ⚠️ Not supported |
| `ytd_pnl` | *(not available)* | ⚠️ Not supported |

---

## Investigation Results

### Rules Found for Use Case 3

**Total Rules:** 2

### Problematic Rule

**Rule ID:** 69  
**Node ID:** NODE_5  
**Rule Type:** FILTER  
**Measure:** pnl_commission  
**Logic (English):** "strategy_id equals 'CORE'"  
**SQL WHERE:** `strategy_id = 'CORE'` ❌

**Issue:** Uses `strategy_id` but table has `strategy`

### Correct Rule

**Rule ID:** (Other rule appears correct - no issues detected)

---

## Impact Assessment

### Current State
- ✅ Code fix is working (correctly routing to `fact_pnl_use_case_3`)
- ❌ Rule has wrong column name (`strategy_id` instead of `strategy`)
- ❌ Calculation fails when this rule is executed

### Affected Functionality
- **Rule 69** cannot execute (causes calculation to fail)
- **Node NODE_5** will not get rule-adjusted values
- **Measure:** `pnl_commission` will show zero or natural value

---

## Recommended Fix

### Option 1: Update Rule SQL WHERE Clause (Recommended)

**SQL Command:**
```sql
UPDATE metadata_rules
SET sql_where = 'strategy = ''CORE'''
WHERE rule_id = 69;
```

**Also update logic_en for consistency:**
```sql
UPDATE metadata_rules
SET logic_en = 'strategy equals ''CORE'''
WHERE rule_id = 69;
```

### Option 2: Update via UI (If Available)

1. Navigate to Tab 3 (Business Rules)
2. Select Use Case 3
3. Find rule for node NODE_5
4. Edit the rule
5. Change SQL WHERE from `strategy_id = 'CORE'` to `strategy = 'CORE'`
6. Save

---

## Column Name Reference Guide

### For Rules Targeting `fact_pnl_use_case_3`:

**✅ CORRECT Column Names:**
```sql
-- Dimensions
strategy = 'CORE'           -- ✅ Use 'strategy'
book = 'Trading'            -- ✅ Use 'book'
cost_center = 'NY'          -- ✅ Use 'cost_center'
division = 'Equity'         -- ✅ Use 'division'
business_area = 'Cash'      -- ✅ Use 'business_area'
product_line = 'Equity'     -- ✅ Use 'product_line'

-- Measures (in SELECT, not WHERE)
pnl_daily                   -- ✅ For daily P&L
pnl_commission              -- ✅ For commission P&L
pnl_trade                   -- ✅ For trade P&L
```

**❌ WRONG Column Names (from fact_pnl_gold):**
```sql
-- Dimensions
strategy_id = 'CORE'        -- ❌ Use 'strategy' instead
book_id = 'Trading'         -- ❌ Use 'book' instead
cc_id = 'NY'                -- ❌ Use 'cost_center' instead

-- Measures
daily_pnl                   -- ❌ Use 'pnl_daily' instead
mtd_pnl                     -- ❌ Not available in fact_pnl_use_case_3
ytd_pnl                     -- ❌ Not available in fact_pnl_use_case_3
```

---

## Verification Steps

### After Fix:

1. **Verify Rule Updated:**
   ```sql
   SELECT rule_id, node_id, sql_where, logic_en
   FROM metadata_rules
   WHERE rule_id = 69;
   ```
   
   **Expected Result:**
   - `sql_where`: `strategy = 'CORE'`
   - `logic_en`: `strategy equals 'CORE'`

2. **Re-run Calculation:**
   - Trigger calculation from Tab 3 or Tab 4
   - Should complete without errors
   - Check logs for: `"Using table 'fact_pnl_use_case_3'"`

3. **Verify Results:**
   - Check Tab 4 (Executive Dashboard)
   - Node NODE_5 should show rule-adjusted values
   - Measure `pnl_commission` should reflect the rule

---

## Additional Checks Needed

### Check for Other Potential Issues:

1. **Other Rules:** Are there other rules that might have similar issues?
   - ✅ Analysis script found only 1 problematic rule
   - ⚠️ But check if new rules are created with wrong column names

2. **Rule Creation Process:**
   - How are rules created? (UI? API? Scripts?)
   - Does the rule creation process know about `input_table_name`?
   - Should rule creation UI show different column names based on use case?

3. **Rule Preview:**
   - Does the rule preview feature use the correct table?
   - Check `preview_rule_impact()` in `app/services/rules.py`

---

## Summary

| Item | Status | Details |
|------|--------|---------|
| **Code Fix** | ✅ Working | Correctly using `fact_pnl_use_case_3` |
| **Rule Configuration** | ❌ Wrong | Rule 69 uses `strategy_id` (should be `strategy`) |
| **Impact** | 🔴 High | Calculation fails when Rule 69 executes |
| **Fix Required** | ✅ Yes | Update Rule 69 SQL WHERE clause |
| **Fix Complexity** | 🟢 Low | Simple SQL UPDATE statement |

---

## Next Steps (Awaiting Approval)

1. **Approve Fix** - Update Rule 69 SQL WHERE clause
2. **Execute SQL** - Run the UPDATE command
3. **Test** - Re-run calculation to verify fix
4. **Monitor** - Check for any other similar issues

---

**Status:** 🔍 **ANALYSIS COMPLETE** - Ready for fix approval

