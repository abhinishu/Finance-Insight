# Phase 5: Use Case 3 Implementation Plan

**Document Purpose:** Comprehensive phased implementation plan with backward compatibility, testing strategy, UI changes, and risk mitigation

**Status:** Implementation Planning  
**Date:** 2026-01-01  
**Priority:** High - Production System Enhancement

---

## Executive Summary

This plan implements Use Case 3 ("America Cash Equity Trading Structure") with:
- ✅ **Backward Compatibility** - Existing use cases continue to work
- ✅ **Incremental Testing** - Each phase is tested before proceeding
- ✅ **UI Enhancements** - Tab 3 (Rule Editor) refactored to support all rule types
- ✅ **Risk Mitigation** - Comprehensive risk analysis and mitigation strategies
- ✅ **Structure Storage** - New structure stored in database
- ✅ **Phased Approach** - Small, logical phases with testing gates

---

## 1. Backward Compatibility Strategy

### 1.1 Database Schema Changes (Non-Breaking)

**Principle:** All new columns are nullable or have defaults

```sql
-- Phase 5.1: Add new columns (all nullable/default)
ALTER TABLE metadata_rules 
ADD COLUMN rule_type VARCHAR(20) DEFAULT 'FILTER';  -- Default for existing rules

ALTER TABLE metadata_rules 
ADD COLUMN measure_name VARCHAR(50) DEFAULT 'daily_pnl';  -- Default for existing rules

ALTER TABLE metadata_rules 
ADD COLUMN rule_expression TEXT;  -- NULL for existing rules (Type 1/2)

ALTER TABLE metadata_rules 
ADD COLUMN rule_dependencies JSONB;  -- NULL for existing rules (Type 1/2)

-- Phase 5.2: Add input table reference
ALTER TABLE use_cases 
ADD COLUMN input_table_name VARCHAR(100);  -- NULL for existing use cases
```

**Impact:** 
- ✅ Existing rules automatically become `rule_type='FILTER'` (Type 1/2)
- ✅ Existing use cases continue using `fact_pnl_gold` (if `input_table_name` is NULL)
- ✅ No data migration required

### 1.2 Code Changes (Backward Compatible)

**Principle:** Feature flags and version detection

```python
# Waterfall engine - detect rule type
def apply_rule(rule: MetadataRule, facts_df: pd.DataFrame):
    rule_type = rule.rule_type or 'FILTER'  # Default for existing rules
    
    if rule_type == 'FILTER':
        # Existing logic (Type 1/2)
        return apply_filter_rule(rule, facts_df)
    elif rule_type == 'FILTER_ARITHMETIC':
        # New logic (Type 2B)
        return apply_arithmetic_filter_rule(rule, facts_df)
    elif rule_type == 'ARITHMETIC':
        # New logic (Type 3)
        return apply_node_arithmetic_rule(rule, node_values)
```

**Impact:**
- ✅ Existing rules use existing code path
- ✅ New rules use new code path
- ✅ No breaking changes

### 1.3 API Changes (Backward Compatible)

**Principle:** Version-aware endpoints

```python
# Rule creation API - supports both old and new formats
@router.post("/rules")
def create_rule(rule: RuleCreate, db: Session):
    # If rule_type not provided, default to 'FILTER' (backward compatible)
    rule_type = rule.rule_type or 'FILTER'
    
    # If predicate_json is old format (v1.0), convert to new format
    if rule.predicate_json.get('version') == '1.0':
        rule.predicate_json = migrate_to_v2(rule.predicate_json)
```

**Impact:**
- ✅ Existing API calls continue to work
- ✅ New API calls use enhanced features
- ✅ Automatic migration of old format

---

## 2. Testing Strategy

### 2.1 Testing Gates (Per Phase)

**Principle:** No phase proceeds without passing all tests

**Test Categories:**
1. **Unit Tests** - Individual functions/components
2. **Integration Tests** - API endpoints, database operations
3. **Regression Tests** - Existing use cases still work
4. **End-to-End Tests** - Complete workflows

### 2.2 Test Coverage Requirements

**Minimum Coverage:**
- Unit tests: 80% code coverage
- Integration tests: All API endpoints
- Regression tests: All existing use cases
- E2E tests: Critical user workflows

