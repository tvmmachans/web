"""
Simple health check server for the agent service.
This allows Render to monitor the agent's health status.
"""

import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="AI Agent Health Server")


@app.get("/health")
async def health():
    """Health check endpoint for Render"""
    return {"status": "running", "service": "ai-agent"}


@app.get("/health/live")
async def health_live():
    """Liveness probe"""
    return {"status": "alive"}


@app.get("/health/ready")
async def health_ready():
    """Readiness probe - check if agent is ready"""
    # TODO: Add actual readiness checks (Celery connection, etc.)
    return {"status": "ready"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
