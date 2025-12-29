@echo off
echo [IMPORTER] RESTORING DATABASE FROM 'golden_state.sql'...
echo ---------------------------------------------------------
echo WARNING: This will OVERWRITE the local database 'finance_insight'.
echo.

:: 1. Setup Connection Details
set /p DB_HOST="Enter Office DB Host (default 127.0.0.1): "
if "%DB_HOST%"=="" set DB_HOST=127.0.0.1

set /p DB_USER="Enter Office DB User (default postgres): "
if "%DB_USER%"=="" set DB_USER=postgres

set /p PGPASSWORD="Enter Office DB Password: "

:: 2. Check if SQL file exists
if not exist "golden_state.sql" (
    echo ERROR: 'golden_state.sql' not found!
    pause
    exit /b 1
)

:: 3. Run the Import
:: NOTE: You may need to edit the path to psql.exe below if the Office PC has a different version (e.g., 14, 15, 16)
echo.
echo Attempting restore...
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -h %DB_HOST% -U %DB_USER% -d finance_insight -f golden_state.sql

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Restore failed.
    echo Common fixes:
    echo 1. Check if the password is correct.
    echo 2. Check if PostgreSQL path in this script matches the Office PC version.
    pause
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] Database restored successfully!
pause
