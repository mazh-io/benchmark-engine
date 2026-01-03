from supabase import create_client, Client
from datetime import datetime
from utils.env_helper import get_env

# Get Supabase credentials from environment
SUPABASE_URL = get_env("SUPABASE_URL")
SUPABASE_SERVICE_ROLE = get_env("SUPABASE_SERVICE_ROLE")

# Check if credentials are available
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE:
    raise Exception(f"Missing Supabase credentials. SUPABASE_URL={SUPABASE_URL is not None}, SUPABASE_SERVICE_ROLE={SUPABASE_SERVICE_ROLE is not None}")

# Create Supabase client to interact with the database
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)


def create_run(run_name: str, triggered_by: str):
    """
    Create a new run in the runs table.
    
    Args:
        run_name: Name of the run (e.g. "mvp-validation-run")
        triggered_by: Who triggered the run (e.g. "system", "user")
    
    Returns:
        UUID of the created run, or None if the creation failed
    """
    try:
        # Insert a new row into the runs table
        # PostgreSQL will automatically generate a UUID for id and a timestamp for started_at
        response = supabase.table("runs").insert({
            "run_name": run_name,
            "triggered_by": triggered_by
        }).execute()
        
        # Return the UUID of the created run
        return response.data[0]["id"] 
    except Exception as e:
        print("DB Error (create_run):", e)
        return None


def finish_run(run_id: str):
    """
    End the run by setting the finished_at timestamp.
    
    Args:
        run_id: UUID of the run to end
    """
    try:
        # Update the run by setting the finished_at timestamp to the current timestamp
        supabase.table("runs").update({
            "finished_at": datetime.utcnow().isoformat()
        }).eq("id", run_id).execute()
    except Exception as e:
        print("DB Error (finish_run):", e)


def save_benchmark(**data):
    """
    Save the results of a benchmark to the benchmark_results table.
    
    Args:
        **data: Dictionary with all the benchmark data:
            - run_id: UUID of the run (foreign key to runs table)
            - provider_id: UUID of the provider (optional, foreign key)
            - model_id: UUID of the model (optional, foreign key)
            - provider: Name of the provider (e.g. "openai") - for backward compatibility
            - model: Name of the model (e.g. "gpt-4o-mini") - for backward compatibility
            - input_tokens: Number of input tokens
            - output_tokens: Number of output tokens
            - total_latency_ms: Total latency in milliseconds (or latency_ms for backward compatibility)
            - ttft_ms: Time to First Token in milliseconds (optional)
            - tps: Tokens Per Second (optional)
            - status_code: HTTP status code (200, 500, 429, etc.) (optional)
            - cost_usd: Cost in USD
            - success: Whether the benchmark was successful (True/False)
            - error_message: Error message if the benchmark failed
            - response_text: Full response text from the AI
    Returns:
        Response from Supabase, or None if the save failed
    """
    try:
        # Remove latency_ms if present (we only use total_latency_ms)
        if "latency_ms" in data:
            del data["latency_ms"]
        
        # Ensure total_latency_ms exists
        if "total_latency_ms" not in data:
            print("Warning: total_latency_ms not provided")
            return None
        
        # Insert a new row into the benchmark_results table
        # PostgreSQL will automatically generate a UUID for id and a timestamp for created_at
        response = supabase.table("benchmark_results").insert(data).execute()
        # Return the UUID of the created benchmark
        return response.data[0]["id"]
    except Exception as e:
        print("DB Error (save_benchmark):", e)
        return None


def get_all_runs():
    """
    Get all runs from the runs table.
    
    Returns:
        List of all runs, or None if query failed
    """
    try:
        response = supabase.table("runs").select("*").execute()
        return response.data
    except Exception as e:
        print("DB Error (get_all_runs):", e)
        return None


def get_all_benchmark_results():
    """
    Get all benchmark results from the benchmark_results table.
    
    Returns:
        List of all benchmark results, or None if query failed
    """
    try:
        response = supabase.table("benchmark_results").select("*").execute()
        return response.data
    except Exception as e:
        print("DB Error (get_all_benchmark_results):", e)
        return None


