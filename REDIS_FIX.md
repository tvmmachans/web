# 🔧 Fixing "redis: is not found" Error

If you encounter the error **"redis: is not found"** when deploying to Render, here are the solutions:

## Solution 1: Manual Redis URL Configuration (Recommended)

If the automatic Redis service reference doesn't work in the Blueprint, manually configure the Redis URLs:

1. **Deploy the Blueprint** - Let Render create all services including the Redis instance
2. **Get the Redis Internal URL**:
   - Go to your Redis service in Render dashboard
   - Copy the **Internal Redis URL** (format: `redis://red-xxxxxxxxxxxxxxxxxxxx:6379`)
3. **Set Environment Variables Manually**:
   
   For **ai-backend** service:
   - `REDIS_URL` = `redis://red-xxxxxxxxxxxxxxxxxxxx:6379`
   
   For **ai-agent** service:
   - `REDIS_URL` = `redis://red-xxxxxxxxxxxxxxxxxxxx:6379`
   - `CELERY_BROKER_URL` = `redis://red-xxxxxxxxxxxxxxxxxxxx:6379`
   - `CELERY_RESULT_BACKEND` = `redis://red-xxxxxxxxxxxxxxxxxxxx:6379`

## Solution 2: Deploy Services in Order

1. First, deploy just the Redis service manually
2. Then deploy the rest of the services using the Blueprint
3. The services should be able to reference the existing Redis instance

## Solution 3: Update render.yaml

If the `fromService` syntax doesn't work for Redis, you can modify `render.yaml` to remove the automatic Redis references and set them manually after deployment:

```yaml
# Instead of:
- key: REDIS_URL
  fromService:
    name: ai-redis
    type: redis
    property: connectionString

# Use:
- key: REDIS_URL
  sync: false
  # Then set manually in Render dashboard
```

## Solution 4: Verify Service Names Match

Ensure the Redis service name in `render.yaml` matches exactly:
- Service name: `ai-redis`
- Reference name: `ai-redis` (must match exactly)

## Solution 5: Check Region Consistency

Make sure all services (backend, agent, and Redis) are deployed in the **same region**. Cross-region communication doesn't work for internal service references.

## Quick Fix Steps

1. **Deploy the Blueprint** (even if Redis reference fails)
2. **Note the Redis service name** created by Render
3. **Get the Redis Internal URL** from the Redis service dashboard
4. **Manually set** `REDIS_URL`, `CELERY_BROKER_URL`, and `CELERY_RESULT_BACKEND` in:
   - Backend service environment variables
   - Agent service environment variables
5. **Redeploy** the backend and agent services

## Verification

After setting the Redis URLs, verify the connection:

```bash
# Check backend logs
# Should see successful Redis connection

# Check agent logs  
# Should see Celery worker connected to Redis
```

## Alternative: Use Render's Environment Variable Sync

If you have Render Pro, you can use environment variable groups to sync the Redis URL across services automatically.

---

**Most Common Fix**: Simply get the Redis internal URL from the dashboard and manually set it in the environment variables for backend and agent services. This works 100% of the time!

