# Phase 2 Requirements: Backend API & GenAI

## Phase Overview
Build the FastAPI backend with REST endpoints for use case management, rule creation, and calculation. Integrate Google Gemini 1.5 Pro for natural language rule generation.

**Goal**: A complete REST API that allows users to manage use cases, create rules (standard and GenAI), run calculations, and retrieve results.

**Success Criteria**: 
- All API endpoints functional and tested
- GenAI translator converts natural language to SQL WHERE clauses
- Rule preview shows impact before saving
- Full workflow: Create use case → Add rules → Calculate → View results

---

## Step 2.1: FastAPI Application Setup

### Requirements

1. **Create `app/main.py`**
   - FastAPI application instance
   - CORS middleware (for frontend integration)
   - Database session dependency
   - Error handling middleware
   - Health check endpoint: `GET /health`

2. **Create `app/api/dependencies.py`**
   - `get_db_session()`: Dependency for database sessions
   - `get_current_user()`: Placeholder for authentication (Phase 3)
   - Error handlers for common exceptions

3. **Create `app/api/schemas.py`**
   - Pydantic models for request/response:
     - `UseCaseCreate`, `UseCaseResponse`
     - `UseCaseRunCreate`, `UseCaseRunResponse`
     - `RuleCreate`, `RuleResponse`, `RuleGenAIRequest`
     - `HierarchyNode`, `HierarchyTree`
     - `CalculationRequest`, `CalculationResponse`
     - `ResultNode`, `ResultsResponse`
   - Validation rules matching database constraints

4. **Project Structure**
   ```
   app/
   ├── main.py
   ├── api/
   │   ├── dependencies.py
   │   ├── schemas.py
   │   ├── routes/
   │   │   ├── use_cases.py
   │   │   ├── rules.py
   │   │   ├── calculations.py
   │   │   └── results.py
   ```

### Deliverables
- ✅ FastAPI app with health check
- ✅ Database session dependency
- ✅ Pydantic schemas for all entities
- ✅ Basic error handling

### Testing
- Health check returns 200
- Database connection works
- Schemas validate correctly

---

## Step 2.2: Use Case Management API

### Requirements

1. **Create `app/api/routes/use_cases.py`**

2. **Endpoints**

   **a. `POST /api/v1/use-cases`**
   - Create new use case
   - Request body: `{name, description, owner_id, atlas_structure_id}`
   - Response: `UseCaseResponse` with UUID
   - Default status: `DRAFT`

   **b. `GET /api/v1/use-cases`**
   - List all use cases
   - Query params: `status`, `owner_id` (optional filters)
   - Response: List of `UseCaseResponse`
   - Pagination: `limit`, `offset` (optional)

   **c. `GET /api/v1/use-cases/{use_case_id}`**
   - Get use case details
   - Include: rules count, runs count
   - Response: `UseCaseResponse` with metadata

   **d. `PUT /api/v1/use-cases/{use_case_id}`**
   - Update use case (name, description, status)
   - Response: Updated `UseCaseResponse`

   **e. `DELETE /api/v1/use-cases/{use_case_id}`**
   - Delete use case (cascade deletes rules and runs)
   - Response: 204 No Content

   **f. `POST /api/v1/use-cases/{use_case_id}/clone`**
   - Clone use case to new period
   - Request body: `{name, description, target_period}`
   - Copy: rules, hierarchy reference
   - Response: New `UseCaseResponse`

   **g. `GET /api/v1/use-cases/{use_case_id}/hierarchy`**
   - Get hierarchy tree for use case
   - Load from `dim_hierarchy` filtered by `atlas_structure_id`
   - Return nested tree structure
   - Response: `HierarchyTree` (nested nodes)

### Deliverables
- ✅ Complete use case CRUD API
- ✅ Clone functionality
- ✅ Hierarchy retrieval endpoint

### Testing
- Create use case successfully
- List and filter use cases
- Clone use case with rules
- Retrieve hierarchy tree

---

## Step 2.3: Rules Management API

### Requirements

1. **Create `app/api/routes/rules.py`**

2. **Endpoints**

   **a. `POST /api/v1/use-cases/{use_case_id}/rules`**
   - Create rule (standard mode)
   - Request body: `{node_id, sql_where, logic_en, last_modified_by}`
   - Validate: Only one rule per node (check constraint)
   - Store: `predicate_json` can be null for standard mode
   - Response: `RuleResponse`

   **b. `POST /api/v1/use-cases/{use_case_id}/rules/genai`**
   - Create rule via GenAI (see Step 2.4)
   - Request body: `{node_id, logic_en, last_modified_by}`
   - Call GenAI translator
   - Store both `predicate_json` and `sql_where`
   - Response: `RuleResponse` with generated SQL

   **c. `GET /api/v1/use-cases/{use_case_id}/rules`**
   - List all rules for use case
   - Response: List of `RuleResponse`
   - Include: node name, rule details

   **d. `GET /api/v1/use-cases/{use_case_id}/rules/{rule_id}`**
   - Get rule details
   - Response: `RuleResponse`

   **e. `PUT /api/v1/use-cases/{use_case_id}/rules/{rule_id}`**
   - Update rule
   - Can update: `sql_where`, `logic_en`, `predicate_json`
   - Update `last_modified_at` timestamp
   - Response: Updated `RuleResponse`

   **f. `DELETE /api/v1/use-cases/{use_case_id}/rules/{rule_id}`**
   - Delete rule
   - Response: 204 No Content

   **g. `POST /api/v1/use-cases/{use_case_id}/rules/{rule_id}/preview`**
   - Preview rule impact
   - Execute SQL WHERE clause on fact table
   - Return: Count of matching rows, sample rows, estimated impact
   - Response: `RulePreviewResponse`

