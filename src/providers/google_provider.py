"""
Google Gemini Provider Integration.

Google's Gemini models are known for their large context windows and multimodal
capabilities. The API uses Google's proprietary SDK structure.

Key Models:
- gemini-1.5-pro: Large context window, high quality
- gemini-1.5-flash: Fast and cost-effective
- gemini-2.0-flash-exp: Experimental (requires paid tier, free tier has 0 quota)

API Documentation: https://ai.google.dev/docs
"""

import uuid
from typing import Dict, Any, Optional, Iterator
import logging

try:
    import google.generativeai as genai
    from google.generativeai.types import GenerateContentResponse
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

from providers.base_provider import BaseProvider, StreamingMetrics
from utils.env_helper import get_env

# Configure module logger
logger = logging.getLogger(__name__)

# Model Pricing (USD per 1M tokens)
# Source: https://ai.google.dev/pricing (as of Jan 2025)
PRICING_TABLE: Dict[str, Dict[str, float]] = {
    "gemini-1.5-pro": {
        "input": 1.25,   # $1.25 per 1M input tokens
        "output": 5.00,  # $5.00 per 1M output tokens
    },
    "gemini-1.5-pro-latest": {
        "input": 1.25,
        "output": 5.00,
    },
    "gemini-1.5-flash": {
        "input": 0.075,  # $0.075 per 1M input tokens
        "output": 0.30,  # $0.30 per 1M output tokens
    },
    "gemini-1.5-flash-latest": {
        "input": 0.075,
        "output": 0.30,
    },
    "gemini-2.0-flash-exp": {
        "input": 0.00,   # Free during preview
        "output": 0.00,
    },
}

# Default fallback pricing
DEFAULT_PRICING = {"input": 1.25, "output": 5.00}

# System prompt for benchmarks
SYSTEM_PROMPT = (
    "You are a helpful assistant. Your task is to summarize the provided "
    "text into exactly three concise bullet points."
)

# Generation configuration
GENERATION_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 1024,
}


