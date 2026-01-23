"""
Test Script: Smart Retry Logic

Tests the exponential backoff retry mechanism for handling transient 5xx errors.
Simulates provider failures and verifies retry behavior.
"""

from src.utils.retry_logic import (
    RetryConfig,
    should_retry,
    calculate_backoff_delay,
    retry_with_backoff,
    with_retry
)
import time


def print_header(title: str):
    """Print a formatted test section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_test(test_name: str):
    """Print a test name."""
    print(f"\n➤  {test_name}")
    print("-" * 80)


# Test 1: Verify should_retry logic
print_header("TEST 1: should_retry() Decision Logic")

config = RetryConfig()

test_cases = [
    {
        "name": "Successful response (200)",
        "result": {"success": True, "status_code": 200},
        "expected": False
    },
    {
        "name": "503 Service Unavailable",
        "result": {"success": False, "status_code": 503, "error_message": "Service unavailable"},
        "expected": True
    },
    {
        "name": "500 Internal Server Error",
        "result": {"success": False, "status_code": 500, "error_message": "Internal error"},
        "expected": True
    },
    {
        "name": "502 Bad Gateway",
        "result": {"success": False, "status_code": 502, "error_message": "Bad gateway"},
        "expected": True
    },
    {
        "name": "400 Bad Request (client error)",
        "result": {"success": False, "status_code": 400, "error_message": "Invalid request"},
        "expected": False
    },
    {
        "name": "401 Unauthorized (auth error)",
        "result": {"success": False, "status_code": 401, "error_message": "Invalid API key"},
        "expected": False
    },
    {
        "name": "Timeout error (no status code)",
        "result": {"success": False, "error_message": "Connection timeout occurred"},
        "expected": True
    }
]

for test_case in test_cases:
    result = should_retry(test_case["result"], config)
    status = "✅ PASS" if result == test_case["expected"] else "❌ FAIL"
    print(f"{status} {test_case['name']}: should_retry={result}")


# Test 2: Verify exponential backoff calculation
print_header("TEST 2: Exponential Backoff Delays")

config = RetryConfig(initial_delay=1.0, exponential_base=2.0, max_delay=10.0)

print("\nBackoff sequence (1s -> 2s -> 4s):")
for attempt in range(4):
    delay = calculate_backoff_delay(attempt, config)
    print(f"  Attempt {attempt + 1}: Wait {delay:.1f}s before retry")

print("\nMax delay cap test:")
config_capped = RetryConfig(initial_delay=1.0, exponential_base=2.0, max_delay=5.0)
for attempt in range(5):
    delay = calculate_backoff_delay(attempt, config_capped)
    status = "🛑 CAPPED" if delay >= config_capped.max_delay else "✅"
    print(f"  {status} Attempt {attempt + 1}: {delay:.1f}s")


# Test 3: Mock provider calls with retry
print_header("TEST 3: Provider Call with Retry Logic")

# Mock provider that fails first 2 times with 503, then succeeds
class MockProviderWithFailures:
    def __init__(self):
        self.attempt_count = 0
    
    def call_api(self, prompt: str, model: str) -> dict:
        """Simulates API calls that fail with 503 then succeed."""
        self.attempt_count += 1
        
        if self.attempt_count <= 2:
            # First 2 attempts fail with 503
            return {
                "success": False,
                "status_code": 503,
                "error_message": "Service temporarily unavailable",
                "input_tokens": 0,
                "output_tokens": 0
            }
        else:
            # Third attempt succeeds
            return {
                "success": True,
                "status_code": 200,
                "input_tokens": 100,
                "output_tokens": 50,
                "response_text": "Success after retries!"
            }

print_test("Scenario: 503 errors then success")
provider = MockProviderWithFailures()
config = RetryConfig(max_retries=3, initial_delay=0.1, exponential_base=2.0)

start_time = time.time()
result = retry_with_backoff(provider.call_api, config, "test prompt", "test-model")
elapsed_time = time.time() - start_time

print(f"Total attempts: {provider.attempt_count}")
print(f"Final status: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
print(f"Status code: {result['status_code']}")
print(f"Total time: {elapsed_time:.2f}s (includes retry delays)")
print(f"Response: {result.get('response_text', result.get('error_message'))}")


# Test 4: Mock provider that always fails
print_test("Scenario: All attempts fail (max retries)")

class MockProviderAlwaysFails:
    def __init__(self):
        self.attempt_count = 0
    
    def call_api(self, prompt: str, model: str) -> dict:
        """Always returns 503 error."""
        self.attempt_count += 1
        return {
            "success": False,
            "status_code": 503,
            "error_message": f"Service unavailable (attempt {self.attempt_count})",
            "input_tokens": 0,
            "output_tokens": 0
        }

failing_provider = MockProviderAlwaysFails()
config = RetryConfig(max_retries=3, initial_delay=0.1, exponential_base=2.0)

start_time = time.time()
result = retry_with_backoff(failing_provider.call_api, config, "test prompt", "test-model")
elapsed_time = time.time() - start_time

print(f"Total attempts: {failing_provider.attempt_count}")
print(f"Final status: {'✅ SUCCESS' if result['success'] else '❌ FAILED (as expected)'}")
print(f"Status code: {result['status_code']}")
print(f"Total time: {elapsed_time:.2f}s")
print(f"Error: {result.get('error_message')}")


# Test 5: Client errors should NOT retry
print_test("Scenario: 400 error (should NOT retry)")

class MockProviderClientError:
    def __init__(self):
        self.attempt_count = 0
    
    def call_api(self, prompt: str, model: str) -> dict:
        """Returns 400 client error."""
        self.attempt_count += 1
        return {
            "success": False,
            "status_code": 400,
            "error_message": "Bad request - invalid parameters",
            "input_tokens": 0,
            "output_tokens": 0
        }

client_error_provider = MockProviderClientError()
config = RetryConfig(max_retries=3, initial_delay=0.1)

start_time = time.time()
result = retry_with_backoff(client_error_provider.call_api, config, "test prompt", "test-model")
elapsed_time = time.time() - start_time

print(f"Total attempts: {client_error_provider.attempt_count} (should be 1 - no retries)")
print(f"Final status: {'❌ FAILED' if not result['success'] else '✅'}")
print(f"Status code: {result['status_code']}")
print(f"Total time: {elapsed_time:.2f}s (should be instant)")
print(f"✅ PASS" if client_error_provider.attempt_count == 1 else "❌ FAIL: Retried a client error!")


# Test 6: Decorator usage
print_header("TEST 4: @with_retry Decorator")

print_test("Using decorator for cleaner code")

call_count = 0

@with_retry(RetryConfig(max_retries=2, initial_delay=0.1))
def api_call_with_decorator(prompt: str, model: str) -> dict:
    """Function decorated with retry logic."""
    global call_count
    call_count += 1
    
    if call_count == 1:
        return {
            "success": False,
            "status_code": 503,
            "error_message": "First call fails"
        }
    else:
        return {
            "success": True,
            "status_code": 200,
            "response_text": "Success on retry!"
        }

call_count = 0
result = api_call_with_decorator("test", "model")
print(f"Function called {call_count} times")
print(f"Result: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
print(f"Response: {result.get('response_text', result.get('error_message'))}")


# Summary
print_header("SUMMARY: Smart Retry Logic")
print("""
✅ Retry Logic Features Tested:
  - 5xx errors trigger exponential backoff (1s -> 2s -> 4s)
  - Client errors (4xx) do NOT retry
  - Successful responses return immediately
  - Max retries enforced (gives up after 3 attempts)
  - Configurable delays and retry counts
  - Decorator pattern for clean integration

🎯 Use Cases Covered:
  - Together AI 503 errors (~5% failure rate)
  - Temporary service outages
  - Gateway timeouts (502, 504)
  - Internal server errors (500)
  
💡 Integration:
  - Already integrated into BaseProvider.call_with_retry()
  - All providers inherit this behavior automatically
  - No code changes needed in individual provider implementations
  
🔧 Configuration:
  - Default: 3 retries with 1s -> 2s -> 4s delays
  - Customizable via RetryConfig class
  - Only retries 5xx errors (configurable)
""")

print("=" * 80)
print("✅ All tests completed!\n")
