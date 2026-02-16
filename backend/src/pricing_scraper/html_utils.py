"""
HTML parsing utilities for web scraping.

This module provides reusable utilities for extracting text from HTML content.
"""

import re
from html.parser import HTMLParser
from typing import List, Optional, Tuple


class TextExtractor(HTMLParser):
    """
    Custom HTML parser that extracts clean text content from HTML.
    
    Filters out script, style, and noscript tags and normalizes whitespace.
    """
    
    def __init__(self) -> None:
        super().__init__()
        self._chunks: List[str] = []
        self._skip_depth = 0
    
    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip_depth += 1
        if tag in ("br", "p", "div", "tr", "li", "h1", "h2", "h3", "h4", "h5"):
            self._chunks.append("\n")
    
    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript") and self._skip_depth > 0:
            self._skip_depth -= 1
        if tag in ("p", "div", "tr", "li"):
            self._chunks.append("\n")
    
    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        s = data.strip()
        if s:
            self._chunks.append(s)
    
    def get_text(self) -> str:
        """Get the extracted text content."""
        return "\n".join(self._chunks)


def html_to_text(html: str) -> str:
    """
    Convert HTML to clean text content.
    
    Args:
        html: Raw HTML string
        
    Returns:
        Clean text with normalized whitespace
    """
    parser = TextExtractor()
    parser.feed(html)
    raw = parser.get_text()
    
    # Normalize whitespace
    raw = re.sub(r"[ \t\r]+", " ", raw)
    raw = re.sub(r"\n{2,}", "\n", raw)
    
    return raw.strip()
