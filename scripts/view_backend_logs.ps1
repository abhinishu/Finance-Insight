# Script to view backend logs
# This will stop any existing backend and start a new one in this terminal

Write-Host "================================================================================`nVIEWING BACKEND LOGS`n================================================================================`n" -ForegroundColor Green

# Step 1: Stop any existing backend processes
Write-Host "Step 1: Stopping any existing backend processes..." -ForegroundColor Yellow
Get-Process | Where-Object { $_.ProcessName -like "*python*" -or $_.CommandLine -like "*uvicorn*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-Host "[OK] Existing processes stopped`n" -ForegroundColor Green

# Step 2: Navigate to project directory
Write-Host "Step 2: Navigating to project directory..." -ForegroundColor Yellow
$projectPath = "C:\Program1\Finance-Insight"
if (Test-Path $projectPath) {
    Set-Location $projectPath
    Write-Host "[OK] In project directory: $projectPath`n" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Project directory not found: $projectPath" -ForegroundColor Red
    exit 1
}

# Step 3: Activate virtual environment
Write-Host "Step 3: Activating virtual environment..." -ForegroundColor Yellow
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    .\.venv\Scripts\Activate.ps1
    Write-Host "[OK] Virtual environment activated`n" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Virtual environment not found. Please create it first." -ForegroundColor Red
    exit 1
}

# Step 4: Start backend with visible output
Write-Host "================================================================================`nSTARTING BACKEND SERVER`n================================================================================`n" -ForegroundColor Cyan
Write-Host "The backend will start now. You'll see:" -ForegroundColor Yellow
Write-Host "  - Server startup messages" -ForegroundColor White
Write-Host "  - [EXECUTION PLAN] debug messages when you test the endpoint" -ForegroundColor White
Write-Host "  - Any errors with full tracebacks`n" -ForegroundColor White
Write-Host "Press Ctrl+C to stop the server`n" -ForegroundColor Yellow
Write-Host "================================================================================`n" -ForegroundColor Cyan

# Start uvicorn (this will block and show all output)
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000



