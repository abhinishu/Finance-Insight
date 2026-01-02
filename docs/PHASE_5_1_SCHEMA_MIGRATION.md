# Phase 5.1: Database Schema Foundation - Migration Guide

**Date:** 2026-01-01  
**Migration:** 007  
**Status:** ✅ Ready for Execution

---

## Overview

This migration implements the database schema foundation for Phase 5, enabling:
- **Rule Type System:** Support for Type 1, Type 2, Type 2B, and Type 3 rules
- **Table-Per-Use-Case Strategy:** Each use case can have its own input table
- **Use Case 3 Support:** Dedicated table for "America Cash Equity Trading" data

---

## Migration File

**File:** `migration_007_phase5_schema.sql`

**Location:** Project root

---

## Changes Summary

### 1. `metadata_rules` Table Updates

**New Columns:**
- `rule_type` (VARCHAR(20), DEFAULT 'FILTER')
  - Values: `'FILTER'` (Type 1/2), `'FILTER_ARITHMETIC'` (Type 2B), `'NODE_ARITHMETIC'` (Type 3)
- `measure_name` (VARCHAR(50), DEFAULT 'daily_pnl')
  - Values: `'daily_pnl'`, `'daily_commission'`, `'daily_trade'`, etc.
- `rule_expression` (TEXT, nullable)
  - Stores arithmetic expressions for Type 3 rules (e.g., `"NODE_3 - NODE_4"`)
- `rule_dependencies` (JSONB, nullable)
  - Stores list of node IDs this rule depends on (e.g., `["NODE_3", "NODE_4"]`)

**Backward Compatibility:**
- ✅ All columns are nullable
- ✅ Default values set for existing rows
- ✅ Existing rules continue to work (default to `rule_type='FILTER'`)

---

### 2. `use_cases` Table Updates

**New Column:**
- `input_table_name` (VARCHAR(100), nullable)
  - Values: `NULL` (use default `fact_pnl_gold`), `'fact_pnl_use_case_3'`, etc.

**Backward Compatibility:**
- ✅ Column is nullable
- ✅ Existing use cases continue to use `fact_pnl_gold` (NULL = default)

---

### 3. `fact_pnl_use_case_3` Table Creation

**Purpose:** Dedicated storage for "America Cash Equity Trading" use case data

**Columns:**
- **Primary Key:** `entry_id` (UUID)
- **Temporal:** `effective_date` (DATE, NOT NULL)
- **Dimensions:**
  - `cost_center` (VARCHAR(50))
  - `division` (VARCHAR(50))
  - `business_area` (VARCHAR(100))
  - `product_line` (VARCHAR(100))
  - `strategy` (VARCHAR(100))
  - `process_1` (VARCHAR(100))
  - `process_2` (VARCHAR(100))
  - `book` (VARCHAR(100))
- **Measures (CRITICAL: NUMERIC(18,2)):**
  - `pnl_daily` (NUMERIC(18,2), DEFAULT 0)
  - `pnl_commission` (NUMERIC(18,2), DEFAULT 0)
  - `pnl_trade` (NUMERIC(18,2), DEFAULT 0)
- **Audit:** `created_at` (TIMESTAMP)

**Indices:**
- `idx_fact_pnl_uc3_effective_date` (on `effective_date`)
- `idx_fact_pnl_uc3_strategy` (on `strategy`)
- `idx_fact_pnl_uc3_process_2` (on `process_2`)
- `idx_fact_pnl_uc3_strategy_process2` (composite: `strategy`, `process_2`)
- `idx_fact_pnl_uc3_date_strategy` (composite: `effective_date`, `strategy`)

**Decimal Precision Compliance:**
- ✅ All PnL columns use `NUMERIC(18,2)` (not FLOAT/REAL)
- ✅ Maintains penny-perfect accuracy

---

## Execution Instructions

### Step 1: Backup Database (Recommended)

```bash
# Create backup before migration
pg_dump -U your_user -d finance_insight > backup_before_phase5_1.sql
```

### Step 2: Run Migration

**Option A: Using psql**
```bash
psql -U your_user -d finance_insight -f migration_007_phase5_schema.sql
```

**Option B: Using Python**
```python
from app.database import get_database_url, create_db_engine
from sqlalchemy import text

engine = create_db_engine()
with engine.connect() as conn:
    with open('migration_007_phase5_schema.sql', 'r') as f:
        sql = f.read()
    conn.execute(text(sql))
    conn.commit()
```

### Step 3: Verify Migration

```bash
python scripts/verify_phase5_schema.py
```

**Expected Output:**
```
✅ Schema Validation Passed
All Phase 5.1 schema changes are correctly applied.
```

---

## Verification Script

**File:** `scripts/verify_phase5_schema.py`

**Checks:**
1. ✅ `fact_pnl_use_case_3` table exists
2. ✅ All PnL columns use `NUMERIC(18,2)` (not FLOAT/REAL)
3. ✅ `metadata_rules` has new columns (`rule_type`, `measure_name`, `rule_expression`, `rule_dependencies`)
4. ✅ `use_cases` has new column (`input_table_name`)
5. ✅ Required indices exist

**CRITICAL:** Script will **FAIL** if any PnL column uses FLOAT/REAL (violates Decimal precision policy).

---

## Rollback Instructions

If migration needs to be rolled back:

```sql
BEGIN;

-- Drop fact_pnl_use_case_3 table
DROP TABLE IF EXISTS fact_pnl_use_case_3 CASCADE;

-- Remove columns from metadata_rules
ALTER TABLE metadata_rules DROP COLUMN IF EXISTS rule_type;
ALTER TABLE metadata_rules DROP COLUMN IF EXISTS rule_dependencies;
ALTER TABLE metadata_rules DROP COLUMN IF EXISTS rule_expression;
ALTER TABLE metadata_rules DROP COLUMN IF EXISTS measure_name;

-- Remove column from use_cases
ALTER TABLE use_cases DROP COLUMN IF EXISTS input_table_name;

COMMIT;
```

**⚠️ WARNING:** Rollback will delete all data in `fact_pnl_use_case_3` table.

---

## Testing Checklist

After migration, verify:

- [ ] Migration runs without errors
- [ ] Verification script passes
- [ ] Existing use cases still work (backward compatibility)
- [ ] Existing rules still work (default to `rule_type='FILTER'`)
- [ ] Can insert data into `fact_pnl_use_case_3`
- [ ] PnL columns accept Decimal values correctly
- [ ] Indices improve query performance

---

## Next Steps

After successful migration:

1. **Phase 5.2:** Create seed scripts for Use Case 3 structure and rules
2. **Update Models:** Update SQLAlchemy models in `app/models.py` (if needed)
3. **Update Engine:** Update waterfall engine to support `input_table_name`

---

## Compliance Status

✅ **Decimal Precision Policy:** All PnL columns use `NUMERIC(18,2)`  
✅ **Backward Compatibility:** All new columns are nullable with defaults  
✅ **Table-Per-Use-Case:** `input_table_name` enables flexible input sources  
✅ **Rule Type System:** New columns support Type 1, 2, 2B, and 3 rules

---

**Migration Status:** ✅ Ready for Execution  
**Verification:** ✅ Script Available  
**Rollback:** ✅ Instructions Provided

