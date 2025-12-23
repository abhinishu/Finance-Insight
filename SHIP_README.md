# Finance-Insight Zero-Touch Deployment Script

## Overview

`ship.ps1` is a comprehensive PowerShell deployment script that automates the entire setup and launch process for the Finance-Insight POC environment. It provides a "zero-touch" deployment experience with intelligent checks, error handling, and user prompts.

## Features

### ✅ Environment Guardrails
- **Python Version Check**: Verifies Python 3.12 (recommended), warns on other versions, allows override
- **Node.js & npm Check**: Verifies Node.js and npm are installed and accessible

### ✅ Automated Setup
- **Virtual Environment**: Automatically creates `.venv` if missing
- **Backend Dependencies**: Installs all Python packages from `requirements.txt`
- **Frontend Dependencies**: Installs all npm packages in `frontend/` directory

### ✅ Database & Seed Sync
- **Interactive Prompt**: Asks user if they want to update database schema
- **Alembic Migrations**: Runs `alembic upgrade head` to apply latest migrations
- **Seed Data**: Runs `scripts/seed_manager.py` to populate pilot data

### ✅ Smart Port Management
- **Port Detection**: Checks if ports 8000 (Backend) and 3000 (Frontend) are in use
- **Process Termination**: Offers to kill processes blocking ports with user confirmation
- **Safety**: Shows process name and PID before termination

### ✅ Service Launch
- **Backend Server**: Launches FastAPI backend in separate minimized window
- **Frontend Server**: Launches Vite dev server in separate minimized window
- **Health Checks**: Verifies both servers are running before proceeding
- **Browser Launch**: Automatically opens `http://localhost:3000` in default browser

### ✅ Final Status
- **Gemini API Status**: Reads `.env` file and displays API key status (masked for security)
- **Success Summary**: Shows all service URLs and access points

## Usage

### Basic Usage
```powershell
.\ship.ps1
```

### Advanced Options
```powershell
# Skip environment checks (use with caution)
.\ship.ps1 -SkipChecks

# Skip database update prompt
.\ship.ps1 -SkipDatabase

# Skip port availability checks
.\ship.ps1 -SkipPortCheck

# Combine options
.\ship.ps1 -SkipDatabase -SkipPortCheck
```

## Prerequisites

Before running `ship.ps1`, ensure you have:

1. **Python 3.12** (recommended) or Python 3.x installed
2. **Node.js** and **npm** installed
3. **PostgreSQL** database running (for database operations)
4. **PowerShell 5.1+** (comes with Windows 10/11)

## What the Script Does

1. **Checks Environment**
   - Verifies Python version (warns if not 3.12)
   - Verifies Node.js and npm are available

2. **Sets Up Dependencies**
   - Creates Python virtual environment (`.venv`)
   - Installs Python packages from `requirements.txt`
   - Installs npm packages in `frontend/` directory

3. **Database Operations** (if user confirms)
   - Runs Alembic migrations (`alembic upgrade head`)
   - Seeds database with pilot data (`scripts/seed_manager.py`)

4. **Port Management**
   - Checks ports 8000 and 3000
   - Offers to kill blocking processes if found

5. **Launches Services**
   - Starts backend server in minimized window
   - Starts frontend server in minimized window
   - Opens browser to frontend URL

6. **Displays Status**
   - Shows Gemini API key status from `.env`
   - Displays all service URLs

## Output

The script provides color-coded output:
- ✅ **Green**: Success messages
- ⚠️ **Yellow**: Warnings
- ❌ **Red**: Errors
- ℹ️ **Cyan**: Information

## Stopping Services

To stop the servers:
1. Find the minimized PowerShell windows running backend/frontend
2. Close those windows or press `Ctrl+C` in them
3. Alternatively, use Task Manager to end the processes

## Troubleshooting

### Python Version Issues
If you see Python version warnings:
- The script will ask if you want to continue
- Type `Y` to proceed or `N` to cancel
- For best results, install Python 3.12

### Port Already in Use
If a port is occupied:
- The script will show the PID and process name
- Type `Y` to kill the process, or `N` to cancel
- You can manually free the port and re-run the script

### Database Connection Errors
If database operations fail:
- Ensure PostgreSQL is running
- Check `DATABASE_URL` in `.env` file
- Verify database credentials are correct

### Missing Dependencies
If installation fails:
- Check internet connection
- Verify `requirements.txt` and `package.json` are valid
- Check for proxy/firewall issues

## Environment Variables

The script reads from `.env` file for:
- `GOOGLE_API_KEY` or `GEMINI_API_KEY`: Gemini API key for GenAI features
- `DATABASE_URL`: PostgreSQL connection string

## Security Notes

- API keys are masked in output (only first 4 and last 4 characters shown)
- Port termination requires user confirmation
- All operations are logged with clear messages

## Support

For issues or questions:
1. Check the script output for specific error messages
2. Verify all prerequisites are installed
3. Review the logs in the minimized PowerShell windows
4. Check `.env` file configuration

---

**Version**: 3.1.0  
**Last Updated**: December 2024  
**Compatible with**: Finance-Insight Phase 3.1+

