"""Profile persistence with explicit user ownership checks."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.profile import Profile


logger = logging.getLogger(__name__)


class ProfileError(Exception):
    """Base error for safe profile-service failures."""


class ProfileNotFoundError(ProfileError):
    pass


class ProfileDatabaseError(ProfileError):
    pass


def _parse_user_id(user_id: str) -> UUID:
    try:
        return UUID(user_id)
    except ValueError as exc:
        logger.warning(
            "Profile operation failed: exception_class=%s category=invalid_identifier",
            type(exc).__name__,
        )
        raise ProfileDatabaseError("Invalid authenticated user identifier") from exc


def _log_database_failure(exc: BaseException, category: str = "database") -> None:
    """Log only safe failure metadata; never log user IDs or exception details."""
    logger.warning(
        "Profile operation failed: exception_class=%s category=%s",
        type(exc).__name__,
        category,
    )


def get_profile(db: Session, user_id: str) -> Profile:
    """Fetch only the profile whose primary key equals the authenticated user."""
    owner_id = _parse_user_id(user_id)
    try:
        profile = db.get(Profile, owner_id)
    except SQLAlchemyError as exc:
        _log_database_failure(exc)
        raise ProfileDatabaseError("Profile lookup failed") from exc
    if profile is None:
        raise ProfileNotFoundError("Profile not found")
    return profile


def ensure_profile(db: Session, user_id: str) -> Profile:
    """Create one empty profile, or return the existing profile for this user."""
    owner_id = _parse_user_id(user_id)
    try:
        profile = db.get(Profile, owner_id)
        if profile is not None:
            return profile
        profile = Profile(user_id=owner_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile
    except IntegrityError as exc:
        _log_database_failure(exc, "integrity")
        db.rollback()
        try:
            profile = db.get(Profile, owner_id)
        except SQLAlchemyError as lookup_error:
            _log_database_failure(lookup_error)
            raise ProfileDatabaseError("Profile creation failed") from lookup_error
        if profile is not None:
            return profile
        raise ProfileDatabaseError("Profile creation failed") from exc
    except SQLAlchemyError as exc:
        _log_database_failure(exc)
        db.rollback()
        raise ProfileDatabaseError("Profile creation failed") from exc


def update_profile(db: Session, user_id: str, display_name: str | None) -> Profile:
    """Update the allow-listed profile field for the authenticated user only."""
    profile = ensure_profile(db, user_id)
    profile.display_name = display_name
    try:
        db.commit()
        db.refresh(profile)
        return profile
    except SQLAlchemyError as exc:
        _log_database_failure(exc)
        db.rollback()
        raise ProfileDatabaseError("Profile update failed") from exc
