# Phase 5 Enhancement Queries: Structure Management & Use Case Design

**Document Purpose:** Architectural design review and enhancement planning for Finance-Insight structure management and use case workflows.

**Status:** Design Review - Questions Accumulation Phase  
**Date:** 2026-01-01  
**Reviewer:** Principal Software Architect

---

## Executive Summary

This document captures architectural questions, concerns, and design alternatives for enhancing the Finance-Insight system's structure management capabilities. The current design treats Atlas structures as implicit entities (derived from hierarchy nodes), which raises concerns about data integrity, auditability, and operational excellence for production financial systems.

---

## 1. Current Design Analysis

### 1.1 Atlas Structure Storage (Current State)

**How Structures Are Stored:**
- Structures are **NOT** stored in a separate table
- Structures are identified by the `atlas_source` field on `dim_hierarchy` nodes
- Each hierarchy node has `atlas_source` (String) indicating which structure it belongs to
- The `/api/v1/structures` endpoint queries distinct `atlas_source` values from `dim_hierarchy`
- A structure "exists" if at least one `dim_hierarchy` node has that `atlas_source` value

**Database Schema:**
```sql
-- Current: No dedicated structures table
-- Structures are implicit via dim_hierarchy.atlas_source

dim_hierarchy:
  - node_id (PK)
  - parent_node_id (FK)
  - node_name
  - atlas_source (String) -- Structure identifier
  - is_leaf
  - depth
```

**API Endpoints:**
- `GET /api/v1/structures` - Queries `dim_hierarchy` for distinct `atlas_source` values
- Returns: `{structure_id, name, node_count}`

### 1.2 Use Case to Structure Mapping (Current State)

**Mapping Mechanism:**
- `use_cases.atlas_structure_id` (String, NOT NULL) references the structure
- When creating a use case, API validates structure exists by checking `DimHierarchy.atlas_source`
- Multiple use cases can share the same `atlas_structure_id` (one structure → many use cases)
- Mapping is stored on use case; no separate mapping table

**Validation Logic:**
```python
# Current validation in use_cases.py
structure_exists = db.query(DimHierarchy).filter(
    DimHierarchy.atlas_source == atlas_structure_id
).first()
```

**Workflow:**
1. Tab 1 loads structures via `/api/v1/structures`
2. User selects structure from dropdown
3. When creating use case, `atlas_structure_id` is set to selected structure
4. API validates structure exists before creating use case

---

## 2. Key Assumptions Identified

### 2.1 User Assumptions (To Be Validated)

1. **"New use case needs new structure"**
   - **Reality:** Not necessarily true - multiple use cases can share a structure
   - **Question:** What is the actual business requirement?

2. **"Structures are managed entities"**
   - **Reality:** Currently structures are implicit (derived from hierarchy nodes)
   - **Question:** Should structures be first-class entities with lifecycle management?

3. **"Structure creation is explicit"**
   - **Reality:** Currently implicit (created when hierarchy nodes are imported)
   - **Question:** Should there be explicit structure creation/import workflow?

4. **"Structure metadata exists"**
   - **Reality:** Currently only `structure_id` and `node_count` are exposed
   - **Question:** What metadata is needed? (description, owner, version, import date, etc.)

---

## 3. Primary Concerns / Risks

### 3.1 Technical Risks

#### Risk 1: No Structure Lifecycle Management
- **Issue:** No explicit structure creation/deletion
- **Impact:** Structures are "discovered" from hierarchy nodes, not managed
- **Severity:** HIGH
- **Mitigation:** Create `dim_atlas_structures` table

#### Risk 2: Data Integrity Issues
- **Issue:** If all nodes for a structure are deleted, structure "disappears" but use cases still reference it
- **Impact:** Orphaned use cases, broken foreign key relationships
- **Severity:** CRITICAL
- **Mitigation:** Foreign key constraint from `use_cases.atlas_structure_id` → `dim_atlas_structures.structure_id`

#### Risk 3: Structure Versioning/Evolution
- **Issue:** If structure changes (nodes added/removed), all use cases using it are affected
- **Impact:** No way to track structure versions or changes over time
- **Severity:** HIGH
- **Mitigation:** Structure versioning table or immutable structures