### Deliverables
- ✅ Complete rules CRUD API
- ✅ Rule preview endpoint
- ✅ Validation (one rule per node)

### Testing
- Create rule successfully
- Prevent duplicate rules on same node
- Preview shows correct row count
- Update and delete rules

---

## Step 2.4: GenAI Translator Integration

### Requirements

1. **Create `app/engine/translator.py`**

2. **Gemini API Integration**
   - Install: `google-generativeai` package
   - Add to `requirements.txt`: `google-generativeai==0.3.0`
   - API key from environment: `GEMINI_API_KEY`

3. **Core Functions**

   **a. `translate_natural_language_to_json(logic_en, fact_schema)`**
   - Call Gemini 1.5 Pro API
   - Prompt: Convert natural language to structured JSON predicate
   - Input: Natural language description
   - Output: JSON predicate (e.g., `{"strategy_id": {"operator": "equals", "value": "EQUITY"}}`)
   - Handle errors: Invalid language, ambiguous requests
   - **Check cache first** (see caching strategy below)

   **b. `validate_json_predicate(json_predicate, fact_schema)`**
   - **Logic Abstraction Layer - CRITICAL**
   - Validate that all fields in JSON predicate exist in fact schema
   - Check: `strategy_id`, `book_id`, `account_id`, `cc_id` are valid columns
   - Validate operator values (equals, in, etc.) are supported
   - Validate data types match (string vs numeric)
   - Return: Validation result with errors if any
   - **This prevents AI "hallucination" - fields must exist before SQL conversion**

   **c. `convert_json_to_sql(json_predicate, fact_table="fact_pnl_gold")`**
   - Convert JSON predicate to SQL WHERE clause
   - **ONLY called after JSON validation passes**
   - Support operators: equals, not_equals, in, not_in, greater_than, less_than
   - Support multiple conditions (AND/OR)
   - Return: SQL WHERE clause string
   - Validate: SQL syntax is safe (no injection)
   - Use parameterized queries for values (prevent SQL injection)

   **d. `translate_rule(logic_en, fact_schema)`**
   - Main function: Natural language → JSON → **Validate JSON** → SQL
   - Returns: `{predicate_json: {...}, sql_where: "...", validation_errors: [...]}`
   - Error handling: Return error message if translation fails
   - **Show validation errors to user before SQL generation**

4. **Prompt Engineering**
   - System prompt: "You are a financial data expert. Convert natural language filters to JSON predicates."
   - Include fact table schema in prompt
   - Examples: "Include all accounts where strategy_id = 'EQUITY'"
   - Output format: Strict JSON schema

5. **Caching Strategy**
   - Create `app/engine/rule_cache.py`
   - Cache frequently used natural language queries
   - Key: Natural language string (normalized)
   - Value: `{predicate_json, sql_where, created_at}`
   - Cache TTL: 30 days (configurable)
   - Examples to cache: "Americas Core P&L", "Equity Trading Revenue"
   - Benefits: Save API costs, improve response times
   - Cache lookup before calling Gemini API

6. **Prompt-to-SQL Transparency**
   - **CRITICAL for Auditability**
   - When AI generates a rule, store both:
     - Original natural language (`logic_en`)
     - Generated JSON predicate (`predicate_json`)
     - Generated SQL WHERE clause (`sql_where`)
   - UI must display all three to user
   - This provides full transparency - no "black box" logic
   - Essential for financial audits

7. **Error Handling**
   - Invalid API key
   - API rate limits
   - Malformed responses
   - Unsupported operations
   - Field validation errors (from abstraction layer)

### Deliverables
- ✅ GenAI translator module
- ✅ JSON to SQL converter
- ✅ Error handling and validation
- ✅ Unit tests with mock Gemini responses

### Testing
- Translate simple natural language to SQL
- Handle complex conditions (AND/OR)
- Validate SQL safety (no injection)
- Handle API errors gracefully

---

## Step 2.5: Calculation & Results API

### Requirements

1. **Create `app/api/routes/calculations.py`**

