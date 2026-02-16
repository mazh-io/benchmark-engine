"""
Base abstract scraper interface.

This module defines the contract that all provider-specific scrapers must implement.
Following the Strategy pattern and Dependency Inversion Principle.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BasePricingScraper(ABC):
    """
    Abstract base class for all provider pricing scrapers.
    
    Each provider scraper must implement the fetch_prices method to retrieve
    pricing data in a standardized format.
    """
    
    def __init__(self, provider_key: str, provider_config: Dict[str, Any]):
        """
        Initialize the scraper with provider configuration.
        
        Args:
            provider_key: Unique identifier for the provider (e.g., "openai", "mistral")
            provider_config: Configuration dict containing display_name, pricing_url, etc.
        """
        self.provider_key = provider_key
        self.provider_config = provider_config
    
    @abstractmethod
    def fetch_prices(self) -> List[Dict[str, Any]]:
        """
        Fetch pricing data from the provider.
        
        Returns:
            List of dictionaries with structure:
            {
                "provider_key": str,
                "provider_name": str,
                "model_name": str,
                "input_per_m": float,
                "output_per_m": float,
                "context_window": Optional[int]
            }
            
        Raises:
            Exception: If scraping fails or data cannot be retrieved
        """
        pass
    
    @property
    def provider_name(self) -> str:
        """Get the display name of the provider."""
        return self.provider_config.get("display_name", self.provider_key)
    
    @property
    def pricing_url(self) -> str:
        """Get the pricing URL for the provider."""
        return self.provider_config.get("pricing_url", "")