#### Risk 4: Performance Concerns
- **Issue:** `/api/v1/structures` does `GROUP BY` on `dim_hierarchy` - may be slow with large hierarchies
- **Impact:** Slow structure listing, poor UX
- **Severity:** MEDIUM
- **Mitigation:** Dedicated structures table with indexes

### 3.2 Domain / Regulatory Risks

#### Risk 5: Auditability
- **Issue:** No audit trail of when structures were created/imported
- **Impact:** Cannot prove structure lineage for regulatory purposes
- **Severity:** HIGH (for production financial systems)
- **Mitigation:** Structure metadata with timestamps, owner, source system

#### Risk 6: Data Governance
- **Issue:** No structure ownership or approval workflow
- **Impact:** Multiple users could create conflicting structures with same `atlas_source`
- **Severity:** MEDIUM
- **Mitigation:** Structure registry with unique constraints, approval workflow

#### Risk 7: Compliance
- **Issue:** If structure represents official org chart, changes should be controlled
- **Impact:** No way to prevent accidental structure modifications
- **Severity:** HIGH (for regulatory compliance)
- **Mitigation:** Immutable structures or versioning with approval workflow

### 3.3 Scalability / Operability Risks

#### Risk 8: Structure Proliferation
- **Issue:** No naming conventions enforced for `atlas_source`
- **Impact:** Risk of typos creating duplicate structures (e.g., "MOCK_ATLAS_v1" vs "MOCK_ATLAS_V1")
- **Severity:** MEDIUM
- **Mitigation:** Structure registry with unique constraints, naming conventions

#### Risk 9: Multi-Tenancy Issues
- **Issue:** If multiple teams use system, structure naming conflicts are likely
- **Impact:** Structure collisions, data contamination
- **Severity:** MEDIUM
- **Mitigation:** Namespace/prefix mechanism or structure ownership

---

## 4. Design Disagreements (Current vs. Recommended)

### 4.1 Structures as Implicit Entities

**Current Design:**
- Structures are derived from hierarchy nodes
- No explicit structure management

**Disagreement:**
- Structures should be first-class entities with their own table
- Current design makes structure management reactive, not proactive

**Recommendation:**
- Create `dim_atlas_structures` table
- Structures become explicit, manageable entities

### 4.2 No Structure Import API

**Current Design:**
- Structures are created implicitly when hierarchy nodes are imported
- No explicit "import structure" workflow

**Disagreement:**
- Should have explicit structure import/creation workflow
- Users should be able to create structures before importing nodes

**Recommendation:**
- Add `POST /api/v1/structures` endpoint
- Explicit structure creation before hierarchy import

### 4.3 Validation Logic in Use Case Creation

**Current Design:**
- Validates structure by checking if any node exists with that `atlas_source`
- Fragile - what if structure exists but has zero nodes?

**Disagreement:**
- Validation should check against structures table, not hierarchy nodes
- Structure existence should be independent of node count

**Recommendation:**
- Validate against `dim_atlas_structures` table
- Structure can exist with zero nodes (empty structure)

### 4.4 No Structure Metadata

**Current Design:**
- Only `structure_id` and `node_count` are exposed
- Missing: description, owner, import date, version, status

**Disagreement:**
- Production systems need structure metadata for governance
- Auditability requires metadata fields

**Recommendation:**
- Add structure metadata fields
- Support structure description, owner, version, status, etc.

---

## 5. Alternative Approaches

### Option A: Explicit Structure Management (RECOMMENDED)

**New Table: `dim_atlas_structures`**
```sql
CREATE TABLE dim_atlas_structures (
    structure_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id VARCHAR(100),
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'ACTIVE', -- ACTIVE, DRAFT, ARCHIVED
    version VARCHAR(20),
    source_system VARCHAR(100), -- e.g., "ATLAS_API", "MANUAL", "MOCK"
    created_by VARCHAR(100),
    last_modified_at TIMESTAMP,
    last_modified_by VARCHAR(100)
);

-- Foreign key constraint
ALTER TABLE use_cases 
ADD CONSTRAINT fk_use_case_structure 
FOREIGN KEY (atlas_structure_id) 
REFERENCES dim_atlas_structures(structure_id);
```

