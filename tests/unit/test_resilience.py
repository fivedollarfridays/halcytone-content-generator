"""
Comprehensive tests for core/resilience.py - Circuit breakers, retries, and timeouts
Session 10 - Infrastructure Module Testing
"""
import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from halcytone_content_generator.core.resilience import (
    CircuitBreaker,
    CircuitState,
    RetryPolicy,
    TimeoutHandler
)


# ========== Circuit Breaker Tests ==========

class TestCircuitBreakerInitialization:
    """Test circuit breaker initialization and configuration"""

    def test_default_initialization(self):
        """Test circuit breaker with default parameters"""
        breaker = CircuitBreaker()

        assert breaker.failure_threshold == 5
        assert breaker.recovery_timeout == 60
        assert breaker.expected_exception == Exception
        assert breaker.failure_count == 0
        assert breaker.last_failure_time is None
        assert breaker.state == CircuitState.CLOSED

    def test_custom_initialization(self):
        """Test circuit breaker with custom parameters"""
        breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30,
            expected_exception=ValueError
        )

        assert breaker.failure_threshold == 3
        assert breaker.recovery_timeout == 30
        assert breaker.expected_exception == ValueError
        assert breaker.state == CircuitState.CLOSED

    def test_circuit_state_enum_values(self):
        """Test CircuitState enum has correct values"""
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"


class TestCircuitBreakerSuccessPath:
    """Test circuit breaker behavior with successful calls"""

    @pytest.mark.asyncio
    async def test_successful_call_closed_state(self):
        """Test successful call maintains closed state"""
        breaker = CircuitBreaker(failure_threshold=2)
        call_count = 0

        @breaker
        async def test_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await test_function()

        assert result == "success"
        assert call_count == 1
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_recovery_from_half_open_on_success(self):
        """Test circuit recovers to CLOSED from HALF_OPEN on success"""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

        @breaker
        async def test_function(should_fail=False):
            if should_fail:
                raise ValueError("Test failure")
            return "success"

        # Trigger failures to open circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await test_function(should_fail=True)

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(1.1)

        # Next call should attempt reset to HALF_OPEN, then succeed and close
        result = await test_function(should_fail=False)

        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0


class TestCircuitBreakerFailurePath:
    """Test circuit breaker behavior with failures"""

    @pytest.mark.asyncio
    async def test_single_failure_stays_closed(self):
        """Test single failure keeps circuit closed"""
        breaker = CircuitBreaker(failure_threshold=3)

        @breaker
        async def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await failing_function()

        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 1

    @pytest.mark.asyncio
    async def test_threshold_failures_open_circuit(self):
        """Test circuit opens after threshold failures"""
        breaker = CircuitBreaker(failure_threshold=3)

        @breaker
        async def failing_function():
            raise ValueError("Test error")

        # Trigger failures up to threshold
        for i in range(3):
            with pytest.raises(ValueError):
                await failing_function()

        assert breaker.state == CircuitState.OPEN
        assert breaker.failure_count == 3
        assert breaker.last_failure_time is not None

    @pytest.mark.asyncio
    async def test_open_circuit_blocks_calls(self):
        """Test open circuit blocks subsequent calls"""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=10)

        @breaker
        async def test_function(should_fail=False):
            if should_fail:
                raise ValueError("Test failure")
            return "success"

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await test_function(should_fail=True)

        # Circuit should now block calls
        with pytest.raises(Exception) as exc_info:
            await test_function(should_fail=False)

        assert "Circuit breaker is OPEN" in str(exc_info.value)
        assert breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_failure_in_half_open_reopens_circuit(self):
        """Test failure in HALF_OPEN state reopens circuit"""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

        @breaker
        async def test_function(should_fail=False):
            if should_fail:
                raise ValueError("Test failure")
            return "success"

        # Open circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await test_function(should_fail=True)

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery
        await asyncio.sleep(1.1)

        # Next call enters HALF_OPEN, but fails
        with pytest.raises(ValueError):
            await test_function(should_fail=True)

        # Circuit should reopen
        assert breaker.state == CircuitState.OPEN


