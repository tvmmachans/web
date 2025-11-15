import asyncio
import logging
import os

import scheduler
from database import init_db
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import orchestrator event bus integration
from orchestrator_event_integration import OrchestratorEventIntegration
from prometheus_fastapi_instrumentator import Instrumentator
from routes.analytics import router as analytics_router
from routes.generate import router as generate_router
from routes.instagram import router as instagram_router
from routes.schedule import router as schedule_router
from routes.upload import router as upload_router
from routes.youtube import router as youtube_router
from routes.automation import router as automation_router
from routes.ai_generation import router as ai_generation_router
from routes.advanced_features import router as advanced_features_router
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

load_dotenv()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="AI Social Media Manager Backend", version="1.0.0")

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app)

# CORS configuration - support both local and Render URLs
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://ai-frontend.onrender.com",
]
# Add FRONTEND_URL from environment if set
if os.getenv("FRONTEND_URL"):
    allowed_origins.append(os.getenv("FRONTEND_URL"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator event integration
orchestrator_integration = None

# Include all routers
app.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
app.include_router(upload_router, prefix="/upload", tags=["Upload"])
app.include_router(schedule_router, prefix="/schedule", tags=["Schedule"])
app.include_router(generate_router, prefix="/generate", tags=["Generate"])
app.include_router(youtube_router, prefix="/youtube", tags=["YouTube"])
app.include_router(instagram_router, prefix="/instagram", tags=["Instagram"])
app.include_router(automation_router, prefix="/agent/automation", tags=["Automation"])
app.include_router(ai_generation_router, prefix="/ai", tags=["AI Generation"])
app.include_router(advanced_features_router, prefix="/advanced", tags=["Advanced Features"])


@app.on_event("startup")
async def on_startup():
    global orchestrator_integration

    await init_db()
    scheduler.start_scheduler()

    # Initialize orchestrator event integration
    orchestrator_integration = OrchestratorEventIntegration()
    await orchestrator_integration.start()


@app.on_event("shutdown")
async def on_shutdown():
    scheduler.shutdown_scheduler()

    # Stop orchestrator integration
    if orchestrator_integration:
        await orchestrator_integration.stop()


@app.get("/health")
async def health():
    """Simple health check endpoint for Render and monitoring"""
    return {"status": "ok"}


@app.get("/health/live")
async def health_live():
    return {"status": "alive"}


@app.get("/health/ready")
async def health_ready():
    # TODO: Add proper health checks for DB, Redis, external APIs
    health_status = {"status": "ready"}

    # Add orchestrator integration health
    if orchestrator_integration:
        health_status["orchestrator_integration"] = (
            await orchestrator_integration.health_check()
        )

    return health_status