**Benefits:**
- Structures are first-class entities
- Explicit lifecycle management
- Better auditability
- Foreign key constraints prevent orphaned use cases
- Faster structure listing (no GROUP BY on large table)

**Workflow:**
1. User creates/imports structure → `POST /api/v1/structures`
2. System imports hierarchy nodes with `atlas_source = structure_id`
3. User creates use case → selects from existing structures

**API Changes:**
- `POST /api/v1/structures` - Create/import structure
- `GET /api/v1/structures` - Query structures table (not hierarchy)
- `PUT /api/v1/structures/{structure_id}` - Update structure metadata
- `DELETE /api/v1/structures/{structure_id}` - Delete structure (with cascade rules)

### Option B: Structure Registry Pattern

**New Table: `structure_registry`**
- Stores structure metadata
- `dim_hierarchy.atlas_source` references `structure_registry.structure_id`
- Allows structure metadata without changing hierarchy table

**Benefits:**
- Minimal changes to existing hierarchy table
- Structure metadata separate from hierarchy

**Drawbacks:**
- Still requires foreign key management
- Two places to check for structure existence

### Option C: Keep Current Design (NOT RECOMMENDED)

**Pros:**
- Simpler (no new table)
- Less code changes

**Cons:**
- All risks mentioned above remain
- Not scalable for production use
- Poor data integrity
- No auditability

---

## 6. Enhancement Queries (To Be Answered)

### 6.1 Structure Lifecycle Management

**Q1.1:** Can structures be deleted? What happens to use cases that reference them?
- **Options:**
  - Prevent deletion if use cases exist (CASCADE RESTRICT)
  - Allow deletion with cascade to use cases
  - Soft delete (mark as ARCHIVED)

**Q1.2:** Can structures be modified after creation? What is the versioning strategy?
- **Options:**
  - Immutable structures (recommended for auditability)
  - Mutable structures with versioning
  - Mutable structures without versioning (not recommended)

**Q1.3:** Who can create/modify structures? Is there role-based access control?
- **Options:**
  - Admin-only structure creation
  - User-level structure creation
  - Approval workflow for structure creation

### 6.2 Structure Import Workflow

**Q2.1:** How are structures imported from Atlas? API? File upload? Manual entry?
- **Options:**
  - Atlas API integration
  - CSV/JSON file upload
  - Manual node-by-node entry
  - Hybrid (API with manual override)

**Q2.2:** What happens if import fails partway through?
- **Options:**
  - Transaction rollback (all or nothing)
  - Partial import with error reporting
  - Retry mechanism

**Q2.3:** Can structures be imported incrementally (add nodes to existing structure)?
- **Options:**
  - Yes, incremental imports allowed
  - No, full replacement only
  - Yes, but with versioning

### 6.3 Structure Relationships

**Q3.1:** Can use cases change structures after creation?
- **Options:**
  - No, immutable after creation (recommended)
  - Yes, with validation
  - Yes, with migration of rules

**Q3.2:** Can one use case reference multiple structures?
- **Options:**
  - No, one structure per use case (current design)
  - Yes, multiple structures per use case
  - Yes, with structure hierarchy/merging

**Q3.3:** What if a structure is "deprecated" but use cases still reference it?
- **Options:**
  - Prevent deprecation if use cases exist
  - Allow deprecation with warning
  - Migration path to new structure

### 6.4 Data Volume & Performance

**Q4.1:** How many structures are expected? (10s? 100s? 1000s?)
- **Impact:** Determines indexing strategy, caching requirements

**Q4.2:** How many nodes per structure? (Current: 21 nodes for mock structure)
- **Impact:** Performance of structure listing, hierarchy loading

**Q4.3:** What are performance requirements for structure listing?
- **Options:**
  - < 100ms for structure list
  - < 500ms acceptable
  - < 1s acceptable

### 6.5 Business Rules & Constraints

