from pathlib import Path
import importlib.util


BACKEND_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (BACKEND_ROOT / "alembic" / "versions" / "0002_supabase_rls.py").read_text()


def load_migration():
    spec = importlib.util.spec_from_file_location("rls_migration", BACKEND_ROOT / "alembic" / "versions" / "0002_supabase_rls.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

APPLICATION_TABLES = (
    "profiles", "user_preferences", "allergens", "equipment", "ingredients",
    "nutrition_sources", "recipes", "recipe_versions", "user_allergens",
    "user_disliked_ingredients", "user_equipment", "ingredient_allergens",
    "ingredient_nutrition", "recipe_ingredients", "cooking_steps",
    "recipe_nutrition", "meal_plans", "planned_meals", "shopping_lists",
    "shopping_list_items", "favourites",
)


def test_every_application_table_enables_and_disables_rls() -> None:
    migration = load_migration()
    assert migration.APPLICATION_TABLES == APPLICATION_TABLES
    assert "ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY" in MIGRATION
    assert "ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY" in MIGRATION


def test_direct_owner_policies_use_auth_uid_for_all_operations() -> None:
    migration = load_migration()
    assert migration.DIRECT_OWNER_TABLES == (
        "profiles", "user_preferences", "user_allergens",
        "user_disliked_ingredients", "user_equipment", "meal_plans",
        "shopping_lists", "favourites",
    )
    assert "CREATE POLICY {table}_owner_all" in MIGRATION
    assert "FOR ALL TO authenticated" in MIGRATION
    assert "USING (user_id = (SELECT auth.uid()))" in MIGRATION
    assert "WITH CHECK (user_id = (SELECT auth.uid()))" in MIGRATION


def test_indirect_owner_policies_follow_verified_foreign_keys() -> None:
    assert "CREATE POLICY planned_meals_owner_all" in MIGRATION
    assert "meal_plans.id = planned_meals.meal_plan_id" in MIGRATION
    assert "meal_plans.user_id = (SELECT auth.uid())" in MIGRATION
    assert "CREATE POLICY shopping_list_items_owner_all" in MIGRATION
    assert "shopping_lists.id = shopping_list_items.shopping_list_id" in MIGRATION
    assert "shopping_lists.user_id = (SELECT auth.uid())" in MIGRATION


def test_shared_tables_allow_authenticated_reads_only() -> None:
    migration = load_migration()
    expected = (
        "allergens", "equipment", "ingredients", "nutrition_sources",
        "recipes", "recipe_versions", "ingredient_allergens",
        "ingredient_nutrition", "recipe_ingredients", "cooking_steps",
        "recipe_nutrition",
    )
    assert migration.SHARED_READ_TABLES == expected
    assert "CREATE POLICY {table}_authenticated_read" in MIGRATION
    assert "FOR SELECT TO authenticated" in MIGRATION
    assert "FOR INSERT TO authenticated" not in MIGRATION
    assert "FOR UPDATE TO authenticated" not in MIGRATION
    assert "FOR DELETE TO authenticated" not in MIGRATION


def test_migration_is_rls_only_and_has_no_credentials() -> None:
    assert 'down_revision: Union[str, Sequence[str], None] = "0001_mvp_schema"' in MIGRATION
    assert "DATABASE_URL" not in MIGRATION
    assert "password" not in MIGRATION.lower()
    assert "op.create_table" not in MIGRATION
    assert "op.drop_table" not in MIGRATION
