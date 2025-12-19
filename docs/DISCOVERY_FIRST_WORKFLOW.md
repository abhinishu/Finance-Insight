# Discovery-First Workflow: Self-Service Model

## User Journey

### Step 1: Select Use Case
- User creates or selects a use case
- Use case is a sandbox for exploration

### Step 2: Import Atlas Structure
- User selects an Atlas Structure ID
- System imports hierarchy (flattened into `dim_hierarchy` table)
- Hierarchy is cached for performance

### Step 3: Discovery Tab (Immediate Display)
- **No calculation run needed** - this is live discovery
- System displays hierarchy tree with:
  - **Natural Values**: Sum of underlying fact rows
  - **Measures**: Daily, MTD, YTD (PYTD optional)
  - **Tree Structure**: Parent-child relationships
- Every node shows sum of its children by default
- User can explore and understand data structure

### Step 4: User Exploration
- Expand/collapse nodes
- See natural rollups at every level
- Understand data distribution
- Identify areas for rule creation

### Step 5: Create Rules (Phase 2)
- After exploration, user creates rules
- Rules override natural values
- Reconciliation plugs calculated

## Technical Implementation

### Discovery API Endpoint
```
GET /api/v1/use-cases/{use_case_id}/discovery
```

**Response**: Hierarchy tree with natural values
- No rules applied
- Pure bottom-up aggregation
- Fast response (< 2 seconds)

### Data Strategy
- **Atlas provides hierarchy**: Imported as parent-child structure
- **Flattened in DB**: Stored in `dim_hierarchy` table (already optimized)
- **Natural rollups**: Calculated on-demand for discovery view
- **Caching**: Natural values cached if use case unchanged

### Performance Considerations
- Discovery view should be fast (< 2 seconds)
- Use flattened hierarchy structure (already in DB)
- Cache natural rollups when possible
- Optimize for read-heavy discovery workflow

## Benefits of Discovery-First Approach

1. **Self-Service**: Users can explore without creating rules first
2. **Understanding**: Users see natural data before making changes
3. **Confidence**: Users understand what they're overriding
4. **Efficiency**: No need to create rules just to see data
5. **Transparency**: Natural values always visible as baseline

## Phase 1 Priority

The Discovery Tab is the **first priority** in Phase 1. Users should be able to:
- Select use case
- Import structure
- **Immediately see hierarchy with natural values**

This enables the self-service model where exploration comes before rule creation.

