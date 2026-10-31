from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.db.session import check_database_connectivity, get_engine


class FakeConnection:
    def __init__(self) -> None:
        self.statements: list[str] = []

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def execute(self, statement: Any) -> None:
        self.statements.append(str(statement))


class FakeEngine:
    def __init__(self) -> None:
        self.connection = FakeConnection()

    def connect(self) -> FakeConnection:
        return self.connection


def test_database_url_comes_from_database_url_environment_variable(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://example.invalid/mealmate")
    get_settings.cache_clear()
    get_engine.cache_clear()

    assert get_settings().database_url == "postgresql+psycopg://example.invalid/mealmate"
    assert get_engine().url.drivername == "postgresql+psycopg"

    get_settings.cache_clear()
    get_engine.cache_clear()


def test_database_connectivity_runs_select_one_without_real_database() -> None:
    fake_engine = FakeEngine()

    assert check_database_connectivity(fake_engine) is True
    assert fake_engine.connection.statements == ["SELECT 1"]


def test_database_connectivity_returns_false_for_database_error() -> None:
    class FailingEngine:
        def connect(self):
            raise SQLAlchemyError("connection unavailable")

    assert check_database_connectivity(FailingEngine()) is False  # type: ignore[arg-type]
