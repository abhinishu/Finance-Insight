# Phase 5.1: Unified Hybrid Engine Architecture Analysis

## Architecture Acknowledgment

I understand the transition from **Hardcoded Legacy Logic** to **Metadata-Driven Auto-Rules**. This is a significant architectural improvement that will:

1. **Eliminate Hardcoding**: Remove `_calculate_legacy_rollup` and `_calculate_strategy_rollup` in favor of a unified resolver
2. **Support 4 Rule Flavors**: Auto-Rollup, Custom SQL, Measure Switch, Node Math
3. **Maintain Backward Compatibility**: Ensure Use Cases 1 & 2 produce identical results

## Current State Analysis

### Legacy Rollup Logic (To Be Replaced)

**Use Case 1 (America Trading P&L):**
- Data Source: `fact_pnl_gold`
- Matching: `cc_id` (fact) = `node_id` (hierarchy)
- Matching Strategies: 
  1. Direct `node_id` match (primary)
  2. `node_name` match (secondary)
  3. `node.cc_id` attribute match (tertiary)
  4. Fuzzy match (normalized, fallback)
- Aggregation: Bottom-up from leaf nodes

**Use Case 2 (Project Sterling):**
- Data Source: `fact_pnl_entries`
- Matching: `category_code` (fact) = `node_id` (hierarchy)
- Filtering: Already filtered by `use_case_id`
- Aggregation: Bottom-up from leaf nodes

**Use Case 3 (Cash Equity Trading):**
- Data Source: `fact_pnl_use_case_3`
- Matching: `strategy` or `product_line` (fact) = `node_name` (hierarchy)
- Matching: Case-insensitive string comparison
- Aggregation: Bottom-up from leaf nodes

## Identified Risks & Mitigation Strategies

### 🔴 **CRITICAL RISK 1: Matching Value Source Ambiguity**

**Issue:**
- UC 1 matches: `cc_id = node_id` (uses `node_id` from hierarchy)
- UC 3 matches: `strategy = node_name` (uses `node_name` from hierarchy)
- The resolver needs to know: **Which value to use for matching?**

**Current Behavior:**
- UC 1: `fact_pnl_gold.cc_id = 'CC_AMER_CASH_NY_001'` matches `hierarchy.node_id = 'CC_AMER_CASH_NY_001'`
- UC 3: `fact_pnl_use_case_3.strategy = 'Commissions (Non Swap)'` matches `hierarchy.node_name = 'Commissions (Non Swap)'`

**Mitigation:**
- Add `rollup_value_source` column to `dim_hierarchy` (enum: 'node_id', 'node_name')
- OR: Make `rollup_driver` logic smarter:
  - If `rollup_driver = 'cc_id'` → use `node_id`
  - If `rollup_driver = 'strategy'` → use `node_name`
  - If `rollup_driver = 'category_code'` → use `node_id`

**Recommendation:** Add `rollup_value_source` column for explicit control.

---

### 🟡 **RISK 2: Multiple Matching Strategies**

**Issue:**
- Current `_calculate_legacy_rollup` uses 4 matching strategies (node_id, node_name, cc_id attribute, fuzzy)
- Virtual rules will only use ONE strategy (the primary one)
- May break edge cases where fuzzy matching was needed

**Mitigation:**
- Document that auto-rollup uses primary strategy only
- Custom rules can still use complex SQL for edge cases
- Add validation script to compare old vs new results

---

### 🟡 **RISK 3: Performance Impact**

**Issue:**
- Current rollup: Single optimized query with GROUP BY
- New approach: One virtual rule per node = N queries (where N = number of nodes)
- Could be significantly slower for large hierarchies

**Mitigation:**
- Batch virtual rules into single query where possible
- Use `IN` clause: `WHERE cc_id IN ('CC_001', 'CC_002', ...)`
- Cache virtual rule generation
- Benchmark before/after performance

---

### 🟡 **RISK 4: Data Migration Complexity**

**Issue:**
- Need to populate `rollup_driver` for all existing hierarchies
- UC 1: Set `rollup_driver = 'cc_id'` for all nodes
- UC 2: Set `rollup_driver = 'category_code'` for all nodes
- UC 3: Set `rollup_driver = 'strategy'` for leaf nodes, `'product_line'` for parents?

