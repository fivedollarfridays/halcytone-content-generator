"""
Prometheus metrics collection for Halcytone Content Generator
"""
import time
import functools
from typing import Dict, Optional, Any, Callable
from contextlib import contextmanager
from prometheus_client import (
    Counter, Histogram, Gauge, Info, Enum,
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry, REGISTRY
)
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

# Global metrics registry
_registry: Optional[CollectorRegistry] = None

# Application metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

http_request_size_bytes = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint']
)

http_response_size_bytes = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint']
)

# Application-specific metrics
app_info = Info(
    'app_info',
    'Application information'
)

app_uptime_seconds = Gauge(
    'app_uptime_seconds',
    'Application uptime in seconds'
)

app_version_info = Info(
    'app_version_info',
    'Application version information'
)

app_health_status = Enum(
    'app_health_status',
    'Application health status',
    states=['healthy', 'degraded', 'unhealthy', 'unknown']
)

app_component_health = Gauge(
    'app_component_health',
    'Component health status (1=healthy, 0=unhealthy)',
    ['component', 'service', 'environment']
)

app_memory_usage_percent = Gauge(
    'app_memory_usage_percent',
    'Memory usage percentage'
)

app_cpu_usage_percent = Gauge(
    'app_cpu_usage_percent',
    'CPU usage percentage'
)

app_disk_usage_percent = Gauge(
    'app_disk_usage_percent',
    'Disk usage percentage'
)

# Content generation metrics
content_generation_requests_total = Counter(
    'content_generation_requests_total',
    'Total content generation requests',
    ['type', 'status']
)

content_generation_duration_seconds = Histogram(
    'content_generation_duration_seconds',
    'Content generation duration in seconds',
    ['type']
)

content_generation_successes_total = Counter(
    'content_generation_successes_total',
    'Successful content generations',
    ['type', 'template']
)

content_generation_failures_total = Counter(
    'content_generation_failures_total',
    'Failed content generations',
    ['type', 'error_type']
)

content_generation_quality_score = Histogram(
    'content_generation_quality_score',
    'Content generation quality scores',
    ['type']
)

# External API metrics
external_api_requests_total = Counter(
    'external_api_requests_total',
    'Total external API requests',
    ['service', 'endpoint', 'status']
)

external_api_duration_seconds = Histogram(
    'external_api_duration_seconds',
    'External API request duration in seconds',
    ['service', 'endpoint']
)

external_api_failures_total = Counter(
    'external_api_failures_total',
    'External API failures',
    ['service', 'error_type']
)

# Database metrics
database_connections_active = Gauge(
    'database_connections_active',
    'Active database connections'
)

database_connections_idle = Gauge(
    'database_connections_idle',
    'Idle database connections'
)

database_query_duration_seconds = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type']
)

database_query_total = Counter(
    'database_query_total',
    'Total database queries',
    ['query_type', 'status']
)

# Cache metrics
cache_operations_total = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'status']
)

cache_hit_rate = Gauge(
    'cache_hit_rate',
    'Cache hit rate percentage'
)

cache_size_bytes = Gauge(
    'cache_size_bytes',
    'Cache size in bytes'
)

# Business metrics
active_users_total = Gauge(
    'active_users_total',
    'Total active users'
)

api_key_usage_total = Counter(
    'api_key_usage_total',
    'API key usage',
    ['api_key_hash', 'endpoint']
)

batch_processing_queue_size = Gauge(
    'batch_processing_queue_size',
    'Batch processing queue size'
)

batch_processing_duration_seconds = Histogram(
    'batch_processing_duration_seconds',
    'Batch processing duration in seconds',
    ['batch_type']
)


def setup_metrics(app_info_dict: Dict[str, str]) -> CollectorRegistry:
    """Setup metrics with application information"""
    global _registry

    _registry = REGISTRY

    # Set application info
    app_info.info(app_info_dict)

    logger.info("Metrics setup complete")
    return _registry


def get_metrics_registry() -> CollectorRegistry:
    """Get the metrics registry"""
    return _registry or REGISTRY


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP metrics"""

    def __init__(self, app, app_name: str = "halcytone-content-generator"):
        super().__init__(app)
        self.app_name = app_name
        self.start_time = time.time()

    async def dispatch(self, request: Request, call_next):
        # Skip metrics collection for metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        start_time = time.time()

        # Get request size
        request_size = int(request.headers.get('content-length', 0))

        # Process request
        response = await call_next(request)

        # Calculate metrics
        duration = time.time() - start_time
        method = request.method
        endpoint = self._normalize_endpoint(request.url.path)
        status = str(response.status_code)

        # Response size
        response_size = 0
        if hasattr(response, 'body'):
            response_size = len(response.body)
        elif 'content-length' in response.headers:
            response_size = int(response.headers['content-length'])

        # Update metrics
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()

        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

        if request_size > 0:
            http_request_size_bytes.labels(
                method=method,
                endpoint=endpoint
            ).observe(request_size)

        if response_size > 0:
            http_response_size_bytes.labels(
                method=method,
                endpoint=endpoint
            ).observe(response_size)

        # Update uptime
        app_uptime_seconds.set(time.time() - self.start_time)

        return response

    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path for metrics"""
        # Replace dynamic parts with placeholders
        parts = path.split('/')
        normalized_parts = []

        for part in parts:
            if not part:
                continue

            # Replace UUIDs, IDs, and other dynamic parts
            if (part.isdigit() or
                len(part) == 36 and part.count('-') == 4 or  # UUID
                part.startswith('temp_') or
                len(part) > 20):  # Likely dynamic content
                normalized_parts.append('{id}')
            else:
                normalized_parts.append(part)

        return '/' + '/'.join(normalized_parts) if normalized_parts else '/'


