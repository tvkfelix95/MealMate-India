"""Add Supabase RLS policies for the MVP schema.

Revision ID: 0002_supabase_rls
Revises: 0001_mvp_schema
"""
from typing import Sequence, Union

from alembic import op


revision: str = "0002_supabase_rls"
down_revision: Union[str, Sequence[str], None] = "0001_mvp_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


APPLICATION_TABLES = (
    "profiles",
    "user_preferences",
    "allergens",
    "equipment",
    "ingredients",
    "nutrition_sources",
    "recipes",
    "recipe_versions",
    "user_allergens",
    "user_disliked_ingredients",
    "user_equipment",
    "ingredient_allergens",
    "ingredient_nutrition",
    "recipe_ingredients",
    "cooking_steps",
    "recipe_nutrition",
    "meal_plans",
    "planned_meals",
    "shopping_lists",
    "shopping_list_items",
    "favourites",
)

DIRECT_OWNER_TABLES = (
    "profiles",
    "user_preferences",
    "user_allergens",
    "user_disliked_ingredients",
    "user_equipment",
    "meal_plans",
    "shopping_lists",
    "favourites",
)

SHARED_READ_TABLES = (
    "allergens",
    "equipment",
    "ingredients",
    "nutrition_sources",
    "recipes",
    "recipe_versions",
    "ingredient_allergens",
    "ingredient_nutrition",
    "recipe_ingredients",
    "cooking_steps",
    "recipe_nutrition",
)


def upgrade() -> None:
    for table in APPLICATION_TABLES:
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")

    for table in DIRECT_OWNER_TABLES:
        op.execute(
            f"""CREATE POLICY {table}_owner_all ON public.{table}
FOR ALL TO authenticated
USING (user_id = (SELECT auth.uid()))
WITH CHECK (user_id = (SELECT auth.uid()))"""
        )

    op.execute(
        """CREATE POLICY planned_meals_owner_all ON public.planned_meals
FOR ALL TO authenticated
USING (EXISTS (
    SELECT 1 FROM public.meal_plans
    WHERE meal_plans.id = planned_meals.meal_plan_id
      AND meal_plans.user_id = (SELECT auth.uid())
))
WITH CHECK (EXISTS (
    SELECT 1 FROM public.meal_plans
    WHERE meal_plans.id = planned_meals.meal_plan_id
      AND meal_plans.user_id = (SELECT auth.uid())
))"""
    )
    op.execute(
        """CREATE POLICY shopping_list_items_owner_all ON public.shopping_list_items
FOR ALL TO authenticated
USING (EXISTS (
    SELECT 1 FROM public.shopping_lists
    WHERE shopping_lists.id = shopping_list_items.shopping_list_id
      AND shopping_lists.user_id = (SELECT auth.uid())
))
WITH CHECK (EXISTS (
    SELECT 1 FROM public.shopping_lists
    WHERE shopping_lists.id = shopping_list_items.shopping_list_id
      AND shopping_lists.user_id = (SELECT auth.uid())
))"""
    )

    for table in SHARED_READ_TABLES:
        op.execute(
            f"""CREATE POLICY {table}_authenticated_read ON public.{table}
FOR SELECT TO authenticated
USING (true)"""
        )


def downgrade() -> None:
    for table in SHARED_READ_TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_authenticated_read ON public.{table}")

    op.execute("DROP POLICY IF EXISTS shopping_list_items_owner_all ON public.shopping_list_items")
    op.execute("DROP POLICY IF EXISTS planned_meals_owner_all ON public.planned_meals")

    for table in DIRECT_OWNER_TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_owner_all ON public.{table}")

    for table in reversed(APPLICATION_TABLES):
        op.execute(f"ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY")
