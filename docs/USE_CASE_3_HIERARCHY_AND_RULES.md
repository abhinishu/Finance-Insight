# Use Case 3: Hierarchy Structure and Business Rules

**Document Purpose:** Complete hierarchy structure and business rule definitions for "America Cash Equity Trading Structure"

**Status:** Confirmed  
**Date:** 2026-01-01  
**Source:** Excel tab "Business rule for use case 3"

---

## Hierarchy Structure

### Level 1 (Root Children)

| NODE_ID | Node Name | Parent | Level |
|---------|-----------|--------|-------|
| 2 | CORE Products | ROOT | 1 |

### Level 2

| NODE_ID | Node Name | Parent | Level |
|---------|-----------|--------|-------|
| 3 | Core Ex CRB | 2 (CORE Products) | 2 |
| 10 | CRB | 2 (CORE Products) | 2 |
| 11 | ETF Amber | 2 (CORE Products) | 2 |
| 12 | MSET | 2 (CORE Products) | 2 |

### Level 3

| NODE_ID | Node Name | Parent | Level |
|---------|-----------|--------|-------|
| 4 | Commissions | 3 (Core Ex CRB) | 3 |
| 7 | Trading | 3 (Core Ex CRB) | 3 |

### Level 4 (Leaf Nodes)

| NODE_ID | Node Name | Parent | Level |
|---------|-----------|--------|-------|
| 5 | Commissions (Non Swap) | 4 (Commissions) | 4 |
| 6 | Swap Commission | 4 (Commissions) | 4 |
| 8 | Facilitations | 7 (Trading) | 4 |
| 9 | Inventory Management | 7 (Trading) | 4 |

### Hierarchy Tree Visualization

```
ROOT
└── CORE Products (NODE_ID: 2)
    ├── Core Ex CRB (NODE_ID: 3)
    │   ├── Commissions (NODE_ID: 4)
    │   │   ├── Commissions (Non Swap) (NODE_ID: 5)
    │   │   └── Swap Commission (NODE_ID: 6)
    │   └── Trading (NODE_ID: 7)
    │       ├── Facilitations (NODE_ID: 8)
    │       └── Inventory Management (NODE_ID: 9)
    ├── CRB (NODE_ID: 10)
    ├── ETF Amber (NODE_ID: 11)
    └── MSET (NODE_ID: 12)
```

---

## Business Rules by Type

### Type 1: Simple Dimension Filtering (Highlight/Standard Logic)

**Pattern:** `SUM(MEASURE) WHERE Dimension = 'Node_Name'`

**Purpose:** Map node name directly to a dimension value. "Highlight" means this is standard logic - just filter by dimension.

#### Rule 1.1: NODE_ID 2 - "CORE Products"
- **Derivation Logic:** "Looks Standard logic- We need to just highlight this as Standard Product line from off SUM (Daily_PNL) where Product line = CORE Products"
- **Business Rule:** `SUM(Daily_PNL) WHERE Product_line = 'CORE Products'`
- **Type:** Type 1 (Simple Filter)
- **Dimension:** `product_line`
- **Measure:** `daily_pnl`

#### Rule 1.2: NODE_ID 11 - "ETF Amber"
- **Derivation Logic:** "Looks Standard logic- We need to just highlight is as Strategy from official CC structure SUM(DAILY_PNL) where Strategy = 'ETF Amer'"
- **Business Rule:** `SUM(DAILY_PNL) WHERE Strategy = 'ETF Amer'`
- **Type:** Type 1 (Simple Filter)
- **Dimension:** `strategy`
- **Measure:** `daily_pnl`
- **Note:** Node name "ETF Amber" maps to Strategy value "ETF Amer" (slight name difference)

#### Rule 1.3: NODE_ID 12 - "MSET"
- **Derivation Logic:** "Looks Standard logic- We need to just highlight is as Process 1 from official CC structure SUM(DAILY_PNL) where Process_1 = 'MSET'"
- **Business Rule:** `SUM(DAILY_PNL) WHERE Process_1 = 'MSET'`
- **Type:** Type 1 (Simple Filter)
- **Dimension:** `process_1`
- **Measure:** `daily_pnl`

---

### Type 2: Multi-Condition Filtering

**Pattern:** `SUM(MEASURE) WHERE Condition1 AND Condition2 [AND Condition3...]`

**Purpose:** Filter by multiple dimensions or use IN clauses for multiple values.

