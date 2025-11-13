# AI Smart Social Media Manager

This project provides a complete solution for automating social media content creation, scheduling, and analytics for Malayalam content creators on YouTube and Instagram. It includes a FastAPI backend, Next.js frontend dashboard, and an AI-powered agent using machine learning and GPT for optimization.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │     Backend     │    │     Agent       │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│ (Celery Worker) │
│                 │    │                 │    │                 │
│ - Dashboard UI  │    │ - REST API      │    │ - Task Queue    │
│ - Analytics     │    │ - Auth/JWT      │    │ - ML Models     │
│ - Content Mgmt  │    │ - Rate Limiting │    │ - Auto Posting  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │    Redis        │    │    MinIO        │
│   (Database)    │    │  (Cache/Queue)  │    │  (File Storage) │
│                 │    │                 │    │                 │
│ - User Data     │    │ - Sessions      │    │ - Videos        │
│ - Posts         │    │ - Celery Tasks  │    │ - Assets        │
│ - Analytics     │    │ - Cache         │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Infrastructure Components:**
- **Monitoring**: Prometheus metrics at `/metrics` endpoints
- **Orchestration**: Kubernetes with HPA for auto-scaling
- **CI/CD**: GitHub Actions for automated testing and deployment
- **Security**: JWT auth, rate limiting, signed URLs for S3

## Features

- **Video Processing**: Automatic clip extraction, subtitle generation with Whisper, and upload handling.
- **AI Content Generation**: Malayalam captions, hashtags, titles, and descriptions using GPT-4.
- **Social Media Integration**: YouTube Data API and Instagram Graph API support.
- **Scheduling**: Automated posting at optimal times using machine learning predictions.
- **Analytics**: Real-time metrics fetching, performance tracking, and insights.
- **AI Agent**: Autonomous posting, content repurposing, comment replies, and weekly reports.
- **Dashboard**: User-friendly interface for managing posts, viewing analytics, and AI chat.

## Local Development Setup

### One-Click Startup

1. **Clone the repository** and navigate to the directory.

2. **Start all services with Docker Compose**:
   ```bash
   docker-compose -f infra/docker-compose.yml up --build
   ```
   This will start:
   - Backend API (FastAPI) on port 8000
   - Frontend Dashboard (Next.js) on port 3000
   - PostgreSQL database on port 5432
   - Redis for caching and Celery on port 6379
   - MinIO for file storage on port 9000
   - Celery worker and beat scheduler

3. **Initialize the database** (run in a separate terminal):
   ```bash
   ./scripts/init_local.sh
   ```
   This script will:
   - Run database migrations with Alembic
   - Create initial data if needed

4. **Access the applications**:
   - **Frontend Dashboard**: http://localhost:3000
   - **Backend API Docs**: http://localhost:8000/docs
   - **MinIO Console**: http://localhost:9001 (admin/minio123)
   - **PostgreSQL**: localhost:5432 (user: postgres, password: postgres)
   - **Redis**: localhost:6379

### Environment Setup

Copy the example environment file and configure your variables:

```bash
cp .env.example .env
```

Required environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `S3_ACCESS_KEY` & `S3_SECRET_KEY`: MinIO/S3 credentials
- `OPENAI_API_KEY`: For AI content generation
- `YOUTUBE_API_KEY`: YouTube Data API key
- `INSTAGRAM_ACCESS_TOKEN`: Instagram Graph API token

### Manual Setup (Alternative)

If you prefer not to use Docker:

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r agent/requirements-agent.txt
   ```

2. **Install Node.js dependencies**:
   ```bash
   cd frontend
   npm install
   ```

3. **Start services individually**:
   ```bash
   # Terminal 1: Backend
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

   # Terminal 2: Frontend
   cd frontend && npm run dev

   # Terminal 3: Agent
   cd agent && python -m celery -A celery_app worker --loglevel=info

   # Terminal 4: Agent Beat (scheduler)
   cd agent && python -m celery -A celery_app beat --loglevel=info
   ```

## Deployment

### Staging (via GitHub Actions)

The CI/CD pipeline automatically builds and deploys to staging on merges to `main`. It uses GitHub Container Registry for images and a Kubernetes cluster for deployment.

### Production

For production, deploy to a cloud provider like AWS EKS or DigitalOcean Kubernetes. Use the provided Kubernetes manifests in `infra/`.

**Quick deployment with Render/Railway**:
- Set environment variables as per `.env.example`.
- Point to a managed Postgres and Redis.
- Use cloud storage like AWS S3 instead of MinIO.

See `RUNBOOK.md` for detailed deployment, backup, and rollback instructions.

## Monitoring

The backend and agent expose Prometheus metrics at `/metrics`. Use the provided Grafana dashboard example for visualization.

## Security

- All API calls use JWT authentication.
- Secrets are managed via environment variables.
- HTTPS is enforced in production.
- Rate limiting is applied to prevent abuse.

## Contributing

- Ensure tests pass with `pytest` in backend.
- Follow Python and React best practices.
- Update documentation for any new features.

## License

MIT
