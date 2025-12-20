# Phase 1 UX Requirements: Premium Executive Command Center

**Document Version:** 2.0  
**Date:** 2024-12-20  
**Author:** Senior Financial Architect & Lead UX Designer  
**Status:** Active Requirements

---

## Executive Summary

Phase 1 must conclude with a **"Discovery" and "Registration" foundation** that feels like an **executive command center**. The UI/UX must meet premium financial application standards with attention to detail, visual polish, and intuitive interaction patterns.

---

## 4-Tab Self-Service Model

### Tab 1: Report Registration (Config)
**Purpose**: Define Report Name, Select Atlas Structure, and Choose Measures/Dimensions to include.

**Components**:
- Report Name input field
- Atlas Structure dropdown/selector
- Measure selection (Daily, WTD, MTD, YTD, PYTD) - multi-select
- Dimension selection - multi-select
- Save/Register button
- Registered reports list/grid

### Tab 2: Input Report (Discovery)
**Purpose**: Interactive tree view of the selected structure with "Natural" P&L values.

**Key Features**:
- Chevron-based tree expansion (not flat lists)
- Default expansion to Level 3
- Group shading for nested rows
- Real-time search bar
- Financial formatting (red negatives with parentheses)
- Monospaced typography for numbers
- Sticky headers and Node Name column
- Custom thin scrollbars
- Density toggle

### Tab 3: Business Rules
**Purpose**: Define and preview GenAI logic overlays.

**Components**:
- Rule creation form (standard mode)
- GenAI rule builder (natural language input)
- Rule list/grid
- Rule preview modal
- Rule edit/delete functionality

### Tab 4: Final Report
**Purpose**: Side-by-side reconciliation (Natural vs. Custom) with "Recon Plugs."

**Components**:
- Side-by-side comparison view
- Natural vs. Custom values
- Reconciliation plugs display
- Export functionality
- Version history selector

---

## Premium UX Standards for Tab 2 (Discovery)

### 1. Tree Grid Interaction

**Chevron-based Expansion**:
- Use AG-Grid's built-in tree data with chevron icons
- Chevrons rotate on expand/collapse
- No flat list display - maintain hierarchical structure

**Default Expansion**:
- Expand to Level 3 by default
- Users can expand/collapse further as needed
- Remember expansion state per session

**Group Shading**:
- Apply subtle background tint: `rgba(0,0,0,0.02)` to nested child rows
- Each level gets slightly darker shade
- Visual hierarchy clearly visible

### 2. Search Bar

**Real-time Global Filter**:
- Positioned at top of grid
- Filters across all columns (Node Name, Region, Product, Desk, Strategy, values)
- Instant filtering as user types
- Clear button to reset filter
- Match highlighting (optional)

### 3. Visual Polish

**Financial Formatting**:
- Negative values displayed in **Red** with **Parentheses**
- Format: `(1,234.56)` for negative, `1,234.56` for positive
- Currency symbol: `$` prefix
- Thousands separator: comma
- Decimal places: 2

**Typography**:
- **Monospaced font** for all numeric columns: `'Roboto Mono', 'Courier New', monospace`
- Ensures decimal alignment across rows
- Regular font for text columns (Node Name, etc.)

**Sticky Elements**:
- **Sticky Headers**: Column headers remain visible when scrolling vertically
- **Sticky Left Column**: 'Node Name' column remains visible when scrolling horizontally
- Smooth scrolling behavior

**Custom Scrollbars**:
- Thin-track CSS scrollbars
- Only appear on hover
- Custom styling to match application theme
- Smooth scrolling

**Density Toggle**:
- Toggle between 'Comfortable' and 'Compact' view
- Comfortable: More padding, larger row height
- Compact: Less padding, smaller row height
- Preference saved per user/session

### 4. Column Configuration

**Required Columns**:
- Node Name (sticky left, tree column)
- Region
- Product
- Desk
- Strategy
- Official GL Baseline
- Daily P&L
- MTD P&L
- YTD P&L

**Column Widths**:
- Node Name: 300px (sticky)
- Region: 120px
- Product: 150px
- Desk: 150px
- Strategy: 200px
- Official GL Baseline: 180px
- Daily P&L: 150px
- MTD P&L: 150px
- YTD P&L: 150px

---

## Data Requirements

### Realistic Structure (15-20 Nodes for POC)

**Hierarchy Path**:
```
ROOT
└── AMER (Region)
    └── CASH_EQUITIES (Product)
        └── HIGH_TOUCH (Desk)
            ├── AMER_CASH_NY (Desk/Strategy)
            ├── AMER_PROG_TRADING (Desk/Strategy)
            ├── EMEA_INDEX_ARB (Desk/Strategy)
            └── APAC_ALGO_G1 (Desk/Strategy)
```

**Desk Names**:
- `AMER_CASH_NY`
- `AMER_PROG_TRADING`
- `EMEA_INDEX_ARB`
- `APAC_ALGO_G1`

**Measures**:
- Daily P&L
- WTD (Week-to-Date) - if supported
- MTD (Month-to-Date)
- YTD (Year-to-Date)

---

## Technical Implementation

### Frontend Stack
- React with TypeScript
- AG-Grid Enterprise (or Community with tree data)
- CSS Modules or Styled Components
- React Query for data fetching

### Backend Requirements
- Support dynamic measure selection
- Return tree structure with natural values
- Include attribute columns (Region, Product, Desk, Strategy)
- Support search/filtering at API level (optional)

### Database Schema
- Report Registration table (new)
  - `report_id` (UUID)
  - `report_name` (VARCHAR)
  - `atlas_structure_id` (VARCHAR)
  - `selected_measures` (JSONB array)
  - `selected_dimensions` (JSONB array)
  - `created_at`, `updated_at`

---

## Success Criteria

1. ✅ Tab 1: Users can register reports with structure and measure selection
2. ✅ Tab 2: Premium discovery view with all UX standards implemented
3. ✅ Tree grid expands to Level 3 by default
4. ✅ Negative values display in red with parentheses
5. ✅ Monospaced font ensures decimal alignment
6. ✅ Sticky headers and Node Name column work smoothly
7. ✅ Search bar filters in real-time
8. ✅ Group shading provides clear visual hierarchy
9. ✅ Custom scrollbars appear on hover
10. ✅ Density toggle switches between Comfortable/Compact views

---

## Implementation Priority

**Phase 1 Must-Have**:
1. Tab 1: Report Registration shell (basic)
2. Tab 2: Discovery view with premium UX
3. Updated mock data (15-20 realistic nodes)
4. Report Registration model/API

**Phase 2+**:
- Tab 3: Business Rules (full implementation)
- Tab 4: Final Report (full implementation)

---

**Status**: Ready for Implementation

