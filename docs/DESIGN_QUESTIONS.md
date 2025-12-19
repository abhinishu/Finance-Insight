# Technical Design Questions: Finance-Insight Enterprise Solution

## 1. USE CASE & APPLICATION MANAGEMENT

### 1.1 Use Case Lifecycle
- **Q1.1**: Should each "use case" be a completely isolated application with its own structures, rules, and results? Or can use cases share structures/rules?
- **Q1.2**: What metadata defines a use case? (name, description, owner, status, date ranges, etc.)
- **Q1.3**: Do you need versioning/audit trail for use cases? (e.g., "Use Case v1.2 created by John on 2024-01-15")
- **Q1.4**: Can users clone/duplicate existing use cases as templates?

### 1.2 Multi-Tenancy & Access Control
- **Q1.5**: Will multiple users/teams work on different use cases simultaneously?
- **Q1.6**: Do you need role-based access control? (Admin, Creator, Viewer, etc.)
- **Q1.7**: Should use cases be private to creators or shared across teams?

## 2. ATLAS INTEGRATION & DATA SOURCES

### 2.1 Atlas Connection
- **Q2.1**: What is "Atlas"? (Database, API, file system, data warehouse?)
- **Q2.2**: How do we connect to Atlas? (SQL connection string, REST API, file exports?)
- **Q2.3**: Is Atlas read-only for Finance-Insight, or do we write back results?
- **Q2.4**: What's the data refresh cadence? (real-time, daily batch, on-demand?)

### 2.2 Structure Import from Atlas
- **Q2.5**: When you say "structures already defined in Atlas" - what format are they in?
  - Hierarchical trees (parent-child relationships)?
  - Flat dimension tables?
  - JSON/YAML metadata files?
- **Q2.6**: How do users "select" structures from Atlas in Tab 1?
  - Browse/search interface?
  - Import by name/ID?
  - Full sync vs. selective import?
- **Q2.7**: Can users modify imported structures, or are they read-only references?
- **Q2.8**: If structures change in Atlas, how are updates handled? (sync, manual refresh, versioning?)

### 2.3 Fact Data Integration
- **Q2.9**: Where does the P&L fact data come from? (same Atlas system, different source?)
- **Q2.10**: What's the relationship between structures and fact data?
  - Do structures define the "reporting view" while facts are the "source data"?
  - Are structures dimension hierarchies that slice/dice the facts?
- **Q2.11**: Fact data schema - is it always the same, or can it vary by use case?
- **Q2.12**: Do you need to support multiple fact tables/data sources per use case?

## 3. METADATA & STRUCTURE MANAGEMENT (Tab 1)

### 3.1 Structure Definition
- **Q3.1**: What exactly can users define/select in Tab 1?
  - Hierarchy structures (tree nodes)?
  - Dimension attributes (account, cost center, book, strategy)?
  - Measure definitions (Daily, MTD, YTD, PYTD)?
  - Filter criteria?
- **Q3.2**: Can users create "alternate hierarchies" that differ from Atlas structures?
- **Q3.3**: How do users define the relationship between structures and fact data?
  - Mapping tables? (e.g., "cc_id in facts maps to node_id in hierarchy")
  - Join conditions?
- **Q3.4**: Do you need support for multiple hierarchies per use case? (e.g., Account hierarchy + Geography hierarchy)

### 3.2 Measures & Dimensions
- **Q3.5**: Are measures always P&L (daily_pnl, mtd_pnl, ytd_pnl, pytd_pnl) or can users define custom measures?
- **Q3.6**: Can users create calculated measures? (e.g., "Net Revenue = Gross Revenue - Returns")
- **Q3.7**: What dimensions are available? (account_id, cc_id, book_id, strategy_id - are these fixed or configurable?)
- **Q3.8**: Do you need time intelligence? (period comparisons, rolling averages, etc.)

### 3.3 Data Storage for Metadata
- **Q3.9**: Where should use case metadata be stored?
  - SQLite for pilot? PostgreSQL for production?
  - JSON files? (less scalable but simpler)
- **Q3.10**: Do you need a database schema for:
  - Use cases table
  - Structures/hierarchies table
  - Structure-to-fact mappings table
  - Measures definitions table

## 4. BUSINESS RULES ENGINE (Tab 2)

### 4.1 Rule Definition Interface
- **Q4.1**: In "standard mode" - what does rule creation look like?
  - Form-based UI? (select node, select filter criteria, enter SQL/expression)
  - Visual builder? (drag-drop filters, conditions)
  - Code editor? (SQL, Python-like expressions)
- **Q4.2**: What's the rule syntax/structure?
  - SQL WHERE clauses? (as mentioned in `metadata_rules.sql_where`)
  - JSON predicates? (as mentioned in `metadata_rules.predicate_json`)
  - Both? (SQL for filtering, JSON for complex logic)
- **Q4.3**: Can rules reference other rules? (rule dependencies/chaining)
- **Q4.4**: Can users test/validate rules before applying them?

