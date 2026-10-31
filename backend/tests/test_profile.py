from datetime import datetime, timezone
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import get_current_user
from app.core.security import AuthenticatedUser
from app.db.session import get_db
from app.main import app
from app.models.profile import Profile
from app.services.profile import ProfileDatabaseError, ensure_profile


USER_A = "00000000-0000-0000-0000-000000000001"
USER_B = "00000000-0000-0000-0000-000000000002"
client = TestClient(app)


class FakeProfileDB:
    def __init__(self, profiles: list[Profile] | None = None) -> None:
        self.profiles = {profile.user_id: profile for profile in profiles or []}

    def get(self, model, user_id: UUID):
        return self.profiles.get(user_id)

    def add(self, profile: Profile) -> None:
        self.profiles[profile.user_id] = profile

    def commit(self) -> None:
        return None

    def refresh(self, profile: Profile) -> None:
        if profile.created_at is None:
            profile.created_at = datetime.now(timezone.utc)
        if profile.updated_at is None:
            profile.updated_at = datetime.now(timezone.utc)

    def rollback(self) -> None:
        return None


def profile(user_id: str, display_name: str | None = None) -> Profile:
    now = datetime.now(timezone.utc)
    return Profile(user_id=UUID(user_id), display_name=display_name, created_at=now, updated_at=now)


def override_profile_dependencies(db: FakeProfileDB, user_id: str = USER_A) -> None:
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(id=user_id)


def test_registration_creates_profile_once() -> None:
    db = FakeProfileDB()
    ensure_profile(db, USER_A)
    ensure_profile(db, USER_A)

    assert list(db.profiles) == [UUID(USER_A)]
    assert db.profiles[UUID(USER_A)].display_name is None


def test_profile_creation_retries_after_database_failure(caplog: pytest.LogCaptureFixture) -> None:
    class RetryProfileDB(FakeProfileDB):
        fail_next = True

        def get(self, model, user_id: UUID):
            if self.fail_next:
                self.fail_next = False
                raise SQLAlchemyError("private database details")
            return super().get(model, user_id)

    db = RetryProfileDB()
    with caplog.at_level("WARNING", logger="app.services.profile"):
        with pytest.raises(ProfileDatabaseError):
            ensure_profile(db, USER_A)
        profile_result = ensure_profile(db, USER_A)

    assert profile_result.user_id == UUID(USER_A)
    assert len(db.profiles) == 1
    assert "category=database" in caplog.text
    assert USER_A not in caplog.text


def test_profile_me_creates_missing_authenticated_profile() -> None:
    db = FakeProfileDB()
    override_profile_dependencies(db, USER_A)
    try:
        response = client.get("/api/v1/profile/me")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["user_id"] == USER_A
    assert UUID(USER_A) in db.profiles


def test_profile_me_returns_only_authenticated_users_profile() -> None:
    db = FakeProfileDB([profile(USER_A, "Anu"), profile(USER_B, "Other")])
    override_profile_dependencies(db, USER_A)
    try:
        response = client.get("/api/v1/profile/me")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["user_id"] == USER_A
    assert response.json()["display_name"] == "Anu"


def test_profile_update_changes_only_allow_listed_field() -> None:
    db = FakeProfileDB([profile(USER_A)])
    override_profile_dependencies(db, USER_A)
    try:
        response = client.patch("/api/v1/profile/me", json={"display_name": "Anu"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["display_name"] == "Anu"
    assert db.profiles[UUID(USER_A)].display_name == "Anu"


def test_cross_user_profile_access_returns_not_found() -> None:
    db = FakeProfileDB([profile(USER_B, "Other")])
    override_profile_dependencies(db, USER_A)
    try:
        get_response = client.get("/api/v1/profile/me")
        patch_response = client.patch("/api/v1/profile/me", json={"display_name": "Intruder"})
    finally:
        app.dependency_overrides.clear()

    assert get_response.status_code == 200
    assert patch_response.status_code == 200
    assert db.profiles[UUID(USER_A)].display_name == "Intruder"
    assert db.profiles[UUID(USER_B)].display_name == "Other"


def test_profile_update_rejects_unknown_fields() -> None:
    db = FakeProfileDB([profile(USER_A)])
    override_profile_dependencies(db, USER_A)
    try:
        response = client.patch("/api/v1/profile/me", json={"user_id": USER_B})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
