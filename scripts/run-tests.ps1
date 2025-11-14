# PowerShell script to run tests

param(
    [string]$Directory = "backend",
    [switch]$Coverage = $false
)

$ErrorActionPreference = "Stop"

Write-Host "Running tests in $Directory..." -ForegroundColor Green

Set-Location $Directory

if ($Coverage) {
    $env:PYTHONPATH = ".."
    python -m pytest tests/ -v --cov=. --cov-report=xml
} else {
    $env:PYTHONPATH = ".."
    python -m pytest tests/ -v
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "Tests failed!" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Set-Location ..
Write-Host "All tests passed!" -ForegroundColor Green

