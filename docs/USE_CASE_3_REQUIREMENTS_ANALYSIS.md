# Use Case 3: America Cash Equity Trading - Requirements Analysis

**Document Purpose:** Detailed architectural analysis of Use Case 3 requirements, including new business rule types and input table structure.

**Status:** Design Review - Analysis Phase  
**Date:** 2026-01-01  
**Reviewer:** Principal Software Architect

---

## Executive Summary

Use Case 3 introduces significant enhancements to the Finance-Insight system:
1. **Per-Use-Case Input Tables** - Each use case has its own dedicated input data source
2. **New Structure** - "America Cash Equity Trading Structure" to be created from Excel
3. **Three Business Rule Types** - Type 1 (simple filter), Type 2 (multi-condition), Type 3 (node arithmetic)
4. **Backward Compatibility** - Must support existing use cases while adding new capabilities

**Critical Finding:** Type 3 rules (node arithmetic) represent a **fundamental architectural change** that requires new execution logic beyond the current waterfall engine.

---

## 1. Requirement Breakdown

### 1.1 Separate Input Table Per Use Case

**Requirement:**
> "For each use case ideally the input data should be separate table/view - for this use case I have a separate table"

**Current State:**
- `fact_pnl_gold` - Shared fact table (all use cases)
- `fact_pnl_entries` - Use-case specific (has `use_case_id` FK, but shared table)

**New Requirement:**
- Use Case 3 needs its **own dedicated input table**
- Structure defined in Excel tab "Input table for use case 3"

**Use Case 3 Input Table Schema (CONFIRMED):**

**Dimensions (8 columns):**
1. `Cost Center` (VARCHAR) - e.g., "ABC1"
2. `Division` (VARCHAR) - e.g., "IED"
3. `Business Area` (VARCHAR) - e.g., "Cash Equity"
4. `Product Line` (VARCHAR) - e.g., "Core Products", "Core Primary"
5. `Strategy` (VARCHAR) - e.g., "CORE", "CORE Primary 1"
6. `Process 1` (VARCHAR) - e.g., "MSET"
7. `Process 2` (VARCHAR) - e.g., "Inventory Man", "ABC", "DEF"
8. `Book` (VARCHAR) - e.g., "CORE 1", "Core Primary 1 - CORE"

**Measures (3 columns):**
9. `Daily_PNL` (NUMERIC) - Daily Profit & Loss
10. `Daily_Commission` (NUMERIC) - Daily Commission
11. `Daily_Trade` (NUMERIC) - Daily Trade Count/Volume

**Sample Data:**
| Cost Center | Division | Business Area | Product Line | Strategy | Process 1 | Process 2 | Book | Daily_PNL | Daily_Commission | Daily_Trade |
|-------------|----------|---------------|--------------|----------|-----------|-----------|------|-----------|------------------|-------------|
| ABC1 | IED | Cash Equity | Core Products | CORE | MSET | Inventory Man | CORE 1 | 100 | 20 | 10 |
| ABC1 | IED | Cash Equity | Core Products | CORE | MSET | ABC | CORE 1 | -200 | -20 | -10 |
| ABC1 | IED | Cash Equity | Core Primary | CORE Primary 1 | MSET | DEF | Core Primary 1 - CORE | 50 | 5 | 10 |

**Key Observations:**
- **8 dimensions** available for filtering (Type 1 and Type 2 rules)
- **3 measures** available for aggregation (Daily_PNL, Daily_Commission, Daily_Trade)
- **No date column** visible - may need to add `pnl_date` for temporal analysis
- **No use_case_id** - will need to add when creating table

**Architectural Impact:**
- **MEDIUM** - Requires input table management per use case
- **Options:**
  1. Physical tables per use case (`fact_pnl_use_case_3`)
  2. Views filtering `fact_pnl_entries` by `use_case_id`
  3. Dynamic table reference in `use_cases` table

**Questions:**
- Should we add `pnl_date` column for temporal analysis? (MTD, YTD calculations)
- Should we add `use_case_id` FK to link to use case?
- How is data loaded into the input table? (Manual import, ETL, API?)
- Should all use cases migrate to separate tables, or only new ones?

---

### 1.2 New Structure: America Cash Equity Trading Structure

**Requirement:**
> "We need to use this to create a new structure called America Cash Equity Trading Structure"

**Source:** Excel tab "Business rule for use case 3" contains:
- **Column "Level"** - Hierarchy level (parent-child relationships)
- **Column "NODE_ID"** - Hierarchy node identifier
- **Column "Node name"** - Hierarchy node display name
- **Column D** - Derivation logic
- **Column E** - Business rule definition

