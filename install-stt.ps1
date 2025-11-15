# PowerShell script to install Speech-to-Text alternatives
# Run this after installing core requirements

$ErrorActionPreference = "Stop"

Write-Host "Installing Speech-to-Text alternatives..." -ForegroundColor Green

# Activate virtual environment if not already activated
$venvPath = Join-Path $PSScriptRoot "venv"
if (Test-Path $venvPath) {
    & "$venvPath\Scripts\Activate.ps1"
}

# Install Google Cloud Speech-to-Text (recommended for Malayalam)
Write-Host "Installing Google Cloud Speech-to-Text..." -ForegroundColor Yellow
python -m pip install google-cloud-speech==2.21.0

# Install Azure Speech Services (alternative)
Write-Host "Installing Azure Speech Services..." -ForegroundColor Yellow
python -m pip install azure-cognitiveservices-speech==1.32.1

# Install Vosk (offline alternative)
Write-Host "Installing Vosk..." -ForegroundColor Yellow
python -m pip install vosk==0.3.45

# Install SpeechRecognition library
Write-Host "Installing SpeechRecognition..." -ForegroundColor Yellow
python -m pip install SpeechRecognition==3.10.0

Write-Host "[OK] Speech-to-Text alternatives installed successfully" -ForegroundColor Green
Write-Host ""
Write-Host "Note: Configure API keys in your .env file:" -ForegroundColor Yellow
Write-Host "  - GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json" -ForegroundColor White
Write-Host "  - AZURE_SPEECH_KEY=your_azure_key" -ForegroundColor White
Write-Host "  - AZURE_SPEECH_REGION=eastus" -ForegroundColor White
Write-Host "  - VOSK_MODEL_PATH=path/to/vosk-model" -ForegroundColor White
Write-Host ""
Write-Host "For offline Malayalam support, download Vosk model:" -ForegroundColor Yellow
Write-Host "  https://alphacephei.com/vosk/models" -ForegroundColor White
