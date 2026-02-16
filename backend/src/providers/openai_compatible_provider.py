"""
Generic OpenAI-Compatible Provider Base.

This module provides a reusable base class for all providers that follow
the OpenAI API specification. Instead of duplicating code for each provider,
we create a generic implementation that can be configured per provider.

This follows the DRY (Don't Repeat Yourself) principle and makes it trivial
to add new OpenAI-compatible providers.

Supported Providers:
- Mistral AI
- Fireworks AI
- SambaNova
- Any other OpenAI-compatible API
"""

import uuid
from typing import Dict, Any, Optional
import logging
import httpx

from openai import OpenAI, RateLimitError, APIError, APIConnectionError, APITimeoutError, AuthenticationError

from providers.base_provider import BaseProvider, StreamingMetrics
from utils.env_helper import get_env
from database.db_connector import get_db_client
from utils.constants import PROVIDER_CONFIG, SYSTEM_PROMPT
from utils.provider_service import is_reasoning_model, get_timeout_for_model

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(BaseProvider):
    """
    Generic provider for any OpenAI-compatible API.
    
    This class can be instantiated with different configurations to support
    multiple providers without code duplication. It's a more senior/enterprise
    approach than creating separate files for each similar provider.
    
    Attributes:
        client: OpenAI client configured for the provider's base URL
        base_url: API base URL for the provider
        pricing_table: Model pricing information
        
    Example:
        >>> # Create a Mistral provider
        >>> mistral = OpenAICompatibleProvider(
        ...     provider_name="mistral",
        ...     api_key="sk-...",
        ...     base_url="https://api.mistral.ai/v1",
        ...     pricing_table={"mistral-large-latest": {"input": 2.0, "output": 6.0}}
        ... )
        >>> result = mistral.call_with_retry("Test", "mistral-large-latest")
    """
    
    def __init__(
        self,
        provider_name: str,
        api_key: str,
        base_url: str,
        pricing_table: Optional[Dict[str, Dict[str, float]]] = None,
        default_pricing: Optional[Dict[str, float]] = None,
        env_key_name: Optional[str] = None
    ) -> None:
        """
        Initialize generic OpenAI-compatible provider.
        
        Args:
            provider_name: Name of the provider (e.g., "mistral", "fireworks")
            api_key: API key for authentication
            base_url: Base URL for the API (e.g., "https://api.mistral.ai/v1")
            pricing_table: Model pricing dict {model: {"input": X, "output": Y}} (deprecated, use DB)
            default_pricing: Fallback pricing if model not in table or DB
            
        Raises:
            ValueError: If required parameters are invalid
        """
        if not api_key:
            raise ValueError(f"{provider_name} API key cannot be empty")
        if not base_url:
            raise ValueError(f"{provider_name} base URL cannot be empty")
            
        super().__init__(provider_name=provider_name, api_key=api_key)
        
        self.base_url = base_url
        self.pricing_table = pricing_table or {}  # Keep for backward compatibility
        self.default_pricing = default_pricing or {"input": 1.0, "output": 1.0}
        self.env_key_name = env_key_name
        
        # Configure HTTP client with reasonable timeout (can be overridden per-request)
        # Default: 60s for regular models, 120s for reasoning models
        http_client = httpx.Client(
            timeout=httpx.Timeout(60.0, connect=10.0)  # 60s request, 10s connect
        )
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            http_client=http_client,
        )
        
        logger.info(
            f"{provider_name.title()} provider initialized",
            extra={"base_url": base_url}
        )
    
    def get_pricing(self, model: str) -> Dict[str, float]:
        """
        Get pricing for a specific model.
        Tries database first, then falls back to hardcoded table, then default.
        """
        # Try to get pricing from database
        provider_display_name = PROVIDER_CONFIG.get(self.provider_name, {}).get("display_name", self.provider_name.title())
        db_client = get_db_client()
        db_pricing = db_client.get_model_pricing(provider_display_name, model)
        
        if db_pricing:
            logger.info(
                f"Using database pricing for {self.provider_name}/{model}",
                extra={"pricing": db_pricing}
            )
            return db_pricing
        
        # Fallback to hardcoded pricing table (deprecated)
        if model in self.pricing_table:
            logger.warning(
                f"Using hardcoded pricing for {self.provider_name}/{model} (database lookup failed)",
                extra={"pricing": self.pricing_table[model]}
            )
            return self.pricing_table[model]
        
        # Use default pricing as last resort
        logger.warning(
            f"Unknown model {model} for {self.provider_name}, using default pricing",
            extra={"model": model, "default_pricing": self.default_pricing}
        )
        
        return self.default_pricing
    
    def call(self, prompt: str, model: str) -> Dict[str, Any]:
        """
        Make a streaming API call to the provider.
        
        Args:
            prompt: Input text
            model: Model identifier
            
        Returns:
            Dictionary with benchmark results
        """
        request_id = str(uuid.uuid4())
        
        logger.info(
            f"Starting {self.provider_name} API call",
            extra={
                "request_id": request_id,
                "model": model,
                "prompt_length": len(prompt)
            }
        )
        
        metrics = StreamingMetrics()
        metrics.start()
        
        # Get timeout based on model type (centralized logic)
        timeout_seconds = get_timeout_for_model(model)
        
        if is_reasoning_model(model):
            logger.info(
                f"Using extended timeout for reasoning model",
                extra={"model": model, "timeout_seconds": timeout_seconds}
            )
        
        try:
            stream = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"REQUEST ID: {request_id}\n\n{prompt}"}
                ],
                temperature=0.7,
                stream=True,
                stream_options={"include_usage": True},
                timeout=timeout_seconds,
            )
            
            response_chunks = []
            usage_data: Optional[Dict[str, int]] = None
            
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    if not metrics.first_token_time:
                        metrics.mark_first_token()
                    response_chunks.append(chunk.choices[0].delta.content)
                
                if hasattr(chunk, 'usage') and chunk.usage:
                    usage_data = {
                        "prompt_tokens": chunk.usage.prompt_tokens,
                        "completion_tokens": chunk.usage.completion_tokens,
                    }
                    # Capture reasoning tokens if available (for reasoning models)
                    if hasattr(chunk.usage, 'completion_tokens_details'):
                        details = chunk.usage.completion_tokens_details
                        if hasattr(details, 'reasoning_tokens'):
                            usage_data["reasoning_tokens"] = details.reasoning_tokens
            
            metrics.end()
            
            response_text = "".join(response_chunks)
            
            # Token counting
            reasoning_tokens = None
            if usage_data:
                input_tokens = usage_data["prompt_tokens"]
                output_tokens = usage_data["completion_tokens"]
                reasoning_tokens = usage_data.get("reasoning_tokens")  # Available for reasoning models
            else:
                logger.warning(
                    f"Usage data not provided by {self.provider_name}",
                    extra={"request_id": request_id}
                )
                input_tokens = self._estimate_tokens(prompt + SYSTEM_PROMPT)
                output_tokens = self._estimate_tokens(response_text)
            
            cost_usd = self.calculate_cost(input_tokens, output_tokens, model)
            
            logger.info(
                f"{self.provider_name.title()} API call successful",
                extra={
                    "request_id": request_id,
                    "model": model,
                    "reasoning_tokens": reasoning_tokens,
                    "total_latency_ms": metrics.get_total_latency_ms(),
                    "ttft_ms": metrics.get_ttft_ms(),
                }
            )
            
            return {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "reasoning_tokens": reasoning_tokens,  # Thinking tokens for reasoning models
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
            logger.warning(
                f"{self.provider_name.title()} authentication failed",
                extra={
                    "request_id": request_id,
                    "model": model,
                    "error": str(e),
                }
            )
            error_result = self.handle_error(e, model)
            env_hint = f" Check {self.env_key_name}." if self.env_key_name else ""
            error_result.update(
                {
                    "status_code": 401,
                    "error_type": "AUTH_ERROR",
                    "error_message": f"[AUTH_ERROR] {self.provider_name} unauthorized.{env_hint}",
                }
            )
            return error_result

        except RateLimitError as e:
            metrics.end()
            logger.warning(
                f"{self.provider_name.title()} rate limit exceeded",
                extra={
                    "request_id": request_id,
                    "model": model,
                    "error": str(e),
                }
            )
            # Return error dict with 429 status so retry logic kicks in
            return self.handle_error(e, model)
            
        except (APIError, APIConnectionError, APITimeoutError) as e:
            metrics.end()
            logger.error(
                f"{self.provider_name.title()} API error",
                extra={
                    "request_id": request_id,
                    "model": model,
                    "error": str(e),
                },
                exc_info=True
            )
            return self.handle_error(e, model)
            
        except Exception as e:
            metrics.end()
            
            logger.error(
                f"{self.provider_name.title()} API call failed",
                extra={
                    "request_id": request_id,
                    "model": model,
                    "error": str(e),
                },
                exc_info=True
            )
            
            return self.handle_error(e, model)
    
    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Estimate token count (1 token ≈ 4 characters)."""
        return max(1, len(text) // 4)


def create_openai_compatible_caller(
    provider_name: str,
    env_key_name: str,
    base_url: str,
    pricing_table: Optional[Dict[str, Dict[str, float]]] = None,
    default_pricing: Optional[Dict[str, float]] = None
):
    """
    Factory function to create a provider caller function.
    
    This is a higher-order function that returns a configured caller function.
    It's a functional programming approach that reduces code duplication.
    
    Args:
        provider_name: Name of provider (lowercase)
        env_key_name: Environment variable name for API key
        base_url: API base URL
        pricing_table: Model pricing information (deprecated, use database instead)
        default_pricing: Fallback pricing
        
    Returns:
        Configured caller function with signature: (prompt: str, model: str) -> Dict
        
    Example:
        >>> call_mistral = create_openai_compatible_caller(
        ...     provider_name="mistral",
        ...     env_key_name="MISTRAL_API_KEY",
        ...     base_url="https://api.mistral.ai/v1"
        ... )
        >>> result = call_mistral("Test prompt", "mistral-large-latest")
    """
    def caller(prompt: str, model: str) -> Dict[str, Any]:
        """Generated caller function for {provider_name}."""
        api_key = get_env(env_key_name)
        
        if not api_key:
            logger.error(f"{env_key_name} not found in environment")
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
        
        try:
            provider = OpenAICompatibleProvider(
                provider_name=provider_name,
                api_key=api_key,
                base_url=base_url,
                pricing_table=pricing_table,
                default_pricing=default_pricing,
                env_key_name=env_key_name
            )
            return provider.call_with_retry(prompt, model)
        except Exception as e:
            logger.error(
                f"Failed to initialize {provider_name} provider",
                extra={"error": str(e)},
                exc_info=True
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
                "error_message": f"[INIT_ERROR] Failed to initialize provider: {str(e)}",
                "error_type": "INIT_ERROR",
                "response_text": None,
            }
    
    # Set function name for better debugging
    caller.__name__ = f"call_{provider_name}"
    caller.__doc__ = f"Call {provider_name.title()} API with retry logic."
    
    return caller

