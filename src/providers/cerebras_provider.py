"""
Cerebras AI Provider Integration.

This module provides integration with Cerebras Cloud API, which is OpenAI-compatible.
Cerebras specializes in ultra-fast inference using custom wafer-scale chips.
Direct competitor to Groq in the "Infrastructure War" benchmark.

Key Features:
- Wafer-Scale Engine (WSE) architecture
- Ultra-low latency inference
- OpenAI-compatible API

API Documentation: https://inference-docs.cerebras.ai/
Pricing: Fetched dynamically from database (updated via pricing scraper)
"""

import uuid
from typing import Dict, Any, Optional
import logging

from openai import OpenAI

from providers.base_provider import BaseProvider, StreamingMetrics
from utils.env_helper import get_env
from database.db_connector import get_db_client
from utils.constants import PROVIDER_CONFIG, SYSTEM_PROMPT

# Configure module logger
logger = logging.getLogger(__name__)


class CerebrasProvider(BaseProvider):
    """
    Cerebras Cloud API provider implementation.
    
    Cerebras uses custom Wafer-Scale Engine (WSE) chips that claim to deliver
    faster inference than traditional GPU-based solutions. This provider is
    used to benchmark Cerebras against Groq, Together, and other infrastructure
    providers for the "same model, different hardware" comparison.
    
    Attributes:
        client: OpenAI client configured for Cerebras base URL
        provider_name: Always "cerebras"
        api_key: Cerebras API key from environment
        
    Example:
        >>> provider = CerebrasProvider(api_key="csk-...")
        >>> result = provider.call_with_retry(
        ...     prompt="Explain neural networks",
        ...     model="llama-3.3-70b"
        ... )
        >>> print(f"Latency: {result['total_latency_ms']:.2f}ms")
    """
    
    def __init__(self, api_key: str) -> None:
        """
        Initialize Cerebras provider with API credentials.
        
        Args:
            api_key: Cerebras API key
            
        Raises:
            ValueError: If api_key is empty or None
        """
        if not api_key:
            raise ValueError("Cerebras API key cannot be empty")
            
        super().__init__(provider_name="cerebras", api_key=api_key)
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=PROVIDER_CONFIG["cerebras"]["base_url"],
        )
        
        logger.info("Cerebras provider initialized")
    
    def get_pricing(self, model: str) -> Dict[str, float]:
        """
        Get pricing information for a specific Cerebras model.
        Tries database first, then falls back to default.
        
        Args:
            model: Model identifier (e.g., "llama-3.3-70b")
            
        Returns:
            Dictionary with 'input' and 'output' prices per 1M tokens
        """
        # Try to get pricing from database
        db_client = get_db_client()
        db_pricing = db_client.get_model_pricing("Cerebras", model)
        
        if db_pricing:
            logger.info(
                f"Using database pricing for Cerebras/{model}",
                extra={"pricing": db_pricing}
            )
            return db_pricing
        
        # Use default pricing as fallback
        default = PROVIDER_CONFIG["cerebras"]["default_pricing"]
        logger.warning(
            f"Database pricing not found for {model}, using default",
            extra={"model": model, "default_pricing": default}
        )
        
        return default
    
    def call(self, prompt: str, model: str) -> Dict[str, Any]:
        """
        Make a streaming API call to Cerebras.
        
        Args:
            prompt: Input text to send to the model
            model: Model identifier to use
            
        Returns:
            Dictionary containing benchmark results
        """
        request_id = str(uuid.uuid4())
        
        logger.info(
            "Starting Cerebras API call",
            extra={
                "request_id": request_id,
                "model": model,
                "prompt_length": len(prompt)
            }
        )
        
        metrics = StreamingMetrics()
        metrics.start()
        
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
            
            metrics.end()
            
            response_text = "".join(response_chunks)
            
            # Extract token counts
            if usage_data:
                input_tokens = usage_data["prompt_tokens"]
                output_tokens = usage_data["completion_tokens"]
            else:
                logger.warning(
                    "Usage data not provided, estimating",
                    extra={"request_id": request_id}
                )
                input_tokens = self._estimate_tokens(prompt + SYSTEM_PROMPT)
                output_tokens = self._estimate_tokens(response_text)
            
            cost_usd = self.calculate_cost(input_tokens, output_tokens, model)
            
            logger.info(
                "Cerebras API call successful",
                extra={
                    "request_id": request_id,
                    "model": model,
                    "total_latency_ms": metrics.get_total_latency_ms(),
                    "ttft_ms": metrics.get_ttft_ms(),
                    "cost_usd": cost_usd,
                }
            )
            
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
            
            logger.error(
                "Cerebras API call failed",
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


def call_cerebras(prompt: str, model: str) -> Dict[str, Any]:
    """
    Convenience function to call Cerebras API with retry logic.
    
    Args:
        prompt: Input text
        model: Model identifier (e.g., "llama-3.3-70b")
        
    Returns:
        Dictionary with benchmark results
    """
    api_key = get_env("CEREBRAS_API_KEY")
    
    if not api_key:
        logger.error("CEREBRAS_API_KEY not found in environment")
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_latency_ms": 0,
            "ttft_ms": None,
            "tps": None,
            "status_code": None,
            "cost_usd": 0.0,
            "success": False,
            "error_message": "[CONFIG_ERROR] CEREBRAS_API_KEY not found in environment",
            "error_type": "CONFIG_ERROR",
            "response_text": None,
        }
    
    try:
        provider = CerebrasProvider(api_key=api_key)
        return provider.call_with_retry(prompt, model)
    except Exception as e:
        logger.error(
            "Failed to initialize Cerebras provider",
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

