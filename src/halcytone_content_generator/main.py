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
from .health import get_health_manager

# Setup logging
logger = setup_logging(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events"""
    logger.info("Starting Halcytone Content Generator Service...")

    # Initialize health check manager with start time
    health_manager = get_health_manager()

    # Initialize production configuration and services
    try:
        from .config.enhanced_config import get_production_settings
        from .core.services import get_service_container, validate_all_services

        # Load production settings
        settings = await get_production_settings()
        logger.info(f"Loaded configuration for {settings.ENVIRONMENT} environment")

        # Initialize service container
        container = await get_service_container(settings)
        logger.info("Service container initialized")

        # Validate service connections
        try:
            validation_results = await validate_all_services()
            logger.info(f"Service validation results: {validation_results}")
        except Exception as e:
            logger.warning(f"Service validation failed: {e}")

        # Initialize database if configured
        try:
            from .database import init_database
            if settings.database.DATABASE_URL or settings.ENVIRONMENT != 'development':
                db_initialized = await init_database()
                if db_initialized:
                    logger.info("Database initialized successfully")
                else:
                    logger.warning("Database initialization failed")
        except Exception as e:
            logger.warning(f"Database initialization skipped: {e}")

    except Exception as e:
        logger.error(f"Failed to initialize production services: {e}")
        logger.info("Continuing with legacy configuration")

    # Initialize WebSocket services (Sprint 3)
    from .api.websocket_endpoints import initialize_websocket_services, cleanup_websocket_services
    await initialize_websocket_services()

    yield

    # Cleanup services
    try:
        from .core.services import reset_service_container
        reset_service_container()
        logger.info("Service container cleaned up")
    except Exception as e:
        logger.warning(f"Service cleanup failed: {e}")

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
settings = get_settings()
cors_origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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


# Legacy health endpoint - kept for backward compatibility
@app.get("/health-legacy")
async def legacy_health_check(settings: Settings = Depends(get_settings)):
    """Legacy health check endpoint for backward compatibility"""
    health_status = {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "environment": settings.ENVIRONMENT
    }

    # Add database health check if available
    try:
        from .database import get_database
        db = get_database()
        if db and db.is_connected:
            db_health = await db.health_check()
            health_status["database"] = db_health
    except Exception as e:
        health_status["database"] = {"status": "error", "error": str(e)}

    return health_status


# Legacy ready endpoint - kept for backward compatibility
@app.get("/ready-legacy")
async def legacy_readiness_check(settings: Settings = Depends(get_settings)):
    """Legacy readiness check for backward compatibility"""
    # Check if required external services are accessible
    checks = {
        "crm_configured": bool(settings.CRM_BASE_URL),
        "platform_configured": bool(settings.PLATFORM_BASE_URL),
        "document_source_configured": bool(settings.LIVING_DOC_ID)
    }

    # Additional service validation if production services are available
    try:
        from .core.services import validate_all_services
        service_validation = await validate_all_services()
        checks["services_validated"] = all(
            result.get("status") in ["connected", "configured"]
            for result in service_validation.values()
        )
    except Exception as e:
        logger.warning(f"Service validation failed in readiness check: {e}")
        checks["services_validated"] = False

    all_ready = all(checks.values())

    return {
        "ready": all_ready,
        "checks": checks
    }


@app.get("/api/v1/services/status")
async def service_status():
    """Get status of all configured services"""
    try:
        from .core.services import validate_all_services, get_service_info

        validation_results = await validate_all_services()
        service_info = await get_service_info()

        return {
            "status": "success",
            "service_info": service_info,
            "validation_results": validation_results
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/api/v1/database/status")
async def database_status():
    """Get database connection status and statistics"""
    try:
        from .database import get_database
        from .database.config import get_database_settings

        db = get_database()
        settings = get_database_settings()

        # Get health check
        health = await db.health_check()

        # Get configuration info
        config_info = {
            "database_type": settings.DATABASE_TYPE.value,
            "database_name": settings.DATABASE_NAME,
            "pool_size": settings.DATABASE_POOL_SIZE,
            "pool_max_overflow": settings.DATABASE_POOL_MAX_OVERFLOW,
            "ssl_mode": settings.DATABASE_SSL_MODE,
            "auto_migrate": settings.DATABASE_AUTO_MIGRATE,
            "use_read_replica": settings.DATABASE_USE_READ_REPLICA
        }

        return {
            "status": "success",
            "health": health,
            "configuration": config_info
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Database not configured or unavailable"
        }


@app.post("/api/v1/database/migrate")
async def run_database_migrations():
    """Run database migrations (requires admin privileges)"""
    try:
        from .database import get_database

        db = get_database()
        await db.run_migrations()

        return {
            "status": "success",
            "message": "Migrations completed successfully"
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to run migrations"
        }


@app.post("/api/v1/services/validate")
async def validate_services():
    """Validate all service connections"""
    try:
        from .core.services import validate_all_services

        results = await validate_all_services()

        all_services_ok = all(
            result.get("status") in ["connected", "configured"]
            for result in results.values()
        )

        return {
            "status": "success" if all_services_ok else "partial_failure",
            "all_services_ok": all_services_ok,
            "results": results
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "results": {}
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

# Include comprehensive health check endpoints
from .api import health_endpoints
app.include_router(health_endpoints.router)