#### Rule 2.1: NODE_ID 4 - "Commissions"
- **Derivation Logic:** "Business RULE 1"
- **Business Rule:** `SUM(DAILY_COMMISION) WHERE Strategy='CORE' + SUM(DAILY_TRADING) WHERE Strategy='CORE' AND Process_2 IN ('SWAP COMMISSION', 'SD COMMISSION')`
- **Type:** Type 2 (Multi-Condition + Arithmetic of Two Queries)
- **Complexity:** This is actually **Type 2 + Arithmetic** - two separate queries added together
- **Query 1:** `SUM(DAILY_COMMISION) WHERE Strategy='CORE'`
- **Query 2:** `SUM(DAILY_TRADING) WHERE Strategy='CORE' AND Process_2 IN ('SWAP COMMISSION', 'SD COMMISSION')`
- **Result:** Query 1 + Query 2
- **Measures Used:** `daily_commission`, `daily_trade`

#### Rule 2.2: NODE_ID 5 - "Commissions (Non Swap)"
- **Derivation Logic:** "Business RULE 2"
- **Business Rule:** `SUM(DAILY_COMMISION) WHERE Strategy='CORE'`
- **Type:** Type 2 (Single Condition, but uses different measure)
- **Dimension:** `strategy`
- **Measure:** `daily_commission` (not `daily_pnl`)

#### Rule 2.3: NODE_ID 6 - "Swap Commission"
- **Derivation Logic:** "Business RULE 3"
- **Business Rule:** `SUM(DAILY_TRADING) WHERE Strategy='CORE' AND Process_2 IN ('SWAP COMMISSION', 'SD COMMISSION')`
- **Type:** Type 2 (Multi-Condition with IN clause)
- **Dimensions:** `strategy`, `process_2`
- **Measure:** `daily_trade` (not `daily_pnl`)

#### Rule 2.4: NODE_ID 9 - "Inventory Management"
- **Derivation Logic:** "BUSINESS RULE 4"
- **Business Rule:** `SUM(DAILY_PNL) WHERE Strategy = 'CORE' AND PROCESS_2 = 'Inventory Management'`
- **Type:** Type 2 (Multi-Condition)
- **Dimensions:** `strategy`, `process_2`
- **Measure:** `daily_pnl`

#### Rule 2.5: NODE_ID 10 - "CRB"
- **Derivation Logic:** "BUSINESS RULE 5"
- **Business Rule:** `SUM(DAILY_PNL) WHERE Strategy='CORE' AND Books IN ('MSAL', 'ETFUS', 'Central Risk Book', 'CRB Risk')`
- **Type:** Type 2 (Multi-Condition with IN clause)
- **Dimensions:** `strategy`, `book`
- **Measure:** `daily_pnl`

---

### Type 3: Node Arithmetic Operations

**Pattern:** `NODE_X = NODE_Y [operator] NODE_Z`

**Purpose:** Calculate node value from other nodes (not from fact table).

#### Rule 3.1: NODE_ID 7 - "Trading"
- **Derivation Logic:** "Core Ex CRB - Commissions (Node 3 - Node 4)"
- **Business Rule:** `NODE_7 = NODE_3 - NODE_4`
- **Type:** Type 3 (Node Arithmetic)
- **Operation:** Subtraction
- **Dependencies:** NODE_3 (Core Ex CRB), NODE_4 (Commissions)
- **Note:** NODE_3 and NODE_4 must be calculated first (they have Type 2 rules)

#### Rule 3.2: NODE_ID 8 - "Facilitations"
- **Derivation Logic:** "Node 7 - Node 9"
- **Business Rule:** `NODE_8 = NODE_7 - NODE_9`
- **Type:** Type 3 (Node Arithmetic)
- **Operation:** Subtraction
- **Dependencies:** NODE_7 (Trading), NODE_9 (Inventory Management)
- **Note:** NODE_7 has Type 3 rule, NODE_9 has Type 2 rule

#### Rule 3.3: NODE_ID 3 - "Core Ex CRB" (Implicit)
- **Derivation Logic:** Not explicitly stated, but can be inferred
- **Business Rule:** `NODE_3 = NODE_2 - NODE_10` (CORE Products - CRB)
- **Type:** Type 3 (Node Arithmetic) - **INFERRED**
- **Operation:** Subtraction
- **Dependencies:** NODE_2 (CORE Products), NODE_10 (CRB)
- **Note:** This is inferred from hierarchy structure - NODE_3 is child of NODE_2, and NODE_10 is sibling

