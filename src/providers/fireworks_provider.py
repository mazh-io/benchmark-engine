"""
Fireworks AI Provider Integration.

Fireworks AI specializes in fast inference on standard GPUs with optimized serving infrastructure.
Famous for low latency on commodity hardware in the "Infrastructure War" benchmark.

API Documentation: https://readme.fireworks.ai/
"""

from typing import Dict, Any

from providers.openai_compatible_provider import create_openai_compatible_caller

# API Configuration
FIREWORKS_BASE_URL = "https://api.fireworks.ai/inference/v1"

# Model Pricing (USD per 1M tokens)
# Source: https://fireworks.ai/pricing (as of Jan 2025)
FIREWORKS_PRICING: Dict[str, Dict[str, float]] = {
    "accounts/fireworks/models/llama-v3p3-70b-instruct": {
        "input": 0.90,   # $0.90 per 1M input tokens
        "output": 0.90,  # $0.90 per 1M output tokens
    },
    "accounts/fireworks/models/llama-v3p1-70b-instruct": {
        "input": 0.90,
        "output": 0.90,
    },
    "accounts/fireworks/models/llama-v3p1-8b-instruct": {
        "input": 0.20,
        "output": 0.20,
    },
}

# Default pricing
FIREWORKS_DEFAULT_PRICING = {"input": 0.90, "output": 0.90}

# Create the callable function
call_fireworks = create_openai_compatible_caller(
    provider_name="fireworks",
    env_key_name="FIREWORKS_API_KEY",
    base_url=FIREWORKS_BASE_URL,
    pricing_table=FIREWORKS_PRICING,
    default_pricing=FIREWORKS_DEFAULT_PRICING
)

