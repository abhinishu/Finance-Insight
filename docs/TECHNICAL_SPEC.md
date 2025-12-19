# Technical Specification: Finance-Insight

## 1. System Architecture

### 1.1 Overview
Finance-Insight is a metadata-driven calculation engine that allows Finance users to define "Alternate Hierarchies" and "Business Logic Overlays" atop official GL data. The system operates as a read-only reporting/overlay tool that does not write back to source systems.

### 1.2 Core Principles
1. **Mathematical Integrity**: Every P&L dollar must be accounted for.
2. **The Waterfall**: Natural rollups are the default; custom rules are overrides.
3. **Auditability**: Always include a 'Reconciliation Plug' for every override.
4. **Precision**: Use decimal-safe math (Pandas/SQL) for P&L values.

## 2. Data Schema

### 2.1 Fact Table (Gold View)
**Table**: `fact_pnl_gold`
- `account_id` (INTEGER)
- `cc_id` (INTEGER) - Cost Center ID, maps to hierarchy leaf nodes
- `book_id` (INTEGER)
- `strategy_id` (INTEGER)
- `daily_pnl` (DECIMAL)
- `mtd_pnl` (DECIMAL)
- `ytd_pnl` (DECIMAL)
- `pytd_pnl` (DECIMAL)

**Note**: Fact data comes from a unified "Gold View" external system. `cc_id` maps to `node_id` where `is_leaf = True` in the hierarchy.

### 2.2 Hierarchy Dimension
**Table**: `dim_hierarchy`
- `node_id` (INTEGER, PRIMARY KEY)
- `parent_node_id` (INTEGER, FOREIGN KEY to node_id)
- `node_name` (VARCHAR)
- `is_leaf` (BOOLEAN)

**Note**: Hierarchies are imported from Atlas (external read-only API/system) as Parent-Child JSON or CSV. Users select a `structure_id` from Atlas which pulls a tree structure.

### 2.3 Use Cases
**Table**: `use_cases`
- `use_case_id` (SERIAL, PRIMARY KEY)
- `name` (VARCHAR) - e.g., "Nov 2024 Budget vs. Actuals"
- `description` (TEXT)
- `owner` (VARCHAR)
- `created_at` (TIMESTAMP)
- `target_period` (VARCHAR) - Period identifier
- `structure_id` (INTEGER) - Reference to Atlas structure
- `status` (VARCHAR) - Active, Archived, etc.

**Note**: Use cases are isolated sandboxes. Rules in Use Case A do not affect Use Case B.

### 2.4 Business Rules
**Table**: `metadata_rules`
- `rule_id` (SERIAL, PRIMARY KEY)
- `use_case_id` (INTEGER, FOREIGN KEY to use_cases)
- `node_id` (INTEGER, FOREIGN KEY to dim_hierarchy)
- `predicate_json` (JSONB) - JSON predicate for UI/GenAI
- `sql_where` (TEXT) - SQL WHERE clause for engine execution
- `logic_en` (TEXT) - Natural language description
- `created_at` (TIMESTAMP)
- `created_by` (VARCHAR)

**Constraints**:
- Only ONE rule per node per use case (enforced by unique constraint on `use_case_id` + `node_id`)
- Parent rules always win over children (Top-Down precedence)

### 2.5 Run History / Results
**Table**: `run_history`
- `run_id` (SERIAL, PRIMARY KEY)
- `use_case_id` (INTEGER, FOREIGN KEY to use_cases)
- `version_id` (VARCHAR) - Unique version identifier
- `calculated_at` (TIMESTAMP)
- `calculated_by` (VARCHAR)
- `status` (VARCHAR) - Success, Failed, In Progress

**Table**: `run_results`
- `result_id` (SERIAL, PRIMARY KEY)
- `run_id` (INTEGER, FOREIGN KEY to run_history)
- `node_id` (INTEGER, FOREIGN KEY to dim_hierarchy)
- `daily_pnl` (DECIMAL)
- `mtd_pnl` (DECIMAL)
- `ytd_pnl` (DECIMAL)
- `pytd_pnl` (DECIMAL)
- `recon_plug_daily` (DECIMAL)
- `recon_plug_mtd` (DECIMAL)
- `recon_plug_ytd` (DECIMAL)
- `recon_plug_pytd` (DECIMAL)
- `has_override` (BOOLEAN) - True if node has a rule applied
- `is_plug_row` (BOOLEAN) - True if this is a reconciliation plug row

