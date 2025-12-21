#!/usr/bin/env python3
"""
Test script for a single provider
Quick test to verify a provider is working correctly.
"""

import sys
import os

# Add src folder to PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from providers.openai_provider import call_openai
from providers.groq_provider import call_groq
from providers.together_provider import call_together
from providers.openrouter_provider import call_openrouter

# Test prompt (shorter for quick testing)
TEST_PROMPT = "Summarize this in 3 bullet points: The history of timekeeping shows humanity's evolution from sundials to atomic clocks."

def test_provider(provider_name, func, model):
    """Test a single provider"""
    print(f"\n{'='*60}")
    print(f"Testing {provider_name} / {model}")
    print(f"{'='*60}\n")
    
    result = func(TEST_PROMPT, model)
    
    if result["success"]:
        print(f" Success!")
        print(f" Total Latency: {result.get('total_latency_ms') or result.get('latency_ms', 0):.2f} ms")
        if result.get("ttft_ms"):
            print(f"   TTFT: {result['ttft_ms']:.2f} ms")
        if result.get("tps"):
            print(f"   TPS: {result['tps']:.2f} tokens/sec")
        print(f"Tokens: {result['input_tokens']} in / {result['output_tokens']} out")
        print(f"Cost: ${result['cost_usd']:.6f}")
        if result.get("status_code"):
            print(f"   Status: {result['status_code']}")
        if result.get("response_text"):
            print(f"   Response: {result['response_text'][:100]}...")
    else:
        print(f" Failed: {result['error_message']}")
        if result.get("status_code"):
            print(f"   Status: {result['status_code']}")
    
    return result["success"]

if __name__ == "__main__":
    print("=" * 60)
    print("Single Provider Test")
    print("=" * 60)
    
    # Test providers
    providers = [
        ("OpenAI", call_openai, "gpt-4o-mini"),
        ("Groq", call_groq, "llama-3.1-8b-instant"),
        ("Together AI", call_together, "mistralai/Mixtral-8x7B-Instruct-v0.1"),
        ("OpenRouter", call_openrouter, "openai/gpt-4o-mini"),
    ]
    
    results = []
    for provider_name, func, model in providers:
        success = test_provider(provider_name, func, model)
        results.append((provider_name, success))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for provider_name, success in results:
        status = "✅ PASS" if success else " FAIL"
        print(f"{status} - {provider_name}")
    print("=" * 60)

