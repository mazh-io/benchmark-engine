"""OpenAI pricing scraper."""

import re
from typing import Dict, Any, List

from ..base_scraper import BasePricingScraper
from ..http_client import HTTPClient
from ..html_utils import html_to_text


class OpenAIScraper(BasePricingScraper):
    """
    OpenAI pricing scraper.
    
    Scrapes OpenAI's pricing documentation page to extract model pricing.
    Focuses on the "Text tokens" -> "Standard" pricing section.
    """
    
    def __init__(self, provider_key: str, provider_config: Dict[str, Any]):
        super().__init__(provider_key, provider_config)
        self.http_client = HTTPClient()
    
    def fetch_prices(self) -> List[Dict[str, Any]]:
        """
        Scrapes OpenAI pricing page.
        New format (2026-01): Individual model cards with Input/Cached input/Output prices.
        """
        html = self.http_client.get_html(self.pricing_url)
        text = html_to_text(html)

        out: List[Dict[str, Any]] = []
        
        # Pattern to match model cards with pricing
        # Format: Model Name ... Input: $X.XXX / 1M tokens ... Output: $X.XXX / 1M tokens
        pattern = re.compile(
            r'(GPT-[^\n]+?)\s+.*?Input:\s+\$([0-9.]+)\s*/\s*1M\s+tokens.*?Output:\s+\$([0-9.]+)\s*/\s*1M\s+tokens',
            re.IGNORECASE | re.DOTALL
        )
        
        for match in pattern.finditer(text):
            model_name = match.group(1).strip()
            # Clean up model name (remove extra text)
            model_name = re.sub(r'\s+(The|A)\s+.*', '', model_name, flags=re.IGNORECASE).strip()
            
            input_price = float(match.group(2))
            output_price = float(match.group(3))
            
            out.append({
                "provider_key": self.provider_key,
                "provider_name": self.provider_name,
                "model_name": model_name,
                "input_per_m": input_price,
                "output_per_m": output_price,
                "context_window": None,
            })

        if not out:
            raise RuntimeError(f"[{self.provider_key}] Parsed 0 rows (page structure likely changed)")

        return out
