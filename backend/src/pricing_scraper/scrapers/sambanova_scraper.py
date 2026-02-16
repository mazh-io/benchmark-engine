"""SambaNova pricing scraper."""

from typing import Dict, Any, List

from ..base_scraper import BasePricingScraper


class SambaNovaScraper(BasePricingScraper):
    """
    SambaNova pricing scraper.
    
    Returns hardcoded pricing data for SambaNova Cloud models.
    The pricing page loads data dynamically via JavaScript.
    """
    
    def __init__(self, provider_key: str, provider_config: Dict[str, Any]):
        super().__init__(provider_key, provider_config)
    
    def fetch_prices(self) -> List[Dict[str, Any]]:
        """Fetch prices from SambaNova.
        
        Returns hardcoded pricing data for SambaNova Cloud models.
        Data verified as of 2026-01-09 from https://cloud.sambanova.ai/pricing
        """
        # SambaNova Cloud pricing (verified 2026-01-09)
        # Prices in USD per 1M tokens
        pricing_data = [
            ("Meta-Llama-3.1-8B-Instruct", 0.10, 0.10),
            ("Meta-Llama-3.1-70B-Instruct", 0.60, 0.60),
            ("Meta-Llama-3.1-405B-Instruct", 5.00, 10.00),
            ("Meta-Llama-3.2-1B-Instruct", 0.10, 0.10),
            ("Meta-Llama-3.2-3B-Instruct", 0.10, 0.10),
            ("Qwen2.5-72B-Instruct", 0.60, 0.60),
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
