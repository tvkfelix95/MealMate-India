"""Validation rules for trusted recipe and nutrition data.

These checks operate on SQLAlchemy objects already loaded by the caller. They
do not create tables, query the database, or change model state.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from app.models.food_data import (
    IngredientNutrition,
    Recipe,
    RecipeIngredient,
    RecipeNutrition,
    RecipeVersion,
)


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    message: str


class FoodDataValidationError(ValueError):
    """Raised when food data cannot safely be used or published."""

    def __init__(self, issues: Iterable[ValidationIssue]) -> None:
        self.issues = tuple(issues)
        super().__init__("; ".join(f"{issue.path}: {issue.message}" for issue in self.issues))


def _raise_if_invalid(issues: list[ValidationIssue]) -> None:
    if issues:
        raise FoodDataValidationError(issues)


def _recipe_current_version_issues(recipe: Recipe) -> list[ValidationIssue]:
    version = recipe.current_version
    if recipe.current_version_id is not None and version is None:
        return [
            ValidationIssue(
                "current_version_missing",
                "current_version_id",
                "Load the referenced current recipe version before validation.",
            )
        ]
    if version is not None and (version.recipe_id != recipe.id or version.recipe is not recipe):
        return [
            ValidationIssue(
                "current_version_mismatch",
                "current_version_id",
                "The current version must belong to the same recipe.",
            )
        ]
    return []


def validate_recipe_current_version(recipe: Recipe) -> None:
    """Ensure a selected current version belongs to its recipe."""
    _raise_if_invalid(_recipe_current_version_issues(recipe))


def _recipe_ingredient_issues(ingredient: RecipeIngredient, index: int) -> list[ValidationIssue]:
    path = f"ingredients[{index}]"
    if ingredient.ingredient is None:
        return [
            ValidationIssue(
                "ingredient_reference_missing",
                path,
                "Load the referenced ingredient before validating its raw/cooked state.",
            )
        ]
    issues: list[ValidationIssue] = []
    if ingredient.ingredient_id != ingredient.ingredient.id:
        issues.append(
            ValidationIssue("ingredient_mismatch", path, "The ingredient relationship does not match ingredient_id.")
        )
    if ingredient.ingredient_state != ingredient.ingredient.state:
        issues.append(
            ValidationIssue(
                "ingredient_state_mismatch",
                path + ".ingredient_state",
                "Use the same raw/cooked state as the referenced ingredient.",
            )
        )
    return issues


def validate_recipe_ingredient_states(recipe_version: RecipeVersion) -> None:
    """Ensure every recipe ingredient uses the referenced ingredient state."""
    issues = [
        issue
        for index, ingredient in enumerate(recipe_version.ingredients)
        for issue in _recipe_ingredient_issues(ingredient, index)
    ]
    _raise_if_invalid(issues)


def _nutrition_value_issues(record: IngredientNutrition | RecipeNutrition) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for field_name in ("calories_kcal", "protein_g", "carbohydrate_g", "fat_g"):
        value: Decimal | None = getattr(record, field_name)
        if value is not None and value < 0:
            issues.append(
                ValidationIssue(
                    "negative_nutrition",
                    field_name,
                    "Use a non-negative value or leave the value NULL when it is unknown.",
                )
            )
    return issues


def _ingredient_nutrition_issues(record: IngredientNutrition) -> list[ValidationIssue]:
    issues = _nutrition_value_issues(record)
    if record.nutrition_source_id is None or record.nutrition_source is None:
        issues.append(
            ValidationIssue(
                "nutrition_source_missing",
                "nutrition_source_id",
                "Attach a verified nutrition source before publishing this record.",
            )
        )
    elif record.nutrition_source.id != record.nutrition_source_id:
        issues.append(
            ValidationIssue(
                "nutrition_source_mismatch",
                "nutrition_source_id",
                "The nutrition source relationship does not match nutrition_source_id.",
            )
        )
    return issues


def validate_ingredient_nutrition(record: IngredientNutrition) -> None:
    """Validate source provenance without changing nullable nutrient values."""
    _raise_if_invalid(_ingredient_nutrition_issues(record))


def _recipe_nutrition_issues(record: RecipeNutrition, version: RecipeVersion | None = None) -> list[ValidationIssue]:
    issues = _nutrition_value_issues(record)
    if record.nutrition_source_id is None or record.nutrition_source is None:
        issues.append(
            ValidationIssue(
                "nutrition_source_missing",
                "nutrition_source_id",
                "Attach a verified nutrition source before publishing this record.",
            )
        )
    elif record.nutrition_source.id != record.nutrition_source_id:
        issues.append(
            ValidationIssue(
                "nutrition_source_mismatch",
                "nutrition_source_id",
                "The nutrition source relationship does not match nutrition_source_id.",
            )
        )
    if version is not None:
        if record.recipe_version is None or record.recipe_version_id != version.id or record.recipe_version is not version:
            issues.append(
                ValidationIssue(
                    "recipe_version_mismatch",
                    "recipe_version_id",
                    "Recipe nutrition must belong to the recipe version being published.",
                )
            )
    return issues


def validate_recipe_nutrition(record: RecipeNutrition, version: RecipeVersion) -> None:
    """Ensure recipe nutrition belongs to the exact recipe version."""
    _raise_if_invalid(_recipe_nutrition_issues(record, version))


def validate_recipe_for_publication(recipe: Recipe) -> None:
    """Validate all required content before marking a recipe publishable."""
    issues = _recipe_current_version_issues(recipe)
    if not recipe.slug.strip():
        issues.append(ValidationIssue("recipe_slug_missing", "slug", "Provide a non-empty recipe slug."))
    if not recipe.title.strip():
        issues.append(ValidationIssue("recipe_title_missing", "title", "Provide a non-empty recipe title."))
    if not recipe.cuisine.strip():
        issues.append(ValidationIssue("recipe_cuisine_missing", "cuisine", "Provide a cuisine."))

    version = recipe.current_version
    if version is None:
        issues.append(ValidationIssue("recipe_version_missing", "current_version_id", "Select a current recipe version."))
        _raise_if_invalid(issues)
        return
    if not version.description or not version.description.strip():
        issues.append(ValidationIssue("description_missing", "current_version.description", "Provide recipe instructions or a description."))
    if not version.ingredients:
        issues.append(ValidationIssue("ingredients_missing", "current_version.ingredients", "Add at least one recipe ingredient."))
    else:
        for index, ingredient in enumerate(version.ingredients):
            issues.extend(_recipe_ingredient_issues(ingredient, index))
            if ingredient.quantity is None or ingredient.quantity <= 0:
                issues.append(ValidationIssue("ingredient_quantity_invalid", f"ingredients[{index}].quantity", "Use a quantity greater than zero."))
            if not ingredient.unit.strip():
                issues.append(ValidationIssue("ingredient_unit_missing", f"ingredients[{index}].unit", "Provide an ingredient unit."))
    if not version.cooking_steps:
        issues.append(ValidationIssue("steps_missing", "current_version.cooking_steps", "Add at least one cooking step."))
    else:
        for index, step in enumerate(version.cooking_steps):
            if not step.instruction.strip():
                issues.append(ValidationIssue("step_instruction_missing", f"cooking_steps[{index}].instruction", "Provide step instructions."))
    if version.nutrition is None:
        issues.append(ValidationIssue("nutrition_missing", "current_version.nutrition", "Add nutrition with a verified source."))
    else:
        issues.extend(_recipe_nutrition_issues(version.nutrition, version))

    _raise_if_invalid(issues)
