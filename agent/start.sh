#!/bin/bash
# Start script for agent service - runs both health server and Celery worker

set -e

# Start health server in background
echo "Starting health server on port ${PORT:-8080}..."
uvicorn agent.health_server:app --host 0.0.0.0 --port ${PORT:-8080} &

# Start Celery worker
echo "Starting Celery worker..."
celery -A agent.celery_app worker --loglevel=info --concurrency=2

# Wait for background processes
wait

