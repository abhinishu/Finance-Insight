@echo off
echo === FINANCE INSIGHT: DIGITAL TWIN LAUNCHER ===
echo.

echo [1/4] Pulling latest code from main branch...
git pull origin main
if %errorlevel% neq 0 (
    echo ERROR: Failed to pull from git repository
    pause
    exit /b %errorlevel%
)
echo.

echo [2/4] Checking for virtual environment...
if not exist ".venv" (
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

echo [3/4] Activating virtual environment and installing dependencies...
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

echo [4/4] Configuration check...
:: CONFIGURATION CHECK
if not exist ".env" (
    echo [SETUP] No configuration found. Let's connect to Office Postgres.
    set /p DB_USER=Enter Office Postgres Username (e.g. postgres): 
    set /p DB_PASS=Enter Office Postgres Password: 
    echo DATABASE_URL=postgresql://%DB_USER%:%DB_PASS%@localhost:5432/finance_insight > .env
    echo [SETUP] Configuration saved to .env
) else (
    echo [SETUP] Using existing .env configuration.
)
echo.

echo [LAUNCH] Starting System...
echo ========================================
uvicorn app.main:app --reload
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Backend server failed to start
)

echo.
pause
