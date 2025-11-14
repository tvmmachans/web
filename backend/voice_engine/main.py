import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from routes.analyze import router as analyze_router
from routes.dub import router as dub_router
from routes.generate import router as generate_router
from routes.train import router as train_router
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

load_dotenv()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Voice Engine Service", version="1.0.0")

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(train_router, prefix="/voice/train", tags=["Voice Training"])
app.include_router(generate_router, prefix="/voice/generate", tags=["Voice Generation"])
app.include_router(dub_router, prefix="/voice/dub", tags=["Video Dubbing"])
app.include_router(analyze_router, prefix="/voice/analyze", tags=["Voice Analysis"])


@app.on_event("startup")
async def on_startup():
    # Initialize voice engine components
    pass


@app.on_event("shutdown")
async def on_shutdown():
    # Cleanup voice engine resources
    pass


@app.get("/health/live")
async def health_live():
    return {"status": "alive"}


@app.get("/health/ready")
async def health_ready():
    # TODO: Add proper health checks for voice models, storage, etc.
    return {"status": "ready"}
