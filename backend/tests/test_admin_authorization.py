from uuid import UUID

import pytest
from fastapi import HTTPException

from app.api.dependencies import require_admin
from app.core.security import AuthenticatedUser
from app.models.admin import AdminUser


USER_A = "00000000-0000-0000-0000-000000000001"
USER_B = "00000000-0000-0000-0000-000000000002"


class FakeAdminDB:
    def __init__(self, admin_ids: set[UUID] | None = None) -> None:
        self.admin_ids = admin_ids or set()
        self.looked_up: list[UUID] = []

    def get(self, model: type, user_id: UUID):
        assert model is AdminUser
        self.looked_up.append(user_id)
        return AdminUser(user_id=user_id) if user_id in self.admin_ids else None


def test_missing_authentication_is_rejected_by_existing_dependency() -> None:
    from app.api.dependencies import get_current_user

    with pytest.raises(HTTPException) as error:
        get_current_user(None)  # type: ignore[arg-type]

    assert error.value.status_code == 401


def test_authenticated_non_admin_is_denied() -> None:
    with pytest.raises(HTTPException) as error:
        require_admin(AuthenticatedUser(id=USER_A), FakeAdminDB())

    assert error.value.status_code == 403


def test_registered_admin_is_allowed() -> None:
    db = FakeAdminDB({UUID(USER_A)})
    user = AuthenticatedUser(id=USER_A)

    assert require_admin(user, db) is user
    assert db.looked_up == [UUID(USER_A)]


def test_admin_lookup_uses_verified_subject_not_client_data() -> None:
    db = FakeAdminDB({UUID(USER_A)})
    verified_user = AuthenticatedUser(id=USER_A)

    # There is no user-supplied role or user ID in this dependency's inputs.
    assert require_admin(verified_user, db) is verified_user
    assert db.looked_up == [UUID(USER_A)]
    assert UUID(USER_B) not in db.looked_up


def test_invalid_authenticated_subject_is_rejected() -> None:
    with pytest.raises(HTTPException) as error:
        require_admin(AuthenticatedUser(id="not-a-uuid"), FakeAdminDB())

    assert error.value.status_code == 401
