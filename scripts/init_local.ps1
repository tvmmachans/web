# PowerShell script to initialize local development environment
# This script sets up the database and runs migrations

$ErrorActionPreference = "Stop"

Write-Host "Initializing local development environment..." -ForegroundColor Green

# Check if PostgreSQL is running
try {
    $pgCheck = & pg_isready -h localhost -p 5432 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "PostgreSQL is not running"
    }
} catch {
    Write-Host "PostgreSQL is not running. Please start PostgreSQL service." -ForegroundColor Red
    Write-Host "On Windows: Start PostgreSQL from Services panel" -ForegroundColor Yellow
    Write-Host "Or use: net start postgresql-x64-XX" -ForegroundColor Yellow
    exit 1
}

# Create database if it doesn't exist
Write-Host "Creating database..." -ForegroundColor Green
& createdb social_media_manager 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Database already exists or creation failed" -ForegroundColor Yellow
}

# Run migrations
Write-Host "Running database migrations..." -ForegroundColor Green
Set-Location backend
python -m alembic upgrade head

Set-Location ..

Write-Host "Local environment initialized successfully!" -ForegroundColor Green
Write-Host "You can now run: docker-compose up --build" -ForegroundColor Cyan

