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

## Phase 4: Frontend (React)

### Step 4.1: Project Setup & Base Components
- **Task**: Set up React project with TypeScript
  - Initialize React app (Vite recommended)
  - Set up routing (React Router)
  - Set up state management (React Query/Zustand)
  - Create base layout with tab navigation
  - Set up AG-Grid
- **Deliverable**: React app foundation

### Step 4.2: Tab 1 - Use Case & Structure Management
- **Task**: Build Tab 1 UI
  - Use case creation form
  - Use case list/grid
  - Structure import interface (mock Atlas)
  - Hierarchy tree viewer
  - Clone use case functionality
- **Deliverable**: Complete Tab 1 interface

### Step 4.3: Tab 2 - Business Rules Builder
- **Task**: Build Tab 2 UI
  - Rule creation form (standard mode)
  - GenAI rule builder (natural language input)
  - Rule list/grid
  - Rule preview modal
  - Rule edit/delete functionality
  - Visual indicators for nodes with rules
- **Deliverable**: Complete Tab 2 interface

### Step 4.4: Tab 3 - Results Visualization
- **Task**: Build Tab 3 UI
  - AG-Grid Tree Data setup
  - Columns: Node Name, Daily, MTD, YTD, Recon Plug
  - Color coding: Blue for rule-impacted, Red for plugs
  - Row click drill-down (show rule details)
  - Export to CSV/Excel
  - Version history selector
  - Calculate button
- **Deliverable**: Complete Tab 3 interface

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

1. **Milestone 1**: Core engine working with mock data (End of Phase 1)
2. **Milestone 2**: GenAI rule builder functional (End of Phase 2)
3. **Milestone 3**: Full backend API complete (End of Phase 3)
4. **Milestone 4**: Complete UI with all three tabs (End of Phase 4)
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
