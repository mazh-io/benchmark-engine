"""
Local PostgreSQL Database Client

Alternative to supabase_client.py for local development/testing.
Connects directly to PostgreSQL database using psycopg2.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from utils.env_helper import get_env


class LocalDBClient:
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
        
        Args:
            run_id: UUID of the run
            status: Ignored (kept for backward compatibility)
            
        Returns:
            True if successful
        """
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
    
    def get_or_create_provider(self, provider_name: str) -> Optional[str]:
        """
        Get or create provider.
        
        Args:
            provider_name: Name of provider
            
        Returns:
            UUID of provider
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Try to get existing
            cur.execute("SELECT id FROM providers WHERE name = %s", (provider_name,))
            result = cur.fetchone()
            
            if result:
                provider_id = str(result['id'])
            else:
                # Create new
                cur.execute(
                    "INSERT INTO providers (name) VALUES (%s) RETURNING id",
                    (provider_name,)
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
    
    def get_or_create_model(self, model_name: str, provider_id: str) -> Optional[str]:
        """
        Get or create model.
        
        Args:
            model_name: Name of model
            provider_id: UUID of provider
            
        Returns:
            UUID of model
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Try to get existing
            cur.execute(
                "SELECT id FROM models WHERE name = %s AND provider_id = %s",
                (model_name, provider_id)
            )
            result = cur.fetchone()
            
            if result:
                model_id = str(result['id'])
            else:
                # Create new
                cur.execute(
                    "INSERT INTO models (name, provider_id) VALUES (%s, %s) RETURNING id",
                    (model_name, provider_id)
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
    
    def save_result(self, **data) -> Optional[str]:
        """
        Save benchmark result.
        
        Args:
            **data: Result data dictionary
            
        Returns:
            UUID of created result
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                INSERT INTO benchmark_results (
                    run_id, provider_id, model_id, provider, model,
                    input_tokens, output_tokens, total_latency_ms, ttft_ms, tps,
                    cost_usd, status_code, success, response_text
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
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
                data.get('total_latency_ms'),
                data.get('ttft_ms'),
                data.get('tps'),
                data.get('cost_usd'),
                data.get('status_code'),
                data.get('success'),
                data.get('response_text')
            )
            
            cur.execute(query, values)
            result = cur.fetchone()
            result_id = str(result['id'])
            
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


# Singleton instance
_local_db_client = None

def get_local_db_client() -> LocalDBClient:
    """Get or create local DB client instance."""
    global _local_db_client
    if _local_db_client is None:
        _local_db_client = LocalDBClient()
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

