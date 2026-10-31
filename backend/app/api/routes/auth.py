from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import field_validator

from app.api.dependencies import get_access_token, get_auth_service, get_current_user
from app.core.security import AuthenticatedUser
from app.schemas.auth import AuthCredentials, AuthenticatedUserResponse, AuthSessionResponse
from app.services.supabase_auth import (
    DuplicateEmailError,
    InvalidCredentialsError,
    SupabaseAuthError,
    SupabaseAuthService,
    UnverifiedEmailError,
)
from app.db.session import get_db
from app.services.profile import ProfileDatabaseError, ensure_profile
from sqlalchemy.orm import Session


router = APIRouter(prefix="/auth", tags=["auth"])


class ValidatedAuthCredentials(AuthCredentials):
    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        email = value.strip().lower()
        local, separator, domain = email.rpartition("@")
        if not separator or not local or "." not in domain or domain.startswith(".") or domain.endswith("."):
            raise ValueError("Enter a valid email address")
        return email

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8 or len(value) > 128:
            raise ValueError("Password must be 8 to 128 characters")
        return value


def _auth_error(error: SupabaseAuthError) -> HTTPException:
    if isinstance(error, DuplicateEmailError):
        detail = "Email is already registered"
        code = status.HTTP_409_CONFLICT
    elif isinstance(error, InvalidCredentialsError):
        detail = "Invalid email or password"
        code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(error, UnverifiedEmailError):
        detail = "Email address must be verified"
        code = status.HTTP_403_FORBIDDEN
    else:
        detail = "Authentication service unavailable"
        code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HTTPException(status_code=code, detail=detail)


@router.get("/me", response_model=AuthenticatedUserResponse)
def get_authenticated_user(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUserResponse:
    return AuthenticatedUserResponse(id=current_user.id)


@router.post("/register", response_model=AuthSessionResponse, status_code=status.HTTP_201_CREATED)
def register(
    credentials: ValidatedAuthCredentials,
    auth_service: SupabaseAuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
) -> AuthSessionResponse:
    try:
        session = auth_service.register(credentials.email, credentials.password)
    except SupabaseAuthError as error:
        raise _auth_error(error) from error
    try:
        ensure_profile(db, session.user_id)
    except ProfileDatabaseError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Profile service unavailable",
        ) from error
    return AuthSessionResponse(
        user_id=session.user_id,
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        email_confirmation_required=session.email_confirmation_required,
    )


@router.post("/login", response_model=AuthSessionResponse)
def login(
    credentials: ValidatedAuthCredentials,
    auth_service: SupabaseAuthService = Depends(get_auth_service),
) -> AuthSessionResponse:
    try:
        session = auth_service.login(credentials.email, credentials.password)
    except SupabaseAuthError as error:
        raise _auth_error(error) from error
    return AuthSessionResponse(
        user_id=session.user_id,
        access_token=session.access_token,
        refresh_token=session.refresh_token,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    access_token: str = Depends(get_access_token),
    _: AuthenticatedUser = Depends(get_current_user),
    auth_service: SupabaseAuthService = Depends(get_auth_service),
) -> Response:
    try:
        auth_service.logout(access_token)
    except SupabaseAuthError as error:
        raise _auth_error(error) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
