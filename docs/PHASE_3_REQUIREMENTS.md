# Phase 3 Requirements: Frontend UI

## Phase Overview
Build the React TypeScript frontend with three-tab interface for use case management, rule creation, and results visualization. Integrate with FastAPI backend and use AG-Grid for tree data display.

**Goal**: A complete, user-friendly web application that allows finance users to create use cases, define business rules (standard and GenAI), run calculations, and view results with full transparency.

**Success Criteria**: 
- All three tabs functional
- GenAI rule builder working
- AG-Grid tree view displaying results correctly
- Full end-to-end workflow: Tab 1 → Tab 2 → Tab 3

---

## Step 3.1: React Project Setup

### Requirements

1. **Initialize React Project**
   - Use Vite: `npm create vite@latest frontend -- --template react-ts`
   - Install dependencies:
     - `react-router-dom` (routing)
     - `axios` (HTTP client)
     - `@tanstack/react-query` (server state management)
     - `ag-grid-react` and `ag-grid-community` (grid component)
     - `zustand` (client state management, optional)
     - UI library: `@mui/material` or `antd` (choose one)

2. **Project Structure**
   ```
   frontend/
   ├── src/
   │   ├── components/
   │   │   ├── Layout/
   │   │   │   ├── AppLayout.tsx
   │   │   │   └── TabNavigation.tsx
   │   │   ├── Tab1/
   │   │   │   ├── UseCaseList.tsx
   │   │   │   ├── UseCaseForm.tsx
   │   │   │   └── HierarchyViewer.tsx
   │   │   ├── Tab2/
   │   │   │   ├── RuleList.tsx
   │   │   │   ├── RuleForm.tsx
   │   │   │   └── GenAIRuleBuilder.tsx
   │   │   └── Tab3/
   │   │       ├── ResultsGrid.tsx
   │   │       └── NodeDetails.tsx
   │   ├── api/
   │   │   ├── client.ts
   │   │   ├── useCases.ts
   │   │   ├── rules.ts
   │   │   └── calculations.ts
   │   ├── hooks/
   │   │   └── useUseCase.ts
   │   ├── types/
   │   │   └── index.ts
   │   ├── App.tsx
   │   └── main.tsx
   ```

3. **Configuration**
   - Create `vite.config.ts`
   - Set API base URL: `VITE_API_BASE_URL=http://localhost:8000`
   - Configure proxy for development (if needed)

4. **TypeScript Types**
   - Create `src/types/index.ts` with interfaces matching API schemas:
     - `UseCase`, `UseCaseRun`, `Rule`, `HierarchyNode`, `ResultNode`
     - Match Pydantic schemas from backend

### Deliverables
- ✅ React app initialized with TypeScript
- ✅ Project structure created
- ✅ Dependencies installed
- ✅ TypeScript types defined

### Testing
- App runs without errors
- TypeScript compiles successfully
- Basic routing works

---

## Step 3.2: API Client & State Management

### Requirements

1. **Create `src/api/client.ts`**
   - Axios instance with base URL
   - Request interceptors (add auth headers if needed)
   - Response interceptors (error handling)
   - Export configured axios instance

2. **Create API Functions**
   - `src/api/useCases.ts`: All use case endpoints
   - `src/api/rules.ts`: All rule endpoints
   - `src/api/calculations.ts`: Calculation and results endpoints
   - `src/api/atlas.ts`: Atlas mock endpoints
   - Functions return typed responses

3. **React Query Setup**
   - Create `src/hooks/useUseCase.ts`
   - Custom hooks:
     - `useUseCases()`: List use cases
     - `useUseCase(id)`: Get use case
     - `useCreateUseCase()`: Create mutation
     - `useRules(useCaseId)`: List rules
     - `useCreateRule()`: Create rule mutation
     - `useGenAIRule()`: GenAI rule mutation
     - `useCalculate()`: Calculation mutation
     - `useResults(useCaseId, runId?)`: Get results

4. **Error Handling**
   - Global error handler
   - Toast notifications for errors
   - Loading states for async operations

### Deliverables
- ✅ API client configured
- ✅ All API functions implemented
- ✅ React Query hooks created
- ✅ Error handling in place

### Testing
- API calls work correctly
- Errors handled gracefully
- Loading states display

---

## Step 3.3: Tab 1 - Use Case & Structure Management

### Requirements

1. **Layout Component**
   - Create `src/components/Layout/AppLayout.tsx`
   - Three-tab navigation: "Use Cases", "Rules", "Results"
   - Active tab highlighting
   - Use case selector (if multiple use cases)

2. **Use Case List (`UseCaseList.tsx`)**
   - Display table/grid of use cases
   - Columns: Name, Owner, Status, Created Date, Actions
   - Actions: View, Edit, Delete, Clone, Calculate
   - Filter by status, owner
   - Create new use case button

