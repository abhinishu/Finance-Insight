# Implementation Roadmap: Finance-Insight

## Phase 1: The Engine & Mock Data

### Step 1.1: Database Setup & Schema
- **Task**: Set up PostgreSQL database and create all tables
  - Create `fact_pnl_gold` table
  - Create `dim_hierarchy` table
  - Create `use_cases` table
  - Create `metadata_rules` table
  - Create `run_history` table
  - Create `run_results` table
  - Create `use_case_structures` table
  - Set up Alembic for migrations
- **Deliverable**: Database schema with all tables and relationships

### Step 1.2: Mock Data Generation
- **Task**: Create `app/engine/mock_data.py`
  - Generate 1,000 P&L rows with realistic values
  - Generate ragged hierarchy (3-5 levels, varying depths)
  - Ensure `cc_id` in facts maps to leaf `node_id` in hierarchy
  - Populate all measures: daily_pnl, mtd_pnl, ytd_pnl, pytd_pnl
  - Load data into PostgreSQL tables
- **Deliverable**: Populated database with mock data

### Step 1.3: Waterfall Engine Core
- **Task**: Create `app/engine/waterfall.py`
  - Implement bottom-up aggregation (natural rollups)
  - Implement top-down rule application
  - Implement reconciliation plug calculation
  - Support all measures (Daily, MTD, YTD, PYTD)
  - Use Pandas for set-based operations
  - Ensure decimal-safe math
- **Deliverable**: Core calculation engine with waterfall logic

### Step 1.4: Mathematical Validation
- **Task**: Create validation functions
  - Validate total P&L in fact table matches Report Root
  - Validate plug calculations
  - Create test cases for edge cases
- **Deliverable**: Validation suite ensuring mathematical integrity

## Phase 2: The GenAI Gateway

### Step 2.1: GenAI Translator
- **Task**: Create `app/engine/translator.py`
  - Integrate Google Gemini 1.5 Pro API
  - Implement natural language → JSON predicate conversion
  - Implement JSON predicate → SQL WHERE clause conversion
  - Handle error cases and edge cases
  - Add prompt engineering for consistent outputs
- **Deliverable**: GenAI translator module

### Step 2.2: Rule Preview System
- **Task**: Implement rule preview functionality
  - Show number of fact rows matching rule
  - Display sample matching rows
  - Estimate impact on node value
  - Validate SQL before saving
- **Deliverable**: Rule preview API endpoint

### Step 2.3: Integration with Waterfall Engine
- **Task**: Connect GenAI translator to waterfall engine
  - Store both `predicate_json` and `sql_where` in database
  - Ensure rules from GenAI work correctly in waterfall
  - Test end-to-end: Natural Language → Rule → Calculation
- **Deliverable**: Fully integrated GenAI rule builder

## Phase 3: Backend API (FastAPI)

### Step 3.1: Use Case Management API
- **Task**: Create FastAPI endpoints for Tab 1
  - `POST /api/v1/use-cases` - Create new use case
  - `GET /api/v1/use-cases` - List use cases
  - `GET /api/v1/use-cases/{id}` - Get use case details
  - `POST /api/v1/use-cases/{id}/clone` - Clone use case
  - `POST /api/v1/use-cases/{id}/import-structure` - Import hierarchy from Atlas
  - `GET /api/v1/use-cases/{id}/hierarchy` - Get hierarchy tree
- **Deliverable**: Complete use case management API

### Step 3.2: Rules Management API
- **Task**: Create FastAPI endpoints for Tab 2
  - `POST /api/v1/use-cases/{id}/rules` - Create rule (standard mode)
  - `POST /api/v1/use-cases/{id}/rules/genai` - Create rule via GenAI
  - `GET /api/v1/use-cases/{id}/rules` - List all rules
  - `GET /api/v1/use-cases/{id}/rules/{rule_id}` - Get rule details
  - `PUT /api/v1/use-cases/{id}/rules/{rule_id}` - Update rule
  - `DELETE /api/v1/use-cases/{id}/rules/{rule_id}` - Delete rule
  - `POST /api/v1/use-cases/{id}/rules/{rule_id}/preview` - Preview rule impact
- **Deliverable**: Complete rules management API

### Step 3.3: Calculation & Results API
- **Task**: Create FastAPI endpoints for Tab 3
  - `POST /api/v1/use-cases/{id}/calculate` - Trigger calculation
  - `GET /api/v1/use-cases/{id}/results` - Get latest results
  - `GET /api/v1/use-cases/{id}/results/{version_id}` - Get specific version
  - `GET /api/v1/use-cases/{id}/results/{version_id}/node/{node_id}` - Get node details
  - `GET /api/v1/use-cases/{id}/history` - Get run history
- **Deliverable**: Complete calculation and results API

### Step 3.4: Atlas Integration Mock
- **Task**: Create mock Atlas integration for POC
  - Mock API endpoint for structure import
  - Simulate Parent-Child JSON/CSV format
  - Store imported hierarchies in database
- **Deliverable**: Mock Atlas integration (replaceable with real API later)

## Phase 4: Frontend (React) - 4-Tab Self-Service Model

### Step 4.1: Project Setup & Base Components
- **Task**: Set up React project with TypeScript
  - Initialize React app (Vite recommended)
  - Set up routing (React Router)
  - Set up state management (React Query/Zustand)
  - Create base layout with 4-tab navigation
  - Set up AG-Grid with tree data support
  - Implement premium UX standards (sticky headers, custom scrollbars, density toggle)
