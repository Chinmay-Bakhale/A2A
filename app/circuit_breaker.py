"""
Circuit Breaker pattern implementation for resilient external service calls
Prevents cascading failures by failing fast when a service is unavailable
"""

import time
import logging
from typing import Callable, Any
from enum import Enum
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Blocking requests, service is down
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit Breaker implementation
    
    States:
    - CLOSED: Normal operation, requests go through
    - OPEN: Service is failing, requests are blocked
    - HALF_OPEN: Testing if service has recovered
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: type = Exception,
        name: str = "CircuitBreaker"
    ):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting recovery (HALF_OPEN)
            expected_exception: Exception type to catch
            name: Name for logging
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.name = name
        
        # State tracking
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        
        logger.info(
            f"Circuit Breaker '{name}' initialized: "
            f"threshold={failure_threshold}, timeout={timeout}s"
        )
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is OPEN or function fails
        """
        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if time.time() - self.last_failure_time >= self.timeout:
                logger.info(f"Circuit Breaker '{self.name}': Entering HALF_OPEN state")
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Service unavailable. Try again later."
                )
        
        try:
            # Execute the function
            result = func(*args, **kwargs)
            
            # Success - reset if in HALF_OPEN
            if self.state == CircuitState.HALF_OPEN:
                logger.info(f"Circuit Breaker '{self.name}': Service recovered, closing circuit")
                self._reset()
            
            return result
            
        except self.expected_exception as e:
            # Handle failure
            self._handle_failure()
            logger.error(
                f"Circuit Breaker '{self.name}': Function failed - {str(e)}"
            )
            raise
    
    def _handle_failure(self):
        """Handle a failed function call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        logger.warning(
            f"Circuit Breaker '{self.name}': Failure {self.failure_count}/{self.failure_threshold}"
        )
        
        # Open circuit if threshold reached
        if self.failure_count >= self.failure_threshold:
            logger.error(
                f"Circuit Breaker '{self.name}': OPENING circuit after "
                f"{self.failure_count} failures"
            )
            self.state = CircuitState.OPEN
    
    def _reset(self):
        """Reset circuit breaker to CLOSED state"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def get_state(self) -> dict:
        """Get current circuit breaker state"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "threshold": self.failure_threshold,
            "last_failure": self.last_failure_time
        }


def circuit_breaker(
    failure_threshold: int = 5,
    timeout: int = 60,
    expected_exception: type = Exception,
    name: str = None
):
    """
    Decorator for applying circuit breaker to a function
    
    Usage:
        @circuit_breaker(failure_threshold=3, timeout=30)
        def my_function():
            # Your code here
            pass
    """
    def decorator(func: Callable) -> Callable:
        breaker_name = name or func.__name__
        breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            timeout=timeout,
            expected_exception=expected_exception,
            name=breaker_name
        )
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        
        # Attach circuit breaker instance to wrapper for inspection
        wrapper.circuit_breaker = breaker
        
        return wrapper
    
    return decorator