3. **Use Case Form (`UseCaseForm.tsx`)**
   - Modal or separate page
   - Fields:
     - Name (required)
     - Description
     - Owner ID (required)
     - Atlas Structure ID (required)
   - Validation
   - Submit creates use case
   - Success: Navigate to Tab 2

4. **Structure Import (`HierarchyViewer.tsx`)**
   - Button: "Import Structure from Atlas"
   - Modal: List available structures
   - Select structure → Import
   - Display imported hierarchy:
     - Tree view (collapsible)
     - Show node names, depths, leaf indicators
   - Visual indicator: Structure imported/not imported

5. **Clone Use Case**
   - Button on use case row
   - Modal: Enter new name, target period
   - Clone creates new use case with copied rules

### Deliverables
- ✅ Tab 1 complete with all components
- ✅ Use case CRUD working
- ✅ Structure import working
- ✅ Clone functionality working

### Testing
- Create use case successfully
- List and filter use cases
- Import structure and view hierarchy
- Clone use case

---

## Step 3.4: Tab 2 - Business Rules Builder

### Requirements

1. **Rule List (`RuleList.tsx`)**
   - Display rules for selected use case
   - Columns: Node Name, Logic Description, SQL WHERE, Actions
   - Visual indicator: Which nodes have rules
   - Actions: Edit, Delete, Preview

2. **Rule Form - Standard Mode (`RuleForm.tsx`)**
   - Modal or separate page
   - Fields:
     - Node selector (dropdown/tree)
     - SQL WHERE clause (text area)
     - Logic description (text area)
     - Last modified by (input)
   - Validation: SQL syntax check
   - Preview button: Shows row count
   - Submit creates/updates rule

3. **GenAI Rule Builder (`GenAIRuleBuilder.tsx`)**
   - Modal or separate page
   - Fields:
     - Node selector
     - Natural language input (text area)
     - Example: "Include all accounts where strategy_id = 'EQUITY'"
   - "Generate Rule" button:
     - Calls GenAI API
     - Shows loading state
     - **Display Full Transparency**:
       - Show original natural language input
       - Show generated JSON predicate (formatted)
       - Show generated SQL WHERE clause (highlighted)
       - Show validation status (field validation passed/failed)
     - Shows preview (row count)
   - User can:
     - Edit generated SQL
     - Edit JSON predicate (advanced users)
     - Regenerate
     - Save rule
   - **Error Display**:
     - Show validation errors if fields don't exist
     - Show GenAI errors clearly
     - Provide suggestions for fixing errors

4. **Rule Preview**
   - Modal showing:
     - Number of matching rows
     - Sample rows (first 10)
     - Estimated impact on node value
   - "Apply Rule" button

5. **Visual Indicators**
   - Hierarchy tree with rule indicators:
     - Blue dot/icon: Node has rule
     - Hover: Show rule details
   - Rule count badge

### Deliverables
- ✅ Tab 2 complete with all components
- ✅ Standard rule creation working
- ✅ GenAI rule builder working
- ✅ Rule preview working
- ✅ Visual indicators implemented

### Testing
- Create standard rule successfully
- Generate rule via GenAI
- Preview shows correct row count
- Edit and delete rules
- Visual indicators update correctly

---

## Step 3.5: Tab 3 - Results Visualization

### Requirements

1. **Results Grid (`ResultsGrid.tsx`)**
   - AG-Grid Tree Data setup
   - Columns:
     - Node Name (tree column)
     - Daily P&L
     - MTD P&L
     - YTD P&L
     - PYTD P&L
     - Recon Plug (Daily)
     - Recon Plug (MTD)
     - Recon Plug (YTD)
     - Recon Plug (PYTD)
   - **Interactive Tree States**:
     - Expand/collapse nodes
     - Default expand to level 2
     - **Expansion Persistence**: Use AG-Grid's `treeData` properties
     - When user applies rule at Level 2, grid stays expanded at that node
     - User can see resulting change immediately without re-expanding
     - Persist expansion state in browser localStorage (optional)
     - Remember user's preferred expansion level per use case
   - **Differential Highlighting - Visual Cues**:
     - **Natural Data**: Standard font, white background (default)
     - **Override Data**: **Bold Blue** font, light blue background (`is_override = true`)
     - **Plugs**: **Red Italics** font, light red background (if plug != 0)
     - Visual distinction helps users quickly identify data types
     - Tooltip on hover: "Natural Rollup" / "User Override" / "Reconciliation Plug"

2. **Calculate Button**
   - Prominent button: "Calculate Results"
   - On click:
     - Show loading state
     - Call calculation API
     - Poll for completion (or wait for response)
     - Refresh results grid
   - Success message: "Calculation completed successfully"

