# Use Case 3: Complete Design Summary & Recommendations

**Document Purpose:** Final architectural design and recommendations for Use Case 3 implementation

**Status:** Design Complete - Ready for Implementation Planning  
**Date:** 2026-01-01  
**Reviewer:** Principal Software Architect

---

## Executive Summary

Use Case 3 ("America Cash Equity Trading Structure") introduces **three business rule types** and requires **per-use-case input tables**. The analysis reveals:

1. ✅ **Type 1 Rules** - Simple dimension filtering (SUPPORTED with minor enhancements)
2. ✅ **Type 2 Rules** - Multi-condition filtering (SUPPORTED with enhancements)
3. ❌ **Type 3 Rules** - Node arithmetic (NOT SUPPORTED - requires major architectural changes)
4. ⚠️ **Type 2B Rules** - Arithmetic of multiple queries (NEW - requires enhancement)

**Critical Finding:** Type 3 rules require a new execution phase in the waterfall engine with dependency resolution.

---

## 1. Complete Requirements Summary

### 1.1 Input Table Structure (CONFIRMED)

**Table:** `fact_pnl_use_case_3` (or similar)

**Dimensions (8):**
- Cost Center, Division, Business Area, Product Line, Strategy, Process 1, Process 2, Book

**Measures (3):**
- Daily_PNL, Daily_Commission, Daily_Trade

**See:** `docs/USE_CASE_3_INPUT_TABLE_SCHEMA.md` for complete schema

### 1.2 Hierarchy Structure (CONFIRMED)

**Structure Name:** "America Cash Equity Trading Structure"

**12 Nodes across 4 Levels:**
- Level 1: CORE Products (NODE_ID: 2)
- Level 2: Core Ex CRB (3), CRB (10), ETF Amber (11), MSET (12)
- Level 3: Commissions (4), Trading (7)
- Level 4: Commissions (Non Swap) (5), Swap Commission (6), Facilitations (8), Inventory Management (9)

**See:** `docs/USE_CASE_3_HIERARCHY_AND_RULES.md` for complete hierarchy

### 1.3 Business Rules (CONFIRMED)

**12 Rules Total:**
- **Type 1:** 3 rules (NODE_ID: 2, 11, 12)
- **Type 2:** 5 rules (NODE_ID: 4, 5, 6, 9, 10)
- **Type 2B:** 1 rule (NODE_ID: 4 - arithmetic of two queries)
- **Type 3:** 3 rules (NODE_ID: 3, 7, 8)

**See:** `docs/USE_CASE_3_HIERARCHY_AND_RULES.md` for complete rule definitions

---

## 2. Architectural Design Decisions

### 2.1 Rule Type Classification

**Proposed Schema Enhancement:**
```sql
ALTER TABLE metadata_rules ADD COLUMN rule_type VARCHAR(20) DEFAULT 'FILTER';
-- Values: 'FILTER_SIMPLE' (Type 1), 'FILTER_MULTI' (Type 2), 'FILTER_ARITHMETIC' (Type 2B), 'ARITHMETIC' (Type 3)

ALTER TABLE metadata_rules ADD COLUMN measure_name VARCHAR(50);
-- Values: 'daily_pnl', 'daily_commission', 'daily_trade'

ALTER TABLE metadata_rules ADD COLUMN rule_expression TEXT;
-- For Type 3: "NODE_3 - NODE_4"
-- For Type 2B: "QUERY1 + QUERY2" (with query definitions in predicate_json)

ALTER TABLE metadata_rules ADD COLUMN rule_dependencies JSONB;
-- For Type 3: ["NODE_3", "NODE_4"] - list of referenced nodes
```

**Rationale:**
- Backward compatible (default `rule_type='FILTER'` for existing rules)
- Supports all four rule types
- Enables dependency resolution for Type 3

### 2.2 Input Table Management

**Decision: Physical Tables Per Use Case**

**Rationale:**
- Better data isolation
- Performance (no filtering overhead)
- Clear ownership per use case
- Easier to manage different schemas

**Implementation:**
```sql
-- Add to use_cases table
ALTER TABLE use_cases ADD COLUMN input_table_name VARCHAR(100);
-- e.g., "fact_pnl_use_case_3"

-- Create table per use case
CREATE TABLE fact_pnl_use_case_3 (
    -- See USE_CASE_3_INPUT_TABLE_SCHEMA.md for complete schema
);
```

### 2.3 Enhanced Waterfall Execution

