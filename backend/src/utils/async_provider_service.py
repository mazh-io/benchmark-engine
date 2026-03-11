"""
Async Provider Service

Dynamic provider registry that loads *async* provider functions on-demand.
Mirrors provider_service.py but resolves ``async_call_<provider>`` functions
from ``providers.async_*`` modules.

Re-exports ACTIVE_MODELS, is_reasoning_model, get_timeout_for_model from the
sync provider_service so callers don't need two imports.
"""

from typing import List, Tuple, Callable, Optional, Dict, Any

from utils.constants import PROVIDER_CONFIG
from utils.provider_service import (           # re-export unchanged helpers
    ACTIVE_MODELS,
    is_reasoning_model,
    get_timeout_for_model,
)


# ============================================================================
# Mapping: provider_key → (async_module, async_function_name)
# ============================================================================
# For OpenAI-compatible providers, we map to a special "FACTORY" sentinel.
# The factory needs (provider_name, env_key_name, base_url, default_pricing)
# which we pull from PROVIDER_CONFIG at load time.
#
# For custom SDK / legacy providers we map to a plain async function.
# ============================================================================

_FACTORY_SENTINEL = "__FACTORY__"

_ASYNC_PROVIDER_MAP: Dict[str, Tuple[str, str]] = {
    # --- OpenAI-compatible providers (factory) ---
    "deepseek":   ("providers.async_openai_compatible_provider", _FACTORY_SENTINEL),
    "cerebras":   ("providers.async_openai_compatible_provider", _FACTORY_SENTINEL),
    "mistral":    ("providers.async_openai_compatible_provider", _FACTORY_SENTINEL),
    "fireworks":  ("providers.async_openai_compatible_provider", _FACTORY_SENTINEL),
    "sambanova":  ("providers.async_openai_compatible_provider", _FACTORY_SENTINEL),
    "xai":        ("providers.async_openai_compatible_provider", _FACTORY_SENTINEL),
    "perplexity": ("providers.async_openai_compatible_provider", _FACTORY_SENTINEL),

    # --- Custom SDK providers ---
    "anthropic":  ("providers.async_anthropic_provider", "async_call_anthropic"),
    "google":     ("providers.async_google_provider", "async_call_google"),
    "cohere":     ("providers.async_cohere_provider", "async_call_cohere"),

    # --- Legacy standalone providers ---
    "openai":     ("providers.async_legacy_providers", "async_call_openai"),
    "groq":       ("providers.async_legacy_providers", "async_call_groq"),
    "together":   ("providers.async_legacy_providers", "async_call_together"),
    "openrouter": ("providers.async_legacy_providers", "async_call_openrouter"),
}


class AsyncProviderService:
    """
    Async mirror of ProviderService.

    Loads async call functions lazily and caches them.
    For factory-created providers (OpenAI-compatible), calls the factory
    with the correct (provider_name, env_key, base_url, pricing) args.
    """

    def __init__(self):
        self._provider_cache: Dict[str, Callable] = {}
        self._models_config: List[Tuple[str, str]] = []

    # ------------------------------------------------------------------
    def _load_async_provider_function(self, provider_key: str) -> Callable:
        if provider_key in self._provider_cache:
            return self._provider_cache[provider_key]

        if provider_key not in _ASYNC_PROVIDER_MAP:
            raise ImportError(
                f"No async mapping for provider '{provider_key}'. "
                f"Add it to _ASYNC_PROVIDER_MAP in async_provider_service.py"
            )

        module_name, function_name = _ASYNC_PROVIDER_MAP[provider_key]

        if function_name == _FACTORY_SENTINEL:
            # Factory path — import the factory and call it with full args
            mod = __import__(module_name, fromlist=["create_async_openai_compatible_caller"])
            factory = getattr(mod, "create_async_openai_compatible_caller")

            cfg = PROVIDER_CONFIG.get(provider_key, {})
            call_fn = factory(
                provider_name=provider_key,
                env_key_name=f"{provider_key.upper()}_API_KEY",
                base_url=cfg.get("base_url", ""),
                default_pricing=cfg.get("default_pricing"),
            )
        else:
            # Direct function import (custom SDK / legacy providers)
            mod = __import__(module_name, fromlist=[function_name])
            call_fn = getattr(mod, function_name)

        self._provider_cache[provider_key] = call_fn
        return call_fn

    # ------------------------------------------------------------------
    def register_model(self, provider_key: str, model_name: str):
        if provider_key not in PROVIDER_CONFIG:
            raise ValueError(f"Unknown provider: {provider_key}")
        self._models_config.append((provider_key, model_name))

    # ------------------------------------------------------------------
    def get_providers(self) -> List[Tuple[str, Callable, str]]:
        """Return list of (provider_key, async_call_function, model_name)."""
        providers = []
        for provider_key, model_name in self._models_config:
            try:
                call_fn = self._load_async_provider_function(provider_key)
                providers.append((provider_key, call_fn, model_name))
            except ImportError as e:
                print(f"Warning: Skipping {provider_key}/{model_name}: {e}")
        return providers

    # ------------------------------------------------------------------
    def get_provider_function(self, provider_key: str) -> Callable:
        return self._load_async_provider_function(provider_key)

    def clear_cache(self):
        self._provider_cache.clear()

    def clear_models(self):
        self._models_config.clear()


# ============================================================================
# Singleton
# ============================================================================

_async_provider_service: Optional[AsyncProviderService] = None


def get_async_provider_service() -> AsyncProviderService:
    global _async_provider_service
    if _async_provider_service is None:
        _async_provider_service = AsyncProviderService()
        _initialize_async_default_models()
    return _async_provider_service


def _initialize_async_default_models():
    service = _async_provider_service
    for provider, model, _category, _notes in ACTIVE_MODELS:
        service.register_model(provider, model)


def get_async_providers() -> List[Tuple[str, Callable, str]]:
    """Convenience function — mirrors get_providers() from sync module."""
    return get_async_provider_service().get_providers()
