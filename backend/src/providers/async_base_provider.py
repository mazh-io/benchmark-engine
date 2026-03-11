"""
Async Base Provider Class — Abstract base for async AI provider integrations.

Mirror of base_provider.py but with async call() and call_with_retry().
Shared utilities (handle_error, calculate_cost, StreamingMetrics) are
imported from the sync base to avoid duplication.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import asyncio

from providers.base_provider import BaseProvider, StreamingMetrics  # noqa: re-export
from utils.async_retry_logic import RetryConfig, async_retry_with_backoff


class AsyncBaseProvider(ABC):
    """
    Abstract base class for all **async** AI provider implementations.

    Mirrors BaseProvider but with ``async def call()`` and
    ``async def call_with_retry()``.  Non-async helpers (handle_error,
    calculate_cost, get_pricing) are inherited from the sync mixin approach
    or duplicated minimally here so each async provider stays self-contained.
    """

    def __init__(self, provider_name: str, api_key: str):
        self.provider_name = provider_name
        self.api_key = api_key

        # Retry config — 5xx only; 429s are handled by the benchmark runner's
        # deferred retry loop.
        self.retry_config = RetryConfig(
            max_retries=3,
            initial_delay=1.0,
            exponential_base=2.0,
            retry_on_status_codes=list(range(500, 600)),
        )

    # ------------------------------------------------------------------
    # Abstract methods
    # ------------------------------------------------------------------

    @abstractmethod
    async def call(self, prompt: str, model: str) -> Dict[str, Any]:
        """Make an async API call.  Must return the standard result dict."""
        ...

    @abstractmethod
    def get_pricing(self, model: str) -> Dict[str, float]:
        """Return {"input": X, "output": Y} per 1M tokens."""
        ...

    # ------------------------------------------------------------------
    # Shared helpers (same logic as BaseProvider)
    # ------------------------------------------------------------------

    def calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        pricing = self.get_pricing(model)
        return (input_tokens / 1_000_000) * pricing["input"] + \
               (output_tokens / 1_000_000) * pricing["output"]

    def handle_error(self, error: Exception, model: str) -> Dict[str, Any]:
        """Convert any exception to a standardised error result dict."""
        status_code = 500
        if hasattr(error, "status_code"):
            status_code = error.status_code
        elif hasattr(error, "response") and hasattr(error.response, "status_code"):
            status_code = error.response.status_code

        error_type_name = type(error).__name__
        if "RateLimitError" in error_type_name:
            status_code = 429

        error_message = str(error)
        if "429" in error_message or status_code == 429:
            error_type = "RATE_LIMIT"
            status_code = 429
        elif "401" in error_message or status_code == 401:
            error_type = "AUTH_ERROR"
            status_code = 401
        elif "400" in error_message or status_code == 400:
            error_type = "BAD_REQUEST"
            status_code = 400
        elif "404" in error_message or status_code == 404:
            error_type = "NOT_FOUND"
            status_code = 404
        elif "timeout" in error_message.lower():
            error_type = "TIMEOUT"
            status_code = 504
        elif "credit balance" in error_message.lower():
            error_type = "INSUFFICIENT_CREDITS"
            status_code = 402
        else:
            error_type = "UNKNOWN_ERROR"

        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_latency_ms": 0,
            "ttft_ms": None,
            "tps": None,
            "status_code": status_code,
            "cost_usd": 0,
            "success": False,
            "error_message": f"[{error_type}] {error_message}",
            "error_type": error_type,
            "response_text": None,
        }

    # ------------------------------------------------------------------
    # Async retry wrapper
    # ------------------------------------------------------------------

    async def call_with_retry(self, prompt: str, model: str) -> Dict[str, Any]:
        """Call with automatic async retry logic for transient 5xx failures."""
        return await async_retry_with_backoff(
            self.call,
            self.retry_config,
            prompt,
            model,
        )
