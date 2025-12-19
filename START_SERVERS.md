# How to Start Finance-Insight Servers

## ✅ Debug Status: ALL CHECKS PASSED

- ✅ Node.js v24.12.0 installed
- ✅ npm 11.6.2 available
- ✅ Frontend dependencies installed (96 packages)
- ✅ Backend files ready
- ✅ Frontend dev server starting...

---

## 🚀 Starting the Application

### Option 1: Automatic Start (Recommended)

I've started the frontend server in the background. Now you need to start the backend:

**Terminal 1: Start Backend**
```powershell
cd C:\Finance-Insight
uvicorn app.main:app --reload
```

**Frontend is already starting** - check if it's running on port 3000.

---

### Option 2: Manual Start (Two Terminals)

**Terminal 1: Backend Server**
```powershell
cd C:\Finance-Insight
uvicorn app.main:app --reload
```
**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Terminal 2: Frontend Server**
```powershell
cd C:\Finance-Insight\frontend
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
npm run dev
```
**Expected Output:**
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

---

## 🌐 Access the Application

1. **Frontend UI**: http://localhost:3000
2. **Backend API**: http://localhost:8000
3. **API Docs**: http://localhost:8000/docs
4. **Health Check**: http://localhost:8000/health

---

## ✅ Verification Steps

### 1. Check Backend
```powershell
# Test health endpoint
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

### 2. Check Frontend
- Open browser: http://localhost:3000
- Should see Finance-Insight Discovery screen
- Select "MOCK_ATLAS_v1" structure
- See hierarchy tree with natural values

### 3. Test API Connection
- Open browser console (F12)
- Check for any errors
- Verify API calls are working

---

## 🔧 Troubleshooting

### Frontend Not Starting
- **Check port 3000**: `netstat -ano | Select-String ":3000"`
- **Check if process is running**: Look for Vite process
- **Restart**: Stop and run `npm run dev` again

### Backend Not Starting
- **Check database**: Ensure PostgreSQL is running
- **Check dependencies**: `pip install -r requirements.txt`
- **Check port 8000**: `netstat -ano | Select-String ":8000"`

### API Connection Errors
- **Verify backend is running** on port 8000
- **Check CORS settings** in `app/main.py`
- **Check browser console** for detailed errors

---

## 📝 Notes

- **PATH Refresh**: If Node.js commands don't work, refresh PATH:
  ```powershell
  $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
  ```
- **New Terminal Windows**: Will automatically have Node.js in PATH
- **Background Process**: Frontend server is running in background
- **Stop Servers**: Press `Ctrl+C` in each terminal

---

## ✅ Next Steps

1. **Start backend** (if not already running)
2. **Verify frontend** is accessible at http://localhost:3000
3. **Test Discovery screen** with structure "MOCK_ATLAS_v1"
4. **Verify natural values** are displayed correctly

**You're all set!** 🎉