def get_benchmark_results_by_run_id(run_id: str):
    """
    Get all benchmark results for a specific run.
    
    Args:
        run_id: UUID of the run
    
    Returns:
        List of benchmark results for that run, or None if query failed
    """
    try:
        response = supabase.table("benchmark_results").select("*").eq("run_id", run_id).execute()
        return response.data
    except Exception as e:
        print("DB Error (get_benchmark_results_by_run_id):", e)
        return None


# ============================================================================
# PROVIDERS FUNCTIONS
# ============================================================================

def get_or_create_provider(name: str, base_url: str = None, logo_url: str = None):
    """
    Get existing provider or create a new one if it doesn't exist.
    
    Args:
        name: Name of the provider (e.g. "OpenAI", "Groq")
        base_url: Base URL of the provider API (optional)
        logo_url: URL to provider logo (optional)
    
    Returns:
        UUID of the provider, or None if creation failed
    """
    try:
        # Try to get existing provider
        response = supabase.table("providers").select("id").eq("name", name).execute()
        
        if response.data:
            return response.data[0]["id"]
        
        # Create new provider if it doesn't exist
        response = supabase.table("providers").insert({
            "name": name,
            "base_url": base_url,
            "logo_url": logo_url
        }).execute()
        
        return response.data[0]["id"]
    except Exception as e:
        print("DB Error (get_or_create_provider):", e)
        return None


def get_all_providers():
    """
    Get all providers from the providers table.
    
    Returns:
        List of all providers, or None if query failed
    """
    try:
        response = supabase.table("providers").select("*").execute()
        return response.data
    except Exception as e:
        print("DB Error (get_all_providers):", e)
        return None


# ============================================================================
# MODELS FUNCTIONS
# ============================================================================

def get_or_create_model(name: str, provider_id: str, context_window: int = None):
    """
    Get existing model or create a new one if it doesn't exist.
    
    Args:
        name: Name of the model (e.g. "gpt-4o-mini", "llama-3-70b-instruct")
        provider_id: UUID of the provider (foreign key)
        context_window: Context window size in tokens (optional)
    
    Returns:
        UUID of the model, or None if creation failed
    """
    try:
        # Try to get existing model
        response = supabase.table("models").select("id").eq("name", name).eq("provider_id", provider_id).execute()
        
        if response.data:
            return response.data[0]["id"]
        
        # Create new model if it doesn't exist
        response = supabase.table("models").insert({
            "name": name,
            "provider_id": provider_id,
            "context_window": context_window
        }).execute()
        
        return response.data[0]["id"]
    except Exception as e:
        print("DB Error (get_or_create_model):", e)
        return None


def get_all_models():
    """
    Get all models from the models table.
    
    Returns:
        List of all models, or None if query failed
    """
    try:
        response = supabase.table("models").select("*").execute()
        return response.data
    except Exception as e:
        print("DB Error (get_all_models):", e)
        return None


# ============================================================================
# PRICES FUNCTIONS
# ============================================================================

def save_price(provider_id: str, model_id: str, input_price_per_m: float, output_price_per_m: float):
    """
    Save pricing data to the prices table (history table).
    
    Args:
        provider_id: UUID of the provider
        model_id: UUID of the model
        input_price_per_m: Input price per 1M tokens
        output_price_per_m: Output price per 1M tokens
    
    Returns:
        UUID of the created price record, or None if save failed
    """
    try:
        response = supabase.table("prices").insert({
            "provider_id": provider_id,
            "model_id": model_id,
            "input_price_per_m": input_price_per_m,
            "output_price_per_m": output_price_per_m
        }).execute()
        
        return response.data[0]["id"]
    except Exception as e:
        print("DB Error (save_price):", e)
        return None


