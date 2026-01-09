"""Google pricing scraper."""

from typing import Dict, Any, List

from ..base_scraper import BasePricingScraper


class GoogleScraper(BasePricingScraper):
    """
    Google AI pricing scraper.
    
    Returns hardcoded pricing data for Gemini models.
    The pricing page shows tier information but not detailed model pricing.
    """
    
    def __init__(self, provider_key: str, provider_config: Dict[str, Any]):
        super().__init__(provider_key, provider_config)
    
    def fetch_prices(self) -> List[Dict[str, Any]]:
        """Fetch prices from Google Gemini.
        
        Returns hardcoded pricing data for Gemini models.
        Data verified as of 2026-01-09 from https://ai.google.dev/pricing
        Note: For more complete Google pricing, see OpenRouter which includes
        many Gemini models.
        """
        # Gemini model pricing (verified 2026-01-09)
        # Prices in USD per 1M tokens
        pricing_data = [
            ("gemini-1.5-flash", 0.075, 0.30),
            ("gemini-1.5-flash-8b", 0.0375, 0.15),
            ("gemini-1.5-pro", 1.25, 5.00),
            ("gemini-2.0-flash-exp", 0.075, 0.30),
            ("gemini-exp-1206", 0.075, 0.30),
        ]
        
        out: List[Dict[str, Any]] = []
        for model_name, input_price, output_price in pricing_data:
            out.append({
                "provider_key": self.provider_key,
                "provider_name": self.provider_name,
                "model_name": model_name,
                "input_per_m": input_price,
                "output_per_m": output_price,
                "context_window": None,
            })
        
        return out