### 2.3 Test Data Strategy

**Separate Test Database:**
- Use separate test database for all testing
- Seed with existing use case data (Use Case 1, Use Case 2)
- Add Use Case 3 test data incrementally

**Test Cases:**
- ✅ Existing use cases (Use Case 1, Use Case 2) - Must pass
- ✅ New use case (Use Case 3) - Must pass
- ✅ Mixed scenarios (old + new rules in same use case)

---

## 3. UI Changes - Tab 3 (Rule Editor)

### 3.1 Current Tab 3 State

**Current Features:**
- Rule creation with natural language (GenAI)
- SQL WHERE clause editing
- Rule preview
- Rule list/management

**Current Limitations:**
- Only supports Type 1/Type 2 rules (fact table filters)
- Single measure (daily_pnl)
- No rule type selection
- No node arithmetic support

### 3.2 Enhanced Tab 3 Design

#### 3.2.1 Rule Type Selection

**New UI Component:**
```
┌─────────────────────────────────────────┐
│ Rule Type:                              │
│ ○ Type 1: Simple Filter                │
│ ○ Type 2: Multi-Condition Filter        │
│ ○ Type 2B: Arithmetic of Queries       │
│ ○ Type 3: Node Arithmetic               │
└─────────────────────────────────────────┘
```

**Implementation:**
- Radio button group for rule type selection
- Dynamic form based on selected type
- Show/hide fields based on rule type

#### 3.2.2 Measure Selection (Type 1/2/2B)

**New UI Component:**
```
┌─────────────────────────────────────────┐
│ Measure:                                 │
│ [Dropdown: daily_pnl ▼]                 │
│   - daily_pnl                            │
│   - daily_commission                     │
│   - daily_trade                          │
└─────────────────────────────────────────┘
```

**Implementation:**
- Dropdown populated from use case input table schema
- Default: `daily_pnl` (backward compatible)

#### 3.2.3 Type 2B Rule Builder (New)

**New UI Component:**
```
┌─────────────────────────────────────────┐
│ Query 1:                                 │
│   Measure: [daily_commission ▼]         │
│   Filters:                               │
│     Strategy = [CORE]                    │
│   [+ Add Filter]                         │
│                                          │
│ Operator: [+]                            │
│                                          │
│ Query 2:                                 │
│   Measure: [daily_trade ▼]              │
│   Filters:                               │
│     Strategy = [CORE]                    │
│     Process_2 IN [SWAP COMMISSION, ...]  │
│   [+ Add Filter]                         │
│                                          │
│ [+ Add Query]                            │
└─────────────────────────────────────────┘
```

**Implementation:**
- Dynamic query builder
- Add/remove queries
- Operator selection (+, -, *, /)
- Visual query composition

#### 3.2.4 Type 3 Rule Builder (New)

**New UI Component:**
```
┌─────────────────────────────────────────┐
│ Node Arithmetic Expression:             │
│                                          │
│ [NODE_3] [-] [NODE_4]                   │
│                                          │
│ Available Nodes:                         │
│   [NODE_2] [NODE_3] [NODE_4] ...        │
│                                          │
│ Operators: [+][-][*][/]                  │
│                                          │
│ Expression: NODE_3 - NODE_4             │
│                                          │
│ Dependencies: NODE_3, NODE_4            │
│                                          │
│ [Validate] [Preview Impact]              │
└─────────────────────────────────────────┘
```

**Implementation:**
- Visual expression builder
- Node picker from hierarchy
- Operator buttons
- Dependency visualization
- Circular dependency detection (real-time)

#### 3.2.5 Enhanced Rule List

**New Columns:**
```
┌──────┬──────────────┬──────────┬─────────────┬──────────────┐
│ Node │ Rule Type    │ Measure  │ Expression  │ Status       │
├──────┼──────────────┼──────────┼─────────────┼──────────────┤
│  2   │ Type 1       │ daily_pnl│ -           │ ✅ Active    │
│  4   │ Type 2B      │ Multiple │ Query1+Query2│ ✅ Active   │
│  7   │ Type 3       │ -        │ NODE_3-NODE_4│ ✅ Active   │
└──────┴──────────────┴──────────┴─────────────┴──────────────┘
```