**Architectural Impact:**
- **LOW** - Structure creation is already supported (via hierarchy import)
- **Enhancement:** Excel-based structure import workflow

**Questions:**
- What is the exact hierarchy structure? (How many levels, root node, leaf nodes?)
- How should structure be imported? (Excel upload, API, manual entry?)
- Should structure import validate hierarchy integrity?

---

### 1.3 Three Types of Business Rules

#### Type 1: Simple Dimension Filtering

**Pattern:** `SUM(DAILY_PNL) WHERE Strategy='NODE_NAME'`

**Example:**
- Node name: "CORE"
- Rule: `SUM(DAILY_PNL) WHERE Strategy='CORE'`
- Interpretation: Node name maps directly to dimension value

**Current System Support:**
- ✅ **SUPPORTED** - Current `sql_where` can handle this
- Current: `WHERE strategy_id = 'CORE'`
- Enhancement: Auto-map node name to dimension value

**Architectural Impact:**
- **LOW** - Minor enhancement to rule creation UI/API
- Need to add node-name-to-dimension mapping logic

**Questions:**
- How is node name mapped to dimension? (Exact match? Case-sensitive? Mapping table?)
- Which dimensions can be used? (Strategy only? Any dimension? Configurable?)

---

#### Type 2: Multi-Condition Filtering

**Pattern:** `SUM(DAILY_PNL) WHERE Strategy='CORE' AND PROCESS_2='Inventory Management'`

**Example:**
- Multiple dimension conditions with AND logic
- More complex filtering than Type 1

**Current System Support:**
- ✅ **SUPPORTED** - Current `sql_where` can handle this
- Current: `WHERE strategy_id='CORE' AND process_2='Inventory Management'`
- Enhancement: Better UI/API for multi-condition rule creation

**Architectural Impact:**
- **LOW** - Enhancement to rule creation workflow
- Need better support for multiple conditions in `predicate_json` and UI

**Questions:**
- How are multiple conditions specified? (Natural language? JSON? SQL?)
- What dimensions are available in Use Case 3 input table?
- Should we support OR/NOT logic, or AND only?

---

#### Type 3: Node Arithmetic Operations

**Pattern:** `NODE 5 = NODE 3 + NODE 4`

**Example:**
- **NOT** a fact table filter
- Arithmetic operations between hierarchy nodes
- Parent node = Sum of specific child nodes (not natural rollup)

**Current System Support:**
- ❌ **NOT SUPPORTED** - This is a **fundamental new capability**
- Current system only supports fact table filtering via `sql_where`
- Type 3 rules require:
  - Node reference resolution
  - Arithmetic expression evaluation
  - Dependency resolution
  - New execution phase in waterfall

**Architectural Impact:**
- **CRITICAL** - Requires major architectural changes
- New rule type classification
- New execution engine for arithmetic rules
- Dependency resolution system
- Potential circular dependency detection

**Questions:**
- What arithmetic operations are needed? (+, -, *, /, complex formulas?)
- How are node references specified? (node_id? node_name? position?)
- Execution order? (Bottom-up? Top-down? Dependency-based?)
- Can Type 3 reference nodes with Type 1/2 rules?
- How to handle circular dependencies?

---

## 2. Current System Analysis

### 2.1 Current Rule Storage

**Table:** `metadata_rules`
```sql
rule_id (PK)
use_case_id (FK)
node_id (FK)
predicate_json (JSONB)  -- UI/GenAI state
sql_where (TEXT)        -- SQL WHERE clause for execution
logic_en (TEXT)         -- Natural language description
```

**Current Limitations:**
- Only supports fact table filtering (`sql_where`)
- No rule type classification
- No support for node arithmetic
- No dependency tracking

### 2.2 Current Waterfall Execution

**Current Flow:**
1. Load hierarchy
2. Calculate natural rollups (bottom-up aggregation)
3. Apply rule overrides (top-down, using `sql_where` filters)
4. Calculate reconciliation plugs

**Type 1/2 Rules:**
- ✅ Compatible with current waterfall
- Applied in step 3 (rule overrides)
- Filter fact table, override node value

**Type 3 Rules:**
- ❌ **BREAKS CURRENT WATERFALL**
- Not fact table filters
- Need new execution phase
- May require dependency resolution

---

## 3. Architectural Design Questions

### 3.1 Input Table Design

**Q1:** ✅ **ANSWERED** - Input table schema confirmed (see Section 1.1)
- **Dimensions:** Cost Center, Division, Business Area, Product Line, Strategy, Process 1, Process 2, Book
- **Measures:** Daily_PNL, Daily_Commission, Daily_Trade
- **Follow-up:** Should we add `pnl_date` and `use_case_id` columns?