**Mitigation:**
- Create migration script that:
  1. Identifies use case by `atlas_structure_id` or `use_case.name`
  2. Sets `rollup_driver` based on use case type
  3. Validates migration (counts, sample checks)

---

### 🟡 **RISK 5: Measure Column Mapping**

**Issue:**
- UC 1 & 2: Use `daily_pnl`, `mtd_pnl`, `ytd_pnl` (standard names)
- UC 3: Use `pnl_daily`, `pnl_commission`, `pnl_trade` (different names)
- Virtual rules need to know which measure columns exist in which table

**Mitigation:**
- Add `measure_mapping` JSONB column to `use_cases` table
- OR: Infer from `input_table_name`:
  - `fact_pnl_gold` → `daily_pnl`, `mtd_pnl`, `ytd_pnl`
  - `fact_pnl_entries` → `daily_amount`, `wtd_amount`, `ytd_amount`
  - `fact_pnl_use_case_3` → `pnl_daily`, `pnl_commission`, `pnl_trade`

**Recommendation:** Add `measure_mapping` for explicit control.

---

### 🟢 **LOW RISK 6: Rule Priority Conflicts**

**Issue:**
- What if a node has BOTH `rollup_driver` AND an explicit custom rule?
- Current design says: "Explicit rule wins" (correct)

**Mitigation:**
- Document priority clearly
- Add validation: Warn if both exist (shouldn't happen in practice)

---

## Proposed Schema Changes

### 1. `dim_hierarchy` Table

```sql
ALTER TABLE dim_hierarchy 
ADD COLUMN rollup_driver VARCHAR(50) NULL,
ADD COLUMN rollup_value_source VARCHAR(20) NULL DEFAULT 'node_id';

COMMENT ON COLUMN dim_hierarchy.rollup_driver IS 
  'Column name in fact table to filter on (e.g., cc_id, category_code, strategy)';

COMMENT ON COLUMN dim_hierarchy.rollup_value_source IS 
  'Which hierarchy value to use for matching: node_id or node_name';
```

### 2. `metadata_rules` Table

```sql
-- Already exists: measure_name (VARCHAR(50), default 'daily_pnl')
-- No changes needed, but ensure it's used correctly
```

### 3. `use_cases` Table (Optional Enhancement)

```sql
ALTER TABLE use_cases
ADD COLUMN measure_mapping JSONB NULL;

COMMENT ON COLUMN use_cases.measure_mapping IS 
  'JSON mapping: {"daily": "daily_pnl", "mtd": "mtd_pnl", "ytd": "ytd_pnl"}';
```

---

## Implementation Plan

### Step 1: Database Migration ✅
- Add `rollup_driver` and `rollup_value_source` to `dim_hierarchy`
- Create migration script to populate existing data
- Validate migration

### Step 2: Rule Resolver Service ✅
- Create `app/services/rule_resolver.py`
- Implement resolution priority logic
- Generate virtual rules for nodes with `rollup_driver`

### Step 3: Refactor Calculation Engine ✅
- Update `app/services/calculator.py` to use RuleResolver
- Remove `_calculate_legacy_rollup` (after validation)
- Support `target_measure` in SQL execution

### Step 4: Verification ✅
- Create `scripts/verify_hybrid_engine.py`
- Compare old vs new results for UC 1 & 2
- Ensure 100% match before removing legacy code

---

## Questions for Clarification

1. **Rollup Value Source**: Should we add `rollup_value_source` column, or infer from `rollup_driver`?
2. **Measure Mapping**: Should we add `measure_mapping` to `use_cases`, or hardcode in resolver?
3. **Performance**: Should we batch virtual rules into single queries, or execute individually?
4. **Migration Strategy**: Should we migrate all use cases at once, or one at a time?

---

## Approval Status

✅ **Architecture Understood**
✅ **Risks Identified**
✅ **Mitigation Strategies Proposed**
⏳ **Awaiting User Confirmation on Questions Above**

Ready to proceed with implementation once clarifications are provided.

