import importlib

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings


main_module = importlib.import_module("app.main")


def create_test_app(monkeypatch: pytest.MonkeyPatch, *, environment: str, origins: str) -> object:
    settings = Settings(environment=environment, cors_origins=origins)
    monkeypatch.setattr(main_module, "get_settings", lambda: settings)
    return main_module.create_app()


def test_local_origins_are_allowed_in_development(monkeypatch: pytest.MonkeyPatch) -> None:
    application = create_test_app(monkeypatch, environment="development", origins="")

    response = TestClient(application).get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "*" not in response.headers["access-control-allow-origin"]


def test_unconfigured_origin_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    application = create_test_app(
        monkeypatch,
        environment="production",
        origins="https://frontend.example.com",
    )

    response = TestClient(application).get(
        "/api/v1/health",
        headers={"Origin": "https://untrusted.example.com"},
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_preflight_allows_required_headers_and_methods(monkeypatch: pytest.MonkeyPatch) -> None:
    application = create_test_app(
        monkeypatch,
        environment="production",
        origins="https://frontend.example.com",
    )

    response = TestClient(application).options(
        "/api/v1/auth/login",
        headers={
            "Origin": "https://frontend.example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization, Content-Type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://frontend.example.com"
    assert response.headers["access-control-allow-methods"]
    assert response.headers["access-control-allow-headers"]
    assert response.headers.get("access-control-allow-credentials") != "true"


def test_production_requires_explicit_origins() -> None:
    settings = Settings(environment="production", cors_origins="")

    with pytest.raises(ValueError, match="CORS_ORIGINS must be configured"):
        settings.get_cors_origins()


def test_wildcard_origin_is_rejected() -> None:
    with pytest.raises(ValueError, match=r"exact HTTP\(S\) origins"):
        Settings(cors_origins="*")
