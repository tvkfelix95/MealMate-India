from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.food_data import (
    Ingredient,
    IngredientNutrition,
    NutritionSource,
    Recipe,
    RecipeIngredient,
    RecipeNutrition,
    RecipeVersion,
    CookingStep,
)
from app.validators.food_data import (
    FoodDataValidationError,
    validate_ingredient_nutrition,
    validate_recipe_current_version,
    validate_recipe_for_publication,
    validate_recipe_ingredient_states,
    validate_recipe_nutrition,
)


def ingredient(state: str = "raw") -> Ingredient:
    return Ingredient(
        id=uuid4(), canonical_name="Rice", state=state, default_unit="g", is_active=True
    )


def source() -> NutritionSource:
    return NutritionSource(
        id=uuid4(), publisher="Verified Publisher", reference="source-1", retrieved_at=datetime.now(timezone.utc)
    )


def recipe_graph() -> tuple[Recipe, RecipeVersion, Ingredient, NutritionSource]:
    recipe = Recipe(
        id=uuid4(), slug="rice-dish", title="Rice Dish", cuisine="south_indian", food_preference="vegetarian"
    )
    version = RecipeVersion(
        id=uuid4(), recipe_id=recipe.id, recipe=recipe, version_number=1, description="Cook the rice.",
        preparation_minutes=5, cooking_minutes=20, servings=2, skill_level="beginner"
    )
    recipe.current_version_id = version.id
    recipe.current_version = version
    rice = ingredient()
    version.ingredients = [
        RecipeIngredient(
            recipe_version_id=version.id, recipe_version=version, ingredient_id=rice.id,
            ingredient=rice, quantity=Decimal("100"), unit="g", ingredient_state="raw", display_order=1
        )
    ]
    version.cooking_steps = [
        CookingStep(recipe_version_id=version.id, recipe_version=version, step_number=1, instruction="Cook the rice.")
    ]
    nutrition_source = source()
    version.nutrition = RecipeNutrition(
        recipe_version_id=version.id, recipe_version=version, nutrition_source_id=nutrition_source.id,
        nutrition_source=nutrition_source, serving_size=Decimal("1"), serving_unit="serving",
        calories_kcal=None, protein_g=Decimal("3"), carbohydrate_g=None, fat_g=Decimal("1"),
        calculation_note="Verified source calculation."
    )
    return recipe, version, rice, nutrition_source


def assert_codes(error: FoodDataValidationError, *codes: str) -> None:
    assert {issue.code for issue in error.issues} >= set(codes)


def test_valid_food_data_graph_passes_validation() -> None:
    recipe, version, rice, nutrition_source = recipe_graph()

    validate_recipe_current_version(recipe)
    validate_recipe_ingredient_states(version)
    validate_recipe_nutrition(version.nutrition, version)
    validate_ingredient_nutrition(
        IngredientNutrition(
            id=uuid4(), ingredient_id=rice.id, ingredient=rice, nutrition_source_id=nutrition_source.id,
            nutrition_source=nutrition_source, serving_quantity=Decimal("100"), serving_unit="g",
            calories_kcal=None, protein_g=None, carbohydrate_g=None, fat_g=None
        )
    )
    validate_recipe_for_publication(recipe)


def test_current_version_must_belong_to_recipe() -> None:
    recipe, version, _rice, _source = recipe_graph()
    version.recipe_id = uuid4()

    with pytest.raises(FoodDataValidationError) as error:
        validate_recipe_current_version(recipe)

    assert_codes(error.value, "current_version_mismatch")


def test_recipe_ingredient_state_must_match_ingredient() -> None:
    _recipe, version, _rice, _source = recipe_graph()
    version.ingredients[0].ingredient_state = "cooked"

    with pytest.raises(FoodDataValidationError) as error:
        validate_recipe_ingredient_states(version)

    assert_codes(error.value, "ingredient_state_mismatch")


def test_missing_nutrition_source_is_rejected_and_null_values_remain_null() -> None:
    _recipe, _version, rice, _source = recipe_graph()
    record = IngredientNutrition(
        id=uuid4(), ingredient_id=rice.id, ingredient=rice, serving_quantity=Decimal("100"), serving_unit="g",
        calories_kcal=None, protein_g=None, carbohydrate_g=None, fat_g=None
    )

    with pytest.raises(FoodDataValidationError) as error:
        validate_ingredient_nutrition(record)

    assert_codes(error.value, "nutrition_source_missing")
    assert record.calories_kcal is None
    assert record.protein_g is None
    assert record.carbohydrate_g is None
    assert record.fat_g is None


def test_recipe_nutrition_must_belong_to_exact_version() -> None:
    _recipe, version, _rice, nutrition_source = recipe_graph()
    record = version.nutrition
    record.recipe_version_id = uuid4()

    with pytest.raises(FoodDataValidationError) as error:
        validate_recipe_nutrition(record, version)

    assert_codes(error.value, "recipe_version_mismatch")


def test_publication_validation_reports_missing_required_content() -> None:
    recipe = Recipe(id=uuid4(), slug="draft", title="Draft", cuisine="south_indian", food_preference="vegetarian")
    version = RecipeVersion(
        id=uuid4(), recipe_id=recipe.id, recipe=recipe, version_number=1, description=None,
        preparation_minutes=0, cooking_minutes=0, servings=1, skill_level="beginner"
    )
    recipe.current_version_id = version.id
    recipe.current_version = version

    with pytest.raises(FoodDataValidationError) as error:
        validate_recipe_for_publication(recipe)

    assert_codes(error.value, "description_missing", "ingredients_missing", "steps_missing", "nutrition_missing")