# Convenience function for middleware
def metrics_middleware(app_name: str = "halcytone-content-generator") -> MetricsMiddleware:
    """Create metrics middleware"""
    return MetricsMiddleware(None, app_name)


@contextmanager
def track_request(method: str, endpoint: str):
    """Context manager to track request metrics"""
    start_time = time.time()
    try:
        yield
        status = "success"
    except Exception as e:
        status = "error"
        logger.error(f"Request failed: {e}")
        raise
    finally:
        duration = time.time() - start_time
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()


@contextmanager
def track_content_generation(content_type: str, template: Optional[str] = None):
    """Context manager to track content generation metrics"""
    start_time = time.time()
    try:
        yield
        # Success
        content_generation_successes_total.labels(
            type=content_type,
            template=template or "default"
        ).inc()
        status = "success"
    except Exception as e:
        # Failure
        error_type = type(e).__name__
        content_generation_failures_total.labels(
            type=content_type,
            error_type=error_type
        ).inc()
        status = "error"
        raise
    finally:
        duration = time.time() - start_time
        content_generation_duration_seconds.labels(
            type=content_type
        ).observe(duration)

        content_generation_requests_total.labels(
            type=content_type,
            status=status
        ).inc()


@contextmanager
def track_external_api_call(service: str, endpoint: str):
    """Context manager to track external API call metrics"""
    start_time = time.time()
    try:
        yield
        status = "success"
    except Exception as e:
        error_type = type(e).__name__
        external_api_failures_total.labels(
            service=service,
            error_type=error_type
        ).inc()
        status = "error"
        raise
    finally:
        duration = time.time() - start_time
        external_api_duration_seconds.labels(
            service=service,
            endpoint=endpoint
        ).observe(duration)

        external_api_requests_total.labels(
            service=service,
            endpoint=endpoint,
            status=status
        ).inc()


def update_system_metrics():
    """Update system-level metrics"""
    try:
        import psutil
        import os

        # Memory metrics
        memory = psutil.virtual_memory()
        app_memory_usage_percent.set(memory.percent)

        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        app_cpu_usage_percent.set(cpu_percent)

        # Disk metrics
        disk = psutil.disk_usage('/')
        app_disk_usage_percent.set(disk.percent)

        # Process-specific metrics
        process = psutil.Process(os.getpid())

        # Database connections (if available)
        try:
            from ..database import get_database
            db = get_database()
            if db and hasattr(db, 'pool'):
                pool = db.pool
                database_connections_active.set(pool.size - pool.checkedin())
                database_connections_idle.set(pool.checkedin())
        except:
            pass

        # Cache metrics (if available)
        try:
            from ..core.cache import get_cache_manager
            cache_manager = get_cache_manager()
            if cache_manager and hasattr(cache_manager, 'get_stats'):
                stats = cache_manager.get_stats()
                if 'hit_rate' in stats:
                    cache_hit_rate.set(stats['hit_rate'])
                if 'size' in stats:
                    cache_size_bytes.set(stats['size'])
        except:
            pass

    except ImportError:
        logger.warning("psutil not available for system metrics")
    except Exception as e:
        logger.error(f"Error updating system metrics: {e}")


def record_content_quality_score(content_type: str, score: float):
    """Record content quality score"""
    content_generation_quality_score.labels(type=content_type).observe(score)


def track_api_key_usage(api_key_hash: str, endpoint: str):
    """Track API key usage"""
    api_key_usage_total.labels(
        api_key_hash=api_key_hash,
        endpoint=endpoint
    ).inc()


def update_health_metrics(component_health: Dict[str, Any], service: str, environment: str):
    """Update component health metrics"""
    for component, status in component_health.items():
        health_value = 1 if status.get('status') == 'healthy' else 0
        app_component_health.labels(
            component=component,
            service=service,
            environment=environment
        ).set(health_value)


def track_database_query(query_type: str, duration: float, success: bool):
    """Track database query metrics"""
    database_query_duration_seconds.labels(query_type=query_type).observe(duration)
    database_query_total.labels(
        query_type=query_type,
        status="success" if success else "error"
    ).inc()


def track_cache_operation(operation: str, success: bool):
    """Track cache operation metrics"""
    cache_operations_total.labels(
        operation=operation,
        status="success" if success else "error"
    ).inc()


def update_business_metrics(active_users: int, queue_size: int):
    """Update business-related metrics"""
    active_users_total.set(active_users)
    batch_processing_queue_size.set(queue_size)


def metrics_handler() -> Response:
    """Handler for /metrics endpoint"""
    try:
        # Update system metrics before serving
        update_system_metrics()

        # Generate metrics
        metrics_data = generate_latest(get_metrics_registry())

        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return Response(
            content=f"Error generating metrics: {str(e)}",
            status_code=500
        )


def metrics_decorator(metric_type: str = "request"):
    """Decorator to automatically track metrics"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if metric_type == "content_generation":
                content_type = kwargs.get('content_type', 'unknown')
                with track_content_generation(content_type):
                    return await func(*args, **kwargs)
            elif metric_type == "external_api":
                service = kwargs.get('service', 'unknown')
                endpoint = kwargs.get('endpoint', 'unknown')
                with track_external_api_call(service, endpoint):
                    return await func(*args, **kwargs)
            else:
                # Default request tracking
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if metric_type == "content_generation":
                content_type = kwargs.get('content_type', 'unknown')
                with track_content_generation(content_type):
                    return func(*args, **kwargs)
            elif metric_type == "external_api":
                service = kwargs.get('service', 'unknown')
                endpoint = kwargs.get('endpoint', 'unknown')
                with track_external_api_call(service, endpoint):
                    return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator