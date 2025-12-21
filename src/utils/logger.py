"""
Error Logging Module
Logs errors to file and optionally to database.
"""

import os
import logging
from datetime import datetime
from pathlib import Path

# Create logs directory if it doesn't exist
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Log file path
LOG_FILE = LOG_DIR / f"benchmark_engine_{datetime.now().strftime('%Y%m%d')}.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()  # Also print to console
    ]
)

logger = logging.getLogger("benchmark_engine")


def log_error(error_message: str, context: dict = None):
    """
    Log an error to file and console.
    
    Args:
        error_message: The error message to log
        context: Optional dictionary with additional context (e.g., provider, model, run_id)
    """
    if context:
        context_str = " | ".join([f"{k}={v}" for k, v in context.items()])
        full_message = f"{error_message} | Context: {context_str}"
    else:
        full_message = error_message
    
    logger.error(full_message)


def log_info(message: str, context: dict = None):
    """
    Log an info message to file and console.
    
    Args:
        message: The message to log
        context: Optional dictionary with additional context
    """
    if context:
        context_str = " | ".join([f"{k}={v}" for k, v in context.items()])
        full_message = f"{message} | Context: {context_str}"
    else:
        full_message = message
    
    logger.info(full_message)


def log_warning(message: str, context: dict = None):
    """
    Log a warning to file and console.
    
    Args:
        message: The warning message to log
        context: Optional dictionary with additional context
    """
    if context:
        context_str = " | ".join([f"{k}={v}" for k, v in context.items()])
        full_message = f"{message} | Context: {context_str}"
    else:
        full_message = message
    
    logger.warning(full_message)

