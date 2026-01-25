"""
Supabase Database Client

Implements BaseDatabaseClient interface for Supabase backend.
Wraps all Supabase database operations in a class-based interface.
"""

from supabase import create_client, Client
from datetime import datetime
from typing import Optional, Dict, Any, List
from database.base_db_client import BaseDatabaseClient
from utils.env_helper import get_env


class SupabaseDatabaseClient(BaseDatabaseClient):
    """Supabase implementation of database client."""
    
    def __init__(self):
        """Initialize Supabase client from environment variables."""
        # Get Supabase credentials from environment
        supabase_url = get_env("SUPABASE_URL")
        supabase_key = get_env("SUPABASE_SERVICE_ROLE")
        
        if not supabase_url or not supabase_key:
            raise Exception(
                f"Missing Supabase credentials. "
                f"SUPABASE_URL={supabase_url is not None}, "
                f"SUPABASE_SERVICE_ROLE={supabase_key is not None}"
            )
        
        # Create Supabase client
        self.supabase: Client = create_client(supabase_url, supabase_key)
    
    # ============================================================================
    # RUN MANAGEMENT
    # ============================================================================
    
    def create_run(self, run_name: str, triggered_by: str) -> Optional[str]:
        """Create a new run in the runs table."""
        try:
            response = self.supabase.table("runs").insert({
                "run_name": run_name,
                "triggered_by": triggered_by
            }).execute()
            return response.data[0]["id"]
        except Exception as e:
            print("DB Error (create_run):", e)
            return None
    
    def finish_run(self, run_id: str) -> bool:
        """Mark run as finished by setting finished_at timestamp."""
        try:
            self.supabase.table("runs").update({
                "finished_at": datetime.utcnow().isoformat()
            }).eq("id", run_id).execute()
            return True
        except Exception as e:
            print("DB Error (finish_run):", e)
            return False
    
    def get_all_runs(self) -> Optional[List[Dict[str, Any]]]:
        """Get all runs from the runs table."""
        try:
            response = self.supabase.table("runs").select("*").execute()
            return response.data
        except Exception as e:
            print("DB Error (get_all_runs):", e)
            return None
    
    # ============================================================================
    # BENCHMARK RESULTS
    # ============================================================================
    
    def save_benchmark(self, **data) -> Optional[str]:
        """Save benchmark result."""
        try:
            # Remove latency_ms if present (we only use total_latency_ms)
            if "latency_ms" in data:
                del data["latency_ms"]
            
            # Ensure total_latency_ms exists
            if "total_latency_ms" not in data:
                print("Warning: total_latency_ms not provided")
                return None
            
            # Validate and correct token counts
            validation = validate_token_counts(
                input_tokens=data.get("input_tokens"),
                output_tokens=data.get("output_tokens"),
                prompt=None,  # We don't store prompt, can't estimate without it
                response=data.get("response_text")
            )
            
            # Update token counts with validated/estimated values
            data["input_tokens"] = validation["input_tokens"]
            data["output_tokens"] = validation["output_tokens"]
            
            # Mark benchmark as failed if token counts are suspicious
            if should_fail_benchmark(validation):
                data["success"] = False
                error_msg = f"Token validation failed: {get_validation_summary(validation)}"
                data["error_message"] = error_msg
                print(f"⚠️  {error_msg}")
            elif not validation["is_valid"]:
                # Log warning but don't fail the benchmark
                print(f"⚠️  Token count warning: {get_validation_summary(validation)}")
            
            # Optimize storage: truncate response_text for successful runs
            if "response_text" in data and data.get("response_text"):
                success = data.get("success", True)
                data["response_text"] = truncate_response_text(
                    data["response_text"],
                    success=success,
                    max_length=100
                )
            
            response = self.supabase.table("benchmark_results").insert(data).execute()
            return response.data[0]["id"]
        except Exception as e:
            print("DB Error (save_benchmark):", e)
            return None
    
    def get_all_benchmark_results(self) -> Optional[List[Dict[str, Any]]]:
        """Get all benchmark results."""
        try:
            response = self.supabase.table("benchmark_results").select("*").execute()
            return response.data
        except Exception as e:
            print("DB Error (get_all_benchmark_results):", e)
            return None
    
    def get_benchmark_results_by_run_id(self, run_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get benchmark results for a specific run."""
        try:
            response = self.supabase.table("benchmark_results").select("*").eq("run_id", run_id).execute()
            return response.data
        except Exception as e:
            print("DB Error (get_benchmark_results_by_run_id):", e)
            return None
    
    def save_run_error(self, **data) -> Optional[str]:
        """Save run error."""
        try:
            # Ensure required fields are present
            if 'run_id' not in data or 'error_type' not in data or 'error_message' not in data:
                print(f"DB Error (save_run_error): Missing required fields. Data: {data}")
                return None
            
            response = self.supabase.table("run_errors").insert(data).execute()
            if response.data:
                return response.data[0]["id"]
            else:
                print(f"DB Error (save_run_error): No data returned from insert")
                return None
        except Exception as e:
            print(f"DB Error (save_run_error): {e}")
            print(f"Data attempted: {data}")
            import traceback
            traceback.print_exc()
            return None
    
    # ============================================================================
    # PROVIDERS & MODELS
    # ============================================================================
    
    def get_or_create_provider(self, name: str, base_url: str = None, logo_url: str = None) -> Optional[str]:
        """Get existing provider or create new one."""
        try:
            # Try to get existing provider
            response = self.supabase.table("providers").select("id").eq("name", name).execute()
            
            if response.data:
                return response.data[0]["id"]
            
            # Create new provider if it doesn't exist
            response = self.supabase.table("providers").insert({
                "name": name,
                "base_url": base_url,
                "logo_url": logo_url
            }).execute()
            
            return response.data[0]["id"]
        except Exception as e:
            print("DB Error (get_or_create_provider):", e)
            return None
    
    def get_all_providers(self) -> Optional[List[Dict[str, Any]]]:
        """Get all providers."""
        try:
            response = self.supabase.table("providers").select("*").execute()
            return response.data
        except Exception as e:
            print("DB Error (get_all_providers):", e)
            return None
    
    def get_or_create_model(self, model_name: str, provider_id: str, context_window: int = None) -> Optional[str]:
        """Get existing model or create new one."""
        try:
            # Normalize model name before saving/querying
            normalized_name = normalize_model_name(model_name)
            
            # Try to get existing model
            response = self.supabase.table("models").select("id").eq("name", normalized_name).eq("provider_id", provider_id).execute()
            
            if response.data:
                return response.data[0]["id"]
            
            # Create new model if it doesn't exist
            response = self.supabase.table("models").insert({
                "name": normalized_name,
                "provider_id": provider_id,
                "context_window": context_window
            }).execute()
            
            return response.data[0]["id"]
        except Exception as e:
            print("DB Error (get_or_create_model):", e)
            return None
    
    def get_all_models(self) -> Optional[List[Dict[str, Any]]]:
        """Get all models."""
        try:
            response = self.supabase.table("models").select("*").execute()
            return response.data
        except Exception as e:
            print("DB Error (get_all_models):", e)
            return None    
    def upsert_models_from_discovery(self, provider_name: str, model_names: List[str]) -> bool:
        """Upsert models discovered from provider API."""
        try:
            # Get provider ID
            provider = self.get_or_create_provider(provider_name)
            if not provider:
                print(f"DB Error: Provider '{provider_name}' not found")
                return False
            
            provider_id = provider["id"]
            now = datetime.now().isoformat()
            
            # Prepare upsert data
            models_data = []
            for model_name in model_names:
                models_data.append({
                    "name": model_name,
                    "provider_id": provider_id,
                    "active": False,  # New discoveries default to inactive
                    "last_seen_at": now
                })
            
            # Upsert models (on conflict, only update last_seen_at)
            for model_data in models_data:
                # Check if exists
                existing = self.supabase.table("models").select("id").eq(
                    "name", model_data["name"]
                ).eq("provider_id", provider_id).execute()
                
                if existing.data:
                    # Update last_seen_at
                    self.supabase.table("models").update({
                        "last_seen_at": now
                    }).eq("id", existing.data[0]["id"]).execute()
                else:
                    # Insert new
                    self.supabase.table("models").insert(model_data).execute()
            
            return True
        except Exception as e:
            print(f"DB Error (upsert_models_from_discovery): {e}")
            return False
    
    def set_models_active(self, provider_name: str, model_names: List[str]) -> bool:
        """Mark specific models as active."""
        try:
            # Get provider ID
            provider = self.get_or_create_provider(provider_name)
            if not provider:
                print(f"DB Error: Provider '{provider_name}' not found")
                return False
            
            provider_id = provider["id"]
            
            # First, set all models for this provider to inactive
            self.supabase.table("models").update({
                "active": False
            }).eq("provider_id", provider_id).execute()
            
            # Then set specified models to active
            for model_name in model_names:
                self.supabase.table("models").update({
                    "active": True
                }).eq("name", model_name).eq("provider_id", provider_id).execute()
            
            return True
        except Exception as e:
            print(f"DB Error (set_models_active): {e}")
            return False
    
    def get_active_models(self) -> Optional[List[Dict[str, Any]]]:
        """Get all active models."""
        try:
            response = self.supabase.table("models").select(
                "*, providers(name)"
            ).eq("active", True).execute()
            return response.data
        except Exception as e:
            print(f"DB Error (get_active_models): {e}")
            return None    
    # ============================================================================
    # PRICING
    # ============================================================================
    
    def save_price(self, provider_id: str, model_id: str, input_price: float, output_price: float) -> Optional[str]:
        """Save pricing data for a model."""
        try:
            response = self.supabase.table("prices").insert({
                "provider_id": provider_id,
                "model_id": model_id,
                "input_price_per_m": input_price,
                "output_price_per_m": output_price
            }).execute()
            
            return response.data[0]["id"]
        except Exception as e:
            print("DB Error (save_price):", e)
            return None
    
    def get_last_price_timestamp(self, provider_id: str, model_id: str) -> Optional[str]:
        """Get timestamp of last price update for a model."""
        try:
            response = self.supabase.table("prices").select("timestamp").eq(
                "provider_id", provider_id
            ).eq("model_id", model_id).order("timestamp", desc=True).limit(1).execute()
            
            if response.data:
                return response.data[0]["timestamp"]
            return None
        except Exception as e:
            print("DB Error (get_last_price_timestamp):", e)
            return None
    
    def get_model_pricing(self, provider_name: str, model_name: str) -> Optional[Dict[str, float]]:
        """Get current pricing for a model."""
        try:
            # Get provider ID
            provider_response = self.supabase.table("providers").select("id").eq("name", provider_name).execute()
            if not provider_response.data:
                return None
            provider_id = provider_response.data[0]["id"]
            
            # Get model ID
            model_response = self.supabase.table("models").select("id").eq("name", model_name).eq("provider_id", provider_id).execute()
            if not model_response.data:
                return None
            model_id = model_response.data[0]["id"]
            
            # Get latest pricing
            price_response = self.supabase.table("prices").select(
                "input_price_per_m, output_price_per_m"
            ).eq("provider_id", provider_id).eq("model_id", model_id).order("timestamp", desc=True).limit(1).execute()
            
            if price_response.data:
                price = price_response.data[0]
                return {
                    "input": price["input_price_per_m"],
                    "output": price["output_price_per_m"]
                }
            return None
        except Exception as e:
            print(f"DB Error (get_model_pricing): {e}")
            return None
    
    # ============================================================================
    # BENCHMARK QUEUE
    # ============================================================================
    
    def enqueue_benchmarks(self, run_id: str, provider_models: List[tuple]) -> bool:
        """Add provider/model combinations to the benchmark queue."""
        try:
            queue_items = [
                {
                    "run_id": run_id,
                    "provider_key": provider_key,
                    "model_name": model_name,
                    "status": "pending"
                }
                for provider_key, model_name in provider_models
            ]
            self.supabase.table("benchmark_queue").insert(queue_items).execute()
            return True
        except Exception as e:
            print(f"DB Error (enqueue_benchmarks): {e}")
            return False
    
    def get_pending_queue_items(self, limit: int = 5) -> Optional[List[Dict[str, Any]]]:
        """Get pending items from the queue."""
        try:
            response = self.supabase.table("benchmark_queue").select(
                "*"
            ).eq("status", "pending").order("created_at").limit(limit).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"DB Error (get_pending_queue_items): {e}")
            return None
    
    def mark_queue_item_processing(self, queue_id: str) -> bool:
        """Mark a queue item as being processed."""
        try:
            self.supabase.table("benchmark_queue").update({
                "status": "processing",
                "started_at": datetime.utcnow().isoformat(),
                "attempts": self.supabase.table("benchmark_queue").select("attempts").eq("id", queue_id).execute().data[0]["attempts"] + 1
            }).eq("id", queue_id).execute()
            return True
        except Exception as e:
            print(f"DB Error (mark_queue_item_processing): {e}")
            return False
    
    def mark_queue_item_completed(self, queue_id: str) -> bool:
        """Mark a queue item as completed."""
        try:
            self.supabase.table("benchmark_queue").update({
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat()
            }).eq("id", queue_id).execute()
            return True
        except Exception as e:
            print(f"DB Error (mark_queue_item_completed): {e}")
            return False
    
    def mark_queue_item_failed(self, queue_id: str, error_message: str) -> bool:
        """Mark a queue item as failed and increment attempts."""
        try:
            # First get current attempts count
            current = self.supabase.table("benchmark_queue").select("attempts, max_attempts").eq("id", queue_id).execute()
            if not current.data:
                return False
            
            attempts = current.data[0]["attempts"] + 1
            max_attempts = current.data[0]["max_attempts"]
            
            # Update status to failed only if max attempts reached, otherwise back to pending
            status = "failed" if attempts >= max_attempts else "pending"
            
            self.supabase.table("benchmark_queue").update({
                "status": status,
                "attempts": attempts,
                "error_message": error_message,
                "completed_at": datetime.utcnow().isoformat() if status == "failed" else None
            }).eq("id", queue_id).execute()
            return True
        except Exception as e:
            print(f"DB Error (mark_queue_item_failed): {e}")
            return False
    
    def get_queue_stats(self, run_id: str) -> Optional[Dict[str, int]]:
        """Get statistics for a run's queue."""
        try:
            response = self.supabase.table("benchmark_queue").select("status").eq("run_id", run_id).execute()
            if not response.data:
                return {"pending": 0, "processing": 0, "completed": 0, "failed": 0}
            
            stats = {"pending": 0, "processing": 0, "completed": 0, "failed": 0}
            for item in response.data:
                status = item["status"]
                if status in stats:
                    stats[status] += 1
            
            return stats
        except Exception as e:
            print(f"DB Error (get_queue_stats): {e}")
            return None


# ============================================================================
# BACKWARD COMPATIBILITY - Module-level functions
# ============================================================================
# These functions maintain backward compatibility with existing code that imports
# functions directly from this module. They create a singleton instance and
# delegate to its methods.

_default_client: Optional[SupabaseDatabaseClient] = None


def _get_default_client() -> SupabaseDatabaseClient:
    """Get or create default Supabase client instance."""
    global _default_client
    if _default_client is None:
        _default_client = SupabaseDatabaseClient()
    return _default_client


# Run management functions
def create_run(run_name: str, triggered_by: str):
    return _get_default_client().create_run(run_name, triggered_by)


def finish_run(run_id: str):
    return _get_default_client().finish_run(run_id)


def get_all_runs():
    return _get_default_client().get_all_runs()


# Benchmark functions
def save_benchmark(**data):
    return _get_default_client().save_benchmark(**data)


def get_all_benchmark_results():
    return _get_default_client().get_all_benchmark_results()


def get_benchmark_results_by_run_id(run_id: str):
    return _get_default_client().get_benchmark_results_by_run_id(run_id)


# Provider functions
def get_or_create_provider(name: str, base_url: str = None, logo_url: str = None):
    return _get_default_client().get_or_create_provider(name, base_url, logo_url)


def get_all_providers():
    return _get_default_client().get_all_providers()


# Model functions
def get_or_create_model(name: str, provider_id: str, context_window: int = None):
    return _get_default_client().get_or_create_model(name, provider_id, context_window)


def get_all_models():
    return _get_default_client().get_all_models()


# Pricing functions
def save_price(provider_id: str, model_id: str, input_price_per_m: float, output_price_per_m: float):
    return _get_default_client().save_price(provider_id, model_id, input_price_per_m, output_price_per_m)


def get_last_price_timestamp(provider_id: str, model_id: str):
    return _get_default_client().get_last_price_timestamp(provider_id, model_id)


def get_model_pricing(provider_name: str, model_name: str):
    return _get_default_client().get_model_pricing(provider_name, model_name)
