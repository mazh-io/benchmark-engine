"""
Async Google Gemini Provider Integration.

Async mirror of google_provider.py — uses the google.genai SDK's async
streaming methods (``aio`` namespace).
"""

import uuid
from typing import Dict, Any
import logging

try:
    from google import genai
    from google.genai import types
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

from providers.async_base_provider import AsyncBaseProvider, StreamingMetrics
from utils.env_helper import get_env
from database.db_connector import get_db_client
from utils.constants import SYSTEM_PROMPT, PROVIDER_CONFIG

logger = logging.getLogger(__name__)


class AsyncGoogleProvider(AsyncBaseProvider):
    """Async Google Gemini provider using ``google.genai`` async API."""

    def __init__(self, api_key: str) -> None:
        if not GOOGLE_AVAILABLE:
            raise ImportError("Google GenAI SDK not installed. pip install google-genai")
        if not api_key:
            raise ValueError("Google API key cannot be empty")

        super().__init__(provider_name="google", api_key=api_key)
        self.client = genai.Client(api_key=api_key)
        logger.info("Async Google provider initialized")

    def get_pricing(self, model: str) -> Dict[str, float]:
        db_client = get_db_client()
        db_pricing = db_client.get_model_pricing("Google", model)
        if db_pricing:
            return db_pricing
        return PROVIDER_CONFIG["google"]["default_pricing"]

    async def call(self, prompt: str, model: str) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        logger.info("Starting async Google Gemini API call",
                     extra={"request_id": request_id, "model": model})

        metrics = StreamingMetrics()
        metrics.start()

        try:
            full_prompt = f"{SYSTEM_PROMPT}\n\nREQUEST ID: {request_id}\n\n{prompt}"

            # google.genai async streaming via the aio namespace
            response = await self.client.aio.models.generate_content_stream(
                model=model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=1024,
                ),
            )

            response_parts: list[str] = []
            first_chunk = False
            chunk_count = 0

            async for chunk in response:
                chunk_count += 1
                try:
                    text = None
                    if hasattr(chunk, "text") and chunk.text:
                        text = chunk.text
                    elif hasattr(chunk, "candidates") and chunk.candidates:
                        candidate = chunk.candidates[0]
                        if hasattr(candidate, "content") and candidate.content:
                            if hasattr(candidate.content, "parts") and candidate.content.parts:
                                text = candidate.content.parts[0].text
                    if text:
                        if not first_chunk:
                            metrics.mark_first_token()
                            first_chunk = True
                        response_parts.append(text)
                except Exception as e:
                    logger.warning(f"Error extracting chunk {chunk_count}: {e}")
                    continue

            metrics.end()
            response_text = "".join(response_parts)

            # Usage metadata
            try:
                usage = response.usage_metadata
                input_tokens = getattr(usage, "prompt_token_count", None) or max(1, len(prompt + SYSTEM_PROMPT) // 4)
                output_tokens = getattr(usage, "candidates_token_count", None) or max(1, len(response_text) // 4)
            except Exception:
                input_tokens = max(1, len(prompt + SYSTEM_PROMPT) // 4)
                output_tokens = max(1, len(response_text) // 4)

            if not response_text.strip():
                return {
                    "input_tokens": input_tokens, "output_tokens": 0,
                    "total_latency_ms": metrics.get_total_latency_ms(),
                    "ttft_ms": None, "tps": None, "status_code": 200,
                    "cost_usd": 0, "success": False,
                    "error_message": "[EMPTY_RESPONSE] API returned no text",
                    "error_type": "EMPTY_RESPONSE", "response_text": None,
                }

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
            logger.error("Google async call failed",
                         extra={"request_id": request_id, "error": str(e)},
                         exc_info=True)
            return self.handle_error(e, model)


# ------------------------------------------------------------------
# Async caller
# ------------------------------------------------------------------

async def async_call_google(prompt: str, model: str) -> Dict[str, Any]:
    if not GOOGLE_AVAILABLE:
        return {
            "input_tokens": 0, "output_tokens": 0, "total_latency_ms": 0,
            "ttft_ms": None, "tps": None, "status_code": None, "cost_usd": 0.0,
            "success": False,
            "error_message": "[DEPENDENCY_ERROR] Google GenAI SDK not installed.",
            "error_type": "DEPENDENCY_ERROR", "response_text": None,
        }

    api_key = get_env("GOOGLE_API_KEY")
    if not api_key:
        return {
            "input_tokens": 0, "output_tokens": 0, "total_latency_ms": 0,
            "ttft_ms": None, "tps": None, "status_code": None, "cost_usd": 0.0,
            "success": False,
            "error_message": "[CONFIG_ERROR] GOOGLE_API_KEY not found.",
            "error_type": "CONFIG_ERROR", "response_text": None,
        }

    try:
        provider = AsyncGoogleProvider(api_key=api_key)
        return await provider.call_with_retry(prompt, model)
    except Exception as e:
        return {
            "input_tokens": 0, "output_tokens": 0, "total_latency_ms": 0,
            "ttft_ms": None, "tps": None, "status_code": None, "cost_usd": 0.0,
            "success": False,
            "error_message": f"[INIT_ERROR] {e}",
            "error_type": "INIT_ERROR", "response_text": None,
        }
