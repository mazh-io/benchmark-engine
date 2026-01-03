"""
SambaNova Systems Provider Integration.

SambaNova specializes in custom AI chip architecture (Reconfigurable Dataflow Units).
Another competitor in the "Infrastructure War" benchmark testing custom silicon vs GPUs.

API Documentation: https://sambanova.ai/products/cloud
"""

from typing import Dict, Any

from providers.openai_compatible_provider import create_openai_compatible_caller

# API Configuration
SAMBANOVA_BASE_URL = "https://api.sambanova.ai/v1"

# Model Pricing (USD per 1M tokens)
# Note: Pricing may vary, check https://sambanova.ai/pricing
SAMBANOVA_PRICING: Dict[str, Dict[str, float]] = {
    "Meta-Llama-3.3-70B-Instruct": {
        "input": 0.60,   # $0.60 per 1M input tokens (estimated)
        "output": 0.60,  # $0.60 per 1M output tokens (estimated)
    },
    "Meta-Llama-3.1-70B-Instruct": {
        "input": 0.60,
        "output": 0.60,
    },
    "Meta-Llama-3.1-8B-Instruct": {
        "input": 0.10,
        "output": 0.10,
    },
}

# Default pricing
SAMBANOVA_DEFAULT_PRICING = {"input": 0.60, "output": 0.60}

# Create the callable function
call_sambanova = create_openai_compatible_caller(
    provider_name="sambanova",
    env_key_name="SAMBANOVA_API_KEY",
    base_url=SAMBANOVA_BASE_URL,
    pricing_table=SAMBANOVA_PRICING,
    default_pricing=SAMBANOVA_DEFAULT_PRICING
)

