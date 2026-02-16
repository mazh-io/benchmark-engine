"""
FastAPI Dependencies

Provides dependency injection for database clients, budget checks, etc.
Used via FastAPI's Depends() mechanism in route handlers.
"""

import sys
import os
from functools import lru_cache

# Add src folder to path so business logic modules are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from database.db_connector import get_db_client
from database.base_db_client import BaseDatabaseClient
from utils.budget_breaker import BudgetCircuitBreaker


def get_db() -> BaseDatabaseClient:
    """
    Dependency that provides the database client.
    
    Usage in routes:
        @router.get("/example")
        def example(db: BaseDatabaseClient = Depends(get_db)):
            ...
    """
    return get_db_client()


def get_budget_breaker() -> BudgetCircuitBreaker:
    """
    Dependency that provides a BudgetCircuitBreaker instance.
    
    Usage in routes:
        @router.get("/example")
        def example(breaker: BudgetCircuitBreaker = Depends(get_budget_breaker)):
            ...
    """
    return BudgetCircuitBreaker()
