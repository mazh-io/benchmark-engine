"""
Async Legacy Provider Wrappers.

Provides async caller functions for providers that were originally written
as standalone sync functions (OpenAI, Groq, Together, OpenRouter).

OpenAI and Groq use ``AsyncOpenAI`` / ``AsyncGroq`` SDKs.
Together and OpenRouter use ``aiohttp`` for raw SSE streaming.
"""

import uuid
import json
import time
import logging
from typing import Dict, Any, Optional

import httpx

from openai import (
    AsyncOpenAI,
    RateLimitError,
    APIError,
    APIConnectionError,
    APITimeoutError,
)

try:
    from groq import AsyncGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

from providers.async_base_provider import StreamingMetrics
from utils.env_helper import get_env
from utils.constants import SYSTEM_PROMPT
from utils.provider_service import is_reasoning_model, get_timeout_for_model

logger = logging.getLogger(__name__)


# ======================================================================
# OpenAI — AsyncOpenAI SDK
# ======================================================================

OPENAI_PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "o1-preview": {"input": 15.00, "output": 60.00},
    "o1-mini": {"input": 3.00, "output": 12.00},
    "o1": {"input": 15.00, "output": 60.00},
}


async def async_call_openai(prompt: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """Async OpenAI benchmark call using AsyncOpenAI SDK."""
    api_key = get_env("OPENAI_API_KEY")
    if not api_key:
        return _config_error("OPENAI_API_KEY")

    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(120.0, connect=10.0),
    )
    client = AsyncOpenAI(api_key=api_key, http_client=http_client)
    request_id = str(uuid.uuid4())
    metrics = StreamingMetrics()
    metrics.start()

    try:
        is_reasoning = model.startswith("o") and any(c.isdigit() for c in model)
        timeout_seconds = get_timeout_for_model(model)

        params: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"REQUEST ID: {request_id}\n\n{prompt}"},
            ],
            "stream": True,
            "timeout": timeout_seconds,
        }
        if is_reasoning:
            params["temperature"] = 1.0
        else:
            params["temperature"] = 0.8
            params["top_p"] = 0.9

        stream = await client.chat.completions.create(**params)

        chunks: list[str] = []
        output_tokens_est = 0

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                if not metrics.first_token_time:
                    metrics.mark_first_token()
                chunks.append(content)
                output_tokens_est += len(content) // 4

        metrics.end()
        response_text = "".join(chunks)

        input_tokens = int(len(prompt.split()) / 0.75)
        output_tokens = output_tokens_est

        pricing = OPENAI_PRICING.get(model, OPENAI_PRICING["gpt-4o-mini"])
        cost = (input_tokens / 1e6 * pricing["input"]) + (output_tokens / 1e6 * pricing["output"])

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_latency_ms": metrics.get_total_latency_ms(),
            "latency_ms": metrics.get_total_latency_ms(),
            "ttft_ms": metrics.get_ttft_ms(),
            "tps": metrics.get_tps(output_tokens),
            "status_code": 200,
            "cost_usd": cost,
            "success": True,
            "error_message": None,
            "response_text": response_text,
        }

    except RateLimitError as e:
        metrics.end()
        return _error_result(429, "RATE_LIMIT", e, metrics)

    except (APIError, APIConnectionError, APITimeoutError) as e:
        metrics.end()
        sc = getattr(e, "status_code", 500)
        return _error_result(sc, type(e).__name__, e, metrics)

    except Exception as e:
        metrics.end()
        return _error_result(500, "UNKNOWN", e, metrics)


# ======================================================================
# Groq — AsyncGroq SDK
# ======================================================================

GROQ_PRICING = {
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "llama-3.1-70b-versatile": {"input": 0.59, "output": 0.79},
    "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
    "mixtral-8x7b-32768": {"input": 0.24, "output": 0.24},
}


async def async_call_groq(prompt: str, model: str = "llama-3.1-8b-instant") -> Dict[str, Any]:
    """Async Groq benchmark call using AsyncGroq SDK."""
    if not GROQ_AVAILABLE:
        return _dep_error("Groq SDK")

    api_key = get_env("GROQ_API_KEY")
    if not api_key:
        return _config_error("GROQ_API_KEY")

    http_client = httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0))
    client = AsyncGroq(api_key=api_key, http_client=http_client)
    request_id = str(uuid.uuid4())
    metrics = StreamingMetrics()
    metrics.start()

    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"REQUEST ID: {request_id}\n\n{prompt}"},
            ],
            temperature=0.8,
            stream=True,
        )

        chunks: list[str] = []
        output_tokens_est = 0

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                if not metrics.first_token_time:
                    metrics.mark_first_token()
                chunks.append(content)
                output_tokens_est += len(content) // 4

        metrics.end()
        response_text = "".join(chunks)

        input_tokens = int(len(prompt.split()) / 0.75)
        output_tokens = output_tokens_est
        pricing = GROQ_PRICING.get(model, GROQ_PRICING["llama-3.1-8b-instant"])
        cost = (input_tokens / 1e6 * pricing["input"]) + (output_tokens / 1e6 * pricing["output"])

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_latency_ms": metrics.get_total_latency_ms(),
            "latency_ms": metrics.get_total_latency_ms(),
            "ttft_ms": metrics.get_ttft_ms(),
            "tps": metrics.get_tps(output_tokens),
            "status_code": 200,
            "cost_usd": cost,
            "success": True,
            "error_message": None,
            "response_text": response_text,
        }

    except Exception as e:
        metrics.end()
        sc = getattr(e, "status_code", 500)
        return _error_result(sc, type(e).__name__, e, metrics)


