# PowerShell script to install PyTorch with CPU support
# Run this after installing other requirements

$ErrorActionPreference = "Stop"

Write-Host "Installing PyTorch (CPU version)..." -ForegroundColor Green

# Activate virtual environment if not already activated
$venvPath = Join-Path $PSScriptRoot "venv"
if (Test-Path $venvPath) {
    & "$venvPath\Scripts\Activate.ps1"
}

# Install PyTorch from the CPU index
python -m pip install torch==2.1.1 --index-url https://download.pytorch.org/whl/cpu

Write-Host "[OK] PyTorch installed successfully" -ForegroundColor Green
Write-Host ""
Write-Host "Note: If you need GPU support, visit https://pytorch.org/get-started/locally/" -ForegroundColor Yellow

