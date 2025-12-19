# Phase 1 Enhancement Requirements: Self-Service Discovery Mode

**Document Version:** 1.0  
**Date:** 2024-12-19  
**Author:** Lead Financial Architect - Finance-Insight  
**Status:** Requirements Gathering & Design

---

## Executive Summary

Phase 1 is currently **functionally complete** with backend engine, database, and basic discovery API working. However, to meet the **Self-Service Discovery Mode** vision, we need enhancements to:

1. **Use Case Management** - Allow users to create/select use cases (e.g., "America Trading P&L")
2. **Structure Selection** - Dynamic dropdown showing all available structures from database
3. **Realistic Finance Domain Data** - Replace generic mock data with realistic Cost Center (CC) structures
4. **Multi-Dimensional Hierarchy** - Enhanced grid display with better expand/collapse UX

---

## Current State Assessment

### ✅ What's Working (Phase 1 Complete)

1. **Backend Engine**
   - ✅ Waterfall calculation engine with natural rollups
   - ✅ Mathematical validation suite
   - ✅ Decimal-safe calculations
   - ✅ Performance: < 2 seconds for discovery

2. **Database**
   - ✅ All 6 tables created and populated
   - ✅ 1,000 fact rows with P&L data
   - ✅ 70 hierarchy nodes (50 leaf nodes)
   - ✅ MOCK_ATLAS_v1 structure available

3. **Discovery API**
   - ✅ `GET /api/v1/discovery?structure_id=MOCK_ATLAS_v1`
   - ✅ Returns hierarchy with natural values (Daily, MTD, YTD)
   - ✅ Tree structure format for AG-Grid

4. **Frontend**
   - ✅ React app with DiscoveryScreen component
   - ✅ AG-Grid tree data display
   - ✅ Basic structure dropdown (hardcoded)

### ❌ Gaps Identified

1. **Use Case Management**
   - ❌ No API endpoints for creating/listing use cases
   - ❌ No UI for use case selection/creation
   - ❌ Discovery API doesn't require use case (uses structure_id directly)

2. **Structure Selection**
   - ❌ Frontend dropdown is hardcoded: `['MOCK_ATLAS_v1']`
   - ❌ No API endpoint to list available structures
   - ❌ No dynamic structure discovery

3. **Data Realism**
   - ❌ Generic node names: "Region_A", "CC_001", "Division_1"
   - ❌ Not finance-domain specific
   - ❌ Doesn't reflect real Cost Center structures

4. **Multi-Dimensional Hierarchy**
   - ⚠️ Current implementation is single-dimensional tree
   - ⚠️ Need clarification on "multi-dimensional" requirement

---

## User Requirements (From Stakeholder)

### Primary Requirement: Self-Service Discovery Mode

**User Journey:**
1. User launches a use case (e.g., "America Trading P&L")
2. **Tab 1**: Select Structure from dropdown (should show ALL available structures)
3. After selecting structure:
   - Display multi-dimensional hierarchy in grid
   - Easy expand/collapse
   - Show P&L values accordingly
4. **Phase 2** (Future): Define business rules

### Specific Requirements

#### 1. Use Case Creation/Selection
- **Requirement**: Users should be able to create or select a use case
- **Example**: "America Trading P&L"
- **Current Gap**: No UI or API for use case management

#### 2. Structure Dropdown
- **Requirement**: Dropdown should show **ALL available structures** (not hardcoded)
- **Current Gap**: Hardcoded `['MOCK_ATLAS_v1']`
- **Needed**: API endpoint to list structures from `dim_hierarchy.atlas_source`

#### 3. Realistic Node Names
- **Requirement**: Use realistic Cost Center (CC) structures from finance domain
- **Current Gap**: Generic names like "Region_A", "CC_001"
- **Needed**: 
  - Realistic finance domain names
  - Use public finance information or standard CC structures
  - Examples: "Americas Trading", "Equity Derivatives", "Fixed Income", etc.

#### 4. Multi-Dimensional Hierarchy
- **Requirement**: Structure should be multi-dimensional hierarchy in grid
- **Current Gap**: Need clarification on what "multi-dimensional" means
- **Questions** (see below)

---

## Design Questions & Clarifications Needed

### Q1: Use Case Workflow
**Question**: Should Phase 1 support:
- **Option A**: Create use case first, then select structure?
- **Option B**: Select structure first (discovery mode), then optionally create use case?
- **Option C**: Use case is optional for Phase 1 - just structure selection?

**Recommendation**: Option B - Discovery-first (aligns with existing design)
- User selects structure → sees data immediately
- Optionally create use case to save for Phase 2 (rules)

