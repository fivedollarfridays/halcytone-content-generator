"""
Production-grade structured logging configuration
"""
import logging
import logging.config
import json
import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime
import traceback
from pythonjsonlogger import jsonlogger


class StructuredFormatter(jsonlogger.JsonFormatter):
    """Custom structured JSON formatter"""

    def add_fields(self, log_record, record, message_dict):
        super(StructuredFormatter, self).add_fields(log_record, record, message_dict)

        # Add standard fields
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.utcnow().isoformat()

        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

        # Add service information
        log_record['service'] = 'halcytone-content-generator'
        log_record['logger'] = record.name

        # Add correlation ID if available
        correlation_id = getattr(record, 'correlation_id', None)
        if correlation_id:
            log_record['correlation_id'] = correlation_id

        # Add user context if available
        user_id = getattr(record, 'user_id', None)
        if user_id:
            log_record['user_id'] = user_id

        # Add request context if available
        request_id = getattr(record, 'request_id', None)
        if request_id:
            log_record['request_id'] = request_id

        # Add environment information
        log_record['environment'] = os.getenv('ENVIRONMENT', 'development')

        # Add exception information if present
        if record.exc_info:
            log_record['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }


class HealthCheckFilter(logging.Filter):
    """Filter to reduce noise from health check requests"""

    def filter(self, record):
        # Filter out health check requests unless they're errors
        if hasattr(record, 'pathname') and '/health' in getattr(record, 'pathname', ''):
            return record.levelno >= logging.WARNING
        return True


class SensitiveDataFilter(logging.Filter):
    """Filter to remove sensitive data from logs"""

    SENSITIVE_FIELDS = {
        'password', 'token', 'key', 'secret', 'auth', 'credential',
        'api_key', 'openai_api_key', 'jwt_secret'
    }

    def filter(self, record):
        # Sanitize message
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = self._sanitize_message(record.msg)

        # Sanitize args
        if hasattr(record, 'args') and record.args:
            record.args = tuple(
                self._sanitize_value(arg) if isinstance(arg, (str, dict)) else arg
                for arg in record.args
            )

        return True

    def _sanitize_message(self, message: str) -> str:
        """Sanitize sensitive data in log message"""
        for field in self.SENSITIVE_FIELDS:
            if field in message.lower():
                # Basic sanitization - replace with asterisks
                import re
                pattern = rf'({field}["\'\s:=]+)([^"\'\s,}}]+)'
                message = re.sub(pattern, r'\1***', message, flags=re.IGNORECASE)
        return message

    def _sanitize_value(self, value):
        """Sanitize sensitive values"""
        if isinstance(value, str):
            return self._sanitize_message(value)
        elif isinstance(value, dict):
            return self._sanitize_dict(value)
        return value

    def _sanitize_dict(self, data: dict) -> dict:
        """Sanitize dictionary data"""
        sanitized = {}
        for key, value in data.items():
            if isinstance(key, str) and any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                sanitized[key] = '***'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, str):
                sanitized[key] = self._sanitize_message(value)
            else:
                sanitized[key] = value
        return sanitized


def setup_production_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[str] = None,
    enable_elk: bool = True
) -> None:
    """Setup production logging configuration"""

    # Base configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': StructuredFormatter,
                'format': '%(timestamp)s %(level)s %(logger)s %(message)s'
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d'
            },
            'simple': {
                'format': '%(levelname)s - %(message)s'
            }
        },
        'filters': {
            'health_check': {
                '()': HealthCheckFilter,
            },
            'sensitive_data': {
                '()': SensitiveDataFilter,
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'json' if log_format == 'json' else 'detailed',
                'stream': sys.stdout,
                'filters': ['health_check', 'sensitive_data']
            }
        },
        'root': {
            'level': log_level,
            'handlers': ['console']
        },
        'loggers': {
            'halcytone_content_generator': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            },
            'uvicorn': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            'uvicorn.access': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False,
                'filters': ['health_check']
            },
            'fastapi': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            'prometheus_client': {
                'level': 'WARNING',
                'handlers': ['console'],
                'propagate': False
            }
        }
    }

    # Add file handler if log file specified
    if log_file:
        config['handlers']['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': log_level,
            'formatter': 'json' if log_format == 'json' else 'detailed',
            'filename': log_file,
            'maxBytes': 100 * 1024 * 1024,  # 100MB
            'backupCount': 5,
            'filters': ['health_check', 'sensitive_data']
        }
        config['root']['handlers'].append('file')
        for logger_config in config['loggers'].values():
            if 'handlers' in logger_config:
                logger_config['handlers'].append('file')

    # Add ELK handler for production
    if enable_elk and os.getenv('ENVIRONMENT') == 'production':
        elk_host = os.getenv('ELASTICSEARCH_HOST', 'localhost')
        elk_port = int(os.getenv('ELASTICSEARCH_PORT', '9200'))

        config['handlers']['elk'] = {
            'class': 'logging_elk.ElkHandler',
            'level': log_level,
            'formatter': 'json',
            'host': elk_host,
            'port': elk_port,
            'index': f'halcytone-logs-{datetime.now().strftime("%Y.%m")}',
            'filters': ['health_check', 'sensitive_data']
        }

        # Add ELK handler to all loggers
        config['root']['handlers'].append('elk')
        for logger_config in config['loggers'].values():
            if 'handlers' in logger_config:
                logger_config['handlers'].append('elk')

    # Apply configuration
    logging.config.dictConfig(config)

    # Set up custom exception handler
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger = logging.getLogger(__name__)
        logger.critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback),
            extra={
                'exception_type': exc_type.__name__,
                'exception_message': str(exc_value)
            }
        )

    sys.excepthook = handle_exception

    logging.info("Production logging configured", extra={
        'log_level': log_level,
        'log_format': log_format,
        'log_file': log_file,
        'elk_enabled': enable_elk
    })


