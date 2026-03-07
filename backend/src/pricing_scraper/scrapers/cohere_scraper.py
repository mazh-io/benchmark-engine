"""Cohere pricing scraper."""

from typing import Dict, Any, List

from ..base_scraper import BasePricingScraper


class CohereScraper(BasePricingScraper):
    """
    Cohere pricing scraper.
    
    Returns hardcoded pricing data from Cohere's documentation.
    The Cohere pricing page is heavily JavaScript-rendered, making
    automated scraping complex and unreliable in production environments.
    
    Pricing verified from individual model doc pages:
    - https://docs.cohere.com/docs/command-a
    - https://docs.cohere.com/docs/command-r-plus
    - https://docs.cohere.com/docs/command-r
    - https://docs.cohere.com/docs/command-r7b
    - https://docs.cohere.com/docs/command-a-reasoning
    """
    
    def __init__(self, provider_key: str, provider_config: Dict[str, Any]):
        super().__init__(provider_key, provider_config)
    
    def fetch_prices(self) -> List[Dict[str, Any]]:
        """Fetch prices from Cohere.
        
        Returns hardcoded pricing data verified from Cohere documentation.
        Data verified as of 2026-03-07 from https://docs.cohere.com/docs/models
        
        Note: command-r and command-r-plus (without date suffix) were
        deprecated on September 15, 2025.
        """
        # Current live models with pricing (verified 2026-03-07)
        pricing_data = [
            # (model_name, input_per_m, output_per_m, context_window)
            ("command-a-03-2025", 2.50, 10.00, 256000),
            ("command-r-plus-08-2024", 2.50, 10.00, 128000),
            ("command-r-08-2024", 0.15, 0.60, 128000),
            ("command-r7b-12-2024", 0.0375, 0.15, 128000),
            ("command-a-reasoning-08-2025", 0.00, 0.00, 256000),  # Free tier
        ]
        
        out: List[Dict[str, Any]] = []
        for model_name, input_price, output_price, context_window in pricing_data:
            out.append({
                "provider_key": self.provider_key,
                "provider_name": self.provider_name,
                "model_name": model_name,
                "input_per_m": input_price,
                "output_per_m": output_price,
                "context_window": context_window,
            })
        
        return out
