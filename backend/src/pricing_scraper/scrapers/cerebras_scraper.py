"""Cerebras pricing scraper."""

from typing import Dict, Any, List

from ..base_scraper import BasePricingScraper


class CerebrasScraper(BasePricingScraper):
    """
    Cerebras pricing scraper.
    
    Returns hardcoded pricing data from Cerebras Developer tier.
    The Cerebras pricing page is heavily JavaScript-rendered, making
    automated scraping complex and unreliable in production environments.
    """
    
    def __init__(self, provider_key: str, provider_config: Dict[str, Any]):
        super().__init__(provider_key, provider_config)
    
    def fetch_prices(self) -> List[Dict[str, Any]]:
        """Fetch prices from Cerebras.
        
        Returns hardcoded pricing data from Developer tier.
        Data verified as of 2026-01-09 from https://www.cerebras.ai/pricing
        """
        # Developer tier pricing (verified 2026-01-09)
        pricing_data = [
            ("ZAI GLM 4.7", 2.25, 2.75),
            ("ZAI GLM 4.6", 2.25, 2.75),
            ("OPENAI GPT OSS 120B", 0.35, 0.75),
            ("META Llama 3.1 8B", 0.10, 0.10),
            ("META Llama 3.3 70B", 0.85, 1.20),
            ("QWEN Qwen 3 32B", 0.40, 0.80),
            ("QWEN Qwen 3 235B Instruct", 0.60, 1.20),
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
