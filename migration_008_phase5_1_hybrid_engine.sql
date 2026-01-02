-- ============================================================================
-- Migration 008: Phase 5.1 Unified Hybrid Engine Schema
-- ============================================================================
-- Purpose: Enable metadata-driven auto-rollup rules
--          - Add rollup_driver and rollup_value_source to dim_hierarchy
--          - Add measure_mapping to use_cases
--          - Migrate existing data for Use Cases 1, 2, and 3
--
-- Date: 2026-01-27
-- Phase: 5.1 - Unified Hybrid Engine
-- ============================================================================

BEGIN;

-- ============================================================================
-- PART 1: Update dim_hierarchy Table
-- ============================================================================
-- Add columns to support auto-rollup rule generation

-- Add rollup_driver column (VARCHAR(50), nullable)
-- Purpose: Tells the engine which database column to filter for this node
-- Values: 'cc_id', 'category_code', 'strategy', 'product_line', etc.
ALTER TABLE dim_hierarchy
ADD COLUMN IF NOT EXISTS rollup_driver VARCHAR(50) NULL;

-- Add rollup_value_source column (VARCHAR(20), nullable, default 'node_id')
-- Purpose: Explicitly tells the engine to use node_id or node_name for matching
-- Values: 'node_id' (default, works for UC 1 & 2), 'node_name' (for UC 3)
ALTER TABLE dim_hierarchy
ADD COLUMN IF NOT EXISTS rollup_value_source VARCHAR(20) NULL DEFAULT 'node_id';

-- Add comments for documentation
COMMENT ON COLUMN dim_hierarchy.rollup_driver IS 
  'Column name in fact table to filter on for auto-rollup (e.g., cc_id, category_code, strategy). NULL = no auto-rollup.';

COMMENT ON COLUMN dim_hierarchy.rollup_value_source IS 
  'Which hierarchy value to use for matching: node_id (default) or node_name. Ensures deterministic matching.';

-- ============================================================================
-- PART 2: Update use_cases Table
-- ============================================================================
-- Add measure_mapping to support different column names across use cases

-- Add measure_mapping column (JSONB, nullable)
-- Purpose: Maps standard measure names to actual database column names
-- Format: {"daily": "daily_pnl", "mtd": "mtd_pnl", "ytd": "ytd_pnl"}
ALTER TABLE use_cases
ADD COLUMN IF NOT EXISTS measure_mapping JSONB NULL;

-- Add comment for documentation
COMMENT ON COLUMN use_cases.measure_mapping IS 
  'JSON mapping of standard measure names to actual database column names. Example: {"daily": "pnl_daily", "mtd": "pnl_commission", "ytd": "pnl_trade"}';

-- ============================================================================
-- PART 3: Data Migration - Use Case 1 (America Trading P&L)
-- ============================================================================
-- Migration Logic:
-- - rollup_driver = 'cc_id' (matches fact_pnl_gold.cc_id)
-- - rollup_value_source = 'node_id' (matches hierarchy.node_id to fact.cc_id)
-- - measure_mapping = standard mapping (daily_pnl, mtd_pnl, ytd_pnl)

UPDATE dim_hierarchy
SET 
    rollup_driver = 'cc_id',
    rollup_value_source = 'node_id'
WHERE atlas_source = 'MOCK_ATLAS_v1'
  AND rollup_driver IS NULL;

-- Set measure_mapping for Use Case 1
UPDATE use_cases
SET measure_mapping = '{"daily": "daily_pnl", "mtd": "mtd_pnl", "ytd": "ytd_pnl", "pytd": "pytd_pnl"}'::jsonb
WHERE name ILIKE '%America Trading%'
  AND measure_mapping IS NULL;

-- ============================================================================
-- PART 4: Data Migration - Use Case 2 (Project Sterling)
-- ============================================================================
-- Migration Logic:
-- - rollup_driver = 'category_code' (matches fact_pnl_entries.category_code)
-- - rollup_value_source = 'node_id' (matches hierarchy.node_id to fact.category_code)
-- - measure_mapping = entries mapping (daily_amount, wtd_amount, ytd_amount)

-- Find Use Case 2 by name pattern
UPDATE dim_hierarchy
SET 
    rollup_driver = 'category_code',
    rollup_value_source = 'node_id'
WHERE atlas_source IN (
    SELECT DISTINCT atlas_structure_id 
    FROM use_cases 
    WHERE name ILIKE '%Sterling%' OR name ILIKE '%Project%'
)
  AND rollup_driver IS NULL;

-- Set measure_mapping for Use Case 2
UPDATE use_cases
SET measure_mapping = '{"daily": "daily_amount", "mtd": "wtd_amount", "ytd": "ytd_amount"}'::jsonb
WHERE (name ILIKE '%Sterling%' OR name ILIKE '%Project%')
  AND measure_mapping IS NULL;

-- ============================================================================
-- PART 5: Data Migration - Use Case 3 (Cash Equity Trading)
-- ============================================================================
-- Migration Logic:
-- - rollup_driver = 'strategy' (for LEAF NODES ONLY - parents aggregate from children)
-- - rollup_value_source = 'node_name' (matches hierarchy.node_name to fact.strategy)
-- - measure_mapping = use case 3 mapping (pnl_daily, pnl_commission, pnl_trade)

-- Find Use Case 3 by name pattern and input_table_name
UPDATE dim_hierarchy
SET 
    rollup_driver = 'strategy',
    rollup_value_source = 'node_name'
