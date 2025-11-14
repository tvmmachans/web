# 🔧 Common Deployment Issues & Solutions

## Issue 1: "service type is not available for this plan" (Worker Service)

### Problem
Render's free plan doesn't support `type: worker` services.

### Solution
✅ **FIXED**: Changed agent service from `type: worker` to `type: web` in `render.yaml`.

The agent now runs as a web service with:
- Health check endpoint at `/health` (required for web services)
- Celery worker running in background
- Health server on port 8080 for Render monitoring

### Why This Works
- Web services on free plan can run background processes
- The agent's health server satisfies Render's web service requirements
- Celery worker continues to function normally

## Issue 2: Frontend Deployment Failed

### Possible Causes

1. **Missing Next.js App Structure**
   - The `frontend/` directory needs a complete Next.js app
   - Required: `app/` or `pages/` directory with React components
   - Check: Does `frontend/` have actual Next.js pages/components?

2. **Missing Dependencies**
   - Ensure `package-lock.json` exists
   - Run `npm install` in frontend directory before deploying

3. **Build Errors**
   - Check Render build logs for specific errors
   - Common issues:
     - Missing environment variables
     - TypeScript errors
     - Missing dependencies

### Quick Fix Steps

1. **Verify Frontend Structure**:
   ```bash
   cd frontend
   ls -la
   # Should see: app/ or pages/, components/, etc.
   ```

2. **Install Dependencies Locally**:
   ```bash
   cd frontend
   npm install
   npm run build  # Test build locally
   ```

3. **Check Build Logs**:
   - Go to Render dashboard → ai-frontend service
   - Click "Logs" tab
   - Look for build errors

4. **If Frontend is Incomplete**:
   - Option A: Create a minimal Next.js app structure
   - Option B: Temporarily remove frontend from Blueprint
   - Option C: Deploy frontend separately after fixing structure

## Issue 3: Environment Variable Creation Canceled

### Problem
When one service fails, dependent operations (like env var creation) are canceled.

### Solution
1. Fix the failing service first (see Issue 1 & 2)
2. Redeploy the Blueprint
3. Environment variables will be created automatically once services deploy

## Current Status

✅ **Agent Service**: Fixed - Changed to `type: web`  
⚠️ **Frontend Service**: Needs investigation - Check build logs  
✅ **Backend Service**: Should work once dependencies are resolved  
✅ **Redis Service**: Configured correctly  
✅ **Database Service**: Configured correctly  

## Next Steps

1. **Deploy Again** with updated `render.yaml` (agent is now web service)
2. **Check Frontend Build Logs** to identify specific errors
3. **Fix Frontend Issues** based on build log errors
4. **Redeploy** once all issues are resolved

## Alternative: Deploy Services Separately

If Blueprint deployment continues to fail:

1. **Deploy Backend First**:
   - Create web service manually
   - Use `Dockerfile.backend`
   - Set environment variables

2. **Deploy Database & Redis**:
   - Create PostgreSQL database
   - Create Redis (keyvalue) service

3. **Deploy Agent**:
   - Create web service
   - Use `Dockerfile.agent`
   - Connect to database and Redis

4. **Deploy Frontend Last**:
   - Once backend is live
   - Use `Dockerfile.frontend`
   - Set `NEXT_PUBLIC_API_BASE_URL`

This approach allows you to fix issues one service at a time.

