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
    
    def fetch_available_models(self, provider_key: str) -> Dict[str, Any]:
        """
        Fetch available models from a provider by calling its fetch_models function.
        
        Args:
            provider_key: Provider key (e.g., "openai", "together")
            
        Returns:
            Dictionary with:
                - success: bool
                - models: List[str] (model IDs)
                - error: Optional[str]
                - note: Optional[str]
        """
        # Dynamic import to get provider's fetch_models function
        module_name = f"providers.{provider_key}_provider"
        function_name = f"fetch_models_{provider_key}"
        
        try:
            # Import the provider module
            module = __import__(module_name, fromlist=[function_name])
            # Get the fetch_models function
            fetch_function = getattr(module, function_name)
            # Call it and return result
            return fetch_function()
        except (ImportError, AttributeError) as e:
            return {
                "success": False,
                "models": [],
                "error": f"Failed to load fetch_models for '{provider_key}': {e}",
                "note": None
            }
        except Exception as e:
            return {
                "success": False,
                "models": [],
                "error": f"Error fetching models from '{provider_key}': {e}",
                "note": None
            }


# ============================================================================
# AVAILABLE MODELS - Cached from Provider APIs
# ============================================================================
# This dictionary stores models fetched from provider APIs.
# Updated by calling refresh_available_models()
# ============================================================================

AVAILABLE_MODELS: Dict[str, List[str]] = {}


def refresh_available_models(provider_key: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Fetch and cache available models from provider APIs.
    
    Args:
        provider_key: Optional provider to refresh. If None, refreshes all providers.
        
    Returns:
        Dictionary mapping provider keys to fetch results
    """
    service = get_provider_service()
    results = {}
    
    providers_to_fetch = [provider_key] if provider_key else list(PROVIDER_CONFIG.keys())
    
    for provider in providers_to_fetch:
        result = service.fetch_available_models(provider)
        
        if result["success"]:
            AVAILABLE_MODELS[provider] = result["models"]
        
        results[provider] = result
    
    return results


def get_available_models(provider_key: Optional[str] = None) -> Dict[str, List[str]]:
    """
    Get cached available models.
    
    Args:
        provider_key: Optional provider key. If None, returns all providers.
        
    Returns:
        Dictionary mapping provider keys to model lists
    """
    if provider_key:
        return {provider_key: AVAILABLE_MODELS.get(provider_key, [])}
    return AVAILABLE_MODELS.copy()


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
# HELPER FUNCTIONS
# ============================================================================

def is_reasoning_model(model: str) -> bool:
    """
    Detect if a model is a reasoning model that needs extended timeout.
    
    Reasoning models (DeepSeek R1, OpenAI o3/o4-mini) take 10-20s to "think"
    before sending the first token, requiring longer timeouts (120s vs 60s).
    
    This is the centralized source of truth for reasoning model detection,
    used by all providers to determine timeout configuration.
    
    Args:
        model: Model identifier (e.g., "deepseek-reasoner", "o3", "gpt-4o")
        
    Returns:
        True if reasoning model, False otherwise
        
    Example:
        >>> is_reasoning_model("deepseek-reasoner")
        True
        >>> is_reasoning_model("gpt-4o")
        False
    """
    # ACTIVE_MODELS is the single source of truth for model categorization
    for provider, model_id, category, notes in ACTIVE_MODELS:
        if model_id == model and category == "reasoning":
            return True
    
    return False


def get_timeout_for_model(model: str) -> float:
    """
    Get the appropriate HTTP timeout for a model.
    
    Args:
        model: Model identifier
        
    Returns:
        Timeout in seconds (120.0 for reasoning models, 60.0 for regular)
    """
    return 120.0 if is_reasoning_model(model) else 60.0


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
    ("together", "Qwen/Qwen3-Next-80B-A3B-Instruct", "flagship", "Chinese model"),
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


def sync_models_to_database() -> Dict[str, Any]:
    """
    Sync available models to database.
    
    This function:
    1. Fetches available models from all provider APIs
    2. Upserts them to database with active=false
    3. Marks models from ACTIVE_MODELS as active=true
    
    Returns:
        Dictionary with sync results
    """
    from database.db_connector import get_db_client
    
    db = get_db_client()
    results = {
        "success": True,
        "providers_synced": 0,
        "models_discovered": 0,
        "models_activated": 0,
        "errors": []
    }
    
    service = get_provider_service()
    
    # Fetch models from each provider
    for provider_key in PROVIDER_CONFIG.keys():
        try:
            print(f"Fetching models from {provider_key}...")
            fetch_result = service.fetch_available_models(provider_key)
            
            if fetch_result["success"]:
                model_names = fetch_result["models"]
                
                # Upsert models to database (active=false by default)
                success = db.upsert_models_from_discovery(provider_key, model_names)
                
                if success:
                    results["providers_synced"] += 1
                    results["models_discovered"] += len(model_names)
                    print(f"  ✓ {len(model_names)} models from {provider_key}")
                else:
                    results["errors"].append(f"{provider_key}: Database upsert failed")
            else:
                error_msg = fetch_result.get("error", "Unknown error")
                results["errors"].append(f"{provider_key}: {error_msg}")
                print(f"  ✗ {provider_key}: {error_msg}")
                
        except Exception as e:
            results["errors"].append(f"{provider_key}: {str(e)}")
            print(f"  ✗ {provider_key}: {str(e)}")
    
    # Mark active models from ACTIVE_MODELS config
    print("\nActivating models from ACTIVE_MODELS config...")
    active_by_provider = {}
    for provider_key, model_id, _, _ in ACTIVE_MODELS:
        if provider_key not in active_by_provider:
            active_by_provider[provider_key] = []
        active_by_provider[provider_key].append(model_id)
    
    for provider_key, model_names in active_by_provider.items():
        try:
            success = db.set_models_active(provider_key, model_names)
            if success:
                results["models_activated"] += len(model_names)
                print(f"  ✓ Activated {len(model_names)} models for {provider_key}")
            else:
                results["errors"].append(f"Failed to activate models for {provider_key}")
        except Exception as e:
            results["errors"].append(f"Activation error for {provider_key}: {str(e)}")
    
    if results["errors"]:
        results["success"] = False
    
    return results
