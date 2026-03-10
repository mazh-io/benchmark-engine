import time
import uuid
import requests
import httpx
from openai import OpenAI, RateLimitError, APIError, APIConnectionError, APITimeoutError
from utils.env_helper import get_env
from utils.provider_service import is_reasoning_model, get_timeout_for_model



PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    # O1 models (reasoning models)
    "o1-preview": {"input": 15.00, "output": 60.00},
    "o1-mini": {"input": 3.00, "output": 12.00},
    "o1": {"input": 15.00, "output": 60.00},  # Alias for o1-preview
}

def call_openai(prompt: str, model: str = "gpt-4o-mini"):
    """
    Call OpenAI API and return benchmark results.
    
    Args:
        prompt: Text that was sent to the AI
        model: Name of the model (e.g. "gpt-4o-mini")
    
    Returns:
        Dictionary with all the request data: input_tokens, output_tokens, latency_ms, cost_usd, 
        success, error_message, response_text
    """
    # Get API key from .env file
    api_key = get_env("OPENAI_API_KEY")
    if not api_key:
        # If no API key, return error result with all the request data
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "latency_ms": 0,
            "cost_usd": 0,
            "success": False,
            "error_message": "OPENAI_API_KEY not found in environment",
            "response_text": None
        }
    
    # Configure HTTP client with extended timeout for reasoning models
    # O-series models (o1, o3, o4-mini) can take 10-20s to think before first token
    http_client = httpx.Client(
        timeout=httpx.Timeout(120.0, connect=10.0)  # 120s request, 10s connect
    )
    
    # Create OpenAI client to interact with the API
    client = OpenAI(api_key=api_key, http_client=http_client)
    
    # Generate unique UUID for this request (for tracking)
    request_id = str(uuid.uuid4())
    
    # Start time for latency calculation
    start_time = time.time()
    first_token_time = None
    status_code = 200
    
    try:
        reasoning = is_reasoning_model(model)
        timeout_seconds = get_timeout_for_model(model)
        
        request_params = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant. Your task is to summarize the provided text into exactly three concise bullet points."},
                {"role": "user", "content": f"REQUEST ID: {request_id}\n\n{prompt}"}
            ],
            "user": request_id,
            "stream": True,
            "stream_options": {"include_usage": True},
            "timeout": timeout_seconds,
        }
        
        if reasoning:
            request_params["temperature"] = 1.0
            print(f"⏱️  Using extended {timeout_seconds:.0f}s timeout for reasoning model: {model}")
        else:
            request_params["temperature"] = 0.8
            request_params["top_p"] = 0.9
        
        stream = client.chat.completions.create(**request_params)
        
        response_text_parts = []
        first_chunk_received = False
        estimated_output_tokens = 0
        usage_data = None
        
        for chunk in stream:
            if not first_chunk_received and chunk.choices and chunk.choices[0].delta.content:
                first_token_time = time.time()
                first_chunk_received = True
            
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                response_text_parts.append(content)
                estimated_output_tokens += max(1, len(content) // 4)
            
            if hasattr(chunk, 'usage') and chunk.usage:
                usage_data = {
                    "prompt_tokens": chunk.usage.prompt_tokens,
                    "completion_tokens": chunk.usage.completion_tokens,
                }
        
        end_time = time.time()
        total_latency_ms = (end_time - start_time) * 1000
        
        ttft_ms = None
        if first_token_time:
            ttft_ms = (first_token_time - start_time) * 1000
        
        response_text = "".join(response_text_parts)
        
        # Use real usage data from API when available, fall back to estimates
        if usage_data:
            input_tokens = usage_data["prompt_tokens"]
            output_tokens = usage_data["completion_tokens"]
        else:
            input_tokens = max(1, len(prompt) // 4)
            output_tokens = estimated_output_tokens
        
        tps = None
        if first_token_time and output_tokens > 1:
            time_for_tokens = end_time - first_token_time
            if time_for_tokens > 0:
                tps = (output_tokens - 1) / time_for_tokens
        
        pricing = PRICING.get(model, PRICING["gpt-4o-mini"])
        cost_usd = (input_tokens / 1_000_000 * pricing["input"]) + (output_tokens / 1_000_000 * pricing["output"])
        
        return {
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
            "total_latency_ms": total_latency_ms,
            "latency_ms": total_latency_ms,
            "ttft_ms": ttft_ms,
            "tps": tps,
            "status_code": status_code,
            "cost_usd": cost_usd,
            "success": True,
            "error_message": None,
            "response_text": response_text
        }
    
    except RateLimitError as e:
        # Rate limit error - will be retried by call_with_retry
        end_time = time.time()
        total_latency_ms = (end_time - start_time) * 1000
        
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_latency_ms": total_latency_ms,
            "latency_ms": total_latency_ms,
            "ttft_ms": None,
            "tps": None,
            "status_code": 429,
            "cost_usd": 0,
            "success": False,
            "error_message": f"[RATE_LIMIT] {str(e)}",
            "response_text": None
        }
    
    except (APIError, APIConnectionError, APITimeoutError) as e:
        # OpenAI API specific errors
        end_time = time.time()
        total_latency_ms = (end_time - start_time) * 1000
        
        status_code = 500
        if hasattr(e, 'status_code'):
            status_code = e.status_code
        
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_latency_ms": total_latency_ms,
            "latency_ms": total_latency_ms,
            "ttft_ms": None,
            "tps": None,
            "status_code": status_code,
            "cost_usd": 0,
            "success": False,
            "error_message": f"[{type(e).__name__}] {str(e)}",
            "response_text": None
        }
        
    except Exception as e:
        # Generic error handling
        end_time = time.time()
        total_latency_ms = (end_time - start_time) * 1000
        
        status_code = 500
        if hasattr(e, 'status_code'):
            status_code = e.status_code
        elif hasattr(e, 'response') and hasattr(e.response, 'status_code'):
            status_code = e.response.status_code
        
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_latency_ms": total_latency_ms,
            "latency_ms": total_latency_ms,
            "ttft_ms": None,
            "tps": None,
            "status_code": status_code,
            "cost_usd": 0,
            "success": False,
            "error_message": str(e),
            "response_text": None
        }


def fetch_models_openai():
    """
    Fetch available models from OpenAI API.
    
    Returns:
        Dictionary with:
            - success: bool
            - models: List[str] (model IDs)
            - error: Optional[str]
    """
    api_key = get_env("OPENAI_API_KEY")
    if not api_key:
        return {
            "success": False,
            "models": [],
            "error": "OPENAI_API_KEY not found in environment"
        }
    
    try:
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        # Filter for chat/completion models only
        models = [
            model["id"] for model in data.get("data", [])
            if any(prefix in model["id"] for prefix in ["gpt-", "o1", "o3", "o4"])
        ]
        
        return {
            "success": True,
            "models": sorted(models),
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "models": [],
            "error": str(e)
        }

