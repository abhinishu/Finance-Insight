# Finance-Insight Zero-Touch Deployment Script
# ship.ps1 - Master deployment script for POC setup
# Version: 3.1.0

param(
    [switch]$SkipChecks,
    [switch]$SkipDatabase,
    [switch]$SkipPortCheck
)

$ErrorActionPreference = "Continue"
$script:ProjectRoot = $PSScriptRoot
$script:BackendPort = 8000
$script:FrontendPort = 3000
$script:BackendProcess = $null
$script:FrontendProcess = $null

# Color output functions
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Section {
    param([string]$Title)
    Write-Host ""
    $separator = "=" * 70
    Write-Host $separator -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host $separator -ForegroundColor Cyan
    Write-Host ""
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "✅ $Message" "Green"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "⚠️  $Message" "Yellow"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "❌ $Message" "Red"
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "ℹ️  $Message" "Cyan"
}

# ============================================================================
# ENVIRONMENT GUARDRAILS
# ============================================================================

function Test-PythonVersion {
    Write-Section "Environment Guardrails: Python Version Check"
    
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Python is not installed or not in PATH"
            Write-Info "Please install Python 3.12 from https://www.python.org/downloads/"
            return $false
        }
        
        Write-Info "Found: $pythonVersion"
        
        # Extract version number
        if ($pythonVersion -match "Python (\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            
            if ($major -eq 3 -and $minor -eq 12) {
                Write-Success "Python 3.12 detected - Recommended version"
                return $true
            }
            elseif ($major -eq 3 -and $minor -lt 12) {
                Write-Warning "Python $major.$minor detected (Recommended: 3.12)"
            }
            elseif ($major -eq 3 -and $minor -ge 13) {
                Write-Warning "Python $major.$minor detected (Known issues with 3.14+, Recommended: 3.12)"
            }
            else {
                Write-Warning "Python $major.$minor detected (Recommended: 3.12)"
            }
            
            if (-not $SkipChecks) {
                $continue = Read-Host "Continue with this Python version? (Y/N)"
                if ($continue -ne "Y" -and $continue -ne "y") {
                    Write-Info "Deployment cancelled by user"
                    return $false
                }
            }
            return $true
        }
        else {
            Write-Warning "Could not parse Python version, but Python is available"
            return $true
        }
    }
    catch {
        Write-Error "Error checking Python version: $_"
        return $false
    }
}

function Test-NodeJS {
    Write-Section "Environment Guardrails: Node.js and npm Check"
    
    try {
        $nodeVersion = node --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Node.js is not installed or not in PATH"
            Write-Info "Please install Node.js from https://nodejs.org/"
            return $false
        }
        
        Write-Success "Node.js: $nodeVersion"
        
        $npmVersion = npm --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "npm is not installed or not in PATH"
            return $false
        }
        
        Write-Success "npm: $npmVersion"
        return $true
    }
    catch {
        Write-Error "Error checking Node.js/npm: $_"
        return $false
    }
}

# ============================================================================
# AUTOMATED SETUP
# ============================================================================

function Install-BackendDependencies {
    Write-Section "Backend Setup: Python Virtual Environment"
    
    $venvPath = Join-Path $script:ProjectRoot ".venv"
    $venvPython = Join-Path $venvPath "Scripts\python.exe"
    
    if (-not (Test-Path $venvPath)) {
        Write-Info "Creating Python virtual environment..."
        python -m venv .venv
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to create virtual environment"
            return $false
        }
        Write-Success "Virtual environment created"
    }
    else {
        Write-Info "Virtual environment already exists"
    }
    
    if (-not (Test-Path $venvPython)) {
        Write-Error "Virtual environment Python not found at $venvPython"
        return $false
    }
    
    Write-Info "Installing Python dependencies..."
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r requirements.txt
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install Python dependencies"
        return $false
    }
    
    Write-Success "Backend dependencies installed"
    return $true
}

function Install-FrontendDependencies {
    Write-Section "Frontend Setup: Node.js Dependencies"
    
    $frontendPath = Join-Path $script:ProjectRoot "frontend"
    $nodeModulesPath = Join-Path $frontendPath "node_modules"
    
    if (-not (Test-Path $frontendPath)) {
        Write-Error "Frontend directory not found at $frontendPath"
        return $false
    }
    
    Push-Location $frontendPath
    
    try {
        if (-not (Test-Path $nodeModulesPath)) {
            Write-Info "Installing frontend dependencies..."
            npm install
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Failed to install frontend dependencies"
                return $false
            }
            Write-Success "Frontend dependencies installed"
        }
        else {
            Write-Info "Frontend dependencies already installed"
        }
        return $true
    }
    finally {
        Pop-Location
    }
}

