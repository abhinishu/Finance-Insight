# Phase 1 Testing Guide

## 📋 Phase 1 Key Features

### ✅ What's Built (Backend Only - No UI Yet)

1. **Database & Schema**
   - PostgreSQL database with all tables
   - Alembic migrations
   - 6 core tables: use_cases, use_case_runs, dim_hierarchy, metadata_rules, fact_pnl_gold, fact_calculated_results

2. **Mock Data Generation**
   - 1,000 P&L fact rows
   - Ragged hierarchy with 50 leaf nodes
   - Decimal precision throughout

3. **Waterfall Engine**
   - Natural rollup calculation (bottom-up)
   - Rule application (top-down)
   - Reconciliation plug calculation
   - Performance tracking

4. **Mathematical Validation**
   - Root reconciliation
   - Plug sum validation
   - Hierarchy integrity
   - Orphan check (completeness)

5. **CLI Tools**
   - Database initialization
   - Mock data generation
   - Calculation execution
   - Test use case creation

6. **Discovery API** (FastAPI Endpoint)
   - REST API endpoint for discovery view
   - Returns hierarchy with natural values
   - JSON response format

### ❌ What's NOT Built (Phase 3)

- **No React UI** - Frontend will be built in Phase 3
- **No visual interface** - Testing via CLI and API only
- **No browser-based testing** - Use API tools (curl, Postman, etc.)

---

## 🧪 How to Test Phase 1

### Prerequisites

1. **PostgreSQL Running**
   ```bash
   # Check if PostgreSQL is running
   # Default: localhost:5432
   ```

2. **Python Dependencies Installed**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Setup**
   - Create `.env` file (optional, uses defaults if not present)
   - `DATABASE_URL=postgresql://finance_user:finance_pass@localhost:5432/finance_insight`

---

## 📝 Step-by-Step Testing

### Step 1: Initialize Database

```bash
python scripts/init_db.py
```

**Expected Output:**
- Database created (if not exists)
- All tables created
- Schema verified

**Verify:**
- Check PostgreSQL: All 6 tables should exist

---

### Step 2: Generate Mock Data

```bash
python scripts/generate_mock_data.py
```

**Expected Output:**
- 1,000 fact rows generated
- ~38 hierarchy nodes generated
- 50 leaf nodes created
- Validation passed

**Verify:**
- Fact row count: 1,000
- Leaf node count: 50
- All CC IDs mapped to leaf nodes

---

### Step 3: Create Test Use Case

```bash
python scripts/create_test_use_case.py --add-rules
```

**Expected Output:**
- Use case created
- Sample rules added
- Use case ID displayed

**Save the Use Case ID** - You'll need it for testing!

---

### Step 4: Run Calculation

```bash
python scripts/run_calculation.py --use-case-id <USE_CASE_ID>
```

**Expected Output:**
- Run record created
- Calculation completed (< 5 seconds)
- Results saved
- Validation passed
- Summary printed

**Verify:**
- Duration < 5 seconds
- Result rows saved
- Root values displayed
- Validation status: PASSED

---

### Step 5: Test Discovery API

#### Option A: Start FastAPI Server

```bash
uvicorn app.main:app --reload
```

Server will start at: `http://localhost:8000`

#### Option B: Test Discovery Endpoint

**Using curl:**
```bash
curl http://localhost:8000/api/v1/use-cases/<USE_CASE_ID>/discovery
```

**Using Python test script:**
```bash
python scripts/test_discovery_api.py <USE_CASE_ID>
```

**Using browser:**
- Navigate to: `http://localhost:8000/api/v1/use-cases/<USE_CASE_ID>/discovery`
- View JSON response

**Expected Response:**
```json
{
  "use_case_id": "uuid",
  "hierarchy": [
    {
      "node_id": "ROOT",
      "node_name": "Root",
      "parent_node_id": null,
      "depth": 0,
      "is_leaf": false,
      "daily_pnl": "1234567.89",
      "mtd_pnl": "12345678.90",
      "ytd_pnl": "123456789.01",
      "children": [...]
    }
  ]
}
```

---

### Step 6: Run End-to-End Test

```bash
python scripts/end_to_end_test.py
```

**Expected Output:**
- Mock data generated
- Test use case created
- Calculation completed
- Validation passed
- **Overall: PASSED**

---

## 🔍 What to Verify

### 1. Mathematical Integrity
- Root natural rollup = Sum of all fact rows
- Plug sum = 0 (or within tolerance)
- All validations pass

### 2. Performance
- Calculation: < 5 seconds for 1,000 rows
- Discovery API: < 2 seconds response

### 3. Data Quality
- All 50 cost centers mapped to leaf nodes
- Hierarchy is valid tree (single root, no cycles)
- All measures calculated correctly

### 4. API Functionality
- Discovery endpoint returns valid JSON
- Tree structure is nested correctly
- Natural values are present for all nodes

---

## 🛠️ Testing Tools

### 1. CLI Tools (Built-in)
- `scripts/init_db.py` - Database setup
- `scripts/generate_mock_data.py` - Data generation
- `scripts/create_test_use_case.py` - Use case creation
- `scripts/run_calculation.py` - Run calculations
- `scripts/end_to_end_test.py` - Full workflow test

### 2. API Testing
- **curl** - Command line HTTP client
- **Postman** - GUI API testing tool
- **Browser** - Direct URL access
- **Python requests** - `scripts/test_discovery_api.py`

### 3. Database Inspection
- **psql** - PostgreSQL command line
- **pgAdmin** - PostgreSQL GUI tool
- **SQLAlchemy** - Python ORM queries

---

## 📊 Quick Test Checklist

- [ ] Database initialized successfully
- [ ] Mock data generated (1,000 rows, 50 leaf nodes)
- [ ] Test use case created
- [ ] Calculation runs successfully (< 5 seconds)
- [ ] Validation passes (all checks)
- [ ] Discovery API returns valid JSON
- [ ] Tree structure is correct
- [ ] Natural values match fact sums
- [ ] End-to-end test passes

---

## 🎯 Testing Without UI

Since there's **no React UI yet** (Phase 3), you can test via:

1. **CLI Commands** - All functionality accessible via scripts
2. **API Endpoints** - Use curl, Postman, or browser
3. **Database Queries** - Direct SQL inspection
4. **Python Scripts** - Programmatic testing

---

## 🚀 Next Steps After Testing

Once Phase 1 is validated:
- **Phase 2**: Complete REST API + GenAI integration
- **Phase 3**: Build React UI with three-tab interface

---

## 📝 Notes

- **No Visual UI**: Phase 1 is backend-only
- **API Testing**: Use tools like Postman for better visualization
- **JSON Response**: Discovery API returns JSON that will power the UI in Phase 3
- **Performance**: Monitor calculation and API response times

**Phase 1 is fully testable via CLI and API - no UI required!**