WHERE atlas_source IN (
    SELECT DISTINCT atlas_structure_id 
    FROM use_cases 
    WHERE input_table_name = 'fact_pnl_use_case_3'
       OR name ILIKE '%Cash Equity%'
       OR name ILIKE '%America Cash Equity%'
)
  AND is_leaf = TRUE  -- CRITICAL: Only leaf nodes get rollup_driver
  AND rollup_driver IS NULL;

-- Set measure_mapping for Use Case 3
UPDATE use_cases
SET measure_mapping = '{"daily": "pnl_daily", "mtd": "pnl_commission", "ytd": "pnl_trade"}'::jsonb
WHERE input_table_name = 'fact_pnl_use_case_3'
   OR name ILIKE '%Cash Equity%'
   OR name ILIKE '%America Cash Equity%'
  AND measure_mapping IS NULL;

-- ============================================================================
-- PART 6: Validation Queries
-- ============================================================================
-- Verify migration results

-- Check dim_hierarchy migration
DO $$
DECLARE
    uc1_count INTEGER;
    uc2_count INTEGER;
    uc3_count INTEGER;
BEGIN
    -- Use Case 1: Should have rollup_driver = 'cc_id'
    SELECT COUNT(*) INTO uc1_count
    FROM dim_hierarchy
    WHERE atlas_source = 'MOCK_ATLAS_v1'
      AND rollup_driver = 'cc_id'
      AND rollup_value_source = 'node_id';
    
    RAISE NOTICE 'Use Case 1 (America Trading): % nodes migrated with rollup_driver=cc_id', uc1_count;
    
    -- Use Case 2: Should have rollup_driver = 'category_code'
    SELECT COUNT(*) INTO uc2_count
    FROM dim_hierarchy
    WHERE atlas_source IN (
        SELECT DISTINCT atlas_structure_id 
        FROM use_cases 
        WHERE name ILIKE '%Sterling%' OR name ILIKE '%Project%'
    )
      AND rollup_driver = 'category_code'
      AND rollup_value_source = 'node_id';
    
    RAISE NOTICE 'Use Case 2 (Sterling): % nodes migrated with rollup_driver=category_code', uc2_count;
    
    -- Use Case 3: Should have rollup_driver = 'strategy' (leaf nodes only)
    SELECT COUNT(*) INTO uc3_count
    FROM dim_hierarchy
    WHERE atlas_source IN (
        SELECT DISTINCT atlas_structure_id 
        FROM use_cases 
        WHERE input_table_name = 'fact_pnl_use_case_3'
           OR name ILIKE '%Cash Equity%'
    )
      AND is_leaf = TRUE
      AND rollup_driver = 'strategy'
      AND rollup_value_source = 'node_name';
    
    RAISE NOTICE 'Use Case 3 (Cash Equity): % leaf nodes migrated with rollup_driver=strategy', uc3_count;
END $$;

-- Check use_cases measure_mapping
DO $$
DECLARE
    uc1_mapping JSONB;
    uc2_mapping JSONB;
    uc3_mapping JSONB;
BEGIN
    -- Use Case 1
    SELECT measure_mapping INTO uc1_mapping
    FROM use_cases
    WHERE name ILIKE '%America Trading%'
    LIMIT 1;
    
    IF uc1_mapping IS NOT NULL THEN
        RAISE NOTICE 'Use Case 1 measure_mapping: %', uc1_mapping;
    ELSE
        RAISE WARNING 'Use Case 1 measure_mapping is NULL!';
    END IF;
    
    -- Use Case 2
    SELECT measure_mapping INTO uc2_mapping
    FROM use_cases
    WHERE (name ILIKE '%Sterling%' OR name ILIKE '%Project%')
    LIMIT 1;
    
    IF uc2_mapping IS NOT NULL THEN
        RAISE NOTICE 'Use Case 2 measure_mapping: %', uc2_mapping;
    ELSE
        RAISE WARNING 'Use Case 2 measure_mapping is NULL!';
    END IF;
    
    -- Use Case 3
    SELECT measure_mapping INTO uc3_mapping
    FROM use_cases
    WHERE input_table_name = 'fact_pnl_use_case_3'
       OR name ILIKE '%Cash Equity%'
    LIMIT 1;
    
    IF uc3_mapping IS NOT NULL THEN
        RAISE NOTICE 'Use Case 3 measure_mapping: %', uc3_mapping;
    ELSE
        RAISE WARNING 'Use Case 3 measure_mapping is NULL!';
    END IF;
END $$;

-- ============================================================================
-- PART 7: Create Indexes for Performance
-- ============================================================================
-- Index on rollup_driver for fast lookups during rule resolution

CREATE INDEX IF NOT EXISTS idx_dim_hierarchy_rollup_driver 
ON dim_hierarchy(rollup_driver) 
WHERE rollup_driver IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_dim_hierarchy_rollup_value_source 
ON dim_hierarchy(rollup_value_source) 
WHERE rollup_value_source IS NOT NULL;

-- ============================================================================
-- COMMIT TRANSACTION
-- ============================================================================

COMMIT;

-- ============================================================================
-- Migration 008 Complete
-- ============================================================================
-- Summary:
-- ✅ Added rollup_driver and rollup_value_source to dim_hierarchy
-- ✅ Added measure_mapping to use_cases
-- ✅ Migrated Use Case 1: rollup_driver='cc_id', rollup_value_source='node_id'
-- ✅ Migrated Use Case 2: rollup_driver='category_code', rollup_value_source='node_id'
-- ✅ Migrated Use Case 3: rollup_driver='strategy' (leaf only), rollup_value_source='node_name'
-- ✅ Created indexes for performance
-- ============================================================================

