@echo off
echo [IMPORTER] Overwriting Local Database with Golden State...
if not exist "golden_state.sql" (
    echo ERROR: golden_state.sql not found!
    echo Please ensure golden_state.sql exists in the current directory.
    pause
    exit /b 1
)
set /p PGPASSWORD=Enter DB Password:
:: Reads 'golden_state.sql' and recreates the DB
psql -h localhost -U postgres -d finance_insight -f "golden_state.sql"
if %errorlevel% neq 0 (
    echo ERROR: Failed to import database
    pause
    exit /b %errorlevel%
)
echo [SUCCESS] Database is now identical to Laptop.
pause