class GoogleProvider(BaseProvider):
    """
    Google Gemini API provider implementation.
    
    Gemini uses Google's proprietary generative AI SDK which has a different
    structure from both OpenAI and Anthropic:
    - Uses GenerativeModel class
    - Streaming returns generator of chunks
    - Token counting may not be available in stream
    - System instructions are set on the model
    
    Attributes:
        provider_name: Always "google"
        api_key: Google API key from environment
        
    Example:
        >>> provider = GoogleProvider(api_key="AIza...")
        >>> result = provider.call_with_retry(
        ...     prompt="Explain neural networks",
        ...     model="gemini-1.5-flash"
        ... )
        >>> print(f"Context window: Huge!")
    """
    
    def __init__(self, api_key: str) -> None:
        """
        Initialize Google provider with API credentials.
        
        Args:
            api_key: Google API key (starts with 'AIza')
            
        Raises:
            ValueError: If api_key is empty or None
            ImportError: If google-generativeai package is not installed
        """
        if not GOOGLE_AVAILABLE:
            raise ImportError(
                "Google Generative AI SDK not installed. "
                "Install with: pip install google-generativeai"
            )
        
        if not api_key:
            raise ValueError("Google API key cannot be empty")
        
        super().__init__(provider_name="google", api_key=api_key)
        
        # Configure the SDK with API key
        genai.configure(api_key=api_key)
        
        logger.info(
            "Google provider initialized",
            extra={"models": list(PRICING_TABLE.keys())}
        )
    
    def get_pricing(self, model: str) -> Dict[str, float]:
        """
        Get pricing information for a specific Gemini model.
        
        Args:
            model: Model identifier (e.g., "gemini-1.5-flash")
            
        Returns:
            Dictionary with 'input' and 'output' prices per 1M tokens
        """
        pricing = PRICING_TABLE.get(model, DEFAULT_PRICING)
        
        if model not in PRICING_TABLE:
            logger.warning(
                "Unknown Gemini model, using default pricing",
                extra={"model": model, "default_pricing": DEFAULT_PRICING}
            )
        
        return pricing
    
    def call(self, prompt: str, model: str) -> Dict[str, Any]:
        """
        Make a streaming API call to Google Gemini.
        
        Google's API structure:
        - Create GenerativeModel with system_instruction
        - Call generate_content with stream=True
        - Iterate over chunks to get text
        - Token counting may require separate API call
        
        Args:
            prompt: Input text to send to the model
            model: Model identifier to use
            
        Returns:
            Dictionary containing benchmark results
        """
        request_id = str(uuid.uuid4())
        
        logger.info(
            "Starting Google Gemini API call",
            extra={
                "request_id": request_id,
                "model": model,
                "prompt_length": len(prompt)
            }
        )
        
        metrics = StreamingMetrics()
        metrics.start()
        
        try:
            # Create model with system instruction
            gemini_model = genai.GenerativeModel(
                model_name=model,
                generation_config=GENERATION_CONFIG,
                system_instruction=SYSTEM_PROMPT,
            )
            
            # Generate content with streaming
            response_stream = gemini_model.generate_content(
                f"REQUEST ID: {request_id}\n\n{prompt}",
                stream=True
            )
            
            response_text_parts = []
            first_chunk_received = False
            
            # Process streaming chunks
            for chunk in response_stream:
                if chunk.text:
                    if not first_chunk_received:
                        metrics.mark_first_token()
                        first_chunk_received = True
                    response_text_parts.append(chunk.text)
            
            metrics.end()
            
            # Combine response
            response_text = "".join(response_text_parts)
            
            # Try to get token counts
            # Note: Google may not provide usage in streaming mode
            # We may need to estimate
            try:
                # Some models provide usage_metadata
                if hasattr(response_stream, 'usage_metadata'):
                    input_tokens = response_stream.usage_metadata.prompt_token_count
                    output_tokens = response_stream.usage_metadata.candidates_token_count
                else:
                    raise AttributeError("No usage_metadata")
            except (AttributeError, Exception):
                # Fallback: estimate tokens
                logger.warning(
                    "Usage data not provided by Google, estimating",
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
                "Google Gemini API call successful",
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
                "Google Gemini API call failed",
                extra={
                    "request_id": request_id,
                    "model": model,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True
            )
            
            return self.handle_error(e, model)
    
    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Estimate token count (1 token ≈ 4 characters)."""
        return max(1, len(text) // 4)


def call_google(prompt: str, model: str) -> Dict[str, Any]:
    """
    Convenience function to call Google Gemini API with retry logic.
    
    This is the main entry point used by the benchmark runner.
    Handles API key loading, SDK availability check, and automatic retries.
    
    Args:
        prompt: Input text
        model: Model identifier (e.g., "gemini-1.5-flash")
        
    Returns:
        Dictionary with benchmark results
    """
    # Check if SDK is installed
    if not GOOGLE_AVAILABLE:
        logger.error("Google Generative AI SDK not installed")
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_latency_ms": 0,
            "ttft_ms": None,
            "tps": None,
            "status_code": None,
            "cost_usd": 0.0,
            "success": False,
            "error_message": "[DEPENDENCY_ERROR] Google SDK not installed. Run: pip install google-generativeai",
            "error_type": "DEPENDENCY_ERROR",
            "response_text": None,
        }
    
    # Load API key
    api_key = get_env("GOOGLE_API_KEY")
    
    if not api_key:
        logger.error("GOOGLE_API_KEY not found in environment")
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_latency_ms": 0,
            "ttft_ms": None,
            "tps": None,
            "status_code": None,
            "cost_usd": 0.0,
            "success": False,
            "error_message": "[CONFIG_ERROR] GOOGLE_API_KEY not found in environment",
            "error_type": "CONFIG_ERROR",
            "response_text": None,
        }
    
    try:
        provider = GoogleProvider(api_key=api_key)
        return provider.call_with_retry(prompt, model)
    except Exception as e:
        logger.error(
            "Failed to initialize Google provider",
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