def get_latest_prices(provider_id: str = None, model_id: str = None):
    """
    Get latest pricing data from the prices table.
    
    Args:
        provider_id: Optional filter by provider UUID
        model_id: Optional filter by model UUID
    
    Returns:
        List of latest prices, or None if query failed
    """
    try:
        query = supabase.table("prices").select("*")
        
        if provider_id:
            query = query.eq("provider_id", provider_id)
        if model_id:
            query = query.eq("model_id", model_id)
        
        # Order by timestamp descending and get latest
        response = query.order("timestamp", desc=True).execute()
        return response.data
    except Exception as e:
        print("DB Error (get_latest_prices):", e)
        return None


def get_last_price_timestamp(provider_id: str, model_id: str):
    """
    Get the timestamp of the last price record for a specific provider/model.
    
    Args:
        provider_id: UUID of the provider
        model_id: UUID of the model
    
    Returns:
        Timestamp of the last price record, or None if no record exists
    """
    try:
        response = supabase.table("prices").select("timestamp").eq("provider_id", provider_id).eq("model_id", model_id).order("timestamp", desc=True).limit(1).execute()
        
        if response.data:
            return response.data[0]["timestamp"]
        return None
    except Exception as e:
        print("DB Error (get_last_price_timestamp):", e)
        return None


# ============================================================================
# RUN ERRORS FUNCTIONS
# ============================================================================

def save_run_error(run_id: str, provider: str, model: str, error_type: str, error_message: str, 
                   status_code: int = None, provider_id: str = None, model_id: str = None):
    """
    Save an error that occurred during a benchmark run.
    
    This function logs errors to the run_errors table so we can track provider reliability
    and ensure that one failing provider doesn't crash the entire benchmark.
    
    Args:
        run_id: UUID of the run (foreign key to runs table)
        provider: Name of the provider (e.g. "openai", "anthropic")
        model: Name of the model (e.g. "gpt-4o-mini")
        error_type: Type of error (e.g. "RATE_LIMIT", "AUTH_ERROR", "TIMEOUT", "UNKNOWN_ERROR")
        error_message: Detailed error message
        status_code: HTTP status code if available (optional)
        provider_id: UUID of the provider (optional, foreign key)
        model_id: UUID of the model (optional, foreign key)
    
    Returns:
        UUID of the created error record, or None if save failed
    """
    try:
        error_data = {
            "run_id": run_id,
            "provider": provider,
            "model": model,
            "error_type": error_type,
            "error_message": error_message
        }
        
        # Add optional fields if provided
        if status_code is not None:
            error_data["status_code"] = status_code
        if provider_id is not None:
            error_data["provider_id"] = provider_id
        if model_id is not None:
            error_data["model_id"] = model_id
        
        response = supabase.table("run_errors").insert(error_data).execute()
        return response.data[0]["id"]
    except Exception as e:
        print("DB Error (save_run_error):", e)
        return None


def get_run_errors(run_id: str = None, provider: str = None, error_type: str = None):
    """
    Get errors from the run_errors table with optional filters.
    
    Args:
        run_id: Optional filter by run UUID
        provider: Optional filter by provider name
        error_type: Optional filter by error type
    
    Returns:
        List of errors, or None if query failed
    """
    try:
        query = supabase.table("run_errors").select("*")
        
        if run_id:
            query = query.eq("run_id", run_id)
        if provider:
            query = query.eq("provider", provider)
        if error_type:
            query = query.eq("error_type", error_type)
        
        # Order by timestamp descending (most recent first)
        response = query.order("timestamp", desc=True).execute()
        return response.data
    except Exception as e:
        print("DB Error (get_run_errors):", e)
        return None


def get_error_count_by_provider(hours: int = 24):
    """
    Get count of errors grouped by provider for the last N hours.
    
    This is useful for monitoring which providers are having issues.
    
    Args:
        hours: Number of hours to look back (default 24)
    
    Returns:
        List of dicts with provider and error count, or None if query failed
    """
    try:
        # Note: This requires a raw SQL query since Supabase Python client
        # doesn't support GROUP BY directly. For now, we'll return all errors
        # and let the caller group them.
        response = supabase.table("run_errors").select("provider, error_type").gte(
            "timestamp", 
            f"now() - interval '{hours} hours'"
        ).execute()
        
        return response.data
    except Exception as e:
        print("DB Error (get_error_count_by_provider):", e)
        return None