**Implementation:**
- Add rule type column
- Add measure column (or "Multiple" for Type 2B)
- Add expression column (for Type 3)
- Visual indicators for rule types

### 3.3 UI Refactoring Approach

**Principle:** Incremental enhancement, not complete rewrite

**Strategy:**
1. **Phase 5.7:** Add rule type selector (hidden by default, feature flag)
2. **Phase 5.8:** Add measure selector (for Type 1/2)
3. **Phase 5.9:** Add Type 2B builder (new component)
4. **Phase 5.10:** Add Type 3 builder (new component)
5. **Phase 5.11:** Enhance rule list (add columns)

**Backward Compatibility:**
- Default rule type: "Type 1" (existing behavior)
- Existing rules show as "Type 1" or "Type 2" (auto-detected)
- Old UI still works for existing rules

---

## 4. Risk Analysis & Mitigation

### Risk 1: Existing Use Cases Break

**Severity:** CRITICAL  
**Probability:** MEDIUM  
**Impact:** Production system failure

**Mitigation:**
- ✅ All schema changes are backward compatible (nullable columns, defaults)
- ✅ Code uses feature detection (rule_type or default)
- ✅ Comprehensive regression tests for existing use cases
- ✅ Staged rollout (test environment first)
- ✅ Rollback plan (database migration rollback scripts)

**Testing:**
- Run all existing use cases after each phase
- Verify calculations match previous results
- Performance benchmarks (no degradation)

### Risk 2: Type 3 Circular Dependencies

**Severity:** HIGH  
**Probability:** MEDIUM  
**Impact:** Infinite loops, incorrect calculations

**Mitigation:**
- ✅ Circular dependency detection (already implemented)
- ✅ Validation on rule creation (prevent invalid rules)
- ✅ Real-time validation in UI
- ✅ Clear error messages
- ✅ Unit tests for cycle detection

**Testing:**
- Test all cycle scenarios (2-node, 3-node, complex)
- Test valid dependencies
- Test edge cases (self-reference, etc.)

### Risk 3: Performance Degradation

**Severity:** MEDIUM  
**Probability:** MEDIUM  
**Impact:** Slow calculations, poor UX

**Mitigation:**
- ✅ Efficient algorithms (O(V+E) for topological sort)
- ✅ Caching of dependency graphs
- ✅ Performance benchmarks before/after
- ✅ Database indexes on new columns
- ✅ Query optimization

**Testing:**
- Performance tests with large hierarchies (1000+ nodes)
- Load testing (multiple concurrent calculations)
- Benchmark existing vs. new code paths

### Risk 4: Data Migration Issues

**Severity:** HIGH  
**Probability:** LOW  
**Impact:** Data loss, incorrect calculations

**Mitigation:**
- ✅ No data migration required (backward compatible)
- ✅ Database backups before each migration
- ✅ Migration scripts tested in test environment
- ✅ Rollback scripts prepared
- ✅ Data validation after migration

**Testing:**
- Test migrations on copy of production data
- Verify data integrity after migration
- Test rollback procedures

### Risk 5: UI Complexity

**Severity:** MEDIUM  
**Probability:** HIGH  
**Impact:** Poor UX, user confusion

**Mitigation:**
- ✅ Incremental UI changes (not big bang)
- ✅ User testing/feedback
- ✅ Clear labels and help text
- ✅ Progressive disclosure (show advanced features only when needed)
- ✅ Training materials/documentation

**Testing:**
- Usability testing with finance users
- A/B testing for UI changes
- User feedback collection

### Risk 6: Type 2B Rule Complexity

**Severity:** MEDIUM  
**Probability:** MEDIUM  
**Impact:** Incorrect calculations, user errors

**Mitigation:**
- ✅ Clear UI for query composition
- ✅ Validation of query syntax
- ✅ Preview of query results
- ✅ Comprehensive error messages
- ✅ Unit tests for all operators

**Testing:**
- Test all arithmetic operators (+, -, *, /)
- Test complex expressions
- Test edge cases (division by zero, etc.)

---

## 5. Structure Storage

### 5.1 New Structure: "America Cash Equity Trading Structure"

**Storage Location:**
- **Hierarchy Nodes:** `dim_hierarchy` table with `atlas_source = 'America Cash Equity Trading Structure'`
- **Structure Metadata:** `dim_atlas_structures` table (from Phase 5.1-5.5)

