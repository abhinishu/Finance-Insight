# Use Case 3: Input Table Schema Definition

**Document Purpose:** Detailed schema definition for Use Case 3 input table based on Excel structure.

**Status:** Confirmed  
**Date:** 2026-01-01  
**Source:** Excel tab "Input table for use case 3"

---

## Schema Definition

### Table Name
**Proposed:** `fact_pnl_use_case_3` or `fact_pnl_america_cash_equity`

### Columns

#### Dimensions (8 columns)

| Column Name | Data Type | Nullable | Description | Sample Values |
|-------------|-----------|----------|-------------|---------------|
| `cost_center` | VARCHAR(50) | NO | Cost Center identifier | "ABC1" |
| `division` | VARCHAR(50) | NO | Division identifier | "IED" |
| `business_area` | VARCHAR(100) | NO | Business Area name | "Cash Equity" |
| `product_line` | VARCHAR(100) | NO | Product Line name | "Core Products", "Core Primary" |
| `strategy` | VARCHAR(100) | NO | Strategy identifier | "CORE", "CORE Primary 1" |
| `process_1` | VARCHAR(50) | NO | Process 1 identifier | "MSET" |
| `process_2` | VARCHAR(100) | NO | Process 2 identifier | "Inventory Man", "ABC", "DEF" |
| `book` | VARCHAR(100) | NO | Book identifier | "CORE 1", "Core Primary 1 - CORE" |

#### Measures (3 columns)

| Column Name | Data Type | Nullable | Description | Sample Values |
|-------------|-----------|----------|-------------|---------------|
| `daily_pnl` | NUMERIC(18,2) | NO | Daily Profit & Loss | 100, -200, 50 |
| `daily_commission` | NUMERIC(18,2) | NO | Daily Commission | 20, -20, 5 |
| `daily_trade` | NUMERIC(18,2) | NO | Daily Trade Count/Volume | 10, -10, 10 |

#### System Columns (Recommended)

| Column Name | Data Type | Nullable | Description |
|-------------|-----------|----------|-------------|
| `id` | UUID | NO | Primary key |
| `use_case_id` | UUID | NO | Foreign key to `use_cases.use_case_id` |
| `pnl_date` | DATE | NO | P&L date (for temporal analysis) |
| `created_at` | TIMESTAMP | NO | Record creation timestamp |
| `updated_at` | TIMESTAMP | YES | Record update timestamp |

---

## Sample Data

```sql
INSERT INTO fact_pnl_use_case_3 (
    cost_center, division, business_area, product_line, strategy, 
    process_1, process_2, book,
    daily_pnl, daily_commission, daily_trade,
    use_case_id, pnl_date
) VALUES
('ABC1', 'IED', 'Cash Equity', 'Core Products', 'CORE', 'MSET', 'Inventory Man', 'CORE 1', 100, 20, 10, '...', '2026-01-01'),
('ABC1', 'IED', 'Cash Equity', 'Core Products', 'CORE', 'MSET', 'ABC', 'CORE 1', -200, -20, -10, '...', '2026-01-01'),
('ABC1', 'IED', 'Cash Equity', 'Core Primary', 'CORE Primary 1', 'MSET', 'DEF', 'Core Primary 1 - CORE', 50, 5, 10, '...', '2026-01-01');
```

---

## Business Rule Implications

### Type 1 Rules (Simple Dimension Filtering)

**Example:** `SUM(DAILY_PNL) WHERE Strategy='CORE'`

**Available Dimensions for Type 1:**
- `cost_center` - e.g., `WHERE cost_center = 'ABC1'`
- `division` - e.g., `WHERE division = 'IED'`
- `business_area` - e.g., `WHERE business_area = 'Cash Equity'`
- `product_line` - e.g., `WHERE product_line = 'Core Products'`
- `strategy` - e.g., `WHERE strategy = 'CORE'` ✅ **Confirmed in requirement**
- `process_1` - e.g., `WHERE process_1 = 'MSET'`
- `process_2` - e.g., `WHERE process_2 = 'Inventory Man'`
- `book` - e.g., `WHERE book = 'CORE 1'`

### Type 2 Rules (Multi-Condition Filtering)

**Example:** `SUM(DAILY_PNL) WHERE Strategy='CORE' AND Process_2='Inventory Man'`

**Available Dimensions for Type 2:**
- Any combination of the 8 dimensions
- **Confirmed:** Strategy + Process_2 combination (as per requirement)

### Type 3 Rules (Node Arithmetic)

**Example:** `NODE_5 = NODE_3 + NODE_4`

**Measures Available:**
- `daily_pnl` - Primary measure for P&L calculations
- `daily_commission` - Secondary measure
- `daily_trade` - Trade count/volume measure

---

## SQL CREATE TABLE Statement

```sql
CREATE TABLE fact_pnl_use_case_3 (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Dimensions
    cost_center VARCHAR(50) NOT NULL,
    division VARCHAR(50) NOT NULL,
    business_area VARCHAR(100) NOT NULL,
    product_line VARCHAR(100) NOT NULL,
    strategy VARCHAR(100) NOT NULL,
    process_1 VARCHAR(50) NOT NULL,
    process_2 VARCHAR(100) NOT NULL,
    book VARCHAR(100) NOT NULL,
    
    -- Measures
    daily_pnl NUMERIC(18,2) NOT NULL,
    daily_commission NUMERIC(18,2) NOT NULL,
    daily_trade NUMERIC(18,2) NOT NULL,
    
    -- System Columns
    use_case_id UUID NOT NULL REFERENCES use_cases(use_case_id) ON DELETE CASCADE,
    pnl_date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    
    -- Indexes for performance
    CONSTRAINT idx_use_case_3_dimensions UNIQUE (cost_center, division, business_area, product_line, strategy, process_1, process_2, book, pnl_date)
);

-- Indexes for common filter patterns
CREATE INDEX idx_use_case_3_strategy ON fact_pnl_use_case_3(strategy);
CREATE INDEX idx_use_case_3_process_2 ON fact_pnl_use_case_3(process_2);
CREATE INDEX idx_use_case_3_strategy_process2 ON fact_pnl_use_case_3(strategy, process_2);
CREATE INDEX idx_use_case_3_date ON fact_pnl_use_case_3(pnl_date);
CREATE INDEX idx_use_case_3_use_case ON fact_pnl_use_case_3(use_case_id);
```

---

## Questions for Clarification

1. **Temporal Analysis:**
   - Should we add `pnl_date` column? (Needed for MTD, YTD calculations)
   - Should we add `mtd_pnl`, `ytd_pnl` columns? (Or calculate on-the-fly?)

2. **Data Volume:**
   - How many rows expected per day?
   - Historical data retention period?
   - Partitioning strategy? (By date?)

3. **Data Loading:**
   - How is data loaded? (Manual import, ETL, API?)
   - Frequency? (Daily, real-time, batch?)
   - Source system?

4. **Additional Measures:**
   - Are `Daily_Commission` and `Daily_Trade` used in business rules?
   - Or only `Daily_PNL`?

5. **Dimension Values:**
   - Are dimension values fixed/enumerated? (Should we create `dim_dictionary` entries?)
   - Or free-form text?

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-01  
**Status:** Schema Confirmed, Awaiting Business Rules Tab

