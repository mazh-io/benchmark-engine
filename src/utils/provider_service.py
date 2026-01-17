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


def _initialize_default_models():
    """Initialize default model configurations."""
    service = _provider_service

    # Phase 0 - MVP (Existing providers with updates)
    # OpenAI - Industry standard
    service.register_model("openai", "gpt-4o-mini")          # Baseline budget model
    service.register_model("openai", "gpt-4o")               # Flagship
    service.register_model("openai", "o3")                   # New reasoning model
    service.register_model("openai", "o4-mini")              # New budget reasoning model
    
    # Groq - LPU benchmark (updated to latest)
    service.register_model("groq", "llama-3.3-70b-versatile")  # Latest Llama 3.3
    
    # Together AI - GPU cloud
    service.register_model("together", "mistralai/Mixtral-8x7B-Instruct-v0.1")  # Existing
    service.register_model("together", "meta-llama/Llama-3.3-70B-Instruct-Turbo")  # Infrastructure War
    
    # OpenRouter - Aggregator
    service.register_model("openrouter", "openai/gpt-4o-mini")  # Baseline
    service.register_model("openrouter", "meta-llama/llama-3.3-70b-instruct")  # Infrastructure War
    service.register_model("openrouter", "minimax/minimax-01")  # Challenger to Claude
    
    # Phase 2 - OpenAI Compatible
    # DeepSeek - Budget champion with disruptive pricing
    service.register_model("deepseek", "deepseek-chat")      # V3 - Budget model
    service.register_model("deepseek", "deepseek-reasoner")  # R1 - Reasoning model
    
    # Cerebras - Infrastructure War competitor (Groq challenger)
    service.register_model("cerebras", "llama-3.3-70b")
    
    # Mistral - European flagship
    service.register_model("mistral", "mistral-large-latest")
    
    # Fireworks - Low latency on standard GPUs
    service.register_model("fireworks", "accounts/fireworks/models/llama-v3p3-70b-instruct")
    
    # SambaNova - Custom chip architecture
    service.register_model("sambanova", "Meta-Llama-3.3-70B-Instruct")
    
    # Phase 3 - Custom SDK Providers
    # Anthropic Claude 4.5 - NEW VERSION (3.5 retired Oct 2025)
    service.register_model("anthropic", "claude-sonnet-4-5-20250929")  # Flagship (Sonnet 4.5)
    service.register_model("anthropic", "claude-haiku-4-5-20251001")   # Budget (Haiku 4.5)
    
    # Google Gemini - NEW SDK with Gemini 2.5
    service.register_model("google", "models/gemini-2.5-pro")    # Latest Pro - best quality
    service.register_model("google", "models/gemini-2.5-flash")  # Latest Flash - fast & cheap

    # ============================================================
    # BATTLE MAP ADDITIONS
    # ============================================================
    
    # 1. "East vs. West" Front (China Models)
    service.register_model("together", "Qwen/Qwen2.5-72B-Instruct-Turbo")  # CRITICAL
    
    # 2. "Heavyweight" Division (405B Giants) 
    service.register_model("together", "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo")  # CRITICAL
    
    # # 3. "Celebrity & Specialist" Class 
    service.register_model("openrouter", "x-ai/grok-3")  # xAI Grok 3 flagship - $3/$15 per 1M tokens
    service.register_model("anthropic", "claude-sonnet-4-20250514")  # Celebrity benchmark
    service.register_model("mistral", "codestral-latest")  # Mistral code specialist
    service.register_model("groq", "llama-3.1-8b-instant")  # Replacement for deprecated gemma2-9b-it
    
    # # 4. "Router Tax" Proof (B2B)  - Compare OpenRouter vs Direct
    service.register_model("openrouter", "deepseek/deepseek-chat")  # vs Direct DeepSeek
    service.register_model("openrouter", "openai/gpt-4o")  # vs Direct OpenAI


def get_providers() -> List[Tuple[str, Callable, str]]:
    """
    Get list of all registered providers.
    
    Convenience function for backward compatibility.
    
    Returns:
        List of tuples: (provider_key, call_function, model_name)
    """
    return get_provider_service().get_providers()
