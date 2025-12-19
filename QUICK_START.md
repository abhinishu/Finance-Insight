# Quick Start Guide - Finance-Insight

## 🚀 Fastest Way to Get Started

### Prerequisites Check

```powershell
# Check Node.js (required for frontend)
node --version

# Check Python (required for backend)
python --version
```

**If Node.js is missing:** Install from https://nodejs.org/ (LTS version)

---

## Step-by-Step Launch

### Terminal 1: Backend Setup

```powershell
# Navigate to project
cd C:\Finance-Insight

# Initialize database (first time only)
python scripts/init_db.py

# Generate mock data (first time only)
python scripts/generate_mock_data.py

# Start FastAPI server
uvicorn app.main:app --reload
```

**Expected:** Server running on `http://127.0.0.1:8000`

---

### Terminal 2: Frontend Setup

```powershell
# Navigate to frontend
cd C:\Finance-Insight\frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

**OR use the PowerShell script:**
```powershell
cd C:\Finance-Insight\frontend
.\start.ps1
```

**Expected:** Server running on `http://localhost:3000`

---

### Open Browser

Navigate to: **http://localhost:3000**

You should see:
- Finance-Insight header
- Atlas Structure selector
- AG-Grid with hierarchy tree
- Natural values (Daily, MTD, YTD)

---

## 🔍 Troubleshooting

### Frontend Won't Start

**Issue:** "npm is not recognized"
- **Solution:** Install Node.js from https://nodejs.org/
- Restart terminal after installation

**Issue:** "Cannot find module"
- **Solution:** Run `npm install` in `frontend` directory

**Issue:** Port 3000 in use
- **Solution:** Change port in `frontend/vite.config.ts`:
  ```typescript
  server: { port: 3001 }
  ```

### Backend Won't Start

**Issue:** "PostgreSQL connection error"
- **Solution:** Start PostgreSQL service
- Check `DATABASE_URL` in `.env` or `app/database.py`

**Issue:** "Module not found"
- **Solution:** Run `pip install -r requirements.txt`

### API Not Responding

**Issue:** "Failed to load discovery data"
- **Solution:** 
  1. Verify backend is running: `http://localhost:8000/health`
  2. Check browser console (F12) for errors
  3. Verify structure_id: Use "MOCK_ATLAS_v1"

---

## ✅ Verification

### Backend Health Check
```powershell
# Test backend
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

### Frontend Check
- Open: `http://localhost:3000`
- Should see Finance-Insight interface
- No console errors (F12)

### API Test
```powershell
# Test discovery endpoint
curl "http://localhost:8000/api/v1/discovery?structure_id=MOCK_ATLAS_v1"
# Should return JSON with hierarchy
```

---

## 📝 Notes

- **Backend runs on:** `http://localhost:8000`
- **Frontend runs on:** `http://localhost:3000`
- **Frontend proxies API calls** to backend automatically
- **First time setup:** Run `init_db.py` and `generate_mock_data.py` before starting servers

---

## 🎯 Expected Result

When everything works:
1. Backend server running (port 8000)
2. Frontend server running (port 3000)
3. Browser shows Discovery screen
4. Select "MOCK_ATLAS_v1" structure
5. See hierarchy tree with natural values
6. Can expand/collapse nodes

**If you see this, Phase 1 is working!** ✅

