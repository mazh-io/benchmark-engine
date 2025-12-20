import time
import uuid
from groq import Groq
from utils.env_helper import get_env

# Pricing per 1M tokens (approximate, check Groq website for latest)
PRICING = {
    "llama-3.1-70b-versatile": {"input": 0.59, "output": 0.79},
    "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
    "mixtral-8x7b-32768": {"input": 0.24, "output": 0.24},
    "gemma-7b-it": {"input": 0.07, "output": 0.07},
}

def call_groq(prompt: str, model: str = "llama-3.1-8b-instant"):
    """
    Call Groq API and return benchmark results.
    Returns: dict with input_tokens, output_tokens, latency_ms, cost_usd, success, error_message, response_text
    """
    api_key = get_env("GROQ_API_KEY")
    if not api_key:
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "latency_ms": 0,
            "cost_usd": 0,
            "success": False,
            "error_message": "GROQ_API_KEY not found in environment",
            "response_text": None
        }
    
    client = Groq(api_key=api_key)
    
    # Generate unique UUID for this request
    request_id = str(uuid.uuid4())
    
    start_time = time.time()
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Your task is to summarize the provided text into exactly three concise bullet points."},
                {"role": "user", "content": f"REQUEST ID: {request_id}\n\n{prompt}"}
            ],
            temperature=0.8  # Higher temperature for more variation
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        response_text = response.choices[0].message.content
        
        # Calculate cost
        pricing = PRICING.get(model, PRICING["llama-3.1-8b-instant"])
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

