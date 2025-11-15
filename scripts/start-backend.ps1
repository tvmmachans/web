# PowerShell script to start backend server
# Run this after running start-dev.ps1

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

# Activate virtual environment
$venvPath = Join-Path $projectRoot "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "✗ Virtual environment not found. Run .\scripts\start-dev.ps1 first" -ForegroundColor Red
    exit 1
}

Write-Host "Activating virtual environment..." -ForegroundColor Green
& "$venvPath\Scripts\Activate.ps1"

# Navigate to backend
Set-Location backend

Write-Host "🚀 Starting Backend Server..." -ForegroundColor Cyan
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Green
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""

# Start uvicorn
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

