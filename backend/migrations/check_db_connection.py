"""
Database Connection Check

Quick script to verify which database is configured in .env
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from database.db_connector import get_db_client
from utils.env_helper import get_env


def check_database_config():
    """Check which database is configured."""
    
    print("=" * 80)
    print("DATABASE CONNECTION CHECK")
    print("=" * 80)
    
    # Check environment variables
    print("\n📋 Environment Variables:")
    print("-" * 80)
    
    supabase_url = get_env("SUPABASE_URL")
    supabase_key = get_env("SUPABASE_SERVICE_ROLE")
    pg_host = get_env("PG_HOST")
    pg_database = get_env("PG_DATABASE")
    
    if supabase_url and supabase_key:
        print("✅ SUPABASE_URL found")
        print("✅ SUPABASE_SERVICE_ROLE found")
        print(f"   URL: {supabase_url[:50]}...")
        print("\n🎯 Configured for: SUPABASE")
    else:
        print("❌ SUPABASE_URL not found")
        print("❌ SUPABASE_SERVICE_ROLE not found")
    
    print()
    
    if pg_host and pg_database:
        print("✅ PG_HOST found:", pg_host)
        print("✅ PG_DATABASE found:", pg_database)
        print("\n🎯 Configured for: LOCAL POSTGRESQL")
    else:
        print("❌ PG_HOST not found")
        print("❌ PG_DATABASE not found")
    
    # Try to connect
    print("\n" + "=" * 80)
    print("CONNECTION TEST")
    print("=" * 80)
    
    try:
        db = get_db_client()
        
        if hasattr(db, 'supabase'):
            print("\n✅ Connected to: SUPABASE")
            print("   Type: SupabaseDatabaseClient")
            
            # Test query
            try:
                response = db.supabase.table("benchmark_results").select("id").limit(1).execute()
                if response.data:
                    print(f"   Test query: ✅ Success (found {len(response.data)} record)")
                else:
                    print("   Test query: ⚠️  No data found")
            except Exception as e:
                print(f"   Test query: ❌ Failed - {e}")
                
        else:
            print("\n✅ Connected to: LOCAL POSTGRESQL")
            print("   Type: LocalDatabaseClient")
            
            # Test query
            try:
                conn = db._get_connection()
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM benchmark_results")
                count = cur.fetchone()[0]
                cur.close()
                conn.close()
                print(f"   Test query: ✅ Success ({count} records in benchmark_results)")
            except Exception as e:
                print(f"   Test query: ❌ Failed - {e}")
        
        print("\n" + "=" * 80)
        print("✅ DATABASE CONNECTION SUCCESSFUL")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print("\n" + "=" * 80)
        print("❌ DATABASE CONNECTION FAILED")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    check_database_config()
