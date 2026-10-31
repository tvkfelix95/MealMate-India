"""Create the approved MealMate India MVP schema.

Revision ID: 0001_mvp_schema
Revises:
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_mvp_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)
NOW = sa.text("now()")
UUID_DEFAULT = sa.text("gen_random_uuid()")


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("user_id", UUID, sa.ForeignKey("auth.users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("display_name", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=NOW, nullable=False),
        sa.CheckConstraint("display_name IS NULL OR length(display_name) <= 120", name="ck_profiles_display_name_length"),
    )
    op.create_table(
        "user_preferences",
        sa.Column("user_id", UUID, sa.ForeignKey("profiles.user_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("food_preference", sa.Text(), nullable=False),
        sa.Column("daily_budget_inr", sa.Numeric(10, 2), nullable=False),
        sa.Column("skill_level", sa.Text(), nullable=False),
        sa.Column("available_minutes", sa.SmallInteger(), nullable=False),
        sa.Column("preferred_cuisine", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=NOW, nullable=False),
        sa.CheckConstraint("food_preference IN ('vegetarian', 'egg', 'non_vegetarian')", name="ck_preferences_food_preference"),
        sa.CheckConstraint("daily_budget_inr >= 0", name="ck_preferences_budget_nonnegative"),
        sa.CheckConstraint("skill_level IN ('beginner', 'intermediate', 'experienced')", name="ck_preferences_skill_level"),
        sa.CheckConstraint("available_minutes > 0", name="ck_preferences_minutes_positive"),
        sa.CheckConstraint("length(preferred_cuisine) > 0", name="ck_preferences_cuisine_present"),
    )
    op.create_index("ix_user_preferences_food_preference", "user_preferences", ["food_preference"])
    op.create_index("ix_user_preferences_preferred_cuisine", "user_preferences", ["preferred_cuisine"])

    op.create_table(
        "allergens",
        sa.Column("id", UUID, server_default=UUID_DEFAULT, primary_key=True),
        sa.Column("name", sa.Text(), nullable=False, unique=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=NOW, nullable=False),
    )
    op.create_table(
        "equipment",
        sa.Column("id", UUID, server_default=UUID_DEFAULT, primary_key=True),
        sa.Column("name", sa.Text(), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.create_table(
        "ingredients",
        sa.Column("id", UUID, server_default=UUID_DEFAULT, primary_key=True),
        sa.Column("canonical_name", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("default_unit", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=NOW, nullable=False),
        sa.UniqueConstraint("canonical_name", "state", name="uq_ingredients_name_state"),
        sa.CheckConstraint("state IN ('raw', 'cooked')", name="ck_ingredients_state"),
    )
    op.create_index("ix_ingredients_canonical_name", "ingredients", ["canonical_name"])

    op.create_table(
        "nutrition_sources",
        sa.Column("id", UUID, server_default=UUID_DEFAULT, primary_key=True),
        sa.Column("publisher", sa.Text(), nullable=False),
        sa.Column("reference", sa.Text(), nullable=False),
        sa.Column("retrieved_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("publisher", "reference", name="uq_nutrition_sources_publisher_reference"),
    )
    op.create_table(
        "recipes",
        sa.Column("id", UUID, server_default=UUID_DEFAULT, primary_key=True),
        sa.Column("slug", sa.Text(), nullable=False, unique=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("cuisine", sa.Text(), nullable=False),
        sa.Column("food_preference", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("current_version_id", UUID, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=NOW, nullable=False),
        sa.CheckConstraint("food_preference IN ('vegetarian', 'egg', 'non_vegetarian')", name="ck_recipes_food_preference"),
    )
    op.create_table(
        "recipe_versions",
        sa.Column("id", UUID, server_default=UUID_DEFAULT, primary_key=True),
        sa.Column("recipe_id", UUID, sa.ForeignKey("recipes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("preparation_minutes", sa.SmallInteger(), nullable=False),
        sa.Column("cooking_minutes", sa.SmallInteger(), nullable=False),
        sa.Column("servings", sa.SmallInteger(), nullable=False),
        sa.Column("skill_level", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=NOW, nullable=False),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.UniqueConstraint("recipe_id", "version_number", name="uq_recipe_versions_recipe_version"),
        sa.CheckConstraint("preparation_minutes >= 0", name="ck_recipe_versions_prep_minutes"),
        sa.CheckConstraint("cooking_minutes >= 0", name="ck_recipe_versions_cooking_minutes"),
        sa.CheckConstraint("servings > 0", name="ck_recipe_versions_servings"),
        sa.CheckConstraint("skill_level IN ('beginner', 'intermediate', 'experienced')", name="ck_recipe_versions_skill_level"),
    )
    op.create_index("ix_recipe_versions_recipe_published", "recipe_versions", ["recipe_id", sa.text("published_at DESC")])
    op.create_foreign_key("fk_recipes_current_version", "recipes", "recipe_versions", ["current_version_id"], ["id"], ondelete="RESTRICT")

    op.create_table(
        "user_allergens",
        sa.Column("user_id", UUID, sa.ForeignKey("profiles.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("allergen_id", UUID, sa.ForeignKey("allergens.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=NOW, nullable=False),
        sa.PrimaryKeyConstraint("user_id", "allergen_id"),
    )
    op.create_index("ix_user_allergens_allergen_id", "user_allergens", ["allergen_id"])
    op.create_table(
        "user_disliked_ingredients",
        sa.Column("user_id", UUID, sa.ForeignKey("profiles.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("ingredient_id", UUID, sa.ForeignKey("ingredients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=NOW, nullable=False),
        sa.PrimaryKeyConstraint("user_id", "ingredient_id"),
    )
    op.create_index("ix_user_disliked_ingredients_ingredient_id", "user_disliked_ingredients", ["ingredient_id"])
    op.create_table(
        "user_equipment",
        sa.Column("user_id", UUID, sa.ForeignKey("profiles.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("equipment_id", UUID, sa.ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=NOW, nullable=False),
        sa.PrimaryKeyConstraint("user_id", "equipment_id"),
    )
    op.create_index("ix_user_equipment_equipment_id", "user_equipment", ["equipment_id"])
    op.create_table(
        "ingredient_allergens",
        sa.Column("ingredient_id", UUID, sa.ForeignKey("ingredients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("allergen_id", UUID, sa.ForeignKey("allergens.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_note", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("ingredient_id", "allergen_id"),
    )
    op.create_index("ix_ingredient_allergens_allergen_id", "ingredient_allergens", ["allergen_id"])

    op.create_table(
        "ingredient_nutrition",
        sa.Column("id", UUID, server_default=UUID_DEFAULT, primary_key=True),
        sa.Column("ingredient_id", UUID, sa.ForeignKey("ingredients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("nutrition_source_id", UUID, sa.ForeignKey("nutrition_sources.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("serving_quantity", sa.Numeric(10, 3), nullable=False),
        sa.Column("serving_unit", sa.Text(), nullable=False),
        sa.Column("calories_kcal", sa.Numeric(10, 3), nullable=True),
        sa.Column("protein_g", sa.Numeric(10, 3), nullable=True),
        sa.Column("carbohydrate_g", sa.Numeric(10, 3), nullable=True),
        sa.Column("fat_g", sa.Numeric(10, 3), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=NOW, nullable=False),
        sa.CheckConstraint("serving_quantity > 0", name="ck_ingredient_nutrition_quantity"),
        sa.CheckConstraint("calories_kcal IS NULL OR calories_kcal >= 0", name="ck_ingredient_nutrition_calories"),
        sa.CheckConstraint("protein_g IS NULL OR protein_g >= 0", name="ck_ingredient_nutrition_protein"),
        sa.CheckConstraint("carbohydrate_g IS NULL OR carbohydrate_g >= 0", name="ck_ingredient_nutrition_carbohydrate"),
        sa.CheckConstraint("fat_g IS NULL OR fat_g >= 0", name="ck_ingredient_nutrition_fat"),
    )
    op.create_index("ix_ingredient_nutrition_ingredient_created", "ingredient_nutrition", ["ingredient_id", sa.text("created_at DESC")])

    op.create_table(
        "recipe_ingredients",
        sa.Column("recipe_version_id", UUID, sa.ForeignKey("recipe_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ingredient_id", UUID, sa.ForeignKey("ingredients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity", sa.Numeric(10, 3), nullable=False),
        sa.Column("unit", sa.Text(), nullable=False),
        sa.Column("ingredient_state", sa.Text(), nullable=False),
        sa.Column("display_order", sa.SmallInteger(), nullable=False),
        sa.PrimaryKeyConstraint("recipe_version_id", "display_order"),
        sa.CheckConstraint("quantity > 0", name="ck_recipe_ingredients_quantity"),
        sa.CheckConstraint("ingredient_state IN ('raw', 'cooked')", name="ck_recipe_ingredients_state"),
        sa.CheckConstraint("display_order > 0", name="ck_recipe_ingredients_display_order"),
    )
    op.create_index("ix_recipe_ingredients_ingredient_id", "recipe_ingredients", ["ingredient_id"])
    op.create_table(
        "cooking_steps",
        sa.Column("recipe_version_id", UUID, sa.ForeignKey("recipe_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_number", sa.SmallInteger(), nullable=False),
        sa.Column("instruction", sa.Text(), nullable=False),
        sa.Column("duration_minutes", sa.SmallInteger(), nullable=True),
        sa.PrimaryKeyConstraint("recipe_version_id", "step_number"),
        sa.CheckConstraint("step_number > 0", name="ck_cooking_steps_number"),
        sa.CheckConstraint("duration_minutes IS NULL OR duration_minutes >= 0", name="ck_cooking_steps_duration"),
    )
    op.create_table(
        "recipe_nutrition",
        sa.Column("recipe_version_id", UUID, sa.ForeignKey("recipe_versions.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("nutrition_source_id", UUID, sa.ForeignKey("nutrition_sources.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("serving_size", sa.Numeric(10, 3), nullable=False),
        sa.Column("serving_unit", sa.Text(), nullable=False),
        sa.Column("calories_kcal", sa.Numeric(10, 3), nullable=True),
        sa.Column("protein_g", sa.Numeric(10, 3), nullable=True),
        sa.Column("carbohydrate_g", sa.Numeric(10, 3), nullable=True),
        sa.Column("fat_g", sa.Numeric(10, 3), nullable=True),
        sa.Column("calculation_note", sa.Text(), nullable=False),
        sa.Column("calculated_at", sa.TIMESTAMP(timezone=True), server_default=NOW, nullable=False),
        sa.CheckConstraint("serving_size > 0", name="ck_recipe_nutrition_serving_size"),
        sa.CheckConstraint("calories_kcal IS NULL OR calories_kcal >= 0", name="ck_recipe_nutrition_calories"),
        sa.CheckConstraint("protein_g IS NULL OR protein_g >= 0", name="ck_recipe_nutrition_protein"),
        sa.CheckConstraint("carbohydrate_g IS NULL OR carbohydrate_g >= 0", name="ck_recipe_nutrition_carbohydrate"),
        sa.CheckConstraint("fat_g IS NULL OR fat_g >= 0", name="ck_recipe_nutrition_fat"),
    )
    op.create_index("ix_recipe_nutrition_source_id", "recipe_nutrition", ["nutrition_source_id"])

    op.create_table(
        "meal_plans",
        sa.Column("id", UUID, server_default=UUID_DEFAULT, primary_key=True),
        sa.Column("user_id", UUID, sa.ForeignKey("profiles.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_type", sa.Text(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("budget_snapshot_inr", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=NOW, nullable=False),
        sa.CheckConstraint("plan_type IN ('daily', 'weekly')", name="ck_meal_plans_type"),
        sa.CheckConstraint("end_date >= start_date", name="ck_meal_plans_date_range"),
        sa.CheckConstraint("plan_type <> 'daily' OR end_date = start_date", name="ck_meal_plans_daily_date_range"),
        sa.CheckConstraint("plan_type <> 'weekly' OR end_date <= start_date + 6", name="ck_meal_plans_weekly_date_range"),
        sa.CheckConstraint("budget_snapshot_inr >= 0", name="ck_meal_plans_budget"),
    )
    op.create_index("ix_meal_plans_user_start_date", "meal_plans", ["user_id", sa.text("start_date DESC")])
    op.create_table(
        "planned_meals",
        sa.Column("id", UUID, server_default=UUID_DEFAULT, primary_key=True),
        sa.Column("meal_plan_id", UUID, sa.ForeignKey("meal_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("meal_date", sa.Date(), nullable=False),
        sa.Column("meal_slot", sa.Text(), nullable=False),
        sa.Column("recipe_version_id", UUID, sa.ForeignKey("recipe_versions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("servings", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=NOW, nullable=False),
        sa.UniqueConstraint("meal_plan_id", "meal_date", "meal_slot", name="uq_planned_meals_plan_date_slot"),
        sa.CheckConstraint("meal_slot IN ('breakfast', 'morning_snack', 'lunch', 'evening_snack', 'dinner')", name="ck_planned_meals_slot"),
        sa.CheckConstraint("servings > 0", name="ck_planned_meals_servings"),
    )
    op.create_index("ix_planned_meals_plan_date", "planned_meals", ["meal_plan_id", "meal_date"])

    op.create_table(
        "shopping_lists",
        sa.Column("id", UUID, server_default=UUID_DEFAULT, primary_key=True),
        sa.Column("user_id", UUID, sa.ForeignKey("profiles.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("meal_plan_id", UUID, sa.ForeignKey("meal_plans.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=NOW, nullable=False),
    )
    op.create_index("ix_shopping_lists_user_created", "shopping_lists", ["user_id", sa.text("created_at DESC")])
    op.create_table(
        "shopping_list_items",
        sa.Column("id", UUID, server_default=UUID_DEFAULT, primary_key=True),
        sa.Column("shopping_list_id", UUID, sa.ForeignKey("shopping_lists.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ingredient_id", UUID, sa.ForeignKey("ingredients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity", sa.Numeric(10, 3), nullable=False),
        sa.Column("unit", sa.Text(), nullable=False),
        sa.Column("ingredient_state", sa.Text(), nullable=False),
        sa.Column("is_checked", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=NOW, nullable=False),
        sa.UniqueConstraint("shopping_list_id", "ingredient_id", "unit", "ingredient_state", name="uq_shopping_items_ingredient_unit_state"),
        sa.CheckConstraint("quantity > 0", name="ck_shopping_items_quantity"),
        sa.CheckConstraint("ingredient_state IN ('raw', 'cooked')", name="ck_shopping_items_state"),
    )
    op.create_index("ix_shopping_list_items_list_id", "shopping_list_items", ["shopping_list_id"])
    op.create_table(
        "favourites",
        sa.Column("user_id", UUID, sa.ForeignKey("profiles.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("recipe_version_id", UUID, sa.ForeignKey("recipe_versions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=NOW, nullable=False),
        sa.PrimaryKeyConstraint("user_id", "recipe_version_id"),
    )
    op.create_index("ix_favourites_recipe_version_id", "favourites", ["recipe_version_id"])


def downgrade() -> None:
    op.drop_index("ix_favourites_recipe_version_id", table_name="favourites")
    op.drop_table("favourites")
    op.drop_index("ix_shopping_list_items_list_id", table_name="shopping_list_items")
    op.drop_table("shopping_list_items")
    op.drop_index("ix_shopping_lists_user_created", table_name="shopping_lists")
    op.drop_table("shopping_lists")
    op.drop_index("ix_planned_meals_plan_date", table_name="planned_meals")
    op.drop_table("planned_meals")
    op.drop_index("ix_meal_plans_user_start_date", table_name="meal_plans")
    op.drop_constraint("ck_meal_plans_weekly_date_range", "meal_plans", type_="check")
    op.drop_constraint("ck_meal_plans_daily_date_range", "meal_plans", type_="check")
    op.drop_constraint("ck_meal_plans_date_range", "meal_plans", type_="check")
    op.drop_table("meal_plans")
    op.drop_index("ix_recipe_nutrition_source_id", table_name="recipe_nutrition")
    op.drop_table("recipe_nutrition")
    op.drop_table("cooking_steps")
    op.drop_index("ix_recipe_ingredients_ingredient_id", table_name="recipe_ingredients")
    op.drop_table("recipe_ingredients")
    op.drop_index("ix_ingredient_nutrition_ingredient_created", table_name="ingredient_nutrition")
    op.drop_table("ingredient_nutrition")
    op.drop_index("ix_ingredient_allergens_allergen_id", table_name="ingredient_allergens")
    op.drop_table("ingredient_allergens")
    op.drop_index("ix_user_equipment_equipment_id", table_name="user_equipment")
    op.drop_table("user_equipment")
    op.drop_index("ix_user_disliked_ingredients_ingredient_id", table_name="user_disliked_ingredients")
    op.drop_table("user_disliked_ingredients")
    op.drop_index("ix_user_allergens_allergen_id", table_name="user_allergens")
    op.drop_table("user_allergens")
    op.drop_constraint("fk_recipes_current_version", "recipes", type_="foreignkey")
    op.drop_index("ix_recipe_versions_recipe_published", table_name="recipe_versions")
    op.drop_table("recipe_versions")
    op.drop_table("recipes")
    op.drop_table("nutrition_sources")
    op.drop_index("ix_ingredients_canonical_name", table_name="ingredients")
    op.drop_table("ingredients")
    op.drop_table("equipment")
    op.drop_table("allergens")
    op.drop_index("ix_user_preferences_preferred_cuisine", table_name="user_preferences")
    op.drop_index("ix_user_preferences_food_preference", table_name="user_preferences")
    op.drop_table("user_preferences")
    op.drop_table("profiles")
