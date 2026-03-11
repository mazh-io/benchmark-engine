"""
Async Cohere Provider Integration.

Async mirror of cohere_provider.py — uses ``AsyncClientV2`` for
non-blocking streaming calls.
"""

import uuid
from typing import Dict, Any
import logging

try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False

from providers.async_base_provider import AsyncBaseProvider, StreamingMetrics
from utils.env_helper import get_env
from database.db_connector import get_db_client
from utils.constants import SYSTEM_PROMPT, PROVIDER_CONFIG, MAX_TOKENS

logger = logging.getLogger(__name__)


class AsyncCohereProvider(AsyncBaseProvider):
    """Async Cohere provider using ``AsyncClientV2``."""

    def __init__(self, api_key: str) -> None:
        if not COHERE_AVAILABLE:
            raise ImportError("Cohere SDK not installed. pip install cohere")
        if not api_key:
            raise ValueError("Cohere API key cannot be empty")

        super().__init__(provider_name="cohere", api_key=api_key)
        self.client = cohere.AsyncClientV2(api_key=api_key)
        logger.info("Async Cohere provider initialized")

    def get_pricing(self, model: str) -> Dict[str, float]:
        db_client = get_db_client()
        db_pricing = db_client.get_model_pricing("Cohere", model)
        if db_pricing:
            return db_pricing
        return PROVIDER_CONFIG["cohere"]["default_pricing"]

    async def call(self, prompt: str, model: str) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        logger.info("Starting async Cohere API call",
                     extra={"request_id": request_id, "model": model})

        metrics = StreamingMetrics()
        metrics.start()

        try:
            stream = self.client.chat_stream(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",
                     "content": f"REQUEST ID: {request_id}\n\n{prompt}"},
                ],
                max_tokens=MAX_TOKENS,
                temperature=0.7,
            )

            response_parts: list[str] = []
            first_chunk = False
            input_tokens = 0
            output_tokens = 0

            async for event in stream:
                if event.type == "content-delta":
                    text = (event.delta.message.content.text
                            if event.delta and event.delta.message else None)
                    if text:
                        if not first_chunk:
                            metrics.mark_first_token()
                            first_chunk = True
                        response_parts.append(text)

                elif event.type == "message-end":
                    if hasattr(event, "delta") and event.delta:
                        usage = getattr(event.delta, "usage", None)
                        if usage:
                            billed = getattr(usage, "billed_units", None)
                            if billed:
                                input_tokens = getattr(billed, "input_tokens", 0)
                                output_tokens = getattr(billed, "output_tokens", 0)
                            else:
                                tokens = getattr(usage, "tokens", None)
                                if tokens:
                                    input_tokens = getattr(tokens, "input_tokens", 0)
                                    output_tokens = getattr(tokens, "output_tokens", 0)

            metrics.end()
            response_text = "".join(response_parts)

            if input_tokens == 0:
                input_tokens = max(1, len(prompt + SYSTEM_PROMPT) // 4)
            if output_tokens == 0:
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

        except Exception as e:
            metrics.end()
            logger.error("Cohere async call failed",
                         extra={"request_id": request_id, "error": str(e)},
                         exc_info=True)
            return self.handle_error(e, model)


# ------------------------------------------------------------------
# Async caller
# ------------------------------------------------------------------

async def async_call_cohere(prompt: str, model: str) -> Dict[str, Any]:
    if not COHERE_AVAILABLE:
        return {
            "input_tokens": 0, "output_tokens": 0, "total_latency_ms": 0,
            "ttft_ms": None, "tps": None, "status_code": None, "cost_usd": 0.0,
            "success": False,
            "error_message": "[DEPENDENCY_ERROR] Cohere SDK not installed.",
            "error_type": "DEPENDENCY_ERROR", "response_text": None,
        }

    api_key = get_env("COHERE_API_KEY")
    if not api_key:
        return {
            "input_tokens": 0, "output_tokens": 0, "total_latency_ms": 0,
            "ttft_ms": None, "tps": None, "status_code": None, "cost_usd": 0.0,
            "success": False,
            "error_message": "[CONFIG_ERROR] COHERE_API_KEY not found.",
            "error_type": "CONFIG_ERROR", "response_text": None,
        }

    try:
        provider = AsyncCohereProvider(api_key=api_key)
        return await provider.call_with_retry(prompt, model)
    except Exception as e:
        return {
            "input_tokens": 0, "output_tokens": 0, "total_latency_ms": 0,
            "ttft_ms": None, "tps": None, "status_code": None, "cost_usd": 0.0,
            "success": False,
            "error_message": f"[INIT_ERROR] {e}",
            "error_type": "INIT_ERROR", "response_text": None,
        }
