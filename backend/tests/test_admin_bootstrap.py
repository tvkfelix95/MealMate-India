from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.dependencies import get_access_token, get_auth_service, get_current_user
from app.core.security import AuthenticatedUser
from app.db.session import get_db
from app.main import app
from app.models.admin import AdminUser
from app.services.admin import AdminAlreadyExistsError, bootstrap_first_admin
from app.services.supabase_auth import SupabaseUser


USER_ID = "00000000-0000-0000-0000-000000000001"
client = TestClient(app)


class FakeAuthService:
    def __init__(self, user: SupabaseUser | None = None) -> None:
        self.user = user

    def get_user(self, access_token: str) -> SupabaseUser:
        assert access_token == "valid-token"
        assert self.user is not None
        return self.user


class FakeQuery:
    def __init__(self, db: "FakeBootstrapDB") -> None:
        self.db = db

    def first(self):
        return self.db.rows[0] if self.db.rows else None


class FakeBootstrapDB:
    def __init__(self, rows: list[AdminUser] | None = None) -> None:
        self.rows = rows or []
        self.transaction_lock = Lock()
        self.commit_count = 0
        self.rollback_count = 0
        self.lock_statement_seen = False

    def execute(self, statement) -> None:
        self.lock_statement_seen = "pg_advisory_xact_lock" in str(statement)
        self.transaction_lock.acquire()

    def query(self, model: type) -> FakeQuery:
        assert model is AdminUser
        return FakeQuery(self)

    def add(self, admin: AdminUser) -> None:
        self.rows.append(admin)

    def commit(self) -> None:
        self.commit_count += 1
        self.transaction_lock.release()

    def rollback(self) -> None:
        self.rollback_count += 1
        if self.transaction_lock.locked():
            self.transaction_lock.release()


def override_bootstrap_dependencies(
    db: FakeBootstrapDB,
    auth_service: FakeAuthService,
    user_id: str = USER_ID,
) -> None:
    app.dependency_overrides[get_access_token] = lambda: "valid-token"
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(id=user_id)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_db] = lambda: db


def test_successful_bootstrap_inserts_verified_jwt_subject(monkeypatch: pytest.MonkeyPatch) -> None:
    db = FakeBootstrapDB()
    auth = FakeAuthService(SupabaseUser(USER_ID, "Admin@Example.com", True))
    override_bootstrap_dependencies(db, auth)
    monkeypatch.setattr(
        "app.api.routes.admin.get_settings",
        lambda: SimpleNamespace(admin_bootstrap_email="admin@example.com"),
    )
    try:
        response = client.post("/api/v1/admin/bootstrap")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json() == {"message": "Administrator bootstrap completed"}
    assert db.rows[0].user_id == UUID(USER_ID)


@pytest.mark.parametrize(
    "user",
    [
        SupabaseUser(USER_ID, "other@example.com", True),
        SupabaseUser(USER_ID, "admin@example.com", False),
    ],
)
def test_wrong_or_unverified_email_is_forbidden(
    monkeypatch: pytest.MonkeyPatch, user: SupabaseUser
) -> None:
    db = FakeBootstrapDB()
    override_bootstrap_dependencies(db, FakeAuthService(user))
    monkeypatch.setattr(
        "app.api.routes.admin.get_settings",
        lambda: SimpleNamespace(admin_bootstrap_email="admin@example.com"),
    )
    try:
        response = client.post("/api/v1/admin/bootstrap")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert not db.rows


def test_non_empty_admin_table_is_forbidden(monkeypatch: pytest.MonkeyPatch) -> None:
    db = FakeBootstrapDB([AdminUser(user_id=UUID("00000000-0000-0000-0000-000000000002"))])
    override_bootstrap_dependencies(
        db,
        FakeAuthService(SupabaseUser(USER_ID, "admin@example.com", True)),
    )
    monkeypatch.setattr(
        "app.api.routes.admin.get_settings",
        lambda: SimpleNamespace(admin_bootstrap_email="admin@example.com"),
    )
    try:
        response = client.post("/api/v1/admin/bootstrap")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert len(db.rows) == 1


def test_missing_or_invalid_token_is_rejected() -> None:
    assert client.post("/api/v1/admin/bootstrap").status_code == 401


def test_invalid_token_is_rejected() -> None:
    def reject_token():
        raise HTTPException(status_code=401, detail="Invalid or expired access token")

    app.dependency_overrides[get_current_user] = reject_token
    try:
        response = client.post(
            "/api/v1/admin/bootstrap",
            headers={"Authorization": "Bearer invalid-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401


def test_concurrent_bootstrap_attempts_allow_only_one() -> None:
    db = FakeBootstrapDB()

    def attempt():
        return bootstrap_first_admin(db, USER_ID)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: _attempt_result(attempt), range(2)))

    assert results.count("success") == 1
    assert results.count("already_exists") == 1
    assert len(db.rows) == 1
    assert db.lock_statement_seen


def _attempt_result(attempt) -> str:
    try:
        attempt()
    except AdminAlreadyExistsError:
        return "already_exists"
    return "success"
