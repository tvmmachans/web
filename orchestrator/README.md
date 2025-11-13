# AI Trend Orchestrator

Autonomous service for discovering Malayalam trends and generating content.

## Overview

The AI Trend Orchestrator is a FastAPI microservice that autonomously discovers trending topics in Malayalam across multiple social media platforms (YouTube, Instagram, Twitter, RSS feeds) and generates optimized content blueprints for short-form video creation.

## Features

- **Multi-Source Trend Discovery**: Aggregates trends from YouTube, Instagram, Twitter, and RSS feeds
- **Malayalam Content Focus**: Specialized detection and processing of Malayalam language content
- **ML-Powered Predictions**: XGBoost models for engagement prediction and ROI scoring
- **Automated Content Generation**: GPT-4 powered blueprint creation with voiceover and captions
- **Intelligent Scheduling**: Optimal posting time recommendations and auto-scheduling
- **Performance Tracking**: Real-time analytics and continuous model retraining
- **Prometheus Monitoring**: Comprehensive metrics and health monitoring

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Trend         │    │   Content       │    │   Scheduling    │
│   Discovery     │───▶│   Generation    │───▶│   & Posting     │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ML            │    │   Voice         │    │   Backend       │
│   Prediction    │    │   Engine        │    │   Integration   │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## API Endpoints

### Discovery
- `POST /orchestrator/discovery/run_once` - Trigger trend discovery
- `GET /orchestrator/discovery/status` - Get discovery status
- `GET /orchestrator/discovery/trends` - List discovered trends

### Generation
- `POST /orchestrator/generation/generate` - Generate content blueprint
- `GET /orchestrator/generation/blueprints` - List blueprints
- `GET /orchestrator/generation/blueprint/{id}` - Get blueprint details

### Scheduling
- `POST /orchestrator/scheduling/schedule` - Schedule blueprint for posting
- `POST /orchestrator/scheduling/auto_schedule` - Auto-schedule top blueprints
- `GET /orchestrator/scheduling/scheduled` - List scheduled posts

### Models
- `GET /orchestrator/models/` - Get ML model status
- `POST /orchestrator/models/retrain` - Retrain ML models

### Feedback
- `POST /orchestrator/feedback/performance` - Update performance metrics
- `POST /orchestrator/feedback/feedback` - Submit human feedback
- `GET /orchestrator/feedback/analytics` - Get analytics

## Configuration

Environment variables:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/orchestrator

# External APIs
YOUTUBE_API_KEY=your_youtube_key
OPENAI_API_KEY=your_openai_key
INSTAGRAM_ACCESS_TOKEN=your_instagram_token
TWITTER_BEARER_TOKEN=your_twitter_token

# Services
BACKEND_BASE_URL=http://backend:8000
VOICE_ENGINE_URL=http://voice-engine:8002

# Settings
DEBUG=false
ENABLE_AUTO_POST=false
DISCOVERY_INTERVAL_MINUTES=30
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables in `.env`

3. Initialize database:
```bash
alembic upgrade head
```

4. Run the service:
```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## Docker

```bash
docker build -f Dockerfile.orchestrator -t orchestrator .
docker run -p 8001:8001 orchestrator
```

## Celery Tasks

Background tasks are handled by Celery:

- Trend discovery every 30 minutes
- Blueprint generation every 30 minutes
- ML model retraining daily
- Auto-scheduling hourly

Start Celery worker:
```bash
celery -A orchestrator.celery_app worker --loglevel=info
```

Start Celery beat scheduler:
```bash
celery -A orchestrator.celery_app beat --loglevel=info
```

## Monitoring

- **Prometheus Metrics**: Available at `/metrics` (port 8002)
- **Health Check**: `GET /health`
- **Grafana Dashboard**: Pre-configured dashboard available

## Development

### Testing
```bash
pytest tests/
```

### Code Quality
```bash
black orchestrator/
flake8 orchestrator/
mypy orchestrator/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

MIT License
