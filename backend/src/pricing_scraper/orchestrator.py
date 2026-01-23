"""Pricing scraper orchestrator."""

from typing import Dict, Any, List
import logging

from .base_scraper import BasePricingScraper
from .scrapers.openai_scraper import OpenAIScraper
from .scrapers.groq_scraper import GroqScraper
from .scrapers.together_scraper import TogetherScraper
from .scrapers.openrouter_scraper import OpenRouterScraper
from .scrapers.mistral_scraper import MistralScraper
from .scrapers.anthropic_scraper import AnthropicScraper
from .scrapers.google_scraper import GoogleScraper
from .scrapers.deepseek_scraper import DeepSeekScraper
from .scrapers.cerebras_scraper import CerebrasScraper
from .scrapers.fireworks_scraper import FireworksScraper
from .scrapers.sambanova_scraper import SambaNovaScraper
from utils.constants import PROVIDER_CONFIG


logger = logging.getLogger(__name__)


class ScraperFactory:
    """Factory for creating scraper instances."""
    
    # Map provider keys to scraper classes
    SCRAPER_MAP = {
        "openai": OpenAIScraper,
        "groq": GroqScraper,
        "together": TogetherScraper,
        "openrouter": OpenRouterScraper,
        "mistral": MistralScraper,
        "anthropic": AnthropicScraper,
        "google": GoogleScraper,
        "deepseek": DeepSeekScraper,
        "cerebras": CerebrasScraper,
        "fireworks": FireworksScraper,
        "sambanova": SambaNovaScraper,
    }
    
    @staticmethod
    def create_scraper(provider_key: str, provider_config: Dict[str, Any]) -> BasePricingScraper:
        """
        Create a scraper instance for the given provider.
        
        Args:
            provider_key: The provider key (e.g., "openai", "groq")
            provider_config: The provider configuration from PROVIDER_CONFIG
            
        Returns:
            An instance of the appropriate scraper class
            
        Raises:
            ValueError: If provider_key is not supported
        """
        scraper_class = ScraperFactory.SCRAPER_MAP.get(provider_key)
        
        if scraper_class is None:
            raise ValueError(f"No scraper available for provider: {provider_key}")
        
        return scraper_class(provider_key, provider_config)


class PricingScraperOrchestrator:
    """
    Orchestrates the execution of all pricing scrapers.
    
    Manages scraper instantiation, execution, and aggregation of results.
    """
    
    def __init__(self):
        self.factory = ScraperFactory()
        self.results: List[Dict[str, Any]] = []
    
    def scrape_all_providers(self) -> List[Dict[str, Any]]:
        """
        Scrape pricing from all configured providers.
        
        Returns:
            List of pricing data dictionaries from all providers
        """
        self.results = []
        
        for provider_key, provider_config in PROVIDER_CONFIG.items():
            # Skip providers without pricing_url
            if "pricing_url" not in provider_config:
                logger.info(f"Skipping {provider_key}: no pricing_url configured")
                continue
            
            try:
                logger.info(f"Scraping {provider_key}...")
                scraper = self.factory.create_scraper(provider_key, provider_config)
                prices = scraper.fetch_prices()
                self.results.extend(prices)
                logger.info(f"  ✓ Fetched {len(prices)} models from {provider_key}")
            except Exception as e:
                logger.error(f"  ✗ Failed to scrape {provider_key}: {e}")
                continue
        
        return self.results
    
    def scrape_provider(self, provider_key: str) -> List[Dict[str, Any]]:
        """
        Scrape pricing from a specific provider.
        
        Args:
            provider_key: The provider to scrape (e.g., "openai")
            
        Returns:
            List of pricing data dictionaries for the provider
            
        Raises:
            ValueError: If provider_key is not in PROVIDER_CONFIG or has no pricing_url
        """
        if provider_key not in PROVIDER_CONFIG:
            raise ValueError(f"Provider not found in config: {provider_key}")
        
        provider_config = PROVIDER_CONFIG[provider_key]
        
        if "pricing_url" not in provider_config:
            raise ValueError(f"No pricing_url configured for {provider_key}")
        
        logger.info(f"Scraping {provider_key}...")
        scraper = self.factory.create_scraper(provider_key, provider_config)
        prices = scraper.fetch_prices()
        logger.info(f"  ✓ Fetched {len(prices)} models from {provider_key}")
        
        return prices
    
    def get_results(self) -> List[Dict[str, Any]]:
        """Get the accumulated scraping results."""
        return self.results
