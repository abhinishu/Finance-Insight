# Step 4.2 Complete: Schema Patch, Orchestrator Service, and Versioned Runs

## ✅ Completed Tasks

### 1. Schema Patch (Alembic Migration)
- ✅ Created migration `aa275d79876c_step_4_2_schema_patch_calculation_runs_and_explicit_measures`
- ✅ Updated `fact_pnl_entries` to include explicit columns:
  - `daily_amount` (Numeric 18,2) - Explicit daily measure
  - `wtd_amount` (Numeric 18,2) - Week-to-date measure
  - `ytd_amount` (Numeric 18,2) - Year-to-date measure
  - Kept `amount` column for backward compatibility
- ✅ Created `calculation_runs` table (Header for temporal versioning):
  - `id` (UUID, primary key)
  - `pnl_date` (Date) - COB date anchor
  - `use_case_id` (UUID, FK with CASCADE)
  - `run_name` (String 200) - e.g., "Initial Run", "Adjusted v2"
  - `executed_at` (Timestamp)
  - `status` (String 20) - IN_PROGRESS, COMPLETED, FAILED
  - `triggered_by` (String 100)
  - `calculation_duration_ms` (Integer)
- ✅ Updated `fact_calculated_results` to link to `calculation_runs.id`:
  - Added `calculation_run_id` (UUID, FK with CASCADE)
  - Kept `run_id` (nullable) for backward compatibility during transition
- ✅ Created indexes for performance:
  - `ix_calculation_runs_pnl_date`
  - `ix_calculation_runs_use_case_id`
  - `ix_calculation_runs_date_use_case` (composite)
  - `ix_fact_calculated_results_calc_run_id`

### 2. Snapshot Orchestrator Service
- ✅ Created `app/services/orchestrator.py` with:
  - `create_snapshot()`: Main orchestrator function
    - Accepts `use_case_id` and `pnl_date`
    - Creates entry in `calculation_runs`
    - Fetches facts for that date/use-case (ACTUAL and PRIOR scenarios)
    - Applies Business Rules to daily, wtd, and ytd measures
    - Computes Variance for all three measures (ACTUAL - PRIOR)
    - Bulk-inserts results into `fact_calculated_results`
  - `load_facts_for_date()`: Loads facts from `fact_pnl_entries` by date and scenario
  - `calculate_variance()`: Computes variance between ACTUAL and PRIOR
  - `calculate_natural_rollup_from_entries()`: Aggregates from fact_pnl_entries
  - `apply_rules_to_results()`: Applies rules with "Most Specific Wins" policy
  - `save_calculation_results()`: Bulk-inserts results

### 3. Summary Deletion API
- ✅ Enhanced `DELETE /api/v1/admin/use-case/{id}`:
  - Counts Rules before deletion
  - Counts Legacy Runs (`use_case_runs`) before deletion
  - Counts Calculation Runs (`calculation_runs`) before deletion
  - Counts Facts (`fact_pnl_entries`) before deletion
  - Returns comprehensive summary:
    ```json
    {
      "deleted_use_case": "uuid",
      "rules_purged": X,
      "legacy_runs_purged": Y,
      "calculation_runs_purged": Z,
      "facts_purged": W,
      "total_items_deleted": X+Y+Z+W,
      "message": "..."
    }
    ```

### 4. API for UI Date Selection
- ✅ Created `GET /api/v1/runs`:
  - Query parameters: `pnl_date` (optional), `use_case_id` (optional)
  - Returns list of calculation runs for date selection
  - Supports filtering by:
    - Date only: All runs for that date
    - Use case only: All runs for that use case
    - Both: Runs for specific date and use case
    - Neither: All runs (limited to 100)
  - Response format:
    ```json
    {
      "runs": [
        {
          "id": "uuid",
          "pnl_date": "2025-12-24",
          "run_name": "Initial Run",
          "executed_at": "2025-12-24T09:00:00",
          "status": "COMPLETED",
          "triggered_by": "user123",
          "duration_ms": 1250
        }
      ],
      "total": 1,
      "filters": {...}
    }
    ```