### Q2: Multi-Dimensional Hierarchy
**Question**: What does "multi-dimensional hierarchy" mean?
- **Option A**: Multiple hierarchy trees side-by-side (e.g., by Region, by Product, by Strategy)?
- **Option B**: Single hierarchy with multiple attribute columns (Region, Product, Strategy as columns)?
- **Option C**: Drill-down across dimensions (e.g., Region → Product → Strategy)?
- **Option D**: Something else?

**Current Implementation**: Single tree hierarchy (parent-child)
- ROOT → Region → Division → Department → Cost Center

**Recommendation**: Need stakeholder clarification

### Q3: Structure Source
**Question**: Where do structures come from?
- **Option A**: All structures are in `dim_hierarchy` table (already imported from Atlas)?
- **Option B**: Need to fetch from external Atlas API?
- **Option C**: Mock structures for Phase 1, real Atlas in Phase 2?

**Current State**: Structures are in `dim_hierarchy` with `atlas_source` field
- Can query: `SELECT DISTINCT atlas_source FROM dim_hierarchy`

**Recommendation**: Option A for Phase 1 (query database)

### Q4: Realistic Finance Domain Data
**Question**: What level of realism is needed?
- **Option A**: Generic but finance-sounding names (e.g., "Americas Trading", "Equity Desk")?
- **Option B**: Real bank/trading floor structure (if public info available)?
- **Option C**: Standard Cost Center hierarchy template?

**Recommendation**: Option A - Use realistic finance domain terminology
- Regions: Americas, EMEA, APAC
- Business Lines: Trading, Sales, Operations
- Products: Equity, Fixed Income, Derivatives, FX
- Desks: Equity Trading, Fixed Income Trading, etc.

### Q5: Use Case Naming
**Question**: Should use case name be:
- **Option A**: Free-form text (user types "America Trading P&L")?
- **Option B**: Predefined templates?
- **Option C**: Auto-generated from structure selection?

**Recommendation**: Option A - Free-form for flexibility

---

## Proposed Enhancements

### Enhancement 1: Structure List API

**New Endpoint:**
```
GET /api/v1/structures
```

**Response:**
```json
{
  "structures": [
    {
      "structure_id": "MOCK_ATLAS_v1",
      "name": "Americas Trading P&L Structure",
      "node_count": 70,
      "created_at": "2024-01-01T00:00:00Z"
    },
    {
      "structure_id": "MOCK_ATLAS_v2",
      "name": "EMEA Trading P&L Structure",
      "node_count": 65,
      "created_at": "2024-01-02T00:00:00Z"
    }
  ]
}
```

**Implementation:**
- Query `dim_hierarchy` table
- Group by `atlas_source`
- Return distinct structures with metadata

### Enhancement 2: Use Case Management API (Phase 1 Scope)

**New Endpoints:**
```
POST /api/v1/use-cases
GET /api/v1/use-cases
GET /api/v1/use-cases/{use_case_id}
```

**Use Case Creation:**
```json
{
  "name": "America Trading P&L",
  "description": "Q4 2024 Americas Trading P&L analysis",
  "owner_id": "user123",
  "atlas_structure_id": "MOCK_ATLAS_v1"
}
```

**Note**: Full CRUD will be in Phase 2, but basic create/list needed for Phase 1

### Enhancement 3: Realistic Finance Domain Mock Data

**New Mock Data Structure:**
```
ROOT
├── Americas
│   ├── Trading
│   │   ├── Equity Trading
│   │   │   ├── Cash Equities
│   │   │   │   ├── CC_AMER_EQUITY_CASH_001
│   │   │   │   └── CC_AMER_EQUITY_CASH_002
│   │   │   └── Equity Derivatives
│   │   │       ├── CC_AMER_EQUITY_DERIV_001
│   │   │       └── CC_AMER_EQUITY_DERIV_002
│   │   └── Fixed Income Trading
│   │       ├── Government Bonds
│   │       │   └── CC_AMER_FI_GOVT_001
│   │       └── Corporate Bonds
│   │           └── CC_AMER_FI_CORP_001
│   └── Sales
│       └── Institutional Sales
│           └── CC_AMER_SALES_INST_001
├── EMEA
│   └── Trading
│       └── Equity Trading
│           └── CC_EMEA_EQUITY_001
└── APAC
    └── Trading
        └── FX Trading
            └── CC_APAC_FX_001
```

**Node Naming Convention:**
- **Regions**: Americas, EMEA, APAC
- **Business Lines**: Trading, Sales, Operations, Risk
- **Products**: Equity, Fixed Income, Derivatives, FX, Commodities
- **Desks**: Specific trading desks (e.g., "Cash Equities", "Equity Derivatives")
- **Cost Centers**: Format: `CC_{REGION}_{PRODUCT}_{DESK}_{NUMBER}`

