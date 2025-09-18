"""
Resilience patterns: Circuit breakers, retries, and timeouts
"""
import asyncio
import time
from typing import Callable, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    Circuit breaker pattern implementation

    Prevents cascading failures by temporarily blocking calls to failing services
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def __call__(self, func: Callable) -> Callable:
        """Decorator for circuit breaker protection"""

        async def wrapper(*args, **kwargs):
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                else:
                    raise Exception(f"Circuit breaker is OPEN for {func.__name__}")

            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise e

        return wrapper

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout

    def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            logger.info("Circuit breaker recovered, closing circuit")
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning("Circuit breaker reopened after failure in half-open state")


class RetryPolicy:
    """
    Retry policy with exponential backoff
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ):
        """
        Initialize retry policy

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay between retries (seconds)
            max_delay: Maximum delay between retries (seconds)
            exponential_base: Base for exponential backoff
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    def __call__(self, func: Callable) -> Callable:
        """Decorator for retry logic"""

        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(self.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt == self.max_retries:
                        logger.error(f"Max retries ({self.max_retries}) reached for {func.__name__}")
                        raise

                    delay = min(
                        self.base_delay * (self.exponential_base ** attempt),
                        self.max_delay
                    )
                    logger.warning(f"Retry {attempt + 1}/{self.max_retries} after {delay}s for {func.__name__}")
                    await asyncio.sleep(delay)

            raise last_exception

        return wrapper


class TimeoutHandler:
    """
    Timeout handler for async operations
    """

    def __init__(self, timeout_seconds: float):
        """
        Initialize timeout handler

        Args:
            timeout_seconds: Timeout duration in seconds
        """
        self.timeout_seconds = timeout_seconds

    def __call__(self, func: Callable) -> Callable:
        """Decorator for timeout handling"""

        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.timeout_seconds
                )
            except asyncio.TimeoutError:
                logger.error(f"Timeout after {self.timeout_seconds}s for {func.__name__}")
                raise

        return wrapper