### 4.2 GenAI Rule Builder
- **Q4.5**: For GenAI mode - what's the workflow?
  - User types natural language → Gemini converts to JSON/SQL → User reviews/edits → Save?
- **Q4.6**: What natural language examples should Gemini understand?
  - "Include all accounts where strategy_id = 'EQUITY'"
  - "Exclude cost centers in region 'EMEA'"
  - "Override node 'Trading Revenue' with sum of accounts 100-199"
- **Q4.7**: Should Gemini generate both `predicate_json` AND `sql_where`, or just one?
- **Q4.8**: Do you need rule explanation/transparency? (show user what Gemini generated and why)

### 4.3 Rule Scope & Application
- **Q4.9**: Can rules apply to:
  - Single nodes only?
  - Multiple nodes? (bulk rule application)
  - Entire subtrees?
- **Q4.10**: Rule priority/precedence - if multiple rules apply to same node, which wins?
- **Q4.11**: Can rules be conditional? (e.g., "Apply this rule only if MTD > threshold")
- **Q4.12**: Do you need rule templates/libraries? (reusable rule patterns)

### 4.4 Rule Storage & Versioning
- **Q4.13**: How are rules stored?
  - Database table `metadata_rules`?
  - JSON files per use case?
- **Q4.14**: Do you need rule versioning? (track changes, rollback, compare versions)
- **Q4.15**: Can rules be shared across use cases?

## 5. PROCESSING ENGINE & WATERFALL LOGIC

### 5.1 Calculation Flow
- **Q5.1**: When does processing happen?
  - On-demand (user clicks "Calculate" in Tab 3)?
  - Automatic on rule save?
  - Scheduled batch?
- **Q5.2**: Processing order:
  1. Load fact data
  2. Apply structure mappings
  3. Bottom-up aggregation (natural rollup)
  4. Apply top-down rules (overrides)
  5. Calculate reconciliation plugs
  6. Return results
  - Is this correct?
- **Q5.3**: For "bottom-up aggregation" - do you aggregate ALL measures simultaneously, or one at a time?
- **Q5.4**: Performance requirements:
  - How many fact rows? (1,000 for pilot, but production scale?)
  - How many hierarchy nodes?
  - Expected calculation time? (seconds, minutes?)

### 5.2 Reconciliation Plug Logic
- **Q5.5**: Plug calculation - is it:
  - `Plug = Parent_Override - SUM(Children_Natural)` for each measure?
  - Or `Plug = Parent_Override - SUM(Children_Override)` if children also have rules?
- **Q5.6**: Should plugs be:
  - Stored as separate rows in results?
  - Shown as a separate column?
  - Only calculated for nodes with overrides?
- **Q5.7**: Do plugs need to be "explained" to users? (show which children contributed)

### 5.3 Multi-Measure Processing
- **Q5.8**: When a rule applies to a node, does it automatically apply to all measures (Daily, MTD, YTD, PYTD)?
- **Q5.9**: Or can rules be measure-specific? (e.g., "Override MTD only, leave Daily/YTD as natural rollup")
- **Q5.10**: Are measures calculated independently, or do they have dependencies? (e.g., YTD = sum of Daily)

## 6. RESULTS & VISUALIZATION (Tab 3)

### 6.1 Results Display
- **Q6.1**: What should Tab 3 show?
  - Tree/hierarchy view with aggregated values?
  - Table/grid with all nodes and measures?
  - Both? (tree + detail table)
- **Q6.2**: AG-Grid Tree Mode - requirements:
  - Expand/collapse nodes?
  - Sort/filter columns?
  - Export to Excel/CSV?
  - Drill-down capabilities?
- **Q6.3**: Should results show:
  - Natural rollup values?
  - Override values?
  - Reconciliation plugs?
  - All of the above? (side-by-side comparison)
- **Q6.4**: Do you need "what-if" analysis? (preview results before saving rules)

### 6.2 Results Storage
- **Q6.5**: Should calculated results be:
  - Stored in database? (for historical comparison, audit trail)
  - Regenerated on-demand? (always fresh, but slower)
  - Cached? (with invalidation on rule/structure changes)
- **Q6.6**: Do you need result versioning? (compare results across rule versions)

### 6.3 Audit & Transparency
- **Q6.7**: How do users see "why" a node has a certain value?
  - Tooltip showing applied rules?
  - Drill-down to source facts?
  - Audit log of calculations?
- **Q6.8**: Should users be able to export:
  - Results only?
  - Results + rules + metadata? (full audit package)

## 7. TECHNICAL ARCHITECTURE

### 7.1 Backend Architecture
- **Q7.1**: FastAPI structure - do you want:
  - RESTful API with separate endpoints per resource?
  - GraphQL? (for flexible queries)
  - Both?
- **Q7.2**: API organization:
  - `/api/v1/use-cases` - CRUD for use cases
  - `/api/v1/structures` - structure management
  - `/api/v1/rules` - rule CRUD
  - `/api/v1/calculate` - processing engine
  - `/api/v1/results` - results retrieval
  - Does this make sense?
