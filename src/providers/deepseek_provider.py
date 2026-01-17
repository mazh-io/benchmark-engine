"""
DeepSeek AI Provider Integration.

This module provides integration with DeepSeek's API, which is OpenAI-compatible.
DeepSeek offers two main models:
- deepseek-chat (V3): Budget-friendly model with competitive pricing
- deepseek-reasoner (R1): Advanced reasoning model for complex tasks

API Documentation: https://platform.deepseek.com/api-docs
Pricing: Fetched dynamically from database (updated via pricing scraper)
"""

import uuid
from typing import Dict, Any, Optional
import logging

from openai import OpenAI
from openai.types.chat import ChatCompletion

from providers.base_provider import BaseProvider, StreamingMetrics
from utils.env_helper import get_env
from database.db_connector import get_db_client
from utils.constants import PROVIDER_CONFIG, SYSTEM_PROMPT

# Configure module logger
logger = logging.getLogger(__name__)


def fetch_models_deepseek():
    """
    Return known DeepSeek models.
    
    Returns:
        Dictionary with success, models, and note
    """
    models = [
        "deepseek-chat",      # V3
        "deepseek-reasoner",  # R1
    ]
    return {
        "success": True,
        "models": models,
        "error": None,
        "note": "Curated list - Check https://platform.deepseek.com/api-docs/ for updates"
    }


