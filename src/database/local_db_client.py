"""
Local PostgreSQL Database Client

Alternative to supabase_client.py for local development/testing.
Connects directly to PostgreSQL database using psycopg2.
Implements BaseDatabaseClient interface.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from database.base_db_client import BaseDatabaseClient
from utils.env_helper import get_env
from utils.model_name_normalizer import normalize_model_name
from utils.response_optimizer import truncate_response_text
from utils.token_validator import validate_token_counts, should_fail_benchmark, get_validation_summary


class LocalDatabaseClient(BaseDatabaseClient):
    """PostgreSQL client for local database operations."""
    
    def __init__(self):
        """Initialize database connection from environment variables."""
        # Get database credentials from .env
        self.db_config = {
            'host': get_env('LOCAL_DB_HOST', 'localhost'),
            'port': get_env('LOCAL_DB_PORT', '5432'),
            'database': get_env('LOCAL_DB_NAME', 'benchmark_engine_local'),
            'user': get_env('LOCAL_DB_USER', 'postgres'),
            'password': get_env('LOCAL_DB_PASSWORD', 'postgres')
        }
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self):
        """Test database connection."""
        try:
            conn = self._get_connection()
            conn.close()
            print(f"✅ Connected to local PostgreSQL: {self.db_config['database']} @ {self.db_config['host']}")
        except Exception as e:
            raise Exception(f" Failed to connect to local database: {str(e)}")
    
    def _get_connection(self):
        """Get database connection."""
        return psycopg2.connect(**self.db_config)
    
    def create_run(self, run_name: str, triggered_by: str) -> Optional[str]:
        """
        Create a new run in the runs table.
        
        Args:
            run_name: Name of the run
            triggered_by: Who triggered the run
            
        Returns:
            UUID of the created run
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                INSERT INTO runs (run_name, triggered_by)
                VALUES (%s, %s)
                RETURNING id
            """
            
            cur.execute(query, (run_name, triggered_by))
            result = cur.fetchone()
            run_id = str(result['id'])
            
            conn.commit()
            cur.close()
            conn.close()
            
            return run_id
        
        except Exception as e:
            print(f"DB Error (create_run): {e}")
            return None
    
    def update_run_status(self, run_id: str, status: str = None) -> bool:
        """
        Mark run as finished by setting finished_at timestamp.
        Note: Renamed to finish_run in base interface for consistency.
        """
        return self.finish_run(run_id)
    
    def finish_run(self, run_id: str) -> bool:
        """Mark run as finished by setting finished_at timestamp."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            query = """
                UPDATE runs 
                SET finished_at = %s
                WHERE id = %s
            """
            
            cur.execute(query, (datetime.utcnow(), run_id))
            conn.commit()
            cur.close()
            conn.close()
            
            return True
        
        except Exception as e:
            print(f"DB Error (update_run_status): {e}")
            return False
    
    def get_or_create_provider(self, name: str, base_url: str = None, logo_url: str = None) -> Optional[str]:
        """Get or create provider."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Try to get existing
            cur.execute("SELECT id FROM providers WHERE name = %s", (name,))
            result = cur.fetchone()
            
            if result:
                provider_id = str(result['id'])
            else:
                # Create new with optional fields
                if base_url or logo_url:
                    cur.execute(
                        "INSERT INTO providers (name, base_url, logo_url) VALUES (%s, %s, %s) RETURNING id",
                        (name, base_url, logo_url)
                    )
                else:
                    cur.execute(
                        "INSERT INTO providers (name) VALUES (%s) RETURNING id",
                        (name,)
                    )
                result = cur.fetchone()
                provider_id = str(result['id'])
                conn.commit()
            
            cur.close()
            conn.close()
            
            return provider_id
        
        except Exception as e:
            print(f"DB Error (get_or_create_provider): {e}")
            return None
    
    def get_or_create_model(self, model_name: str, provider_id: str, context_window: int = None) -> Optional[str]:
        """Get or create model."""
        try:
            # Normalize model name before saving/querying
            normalized_name = normalize_model_name(model_name)
            
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Try to get existing
            cur.execute(
                "SELECT id FROM models WHERE name = %s AND provider_id = %s",
                (normalized_name, provider_id)
            )
            result = cur.fetchone()
            
            if result:
                model_id = str(result['id'])
            else:
                # Create new with optional context_window
                if context_window is not None:
                    cur.execute(
                        "INSERT INTO models (name, provider_id, context_window) VALUES (%s, %s, %s) RETURNING id",
                        (normalized_name, provider_id, context_window)
                    )
                else:
                    cur.execute(
                        "INSERT INTO models (name, provider_id) VALUES (%s, %s) RETURNING id",
                        (normalized_name, provider_id)
                    )
                result = cur.fetchone()
                model_id = str(result['id'])
                conn.commit()
            
            cur.close()
            conn.close()
            
            return model_id
        
        except Exception as e:
            print(f"DB Error (get_or_create_model): {e}")
            return None
    
    def save_pricing(self, provider_id: str, model_id: str, input_price: float, output_price: float) -> Optional[str]:
        """Save pricing data for a model. Renamed to save_price in base interface."""
        return self.save_price(provider_id, model_id, input_price, output_price)
    
    def save_price(self, provider_id: str, model_id: str, input_price: float, output_price: float) -> Optional[str]:
        """Save pricing data for a model."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                INSERT INTO prices (provider_id, model_id, input_price_per_m, output_price_per_m)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
            """
            
            cur.execute(query, (provider_id, model_id, input_price, output_price))
            result = cur.fetchone()
            
            if result:
                price_id = str(result['id'])
            else:
                price_id = None  # Already exists
            
            conn.commit()
            cur.close()
            conn.close()
            
            return price_id
        
        except Exception as e:
            print(f"DB Error (save_pricing): {e}")
            return None
    
    def save_result(self, **data) -> Optional[str]:
        """
        Save benchmark result.
        
        Args:
            **data: Result data dictionary
            
        Returns:
            UUID of created result
        """
        try:
            # Validate and correct token counts
            validation = validate_token_counts(
                input_tokens=data.get('input_tokens'),
                output_tokens=data.get('output_tokens'),
                prompt=None,  # We don't store prompt, can't estimate without it
                response=data.get('response_text')
            )
            
            # Update token counts with validated/estimated values
            data['input_tokens'] = validation['input_tokens']
            data['output_tokens'] = validation['output_tokens']
            
            # Mark benchmark as failed if token counts are suspicious
            if should_fail_benchmark(validation):
                data['success'] = False
                error_msg = f"Token validation failed: {get_validation_summary(validation)}"
                data['error_message'] = error_msg
                print(f"⚠️  {error_msg}")
            elif not validation['is_valid']:
                # Log warning but don't fail the benchmark
                print(f"⚠️  Token count warning: {get_validation_summary(validation)}")
            
            # Optimize storage: truncate response_text for successful runs
            response_text = data.get('response_text')
            if response_text:
                success = data.get('success', True)
                response_text = truncate_response_text(
                    response_text,
                    success=success,
                    max_length=100
                )
            
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                INSERT INTO benchmark_results (
                    run_id, provider_id, model_id, provider, model,
                    input_tokens, output_tokens, reasoning_tokens, total_latency_ms, ttft_ms, tps,
                    cost_usd, status_code, success, response_text
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
                ) RETURNING id
            """
            
            values = (
                data.get('run_id'),
                data.get('provider_id'),
                data.get('model_id'),
                data.get('provider'),
                data.get('model'),
                data.get('input_tokens'),
                data.get('output_tokens'),
                data.get('reasoning_tokens'),  # Thinking tokens for reasoning models
                data.get('total_latency_ms'),
                data.get('ttft_ms'),
                data.get('tps'),
                data.get('cost_usd'),
                data.get('status_code'),
                data.get('success'),
                response_text
            )
            
            cur.execute(query, values)
            result = cur.fetchone()
            result_id = str(result['id'])
            
            # Save pricing if available
            if data.get('provider_id') and data.get('model_id'):
                if data.get('input_price_per_m') and data.get('output_price_per_m'):
                    self.save_pricing(
                        provider_id=data.get('provider_id'),
                        model_id=data.get('model_id'),
                        input_price=data.get('input_price_per_m'),
                        output_price=data.get('output_price_per_m')
                    )
            
            conn.commit()
            cur.close()
            conn.close()
            
            return result_id
        
        except Exception as e:
            print(f"DB Error (save_result): {e}")
            return None
    
    def save_run_error(self, **data) -> Optional[str]:
        """
        Save run error.
        
        Args:
            **data: Error data dictionary
            
        Returns:
            UUID of created error record
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                INSERT INTO run_errors (
                    run_id, provider_id, model_id, provider, model,
                    error_type, error_message, status_code
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s
                ) RETURNING id
            """
            
            values = (
                data.get('run_id'),
                data.get('provider_id'),
                data.get('model_id'),
                data.get('provider'),
                data.get('model'),
                data.get('error_type'),
                data.get('error_message'),
                data.get('status_code')
            )
            
            cur.execute(query, values)
            result = cur.fetchone()
            error_id = str(result['id'])
            
            conn.commit()
            cur.close()
            conn.close()
            
            return error_id
        
        except Exception as e:
            print(f"DB Error (save_run_error): {e}")
            return None
    
    def get_recent_results(self, limit: int = 10) -> Optional[List[Dict]]:
        """Get recent results."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT * FROM benchmark_results
                ORDER BY created_at DESC
                LIMIT %s
            """
            
            cur.execute(query, (limit,))
            results = cur.fetchall()
            
            cur.close()
            conn.close()
            
            return [dict(r) for r in results]
        
        except Exception as e:
            print(f"DB Error (get_recent_results): {e}")
            return None
    
    # ============================================================================
    # Additional methods to match BaseDatabaseClient interface
    # ============================================================================
    
    def save_benchmark(self, **data) -> Optional[str]:
        """Save benchmark result (alias for save_result)."""
        return self.save_result(**data)
    
    def get_all_runs(self) -> Optional[List[Dict[str, Any]]]:
        """Get all runs."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM runs ORDER BY started_at DESC")
            results = cur.fetchall()
            cur.close()
            conn.close()
            return [dict(r) for r in results]
        except Exception as e:
            print(f"DB Error (get_all_runs): {e}")
            return None
    
    def get_all_benchmark_results(self) -> Optional[List[Dict[str, Any]]]:
        """Get all benchmark results."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM benchmark_results ORDER BY created_at DESC")
            results = cur.fetchall()
            cur.close()
            conn.close()
            return [dict(r) for r in results]
        except Exception as e:
            print(f"DB Error (get_all_benchmark_results): {e}")
            return None
    
    def get_benchmark_results_by_run_id(self, run_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get benchmark results for a specific run."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM benchmark_results WHERE run_id = %s ORDER BY created_at DESC", (run_id,))
            results = cur.fetchall()
            cur.close()
            conn.close()
            return [dict(r) for r in results]
        except Exception as e:
            print(f"DB Error (get_benchmark_results_by_run_id): {e}")
            return None
    
    def get_all_providers(self) -> Optional[List[Dict[str, Any]]]:
        """Get all providers."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM providers ORDER BY name")
            results = cur.fetchall()
            cur.close()
            conn.close()
            return [dict(r) for r in results]
        except Exception as e:
            print(f"DB Error (get_all_providers): {e}")
            return None
    
    def get_all_models(self) -> Optional[List[Dict[str, Any]]]:
        """Get all models."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM models ORDER BY name")
            results = cur.fetchall()
            cur.close()
            conn.close()
            return [dict(r) for r in results]
        except Exception as e:
            print(f"DB Error (get_all_models): {e}")
            return None
    
    def upsert_models_from_discovery(self, provider_name: str, model_names: List[str]) -> bool:
        """Upsert models discovered from provider API."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get provider ID
            cur.execute("SELECT id FROM providers WHERE name = %s", (provider_name,))
            provider = cur.fetchone()
            
            if not provider:
                print(f"DB Error: Provider '{provider_name}' not found")
                cur.close()
                conn.close()
                return False
            
            provider_id = provider['id']
            now = datetime.now()
            
            # Upsert each model
            for model_name in model_names:
                cur.execute("""
                    INSERT INTO models (name, provider_id, active, last_seen_at)
                    VALUES (%s, %s, false, %s)
                    ON CONFLICT (name, provider_id) 
                    DO UPDATE SET last_seen_at = EXCLUDED.last_seen_at
                """, (model_name, provider_id, now))
            
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"DB Error (upsert_models_from_discovery): {e}")
            return False
    
    def set_models_active(self, provider_name: str, model_names: List[str]) -> bool:
        """Mark specific models as active."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get provider ID
            cur.execute("SELECT id FROM providers WHERE name = %s", (provider_name,))
            provider = cur.fetchone()
            
            if not provider:
                print(f"DB Error: Provider '{provider_name}' not found")
                cur.close()
                conn.close()
                return False
            
            provider_id = provider['id']
            
            # First, set all models for this provider to inactive
            cur.execute(
                "UPDATE models SET active = false WHERE provider_id = %s",
                (provider_id,)
            )
            
            # Then set specified models to active
            for model_name in model_names:
                cur.execute(
                    "UPDATE models SET active = true WHERE name = %s AND provider_id = %s",
                    (model_name, provider_id)
                )
            
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"DB Error (set_models_active): {e}")
            return False
    
    def get_active_models(self) -> Optional[List[Dict[str, Any]]]:
        """Get all active models."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                SELECT m.*, p.name as provider_name
                FROM models m
                JOIN providers p ON m.provider_id = p.id
                WHERE m.active = true
                ORDER BY p.name, m.name
            """)
            
            results = cur.fetchall()
            cur.close()
            conn.close()
            
            return [dict(row) for row in results]
        except Exception as e:
            print(f"DB Error (get_active_models): {e}")
            return None
    
    def get_last_price_timestamp(self, provider_id: str, model_id: str) -> Optional[str]:
        """Get timestamp of last price update for a model."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                "SELECT timestamp FROM prices WHERE provider_id = %s AND model_id = %s ORDER BY timestamp DESC LIMIT 1",
                (provider_id, model_id)
            )
            result = cur.fetchone()
            cur.close()
            conn.close()
            if result:
                return result['timestamp'].isoformat() if hasattr(result['timestamp'], 'isoformat') else str(result['timestamp'])
            return None
        except Exception as e:
            print(f"DB Error (get_last_price_timestamp): {e}")
            return None
    
    def get_model_pricing(self, provider_name: str, model_name: str) -> Optional[Dict[str, float]]:
        """Get current pricing for a model."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get provider ID
            cur.execute("SELECT id FROM providers WHERE name = %s", (provider_name,))
            provider_result = cur.fetchone()
            if not provider_result:
                cur.close()
                conn.close()
                return None
            provider_id = str(provider_result['id'])
            
            # Get model ID
            cur.execute("SELECT id FROM models WHERE name = %s AND provider_id = %s", (model_name, provider_id))
            model_result = cur.fetchone()
            if not model_result:
                cur.close()
                conn.close()
                return None
            model_id = str(model_result['id'])
            
            # Get latest pricing
            cur.execute(
                "SELECT input_price_per_m, output_price_per_m FROM prices WHERE provider_id = %s AND model_id = %s ORDER BY timestamp DESC LIMIT 1",
                (provider_id, model_id)
            )
            price_result = cur.fetchone()
            cur.close()
            conn.close()
            
            if price_result:
                return {
                    "input": float(price_result['input_price_per_m']),
                    "output": float(price_result['output_price_per_m'])
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
            conn = self._get_connection()
            cur = conn.cursor()
            
            for provider_key, model_name in provider_models:
                cur.execute(
                    """
                    INSERT INTO benchmark_queue (run_id, provider_key, model_name, status)
                    VALUES (%s, %s, %s, 'pending')
                    ON CONFLICT (run_id, provider_key, model_name) DO NOTHING
                    """,
                    (run_id, provider_key, model_name)
                )
            
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"DB Error (enqueue_benchmarks): {e}")
            return False
    
    def get_pending_queue_items(self, limit: int = 5) -> Optional[List[Dict[str, Any]]]:
        """Get pending items from the queue."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute(
                """
                SELECT * FROM benchmark_queue 
                WHERE status = 'pending' 
                ORDER BY created_at 
                LIMIT %s
                """,
                (limit,)
            )
            results = cur.fetchall()
            cur.close()
            conn.close()
            
            # Convert to list of dicts with string UUIDs
            return [dict(row) for row in results] if results else []
        except Exception as e:
            print(f"DB Error (get_pending_queue_items): {e}")
            return None
    
    def mark_queue_item_processing(self, queue_id: str) -> bool:
        """Mark a queue item as being processed."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            cur.execute(
                """
                UPDATE benchmark_queue 
                SET status = 'processing',
                    started_at = NOW(),
                    attempts = attempts + 1
                WHERE id = %s
                """,
                (queue_id,)
            )
            
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"DB Error (mark_queue_item_processing): {e}")
            return False
    
    def mark_queue_item_completed(self, queue_id: str) -> bool:
        """Mark a queue item as completed."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            cur.execute(
                """
                UPDATE benchmark_queue 
                SET status = 'completed',
                    completed_at = NOW()
                WHERE id = %s
                """,
                (queue_id,)
            )
            
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"DB Error (mark_queue_item_completed): {e}")
            return False
    
    def mark_queue_item_failed(self, queue_id: str, error_message: str) -> bool:
        """Mark a queue item as failed and increment attempts."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get current attempts and max_attempts
            cur.execute(
                "SELECT attempts, max_attempts FROM benchmark_queue WHERE id = %s",
                (queue_id,)
            )
            result = cur.fetchone()
            if not result:
                cur.close()
                conn.close()
                return False
            
            attempts = result['attempts'] + 1
            max_attempts = result['max_attempts']
            
            # Update status to failed only if max attempts reached, otherwise back to pending
            status = 'failed' if attempts >= max_attempts else 'pending'
            completed_at = 'NOW()' if status == 'failed' else 'NULL'
            
            cur.execute(
                f"""
                UPDATE benchmark_queue 
                SET status = %s,
                    attempts = %s,
                    error_message = %s,
                    completed_at = {completed_at}
                WHERE id = %s
                """,
                (status, attempts, error_message, queue_id)
            )
            
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"DB Error (mark_queue_item_failed): {e}")
            return False
    
    def get_queue_stats(self, run_id: str) -> Optional[Dict[str, int]]:
        """Get statistics for a run's queue."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute(
                """
                SELECT status, COUNT(*) as count 
                FROM benchmark_queue 
                WHERE run_id = %s 
                GROUP BY status
                """,
                (run_id,)
            )
            results = cur.fetchall()
            cur.close()
            conn.close()
            
            stats = {"pending": 0, "processing": 0, "completed": 0, "failed": 0}
            for row in results:
                status = row['status']
                if status in stats:
                    stats[status] = int(row['count'])
            
            return stats
        except Exception as e:
            print(f"DB Error (get_queue_stats): {e}")
            return None



