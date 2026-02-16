import time
import requests
import uuid
import json
from utils.env_helper import get_env
from utils.provider_service import is_reasoning_model, get_timeout_for_model

# OpenRouter pricing varies by model, using approximate values
# Check https://openrouter.ai/models for exact pricing
PRICING = {
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "anthropic/claude-3-haiku": {"input": 0.25, "output": 1.25},
    "google/gemini-pro": {"input": 0.50, "output": 1.50},
    "meta-llama/llama-3.1-70b-instruct": {"input": 0.59, "output": 0.79},
    "minimax/minimax-01": {"input": 0.30, "output": 1.50},  # Challenger to Claude Sonnet
}

def call_openrouter(prompt: str, model: str = "openai/gpt-4o-mini"):
    """
    Call OpenRouter API and return benchmark results.
    Returns: dict with input_tokens, output_tokens, latency_ms, cost_usd, success, error_message, response_text
    """
    api_key = get_env("OPENROUTER_API_KEY")
    if not api_key:
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "latency_ms": 0,
            "cost_usd": 0,
            "success": False,
            "error_message": "OPENROUTER_API_KEY not found in environment",
            "response_text": None
        }
    
    # Get timeout based on model type (centralized logic)
    timeout_seconds = get_timeout_for_model(model)
    
    if is_reasoning_model(model):
        print(f"⏱️  Using extended {timeout_seconds:.0f}s timeout for reasoning model: {model}")
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/benchmark-engine",  # Optional
        "X-Title": "Benchmark Engine"  # Optional
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
        "max_tokens": 1024,  # Limit output tokens (some models like Minimax have restrictions)
        "stream": True  # Enable streaming for TTFT measurement
    }
    
    start_time = time.time()
    first_token_time = None
    status_code = 200
    
    try:
        # Send streaming request to OpenRouter API
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
        total_cost = None
        
        for line in response.iter_lines():
            if not line:
                continue
            
            line_text = line.decode('utf-8')
            if line_text.startswith('data: '):
                data_str = line_text[6:]  # Remove 'data: ' prefix
                if data_str == '[DONE]':
                    break
                
                try:
                    import json
                    chunk_data = json.loads(data_str)
                    
                    # Measure Time to First Token (TTFT)
                    if not first_chunk_received and chunk_data.get('choices') and chunk_data['choices'][0].get('delta', {}).get('content'):
                        first_token_time = time.time()
                        first_chunk_received = True
                    
                    # Collect content
                    if chunk_data.get('choices') and chunk_data['choices'][0].get('delta', {}).get('content'):
                        content = chunk_data['choices'][0]['delta']['content']
                        response_text_parts.append(content)
                        total_output_tokens += len(content) // 4  # Estimate
                    
                    # Get token usage from final chunk if available
                    if chunk_data.get('usage'):
                        input_tokens = chunk_data['usage'].get('prompt_tokens', 0)
                        output_tokens = chunk_data['usage'].get('completion_tokens', 0)
                    
                    # Get cost if available
                    if chunk_data.get('total_cost'):
                        total_cost = chunk_data['total_cost']
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse SSE chunk: {e}")
                    print(f"  Raw data: {data_str[:200]}")
                except Exception as e:
                    print(f"Warning: Error processing chunk: {e}")
                    print(f"  Chunk data keys: {chunk_data.keys() if 'chunk_data' in locals() else 'N/A'}")
        
        # End time for total latency
        end_time = time.time()
        total_latency_ms = (end_time - start_time) * 1000
        
        # Calculate TTFT (Time to First Token)
        ttft_ms = None
        if first_token_time:
            ttft_ms = (first_token_time - start_time) * 1000
        
        # Calculate TPS (Tokens Per Second)
        tps = None
        if first_token_time and output_tokens > 1:
            time_for_tokens = end_time - first_token_time
            if time_for_tokens > 0:
                tps = (output_tokens - 1) / time_for_tokens
        
        # Combine response text
        response_text = "".join(response_text_parts)
        
        # Check if we got an empty response
        if not response_text or len(response_text.strip()) == 0:
            print(f"Warning: OpenRouter ({model}) returned empty response")
            print(f"  Chunks received: {len(response_text_parts)}")
            print(f"  First chunk received: {first_chunk_received}")
            return {
                "input_tokens": len(prompt.split()) // 0.75 or 1,
                "output_tokens": 0,
                "total_latency_ms": total_latency_ms,
                "latency_ms": total_latency_ms,
                "ttft_ms": None,
                "tps": None,
                "status_code": 200,
                "cost_usd": 0,
                "success": False,
                "error_message": "[EMPTY_RESPONSE] API returned 200 but no text content",
                "response_text": None
            }
        
        # Use actual token counts if available, otherwise estimate
        if input_tokens == 0:
            input_tokens = len(prompt.split()) // 0.75
        if output_tokens == 0:
            output_tokens = total_output_tokens
        
        # Calculate cost - OpenRouter provides cost in response, but we'll calculate if not available
        if total_cost:
            cost_usd = total_cost / 100 if total_cost > 1 else total_cost  # Convert from cents if needed
        else:
            pricing = PRICING.get(model, PRICING["openai/gpt-4o-mini"])
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


def fetch_models_openrouter():
    """
    Fetch available models from OpenRouter API (public endpoint).
    
    Returns:
        Dictionary with success, models, and error
    """
    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        models = [model["id"] for model in data.get("data", [])]
        
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

