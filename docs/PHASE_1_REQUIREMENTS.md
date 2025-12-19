# Phase 1 Requirements: Core Engine & Data

## Phase Overview
Build the core calculation engine, generate mock data, and implement the **Discovery-First** workflow. This phase prioritizes a self-service model where users can immediately explore hierarchies with natural values before creating rules.

**Goal**: A working discovery interface that displays hierarchy with initial natural values (Daily, MTD, YTD) when a user selects a Use Case and Atlas Structure. The engine calculates natural rollups by default, showing the sum of underlying fact rows for every node.

**Success Criteria**: 
- Discovery Tab displays hierarchy with natural values immediately
- Engine processes 1,000 fact rows in < 5 seconds
- Mathematical validation passes (total fact = total root)
- Natural rollups calculated correctly for all measures (Daily, MTD, YTD)
- Hierarchy flattened in DB for performance (already in dim_hierarchy structure)

---

## Step 1.1: Database Setup & Initialization

### Requirements
1. **PostgreSQL Database Setup**
   - Create database: `finance_insight`
   - User: `finance_user` (or from .env)
   - Password: `finance_pass` (or from .env)
   - Port: `5432` (default)

2. **Alembic Migration Setup**
   - Initialize Alembic: `alembic init alembic`
   - Create initial migration from models
   - Migration should create all 6 tables:
     - `use_cases`
     - `use_case_runs`
     - `dim_hierarchy`
     - `metadata_rules`
     - `fact_pnl_gold`
     - `fact_calculated_results`

3. **Database Initialization Script**
   - Create `scripts/init_db.py`
   - Function to create database if not exists
   - Function to run migrations
   - Function to verify schema

### Deliverables
- ✅ Alembic configuration (`alembic.ini`, `alembic/env.py`)
- ✅ Initial migration file
- ✅ Database initialization script
- ✅ `.env.example` file with database connection template

### Testing
- Run `python scripts/init_db.py` successfully
- Verify all tables exist in PostgreSQL
- Verify foreign key constraints are in place

---

## Step 1.2: Mock Data Generation

### Requirements

1. **Create `app/engine/mock_data.py`**

2. **Generate Fact Data (`fact_pnl_gold`)**
   - Generate exactly **1,000 rows**
   - **Dimensions** (all VARCHAR(50)):
     - `account_id`: Use format "ACC_001" through "ACC_100" (10 accounts)
     - `cc_id`: Use format "CC_001" through "CC_050" (50 cost centers - these map to leaf nodes)
     - `book_id`: Use format "BOOK_01" through "BOOK_10" (10 books)
     - `strategy_id`: Use format "STRAT_01" through "STRAT_05" (5 strategies)
   - **Measures** (all NUMERIC(18,2)):
     - `daily_pnl`: Random between -100,000 and +100,000
     - `mtd_pnl`: Random between -500,000 and +500,000
     - `ytd_pnl`: Random between -2,000,000 and +2,000,000
     - `pytd_pnl`: Random between -1,800,000 and +1,800,000
   - **Trade Date**: Use dates from 2024-01-01 to 2024-12-31 (distribute randomly)
   - **UUID**: Generate unique `fact_id` for each row

3. **Generate Hierarchy (`dim_hierarchy`)**
   - Create a **ragged hierarchy** (varying depths: 3-5 levels)
   - **Structure**:
     ```
     ROOT
     ├── Region_A (depth=1)
     │   ├── Division_1 (depth=2)
     │   │   ├── CC_001 (leaf, depth=3)
     │   │   ├── CC_002 (leaf, depth=3)
     │   │   └── CC_003 (leaf, depth=3)
     │   └── Division_2 (depth=2)
     │       ├── CC_004 (leaf, depth=3)
     │       └── CC_005 (leaf, depth=3)
     ├── Region_B (depth=1)
     │   ├── Division_3 (depth=2)
     │   │   ├── Department_X (depth=3)
     │   │   │   ├── CC_006 (leaf, depth=4)
     │   │   │   └── CC_007 (leaf, depth=4)
     │   │   └── Department_Y (depth=3)
     │   │       └── CC_008 (leaf, depth=4)
     │   └── Division_4 (depth=2)
     │       └── CC_009 (leaf, depth=3)
     └── Region_C (depth=1)
         └── CC_010 (leaf, depth=2)  # Direct child of root
     ```
   - **Total nodes**: ~30-40 nodes
   - **Leaf nodes**: Exactly 50 (CC_001 through CC_050)
   - **Mapping**: Each `cc_id` in fact table must map to a leaf `node_id` in hierarchy
   - **Fields**:
     - `node_id`: VARCHAR (e.g., "ROOT", "Region_A", "CC_001")
     - `parent_node_id`: VARCHAR (NULL for root)
     - `node_name`: Human-readable name
     - `depth`: Integer (0 for root, incrementing)
     - `is_leaf`: Boolean (True only for CC_001 through CC_050)
     - `atlas_source`: "MOCK_ATLAS_v1"

