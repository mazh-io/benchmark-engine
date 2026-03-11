"""
Async Anthropic Claude Provider Integration.

Async mirror of anthropic_provider.py — uses ``AsyncAnthropic`` for
non-blocking streaming calls.
"""

import uuid
from typing import Dict, Any
import logging

try:
    from anthropic import AsyncAnthropic
    from anthropic import (
        APIError,
        APIConnectionError,
        APITimeoutError,
        RateLimitError,
        BadRequestError,
        AuthenticationError,
    )
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from providers.async_base_provider import AsyncBaseProvider, StreamingMetrics
from utils.env_helper import get_env
from database.db_connector import get_db_client
from utils.constants import SYSTEM_PROMPT, PROVIDER_CONFIG, MAX_TOKENS

logger = logging.getLogger(__name__)


class AsyncAnthropicProvider(AsyncBaseProvider):
    """Async Anthropic Claude provider using ``AsyncAnthropic``."""

    def __init__(self, api_key: str) -> None:
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic SDK not installed. pip install anthropic")
        if not api_key:
            raise ValueError("Anthropic API key cannot be empty")

        super().__init__(provider_name="anthropic", api_key=api_key)
        self.client = AsyncAnthropic(api_key=api_key)
        logger.info("Async Anthropic provider initialized")

    def get_pricing(self, model: str) -> Dict[str, float]:
        db_client = get_db_client()
        db_pricing = db_client.get_model_pricing("Anthropic", model)
        if db_pricing:
            return db_pricing
        return PROVIDER_CONFIG["anthropic"]["default_pricing"]

    async def call(self, prompt: str, model: str) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        logger.info("Starting async Anthropic API call",
                     extra={"request_id": request_id, "model": model})

        metrics = StreamingMetrics()
        metrics.start()

        try:
            async with self.client.messages.stream(
                model=model,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user",
                     "content": f"REQUEST ID: {request_id}\n\n{prompt}"},
                ],
                temperature=0.7,
            ) as stream:
                response_parts: list[str] = []
                first_chunk = False

                async for event in stream:
                    if not first_chunk and hasattr(event, "delta"):
                        if hasattr(event.delta, "text") and event.delta.text:
                            metrics.mark_first_token()
                            first_chunk = True
                            response_parts.append(event.delta.text)
                    elif first_chunk and hasattr(event, "delta"):
                        if hasattr(event.delta, "text") and event.delta.text:
                            response_parts.append(event.delta.text)

                final_message = await stream.get_final_message()

            metrics.end()
            response_text = "".join(response_parts)

            if hasattr(final_message, "usage") and final_message.usage:
                input_tokens = final_message.usage.input_tokens
                output_tokens = final_message.usage.output_tokens
            else:
                input_tokens = max(1, len(prompt + SYSTEM_PROMPT) // 4)
                output_tokens = max(1, len(response_text) // 4)

            cost_usd = self.calculate_cost(input_tokens, output_tokens, model)

            return {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_latency_ms": metrics.get_total_latency_ms(),
                "ttft_ms": metrics.get_ttft_ms(),
                "tps": metrics.get_tps(output_tokens),
                "status_code": 200,
                "cost_usd": cost_usd,
                "success": True,
                "error_message": None,
                "response_text": response_text,
            }

        except (BadRequestError, RateLimitError, APITimeoutError,
                APIConnectionError, AuthenticationError) as e:
            metrics.end()
            logger.error(f"Anthropic async API error: {type(e).__name__}",
                         extra={"request_id": request_id, "error": str(e)})
            return self.handle_error(e, model)

        except Exception as e:
            metrics.end()
            logger.error("Anthropic async call failed",
                         extra={"request_id": request_id, "error": str(e)},
                         exc_info=True)
            return self.handle_error(e, model)


# ------------------------------------------------------------------
# Async caller function (used by async_provider_service)
# ------------------------------------------------------------------

async def async_call_anthropic(prompt: str, model: str) -> Dict[str, Any]:
    """Async entry point for Anthropic Claude benchmarks."""
    if not ANTHROPIC_AVAILABLE:
        return {
            "input_tokens": 0, "output_tokens": 0, "total_latency_ms": 0,
            "ttft_ms": None, "tps": None, "status_code": None, "cost_usd": 0.0,
            "success": False,
            "error_message": "[DEPENDENCY_ERROR] Anthropic SDK not installed.",
            "error_type": "DEPENDENCY_ERROR", "response_text": None,
        }

    api_key = get_env("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "input_tokens": 0, "output_tokens": 0, "total_latency_ms": 0,
            "ttft_ms": None, "tps": None, "status_code": None, "cost_usd": 0.0,
            "success": False,
            "error_message": "[CONFIG_ERROR] ANTHROPIC_API_KEY not found.",
            "error_type": "CONFIG_ERROR", "response_text": None,
        }

    try:
        provider = AsyncAnthropicProvider(api_key=api_key)
        return await provider.call_with_retry(prompt, model)
    except Exception as e:
        return {
            "input_tokens": 0, "output_tokens": 0, "total_latency_ms": 0,
            "ttft_ms": None, "tps": None, "status_code": None, "cost_usd": 0.0,
            "success": False,
            "error_message": f"[INIT_ERROR] {e}",
            "error_type": "INIT_ERROR", "response_text": None,
        }
