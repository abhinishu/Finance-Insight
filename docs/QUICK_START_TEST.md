# Quick Start: Test Phase 1 in 5 Minutes

## 🚀 Fastest Way to Test Phase 1

### 1. Start PostgreSQL (if not running)
```bash
# Windows (if installed as service, it should auto-start)
# Or start manually from Services

# Linux/Mac
sudo service postgresql start
# or
brew services start postgresql
```

### 2. Run End-to-End Test (Does Everything!)
```bash
python scripts/end_to_end_test.py
```

This single command will:
- ✅ Initialize database
- ✅ Generate mock data
- ✅ Create test use case
- ✅ Run calculation
- ✅ Validate results
- ✅ Print summary

**Expected Output:**
```
✓ Mock data generated and validated
✓ Test use case created: <uuid>
✓ Calculation completed: <duration>ms
✓ Results saved: <count> rows
✓ Validation status: PASSED
✓ End-to-End Test PASSED!
```

### 3. Test Discovery API

**Start FastAPI server:**
```bash
uvicorn app.main:app --reload
```

**In another terminal, test the endpoint:**
```bash
# Get the use case ID from end_to_end_test output, then:
python scripts/test_discovery_api.py <USE_CASE_ID>
```

**Or use curl:**
```bash
curl http://localhost:8000/api/v1/use-cases/<USE_CASE_ID>/discovery
```

**Or open in browser:**
```
http://localhost:8000/api/v1/use-cases/<USE_CASE_ID>/discovery
```

---

## ✅ What You Should See

### End-to-End Test Output
- All steps complete successfully
- Validation status: PASSED
- Performance metrics displayed

### Discovery API Response
- JSON with hierarchy tree
- Natural values for each node
- Nested children structure
- Root node with aggregated values

---

## 🎯 Key Verification Points

1. **Calculation Speed**: Should complete in < 5 seconds
2. **API Response**: Should return in < 2 seconds
3. **Data Integrity**: All validations pass
4. **Tree Structure**: Nested hierarchy is correct
5. **Natural Values**: Match fact table sums

---

## 📊 Sample API Response

```json
{
  "use_case_id": "123e4567-e89b-12d3-a456-426614174000",
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
      "children": [
        {
          "node_id": "Region_A",
          "node_name": "Region A",
          "parent_node_id": "ROOT",
          "depth": 1,
          "is_leaf": false,
          "daily_pnl": "500000.00",
          "mtd_pnl": "5000000.00",
          "ytd_pnl": "50000000.00",
          "children": [...]
        }
      ]
    }
  ]
}
```

---

## 🐛 Troubleshooting

### Database Connection Error
- Check PostgreSQL is running
- Verify DATABASE_URL in .env or database.py
- Check credentials

### Import Errors
- Run: `pip install -r requirements.txt`
- Verify Python version (3.8+)

### API Not Responding
- Check server is running: `uvicorn app.main:app --reload`
- Verify port 8000 is available
- Check for error messages in terminal

---

**That's it! Phase 1 is fully testable without any UI.**

