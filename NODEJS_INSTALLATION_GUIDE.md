# Node.js Installation Guide for Finance-Insight

## ❌ Current Status

**Node.js is NOT installed** - This is required for the frontend.

## ✅ Solution: Install Node.js

### Step 1: Download Node.js

1. Go to: **https://nodejs.org/**
2. Download the **LTS version** (Long Term Support) - recommended
3. Choose the Windows Installer (.msi) for your system:
   - **64-bit**: `node-v20.x.x-x64.msi` (most common)
   - **32-bit**: `node-v20.x.x-x86.msi` (if you have 32-bit Windows)

### Step 2: Install Node.js

1. Run the downloaded `.msi` installer
2. Follow the installation wizard:
   - ✅ Accept the license agreement
   - ✅ Keep default installation path
   - ✅ **IMPORTANT**: Check "Add to PATH" option (should be checked by default)
   - ✅ Click "Install"
3. Wait for installation to complete
4. Click "Finish"

### Step 3: Verify Installation

**IMPORTANT**: Close and reopen your terminal/PowerShell after installation!

Then run:
```powershell
node --version
npm --version
```

**Expected output:**
```
v20.x.x
10.x.x
```

If you see version numbers, Node.js is installed correctly! ✅

### Step 4: Install Frontend Dependencies

Once Node.js is installed:

```powershell
cd C:\Finance-Insight\frontend
npm install
```

This will take 1-2 minutes to download all packages.

### Step 5: Start Frontend Server

```powershell
npm run dev
```

---

## 🔄 Alternative: Use Backend-Only Testing

If you want to test Phase 1 **without installing Node.js**, you can:

1. **Test Backend API directly:**
   ```powershell
   # Start backend
   uvicorn app.main:app --reload
   
   # Test in browser
   http://localhost:8000/api/v1/discovery?structure_id=MOCK_ATLAS_v1
   ```

2. **Use API testing tools:**
   - Postman
   - curl
   - Browser (direct API calls)

The React UI is optional for Phase 1 - the backend API works independently.

---

## 📝 Next Steps

**Option A: Install Node.js (Recommended)**
- Follow steps above
- Get full UI experience
- Better for Phase 2/3 development

**Option B: Test Backend Only**
- Skip frontend for now
- Test API endpoints directly
- Proceed to Phase 2 backend work

---

## ⚠️ Important Notes

- **Restart terminal** after installing Node.js
- **PATH update** may require terminal restart
- **npm comes with Node.js** - no separate installation needed
- **LTS version** is recommended (more stable)

---

**Which option would you like to proceed with?**

