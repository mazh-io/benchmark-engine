"""
Token Count Validator

Validates and corrects token counts from provider APIs.
Provides fallback estimation when providers return invalid counts (0 or null).

This solves the problem of providers like OpenRouter sometimes reporting 
0 input tokens, which skews benchmark statistics.
"""

from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def estimate_tokens(text: str, method: str = "simple") -> int:
    """
    Estimate token count for text using various methods.
    
    Args:
        text: The text to estimate tokens for
        method: Estimation method - "simple", "tiktoken", or "word_based"
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    
    if method == "tiktoken":
        try:
            import tiktoken
            # Use cl100k_base (GPT-4/GPT-3.5-turbo tokenizer) as default
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except ImportError:
            logger.warning("tiktoken not installed, falling back to simple estimation")
            method = "simple"
        except Exception as e:
            logger.warning(f"tiktoken estimation failed: {e}, falling back to simple")
            method = "simple"
    
    if method == "word_based":
        # More conservative: ~1.3 tokens per word on average for English
        words = len(text.split())
        return int(words * 1.3)
    
    # Simple method (default): ~4 characters per token
    # This is a reasonable approximation for most languages
    return max(1, len(text) // 4)


def validate_token_counts(
    input_tokens: Optional[int],
    output_tokens: Optional[int],
    prompt: Optional[str] = None,
    response: Optional[str] = None,
    min_input_tokens: int = 10
) -> Dict[str, any]:
    """
    Validate token counts and provide fallback estimates if needed.
    
    This function:
    1. Checks if token counts are valid (not None, not 0, not negative)
    2. Verifies input tokens meet minimum threshold
    3. Provides fallback estimates using local tokenizer if needed
    4. Flags suspicious token counts for review
    
    Args:
        input_tokens: Input token count from provider API (may be None/0)
        output_tokens: Output token count from provider API (may be None/0)
        prompt: The input prompt text (for estimation if needed)
        response: The output response text (for estimation if needed)
        min_input_tokens: Minimum expected input tokens (default: 10)
        
    Returns:
        Dict with:
        - input_tokens: Validated/estimated input tokens
        - output_tokens: Validated/estimated output tokens
        - input_tokens_estimated: Boolean flag
        - output_tokens_estimated: Boolean flag
        - validation_warnings: List of warnings
        - is_valid: Whether token counts are trustworthy
        
    Examples:
        >>> validate_token_counts(0, 100, prompt="Hello world" * 50)
        {
            'input_tokens': 127,  # Estimated
            'output_tokens': 100,
            'input_tokens_estimated': True,
            'output_tokens_estimated': False,
            'validation_warnings': ['Input tokens was 0, used estimation'],
            'is_valid': False
        }
    """
    result = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_tokens_estimated": False,
        "output_tokens_estimated": False,
        "validation_warnings": [],
        "is_valid": True
    }
    
    # Validate input tokens
    if input_tokens is None or input_tokens <= 0:
        if prompt:
            estimated = estimate_tokens(prompt, method="tiktoken")
            result["input_tokens"] = estimated
            result["input_tokens_estimated"] = True
            result["validation_warnings"].append(
                f"Input tokens was {input_tokens}, estimated {estimated} from prompt"
            )
            result["is_valid"] = False
            logger.warning(
                f"Invalid input_tokens ({input_tokens}), estimated {estimated} tokens"
            )
        else:
            result["input_tokens"] = 0
            result["validation_warnings"].append(
                "Input tokens invalid and no prompt provided for estimation"
            )
            result["is_valid"] = False
    
    # Check if input tokens meet minimum threshold
    if result["input_tokens"] < min_input_tokens:
        result["validation_warnings"].append(
            f"Input tokens ({result['input_tokens']}) below minimum threshold ({min_input_tokens})"
        )
        result["is_valid"] = False
    
    # Validate output tokens
    if output_tokens is None or output_tokens <= 0:
        if response:
            estimated = estimate_tokens(response, method="tiktoken")
            result["output_tokens"] = estimated
            result["output_tokens_estimated"] = True
            result["validation_warnings"].append(
                f"Output tokens was {output_tokens}, estimated {estimated} from response"
            )
            result["is_valid"] = False
            logger.warning(
                f"Invalid output_tokens ({output_tokens}), estimated {estimated} tokens"
            )
        else:
            result["output_tokens"] = 0
            result["validation_warnings"].append(
                "Output tokens invalid and no response provided for estimation"
            )
            result["is_valid"] = False
    
    return result


def should_fail_benchmark(validation_result: Dict) -> bool:
    """
    Determine if a benchmark should be marked as failed based on token validation.
    
    Benchmarks should fail if:
    - Input tokens < 10 (model didn't read the prompt properly)
    - Both input and output tokens are 0/invalid
    
    Args:
        validation_result: Result from validate_token_counts()
        
    Returns:
        True if benchmark should be marked as failed
    """
    input_tokens = validation_result.get("input_tokens", 0)
    output_tokens = validation_result.get("output_tokens", 0)
    
    # Fail if input tokens too low (prompt not properly processed)
    if input_tokens < 10:
        return True
    
    # Fail if both are invalid
    if input_tokens == 0 and output_tokens == 0:
        return True
    
    return False


def get_validation_summary(validation_result: Dict) -> str:
    """
    Get a human-readable summary of validation issues.
    
    Args:
        validation_result: Result from validate_token_counts()
        
    Returns:
        Summary string for logging/display
    """
    if validation_result["is_valid"]:
        return "Token counts valid"
    
    warnings = validation_result["validation_warnings"]
    summary_parts = []
    
    if validation_result["input_tokens_estimated"]:
        summary_parts.append(f"Input: {validation_result['input_tokens']} (estimated)")
    else:
        summary_parts.append(f"Input: {validation_result['input_tokens']}")
    
    if validation_result["output_tokens_estimated"]:
        summary_parts.append(f"Output: {validation_result['output_tokens']} (estimated)")
    else:
        summary_parts.append(f"Output: {validation_result['output_tokens']}")
    
    summary = " | ".join(summary_parts)
    
    if warnings:
        summary += f" | Warnings: {len(warnings)}"
    
    return summary


# Example usage and tests
if __name__ == "__main__":
    print("Testing token count validator...")
    print("=" * 80)
    
    # Test case 1: Invalid input tokens (0)
    print("\n1. Invalid input tokens (0):")
    result = validate_token_counts(
        input_tokens=0,
        output_tokens=100,
        prompt="The history of timekeeping is a testament to humanity's obsession with measuring the passage of existence." * 5,
        response="Summary bullet points here..."
    )
    print(f"   Input: {result['input_tokens']} (estimated: {result['input_tokens_estimated']})")
    print(f"   Output: {result['output_tokens']} (estimated: {result['output_tokens_estimated']})")
    print(f"   Valid: {result['is_valid']}")
    print(f"   Should fail: {should_fail_benchmark(result)}")
    print(f"   Warnings: {result['validation_warnings']}")
    
    # Test case 2: Valid tokens
    print("\n2. Valid token counts:")
    result = validate_token_counts(
        input_tokens=500,
        output_tokens=150,
        prompt="Test prompt",
        response="Test response"
    )
    print(f"   Input: {result['input_tokens']} (estimated: {result['input_tokens_estimated']})")
    print(f"   Output: {result['output_tokens']} (estimated: {result['output_tokens_estimated']})")
    print(f"   Valid: {result['is_valid']}")
    print(f"   Should fail: {should_fail_benchmark(result)}")
    
    # Test case 3: Input tokens too low
    print("\n3. Input tokens below threshold:")
    result = validate_token_counts(
        input_tokens=5,
        output_tokens=100,
        prompt="Hi",
        response="Hello there!"
    )
    print(f"   Input: {result['input_tokens']} (estimated: {result['input_tokens_estimated']})")
    print(f"   Output: {result['output_tokens']} (estimated: {result['output_tokens_estimated']})")
    print(f"   Valid: {result['is_valid']}")
    print(f"   Should fail: {should_fail_benchmark(result)}")
    print(f"   Warnings: {result['validation_warnings']}")
    
    # Test case 4: Both tokens invalid
    print("\n4. Both tokens invalid (null):")
    result = validate_token_counts(
        input_tokens=None,
        output_tokens=None,
        prompt="Test prompt here",
        response="Test response here"
    )
    print(f"   Input: {result['input_tokens']} (estimated: {result['input_tokens_estimated']})")
    print(f"   Output: {result['output_tokens']} (estimated: {result['output_tokens_estimated']})")
    print(f"   Valid: {result['is_valid']}")
    print(f"   Should fail: {should_fail_benchmark(result)}")
    
    print("\n" + "=" * 80)
    print("✅ All tests complete!")
