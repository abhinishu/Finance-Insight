-- ============================================================================
-- Migration 007: Phase 5.1 Database Schema Foundation
-- ============================================================================
-- Purpose: Add support for Use Case 3 (America Cash Equity Trading)
--          - Extend metadata_rules with rule types and expressions
--          - Add input_table_name to use_cases for table-per-use-case strategy
--          - Create fact_pnl_use_case_3 table for Use Case 3 data
--
-- Date: 2026-01-01
-- Phase: 5.1 - Database Schema Foundation
-- ============================================================================

BEGIN;

-- ============================================================================
-- PART 1: Update metadata_rules Table
-- ============================================================================
-- Add columns to support new rule types (Type 1, Type 2, Type 2B, Type 3)

-- Add rule_type column (VARCHAR(20), nullable, default 'FILTER')
-- Values: 'FILTER' (Type 1/2), 'FILTER_ARITHMETIC' (Type 2B), 'NODE_ARITHMETIC' (Type 3)
ALTER TABLE metadata_rules
ADD COLUMN IF NOT EXISTS rule_type VARCHAR(20) DEFAULT 'FILTER';

-- Add measure_name column (VARCHAR(50), nullable, default 'daily_pnl')
-- Values: 'daily_pnl', 'daily_commission', 'daily_trade', etc.
ALTER TABLE metadata_rules
ADD COLUMN IF NOT EXISTS measure_name VARCHAR(50) DEFAULT 'daily_pnl';

-- Add rule_expression column (TEXT, nullable)
-- Stores arithmetic expressions for Type 3 rules (e.g., "NODE_3 - NODE_4")
ALTER TABLE metadata_rules
ADD COLUMN IF NOT EXISTS rule_expression TEXT;

-- Add rule_dependencies column (JSONB, nullable)
-- Stores list of node IDs this rule depends on (for Type 3 rules)
-- Format: ["NODE_3", "NODE_4"]
ALTER TABLE metadata_rules
ADD COLUMN IF NOT EXISTS rule_dependencies JSONB;

-- Update existing rows to have default values
UPDATE metadata_rules
SET rule_type = 'FILTER'
WHERE rule_type IS NULL;

UPDATE metadata_rules
SET measure_name = 'daily_pnl'
WHERE measure_name IS NULL;

-- Add comment for documentation
COMMENT ON COLUMN metadata_rules.rule_type IS 'Rule type: FILTER (Type 1/2), FILTER_ARITHMETIC (Type 2B), NODE_ARITHMETIC (Type 3)';
COMMENT ON COLUMN metadata_rules.measure_name IS 'Measure name for rule execution (e.g., daily_pnl, daily_commission, daily_trade)';
COMMENT ON COLUMN metadata_rules.rule_expression IS 'Arithmetic expression for Type 3 rules (e.g., "NODE_3 - NODE_4")';
COMMENT ON COLUMN metadata_rules.rule_dependencies IS 'JSON array of node IDs this rule depends on (for Type 3 rules)';

-- ============================================================================
-- PART 2: Update use_cases Table
-- ============================================================================
-- Add input_table_name to support table-per-use-case strategy

-- Add input_table_name column (VARCHAR(100), nullable)
-- Values: NULL (use default fact_pnl_gold), 'fact_pnl_use_case_3', etc.
ALTER TABLE use_cases
ADD COLUMN IF NOT EXISTS input_table_name VARCHAR(100);

-- Add comment for documentation
COMMENT ON COLUMN use_cases.input_table_name IS 'Input table name for this use case (NULL = use default fact_pnl_gold). Enables table-per-use-case strategy.';

-- ============================================================================
-- PART 3: Create fact_pnl_use_case_3 Table
-- ============================================================================
-- Dedicated storage for "America Cash Equity Trading" use case data
-- All PnL columns use NUMERIC(18,2) to maintain Decimal precision

