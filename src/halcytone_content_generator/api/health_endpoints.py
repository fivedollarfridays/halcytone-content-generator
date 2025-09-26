"""
Health check endpoints for monitoring
"""
from fastapi import APIRouter, Depends, Response, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import time
import os
import psutil
from datetime import datetime

from ..config import Settings, get_settings
from ..health import (
    get_health_manager,
    HealthStatus,
    HealthResponse,
    DetailedHealthResponse,
    ReadinessResponse,
    ReadinessCheck,
    LivenessResponse,
    ComponentStatus
)

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    response: Response,
    settings: Settings = Depends(get_settings)
) -> HealthResponse:
    """
    Basic health check endpoint

    Returns:
    - 200: Service is healthy
    - 503: Service is unhealthy
    """
    start_time = time.time()
    health_manager = get_health_manager()

    # Get overall status
    overall_status = health_manager.get_overall_status()

    # Set response status code based on health
    if overall_status == HealthStatus.UNHEALTHY:
        response.status_code = 503
    elif overall_status == HealthStatus.DEGRADED:
        response.status_code = 200  # Still return 200 for degraded
    else:
        response.status_code = 200

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        service=settings.SERVICE_NAME,
        version=settings.get("VERSION", "0.1.0"),
        environment=settings.ENVIRONMENT,
        uptime_seconds=health_manager.get_uptime_seconds()
    )


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(
    response: Response,
    check_database: bool = True,
    check_cache: bool = True,
    check_external: bool = True,
    check_system: bool = True,
    settings: Settings = Depends(get_settings)
) -> DetailedHealthResponse:
    """
    Detailed health check with component status

    Query parameters:
    - check_database: Check database connectivity
    - check_cache: Check cache connectivity
    - check_external: Check external services
    - check_system: Check system resources (CPU, memory, disk)

    Returns:
    - 200: Service is healthy or degraded
    - 503: Service is unhealthy
    """
    start_time = time.time()
    health_manager = get_health_manager()

    # Determine which checks to run
    checks_to_run = []
    if check_database:
        checks_to_run.append("database")
    if check_cache:
        checks_to_run.append("cache")
    if check_external:
        checks_to_run.append("external_services")
    if check_system:
        checks_to_run.extend(["disk_space", "memory", "cpu"])

    # Run selected checks
    components = {}
    warnings = []
    errors = []
    checks_passed = 0
    checks_failed = 0

    for check_name in checks_to_run:
        try:
            result = await health_manager.run_check(check_name)

            components[check_name] = ComponentStatus(
                name=check_name,
                status=result.status,
                message=result.message,
                response_time_ms=result.response_time_ms,
                last_check=datetime.utcnow(),
                metadata=result.metadata or {}
            )

            if result.status == HealthStatus.HEALTHY:
                checks_passed += 1
            elif result.status == HealthStatus.DEGRADED:
                checks_passed += 1
                if result.message:
                    warnings.append(f"{check_name}: {result.message}")
            else:
                checks_failed += 1
                if result.error:
                    errors.append(f"{check_name}: {result.error}")
                elif result.message:
                    errors.append(f"{check_name}: {result.message}")

        except Exception as e:
            checks_failed += 1
            errors.append(f"{check_name}: {str(e)}")
            components[check_name] = ComponentStatus(
                name=check_name,
                status=HealthStatus.UNKNOWN,
                message=f"Check failed: {str(e)}",
                last_check=datetime.utcnow()
            )

    # Calculate overall status
    overall_status = health_manager.get_overall_status()
    response_time = (time.time() - start_time) * 1000

    # Set response status code
    if overall_status == HealthStatus.UNHEALTHY:
        response.status_code = 503
    else:
        response.status_code = 200

    return DetailedHealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        service=settings.SERVICE_NAME,
        version=settings.get("VERSION", "0.1.0"),
        environment=settings.ENVIRONMENT,
        uptime_seconds=health_manager.get_uptime_seconds(),
        components=components,
        checks_passed=checks_passed,
        checks_failed=checks_failed,
        checks_total=checks_passed + checks_failed,
        response_time_ms=response_time,
        warnings=warnings,
        errors=errors
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check(
    response: Response,
    settings: Settings = Depends(get_settings)
) -> ReadinessResponse:
    """
    Readiness check for deployment orchestration

    Checks if the service is ready to handle requests.
    Used by Kubernetes and load balancers.

    Returns:
    - 200: Service is ready
    - 503: Service is not ready
    """
    checks = []
    passed = 0
    failed = 0

    # Check configuration
    config_check = ReadinessCheck(
        name="configuration",
        ready=bool(settings.CRM_BASE_URL and settings.PLATFORM_BASE_URL),
        message="Required configuration present",
        required=True
    )
    checks.append(config_check)
    if config_check.ready:
        passed += 1
    else:
        failed += 1

    # Check database if configured
    try:
        from ..database import get_database
        db = get_database()
        if db:
            health = await db.health_check()
            db_ready = health.get("status") == "connected"
            db_check = ReadinessCheck(
                name="database",
                ready=db_ready,
                message=health.get("message", "Database check complete"),
                required=settings.ENVIRONMENT == "production"
            )
            checks.append(db_check)
            if db_check.ready:
                passed += 1
            else:
                failed += 1
    except:
        # Database not configured, which is ok for development
        if settings.ENVIRONMENT != "development":
            checks.append(ReadinessCheck(
                name="database",
                ready=False,
                message="Database not available",
                required=True
            ))
            failed += 1

    # Check external services
    try:
        from ..core.services import validate_all_services
        service_results = await validate_all_services()

        for service_name, result in service_results.items():
            service_ready = result.get("status") in ["connected", "configured", "mocked"]
            service_check = ReadinessCheck(
                name=f"service_{service_name}",
                ready=service_ready,
                message=result.get("message", ""),
                required=settings.ENVIRONMENT == "production"
            )
            checks.append(service_check)
            if service_check.ready:
                passed += 1
            else:
                failed += 1
    except Exception as e:
        checks.append(ReadinessCheck(
            name="services",
            ready=False,
            message=f"Service validation failed: {str(e)}",
            required=False
        ))
        failed += 1

    # Check if living document is configured
    doc_check = ReadinessCheck(
        name="living_document",
        ready=bool(settings.LIVING_DOC_ID),
        message="Living document configured",
        required=settings.ENVIRONMENT == "production"
    )
    checks.append(doc_check)
    if doc_check.ready:
        passed += 1
    else:
        failed += 1

    # Determine overall readiness
    required_checks_passed = all(
        check.ready for check in checks if check.required
    )
    overall_ready = required_checks_passed

    # Set response status code
    if not overall_ready:
        response.status_code = 503

    return ReadinessResponse(
        ready=overall_ready,
        timestamp=datetime.utcnow(),
        checks=checks,
        total_checks=len(checks),
        passed_checks=passed,
        failed_checks=failed,
        required_checks_passed=required_checks_passed
    )


