"""
Supabase Admin client for server-only auth operations (e.g. delete user).

Uses SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY. If either is missing,
get_admin_client() returns None and delete-me endpoint returns 503.
"""

import os
from typing import Optional

def get_admin_client():
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        return None
    from supabase import create_client
    return create_client(url, key)