**Q5.1:** Are structures immutable once created? (Recommended for auditability)
- **Options:**
  - Yes, immutable (recommended)
  - No, mutable with versioning
  - No, mutable without versioning

**Q5.2:** Can structures be "cloned" for new periods?
- **Options:**
  - Yes, structure cloning with new structure_id
  - Yes, structure versioning
  - No, create new structure manually

**Q5.3:** What is the relationship between structures and fact data?
- **Current:** `fact_pnl_gold.cc_id` maps to hierarchy leaf nodes
- **Question:** Is this mapping structure-specific or global?

### 6.6 User Experience (Tab 1 Workflow)

**Q6.1:** When user creates a new use case, can they create a new structure on-the-fly?
- **Options:**
  - Yes, inline structure creation in Tab 1
  - No, structures must be pre-created by admin
  - Yes, but with approval workflow

**Q6.2:** What is the UX for structure selection/creation?
- **Options:**
  - Dropdown with "Create New" option
  - Separate structure management screen
  - Wizard: Structure → Hierarchy → Use Case

**Q6.3:** Should structure import be part of Tab 1 or separate admin screen?
- **Options:**
  - Part of Tab 1 (user-facing)
  - Separate admin screen
  - Both (admin creates, user selects)

### 6.7 Structure Metadata Requirements

**Q7.1:** What metadata fields are required for structures?
- **Current:** Only `structure_id` and `node_count`
- **Proposed:** `name`, `description`, `owner_id`, `imported_at`, `status`, `version`, `source_system`
- **Question:** Are there additional fields needed?

**Q7.2:** Should structures have a "friendly name" separate from `structure_id`?
- **Options:**
  - Yes, `name` field for display
  - No, use `structure_id` as display name
  - Yes, with localization support

**Q7.3:** Should structures track their source system (Atlas, Manual, Mock)?
- **Options:**
  - Yes, for auditability
  - No, not needed
  - Yes, with source system metadata

### 6.8 Structure Validation & Constraints

**Q8.1:** Should structure names be unique? (Prevent duplicates)
- **Options:**
  - Yes, unique constraint on `structure_id`
  - Yes, unique constraint on `name` (separate from ID)
  - No, allow duplicates

**Q8.2:** Should structures validate hierarchy integrity on import?
- **Options:**
  - Yes, validate parent-child relationships
  - Yes, validate single root node
  - No, allow any hierarchy structure

**Q8.3:** Should structures validate leaf node mapping to fact data?
- **Options:**
  - Yes, validate all leaf nodes have corresponding fact data
  - No, allow structures with unmapped leaf nodes
  - Yes, with warnings only

---

## 7. Recommended Approach (Pending Answers)

### 7.1 High-Level Recommendation

**Option A: Explicit Structure Management** is recommended for production financial systems due to:
- Data integrity (foreign key constraints)
- Auditability (structure metadata, timestamps)
- Operational excellence (explicit lifecycle management)
- Regulatory compliance (lineage tracking)

### 7.2 Implementation Phases

**Phase 5.1: Structure Table Creation**
- Create `dim_atlas_structures` table
- Migrate existing structures (extract distinct `atlas_source` values)
- Add foreign key constraint to `use_cases`

**Phase 5.2: Structure API Enhancement**
- Add `POST /api/v1/structures` endpoint
- Update `GET /api/v1/structures` to query structures table
- Add structure metadata fields

**Phase 5.3: Use Case Validation Update**
- Update `POST /api/v1/use-cases` to validate against structures table
- Remove dependency on hierarchy nodes for structure validation

**Phase 5.4: Frontend Updates**
- Update Tab 1 to support structure creation
- Add structure metadata display
- Update structure selection workflow

**Phase 5.5: Structure Import Workflow**
- Implement structure import from Atlas API (if applicable)
- Add structure import validation
- Add error handling and rollback

---

## 8. Next Steps

1. **Answer Enhancement Queries** (Sections 6.1 - 6.8)
2. **Finalize Structure Design** based on answers
3. **Create Detailed Implementation Plan** with migration strategy
4. **Design Review Approval** before implementation
5. **Implement in Phases** (5.1 → 5.5)