**Q2:** Should input tables be:
- **Option A:** Physical tables per use case (`fact_pnl_use_case_3`)
  - Pros: Better isolation, performance
  - Cons: More complex, many tables
- **Option B:** Views filtering `fact_pnl_entries` by `use_case_id`
  - Pros: Simpler, shared storage
  - Cons: Less isolation
- **Option C:** Dynamic table reference in `use_cases` table
  - Pros: Flexible, metadata-driven
  - Cons: Requires metadata management

**Q3:** How is data loaded into input tables?
- Manual import?
- ETL from external system?
- API integration?
- Excel/CSV upload?

**Q4:** Should all use cases migrate to separate tables, or only new ones?
- Backward compatibility requirement
- Migration strategy

---

### 3.2 Type 3 Rule Design

**Q5:** What arithmetic operations are needed?
- Addition: `NODE_A + NODE_B`
- Subtraction: `NODE_A - NODE_B`
- Multiplication: `NODE_A * NODE_B`
- Division: `NODE_A / NODE_B`
- Complex: `(NODE_A + NODE_B) * 0.5`
- Functions: `SUM(NODE_A, NODE_B, NODE_C)`, `MAX(NODE_A, NODE_B)`

**Q6:** How are node references specified?
- By `node_id`? (e.g., "NODE_3")
- By `node_name`? (e.g., "Core Trading")
- By position in hierarchy? (e.g., "3rd child")
- By path? (e.g., "ROOT > Americas > Core")

**Q7:** Execution order for Type 3 rules?
- **Option A:** Bottom-up (children calculated first)
  - Pros: Natural dependency resolution
  - Cons: May not work for all formulas
- **Option B:** Top-down (parents calculated first)
  - Pros: Matches current waterfall
  - Cons: May reference uncalculated nodes
- **Option C:** Dependency-based (calculate dependencies first)
  - Pros: Handles complex dependencies
  - Cons: More complex, requires dependency graph

**Q8:** Can Type 3 rules reference nodes with Type 1/2 rules?
- Example: `NODE_5 = NODE_3 + NODE_4` where NODE_3 has Type 1 rule
- Should use rule-adjusted value or natural value?
- Execution order: Type 1/2 first, then Type 3?

**Q9:** How to handle circular dependencies?
- Example: `NODE_3 = NODE_4 + 100`, `NODE_4 = NODE_3 - 50`
- Detection: Build dependency graph, detect cycles
- Prevention: Validation on rule creation
- Error handling: Fail gracefully with clear error message

**Q10:** Reconciliation plugs for Type 3 rules?
- `Plug = Type3_Value - SUM(Children_Natural)`?
- `Plug = Type3_Value - SUM(Children_Adjusted)`?
- No plug needed (Type 3 is the source of truth)?

---

### 3.3 Waterfall Execution Design

**Q11:** Execution order for mixed rule types?
- **Proposed Flow:**
  1. Phase 1: Natural rollup (bottom-up)
  2. Phase 2: Type 1/2 rules (top-down, fact filters)
  3. Phase 3: Type 3 rules (node arithmetic) - **NEW**
  4. Phase 4: Reconciliation plugs

**Q12:** How to handle Type 3 rules that reference nodes with Type 1/2 rules?
- Use rule-adjusted value from Phase 2?
- Use natural value from Phase 1?
- Configurable per rule?

**Q13:** Performance impact of Type 3 rules?
- Dependency resolution overhead?
- Multiple passes through hierarchy?
- Caching strategy?

---

### 3.4 Database Schema Changes

**Q14:** How to store Type 3 rules?
- **Proposed Schema:**
  ```sql
  ALTER TABLE metadata_rules ADD COLUMN rule_type VARCHAR(20) DEFAULT 'FILTER';
  -- Values: 'FILTER' (Type 1/2), 'ARITHMETIC' (Type 3)
  
  ALTER TABLE metadata_rules ADD COLUMN rule_expression TEXT;
  -- For Type 3: "NODE_5 = NODE_3 + NODE_4"
  
  ALTER TABLE metadata_rules ADD COLUMN rule_dependencies JSONB;
  -- For Type 3: ["NODE_3", "NODE_4"] - list of referenced nodes
  ```

**Q15:** Backward compatibility?
- Should existing rules (Type 1/2 only) work unchanged?
- Require migration to new schema?
- Support both old and new formats?

---

### 3.5 Excel File Structure

**Q16:** Can Excel file be provided?
- Upload to workspace?
- Share structure details?
- Provide sample data?

