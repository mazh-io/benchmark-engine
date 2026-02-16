"""DeepSeek pricing scraper."""

import re
from typing import Dict, Any, List

from ..base_scraper import BasePricingScraper
from ..http_client import HTTPClient
from ..html_utils import html_to_text


class DeepSeekScraper(BasePricingScraper):
    """
    DeepSeek pricing scraper.
    
    Scrapes DeepSeek's pricing page to extract model pricing.
    """
    
    def __init__(self, provider_key: str, provider_config: Dict[str, Any]):
        super().__init__(provider_key, provider_config)
        self.http_client = HTTPClient()
    
    def fetch_prices(self) -> List[Dict[str, Any]]:
        """Scrape prices from DeepSeek API docs pricing page."""
        html = self.http_client.get_html(self.pricing_url)
        text = html_to_text(html)
        
        out: List[Dict[str, Any]] = []
        
        # The pricing table has models in the header row and pricing below
        # Format: "MODEL deepseek-chat deepseek-reasoner ... 1M INPUT TOKENS (CACHE MISS) $0.28 1M OUTPUT TOKENS $0.42"
        
        # Extract model names
        models = []
        model_match = re.search(r'MODEL\s+(deepseek-\w+)\s+(deepseek-\w+)', text)
        if model_match:
            models = [model_match.group(1), model_match.group(2)]
        
        # Extract cache miss input price
        input_match = re.search(r'1M INPUT TOKENS \(CACHE MISS\)\s+\$([0-9.]+)', text)
        input_price = float(input_match.group(1)) if input_match else None
        
        # Extract output price
        output_match = re.search(r'1M OUTPUT TOKENS\s+\$([0-9.]+)', text)
        output_price = float(output_match.group(1)) if output_match else None
        
        # Both models share the same pricing
        if models and input_price is not None and output_price is not None:
            for model_name in models:
                out.append({
                    "provider_key": self.provider_key,
                    "provider_name": self.provider_name,
                    "model_name": model_name,
                    "input_per_m": input_price,
                    "output_per_m": output_price,
                    "context_window": 128000,
                })
        
        if not out:
            raise RuntimeError(f"[{self.provider_key}] Parsed 0 rows (page structure likely changed)")
        
        return out