---

## 9. Additional Requirements: Use Case 3 - America Cash Equity Trading

### 9.1 Overview

**Use Case 3:** America Cash Equity Trading Structure  
**New Structure:** "America Cash Equity Trading Structure"  
**Source:** Excel file with two tabs:
- Tab 1: "Input table for use case 3" - Describes input table structure
- Tab 2: "Business rule for use case 3" - Contains business rules and hierarchy structure

**Key Requirements:**
1. Each use case should have a **separate input table/view**
2. New structure creation from Excel hierarchy definition
3. Three types of business rules (Type 1, Type 2, Type 3)
4. Support existing and new use cases simultaneously

---

### 9.2 Input Table Per Use Case Requirement

**Current State:**
- `fact_pnl_gold` - Shared fact table (all use cases)
- `fact_pnl_entries` - Use-case specific (has `use_case_id` FK)

**New Requirement:**
- Each use case should have its **own dedicated input table/view**
- Use Case 3 needs a separate input table

**Questions:**
- **Q9.2.1:** Should input tables be:
  - Physical tables per use case? (e.g., `fact_pnl_use_case_3`)
  - Views pointing to a shared source?
  - Use-case filtered views of `fact_pnl_entries`?

- **Q9.2.2:** What is the schema of the input table for Use Case 3?
  - What columns does it have?
  - What dimensions are present? (Strategy, PROCESS_2, etc.)
  - What measures? (DAILY_PNL, MTD_PNL, YTD_PNL?)

- **Q9.2.3:** How is input data loaded?
  - Manual import?
  - ETL from external system?
  - API integration?

- **Q9.2.4:** Should input tables be:
  - Created automatically when use case is created?
  - Created manually by admin?
  - Imported from Excel/CSV?

---

### 9.3 Structure Creation from Excel

**Requirement:**
- Create new structure "America Cash Equity Trading Structure" from Excel
- Excel tab "Business rule for use case 3" contains:
  - Column "Level" = hierarchy level (parent-child relationships)
  - Column "NODE_ID" = hierarchy node identifier
  - Column "Node name" = hierarchy node display name
  - Column "D" = Derivation logic
  - Column "E" = Business rule definition

**Questions:**
- **Q9.3.1:** What is the exact hierarchy structure in the Excel?
  - How many levels?
  - What is the root node?
  - What are the leaf nodes?

- **Q9.3.2:** How should structure be imported?
  - Excel file upload?
  - Manual entry via UI?
  - API endpoint for structure import?

- **Q9.3.3:** Should structure import:
  - Create hierarchy nodes automatically?
  - Validate hierarchy integrity?
  - Support incremental updates?

---

### 9.4 Business Rule Types

#### Type 1: Simple Dimension Filtering
**Pattern:** `SUM(DAILY_PNL) WHERE Strategy='NODE_NAME'`

**Description:**
- Node name maps directly to a dimension value
- Example: Node "CORE" means `WHERE Strategy='CORE'`
- Simple one-to-one mapping: Node Name → Dimension Value

**Current System Support:**
- ✅ **Supported** - Current `sql_where` can handle: `WHERE strategy_id = 'CORE'`
- ⚠️ **Enhancement Needed:** Need to map node name to dimension value automatically

**Questions:**
- **Q9.4.1:** How is node name mapped to dimension?
  - Exact match? (Node "CORE" → `Strategy='CORE'`)
  - Case-sensitive?
  - Mapping table needed?

- **Q9.4.2:** Which dimensions can be used?
  - Strategy only?
  - Any dimension in input table?
  - Configurable per use case?

#### Type 2: Multi-Condition Filtering
**Pattern:** `SUM(DAILY_PNL) WHERE Strategy='CORE' AND PROCESS_2='Inventory Management'`

**Description:**
- Multiple dimension conditions (AND logic)
- Example: `WHERE Strategy='CORE' AND PROCESS_2='Inventory Management'`
- More complex filtering with multiple dimensions

**Current System Support:**
- ✅ **Supported** - Current `sql_where` can handle: `WHERE strategy_id='CORE' AND process_2='Inventory Management'`
- ⚠️ **Enhancement Needed:** Need to support multiple dimensions in rule definition

