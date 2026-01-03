-- Migration 006: Create fact_trading_pnl table for Phase 5 (Rich Trading Use Case)
-- This table stores granular trading P&L data with multiple dimensions
-- Created: Phase 5.0

CREATE TABLE fact_trading_pnl (
    entry_id UUID PRIMARY KEY,
    use_case_id UUID NOT NULL REFERENCES use_cases(use_case_id) ON DELETE CASCADE,
    effective_date DATE NOT NULL,
    taps_account VARCHAR(50),
    company_code VARCHAR(50),   -- '1234'
    cost_center VARCHAR(50),    -- 'ABC1'
    division VARCHAR(50),       -- 'IED'
    business_area VARCHAR(100), -- 'Cash Equity'
    product_line VARCHAR(100),  -- 'Core Products'
    strategy VARCHAR(100),      -- 'CORE'
    book VARCHAR(100),          -- 'CORE 1'
    daily_pnl NUMERIC(18, 2) DEFAULT 0,
    wtd_pnl NUMERIC(18, 2) DEFAULT 0,
    mtd_pnl NUMERIC(18, 2) DEFAULT 0,
    qtd_pnl NUMERIC(18, 2) DEFAULT 0,
    ytd_pnl NUMERIC(18, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance indexes
CREATE INDEX idx_trading_pnl_date ON fact_trading_pnl(effective_date);
CREATE INDEX idx_trading_pnl_strategy ON fact_trading_pnl(strategy);
CREATE INDEX idx_trading_pnl_division ON fact_trading_pnl(division);
CREATE INDEX idx_trading_pnl_use_case ON fact_trading_pnl(use_case_id);



