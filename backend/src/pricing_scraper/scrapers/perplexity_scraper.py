"""Perplexity pricing scraper."""

from typing import Dict, Any, List

from ..base_scraper import BasePricingScraper


class PerplexityScraper(BasePricingScraper):
    """
    Perplexity pricing scraper.
    
    Returns hardcoded pricing data from Perplexity's documentation.
    
    Note: Perplexity Sonar models also have per-request fees for search
    ($0.005/request) on top of token costs. Only token pricing is tracked here
    since the benchmark engine measures per-token costs.
    
    Pricing verified from:
    - https://docs.perplexity.ai/guides/pricing
    """
    
    def __init__(self, provider_key: str, provider_config: Dict[str, Any]):
        super().__init__(provider_key, provider_config)
    
    def fetch_prices(self) -> List[Dict[str, Any]]:
        """Fetch prices from Perplexity.
        
        Returns hardcoded pricing data verified from Perplexity documentation.
        Data verified as of 2026-03-07 from https://docs.perplexity.ai/guides/pricing
        """
        # Sonar API token pricing (verified 2026-03-07)
        # Format: (model_name, input_per_m, output_per_m, context_window)
        pricing_data = [
            ("sonar", 1.00, 1.00, 128000),
            ("sonar-pro", 3.00, 15.00, 200000),
            ("sonar-reasoning-pro", 2.00, 8.00, 128000),
            ("sonar-deep-research", 2.00, 8.00, 128000),
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
