"""
Model Name Normalizer

Utility to normalize/sanitize model names before saving to database.
Converts provider-specific raw API strings to clean, consistent names.

Examples:
    - accounts/fireworks/models/llama-v3p3-70b-instruct → llama-3.3-70b-instruct
    - models/gemini-2.5-flash → gemini-2.5-flash
    - openai/gpt-4o → gpt-4o
    - meta-llama/Llama-3.3-70B-Instruct → llama-3.3-70b-instruct
"""

import re
from typing import Dict


# Provider-specific path prefixes to remove
PROVIDER_PREFIXES = [
    # Fireworks
    r"^accounts/fireworks/models/",
    # Google
    r"^models/",
    # OpenRouter
    r"^[^/]+/",  # Remove provider prefix like "openai/" or "anthropic/"
    # Together AI
    r"^meta-llama/",
    r"^mistralai/",
    r"^NousResearch/",
    r"^Qwen/",
]

# Common replacements for model name parts
REPLACEMENTS = {
    # Version number patterns
    r"v3p3": "3.3",
    r"v3p2": "3.2",
    r"v3p1": "3.1",
    r"v2p5": "2.5",
    r"v2p0": "2.0",
    r"v1p5": "1.5",
    
    # Separators
    r"_": "-",
    
    # Common model name patterns
    r"-instruct": "-instruct",  # Keep as-is
    r"-Instruct": "-instruct",  # Normalize case
    r"Llama": "llama",
    r"Mixtral": "mixtral",
    r"Mistral": "mistral",
    r"Qwen": "qwen",
}


def normalize_model_name(raw_model_name: str, provider_name: str = None) -> str:
    """
    Normalize a raw model name from an API to a clean, standardized format.
    
    This function:
    1. Removes provider-specific path prefixes
    2. Normalizes version numbers (v3p3 → 3.3)
    3. Converts to lowercase (with exceptions for known patterns)
    4. Standardizes separators
    5. Removes redundant information
    
    Args:
        raw_model_name: The raw model name from the API
        provider_name: Optional provider name for provider-specific logic
        
    Returns:
        Normalized model name (e.g., "llama-3.3-70b-instruct")
        
    Examples:
        >>> normalize_model_name("accounts/fireworks/models/llama-v3p3-70b-instruct")
        'llama-3.3-70b-instruct'
        
        >>> normalize_model_name("models/gemini-2.5-flash")
        'gemini-2.5-flash'
        
        >>> normalize_model_name("openai/gpt-4o")
        'gpt-4o'
        
        >>> normalize_model_name("meta-llama/Llama-3.3-70B-Instruct")
        'llama-3.3-70b-instruct'
    """
    if not raw_model_name:
        return raw_model_name
    
    normalized = raw_model_name.strip()
    
    # Step 1: Remove provider-specific prefixes
    for prefix_pattern in PROVIDER_PREFIXES:
        normalized = re.sub(prefix_pattern, "", normalized)
    
    # Step 2: Apply version number replacements
    for pattern, replacement in REPLACEMENTS.items():
        if pattern.startswith("v"):  # Version patterns
            normalized = re.sub(pattern, replacement, normalized)
    
    # Step 3: Normalize case for common model families
    # Keep numbers and already-lowercase parts as-is
    if re.search(r"llama", normalized, re.IGNORECASE):
        normalized = re.sub(r"llama", "llama", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"Llama", "llama", normalized)
    
    if re.search(r"mixtral", normalized, re.IGNORECASE):
        normalized = re.sub(r"mixtral", "mixtral", normalized, flags=re.IGNORECASE)
    
    if re.search(r"mistral", normalized, re.IGNORECASE):
        normalized = re.sub(r"mistral", "mistral", normalized, flags=re.IGNORECASE)
    
    if re.search(r"qwen", normalized, re.IGNORECASE):
        normalized = re.sub(r"qwen", "qwen", normalized, flags=re.IGNORECASE)
    
    # Step 4: Standardize "instruct" suffix
    normalized = re.sub(r"-Instruct", "-instruct", normalized)
    normalized = re.sub(r"_instruct", "-instruct", normalized)
    
    # Step 5: Convert underscores to hyphens (except in specific cases)
    normalized = normalized.replace("_", "-")
    
    # Step 6: Remove any double hyphens
    normalized = re.sub(r"-+", "-", normalized)
    
    # Step 7: Handle "B" suffix for model sizes (70B → 70b)
    normalized = re.sub(r"(\d+)B-", r"\1b-", normalized)
    normalized = re.sub(r"(\d+)B$", r"\1b", normalized)
    
    return normalized.strip()


def normalize_model_names_batch(model_names: list, provider_name: str = None) -> Dict[str, str]:
    """
    Normalize a batch of model names and return a mapping.
    
    Args:
        model_names: List of raw model names
        provider_name: Optional provider name for provider-specific logic
        
    Returns:
        Dictionary mapping raw names to normalized names
        
    Example:
        >>> names = [
        ...     "accounts/fireworks/models/llama-v3p3-70b-instruct",
        ...     "models/gemini-2.5-flash"
        ... ]
        >>> normalize_model_names_batch(names)
        {
            'accounts/fireworks/models/llama-v3p3-70b-instruct': 'llama-3.3-70b-instruct',
            'models/gemini-2.5-flash': 'gemini-2.5-flash'
        }
    """
    return {
        raw_name: normalize_model_name(raw_name, provider_name)
        for raw_name in model_names
    }


# Test cases (can be run with pytest or manually)
if __name__ == "__main__":
    # Test cases
    test_cases = [
        ("accounts/fireworks/models/llama-v3p3-70b-instruct", "llama-3.3-70b-instruct"),
        ("accounts/fireworks/models/llama-v3p1-405b-instruct", "llama-3.1-405b-instruct"),
        ("accounts/fireworks/models/qwen2p5-72b-instruct", "qwen2p5-72b-instruct"),
        ("models/gemini-2.5-flash", "gemini-2.5-flash"),
        ("models/gemini-1.5-pro", "gemini-1.5-pro"),
        ("openai/gpt-4o", "gpt-4o"),
        ("anthropic/claude-3-5-sonnet", "claude-3-5-sonnet"),
        ("meta-llama/Llama-3.3-70B-Instruct", "llama-3.3-70b-instruct"),
        ("gpt-4o-mini", "gpt-4o-mini"),
        ("llama-3.1-8b-instant", "llama-3.1-8b-instant"),
        ("mistral-large-latest", "mistral-large-latest"),
    ]
    
    print("Testing model name normalization:")
    print("=" * 80)
    
    all_passed = True
    for raw, expected in test_cases:
        result = normalize_model_name(raw)
        status = "✅" if result == expected else "❌"
        if result != expected:
            all_passed = False
        print(f"{status} {raw}")
        print(f"   Expected: {expected}")
        print(f"   Got:      {result}")
        print()
    
    print("=" * 80)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
