from datetime import datetime, timedelta, timezone
import json

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_auth_service, get_current_user, get_token_verifier
from app.db.session import get_db
from app.core.security import AuthenticatedUser, AuthenticationError
from app.main import app
from app.services.supabase_auth import (
    AuthSession,
    DuplicateEmailError,
    InvalidCredentialsError,
    UnverifiedEmailError,
)


client = TestClient(app)


class FakeProfileDB:
    def __init__(self) -> None:
        self.profile = None

    def get(self, model, user_id):
        if self.profile is not None and self.profile.user_id == user_id:
            return self.profile
        return None

    def add(self, profile) -> None:
        self.profile = profile

    def commit(self) -> None:
        return None

    def refresh(self, profile) -> None:
        return None

    def rollback(self) -> None:
        return None


def test_auth_me_rejects_missing_token() -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_auth_me_returns_verified_user_id() -> None:
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(id="user-123")
    try:
        response = client.get("/api/v1/auth/me")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"id": "user-123"}


def test_invalid_token_is_rejected_without_exposing_details(monkeypatch: pytest.MonkeyPatch) -> None:
    class InvalidVerifier:
        def verify(self, token: str) -> AuthenticatedUser:
            raise AuthenticationError("internal token details")

    monkeypatch.setattr("app.api.dependencies.get_token_verifier", lambda: InvalidVerifier())
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or expired access token"}


def _signed_token(expiry: datetime):
    jwt = pytest.importorskip("jwt")
    from cryptography.hazmat.primitives.asymmetric import rsa

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(public_key))
    jwk.update({"kid": "test-key", "alg": "RS256", "use": "sig"})
    token = jwt.encode(
        {
            "sub": "user-123",
            "iss": "https://example.supabase.co/auth/v1",
            "aud": "authenticated",
            "exp": expiry,
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "test-key"},
    )
    return token, jwk


def test_valid_jwt_returns_authenticated_user(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.security import SupabaseTokenVerifier

    token, jwk = _signed_token(datetime.now(timezone.utc) + timedelta(minutes=5))
    verifier = SupabaseTokenVerifier("https://example.supabase.co")
    monkeypatch.setattr(verifier.jwks, "_load_keys", lambda force_refresh=False: [jwk])
    monkeypatch.setattr("app.api.dependencies.get_token_verifier", lambda: verifier)

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {"id": "user-123"}


def test_expired_jwt_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.security import SupabaseTokenVerifier

    token, jwk = _signed_token(datetime.now(timezone.utc) - timedelta(minutes=5))
    verifier = SupabaseTokenVerifier("https://example.supabase.co")
    monkeypatch.setattr(verifier.jwks, "_load_keys", lambda force_refresh=False: [jwk])
    monkeypatch.setattr("app.api.dependencies.get_token_verifier", lambda: verifier)

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or expired access token"}


def test_unsupported_algorithm_is_rejected() -> None:
    # Header declares an algorithm outside the verifier allowlist.
    token = "eyJhbGciOiJIUzI1NiIsImtpZCI6InRlc3Qta2V5IiwidHlwIjoiSldUIn0.eyJzdWIiOiJ1c2VyLTEyMyJ9.signature"

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or expired access token"}


class FakeAuthService:
    def register(self, email: str, password: str) -> AuthSession:
        return AuthSession("00000000-0000-0000-0000-000000000001", "access-token", "refresh-token")

    def login(self, email: str, password: str) -> AuthSession:
        return AuthSession("user-123", "access-token", "refresh-token")

    def logout(self, access_token: str) -> None:
        assert access_token == "access-token"


def with_auth_service(service: object) -> None:
    app.dependency_overrides[get_auth_service] = lambda: service


def test_register_returns_supabase_session() -> None:
    db = FakeProfileDB()
    with_auth_service(FakeAuthService())
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.post("/api/v1/auth/register", json={"email": "User@example.com", "password": "password123"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json() == {
        "user_id": "00000000-0000-0000-0000-000000000001",
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "email_confirmation_required": False,
    }
    assert db.profile is not None
    assert str(db.profile.user_id) == "00000000-0000-0000-0000-000000000001"


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"email": "not-an-email", "password": "password123"}, "valid email"),
        ({"email": "user@example.com", "password": "short"}, "8 to 128"),
    ],
)
def test_auth_input_validation(payload: dict[str, str], message: str) -> None:
    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 422
    assert message in response.text


def test_duplicate_email_is_sanitised() -> None:
    class DuplicateService(FakeAuthService):
        def register(self, email: str, password: str) -> AuthSession:
            raise DuplicateEmailError("provider details")

    with_auth_service(DuplicateService())
    try:
        response = client.post("/api/v1/auth/register", json={"email": "user@example.com", "password": "password123"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json() == {"detail": "Email is already registered"}


def test_invalid_credentials_are_sanitised() -> None:
    class InvalidService(FakeAuthService):
        def login(self, email: str, password: str) -> AuthSession:
            raise InvalidCredentialsError("provider details")

    with_auth_service(InvalidService())
    try:
        response = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "password123"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}


def test_unverified_email_is_rejected() -> None:
    class UnverifiedService(FakeAuthService):
        def login(self, email: str, password: str) -> AuthSession:
            raise UnverifiedEmailError("provider details")

    with_auth_service(UnverifiedService())
    try:
        response = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "password123"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {"detail": "Email address must be verified"}


def test_logout_requires_verified_user_and_calls_supabase() -> None:
    service = FakeAuthService()
    with_auth_service(service)
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(id="user-123")
    try:
        response = client.post("/api/v1/auth/logout", headers={"Authorization": "Bearer access-token"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