**Proposed Execution Flow:**
```
Phase 1: Natural Rollup
  - Load hierarchy
  - Load input data (use-case specific table)
  - Calculate natural rollups (bottom-up) for nodes without rules

Phase 2: Type 1 Rules (Simple Filters)
  - Load Type 1 rules
  - Apply fact table filters (top-down)
  - Override node values

Phase 3: Type 2 Rules (Multi-Condition Filters)
  - Load Type 2 rules
  - Apply fact table filters (top-down)
  - Override node values

Phase 4: Type 2B Rules (Arithmetic of Queries)
  - Load Type 2B rules
  - Execute multiple queries
  - Combine results with arithmetic operations
  - Override node values

Phase 5: Type 3 Rules (Node Arithmetic) - NEW
  - Load Type 3 rules
  - Build dependency graph
  - Detect circular dependencies
  - Execute in topological order (dependency-based)
  - Override node values

Phase 6: Reconciliation Plugs
  - Calculate plugs for all overridden nodes
  - Formula: Plug = Override_Value - SUM(Children_Adjusted)
```

**Key Changes:**
- New Phase 5 for Type 3 rules
- Dependency resolution required
- Topological sort for execution order

---

## 3. Type 3 Rule Dependency Analysis

### 3.1 Dependency Graph

```
NODE_2 (Type 1) ──┐
                  ├──> NODE_3 (Type 3: NODE_2 - NODE_10)
NODE_10 (Type 2) ─┘

NODE_3 (Type 3) ──┐
                  ├──> NODE_7 (Type 3: NODE_3 - NODE_4)
NODE_4 (Type 2B) ─┘

NODE_7 (Type 3) ──┐
                  ├──> NODE_8 (Type 3: NODE_7 - NODE_9)
NODE_9 (Type 2) ──┘
```

### 3.2 Execution Order (Topological Sort)

1. **NODE_2** (Type 1) - No dependencies
2. **NODE_10** (Type 2) - No dependencies
3. **NODE_4** (Type 2B) - No dependencies
5. **NODE_9** (Type 2) - No dependencies
6. **NODE_11** (Type 1) - No dependencies
7. **NODE_12** (Type 1) - No dependencies
8. **NODE_5** (Type 2) - No dependencies
9. **NODE_6** (Type 2) - No dependencies
10. **NODE_3** (Type 3) - Depends on NODE_2, NODE_10 ✅
11. **NODE_7** (Type 3) - Depends on NODE_3, NODE_4 ✅
12. **NODE_8** (Type 3) - Depends on NODE_7, NODE_9 ✅

### 3.3 Circular Dependency Detection

**Algorithm:**
1. Build directed graph from Type 3 rules
2. Use DFS to detect cycles
3. Report error if cycle found

**Example of Invalid Rule:**
- `NODE_3 = NODE_7 - 100`
- `NODE_7 = NODE_3 + 50`
- **Result:** Circular dependency detected, rule creation rejected

---

## 4. Implementation Phases

### Phase 5.6: Input Table Per Use Case
**Priority:** HIGH  
**Effort:** Medium

**Tasks:**
1. Add `input_table_name` to `use_cases` table
2. Create `fact_pnl_use_case_3` table
3. Update waterfall to use use-case specific tables
4. Add data import functionality

**Deliverables:**
- Database schema updated
- Input table created
- Waterfall engine updated

### Phase 5.7: Rule Type System
**Priority:** HIGH  
**Effort:** Low

**Tasks:**
1. Add `rule_type`, `measure_name`, `rule_expression`, `rule_dependencies` to `metadata_rules`
2. Migrate existing rules (set `rule_type='FILTER'`)
3. Update rule creation UI/API
4. Support Type 1, Type 2, Type 2B, Type 3 classification

**Deliverables:**
- Database schema updated
- Migration script
- Rule creation API updated

### Phase 5.8: Type 2B Rules (Arithmetic of Queries)
**Priority:** MEDIUM  
**Effort:** Medium

**Tasks:**
1. Extend `predicate_json` to support multiple queries
2. Implement query execution and arithmetic combination
3. Update waterfall Phase 4

**Deliverables:**
- Type 2B rule execution engine
- Waterfall Phase 4 updated

### Phase 5.9: Type 3 Rule Engine
**Priority:** CRITICAL  
**Effort:** High

**Tasks:**
1. Implement dependency graph builder
2. Implement topological sort algorithm
3. Implement circular dependency detection
4. Implement arithmetic expression evaluator
5. Integrate with waterfall Phase 5

**Deliverables:**
- Type 3 rule execution engine
- Dependency resolution system
- Waterfall Phase 5 implemented

### Phase 5.10: Structure Import
**Priority:** MEDIUM  
**Effort:** Medium

**Tasks:**
1. Excel import functionality
2. Structure creation from Excel
3. Hierarchy validation
4. Rule import from Excel

**Deliverables:**
- Excel import API
- Structure creation workflow
- Validation and error handling

### Phase 5.11: Backward Compatibility
**Priority:** HIGH  
**Effort:** Medium

