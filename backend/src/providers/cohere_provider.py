"""
Cohere Provider Integration.

Cohere specializes in enterprise/RAG-focused language models.
Requires the official Cohere SDK (not OpenAI-compatible).

Key Models:
- command-a-03-2025: Flagship enterprise model (256K context)
- command-r7b-12-2024: Budget RAG model (128K context)

API Documentation: https://docs.cohere.com/
Pricing: Fetched dynamically from database (updated via pricing scraper)
"""

import uuid
from typing import Dict, Any
import logging

try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False

from providers.base_provider import BaseProvider, StreamingMetrics
from utils.env_helper import get_env
from database.db_connector import get_db_client
from utils.constants import SYSTEM_PROMPT, PROVIDER_CONFIG, MAX_TOKENS

# Configure module logger
logger = logging.getLogger(__name__)


class CohereProvider(BaseProvider):
    """
    Cohere API provider implementation.

    Cohere uses its own SDK with a Chat API that differs from OpenAI:
    - Uses chat() / chat_stream() methods
    - Preamble parameter for system instructions
    - Streaming yields different event types (text-generation, stream-end)
    - Token usage reported in stream-end event

    Attributes:
        client: Cohere client instance
        provider_name: Always "cohere"
        api_key: Cohere API key from environment
    """

    def __init__(self, api_key: str) -> None:
        """
        Initialize Cohere provider with API credentials.

        Args:
            api_key: Cohere API key

        Raises:
            ValueError: If api_key is empty or None
            ImportError: If cohere package is not installed
        """
        if not COHERE_AVAILABLE:
            raise ImportError(
                "Cohere SDK not installed. Install with: pip install cohere"
            )

        if not api_key:
            raise ValueError("Cohere API key cannot be empty")

        super().__init__(provider_name="cohere", api_key=api_key)

        # Initialize Cohere client (v2 API)
        self.client = cohere.ClientV2(api_key=api_key)

        logger.info("Cohere provider initialized")

    def get_pricing(self, model: str) -> Dict[str, float]:
        """
        Get pricing information for a specific Cohere model.
        Tries database first, then falls back to default.

        Args:
            model: Model identifier (e.g., "command-a-03-2025")

        Returns:
            Dictionary with 'input' and 'output' prices per 1M tokens
        """
        # Try to get pricing from database
        db_client = get_db_client()
        db_pricing = db_client.get_model_pricing("Cohere", model)

        if db_pricing:
            logger.info(
                f"Using database pricing for Cohere/{model}",
                extra={"pricing": db_pricing}
            )
            return db_pricing

        # Use default pricing as fallback
        default = PROVIDER_CONFIG["cohere"]["default_pricing"]
        logger.warning(
            f"Database pricing not found for {model}, using default",
            extra={"model": model, "default_pricing": default}
        )

        return default

    def call(self, prompt: str, model: str) -> Dict[str, Any]:
        """
        Make a streaming API call to Cohere.

        Cohere's v2 Chat API uses:
        - chat_stream() for streaming responses
        - preamble for system instructions
        - Events: text-generation (content chunks), stream-end (usage)

        Args:
            prompt: Input text to send to the model
            model: Model identifier to use

        Returns:
            Dictionary containing benchmark results
        """
        request_id = str(uuid.uuid4())

        logger.info(
            "Starting Cohere API call",
            extra={
                "request_id": request_id,
                "model": model,
                "prompt_length": len(prompt)
            }
        )

        metrics = StreamingMetrics()
        metrics.start()

        try:
            # Create streaming chat request using v2 API
            stream = self.client.chat_stream(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"REQUEST ID: {request_id}\n\n{prompt}"},
                ],
                max_tokens=MAX_TOKENS,
                temperature=0.7,
            )

            response_text_parts = []
            first_chunk_received = False
            input_tokens = 0
            output_tokens = 0

            for event in stream:
                # Content chunks
                if event.type == "content-delta":
                    text = event.delta.message.content.text if event.delta and event.delta.message else None
                    if text:
                        if not first_chunk_received:
                            metrics.mark_first_token()
                            first_chunk_received = True
                        response_text_parts.append(text)

                # Usage info at stream end
                elif event.type == "message-end":
                    if hasattr(event, 'delta') and event.delta:
                        usage = getattr(event.delta, 'usage', None)
                        if usage:
                            input_tokens = getattr(usage, 'billed_units', None)
                            if input_tokens:
                                output_tokens = getattr(input_tokens, 'output_tokens', 0)
                                input_tokens = getattr(input_tokens, 'input_tokens', 0)
                            else:
                                tokens = getattr(usage, 'tokens', None)
                                if tokens:
                                    input_tokens = getattr(tokens, 'input_tokens', 0)
                                    output_tokens = getattr(tokens, 'output_tokens', 0)

            metrics.end()

            # Combine response
            response_text = "".join(response_text_parts)

            # Fallback token estimation if usage not reported
            if input_tokens == 0:
                input_tokens = self._estimate_tokens(prompt + SYSTEM_PROMPT)
            if output_tokens == 0:
                output_tokens = self._estimate_tokens(response_text)

            # Calculate cost
            cost_usd = self.calculate_cost(input_tokens, output_tokens, model)

            # Calculate metrics
            total_latency_ms = metrics.get_total_latency_ms()
            ttft_ms = metrics.get_ttft_ms()
            tps = metrics.get_tps(output_tokens)

            logger.info(
                "Cohere API call successful",
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
                "Cohere API call failed",
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


def call_cohere(prompt: str, model: str) -> Dict[str, Any]:
    """
    Convenience function to call Cohere API with retry logic.

    This is the main entry point used by the benchmark runner.
    Handles API key loading, SDK availability check, and automatic retries.

    Args:
        prompt: Input text
        model: Model identifier (e.g., "command-a-03-2025")

    Returns:
        Dictionary with benchmark results
    """
    # Check if SDK is installed
    if not COHERE_AVAILABLE:
        logger.error("Cohere SDK not installed")
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_latency_ms": 0,
            "ttft_ms": None,
            "tps": None,
            "status_code": None,
            "cost_usd": 0.0,
            "success": False,
            "error_message": "[DEPENDENCY_ERROR] Cohere SDK not installed. Run: pip install cohere",
            "error_type": "DEPENDENCY_ERROR",
            "response_text": None,
        }

    # Load API key
    api_key = get_env("COHERE_API_KEY")

    if not api_key:
        logger.error("COHERE_API_KEY not found in environment")
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_latency_ms": 0,
            "ttft_ms": None,
            "tps": None,
            "status_code": None,
            "cost_usd": 0.0,
            "success": False,
            "error_message": "[CONFIG_ERROR] COHERE_API_KEY not found in environment",
            "error_type": "CONFIG_ERROR",
            "response_text": None,
        }

    try:
        provider = CohereProvider(api_key=api_key)
        return provider.call_with_retry(prompt, model)
    except Exception as e:
        logger.error(
            "Failed to initialize Cohere provider",
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


def fetch_models_cohere():
    """
    Return known Cohere models.

    Returns:
        Dictionary with success, models, and note
    """
    models = [
        "command-a-03-2025",
        "command-r7b-12-2024",
        "command-r-plus-08-2024",
        "command-r-08-2024",
    ]
    return {
        "success": True,
        "models": models,
        "error": None,
        "note": "Curated list - Cohere enterprise models"
    }
