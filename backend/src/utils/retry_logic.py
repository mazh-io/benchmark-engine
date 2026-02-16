"""
Smart Retry Logic with Exponential Backoff

Handles transient API failures (5xx errors) with intelligent retry logic.
Uses exponential backoff: 1s -> 2s -> 4s to smooth out temporary provider issues.

This prevents temporary API hiccups from appearing as permanent outages in benchmarks.
"""

import time
import logging
from typing import Callable, Any, List, Optional
from functools import wraps

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 10.0,
        exponential_base: float = 2.0,
        retry_on_status_codes: Optional[List[int]] = None
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_retries: Maximum number of retry attempts (default: 3)
            initial_delay: Initial delay in seconds (default: 1.0)
            max_delay: Maximum delay in seconds (default: 10.0)
            exponential_base: Multiplier for exponential backoff (default: 2.0)
            retry_on_status_codes: List of HTTP status codes to retry on.
                                  If None, retries on all 5xx errors (500-599)
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retry_on_status_codes = retry_on_status_codes or list(range(500, 600))


def should_retry(result: dict, config: RetryConfig) -> bool:
    """
    Determine if a request should be retried based on the result.
    
    Args:
        result: Result dictionary from provider call
        config: Retry configuration
        
    Returns:
        True if should retry, False otherwise
    """
    # Don't retry if explicitly successful
    if result.get("success", False):
        return False
    
    # Check status code
    status_code = result.get("status_code")
    if status_code and status_code in config.retry_on_status_codes:
        return True
    
    # Check error message for known transient errors
    error_msg = str(result.get("error_message", "")).lower()
    transient_errors = [
        "503",  # Service Unavailable
        "502",  # Bad Gateway
        "504",  # Gateway Timeout
        "429",  # Rate limit (sometimes transient)
        "timeout",
        "connection reset",
        "connection refused",
        "temporary failure"
    ]
    
    for error_keyword in transient_errors:
        if error_keyword in error_msg:
            return True
    
    return False


def calculate_backoff_delay(attempt: int, config: RetryConfig) -> float:
    """
    Calculate exponential backoff delay for retry attempt.
    
    Args:
        attempt: Current retry attempt number (0-indexed)
        config: Retry configuration
        
    Returns:
        Delay in seconds
        
    Examples:
        >>> config = RetryConfig(initial_delay=1.0, exponential_base=2.0)
        >>> calculate_backoff_delay(0, config)
        1.0
        >>> calculate_backoff_delay(1, config)
        2.0
        >>> calculate_backoff_delay(2, config)
        4.0
    """
    delay = config.initial_delay * (config.exponential_base ** attempt)
    return min(delay, config.max_delay)


def retry_with_backoff(
    func: Callable,
    config: Optional[RetryConfig] = None,
    *args,
    **kwargs
) -> Any:
    """
    Execute function with exponential backoff retry logic.
    
    Args:
        func: Function to execute
        config: Retry configuration (uses default if None)
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func
        
    Returns:
        Result from func
        
    Example:
        >>> def api_call(prompt, model):
        ...     # May fail with 503
        ...     return call_api(prompt, model)
        >>> 
        >>> result = retry_with_backoff(api_call, prompt="test", model="gpt-4")
    """
    if config is None:
        config = RetryConfig()
    
    last_result = None
    
    for attempt in range(config.max_retries + 1):  # +1 for initial attempt
        try:
            result = func(*args, **kwargs)
            
            # If successful or shouldn't retry, return immediately
            if not should_retry(result, config):
                if attempt > 0:
                    logger.info(f"✅ Retry succeeded after {attempt} attempt(s)")
                return result
            
            # Store result for potential final return
            last_result = result
            
            # If this isn't the last attempt, wait and retry
            if attempt < config.max_retries:
                delay = calculate_backoff_delay(attempt, config)
                logger.warning(
                    f"⚠️  Attempt {attempt + 1}/{config.max_retries + 1} failed "
                    f"(status: {result.get('status_code', 'unknown')}). "
                    f"Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
            else:
                logger.error(
                    f"❌ All {config.max_retries + 1} attempts failed. "
                    f"Giving up."
                )
        
        except Exception as e:
            logger.error(f"Exception during attempt {attempt + 1}: {e}")
            if attempt >= config.max_retries:
                # Return error result on final attempt
                return {
                    "success": False,
                    "error_message": f"Failed after {config.max_retries + 1} attempts: {str(e)}",
                    "status_code": None,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_latency_ms": 0,
                    "cost_usd": 0,
                    "response_text": None
                }
            else:
                delay = calculate_backoff_delay(attempt, config)
                logger.warning(f"Exception occurred. Retrying in {delay:.1f}s...")
                time.sleep(delay)
    
    return last_result


def with_retry(config: Optional[RetryConfig] = None):
    """
    Decorator to add retry logic to a function.
    
    Args:
        config: Retry configuration (uses default if None)
        
    Returns:
        Decorated function with retry logic
        
    Example:
        >>> @with_retry(RetryConfig(max_retries=3))
        >>> def call_api(prompt, model):
        ...     # API call that might fail
        ...     return result
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return retry_with_backoff(func, config, *args, **kwargs)
        return wrapper
    return decorator


# Test scenarios
if __name__ == "__main__":
    print("Smart Retry Logic - Test Scenarios")
    print("=" * 80)
    
    # Scenario 1: Success on first try
    print("\n1. Success on first attempt:")
    print("-" * 80)
    result = {
        "success": True,
        "status_code": 200,
        "input_tokens": 100,
        "output_tokens": 50
    }
    print(f"Result: {result}")
    print(f"Should retry: {should_retry(result, RetryConfig())}")
    print("✅ Returns immediately, no retry")
    
    # Scenario 2: 503 error (transient)
    print("\n2. 503 Service Unavailable (transient error):")
    print("-" * 80)
    result = {
        "success": False,
        "status_code": 503,
        "error_message": "Service temporarily unavailable"
    }
    print(f"Result: {result}")
    print(f"Should retry: {should_retry(result, RetryConfig())}")
    print("🔄 Will retry with backoff: 1s -> 2s -> 4s")
    
    # Scenario 3: 400 error (client error, don't retry)
    print("\n3. 400 Bad Request (client error):")
    print("-" * 80)
    result = {
        "success": False,
        "status_code": 400,
        "error_message": "Invalid request"
    }
    print(f"Result: {result}")
    print(f"Should retry: {should_retry(result, RetryConfig())}")
    print("❌ Won't retry (client error, not transient)")
    
    # Scenario 4: Backoff calculation
    print("\n4. Exponential backoff delays:")
    print("-" * 80)
    config = RetryConfig(initial_delay=1.0, exponential_base=2.0)
    for i in range(4):
        delay = calculate_backoff_delay(i, config)
        print(f"Attempt {i + 1}: Wait {delay:.1f}s before retry")
    
    print("\n" + "=" * 80)
    print("Configuration:")
    print(f"  Default max retries: 3")
    print(f"  Default backoff: 1s -> 2s -> 4s")
    print(f"  Retry on: 5xx errors (500-599)")
    print(f"  Max delay cap: 10s")
