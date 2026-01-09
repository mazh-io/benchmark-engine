"""Fireworks pricing scraper."""

import re
from typing import Dict, Any, List

from ..base_scraper import BasePricingScraper
from ..http_client import HTTPClient
from ..html_utils import html_to_text


class FireworksScraper(BasePricingScraper):
    """
    Fireworks AI pricing scraper.
    
    Scrapes Fireworks's pricing page to extract model pricing.
    """
    
    def __init__(self, provider_key: str, provider_config: Dict[str, Any]):
        super().__init__(provider_key, provider_config)
        self.http_client = HTTPClient()
    
    def fetch_prices(self) -> List[Dict[str, Any]]:
        """Scrape prices from Fireworks pricing page."""
        html = self.http_client.get_html(self.pricing_url)
        text = html_to_text(html)
        
        out: List[Dict[str, Any]] = []
        
        # Pattern: Model name followed by pricing in per million tokens format
        # e.g., "Llama 3.1 405B $3.00 $3.00"
        lines = text.split("\n")
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for model names (typically contain version numbers and sizes)
            if re.search(r"(llama|qwen|mixtral|deepseek)", line, re.IGNORECASE):
                # Check next few lines for pricing
                pricing_text = " ".join(lines[i:i+3])
                
                # Extract prices - look for two dollar amounts
                prices = re.findall(r"\$(\d+(?:\.\d+)?)", pricing_text)
                
                if len(prices) >= 2:
                    model_name = line
                    inp = prices[0]
                    outp = prices[1]
                    
                    out.append({
                        "provider_key": self.provider_key,
                        "provider_name": self.provider_name,
                        "model_name": model_name,
                        "input_per_m": float(inp),
                        "output_per_m": float(outp),
                        "context_window": None,
                    })
        
        if not out:
            raise RuntimeError(f"[{self.provider_key}] Parsed 0 rows (page structure likely changed)")
        
        return out
