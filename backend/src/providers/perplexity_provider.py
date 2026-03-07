"""
Perplexity Provider Integration.

Perplexity offers search-augmented LLMs — unique niche combining
real-time web search with language model generation.

API Documentation: https://docs.perplexity.ai/
Pricing: sonar-pro ~$3/$15, sonar ~$1/$1 per 1M tokens
"""

from typing import Dict, Any

from providers.openai_compatible_provider import create_openai_compatible_caller
from utils.constants import PROVIDER_CONFIG

# Create the callable function using factory pattern
# OpenAI-compatible API at https://api.perplexity.ai
call_perplexity = create_openai_compatible_caller(
    provider_name="perplexity",
    env_key_name="PERPLEXITY_API_KEY",
    base_url=PROVIDER_CONFIG["perplexity"]["base_url"],
    default_pricing=PROVIDER_CONFIG["perplexity"]["default_pricing"]
)


def fetch_models_perplexity():
    """
    Return known Perplexity models.

    Returns:
        Dictionary with success, models, and note
    """
    models = [
        "sonar-pro",
        "sonar",
    ]
    return {
        "success": True,
        "models": models,
        "error": None,
        "note": "Curated list - Perplexity search-augmented models"
    }
