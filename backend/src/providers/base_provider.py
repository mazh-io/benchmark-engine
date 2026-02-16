"""
Base Provider Class - Abstract base for all AI provider integrations.

This module provides a base class that all provider adapters should inherit from.
It enforces a consistent interface and provides common functionality for:
- Error handling
- Rate limiting
- Cost calculation
- Response parsing
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
from src.utils.retry_logic import RetryConfig, retry_with_backoff


class BaseProvider(ABC):
    """
    Abstract base class for all AI provider implementations.
    
    All provider classes (OpenAI, Groq, Anthropic, etc.) should inherit from this
    and implement the required methods.
    """
    
    def __init__(self, provider_name: str, api_key: str):
        """
        Initialize the provider.
        
        Args:
            provider_name: Name of the provider (e.g., "openai", "anthropic")
            api_key: API key for authentication
        """
        self.provider_name = provider_name
        self.api_key = api_key
        self.max_retries = 3
        self.base_backoff = 2  # seconds
        
        # Configure smart retry logic for 5xx errors only
        # Rate limits (429) should NOT be retried here - they're handled by 
        # the benchmark runner's retry queue (60s delay + retry all at once)
        self.retry_config = RetryConfig(
            max_retries=3,
            initial_delay=1.0,  # 1s → 2s → 4s for 5xx errors
            exponential_base=2.0,
            retry_on_status_codes=list(range(500, 600))  # Only 5xx errors
        )
    
    @abstractmethod
    def call(self, prompt: str, model: str) -> Dict[str, Any]:
        """
        Make an API call to the provider.
        
        This is the main method that each provider must implement.
        It should handle streaming, token counting, and return standardized results.
        
        Args:
            prompt: The input prompt/text to send
            model: The model identifier to use
            
        Returns:
            Dict with keys:
                - input_tokens: int
                - output_tokens: int
                - total_latency_ms: float
                - ttft_ms: float | None (Time to First Token)
                - tps: float | None (Tokens Per Second)
                - status_code: int
                - cost_usd: float
                - success: bool
                - error_message: str | None
                - response_text: str | None
        """
        pass
    
    @abstractmethod
    def get_pricing(self, model: str) -> Dict[str, float]:
        """
        Get pricing information for a specific model.
        
        Args:
            model: The model identifier
            
        Returns:
            Dict with keys:
                - input: float (price per 1M input tokens in USD)
                - output: float (price per 1M output tokens in USD)
        """
        pass
    
    def fetch_models(self) -> Dict[str, Any]:
        """
        Fetch available models from the provider.
        
        This is an optional method that providers can implement to support
        dynamic model discovery. Providers without API support should return
        a curated list.
        
        Returns:
            Dict with keys:
                - success: bool
                - models: List[str] (model IDs)
                - error: Optional[str]
                - note: Optional[str] (additional info)
        """
        return {
            "success": False,
            "models": [],
            "error": f"fetch_models not implemented for {self.provider_name}",
            "note": None
        }
    
    def calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """
        Calculate the cost of a request.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: The model identifier
            
        Returns:
            Cost in USD
        """
        pricing = self.get_pricing(model)
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost
    
    def handle_error(self, error: Exception, model: str) -> Dict[str, Any]:
        """
        Handle errors in a standardized way.
        
        This method converts any exception into a standardized error response
        that matches the expected return format.
        
        Args:
            error: The exception that occurred
            model: The model that was being called
            
        Returns:
            Standardized error response dict
        """
        # Try to extract status code from error
        status_code = 500  # Default to internal server error
        
        # Check for status_code attribute (OpenAI SDK errors)
        if hasattr(error, 'status_code'):
            status_code = error.status_code
        elif hasattr(error, 'response') and hasattr(error.response, 'status_code'):
            status_code = error.response.status_code
        
        # Check error type name for rate limit errors
        error_type_name = type(error).__name__
        if 'RateLimitError' in error_type_name:
            status_code = 429
        
        # Check for specific error types
        error_message = str(error)
        if "429" in error_message or status_code == 429:
            error_type = "RATE_LIMIT"
            status_code = 429
        elif "401" in error_message or status_code == 401:
            error_type = "AUTH_ERROR"
            status_code = 401
        elif "400" in error_message or status_code == 400:
            error_type = "BAD_REQUEST"
            status_code = 400
        elif "404" in error_message or status_code == 404:
            error_type = "NOT_FOUND"
            status_code = 404
        elif "timeout" in error_message.lower():
            error_type = "TIMEOUT"
            status_code = 504
        elif "credit balance" in error_message.lower():
            error_type = "INSUFFICIENT_CREDITS"
            status_code = 402
        else:
            error_type = "UNKNOWN_ERROR"
        
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_latency_ms": 0,
            "ttft_ms": None,
            "tps": None,
            "status_code": status_code,
            "cost_usd": 0,
            "success": False,
            "error_message": f"[{error_type}] {error_message}",
            "error_type": error_type,
            "response_text": None
        }
    
    def handle_rate_limit(self, attempt: int) -> bool:
        """
        Handle rate limiting with exponential backoff.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            True if should retry, False if max retries reached
        """
        if attempt >= self.max_retries:
            return False
        
        # Calculate backoff time: 2s, 4s, 8s
        backoff_time = self.base_backoff * (2 ** attempt)
        
        print(f"⏳ Rate limit hit for {self.provider_name}, waiting {backoff_time}s before retry {attempt + 1}/{self.max_retries}...")
        time.sleep(backoff_time)
        
        return True
    
    def call_with_retry(self, prompt: str, model: str) -> Dict[str, Any]:
        """
        Call the provider with automatic retry logic for transient failures.
        
        This wrapper method handles:
        - Rate limiting (429) with exponential backoff
        - 5xx errors (500-599) with exponential backoff (1s -> 2s -> 4s)
        - Other errors are returned immediately
        
        The retry logic helps smooth out temporary API hiccups so they don't
        appear as permanent outages in benchmarks.
        
        Args:
            prompt: The input prompt
            model: The model identifier
            
        Returns:
            Standardized response dict
        """
        # Use smart retry logic for 5xx errors
        return retry_with_backoff(
            self.call,
            self.retry_config,
            prompt,
            model
        )


class StreamingMetrics:
    """
    Helper class to track streaming metrics (TTFT, TPS).
    
    Usage:
        metrics = StreamingMetrics()
        metrics.start()
        # ... receive first chunk ...
        metrics.mark_first_token()
        # ... receive more chunks ...
        metrics.end()
        
        ttft_ms = metrics.get_ttft_ms()
        tps = metrics.get_tps(total_tokens)
    """
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.first_token_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def start(self):
        """Mark the start of the request."""
        self.start_time = time.time()
    
    def mark_first_token(self):
        """Mark when the first token arrives."""
        if self.first_token_time is None:
            self.first_token_time = time.time()
    
    def end(self):
        """Mark the end of the response."""
        self.end_time = time.time()
    
    def get_total_latency_ms(self) -> float:
        """Get total latency in milliseconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0
    
    def get_ttft_ms(self) -> Optional[float]:
        """Get Time to First Token in milliseconds."""
        if self.start_time and self.first_token_time:
            return (self.first_token_time - self.start_time) * 1000
        return None
    
    def get_tps(self, output_tokens: int) -> Optional[float]:
        """
        Calculate Tokens Per Second.
        
        Args:
            output_tokens: Total number of output tokens
            
        Returns:
            Tokens per second, or None if calculation not possible
        """
        if self.first_token_time and self.end_time and output_tokens > 1:
            time_for_tokens = self.end_time - self.first_token_time
            if time_for_tokens > 0:
                return (output_tokens - 1) / time_for_tokens
        return None

