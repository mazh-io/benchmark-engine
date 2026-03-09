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
    - grok-4-1-fast-non-reasoning → grok-4.1
    - zai-glm-4.7 → glm-4.7
    - Qwen/Qwen3.5-397B-A17B → qwen-3.5-397b-a17b
"""

import re
from typing import Dict


# Provider-specific path prefixes to remove
PROVIDER_PREFIXES = [
    # Fireworks
    r"^accounts/fireworks/models/",
    # Google
    r"^models/",
    # Generic: remove any provider/ prefix (openai/, meta-llama/, zai-org/, etc.)
    r"^[^/]+/",
]

# Common replacements for model name parts
REPLACEMENTS = {
    # Version number patterns (Fireworks encoding)
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

    Args:
        raw_model_name: The raw model name from the API
        provider_name: Optional provider name (unused, kept for compatibility)

    Returns:
        Normalized model name
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
    for family in ["llama", "mixtral", "mistral", "qwen"]:
        normalized = re.sub(family, family, normalized, flags=re.IGNORECASE)

    # Standardize separators and case
    normalized = re.sub(r"-Instruct", "-instruct", normalized)
    normalized = re.sub(r"-Thinking", "-thinking", normalized)
    normalized = re.sub(r"_instruct", "-instruct", normalized)
    normalized = normalized.replace("_", "-")
    normalized = re.sub(r"-+", "-", normalized)

    # Handle "B" suffix for model sizes (70B → 70b)
    normalized = re.sub(r"(\d+)B(?=-|$)", r"\1b", normalized)

    # Lowercase everything
    normalized = normalized.lower()

    # Step 4: Strip meta- prefix before llama (SambaNova uses Meta-Llama-...)
    normalized = re.sub(r"^meta-(?=llama)", "", normalized)

    # Step 4b: Strip zai- prefix before glm (Cerebras uses zai-glm-...)
    normalized = re.sub(r"^zai-(?=glm)", "", normalized)

    # Step 5: Normalize Cerebras format (llama3.1 → llama-3.1, qwen3 → qwen-3)
    normalized = re.sub(r"llama(\d)", r"llama-\1", normalized)
    normalized = re.sub(r"qwen(\d)", r"qwen-\1", normalized)

    # Step 5b: Normalize DeepSeek version (deepseek-v3.1 → deepseek-3.1)
    normalized = re.sub(r"(deepseek-)v(\d)", r"\1\2", normalized)

    # Step 6: Map Groq variant names to standard
    normalized = re.sub(r"-versatile$", "-instruct", normalized)

    # Step 7: Strip hosting variant suffixes
    normalized = re.sub(r"-turbo(?=$|-)", "", normalized)
    normalized = re.sub(r"-instant$", "", normalized)
    normalized = re.sub(r"-fast(?=-|$)", "", normalized)
    normalized = re.sub(r"-non-reasoning$", "", normalized)
    normalized = re.sub(r"-tput$", "", normalized)
    normalized = re.sub(r"-preview$", "", normalized)
    normalized = re.sub(r"-latest$", "", normalized)

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

    # Step 12b: Strip MMDD date suffixes (xAI: -0709, DeepSeek: -0528)
    normalized = re.sub(
        r"-(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])$", "", normalized
    )

    # Step 12c: Strip YYMM version suffixes (Together/Cerebras: -2507)
    normalized = re.sub(r"-2[0-9](?:0[1-9]|1[0-2])$", "", normalized)

    # Step 13: Convert Claude version separators (claude-sonnet-4-5 → claude-sonnet-4.5)
    normalized = re.sub(
        r"(claude-(?:sonnet|opus|haiku)-\d+)-(\d+)$", r"\1.\2", normalized
    )

    # Step 13b: Convert Grok version separators (grok-4-1 → grok-4.1)
    normalized = re.sub(r"(grok-\d+)-(\d+)$", r"\1.\2", normalized)

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
        # === Cross-provider: Llama 3.3 70B (should all → llama-3.3-70b) ===
        ("llama-3.3-70b-instruct", "llama-3.3-70b"),
        ("meta-llama/Llama-3.3-70B-Instruct", "llama-3.3-70b"),
        ("Meta-Llama-3.3-70B-Instruct", "llama-3.3-70b"),
        ("meta-llama/Llama-3.3-70B-Instruct-Turbo", "llama-3.3-70b"),
        ("llama-3.3-70b-versatile", "llama-3.3-70b"),
        # === Cross-provider: Llama 3.1 8B (should all → llama-3.1-8b) ===
        ("llama-3.1-8b-instant", "llama-3.1-8b"),
        ("llama3.1-8b", "llama-3.1-8b"),
        ("Meta-Llama-3.1-8B-Instruct", "llama-3.1-8b"),
        # === Cross-provider: Llama 4 Maverick (should all → llama-4-maverick) ===
        ("meta-llama/llama-4-maverick", "llama-4-maverick"),
        ("meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8", "llama-4-maverick"),
        ("meta-llama/llama-4-maverick-17b-128e-instruct", "llama-4-maverick"),
        ("Llama-4-Maverick-17B-128E-Instruct", "llama-4-maverick"),
        # === Cross-provider: Llama 4 Scout ===
        ("meta-llama/llama-4-scout-17b-16e-instruct", "llama-4-scout"),
        ("meta-llama/Llama-4-Scout-17B-16E-Instruct", "llama-4-scout"),
        # === Cross-provider: Llama 3.1 405B ===
        ("meta-llama/Llama-3.1-405B-Instruct", "llama-3.1-405b"),
        # === Cross-provider: GPT-OSS (should all → gpt-oss-Xb) ===
        ("gpt-oss-120b", "gpt-oss-120b"),
        ("openai/gpt-oss-120b", "gpt-oss-120b"),
        ("openai/gpt-oss-20b", "gpt-oss-20b"),
        # === Cross-provider: DeepSeek V3.1/V3.2 ===
        ("deepseek-ai/DeepSeek-V3.1", "deepseek-3.1"),
        ("DeepSeek-V3.1", "deepseek-3.1"),
        ("accounts/fireworks/models/deepseek-v3p1", "deepseek-3.1"),
        ("DeepSeek-V3.2", "deepseek-3.2"),
        ("accounts/fireworks/models/deepseek-v3p2", "deepseek-3.2"),
        ("deepseek/deepseek-v3.2", "deepseek-3.2"),
        # === Cross-provider: DeepSeek R1 ===
        ("deepseek-ai/DeepSeek-R1", "deepseek-r1"),
        ("DeepSeek-R1-0528", "deepseek-r1"),
        ("deepseek-ai/DeepSeek-R1-Distill-Llama-70B", "deepseek-r1-distill-llama-70b"),
        ("DeepSeek-R1-Distill-Llama-70B", "deepseek-r1-distill-llama-70b"),
        # === Cross-provider: Qwen3-235B ===
        ("qwen-3-235b-a22b-instruct-2507", "qwen-3-235b-a22b"),
        ("Qwen/Qwen3-235B-A22B-Instruct-2507-tput", "qwen-3-235b-a22b"),
        ("Qwen3-235B", "qwen-3-235b"),
        # === Cross-provider: Qwen3-32B ===
        ("qwen/qwen3-32b", "qwen-3-32b"),
        ("Qwen3-32B", "qwen-3-32b"),
        # === Cross-provider: GLM-4.7 ===
        ("zai-glm-4.7", "glm-4.7"),
        ("zai-org/GLM-4.7", "glm-4.7"),
        # === Cross-provider: GLM-5 ===
        ("zai-org/GLM-5", "glm-5"),
        ("z-ai/glm-5", "glm-5"),
        # === Cross-provider: MiniMax M2.5 ===
        ("MiniMaxAI/MiniMax-M2.5", "minimax-m2.5"),
        ("MiniMax-M2.5", "minimax-m2.5"),
        ("minimax/minimax-m2.5", "minimax-m2.5"),
        # === Cross-provider: Kimi K2 / K2.5 ===
        ("moonshotai/kimi-k2-instruct", "kimi-k2"),
        ("moonshotai/Kimi-K2.5", "kimi-k2.5"),
        ("moonshotai/kimi-k2.5", "kimi-k2.5"),
        # === Anthropic: date suffixes + version separators ===
        ("claude-sonnet-4-5-20250929", "claude-sonnet-4.5"),
        ("claude-haiku-4-5-20251001", "claude-haiku-4.5"),
        ("claude-opus-4-20250514", "claude-opus-4"),
        ("claude-sonnet-4-20250514", "claude-sonnet-4"),
        ("claude-opus-4-6", "claude-opus-4.6"),
        ("claude-sonnet-4-6", "claude-sonnet-4.6"),
        ("claude-opus-4-5-20251101", "claude-opus-4.5"),
        ("claude-opus-4-1-20250805", "claude-opus-4.1"),
        # === Google: strip models/ and -preview ===
        ("models/gemini-2.5-flash", "gemini-2.5-flash"),
        ("models/gemini-2.5-pro", "gemini-2.5-pro"),
        ("models/gemini-2.5-flash-lite", "gemini-2.5-flash-lite"),
        ("models/gemini-2.0-flash", "gemini-2.0-flash"),
        ("models/gemini-3.1-pro-preview", "gemini-3.1-pro"),
        ("models/gemini-3-pro-preview", "gemini-3-pro"),
        ("models/gemini-3-flash-preview", "gemini-3-flash"),
        # === OpenAI ===
        ("gpt-4o", "gpt-4o"),
        ("gpt-4o-mini", "gpt-4o-mini"),
        ("gpt-4.1", "gpt-4.1"),
        ("gpt-5.4", "gpt-5.4"),
        ("gpt-5.2", "gpt-5.2"),
        ("gpt-5.1", "gpt-5.1"),
        ("gpt-5-mini", "gpt-5-mini"),
        ("o3", "o3"),
        ("o3-mini", "o3-mini"),
        ("o4-mini", "o4-mini"),
        # === xAI: strip dates and hosting variants ===
        ("grok-3", "grok-3"),
        ("grok-3-mini", "grok-3-mini"),
        ("grok-4-0709", "grok-4"),
        ("grok-4-1-fast-non-reasoning", "grok-4.1"),
        ("x-ai/grok-4", "grok-4"),
        # === Mistral: strip -latest ===
        ("mistral-large-latest", "mistral-large"),
        ("mistral-small-latest", "mistral-small"),
        ("mistral-medium-latest", "mistral-medium"),
        ("codestral-latest", "codestral"),
        ("magistral-medium-latest", "magistral-medium"),
        ("magistral-small-latest", "magistral-small"),
        # === Fireworks ===
        ("accounts/fireworks/models/llama-v3p3-70b-instruct", "llama-3.3-70b"),
        # === Together ===
        ("mistralai/Mixtral-8x7B-Instruct-v0.1", "mixtral-8x7b-v0.1"),
        ("Qwen/Qwen3-Next-80B-A3B-Instruct", "qwen-3-next-80b-a3b"),
        ("Qwen/Qwen3.5-397B-A17B", "qwen-3.5-397b-a17b"),
        # === Other providers ===
        ("deepseek-chat", "deepseek-chat"),
        ("deepseek-reasoner", "deepseek-reasoner"),
        ("sonar-pro", "sonar-pro"),
        ("sonar", "sonar"),
        ("command-a-03-2025", "command-a-03-2025"),
        ("command-r7b-12-2024", "command-r7b-12-2024"),
        ("minimax/minimax-01", "minimax-01"),
        ("xiaomi/mimo-v2-flash", "mimo-v2-flash"),
        ("qwen/qwen3-max", "qwen-3-max"),
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
