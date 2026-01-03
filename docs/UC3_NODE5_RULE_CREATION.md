# Use Case 3 - NODE_5 Rule Creation Summary

## ✅ Rule Created Successfully

**Date:** 2026-01-XX  
**Task:** Create a new business rule for Use Case 3, Node NODE_5 (Commissions) to test the new table configuration.

---

## Rule Details

| Field | Value |
|-------|-------|
| **Rule ID** | 70 |
| **Use Case** | America Cash Equity Trading |
| **Use Case ID** | `fce60983-0328-496b-b6e1-34249ec5aa5a` |
| **Node ID** | NODE_5 |
| **Node Name** | Commissions (Non Swap) |
| **Rule Type** | FILTER |
| **Measure Name** | `pnl_commission` |
| **SQL WHERE** | `strategy = 'CORE'` |
| **Logic (English)** | `strategy equals 'CORE'` |
| **Last Modified By** | system |

---

## ✅ Column Name Verification

**CRITICAL:** The rule uses the correct column name `strategy` (NOT `strategy_id`).

- ✅ **Correct:** `strategy = 'CORE'` 
- ❌ **Incorrect:** `strategy_id = 'CORE'` (would fail on `fact_pnl_use_case_3`)

This matches the `fact_pnl_use_case_3` table schema:
- Column: `strategy` (String)
- Column: `pnl_commission` (Numeric)

---

## SQL Command Executed

```sql
INSERT INTO metadata_rules (
    use_case_id,
    node_id,
    rule_type,
    sql_where,
    measure_name,
    logic_en,
    last_modified_by
) VALUES (
    'fce60983-0328-496b-b6e1-34249ec5aa5a',
    'NODE_5',
    'FILTER',
    'strategy = ''CORE''',
    'pnl_commission',
    'strategy equals ''CORE''',
    'system'
);
```

**Note:** The SQL uses double single quotes (`''`) to escape the single quote in the string literal `'CORE'`.

---

## Expected Behavior

When this rule is executed during calculation:

1. **Table:** `fact_pnl_use_case_3`
2. **Measure Column:** `pnl_commission`
3. **Filter:** `WHERE strategy = 'CORE'`
4. **Result:** Sum of `pnl_commission` for all rows where `strategy = 'CORE'`

The calculation engine will:
- Query: `SELECT COALESCE(SUM(pnl_commission), 0) FROM fact_pnl_use_case_3 WHERE strategy = 'CORE'`
- Apply the result to Node NODE_5 (Commissions)

---

## Testing

To test this rule:

1. Navigate to **Tab 3 (Rule Editor)** in the UI
2. Select Use Case: **"America Cash Equity Trading"**
3. Find Node **NODE_5** in the hierarchy
4. Verify the rule badge (fx icon) appears next to NODE_5
5. Click **"Execute Business Rules"**
6. Check the results in **Tab 4 (Executive Dashboard)**
7. Verify NODE_5 shows the sum of `pnl_commission` for `strategy = 'CORE'`

---

## Related Fixes

- **Rule 4:** Fixed `strategy_id` → `strategy` for "America Trading P&L" use case
- **Table Routing:** Updated `apply_rule_to_leaf()` to dynamically select `fact_pnl_use_case_3` for Use Case 3
- **Column Mapping:** Implemented `get_measure_column_name()` to map `pnl_commission` → `pnl_commission` for UC3

---

## Status

✅ **COMPLETE** - Rule created and verified with correct column names.

