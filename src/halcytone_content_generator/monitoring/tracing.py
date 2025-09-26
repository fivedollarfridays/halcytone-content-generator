"""
Distributed tracing implementation with Jaeger and OpenTelemetry
"""
import os
import logging
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager
from functools import wraps

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider, sampling
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.jaeger import JaegerPropagator
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace import Status, StatusCode

logger = logging.getLogger(__name__)

# Global tracer instance
_tracer: Optional[trace.Tracer] = None


def setup_tracing(
    service_name: str = "halcytone-content-generator",
    jaeger_endpoint: str = "http://jaeger:14268/api/traces",
    environment: str = "production",
    version: str = "0.1.0",
    sample_rate: float = 1.0
) -> trace.Tracer:
    """Setup distributed tracing with Jaeger"""
    global _tracer

    # Create resource with service information
    resource = Resource.create({
        "service.name": service_name,
        "service.version": version,
        "environment": environment,
        "deployment.environment": environment
    })

    # Create tracer provider
    if sample_rate < 1.0:
        sampler = sampling.TraceIdRatioBased(sample_rate)
    else:
        sampler = sampling.AlwaysOnSampler()

    tracer_provider = TracerProvider(
        resource=resource,
        sampler=sampler
    )

    # Create Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=os.getenv("JAEGER_AGENT_HOST", "jaeger"),
        agent_port=int(os.getenv("JAEGER_AGENT_PORT", "6831")),
        collector_endpoint=jaeger_endpoint,
        max_tag_value_length=1024
    )

    # Add span processor
    span_processor = BatchSpanProcessor(
        jaeger_exporter,
        max_queue_size=2048,
        max_export_batch_size=512,
        export_timeout=30000,  # 30 seconds
        schedule_delay=5000    # 5 seconds
    )
    tracer_provider.add_span_processor(span_processor)

    # Set global tracer provider
    trace.set_tracer_provider(tracer_provider)

    # Set global propagator
    set_global_textmap(JaegerPropagator())

    # Get tracer instance
    _tracer = trace.get_tracer(__name__)

    logger.info(f"Tracing setup complete for {service_name}")
    return _tracer


def get_tracer() -> trace.Tracer:
    """Get the global tracer instance"""
    global _tracer
    if _tracer is None:
        _tracer = trace.get_tracer(__name__)
    return _tracer


def instrument_fastapi(app):
    """Instrument FastAPI application for tracing"""
    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls="health,ready,live,metrics",
        server_request_hook=_server_request_hook,
        client_request_hook=_client_request_hook,
        client_response_hook=_client_response_hook
    )

    # Instrument HTTP clients
    HTTPXClientInstrumentor().instrument()
    RequestsInstrumentor().instrument()

    # Instrument database if available
    try:
        Psycopg2Instrumentor().instrument()
    except:
        pass

    # Instrument Redis if available
    try:
        RedisInstrumentor().instrument()
    except:
        pass

    logger.info("FastAPI tracing instrumentation complete")


def _server_request_hook(span: trace.Span, scope: dict):
    """Hook for server request spans"""
    if span and span.is_recording():
        # Add custom attributes
        span.set_attribute("http.route", scope.get("route", {}).get("path", "unknown"))

        # Add user context if available
        headers = dict(scope.get("headers", []))
        if b"authorization" in headers:
            # Don't log the actual token, just that it exists
            span.set_attribute("auth.present", True)

        if b"user-agent" in headers:
            span.set_attribute(SpanAttributes.HTTP_USER_AGENT,
                             headers[b"user-agent"].decode())


def _client_request_hook(span: trace.Span, request):
    """Hook for client request spans"""
    if span and span.is_recording():
        # Add request size
        if hasattr(request, 'content') and request.content:
            span.set_attribute("http.request.content_length", len(request.content))


def _client_response_hook(span: trace.Span, request, response):
    """Hook for client response spans"""
    if span and span.is_recording():
        # Add response size
        if hasattr(response, 'content') and response.content:
            span.set_attribute("http.response.content_length", len(response.content))


@contextmanager
def trace_request(operation_name: str, **attributes):
    """Context manager for tracing operations"""
    tracer = get_tracer()
    with tracer.start_as_current_span(operation_name) as span:
        if span.is_recording():
            # Add custom attributes
            for key, value in attributes.items():
                span.set_attribute(key, value)

            # Add operation type
            span.set_attribute("operation.name", operation_name)

        try:
            yield span
        except Exception as e:
            if span.is_recording():
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
            raise