**Questions:**
- **Q9.4.3:** How are multiple conditions specified?
  - In `logic_en` field? (Natural language)
  - In `predicate_json`? (Structured JSON)
  - In `sql_where`? (Direct SQL)

- **Q9.4.4:** What dimensions are available in Use Case 3 input table?
  - Strategy?
  - PROCESS_2?
  - Others?

- **Q9.4.5:** Should we support:
  - AND logic only?
  - OR logic?
  - NOT logic?
  - Complex parentheses?

#### Type 3: Node Arithmetic Operations
**Pattern:** `NODE 5 = NODE 3 + NODE 4`

**Description:**
- **NOT** a fact table filter
- Arithmetic operations between hierarchy nodes
- Example: Parent node = Sum of child nodes (but with custom formula)
- Example: Node 5 = Node 3 + Node 4 (not natural rollup)

**Current System Support:**
- ❌ **NOT SUPPORTED** - Current system only supports fact table filtering via `sql_where`
- ⚠️ **MAJOR ENHANCEMENT NEEDED:** This is a new rule type

**Questions:**
- **Q9.4.6:** What arithmetic operations are needed?
  - Addition: `NODE_A + NODE_B`
  - Subtraction: `NODE_A - NODE_B`
  - Multiplication: `NODE_A * NODE_B`
  - Division: `NODE_A / NODE_B`
  - Complex formulas: `(NODE_A + NODE_B) * 0.5`

- **Q9.4.7:** How are node references specified?
  - By `node_id`? (e.g., "NODE_3")
  - By `node_name`? (e.g., "Core Trading")
  - By position in hierarchy?

- **Q9.4.8:** What happens if referenced node doesn't exist?
  - Error?
  - Zero value?
  - Skip rule?

- **Q9.4.9:** Execution order for Type 3 rules?
  - Bottom-up (children calculated first)?
  - Top-down (parents calculated first)?
  - Dependency resolution (calculate dependencies first)?

- **Q9.4.10:** Can Type 3 rules reference nodes with Type 1/2 rules?
  - Example: `NODE_5 = NODE_3 + NODE_4` where NODE_3 has Type 1 rule?
  - Execution order: Type 1/2 first, then Type 3?

- **Q9.4.11:** Can Type 3 rules create circular dependencies?
  - Example: `NODE_3 = NODE_4 + 100`, `NODE_4 = NODE_3 - 50`
  - How to detect/prevent?

---

### 9.5 Waterfall Execution Impact

**Current Waterfall Logic:**
1. Load hierarchy
2. Calculate natural rollups (bottom-up)
3. Apply rule overrides (top-down) using `sql_where` filters
4. Calculate reconciliation plugs

**New Requirements Impact:**

**Type 1 & Type 2 Rules:**
- ✅ Compatible with current waterfall
- Rules still filter fact table
- Applied top-down after natural rollup

**Type 3 Rules:**
- ❌ **BREAKS CURRENT WATERFALL**
- Not fact table filters
- Need new execution phase
- May require dependency resolution

**Questions:**
- **Q9.5.1:** Execution order for mixed rule types?
  - Phase 1: Natural rollup (bottom-up)
  - Phase 2: Type 1/2 rules (top-down, fact filters)
  - Phase 3: Type 3 rules (node arithmetic) - **NEW**
  - Phase 4: Reconciliation plugs

- **Q9.5.2:** How to handle Type 3 rules that reference nodes with Type 1/2 rules?
  - Use rule-adjusted value?
  - Use natural value?
  - Configurable?

- **Q9.5.3:** Reconciliation plugs for Type 3 rules?
  - `Plug = Type3_Value - SUM(Children_Natural)`?
  - `Plug = Type3_Value - SUM(Children_Adjusted)`?
  - No plug needed?

---

### 9.6 Database Schema Changes Required

#### 9.6.1 Rule Type Classification

**Current:** `metadata_rules` table has:
- `sql_where` (Text) - For fact filtering
- `predicate_json` (JSONB) - For UI state
- `logic_en` (Text) - Natural language