### Enhancement 4: Frontend Updates

**DiscoveryScreen.tsx Changes:**
1. **Fetch structures from API** (replace hardcoded list)
2. **Add use case selector** (optional for Phase 1)
3. **Enhanced grid display** (better expand/collapse UX)
4. **Structure metadata display** (show structure name, not just ID)

---

## Implementation Plan

### Phase 1.7: Structure List API (Priority: HIGH)
- [ ] Create `GET /api/v1/structures` endpoint
- [ ] Query `dim_hierarchy` for distinct `atlas_source` values
- [ ] Return structure metadata
- [ ] Update frontend to fetch from API

### Phase 1.8: Use Case Basic API (Priority: MEDIUM)
- [ ] Create `POST /api/v1/use-cases` endpoint
- [ ] Create `GET /api/v1/use-cases` endpoint
- [ ] Basic validation
- [ ] Frontend use case selector (optional)

### Phase 1.9: Realistic Mock Data (Priority: HIGH)
- [ ] Update `app/engine/mock_data.py` with finance domain names
- [ ] Create realistic hierarchy structure
- [ ] Update cost center naming convention
- [ ] Regenerate mock data
- [ ] Validate data integrity

### Phase 1.10: Enhanced Frontend (Priority: MEDIUM)
- [ ] Fetch structures from API
- [ ] Display structure names (not just IDs)
- [ ] Enhanced grid UX
- [ ] Better expand/collapse indicators

---

## Acceptance Criteria

### Structure Selection
- [ ] Dropdown shows all available structures from database
- [ ] Structure names are human-readable
- [ ] Selecting structure loads hierarchy immediately

### Realistic Data
- [ ] Node names use finance domain terminology
- [ ] Cost centers follow realistic naming convention
- [ ] Hierarchy reflects typical trading floor structure

### Use Case (Optional for Phase 1)
- [ ] Users can create use case with name "America Trading P&L"
- [ ] Users can list existing use cases
- [ ] Use case links to structure

### Grid Display
- [ ] Multi-dimensional hierarchy displays correctly
- [ ] Easy expand/collapse functionality
- [ ] P&L values display correctly at all levels

---

## Open Questions for Stakeholder

1. **Multi-Dimensional Hierarchy**: What exactly does this mean? (See Q2 above)

2. **Use Case Priority**: Is use case creation required for Phase 1, or can we defer to Phase 2?

3. **Structure Naming**: Should structure names be:
   - Auto-generated from hierarchy content?
   - User-provided when importing?
   - From Atlas metadata?

4. **Data Volume**: How many structures should we support in Phase 1?
   - Single structure (MOCK_ATLAS_v1)?
   - Multiple mock structures?
   - Real Atlas structures?

5. **Cost Center Format**: What naming convention for Cost Centers?
   - Current: `CC_001`, `CC_002`
   - Proposed: `CC_AMER_EQUITY_CASH_001`
   - Other format?

---

## Next Steps

1. **Stakeholder Review**: Review this document and answer open questions
2. **Design Approval**: Approve proposed enhancements
3. **Implementation**: Begin with Phase 1.7 (Structure List API)
4. **Testing**: Validate with realistic data
5. **Documentation**: Update requirements docs

---

## References

- Current Phase 1 Requirements: `docs/PHASE_1_REQUIREMENTS.md`
- Discovery Workflow: `docs/DISCOVERY_FIRST_WORKFLOW.md`
- Database Schema: `docs/DB_SCHEMA.md`
- Phase 2 Requirements: `docs/PHASE_2_REQUIREMENTS.md`

---

---

## Stakeholder Decisions (2024-12-19)

### Q1: Multi-Dimensional Hierarchy
**Decision**: Option C (Drill-down) + Option B (Attribute columns)

**Implementation**:
- Hierarchy path: **Region → Product → Desk → Strategy**
- AG-Grid will show these as **fixed attribute columns** (Region, Product, Desk, Strategy)
- Users can drill-down by expanding tree nodes
- Each node shows its full dimensional path in columns

**Example Grid Display**:
```
Node Name          | Region | Product          | Desk           | Strategy          | Daily P&L | MTD P&L | YTD P&L
-------------------|--------|------------------|----------------|-------------------|-----------|---------|--------
Americas Trading   | AMER   | CASH_EQUITIES    | HIGH_TOUCH    | AMER_CASH_HIGH... | $1.2M     | $15.3M  | $180M
  Equity Desk      | AMER   | CASH_EQUITIES    | HIGH_TOUCH    | AMER_CASH_HIGH... | $800K     | $10.2M  | $120M
    CC_AMER_EQU... | AMER   | CASH_EQUITIES    | HIGH_TOUCH    | AMER_CASH_HIGH... | $400K     | $5.1M   | $60M
```

