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
    first_token_time = None
    status_code = 200
    
    try:
        # Send streaming request to Groq API for TTFT measurement
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Your task is to summarize the provided text into exactly three concise bullet points."},
                {"role": "user", "content": f"REQUEST ID: {request_id}\n\n{prompt}"}
            ],
            temperature=0.8,  # Higher temperature for more variation
            stream=True  # Enable streaming for TTFT measurement
        )
        
        # Collect streaming response
        response_text_parts = []
        first_chunk_received = False
        total_output_tokens = 0
        
        for chunk in stream:
            # Measure Time to First Token (TTFT)
            if not first_chunk_received and chunk.choices and chunk.choices[0].delta.content:
                first_token_time = time.time()
                first_chunk_received = True
            
            # Collect content
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                response_text_parts.append(content)
                # Approximate token count (rough estimate: 1 token ≈ 4 characters)
                total_output_tokens += len(content) // 4
        
        # End time for total latency
        end_time = time.time()
        total_latency_ms = (end_time - start_time) * 1000
        
        # Calculate TTFT (Time to First Token)
        ttft_ms = None
        if first_token_time:
            ttft_ms = (first_token_time - start_time) * 1000
        
        # Calculate TPS (Tokens Per Second)
        # Formula: (Total Tokens - 1) / (Time End - Time First Token)
        tps = None
        if first_token_time and total_output_tokens > 1:
            time_for_tokens = end_time - first_token_time
            if time_for_tokens > 0:
                tps = (total_output_tokens - 1) / time_for_tokens
        
        # Combine response text
        response_text = "".join(response_text_parts)
        
        # Estimate token counts (Groq streaming doesn't provide usage in chunks)
        input_tokens = len(prompt.split()) // 0.75  # Rough estimate: 1 token ≈ 0.75 words
        output_tokens = total_output_tokens
        
        # Calculate cost
        pricing = PRICING.get(model, PRICING["llama-3.1-8b-instant"])
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
        
    except Exception as e:
        # If there is an error, calculate latency and return error result
        end_time = time.time()
        total_latency_ms = (end_time - start_time) * 1000
        
        # Try to extract status code from error if available
        status_code = 500  # Default error code
        if hasattr(e, 'status_code'):
            status_code = e.status_code
        elif hasattr(e, 'response') and hasattr(e.response, 'status_code'):
            status_code = e.response.status_code
        
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
            "error_message": str(e),
            "response_text": None
        }