**Schema:**
```sql
-- Structure metadata (if Phase 5.1-5.5 implemented)
INSERT INTO dim_atlas_structures (
    structure_id,
    name,
    description,
    owner_id,
    status,
    source_system
) VALUES (
    'America Cash Equity Trading Structure',
    'America Cash Equity Trading Structure',
    'Hierarchy for America Cash Equity Trading use case',
    'system',
    'ACTIVE',
    'EXCEL_IMPORT'
);

-- Hierarchy nodes (12 nodes)
INSERT INTO dim_hierarchy (
    node_id,
    parent_node_id,
    node_name,
    depth,
    is_leaf,
    atlas_source
) VALUES
('NODE_2', 'ROOT', 'CORE Products', 1, FALSE, 'America Cash Equity Trading Structure'),
('NODE_3', 'NODE_2', 'Core Ex CRB', 2, FALSE, 'America Cash Equity Trading Structure'),
('NODE_4', 'NODE_3', 'Commissions', 3, FALSE, 'America Cash Equity Trading Structure'),
-- ... (all 12 nodes)
;
```

**Import Process:**
1. User uploads Excel file
2. System parses hierarchy structure
3. Creates structure in `dim_atlas_structures`
4. Creates nodes in `dim_hierarchy`
5. Validates hierarchy integrity
6. Creates use case with `atlas_structure_id`

---

## 6. Phased Implementation Plan

### Phase 5.0: Pre-Implementation (Before Week 1)

**Goal:** Address critical concerns before starting implementation

**Tasks:**
1. **Code Audit:** Find all float usage in financial calculations
2. **Fix Float Conversions:** Replace float with Decimal in calculation paths
3. **Decimal Policy:** Add to `.cursorrules` - "No float in financial calculations"
4. **Seed Script Template:** Create template for Use Case 3 structure/rules

**Deliverables:**
- Code audit report
- Fixed float conversions
- Updated `.cursorrules`
- Seed script template

**Gate:** All float conversions fixed, Decimal policy documented

---

### Phase 5.1: Database Schema Foundation (Week 1)

**Goal:** Add database columns without breaking existing functionality

**Tasks:**
1. Create Alembic migration for new columns
2. Add `rule_type`, `measure_name`, `rule_expression`, `rule_dependencies` to `metadata_rules`
3. Add `input_table_name` to `use_cases`
4. Set defaults for existing rows
5. Add database indexes

**Testing:**
- ✅ Unit tests: Verify schema changes
- ✅ Integration tests: Verify existing queries still work
- ✅ Regression tests: Run existing use cases
- ✅ Performance tests: No degradation

**Deliverables:**
- Migration script
- Test results
- Rollback script

**Gate:** All tests pass, existing use cases work

---

### Phase 5.2: Input Table Per Use Case (Week 2)

**Goal:** Support per-use-case input tables

**Tasks:**
1. Create `fact_pnl_use_case_3` table
2. Update waterfall engine to use `input_table_name` from use case
3. Add fallback to `fact_pnl_gold` if `input_table_name` is NULL
4. Add data import functionality
5. Update API to support input table selection

**Testing:**
- ✅ Unit tests: Input table loading
- ✅ Integration tests: Use Case 3 with new table
- ✅ Regression tests: Existing use cases still use `fact_pnl_gold`
- ✅ Data validation: Verify data integrity

**Deliverables:**
- Input table schema
- Waterfall engine updates
- Import functionality
- Test results

**Gate:** All tests pass, existing use cases work, Use Case 3 can use new table

---

### Phase 5.3: Rule Type System (Week 3)

**Goal:** Classify rules by type

**Tasks:**
1. Update rule creation API to accept `rule_type`
2. Auto-detect rule type from existing rules (migration)
3. Update rule validation
4. Add rule type to rule list API response
5. Update rule editor UI (add rule type selector - hidden by default)

**Testing:**
- ✅ Unit tests: Rule type detection
- ✅ Integration tests: Rule creation with types
- ✅ Regression tests: Existing rules work
- ✅ Migration tests: Existing rules auto-classified

**Deliverables:**
- Rule type detection logic
- API updates
- UI component (hidden)
- Test results