**Enhancement Needed:**
- Add `rule_type` field (Enum: 'FILTER', 'ARITHMETIC', 'HYBRID')
- Add `rule_expression` field (Text) - For Type 3 arithmetic formulas
- Add `rule_dependencies` (JSONB) - For Type 3 node references

**Proposed Schema:**
```sql
ALTER TABLE metadata_rules ADD COLUMN rule_type VARCHAR(20) DEFAULT 'FILTER';
-- Values: 'FILTER' (Type 1/2), 'ARITHMETIC' (Type 3), 'HYBRID'

ALTER TABLE metadata_rules ADD COLUMN rule_expression TEXT;
-- For Type 3: "NODE_5 = NODE_3 + NODE_4"

ALTER TABLE metadata_rules ADD COLUMN rule_dependencies JSONB;
-- For Type 3: ["NODE_3", "NODE_4"] - list of referenced nodes
```

#### 9.6.2 Input Table Per Use Case

**Option A: Physical Tables**
```sql
-- Create table per use case
CREATE TABLE fact_pnl_use_case_3 (
    id UUID PRIMARY KEY,
    -- columns from Excel "Input table for use case 3"
    strategy VARCHAR(50),
    process_2 VARCHAR(50),
    daily_pnl NUMERIC(18,2),
    -- ... other columns
    use_case_id UUID REFERENCES use_cases(use_case_id)
);
```

**Option B: Use-Case Filtered Views**
```sql
-- Create view per use case
CREATE VIEW fact_pnl_use_case_3 AS
SELECT * FROM fact_pnl_entries
WHERE use_case_id = '...';
```

**Option C: Dynamic Table Reference**
```sql
-- Add table_name to use_cases
ALTER TABLE use_cases ADD COLUMN input_table_name VARCHAR(100);
-- e.g., "fact_pnl_use_case_3"
```

**Questions:**
- **Q9.6.1:** Which approach for input tables?
  - Physical tables (Option A) - Better isolation, more complex
  - Views (Option B) - Simpler, shared storage
  - Dynamic reference (Option C) - Flexible, requires metadata

---

### 9.7 Backward Compatibility

**Requirement:**
- Support existing use cases (Use Case 1, Use Case 2)
- Support new Use Case 3 with new rule types
- Ensure waterfall works for both

**Questions:**
- **Q9.7.1:** Should existing use cases:
  - Continue using `fact_pnl_gold`?
  - Migrate to use-case specific tables?
  - Support both?

- **Q9.7.2:** Should existing rules (Type 1/2 only):
  - Work unchanged?
  - Require migration to new schema?
  - Support both old and new formats?

- **Q9.7.3:** Should waterfall engine:
  - Detect rule type and execute accordingly?
  - Support both execution modes?
  - Require separate execution paths?

---

### 9.8 Excel File Structure (To Be Clarified)

**Missing Information:**
- Excel file not yet provided in workspace
- Need to see actual structure to design properly

**Questions:**
- **Q9.8.1:** Can Excel file be provided?
  - Upload to workspace?
  - Share structure details?
  - Provide sample data?

- **Q9.8.2:** What is the exact format of:
  - Input table columns?
  - Hierarchy structure (Level, NODE_ID, Node name)?
  - Derivation logic (Column D)?
  - Business rule definition (Column E)?

---

## 10. Design Recommendations (Pending Answers)

### 10.1 High-Level Architecture Changes

**Required Enhancements:**
1. **Rule Type System** - Add rule type classification
2. **Arithmetic Rule Engine** - New execution phase for Type 3 rules
3. **Input Table Management** - Per-use-case input tables/views
4. **Structure Import** - Excel-based structure creation
5. **Dependency Resolution** - For Type 3 rule execution order

### 10.2 Implementation Phases

**Phase 5.6: Input Table Per Use Case**
- Design input table schema per use case
- Implement table/view creation
- Update waterfall to use use-case specific tables

**Phase 5.7: Rule Type System**
- Add `rule_type` to `metadata_rules`
- Update rule creation UI/API
- Support Type 1, Type 2, Type 3 rules

