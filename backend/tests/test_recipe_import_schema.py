import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.recipe_import import RecipeImport


FIXTURE = Path(__file__).parent / "fixtures" / "sample_recipe.json"


@pytest.fixture
def sample_recipe() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_illustrative_sample_is_a_valid_draft(sample_recipe: dict) -> None:
    imported = RecipeImport.model_validate(sample_recipe)

    assert imported.recipe.publication_status == "draft"
    assert imported.recipe.version.nutrition is not None
    assert imported.recipe.version.nutrition.calories_kcal is None


def test_unsupported_fields_are_rejected(sample_recipe: dict) -> None:
    sample_recipe["unexpected"] = True

    with pytest.raises(ValidationError, match="unexpected"):
        RecipeImport.model_validate(sample_recipe)


def test_invalid_enum_is_rejected(sample_recipe: dict) -> None:
    sample_recipe["recipe"]["food_preference"] = "vegan"

    with pytest.raises(ValidationError, match="food_preference"):
        RecipeImport.model_validate(sample_recipe)


def test_ingredient_order_must_be_unique_and_consecutive(sample_recipe: dict) -> None:
    sample_recipe["recipe"]["version"]["ingredients"][1]["display_order"] = 1

    with pytest.raises(ValidationError, match="display_order"):
        RecipeImport.model_validate(sample_recipe)


def test_step_order_must_be_unique_and_consecutive(sample_recipe: dict) -> None:
    sample_recipe["recipe"]["version"]["steps"][1]["step_number"] = 3

    with pytest.raises(ValidationError, match="step_number"):
        RecipeImport.model_validate(sample_recipe)


def test_ingredient_raw_cooked_states_must_match(sample_recipe: dict) -> None:
    sample_recipe["recipe"]["version"]["ingredients"][0]["ingredient_state"] = "cooked"

    with pytest.raises(ValidationError, match="must match"):
        RecipeImport.model_validate(sample_recipe)


def test_recipe_version_must_be_current_version(sample_recipe: dict) -> None:
    sample_recipe["recipe"]["current_version_id"] = "00000000-0000-0000-0000-000000000999"

    with pytest.raises(ValidationError, match="current_version_id"):
        RecipeImport.model_validate(sample_recipe)


def test_illustrative_data_cannot_be_publication_ready(sample_recipe: dict) -> None:
    sample_recipe["recipe"]["publication_status"] = "ready"

    with pytest.raises(ValidationError, match="illustrative"):
        RecipeImport.model_validate(sample_recipe)


def test_verified_data_requires_nutrition_source(sample_recipe: dict) -> None:
    verified = deepcopy(sample_recipe)
    verified["data_status"] = "verified"

    with pytest.raises(ValidationError, match="nutrition source"):
        RecipeImport.model_validate(verified)
