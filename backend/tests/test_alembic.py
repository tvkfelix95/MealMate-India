from pathlib import Path
from datetime import date

from alembic.config import Config


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_alembic_config_does_not_store_database_url() -> None:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))

    assert config.get_main_option("sqlalchemy.url") == ""
    assert "get_settings" in (BACKEND_ROOT / "alembic" / "env.py").read_text()
    assert "target_metadata = Base.metadata" in (BACKEND_ROOT / "alembic" / "env.py").read_text()


def test_initial_migration_contains_mvp_tables() -> None:
    migration = (BACKEND_ROOT / "alembic" / "versions" / "0001_mvp_schema.py").read_text()

    for table in (
        "profiles",
        "ingredients",
        "ingredient_nutrition",
        "recipes",
        "recipe_versions",
        "recipe_nutrition",
        "meal_plans",
        "planned_meals",
        "shopping_lists",
        "favourites",
    ):
        assert f'"{table}"' in migration

    assert "calories_kcal IS NULL OR calories_kcal >= 0" in migration
    assert 'sa.text("gen_random_uuid()")' in migration


def test_meal_plan_date_rules_cover_valid_and_invalid_ranges() -> None:
    migration = (BACKEND_ROOT / "alembic" / "versions" / "0001_mvp_schema.py").read_text()

    assert 'end_date >= start_date' in migration
    assert "plan_type <> 'daily' OR end_date = start_date" in migration
    assert "plan_type <> 'weekly' OR end_date <= start_date + 6" in migration
    assert 'op.drop_constraint("ck_meal_plans_weekly_date_range"' in migration
    assert 'op.drop_constraint("ck_meal_plans_daily_date_range"' in migration

    def is_valid(plan_type: str, start_date: date, end_date: date) -> bool:
        days = (end_date - start_date).days
        return end_date >= start_date and (
            (plan_type == "daily" and days == 0)
            or (plan_type == "weekly" and 0 <= days <= 6)
        )

    assert is_valid("daily", date(2026, 1, 1), date(2026, 1, 1))
    assert is_valid("weekly", date(2026, 1, 1), date(2026, 1, 7))
    assert not is_valid("daily", date(2026, 1, 1), date(2026, 1, 2))
    assert not is_valid("weekly", date(2026, 1, 1), date(2026, 1, 8))
    assert not is_valid("weekly", date(2026, 1, 2), date(2026, 1, 1))
