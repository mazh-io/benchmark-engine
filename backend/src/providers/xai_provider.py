"""
xAI (Grok) Provider Integration.

xAI builds Grok models — direct API access for true latency measurement
without OpenRouter's router tax.

API Documentation: https://docs.x.ai/
Pricing: grok-3 $3/$15 per 1M tokens, grok-3-mini TBD
"""

from typing import Dict, Any

from providers.openai_compatible_provider import create_openai_compatible_caller
from utils.constants import PROVIDER_CONFIG

# Create the callable function using factory pattern
# OpenAI-compatible API at https://api.x.ai/v1
call_xai = create_openai_compatible_caller(
    provider_name="xai",
    env_key_name="XAI_API_KEY",
    base_url=PROVIDER_CONFIG["xai"]["base_url"],
    default_pricing=PROVIDER_CONFIG["xai"]["default_pricing"]
)


def fetch_models_xai():
    """
    Return known xAI Grok models.

    Returns:
        Dictionary with success, models, and note
    """
    models = [
        "grok-3",
        "grok-3-mini",
    ]
    return {
        "success": True,
        "models": models,
        "error": None,
        "note": "Curated list - xAI Grok models"
    }
