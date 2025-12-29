@echo off
echo [EXPORTER] Saving Database Snapshot...
set /p PGPASSWORD=Enter DB Password:
:: Dumps structure AND data to 'golden_state.sql'
pg_dump -h localhost -U postgres -d finance_insight --clean --if-exists --file="golden_state.sql"
if %errorlevel% neq 0 (
    echo ERROR: Failed to export database
    pause
    exit /b %errorlevel%
)
echo [SUCCESS] Saved to 'golden_state.sql'. Commit this file to Git to transfer it.
pause

