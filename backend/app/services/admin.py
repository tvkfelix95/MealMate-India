"""Server-managed administrator bootstrap operations."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.admin import AdminUser


class AdminBootstrapError(Exception):
    """Base error for administrator bootstrap failures."""


class AdminAlreadyExistsError(AdminBootstrapError):
    """Raised when bootstrap has already been completed."""


class AdminBootstrapDatabaseError(AdminBootstrapError):
    """Raised for safe, sanitised database failures."""


BOOTSTRAP_LOCK_SQL = "SELECT pg_advisory_xact_lock(hashtextextended('mealmate.admin.bootstrap', 0))"


def bootstrap_first_admin(db: Session, user_id: str) -> AdminUser:
    """Atomically insert the first administrator and no subsequent one."""
    try:
        owner_id = UUID(user_id)
    except (AttributeError, ValueError) as exc:
        raise AdminBootstrapError("Invalid authenticated user identifier") from exc

    try:
        # This transaction-scoped lock serializes all first-admin attempts,
        # including the empty-table case where row locks cannot help.
        db.execute(text(BOOTSTRAP_LOCK_SQL))
        if db.query(AdminUser).first() is not None:
            raise AdminAlreadyExistsError("Administrator bootstrap is complete")

        admin = AdminUser(user_id=owner_id)
        db.add(admin)
        db.commit()
        return admin
    except AdminAlreadyExistsError:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise AdminAlreadyExistsError("Administrator bootstrap is complete") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise AdminBootstrapDatabaseError("Administrator bootstrap unavailable") from exc


__all__ = [
    "AdminAlreadyExistsError",
    "AdminBootstrapDatabaseError",
    "AdminBootstrapError",
    "BOOTSTRAP_LOCK_SQL",
    "bootstrap_first_admin",
]
