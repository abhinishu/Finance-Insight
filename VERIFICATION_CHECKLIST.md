# Phase 1 Verification Checklist

## ✅ Database Connection
- [x] PostgreSQL connected
- [x] Database `finance_insight` exists
- [x] User `finance_user` created with correct permissions

## ✅ Database Schema
- [x] All 6 tables created:
  - [x] use_cases
  - [x] use_case_runs
  - [x] dim_hierarchy
  - [x] metadata_rules
  - [x] fact_pnl_gold
  - [x] fact_calculated_results

## ✅ Mock Data
- [x] 1,000 fact rows generated
- [x] 70 hierarchy nodes created
- [x] 50 leaf nodes
- [x] MOCK_ATLAS_v1 structure available

## ✅ Backend API
- [x] Backend server running (http://localhost:8000)
- [x] Health endpoint working (`/health`)
- [x] Discovery API working (`/api/v1/discovery`)
- [x] API returns hierarchy data with natural values

## ✅ Frontend
- [ ] Open http://localhost:3000
- [ ] Select "MOCK_ATLAS_v1" from dropdown
- [ ] Grid displays hierarchy tree
- [ ] No network errors in browser console (F12)
- [ ] Natural values (Daily, MTD, YTD) visible
- [ ] Can expand/collapse tree nodes

---

## 🧪 Quick Test Commands

### Test Backend API:
```powershell
curl "http://localhost:8000/api/v1/discovery?structure_id=MOCK_ATLAS_v1"
```

### Test Backend Health:
```powershell
curl http://localhost:8000/health
```

### Run Full Test Suite:
```powershell
$env:DATABASE_URL="postgresql://finance_user:finance_pass@localhost:5432/finance_insight"
python scripts/test_backend.py
```

---

## 🎯 Expected Frontend Behavior

When you open http://localhost:3000:

1. **Discovery Screen** should load
2. **Atlas Structure dropdown** should show "MOCK_ATLAS_v1"
3. **After selecting structure:**
   - Grid should populate with hierarchy tree
   - Root node should be visible
   - Daily, MTD, YTD columns should show values
   - Can expand nodes to see children
   - No error messages

---

## 🐛 If Frontend Still Shows Network Error

1. **Check browser console (F12):**
   - Look for specific error messages
   - Check Network tab for failed requests

2. **Verify backend is running:**
   ```powershell
   curl http://localhost:8000/health
   ```

3. **Verify API endpoint:**
   ```powershell
   curl "http://localhost:8000/api/v1/discovery?structure_id=MOCK_ATLAS_v1"
   ```

4. **Check CORS settings** in `app/main.py` (should allow all origins for development)

5. **Restart backend** if needed:
   ```powershell
   $env:DATABASE_URL="postgresql://finance_user:finance_pass@localhost:5432/finance_insight"
   uvicorn app.main:app --reload
   ```

---

## ✅ Phase 1 Complete When:

- [x] All backend tests pass
- [x] Discovery API returns data
- [ ] Frontend displays data in grid
- [ ] No network errors
- [ ] Can interact with hierarchy tree

**Once frontend works, Phase 1 is 100% complete!** 🎉