**Note**: Every time a user clicks "Calculate," we save a snapshot of results with a `version_id`.

### 2.6 Structure Mappings
**Table**: `use_case_structures`
- `use_case_id` (INTEGER, FOREIGN KEY to use_cases)
- `structure_id` (INTEGER) - Atlas structure identifier
- `hierarchy_data` (JSONB) - Cached hierarchy tree
- `imported_at` (TIMESTAMP)

## 3. Calculation Logic (The Waterfall)

### 3.1 Processing Workflow
1. **Load Hierarchy**: Import or retrieve hierarchy structure for the use case
2. **Calculate Natural Sums**: Bottom-up aggregation from leaf nodes to parents
   - Aggregate all measures: Daily, MTD, YTD, PYTD
   - Formula: `Parent_Value = SUM(Children_Values)` for each measure
3. **Identify Nodes with Rules**: Top-Down scan to find nodes with override rules
4. **Apply Rules**: For each node with a rule:
   - Filter `fact_pnl_gold` using `sql_where` clause
   - Override node value with filtered sum
   - Apply to ALL measures simultaneously (All-or-Nothing)
5. **Calculate Reconciliation Plug**: For each node with an override:
   - `Plug = [Override Value] - [Natural Rollup of Immediate Children]`
   - Calculated for each measure independently

### 3.2 Bottom-Up Aggregation
- Start from leaf nodes (`is_leaf = True`)
- Leaf nodes: Sum fact rows where `fact_pnl_gold.cc_id = dim_hierarchy.node_id`
- Parent nodes: Sum of all immediate children
- Recursive aggregation up the tree

### 3.3 Top-Down Overrides
- If a node has a rule in `metadata_rules`, apply the override
- Rule execution: `SELECT SUM(measure) FROM fact_pnl_gold WHERE [sql_where]`
- Parent rules supersede child rollups (Top-Down precedence)
- Rules apply to ALL measures: Daily, MTD, YTD, PYTD

### 3.4 Reconciliation Plug Calculation
- Formula: `Plug = Parent_Override - SUM(Children_Natural)`
- Only calculated for nodes with overrides
- Plug is calculated for each measure independently
- Plug rows are marked with `is_plug_row = True` in results

### 3.5 Multi-Measure Support
- Single rule applies to all measures simultaneously
- No measure-specific rules in MVP
- All measures calculated independently but using same rule filter

## 4. GenAI Rule Builder

### 4.1 Workflow
1. User types natural language description in Tab 2
2. Frontend sends natural language to backend API
3. Backend calls Gemini 1.5 Pro API with prompt
4. Gemini returns JSON predicate
5. Backend converts JSON predicate to SQL WHERE clause
6. User reviews preview (shows how many rows impacted)
7. User saves rule

### 4.2 Translation Process
- **Input**: Natural language (e.g., "Include all accounts where strategy_id = 'EQUITY'")
- **Gemini Output**: JSON predicate (structured filter conditions)
- **Backend Conversion**: JSON → SQL WHERE clause
- **Storage**: Both `predicate_json` and `sql_where` stored in `metadata_rules`

### 4.3 Rule Preview
- Before saving, show user:
  - Number of fact rows that match the rule
  - Sample rows (preview)
  - Estimated impact on node value

## 5. Tech Stack

### 5.1 Backend
- **Framework**: FastAPI (Python)
- **Data Processing**: Pandas (for set-based operations)
- **Database**: PostgreSQL (from start, even if running locally)
- **ORM**: SQLAlchemy (recommended)
- **Migrations**: Alembic
- **AI Integration**: Google Gemini 1.5 Pro API
- **Validation**: Pydantic

### 5.2 Frontend
- **Framework**: React
- **Language**: TypeScript (strongly recommended)
- **Grid Component**: AG-Grid (Tree Data Mode)
- **Build Tool**: Vite (recommended)
- **Routing**: React Router
- **HTTP Client**: Axios or Fetch API

