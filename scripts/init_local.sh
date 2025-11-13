#!/bin/bash

# Script to initialize local development environment
# This script sets up the database and runs migrations

set -e

echo "Initializing local development environment..."

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "PostgreSQL is not running. Please start PostgreSQL service."
    echo "On macOS: brew services start postgresql"
    echo "On Ubuntu: sudo systemctl start postgresql"
    echo "On Windows: Start PostgreSQL from Services panel"
    exit 1
fi

# Create database if it doesn't exist
echo "Creating database..."
createdb social_media_manager 2>/dev/null || echo "Database already exists"

# Run migrations
echo "Running database migrations..."
cd backend
python -m alembic upgrade head

echo "Local environment initialized successfully!"
echo "You can now run: docker-compose up --build"
