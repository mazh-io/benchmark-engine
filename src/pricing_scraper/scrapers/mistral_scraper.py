"""Mistral pricing scraper."""

import re
from typing import Dict, Any, List

from ..base_scraper import BasePricingScraper
from ..http_client import HTTPClient
from ..html_utils import html_to_text


class MistralScraper(BasePricingScraper):
    """
    Mistral AI pricing scraper.
    
    Scrapes Mistral's pricing page to extract model pricing.
    """
    
    def __init__(self, provider_key: str, provider_config: Dict[str, Any]):
        super().__init__(provider_key, provider_config)
        self.http_client = HTTPClient()
    
    def fetch_prices(self) -> List[Dict[str, Any]]:
        """Scrape prices from Mistral pricing page."""
        html = self.http_client.get_html(self.pricing_url)
        text = html_to_text(html)
        
        # Locate "Available models" section
        start = text.find("Available models")
        if start == -1:
            raise RuntimeError(f"[{self.provider_key}] Could not locate 'Available models' section")
        
        # End at "Free tier"
        end = text.find("Free tier", start)
        section = text[start : (end if end != -1 else None)]
        
        out: List[Dict[str, Any]] = []
        
        # Pattern: $input / $output / 1M tokens
        # e.g., "$0.15 / $0.60 / 1M tokens"
        pattern = re.compile(
            r"\$(?P<input>\d+(?:\.\d+)?)\s*/\s*\$(?P<output>\d+(?:\.\d+)?)\s*/\s*1M\s*tokens"
        )
        
        lines = section.split("\n")
        current_model: str | None = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line contains a model name (no $ sign, contains letters)
            if "$" not in line and re.search(r"[a-zA-Z]", line) and " " in line:
                # This could be a model name
                # Skip section headers
                if any(header in line.lower() for header in [
                    "available models", "pricing", "input", "output", "context"
                ]):
                    continue
                
                current_model = line.strip()
            
            # Check for pricing pattern
            m = pattern.search(line)
            if m and current_model:
                out.append({
                    "provider_key": self.provider_key,
                    "provider_name": self.provider_name,
                    "model_name": current_model,
                    "input_per_m": float(m.group("input")),
                    "output_per_m": float(m.group("output")),
                    "context_window": None,
                })
                current_model = None  # Reset after finding price
        
        if not out:
            raise RuntimeError(f"[{self.provider_key}] Parsed 0 rows (page structure likely changed)")
        
        return out
