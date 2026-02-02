import time
import uuid
import json
import requests
from utils.env_helper import get_env
from utils.provider_service import is_reasoning_model, get_timeout_for_model
from utils.retry_logic import with_retry, RetryConfig

# Pricing per 1M tokens (approximate, check Together.ai website for latest)
PRICING = {
    "meta-llama/Llama-3.3-70B-Instruct-Turbo": {"input": 0.88, "output": 0.88},  # Latest
    "meta-llama/Llama-3-70b-chat-hf": {"input": 0.59, "output": 0.79},
    "meta-llama/Llama-3-8b-chat-hf": {"input": 0.10, "output": 0.10},
    "mistralai/Mixtral-8x7B-Instruct-v0.1": {"input": 0.24, "output": 0.24},
}

@with_retry(RetryConfig(max_retries=3, initial_delay=1.0, exponential_base=2.0))
def call_together(prompt: str, model: str = "meta-llama/Llama-3-8b-chat-hf"):
    """
    Call Together AI API and return benchmark results.
    Returns: dict with input_tokens, output_tokens, latency_ms, cost_usd, success, error_message, response_text
    """
    api_key = get_env("TOGETHER_API_KEY")
    if not api_key:
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "latency_ms": 0,
            "cost_usd": 0,
            "success": False,
            "error_message": "TOGETHER_API_KEY not found in environment",
            "response_text": None
        }
    
    # Get timeout based on model type (centralized logic)
    timeout_seconds = get_timeout_for_model(model)
    
    if is_reasoning_model(model):
        print(f"⏱️  Using extended {timeout_seconds:.0f}s timeout for reasoning model: {model}")
    
    url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Generate unique UUID for this request
    request_id = str(uuid.uuid4())
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Your task is to summarize the provided text into exactly three concise bullet points."},
            {"role": "user", "content": f"REQUEST ID: {request_id}\n\n{prompt}"}
        ],
        "temperature": 0.8,  # Higher temperature for more variation
        "stream": True  # Enable streaming for TTFT measurement
    }
    
    start_time = time.time()
    first_token_time = None
    status_code = 200
    
    try:
        # Send streaming request to Together AI API
        response = requests.post(url, json=payload, headers=headers, timeout=timeout_seconds, stream=True)
        status_code = response.status_code
        
        if response.status_code != 200:
            error_detail = response.json() if response.text else {}
            raise requests.exceptions.HTTPError(
                f"{response.status_code} {response.reason}: {error_detail.get('error', {}).get('message', response.text)}",
                response=response
            )
        
        # Collect streaming response (SSE format)
        response_text_parts = []
        first_chunk_received = False
        total_output_tokens = 0
        input_tokens = 0
        output_tokens = 0
        
        for line in response.iter_lines():
            if not line:
                continue
            
            line_text = line.decode('utf-8')
            if line_text.startswith('data: '):
                data_str = line_text[6:].strip()  # Remove 'data: ' prefix and whitespace
                if data_str == '[DONE]' or data_str == '':
                    break
                
                try:
                    # Parse JSON properly (not using eval)
                    chunk_data = json.loads(data_str)
                    
                    # Check if this chunk has content
                    if chunk_data.get('choices') and len(chunk_data['choices']) > 0:
                        choice = chunk_data['choices'][0]
                        delta = choice.get('delta', {})
                        content = delta.get('content')
                        
                        # Measure Time to First Token (TTFT) - when first content appears
                        if content and not first_chunk_received:
                            first_token_time = time.time()
                            first_chunk_received = True
                        
                        # Collect content
                        if content:
                            response_text_parts.append(content)
                            # Estimate tokens (rough: 1 token ≈ 4 characters)
                            total_output_tokens += len(content) // 4
                    
                    # Get token usage from final chunk if available
                    if chunk_data.get('usage'):
                        input_tokens = chunk_data['usage'].get('prompt_tokens', 0)
                        output_tokens = chunk_data['usage'].get('completion_tokens', 0)
                        
                except json.JSONDecodeError as e:
                    # Skip invalid JSON lines
                    continue
                except Exception as e:
                    # Skip other errors but continue processing
                    continue
        
        # End time for total latency
        end_time = time.time()
        total_latency_ms = (end_time - start_time) * 1000
        
        # Calculate TTFT (Time to First Token)
        ttft_ms = None
        if first_token_time:
            ttft_ms = (first_token_time - start_time) * 1000
        
        # Calculate TPS (Tokens Per Second)
        # Use actual output_tokens if available, otherwise use estimated total_output_tokens
        tps = None
        tokens_for_tps = output_tokens if output_tokens > 0 else total_output_tokens
        if first_token_time and tokens_for_tps > 1:
            time_for_tokens = end_time - first_token_time
            if time_for_tokens > 0:
                tps = (tokens_for_tps - 1) / time_for_tokens
        
        # Combine response text
        response_text = "".join(response_text_parts)
        
        # Use actual token counts if available, otherwise estimate
        if input_tokens == 0:
            input_tokens = len(prompt.split()) // 0.75
        if output_tokens == 0:
            output_tokens = total_output_tokens
        
        # Calculate cost
        pricing = PRICING.get(model, PRICING["meta-llama/Llama-3-8b-chat-hf"])
        cost_usd = (input_tokens / 1_000_000 * pricing["input"]) + (output_tokens / 1_000_000 * pricing["output"])
        
        return {
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
            "total_latency_ms": total_latency_ms,
            "latency_ms": total_latency_ms,  # Backward compatibility
            "ttft_ms": ttft_ms,
            "tps": tps,
            "status_code": status_code,
            "cost_usd": cost_usd,
            "success": True,
            "error_message": None,
            "response_text": response_text
        }
        
    except requests.exceptions.HTTPError as e:
        end_time = time.time()
        total_latency_ms = (end_time - start_time) * 1000
        error_msg = str(e)
        try:
            if hasattr(e, 'response') and e.response:
                error_detail = e.response.json() if e.response.text else {}
                if "error" in error_detail:
                    error_msg = f"{error_msg}: {error_detail.get('error', {}).get('message', '')}"
        except:
            pass
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_latency_ms": total_latency_ms,
            "latency_ms": total_latency_ms,  # Backward compatibility
            "ttft_ms": None,
            "tps": None,
            "status_code": status_code,
            "cost_usd": 0,
            "success": False,
            "error_message": error_msg,
            "response_text": None
        }
    except Exception as e:
        end_time = time.time()
        total_latency_ms = (end_time - start_time) * 1000
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_latency_ms": total_latency_ms,
            "latency_ms": total_latency_ms,  # Backward compatibility
            "ttft_ms": None,
            "tps": None,
            "status_code": 500,
            "cost_usd": 0,
            "success": False,
            "error_message": str(e),
            "response_text": None
        }


def fetch_models_together():
    """
    Fetch available models from Together AI API.
    
    Returns:
        Dictionary with success, models, and error
    """
    api_key = get_env("TOGETHER_API_KEY")
    if not api_key:
        return {
            "success": False,
            "models": [],
            "error": "TOGETHER_API_KEY not found in environment"
        }
    
    try:
        response = requests.get(
            "https://api.together.xyz/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        # Filter for chat/instruct models
        models = [
            model["id"] for model in data
            if model.get("type") == "chat" or "instruct" in model["id"].lower()
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