# ======================================================================
# Together AI — aiohttp raw SSE
# ======================================================================

TOGETHER_PRICING = {
    "meta-llama/Llama-3.3-70B-Instruct-Turbo": {"input": 0.88, "output": 0.88},
    "meta-llama/Llama-3-70b-chat-hf": {"input": 0.59, "output": 0.79},
    "meta-llama/Llama-3-8b-chat-hf": {"input": 0.10, "output": 0.10},
    "mistralai/Mixtral-8x7B-Instruct-v0.1": {"input": 0.24, "output": 0.24},
}


async def async_call_together(prompt: str, model: str = "meta-llama/Llama-3-8b-chat-hf") -> Dict[str, Any]:
    """Async Together AI call using aiohttp SSE streaming."""
    if not AIOHTTP_AVAILABLE:
        return _dep_error("aiohttp")

    api_key = get_env("TOGETHER_API_KEY")
    if not api_key:
        return _config_error("TOGETHER_API_KEY")

    timeout_seconds = get_timeout_for_model(model)
    request_id = str(uuid.uuid4())
    metrics = StreamingMetrics()
    metrics.start()

    try:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"REQUEST ID: {request_id}\n\n{prompt}"},
            ],
            "temperature": 0.8,
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        chunks: list[str] = []
        input_tokens = 0
        output_tokens = 0
        output_tokens_est = 0

        timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                "https://api.together.xyz/v1/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    return _error_result(resp.status, "HTTP_ERROR", Exception(body), metrics)

                async for line in resp.content:
                    line_text = line.decode("utf-8").strip()
                    if not line_text.startswith("data: "):
                        continue
                    data_str = line_text[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk_data = json.loads(data_str)
                        choices = chunk_data.get("choices", [])
                        if choices:
                            content = choices[0].get("delta", {}).get("content")
                            if content:
                                if not metrics.first_token_time:
                                    metrics.mark_first_token()
                                chunks.append(content)
                                output_tokens_est += len(content) // 4

                        if chunk_data.get("usage"):
                            input_tokens = chunk_data["usage"].get("prompt_tokens", 0)
                            output_tokens = chunk_data["usage"].get("completion_tokens", 0)
                    except json.JSONDecodeError:
                        continue

        metrics.end()
        response_text = "".join(chunks)

        if not input_tokens:
            input_tokens = int(len(prompt.split()) / 0.75)
        if not output_tokens:
            output_tokens = output_tokens_est

        pricing = TOGETHER_PRICING.get(model, {"input": 0.60, "output": 0.60})
        cost = (input_tokens / 1e6 * pricing["input"]) + (output_tokens / 1e6 * pricing["output"])

        return {
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
            "total_latency_ms": metrics.get_total_latency_ms(),
            "latency_ms": metrics.get_total_latency_ms(),
            "ttft_ms": metrics.get_ttft_ms(),
            "tps": metrics.get_tps(output_tokens),
            "status_code": 200,
            "cost_usd": cost,
            "success": True,
            "error_message": None,
            "response_text": response_text,
        }

    except Exception as e:
        metrics.end()
        return _error_result(500, type(e).__name__, e, metrics)


# ======================================================================
# OpenRouter — aiohttp raw SSE
# ======================================================================

OPENROUTER_PRICING = {
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "anthropic/claude-3-haiku": {"input": 0.25, "output": 1.25},
    "meta-llama/llama-3.1-70b-instruct": {"input": 0.59, "output": 0.79},
    "minimax/minimax-01": {"input": 0.30, "output": 1.50},
}


async def async_call_openrouter(prompt: str, model: str = "openai/gpt-4o-mini") -> Dict[str, Any]:
    """Async OpenRouter call using aiohttp SSE streaming."""
    if not AIOHTTP_AVAILABLE:
        return _dep_error("aiohttp")

    api_key = get_env("OPENROUTER_API_KEY")
    if not api_key:
        return _config_error("OPENROUTER_API_KEY")

    timeout_seconds = get_timeout_for_model(model)
    request_id = str(uuid.uuid4())
    metrics = StreamingMetrics()
    metrics.start()

    try:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"REQUEST ID: {request_id}\n\n{prompt}"},
            ],
            "temperature": 0.8,
            "max_tokens": 1024,
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/benchmark-engine",
            "X-Title": "Benchmark Engine",
        }

        chunks: list[str] = []
        input_tokens = 0
        output_tokens = 0
        output_tokens_est = 0
        total_cost = None

        timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    return _error_result(resp.status, "HTTP_ERROR", Exception(body), metrics)

                async for line in resp.content:
                    line_text = line.decode("utf-8").strip()
                    if not line_text.startswith("data: "):
                        continue
                    data_str = line_text[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk_data = json.loads(data_str)
                        choices = chunk_data.get("choices", [])
                        if choices:
                            content = choices[0].get("delta", {}).get("content")
                            if content:
                                if not metrics.first_token_time:
                                    metrics.mark_first_token()
                                chunks.append(content)
                                output_tokens_est += len(content) // 4

                        if chunk_data.get("usage"):
                            input_tokens = chunk_data["usage"].get("prompt_tokens", 0)
                            output_tokens = chunk_data["usage"].get("completion_tokens", 0)
                        if chunk_data.get("total_cost"):
                            total_cost = chunk_data["total_cost"]
                    except json.JSONDecodeError:
                        continue

        metrics.end()
        response_text = "".join(chunks)

        if not response_text.strip():
            return {
                "input_tokens": int(len(prompt.split()) / 0.75) or 1,
                "output_tokens": 0,
                "total_latency_ms": metrics.get_total_latency_ms(),
                "latency_ms": metrics.get_total_latency_ms(),
                "ttft_ms": None, "tps": None, "status_code": 200, "cost_usd": 0,
                "success": False,
                "error_message": "[EMPTY_RESPONSE] API returned 200 but no text",
                "response_text": None,
            }

        if not input_tokens:
            input_tokens = int(len(prompt.split()) / 0.75)
        if not output_tokens:
            output_tokens = output_tokens_est

        if total_cost:
            cost = total_cost / 100 if total_cost > 1 else total_cost
        else:
            pricing = OPENROUTER_PRICING.get(model, {"input": 0.20, "output": 0.60})
            cost = (input_tokens / 1e6 * pricing["input"]) + (output_tokens / 1e6 * pricing["output"])

        return {
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
            "total_latency_ms": metrics.get_total_latency_ms(),
            "latency_ms": metrics.get_total_latency_ms(),
            "ttft_ms": metrics.get_ttft_ms(),
            "tps": metrics.get_tps(output_tokens),
            "status_code": 200,
            "cost_usd": cost,
            "success": True,
            "error_message": None,
            "response_text": response_text,
        }

    except Exception as e:
        metrics.end()
        return _error_result(500, type(e).__name__, e, metrics)


# ======================================================================
# Shared helpers
# ======================================================================

def _config_error(env_key: str) -> Dict[str, Any]:
    return {
        "input_tokens": 0, "output_tokens": 0, "total_latency_ms": 0,
        "latency_ms": 0, "ttft_ms": None, "tps": None,
        "status_code": None, "cost_usd": 0, "success": False,
        "error_message": f"[CONFIG_ERROR] {env_key} not found in environment",
        "error_type": "CONFIG_ERROR", "response_text": None,
    }


def _dep_error(dep_name: str) -> Dict[str, Any]:
    return {
        "input_tokens": 0, "output_tokens": 0, "total_latency_ms": 0,
        "latency_ms": 0, "ttft_ms": None, "tps": None,
        "status_code": None, "cost_usd": 0, "success": False,
        "error_message": f"[DEPENDENCY_ERROR] {dep_name} not installed.",
        "error_type": "DEPENDENCY_ERROR", "response_text": None,
    }


def _error_result(status_code: int, error_type: str, e: Exception,
                  metrics: StreamingMetrics) -> Dict[str, Any]:
    # Detect rate limit
    msg = str(e)
    if status_code == 429 or "429" in msg:
        error_type = "RATE_LIMIT"
        status_code = 429

    return {
        "input_tokens": 0, "output_tokens": 0,
        "total_latency_ms": metrics.get_total_latency_ms(),
        "latency_ms": metrics.get_total_latency_ms(),
        "ttft_ms": None, "tps": None,
        "status_code": status_code,
        "cost_usd": 0, "success": False,
        "error_message": f"[{error_type}] {msg}",
        "error_type": error_type,
        "response_text": None,
    }
