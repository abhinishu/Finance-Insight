-- Migration 006: Trading Track Foundation
-- Phase 5: Rich Trading Use Case - Parallel Data Track
-- Created: Phase 5.0

-- 1. Create the detailed Fact Table
CREATE TABLE fact_trading_pnl (
    entry_id UUID PRIMARY KEY,
    use_case_id UUID NOT NULL REFERENCES use_cases(use_case_id) ON DELETE CASCADE,
    effective_date DATE NOT NULL,
    
    -- Dimensions (Matches Screenshot + Requirements)
    taps_account VARCHAR(50),
    company_code VARCHAR(50),
    cost_center VARCHAR(50),
    division VARCHAR(50),
    business_area VARCHAR(100),
    product_line VARCHAR(100),
    strategy VARCHAR(100),
    book VARCHAR(100),
    process_1 VARCHAR(100), -- For Rule Logic
    process_2 VARCHAR(100), -- For Rule Logic

    -- Measures (Daily & YTD for separate components)
    pnl_trading_daily    NUMERIC(18, 2) DEFAULT 0,
    pnl_trading_ytd      NUMERIC(18, 2) DEFAULT 0,
    pnl_commission_daily NUMERIC(18, 2) DEFAULT 0,
    pnl_commission_ytd   NUMERIC(18, 2) DEFAULT 0,
    
    -- Totals (Pre-calculated for performance)
    pnl_total_daily      NUMERIC(18, 2) DEFAULT 0,
    pnl_total_ytd        NUMERIC(18, 2) DEFAULT 0,
    pnl_qtd              NUMERIC(18, 2) DEFAULT 0, -- As per screenshot

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices for Rule Engine Performance
CREATE INDEX idx_trade_dt ON fact_trading_pnl(effective_date);
CREATE INDEX idx_trade_strat ON fact_trading_pnl(strategy);
CREATE INDEX idx_trade_proc2 ON fact_trading_pnl(process_2);
CREATE INDEX idx_trade_use_case ON fact_trading_pnl(use_case_id);

-- 2. Update Use Case Table to support "Types"
-- This flag tells the UI which "Mode" to load.
ALTER TABLE use_cases ADD COLUMN use_case_type VARCHAR(50) DEFAULT 'STANDARD'; 

-- 3. Update Rules Table to support the 3 Logic Types
ALTER TABLE metadata_rules ADD COLUMN rule_type VARCHAR(20) DEFAULT 'DIRECT'; -- DIRECT, FILTER, FORMULA
ALTER TABLE metadata_rules ADD COLUMN target_measure VARCHAR(50); -- To store 'pnl_commission' vs 'pnl_trading'