4. **Data Loading Function**
   - Function `generate_and_load_mock_data(session)`
   - Clear existing data (optional flag)
   - Generate facts
   - Generate hierarchy
   - Bulk insert using SQLAlchemy
   - Return summary: counts, date ranges, value ranges

5. **Data Validation Function**
   - Verify all 50 cost centers have corresponding leaf nodes
   - Verify all fact rows have valid cc_id references
   - Verify hierarchy is a valid tree (no cycles, single root)
   - Verify all measures are within expected ranges

### Deliverables
- ✅ `app/engine/mock_data.py` with all functions
- ✅ Data generation script (`scripts/generate_mock_data.py`)
- ✅ Validation report showing:
  - Fact row count: 1,000
  - Hierarchy node count: ~30-40
  - Leaf node count: 50
  - All cc_id values mapped

### Testing
- Run data generation successfully
- Verify data integrity (all foreign keys valid)
- Verify hierarchy structure (can traverse from root to leaves)
- Verify fact-to-hierarchy mapping (all cc_id exist as leaf nodes)

---

## Step 1.3: Waterfall Engine Core

### Requirements

1. **Create `app/engine/waterfall.py`**

2. **Core Functions**

   **a. `load_hierarchy(session, use_case_id=None)`**
   - Load hierarchy from `dim_hierarchy` table
   - If `use_case_id` provided, filter by use case's atlas_structure_id
   - Return: Dictionary mapping `node_id` → node data
   - Return: Dictionary mapping `parent_node_id` → list of children
   - Return: List of leaf nodes

   **b. `load_facts(session, filters=None)`**
   - Load fact data from `fact_pnl_gold`
   - Optional filters (dict): `{account_id: [...], cc_id: [...], etc.}`
   - Return: Pandas DataFrame with all fact rows
   - Use decimal-safe types (ensure NUMERIC precision)

   **c. `calculate_natural_rollup(hierarchy, facts)`**
   - **Bottom-Up Aggregation**:
     - Start with leaf nodes
     - For each leaf: Sum fact rows where `fact.cc_id = node.node_id`
     - For each parent: Sum all immediate children's values
     - Recursively aggregate up the tree
   - **Measures**: Process all 4 measures independently:
     - `daily_pnl`, `mtd_pnl`, `ytd_pnl`, `pytd_pnl`
   - **Return**: Dictionary `{node_id: {daily: X, mtd: Y, ytd: Z, pytd: W}}`
   - **Use Pandas**: Set-based operations (groupby, sum) - NO row-by-row loops

   **d. `load_rules(session, use_case_id)`**
   - Load all rules for a use case from `metadata_rules`
   - Return: Dictionary `{node_id: rule_object}`
   - Validate: Only one rule per node (enforced by DB constraint)

   **e. `apply_rule_override(facts, rule)`**
   - Execute SQL WHERE clause: `SELECT SUM(measure) FROM facts WHERE [sql_where]`
   - Apply to ALL measures simultaneously
   - Return: Dictionary `{daily: X, mtd: Y, ytd: Z, pytd: W}`
   - Handle empty results (return zeros)

   **f. `calculate_waterfall(use_case_id, session, triggered_by=None)`**
   - **Main Orchestration Function**:
     1. **Start timer**: Record start time for performance monitoring
     2. Load hierarchy
     3. Load facts
     4. Calculate natural rollups (bottom-up) - **using Decimal library**
     5. Load rules for use case
     6. For each node with a rule (top-down):
        - Apply rule override - **using Decimal library**
        - Replace natural value with override
     7. Calculate reconciliation plugs:
        - For each node with override:
          - `plug = override_value - sum(children_natural_values)` - **using Decimal**
          - Calculate for each measure independently
     8. **End timer**: Calculate duration in milliseconds
     9. Return results dictionary with timing information
   - **Performance Tracking**: Store `calculation_duration_ms` and `triggered_by` in run record

   **g. `save_results(run_id, results, session)`**
   - Create `FactCalculatedResult` rows for each node
   - Format:
     - `measure_vector`: `{daily: X, mtd: Y, ytd: Z, pytd: W}`
     - `plug_vector`: `{daily: X, mtd: Y, ytd: Z, pytd: W}` or NULL if no override
     - `is_override`: True if node has a rule
     - `is_reconciled`: True if plug is zero (or within tolerance)
   - Bulk insert using SQLAlchemy

