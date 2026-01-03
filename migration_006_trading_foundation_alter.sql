-- Migration 006: Trading Track Foundation - ALTER existing table
-- Phase 5: Rich Trading Use Case - Parallel Data Track
-- This migration alters the existing fact_trading_pnl table to add new columns

-- 1. Add missing dimension columns to fact_trading_pnl
ALTER TABLE fact_trading_pnl 
ADD COLUMN IF NOT EXISTS process_1 VARCHAR(100),
ADD COLUMN IF NOT EXISTS process_2 VARCHAR(100);

-- 2. Add new measure columns (keeping old ones for backward compatibility)
ALTER TABLE fact_trading_pnl 
ADD COLUMN IF NOT EXISTS pnl_trading_daily NUMERIC(18, 2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS pnl_trading_ytd NUMERIC(18, 2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS pnl_commission_daily NUMERIC(18, 2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS pnl_commission_ytd NUMERIC(18, 2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS pnl_total_daily NUMERIC(18, 2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS pnl_total_ytd NUMERIC(18, 2) DEFAULT 0;

-- Note: pnl_qtd already exists, so we don't need to add it

-- 3. Create indexes (with IF NOT EXISTS equivalent using DO block)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_trade_proc2') THEN
        CREATE INDEX idx_trade_proc2 ON fact_trading_pnl(process_2);
    END IF;
END $$;

-- 4. Update Use Case Table to support "Types" (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'use_cases' AND column_name = 'use_case_type'
    ) THEN
        ALTER TABLE use_cases ADD COLUMN use_case_type VARCHAR(50) DEFAULT 'STANDARD';
    END IF;
END $$;

-- 5. Update Rules Table to support the 3 Logic Types (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'metadata_rules' AND column_name = 'rule_type'
    ) THEN
        ALTER TABLE metadata_rules ADD COLUMN rule_type VARCHAR(20) DEFAULT 'DIRECT';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'metadata_rules' AND column_name = 'target_measure'
    ) THEN
        ALTER TABLE metadata_rules ADD COLUMN target_measure VARCHAR(50);
    END IF;
END $$;



