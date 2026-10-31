import logging
import ssl

import httpx
import pytest

from app.services.supabase_auth import SupabaseAuthError, SupabaseAuthService, _failure_category


@pytest.mark.parametrize(
    ("error", "category"),
    [
        (httpx.ConnectTimeout("sensitive timeout details"), "timeout"),
        (httpx.ConnectError("sensitive network details"), "network"),
        (ValueError("sensitive response details"), "response_parsing"),
    ],
)
def test_failure_category_is_sanitised(error: BaseException, category: str) -> None:
    assert _failure_category(error) == category


def test_tls_failure_category_uses_exception_types_only() -> None:
    error = httpx.ConnectError("sensitive network details")
    error.__cause__ = ssl.SSLError("sensitive TLS details")

    assert _failure_category(error) == "tls"


def test_network_failure_logs_only_class_and_category(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    service = SupabaseAuthService("https://example.supabase.co", "safe-test-key")
    error = httpx.ConnectError("password=must-not-be-logged")
    monkeypatch.setattr(
        "app.services.supabase_auth.httpx.post",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(error),
    )

    with caplog.at_level(logging.WARNING, logger="app.services.supabase_auth"):
        with pytest.raises(SupabaseAuthError):
            service.register("user@example.com", "password123")

    assert "exception_class=ConnectError" in caplog.text
    assert "category=network" in caplog.text
    assert "password=must-not-be-logged" not in caplog.text


def test_http_failure_logs_status_and_sanitised_category(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    class FakeResponse:
        content = b"provider response"
        status_code = 400

        @staticmethod
        def json() -> dict[str, str]:
            return {"code": "email_exists", "message": "private provider details"}

    service = SupabaseAuthService("https://example.supabase.co", "safe-test-key")
    monkeypatch.setattr(
        "app.services.supabase_auth.httpx.post",
        lambda *_args, **_kwargs: FakeResponse(),
    )

    with caplog.at_level(logging.WARNING, logger="app.services.supabase_auth"):
        with pytest.raises(SupabaseAuthError):
            service.register("user@example.com", "password123")

    assert "status_code=400" in caplog.text
    assert "category=duplicate_email" in caplog.text
    assert "private provider details" not in caplog.text
