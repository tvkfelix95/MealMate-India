"""Transactional persistence for validated recipe import documents."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.food_data import (
    Allergen,
    Ingredient,
    IngredientAllergen,
    NutritionSource,
    Recipe,
    RecipeIngredient,
    RecipeNutrition,
    RecipeVersion,
    CookingStep,
)
from app.schemas.recipe_import import RecipeImport
from app.validators.food_data import (
    validate_recipe_current_version,
    validate_recipe_for_publication,
    validate_recipe_ingredient_states,
    validate_recipe_nutrition,
)


class RecipeImportError(ValueError):
    """Base error for a recipe import that cannot be safely persisted."""


class RecipeImportConflictError(RecipeImportError):
    """Raised when supplied identifiers conflict with existing catalogue data."""


class RecipeImportDatabaseError(RecipeImportError):
    """Raised for safe, sanitised persistence failures."""


ModelT = TypeVar("ModelT")


def _one_by_fields(db: Session, model: type[ModelT], **fields: object) -> ModelT | None:
    return db.query(model).filter_by(**fields).one_or_none()


def _resolve_ingredient(db: Session, item) -> Ingredient:
    existing = db.get(Ingredient, item.ingredient_id)
    if existing is not None:
        if (
            existing.canonical_name != item.canonical_name
            or existing.state != item.state
            or existing.default_unit != item.default_unit
        ):
            raise RecipeImportConflictError(
                f"Ingredient {item.ingredient_id} conflicts with the existing catalogue record"
            )
        return existing

    by_name = _one_by_fields(
        db,
        Ingredient,
        canonical_name=item.canonical_name,
        state=item.state,
    )
    if by_name is not None:
        raise RecipeImportConflictError(
            f"Ingredient {item.canonical_name!r} with state {item.state!r} already has another identifier"
        )

    ingredient = Ingredient(
        id=item.ingredient_id,
        canonical_name=item.canonical_name,
        state=item.state,
        default_unit=item.default_unit,
        is_active=True,
    )
    db.add(ingredient)
    return ingredient


def _resolve_allergens(db: Session, items: Iterable[object]) -> dict[object, Allergen]:
    resolved: dict[object, Allergen] = {}
    for item in items:
        existing = db.get(Allergen, item.allergen_id)
        if existing is not None:
            if existing.name.casefold() != item.name.casefold():
                raise RecipeImportConflictError(
                    f"Allergen {item.allergen_id} conflicts with the existing catalogue record"
                )
            resolved[item.allergen_id] = existing
            continue

        by_name = _one_by_fields(db, Allergen, name=item.name)
        if by_name is not None:
            raise RecipeImportConflictError(
                f"Allergen {item.name!r} already has another identifier"
            )

        allergen = Allergen(id=item.allergen_id, name=item.name)
        db.add(allergen)
        resolved[item.allergen_id] = allergen
    return resolved


def _resolve_source(db: Session, source) -> NutritionSource:
    existing = db.get(NutritionSource, source.id)
    if existing is not None:
        if existing.publisher != source.publisher or existing.reference != source.reference:
            raise RecipeImportConflictError(
                f"Nutrition source {source.id} conflicts with the existing provenance record"
            )
        return existing

    by_reference = _one_by_fields(
        db,
        NutritionSource,
        publisher=source.publisher,
        reference=source.reference,
    )
    if by_reference is not None:
        if by_reference.id != source.id:
            raise RecipeImportConflictError("Nutrition source has a conflicting identifier")
        return by_reference

    nutrition_source = NutritionSource(
        id=source.id,
        publisher=source.publisher,
        reference=source.reference,
        retrieved_at=source.retrieved_at,
        notes=source.notes,
    )
    db.add(nutrition_source)
    return nutrition_source


def _validate_allergen_mappings(db: Session, recipe_version: RecipeVersion, allergen_ids: set[object]) -> None:
    ingredient_ids = {item.ingredient_id for item in recipe_version.ingredients}
    for allergen_id in allergen_ids:
        mapping_exists = False
        for ingredient_id in ingredient_ids:
            mapping = _one_by_fields(
                db,
                IngredientAllergen,
                ingredient_id=ingredient_id,
                allergen_id=allergen_id,
            )
            if mapping is not None:
                mapping_exists = True
                break
        if not mapping_exists:
            raise RecipeImportError(
                f"Allergen {allergen_id} is not mapped to an ingredient in the recipe"
            )


def import_recipe(db: Session, document: RecipeImport) -> Recipe:
    """Persist one validated import atomically and return its recipe.

    The caller supplies an already validated :class:`RecipeImport`. This
    function does not publish illustrative data and never updates an existing
    recipe or version.
    """

    recipe_data = document.recipe
    try:
        if db.get(Recipe, recipe_data.id) is not None:
            raise RecipeImportConflictError("Recipe identifier already exists")
        if _one_by_fields(db, Recipe, slug=recipe_data.slug) is not None:
            raise RecipeImportConflictError("Recipe slug already exists")
        if db.get(RecipeVersion, recipe_data.version.id) is not None:
            raise RecipeImportConflictError("Recipe version identifier already exists")

        # Resolve shared catalogue data before creating immutable recipe rows.
        ingredients = {
            item.ingredient_id: _resolve_ingredient(db, item)
            for item in recipe_data.version.ingredients
        }
        _resolve_allergens(db, recipe_data.allergen_info.items)

        recipe = Recipe(
            id=recipe_data.id,
            slug=recipe_data.slug,
            title=recipe_data.title,
            cuisine=recipe_data.cuisine,
            food_preference=recipe_data.food_preference,
            is_active=recipe_data.is_active and recipe_data.publication_status == "published",
        )
        version = RecipeVersion(
            id=recipe_data.version.id,
            recipe_id=recipe.id,
            recipe=recipe,
            version_number=recipe_data.version.version_number,
            description=recipe_data.version.description,
            preparation_minutes=recipe_data.version.preparation_minutes,
            cooking_minutes=recipe_data.version.cooking_minutes,
            servings=int(recipe_data.version.servings),
            skill_level=recipe_data.version.skill_level,
            published_at=recipe_data.version.published_at
            if recipe_data.publication_status == "published"
            else None,
        )
        recipe.current_version = version
        recipe.current_version_id = version.id
        db.add(recipe)
        db.add(version)

        recipe_ingredients = [
            RecipeIngredient(
                recipe_version_id=version.id,
                ingredient_id=ingredients[item.ingredient_id].id,
                quantity=item.quantity,
                unit=item.unit,
                ingredient_state=item.ingredient_state,
                display_order=item.display_order,
                ingredient=ingredients[item.ingredient_id],
            )
            for item in recipe_data.version.ingredients
        ]
        for row in recipe_ingredients:
            db.add(row)
        cooking_steps = [
            CookingStep(
                recipe_version_id=version.id,
                step_number=item.step_number,
                instruction=item.instruction,
                duration_minutes=item.duration_minutes,
            )
            for item in recipe_data.version.steps
        ]
        for row in cooking_steps:
            db.add(row)

        nutrition_data = recipe_data.version.nutrition
        if nutrition_data is not None:
            if nutrition_data.recipe_version_id != version.id:
                raise RecipeImportError("Nutrition must reference the imported recipe version")
            if nutrition_data.source is not None:
                source = _resolve_source(db, nutrition_data.source)
                version.nutrition = RecipeNutrition(
                    recipe_version_id=version.id,
                    recipe_version=version,
                    nutrition_source_id=source.id,
                    nutrition_source=source,
                    serving_size=nutrition_data.serving_size,
                    serving_unit=nutrition_data.serving_unit,
                    calories_kcal=nutrition_data.calories_kcal,
                    protein_g=nutrition_data.protein_g,
                    carbohydrate_g=nutrition_data.carbohydrate_g,
                    fat_g=nutrition_data.fat_g,
                    calculation_note=nutrition_data.calculation_note,
                    calculated_at=nutrition_data.calculated_at,
                )
                db.add(version.nutrition)

        # Establish relationships used by the existing application validators.
        version.ingredients = recipe_ingredients
        version.cooking_steps = cooking_steps
        validate_recipe_current_version(recipe)
        validate_recipe_ingredient_states(version)
        if version.nutrition is not None:
            validate_recipe_nutrition(version.nutrition, version)
        if recipe_data.publication_status in {"ready", "published"}:
            _validate_allergen_mappings(
                db,
                version,
                {item.allergen_id for item in recipe_data.allergen_info.items},
            )
            validate_recipe_for_publication(recipe)

        db.flush()
        db.commit()
        return recipe
    except RecipeImportError:
        db.rollback()
        raise
    except (IntegrityError, SQLAlchemyError) as exc:
        db.rollback()
        raise RecipeImportDatabaseError("Recipe import could not be saved") from exc
    except Exception as exc:
        db.rollback()
        raise RecipeImportDatabaseError("Recipe import could not be saved") from exc


__all__ = [
    "RecipeImportConflictError",
    "RecipeImportDatabaseError",
    "RecipeImportError",
    "import_recipe",
]