@router.get("/live", response_model=LivenessResponse)
@router.get("/liveness", response_model=LivenessResponse)
async def liveness_probe(response: Response) -> LivenessResponse:
    """
    Liveness probe endpoint

    Simple check to verify the service process is alive and responding.
    Used by Kubernetes to determine if the pod should be restarted.

    Returns:
    - 200: Service is alive
    - 503: Service should be restarted
    """
    try:
        # Get process information
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_usage_mb = memory_info.rss / (1024 * 1024)

        # Check if we're in a bad state
        cpu_percent = process.cpu_percent()
        if cpu_percent > 95:
            response.status_code = 503
            return LivenessResponse(
                alive=False,
                timestamp=datetime.utcnow(),
                pid=os.getpid(),
                memory_usage_mb=memory_usage_mb,
                cpu_percent=cpu_percent,
                thread_count=process.num_threads()
            )

        # Check memory usage
        if memory_usage_mb > 2048:  # If using more than 2GB
            response.status_code = 503
            return LivenessResponse(
                alive=False,
                timestamp=datetime.utcnow(),
                pid=os.getpid(),
                memory_usage_mb=memory_usage_mb,
                cpu_percent=cpu_percent,
                thread_count=process.num_threads()
            )

        # Service is alive
        return LivenessResponse(
            alive=True,
            timestamp=datetime.utcnow(),
            pid=os.getpid(),
            memory_usage_mb=memory_usage_mb,
            cpu_percent=cpu_percent,
            thread_count=process.num_threads()
        )

    except Exception as e:
        # If we can't check, assume we're alive but log the error
        import logging
        logging.error(f"Liveness check error: {e}")
        return LivenessResponse(
            alive=True,
            timestamp=datetime.utcnow(),
            pid=os.getpid()
        )


