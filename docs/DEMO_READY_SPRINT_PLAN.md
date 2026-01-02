# Demo Ready Sprint Plan (Weeks 1-4)

**Document Purpose:** Detailed plan for "Demo Ready" release showing Use Case 3 results in 4 weeks

**Status:** Implementation Plan  
**Date:** 2026-01-01  
**Goal:** Show working Use Case 3 calculation to stakeholders

---

## Sprint Goal

**Deliverable:** Working Use Case 3 ("America Cash Equity Trading Structure") with:
- ✅ Structure created (hard-coded via seed script)
- ✅ Rules created (hard-coded via seed script)
- ✅ Calculation executed
- ✅ Results visible in Tab 3

**What We Skip (for now):**
- ❌ Excel import (use seed script instead)
- ❌ Fancy UI (use simple text areas)
- ❌ Full UI enhancements (basic functionality only)

---

## Week 1: Database Schema + Code Audit

### Day 1-2: Code Audit & Fixes

**Tasks:**
1. Audit all float usage in financial calculations
2. Fix float conversions in `app/services/orchestrator.py`
3. Verify Decimal usage in existing code
4. Add Decimal policy to `.cursorrules`

**Deliverables:**
- Code audit report
- Fixed float conversions
- Updated `.cursorrules`

**Testing:**
- ✅ Run existing use cases (verify no regressions)
- ✅ Verify all calculations use Decimal

### Day 3-5: Database Schema

**Tasks:**
1. Create Alembic migration for new columns
2. Add `rule_type`, `measure_name`, `rule_expression`, `rule_dependencies` to `metadata_rules`
3. Add `input_table_name` to `use_cases`
4. Set defaults for existing rows
5. Add database indexes

**Deliverables:**
- Migration script
- Test results
- Rollback script

**Testing:**
- ✅ Migration runs successfully
- ✅ Existing rules work (default to 'FILTER')
- ✅ Rollback works

**Gate:** All tests pass, existing use cases work

---

## Week 2: Input Table + Seed Script

### Day 1-2: Input Table Creation

**Tasks:**
1. Create `fact_pnl_use_case_3` table
2. Add `input_table_name` support to waterfall
3. Update waterfall to use input table if specified
4. Fallback to `fact_pnl_gold` if `input_table_name` is NULL

**Deliverables:**
- Input table schema
- Waterfall engine updates
- Test results

**Testing:**
- ✅ Existing use cases still use `fact_pnl_gold`
- ✅ Use Case 3 can use new table

### Day 3-5: Seed Script for Use Case 3

**Tasks:**
1. Create `scripts/seed_use_case_3_structure.py`
   - Create structure "America Cash Equity Trading Structure"
   - Create 12 hierarchy nodes (NODE_2 through NODE_12)
   - Create ROOT node
2. Create `scripts/seed_use_case_3_rules.py`
   - Create Type 1 rules (NODE_2, NODE_11, NODE_12)
   - Create Type 2 rules (NODE_5, NODE_6, NODE_9, NODE_10)
   - Create Type 2B rule (NODE_4)
   - Create Type 3 rules (NODE_3, NODE_7, NODE_8)
3. Create `scripts/seed_use_case_3_data.py`
   - Load sample data into `fact_pnl_use_case_3`
   - Match data to hierarchy leaf nodes

**Deliverables:**
- Seed scripts
- Test data
- Documentation

**Testing:**
- ✅ Seed script runs successfully
- ✅ Structure created correctly
- ✅ Rules created correctly
- ✅ Data loaded correctly

**Gate:** Seed script creates complete Use Case 3 setup

---

## Week 3: Rule Types + Measures

### Day 1-2: Rule Type System

**Tasks:**
1. Update rule creation API to accept `rule_type`
2. Auto-detect rule type from existing rules (migration)
3. Update rule validation
4. Add rule type to rule list API response

**Deliverables:**
- Rule type detection logic
- API updates
- Test results

**Testing:**
- ✅ Existing rules work (auto-classified)
- ✅ New rules can specify type

### Day 3-5: Multiple Measures Support

**Tasks:**
1. Update rule creation to accept `measure_name`
2. Update waterfall engine to use `measure_name` from rule
3. Add measure selector to UI (hidden by default, feature flag)
4. Update rule preview to show measure

**Deliverables:**
- Measure selection logic
- UI component (hidden)
- Test results

**Testing:**
- ✅ Rules with different measures work
- ✅ Existing rules (default to daily_pnl) work

**Gate:** All tests pass, Type 1/2 rules support multiple measures

---

## Week 4: Type 2B + Type 3 (Basic)

### Day 1-2: Type 2B Engine

**Tasks:**
1. Implement Type 2B rule execution engine
2. Parse `predicate_json` (Version 2.0 format)
3. Execute multiple queries
4. Combine results with arithmetic operations
5. **CRITICAL:** Use Decimal throughout

**Deliverables:**
- Type 2B execution engine
- Test results

**Testing:**
- ✅ Type 2B rules execute correctly
- ✅ Decimal precision maintained
- ✅ All operators work (+, -, *, /)

### Day 3-4: Type 3 Engine

**Tasks:**
1. Integrate `resolve_execution_order()` into waterfall
2. Implement Type 3 rule execution engine
3. Parse `rule_expression` (e.g., "NODE_3 - NODE_4")
4. Evaluate arithmetic expressions
5. **CRITICAL:** Use Decimal throughout
6. Add Phase 5 to waterfall

**Deliverables:**
- Type 3 execution engine
- Waterfall Phase 5
- Test results

**Testing:**
- ✅ Type 3 rules execute in correct order
- ✅ Circular dependencies detected
- ✅ Decimal precision maintained

### Day 5: Simple UI + Demo

**Tasks:**
1. **Simple UI for Type 3:** Text area for rule expression
   - User types: "NODE_3 - NODE_4"
   - System validates and saves
2. **Simple UI for Type 2B:** Basic query builder
   - Two query inputs
   - Operator selection
3. **Demo Preparation:**
   - Run seed scripts
   - Execute calculation
   - Verify results in Tab 3

**Deliverables:**
- Simple UI components
- Working demo
- Demo script

**Testing:**
- ✅ Use Case 3 calculation works end-to-end
- ✅ Results visible in Tab 3
- ✅ All rule types work

**Gate:** Demo ready - Use Case 3 shows results

---

## Demo Script

```bash
# Step 1: Run seed scripts
python scripts/seed_use_case_3_structure.py
python scripts/seed_use_case_3_rules.py
python scripts/seed_use_case_3_data.py

# Step 2: Create use case
# (Via UI or API)

# Step 3: Execute calculation
# (Via UI or API)

# Step 4: View results in Tab 3
# (Results should show all 12 nodes with calculated values)
```

---

## Success Criteria

**Demo Ready When:**
1. ✅ Use Case 3 structure created (12 nodes)
2. ✅ Use Case 3 rules created (all 4 rule types)
3. ✅ Use Case 3 data loaded
4. ✅ Calculation executes successfully
5. ✅ Results visible in Tab 3
6. ✅ All rule types work (Type 1, 2, 2B, 3)
7. ✅ Decimal precision maintained
8. ✅ Existing use cases still work

---

## Risk Mitigation

### Risk: Seed Script Errors
**Mitigation:** Test seed scripts thoroughly, have rollback script ready

### Risk: Type 3 Engine Bugs
**Mitigation:** Comprehensive unit tests, test with Use Case 3 data

### Risk: Decimal Precision Issues
**Mitigation:** Code audit before Week 4, test with penny values

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-01  
**Status:** Ready for Implementation

