"""Anthropic pricing scraper."""

import re
from typing import Dict, Any, List

from ..base_scraper import BasePricingScraper
from ..http_client import HTTPClient
from ..html_utils import html_to_text


class AnthropicScraper(BasePricingScraper):
    """
    Anthropic pricing scraper.
    
    Scrapes Anthropic's pricing page to extract Claude model pricing.
    """
    
    def __init__(self, provider_key: str, provider_config: Dict[str, Any]):
        super().__init__(provider_key, provider_config)
        self.http_client = HTTPClient()
    
    def fetch_prices(self) -> List[Dict[str, Any]]:
        """Scrape prices from Anthropic pricing page."""
        html = self.http_client.get_html(self.pricing_url)
        text = html_to_text(html)
        
        # Collapse whitespace
        collapsed = re.sub(r"\s+", "", text)
        
        # Pattern: Model name followed by input and output prices
        # e.g., "Claude3.5Sonnet Input $3 Output $15"
        pattern = re.compile(
            r"(?P<model>Claude[^$]+?)"
            r"Input\$(?P<input>\d+(?:\.\d+)?)"
            r".*?"
            r"Output\$(?P<output>\d+(?:\.\d+)?)"
        )
        
        out: List[Dict[str, Any]] = []
        
        for m in pattern.finditer(collapsed):
            model_raw = m.group("model")
            inp = m.group("input")
            outp = m.group("output")
            
            # Clean model name: convert "Claude3.5Sonnet" -> "Claude 3.5 Sonnet"
            model_name = re.sub(r"(\d)", r" \1", model_raw).strip()
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
