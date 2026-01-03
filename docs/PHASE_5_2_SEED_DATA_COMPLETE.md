# Phase 5.2: Seed Data & Structure - Complete

**Date:** 2026-01-01  
**Status:** ✅ Complete - Ready for Execution

---

## Overview

Phase 5.2 creates a fully functional "America Cash Equity Trading" demo use case with:
- Complete hierarchy structure (12 nodes)
- Business rules (Type 1, 2, 2B, 3)
- Mock fact data (500 rows)
- NLP training queries

---

## Files Created

### 1. Structure Seeder
**File:** `scripts/seed_use_case_3_structure.py`

**Creates:**
- Use Case: "America Cash Equity Trading"
- Structure: "America Cash Equity Trading Structure"
- 12 Hierarchy Nodes:
  - NODE_2: CORE Products (Level 1)
  - NODE_3: Core Ex CRB (Level 2)
  - NODE_4: Commissions (Level 3)
  - NODE_5: Commissions (Non Swap) (Level 4, Leaf)
  - NODE_6: Swap Commission (Level 4, Leaf)
  - NODE_7: Trading (Level 3)
  - NODE_8: Facilitations (Level 4, Leaf)
  - NODE_9: Inventory Management (Level 4, Leaf)
  - NODE_10: CRB (Level 2)
  - NODE_11: ETF Amber (Level 2)
  - NODE_12: MSET (Level 2)

**Features:**
- ✅ Creates use case with `input_table_name='fact_pnl_use_case_3'`
- ✅ Creates all hierarchy nodes with correct parent-child relationships
- ✅ Sets correct depth and is_leaf flags
- ✅ Verifies hierarchy structure after creation

---

### 2. Rules Seeder
**File:** `scripts/seed_use_case_3_rules.py`

**Creates Business Rules:**

#### Type 1 Rules (Simple Filter):
- **NODE_2:** `SUM(daily_pnl) WHERE product_line='CORE Products'`
- **NODE_11:** `SUM(daily_pnl) WHERE strategy='ETF Amer'`
- **NODE_12:** `SUM(daily_pnl) WHERE process_1='MSET'`

#### Type 2 Rules (Multi-Condition):
- **NODE_10:** `SUM(daily_pnl) WHERE strategy='CORE' AND book IN ('MSAL', 'ETFUS', 'Central Risk Book', 'CRB Risk')`
- **NODE_5:** `SUM(daily_commission) WHERE strategy='CORE'`
- **NODE_6:** `SUM(daily_trade) WHERE strategy='CORE' AND process_2 IN ('SWAP COMMISSION', 'SD COMMISSION')`
- **NODE_9:** `SUM(daily_pnl) WHERE strategy='CORE' AND process_2='Inventory Management'`

#### Type 2B Rule (FILTER_ARITHMETIC):
- **NODE_4:** `SUM(daily_commission) WHERE strategy='CORE' + SUM(daily_trade) WHERE strategy='CORE' AND process_2 IN ('SWAP COMMISSION', 'SD COMMISSION')`
  - Uses JSON Version 2.0 schema
  - Two independent queries with addition operator

#### Type 3 Rules (NODE_ARITHMETIC):
- **NODE_7:** `NODE_3 - NODE_4` (Trading = Core Ex CRB - Commissions)
- **NODE_8:** `NODE_7 - NODE_9` (Facilitations = Trading - Inventory Management)

**Features:**
- ✅ All rule types supported
- ✅ Proper JSON schema for Type 2B
- ✅ Text format for Type 3 expressions
- ✅ Dependencies stored in `rule_dependencies` (JSONB)

---

### 3. Data Seeder
**File:** `scripts/seed_use_case_3_data.py`

**Generates:**
- 500 rows of mock data
- All amounts use `Decimal` type (not float)
- Data designed to "hit" business rules:
  - 40% rows: `product_line='CORE Products'` (hits NODE_2)
  - 50% rows: `strategy='CORE'` (hits multiple nodes)
  - 20% rows: `process_2='SWAP COMMISSION'` (hits NODE_6)
  - 15% rows: `process_2='SD COMMISSION'` (hits NODE_6)
  - 10% rows: `process_2='Inventory Management'` (hits NODE_9)
  - 20% rows: `book IN ('MSAL', 'ETFUS', ...)` (hits NODE_10)
  - 10% rows: `process_1='MSET'` (hits NODE_12)
  - 10% rows: `strategy='ETF Amer'` (hits NODE_11)

