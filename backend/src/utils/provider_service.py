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
    # ===== OpenAI (12) =====
    ("openai", "gpt-4o-mini", "budget", ""),
    ("openai", "gpt-4o", "flagship", ""),
    ("openai", "gpt-4.1", "flagship", ""),
    ("openai", "gpt-4.1-mini", "budget", ""),
    ("openai", "gpt-4.1-nano", "budget", ""),
    ("openai", "gpt-5-mini", "reasoning", ""),
    ("openai", "gpt-5.1", "flagship", ""),
    ("openai", "gpt-5.2", "flagship", ""),
    ("openai", "gpt-5.4", "flagship", "Latest GPT"),
    ("openai", "o3", "reasoning", ""),
    ("openai", "o3-mini", "reasoning", "Budget reasoning"),
    ("openai", "o4-mini", "reasoning", ""),

    # ===== Anthropic (8) =====
    ("anthropic", "claude-haiku-4-5-20251001", "budget", ""),
    ("anthropic", "claude-sonnet-4-5-20250929", "flagship", ""),
    ("anthropic", "claude-sonnet-4-20250514", "flagship", ""),
    ("anthropic", "claude-sonnet-4-6", "flagship", "Latest Sonnet"),
    ("anthropic", "claude-opus-4-20250514", "heavyweight", ""),
    ("anthropic", "claude-opus-4-1-20250805", "flagship", ""),
    ("anthropic", "claude-opus-4-5-20251101", "heavyweight", ""),
    ("anthropic", "claude-opus-4-6", "flagship", "Latest Opus"),

    # ===== Google (6) =====
    ("google", "models/gemini-2.5-flash", "speed", ""),
    ("google", "models/gemini-2.5-flash-lite", "budget", ""),
    ("google", "models/gemini-2.5-pro", "flagship", ""),
    ("google", "models/gemini-3-flash-preview", "speed", ""),
    ("google", "models/gemini-3-pro-preview", "flagship", ""),
    ("google", "models/gemini-3.1-pro-preview", "flagship", "Latest Gemini"),

    # ===== DeepSeek (2) =====
    ("deepseek", "deepseek-chat", "budget", "V3.2"),
    ("deepseek", "deepseek-reasoner", "reasoning", "R1"),

    # ===== xAI (4) =====
    ("xai", "grok-3", "flagship", ""),
    ("xai", "grok-3-mini", "reasoning", ""),
    ("xai", "grok-4-0709", "flagship", "Grok 4"),
    ("xai", "grok-4-1-fast-non-reasoning", "speed", "Grok 4.1"),

    # ===== Mistral (6) =====
    ("mistral", "mistral-small-latest", "budget", ""),
    ("mistral", "mistral-medium-latest", "flagship", ""),
    ("mistral", "mistral-large-latest", "flagship", ""),
    ("mistral", "codestral-latest", "specialist", "Code"),
    ("mistral", "magistral-medium-latest", "reasoning", ""),
    ("mistral", "magistral-small-latest", "reasoning", "Budget"),

    # ===== Groq (6) =====
    ("groq", "llama-3.1-8b-instant", "speed", ""),
    ("groq", "llama-3.3-70b-versatile", "speed", ""),
    ("groq", "meta-llama/llama-4-scout-17b-16e-instruct", "flagship", ""),
    ("groq", "moonshotai/kimi-k2-instruct", "flagship", "Kimi on LPU"),
    ("groq", "openai/gpt-oss-20b", "budget", ""),
    ("groq", "qwen/qwen3-32b", "flagship", "Qwen3 on LPU"),

    # ===== Together AI (11) =====
    ("together", "mistralai/Mixtral-8x7B-Instruct-v0.1", "flagship", ""),
    ("together", "meta-llama/Llama-3.3-70B-Instruct-Turbo", "flagship", ""),
    ("together", "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8", "flagship", ""),
    ("together", "Qwen/Qwen3-Next-80B-A3B-Instruct", "flagship", ""),
    ("together", "Qwen/Qwen3.5-397B-A17B", "flagship", "Latest Qwen"),
    ("together", "deepseek-ai/DeepSeek-V3.1", "flagship", ""),
    ("together", "deepseek-ai/DeepSeek-R1", "reasoning", ""),
    ("together", "MiniMaxAI/MiniMax-M2.5", "flagship", ""),
    ("together", "zai-org/GLM-5", "flagship", "Top open-source"),
    ("together", "zai-org/GLM-4.7", "flagship", ""),
    ("together", "openai/gpt-oss-20b", "budget", ""),

    # ===== Cerebras (4) =====
    ("cerebras", "llama3.1-8b", "speed", ""),
    ("cerebras", "gpt-oss-120b", "flagship", ""),
    ("cerebras", "qwen-3-235b-a22b-instruct-2507", "flagship", "Qwen3 at Cerebras speed"),
    ("cerebras", "zai-glm-4.7", "flagship", "GLM at Cerebras speed"),

    # ===== Fireworks (2) =====
    ("fireworks", "accounts/fireworks/models/llama-v3p3-70b-instruct", "speed", ""),
    ("fireworks", "accounts/fireworks/models/deepseek-v3p2", "flagship", "DeepSeek V3.2"),

    # ===== SambaNova (5) — free-tier rate limit, uses inter_call_delay_s throttling =====
    ("sambanova", "Meta-Llama-3.3-70B-Instruct", "flagship", ""),
    ("sambanova", "Llama-4-Maverick-17B-128E-Instruct", "flagship", ""),
    ("sambanova", "DeepSeek-V3.2", "flagship", ""),
    ("sambanova", "Qwen3-235B", "flagship", ""),
    ("sambanova", "Qwen3-32B", "flagship", ""),

    # ===== Perplexity (2) =====
    ("perplexity", "sonar-pro", "flagship", "Search-augmented"),
    ("perplexity", "sonar", "budget", ""),

    # ===== Cohere (2) =====
    ("cohere", "command-a-03-2025", "flagship", "Enterprise RAG"),
    ("cohere", "command-r7b-12-2024", "budget", ""),

    # ===== OpenRouter (15) — Router tax + exclusive models =====
    ("openrouter", "openai/gpt-4o-mini", "budget", "vs direct"),
    ("openrouter", "openai/gpt-4o", "flagship", "vs direct"),
    ("openrouter", "openai/gpt-4.1", "flagship", "vs direct"),
    ("openrouter", "deepseek/deepseek-chat", "budget", "vs direct"),
    ("openrouter", "meta-llama/llama-3.3-70b-instruct", "flagship", "vs direct"),
    ("openrouter", "meta-llama/llama-4-maverick", "flagship", ""),
    ("openrouter", "x-ai/grok-3", "flagship", "vs direct"),
    ("openrouter", "x-ai/grok-4", "flagship", "vs direct"),
    ("openrouter", "minimax/minimax-01", "flagship", ""),
    ("openrouter", "minimax/minimax-m2.5", "flagship", ""),
    ("openrouter", "z-ai/glm-5", "flagship", "Top open-source"),
    ("openrouter", "moonshotai/kimi-k2.5", "flagship", ""),
    ("openrouter", "xiaomi/mimo-v2-flash", "speed", ""),
    ("openrouter", "qwen/qwen3-max", "flagship", "Alibaba commercial"),
    ("openrouter", "deepseek/deepseek-v3.2", "flagship", "vs SambaNova"),
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
