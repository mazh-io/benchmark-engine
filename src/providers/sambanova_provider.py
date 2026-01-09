"""
SambaNova Systems Provider Integration.

SambaNova specializes in custom AI chip architecture (Reconfigurable Dataflow Units).
Another competitor in the "Infrastructure War" benchmark testing custom silicon vs GPUs.

API Documentation: https://sambanova.ai/products/cloud
Pricing: Fetched dynamically from database (updated via pricing scraper)
"""

from typing import Dict, Any

from providers.openai_compatible_provider import create_openai_compatible_caller
from utils.constants import PROVIDER_CONFIG

# Create the callable function
# Pricing is fetched from database, no hardcoded pricing table needed
call_sambanova = create_openai_compatible_caller(
    provider_name="sambanova",
    env_key_name="SAMBANOVA_API_KEY",
    base_url=PROVIDER_CONFIG["sambanova"]["base_url"],
    default_pricing=PROVIDER_CONFIG["sambanova"]["default_pricing"]
)

