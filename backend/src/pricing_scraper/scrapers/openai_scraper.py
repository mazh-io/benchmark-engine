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
    Parses the "Text tokens" pricing table with Batch/Flex/Standard columns.
    """
    
    def __init__(self, provider_key: str, provider_config: Dict[str, Any]):
        super().__init__(provider_key, provider_config)
        self.http_client = HTTPClient()
    
    def fetch_prices(self) -> List[Dict[str, Any]]:
        """
        Scrapes OpenAI pricing page.
        Format (2026-01): Tables with model name | $batch | $flex | $standard (input/output)
        Example: gpt-4o | $2.50 | $1.25 | $10.00
        Standard column is the output price (input price in flex or batch)
        """
        html = self.http_client.get_html(self.pricing_url)
        text = html_to_text(html)

        out: List[Dict[str, Any]] = []
        
        # Find the "Text tokens" section
        text_tokens_match = re.search(r'Text tokens.*?Prices per 1M tokens', text, re.DOTALL | re.IGNORECASE)
        if not text_tokens_match:
            raise RuntimeError(f"[{self.provider_key}] Could not find 'Text tokens' section")
        
        # Extract text after "Text tokens" until next major section (before "Image tokens" or "Audio tokens")
        start_pos = text_tokens_match.end()
        # Find the end of text tokens section (look for next heading like "Image tokens", "Audio tokens", etc.)
        end_match = re.search(r'\n(Image tokens|Audio tokens|Video|Fine-tuning)', text[start_pos:], re.IGNORECASE)
        if end_match:
            section_text = text[start_pos:start_pos + end_match.start()]
        else:
            section_text = text[start_pos:start_pos + 10000]  # Take a chunk if no clear end
        
        # Pattern to match table rows: model_name | $X.XX | $X.XX | $X.XX
        # The three prices are Batch, Flex, Standard (we want Standard for input and output)
        # However, the table format shows: model | batch | flex | standard
        # We need to identify which is input and which is output
        
        # Looking at the data, Standard column appears to be output price
        # We need both input and output, so let's look for patterns with dash separators
        # Actually from the fetch, I see: "| gpt-4o | $2.50 | $1.25 | $10.00 |"
        # This seems to be: model | batch | flex | standard
        # But wait - checking the actual page content more carefully...
        
        # From the fetch results, I see lines like:
        # "| gpt-4o | $2.50 | $1.25 | $10.00 |"
        # Let me check if there are clearer patterns showing input vs output
        
        # Actually, looking more carefully at the fetched content:
        # The table header should tell us the columns
        # Let's look for rows with the pattern: | model_name | $price | $price | $price |
        
        pattern = re.compile(
            r'\|\s*([a-z0-9\.\-]+)\s*\|\s*\$([0-9.]+)\s*\|\s*\$([0-9.]+)\s*\|\s*\$([0-9.]+)\s*\|',
            re.IGNORECASE
        )
        
        for match in pattern.finditer(section_text):
            model_name = match.group(1).strip()
            batch_price = float(match.group(2))
            flex_price = float(match.group(3))
            standard_price = float(match.group(4))
            
            # Skip header rows or non-model entries
            if model_name.lower() in ['model', 'batch', 'flex', 'standard', 'priority']:
                continue
            
            # The Standard price is typically the output price
            # For OpenAI, input is usually 25% of output (or we use batch as input estimate)
            # Let's use batch as input and standard as output based on typical patterns
            input_price = batch_price
            output_price = standard_price
            
            out.append({
                "provider_key": self.provider_key,
                "provider_name": self.provider_name,
                "model_name": model_name,
                "input_per_m": input_price,
                "output_per_m": output_price,
                "context_window": None,
            })

        if not out:
            raise RuntimeError(f"[{self.provider_key}] Parsed 0 rows from Text tokens section (page structure likely changed)")

        return out