2. **Endpoints**

   **a. `POST /api/v1/use-cases/{use_case_id}/calculate`**
   - Trigger waterfall calculation
   - Request body: `{version_tag, triggered_by}` (triggered_by required)
   - Steps:
     1. Create `UseCaseRun` record (status: IN_PROGRESS, triggered_by set)
     2. Call `calculate_waterfall()` from engine (pass triggered_by)
     3. Save results to `fact_calculated_results`
     4. Update run status: COMPLETED or FAILED
     5. Store `calculation_duration_ms` in run record
     6. Return run_id, version_tag, and duration
   - Response: `CalculationResponse` with run_id, duration_ms

   **b. `GET /api/v1/use-cases/{use_case_id}/results`**
   - Get latest results for use case
   - Find latest run (by timestamp)
   - Load results from `fact_calculated_results`
   - Format as tree structure
   - Response: `ResultsResponse` (tree of nodes with measures)

   **c. `GET /api/v1/use-cases/{use_case_id}/results/{run_id}`**
   - Get results for specific run
   - Response: `ResultsResponse`

   **d. `GET /api/v1/use-cases/{use_case_id}/results/{run_id}/node/{node_id}`**
   - Get detailed view for single node
   - Include: measure_vector, plug_vector, is_override, applied rule
   - Response: `ResultNode` with full details

   **e. `GET /api/v1/use-cases/{use_case_id}/history`**
   - Get run history
   - List all runs with: version_tag, timestamp, status
   - Response: List of `UseCaseRunResponse`

3. **Results Formatting**
   - Convert `measure_vector` JSONB to readable format
   - Convert `plug_vector` JSONB to readable format
   - Include node hierarchy (parent-child relationships)
   - Flag override nodes and plug nodes

### Deliverables
- ✅ Calculation trigger endpoint
- ✅ Results retrieval endpoints
- ✅ Run history endpoint
- ✅ Results formatting utilities

### Testing
- Trigger calculation successfully
- Retrieve results in tree format
- Get node details with rules
- View run history

---

## Step 2.6: Atlas Integration Mock

### Requirements

1. **Create `app/api/routes/atlas.py`**

2. **Mock Endpoints**

   **a. `GET /api/v1/atlas/structures`**
   - List available structures (mock)
   - Return: `[{structure_id: "STRUCT_001", name: "Q4 2024 Hierarchy", ...}]`
   - Hardcoded list for POC

   **b. `GET /api/v1/atlas/structures/{structure_id}`**
   - Get hierarchy for structure
   - Return: Parent-child JSON format
   - Format matches `dim_hierarchy` schema
   - Response: `HierarchyTree`

   **c. `POST /api/v1/use-cases/{use_case_id}/import-structure`**
   - Import hierarchy from Atlas
   - Request body: `{structure_id}`
   - Steps:
     1. Fetch hierarchy from Atlas (mock)
     2. Load into `dim_hierarchy` table
     3. Update use case's `atlas_structure_id`
   - Response: Import summary

3. **Mock Data**
   - Pre-defined hierarchy structures
   - Can be replaced with real Atlas API later

### Deliverables
- ✅ Mock Atlas API endpoints
- ✅ Structure import functionality
- ✅ Documentation for real Atlas integration

### Testing
- List mock structures
- Import structure successfully
- Hierarchy loaded correctly

---

## Step 2.7: API Documentation & Testing

### Requirements

1. **OpenAPI/Swagger Documentation**
   - Auto-generated from FastAPI
   - Accessible at `/docs` and `/redoc`
   - Include request/response examples
   - Include error response formats

2. **API Testing**
   - Create `tests/api/` directory
   - Test all endpoints with pytest
   - Use test database
   - Test error cases

3. **Integration Tests**
   - Full workflow test:
     - Create use case
     - Import structure
     - Add rules (standard + GenAI)
     - Calculate
     - Retrieve results
   - Verify data integrity

### Deliverables
- ✅ Swagger documentation
- ✅ API test suite
- ✅ Integration test for full workflow

### Testing
- All endpoints documented
- All tests pass
- Integration test completes successfully

---

## Phase 2 Acceptance Criteria

✅ **FastAPI App**: Running with all endpoints  
✅ **Use Cases**: Full CRUD + clone + hierarchy  
✅ **Rules**: CRUD + GenAI + preview  
✅ **Calculations**: Trigger and retrieve results  
✅ **GenAI**: Natural language → SQL working  
✅ **Atlas Mock**: Structure import working  
✅ **Documentation**: Swagger UI functional  
✅ **Tests**: All endpoints tested  

## Phase 2 Deliverables Summary

1. FastAPI application (`app/main.py`)
2. API routes (use cases, rules, calculations, results, atlas)
3. GenAI translator (`app/engine/translator.py`)
4. Pydantic schemas (`app/api/schemas.py`)
5. API test suite
6. Swagger documentation

## Dependencies

- Phase 1 complete (engine working)
- Google Gemini API key
- FastAPI, Pydantic installed
- Test database for API tests

## Next Phase

Once Phase 2 is complete and tested, we proceed to **Phase 3: Frontend UI** to build the React application with three-tab interface.

