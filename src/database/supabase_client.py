import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime

# Get variables from env
load_dotenv()

# Get Supabase credentials from .env
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE")

# Check if credentials are in the env file
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE:
    raise Exception("Missing Supabase credentials in .env")

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
            - provider: Name of the provider (e.g. "openai")
            - model: Name of the model (e.g. "gpt-4o-mini")
            - input_tokens: Number of input tokens
            - output_tokens: Number of output tokens
            - latency_ms: Latency in milliseconds
            - cost_usd: Cost in USD
            - success: Whether the benchmark was successful (True/False)
            - error_message: Error message if the benchmark failed
            - response_text: Full response text from the AI
    Returns:
        Response from Supabase, or None if the save failed
    """
    try:
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