**Gate:** All tests pass, existing rules work, new rules can specify type

---

### Phase 5.4: Type 1/2 Enhancements (Week 4)

**Goal:** Support multiple measures for Type 1/2 rules

**Tasks:**
1. Update rule creation to accept `measure_name`
2. Update waterfall engine to use `measure_name` from rule
3. Add measure selector to UI (Type 1/2 rules)
4. Update rule preview to show measure
5. Update rule list to show measure

**Testing:**
- ✅ Unit tests: Measure selection
- ✅ Integration tests: Rules with different measures
- ✅ Regression tests: Existing rules (default to daily_pnl)
- ✅ E2E tests: Create rule with measure selection

**Deliverables:**
- Measure selection logic
- UI updates
- Test results

**Gate:** All tests pass, Type 1/2 rules support multiple measures

---

### Phase 5.5: Type 2B Rules (Week 5-6)

**Goal:** Support arithmetic of multiple queries

**Tasks:**
1. Implement Type 2B rule execution engine
2. Update rule creation API for Type 2B
3. Build Type 2B rule builder UI
4. Add query composition interface
5. Add operator selection
6. Update rule preview for Type 2B

**Testing:**
- ✅ Unit tests: Query execution, arithmetic operations
- ✅ Integration tests: Type 2B rule creation and execution
- ✅ Regression tests: Type 1/2 rules still work
- ✅ E2E tests: Create and execute Type 2B rule

**Deliverables:**
- Type 2B execution engine
- UI components
- Test results

**Gate:** All tests pass, Type 2B rules work, existing rules unaffected

---

### Phase 5.6: Type 3 Rules - Dependency Resolution (Week 7)

**Goal:** Implement dependency resolution for Type 3 rules

**Tasks:**
1. Integrate `resolve_execution_order()` into waterfall engine
2. Add Type 3 rule creation API
3. Add dependency parsing from `rule_expression`
4. Add circular dependency validation
5. Update rule validation

**Testing:**
- ✅ Unit tests: Dependency resolution (use existing test suite)
- ✅ Integration tests: Type 3 rule creation with dependencies
- ✅ Regression tests: Type 1/2/2B rules still work
- ✅ Edge cases: Complex dependencies, large graphs

**Deliverables:**
- Dependency resolution integration
- Validation logic
- Test results

**Gate:** All tests pass, Type 3 rules can be created with dependency validation

---

### Phase 5.7: Type 3 Rules - Execution Engine (Week 8-9)

**Goal:** Execute Type 3 rules in correct order

**Tasks:**
1. Implement Type 3 rule execution engine
2. Add arithmetic expression evaluator
3. Integrate with waterfall Phase 5
4. Add node value caching
5. Update reconciliation plug calculation for Type 3

**Testing:**
- ✅ Unit tests: Expression evaluation, execution order
- ✅ Integration tests: Type 3 rule execution
- ✅ Regression tests: All other rule types still work
- ✅ E2E tests: Complete Use Case 3 calculation

**Deliverables:**
- Type 3 execution engine
- Waterfall Phase 5
- Test results

**Gate:** All tests pass, Type 3 rules execute correctly, Use Case 3 works end-to-end

---

### Phase 5.8: Structure Import (Week 10)

**Goal:** Import structure from Excel

**Tasks:**
1. Create Excel import API endpoint
2. Parse Excel structure (hierarchy + rules)
3. Create structure in database
4. Create hierarchy nodes
5. Create rules from Excel
6. Validate imported structure

**Testing:**
- ✅ Unit tests: Excel parsing
- ✅ Integration tests: Structure import
- ✅ Data validation: Hierarchy integrity
- ✅ E2E tests: Import Use Case 3 structure

**Deliverables:**
- Excel import functionality
- Validation logic
- Test results

**Gate:** All tests pass, Use Case 3 structure can be imported from Excel

---

### Phase 5.9: UI Enhancements (Week 11-12)

**Goal:** Complete UI refactoring for all rule types

**Tasks:**
1. Enable rule type selector (make visible)
2. Complete Type 2B rule builder UI
3. Complete Type 3 rule builder UI
4. Enhance rule list with new columns
5. Add help text and tooltips
6. User testing and feedback