3. **Performance Requirements**
   - Process 1,000 fact rows in < 5 seconds
   - Use Pandas vectorized operations
   - Minimize database round trips
   - Use bulk inserts

4. **Decimal Safety - CRITICAL**
   - **MUST use Python `decimal.Decimal` library for all aggregations**
   - Import: `from decimal import Decimal`
   - Convert all P&L values to Decimal before calculations
   - Use `Decimal()` constructor for all numeric operations
   - **NO float-based math** - Standard float arithmetic introduces rounding errors at 10th decimal place
   - This is essential for "Plug" calculations to pass 100% tie-out checks
   - Pandas operations: Use `dtype='object'` with Decimal or convert to Decimal after operations
   - Example: `df['daily_pnl'] = df['daily_pnl'].apply(Decimal)`

### Deliverables
- ✅ `app/engine/waterfall.py` with all functions
- ✅ Unit tests for each function
- ✅ Performance benchmark (1,000 rows processed in < 5s)

### Testing
- Test natural rollup: Root total = Sum of all fact rows
- Test rule override: Override value replaces natural value
- Test plug calculation: Plug = Override - Sum(Children Natural)
- Test multi-measure: All 4 measures calculated correctly
- Test edge cases: Empty hierarchy, no rules, single node

---

## Step 1.4: Mathematical Validation

### Requirements

1. **Create `app/engine/validation.py`**

2. **Validation Functions**

   **a. `validate_root_reconciliation(results, facts)`**
   - Root node's natural rollup = Sum of all fact rows
   - Check all 4 measures independently
   - Tolerance: ±0.01 (rounding errors)
   - Return: `{measure: {expected: X, actual: Y, difference: Z, passed: bool}}`

   **b. `validate_plug_sum(results)`**
   - Sum of all plugs should be zero (or explain difference)
   - Check all 4 measures independently
   - Return: Validation report

   **c. `validate_hierarchy_integrity(hierarchy)`**
   - Single root node (no parent)
   - No cycles in tree
   - All nodes reachable from root
   - All leaf nodes have valid fact mappings

   **d. `validate_rule_application(results, rules)`**
   - All nodes with rules have `is_override = True`
   - Override values match rule execution results
   - Plugs calculated only for override nodes

   **e. `validate_completeness(facts, hierarchy, results)`**
   - **The "Orphan" Check - CRITICAL**
   - Validate: `SUM(fact_pnl_gold)` equals `SUM(leaf_nodes in report)`
   - Calculate delta: `delta = SUM(facts) - SUM(leaf_nodes)`
   - If delta != 0 (within tolerance):
     - Automatically assign delta to a special `NODE_ORPHAN` node
     - Create orphan node in results if it doesn't exist
     - This ensures report always ties to source data
     - Orphan node represents fact rows not mapped to any hierarchy leaf
   - Check all 4 measures independently
   - Return: Validation result with orphan assignment details

   **f. `run_full_validation(use_case_id, session)`**
   - Run all validations including completeness check
   - Generate comprehensive report
   - Return: Validation result object with orphan node details

3. **Test Cases**
   - Create test use case with known data
   - Add test rules
   - Run calculation
   - Run validation
   - Verify all checks pass

### Deliverables
- ✅ `app/engine/validation.py` with all validation functions
- ✅ Validation test suite
- ✅ Sample validation report output

### Testing
- All validation functions pass with mock data
- Validation catches intentional errors (test with bad data)
- Validation report is human-readable

---

## Step 1.6: Discovery Tab API (Priority)

### Requirements

