import time
import uuid
from openai import OpenAI
from utils.env_helper import get_env



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
    
    # Create OpenAI client to interact with the API
    client = OpenAI(api_key=api_key)
    
    # Generate unique UUID for this request (for tracking)
    request_id = str(uuid.uuid4())
    
    # Start time for latency calculation
    start_time = time.time()
    first_token_time = None
    status_code = 200
    
    try:
        # O-series models (reasoning models) only support temperature=1 and no top_p
        # Check if this is an O-series model (o1, o3, o4-mini, etc.)
        is_reasoning_model = model.startswith('o') and any(c.isdigit() for c in model)
        
        # Build request parameters based on model type
        request_params = {
            "model": model,
            "messages": [
                # System prompt: instruct the AI to summarize the provided text into exactly three concise bullet points
                {"role": "system", "content": "You are a helpful assistant. Your task is to summarize the provided text into exactly three concise bullet points."},
                # User prompt: add UUID for tracking + actual prompt
                {"role": "user", "content": f"REQUEST ID: {request_id}\n\n{prompt}"}
            ],
            "user": request_id,
            "stream": True
        }
        
        # O-series models: only temperature=1, no top_p
        # Regular models: temperature=0.8, top_p=0.9
        if is_reasoning_model:
            request_params["temperature"] = 1.0
        else:
            request_params["temperature"] = 0.8
            request_params["top_p"] = 0.9
        
        # Send streaming request to OpenAI API for TTFT measurement
        stream = client.chat.completions.create(**request_params)
        
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
        
        # Get actual token counts from final chunk (if available) or use estimates
        # Note: OpenAI streaming doesn't provide usage in chunks, so we estimate
        # For accurate counts, we'd need to make a separate non-streaming call or use the final chunk
        # For now, we'll use the estimated output tokens and estimate input tokens
        input_tokens = len(prompt.split()) // 0.75  # Rough estimate: 1 token ≈ 0.75 words
        output_tokens = total_output_tokens
        
        # Make a non-streaming call to get accurate token counts (optional, adds latency)
        # For MVP, we'll use estimates above
        
        # Calculate cost based on the model's pricing
        pricing = PRICING.get(model, PRICING["gpt-4o-mini"])
        cost_usd = (input_tokens / 1_000_000 * pricing["input"]) + (output_tokens / 1_000_000 * pricing["output"])
        
        # Return the result with all the request data
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
        # If there is an error, calculate latency and return error result with all the request data
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

