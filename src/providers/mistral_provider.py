"""
Mistral AI Provider Integration.

Mistral AI is a European AI company specializing in open and efficient models.
Known for "mistral-large-latest" - the best European flagship model.

API Documentation: https://docs.mistral.ai/
"""

from typing import Dict, Any

from providers.openai_compatible_provider import create_openai_compatible_caller

# API Configuration
MISTRAL_BASE_URL = "https://api.mistral.ai/v1"

# Model Pricing (USD per 1M tokens)
# Source: https://mistral.ai/pricing (as of Jan 2025)
MISTRAL_PRICING: Dict[str, Dict[str, float]] = {
    "mistral-large-latest": {
        "input": 2.00,   # $2.00 per 1M input tokens
        "output": 6.00,  # $6.00 per 1M output tokens
    },
    "mistral-medium-latest": {
        "input": 0.50,
        "output": 1.50,
    },
    "mistral-small-latest": {
        "input": 0.20,
        "output": 0.60,
    },
}

# Default pricing for unknown models
MISTRAL_DEFAULT_PRICING = {"input": 2.00, "output": 6.00}

# Create the callable function using factory pattern
call_mistral = create_openai_compatible_caller(
    provider_name="mistral",
    env_key_name="MISTRAL_API_KEY",
    base_url=MISTRAL_BASE_URL,
    pricing_table=MISTRAL_PRICING,
    default_pricing=MISTRAL_DEFAULT_PRICING
)

