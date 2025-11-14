# ✅ Deployment Checklist

Use this checklist to ensure your AI Social Media Manager is ready for production deployment on Render.

## 📋 Pre-Deployment

### Repository Setup
- [ ] Repository is forked/cloned to your GitHub account
- [ ] All code is committed and pushed to `main` branch
- [ ] `render.yaml` exists in root directory
- [ ] All Dockerfiles are present and valid

### Configuration Files
- [ ] `render.yaml` - Render Blueprint configuration
- [ ] `Dockerfile.backend` - Backend service Dockerfile
- [ ] `Dockerfile.frontend` - Frontend service Dockerfile
- [ ] `Dockerfile.agent` - Agent worker Dockerfile
- [ ] `docker-compose.yml` - Local testing configuration
- [ ] `env.example` - Environment variables template

### Environment Variables
- [ ] `OPENAI_API_KEY` - Obtained and ready to set
- [ ] `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET` (optional)
- [ ] `INSTAGRAM_ACCESS_TOKEN` (optional)
- [ ] `JWT_SECRET` - Changed from default value

### Testing
- [ ] Backend tests pass: `pytest backend/tests/`
- [ ] Frontend tests pass: `npm test` in frontend directory
- [ ] Local docker-compose setup works: `docker-compose up`
- [ ] Health endpoints respond correctly:
  - Backend: `curl http://localhost:8000/health`
  - Agent: `curl http://localhost:8080/health`

## 🚀 Deployment Steps

### Render Setup
- [ ] Created Render account
- [ ] Connected GitHub repository to Render
- [ ] Selected "Blueprint" deployment type
- [ ] Render detected `render.yaml` automatically

### Service Configuration
- [ ] Reviewed all services in Render preview:
  - [ ] ai-backend (Web Service)
  - [ ] ai-frontend (Web Service)
  - [ ] ai-agent (Worker Service)
  - [ ] ai-postgres (Database)
  - [ ] ai-redis (Redis Cache)

### Environment Variables Setup
- [ ] Set `OPENAI_API_KEY` for backend service
- [ ] Set `OPENAI_API_KEY` for agent service
- [ ] Verified auto-configured variables:
  - [ ] `DATABASE_URL` (from database)
  - [ ] `REDIS_URL` (from Redis)
  - [ ] `FRONTEND_URL` (from frontend service)
  - [ ] `BACKEND_API_URL` (from backend service)
  - [ ] `NEXT_PUBLIC_API_BASE_URL` (from backend service)

### Deployment
- [ ] Clicked "Apply" to start deployment
- [ ] Monitored build logs for all services
- [ ] All services built successfully
- [ ] All services show "Live" status

## ✅ Post-Deployment Verification

### Service Health
- [ ] Backend health check: `curl https://ai-backend.onrender.com/health`
  - Expected: `{"status": "ok"}`
- [ ] Frontend loads: Open `https://ai-frontend.onrender.com`
  - Page loads without errors
  - No console errors in browser
- [ ] Agent worker is running: Check logs in Render dashboard
  - Celery worker started
  - Health server started

### Functionality Tests
- [ ] Backend API docs accessible: `https://ai-backend.onrender.com/docs`
- [ ] Frontend can connect to backend API
- [ ] Database connection working (check backend logs)
- [ ] Redis connection working (check agent logs)
- [ ] CORS configured correctly (no CORS errors in browser)

### Monitoring
- [ ] Health checks passing in Render dashboard
- [ ] Service metrics visible (CPU, memory, network)
- [ ] Logs accessible and readable
- [ ] No error messages in logs

## 🔧 Optional Enhancements

### Security
- [ ] Changed default `JWT_SECRET`
- [ ] Reviewed and restricted CORS origins
- [ ] Set up environment variable encryption (Render Pro)
- [ ] Enabled HTTPS (automatic on Render)

### Performance
- [ ] Upgraded to paid plan if needed
- [ ] Configured auto-scaling (Render Pro)
- [ ] Set up monitoring alerts
- [ ] Optimized Docker images (multi-stage builds ✅)

### CI/CD
- [ ] GitHub Actions workflow configured
- [ ] `RENDER_API_KEY` added to GitHub secrets
- [ ] `RENDER_SERVICE_ID` added to GitHub secrets (if using)
- [ ] Automatic deployments on push to `main` working

## 📊 Success Criteria

Your deployment is successful when:

✅ All services show "Live" status  
✅ Health endpoints return 200 OK  
✅ Frontend loads and connects to backend  
✅ Agent worker processes tasks  
✅ No critical errors in logs  
✅ Database and Redis connections working  

## 🆘 Troubleshooting

If deployment fails:

1. **Check Build Logs**
   - Review each service's build log
   - Look for dependency installation errors
   - Verify Dockerfile syntax

2. **Check Runtime Logs**
   - Review service startup logs
   - Look for connection errors
   - Check environment variable issues

3. **Verify Configuration**
   - Ensure all required env vars are set
   - Check service names match in `render.yaml`
   - Verify database/Redis are created

4. **Test Locally First**
   - Run `docker-compose up` locally
   - Fix any issues before deploying
   - Verify health endpoints work

## 📚 Resources

- [Full Deployment Guide](infra/RENDER_DEPLOY.md)
- [Render Documentation](https://render.com/docs)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

**Ready to deploy?** Follow the checklist above and refer to [infra/RENDER_DEPLOY.md](infra/RENDER_DEPLOY.md) for detailed instructions!

