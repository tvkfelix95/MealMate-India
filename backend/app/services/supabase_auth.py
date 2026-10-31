"""Small adapter around the Supabase Auth REST API."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

import httpx


logger = logging.getLogger(__name__)


def _exception_chain_contains(exc: BaseException, class_name: str) -> bool:
    """Check exception types without inspecting or logging exception messages."""
    current: BaseException | None = exc
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if class_name in type(current).__name__.upper():
            return True
        current = current.__cause__ or current.__context__
    return False


def _failure_category(exc: BaseException) -> str:
    """Return a small, non-sensitive category for an Auth request failure."""
    if isinstance(exc, httpx.TimeoutException):
        return "timeout"
    if _exception_chain_contains(exc, "SSL"):
        return "tls"
    if isinstance(exc, httpx.NetworkError):
        return "network"
    if isinstance(exc, ValueError):
        return "response_parsing"
    return "provider_error"


def _provider_error_category(data: dict[str, Any]) -> str:
    """Classify provider error payloads without logging their contents."""
    code = str(data.get("code", "")).lower()
    message = str(data.get("msg", data.get("message", ""))).lower()
    if code in {"user_already_exists", "email_exists"} or "already registered" in message:
        return "duplicate_email"
    if code in {"invalid_credentials", "invalid_login_credentials"} or "invalid login credentials" in message:
        return "invalid_credentials"
    if code in {"email_not_confirmed", "email_not_confirmed_error"} or "email not confirmed" in message:
        return "unverified_email"
    return "provider_error"


class SupabaseAuthError(Exception):
    """Base error for sanitised authentication-provider failures."""


class DuplicateEmailError(SupabaseAuthError):
    pass


class InvalidCredentialsError(SupabaseAuthError):
    pass


class UnverifiedEmailError(SupabaseAuthError):
    pass


class RateLimitError(SupabaseAuthError):
    pass


class InvalidAccessTokenError(SupabaseAuthError):
    pass


@dataclass(frozen=True)
class AuthSession:
    user_id: str
    access_token: str | None
    refresh_token: str | None
    email_confirmation_required: bool = False


@dataclass(frozen=True)
class SupabaseUser:
    user_id: str
    email: str
    email_verified: bool


class SupabaseAuthService:
    """Call Supabase Auth without persisting or logging passwords locally."""

    def __init__(self, supabase_url: str, anon_key: str) -> None:
        base_url = supabase_url.rstrip("/")
        self.base_url = f"{base_url}/auth/v1" if base_url else ""
        self.headers = {"apikey": anon_key, "Content-Type": "application/json"}

    def _post(self, path: str, payload: dict[str, str] | None = None, access_token: str | None = None) -> dict[str, Any]:
        if not self.base_url or not self.headers["apikey"]:
            logger.warning(
                "Supabase Auth request failed: stage=request_configuration_failed "
                "exception_class=SupabaseAuthError category=configuration"
            )
            raise SupabaseAuthError("Authentication is not configured")
        headers = dict(self.headers)
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        try:
            response = httpx.post(
                f"{self.base_url}{path}",
                headers=headers,
                json=payload,
                timeout=10.0,
            )
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning(
                "Supabase Auth request failed: stage=request_failed exception_class=%s category=%s",
                type(exc).__name__,
                _failure_category(exc),
            )
            raise SupabaseAuthError("Authentication provider unavailable") from exc
        logger.info(
            "Supabase Auth request: stage=http_response_received status_code=%s",
            response.status_code,
        )
        try:
            data = response.json() if response.content else {}
        except ValueError as exc:
            logger.warning(
                "Supabase Auth request failed: stage=response_json_parse_failed "
                "exception_class=%s category=response_parsing",
                type(exc).__name__,
            )
            raise SupabaseAuthError("Authentication provider unavailable") from exc
        logger.info("Supabase Auth request: stage=response_json_parsed")
        if response.status_code >= 400:
            category = _provider_error_category(data) if isinstance(data, dict) else "invalid_response"
            logger.warning(
                "Supabase Auth HTTP failure: stage=provider_http_error status_code=%s category=%s",
                response.status_code,
                category,
            )
            if not isinstance(data, dict):
                logger.warning(
                    "Supabase Auth request failed: stage=response_schema_validation_failed "
                    "exception_class=SupabaseAuthError category=response_schema"
                )
                raise SupabaseAuthError("Authentication request failed")
            if response.status_code == 429:
                raise RateLimitError("Authentication requests are temporarily rate limited")
            self._raise_provider_error(data)
        if not isinstance(data, dict):
            logger.warning(
                "Supabase Auth request failed: stage=response_schema_validation_failed "
                "exception_class=SupabaseAuthError category=response_schema"
            )
            raise SupabaseAuthError("Invalid authentication provider response")
        return data

    def get_user(self, access_token: str) -> SupabaseUser:
        """Fetch the authenticated provider user without exposing token data."""
        if not self.base_url or not self.headers["apikey"]:
            raise SupabaseAuthError("Authentication is not configured")
        headers = dict(self.headers)
        headers["Authorization"] = f"Bearer {access_token}"
        try:
            response = httpx.get(f"{self.base_url}/user", headers=headers, timeout=10.0)
            data = response.json() if response.content else {}
        except (httpx.HTTPError, ValueError) as exc:
            raise SupabaseAuthError("Authentication provider unavailable") from exc
        if response.status_code in {401, 403}:
            raise InvalidAccessTokenError("Invalid access token")
        if response.status_code >= 400 or not isinstance(data, dict):
            raise SupabaseAuthError("Authentication request failed")

        user_id = data.get("id")
        email = data.get("email")
        if not isinstance(user_id, str) or not isinstance(email, str) or not email.strip():
            raise SupabaseAuthError("Invalid authentication provider response")
        return SupabaseUser(
            user_id=user_id,
            email=email,
            email_verified=bool(data.get("email_confirmed_at") or data.get("confirmed_at")),
        )

    @staticmethod
    def _raise_provider_error(data: dict[str, Any]) -> None:
        category = _provider_error_category(data)
        if category == "duplicate_email":
            raise DuplicateEmailError("Email is already registered")
        if category == "invalid_credentials":
            raise InvalidCredentialsError("Invalid email or password")
        if category == "unverified_email":
            raise UnverifiedEmailError("Email address must be verified")
        raise SupabaseAuthError("Authentication request failed")

    @staticmethod
    def _session_from_response(data: dict[str, Any], require_tokens: bool) -> AuthSession:
        session = data.get("session") if isinstance(data.get("session"), dict) else data
        user = data.get("user")
        if not isinstance(user, dict) or not isinstance(user.get("id"), str):
            logger.warning(
                "Supabase Auth session validation failed: stage=user_id_validation_failed "
                "exception_class=SupabaseAuthError category=response_schema"
            )
            raise SupabaseAuthError("Invalid authentication provider response")
        raw_access_token = session.get("access_token")
        raw_refresh_token = session.get("refresh_token")
        if (
            (raw_access_token is not None and not isinstance(raw_access_token, str))
            or (raw_refresh_token is not None and not isinstance(raw_refresh_token, str))
        ):
            logger.warning(
                "Supabase Auth session validation failed: stage=token_validation_failed "
                "exception_class=SupabaseAuthError category=response_schema"
            )
            raise SupabaseAuthError("Invalid authentication provider response")
        access_token = raw_access_token if isinstance(raw_access_token, str) else None
        refresh_token = raw_refresh_token if isinstance(raw_refresh_token, str) else None
        if require_tokens and (not isinstance(access_token, str) or not isinstance(refresh_token, str)):
            logger.warning(
                "Supabase Auth session validation failed: stage=token_validation_failed "
                "exception_class=SupabaseAuthError category=incomplete_session"
            )
            raise SupabaseAuthError("Invalid authentication provider response")
        email_confirmation_required = access_token is None and refresh_token is None
        logger.info("Supabase Auth session validation: stage=session_validation_passed")
        return AuthSession(
            user_id=user["id"],
            access_token=access_token,
            refresh_token=refresh_token,
            email_confirmation_required=email_confirmation_required,
        )

    def register(self, email: str, password: str) -> AuthSession:
        logger.info("Supabase Auth registration: stage=signup_request_started")
        data = self._post("/signup", {"email": email, "password": password})
        session = self._session_from_response(data, require_tokens=False)
        if session.email_confirmation_required:
            logger.info("Supabase Auth registration: stage=confirmation_pending")
            return session
        if not session.access_token or not session.refresh_token:
            logger.warning(
                "Supabase Auth registration failed: stage=token_validation_failed "
                "exception_class=SupabaseAuthError category=incomplete_session"
            )
            raise SupabaseAuthError("Invalid authentication provider response")
        logger.info("Supabase Auth registration: stage=registration_completed")
        return session

    def login(self, email: str, password: str) -> AuthSession:
        data = self._post("/token?grant_type=password", {"email": email, "password": password})
        session = self._session_from_response(data, require_tokens=True)
        if session.email_confirmation_required:
            raise UnverifiedEmailError("Email address must be verified")
        return session

    def logout(self, access_token: str) -> None:
        self._post("/logout", access_token=access_token)
