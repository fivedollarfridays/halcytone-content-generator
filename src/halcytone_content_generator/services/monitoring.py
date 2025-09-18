"""
Monitoring and telemetry service for distributed tracing
"""
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from contextlib import contextmanager
import logging
import time
import json
from enum import Enum
from collections import defaultdict
import asyncio
from functools import wraps

# OpenTelemetry imports (optional if installed)
try:
    from opentelemetry import trace, metrics
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    HAS_OTEL = True
except ImportError:
    HAS_OTEL = False

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of monitoring events"""
    API_REQUEST = "api_request"
    API_RESPONSE = "api_response"
    CONTENT_GENERATED = "content_generated"
    EMAIL_SENT = "email_sent"
    CONTENT_PUBLISHED = "content_published"
    DOCUMENT_FETCHED = "document_fetched"
    ERROR = "error"
    WARNING = "warning"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    RATE_LIMIT = "rate_limit"
    CIRCUIT_BREAKER = "circuit_breaker"


@dataclass
class MonitoringEvent:
    """Monitoring event data"""
    event_type: EventType
    service: str
    operation: str
    timestamp: datetime
    duration_ms: Optional[float] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    success: bool = True


@dataclass
class HealthStatus:
    """Service health status"""
    service: str
    status: str  # healthy, degraded, unhealthy
    last_check: datetime
    uptime_seconds: float
    error_rate: float
    avg_response_time_ms: float
    active_connections: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class MonitoringService:
    """
    Centralized monitoring and telemetry service
    """

    def __init__(self, service_name: str = "content-generator"):
        """
        Initialize monitoring service

        Args:
            service_name: Name of this service
        """
        self.service_name = service_name
        self.events: List[MonitoringEvent] = []
        self.metrics = defaultdict(lambda: defaultdict(float))
        self.health_checks: Dict[str, Callable] = {}
        self.start_time = datetime.now()

        # Initialize OpenTelemetry if available
        self.tracer = None
        self.meter = None
        self.propagator = None

        if HAS_OTEL:
            self._initialize_telemetry()

        # Metrics collectors
        self.operation_counters = defaultdict(int)
        self.operation_durations = defaultdict(list)
        self.error_counters = defaultdict(int)

        # Performance thresholds
        self.thresholds = {
            'response_time_ms': 1000,  # 1 second
            'error_rate_percent': 5,    # 5%
            'cache_hit_rate_percent': 80  # 80%
        }

    def _initialize_telemetry(self):
        """Initialize OpenTelemetry components"""
        if not HAS_OTEL:
            return

        # Setup tracing
        resource = Resource.create({"service.name": self.service_name})
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)
        self.tracer = trace.get_tracer(__name__)

        # Setup metrics
        reader = PrometheusMetricReader()
        provider = MeterProvider(resource=resource, metric_readers=[reader])
        metrics.set_meter_provider(provider)
        self.meter = metrics.get_meter(__name__)

        # Setup context propagation
        self.propagator = TraceContextTextMapPropagator()

        # Create metrics
        self._create_metrics()

        logger.info("OpenTelemetry initialized for monitoring")

    def _create_metrics(self):
        """Create OpenTelemetry metrics"""
        if not self.meter:
            return

        # Counters
        self.request_counter = self.meter.create_counter(
            "content_generator_requests",
            description="Total number of requests"
        )

        self.error_counter = self.meter.create_counter(
            "content_generator_errors",
            description="Total number of errors"
        )

        # Histograms
        self.duration_histogram = self.meter.create_histogram(
            "content_generator_duration_ms",
            description="Request duration in milliseconds"
        )

        # Gauges
        self.active_requests = self.meter.create_up_down_counter(
            "content_generator_active_requests",
            description="Number of active requests"
        )

    def record_event(
        self,
        event_type: EventType,
        operation: str,
        correlation_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        success: bool = True
    ):
        """
        Record a monitoring event

        Args:
            event_type: Type of event
            operation: Operation name
            correlation_id: Request correlation ID
            duration_ms: Operation duration
            metadata: Additional metadata
            error: Error message if any
            success: Whether operation succeeded
        """
        event = MonitoringEvent(
            event_type=event_type,
            service=self.service_name,
            operation=operation,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            correlation_id=correlation_id,
            metadata=metadata or {},
            error=error,
            success=success
        )

        self.events.append(event)

        # Update metrics
        self.operation_counters[operation] += 1
        if duration_ms:
            self.operation_durations[operation].append(duration_ms)
        if not success:
            self.error_counters[operation] += 1

        # Record in OpenTelemetry
        if HAS_OTEL and self.meter:
            self.request_counter.add(1, {"operation": operation})
            if duration_ms:
                self.duration_histogram.record(duration_ms, {"operation": operation})
            if not success:
                self.error_counter.add(1, {"operation": operation})

        # Log significant events
        if not success:
            logger.error(f"Operation failed: {operation} - {error}")
        elif duration_ms and duration_ms > self.thresholds['response_time_ms']:
            logger.warning(f"Slow operation: {operation} took {duration_ms}ms")

    @contextmanager
    def trace_operation(
        self,
        operation: str,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager for tracing operations

        Args:
            operation: Operation name
            correlation_id: Request correlation ID
            metadata: Additional metadata
        """
        start_time = time.time()
        span = None

        # Start OpenTelemetry span
        if HAS_OTEL and self.tracer:
            span = self.tracer.start_span(operation)
            if correlation_id:
                span.set_attribute("correlation_id", correlation_id)
            if metadata:
                for key, value in metadata.items():
                    span.set_attribute(f"metadata.{key}", str(value))

        try:
            if HAS_OTEL and self.meter:
                self.active_requests.add(1, {"operation": operation})
            yield span

            # Record success
            duration_ms = (time.time() - start_time) * 1000
            self.record_event(
                EventType.API_REQUEST,
                operation,
                correlation_id,
                duration_ms,
                metadata,
                success=True
            )

            if span:
                span.set_status(Status(StatusCode.OK))

        except Exception as e:
            # Record error
            duration_ms = (time.time() - start_time) * 1000
            self.record_event(
                EventType.ERROR,
                operation,
                correlation_id,
                duration_ms,
                metadata,
                error=str(e),
                success=False
            )

            if span:
                span.set_status(Status(StatusCode.ERROR, str(e)))
            raise

        finally:
            if HAS_OTEL and self.meter:
                self.active_requests.add(-1, {"operation": operation})
            if span:
                span.end()

    def trace_async(self, operation: str):
        """
        Decorator for tracing async functions

        Args:
            operation: Operation name
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                correlation_id = kwargs.get('correlation_id')
                with self.trace_operation(operation, correlation_id):
                    return await func(*args, **kwargs)
            return wrapper
        return decorator

    def trace_sync(self, operation: str):
        """
        Decorator for tracing sync functions

        Args:
            operation: Operation name
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                correlation_id = kwargs.get('correlation_id')
                with self.trace_operation(operation, correlation_id):
                    return func(*args, **kwargs)
            return wrapper
        return decorator

    def get_metrics(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        Get metrics for an operation or all operations

        Args:
            operation: Optional specific operation

        Returns:
            Metrics dictionary
        """
        if operation:
            total_calls = self.operation_counters.get(operation, 0)
            errors = self.error_counters.get(operation, 0)
            durations = self.operation_durations.get(operation, [])

            return {
                'operation': operation,
                'total_calls': total_calls,
                'error_count': errors,
                'error_rate': (errors / total_calls * 100) if total_calls > 0 else 0,
                'avg_duration_ms': sum(durations) / len(durations) if durations else 0,
                'min_duration_ms': min(durations) if durations else 0,
                'max_duration_ms': max(durations) if durations else 0,
                'p95_duration_ms': self._calculate_percentile(durations, 95) if durations else 0,
                'p99_duration_ms': self._calculate_percentile(durations, 99) if durations else 0
            }
        else:
            # Aggregate metrics
            total_calls = sum(self.operation_counters.values())
            total_errors = sum(self.error_counters.values())
            all_durations = []
            for durations in self.operation_durations.values():
                all_durations.extend(durations)

            return {
                'total_calls': total_calls,
                'total_errors': total_errors,
                'error_rate': (total_errors / total_calls * 100) if total_calls > 0 else 0,
                'avg_duration_ms': sum(all_durations) / len(all_durations) if all_durations else 0,
                'operations': {
                    op: self.get_metrics(op)
                    for op in self.operation_counters.keys()
                },
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds()
            }

    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def register_health_check(self, name: str, check_func: Callable):
        """
        Register a health check function

        Args:
            name: Health check name
            check_func: Function that returns health status
        """
        self.health_checks[name] = check_func

    async def get_health_status(self) -> HealthStatus:
        """
        Get overall service health status

        Returns:
            Health status
        """
        # Calculate metrics
        metrics = self.get_metrics()
        error_rate = metrics.get('error_rate', 0)
        avg_response_time = metrics.get('avg_duration_ms', 0)
        uptime = metrics.get('uptime_seconds', 0)

        # Run health checks
        health_check_results = {}
        for name, check_func in self.health_checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    health_check_results[name] = await check_func()
                else:
                    health_check_results[name] = check_func()
            except Exception as e:
                health_check_results[name] = {'status': 'unhealthy', 'error': str(e)}

        # Determine overall status
        if error_rate > self.thresholds['error_rate_percent']:
            status = 'unhealthy'
        elif avg_response_time > self.thresholds['response_time_ms']:
            status = 'degraded'
        elif any(r.get('status') == 'unhealthy' for r in health_check_results.values()):
            status = 'unhealthy'
        else:
            status = 'healthy'

        return HealthStatus(
            service=self.service_name,
            status=status,
            last_check=datetime.now(),
            uptime_seconds=uptime,
            error_rate=error_rate,
            avg_response_time_ms=avg_response_time,
            active_connections=len([e for e in self.events if e.timestamp > datetime.now() - timedelta(minutes=1)]),
            metadata={
                'health_checks': health_check_results,
                'thresholds': self.thresholds
            }
        )

    def get_recent_events(
        self,
        minutes: int = 5,
        event_type: Optional[EventType] = None
    ) -> List[MonitoringEvent]:
        """
        Get recent events

        Args:
            minutes: Number of minutes to look back
            event_type: Optional event type filter

        Returns:
            List of recent events
        """
        cutoff = datetime.now() - timedelta(minutes=minutes)
        events = [e for e in self.events if e.timestamp > cutoff]

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        return events

    def export_metrics_prometheus(self) -> str:
        """
        Export metrics in Prometheus format

        Returns:
            Prometheus formatted metrics
        """
        lines = []
        metrics = self.get_metrics()

        # Overall metrics
        lines.append(f'# HELP content_generator_total_calls Total number of API calls')
        lines.append(f'# TYPE content_generator_total_calls counter')
        lines.append(f'content_generator_total_calls {metrics["total_calls"]}')

        lines.append(f'# HELP content_generator_error_rate Error rate percentage')
        lines.append(f'# TYPE content_generator_error_rate gauge')
        lines.append(f'content_generator_error_rate {metrics["error_rate"]}')

        lines.append(f'# HELP content_generator_avg_duration Average duration in ms')
        lines.append(f'# TYPE content_generator_avg_duration gauge')
        lines.append(f'content_generator_avg_duration {metrics["avg_duration_ms"]}')

        # Per-operation metrics
        for op_name, op_metrics in metrics.get('operations', {}).items():
            safe_name = op_name.replace('-', '_').replace(' ', '_')

            lines.append(f'# HELP {safe_name}_calls Total calls for {op_name}')
            lines.append(f'# TYPE {safe_name}_calls counter')
            lines.append(f'{safe_name}_calls {op_metrics["total_calls"]}')

            lines.append(f'# HELP {safe_name}_errors Total errors for {op_name}')
            lines.append(f'# TYPE {safe_name}_errors counter')
            lines.append(f'{safe_name}_errors {op_metrics["error_count"]}')

        return '\n'.join(lines)

    def clear_old_events(self, days: int = 7):
        """
        Clear events older than specified days

        Args:
            days: Number of days to keep
        """
        cutoff = datetime.now() - timedelta(days=days)
        self.events = [e for e in self.events if e.timestamp > cutoff]
        logger.info(f"Cleared events older than {days} days")


# Global monitoring instance
monitoring_service = MonitoringService()


# FastAPI integration helpers
def setup_monitoring_middleware(app):
    """
    Setup monitoring middleware for FastAPI

    Args:
        app: FastAPI application instance
    """
    from fastapi import Request
    import time

    @app.middleware("http")
    async def monitoring_middleware(request: Request, call_next):
        """Track all HTTP requests"""
        start_time = time.time()
        correlation_id = request.headers.get("X-Correlation-ID")

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            monitoring_service.record_event(
                EventType.API_REQUEST,
                f"{request.method} {request.url.path}",
                correlation_id=correlation_id,
                duration_ms=duration_ms,
                metadata={
                    'method': request.method,
                    'path': request.url.path,
                    'status_code': response.status_code
                },
                success=response.status_code < 400
            )

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            monitoring_service.record_event(
                EventType.ERROR,
                f"{request.method} {request.url.path}",
                correlation_id=correlation_id,
                duration_ms=duration_ms,
                error=str(e),
                success=False
            )
            raise