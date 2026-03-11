"""
Async Generic OpenAI-Compatible Provider Base.

Async mirror of openai_compatible_provider.py — uses ``AsyncOpenAI`` client
with ``httpx.AsyncClient`` for true non-blocking I/O.

Covers all providers that speak the OpenAI API protocol:
  Mistral, Fireworks, SambaNova, xAI, Perplexity, DeepSeek, Cerebras,
  and any future OpenAI-compatible API.
"""

import uuid
from typing import Dict, Any, Optional
import logging
import httpx

from openai import (
    AsyncOpenAI,
    RateLimitError,
    APIError,
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
)

from providers.async_base_provider import AsyncBaseProvider, StreamingMetrics
from utils.env_helper import get_env
from database.db_connector import get_db_client
from utils.constants import PROVIDER_CONFIG, SYSTEM_PROMPT
from utils.provider_service import is_reasoning_model, get_timeout_for_model

logger = logging.getLogger(__name__)


class AsyncOpenAICompatibleProvider(AsyncBaseProvider):
    """
    Async generic provider for any OpenAI-compatible API.

    Uses ``AsyncOpenAI`` + ``httpx.AsyncClient`` for fully non-blocking calls.
    Otherwise identical to the sync ``OpenAICompatibleProvider``.
    """

    def __init__(
        self,
        provider_name: str,
        api_key: str,
        base_url: str,
        pricing_table: Optional[Dict[str, Dict[str, float]]] = None,
        default_pricing: Optional[Dict[str, float]] = None,
        env_key_name: Optional[str] = None,
    ) -> None:
        if not api_key:
            raise ValueError(f"{provider_name} API key cannot be empty")
        if not base_url:
            raise ValueError(f"{provider_name} base URL cannot be empty")

        super().__init__(provider_name=provider_name, api_key=api_key)

        self.base_url = base_url
        self.pricing_table = pricing_table or {}
        self.default_pricing = default_pricing or {"input": 1.0, "output": 1.0}
        self.env_key_name = env_key_name

        # Async HTTP client
        http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
        )

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            http_client=http_client,
        )

        logger.info(
            f"{provider_name.title()} async provider initialized",
            extra={"base_url": base_url},
        )

    # ------------------------------------------------------------------
    # Pricing (sync — no I/O hotpath)
    # ------------------------------------------------------------------

    def get_pricing(self, model: str) -> Dict[str, float]:
        provider_display = PROVIDER_CONFIG.get(
            self.provider_name, {}
        ).get("display_name", self.provider_name.title())
        db_client = get_db_client()
        db_pricing = db_client.get_model_pricing(provider_display, model)

        if db_pricing:
            return db_pricing
        if model in self.pricing_table:
            return self.pricing_table[model]
        return self.default_pricing

    # ------------------------------------------------------------------
    # Async call
    # ------------------------------------------------------------------

    async def call(self, prompt: str, model: str) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())

        logger.info(
            f"Starting async {self.provider_name} API call",
            extra={"request_id": request_id, "model": model, "prompt_length": len(prompt)},
        )

        metrics = StreamingMetrics()
        metrics.start()

        timeout_seconds = get_timeout_for_model(model)

        if is_reasoning_model(model):
            logger.info(
                "Using extended timeout for reasoning model",
                extra={"model": model, "timeout_seconds": timeout_seconds},
            )

        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"REQUEST ID: {request_id}\n\n{prompt}"},
                ],
                temperature=0.7,
                stream=True,
                stream_options={"include_usage": True},
                timeout=timeout_seconds,
            )

            response_chunks: list[str] = []
            usage_data: Optional[Dict[str, int]] = None

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    if not metrics.first_token_time:
                        metrics.mark_first_token()
                    response_chunks.append(chunk.choices[0].delta.content)

                if hasattr(chunk, "usage") and chunk.usage:
                    usage_data = {
                        "prompt_tokens": chunk.usage.prompt_tokens,
                        "completion_tokens": chunk.usage.completion_tokens,
                    }
                    if hasattr(chunk.usage, "completion_tokens_details"):
                        details = chunk.usage.completion_tokens_details
                        if hasattr(details, "reasoning_tokens"):
                            usage_data["reasoning_tokens"] = details.reasoning_tokens

            metrics.end()

            response_text = "".join(response_chunks)

            reasoning_tokens = None
            if usage_data:
                input_tokens = usage_data["prompt_tokens"]
                output_tokens = usage_data["completion_tokens"]
                reasoning_tokens = usage_data.get("reasoning_tokens")
            else:
                input_tokens = self._estimate_tokens(prompt + SYSTEM_PROMPT)
                output_tokens = self._estimate_tokens(response_text)

            cost_usd = self.calculate_cost(input_tokens, output_tokens, model)

            return {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "reasoning_tokens": reasoning_tokens,
                "total_latency_ms": metrics.get_total_latency_ms(),
                "ttft_ms": metrics.get_ttft_ms(),
                "tps": metrics.get_tps(output_tokens),
                "status_code": 200,
                "cost_usd": cost_usd,
                "success": True,
                "error_message": None,
                "response_text": response_text,
            }

        except AuthenticationError as e:
            metrics.end()
            error_result = self.handle_error(e, model)
            env_hint = f" Check {self.env_key_name}." if self.env_key_name else ""
            error_result.update({
                "status_code": 401,
                "error_type": "AUTH_ERROR",
                "error_message": f"[AUTH_ERROR] {self.provider_name} unauthorized.{env_hint}",
            })
            return error_result

        except RateLimitError as e:
            metrics.end()
            logger.warning(
                f"{self.provider_name.title()} rate limit exceeded",
                extra={"request_id": request_id, "model": model, "error": str(e)},
            )
            return self.handle_error(e, model)

        except (APIError, APIConnectionError, APITimeoutError) as e:
            metrics.end()
            logger.error(
                f"{self.provider_name.title()} API error",
                extra={"request_id": request_id, "model": model, "error": str(e)},
                exc_info=True,
            )
            return self.handle_error(e, model)

        except Exception as e:
            metrics.end()
            logger.error(
                f"{self.provider_name.title()} async API call failed",
                extra={"request_id": request_id, "model": model, "error": str(e)},
                exc_info=True,
            )
            return self.handle_error(e, model)

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return max(1, len(text) // 4)


# ======================================================================
# Factory — async version of create_openai_compatible_caller
# ======================================================================

def _make_config_error(env_key_name: str) -> Dict[str, Any]:
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_latency_ms": 0,
        "ttft_ms": None,
        "tps": None,
        "status_code": None,
        "cost_usd": 0.0,
        "success": False,
        "error_message": f"[CONFIG_ERROR] {env_key_name} not found in environment",
        "error_type": "CONFIG_ERROR",
        "response_text": None,
    }


