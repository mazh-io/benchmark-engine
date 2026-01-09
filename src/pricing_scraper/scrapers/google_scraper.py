"""Google pricing scraper."""

import re
from typing import Dict, Any, List

from ..base_scraper import BasePricingScraper
from ..http_client import HTTPClient
from ..html_utils import html_to_text


class GoogleScraper(BasePricingScraper):
    """
    Google AI pricing scraper.
    
    Scrapes Google's Gemini pricing page to extract model pricing.
    """
    
    def __init__(self, provider_key: str, provider_config: Dict[str, Any]):
        super().__init__(provider_key, provider_config)
        self.http_client = HTTPClient()
    
    def fetch_prices(self) -> List[Dict[str, Any]]:
        """Scrape prices from Google Gemini pricing page."""
        html = self.http_client.get_html(self.pricing_url)
        text = html_to_text(html)
        
        # Locate "Pricing table" or "Models" section
        start = text.find("Pricing")
        if start == -1:
            start = text.find("Models")
        
        if start == -1:
            raise RuntimeError(f"[{self.provider_key}] Could not locate pricing section")
        
        section = text[start:]
        
        out: List[Dict[str, Any]] = []
        
        # Pattern: Model name followed by pricing in $X.XX / 1M tokens format
        # e.g., "Gemini 1.5 Flash Input: $0.075 Output: $0.30"
        pattern = re.compile(
            r"(?P<model>Gemini[^$\n]+?)"
            r"Input[:\s]*\$(?P<input>\d+(?:\.\d+)?)"
            r".*?"
            r"Output[:\s]*\$(?P<output>\d+(?:\.\d+)?)",
            flags=re.IGNORECASE | re.DOTALL
        )
        
        for m in pattern.finditer(section):
            model_name = m.group("model").strip()
            inp = m.group("input")
            outp = m.group("output")
            
            # Clean up model name
            model_name = re.sub(r"\s+", " ", model_name)
            
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