**Q17:** ✅ **PARTIALLY ANSWERED** - Input table structure confirmed (see Section 1.1)
- **Still Need:**
  - Hierarchy structure? (Level, NODE_ID, Node name columns from Excel tab "Business rule for use case 3")
  - Derivation logic? (Column D format)
  - Business rule definition? (Column E format)
  - Sample business rules from Excel to understand Type 1, 2, 3 patterns

---

## 4. Design Recommendations

### 4.1 High-Level Architecture

**Required Components:**
1. **Rule Type System** - Classify rules as Type 1, 2, or 3
2. **Arithmetic Rule Engine** - Execute Type 3 rules with dependency resolution
3. **Input Table Management** - Per-use-case input tables/views
4. **Structure Import** - Excel-based structure creation
5. **Enhanced Waterfall** - Multi-phase execution supporting all rule types

### 4.2 Proposed Execution Flow

**Enhanced Waterfall:**
```
Phase 1: Natural Rollup
  - Load hierarchy
  - Load input data (use-case specific table)
  - Calculate natural rollups (bottom-up)

Phase 2: Filter Rules (Type 1/2)
  - Load Type 1/2 rules
  - Apply fact table filters (top-down)
  - Override node values

Phase 3: Arithmetic Rules (Type 3) - NEW
  - Load Type 3 rules
  - Build dependency graph
  - Detect circular dependencies
  - Execute in dependency order
  - Override node values

Phase 4: Reconciliation Plugs
  - Calculate plugs for all overridden nodes
  - Formula: Plug = Override_Value - SUM(Children_Adjusted)
```

### 4.3 Database Schema Enhancements

**Option A: Extend `metadata_rules` table**
```sql
ALTER TABLE metadata_rules ADD COLUMN rule_type VARCHAR(20) DEFAULT 'FILTER';
ALTER TABLE metadata_rules ADD COLUMN rule_expression TEXT;
ALTER TABLE metadata_rules ADD COLUMN rule_dependencies JSONB;
```

**Option B: Separate table for Type 3 rules**
```sql
CREATE TABLE metadata_arithmetic_rules (
    rule_id INTEGER PRIMARY KEY REFERENCES metadata_rules(rule_id),
    rule_expression TEXT NOT NULL,
    rule_dependencies JSONB NOT NULL
);
```

**Recommendation:** Option A (extend existing table) for simplicity and backward compatibility.

---

## 5. Implementation Phases

### Phase 5.6: Input Table Per Use Case
- Design input table schema per use case
- Implement table/view creation
- Update waterfall to use use-case specific tables
- **Estimated Effort:** Medium

### Phase 5.7: Rule Type System
- Add `rule_type` to `metadata_rules`
- Update rule creation UI/API
- Support Type 1, Type 2, Type 3 classification
- **Estimated Effort:** Low

### Phase 5.8: Type 3 Rule Engine
- Implement arithmetic rule execution
- Dependency resolution algorithm
- Circular dependency detection
- Integration with waterfall
- **Estimated Effort:** High (Critical)

### Phase 5.9: Structure Import
- Excel import functionality
- Structure creation from Excel
- Validation and error handling
- **Estimated Effort:** Medium

### Phase 5.10: Backward Compatibility
- Ensure existing use cases work
- Migration path for existing rules
- Testing and validation
- **Estimated Effort:** Medium

---

## 6. Critical Risks

### Risk 1: Type 3 Rule Complexity
- **Severity:** HIGH
- **Impact:** Circular dependencies, infinite loops, incorrect calculations
- **Mitigation:** Dependency graph validation, cycle detection, comprehensive testing

### Risk 2: Performance Degradation
- **Severity:** MEDIUM
- **Impact:** Multiple passes through hierarchy, dependency resolution overhead
- **Mitigation:** Efficient dependency graph algorithms, caching, performance testing

### Risk 3: Backward Compatibility
- **Severity:** HIGH
- **Impact:** Existing use cases may break
- **Mitigation:** Default `rule_type='FILTER'`, migration scripts, comprehensive testing

### Risk 4: Input Table Management
- **Severity:** MEDIUM
- **Impact:** Data isolation, table proliferation, maintenance overhead
- **Mitigation:** Clear design decision (physical tables vs views), automated table creation

---

## 7. Next Steps

1. **Answer Critical Questions** (Sections 3.1 - 3.5)
2. **Provide Excel File** (Section 3.5, Q16-Q17)
3. **Finalize Design** based on answers
4. **Create Detailed Implementation Plan**
5. **Design Review Approval**
6. **Implement in Phases** (5.6 → 5.10)

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-01  
**Status:** Design Review - Analysis Complete, Awaiting Answers

