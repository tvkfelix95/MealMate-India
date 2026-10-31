from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


FoodPreference = Literal["vegetarian", "egg", "non_vegetarian"]
SkillLevel = Literal["beginner", "intermediate", "experienced"]


def unique_ids(value: list[UUID] | None) -> list[UUID] | None:
    if value is not None and len(value) != len(set(value)):
        raise ValueError("Duplicate preference entries are not allowed")
    return value


class PreferencesUpdate(BaseModel):
    food_preference: FoodPreference
    daily_budget_inr: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    skill_level: SkillLevel
    available_minutes: int = Field(gt=0, le=1440)
    preferred_cuisines: list[str] = Field(min_length=1, max_length=1)
    allergies: list[UUID] | None = None
    disliked_ingredients: list[UUID] | None = None
    kitchen_equipment: list[UUID] | None = None

    @field_validator("preferred_cuisines")
    @classmethod
    def validate_cuisines(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip().lower() for item in value]
        if any(not item for item in cleaned) or len(set(cleaned)) != len(cleaned):
            raise ValueError("Preferred cuisines must be unique and non-empty")
        return cleaned

    _unique_allergies = field_validator("allergies")(unique_ids)
    _unique_disliked = field_validator("disliked_ingredients")(unique_ids)
    _unique_equipment = field_validator("kitchen_equipment")(unique_ids)


class PreferencesResponse(BaseModel):
    food_preference: FoodPreference
    daily_budget_inr: Decimal
    skill_level: SkillLevel
    available_minutes: int
    preferred_cuisines: list[str]
    allergies: list[UUID]
    disliked_ingredients: list[UUID]
    kitchen_equipment: list[UUID]
