"""
Abstract base class for database operations.

Defines the interface that all database clients must implement.
This allows switching between different database backends (Supabase, local PostgreSQL, etc.)
based on configuration.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class BaseDatabaseClient(ABC):
    """Abstract base class for database operations."""
    
    # ============================================================================
    # RUN MANAGEMENT
    # ============================================================================
    
    @abstractmethod
    def create_run(self, run_name: str, triggered_by: str) -> Optional[str]:
        """
        Create a new run in the runs table.
        
        Args:
            run_name: Name of the run
            triggered_by: Who triggered the run
            
        Returns:
            UUID of the created run, or None if creation failed
        """
        pass
    
    @abstractmethod
    def finish_run(self, run_id: str) -> bool:
        """
        Mark run as finished by setting finished_at timestamp.
        
        Args:
            run_id: UUID of the run
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_all_runs(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get all runs from the runs table.
        
        Returns:
            List of all runs, or None if query failed
        """
        pass
    
    # ============================================================================
    # BENCHMARK RESULTS
    # ============================================================================
    
    @abstractmethod
    def save_benchmark(self, **data) -> Optional[str]:
        """
        Save benchmark result.
        
        Args:
            **data: Benchmark data dictionary
            
        Returns:
            UUID of created result, or None if save failed
        """
        pass
    
    @abstractmethod
    def get_all_benchmark_results(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get all benchmark results.
        
        Returns:
            List of all benchmark results, or None if query failed
        """
        pass
    
    @abstractmethod
    def get_benchmark_results_by_run_id(self, run_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get benchmark results for a specific run.
        
        Args:
            run_id: UUID of the run
            
        Returns:
            List of benchmark results, or None if query failed
        """
        pass
    
    # ============================================================================
    # PROVIDERS & MODELS
    # ============================================================================
    
    @abstractmethod
    def get_or_create_provider(self, name: str, base_url: str = None, logo_url: str = None) -> Optional[str]:
        """
        Get existing provider or create new one.
        
        Args:
            name: Provider name
            base_url: Provider API base URL (optional)
            logo_url: Provider logo URL (optional)
            
        Returns:
            UUID of provider, or None if operation failed
        """
        pass
    
    @abstractmethod
    def get_all_providers(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get all providers.
        
        Returns:
            List of all providers, or None if query failed
        """
        pass
    
    @abstractmethod
    def get_or_create_model(self, model_name: str, provider_id: str) -> Optional[str]:
        """
        Get existing model or create new one.
        
        Args:
            model_name: Model name
            provider_id: UUID of provider
            
        Returns:
            UUID of model, or None if operation failed
        """
        pass
    
    @abstractmethod
    def get_all_models(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get all models.
        
        Returns:
            List of all models, or None if query failed
        """
        pass
    
    # ============================================================================
    # PRICING
    # ============================================================================
    
    @abstractmethod
    def save_price(self, provider_id: str, model_id: str, input_price: float, output_price: float) -> Optional[str]:
        """
        Save pricing data for a model.
        
        Args:
            provider_id: UUID of provider
            model_id: UUID of model
            input_price: Input price per 1M tokens
            output_price: Output price per 1M tokens
            
        Returns:
            UUID of created pricing record, or None if save failed
        """
        pass
    
    @abstractmethod
    def get_last_price_timestamp(self, provider_id: str, model_id: str) -> Optional[str]:
        """
        Get timestamp of last price update for a model.
        
        Args:
            provider_id: UUID of provider
            model_id: UUID of model
            
        Returns:
            Timestamp string, or None if no price found
        """
        pass
    
    @abstractmethod
    def get_model_pricing(self, provider_name: str, model_name: str) -> Optional[Dict[str, float]]:
        """
        Get current pricing for a model.
        
        Args:
            provider_name: Name of provider
            model_name: Name of model
            
        Returns:
            Dictionary with 'input' and 'output' keys (prices per 1M tokens),
            or None if pricing not found
        """
        pass
