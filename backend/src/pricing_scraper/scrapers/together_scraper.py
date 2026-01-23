"""Together AI pricing scraper."""

from typing import Dict, Any, List

from ..base_scraper import BasePricingScraper
from ..http_client import HTTPClient
from utils.env_helper import get_env


class TogetherScraper(BasePricingScraper):
    """
    Together AI pricing scraper.
    
    Uses Together's authenticated API endpoint to fetch model pricing.
    Requires TOGETHER_API_KEY environment variable.
    """
    
    def __init__(self, provider_key: str, provider_config: Dict[str, Any]):
        super().__init__(provider_key, provider_config)
        self.http_client = HTTPClient()
        self.api_key = get_env("TOGETHER_API_KEY")
    
    def fetch_prices(self) -> List[Dict[str, Any]]:
        """Fetch prices from Together AI API."""
        if not self.api_key:
            print(f"[{self.provider_key}] Skipping (missing TOGETHER_API_KEY)")
            return []
        
        models_url = self.provider_config.get("models_url")
        if not models_url:
            raise ValueError(f"Missing 'models_url' in config for {self.provider_key}")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        
        data = self.http_client.get_json(models_url, headers)
        
        # Handle both list and dict responses
        models = data if isinstance(data, list) else data.get("data") or data.get("models") or []
        
        out: List[Dict[str, Any]] = []
        for m in models:
            model_id = m.get("id")
            pricing = m.get("pricing") or {}
            inp = pricing.get("input")
            outp = pricing.get("output")
            ctx = m.get("context_length")
            
            if not model_id or inp is None or outp is None:
                continue
            
            # Skip free models
            if float(inp) == 0.0 and float(outp) == 0.0:
                continue
            
            out.append({
                "provider_key": self.provider_key,
                "provider_name": self.provider_name,
                "model_name": str(model_id),
                "input_per_m": float(inp),
                "output_per_m": float(outp),
                "context_window": int(ctx) if isinstance(ctx, (int, float)) else None,
            })
        
        return out