def trace_content_generation(content_type: str, template: str = None):
    """Decorator for content generation tracing"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with trace_request(
                "content.generation",
                content_type=content_type,
                template=template or "default",
                operation_type="content_generation"
            ) as span:
                try:
                    result = await func(*args, **kwargs)

                    # Add success metrics
                    if span.is_recording():
                        span.set_attribute("content.generated", True)
                        if hasattr(result, 'word_count'):
                            span.set_attribute("content.word_count", result.word_count)
                        if hasattr(result, 'quality_score'):
                            span.set_attribute("content.quality_score", result.quality_score)

                        span.set_status(Status(StatusCode.OK))

                    return result
                except Exception as e:
                    if span.is_recording():
                        span.set_attribute("content.generated", False)
                        span.set_attribute("error.type", type(e).__name__)
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with trace_request(
                "content.generation",
                content_type=content_type,
                template=template or "default",
                operation_type="content_generation"
            ) as span:
                try:
                    result = func(*args, **kwargs)

                    if span.is_recording():
                        span.set_attribute("content.generated", True)
                        span.set_status(Status(StatusCode.OK))

                    return result
                except Exception as e:
                    if span.is_recording():
                        span.set_attribute("content.generated", False)
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def trace_external_api(service: str, endpoint: str):
    """Decorator for external API call tracing"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with trace_request(
                f"external.{service}",
                external_service=service,
                external_endpoint=endpoint,
                operation_type="external_api_call"
            ) as span:
                try:
                    result = await func(*args, **kwargs)

                    if span.is_recording():
                        span.set_attribute("external.call.success", True)
                        if hasattr(result, 'status_code'):
                            span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, result.status_code)

                        span.set_status(Status(StatusCode.OK))

                    return result
                except Exception as e:
                    if span.is_recording():
                        span.set_attribute("external.call.success", False)
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with trace_request(
                f"external.{service}",
                external_service=service,
                external_endpoint=endpoint,
                operation_type="external_api_call"
            ) as span:
                try:
                    result = func(*args, **kwargs)

                    if span.is_recording():
                        span.set_attribute("external.call.success", True)
                        span.set_status(Status(StatusCode.OK))

                    return result
                except Exception as e:
                    if span.is_recording():
                        span.set_attribute("external.call.success", False)
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def trace_database_operation(operation: str, table: str = None):
    """Decorator for database operation tracing"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with trace_request(
                f"db.{operation}",
                db_operation=operation,
                db_table=table or "unknown",
                operation_type="database_operation"
            ) as span:
                try:
                    result = await func(*args, **kwargs)

                    if span.is_recording():
                        span.set_attribute("db.operation.success", True)
                        if hasattr(result, 'rowcount'):
                            span.set_attribute("db.rows_affected", result.rowcount)

                        span.set_status(Status(StatusCode.OK))

                    return result
                except Exception as e:
                    if span.is_recording():
                        span.set_attribute("db.operation.success", False)
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with trace_request(
                f"db.{operation}",
                db_operation=operation,
                db_table=table or "unknown",
                operation_type="database_operation"
            ) as span:
                try:
                    result = func(*args, **kwargs)

                    if span.is_recording():
                        span.set_attribute("db.operation.success", True)
                        span.set_status(Status(StatusCode.OK))

                    return result
                except Exception as e:
                    if span.is_recording():
                        span.set_attribute("db.operation.success", False)
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def add_span_attributes(**attributes):
    """Add attributes to the current span"""
    span = trace.get_current_span()
    if span and span.is_recording():
        for key, value in attributes.items():
            span.set_attribute(key, value)


def add_span_event(name: str, attributes: Dict[str, Any] = None):
    """Add an event to the current span"""
    span = trace.get_current_span()
    if span and span.is_recording():
        span.add_event(name, attributes or {})


def set_span_error(error: Exception):
    """Set error status on the current span"""
    span = trace.get_current_span()
    if span and span.is_recording():
        span.record_exception(error)
        span.set_status(Status(StatusCode.ERROR, str(error)))


def get_trace_context() -> Dict[str, str]:
    """Get current trace context for propagation"""
    from opentelemetry.propagate import inject
    context = {}
    inject(context)
    return context


def set_trace_context(context: Dict[str, str]):
    """Set trace context from propagated headers"""
    from opentelemetry.propagate import extract
    return extract(context)


class TracingMiddleware:
    """Custom tracing middleware for additional context"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        # Add custom attributes to the span
        span = trace.get_current_span()
        if span and span.is_recording():
            # Add request information
            span.set_attribute("http.method", scope.get("method", "unknown"))
            span.set_attribute("http.url", str(scope.get("path", "unknown")))

            # Add headers (sanitized)
            headers = dict(scope.get("headers", []))
            if b"content-type" in headers:
                span.set_attribute("http.request.content_type",
                                 headers[b"content-type"].decode())

            if b"content-length" in headers:
                span.set_attribute("http.request.content_length",
                                 int(headers[b"content-length"]))

        return await self.app(scope, receive, send)


def create_custom_span(name: str, **attributes):
    """Create a custom span with attributes"""
    tracer = get_tracer()
    span = tracer.start_span(name)

    if span.is_recording():
        for key, value in attributes.items():
            span.set_attribute(key, value)

    return span


@contextmanager
def trace_batch_operation(batch_type: str, item_count: int):
    """Context manager for tracing batch operations"""
    with trace_request(
        f"batch.{batch_type}",
        batch_type=batch_type,
        batch_item_count=item_count,
        operation_type="batch_processing"
    ) as span:
        try:
            yield span
            if span.is_recording():
                span.set_attribute("batch.success", True)
                span.set_status(Status(StatusCode.OK))
        except Exception as e:
            if span.is_recording():
                span.set_attribute("batch.success", False)
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
            raise


def trace_health_check():
    """Special tracing for health checks (minimal overhead)"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Only create spans for health check failures
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                with trace_request("health_check_failure") as span:
                    if span.is_recording():
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                with trace_request("health_check_failure") as span:
                    if span.is_recording():
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator