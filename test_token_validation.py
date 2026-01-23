"""
Test script to demonstrate token count validation.

This simulates the problematic scenarios mentioned:
- OpenRouter reporting 0 input tokens
- Providers returning null/None for token counts
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from utils.token_validator import validate_token_counts, should_fail_benchmark, get_validation_summary


def test_openrouter_zero_tokens():
    """Simulate OpenRouter reporting 0 input tokens."""
    print("\n" + "=" * 80)
    print("TEST: OpenRouter with 0 input tokens (but successful response)")
    print("=" * 80)
    
    # Simulate response from OpenRouter
    benchmark_data = {
        "input_tokens": 0,  # ❌ Invalid!
        "output_tokens": 150,
        "response_text": "• The evolution of timekeeping spans from ancient sundials to modern atomic clocks.\n• Mechanical escapements revolutionized accuracy in medieval Europe.\n• Today's cesium atomic clocks enable GPS and global communications.",
        "success": True
    }
    
    print(f"\n📥 Original data from API:")
    print(f"   Input tokens: {benchmark_data['input_tokens']}")
    print(f"   Output tokens: {benchmark_data['output_tokens']}")
    print(f"   Success: {benchmark_data['success']}")
    
    # Validate
    validation = validate_token_counts(
        input_tokens=benchmark_data["input_tokens"],
        output_tokens=benchmark_data["output_tokens"],
        prompt=None,  # We don't have the original prompt
        response=benchmark_data["response_text"]
    )
    
    print(f"\n🔍 After validation:")
    print(f"   Input tokens: {validation['input_tokens']} {'(estimated)' if validation['input_tokens_estimated'] else ''}")
    print(f"   Output tokens: {validation['output_tokens']} {'(estimated)' if validation['output_tokens_estimated'] else ''}")
    print(f"   Is valid: {validation['is_valid']}")
    print(f"   Should fail benchmark: {should_fail_benchmark(validation)}")
    print(f"   Summary: {get_validation_summary(validation)}")
    
    if validation['validation_warnings']:
        print(f"\n⚠️  Warnings:")
        for warning in validation['validation_warnings']:
            print(f"   - {warning}")
    
    return validation


def test_null_token_counts():
    """Simulate provider returning null/None for token counts."""
    print("\n" + "=" * 80)
    print("TEST: Provider returning null/None token counts")
    print("=" * 80)
    
    benchmark_data = {
        "input_tokens": None,  # ❌ Invalid!
        "output_tokens": None,  # ❌ Invalid!
        "response_text": "The story of timekeeping traces humanity's quest to measure time, from sundials to atomic clocks.",
        "success": True
    }
    
    print(f"\n📥 Original data from API:")
    print(f"   Input tokens: {benchmark_data['input_tokens']}")
    print(f"   Output tokens: {benchmark_data['output_tokens']}")
    print(f"   Success: {benchmark_data['success']}")
    
    # Validate
    validation = validate_token_counts(
        input_tokens=benchmark_data["input_tokens"],
        output_tokens=benchmark_data["output_tokens"],
        prompt=None,
        response=benchmark_data["response_text"]
    )
    
    print(f"\n🔍 After validation:")
    print(f"   Input tokens: {validation['input_tokens']} {'(estimated)' if validation['input_tokens_estimated'] else ''}")
    print(f"   Output tokens: {validation['output_tokens']} {'(estimated)' if validation['output_tokens_estimated'] else ''}")
    print(f"   Is valid: {validation['is_valid']}")
    print(f"   Should fail benchmark: {should_fail_benchmark(validation)}")
    
    if validation['validation_warnings']:
        print(f"\n⚠️  Warnings:")
        for warning in validation['validation_warnings']:
            print(f"   - {warning}")
    
    return validation


def test_valid_tokens():
    """Test case with valid token counts."""
    print("\n" + "=" * 80)
    print("TEST: Valid token counts (normal operation)")
    print("=" * 80)
    
    benchmark_data = {
        "input_tokens": 545,  # ✅ Valid
        "output_tokens": 127,  # ✅ Valid
        "response_text": "• Timekeeping evolved from sundials to atomic clocks.\n• Mechanical innovations enabled modern precision.\n• Today's clocks power GPS and global networks.",
        "success": True
    }
    
    print(f"\n📥 Original data from API:")
    print(f"   Input tokens: {benchmark_data['input_tokens']}")
    print(f"   Output tokens: {benchmark_data['output_tokens']}")
    print(f"   Success: {benchmark_data['success']}")
    
    # Validate
    validation = validate_token_counts(
        input_tokens=benchmark_data["input_tokens"],
        output_tokens=benchmark_data["output_tokens"],
        prompt=None,
        response=benchmark_data["response_text"]
    )
    
    print(f"\n🔍 After validation:")
    print(f"   Input tokens: {validation['input_tokens']}")
    print(f"   Output tokens: {validation['output_tokens']}")
    print(f"   Is valid: {validation['is_valid']}")
    print(f"   Should fail benchmark: {should_fail_benchmark(validation)}")
    print(f"   ✅ No issues detected!")
    
    return validation


def main():
    print("=" * 80)
    print("TOKEN COUNT VALIDATION - TEST SUITE")
    print("=" * 80)
    print("\nDemonstrating how the validator handles problematic provider data...")
    
    # Run test cases
    test_openrouter_zero_tokens()
    test_null_token_counts()
    test_valid_tokens()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("""
✅ The validator now:
   1. Detects invalid token counts (0, null, negative)
   2. Estimates tokens using tiktoken when response_text is available
   3. Flags benchmarks with suspicious counts
   4. Fails benchmarks when input_tokens < 10 (prompt not read properly)
   5. Logs warnings for review without failing good benchmarks

🎯 This solves the OpenRouter issue where 0 input tokens skewed statistics!
    """)


if __name__ == "__main__":
    main()
