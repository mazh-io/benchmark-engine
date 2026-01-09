"""OpenRouter pricing scraper."""

import re
from typing import Dict, Any, List

from ..base_scraper import BasePricingScraper
from ..http_client import HTTPClient


class OpenRouterScraper(BasePricingScraper):
    """
    OpenRouter pricing scraper.
    
    Scrapes OpenRouter's models page which displays pricing information.
    """
    
    def __init__(self, provider_key: str, provider_config: Dict[str, Any]):
        super().__init__(provider_key, provider_config)
        self.http_client = HTTPClient()
    
    def fetch_prices(self) -> List[Dict[str, Any]]:
        """Fetch prices from OpenRouter API endpoint."""
        # Use the public API endpoint instead of scraping HTML
        api_url = "https://openrouter.ai/api/v1/models"
        
        data = self.http_client.get_json(api_url)
        
        if not data or "data" not in data:
            print(f"✗ Failed to parse OpenRouter API response")
            return []
        
        out: List[Dict[str, Any]] = []
        for model_info in data["data"]:
            model_id = model_info.get("id", "")
            pricing = model_info.get("pricing", {})
            
            # Get prompt (input) and completion (output) prices
            # Prices are in dollars per token, multiply by 1M to get per-million
            prompt_price = pricing.get("prompt")
            completion_price = pricing.get("completion")
            
            # Skip models with invalid pricing
            if not prompt_price or not completion_price or prompt_price == "-1" or completion_price == "-1":
                continue
            
            # Convert from per-token to per-million-tokens
            try:
                inp = float(prompt_price) * 1_000_000
                outp = float(completion_price) * 1_000_000
            except (ValueError, TypeError):
                continue
            
            out.append({
                "provider_key": self.provider_key,
                "provider_name": self.provider_name,
                "model_name": model_id,  # Full model path like "openai/gpt-4o"
                "input_per_m": inp,
                "output_per_m": outp,
                "context_window": model_info.get("context_length"),
            })
        
        if not out:
            raise RuntimeError(f"[{self.provider_key}] Parsed 0 rows (API returned no valid pricing)")
        
        return out
