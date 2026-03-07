"""xAI (Grok) pricing scraper."""

from typing import Dict, Any, List

from ..base_scraper import BasePricingScraper


class XAIScraper(BasePricingScraper):
    """
    xAI pricing scraper.
    
    Returns hardcoded pricing data from xAI's documentation.
    
    Pricing verified from:
    - https://docs.x.ai/docs/models
    """
    
    def __init__(self, provider_key: str, provider_config: Dict[str, Any]):
        super().__init__(provider_key, provider_config)
    
    def fetch_prices(self) -> List[Dict[str, Any]]:
        """Fetch prices from xAI.
        
        Returns hardcoded pricing data verified from xAI documentation.
        Data verified as of 2026-03-07 from https://docs.x.ai/developers/models
        """
        # xAI Grok model pricing (verified 2026-03-07)
        # Format: (model_name, input_per_m, output_per_m, context_window)
        pricing_data = [
            ("grok-4-0709", 3.00, 15.00, 256000),
            ("grok-4-fast-reasoning", 0.20, 0.50, 2000000),
            ("grok-4-fast-non-reasoning", 0.20, 0.50, 2000000),
            ("grok-4-1-fast-reasoning", 0.20, 0.50, 2000000),
            ("grok-4-1-fast-non-reasoning", 0.20, 0.50, 2000000),
            ("grok-code-fast-1", 0.20, 1.50, 256000),
            ("grok-3", 3.00, 15.00, 131072),
            ("grok-3-mini", 0.30, 0.50, 131072),
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
