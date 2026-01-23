"""
Database connector factory.

Creates and returns the appropriate database client based on environment configuration.
Supports:
- Supabase (cloud database)
- Local PostgreSQL (local development/testing)
"""

from typing import Optional
from database.base_db_client import BaseDatabaseClient
from utils.env_helper import get_env


_db_instance: Optional[BaseDatabaseClient] = None


def get_db_client() -> BaseDatabaseClient:
    """
    Get the configured database client instance.
    
    Returns the appropriate database client based on the DB_TYPE environment variable:
    - 'supabase' (default): Returns Supabase client
    - 'local': Returns local PostgreSQL client
    
    The client is cached as a singleton for the lifetime of the application.
    
    Returns:
        BaseDatabaseClient instance
        
    Raises:
        ValueError: If DB_TYPE is not recognized
        Exception: If database connection fails
    """
    global _db_instance
    
    # Return cached instance if available
    if _db_instance is not None:
        return _db_instance
    
    # Get database type from environment (default to supabase)
    db_type = get_env('DB_TYPE', 'supabase').lower()
    
    if db_type == 'supabase':
        from database.supabase_client import SupabaseDatabaseClient
        _db_instance = SupabaseDatabaseClient()
        print(f"✅ Using Supabase database")
    elif db_type == 'local':
        from database.local_db_client import LocalDatabaseClient
        _db_instance = LocalDatabaseClient()
        print(f"✅ Using Local PostgreSQL database")
    else:
        raise ValueError(f"Unknown DB_TYPE: {db_type}. Must be 'supabase' or 'local'")
    
    return _db_instance


def reset_db_client():
    """Reset the cached database client instance. Used for testing."""
    global _db_instance
    _db_instance = None
