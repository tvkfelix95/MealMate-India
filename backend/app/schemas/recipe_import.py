"""Pydantic validation models for the MealMate recipe import format."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ImportModel(BaseModel):
    """Base model that rejects fields not defined by the import contract."""

    model_config = ConfigDict(extra="forbid")


def _required_text(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("must not be blank")
    return value


class NutritionSourceImport(ImportModel):
    id: UUID
    publisher: str
    reference: str
    retrieved_at: datetime
    notes: str | None = None

    _publisher_not_blank = field_validator("publisher", "reference")(  # type: ignore[misc]
        _required_text
    )


class RecipeImportNutrition(ImportModel):
    recipe_version_id: UUID
    serving_size: Decimal = Field(gt=0, max_digits=10, decimal_places=3)
    serving_unit: str
    calories_kcal: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=3)
    protein_g: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=3)
    carbohydrate_g: Decimal | None = Field(
        default=None, ge=0, max_digits=10, decimal_places=3
    )
    fat_g: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=3)
    calculation_note: str
    calculated_at: datetime
    source: NutritionSourceImport | None

    _text_not_blank = field_validator("serving_unit", "calculation_note")(  # type: ignore[misc]
        _required_text
    )


class RecipeImportIngredient(ImportModel):
    ingredient_id: UUID
    canonical_name: str
    state: Literal["raw", "cooked"]
    default_unit: str
    quantity: Decimal = Field(gt=0, max_digits=10, decimal_places=3)
    unit: str
    ingredient_state: Literal["raw", "cooked"]
    display_order: int = Field(gt=0)

    _text_not_blank = field_validator("canonical_name", "default_unit", "unit")(  # type: ignore[misc]
        _required_text
    )

    @model_validator(mode="after")
    def state_matches_ingredient(self) -> "RecipeImportIngredient":
        if self.state != self.ingredient_state:
            raise ValueError("state and ingredient_state must match")
        return self


class RecipeImportStep(ImportModel):
    step_number: int = Field(gt=0)
    instruction: str
    duration_minutes: int | None = Field(default=None, ge=0)

    _instruction_not_blank = field_validator("instruction")(_required_text)  # type: ignore[misc]


class AllergenImportItem(ImportModel):
    allergen_id: UUID
    name: str
    source_note: str
    data_status: Literal["illustrative", "verified"]

    _text_not_blank = field_validator("name", "source_note")(  # type: ignore[misc]
        _required_text
    )


class RecipeImportAllergenInfo(ImportModel):
    derived_from_ingredient_mappings: bool
    items: list[AllergenImportItem]

    @model_validator(mode="after")
    def unique_allergens(self) -> "RecipeImportAllergenInfo":
        ids = [item.allergen_id for item in self.items]
        names = [item.name.casefold() for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("allergen items must have unique allergen_id values")
        if len(names) != len(set(names)):
            raise ValueError("allergen items must have unique names")
        return self


class RecipeImportVersion(ImportModel):
    id: UUID
    version_number: int = Field(gt=0)
    description: str | None = None
    preparation_minutes: int = Field(ge=0)
    cooking_minutes: int = Field(ge=0)
    servings: Decimal = Field(gt=0, max_digits=10, decimal_places=3)
    skill_level: Literal["beginner", "intermediate", "experienced"]
    published_at: datetime | None = None
    ingredients: list[RecipeImportIngredient]
    steps: list[RecipeImportStep]
    nutrition: RecipeImportNutrition | None

    @field_validator("description")
    @classmethod
    def blank_description_is_null(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def validate_ordering(self) -> "RecipeImportVersion":
        ingredient_orders = [item.display_order for item in self.ingredients]
        step_orders = [item.step_number for item in self.steps]
        for values, label in (
            (ingredient_orders, "ingredient display_order"),
            (step_orders, "step_number"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} values must be unique")
            if values and values != list(range(1, len(values) + 1)):
                raise ValueError(f"{label} values must be consecutive starting at 1")
        return self


class RecipeImportRecipe(ImportModel):
    id: UUID
    slug: str
    title: str
    cuisine: str
    food_preference: Literal["vegetarian", "egg", "non_vegetarian"]
    is_active: bool
    current_version_id: UUID
    publication_status: Literal["draft", "ready", "published"]
    version: RecipeImportVersion
    allergen_info: RecipeImportAllergenInfo

    _text_not_blank = field_validator("slug", "title", "cuisine")(  # type: ignore[misc]
        _required_text
    )

    @model_validator(mode="after")
    def validate_publication(self) -> "RecipeImportRecipe":
        if self.current_version_id != self.version.id:
            raise ValueError("current_version_id must match version.id")

        status = self.publication_status
        if status == "published" and self.version.published_at is None:
            raise ValueError("published recipes require version.published_at")
        if status != "published" and self.version.published_at is not None:
            raise ValueError("version.published_at is only allowed for published recipes")
        if status == "published" and not self.is_active:
            raise ValueError("published recipes must be active")

        if status in {"ready", "published"}:
            if not self.version.description:
                raise ValueError("publication requires a non-empty version.description")
            if not self.version.ingredients:
                raise ValueError("publication requires at least one ingredient")
            if not self.version.steps:
                raise ValueError("publication requires at least one cooking step")
            if self.version.nutrition is None:
                raise ValueError("publication requires nutrition provenance")
            if self.version.nutrition.source is None:
                raise ValueError("publication requires a nutrition source")
            if any(item.data_status != "verified" for item in self.allergen_info.items):
                raise ValueError("publication requires verified allergen data")

        return self


class RecipeImport(ImportModel):
    format_version: Literal["1.0"]
    data_status: Literal["illustrative", "verified"]
    recipe: RecipeImportRecipe

    @model_validator(mode="after")
    def validate_data_status(self) -> "RecipeImport":
        if self.data_status == "illustrative" and self.recipe.publication_status != "draft":
            raise ValueError("illustrative data may only have draft publication_status")
        if self.data_status == "verified":
            nutrition = self.recipe.version.nutrition
            if nutrition is None or nutrition.source is None:
                raise ValueError("verified data requires a nutrition source")
        return self


__all__ = [
    "AllergenImportItem",
    "NutritionSourceImport",
    "RecipeImport",
    "RecipeImportAllergenInfo",
    "RecipeImportIngredient",
    "RecipeImportNutrition",
    "RecipeImportRecipe",
    "RecipeImportStep",
    "RecipeImportVersion",
]
