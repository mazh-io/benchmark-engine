"""
Google Gemini Provider Integration (Updated to google.genai SDK).

Google's Gemini models are known for their large context windows and multimodal
capabilities. This provider uses the NEW google.genai SDK (not the deprecated google.generativeai).

Key Models:
- gemini-1.5-pro: Large context window, high quality
- gemini-1.5-flash: Fast and cost-effective

API Documentation: https://ai.google.dev/gemini-api/docs
Pricing: Fetched dynamically from database (updated via pricing scraper)
"""

import uuid
from typing import Dict, Any, Optional
import logging

try:
    from google import genai
    from google.genai import types
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

from providers.base_provider import BaseProvider, StreamingMetrics
from utils.env_helper import get_env
from database.db_connector import get_db_client
from utils.constants import SYSTEM_PROMPT, PROVIDER_CONFIG

# Configure module logger
logger = logging.getLogger(__name__)


class GoogleProvider(BaseProvider):
    """
    Google Gemini API provider implementation using the NEW google.genai SDK.
    
    This provider uses the modern google.genai SDK which replaces the deprecated
    google.generativeai package.
    
    Attributes:
        client: Google GenAI client instance
        provider_name: Always "google"
        api_key: Google API key from environment
        
    Example:
        >>> provider = GoogleProvider(api_key="AIza...")
        >>> result = provider.call_with_retry(
        ...     prompt="Explain neural networks",
        ...     model="gemini-1.5-flash"
        ... )
    """
    
    def __init__(self, api_key: str) -> None:
        """
        Initialize Google provider with API credentials.
        
        Args:
            api_key: Google API key (starts with 'AIza')
            
        Raises:
            ValueError: If api_key is empty or None
            ImportError: If google.genai package is not installed
        """
        if not GOOGLE_AVAILABLE:
            raise ImportError(
                "Google GenAI SDK not installed. "
                "Install with: pip install google-genai"
            )
        
        if not api_key:
            raise ValueError("Google API key cannot be empty")
        
        super().__init__(provider_name="google", api_key=api_key)
        
        # Initialize Google GenAI client
        self.client = genai.Client(api_key=api_key)
        
        logger.info("Google provider initialized with new SDK")
    
    def get_pricing(self, model: str) -> Dict[str, float]:
        """
        Get pricing information for a specific Gemini model.
        Tries database first, then falls back to default.
        
        Args:
            model: Model identifier (e.g., "models/gemini-2.5-pro")
            
        Returns:
            Dictionary with 'input' and 'output' prices per 1M tokens
        """
        # Try to get pricing from database
        db_client = get_db_client()
        db_pricing = db_client.get_model_pricing("Google", model)
        
        if db_pricing:
            logger.info(
                f"Using database pricing for Google/{model}",
                extra={"pricing": db_pricing}
            )
            return db_pricing
        
        # Use default pricing as fallback
        default = PROVIDER_CONFIG["google"]["default_pricing"]
        logger.warning(
            f"Database pricing not found for {model}, using default",
            extra={"model": model, "default_pricing": default}
        )
        
        return default
    
    def call(self, prompt: str, model: str) -> Dict[str, Any]:
        """
        Make a streaming API call to Google Gemini using the new SDK.
        
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
            # Create system instruction and user message
            full_prompt = f"{SYSTEM_PROMPT}\n\nREQUEST ID: {request_id}\n\n{prompt}"
            
            # Generate content with streaming
            response = self.client.models.generate_content_stream(
                model=model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=1024,
                )
            )
            
            response_text_parts = []
            first_chunk_received = False
            chunk_count = 0
            
            # Process streaming chunks
            for chunk in response:
                chunk_count += 1
                try:
                    # Try to get text from chunk
                    text = None
                    if hasattr(chunk, 'text') and chunk.text:
                        text = chunk.text
                    elif hasattr(chunk, 'candidates') and chunk.candidates:
                        # Try alternative path: chunk.candidates[0].content.parts[0].text
                        candidate = chunk.candidates[0]
                        if hasattr(candidate, 'content') and candidate.content:
                            if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                text = candidate.content.parts[0].text
                    
                    if text:
                        if not first_chunk_received:
                            metrics.mark_first_token()
                            first_chunk_received = True
                        response_text_parts.append(text)
                        
                except Exception as e:
                    logger.warning(
                        f"Error extracting text from chunk {chunk_count}",
                        extra={"error": str(e), "request_id": request_id}
                    )
                    continue
            
            metrics.end()
            
            # Combine response
            response_text = "".join(response_text_parts)
            
            # Log if no response text was captured
            if not response_text:
                logger.warning(
                    "No response text captured from streaming",
                    extra={
                        "request_id": request_id,
                        "model": model,
                        "chunk_count": chunk_count,
                        "first_chunk_received": first_chunk_received
                    }
                )
            
            # Get usage metadata
            try:
                # Try to get usage from response
                usage = response.usage_metadata
                input_tokens = usage.prompt_token_count if hasattr(usage, 'prompt_token_count') else self._estimate_tokens(prompt + SYSTEM_PROMPT)
                output_tokens = usage.candidates_token_count if hasattr(usage, 'candidates_token_count') else self._estimate_tokens(response_text)
            except (AttributeError, Exception) as e:
                # Fallback: estimate tokens
                logger.warning(
                    "Usage data not provided by Google, estimating",
                    extra={"request_id": request_id, "error": str(e)}
                )
                input_tokens = self._estimate_tokens(prompt + SYSTEM_PROMPT)
                output_tokens = self._estimate_tokens(response_text)
            
            # Calculate cost
            cost_usd = self.calculate_cost(input_tokens, output_tokens, model)
            
            # Calculate metrics
            total_latency_ms = metrics.get_total_latency_ms()
            ttft_ms = metrics.get_ttft_ms()
            tps = metrics.get_tps(output_tokens)
            
            # Check if we got a response
            if not response_text or len(response_text.strip()) == 0:
                logger.error(
                    "Google Gemini returned empty response",
                    extra={
                        "request_id": request_id,
                        "model": model,
                        "chunk_count": chunk_count,
                        "output_tokens": output_tokens,
                    }
                )
                return {
                    "input_tokens": input_tokens,
                    "output_tokens": 0,
                    "total_latency_ms": total_latency_ms,
                    "ttft_ms": None,
                    "tps": None,
                    "status_code": 200,  # API succeeded but no content
                    "cost_usd": 0,
                    "success": False,
                    "error_message": "[EMPTY_RESPONSE] API call succeeded but returned no text content",
                    "error_type": "EMPTY_RESPONSE",
                    "response_text": None,
                }
            
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
                    "response_length": len(response_text),
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
        logger.error("Google GenAI SDK not installed")
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_latency_ms": 0,
            "ttft_ms": None,
            "tps": None,
            "status_code": None,
            "cost_usd": 0.0,
            "success": False,
            "error_message": "[DEPENDENCY_ERROR] Google GenAI SDK not installed. Run: pip install google-genai",
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
