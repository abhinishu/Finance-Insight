# Database Design: Finance-Insight (PostgreSQL)

## 1. Core Use Case & Governance
- `use_cases`:
    - `use_case_id` (UUID, PK)
    - `name` (VARCHAR)
    - `description` (TEXT)
    - `owner_id` (VARCHAR)
    - `atlas_structure_id` (VARCHAR) -- Reference to the Atlas tree used
    - `status` (Enum: DRAFT, ACTIVE, ARCHIVED)
    - `created_at` (TIMESTAMP)

- `use_case_runs`:
    - `run_id` (UUID, PK)
    - `use_case_id` (FK)
    - `version_tag` (VARCHAR) -- e.g., "Nov_Actuals_v1"
    - `run_timestamp` (TIMESTAMP)
    - `parameters_snapshot` (JSONB) -- Snapshots the rules used for this specific run

## 2. Structure & Hierarchy
- `dim_hierarchy`:
    - `node_id` (VARCHAR, PK)
    - `parent_node_id` (VARCHAR, FK -> node_id)
    - `node_name` (VARCHAR)
    - `depth` (INT)
    - `is_leaf` (BOOLEAN)
    - `atlas_source` (VARCHAR) -- To track which Atlas version this came from

## 3. Rules & Overlays
- `metadata_rules`:
    - `rule_id` (SERIAL, PK)
    - `use_case_id` (FK)
    - `node_id` (VARCHAR, FK)
    - `predicate_json` (JSONB) -- For UI state
    - `sql_where` (TEXT) -- For execution
    - `logic_en` (TEXT) -- For auditability
    - `last_modified_by` (VARCHAR)

## 4. Fact & Results
- `fact_pnl_gold`:
    - `account_id`, `cc_id`, `book_id`, `strategy_id` (Dimensions)
    - `daily_pnl`, `mtd_pnl`, `ytd_pnl`, `pytd_pnl` (Measures, Numeric 18,2)
    - `trade_date` (DATE)

- `fact_calculated_results`:
    - `run_id` (FK)
    - `node_id` (VARCHAR)
    - `measure_vector` (JSONB) -- Stores {daily: X, mtd: Y, ytd: Z}
    - `is_override` (BOOLEAN)
    - `plug_value` (NUMERIC) -- The difference calculated for this node