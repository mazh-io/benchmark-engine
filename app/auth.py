"""
Supabase JWT verification for FastAPI.

Use Depends(get_current_user) on routes that require auth.
Use Depends(get_current_user_optional) when auth is optional.
"""

import os
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# JWT secret from Supabase: Project Settings → API → JWT Secret
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")

Scheme = HTTPBearer(auto_error=False)


def get_current_user_optional(
    cred: Optional[HTTPAuthorizationCredentials] = Depends(Scheme),
) -> Optional[dict]:
    """
    Verify Supabase JWT if present. Returns payload (sub, email, ...) or None.
    """
    if not SUPABASE_JWT_SECRET:
        return None
    if not cred or not cred.credentials:
        return None
    try:
        payload = jwt.decode(
            cred.credentials,
            SUPABASE_JWT_SECRET,
            audience="authenticated",
            algorithms=["HS256"],
        )
        return payload
    except jwt.PyJWTError:
        return None


def get_current_user(
    cred: Optional[HTTPAuthorizationCredentials] = Depends(Scheme),
) -> dict:
    """
    Require valid Supabase JWT. Raises 401 if missing or invalid.
    """
    if not SUPABASE_JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth not configured (SUPABASE_JWT_SECRET)",
        )
    if not cred or not cred.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )
    try:
        payload = jwt.decode(
            cred.credentials,
            SUPABASE_JWT_SECRET,
            audience="authenticated",
            algorithms=["HS256"],
        )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