# ============================================================================
# DATABASE & SEED SYNC
# ============================================================================

function Update-Database {
    Write-Section "Database Schema and Seed Sync"
    
    if ($SkipDatabase) {
        Write-Info "Skipping database update (SkipDatabase flag set)"
        return $true
    }
    
    $update = Read-Host "Update Database Schema and Seeds? (Y/N)"
    if ($update -ne "Y" -and $update -ne "y") {
        Write-Info "Skipping database update"
        return $true
    }
    
    $venvPython = Join-Path $script:ProjectRoot ".venv\Scripts\python.exe"
    
    if (-not (Test-Path $venvPython)) {
        Write-Error "Virtual environment not found. Run setup first."
        return $false
    }
    
    Write-Info "Running database migrations..."
    & $venvPython -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Database migration failed"
        return $false
    }
    Write-Success "Database migrations completed"
    
    Write-Info "Seeding database with pilot data..."
    & $venvPython scripts\seed_manager.py
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Seed manager encountered issues (may be non-fatal)"
    }
    else {
        Write-Success "Database seeding completed"
    }
    
    return $true
}

# ============================================================================
# SMART PORT MANAGEMENT
# ============================================================================

function Get-PortProcess {
    param([int]$Port)
    
    try {
        # Try modern PowerShell method first
        $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        if ($listener) {
            return $listener.OwningProcess
        }
    }
    catch {
        # Fallback to netstat method
        try {
            $netstatOutput = netstat -ano | Select-String ":$Port\s+.*LISTENING"
            if ($netstatOutput) {
                $parts = ($netstatOutput[0] -split '\s+')
                $pid = $parts[-1]
                return [int]$pid
            }
        }
        catch { }
    }
    return $null
}

function Test-PortAvailability {
    param([int]$Port, [string]$ServiceName)
    
    if ($SkipPortCheck) {
        return $true
    }
    
    $pid = Get-PortProcess -Port $Port
    if ($pid) {
        try {
            $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
            $processName = if ($process) { $process.ProcessName } else { "Unknown" }
            
            Write-Warning "Port $Port is occupied by PID $pid ($processName)"
            $kill = Read-Host "Kill this process? (Y/N)"
            
            if ($kill -eq "Y" -or $kill -eq "y") {
                try {
                    Stop-Process -Id $pid -Force -ErrorAction Stop
                    Write-Success "Process $pid terminated"
                    Start-Sleep -Seconds 2
                    return $true
                }
                catch {
                    Write-Error "Failed to kill process $pid : $_"
                    return $false
                }
            }
            else {
                Write-Error "Port $Port is still occupied. Please free it manually."
                return $false
            }
        }
        catch {
            Write-Warning "Could not get process info for PID $pid"
            return $false
        }
    }
    return $true
}

# ============================================================================
# LAUNCH SERVICES
# ============================================================================

function Start-Backend {
    Write-Section "Launching Backend Server"
    
    $venvPython = Join-Path $script:ProjectRoot ".venv\Scripts\python.exe"
    $uvicorn = Join-Path $script:ProjectRoot ".venv\Scripts\uvicorn.exe"
    
    if (-not (Test-Path $venvPython)) {
        Write-Error "Virtual environment not found"
        return $false
    }
    
    Write-Info "Starting backend on http://127.0.0.1:$script:BackendPort"
    
    # Build the command to run
    $backendScript = @"
cd '$script:ProjectRoot'
if (Test-Path '$uvicorn') {
    & '$uvicorn' app.main:app --reload --host 127.0.0.1 --port $script:BackendPort
} else {
    & '$venvPython' -m uvicorn app.main:app --reload --host 127.0.0.1 --port $script:BackendPort
}
"@
    
    # Start backend in a new minimized PowerShell window
    $script:BackendProcess = Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        $backendScript
    ) -WindowStyle Minimized -PassThru
    
    Start-Sleep -Seconds 3
    
    # Verify backend is running
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$script:BackendPort/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Success "Backend server is running"
            return $true
        }
    }
    catch {
        Write-Warning "Backend may still be starting. Check the backend window for status."
    }
    
    return $true
}

function Start-Frontend {
    Write-Section "Launching Frontend Server"
    
    $frontendPath = Join-Path $script:ProjectRoot "frontend"
    
    if (-not (Test-Path $frontendPath)) {
        Write-Error "Frontend directory not found"
        return $false
    }
    
    Write-Info "Starting frontend on http://localhost:$script:FrontendPort"
    
    # Start frontend in a new minimized PowerShell window
    $script:FrontendProcess = Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "cd '$frontendPath'; npm run dev"
    ) -WindowStyle Minimized -PassThru
    
    Start-Sleep -Seconds 5
    
    # Verify frontend is running
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$script:FrontendPort" -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Success "Frontend server is running"
            return $true
        }
    }
    catch {
        Write-Warning "Frontend may still be starting. Check the frontend window for status."
    }
    
    return $true
}