def create_async_openai_compatible_caller(
    provider_name: str,
    env_key_name: str,
    base_url: str,
    pricing_table: Optional[Dict[str, Dict[str, float]]] = None,
    default_pricing: Optional[Dict[str, float]] = None,
):
    """
    Factory that returns an ``async def caller(prompt, model) -> dict``.

    Async mirror of ``create_openai_compatible_caller``.
    """

    async def caller(prompt: str, model: str) -> Dict[str, Any]:
        api_key = get_env(env_key_name)
        if not api_key:
            logger.error(f"{env_key_name} not found in environment")
            return _make_config_error(env_key_name)

        try:
            provider = AsyncOpenAICompatibleProvider(
                provider_name=provider_name,
                api_key=api_key,
                base_url=base_url,
                pricing_table=pricing_table,
                default_pricing=default_pricing,
                env_key_name=env_key_name,
            )
            return await provider.call_with_retry(prompt, model)
        except Exception as e:
            logger.error(
                f"Failed to initialize async {provider_name} provider",
                extra={"error": str(e)},
                exc_info=True,
            )
            return {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_latency_ms": 0,
                "ttft_ms": None,
                "tps": None,
                "status_code": None,
                "cost_usd": 0.0,
                "success": False,
                "error_message": f"[INIT_ERROR] Failed to initialize provider: {e}",
                "error_type": "INIT_ERROR",
                "response_text": None,
            }

    caller.__name__ = f"async_call_{provider_name}"
    caller.__doc__ = f"Async call {provider_name.title()} API with retry logic."
    return caller