**Features:**
- ✅ All PnL amounts use `Decimal` type
- ✅ Bulk insert for performance
- ✅ Data verification and coverage reporting
- ✅ Handles existing data (prompts for deletion)

---

### 4. NLP Training Data
**File:** `docs/nlp_sample_queries.md`

**Contains:**
- 10 natural language query examples
- Query patterns and mappings
- Expected GenAI behavior
- Testing checklist

**Sample Queries:**
1. "Show me the breakdown of Core Ex CRB."
2. "How is Commissions calculated?"
3. "Calculate Net Trading excluding Inventory."
4. "What is the total P&L for CORE Products?"
5. "Show me all Swap Commission transactions."
6. "What is the P&L for CRB books?"
7. "Break down Commissions into Non-Swap and Swap components."
8. "Compare Trading and Commissions for Core Ex CRB."
9. "What is the P&L for ETF Amber strategy?"
10. "Show me the P&L breakdown for MSET process."

---

## Execution Order

### Step 1: Create Structure
```bash
python scripts/seed_use_case_3_structure.py
```

**Expected Output:**
```
[OK] Created use case: America Cash Equity Trading
[OK] Created node 'NODE_2': CORE Products
...
[OK] Hierarchy structure verified successfully
```

### Step 2: Create Rules
```bash
python scripts/seed_use_case_3_rules.py
```

**Expected Output:**
```
[OK] Created Type 1 rule for NODE_2 (CORE Products)
[OK] Created Type 2 rule for NODE_10 (CRB)
[OK] Created Type 2B rule for NODE_4 (Commissions)
[OK] Created Type 3 rule for NODE_7 (Trading)
...
[OK] All rules created successfully
```

### Step 3: Create Data
```bash
python scripts/seed_use_case_3_data.py
```

**Expected Output:**
```
Generating rows...
  Generated 100/500 rows...
  ...
Inserting data into database...
  Inserted batch 1: 100 rows
  ...
[SUCCESS] Use Case 3 fact data created successfully!
Total rows: 500
Rule coverage:
  Node 2 (CORE Products): 200 rows
  Node 10 (CRB): 100 rows
  ...
```

---

## Verification

### Verify Structure
```sql
-- Check use case
SELECT * FROM use_cases WHERE name = 'America Cash Equity Trading';

-- Check hierarchy nodes
SELECT node_id, node_name, parent_node_id, depth, is_leaf
FROM dim_hierarchy
WHERE atlas_source = 'America Cash Equity Trading Structure'
ORDER BY depth, node_id;
```

### Verify Rules
```sql
-- Check rules
SELECT node_id, rule_type, measure_name, logic_en
FROM metadata_rules
WHERE use_case_id = (SELECT use_case_id FROM use_cases WHERE name = 'America Cash Equity Trading')
ORDER BY node_id;
```

### Verify Data
```sql
-- Check data count
SELECT COUNT(*) FROM fact_pnl_use_case_3;

-- Check rule coverage
SELECT 
    product_line,
    COUNT(*) as count
FROM fact_pnl_use_case_3
WHERE product_line = 'CORE Products'
GROUP BY product_line;

SELECT 
    strategy,
    process_2,
    COUNT(*) as count
FROM fact_pnl_use_case_3
WHERE strategy = 'CORE' 
AND process_2 IN ('SWAP COMMISSION', 'SD COMMISSION')
GROUP BY strategy, process_2;
```

---

## Compliance Status

✅ **Decimal Precision:** All amounts use `Decimal` type  
✅ **Rule Types:** Type 1, 2, 2B, 3 all supported  
✅ **Data Coverage:** Data hits all business rules  
✅ **Structure:** Complete hierarchy with correct relationships  
✅ **NLP Ready:** Training queries documented

---

## Next Steps

After running all seed scripts:

1. **Test Calculation:** Run waterfall engine on Use Case 3
2. **Verify Results:** Check that all nodes have calculated values
3. **Test Type 3:** Verify dependency resolution works
4. **Test Type 2B:** Verify arithmetic of queries works
5. **UI Testing:** Verify results display in Tab 3

---

**Phase 5.2 Status:** ✅ Complete  
**Ready for:** Phase 5.3 (Rule Types + Measures)


