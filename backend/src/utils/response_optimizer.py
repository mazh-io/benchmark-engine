"""
Utility function to optimize response_text storage.

Truncates response_text to save database space while preserving full text for failed runs.
"""


def truncate_response_text(response_text: str, success: bool, max_length: int = 100) -> str:
    """
    Truncate response_text for successful runs to save database storage.
    
    Strategy:
    - For successful runs: Keep only first 100 chars (sufficient for verification)
    - For failed runs: Keep full text (needed for debugging)
    
    This reduces storage by ~98% for successful runs while maintaining
    full debugging context for failures.
    
    Args:
        response_text: The full response text from the model
        success: Whether the run was successful
        max_length: Maximum length for successful runs (default: 100)
        
    Returns:
        Truncated or full response text based on success status
        
    Examples:
        >>> text = "This is a long response..." * 100
        >>> truncate_response_text(text, success=True)
        'This is a long response...This is a long response...This is a long response...This is a lon...'
        
        >>> truncate_response_text(text, success=False)
        'This is a long response...' * 100  # Full text preserved
    """
    if not response_text:
        return response_text
    
    # Keep full text for failed runs (needed for debugging)
    if not success:
        return response_text
    
    # Truncate successful runs to save storage
    if len(response_text) <= max_length:
        return response_text
    
    return response_text[:max_length] + "..."