**Tasks:**
1. Ensure existing use cases work
2. Migration path for existing rules
3. Comprehensive testing
4. Documentation updates

**Deliverables:**
- Backward compatibility verified
- Migration scripts
- Test suite

---

## 5. Critical Design Questions (Final)

### Q1: NODE_ID 3 (Core Ex CRB)
**Question:** Is the inferred rule `NODE_3 = NODE_2 - NODE_10` correct?
- **Option A:** Yes, it's a Type 3 rule (node arithmetic)
- **Option B:** No, NODE_3 has its own Type 2 rule not shown in Excel
- **Recommendation:** Confirm with business user

### Q2: Root Node
**Question:** Should we create a ROOT node that sums all Level 1 nodes?
- **Option A:** Yes, create ROOT = SUM(Level 1 nodes)
- **Option B:** No, NODE_ID 2 (CORE Products) is the effective root
- **Recommendation:** Option A (consistent with existing system)

### Q3: Measure Selection
**Question:** How does user specify which measure to use?
- **Option A:** Part of rule definition (measure_name field)
- **Option B:** Inferred from rule expression
- **Recommendation:** Option A (explicit is better)

### Q4: Node Name Mapping
**Question:** How to handle name differences? (e.g., "ETF Amber" → "ETF Amer")
- **Option A:** Mapping table in `dim_dictionary`
- **Option B:** Fuzzy matching
- **Option C:** User specifies mapping during rule creation
- **Recommendation:** Option C (explicit mapping, stored in rule)

### Q5: Type 2B Rule Storage
**Question:** How to store Type 2B rules (arithmetic of multiple queries)?
- **Option A:** Multiple rows in `metadata_rules` (one per query)
- **Option B:** Single row with `predicate_json` containing multiple queries
- **Recommendation:** Option B (single row, cleaner)

---

## 6. Final Recommendations

### 6.1 Database Schema Changes

**Required:**
1. Add `input_table_name` to `use_cases` table
2. Add `rule_type`, `measure_name`, `rule_expression`, `rule_dependencies` to `metadata_rules`
3. Create `fact_pnl_use_case_3` table (or dynamic table creation)

**Optional:**
1. Add `dim_atlas_structures` table (from Phase 5.1-5.5)
2. Add measure metadata table (if measures vary by use case)

### 6.2 Waterfall Engine Changes

**Required:**
1. Add Phase 5 for Type 3 rules
2. Implement dependency resolution
3. Implement topological sort
4. Add circular dependency detection

**Enhancements:**
1. Add Phase 4 for Type 2B rules
2. Improve error handling
3. Add performance monitoring

### 6.3 API Changes

**Required:**
1. Update rule creation API to support all rule types
2. Add structure import API (Excel upload)
3. Add input table management API

**Enhancements:**
1. Add rule validation API
2. Add dependency graph visualization API
3. Add rule preview API (shows impact before saving)

### 6.4 UI Changes

**Required:**
1. Update rule editor to support all rule types
2. Add structure import UI (Excel upload)
3. Add input table management UI

**Enhancements:**
1. Visual dependency graph
2. Rule impact preview
3. Measure selection dropdown

---

## 7. Risk Assessment

### Risk 1: Type 3 Rule Complexity
- **Severity:** HIGH
- **Impact:** Circular dependencies, incorrect calculations
- **Mitigation:** Dependency graph validation, cycle detection, comprehensive testing

### Risk 2: Performance Degradation
- **Severity:** MEDIUM
- **Impact:** Multiple passes through hierarchy, dependency resolution overhead
- **Mitigation:** Efficient algorithms, caching, performance testing

### Risk 3: Backward Compatibility
- **Severity:** HIGH
- **Impact:** Existing use cases may break
- **Mitigation:** Default `rule_type='FILTER'`, migration scripts, comprehensive testing

### Risk 4: Input Table Proliferation
- **Severity:** LOW
- **Impact:** Many tables to manage
- **Mitigation:** Automated table creation, naming conventions, cleanup scripts

---

## 8. Next Steps

1. **Answer Final Questions** (Section 5)
2. **Approve Design** (Review this document)
3. **Create Detailed Implementation Plan** (Per phase)
4. **Begin Implementation** (Phase 5.6 → 5.11)

---

## 9. Document References

- **Input Table Schema:** `docs/USE_CASE_3_INPUT_TABLE_SCHEMA.md`
- **Hierarchy & Rules:** `docs/USE_CASE_3_HIERARCHY_AND_RULES.md`
- **Requirements Analysis:** `docs/USE_CASE_3_REQUIREMENTS_ANALYSIS.md`
- **Phase 5 Queries:** `docs/PHASE_5_ENHANCEMENT_QUERIES.md`

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-01  
**Status:** Design Complete - Ready for Approval

