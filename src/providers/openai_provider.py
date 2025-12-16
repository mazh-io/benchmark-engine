import os
import time
import uuid
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()



PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
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
    api_key = os.getenv("OPENAI_API_KEY")
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
    
    try:
        # Send request to OpenAI API
        response = client.chat.completions.create(
            model=model,
            messages=[
                # System prompt: instruct the AI to summarize the provided text into exactly three concise bullet points
                {"role": "system", "content": "You are a helpful assistant. Your task is to summarize the provided text into exactly three concise bullet points."},
                # User prompt: add UUID for tracking + actual prompt
                {"role": "user", "content": f"REQUEST ID: {request_id}\n\n{prompt}"}
            ],
            temperature=0.8,  # Higher temperature for more variation in the response
            top_p=0.9,        # Nucleus sampling for diversity in the response
            user=request_id   # OpenAI user parameter for tracking in the dashboard
        )
        
        # Calculate latency in milliseconds
        latency_ms = (time.time() - start_time) * 1000
        
        # Get information from response for input and output tokens
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        response_text = response.choices[0].message.content
        
        # Calculate cost based on the model's pricing
        pricing = PRICING.get(model, PRICING["gpt-4o-mini"])
        cost_usd = (input_tokens / 1_000_000 * pricing["input"]) + (output_tokens / 1_000_000 * pricing["output"])
        
        # Return the result with all the request data
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
        # If there is an error, calculate latency and return error result with all the request data
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

