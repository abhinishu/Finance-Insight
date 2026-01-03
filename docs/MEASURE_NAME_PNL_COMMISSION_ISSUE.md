# Measure Name Issue: Rule Using pnl_daily Instead of pnl_commission

## 🔍 Issue Summary

User created a business rule for "Commissions (Non Swap)" node:
- **Rule:** SUM (PNL_Commission) where strategy = 'Commissions (Non Swap)'
- **Expected:** Should sum `pnl_commission` column → 50,000.51
- **Actual:** It's summing `pnl_daily` column → 19,999.79

## 📊 Current Data State

### Database Values:
- **SUM(pnl_daily)**: 19,999.79 ✅ (What's being returned)
- **SUM(pnl_commission)**: 50,000.51 ❌ (What should be returned)
- **SUM(pnl_trade)**: 200,000.17

### Rule Configuration:
- **Rule ID**: 76
- **Node ID**: NODE_5 (Commissions (Non Swap))
- **Measure Name**: `'pnl_commission'` ⚠️ (Stored as column name, not measure name)
- **Rule Type**: FILTER
- **SQL WHERE**: `strategy = 'Commissions (Non Swap)'`

## 🔎 Root Cause Analysis

### Issue 1: Measure Name Mismatch ⭐⭐⭐

**Location:** Rule storage vs. expected format

**Problem:**
- Rule has `measure_name = 'pnl_commission'` (actual column name)
- But `get_measure_column_name()` expects measure names like `'daily_commission'`
- The mapping function maps:
  - `'daily_commission'` → `'pnl_commission'` ✅
  - `'pnl_commission'` → `'pnl_daily'` ❌ (not in mapping, defaults to pnl_daily)

**Evidence:**
```python
# From get_measure_column_name (app/engine/waterfall.py:514-519)
mapping = {
    'daily_pnl': 'pnl_daily',
    'daily_commission': 'pnl_commission',  # ✅ Correct mapping
    'daily_trade': 'pnl_trade',
}
return mapping.get(measure_name, 'pnl_daily')  # ❌ 'pnl_commission' not in mapping, defaults to 'pnl_daily'
```

### Issue 2: Hardcoded SQL Query ⭐⭐⭐⭐⭐

**Location:** `app/services/calculator.py` lines 104-116

**Problem:**
- Code calculates `target_column = get_measure_column_name(measure_name, table_name)` (line 99)
- But then **IGNORES** it and hardcodes `pnl_daily` in the SQL query (line 110)
- There's even a TODO comment acknowledging this limitation!

**Current Code (WRONG):**
```python
target_column = get_measure_column_name(measure_name, table_name)  # Calculates 'pnl_commission'
# ... but then ...
sql_query = f"""
    SELECT 
        COALESCE(SUM(pnl_daily), 0) as daily_pnl,  # ❌ Hardcoded, ignores target_column!
        0 as mtd_pnl,
        0 as ytd_pnl,
        0 as pytd_pnl
    FROM fact_pnl_use_case_3
    WHERE {sql_where}
"""
```

### Issue 3: Result Mapping Always to 'daily' ⭐⭐⭐

**Location:** `app/services/calculator.py` lines 143-148

**Problem:**
- Result is always mapped to `'daily'` key
- If measure is `'daily_commission'`, result should go to `'mtd'`
- If measure is `'daily_trade'`, result should go to `'ytd'`

**Current Code:**
```python
return {
    'daily': Decimal(str(result[0] or 0)),  # Always uses first column
    'mtd': Decimal(str(result[1] or 0)),   # Always 0 for fact_pnl_use_case_3
    'ytd': Decimal(str(result[2] or 0)),    # Always 0 for fact_pnl_use_case_3
    'pytd': Decimal(str(result[3] or 0)),
}
```

## 💡 Recommended Fix

### Fix 1: Update SQL Query to Use target_column

**File:** `app/services/calculator.py` lines 104-116

**Change:**
```python
if table_name == 'fact_pnl_use_case_3':
    # Use Case 3: fact_pnl_use_case_3 has pnl_daily, pnl_commission, pnl_trade
    # Use target_column to support all measures
    sql_query = f"""
        SELECT 
            COALESCE(SUM({target_column}), 0) as measure_value,
            0 as mtd_pnl,
            0 as ytd_pnl,
            0 as pytd_pnl
        FROM fact_pnl_use_case_3
        WHERE {sql_where}
    """
```

### Fix 2: Map Result to Correct Measure Key

**File:** `app/services/calculator.py` lines 140-148

**Change:**
```python
result = session.execute(text(sql_query)).fetchone()
measure_value = Decimal(str(result[0] or 0))

# Map measure_name to correct result key
if 'commission' in measure_name.lower():
    return {
        'daily': Decimal('0'),
        'mtd': measure_value,  # Commission goes to MTD
        'ytd': Decimal('0'),
        'pytd': Decimal('0'),
    }
elif 'trade' in measure_name.lower():
    return {
        'daily': Decimal('0'),
        'mtd': Decimal('0'),
        'ytd': measure_value,  # Trade goes to YTD
        'pytd': Decimal('0'),
    }
else:
    return {
        'daily': measure_value,  # Default: daily_pnl goes to daily
        'mtd': Decimal('0'),
        'ytd': Decimal('0'),
        'pytd': Decimal('0'),
    }
```

### Fix 3: Update Rule's measure_name (Database Fix)

**Action:** Update the rule to use the correct measure name format

**SQL:**
```sql
UPDATE metadata_rules
SET measure_name = 'daily_commission'
WHERE rule_id = 76
AND measure_name = 'pnl_commission';
```

**Reason:** The rule should store `'daily_commission'` (measure name), not `'pnl_commission'` (column name). The mapping function will convert it to `'pnl_commission'` when needed.

## 📝 Implementation Steps

1. **Fix the SQL query** to use `target_column` instead of hardcoding `pnl_daily`
2. **Fix the result mapping** to use the correct measure key based on `measure_name`
3. **Update the rule** in database to use `'daily_commission'` instead of `'pnl_commission'`
4. **Test** with the rule to verify it returns 50,000.51

## 🔍 Verification

After fix, verify:
```sql
-- Check rule measure_name
SELECT measure_name FROM metadata_rules WHERE rule_id = 76;
-- Expected: 'daily_commission'

-- Check actual data
SELECT SUM(pnl_commission) FROM fact_pnl_use_case_3 
WHERE strategy = 'Commissions (Non Swap)';
-- Expected: 50,000.51
```