- ✅ Created `GET /api/v1/runs/{run_id}`:
  - Returns detailed information about a specific calculation run
  - Includes results count

## 📋 Files Created/Modified

### New Files
1. **`app/services/orchestrator.py`** - Snapshot Orchestrator service
2. **`app/api/routes/runs.py`** - Runs API for UI date selection
3. **`alembic/versions/aa275d79876c_step_4_2_schema_patch_calculation_runs_and_explicit_measures.py`** - Schema migration

### Modified Files
1. **`app/models.py`**:
   - Updated `FactPnlEntries` with `daily_amount`, `wtd_amount`, `ytd_amount`
   - Added `CalculationRun` model
   - Updated `FactCalculatedResult` with `calculation_run_id`

2. **`app/api/routes/admin.py`**:
   - Enhanced `DELETE /api/v1/admin/use-case/{id}` with comprehensive counts

3. **`app/main.py`**:
   - Added `runs` router import and registration

## 🎯 Architectural Pattern: Temporal Versioning

The system now implements the **"Temporal Versioning" Pattern**:

### Header-Detail Relationship
- **`calculation_runs` (Header)**: Stores execution metadata per PNL_DATE
- **`fact_calculated_results` (Detail)**: Stores actual financial rows linked to run_id

### UI Flow
1. User selects Date (e.g., 2025-12-24)
2. API returns Runs: `[Run 1: 09:00 AM, Run 2: 10:30 AM (Adjusted)]`
3. User selects Run 2, and the dashboard populates

### Key Benefits
- **Trial Analysis**: Users can compare different rule versions for the same date
- **Immutable Runs**: Once executed, run data is never modified; new runs are created for changes
- **Date-Aware UI**: All reporting is anchored to COB (Close of Business) date
- **Version Control**: Multiple runs per date enable "what-if" analysis

## 🚀 Usage

### 1. Run Migration
```powershell
alembic upgrade head
```

### 2. Create Snapshot (Orchestrator)
```python
from app.services.orchestrator import create_snapshot
from datetime import date
from uuid import UUID

result = create_snapshot(
    use_case_id=UUID("..."),
    pnl_date=date(2025, 12, 24),
    session=db_session,
    run_name="Initial Run",
    triggered_by="user123"
)
```

### 3. Get Runs for Date Selection
```powershell
# Get runs for a specific date and use case
GET /api/v1/runs?pnl_date=2025-12-24&use_case_id={uuid}

# Get all runs for a date
GET /api/v1/runs?pnl_date=2025-12-24

# Get all runs for a use case
GET /api/v1/runs?use_case_id={uuid}
```

### 4. Delete Use Case (with Summary)
```powershell
DELETE /api/v1/admin/use-case/{uuid}
# Returns comprehensive summary of purged data
```

## ✅ Verification Checklist

- [x] Schema patch migration created and tested
- [x] `fact_pnl_entries` has explicit daily/wtd/ytd columns
- [x] `calculation_runs` table created with proper indexes
- [x] `fact_calculated_results` links to `calculation_runs`
- [x] Snapshot Orchestrator service implemented
- [x] Orchestrator supports ACTUAL and PRIOR scenarios
- [x] Variance calculation implemented
- [x] DELETE API enhanced with comprehensive counts
- [x] GET /api/v1/runs API for UI date selection
- [x] All models updated with new relationships

## 🎯 Goal Achievement

**Version-Controlled, Date-Anchored Reporting Engine**: The backend now supports:
1. ✅ Date-anchored calculation runs (PNL_DATE as primary filter)
2. ✅ Multiple runs per date for "Trial Analysis"
3. ✅ Explicit measure columns (daily, wtd, ytd) for cleaner SQL
4. ✅ ACTUAL vs PRIOR scenario support with variance calculation
5. ✅ Immutable runs (new runs for changes, never modify existing)
6. ✅ UI-ready APIs for date and run selection

The system is ready for the UI to implement date-aware, version-controlled reporting workflows.