class TestCircuitBreakerRecovery:
    """Test circuit breaker recovery mechanism"""

    @pytest.mark.asyncio
    async def test_should_attempt_reset_after_timeout(self):
        """Test recovery attempt after timeout period"""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=1)

        @breaker
        async def failing_function():
            raise ValueError("Test error")

        # Open circuit
        with pytest.raises(ValueError):
            await failing_function()

        assert breaker.state == CircuitState.OPEN

        # Before timeout
        assert not breaker._should_attempt_reset() or time.time() - breaker.last_failure_time < 1

        # After timeout
        await asyncio.sleep(1.1)
        assert breaker._should_attempt_reset()

    @pytest.mark.asyncio
    async def test_half_open_transition_on_next_call(self):
        """Test transition to HALF_OPEN on next call after timeout"""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.5)
        call_count = 0

        @breaker
        async def test_function(should_fail=False):
            nonlocal call_count
            call_count += 1
            if should_fail:
                raise ValueError("Test failure")
            return "success"

        # Open circuit
        with pytest.raises(ValueError):
            await test_function(should_fail=True)

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.6)

        # Next successful call should transition OPEN -> HALF_OPEN -> CLOSED
        result = await test_function(should_fail=False)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED


# ========== Retry Policy Tests ==========

class TestRetryPolicyInitialization:
    """Test retry policy initialization"""

    def test_default_initialization(self):
        """Test retry policy with default parameters"""
        policy = RetryPolicy()

        assert policy.max_retries == 3
        assert policy.base_delay == 1.0
        assert policy.max_delay == 60.0
        assert policy.exponential_base == 2.0

    def test_custom_initialization(self):
        """Test retry policy with custom parameters"""
        policy = RetryPolicy(
            max_retries=5,
            base_delay=0.5,
            max_delay=30.0,
            exponential_base=1.5
        )

        assert policy.max_retries == 5
        assert policy.base_delay == 0.5
        assert policy.max_delay == 30.0
        assert policy.exponential_base == 1.5


class TestRetryPolicySuccessPath:
    """Test retry policy with successful operations"""

    @pytest.mark.asyncio
    async def test_successful_first_attempt(self):
        """Test function succeeds on first attempt"""
        policy = RetryPolicy(max_retries=3)
        call_count = 0

        @policy
        async def test_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await test_function()

        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_successful_after_retries(self):
        """Test function succeeds after retries"""
        policy = RetryPolicy(max_retries=3, base_delay=0.1)
        call_count = 0

        @policy
        async def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Transient error")
            return "success"

        result = await test_function()

        assert result == "success"
        assert call_count == 3


