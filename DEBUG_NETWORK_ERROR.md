# Network Error Debugging - Finance-Insight

## 🔍 Issue Identified

**Problem**: Frontend shows "Network Error" when selecting Atlas structure, and grid is empty.

**Root Cause**: PostgreSQL database is not running/configured, causing the backend API to fail.

---

## ✅ Current Status

### What's Working:
- ✅ Backend server is running (http://localhost:8000)
- ✅ Frontend server is running (http://localhost:3000)
- ✅ Backend health endpoint responds correctly
- ✅ Frontend can connect to backend

### What's Not Working:
- ❌ Database connection (PostgreSQL not running)
- ❌ Discovery API endpoint (returns 500 Internal Server Error)
- ❌ Frontend cannot load hierarchy data (no data in grid)

---

## 🔧 Solution: Set Up PostgreSQL

The application requires PostgreSQL to store:
- Hierarchy structures
- Fact data (P&L rows)
- Use cases and rules
- Calculation results

### Quick Setup Steps:

1. **Install PostgreSQL** (if not installed)
   - Download: https://www.postgresql.org/download/windows/
   - See `POSTGRESQL_SETUP.md` for detailed instructions

2. **Create Database and User:**
   ```sql
   CREATE DATABASE finance_insight;
   CREATE USER finance_user WITH PASSWORD 'finance_pass';
   GRANT ALL PRIVILEGES ON DATABASE finance_insight TO finance_user;
   ```

3. **Initialize Database:**
   ```powershell
   python scripts/init_db.py
   ```
   This will:
   - Create all required tables
   - Run Alembic migrations
   - Verify schema

4. **Generate Mock Data:**
   ```powershell
   python scripts/generate_mock_data.py
   ```
   This will:
   - Generate 1,000 P&L fact rows
   - Create hierarchy with 50 leaf nodes
   - Create "MOCK_ATLAS_v1" structure

5. **Test Backend:**
   ```powershell
   python scripts/test_backend.py
   ```
   This will verify:
   - Database connection
   - Tables exist
   - Mock data exists
   - API endpoints work

6. **Restart Backend** (if needed):
   - Stop current backend (Ctrl+C)
   - Start again: `uvicorn app.main:app --reload`

---

## 🧪 Testing Phase 1

After setting up PostgreSQL, run the comprehensive test:

```powershell
python scripts/test_backend.py
```

**Expected Output:**
```
[OK] Database Connection: SUCCESS
[OK] Database Tables: SUCCESS
[OK] Mock Data: SUCCESS
[OK] Backend Health: SUCCESS
[OK] Discovery API: SUCCESS
```

### Manual API Test:

```powershell
# Test discovery endpoint
curl "http://localhost:8000/api/v1/discovery?structure_id=MOCK_ATLAS_v1"
```

**Expected Response:**
```json
{
  "structure_id": "MOCK_ATLAS_v1",
  "hierarchy": [
    {
      "node_id": "ROOT",
      "node_name": "Root",
      "daily_pnl": "1234567.89",
      "mtd_pnl": "12345678.90",
      "ytd_pnl": "123456789.01",
      "children": [...]
    }
  ]
}
```

### Frontend Test:

1. Open: http://localhost:3000
2. Select: "MOCK_ATLAS_v1" from dropdown
3. **Expected**: Grid should populate with hierarchy tree
4. **Expected**: No network errors in browser console (F12)

---

## 📊 Phase 1 Completion Checklist

Before moving to Phase 2, verify:

- [ ] PostgreSQL installed and running
- [ ] Database `finance_insight` created
- [ ] User `finance_user` created with proper permissions
- [ ] Database initialized (`python scripts/init_db.py` succeeds)
- [ ] Mock data generated (`python scripts/generate_mock_data.py` succeeds)
- [ ] All tests pass (`python scripts/test_backend.py` - all [OK])
- [ ] Discovery API returns data (curl test succeeds)
- [ ] Frontend loads data (no network errors, grid populated)
- [ ] Hierarchy tree displays correctly in AG-Grid
- [ ] Natural values (Daily, MTD, YTD) display correctly

---

## 🐛 Common Issues

### Issue: "Connection refused" Error
**Solution**: PostgreSQL service not running
- Start service: `net start postgresql-x64-XX`
- Or use Services app

### Issue: "Authentication failed"
**Solution**: Wrong credentials
- Check `.env` file or `app/database.py`
- Verify user exists in PostgreSQL

### Issue: "Database does not exist"
**Solution**: Create database (see SQL commands above)

### Issue: "No hierarchy found for structure_id"
**Solution**: Mock data not generated
- Run: `python scripts/generate_mock_data.py`

### Issue: Frontend still shows network error
**Solution**: 
1. Check browser console (F12) for exact error
2. Verify backend is running: http://localhost:8000/health
3. Test API directly: `curl "http://localhost:8000/api/v1/discovery?structure_id=MOCK_ATLAS_v1"`
4. Check CORS settings in `app/main.py`

---

## 📝 Next Steps

1. **Set up PostgreSQL** (see `POSTGRESQL_SETUP.md`)
2. **Run initialization scripts**
3. **Test backend** (`python scripts/test_backend.py`)
4. **Verify frontend** (open http://localhost:3000)
5. **Once all tests pass**, Phase 1 is complete! ✅

---

## 🎯 Goal

**Phase 1 is complete when:**
- All backend tests pass
- Discovery API returns hierarchy data
- Frontend displays hierarchy in AG-Grid
- No network errors
- Natural values (Daily, MTD, YTD) display correctly

**Then we can proceed to Phase 2!** 🚀