### 5.3 Database
- **Primary**: PostgreSQL
- **Connection**: SQLAlchemy with connection pooling
- **Decimal Precision**: Use DECIMAL type for all P&L values

### 5.4 Performance Targets
- **Calculation Time**: < 5 seconds for 100k fact rows
- **Processing**: Synchronous for MVP (user waits for results)
- **Scalability**: Pandas is sufficient for MVP scale

## 6. User Interface (Three-Tab Design)

### 6.1 Tab 1: Define Application/Metadata/Structures
**Purpose**: Set up use case and import structures

**Features**:
- Create new use case (Name, Description, Owner, Target Period)
- Select Structure_ID from Atlas (import hierarchy)
- View imported hierarchy tree
- Clone existing use case (copy rules and structure to new period)
- Map fact data: `fact_pnl_gold.cc_id` → `dim_hierarchy.node_id` (where `is_leaf = True`)

### 6.2 Tab 2: Define Business Rules
**Purpose**: Create and manage override rules

**Features**:
- **Standard Mode**: 
  - Select node from hierarchy
  - Enter SQL WHERE clause directly
  - Preview rule impact
- **GenAI Mode**:
  - Select node from hierarchy
  - Enter natural language description
  - AI generates JSON predicate → SQL WHERE clause
  - Preview and edit before saving
- View all rules for current use case
- Edit/Delete existing rules
- Rule validation: Only one rule per node

### 6.3 Tab 3: Show Final Results
**Purpose**: Display calculated results and audit trail

**Features**:
- **AG-Grid Tree View**:
  - Expand/collapse nodes
  - Columns: Node Name, Daily P&L, MTD P&L, YTD P&L, Recon Plug
  - Visual indicators:
    - Blue highlight: Rule-impacted rows
    - Red highlight: Plug rows
- **Drill-Down**:
  - Click row to see:
    - Applied SQL rule
    - Source fact rows (if leaf node)
    - Natural rollup vs. Override comparison
- **Export**: CSV/Excel export
- **Version History**: View previous calculation runs

## 7. Integration Points

### 7.1 Atlas Integration
- **Type**: External Read-Only API/System
- **Import Format**: Parent-Child JSON or CSV
- **Process**: User selects `structure_id` → System imports hierarchy tree
- **Storage**: Cached in `use_case_structures.hierarchy_data` (JSONB)

### 7.2 Fact Data Integration
- **Source**: Unified "Gold View" external system
- **Access**: Read-only (via API, database connection, or file import)
- **Mapping**: `fact_pnl_gold.cc_id` maps to `dim_hierarchy.node_id` where `is_leaf = True`
- **Refresh**: On-demand or scheduled (TBD)

## 8. Key Implementation Priorities

1. **PostgreSQL**: Use PostgreSQL for all metadata and results (not SQLite)
2. **Top-Down Waterfall**: Parent override generates RECON_PLUG based on difference from natural children
3. **GenAI Translator**: Maps natural language → JSON predicate → SQL WHERE clause
4. **Isolated Use Cases**: Each use case is a sandbox with independent rules
5. **Mathematical Integrity**: Every calculation must reconcile (total fact = total root)

## 9. Data Flow

```
Atlas (External) → Import Hierarchy → dim_hierarchy
Gold View (External) → Load Fact Data → fact_pnl_gold
User Input (Tab 1) → Create Use Case → use_cases
User Input (Tab 2) → Define Rules → metadata_rules
Processing Engine → Calculate Waterfall → run_results
Results (Tab 3) → Display Tree Grid → User Review
```

## 10. Validation & Testing

### 10.1 Mathematical Validation
- **Root Reconciliation**: Total P&L in fact table must equal Report Root
- **Plug Validation**: Sum of all plugs should reconcile to zero (or explain difference)
- **Measure Consistency**: YTD should equal sum of Daily values (if applicable)

### 10.2 Rule Validation
- Only one rule per node per use case
- SQL WHERE clause must be valid
- Preview must show impact before saving
