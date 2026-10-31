"""Supabase Auth JWT verification using the project's JWKS endpoint."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import monotonic
from typing import Any

import httpx

try:
    import jwt
except ImportError:  # pragma: no cover - exercised when dependencies are not installed
    jwt = None  # type: ignore[assignment]


SUPPORTED_ALGORITHMS = frozenset({"ES256", "RS256"})
JWKS_CACHE_SECONDS = 300


class AuthenticationError(Exception):
    """Raised when an access token cannot be trusted."""


@dataclass(frozen=True)
class AuthenticatedUser:
    """The minimum trusted identity exposed to API handlers."""

    id: str


class SupabaseJWKS:
    """Small in-process JWKS cache with bounded network timeouts."""

    def __init__(self, supabase_url: str, cache_seconds: int = JWKS_CACHE_SECONDS) -> None:
        base_url = supabase_url.rstrip("/")
        if not base_url:
            raise AuthenticationError("Authentication is not configured")
        self.issuer = f"{base_url}/auth/v1"
        self.jwks_url = f"{self.issuer}/.well-known/jwks.json"
        self.cache_seconds = cache_seconds
        self._keys: list[dict[str, Any]] = []
        self._expires_at = 0.0
        self._lock = Lock()

    def _load_keys(self, force_refresh: bool = False) -> list[dict[str, Any]]:
        now = monotonic()
        with self._lock:
            if self._keys and not force_refresh and now < self._expires_at:
                return self._keys
            try:
                response = httpx.get(self.jwks_url, timeout=5.0)
                response.raise_for_status()
                keys = response.json().get("keys")
            except (httpx.HTTPError, ValueError, AttributeError) as exc:
                raise AuthenticationError("Unable to retrieve signing keys") from exc
            if not isinstance(keys, list):
                raise AuthenticationError("Invalid signing key response")
            self._keys = [key for key in keys if isinstance(key, dict)]
            self._expires_at = now + self.cache_seconds
            return self._keys

    def get_key(self, key_id: str, algorithm: str) -> Any:
        for force_refresh in (False, True):
            for jwk in self._load_keys(force_refresh=force_refresh):
                if jwk.get("kid") != key_id or jwk.get("alg") not in (None, algorithm):
                    continue
                if jwk.get("kty") not in ("EC", "RSA"):
                    continue
                try:
                    return jwt.PyJWK.from_dict(jwk, algorithm=algorithm).key  # type: ignore[union-attr]
                except Exception as exc:
                    raise AuthenticationError("Invalid signing key") from exc
            if force_refresh:
                break
        raise AuthenticationError("Signing key not found")


class SupabaseTokenVerifier:
    """Verify Supabase access tokens without trusting client-supplied identity."""

    def __init__(self, supabase_url: str) -> None:
        self.jwks = SupabaseJWKS(supabase_url)

    def verify(self, token: str) -> AuthenticatedUser:
        if jwt is None:
            raise AuthenticationError("JWT verification dependency is unavailable")
        try:
            header = jwt.get_unverified_header(token)
            algorithm = header.get("alg")
            key_id = header.get("kid")
            if algorithm not in SUPPORTED_ALGORITHMS or not isinstance(key_id, str):
                raise AuthenticationError("Unsupported access token")
            key = self.jwks.get_key(key_id, algorithm)
            claims = jwt.decode(
                token,
                key,
                algorithms=[algorithm],
                audience="authenticated",
                issuer=self.jwks.issuer,
                options={"require": ["exp", "iss", "aud", "sub"]},
            )
        except AuthenticationError:
            raise
        except Exception as exc:
            raise AuthenticationError("Invalid or expired access token") from exc

        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise AuthenticationError("Invalid access token subject")
        return AuthenticatedUser(id=subject)
