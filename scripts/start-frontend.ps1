# PowerShell script to start frontend server
# Run this after running start-dev.ps1

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

# Navigate to frontend
Set-Location frontend

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing Node.js dependencies..." -ForegroundColor Yellow
    npm install
}

Write-Host "🚀 Starting Frontend Server..." -ForegroundColor Cyan
Write-Host "Dashboard will be available at: http://localhost:3000" -ForegroundColor Green
Write-Host ""

# Start Next.js dev server
npm run dev

