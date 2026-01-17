"""
Provider Service

Dynamic provider registry that loads provider functions on-demand.
Eliminates circular imports and provides flexible provider management.
"""

from typing import List, Tuple, Callable, Optional, Dict, Any
from utils.constants import PROVIDER_CONFIG


class ProviderService:
    """
    Service for managing and accessing provider functions dynamically.
    
    Loads provider call functions lazily to avoid circular imports.
    Uses PROVIDER_CONFIG as the source of truth for available providers.
    """
    
    def __init__(self):
        """Initialize provider service."""
        self._provider_cache: Dict[str, Callable] = {}
        self._models_config: List[Tuple[str, str]] = []
    
    def _load_provider_function(self, provider_key: str) -> Callable:
        """
        Lazy-load provider call function.
        
        Args:
            provider_key: Provider key (e.g., "openai", "anthropic")
            
        Returns:
            Provider call function
            
        Raises:
            ImportError: If provider module not found
            AttributeError: If call function not found in module
        """
        if provider_key in self._provider_cache:
            return self._provider_cache[provider_key]
        
        # Dynamic import based on provider key
        module_name = f"providers.{provider_key}_provider"
        function_name = f"call_{provider_key}"
        
        try:
            # Import the provider module
            module = __import__(module_name, fromlist=[function_name])
            # Get the call function
            call_function = getattr(module, function_name)
            # Cache it
            self._provider_cache[provider_key] = call_function
            return call_function
        except (ImportError, AttributeError) as e:
            raise ImportError(f"Failed to load provider '{provider_key}': {e}")
    
    def register_model(self, provider_key: str, model_name: str):
        """
        Register a model to be benchmarked.
        
        Args:
            provider_key: Provider key (e.g., "openai")
            model_name: Model identifier (e.g., "gpt-4o-mini")
        """
        if provider_key not in PROVIDER_CONFIG:
            raise ValueError(f"Unknown provider: {provider_key}")
        
        self._models_config.append((provider_key, model_name))
    
    def get_providers(self) -> List[Tuple[str, Callable, str]]:
        """
        Get list of registered providers with their call functions.
        
        Returns:
            List of tuples: (provider_key, call_function, model_name)
        """
        providers = []
        for provider_key, model_name in self._models_config:
            try:
                call_function = self._load_provider_function(provider_key)
                providers.append((provider_key, call_function, model_name))
            except ImportError as e:
                print(f"Warning: Skipping {provider_key}/{model_name}: {e}")
        
        return providers
    
    def get_provider_function(self, provider_key: str) -> Callable:
        """
        Get call function for a specific provider.
        
        Args:
            provider_key: Provider key (e.g., "openai")
            
        Returns:
            Provider call function
        """
        return self._load_provider_function(provider_key)
    
    def clear_cache(self):
        """Clear the provider function cache. Useful for testing."""
        self._provider_cache.clear()
    
    def clear_models(self):
        """Clear registered models."""
        self._models_config.clear()


# Singleton instance
_provider_service: Optional[ProviderService] = None


def get_provider_service() -> ProviderService:
    """
    Get the singleton provider service instance.
    
    Returns:
        ProviderService instance
    """
    global _provider_service
    if _provider_service is None:
        _provider_service = ProviderService()
        _initialize_default_models()
    return _provider_service


# ============================================================================
# ACTIVE MODELS - Currently Used for Benchmarking
# ============================================================================
# These models are actively benchmarked in each run.
# Format: (provider, model_id, category, notes)
#
# Categories: flagship, budget, reasoning, speed, heavyweight, specialist
# ============================================================================

ACTIVE_MODELS = [
    # OpenAI - Industry Standard
    ("openai", "gpt-4o-mini", "budget", "Baseline budget model"),
    ("openai", "gpt-4o", "flagship", "GPT-4 Optimized flagship"),
    ("openai", "o3", "reasoning", "Latest reasoning model"),
    ("openai", "o4-mini", "reasoning", "Budget reasoning model"),
    
    # Anthropic - Developer Favorite
    ("anthropic", "claude-sonnet-4-5-20250929", "flagship", "Sonnet 4.5 flagship"),
    ("anthropic", "claude-haiku-4-5-20251001", "budget", "Haiku 4.5 fast & cheap"),
    ("anthropic", "claude-sonnet-4-20250514", "flagship", "Celebrity benchmark"),
    
    # Google - Gemini Latest
    ("google", "models/gemini-2.5-pro", "flagship", "Best quality"),
    ("google", "models/gemini-2.5-flash", "speed", "Fast & cheap"),
    
    # DeepSeek - Disruptive Pricing
    ("deepseek", "deepseek-chat", "budget", "V3 - Ultra budget"),
    ("deepseek", "deepseek-reasoner", "reasoning", "R1 - Reasoning"),
    
    # Groq - LPU Speed Champion
    ("groq", "llama-3.3-70b-versatile", "speed", "Latest Llama 3.3 on LPU"),
    ("groq", "llama-3.1-8b-instant", "speed", "Ultra-fast 8B"),
    
    # Together AI - GPU Cloud
    ("together", "mistralai/Mixtral-8x7B-Instruct-v0.1", "flagship", "Mixtral MoE"),
    ("together", "meta-llama/Llama-3.3-70B-Instruct-Turbo", "flagship", "Llama 3.3"),
    ("together", "Qwen/Qwen2.5-72B-Instruct-Turbo", "flagship", "Chinese model"),
    ("together", "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo", "heavyweight", "405B giant"),
    
    # Infrastructure Providers
    ("cerebras", "llama-3.3-70b", "speed", "Wafer-scale engine"),
    ("mistral", "mistral-large-latest", "flagship", "European flagship"),
    ("mistral", "codestral-latest", "specialist", "Code specialist"),
    ("fireworks", "accounts/fireworks/models/llama-v3p3-70b-instruct", "speed", "Low latency"),
    ("sambanova", "Meta-Llama-3.3-70B-Instruct", "flagship", "RDU chip"),
    
    # OpenRouter - Aggregator (Router Tax Analysis)
    ("openrouter", "openai/gpt-4o-mini", "budget", "Compare vs direct"),
    ("openrouter", "openai/gpt-4o", "flagship", "Compare vs direct"),
    ("openrouter", "meta-llama/llama-3.3-70b-instruct", "flagship", "Llama via router"),
    ("openrouter", "minimax/minimax-01", "flagship", "Chinese Claude challenger"),
    ("openrouter", "x-ai/grok-3", "flagship", "xAI Grok 3"),
    ("openrouter", "deepseek/deepseek-chat", "budget", "Compare vs direct"),
]

def _initialize_default_models():
    """Initialize models from ACTIVE_MODELS table."""
    service = _provider_service
    
    for provider, model, category, notes in ACTIVE_MODELS:
        service.register_model(provider, model)


def get_providers() -> List[Tuple[str, Callable, str]]:
    """
    Get list of all registered providers.
    
    Convenience function for backward compatibility.
    
    Returns:
        List of tuples: (provider_key, call_function, model_name)
    """
    return get_provider_service().get_providers()
