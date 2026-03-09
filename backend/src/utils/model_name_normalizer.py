"""
Model Name Normalizer

Normalizes provider-specific API model names to clean, canonical display names.
Ensures the same base model has the SAME name across all providers for
cross-provider comparison on the website.

Examples:
    - accounts/fireworks/models/llama-v3p3-70b-instruct → llama-3.3-70b
    - models/gemini-2.5-flash → gemini-2.5-flash
    - openai/gpt-4o → gpt-4o
    - meta-llama/Llama-3.3-70B-Instruct → llama-3.3-70b
    - claude-sonnet-4-5-20250929 → claude-sonnet-4.5
    - Meta-Llama-3.3-70B-Instruct → llama-3.3-70b
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
}


def normalize_model_name(raw_model_name: str, provider_name: str = None) -> str:
    """
    Normalize a raw model name to a clean, canonical display name.

    Ensures cross-provider consistency: the same base model gets the same
    normalized name regardless of which provider serves it.

    Normalization steps:
    1. Strip provider path prefixes (accounts/fireworks/models/, models/, etc.)
    2. Normalize version numbers (v3p3 → 3.3)
    3. Lowercase everything
    4. Strip meta- prefix before llama
    5. Normalize llama3.1 → llama-3.1 (Cerebras format)
    6. Map Groq variant names (-versatile → -instruct)
    7. Strip hosting variants (-turbo, -instant)
    8. Strip quantization (-fp8)
    9. Strip MoE expert counts (-128e, -16e)
    10. Strip Llama 4 size after variant name (-17b)
    11. Strip -instruct suffix (all benchmarked models are instruct)
    12. Strip Anthropic date suffixes (-YYYYMMDD)
    13. Convert Claude version separators (4-5 → 4.5)

    Args:
        raw_model_name: The raw model name from the API
        provider_name: Optional provider name (unused, kept for compatibility)

    Returns:
        Normalized model name

    Examples:
        >>> normalize_model_name("meta-llama/Llama-3.3-70B-Instruct")
        'llama-3.3-70b'
        >>> normalize_model_name("claude-sonnet-4-5-20250929")
        'claude-sonnet-4.5'
        >>> normalize_model_name("models/gemini-2.5-flash")
        'gemini-2.5-flash'
    """
    if not raw_model_name:
        return raw_model_name

    normalized = raw_model_name.strip()

    # Step 1: Remove provider-specific path prefixes
    for prefix_pattern in PROVIDER_PREFIXES:
        normalized = re.sub(prefix_pattern, "", normalized)

    # Step 2: Apply version number replacements (v3p3 → 3.3)
    for pattern, replacement in REPLACEMENTS.items():
        normalized = re.sub(pattern, replacement, normalized)

    # Step 3: Normalize case for common model families
    if re.search(r"llama", normalized, re.IGNORECASE):
        normalized = re.sub(r"llama", "llama", normalized, flags=re.IGNORECASE)

    if re.search(r"mixtral", normalized, re.IGNORECASE):
        normalized = re.sub(r"mixtral", "mixtral", normalized, flags=re.IGNORECASE)

    if re.search(r"mistral", normalized, re.IGNORECASE):
        normalized = re.sub(r"mistral", "mistral", normalized, flags=re.IGNORECASE)

    if re.search(r"qwen", normalized, re.IGNORECASE):
        normalized = re.sub(r"qwen", "qwen", normalized, flags=re.IGNORECASE)

    # Standardize separators and case
    normalized = re.sub(r"-Instruct", "-instruct", normalized)
    normalized = re.sub(r"_instruct", "-instruct", normalized)
    normalized = normalized.replace("_", "-")
    normalized = re.sub(r"-+", "-", normalized)

    # Handle "B" suffix for model sizes (70B → 70b)
    normalized = re.sub(r"(\d+)B(?=-|$)", r"\1b", normalized)

    # Lowercase everything
    normalized = normalized.lower()

    # Step 4: Strip meta- prefix before llama (SambaNova uses Meta-Llama-...)
    normalized = re.sub(r"^meta-(?=llama)", "", normalized)

    # Step 5: Normalize Cerebras format (llama3.1 → llama-3.1)
    normalized = re.sub(r"llama(\d)", r"llama-\1", normalized)

    # Step 6: Map Groq variant names to standard
    normalized = re.sub(r"-versatile$", "-instruct", normalized)

    # Step 7: Strip hosting variant suffixes
    normalized = re.sub(r"-turbo(?=$|-)", "", normalized)
    normalized = re.sub(r"-instant$", "", normalized)

    # Step 8: Strip quantization suffixes
    normalized = re.sub(r"-fp8$", "", normalized)

    # Step 9: Strip MoE expert count (-128e, -16e between dashes or at end)
    normalized = re.sub(r"-\d+e(?=-|$)", "", normalized)

    # Step 10: Strip Llama 4 size after variant name (Maverick/Scout only come in 17B)
    normalized = re.sub(r"(llama-4-(?:maverick|scout))-\d+b", r"\1", normalized)

    # Step 11: Strip -instruct suffix (all benchmarked models are instruct variants)
    normalized = re.sub(r"-instruct(?=$|-)", "", normalized)

    # Step 12: Strip Anthropic date suffixes (-YYYYMMDD)
    normalized = re.sub(r"-20\d{6}$", "", normalized)

    # Step 13: Convert Claude version separators (claude-sonnet-4-5 → claude-sonnet-4.5)
    normalized = re.sub(
        r"(claude-(?:sonnet|opus|haiku)-\d+)-(\d+)$", r"\1.\2", normalized
    )

    # Final cleanup
    normalized = re.sub(r"-+", "-", normalized)
    normalized = normalized.strip("-")

    return normalized


def normalize_model_names_batch(
    model_names: list, provider_name: str = None
) -> Dict[str, str]:
    """
    Normalize a batch of model names and return a mapping.

    Args:
        model_names: List of raw model names
        provider_name: Optional provider name for provider-specific logic

    Returns:
        Dictionary mapping raw names to normalized names
    """
    return {
        raw_name: normalize_model_name(raw_name, provider_name)
        for raw_name in model_names
    }


# Test cases
if __name__ == "__main__":
    test_cases = [
        # Cross-provider: Llama 3.3 70B (should all → llama-3.3-70b)
        ("llama-3.3-70b-instruct", "llama-3.3-70b"),  # Fireworks
        ("meta-llama/Llama-3.3-70B-Instruct", "llama-3.3-70b"),  # OpenRouter
        ("Meta-Llama-3.3-70B-Instruct", "llama-3.3-70b"),  # SambaNova
        ("meta-llama/Llama-3.3-70B-Instruct-Turbo", "llama-3.3-70b"),  # Together
        ("llama-3.3-70b-versatile", "llama-3.3-70b"),  # Groq
        # Cross-provider: Llama 3.1 8B (should all → llama-3.1-8b)
        ("llama-3.1-8b-instant", "llama-3.1-8b"),  # Groq
        ("llama3.1-8b", "llama-3.1-8b"),  # Cerebras
        # Cross-provider: Llama 4 Maverick (should all → llama-4-maverick)
        ("meta-llama/llama-4-maverick", "llama-4-maverick"),  # OpenRouter
        (
            "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
            "llama-4-maverick",
        ),  # Together
        # Llama 4 Scout (different model from Maverick)
        (
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "llama-4-scout",
        ),  # Groq
        # Anthropic: clean date suffixes and version separators
        ("claude-sonnet-4-5-20250929", "claude-sonnet-4.5"),
        ("claude-haiku-4-5-20251001", "claude-haiku-4.5"),
        ("claude-opus-4-20250514", "claude-opus-4"),
        ("claude-sonnet-4-20250514", "claude-sonnet-4"),
        ("claude-opus-4-6", "claude-opus-4.6"),
        # Google
        ("models/gemini-2.5-flash", "gemini-2.5-flash"),
        ("models/gemini-2.5-pro", "gemini-2.5-pro"),
        # OpenAI (should stay clean)
        ("gpt-4o", "gpt-4o"),
        ("gpt-4o-mini", "gpt-4o-mini"),
        ("gpt-4.1", "gpt-4.1"),
        ("o3", "o3"),
        ("o4-mini", "o4-mini"),
        # Fireworks
        (
            "accounts/fireworks/models/llama-v3p3-70b-instruct",
            "llama-3.3-70b",
        ),
        # Together
        ("mistralai/Mixtral-8x7B-Instruct-v0.1", "mixtral-8x7b-v0.1"),
        ("Qwen/Qwen3-Next-80B-A3B-Instruct", "qwen3-next-80b-a3b"),
        # Other providers (should stay clean)
        ("deepseek-chat", "deepseek-chat"),
        ("deepseek-reasoner", "deepseek-reasoner"),
        ("grok-3", "grok-3"),
        ("grok-3-mini", "grok-3-mini"),
        ("sonar-pro", "sonar-pro"),
        ("sonar", "sonar"),
        ("command-a-03-2025", "command-a-03-2025"),
        ("command-r7b-12-2024", "command-r7b-12-2024"),
        ("mistral-large-latest", "mistral-large-latest"),
        ("codestral-latest", "codestral-latest"),
        ("gpt-oss-120b", "gpt-oss-120b"),
        ("minimax/minimax-01", "minimax-01"),
    ]

    print("Testing model name normalization:")
    print("=" * 90)

    all_passed = True
    for raw, expected in test_cases:
        result = normalize_model_name(raw)
        status = "PASS" if result == expected else "FAIL"
        if result != expected:
            all_passed = False
        print(f"  [{status}] {raw}")
        print(f"         -> {result}")
        if result != expected:
            print(f"         EXPECTED: {expected}")
        print()

    print("=" * 90)
    if all_passed:
        print("All tests passed!")
    else:
        print("Some tests FAILED!")
