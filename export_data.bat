@echo off
echo [EXPORTER] Saving Database Snapshot (Compatibility Mode)...

:: Auto-Pilot Password
set PGPASSWORD=postgres

:: ADDED FLAGS: --no-owner --no-acl (Ensures it works on Office PC even if users are different)
"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -h 127.0.0.1 -U postgres -d finance_insight --clean --if-exists --no-owner --no-acl --file="golden_state.sql"

if %errorlevel% neq 0 (
    echo ERROR: Failed to export database.
    pause
    exit /b %errorlevel%
)

echo [SUCCESS] Saved clean snapshot to 'golden_state.sql'.
pause