- **Q7.3**: Do you need WebSocket support? (real-time updates, progress notifications)

### 7.2 Data Storage Strategy
- **Q7.4**: For pilot - SQLite sufficient, or PostgreSQL from start?
- **Q7.5**: Fact data storage:
  - Load into memory (Pandas DataFrames) for processing?
  - Query directly from Atlas/database?
  - Cache in local database?
- **Q7.6**: Do you need data partitioning? (by use case, by date range)

### 7.3 Processing Engine Design
- **Q7.7**: Should processing be:
  - Synchronous? (user waits for results)
  - Asynchronous? (background job, poll for status)
  - Both? (small use cases sync, large ones async)
- **Q7.8**: Do you need job queue? (Celery, RQ, or simple FastAPI background tasks?)
- **Q7.9**: Error handling - if calculation fails partway through, how to recover?

### 7.4 Frontend Architecture
- **Q7.10**: React structure:
  - Single-page app (SPA) with routing?
  - Component library? (Material-UI, Ant Design, Chakra UI?)
- **Q7.11**: State management:
  - React Context?
  - Redux/Zustand?
  - Server state (React Query/TanStack Query)?
- **Q7.12**: AG-Grid integration:
  - Community edition sufficient, or need Enterprise features?
  - Tree data mode - do you have sample hierarchy structure?

## 8. INTEGRATION & DEPLOYMENT

### 8.1 Organization Integration (Future)
- **Q8.1**: What does "integrate with organizational codebase" mean?
  - Shared authentication (SSO)?
  - Shared database?
  - API integration?
  - UI embedding?
- **Q8.2**: What technologies does your org use? (helps design for compatibility)
- **Q8.3**: Do you need to design for:
  - Containerization? (Docker)
  - Cloud deployment? (AWS, Azure, GCP?)
  - On-premise?

### 8.2 Security & Authentication
- **Q8.4**: For pilot - simple auth (username/password) or need to integrate with org SSO?
- **Q8.5**: Do you need:
  - API authentication (JWT tokens)?
  - Role-based authorization?
  - Audit logging?

### 8.3 Performance & Scalability
- **Q8.6**: Expected scale:
  - Users: 10? 100? 1000?
  - Use cases: 10? 100?
  - Fact rows: 1K? 1M? 1B?
- **Q8.7**: Do you need:
  - Caching layer? (Redis)
  - Load balancing?
  - Database connection pooling?

## 9. OPEN SOURCE STACK RECOMMENDATIONS

### 9.1 Backend Stack
- **FastAPI** ✅ (already chosen)
- **SQLAlchemy** (ORM) or **raw SQL**?
- **Pandas** ✅ (already chosen)
- **NumPy** (for decimal-safe math?)
- **Pydantic** ✅ (already in requirements.txt)
- **Alembic** (database migrations)?
- **Celery** (async tasks) or **FastAPI BackgroundTasks**?

### 9.2 Frontend Stack
- **React** ✅ (already chosen)
- **TypeScript** (strongly recommended for enterprise)
- **Vite** (build tool) or **Create React App**?
- **React Router** (routing)
- **AG-Grid** ✅ (already chosen)
- **UI Library**: Material-UI, Ant Design, or Chakra UI?
- **State Management**: Zustand, Redux Toolkit, or React Query?
- **HTTP Client**: Axios or Fetch API?

### 9.3 Database
- **SQLite** (pilot) → **PostgreSQL** (production)?
- **SQLAlchemy** for database abstraction?

### 9.4 AI/ML
- **Google Gemini 1.5 Pro API** ✅ (already chosen)
- **LangChain** (for prompt engineering/chain management)?
- **OpenAI SDK** (for Gemini API client)?

### 9.5 DevOps
- **Docker** (containerization)?
- **docker-compose** (local development)?
- **GitHub Actions** (CI/CD)?

## 10. PILOT VS PRODUCTION CONSIDERATIONS

### 10.1 Pilot Scope
- **Q10.1**: What's the minimum viable pilot?
  - Single use case?
  - Mock data only?
  - Basic rule engine?
- **Q10.2**: What must work perfectly for demo?
  - End-to-end flow (Tab 1 → Tab 2 → Tab 3)?
  - GenAI rule generation?
  - Reconciliation plugs?

### 10.2 Production Readiness
- **Q10.3**: What features can be "good enough" for pilot but need enhancement for production?
- **Q10.4**: What's the timeline?
  - Pilot completion date?
  - Production integration timeline?

---

## NEXT STEPS

Once you answer these questions, I'll design:
1. **Database Schema** (ERD)
2. **API Specification** (OpenAPI/Swagger)
3. **Component Architecture** (backend modules, frontend components)
4. **Data Flow Diagrams** (from Atlas → Processing → Results)
5. **Updated Technical Spec** with all decisions documented

