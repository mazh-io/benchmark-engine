"""
Mistral AI Provider Integration.

Mistral AI is a European AI company specializing in open and efficient models.
Known for "mistral-large-latest" - the best European flagship model.

API Documentation: https://docs.mistral.ai/
Pricing: Fetched dynamically from database (updated via pricing scraper)
"""

from typing import Dict, Any

from providers.openai_compatible_provider import create_openai_compatible_caller
from utils.constants import PROVIDER_CONFIG

# Create the callable function using factory pattern
# Pricing is fetched from database, no hardcoded pricing table needed
call_mistral = create_openai_compatible_caller(
    provider_name="mistral",
    env_key_name="MISTRAL_API_KEY",
    base_url=PROVIDER_CONFIG["mistral"]["base_url"],
    default_pricing=PROVIDER_CONFIG["mistral"]["default_pricing"]
)


def fetch_models_mistral():
    """
    Return known Mistral models.
    
    Returns:
        Dictionary with success, models, and note
    """
    models = [
        "mistral-large-latest",
        "mistral-medium-latest",
        "mistral-small-latest",
        "codestral-latest",
        "open-mistral-nemo",
    ]
    return {
        "success": True,
        "models": models,
        "error": None,
        "note": "Curated list - Mistral AI models"
    }