@router.get("/startup")
async def startup_probe(response: Response) -> Dict[str, Any]:
    """
    Startup probe endpoint

    Used by Kubernetes to know when a container has started successfully.
    Allows for longer startup time without failing liveness checks.

    Returns:
    - 200: Startup complete
    - 503: Still starting up
    """
    health_manager = get_health_manager()
    uptime = health_manager.get_uptime_seconds()

    # Check if we've been up for at least 10 seconds
    if uptime < 10:
        response.status_code = 503
        return {
            "started": False,
            "uptime_seconds": uptime,
            "message": "Service is starting up"
        }

    # Run basic checks
    try:
        # Just check if we can import our main modules
        from ..core.services import get_service_container
        from ..database import get_database

        return {
            "started": True,
            "uptime_seconds": uptime,
            "message": "Service startup complete",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        response.status_code = 503
        return {
            "started": False,
            "uptime_seconds": uptime,
            "message": f"Startup incomplete: {str(e)}"
        }


@router.get("/metrics")
async def metrics_endpoint(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Prometheus-compatible metrics endpoint

    Returns application metrics in a format that can be scraped by Prometheus.
    """
    health_manager = get_health_manager()
    metrics = await health_manager.get_system_metrics()

    # Format for Prometheus
    prometheus_metrics = []

    # Uptime metric
    uptime = health_manager.get_uptime_seconds()
    prometheus_metrics.append(f"# HELP app_uptime_seconds Application uptime in seconds")
    prometheus_metrics.append(f"# TYPE app_uptime_seconds gauge")
    prometheus_metrics.append(f'app_uptime_seconds{{service="{settings.SERVICE_NAME}",environment="{settings.ENVIRONMENT}"}} {uptime}')

    # Memory metrics
    prometheus_metrics.append(f"# HELP app_memory_usage_percent Memory usage percentage")
    prometheus_metrics.append(f"# TYPE app_memory_usage_percent gauge")
    prometheus_metrics.append(f'app_memory_usage_percent{{service="{settings.SERVICE_NAME}",environment="{settings.ENVIRONMENT}"}} {metrics.memory_usage_percent}')

    # CPU metrics
    prometheus_metrics.append(f"# HELP app_cpu_usage_percent CPU usage percentage")
    prometheus_metrics.append(f"# TYPE app_cpu_usage_percent gauge")
    prometheus_metrics.append(f'app_cpu_usage_percent{{service="{settings.SERVICE_NAME}",environment="{settings.ENVIRONMENT}"}} {metrics.cpu_usage_percent}')

    # Disk metrics
    prometheus_metrics.append(f"# HELP app_disk_usage_percent Disk usage percentage")
    prometheus_metrics.append(f"# TYPE app_disk_usage_percent gauge")
    prometheus_metrics.append(f'app_disk_usage_percent{{service="{settings.SERVICE_NAME}",environment="{settings.ENVIRONMENT}"}} {metrics.disk_usage_percent}')

    # Component health metrics
    for component_name, component in health_manager.components.items():
        status_value = 1 if component.status == HealthStatus.HEALTHY else 0
        prometheus_metrics.append(f"# HELP app_component_health Component health status (1=healthy, 0=unhealthy)")
        prometheus_metrics.append(f"# TYPE app_component_health gauge")
        prometheus_metrics.append(f'app_component_health{{component="{component_name}",service="{settings.SERVICE_NAME}",environment="{settings.ENVIRONMENT}"}} {status_value}')

    return Response(
        content="\n".join(prometheus_metrics),
        media_type="text/plain; version=0.0.4"
    )


@router.post("/health/check/{component}")
async def trigger_component_check(
    component: str,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Manually trigger a health check for a specific component

    This endpoint is useful for debugging and monitoring specific components.
    """
    health_manager = get_health_manager()

    if component not in health_manager.checks:
        raise HTTPException(
            status_code=404,
            detail=f"Component '{component}' not found. Available components: {list(health_manager.checks.keys())}"
        )

    result = await health_manager.run_check(component)

    return {
        "component": component,
        "status": result.status,
        "message": result.message,
        "response_time_ms": result.response_time_ms,
        "metadata": result.metadata,
        "error": result.error,
        "timestamp": datetime.utcnow().isoformat()
    }