# 🚀 Deploy Your AI Smart Social Media Manager on Render

This guide walks you through deploying your private AI Social Media Automation server on Render — complete with FastAPI backend, React dashboard, and AI Agent.

## 📋 Prerequisites

Before you begin, make sure you have:

- A GitHub account
- A Render account (sign up at [render.com](https://render.com) if you don't have one)
- Your OpenAI API key
- (Optional) YouTube and Instagram API credentials

## 🎯 Step 1: Fork and Connect Repository

1. **Fork this repository** to your GitHub account
2. **Log in to Render** at [dashboard.render.com](https://dashboard.render.com)
3. Click **"New +"** in the top navigation
4. Select **"Blueprint"** from the dropdown

## 🔧 Step 2: Connect Your Repository

1. In the Blueprint setup, paste your GitHub repository URL
2. Render will automatically detect the `render.yaml` file in the root directory
3. Click **"Apply"** to proceed

## ⚙️ Step 3: Configure Environment Variables

Before deploying, you need to set up environment variables. Render will prompt you to add these, or you can add them after deployment in each service's settings:

### Required Environment Variables

#### For Backend (`ai-backend`):
```
OPENAI_API_KEY=your_openai_api_key_here
FRONTEND_URL=https://ai-frontend.onrender.com
```

#### For Frontend (`ai-frontend`):
```
NEXT_PUBLIC_API_BASE_URL=https://ai-backend.onrender.com
```

#### For Agent (`ai-agent`):
```
OPENAI_API_KEY=your_openai_api_key_here
BACKEND_API_URL=https://ai-backend.onrender.com
REDIS_URL=redis://red-xxxxxxxxxxxxxxxxxxxx:6379
CELERY_BROKER_URL=redis://red-xxxxxxxxxxxxxxxxxxxx:6379
CELERY_RESULT_BACKEND=redis://red-xxxxxxxxxxxxxxxxxxxx:6379
```

**Note**: If you get a "redis: is not found" error during Blueprint deployment, you may need to:
1. Let Render create the Redis service first
2. Then manually set the `REDIS_URL`, `CELERY_BROKER_URL`, and `CELERY_RESULT_BACKEND` environment variables in each service (backend and agent) using the internal Redis URL from the Render dashboard
3. The Redis internal URL format is: `redis://red-<instance-id>:6379`

### Optional Environment Variables

You can also configure:
- `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN` - For YouTube integration
- `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_APP_ID`, `INSTAGRAM_APP_SECRET` - For Instagram integration
- `JWT_SECRET` - For authentication (change from default)
- `LOG_LEVEL` - Set to `DEBUG`, `INFO`, `WARNING`, or `ERROR`

## 🚀 Step 4: Deploy All Services

1. After connecting your repository, Render will show you a preview of all services that will be created:
   - **ai-backend** (Web Service)
   - **ai-frontend** (Web Service)
   - **ai-agent** (Worker Service)
   - **ai-postgres** (PostgreSQL Database)
   - **ai-redis** (Redis Cache)

2. Review the configuration and click **"Apply"** to start the deployment

3. Render will automatically:
   - Build Docker images for each service
   - Create the database and Redis instances
   - Set up service connections
   - Deploy all services

## ⏱️ Step 5: Wait for Deployment

The deployment process typically takes 5-10 minutes. You can monitor the progress in the Render dashboard:

1. Each service will show a build log
2. Wait for all services to show **"Live"** status
3. Check the logs if any service fails to start

## ✅ Step 6: Verify Deployment

Once all services are live, verify your deployment:

### Backend Health Check
```bash
curl https://ai-backend.onrender.com/health
```

Expected response:
```json
{"status": "ok"}
```

### Frontend Access
Open your browser and navigate to:
```
https://ai-frontend.onrender.com
```

You should see the AI Social Media Manager dashboard.

### Agent Health Check
The agent runs as a background worker. Check its logs in the Render dashboard to ensure it's processing tasks.

## 🔍 Troubleshooting

### Service Won't Start

1. **Check Build Logs**: Click on the service and review the build logs for errors
2. **Check Runtime Logs**: Review the runtime logs for application errors
3. **Verify Environment Variables**: Ensure all required environment variables are set
4. **Database Connection**: Verify the database connection string is correct

### Common Issues

#### Backend can't connect to database
- Ensure `DATABASE_URL` is correctly set
- Check that the PostgreSQL service is running
- Verify the database name matches in `render.yaml`

#### Frontend can't reach backend
- Verify `NEXT_PUBLIC_API_BASE_URL` points to your backend URL
- Check CORS settings in backend (should include your frontend URL)
- Ensure backend service is live

#### Agent not processing tasks
- Check Redis connection (`REDIS_URL`)
- Verify Celery worker is running (check logs)
- Ensure `BACKEND_API_URL` is correct

### Viewing Logs

1. Navigate to your service in Render dashboard
2. Click on **"Logs"** tab
3. Review real-time logs for debugging

## 🔄 Updating Your Deployment

### Automatic Deployments

By default, Render will automatically deploy when you push to the `main` branch. To update:

1. Make your changes locally
2. Commit and push to `main` branch
3. Render will automatically detect and deploy the changes

### Manual Deployments

1. Go to your service in Render dashboard
2. Click **"Manual Deploy"**
3. Select the branch/commit to deploy

## 📊 Monitoring

### Health Checks

All services include health check endpoints:
- Backend: `/health`, `/health/live`, `/health/ready`
- Agent: `/health` (via health server)

Render automatically monitors these endpoints.

### Metrics

- View service metrics in the Render dashboard
- Monitor CPU, memory, and network usage
- Set up alerts for service downtime

## 🔐 Security Best Practices

1. **Never commit API keys**: Use Render's environment variables
2. **Use strong secrets**: Change default `JWT_SECRET` and passwords
3. **Enable HTTPS**: Render provides SSL certificates automatically
4. **Review access**: Limit who has access to your Render account

## 💰 Cost Management

### Free Tier Limits

Render's free tier includes:
- 750 hours/month of web service runtime
- 100GB bandwidth/month
- PostgreSQL database (90 days retention)
- Redis cache

### Upgrading

If you need more resources:
1. Go to service settings
2. Click **"Change Plan"**
3. Select a paid plan

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Next.js Deployment](https://nextjs.org/docs/deployment)

## 🆘 Support

If you encounter issues:

1. Check the [Render Status Page](https://status.render.com)
2. Review [Render Community Forums](https://community.render.com)
3. Check service logs for error messages
4. Verify all environment variables are set correctly

## 🎉 Success!

Once deployed, your AI Social Media Manager will be:
- ✅ Running 24/7 on Render's infrastructure
- ✅ Automatically scaling based on traffic
- ✅ Backed up with database snapshots
- ✅ Monitored with health checks
- ✅ Accessible via HTTPS URLs

Your services will be available at:
- **Backend API**: `https://ai-backend.onrender.com`
- **Frontend Dashboard**: `https://ai-frontend.onrender.com`
- **API Documentation**: `https://ai-backend.onrender.com/docs`

Happy automating! 🚀

