"""Transactional preference persistence with authenticated-user ownership."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.preferences import (
    Allergen,
    Equipment,
    Ingredient,
    UserAllergen,
    UserDislikedIngredient,
    UserEquipment,
    UserPreferences,
)
from app.models.profile import Profile
from app.schemas.preferences import PreferencesResponse, PreferencesUpdate


class PreferencesError(Exception):
    pass


class PreferencesNotFoundError(PreferencesError):
    pass


class PreferencesValidationError(PreferencesError):
    pass


class PreferencesDatabaseError(PreferencesError):
    pass


def _owner_id(user_id: str) -> UUID:
    try:
        return UUID(user_id)
    except ValueError as exc:
        raise PreferencesValidationError("Invalid authenticated user identifier") from exc


def _existing_ids(db: Session, model: type, ids: list[UUID], active_only: bool = False) -> set[UUID]:
    existing: set[UUID] = set()
    for item_id in ids:
        item = db.get(model, item_id)
        if item is not None and (not active_only or item.is_active):
            existing.add(item_id)
    return existing


def _relation_ids(db: Session, model: type, user_id: UUID, field: str) -> list[UUID]:
    return [getattr(row, field) for row in db.query(model).filter_by(user_id=user_id).all()]


def get_preferences(db: Session, user_id: str) -> PreferencesResponse:
    owner_id = _owner_id(user_id)
    try:
        preferences = db.get(UserPreferences, owner_id)
        if preferences is None:
            raise PreferencesNotFoundError("Preferences not found")
        return PreferencesResponse(
            food_preference=preferences.food_preference,
            daily_budget_inr=preferences.daily_budget_inr,
            skill_level=preferences.skill_level,
            available_minutes=preferences.available_minutes,
            preferred_cuisines=[preferences.preferred_cuisine],
            allergies=_relation_ids(db, UserAllergen, owner_id, "allergen_id"),
            disliked_ingredients=_relation_ids(db, UserDislikedIngredient, owner_id, "ingredient_id"),
            kitchen_equipment=_relation_ids(db, UserEquipment, owner_id, "equipment_id"),
        )
    except PreferencesNotFoundError:
        raise
    except SQLAlchemyError as exc:
        raise PreferencesDatabaseError("Preference lookup failed") from exc


def save_preferences(db: Session, user_id: str, changes: PreferencesUpdate) -> PreferencesResponse:
    owner_id = _owner_id(user_id)
    try:
        if db.get(Profile, owner_id) is None:
            raise PreferencesNotFoundError("Profile not found")

        missing_allergens = set(changes.allergies or []) - _existing_ids(db, Allergen, changes.allergies or [])
        missing_ingredients = set(changes.disliked_ingredients or []) - _existing_ids(
            db, Ingredient, changes.disliked_ingredients or [], active_only=True
        )
        missing_equipment = set(changes.kitchen_equipment or []) - _existing_ids(
            db, Equipment, changes.kitchen_equipment or [], active_only=True
        )
        if missing_allergens or missing_ingredients or missing_equipment:
            raise PreferencesValidationError("One or more preference references are invalid")

        preferences = db.get(UserPreferences, owner_id)
        if preferences is None:
            preferences = UserPreferences(user_id=owner_id)
            db.add(preferences)
        preferences.food_preference = changes.food_preference
        preferences.daily_budget_inr = changes.daily_budget_inr
        preferences.skill_level = changes.skill_level
        preferences.available_minutes = changes.available_minutes
        preferences.preferred_cuisine = changes.preferred_cuisines[0]

        if changes.allergies is not None:
            db.query(UserAllergen).filter_by(user_id=owner_id).delete(synchronize_session=False)
            for allergen_id in changes.allergies:
                db.add(UserAllergen(user_id=owner_id, allergen_id=allergen_id))
        if changes.disliked_ingredients is not None:
            db.query(UserDislikedIngredient).filter_by(user_id=owner_id).delete(synchronize_session=False)
            for ingredient_id in changes.disliked_ingredients:
                db.add(UserDislikedIngredient(user_id=owner_id, ingredient_id=ingredient_id))
        if changes.kitchen_equipment is not None:
            db.query(UserEquipment).filter_by(user_id=owner_id).delete(synchronize_session=False)
            for equipment_id in changes.kitchen_equipment:
                db.add(UserEquipment(user_id=owner_id, equipment_id=equipment_id))

        db.commit()
        db.refresh(preferences)
        return get_preferences(db, user_id)
    except (PreferencesNotFoundError, PreferencesValidationError):
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise PreferencesDatabaseError("Preference update failed") from exc