**Testing:**
- ✅ Unit tests: UI components
- ✅ Integration tests: UI + API integration
- ✅ Usability tests: User feedback
- ✅ E2E tests: Complete user workflows

**Deliverables:**
- Complete UI refactoring
- User documentation
- Test results

**Gate:** All tests pass, UI is user-friendly, users can create all rule types

---

### Phase 5.10: Testing & Validation (Week 13)

**Goal:** Comprehensive testing and validation

**Tasks:**
1. Run full regression test suite
2. Performance testing
3. Load testing
4. User acceptance testing
5. Documentation updates
6. Production readiness review

**Testing:**
- ✅ Full regression suite
- ✅ Performance benchmarks
- ✅ Load tests
- ✅ UAT with finance users

**Deliverables:**
- Test reports
- Performance reports
- UAT results
- Production readiness checklist

**Gate:** All tests pass, performance acceptable, UAT approved

---

### Phase 5.11: Production Deployment (Week 14)

**Goal:** Deploy to production

**Tasks:**
1. Production database migration
2. Deploy backend changes
3. Deploy frontend changes
4. Monitor for issues
5. Rollback plan ready

**Testing:**
- ✅ Smoke tests in production
- ✅ Monitor error rates
- ✅ Monitor performance

**Deliverables:**
- Production deployment
- Monitoring dashboard
- Rollback procedures

**Gate:** Production stable, no critical issues

---

## 7. Testing Checklist (Per Phase)

### Pre-Phase Checklist
- [ ] Database backup created
- [ ] Test environment updated
- [ ] Test data prepared
- [ ] Rollback plan ready

### During Phase Checklist
- [ ] Unit tests written and passing
- [ ] Integration tests written and passing
- [ ] Regression tests passing (existing use cases)
- [ ] Code review completed
- [ ] Documentation updated

### Post-Phase Checklist
- [ ] All tests passing
- [ ] Performance acceptable
- [ ] No breaking changes
- [ ] Migration tested
- [ ] Rollback tested
- [ ] Gate criteria met

---

## 8. Rollback Plan

### Database Rollback
```sql
-- Rollback script for each migration
-- Example: Phase 5.1 rollback
ALTER TABLE metadata_rules DROP COLUMN IF EXISTS rule_type;
ALTER TABLE metadata_rules DROP COLUMN IF EXISTS measure_name;
ALTER TABLE metadata_rules DROP COLUMN IF EXISTS rule_expression;
ALTER TABLE metadata_rules DROP COLUMN IF EXISTS rule_dependencies;
ALTER TABLE use_cases DROP COLUMN IF EXISTS input_table_name;
```

### Code Rollback
- Git tags for each phase
- Feature flags to disable new features
- Database version check to enable/disable features

### Data Rollback
- Database backups before each migration
- Point-in-time recovery if needed

---

## 9. Success Criteria

### Phase 5 Complete When:
1. ✅ All existing use cases work unchanged
2. ✅ Use Case 3 can be created and executed
3. ✅ All four rule types (1, 2, 2B, 3) work
4. ✅ UI supports all rule types
5. ✅ Performance is acceptable
6. ✅ All tests pass
7. ✅ Documentation complete
8. ✅ User training complete

---

## 10. Timeline Summary

| Phase | Duration | Key Deliverable | Testing Gate |
|-------|----------|----------------|--------------|
| 5.1 | Week 1 | Database schema | ✅ Regression tests |
| 5.2 | Week 2 | Input tables | ✅ Regression tests |
| 5.3 | Week 3 | Rule types | ✅ Regression tests |
| 5.4 | Week 4 | Multiple measures | ✅ Regression tests |
| 5.5 | Week 5-6 | Type 2B rules | ✅ Regression tests |
| 5.6 | Week 7 | Dependency resolution | ✅ Regression tests |
| 5.7 | Week 8-9 | Type 3 execution | ✅ Regression tests |
| 5.8 | Week 10 | Structure import | ✅ Regression tests |
| 5.9 | Week 11-12 | UI enhancements | ✅ UAT |
| 5.10 | Week 13 | Testing & validation | ✅ Full test suite |
| 5.11 | Week 14 | Production deployment | ✅ Production stable |

**Total Duration:** 14 weeks (3.5 months)

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-01  
**Status:** Ready for Review and Approval

