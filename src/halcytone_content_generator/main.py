"""
Main FastAPI application for Halcytone Content Generator
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Optional

from .config import Settings, get_settings
from .api import endpoints
from .core.logging import setup_logging

# Setup logging
logger = setup_logging(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events"""
    logger.info("Starting Halcytone Content Generator Service...")

    # Initialize WebSocket services (Sprint 3)
    from .api.websocket_endpoints import initialize_websocket_services, cleanup_websocket_services
    await initialize_websocket_services()

    yield

    # Cleanup WebSocket services
    await cleanup_websocket_services()

    logger.info("Shutting down Halcytone Content Generator Service...")


# Create FastAPI application
app = FastAPI(
    title="Halcytone Content Generator",
    description="Automated multi-channel content generation for marketing communications",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Halcytone Content Generator",
        "version": "0.1.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check(settings: Settings = Depends(get_settings)):
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "environment": settings.ENVIRONMENT
    }


@app.get("/ready")
async def readiness_check(settings: Settings = Depends(get_settings)):
    """Readiness check for deployment orchestration"""
    # Check if required external services are accessible
    checks = {
        "crm_configured": bool(settings.CRM_BASE_URL),
        "platform_configured": bool(settings.PLATFORM_BASE_URL),
        "document_source_configured": bool(settings.LIVING_DOC_ID)
    }

    all_ready = all(checks.values())

    return {
        "ready": all_ready,
        "checks": checks
    }


# Include API routers
app.include_router(endpoints.router, prefix="/api/v1")

# Include enhanced v2 endpoints
from .api import endpoints_v2
app.include_router(endpoints_v2.router, prefix="/api")

# Include critical production endpoints
from .api import endpoints_critical
app.include_router(endpoints_critical.router)

# Include batch generation endpoints
from .api import endpoints_batch
app.include_router(endpoints_batch.router, prefix="/api/v1")

# Include schema-validated endpoints (Sprint 2)
from .api.endpoints_schema_validated import router as schema_validated_router
app.include_router(schema_validated_router, prefix="/api")

# Include WebSocket endpoints (Sprint 3)
from .api import websocket_endpoints
app.include_router(websocket_endpoints.router)

# Include Cache endpoints (Sprint 4)
from .api import cache_endpoints
app.include_router(cache_endpoints.router, prefix="/api/v1")