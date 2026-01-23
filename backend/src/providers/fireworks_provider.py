"""
Fireworks AI Provider Integration.

Fireworks AI specializes in fast inference on standard GPUs with optimized serving infrastructure.
Famous for low latency on commodity hardware in the "Infrastructure War" benchmark.

API Documentation: https://readme.fireworks.ai/
Pricing: Fetched dynamically from database (updated via pricing scraper)
"""

from typing import Dict, Any

from providers.openai_compatible_provider import create_openai_compatible_caller
from utils.constants import PROVIDER_CONFIG

# Create the callable function
# Pricing is fetched from database, no hardcoded pricing table needed
call_fireworks = create_openai_compatible_caller(
    provider_name="fireworks",
    env_key_name="FIREWORKS_API_KEY",
    base_url=PROVIDER_CONFIG["fireworks"]["base_url"],
    default_pricing=PROVIDER_CONFIG["fireworks"]["default_pricing"]
)


def fetch_models_fireworks():
    """
    Return known Fireworks models.
    
    Returns:
        Dictionary with success, models, and note
    """
    models = [
        "accounts/fireworks/models/llama-v3p3-70b-instruct",
        "accounts/fireworks/models/llama-v3p1-405b-instruct",
        "accounts/fireworks/models/qwen2p5-72b-instruct",
    ]
    return {
        "success": True,
        "models": models,
        "error": None,
        "note": "Curated list - Fireworks AI models"
    }

