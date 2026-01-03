# Project Sterling - Step 1: Multi-Dimensional Fact Hydration

**Date:** December 24, 2025  
**Status:** ✅ COMPLETE

---

## ✅ Task Summary

Successfully created and imported 60 rows of trade-level data (30 trades × 2 scenarios) into `fact_pnl_entries` table with multi-dimensional attributes and edge cases.

---

## 📊 Data Created

### CSV File
- **Location:** `metadata/seed/sterling_facts.csv`
- **Total Rows:** 60 (30 trades with ACTUAL + PRIOR scenarios)
- **Format:** CSV with headers

### Data Structure
Each row contains:
- `use_case_id` - Auto-populated during import
- `pnl_date` - 2025-12-24 (COB date)
- `category_code` - Trade identifier (TRADE_001 through TRADE_030)
- `daily_amount` - Daily P&L value
- `wtd_amount` - Week-to-date value
- `ytd_amount` - Year-to-date value
- `scenario` - ACTUAL or PRIOR
- `amount` - Legacy column (same as daily_amount)
- **Dimensions** (stored in `audit_metadata` JSONB):
  - `legal_entity` - US_HOLDINGS or UK_LTD
  - `region` - AMER or EMEA
  - `strategy` - ALGO, VOL, or MARKET_MAKING
  - `risk_officer` - NYC_001 or LDN_001

---

## 🎯 Dimension Mix

### Legal Entity Distribution
- **US_HOLDINGS:** 15 trades (50%)
- **UK_LTD:** 15 trades (50%)

### Region Distribution
- **AMER:** 15 trades (50%)
- **EMEA:** 15 trades (50%)

### Strategy Distribution
- **ALGO:** 10 trades (33.3%)
- **VOL:** 10 trades (33.3%)
- **MARKET_MAKING:** 10 trades (33.3%)

### Risk Officer Distribution
- **NYC_001:** 15 trades (50%)
- **LDN_001:** 15 trades (50%)

---

## 🔍 Edge Cases Included

### Edge Case 1: ACTUAL > 0 and PRIOR = 0
- **Trade:** TRADE_021
- **ACTUAL:** daily=450000, wtd=3150000, ytd=45000000
- **PRIOR:** daily=0, wtd=0, ytd=0
- **Purpose:** Tests new trade scenario where no prior period data exists

### Edge Case 2: Daily = 0 but YTD = 5,000,000
- **Trade:** TRADE_022
- **ACTUAL:** daily=0, wtd=3500000, ytd=5000000
- **PRIOR:** daily=0, wtd=3400000, ytd=4800000
- **Purpose:** Tests scenario where daily activity is zero but cumulative YTD exists

---

## 💾 Database Injection

### Import Script
- **File:** `scripts/import_sterling_facts.py`
- **Function:** `import_sterling_facts()`
- **Logic:** UPSERT (Update if exists, Insert if new)
- **Matching Keys:** use_case_id, pnl_date, category_code, scenario

### Import Results
```
[SUCCESS] Import complete:
   - Imported: 0
   - Updated: 60
   - Skipped: 0
   - Total Processed: 60
   - Final Row Count in DB: 60
   - Use Case ID: b90f1708-4087-4117-9820-9226ed1115bb
```

### Final Status
- ✅ **Total rows injected: 60**
- ✅ All rows have daily, wtd, and ytd values
- ✅ All rows have both ACTUAL and PRIOR scenarios
- ✅ All dimensions stored in audit_metadata
- ✅ Edge cases properly included

---

## 📋 CSV Format

### Headers
```
use_case_id,pnl_date,category_code,daily_amount,wtd_amount,ytd_amount,scenario,legal_entity,region,strategy,risk_officer,amount
```

### Sample Row (ACTUAL)
```
,2025-12-24,TRADE_001,125000.50,875000.25,12500000.75,ACTUAL,US_HOLDINGS,AMER,ALGO,NYC_001,125000.50
```

### Sample Row (PRIOR)
```
,2025-12-24,TRADE_001,120000.00,850000.00,12000000.00,PRIOR,US_HOLDINGS,AMER,ALGO,NYC_001,120000.00
```

---

## 🚀 Usage

### Import Sterling Facts
```powershell
# Auto-create use case
python scripts/import_sterling_facts.py

# Import to specific use case
python scripts/import_sterling_facts.py <use_case_id>
```

### Verify Data
```sql
-- Check total row count
SELECT COUNT(*) FROM fact_pnl_entries WHERE use_case_id = 'b90f1708-4087-4117-9820-9226ed1115bb';

-- Check edge cases
SELECT * FROM fact_pnl_entries 
WHERE category_code = 'TRADE_021' OR category_code = 'TRADE_022'
ORDER BY category_code, scenario;

-- Check dimension distribution
SELECT 
    audit_metadata->>'legal_entity' as legal_entity,
    audit_metadata->>'region' as region,
    audit_metadata->>'strategy' as strategy,
    COUNT(*) as count
FROM fact_pnl_entries
WHERE use_case_id = 'b90f1708-4087-4117-9820-9226ed1115bb'
GROUP BY legal_entity, region, strategy
ORDER BY count DESC;
```

---

## ✅ Verification Checklist

- [x] CSV file created with 60 rows (30 trades × 2 scenarios)
- [x] All rows have daily, wtd, ytd values
- [x] Dimension mix: Legal Entity (UK/US), Region (EMEA/AMER), Strategy (ALGO/VOL/MARKET_MAKING), Risk Officer
- [x] Edge case 1: ACTUAL > 0 and PRIOR = 0 (TRADE_021)
- [x] Edge case 2: Daily = 0 but YTD = 5,000,000 (TRADE_022)
- [x] Import script created with UPSERT logic
- [x] Data successfully injected into fact_pnl_entries
- [x] Total row count: 60 rows

---

## 🎯 Goal Achievement

**Rich, High-Complexity Dataset for F2B Testing:**

1. ✅ **30 trade-level rows** (expanded to 60 with scenarios)
2. ✅ **Multi-dimensional attributes** (Legal Entity, Region, Strategy, Risk Officer)
3. ✅ **Complete measure coverage** (daily, wtd, ytd for both ACTUAL and PRIOR)
4. ✅ **Edge cases included** (new trade, zero daily with YTD)
5. ✅ **UPSERT logic** (idempotent import)
6. ✅ **Total rows injected: 60**

The dataset is ready for F2B (Front-to-Back) testing with realistic complexity and edge case coverage.

---

**Next Steps:**
- F2B testing with Sterling dataset
- Validation of multi-dimensional aggregations
- Testing edge case handling in calculations



