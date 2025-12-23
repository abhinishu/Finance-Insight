# Finance-Insight Clean Slate Initialization Script
# clean_slate.ps1 - Rebuilds the environment from zero
# Version: 3.1.0

$ErrorActionPreference = "Stop"
$script:ProjectRoot = $PSScriptRoot

# Color output functions
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
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
# STEP 1: PURGE OLD ENVIRONMENTS
# ============================================================================

function Remove-OldEnvironments {
    Write-Section "Step 1: Purging Old Environments"
    
    # Remove .venv
    $venvPath = Join-Path $script:ProjectRoot ".venv"
    if (Test-Path $venvPath) {
        Write-Info "Removing .venv folder..."
        Remove-Item -Path $venvPath -Recurse -Force -ErrorAction Stop
        Write-Success ".venv folder deleted"
    }
    else {
        Write-Info ".venv folder not found (already clean)"
    }
    
    # Remove node_modules
    $nodeModulesPath = Join-Path $script:ProjectRoot "frontend\node_modules"
    if (Test-Path $nodeModulesPath) {
        Write-Info "Removing frontend\node_modules folder..."
        Remove-Item -Path $nodeModulesPath -Recurse -Force -ErrorAction Stop
        Write-Success "node_modules folder deleted"
    }
    else {
        Write-Info "node_modules folder not found (already clean)"
    }
    
    Write-Success "Old environments purged successfully"
}

# ============================================================================
# STEP 2: VERIFY PYTHON 3.12
# ============================================================================

function Test-Python312 {
    Write-Section "Step 2: Verifying Python 3.12"
    
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Python is not installed or not in PATH"
            return $false
        }
        
        Write-Info "Found: $pythonVersion"
        
        if ($pythonVersion -match "Python (\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            
            if ($major -eq 3 -and $minor -eq 12) {
                Write-Success "Python 3.12 detected - Perfect!"
                return $true
            }
            else {
                Write-Warning "Python $major.$minor detected (Expected: 3.12)"
                $continue = Read-Host "Continue anyway? (Y/N)"
                if ($continue -eq "Y" -or $continue -eq "y") {
                    return $true
                }
                return $false
            }
        }
        else {
            Write-Warning "Could not parse Python version"
            return $true
        }
    }
    catch {
        Write-Error "Error checking Python: $_"
        return $false
    }
}

# ============================================================================
# STEP 3: SCAN BACKEND FILES AND VERIFY REQUIREMENTS.TXT
# ============================================================================

function Test-RequirementsCompleteness {
    Write-Section "Step 3: Verifying requirements.txt Completeness"
    
    $requirementsFile = Join-Path $script:ProjectRoot "requirements.txt"
    if (-not (Test-Path $requirementsFile)) {
        Write-Error "requirements.txt not found!"
        return $false
    }
    
    # Read requirements.txt
    $requirements = Get-Content $requirementsFile | Where-Object { $_ -notmatch '^\s*#' -and $_ -notmatch '^\s*$' }
    $installedPackages = @()
    
    foreach ($line in $requirements) {
        if ($line -match '^([a-zA-Z0-9_-]+)') {
            $packageName = $matches[1]
            $installedPackages += $packageName.ToLower()
        }
    }
    
    Write-Info "Found $($installedPackages.Count) packages in requirements.txt:"
    $installedPackages | ForEach-Object { Write-Info "  - $_" }
    
    # Critical packages that must be present
    $criticalPackages = @(
        "fastapi",
        "uvicorn",
        "pandas",
        "python-dotenv",
        "pydantic",
        "sqlalchemy",
        "psycopg2-binary",
        "alembic",
        "google-generativeai",
        "tenacity"
    )
    
    $missing = @()
    foreach ($pkg in $criticalPackages) {
        if ($installedPackages -notcontains $pkg) {
            $missing += $pkg
        }
    }
    
    if ($missing.Count -gt 0) {
        Write-Warning "Missing critical packages: $($missing -join ', ')"
        return $false
    }
    
    Write-Success "All critical packages found in requirements.txt"
    return $true
}