class DeepSeekProvider(BaseProvider):
    """
    DeepSeek API provider implementation.
    
    This class implements the BaseProvider interface for DeepSeek's API,
    which follows the OpenAI API specification. It supports streaming
    for accurate TTFT (Time to First Token) measurement.
    
    Attributes:
        client: OpenAI client configured for DeepSeek's base URL
        provider_name: Always "deepseek"
        api_key: DeepSeek API key from environment
        
    Example:
        >>> provider = DeepSeekProvider(api_key="sk-...")
        >>> result = provider.call_with_retry(
        ...     prompt="Explain quantum computing",
        ...     model="deepseek-chat"
        ... )
        >>> print(f"Cost: ${result['cost_usd']:.6f}")
    """
    
    def __init__(self, api_key: str) -> None:
        """
        Initialize DeepSeek provider with API credentials.
        
        Args:
            api_key: DeepSeek API key (starts with 'sk-')
            
        Raises:
            ValueError: If api_key is empty or None
        """
        if not api_key:
            raise ValueError("DeepSeek API key cannot be empty")
            
        super().__init__(provider_name="deepseek", api_key=api_key)
        
        # Initialize OpenAI client with DeepSeek base URL
        self.client = OpenAI(
            api_key=api_key,
            base_url=PROVIDER_CONFIG["deepseek"]["base_url"],
        )
        
        logger.info("DeepSeek provider initialized")
    
    def get_pricing(self, model: str) -> Dict[str, float]:
        """
        Get pricing information for a specific DeepSeek model.
        Tries database first, then falls back to default.
        
        Args:
            model: Model identifier (e.g., "deepseek-chat", "deepseek-reasoner")
            
        Returns:
            Dictionary with 'input' and 'output' prices per 1M tokens
            
        Example:
            >>> provider.get_pricing("deepseek-chat")
            {'input': 0.14, 'output': 0.28}
        """
        # Try to get pricing from database
        db_client = get_db_client()
        db_pricing = db_client.get_model_pricing("DeepSeek", model)
        
        if db_pricing:
            logger.info(
                f"Using database pricing for DeepSeek/{model}",
                extra={"pricing": db_pricing}
            )
            return db_pricing
        
        # Use default pricing as fallback
        default = PROVIDER_CONFIG["deepseek"]["default_pricing"]
        logger.warning(
            f"Database pricing not found for {model}, using default",
            extra={"model": model, "default_pricing": default}
        )
        
        return default
        
        return pricing
    
    def call(self, prompt: str, model: str) -> Dict[str, Any]:
        """
        Make a streaming API call to DeepSeek.
        
        This method creates a chat completion request with streaming enabled
        to accurately measure TTFT (Time to First Token) and TPS (Tokens Per Second).
        
        Args:
            prompt: Input text to send to the model
            model: Model identifier to use
            
        Returns:
            Dictionary containing:
                - input_tokens (int): Number of input tokens
                - output_tokens (int): Number of output tokens
                - total_latency_ms (float): Total request time in milliseconds
                - ttft_ms (float | None): Time to first token in milliseconds
                - tps (float | None): Tokens per second
                - status_code (int): HTTP status code
                - cost_usd (float): Calculated cost in USD
                - success (bool): Whether the request succeeded
                - error_message (str | None): Error message if failed
                - response_text (str | None): Full response text
                
        Example:
            >>> result = provider.call("Summarize AI", "deepseek-chat")
            >>> print(f"TTFT: {result['ttft_ms']:.2f}ms")
        """
        # Generate unique request ID for tracking
        request_id = str(uuid.uuid4())
        
        logger.info(
            "Starting DeepSeek API call",
            extra={
                "request_id": request_id,
                "model": model,
                "prompt_length": len(prompt)
            }
        )
        
        # Initialize streaming metrics tracker
        metrics = StreamingMetrics()
        metrics.start()
        
        try:
            # Create streaming chat completion
            stream = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"REQUEST ID: {request_id}\n\n{prompt}"}
                ],
                temperature=0.7,
                stream=True,
                stream_options={"include_usage": True},  # Request token usage in stream
            )
            
            # Collect streaming response
            response_chunks = []
            usage_data: Optional[Dict[str, int]] = None
            
            for chunk in stream:
                # Mark first token arrival
                if chunk.choices and chunk.choices[0].delta.content:
                    if not metrics.first_token_time:
                        metrics.mark_first_token()
                    response_chunks.append(chunk.choices[0].delta.content)
                
                # Extract usage data if present (in final chunk)
                if hasattr(chunk, 'usage') and chunk.usage:
                    usage_data = {
                        "prompt_tokens": chunk.usage.prompt_tokens,
                        "completion_tokens": chunk.usage.completion_tokens,
                        "total_tokens": chunk.usage.total_tokens,
                    }
            
            metrics.end()
            
            # Combine response chunks
            response_text = "".join(response_chunks)
            
            # Extract token counts
            if usage_data:
                input_tokens = usage_data["prompt_tokens"]
                output_tokens = usage_data["completion_tokens"]
            else:
                # Fallback: estimate token counts
                logger.warning(
                    "Usage data not provided, estimating token counts",
                    extra={"request_id": request_id}
                )
                input_tokens = self._estimate_tokens(prompt + SYSTEM_PROMPT)
                output_tokens = self._estimate_tokens(response_text)
            
            # Calculate cost
            cost_usd = self.calculate_cost(input_tokens, output_tokens, model)
            
            # Calculate metrics
            total_latency_ms = metrics.get_total_latency_ms()
            ttft_ms = metrics.get_ttft_ms()
            tps = metrics.get_tps(output_tokens)
            
            logger.info(
                "DeepSeek API call successful",
                extra={
                    "request_id": request_id,
                    "model": model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_latency_ms": total_latency_ms,
                    "ttft_ms": ttft_ms,
                    "tps": tps,
                    "cost_usd": cost_usd,
                }
            )
            
            return {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_latency_ms": total_latency_ms,
                "ttft_ms": ttft_ms,
                "tps": tps,
                "status_code": 200,
                "cost_usd": cost_usd,
                "success": True,
                "error_message": None,
                "response_text": response_text,
            }
            
        except Exception as e:
            metrics.end()
            
            logger.error(
                "DeepSeek API call failed",
                extra={
                    "request_id": request_id,
                    "model": model,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True
            )
            
            # Use base class error handling
            return self.handle_error(e, model)
    
    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """
        Estimate token count for text.
        
        This is a rough approximation used as fallback when actual
        token counts are not available from the API.
        
        Rule of thumb: ~1 token ≈ 4 characters for English text
        
        Args:
            text: Input text to estimate
            
        Returns:
            Estimated number of tokens
        """
        return max(1, len(text) // 4)


def call_deepseek(prompt: str, model: str) -> Dict[str, Any]:
    """
    Convenience function to call DeepSeek API with retry logic.
    
    This is the main entry point used by the benchmark runner.
    It handles API key loading and automatic retries for rate limits.
    
    Args:
        prompt: Input text to send to the model
        model: Model identifier (e.g., "deepseek-chat", "deepseek-reasoner")
        
    Returns:
        Dictionary with benchmark results (see DeepSeekProvider.call for format)
        
    Raises:
        Returns error dict instead of raising exceptions
        
    Example:
        >>> result = call_deepseek(
        ...     prompt="Explain machine learning",
        ...     model="deepseek-chat"
        ... )
        >>> if result["success"]:
        ...     print(f"Response: {result['response_text']}")
    """
    # Load API key from environment
    api_key = get_env("DEEPSEEK_API_KEY")
    
    if not api_key:
        logger.error("DEEPSEEK_API_KEY not found in environment")
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_latency_ms": 0,
            "ttft_ms": None,
            "tps": None,
            "status_code": None,
            "cost_usd": 0.0,
            "success": False,
            "error_message": "[CONFIG_ERROR] DEEPSEEK_API_KEY not found in environment",
            "error_type": "CONFIG_ERROR",
            "response_text": None,
        }
    
    try:
        # Initialize provider and call with retry logic
        provider = DeepSeekProvider(api_key=api_key)
        return provider.call_with_retry(prompt, model)
        
    except Exception as e:
        logger.error(
            "Failed to initialize DeepSeek provider",
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

