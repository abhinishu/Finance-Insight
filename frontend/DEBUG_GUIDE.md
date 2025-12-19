# Frontend Debugging Guide

## Issue: Cannot Launch Frontend

### Step 1: Check Node.js Installation

```powershell
node --version
npm --version
```

**If not installed:**
- Download Node.js from https://nodejs.org/
- Install LTS version (recommended)
- Restart terminal after installation

### Step 2: Install Dependencies

```powershell
cd C:\Finance-Insight\frontend
npm install
```

**Expected output:**
- Packages downloading
- `node_modules` folder created
- `package-lock.json` created

**If errors occur:**
- Check internet connection
- Try: `npm install --verbose` for detailed output
- Try: `npm cache clean --force` then `npm install`

### Step 3: Start Development Server

```powershell
npm run dev
```

**Expected output:**
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

### Step 4: Verify Backend is Running

In a **separate terminal**, start the backend:

```powershell
cd C:\Finance-Insight
uvicorn app.main:app --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 5: Open Browser

- Navigate to: `http://localhost:3000`
- You should see the Finance-Insight Discovery screen

## Common Errors & Solutions

### Error: "npm is not recognized"
**Solution:** Node.js not installed or not in PATH
- Install Node.js from https://nodejs.org/
- Restart terminal
- Verify: `npm --version`

### Error: "Port 3000 already in use"
**Solution:** Another process is using port 3000
- Change port in `vite.config.ts`:
  ```typescript
  server: {
    port: 3001,  // Use different port
  }
  ```
- Or kill the process using port 3000

### Error: "Cannot find module 'react'"
**Solution:** Dependencies not installed
- Run: `npm install`
- Delete `node_modules` and `package-lock.json`, then `npm install`

### Error: "Failed to load discovery data"
**Solution:** Backend not running or wrong URL
- Verify backend is running on port 8000
- Check browser console for detailed error
- Verify API endpoint: `http://localhost:8000/api/v1/discovery?structure_id=MOCK_ATLAS_v1`

### Error: "ECONNREFUSED"
**Solution:** Backend server not running
- Start backend: `uvicorn app.main:app --reload`
- Verify it's running on port 8000

## Quick Test Commands

```powershell
# Check Node.js
node --version

# Check npm
npm --version

# Install dependencies
cd C:\Finance-Insight\frontend
npm install

# Start dev server
npm run dev

# In another terminal - Start backend
cd C:\Finance-Insight
uvicorn app.main:app --reload
```

## Verification Checklist

- [ ] Node.js installed (`node --version` works)
- [ ] npm installed (`npm --version` works)
- [ ] Dependencies installed (`node_modules` folder exists)
- [ ] Frontend server running (`npm run dev` shows Vite server)
- [ ] Backend server running (`uvicorn` shows server on port 8000)
- [ ] Browser opens `http://localhost:3000`
- [ ] No console errors in browser
- [ ] Discovery screen loads

## Still Having Issues?

1. **Check browser console** (F12) for JavaScript errors
2. **Check terminal output** for build errors
3. **Verify file structure** - all files in `frontend/src/` exist
4. **Check TypeScript errors** - run `npm run build` to see compilation errors

