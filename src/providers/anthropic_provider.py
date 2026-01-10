"""
Anthropic Claude Provider Integration.

Anthropic's Claude models are known as the "developer's favorite" due to their
exceptional quality, reasoning capabilities, and user-friendly API design.

This provider requires the official Anthropic SDK (not OpenAI-compatible).

Key Models:
- claude-3-5-sonnet-latest: Flagship model, best quality (automatically uses latest version)
- claude-3-5-haiku-latest: Fast model, budget-friendly (automatically uses latest version)

API Documentation: https://docs.anthropic.com/claude/reference
Pricing: Fetched dynamically from database (updated via pricing scraper)
"""

import uuid
from typing import Dict, Any, Optional, Iterator
import logging

try:
    from anthropic import Anthropic, Stream
    from anthropic.types import MessageStreamEvent, ContentBlock, Message
    from anthropic import APIError, APIConnectionError, APITimeoutError, RateLimitError, BadRequestError, AuthenticationError
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from providers.base_provider import BaseProvider, StreamingMetrics
from utils.env_helper import get_env
from database.db_connector import get_db_client
from utils.constants import SYSTEM_PROMPT, PROVIDER_CONFIG, MAX_TOKENS

# Configure module logger
logger = logging.getLogger(__name__)


class AnthropicProvider(BaseProvider):
    """
    Anthropic Claude API provider implementation.
    
    Claude models use Anthropic's proprietary API which differs from OpenAI.
    Key differences:
    - Uses Messages API (not ChatCompletion)
    - Streaming events have different structure
    - System prompt is a separate parameter
    - Token counting is included in response
    
    Attributes:
        client: Anthropic client instance
        provider_name: Always "anthropic"
        api_key: Anthropic API key from environment
        
    Example:
        >>> provider = AnthropicProvider(api_key="sk-ant-...")
        >>> result = provider.call_with_retry(
        ...     prompt="Explain quantum computing",
        ...     model="claude-3-5-sonnet-latest"
        ... )
        >>> print(f"Quality: {result['response_text'][:100]}...")
    """
    
    def __init__(self, api_key: str) -> None:
        """
        Initialize Anthropic provider with API credentials.
        
        Args:
            api_key: Anthropic API key (starts with 'sk-ant-')
            
        Raises:
            ValueError: If api_key is empty or None
            ImportError: If anthropic package is not installed
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "Anthropic SDK not installed. Install with: pip install anthropic"
            )
        
        if not api_key:
            raise ValueError("Anthropic API key cannot be empty")
        
        super().__init__(provider_name="anthropic", api_key=api_key)
        
        # Initialize Anthropic client
        self.client = Anthropic(api_key=api_key)
        
        logger.info("Anthropic provider initialized")
    
    def get_pricing(self, model: str) -> Dict[str, float]:
        """
        Get pricing information for a specific Claude model.
        Tries database first, then falls back to default.
        
        Args:
            model: Model identifier (e.g., "claude-3-5-sonnet-latest")
            
        Returns:
            Dictionary with 'input' and 'output' prices per 1M tokens
        """
        # Try to get pricing from database
        db_client = get_db_client()
        db_pricing = db_client.get_model_pricing("Anthropic", model)
        
        if db_pricing:
            logger.info(
                f"Using database pricing for Anthropic/{model}",
                extra={"pricing": db_pricing}
            )
            return db_pricing
        
        # Use default pricing as fallback
        default = PROVIDER_CONFIG["anthropic"]["default_pricing"]
        logger.warning(
            f"Database pricing not found for {model}, using default",
            extra={"model": model, "default_pricing": default}
        )
        
        return default
    
    def call(self, prompt: str, model: str) -> Dict[str, Any]:
        """
        Make a streaming API call to Anthropic Claude.
        
        Anthropic's streaming API is different from OpenAI:
        - Uses Messages API with streaming
        - Events: message_start, content_block_start, content_block_delta, message_stop
        - Token usage is in the message_start event
        
        Args:
            prompt: Input text to send to the model
            model: Model identifier to use
            
        Returns:
            Dictionary containing benchmark results
        """
        request_id = str(uuid.uuid4())
        
        logger.info(
            "Starting Anthropic API call",
            extra={
                "request_id": request_id,
                "model": model,
                "prompt_length": len(prompt)
            }
        )
        
        metrics = StreamingMetrics()
        metrics.start()
        
        try:
            # Create streaming message
            # Note: Anthropic uses with-statement for streaming
            with self.client.messages.stream(
                model=model,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,  # Separate system parameter!
                messages=[
                    {
                        "role": "user",
                        "content": f"REQUEST ID: {request_id}\n\n{prompt}"
                    }
                ],
                temperature=0.7,
            ) as stream:
                
                response_text_parts = []
                first_chunk_received = False
                
                # Process streaming events
                for event in stream:
                    # Anthropic events: message_start, content_block_start, 
                    # content_block_delta, content_block_stop, message_stop
                    
                    # Mark first token
                    if not first_chunk_received and hasattr(event, 'delta'):
                        if hasattr(event.delta, 'text') and event.delta.text:
                            metrics.mark_first_token()
                            first_chunk_received = True
                            response_text_parts.append(event.delta.text)
                    elif first_chunk_received and hasattr(event, 'delta'):
                        if hasattr(event.delta, 'text') and event.delta.text:
                            response_text_parts.append(event.delta.text)
                
                # Get final message (includes usage)
                final_message = stream.get_final_message()
            
            metrics.end()
            
            # Combine response
            response_text = "".join(response_text_parts)
            
            # Extract token counts from final message
            # Anthropic provides usage in the message object
            if hasattr(final_message, 'usage') and final_message.usage:
                input_tokens = final_message.usage.input_tokens
                output_tokens = final_message.usage.output_tokens
            else:
                # Fallback estimation
                logger.warning(
                    "Usage data not provided by Anthropic",
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
                "Anthropic API call successful",
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
            
        except BadRequestError as e:
            # Specific handling for bad request errors (e.g., insufficient credits)
            metrics.end()
            
            logger.error(
                "Anthropic API bad request",
                extra={
                    "request_id": request_id,
                    "model": model,
                    "error": str(e),
                    "status_code": e.status_code if hasattr(e, 'status_code') else 400,
                },
                exc_info=False  # Don't log full traceback for expected errors
            )
            
            return self.handle_error(e, model)
            
        except (RateLimitError, APITimeoutError, APIConnectionError, AuthenticationError) as e:
            # Specific handling for known Anthropic API errors
            metrics.end()
            
            logger.error(
                f"Anthropic API error: {type(e).__name__}",
                extra={
                    "request_id": request_id,
                    "model": model,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=False
            )
            
            return self.handle_error(e, model)
            
        except Exception as e:
            # Catch-all for any other unexpected errors
            metrics.end()
            
            logger.error(
                "Anthropic API call failed",
                extra={
                    "request_id": request_id,
                    "model": model,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True  # Log full traceback for unexpected errors
            )
            
            return self.handle_error(e, model)
    
    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Estimate token count (1 token ≈ 4 characters)."""
        return max(1, len(text) // 4)


def call_anthropic(prompt: str, model: str) -> Dict[str, Any]:
    """
    Convenience function to call Anthropic Claude API with retry logic.
    
    This is the main entry point used by the benchmark runner.
    Handles API key loading, SDK availability check, and automatic retries.
    
    Args:
        prompt: Input text
        model: Model identifier (e.g., "claude-3-5-sonnet-latest")
        
    Returns:
        Dictionary with benchmark results
    """
    # Check if SDK is installed
    if not ANTHROPIC_AVAILABLE:
        logger.error("Anthropic SDK not installed")
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_latency_ms": 0,
            "ttft_ms": None,
            "tps": None,
            "status_code": None,
            "cost_usd": 0.0,
            "success": False,
            "error_message": "[DEPENDENCY_ERROR] Anthropic SDK not installed. Run: pip install anthropic",
            "error_type": "DEPENDENCY_ERROR",
            "response_text": None,
        }
    
    # Load API key
    api_key = get_env("ANTHROPIC_API_KEY")
    
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not found in environment")
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_latency_ms": 0,
            "ttft_ms": None,
            "tps": None,
            "status_code": None,
            "cost_usd": 0.0,
            "success": False,
            "error_message": "[CONFIG_ERROR] ANTHROPIC_API_KEY not found in environment",
            "error_type": "CONFIG_ERROR",
            "response_text": None,
        }
    
    try:
        provider = AnthropicProvider(api_key=api_key)
        return provider.call_with_retry(prompt, model)
    except Exception as e:
        logger.error(
            "Failed to initialize Anthropic provider",
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

