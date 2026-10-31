"""Profile persistence with explicit user ownership checks."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.profile import Profile


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
        raise ProfileDatabaseError("Invalid authenticated user identifier") from exc


def get_profile(db: Session, user_id: str) -> Profile:
    """Fetch only the profile whose primary key equals the authenticated user."""
    owner_id = _parse_user_id(user_id)
    try:
        profile = db.get(Profile, owner_id)
    except SQLAlchemyError as exc:
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
        db.rollback()
        try:
            profile = db.get(Profile, owner_id)
        except SQLAlchemyError as lookup_error:
            raise ProfileDatabaseError("Profile creation failed") from lookup_error
        if profile is not None:
            return profile
        raise ProfileDatabaseError("Profile creation failed") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise ProfileDatabaseError("Profile creation failed") from exc


def update_profile(db: Session, user_id: str, display_name: str | None) -> Profile:
    """Update the allow-listed profile field for the authenticated user only."""
    profile = get_profile(db, user_id)
    profile.display_name = display_name
    try:
        db.commit()
        db.refresh(profile)
        return profile
    except SQLAlchemyError as exc:
        db.rollback()
        raise ProfileDatabaseError("Profile update failed") from exc
