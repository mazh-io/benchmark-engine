"""Groq pricing scraper."""

import re
from typing import Dict, Any, List

from ..base_scraper import BasePricingScraper
from ..http_client import HTTPClient
from ..html_utils import html_to_text


class GroqScraper(BasePricingScraper):
    """
    Groq pricing scraper.
    
    Scrapes Groq's pricing page to extract LLM model pricing.
    """
    
    def __init__(self, provider_key: str, provider_config: Dict[str, Any]):
        super().__init__(provider_key, provider_config)
        self.http_client = HTTPClient()
    
    def fetch_prices(self) -> List[Dict[str, Any]]:
        """Scrape prices from Groq pricing page."""
        html = self.http_client.get_html(self.pricing_url)
        text = html_to_text(html)
        
        # Locate LLM section
        start = text.find("Large Language Models")
        if start == -1:
            raise RuntimeError(f"[{self.provider_key}] Could not locate 'Large Language Models' section")
        
        end = text.find("Text-to-Speech Models", start)
        section = text[start : (end if end != -1 else None)]
        
        out: List[Dict[str, Any]] = []
        
        # Split by "AI Model" blocks
        chunks = section.split("AI Model")
        for ch in chunks:
            ch = ch.strip()
            if not ch:
                continue
            
            # First line is the model name
            model_name = ch.split("\n", 1)[0].strip()
            if not model_name or model_name.lower().startswith(
                ("current speed", "input token price", "output token price")
            ):
                continue
            
            # Extract pricing
            inp_m = re.search(
                r"Input Token Price.*?\$(\d+(?:\.\d+)?)",
                ch,
                flags=re.IGNORECASE | re.DOTALL
            )
            out_m = re.search(
                r"Output Token Price.*?\$(\d+(?:\.\d+)?)",
                ch,
                flags=re.IGNORECASE | re.DOTALL
            )
            
            if not inp_m or not out_m:
                continue
            
            out.append({
                "provider_key": self.provider_key,
                "provider_name": self.provider_name,
                "model_name": model_name,
                "input_per_m": float(inp_m.group(1)),
                "output_per_m": float(out_m.group(1)),
                "context_window": None,
            })
        
        if not out:
            raise RuntimeError(f"[{self.provider_key}] Parsed 0 LLM rows (page structure likely changed)")
        
        return out
