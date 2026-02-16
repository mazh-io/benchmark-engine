"""
HTTP client utilities for making web requests.

This module provides a centralized HTTP client with consistent error handling.
"""

import requests
from typing import Dict, Optional


class HTTPClient:
    """
    Simple HTTP client wrapper with consistent configuration.
    """
    
    def __init__(self, timeout: int = 40):
        """
        Initialize HTTP client.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        # Add user-agent to avoid bot detection
        self.default_headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    
    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None
    ) -> requests.Response:
        """
        Make a GET request.
        
        Args:
            url: URL to request
            headers: Optional HTTP headers
            
        Returns:
            Response object
            
        Raises:
            requests.HTTPError: If request fails
        """
        # Merge default headers with custom headers
        merged_headers = {**self.default_headers}
        if headers:
            merged_headers.update(headers)
        
        response = requests.get(url, headers=merged_headers, timeout=self.timeout)
        response.raise_for_status()
        return response
    
    def get_json(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Make a GET request and parse JSON response.
        
        Args:
            url: URL to request
            headers: Optional HTTP headers
            
        Returns:
            Parsed JSON data
            
        Raises:
            requests.HTTPError: If request fails
            ValueError: If response is not valid JSON
        """
        response = self.get(url, headers)
        return response.json()
    
    def get_html(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Make a GET request and return HTML content.
        
        Args:
            url: URL to request
            headers: Optional HTTP headers
            
        Returns:
            HTML text content
            
        Raises:
            requests.HTTPError: If request fails
        """
        response = self.get(url, headers)
        return response.text