class StructuredLogger:
    """Wrapper for structured logging with context"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.context = {}

    def set_context(self, **kwargs):
        """Set logging context"""
        self.context.update(kwargs)
        return self

    def clear_context(self):
        """Clear logging context"""
        self.context.clear()
        return self

    def with_context(self, **kwargs):
        """Create new logger with additional context"""
        new_logger = StructuredLogger(self.logger)
        new_logger.context = {**self.context, **kwargs}
        return new_logger

    def _log(self, level: int, message: str, **kwargs):
        """Internal log method with context"""
        extra = {**self.context, **kwargs}
        self.logger.log(level, message, extra=extra)

    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        self._log(logging.CRITICAL, message, **kwargs)

    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        kwargs.setdefault('exc_info', True)
        self._log(logging.ERROR, message, **kwargs)

    # Context managers for request tracking
    def request_context(self, request_id: str, method: str, path: str):
        """Context manager for request logging"""
        from contextlib import contextmanager

        @contextmanager
        def _request_context():
            original_context = self.context.copy()
            self.set_context(
                request_id=request_id,
                request_method=method,
                request_path=path
            )
            try:
                yield self
            finally:
                self.context = original_context

        return _request_context()

    def content_generation_context(self, content_type: str, template: str):
        """Context manager for content generation logging"""
        from contextlib import contextmanager

        @contextmanager
        def _content_context():
            original_context = self.context.copy()
            self.set_context(
                content_type=content_type,
                template=template,
                operation="content_generation"
            )
            try:
                yield self
            finally:
                self.context = original_context

        return _content_context()


def get_structured_logger(name: str = None) -> StructuredLogger:
    """Get a structured logger instance"""
    logger_name = name or __name__
    base_logger = logging.getLogger(logger_name)
    return StructuredLogger(base_logger)


def log_request_middleware():
    """Middleware to log requests with structured format"""
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response
    import uuid

    class LoggingMiddleware(BaseHTTPMiddleware):
        def __init__(self, app):
            super().__init__(app)
            self.logger = get_structured_logger("request")

        async def dispatch(self, request: Request, call_next):
            # Generate request ID
            request_id = str(uuid.uuid4())
            start_time = datetime.utcnow()

            # Log request
            with self.logger.request_context(
                request_id=request_id,
                method=request.method,
                path=request.url.path
            ):
                self.logger.info(
                    "Request started",
                    user_agent=request.headers.get("user-agent", "unknown"),
                    remote_addr=request.client.host if request.client else "unknown",
                    query_params=str(request.query_params) if request.query_params else None
                )

                try:
                    response = await call_next(request)

                    # Log response
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    self.logger.info(
                        "Request completed",
                        status_code=response.status_code,
                        duration_seconds=duration,
                        response_size=len(getattr(response, 'body', b''))
                    )

                    return response

                except Exception as e:
                    # Log error
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    self.logger.exception(
                        "Request failed",
                        duration_seconds=duration,
                        exception_type=type(e).__name__,
                        exception_message=str(e)
                    )
                    raise

    return LoggingMiddleware


# Utility functions for common logging patterns
def log_content_generation(logger: StructuredLogger, content_type: str, success: bool, duration: float, **kwargs):
    """Log content generation events"""
    with logger.content_generation_context(content_type, kwargs.get('template', 'default')):
        if success:
            logger.info(
                "Content generation completed",
                duration_seconds=duration,
                quality_score=kwargs.get('quality_score'),
                word_count=kwargs.get('word_count'),
                **kwargs
            )
        else:
            logger.error(
                "Content generation failed",
                duration_seconds=duration,
                error_type=kwargs.get('error_type'),
                error_message=kwargs.get('error_message'),
                **kwargs
            )


def log_external_api_call(logger: StructuredLogger, service: str, endpoint: str, success: bool, duration: float, **kwargs):
    """Log external API calls"""
    logger.set_context(
        external_service=service,
        external_endpoint=endpoint,
        operation="external_api_call"
    )

    if success:
        logger.info(
            "External API call completed",
            duration_seconds=duration,
            status_code=kwargs.get('status_code'),
            response_size=kwargs.get('response_size'),
            **kwargs
        )
    else:
        logger.error(
            "External API call failed",
            duration_seconds=duration,
            status_code=kwargs.get('status_code'),
            error_type=kwargs.get('error_type'),
            error_message=kwargs.get('error_message'),
            **kwargs
        )


def log_database_operation(logger: StructuredLogger, operation: str, table: str, success: bool, duration: float, **kwargs):
    """Log database operations"""
    logger.set_context(
        database_operation=operation,
        database_table=table,
        operation="database_operation"
    )

    if success:
        logger.info(
            "Database operation completed",
            duration_seconds=duration,
            rows_affected=kwargs.get('rows_affected'),
            **kwargs
        )
    else:
        logger.error(
            "Database operation failed",
            duration_seconds=duration,
            error_type=kwargs.get('error_type'),
            error_message=kwargs.get('error_message'),
            **kwargs
        )