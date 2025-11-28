"""
Error handling utilities for production resilience.

Includes retry logic, circuit breakers, and escalation.
"""
import time
import logging
from functools import wraps
from typing import Callable, Any, Optional, Type
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RetryError(Exception):
    """Raised when all retry attempts are exhausted"""
    pass


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open"""
    pass


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for each subsequent delay
        exceptions: Tuple of exceptions to catch
        on_retry: Optional callback on retry (attempt, exception)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        if on_retry:
                            on_retry(attempt, e)
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(f"All {max_attempts} attempts failed: {e}")

            raise RetryError(
                f"Failed after {max_attempts} attempts"
            ) from last_exception

        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern for protecting external services.

    States:
    - CLOSED: Normal operation
    - OPEN: Failing, reject requests immediately
    - HALF_OPEN: Testing if service recovered
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        name: str = "default"
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.success_count = 0

    def _should_allow_request(self) -> bool:
        """Check if request should be allowed"""
        if self.state == self.CLOSED:
            return True

        if self.state == self.OPEN:
            if self.last_failure_time:
                elapsed = datetime.now() - self.last_failure_time
                if elapsed > timedelta(seconds=self.recovery_timeout):
                    logger.info(f"Circuit '{self.name}' transitioning to HALF_OPEN")
                    self.state = self.HALF_OPEN
                    return True
            return False

        return True  # HALF_OPEN allows test requests

    def _on_success(self):
        """Handle successful call"""
        if self.state == self.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 2:
                logger.info(f"Circuit '{self.name}' recovered, now CLOSED")
                self.state = self.CLOSED
                self.failure_count = 0
                self.success_count = 0

    def _on_failure(self, error: Exception):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        self.success_count = 0

        if self.failure_count >= self.failure_threshold:
            logger.warning(
                f"Circuit '{self.name}' OPEN after {self.failure_count} failures"
            )
            self.state = self.OPEN

    def protect(self, func: Callable) -> Callable:
        """Decorator to protect a function with circuit breaker"""
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not self._should_allow_request():
                raise CircuitBreakerOpen(
                    f"Circuit '{self.name}' is OPEN. Try again later."
                )
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure(e)
                raise

        return wrapper

    def reset(self):
        """Manually reset circuit breaker"""
        self.state = self.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info(f"Circuit '{self.name}' manually reset to CLOSED")