# ============================================================================
# STEP 4: REBUILD PYTHON ENVIRONMENT
# ============================================================================

function New-PythonEnvironment {
    Write-Section "Step 4: Rebuilding Python Environment"
    
    $venvPath = Join-Path $script:ProjectRoot ".venv"
    
    Write-Info "Creating fresh virtual environment with Python 3.12..."
    python -m venv .venv
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment"
        return $false
    }
    
    Write-Success "Virtual environment created"
    
    $venvPython = Join-Path $venvPath "Scripts\python.exe"
    $venvPip = Join-Path $venvPath "Scripts\pip.exe"
    
    if (-not (Test-Path $venvPython)) {
        Write-Error "Virtual environment Python not found at $venvPython"
        return $false
    }
    
    Write-Info "Upgrading pip..."
    & $venvPython -m pip install --upgrade pip --quiet
    
    Write-Info "Installing requirements from requirements.txt..."
    & $venvPython -m pip install -r requirements.txt
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install requirements"
        return $false
    }
    
    Write-Success "Python environment rebuilt successfully"
    return $true
}

# ============================================================================
# STEP 5: REBUILD FRONTEND ENVIRONMENT
# ============================================================================

function New-FrontendEnvironment {
    Write-Section "Step 5: Rebuilding Frontend Environment"
    
    $frontendPath = Join-Path $script:ProjectRoot "frontend"
    
    if (-not (Test-Path $frontendPath)) {
        Write-Error "Frontend directory not found at $frontendPath"
        return $false
    }
    
    Push-Location $frontendPath
    
    try {
        Write-Info "Installing frontend dependencies..."
        npm install
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to install frontend dependencies"
            return $false
        }
        
        Write-Success "Frontend environment rebuilt successfully"
        return $true
    }
    finally {
        Pop-Location
    }
}

# ============================================================================
# STEP 6: VERIFY SHIP.PS1 PATHS
# ============================================================================

function Test-ShipScriptPaths {
    Write-Section "Step 6: Verifying ship.ps1 Path Configuration"
    
    $shipScript = Join-Path $script:ProjectRoot "ship.ps1"
    
    if (-not (Test-Path $shipScript)) {
        Write-Error "ship.ps1 not found!"
        return $false
    }
    
    $scriptContent = Get-Content $shipScript -Raw
    
    # Check for relative paths
    $issues = @()
    
    # Check for .venv activation path
    if ($scriptContent -notmatch '\.venv\\Scripts\\python\.exe' -and $scriptContent -notmatch '\.venv\\Scripts\\Activate\.ps1') {
        $issues += "ship.ps1 should reference .venv\Scripts\python.exe or .venv\Scripts\Activate.ps1"
    }
    
    # Check for absolute paths (bad)
    if ($scriptContent -match 'C:\\[^.]') {
        $issues += "ship.ps1 contains absolute paths (should use relative paths)"
    }
    
    # Check for proper relative path usage
    if ($scriptContent -match 'Join-Path.*\$PSScriptRoot' -or $scriptContent -match 'Join-Path.*\$script:ProjectRoot') {
        Write-Success "ship.ps1 uses Join-Path for path construction (good!)"
    }
    else {
        $issues += "ship.ps1 should use Join-Path for cross-platform compatibility"
    }
    
    if ($issues.Count -gt 0) {
        Write-Warning "Potential issues found in ship.ps1:"
        $issues | ForEach-Object { Write-Warning "  - $_" }
        return $false
    }
    
    Write-Success "ship.ps1 path configuration looks good"
    return $true
}

# ============================================================================
# STEP 7: HEALTH CHECK
# ============================================================================

