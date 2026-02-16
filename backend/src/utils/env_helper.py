"""
Environment helper - centralized environment variable loading.
Works both locally (with .env file) and in production (Vercel).
"""

import os

# Try to load from .env file (local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available in production


def get_env(key: str, default: str = None) -> str:
    """
    Get environment variable value.
    
    Args:
        key: Name of the environment variable
        default: Default value if not found
    
    Returns:
        Value of the environment variable or default
    """
    return os.getenv(key, default)
