# Transaction Management Fix - InFailedSqlTransaction Error

**Date:** 2025-01-03  
**Issue:** `psycopg2.errors.InFailedSqlTransaction` during `save_calculation_results`  
**Root Cause:** Prior SQL exception was swallowed, leaving transaction in failed state

---

## Changes Made

### 1. Fixed `apply_rule_to_leaf()` in `app/services/calculator.py`

**Problem:** SQL errors were caught and swallowed, returning zeros but leaving transaction in failed state.

**Solution:**
- Added SQL WHERE clause validation (checks for dangerous patterns)
- Changed exception handling to **re-raise** exceptions instead of swallowing them
- Added detailed error logging with full traceback (`exc_info=True`)
- Logs the actual SQL WHERE clause that failed

**Key Changes:**
```python
# Before: Swallowed exception
except Exception as e:
    logger.error(f"Error applying rule...")
    return {'daily': Decimal('0'), ...}  # Transaction still failed!

# After: Re-raises exception
except Exception as e:
    logger.error(f"SQL execution failed...", exc_info=True)
    raise  # Let caller handle transaction rollback
```

### 2. Fixed `calculate_use_case()` Transaction Management

**Problem:** Exception handler didn't properly rollback transaction before updating run status.

**Solution:**
- Added explicit `session.rollback()` in exception handler
- Added nested try/except for rollback (handles rollback failures gracefully)
- Logs original exception with full traceback BEFORE rollback
- Updates run status in a fresh transaction after rollback
- Re-raises exception so UI knows calculation failed

**Key Changes:**
```python
except Exception as e:
    # 1. Log ORIGINAL exception immediately
    logger.error(f"Calculation failed...", exc_info=True)
    
    # 2. Explicitly rollback transaction
    try:
        session.rollback()
    except Exception as rollback_error:
        logger.error(f"Failed to rollback...", exc_info=True)
    
    # 3. Update run status in fresh transaction
    try:
        run.status = RunStatus.FAILED
        session.commit()
    except Exception as status_error:
        logger.error(f"Failed to update run status...", exc_info=True)
    
    # 4. Re-raise original exception
    raise
```

### 3. Added SQL Validation

**Added validation in `apply_rule_to_leaf()`:**
- Checks for dangerous SQL patterns: `;`, `--`, `/*`, `*/`, `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `CREATE`, `TRUNCATE`
- Raises `ValueError` with clear message if dangerous pattern detected
- Prevents SQL injection and syntax errors from reaching database

**Also added to `app/engine/waterfall.py`** for consistency (legacy code path).

---

## Testing Instructions

### Step 1: Re-run Calculation

**Action:** Trigger a calculation from Tab 3 or Tab 4 for Use Case 3.

**Expected Behavior:**
- If there's a SQL syntax error in a rule, you should now see:
  1. **Detailed error log** in backend console with full traceback
  2. **The actual SQL WHERE clause** that failed
  3. **The rule ID and node ID** where the error occurred
  4. **Transaction properly rolled back** (no InFailedSqlTransaction)
  5. **Run status set to FAILED** in database
  6. **UI shows error message** (not silent failure)

### Step 2: Check Backend Logs

**Look for:**
```
ERROR: SQL execution failed for rule {rule_id} (node {node_id}). 
SQL WHERE clause: {actual_sql_where}. 
Error: {original_error}
```

**This will reveal:**
- Which rule has invalid SQL
- What the actual SQL WHERE clause is
- The exact syntax error (e.g., double quotes, invalid column name)

### Step 3: Fix the Rule

**Common Issues:**
1. **Double quotes instead of single quotes:**
   ```sql
   -- WRONG
   WHERE region = "Americas"
   
   -- CORRECT
   WHERE region = 'Americas'
   ```

2. **Invalid column names:**
   ```sql
   -- WRONG (column doesn't exist)
   WHERE desk_name = 'Trading'
   
   -- CORRECT (check actual column name)
   WHERE desk = 'Trading'
   ```

3. **Missing quotes for string values:**
   ```sql
   -- WRONG
   WHERE region = Americas
   
   -- CORRECT
   WHERE region = 'Americas'
   ```

---

## Files Modified

1. **`app/services/calculator.py`**
   - `apply_rule_to_leaf()`: Added SQL validation, improved error handling
   - `calculate_use_case()`: Added proper transaction rollback

2. **`app/engine/waterfall.py`**
   - `apply_rule_override()`: Added SQL validation (for legacy code path)

---

## Next Steps

1. **Re-run the calculation** and check backend logs for the actual error
2. **Identify the problematic rule** from the error log
3. **Fix the SQL WHERE clause** in that rule (via UI or direct DB update)
4. **Re-run calculation** to verify fix

---

## Benefits

✅ **Unmasks the real bug** - Original SQL error is now visible in logs  
✅ **Prevents transaction corruption** - Proper rollback prevents InFailedSqlTransaction  
✅ **Better error messages** - UI and logs show what actually failed  
✅ **SQL injection protection** - Basic validation prevents dangerous SQL patterns  
✅ **Easier debugging** - Full traceback and SQL clause logged for investigation

