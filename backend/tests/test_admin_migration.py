from pathlib import Path
import importlib.util


BACKEND_ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = BACKEND_ROOT / "alembic" / "versions" / "0003_admin_users.py"
MIGRATION_TEXT = MIGRATION_PATH.read_text(encoding="utf-8")


def load_migration():
    spec = importlib.util.spec_from_file_location("admin_migration", MIGRATION_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_admin_table_migration_has_expected_revision_and_rls() -> None:
    migration = load_migration()

    assert migration.revision == "0003_admin_users"
    assert migration.down_revision == "0002_supabase_rls"
    assert "op.create_table(" in MIGRATION_TEXT
    assert '"admin_users"' in MIGRATION_TEXT
    assert "ALTER TABLE public.admin_users ENABLE ROW LEVEL SECURITY" in MIGRATION_TEXT


def test_admin_migration_has_no_user_facing_policies_and_safe_downgrade() -> None:
    assert "CREATE POLICY" not in MIGRATION_TEXT
    assert "DISABLE ROW LEVEL SECURITY" in MIGRATION_TEXT
    assert 'op.drop_table("admin_users")' in MIGRATION_TEXT