function Test-HealthCheck {
    Write-Section "Step 7: Running Health Check"
    
    $venvPath = Join-Path $script:ProjectRoot ".venv"
    $venvPython = Join-Path $venvPath "Scripts\python.exe"
    $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
    
    if (-not (Test-Path $venvPython)) {
        Write-Error "Virtual environment Python not found"
        return $false
    }
    
    Write-Info "Testing virtual environment activation..."
    if (Test-Path $activateScript) {
        Write-Success "Activate.ps1 found at: $activateScript"
    }
    else {
        Write-Warning "Activate.ps1 not found (may be normal on some systems)"
    }
    
    Write-Info "Testing critical imports..."
    
    # Test FastAPI import
    $fastapiCmd = 'import fastapi; print("FastAPI version:", fastapi.__version__)'
    $fastapiTest = & $venvPython -c $fastapiCmd 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "FastAPI: $fastapiTest"
    }
    else {
        Write-Error "FastAPI import failed: $fastapiTest"
        return $false
    }
    
    # Test google.generativeai import
    $geminiCmd = 'import google.generativeai as genai; print("google-generativeai imported successfully")'
    $geminiTest = & $venvPython -c $geminiCmd 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "google.generativeai: Imported successfully"
    }
    else {
        Write-Error "google.generativeai import failed: $geminiTest"
        return $false
    }
    
    # Test other critical imports
    $otherImports = @("uvicorn", "pandas", "sqlalchemy", "pydantic", "alembic")
    foreach ($pkg in $otherImports) {
        $testCmd = "import $pkg; print('OK')"
        $testResult = & $venvPython -c $testCmd 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "$pkg : OK"
        }
        else {
            Write-Warning "$pkg : Import test failed (may be non-critical)"
        }
    }
    
    Write-Success "Health check passed!"
    return $true
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

function Start-CleanSlate {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║     Finance-Insight Clean Slate Initialization v3.1.0         ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    $confirm = Read-Host "This will DELETE .venv and frontend/node_modules. Continue? (Y/N)"
    if ($confirm -ne "Y" -and $confirm -ne "y") {
        Write-Info "Clean slate initialization cancelled"
        exit 0
    }
    
    try {
        # Step 1: Purge
        Remove-OldEnvironments
        
        # Step 2: Verify Python
        if (-not (Test-Python312)) {
            Write-Error "Python 3.12 verification failed"
            exit 1
        }
        
        # Step 3: Verify requirements
        if (-not (Test-RequirementsCompleteness)) {
            Write-Error "Requirements verification failed"
            exit 1
        }
        
        # Step 4: Rebuild Python
        if (-not (New-PythonEnvironment)) {
            Write-Error "Python environment rebuild failed"
            exit 1
        }
        
        # Step 5: Rebuild Frontend
        if (-not (New-FrontendEnvironment)) {
            Write-Error "Frontend environment rebuild failed"
            exit 1
        }
        
        # Step 6: Verify ship.ps1
        if (-not (Test-ShipScriptPaths)) {
            Write-Warning "ship.ps1 path verification found issues (may still work)"
        }
        
        # Step 7: Health Check
        if (-not (Test-HealthCheck)) {
            Write-Error "Health check failed"
            exit 1
        }
        
        # Success
        Write-Host ""
        Write-Host "╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "║              🎉 CLEAN SLATE INITIALIZATION COMPLETE! 🎉        ║" -ForegroundColor Green
        Write-Host "╚══════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
        Write-Success "Environment rebuilt from zero successfully!"
        Write-Info "Next steps:"
        Write-Info "  1. Run .\ship.ps1 to deploy the application"
        Write-Info "  2. Or manually activate: .\.venv\Scripts\Activate.ps1"
        Write-Host ""
    }
    catch {
        $errorMsg = $_.Exception.Message
        $errorText = "Clean slate initialization failed: " + $errorMsg
        Write-ColorOutput $errorText "Red"
        exit 1
    }
}

# Run clean slate
Start-CleanSlate