### Q2: Use Case Priority
**Decision**: Option B (Optional / Discovery-First)

**User Journey**:
1. User selects structure from dropdown
2. User sees hierarchy with natural values immediately
3. User can explore and drill-down
4. **Optional**: User clicks "Save as New Use Case" button
5. User enters name (e.g., "America Trading P&L")
6. Use case is created and linked to structure

**Implementation**:
- "Save as New Use Case" button in DiscoveryScreen
- Modal/form to enter use case name and description
- Creates use case via API
- Use case is optional - discovery works without it

### Q3: Cost Center Naming
**Decision**: Proposed Format: `CC_AMER_EQUITY_CASH_001`

**Naming Convention**:
- Format: `CC_{REGION}_{PRODUCT}_{DESK}_{NUMBER}`
- Example: `CC_AMER_CASH_EQUITIES_HIGH_TOUCH_001`
- Reflects real business structure

### Q4: Structure Source
**Decision**: Option A (Query Database)

**Implementation**:
- Query: `SELECT DISTINCT atlas_source FROM dim_hierarchy`
- Return structure metadata
- Cache in frontend for dropdown

### Q5: Real-World Finance Domain Data

**Regions**:
- `AMER` (Americas)
- `EMEA` (Europe/Middle-East/Africa)
- `APAC` (Asia-Pacific)

**Products**:
- `CASH_EQUITIES`
- `EQUITY_DERIVATIVES`
- `FIXED_INCOME`
- `FX_SPOT`

**Strategy/Desk Examples**:
- `AMER_CASH_HIGH_TOUCH`
- `EMEA_INDEX_ARB`
- `APAC_ALGO_TRADING`
- `GLOBAL_PROB_TRADING`

**Hierarchy Structure**:
```
ROOT
├── AMER (Region)
│   ├── CASH_EQUITIES (Product)
│   │   ├── HIGH_TOUCH (Desk)
│   │   │   ├── AMER_CASH_HIGH_TOUCH (Strategy)
│   │   │   │   ├── CC_AMER_CASH_EQUITIES_HIGH_TOUCH_001
│   │   │   │   └── CC_AMER_CASH_EQUITIES_HIGH_TOUCH_002
│   │   │   └── AMER_CASH_LOW_TOUCH (Strategy)
│   │   │       └── CC_AMER_CASH_EQUITIES_LOW_TOUCH_001
│   │   └── EQUITY_DERIVATIVES (Product)
│   │       └── ...
│   └── FIXED_INCOME (Product)
│       └── ...
├── EMEA (Region)
│   └── ...
└── APAC (Region)
    └── ...
```

### Q6: Additional Requirement - Official GL Baseline Column

**Requirement**: Add "Official GL Baseline" column in Discovery Tab

**Purpose**: Show the natural sum from `fact_pnl_gold` before any rules are applied

**Implementation**:
- New column in AG-Grid: "Official GL Baseline"
- Shows natural rollup value (same as current Daily/MTD/YTD but labeled as baseline)
- Helps users understand what the "natural" value is before rules

---

## Updated Implementation Plan

### Phase 1.7: Structure List API ✅ HIGH PRIORITY
- [x] Create `GET /api/v1/structures` endpoint
- [x] Query `dim_hierarchy` for distinct `atlas_source` values
- [x] Return structure metadata with node counts

### Phase 1.8: Realistic Finance Domain Mock Data ✅ HIGH PRIORITY
- [x] Update `app/engine/mock_data.py` with finance domain names
- [x] Implement Region → Product → Desk → Strategy hierarchy
- [x] Use naming convention: `CC_{REGION}_{PRODUCT}_{DESK}_{NUMBER}`
- [x] Regenerate mock data with realistic structure

### Phase 1.9: Enhanced Discovery API ✅ HIGH PRIORITY
- [x] Add attribute columns to response (Region, Product, Desk, Strategy)
- [x] Extract attributes from node_id or hierarchy path
- [x] Include in DiscoveryResponse schema

### Phase 1.10: Enhanced Frontend - Attribute Columns ✅ HIGH PRIORITY
- [x] Add Region, Product, Desk, Strategy columns to AG-Grid
- [x] Add "Official GL Baseline" column
- [x] Fetch structures from API (not hardcoded)
- [x] Implement "Save as New Use Case" button

### Phase 1.11: Use Case Basic API ✅ MEDIUM PRIORITY
- [x] Create `POST /api/v1/use-cases` endpoint
- [x] Create `GET /api/v1/use-cases` endpoint
- [x] Basic validation

---

**Document Status**: ✅ Approved - Implementation in Progress

