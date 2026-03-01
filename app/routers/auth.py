"""
Auth Router

Endpoints:
  - GET /api/auth/me  → Current user from Supabase JWT (Authorization: Bearer <access_token>)
  - DELETE /api/auth/delete-me → Delete current user (Supabase admin); requires Bearer token.
"""

from fastapi import APIRouter, Depends, status

from app.auth import get_current_user
from app.schemas import AuthUserResponse
from app.supabase_admin import get_admin_client

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.get("/me", response_model=AuthUserResponse)
def auth_me(payload: dict = Depends(get_current_user)):
    """
    Return the current user from the Supabase JWT.
    Send header: Authorization: Bearer <access_token> (from supabase.auth.getSession().access_token).
    """
    return AuthUserResponse(
        id=payload.get("sub", ""),
        email=payload.get("email"),
    )


@router.delete("/delete-me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(payload: dict = Depends(get_current_user)):
    """
    Permanently delete the current user's account (Supabase Auth).
    Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY on the server.
    """
    admin = get_admin_client()
    if not admin:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account deletion not configured (missing SUPABASE_SERVICE_ROLE_KEY)",
        )
    user_id = payload.get("sub")
    if not user_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    try:
        admin.auth.admin.delete_user(user_id)
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    return None
