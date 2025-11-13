"""
AI Social Manager Orchestrator - FastAPI Microservice
Orchestrates AI pipeline: UPLOAD → CAPTION → SCHEDULE → POST → ANALYZE
"""

import logging
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from prometheus_client import make_asgi_app, Counter, Histogram
import uvicorn
import jwt
from datetime import datetime, timedelta

from orchestrator.config.settings import settings
from orchestrator.database.session import get_db, init_db
from orchestrator.routes import (
    discovery, generation, scheduling, models, feedback
)
from orchestrator.services.monitoring import MonitoringService

# Import orchestration components
from orchestrator.ai_pipeline import AIPipeline
from orchestrator.event_bus import EventBus
from orchestrator.websocket_manager import WebSocketManager
from orchestrator.retry_manager import RetryManager
from orchestrator.cache_manager import CacheManager
from orchestrator.health_monitor import HealthMonitor

# Configure structured logging
logging.basicConfig(level=logging.INFO)
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global orchestration components
event_bus = None
ai_pipeline = None
websocket_manager = None
retry_manager = None
cache_manager = None
health_monitor = None

# Prometheus metrics
REQUEST_COUNT = Counter('orchestrator_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('orchestrator_request_duration_seconds', 'Request duration')
PIPELINE_STARTED = Counter('orchestrator_pipelines_started_total', 'Total pipelines started')
PIPELINE_COMPLETED = Counter('orchestrator_pipelines_completed_total', 'Total pipelines completed')
PIPELINE_FAILED = Counter('orchestrator_pipelines_failed_total', 'Total pipelines failed')

# Security
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify JWT token and return user ID."""
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global event_bus, ai_pipeline, websocket_manager, retry_manager, cache_manager, health_monitor

    # Startup
    logger.info("Starting AI Social Manager Orchestrator", version=settings.VERSION)

    # Initialize database
    await init_db()

    # Initialize orchestration components
    event_bus = EventBus(settings.REDIS_URL)
    await event_bus.connect()

    cache_manager = CacheManager(settings.REDIS_URL)
    await cache_manager.start()

    retry_manager = RetryManager()
    await retry_manager.start()

    health_monitor = HealthMonitor(event_bus, check_interval=300)  # 5 minutes
    await health_monitor.start()

    websocket_manager = WebSocketManager(event_bus)
    await websocket_manager.start()

    ai_pipeline = AIPipeline(event_bus, retry_manager, cache_manager, health_monitor)

    # Initialize monitoring
    monitoring = MonitoringService()
    await monitoring.start()

    logger.info("All orchestration components initialized")

    yield

    # Shutdown
    logger.info("Shutting down AI Social Manager Orchestrator")

    if websocket_manager:
        await websocket_manager.stop()

    if health_monitor:
        await health_monitor.stop()

    if retry_manager:
        await retry_manager.stop()

    if cache_manager:
        await cache_manager.disconnect()

    if event_bus:
        await event_bus.disconnect()

    await monitoring.stop()

# Create FastAPI app
app = FastAPI(
    title="AI Social Manager Orchestrator",
    description="Orchestrates AI pipeline: UPLOAD → CAPTION → SCHEDULE → POST → ANALYZE",
    version=settings.VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include existing routers
app.include_router(discovery.router, prefix="/orchestrator", tags=["discovery"])
app.include_router(generation.router, prefix="/orchestrator", tags=["generation"])
app.include_router(scheduling.router, prefix="/orchestrator", tags=["scheduling"])
app.include_router(models.router, prefix="/orchestrator", tags=["models"])
app.include_router(feedback.router, prefix="/orchestrator", tags=["feedback"])

# New orchestration routes
@app.post("/orchestrator/pipeline/start")
async def start_pipeline(request: dict, user_id: str = Depends(verify_token)):
    """Start a new AI pipeline execution."""
    try:
        video_path = request.get("video_path")
        if not video_path:
            raise HTTPException(status_code=400, detail="video_path is required")

        task_id = await ai_pipeline.start_pipeline(
            task_id=f"pipeline_{int(datetime.utcnow().timestamp())}",
            user_id=user_id,
            video_path=video_path
        )

        PIPELINE_STARTED.inc()

        return {
            "task_id": task_id,
            "status": "started",
            "message": "AI pipeline started successfully"
        }

    except Exception as e:
        logger.error(f"Failed to start pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/orchestrator/pipeline/{task_id}/status")
async def get_pipeline_status(task_id: str, user_id: str = Depends(verify_token)):
    """Get pipeline execution status."""
    try:
        status = await ai_pipeline.get_pipeline_status(task_id)
        if not status:
            raise HTTPException(status_code=404, detail="Pipeline not found")

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pipeline status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/orchestrator/metrics")
async def get_orchestration_metrics(user_id: str = Depends(verify_token)):
    """Get orchestration metrics."""
    try:
        return {
            "pipeline_metrics": await ai_pipeline.get_metrics(),
            "cache_metrics": cache_manager.get_metrics(),
            "retry_metrics": retry_manager.get_metrics(),
            "websocket_connections": websocket_manager.get_connection_stats(),
            "health_status": health_monitor.get_health_status()
        }

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/orchestrator/health")
async def health_check():
    """Enhanced health check endpoint."""
    try:
        health_status = health_monitor.get_health_status()

        # Add orchestration component status
        health_status.update({
            "orchestration_components": {
                "event_bus": "healthy" if event_bus and event_bus.redis else "unhealthy",
                "cache_manager": "healthy" if cache_manager and cache_manager.redis else "unhealthy",
                "websocket_manager": "healthy" if websocket_manager and websocket_manager._running else "unhealthy",
                "retry_manager": "healthy" if retry_manager and retry_manager._running else "unhealthy",
                "ai_pipeline": "healthy" if ai_pipeline else "unhealthy"
            }
        })

        status_code = 200 if health_status.get("overall_status") == "healthy" else 503

        return JSONResponse(
            content={"status": "healthy", "service": "orchestrator", **health_status},
            status_code=status_code
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            content={"status": "unhealthy", "service": "orchestrator", "error": str(e)},
            status_code=503
        )

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Social Manager Orchestrator API",
        "version": settings.VERSION,
        "pipeline_status": "UPLOAD → CAPTION → SCHEDULE → POST → ANALYZE",
        "docs": "/docs",
        "websocket": f"ws://localhost:{settings.WEBSOCKET_PORT}"
    }

@app.middleware("http")
async def add_metrics(request: Request, call_next):
    """Add Prometheus metrics to requests."""
    method = request.method
    endpoint = request.url.path

    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()

    with REQUEST_LATENCY.time():
        response = await call_next(request)

    return response

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    """WebSocket endpoint handled by WebSocketManager."""
    # This is handled by the WebSocketManager server
    pass

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_config=None  # Use structlog
    )
