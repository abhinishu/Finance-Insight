# Git Configuration Script for Finance-Insight
# Run this script to configure git before pushing to GitHub

Write-Host "Git Configuration Setup" -ForegroundColor Green
Write-Host "=======================" -ForegroundColor Green
Write-Host ""

# Check if git is configured
$currentName = git config --global user.name 2>$null
$currentEmail = git config --global user.email 2>$null

if ($currentName -and $currentEmail) {
    Write-Host "Current Git Configuration:" -ForegroundColor Yellow
    Write-Host "  Name:  $currentName" -ForegroundColor Cyan
    Write-Host "  Email: $currentEmail" -ForegroundColor Cyan
    Write-Host ""
    $useCurrent = Read-Host "Use current configuration? (Y/N)"
    
    if ($useCurrent -eq "Y" -or $useCurrent -eq "y") {
        Write-Host "Using existing configuration." -ForegroundColor Green
        exit 0
    }
}

# Get user input
Write-Host "Please provide your Git configuration:" -ForegroundColor Yellow
Write-Host ""

$userName = Read-Host "Enter your name (or GitHub username)"
$userEmail = Read-Host "Enter your email (preferably GitHub email)"

# Validate input
if ([string]::IsNullOrWhiteSpace($userName) -or [string]::IsNullOrWhiteSpace($userEmail)) {
    Write-Host "Error: Name and email are required!" -ForegroundColor Red
    exit 1
}

# Configure git
Write-Host ""
Write-Host "Configuring Git..." -ForegroundColor Yellow
git config --global user.name "$userName"
git config --global user.email "$userEmail"

# Verify
Write-Host ""
Write-Host "Configuration complete!" -ForegroundColor Green
Write-Host "  Name:  $(git config --global user.name)" -ForegroundColor Cyan
Write-Host "  Email: $(git config --global user.email)" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now commit and push to GitHub." -ForegroundColor Green