# Singleton instance
_local_db_client = None

def get_local_db_client() -> LocalDatabaseClient:
    """Get or create local DB client instance."""
    global _local_db_client
    if _local_db_client is None:
        _local_db_client = LocalDatabaseClient()
    return _local_db_client


# Convenience functions (compatible with supabase_client.py interface)
def create_run(run_name: str, triggered_by: str) -> Optional[str]:
    """Create run."""
    return get_local_db_client().create_run(run_name, triggered_by)

def update_run_status(run_id: str, status: str = None) -> bool:
    """Mark run as finished."""
    return get_local_db_client().update_run_status(run_id, status)

def get_or_create_provider(provider_name: str) -> Optional[str]:
    """Get or create provider."""
    return get_local_db_client().get_or_create_provider(provider_name)

def get_or_create_model(model_name: str, provider_id: str) -> Optional[str]:
    """Get or create model."""
    return get_local_db_client().get_or_create_model(model_name, provider_id)

def save_result(**data) -> Optional[str]:
    """Save result."""
    return get_local_db_client().save_result(**data)

def save_run_error(**data) -> Optional[str]:
    """Save run error."""
    return get_local_db_client().save_run_error(**data)

def get_recent_results(limit: int = 10) -> Optional[List[Dict]]:
    """Get recent results."""
    return get_local_db_client().get_recent_results(limit)

