"""Reusable API dependencies."""

from functools import lru_cache
from uuid import UUID

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import AuthenticatedUser, AuthenticationError, SupabaseTokenVerifier
from app.db.session import get_db
from app.models.admin import AdminUser
from app.services.supabase_auth import SupabaseAuthService


bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def get_token_verifier() -> SupabaseTokenVerifier:
    return SupabaseTokenVerifier(get_settings().supabase_url)


@lru_cache
def get_auth_service() -> SupabaseAuthService:
    settings = get_settings()
    return SupabaseAuthService(settings.supabase_url, settings.supabase_anon_key)


def get_access_token(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


def get_current_user(
    access_token: str = Depends(get_access_token),
) -> AuthenticatedUser:
    """Return the user from a verified Bearer token, never from request data."""
    try:
        return get_token_verifier().verify(access_token)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def require_admin(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuthenticatedUser:
    """Allow only users explicitly listed by a trusted administrator.

    The UUID comes exclusively from the already verified JWT subject. No
    request body, path parameter, JWT user metadata or client role is used.
    """
    try:
        user_id = UUID(current_user.id)
    except (AttributeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authenticated user",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    try:
        admin = db.get(AdminUser, user_id)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authorization service unavailable",
        ) from exc

    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return current_user