function Open-Browser {
    Write-Info "Opening browser to http://localhost:$script:FrontendPort"
    Start-Process "http://localhost:$script:FrontendPort"
}

# ============================================================================
# FINAL TOUCH: GEMINI API STATUS
# ============================================================================

function Get-GeminiAPIStatus {
    Write-Section "Gemini API Configuration Status"
    
    $envFile = Join-Path $script:ProjectRoot ".env"
    
    if (Test-Path $envFile) {
        $envContent = Get-Content $envFile -Raw
        $apiKey = $null
        
        # Check for GOOGLE_API_KEY
        if ($envContent -match "GOOGLE_API_KEY\s*=\s*(.+)") {
            $apiKey = $matches[1].Trim()
        }
        # Check for GEMINI_API_KEY (backward compatibility)
        elseif ($envContent -match "GEMINI_API_KEY\s*=\s*(.+)") {
            $apiKey = $matches[1].Trim()
        }
        
        if ($apiKey) {
            # Mask the API key for display
            if ($apiKey.Length -gt 8) {
                $maskedKey = $apiKey.Substring(0, 4) + "..." + $apiKey.Substring($apiKey.Length - 4)
            }
            else {
                $maskedKey = "***"
            }
            
            Write-Success "Gemini API Key: Found ($maskedKey)"
            Write-Info "API key is configured and ready for GenAI rule translation"
        }
        else {
            Write-Warning "Gemini API Key: Not found in .env file"
            Write-Info "GenAI features will be disabled. Add GOOGLE_API_KEY to .env to enable."
        }
    }
    else {
        Write-Warning ".env file not found"
        Write-Info "Create a .env file with GOOGLE_API_KEY=your_key_here to enable GenAI features"
    }
}

# ============================================================================
# MAIN DEPLOYMENT FLOW
# ============================================================================

function Start-Deployment {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║     Finance-Insight Zero-Touch Deployment Script v3.1.0        ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    # Step 1: Environment Guardrails
    if (-not (Test-PythonVersion)) {
        Write-Error "Python version check failed"
        exit 1
    }
    
    if (-not (Test-NodeJS)) {
        Write-Error "Node.js check failed"
        exit 1
    }
    
    # Step 2: Automated Setup
    if (-not (Install-BackendDependencies)) {
        Write-Error "Backend setup failed"
        exit 1
    }
    
    if (-not (Install-FrontendDependencies)) {
        Write-Error "Frontend setup failed"
        exit 1
    }
    
    # Step 3: Database & Seed Sync
    if (-not (Update-Database)) {
        Write-Error "Database update failed"
        exit 1
    }
    
    # Step 4: Smart Port Management
    if (-not (Test-PortAvailability -Port $script:BackendPort -ServiceName "Backend")) {
        Write-Error "Backend port check failed"
        exit 1
    }
    
    if (-not (Test-PortAvailability -Port $script:FrontendPort -ServiceName "Frontend")) {
        Write-Error "Frontend port check failed"
        exit 1
    }
    
    # Step 5: Launch Services
    if (-not (Start-Backend)) {
        Write-Error "Backend launch failed"
        exit 1
    }
    
    if (-not (Start-Frontend)) {
        Write-Error "Frontend launch failed"
        exit 1
    }
    
    # Step 6: Open Browser
    Start-Sleep -Seconds 2
    Open-Browser
    
    # Step 7: Final Touch - Gemini API Status
    Get-GeminiAPIStatus
    
    # Success Summary
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║                    🎉 DEPLOYMENT SUCCESSFUL! 🎉                 ║" -ForegroundColor Green
    Write-Host "╚══════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Success "Finance-Insight is now running!"
    Write-Info "Backend API: http://localhost:$script:BackendPort"
    Write-Info "Frontend UI: http://localhost:$script:FrontendPort"
    Write-Info "API Docs: http://localhost:$script:BackendPort/docs"
    Write-Host ""
    Write-Info "Backend and Frontend are running in separate minimized windows."
    Write-Info "Close those windows or press Ctrl+C in them to stop the servers."
    Write-Host ""
}

# Run deployment
try {
    Start-Deployment
}
catch {
    Write-Error "Deployment failed with error: $_"
    exit 1
}

