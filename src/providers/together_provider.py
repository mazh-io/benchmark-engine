import os
import time
import uuid
import requests
from dotenv import load_dotenv

load_dotenv()

# Pricing per 1M tokens (approximate, check Together.ai website for latest)
PRICING = {
    "meta-llama/Llama-3-70b-chat-hf": {"input": 0.59, "output": 0.79},
    "meta-llama/Llama-3-8b-chat-hf": {"input": 0.10, "output": 0.10},
    "mistralai/Mixtral-8x7B-Instruct-v0.1": {"input": 0.24, "output": 0.24},
}

def call_together(prompt: str, model: str = "meta-llama/Llama-3-8b-chat-hf"):
    """
    Call Together AI API and return benchmark results.
    Returns: dict with input_tokens, output_tokens, latency_ms, cost_usd, success, error_message, response_text
    """
    api_key = os.getenv("TOGETHER_API_KEY")
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
        "temperature": 0.8  # Higher temperature for more variation
    }
    
    start_time = time.time()
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        if response.status_code != 200:
            error_detail = response.json() if response.text else {}
            raise requests.exceptions.HTTPError(
                f"{response.status_code} {response.reason}: {error_detail.get('error', {}).get('message', response.text)}",
                response=response
            )
        response.raise_for_status()
        data = response.json()
        
        latency_ms = (time.time() - start_time) * 1000
        
        input_tokens = data["usage"]["prompt_tokens"]
        output_tokens = data["usage"]["completion_tokens"]
        response_text = data["choices"][0]["message"]["content"]
        
        # Calculate cost
        pricing = PRICING.get(model, PRICING["meta-llama/Llama-3-8b-chat-hf"])
        cost_usd = (input_tokens / 1_000_000 * pricing["input"]) + (output_tokens / 1_000_000 * pricing["output"])
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": latency_ms,
            "cost_usd": cost_usd,
            "success": True,
            "error_message": None,
            "response_text": response_text
        }
        
    except requests.exceptions.HTTPError as e:
        latency_ms = (time.time() - start_time) * 1000
        error_msg = str(e)
        try:
            error_detail = response.json()
            if "error" in error_detail:
                error_msg = f"{error_msg}: {error_detail.get('error', {}).get('message', '')}"
        except:
            pass
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "latency_ms": latency_ms,
            "cost_usd": 0,
            "success": False,
            "error_message": error_msg,
            "response_text": None
        }
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "latency_ms": latency_ms,
            "cost_usd": 0,
            "success": False,
            "error_message": str(e),
            "response_text": None
        }
