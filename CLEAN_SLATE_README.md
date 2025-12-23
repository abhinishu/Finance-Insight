# Finance-Insight Clean Slate Initialization

## Overview

`clean_slate.ps1` is a comprehensive PowerShell script that performs a complete "clean slate" rebuild of the Finance-Insight environment. It purges old environments, verifies dependencies, and rebuilds everything from zero to prove the project can be deployed on any Windows machine.

## What It Does

### Step 1: Purge Old Environments
- Deletes `.venv` folder in the root directory
- Deletes `frontend\node_modules` folder
- Ensures a completely clean starting point

### Step 2: Verify Python 3.12
- Checks if Python 3.12 is installed (recommended)
- Warns if a different version is found but allows continuation
- Ensures Python is available before proceeding

### Step 3: Verify requirements.txt Completeness
- Scans `requirements.txt` for all critical packages
- Verifies all required dependencies are listed:
  - fastapi
  - uvicorn
  - pandas
  - python-dotenv
  - pydantic
  - sqlalchemy
  - psycopg2-binary
  - alembic
  - google-generativeai
  - tenacity

### Step 4: Rebuild Python Environment
- Creates a fresh `.venv` virtual environment
- Upgrades pip to latest version
- Installs all packages from `requirements.txt`

### Step 5: Rebuild Frontend Environment
- Navigates to `frontend/` directory
- Runs `npm install` to install all Node.js dependencies

### Step 6: Verify ship.ps1 Paths
- Checks that `ship.ps1` uses relative paths (not absolute)
- Verifies `Join-Path` is used for cross-platform compatibility
- Ensures `.venv\Scripts\python.exe` paths are correct

### Step 7: Health Check
- Tests virtual environment activation
- Verifies critical imports:
  - `fastapi` (with version check)
  - `google.generativeai` (Gemini API)
  - `uvicorn`, `pandas`, `sqlalchemy`, `pydantic`, `alembic`

## Usage

### Basic Usage
```powershell
.\clean_slate.ps1
```

The script will:
1. Ask for confirmation before deleting environments
2. Guide you through each step with color-coded output
3. Stop and report errors if any step fails
4. Provide a success summary at the end

### Prerequisites

Before running, ensure:
- **Python 3.12** (recommended) or Python 3.x is installed
- **Node.js** and **npm** are installed
- **PowerShell 5.1+** (comes with Windows 10/11)
- You have write permissions to the project directory

## Output

The script provides color-coded output:
- ✅ **Green**: Success messages
- ⚠️ **Yellow**: Warnings
- ❌ **Red**: Errors
- ℹ️ **Cyan**: Information

## Verification

After running `clean_slate.ps1`, you can verify the setup:

### Manual Verification
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Test imports
python -c "import fastapi; print('FastAPI OK')"
python -c "import google.generativeai; print('Gemini OK')"
```

### Next Steps

After successful clean slate initialization:
1. Run `.\ship.ps1` to deploy the application
2. Or manually start servers:
   ```powershell
   # Backend
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
   
   # Frontend (in another terminal)
   cd frontend
   npm run dev
   ```

## Troubleshooting

### Python Version Warning
If you see a Python version warning:
- The script will ask if you want to continue
- Type `Y` to proceed (works with Python 3.8+)
- For best results, install Python 3.12

### Import Failures
If health check fails on imports:
- Check that `requirements.txt` is complete
- Verify internet connection for pip install
- Check for proxy/firewall issues

### Path Issues
If ship.ps1 path verification fails:
- Ensure all paths use `Join-Path` or relative paths
- Avoid absolute paths like `C:\Program1\...`
- Use `$PSScriptRoot` or `$script:ProjectRoot` for base paths

## Success Criteria

A successful clean slate initialization should:
1. ✅ Delete old environments without errors
2. ✅ Create fresh `.venv` with Python 3.12 (or available version)
3. ✅ Install all requirements successfully
4. ✅ Install all frontend dependencies
5. ✅ Pass all health checks (FastAPI, Gemini API imports)
6. ✅ Verify ship.ps1 uses relative paths

## Purpose

This script proves that:
- The project can be rebuilt from zero
- All dependencies are properly documented
- The deployment process is portable
- The project is ready for office POC environment

---

**Version**: 3.1.0  
**Last Updated**: December 2024  
**Compatible with**: Finance-Insight Phase 3.1+

