from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_access_token, get_current_user
from app.core.config import get_settings
from app.core.security import AuthenticatedUser
from app.db.session import get_db
from app.schemas.admin import AdminBootstrapResponse
from app.services.admin import (
    AdminAlreadyExistsError,
    AdminBootstrapDatabaseError,
    AdminBootstrapError,
    bootstrap_first_admin,
)
from app.services.supabase_auth import (
    InvalidAccessTokenError,
    SupabaseAuthError,
    SupabaseAuthService,
)
from app.api.dependencies import get_auth_service


router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/bootstrap", response_model=AdminBootstrapResponse, status_code=status.HTTP_201_CREATED)
def bootstrap_admin(
    access_token: str = Depends(get_access_token),
    current_user: AuthenticatedUser = Depends(get_current_user),
    auth_service: SupabaseAuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
) -> AdminBootstrapResponse:
    try:
        provider_user = auth_service.get_user(access_token)
    except InvalidAccessTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except SupabaseAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        ) from exc

    configured_email = get_settings().admin_bootstrap_email.strip().casefold()
    same_user = provider_user.user_id == current_user.id
    email_matches = bool(configured_email) and provider_user.email.strip().casefold() == configured_email
    if not same_user or not provider_user.email_verified or not email_matches:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator bootstrap is not permitted",
        )

    try:
        bootstrap_first_admin(db, current_user.id)
    except AdminAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator bootstrap is not permitted",
        ) from exc
    except AdminBootstrapDatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Administrator bootstrap unavailable",
        ) from exc
    except AdminBootstrapError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authenticated user",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return AdminBootstrapResponse(message="Administrator bootstrap completed")