CREATE TABLE IF NOT EXISTS fact_pnl_use_case_3 (
    -- Primary Key
    entry_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Temporal Dimension
    effective_date DATE NOT NULL,
    
    -- Hierarchical Dimensions (matching Use Case 3 input structure)
    cost_center VARCHAR(50),
    division VARCHAR(50),
    business_area VARCHAR(100),
    product_line VARCHAR(100),
    strategy VARCHAR(100),
    process_1 VARCHAR(100),
    process_2 VARCHAR(100),
    book VARCHAR(100),
    
    -- Financial Measures (CRITICAL: NUMERIC(18,2) for Decimal precision)
    pnl_daily NUMERIC(18, 2) NOT NULL DEFAULT 0,
    pnl_commission NUMERIC(18, 2) NOT NULL DEFAULT 0,
    pnl_trade NUMERIC(18, 2) NOT NULL DEFAULT 0,
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add table comment
COMMENT ON TABLE fact_pnl_use_case_3 IS 'Dedicated fact table for Use Case 3: America Cash Equity Trading. All PnL columns use NUMERIC(18,2) for Decimal precision.';

-- Add column comments
COMMENT ON COLUMN fact_pnl_use_case_3.entry_id IS 'Primary key UUID';
COMMENT ON COLUMN fact_pnl_use_case_3.effective_date IS 'Effective date for P&L entry';
COMMENT ON COLUMN fact_pnl_use_case_3.cost_center IS 'Cost center dimension';
COMMENT ON COLUMN fact_pnl_use_case_3.division IS 'Division dimension';
COMMENT ON COLUMN fact_pnl_use_case_3.business_area IS 'Business area dimension';
COMMENT ON COLUMN fact_pnl_use_case_3.product_line IS 'Product line dimension';
COMMENT ON COLUMN fact_pnl_use_case_3.strategy IS 'Strategy dimension (e.g., CORE, NON-CORE)';
COMMENT ON COLUMN fact_pnl_use_case_3.process_1 IS 'Process 1 dimension';
COMMENT ON COLUMN fact_pnl_use_case_3.process_2 IS 'Process 2 dimension (e.g., Inventory Management, SWAP COMMISSION)';
COMMENT ON COLUMN fact_pnl_use_case_3.book IS 'Book dimension';
COMMENT ON COLUMN fact_pnl_use_case_3.pnl_daily IS 'Daily P&L amount (NUMERIC(18,2) for Decimal precision)';
COMMENT ON COLUMN fact_pnl_use_case_3.pnl_commission IS 'Daily commission amount (NUMERIC(18,2) for Decimal precision)';
COMMENT ON COLUMN fact_pnl_use_case_3.pnl_trade IS 'Daily trade amount (NUMERIC(18,2) for Decimal precision)';
COMMENT ON COLUMN fact_pnl_use_case_3.created_at IS 'Record creation timestamp';

-- ============================================================================
-- PART 4: Create Indices for Performance
-- ============================================================================
-- Indices on frequently queried columns

-- Index on effective_date (for date range queries)
CREATE INDEX IF NOT EXISTS idx_fact_pnl_uc3_effective_date 
ON fact_pnl_use_case_3(effective_date);

-- Index on strategy (for Type 1/2 rule filtering)
CREATE INDEX IF NOT EXISTS idx_fact_pnl_uc3_strategy 
ON fact_pnl_use_case_3(strategy);

-- Index on process_2 (for Type 2 rule filtering)
CREATE INDEX IF NOT EXISTS idx_fact_pnl_uc3_process_2 
ON fact_pnl_use_case_3(process_2);

-- Composite index for common query patterns (strategy + process_2)
CREATE INDEX IF NOT EXISTS idx_fact_pnl_uc3_strategy_process2 
ON fact_pnl_use_case_3(strategy, process_2);

-- Index on effective_date + strategy (for date-filtered strategy queries)
CREATE INDEX IF NOT EXISTS idx_fact_pnl_uc3_date_strategy 
ON fact_pnl_use_case_3(effective_date, strategy);

-- ============================================================================
-- PART 5: Verification Queries (for manual validation)
-- ============================================================================
-- Uncomment to verify migration:

-- Verify metadata_rules columns
-- SELECT column_name, data_type, column_default, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'metadata_rules'
-- AND column_name IN ('rule_type', 'measure_name', 'rule_expression', 'rule_dependencies')
-- ORDER BY column_name;

-- Verify use_cases column
-- SELECT column_name, data_type, column_default, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'use_cases'
-- AND column_name = 'input_table_name';

-- Verify fact_pnl_use_case_3 table and columns
-- SELECT column_name, data_type, numeric_precision, numeric_scale, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'fact_pnl_use_case_3'
-- ORDER BY ordinal_position;

-- Verify PnL columns are NUMERIC (not FLOAT/REAL)
-- SELECT column_name, data_type
-- FROM information_schema.columns
-- WHERE table_name = 'fact_pnl_use_case_3'
-- AND column_name LIKE 'pnl_%'
-- AND data_type NOT IN ('numeric', 'decimal');

-- Verify indices
-- SELECT indexname, indexdef
-- FROM pg_indexes
-- WHERE tablename = 'fact_pnl_use_case_3'
-- ORDER BY indexname;

COMMIT;

-- ============================================================================
-- Migration 007 Complete
-- ============================================================================
-- Next Steps:
-- 1. Run verification script: python scripts/verify_phase5_schema.py
-- 2. Update SQLAlchemy models in app/models.py
-- 3. Test with existing use cases (backward compatibility)
-- ============================================================================


