@echo off
echo ========================================
echo FINANCE INSIGHT - OFFICE DEPLOYMENT
echo ========================================
echo.

echo [1/5] Pulling latest code from main branch...
git pull origin main
if %errorlevel% neq 0 (
    echo ERROR: Failed to pull from git repository
    pause
    exit /b %errorlevel%
)
echo.

echo [2/5] Checking for existing database...
if exist finance_insight.db (
    del finance_insight.db
    echo Old database deleted. Starting fresh.
) else (
    echo No existing database found.
)
echo.

echo [3/5] Checking for virtual environment...
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b %errorlevel%
    )
) else (
    echo Virtual environment already exists.
)
echo.

echo [4/5] Activating virtual environment and installing dependencies...
call .venv\Scripts\activate
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b %errorlevel%
)

pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install requirements
    pause
    exit /b %errorlevel%
)
echo.

echo [5/5] Starting backend server...
echo ========================================
uvicorn app.main:app --reload
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Backend server failed to start
)

echo.
pause

