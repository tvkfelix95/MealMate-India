"""Small adapter around the Supabase Auth REST API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


class SupabaseAuthError(Exception):
    """Base error for sanitised authentication-provider failures."""


class DuplicateEmailError(SupabaseAuthError):
    pass


class InvalidCredentialsError(SupabaseAuthError):
    pass


class UnverifiedEmailError(SupabaseAuthError):
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
            data = response.json() if response.content else {}
        except (httpx.HTTPError, ValueError) as exc:
            raise SupabaseAuthError("Authentication provider unavailable") from exc
        if response.status_code >= 400:
            if not isinstance(data, dict):
                raise SupabaseAuthError("Authentication request failed")
            self._raise_provider_error(data)
        if not isinstance(data, dict):
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
        code = str(data.get("code", "")).lower()
        message = str(data.get("msg", data.get("message", ""))).lower()
        if code in {"user_already_exists", "email_exists"} or "already registered" in message:
            raise DuplicateEmailError("Email is already registered")
        if code in {"invalid_credentials", "invalid_login_credentials"} or "invalid login credentials" in message:
            raise InvalidCredentialsError("Invalid email or password")
        raise SupabaseAuthError("Authentication request failed")

    @staticmethod
    def _session_from_response(data: dict[str, Any], require_tokens: bool) -> AuthSession:
        session = data.get("session") if isinstance(data.get("session"), dict) else data
        user = data.get("user")
        if not isinstance(user, dict) or not isinstance(user.get("id"), str):
            raise SupabaseAuthError("Invalid authentication provider response")
        access_token = session.get("access_token")
        refresh_token = session.get("refresh_token")
        if require_tokens and (not isinstance(access_token, str) or not isinstance(refresh_token, str)):
            raise SupabaseAuthError("Invalid authentication provider response")
        email_confirmation_required = (
            "email_confirmed_at" in user
            and not user.get("email_confirmed_at")
            and not user.get("confirmed_at")
        )
        return AuthSession(
            user_id=user["id"],
            access_token=access_token if isinstance(access_token, str) else None,
            refresh_token=refresh_token if isinstance(refresh_token, str) else None,
            email_confirmation_required=email_confirmation_required,
        )

    def register(self, email: str, password: str) -> AuthSession:
        data = self._post("/signup", {"email": email, "password": password})
        session = self._session_from_response(data, require_tokens=False)
        if session.email_confirmation_required:
            return session
        if not session.access_token or not session.refresh_token:
            raise SupabaseAuthError("Invalid authentication provider response")
        return session

    def login(self, email: str, password: str) -> AuthSession:
        data = self._post("/token?grant_type=password", {"email": email, "password": password})
        session = self._session_from_response(data, require_tokens=True)
        if session.email_confirmation_required:
            raise UnverifiedEmailError("Email address must be verified")
        return session

    def logout(self, access_token: str) -> None:
        self._post("/logout", access_token=access_token)
