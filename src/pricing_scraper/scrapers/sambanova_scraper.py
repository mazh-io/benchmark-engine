"""SambaNova pricing scraper."""

import re
from typing import Dict, Any, List

from ..base_scraper import BasePricingScraper
from ..http_client import HTTPClient
from ..html_utils import html_to_text


class SambaNovaScraper(BasePricingScraper):
    """
    SambaNova pricing scraper.
    
    Scrapes SambaNova's pricing page to extract model pricing.
    """
    
    def __init__(self, provider_key: str, provider_config: Dict[str, Any]):
        super().__init__(provider_key, provider_config)
        self.http_client = HTTPClient()
    
    def fetch_prices(self) -> List[Dict[str, Any]]:
        """Scrape prices from SambaNova pricing page."""
        html = self.http_client.get_html(self.pricing_url)
        text = html_to_text(html)
        
        out: List[Dict[str, Any]] = []
        
        # Pattern: Model name followed by pricing
        # Looking for model names and associated prices
        pattern = re.compile(
            r"(?P<model>(Meta-)?Llama[^\n$]+?)"
            r".*?"
            r"Input[:\s]*\$(?P<input>\d+(?:\.\d+)?)"
            r".*?"
            r"Output[:\s]*\$(?P<output>\d+(?:\.\d+)?)",
            flags=re.IGNORECASE | re.DOTALL
        )
        
        for m in pattern.finditer(text):
            model_name = m.group("model").strip()
            inp = m.group("input")
            outp = m.group("output")
            
            # Clean up model name
            model_name = re.sub(r"\s+", " ", model_name)
            
            # Skip if model name is too long (likely not a real model name)
            if len(model_name) > 100:
                continue
            
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