3. **Node Details Modal (`NodeDetails.tsx`)**
   - Opens on row click
   - Shows:
     - Node name and path
     - Measure values (Daily, MTD, YTD, PYTD)
     - Plug values (if applicable)
     - Is Override flag
     - Applied rule (if override):
       - **Natural language** (`logic_en`)
       - **Generated JSON predicate** (`predicate_json`) - formatted display
       - **Generated SQL WHERE clause** (`sql_where`) - full transparency
     - Natural rollup value (for comparison)
   - **Drill-to-Source for Plugs**:
     - If node has plug (plug != 0), show "Calculation Trace" section
     - Display: `(Parent Override Value) - SUM(Children Natural Values) = [Plug Result]`
     - Show breakdown by measure (Daily, MTD, YTD, PYTD)
     - Show list of children with their natural values
     - This provides the "Why" behind every plug number
   - "View Source Facts" button (if leaf node)

4. **Version History**
   - Dropdown: Select run version
   - Load results for selected version
   - Show version tag and timestamp

5. **Export Functionality**
   - "Export to CSV" button
   - Export current grid view
   - Include all columns
   - Preserve tree structure (indentation)

6. **Results Summary**
   - Header showing:
     - Total P&L (root node values)
     - Number of override nodes
     - Number of plug nodes
     - Calculation timestamp

### Deliverables
- ✅ Tab 3 complete with AG-Grid
- ✅ Calculate button working
- ✅ Node details modal working
- ✅ Version history working
- ✅ Export functionality working

### Testing
- Trigger calculation successfully
- Results display in tree format
- Color coding works correctly
- Node details show correct information
- Export generates valid CSV

---

## Step 3.6: Integration & Polish

### Requirements

1. **End-to-End Workflow**
   - Test full flow:
     1. Tab 1: Create use case → Import structure
     2. Tab 2: Add rules (standard + GenAI)
     3. Tab 3: Calculate → View results
   - Ensure data flows correctly between tabs

2. **Error Handling**
   - API errors: Show user-friendly messages
   - Validation errors: Show field-level errors
   - Network errors: Retry mechanism
   - Loading states: Show spinners/loading bars

3. **User Experience**
   - Form validation (client-side)
   - Confirmation dialogs (delete, calculate)
   - Success notifications (toasts)
   - Responsive design (mobile-friendly)
   - Keyboard navigation

4. **Performance**
   - Lazy load components
   - Optimize AG-Grid rendering (virtual scrolling)
   - Cache API responses (React Query)
   - Debounce search/filter inputs

5. **Styling**
   - Consistent design system
   - Professional finance application look
   - Accessible colors (contrast ratios)
   - Print-friendly styles

### Deliverables
- ✅ Full workflow working end-to-end
- ✅ Error handling complete
- ✅ UX polish applied
- ✅ Performance optimized
- ✅ Styling complete

### Testing
- Full workflow test passes
- Errors handled gracefully
- UI is responsive
- Performance is acceptable

---

## Step 3.7: Documentation & Deployment

### Requirements

1. **User Documentation**
   - Create `docs/USER_GUIDE.md`
   - Sections:
     - Getting Started
     - Tab 1: Creating Use Cases
     - Tab 2: Defining Rules
     - Tab 3: Viewing Results
     - Troubleshooting

2. **Build Configuration**
   - Production build script
   - Environment variables for API URL
   - Build output: `dist/` directory

3. **Deployment Guide**
   - How to build frontend
   - How to serve static files (nginx, etc.)
   - CORS configuration
   - Environment setup

### Deliverables
- ✅ User guide documentation
- ✅ Build configuration
- ✅ Deployment guide

### Testing
- Production build succeeds
- Build output is correct
- Documentation is clear

---

## Phase 3 Acceptance Criteria

✅ **Tab 1**: Use case management complete  
✅ **Tab 2**: Rule creation (standard + GenAI) working  
✅ **Tab 3**: Results visualization with AG-Grid  
✅ **Integration**: Full workflow end-to-end  
✅ **UX**: Professional, user-friendly interface  
✅ **Performance**: Acceptable load times  
✅ **Documentation**: User guide complete  

## Phase 3 Deliverables Summary

1. React TypeScript application
2. Three-tab interface (Use Cases, Rules, Results)
3. AG-Grid tree view for results
4. GenAI rule builder UI
5. API integration complete
6. User documentation
7. Production build configuration

## Dependencies

- Phase 2 complete (API working)
- Node.js and npm installed
- Backend API running on port 8000

## Technology Stack

- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite
- **Routing**: React Router
- **State Management**: TanStack Query (React Query)
- **Grid**: AG-Grid Community
- **HTTP Client**: Axios
- **UI Library**: Material-UI or Ant Design
- **Styling**: CSS Modules or Styled Components

## Next Steps After Phase 3

Once Phase 3 is complete, the application is ready for:
- User acceptance testing
- Production deployment
- Integration with real Atlas system
- Performance optimization
- Security hardening

