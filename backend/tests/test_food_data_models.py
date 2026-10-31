from sqlalchemy import inspect

from app.models.base import Base
from app.models.food_data import (
    IngredientNutrition,
    NutritionSource,
    Recipe,
    RecipeIngredient,
    RecipeNutrition,
    RecipeVersion,
)
from app.models.preferences import Allergen, Ingredient


def test_food_data_tables_and_columns_match_schema() -> None:
    expected = {
        "allergens",
        "ingredients",
        "nutrition_sources",
        "ingredient_nutrition",
        "recipes",
        "recipe_versions",
        "recipe_ingredients",
        "cooking_steps",
        "recipe_nutrition",
    }

    assert expected <= set(Base.metadata.tables)
    assert {column.name for column in Allergen.__table__.columns} == {"id", "name", "created_at"}
    assert {column.name for column in Ingredient.__table__.columns} == {
        "id", "canonical_name", "state", "default_unit", "is_active", "created_at", "updated_at"
    }
    assert {column.name for column in NutritionSource.__table__.columns} == {
        "id", "publisher", "reference", "retrieved_at", "notes"
    }
    assert {column.name for column in RecipeVersion.__table__.columns} == {
        "id", "recipe_id", "version_number", "description", "preparation_minutes",
        "cooking_minutes", "servings", "skill_level", "created_at", "published_at",
    }


def test_foreign_keys_and_delete_actions_match_migration() -> None:
    ingredient_nutrition_fks = {
        (fk.column.table.name, fk.parent.name, fk.ondelete)
        for fk in IngredientNutrition.__table__.foreign_keys
    }
    assert ("ingredients", "ingredient_id", "RESTRICT") in ingredient_nutrition_fks
    assert ("nutrition_sources", "nutrition_source_id", "RESTRICT") in ingredient_nutrition_fks

    recipe_ingredient_fks = {
        (fk.column.table.name, fk.parent.name, fk.ondelete)
        for fk in RecipeIngredient.__table__.foreign_keys
    }
    assert ("recipe_versions", "recipe_version_id", "CASCADE") in recipe_ingredient_fks
    assert ("ingredients", "ingredient_id", "RESTRICT") in recipe_ingredient_fks

    assert any(fk.column.table.name == "recipes" and fk.ondelete == "RESTRICT" for fk in RecipeVersion.__table__.foreign_keys)
    assert any(fk.column.table.name == "recipe_versions" and fk.ondelete == "CASCADE" for fk in RecipeNutrition.__table__.foreign_keys)


def test_nutrition_values_are_nullable_and_source_provenance_is_required() -> None:
    for model in (IngredientNutrition, RecipeNutrition):
        columns = model.__table__.c
        assert columns.calories_kcal.nullable is True
        assert columns.protein_g.nullable is True
        assert columns.carbohydrate_g.nullable is True
        assert columns.fat_g.nullable is True
        assert columns.nutrition_source_id.nullable is False


def test_constraints_indexes_and_relationships_are_present() -> None:
    assert "uq_ingredients_name_state" in {constraint.name for constraint in Ingredient.__table__.constraints}
    assert "uq_recipe_versions_recipe_version" in {constraint.name for constraint in RecipeVersion.__table__.constraints}
    assert "ix_ingredient_nutrition_ingredient_created" in {index.name for index in IngredientNutrition.__table__.indexes}
    assert "ix_recipe_versions_recipe_published" in {index.name for index in RecipeVersion.__table__.indexes}
    assert "ix_recipe_ingredients_ingredient_id" in {index.name for index in RecipeIngredient.__table__.indexes}

    assert {"versions", "current_version"} <= set(inspect(Recipe).relationships.keys())
    assert {"recipe", "ingredients", "cooking_steps", "nutrition"} <= set(inspect(RecipeVersion).relationships.keys())
    assert {"ingredient", "nutrition_source"} <= set(inspect(IngredientNutrition).relationships.keys())
