# PowerShell script to format code with Black and isort

$ErrorActionPreference = "Stop"

Write-Host "Formatting code with Black and isort..." -ForegroundColor Green

# Format with Black
Write-Host "Running Black..." -ForegroundColor Cyan
python -m black backend/ agent/
if ($LASTEXITCODE -ne 0) {
    Write-Host "Black formatting failed!" -ForegroundColor Red
    exit 1
}

# Sort imports with isort
Write-Host "Running isort..." -ForegroundColor Cyan
python -m isort backend/ agent/
if ($LASTEXITCODE -ne 0) {
    Write-Host "isort failed!" -ForegroundColor Red
    exit 1
}

# Run Black again to ensure compatibility
Write-Host "Running Black again for compatibility..." -ForegroundColor Cyan
python -m black backend/ agent/

Write-Host "Code formatting complete!" -ForegroundColor Green