**Discovery-First Workflow**: Users can immediately explore hierarchies with natural values before creating rules.

1. **Create `app/api/routes/discovery.py`** (Basic FastAPI endpoint)

2. **Discovery Endpoint**

   **`GET /api/v1/use-cases/{use_case_id}/discovery`**
   - Get hierarchy with natural values for discovery view
   - **No rules applied** - pure natural rollups
   - Returns tree structure with:
     - Node hierarchy (parent-child relationships)
     - Natural values for Daily, MTD, YTD measures
     - Node metadata (name, depth, is_leaf)
   - Response format: Nested tree structure suitable for AG-Grid Tree Data

3. **Natural Values Calculation**
   - Call `calculate_natural_rollup()` from waterfall engine
   - **No rules** - just bottom-up aggregation
   - Calculate for Daily, MTD, YTD (PYTD optional for discovery)
   - Return immediately (no run_id needed - this is live discovery)

4. **Response Schema**
   ```json
   {
     "use_case_id": "uuid",
     "hierarchy": [
       {
         "node_id": "ROOT",
         "node_name": "Root",
         "parent_node_id": null,
         "depth": 0,
         "is_leaf": false,
         "daily_pnl": "1234567.89",
         "mtd_pnl": "12345678.90",
         "ytd_pnl": "123456789.01",
         "children": [...]
       }
     ]
   }
   ```

5. **Performance**
   - Cache natural rollups if use case hasn't changed
   - Return in < 2 seconds for discovery view
   - Use flattened hierarchy from DB (already optimized)

### Deliverables
- ✅ Discovery API endpoint
- ✅ Natural rollup calculation (no rules)
- ✅ Tree structure response format
- ✅ Fast response time for exploration

### Testing
- Call discovery endpoint successfully
- Verify natural values match fact table sums
- Verify tree structure is correct
- Verify performance < 2 seconds

---

## Step 1.5: Integration & CLI

### Requirements

1. **Create `scripts/run_calculation.py`**
   - CLI script to run waterfall calculation
   - Arguments:
     - `--use-case-id`: UUID of use case
     - `--version-tag`: Version tag for run
   - Steps:
     1. Create use case run record
     2. Run waterfall calculation
     3. Save results
     4. Run validation
     5. Update run status
     6. Print summary

2. **Create Test Use Case**
   - Script to create a test use case
   - Link to mock hierarchy
   - Add sample rules (for testing)

### Deliverables
- ✅ CLI script for running calculations
- ✅ Test use case creation script
- ✅ End-to-end test: Generate data → Create use case → Calculate → Validate

### Testing
- Run full workflow from command line
- Verify results in database
- Verify validation passes

---

## Phase 1 Acceptance Criteria

✅ **Database**: All tables created, migrations working  
✅ **Mock Data**: 1,000 fact rows + ragged hierarchy generated and loaded  
✅ **Waterfall Engine**: Processes data, calculates natural rollups, applies rules, calculates plugs  
✅ **Discovery API**: Endpoint returns hierarchy with natural values immediately  
✅ **Validation**: Mathematical integrity verified  
✅ **Performance**: < 5 seconds for 1,000 rows, < 2 seconds for discovery view  
✅ **CLI**: Can run calculations from command line  

## Phase 1 Deliverables Summary

1. Database schema (Alembic migrations)
2. Mock data generator (`app/engine/mock_data.py`)
3. Waterfall engine (`app/engine/waterfall.py`) - with natural rollup calculation
4. **Discovery API** (`app/api/routes/discovery.py`) - **Priority: Discovery-First**
5. Validation suite (`app/engine/validation.py`)
6. CLI tools (`scripts/`)
7. Test suite and documentation

## Discovery-First User Journey

1. User selects Use Case
2. User selects Atlas Structure (imports hierarchy)
3. **Discovery Tab displays immediately**:
   - Hierarchy tree with natural values
   - Daily, MTD, YTD measures shown
   - No rules applied - pure natural rollups
   - User can explore and understand data before creating rules
4. User can then proceed to create rules (Phase 2)

## Dependencies

- PostgreSQL database running
- Python 3.9+
- All packages from `requirements.txt` installed

## Next Phase

Once Phase 1 is complete and validated, we proceed to **Phase 2: Backend API & GenAI** to expose the engine via REST API and add GenAI rule generation.

