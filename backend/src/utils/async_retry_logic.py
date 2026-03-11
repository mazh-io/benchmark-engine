"""
Async Smart Retry Logic with Exponential Backoff.

Async mirror of retry_logic.py — uses ``asyncio.sleep`` instead of
``time.sleep`` so the event loop stays unblocked during backoff waits.

Re-exports ``RetryConfig``, ``should_retry``, and ``calculate_backoff_delay``
from the sync module to avoid duplication.
"""

import asyncio
import logging
from typing import Callable, Any, Optional

from utils.retry_logic import (        # shared, sync-safe helpers
    RetryConfig,
    should_retry,
    calculate_backoff_delay,
)

logger = logging.getLogger(__name__)

# Re-export so callers only need one import
__all__ = [
    "RetryConfig",
    "should_retry",
    "calculate_backoff_delay",
    "async_retry_with_backoff",
]


async def async_retry_with_backoff(
    func: Callable,
    config: Optional[RetryConfig] = None,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """
    Async version of ``retry_with_backoff``.

    Calls *func* (which must be an ``async def``) with exponential backoff
    on retryable failures.  Uses ``asyncio.sleep`` so other coroutines
    can proceed while we wait.

    Args:
        func: Async function to execute.
        config: Retry configuration (defaults to ``RetryConfig()``).
        *args, **kwargs: Forwarded to *func*.

    Returns:
        Result dict from *func*.
    """
    if config is None:
        config = RetryConfig()

    last_result = None

    for attempt in range(config.max_retries + 1):
        try:
            result = await func(*args, **kwargs)

            if not should_retry(result, config):
                if attempt > 0:
                    logger.info(f"✅ Async retry succeeded after {attempt} attempt(s)")
                return result

            last_result = result

            if attempt < config.max_retries:
                delay = calculate_backoff_delay(attempt, config)
                logger.warning(
                    f"⚠️  Attempt {attempt + 1}/{config.max_retries + 1} failed "
                    f"(status: {result.get('status_code', 'unknown')}). "
                    f"Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"❌ All {config.max_retries + 1} async attempts failed. Giving up."
                )

        except Exception as e:
            logger.error(f"Exception during async attempt {attempt + 1}: {e}")
            if attempt >= config.max_retries:
                return {
                    "success": False,
                    "error_message": f"Failed after {config.max_retries + 1} attempts: {str(e)}",
                    "status_code": None,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_latency_ms": 0,
                    "cost_usd": 0,
                    "response_text": None,
                }
            else:
                delay = calculate_backoff_delay(attempt, config)
                logger.warning(f"Exception occurred. Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)

    return last_result