- **Deliverable**: React app foundation with executive command center UI

### Step 4.2: Tab 1 - Report Registration (Config)
- **Task**: Build Tab 1 UI - Report Registration
  - **Report Name**: Text input for report name
  - **Atlas Structure Selection**: Dropdown/selector for available structures
  - **Measure Selection**: Multi-select for measures (Daily, WTD, MTD, YTD, PYTD)
  - **Dimension Selection**: Multi-select for dimensions to include
  - **Save/Register Button**: Persist report configuration
  - **Report List**: Display registered reports
- **Deliverable**: Complete Report Registration interface

### Step 4.3: Tab 2 - Input Report (Discovery)
- **Task**: Build Tab 2 UI - Interactive Discovery View
  - **Chevron-based Tree Grid**: AG-Grid with tree data, chevron expansion icons
  - **Default Expansion**: Level 3 expanded by default
  - **Group Shading**: Subtle background tint (rgba(0,0,0,0.02)) for nested rows
  - **Search Bar**: Real-time global filter at top of grid
  - **Financial Formatting**: Negative values in Red with Parentheses - e.g., (1,234.56)
  - **Monospaced Typography**: 'Roboto Mono' font for all numeric columns
  - **Sticky Elements**: Sticky headers and sticky left 'Node Name' column
  - **Custom Scrollbars**: Thin-track CSS scrollbars that appear on hover
  - **Density Toggle**: 'Comfortable' vs. 'Compact' view
  - **Columns**: Node Name, Region, Product, Desk, Strategy, Official GL Baseline, Daily, MTD, YTD
- **Deliverable**: Premium discovery interface with "WOW" UX

### Step 4.4: Tab 3 - Business Rules
- **Task**: Build Tab 3 UI - Business Rules Builder
  - Rule creation form (standard mode)
  - GenAI rule builder (natural language input)
  - Rule list/grid
  - Rule preview modal
  - Rule edit/delete functionality
  - Visual indicators for nodes with rules
- **Deliverable**: Complete Business Rules interface

### Step 4.5: Tab 4 - Final Report
- **Task**: Build Tab 4 UI - Final Report with Reconciliation
  - **Side-by-Side View**: Natural vs. Custom values
  - **Recon Plugs**: Display reconciliation plugs for each node
  - **AG-Grid Tree Data**: Same premium UX as Tab 2
  - **Color Coding**: Blue for rule-impacted, Red for plugs
  - **Export**: CSV/Excel export functionality
  - **Version History**: Selector for different calculation runs
- **Deliverable**: Complete Final Report interface with reconciliation

### Step 4.5: Integration & Polish
- **Task**: Connect frontend to backend APIs
  - Wire up all API calls
  - Error handling and loading states
  - Form validation
  - User feedback (toasts/notifications)
  - Responsive design
- **Deliverable**: Fully functional end-to-end application

## Phase 5: Testing & Documentation

### Step 5.1: Unit Tests
- **Task**: Write comprehensive unit tests
  - Test waterfall engine logic
  - Test GenAI translator
  - Test API endpoints
  - Test validation functions
- **Deliverable**: Test suite with good coverage

### Step 5.2: Integration Tests
- **Task**: Write end-to-end integration tests
  - Test full workflow: Create use case → Add rules → Calculate → View results
  - Test GenAI workflow
  - Test edge cases
- **Deliverable**: Integration test suite

### Step 5.3: Documentation
- **Task**: Create user and technical documentation
  - API documentation (OpenAPI/Swagger)
  - User guide for Tab 1, 2, 3
  - Developer setup guide
  - Architecture documentation
- **Deliverable**: Complete documentation

## Phase 6: Production Readiness

### Step 6.1: Performance Optimization
- **Task**: Optimize for production scale
  - Database query optimization
  - Caching strategy
  - Pagination for large result sets
  - Async processing for large calculations (if needed)
- **Deliverable**: Performance-optimized system

### Step 6.2: Security & Authentication
- **Task**: Add security features
  - Authentication (JWT or SSO integration)
  - Authorization (role-based access)
  - API security (rate limiting, input validation)
  - Audit logging
- **Deliverable**: Secure production-ready system

### Step 6.3: Real Atlas Integration
- **Task**: Replace mock Atlas with real integration
  - Connect to actual Atlas API/system
  - Handle real data formats
  - Error handling for external system failures
- **Deliverable**: Production Atlas integration

## Key Milestones

1. **Milestone 1**: Core engine working with mock data + Premium Discovery UX (End of Phase 1)
2. **Milestone 2**: GenAI rule builder functional (End of Phase 2)
3. **Milestone 3**: Full backend API complete (End of Phase 3)
4. **Milestone 4**: Complete UI with all 4 tabs - Executive Command Center (End of Phase 4)
5. **Milestone 5**: Production-ready system (End of Phase 6)

## Immediate Next Steps (Priority Order)

1. Set up PostgreSQL database and create schema
2. Generate mock data (1,000 rows + hierarchy)
3. Implement core waterfall engine
4. Build FastAPI endpoints for use case management
5. Build Tab 1 UI (Use Case & Structure Management)
6. Build Tab 2 UI (Rules Builder)
7. Implement GenAI translator
8. Build Tab 3 UI (Results Visualization)
9. Integrate all components
10. Testing and documentation
