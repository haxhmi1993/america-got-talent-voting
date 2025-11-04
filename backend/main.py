"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from routes import vote, health, metrics
from services.cache import cache
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown."""
    # Startup
    logger.info("Starting up voting system application...")
    await cache.initialize()
    yield
    # Shutdown
    logger.info("Shutting down voting system application...")
    await cache.close()


app = FastAPI(
    title="AGT Voting System POC",
    description="Proof of Concept for America's Got Talent voting system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(vote.router, prefix="/api", tags=["voting"])
app.include_router(health.router, tags=["health"])
app.include_router(metrics.router, tags=["metrics"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AGT Voting System API",
        "version": "1.0.0",
        "endpoints": {
            "vote": "/api/vote",
            "health": "/health",
            "metrics": "/metrics"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