**Phase 5.8: Type 3 Rule Engine**
- Implement arithmetic rule execution
- Dependency resolution
- Integration with waterfall

**Phase 5.9: Structure Import**
- Excel import functionality
- Structure creation from Excel
- Validation and error handling

**Phase 5.10: Backward Compatibility**
- Ensure existing use cases work
- Migration path for existing rules
- Testing and validation

---

## 11. Critical Questions Summary

### Must Answer Before Design:

1. **Input Table Structure:**
   - What columns in Use Case 3 input table?
   - What dimensions available?
   - Physical table vs view?

2. **Type 3 Rule Details:**
   - What arithmetic operations needed?
   - How to specify node references?
   - Execution order and dependencies?

3. **Excel File:**
   - Can Excel be provided?
   - What is exact structure?
   - Sample data available?

4. **Backward Compatibility:**
   - How to handle existing use cases?
   - Migration strategy?
   - Support both old and new?

5. **Waterfall Execution:**
   - Execution order for mixed rules?
   - Reconciliation plugs for Type 3?
   - Performance impact?

---

## Appendix A: Current Code References

### Structure Listing Endpoint
```186:224:app/api/routes/discovery.py
@router.get("/structures")
def list_structures(db: Session = Depends(get_db)):
    """
    List all available Atlas structures.
    
    Returns list of structures with metadata (structure_id, name, node_count).
    """
    from app.models import DimHierarchy
    from sqlalchemy import func
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Get distinct structures with counts (filter out NULL atlas_source)
    structures = db.query(
        DimHierarchy.atlas_source,
        func.count(DimHierarchy.node_id).label('node_count')
    ).filter(
        DimHierarchy.atlas_source.isnot(None)  # Filter out NULL structures
    ).group_by(DimHierarchy.atlas_source).all()
    
    logger.info(f"Structures: Found {len(structures)} structures in database")
    
    result = []
    for structure_id, node_count in structures:
        if structure_id:  # Additional safety check
            # Generate friendly name from structure_id
            name = structure_id.replace('_', ' ').title()
            if structure_id.startswith('MOCK_ATLAS'):
                name = f"Mock Atlas Structure {structure_id.split('_')[-1]}"
            
            result.append({
                "structure_id": structure_id,
                "name": name,
                "node_count": node_count
            })
    
    logger.info(f"Structures: Returning {len(result)} valid structures")
    return {"structures": result}
```

### Use Case Creation with Structure Validation
```18:77:app/api/routes/use_cases.py
@router.post("/use-cases")
def create_use_case(
    name: str,
    description: Optional[str] = None,
    owner_id: str = "default_user",
    atlas_structure_id: str = None,
    db: Session = Depends(get_db)
):
    """
    Create a new use case.
    
    Args:
        name: Use case name (e.g., "America Trading P&L")
        description: Optional description
        owner_id: Owner user ID
        atlas_structure_id: Atlas structure identifier (required)
    
    Returns:
        Created use case with UUID
    """
    if not atlas_structure_id:
        raise HTTPException(
            status_code=400,
            detail="atlas_structure_id is required"
        )
    
    # Verify structure exists
    from app.models import DimHierarchy
    structure_exists = db.query(DimHierarchy).filter(
        DimHierarchy.atlas_source == atlas_structure_id
    ).first()
    
    if not structure_exists:
        raise HTTPException(
            status_code=404,
            detail=f"Structure '{atlas_structure_id}' not found"
        )
    
    # Create use case
    use_case = UseCase(
        name=name,
        description=description,
        owner_id=owner_id,
        atlas_structure_id=atlas_structure_id,
        status=UseCaseStatus.DRAFT
    )
    
    db.add(use_case)
    db.commit()
    db.refresh(use_case)
    
    return {
        "use_case_id": str(use_case.use_case_id),
        "name": use_case.name,
        "description": use_case.description,
        "owner_id": use_case.owner_id,
        "atlas_structure_id": use_case.atlas_structure_id,
        "status": use_case.status.value,
        "created_at": use_case.created_at.isoformat()
    }
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-01  
**Status:** Design Review - Questions Accumulation

