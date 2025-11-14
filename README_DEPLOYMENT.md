# 🚀 Quick Start Deployment Guide

This repository is configured for one-click deployment on Render.com.

## 📦 What's Included

- ✅ **render.yaml** - Complete Render Blueprint configuration
- ✅ **Dockerfiles** - Production-ready multi-stage builds for all services
- ✅ **docker-compose.yml** - Local testing environment
- ✅ **GitHub Actions** - Automated CI/CD pipeline
- ✅ **Health Checks** - Monitoring endpoints for all services
- ✅ **Tests** - Backend and frontend test suites

## 🎯 One-Click Deployment

### Option 1: Render Blueprint (Recommended)

1. Fork this repository
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click **"New +"** → **"Blueprint"**
4. Paste your repository URL
5. Click **"Apply"** - Render will auto-detect `render.yaml`
6. Set your `OPENAI_API_KEY` environment variable
7. Click **"Deploy All"**

That's it! Your entire stack will be deployed automatically.

### Option 2: Manual Service Setup

If you prefer to set up services individually:

1. Create a PostgreSQL database
2. Create a Redis instance
3. Create web services for backend and frontend
4. Create a worker service for the agent
5. Configure environment variables (see `env.example`)

See [infra/RENDER_DEPLOY.md](infra/RENDER_DEPLOY.md) for detailed instructions.

## 🧪 Local Testing

Before deploying, test locally:

```bash
# Copy environment template
cp env.example .env

# Edit .env with your local configuration
# Then start all services
docker-compose up --build
```

Services will be available at:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- Database: localhost:5432
- Redis: localhost:6379

## ✅ Health Checks

All services include health endpoints:

- **Backend**: `/health`, `/health/live`, `/health/ready`
- **Agent**: `/health` (via health server on port 8080)
- **Frontend**: Root path `/` returns 200 OK

## 🔧 Environment Variables

Required variables (see `env.example` for full list):

- `OPENAI_API_KEY` - Your OpenAI API key
- `DATABASE_URL` - PostgreSQL connection string (auto-set by Render)
- `REDIS_URL` - Redis connection string (auto-set by Render)

## 📚 Documentation

- **Full Deployment Guide**: [infra/RENDER_DEPLOY.md](infra/RENDER_DEPLOY.md)
- **API Documentation**: Available at `/docs` endpoint after deployment
- **Backend Tests**: `backend/tests/`
- **Frontend Tests**: `frontend/__tests__/` and `frontend/e2e/`

## 🐛 Troubleshooting

### Build Fails
- Check Dockerfile paths match your directory structure
- Verify all dependencies are in requirements files
- Review build logs in Render dashboard

### Services Won't Start
- Verify all environment variables are set
- Check service logs for errors
- Ensure database and Redis are running

### Connection Issues
- Verify CORS settings include your frontend URL
- Check `NEXT_PUBLIC_API_BASE_URL` points to backend
- Ensure services can reach each other (check Render service names)

## 🎉 Success Indicators

Your deployment is successful when:

- ✅ All services show "Live" status in Render
- ✅ Backend health check returns `{"status": "ok"}`
- ✅ Frontend loads without errors
- ✅ Agent worker is processing tasks (check logs)
- ✅ Database migrations completed

## 📞 Support

- Check [Render Status](https://status.render.com)
- Review service logs in Render dashboard
- See [infra/RENDER_DEPLOY.md](infra/RENDER_DEPLOY.md) for detailed troubleshooting

---

**Ready to deploy?** Follow the [Render Deployment Guide](infra/RENDER_DEPLOY.md) for step-by-step instructions!