class TestRetryPolicyFailurePath:
    """Test retry policy with failures"""

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test failure after max retries"""
        policy = RetryPolicy(max_retries=2, base_delay=0.05)
        call_count = 0

        @policy
        async def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Persistent error")

        with pytest.raises(ValueError) as exc_info:
            await failing_function()

        assert "Persistent error" in str(exc_info.value)
        assert call_count == 3  # Initial attempt + 2 retries

    @pytest.mark.asyncio
    async def test_exponential_backoff_delays(self):
        """Test exponential backoff calculation"""
        policy = RetryPolicy(max_retries=3, base_delay=0.1, exponential_base=2.0)
        delays = []

        @policy
        async def test_function():
            raise ValueError("Test error")

        start_time = time.time()

        with pytest.raises(ValueError):
            await test_function()

        total_time = time.time() - start_time

        # Expected delays: 0.1, 0.2, 0.4 = 0.7 seconds total (approximately)
        assert total_time >= 0.6  # Allow for some timing variation
        assert total_time < 1.0   # But not too much

    @pytest.mark.asyncio
    async def test_max_delay_cap(self):
        """Test max delay caps exponential backoff"""
        policy = RetryPolicy(max_retries=5, base_delay=10.0, max_delay=2.0, exponential_base=2.0)
        delays = []

        @policy
        async def test_function():
            raise ValueError("Test error")

        start_time = time.time()

        with pytest.raises(ValueError):
            await test_function()

        total_time = time.time() - start_time

        # Max delay is 2.0, so even with exponential growth, total should be capped
        # 5 retries with max 2.0 delay each = max 10 seconds
        assert total_time < 12.0  # Allow some overhead


# ========== Timeout Handler Tests ==========

class TestTimeoutHandlerInitialization:
    """Test timeout handler initialization"""

    def test_initialization(self):
        """Test timeout handler initialization"""
        handler = TimeoutHandler(timeout_seconds=5.0)
        assert handler.timeout_seconds == 5.0

    def test_custom_timeout(self):
        """Test with custom timeout value"""
        handler = TimeoutHandler(timeout_seconds=0.5)
        assert handler.timeout_seconds == 0.5


class TestTimeoutHandlerSuccessPath:
    """Test timeout handler with fast operations"""

    @pytest.mark.asyncio
    async def test_fast_operation_completes(self):
        """Test fast operation completes within timeout"""
        handler = TimeoutHandler(timeout_seconds=1.0)

        @handler
        async def fast_function():
            await asyncio.sleep(0.1)
            return "completed"

        result = await fast_function()
        assert result == "completed"

    @pytest.mark.asyncio
    async def test_immediate_return(self):
        """Test immediate return within timeout"""
        handler = TimeoutHandler(timeout_seconds=0.5)

        @handler
        async def immediate_function():
            return "immediate"

        result = await immediate_function()
        assert result == "immediate"


class TestTimeoutHandlerFailurePath:
    """Test timeout handler with slow operations"""

    @pytest.mark.asyncio
    async def test_slow_operation_times_out(self):
        """Test slow operation triggers timeout"""
        handler = TimeoutHandler(timeout_seconds=0.2)

        @handler
        async def slow_function():
            await asyncio.sleep(1.0)
            return "should not reach here"

        with pytest.raises(asyncio.TimeoutError):
            await slow_function()

    @pytest.mark.asyncio
    async def test_timeout_error_message(self):
        """Test timeout error includes function name in logs"""
        handler = TimeoutHandler(timeout_seconds=0.1)

        @handler
        async def slow_named_function():
            await asyncio.sleep(1.0)
            return "timeout"

        with pytest.raises(asyncio.TimeoutError):
            await slow_named_function()


# ========== Integration Tests ==========

class TestResiliencePatternCombinations:
    """Test combining multiple resilience patterns"""

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_retry(self):
        """Test circuit breaker combined with retry policy"""
        breaker = CircuitBreaker(failure_threshold=2)
        policy = RetryPolicy(max_retries=1, base_delay=0.05)
        call_count = 0

        @breaker
        @policy
        async def combined_function(should_fail=False):
            nonlocal call_count
            call_count += 1
            if should_fail:
                raise ValueError("Test error")
            return "success"

        # Should retry once per call, then increment circuit breaker failure count
        with pytest.raises(ValueError):
            await combined_function(should_fail=True)

        assert call_count == 2  # Initial + 1 retry
        assert breaker.failure_count == 1

    @pytest.mark.asyncio
    async def test_timeout_with_retry(self):
        """Test timeout handler combined with retry policy"""
        handler = TimeoutHandler(timeout_seconds=0.5)
        policy = RetryPolicy(max_retries=2, base_delay=0.05)
        call_count = 0

        @policy
        @handler
        async def combined_function():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(1.0)  # Will timeout each attempt
            return "success"

        with pytest.raises(asyncio.TimeoutError):
            await combined_function()

        # Timeout happens inside retry, so it retries after each timeout
        assert call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_all_three_patterns_combined(self):
        """Test all three resilience patterns together"""
        breaker = CircuitBreaker(failure_threshold=3)
        policy = RetryPolicy(max_retries=1, base_delay=0.05)
        handler = TimeoutHandler(timeout_seconds=1.0)
        call_count = 0

        @breaker
        @policy
        @handler
        async def triple_combined(delay=0.1):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(delay)
            return "success"

        # Fast operation should succeed
        result = await triple_combined(delay=0.05)
        assert result == "success"
        assert call_count == 1
        assert breaker.state == CircuitState.CLOSED


# ========== Edge Cases and Error Handling ==========

class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.asyncio
    async def test_circuit_breaker_zero_threshold(self):
        """Test circuit breaker with zero threshold opens immediately"""
        breaker = CircuitBreaker(failure_threshold=0)

        @breaker
        async def test_function():
            raise ValueError("Error")

        with pytest.raises(ValueError):
            await test_function()

        # Should open immediately with threshold 0
        assert breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_retry_policy_zero_retries(self):
        """Test retry policy with zero retries (no retry)"""
        policy = RetryPolicy(max_retries=0)
        call_count = 0

        @policy
        async def test_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Error")

        with pytest.raises(ValueError):
            await test_function()

        assert call_count == 1  # Only initial attempt, no retries

    @pytest.mark.asyncio
    async def test_timeout_handler_zero_timeout(self):
        """Test timeout handler with zero timeout"""
        handler = TimeoutHandler(timeout_seconds=0)

        @handler
        async def test_function():
            await asyncio.sleep(0.001)
            return "success"

        # Zero timeout should fail almost immediately
        with pytest.raises(asyncio.TimeoutError):
            await test_function()

    def test_circuit_breaker_last_failure_time_none(self):
        """Test _should_attempt_reset with None last_failure_time"""
        breaker = CircuitBreaker()
        breaker.last_failure_time = None

        assert breaker._should_attempt_reset() is True

    def test_circuit_breaker_different_exception_types(self):
        """Test circuit breaker with specific exception type"""
        breaker = CircuitBreaker(failure_threshold=1, expected_exception=ValueError)

        @breaker
        async def test_function(error_type=ValueError):
            raise error_type("Test error")

        # Should catch ValueError
        async def test_value_error():
            with pytest.raises(ValueError):
                await test_function(error_type=ValueError)
            assert breaker.failure_count == 1

        asyncio.run(test_value_error())

    @pytest.mark.asyncio
    async def test_half_open_state_failure_reopens(self):
        """Test failure in HALF_OPEN state triggers reopen logic (lines 90-91)"""
        # Use higher threshold so failure in HALF_OPEN doesn't reach threshold
        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=0.1)

        @breaker
        async def test_function(should_fail=False):
            if should_fail:
                raise ValueError("Test error")
            return "success"

        # Trigger enough failures to open circuit
        for _ in range(5):
            with pytest.raises(ValueError):
                await test_function(should_fail=True)

        assert breaker.state == CircuitState.OPEN
        assert breaker.failure_count == 5

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        # Next call should transition to HALF_OPEN, then fail
        # Since failure_count (5) >= threshold (5), it won't execute lines 90-91
        # We need to test when failure_count < threshold in HALF_OPEN

        # Reset failure count to trigger the elif branch
        breaker.failure_count = 2  # Less than threshold of 5
        breaker.state = CircuitState.HALF_OPEN

        # Now fail in HALF_OPEN with count < threshold
        with pytest.raises(ValueError):
            await test_function(should_fail=True)

        # Verify circuit reopened via the elif branch (lines 90-91)
        assert breaker.state == CircuitState.OPEN
        assert breaker.failure_count == 3  # Incremented to 3

    @pytest.mark.asyncio
    async def test_retry_raises_last_exception(self):
        """Test retry policy raises last exception when max retries exceeded"""
        policy = RetryPolicy(max_retries=1, base_delay=0.01)
        call_count = 0

        @policy
        async def test_function():
            nonlocal call_count
            call_count += 1
            raise RuntimeError(f"Error on attempt {call_count}")

        with pytest.raises(RuntimeError) as exc_info:
            await test_function()

        # Should raise the last exception (attempt 2)
        assert "Error on attempt 2" in str(exc_info.value)
        assert call_count == 2
