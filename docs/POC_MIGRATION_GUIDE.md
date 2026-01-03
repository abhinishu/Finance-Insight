# POC Migration Guide: Laptop Dev → Office POC

## Overview

This guide describes the "Clean Slate" deployment strategy for migrating the Finance-Insight application from a Laptop Dev Environment to an Office POC Environment.

## Migration Strategy

The migration uses a **three-step process**:
1. **Export** data from Laptop Dev to portable JSON files
2. **Recreate** schema in Office POC using SQLAlchemy models
3. **Reload** data from JSON files

## Prerequisites

### 1. Model Verification

**CRITICAL:** Before running the migration scripts, verify that your SQLAlchemy models include all required columns:

#### FactPnlUseCase3 Model (`app/models.py`)
- ✅ `process_1` (Column(String(100), nullable=True))
- ✅ `process_2` (Column(String(100), nullable=True))

#### MetadataRule Model (`app/models.py`)
- ✅ `predicate_json` (Column(JSONB))

**Why this matters:** The `create_all()` function in `init_office_poc.py` relies on these class definitions to create the database schema. If columns are missing from the models, they will not be created in the database.

### 2. Database Access

Ensure you have:
- **Laptop Dev:** Read access to source database
- **Office POC:** Write access to target database (with schema creation permissions)

### 3. Environment Variables

Set `DATABASE_URL` environment variable to point to the correct database:
- **Laptop Dev:** `export DATABASE_URL="postgresql://user:pass@localhost:5432/finance_insight"`
- **Office POC:** `export DATABASE_URL="postgresql://user:pass@office-server:5432/finance_insight_poc"`

## Step 1: Export Data from Laptop Dev

Run the export script on your **Laptop Dev** environment:

```bash
python scripts/export_poc_data.py
```

**What it does:**
- Connects to the Laptop Dev database
- Exports the following tables to JSON files:
  - `use_cases`
  - `dim_hierarchy`
  - `fact_pnl_use_case_3`
  - `metadata_rules` (with `predicate_json` JSONB column properly handled)
- Saves files to `app/data_seed/` directory

**Output:**
```
app/data_seed/
├── use_cases.json
├── dim_hierarchy.json
├── fact_pnl_use_case_3.json
└── metadata_rules.json
```

**Features:**
- ✅ Handles UUID, Decimal, datetime, and JSONB types correctly
- ✅ Preserves nested structures (like `predicate_json`) without escaping issues
- ✅ Uses JSON format (not CSV) to ensure data integrity

## Step 2: Transfer Files to Office POC

Copy the `app/data_seed/` directory to the Office POC environment:

```bash
# Option 1: Using SCP
scp -r app/data_seed/ user@office-server:/path/to/Finance-Insight/app/

# Option 2: Using Git (if using version control)
git add app/data_seed/
git commit -m "Export POC data for migration"
git push
# Then pull on Office POC server
```

## Step 3: Initialize Office POC Database

Run the initialization script on your **Office POC** environment:

### Option A: Clean Slate (Recommended for first deployment)

```bash
python scripts/init_office_poc.py --reset
```

**What it does:**
1. **Drops all existing tables** (clean slate)
2. **Creates schema** from SQLAlchemy models (`Base.metadata.create_all()`)
3. **Loads data** from JSON files in dependency order:
   - `use_cases` (no dependencies)
   - `dim_hierarchy` (no dependencies)
   - `fact_pnl_use_case_3` (no dependencies)
   - `metadata_rules` (depends on use_cases and dim_hierarchy)

### Option B: Incremental Update (Skip existing rows)

```bash
python scripts/init_office_poc.py
```

**What it does:**
1. **Creates schema** if tables don't exist
2. **Loads data** from JSON files
3. **Skips rows** that already exist (by primary key) - idempotent operation

## Data Loading Order

The script loads data in the correct order to satisfy foreign key constraints:

1. **use_cases** → No dependencies
2. **dim_hierarchy** → No dependencies on exported tables
3. **fact_pnl_use_case_3** → No dependencies on exported tables
4. **metadata_rules** → Depends on `use_cases.use_case_id` and `dim_hierarchy.node_id`

## Error Handling

### Common Issues

1. **Missing JSON files:**
   - **Error:** `File not found: app/data_seed/use_cases.json`
   - **Solution:** Run `export_poc_data.py` first on Laptop Dev

2. **Foreign Key Violations:**
   - **Error:** `insert or update on table "metadata_rules" violates foreign key constraint`
   - **Solution:** Ensure data is loaded in the correct order (script handles this automatically)

3. **Missing Model Columns:**
   - **Error:** Column not found in database after `create_all()`
   - **Solution:** Verify models include all required columns (see Prerequisites)

4. **Duplicate Key Violations:**
   - **Behavior:** Script skips existing rows (idempotent)
   - **Solution:** Use `--reset` flag for clean slate, or manually delete conflicting rows

## Verification

After initialization, verify the data:

```sql
-- Check row counts
SELECT 'use_cases' as table_name, COUNT(*) as row_count FROM use_cases
UNION ALL
SELECT 'dim_hierarchy', COUNT(*) FROM dim_hierarchy
UNION ALL
SELECT 'fact_pnl_use_case_3', COUNT(*) FROM fact_pnl_use_case_3
UNION ALL
SELECT 'metadata_rules', COUNT(*) FROM metadata_rules;

-- Verify predicate_json is loaded correctly
SELECT rule_id, predicate_json FROM metadata_rules WHERE predicate_json IS NOT NULL LIMIT 5;

-- Verify process_1 and process_2 columns exist
SELECT process_1, process_2 FROM fact_pnl_use_case_3 LIMIT 5;
```

## Rollback Plan

If something goes wrong:

1. **Backup Office POC database** before running `--reset`:
   ```bash
   pg_dump -h office-server -U user -d finance_insight_poc > backup_$(date +%Y%m%d).sql
   ```

2. **Restore from backup:**
   ```bash
   psql -h office-server -U user -d finance_insight_poc < backup_YYYYMMDD.sql
   ```

## Scripts Reference

### `scripts/export_poc_data.py`
- **Purpose:** Export database to JSON files
- **Input:** Laptop Dev database
- **Output:** `app/data_seed/*.json` files
- **Dependencies:** None

### `scripts/init_office_poc.py`
- **Purpose:** Initialize Office POC database
- **Input:** `app/data_seed/*.json` files
- **Output:** Populated Office POC database
- **Flags:**
  - `--reset`: Drop all tables before creating schema (clean slate)
  - `--data-dir`: Custom directory for JSON files (default: `app/data_seed`)

## Next Steps

After successful migration:

1. **Test the application:**
   - Verify all use cases are accessible
   - Run a test calculation
   - Check that rules are applied correctly

2. **Update configuration:**
   - Update `DATABASE_URL` in `.env` file
   - Verify API endpoints are working

3. **Document any issues:**
   - Note any data discrepancies
   - Report missing columns or data

## Support

For issues or questions:
1. Check the logs from both scripts
2. Verify model definitions match database schema
3. Ensure JSON files are valid and complete