---

## Rule Type Summary

| NODE_ID | Node Name | Rule Type | Measure | Dimensions Used |
|---------|-----------|-----------|---------|-----------------|
| 2 | CORE Products | Type 1 | daily_pnl | product_line |
| 3 | Core Ex CRB | Type 3 (Inferred) | - | - (Node arithmetic) |
| 4 | Commissions | Type 2 + Arithmetic | daily_commission, daily_trade | strategy, process_2 |
| 5 | Commissions (Non Swap) | Type 2 | daily_commission | strategy |
| 6 | Swap Commission | Type 2 | daily_trade | strategy, process_2 |
| 7 | Trading | Type 3 | - | - (Node arithmetic) |
| 8 | Facilitations | Type 3 | - | - (Node arithmetic) |
| 9 | Inventory Management | Type 2 | daily_pnl | strategy, process_2 |
| 10 | CRB | Type 2 | daily_pnl | strategy, book |
| 11 | ETF Amber | Type 1 | daily_pnl | strategy |
| 12 | MSET | Type 1 | daily_pnl | process_1 |

---

## Key Observations

### 1. Measure Variety
- **daily_pnl** - Used in Type 1 and Type 2 rules
- **daily_commission** - Used in Type 2 rules (NODE_ID 4, 5)
- **daily_trade** - Used in Type 2 rules (NODE_ID 4, 6)

### 2. Type 2 Complexity
- **NODE_ID 4** is actually **Type 2 + Arithmetic** - two separate queries added together
- This is a **hybrid rule type** not previously identified

### 3. Type 3 Dependencies
- **NODE_7** depends on NODE_3 and NODE_4 (both have Type 2 rules)
- **NODE_8** depends on NODE_7 (Type 3) and NODE_9 (Type 2)
- **NODE_3** (inferred) depends on NODE_2 (Type 1) and NODE_10 (Type 2)

### 4. Execution Order Requirements
1. **Phase 1:** Natural rollup (if any nodes don't have rules)
2. **Phase 2:** Type 1 rules (simple filters)
3. **Phase 3:** Type 2 rules (multi-condition filters)
4. **Phase 4:** Type 3 rules (node arithmetic) - **Must execute in dependency order**
   - NODE_3 first (depends on NODE_2, NODE_10)
   - NODE_7 second (depends on NODE_3, NODE_4)
   - NODE_8 last (depends on NODE_7, NODE_9)

### 5. Missing Root Node
- Hierarchy shows NODE_ID 2 as Level 1, but no explicit ROOT node
- **Question:** Should we create a ROOT node that sums all Level 1 nodes?

---

## Architectural Implications

### 1. Enhanced Type 2 Rules
- Need to support **arithmetic of multiple queries** (NODE_ID 4)
- Pattern: `SUM(Measure1) WHERE ... + SUM(Measure2) WHERE ...`

### 2. Type 3 Dependency Resolution
- Must build dependency graph
- Execute Type 3 rules in topological order
- Detect circular dependencies

### 3. Multiple Measures
- Rules can use different measures (`daily_pnl`, `daily_commission`, `daily_trade`)
- Need to track which measure each rule uses

### 4. IN Clauses
- Type 2 rules use `IN` clauses for multiple values
- Examples: `Books IN ('MSAL', 'ETFUS', ...)`, `Process_2 IN ('SWAP COMMISSION', 'SD COMMISSION')`

---

## Questions for Clarification

1. **NODE_ID 3 (Core Ex CRB):**
   - Is the inferred rule `NODE_3 = NODE_2 - NODE_10` correct?
   - Or does NODE_3 have its own Type 2 rule not shown?

2. **Root Node:**
   - Should we create a ROOT node that sums all Level 1 nodes?
   - Or is NODE_ID 2 (CORE Products) the effective root?

3. **Type 2 + Arithmetic (NODE_ID 4):**
   - Should this be a new rule type "Type 2B"?
   - Or handled as Type 2 with special syntax?

4. **Measure Selection:**
   - How does user specify which measure to use? (daily_pnl vs daily_commission vs daily_trade)
   - Is this part of the rule definition?

5. **Node Name Mapping:**
   - NODE_ID 11: Node name "ETF Amber" maps to Strategy "ETF Amer" - how to handle name differences?
   - Mapping table needed?

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-01  
**Status:** Complete - All Rules Documented


