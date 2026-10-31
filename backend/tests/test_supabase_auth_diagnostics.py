import logging
import ssl

import httpx
import pytest

from app.services.supabase_auth import (
    RateLimitError,
    SupabaseAuthError,
    SupabaseAuthService,
    UnverifiedEmailError,
    _failure_category,
)


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


def test_http_429_raises_sanitised_rate_limit_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        content = b"provider response"
        status_code = 429

        @staticmethod
        def json() -> dict[str, str]:
            return {"code": "over_email_send_rate_limit", "message": "private provider details"}

    service = SupabaseAuthService("https://example.supabase.co", "safe-test-key")
    monkeypatch.setattr(
        "app.services.supabase_auth.httpx.post",
        lambda *_args, **_kwargs: FakeResponse(),
    )

    with pytest.raises(RateLimitError, match="temporarily rate limited"):
        service.register("user@example.com", "password123")


def test_provider_email_confirmation_error_is_unverified(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        content = b"provider response"
        status_code = 400

        @staticmethod
        def json() -> dict[str, str]:
            return {"code": "email_not_confirmed", "message": "private provider details"}

    service = SupabaseAuthService("https://example.supabase.co", "safe-test-key")
    monkeypatch.setattr(
        "app.services.supabase_auth.httpx.post",
        lambda *_args, **_kwargs: FakeResponse(),
    )

    with pytest.raises(UnverifiedEmailError, match="must be verified"):
        service.login("user@example.com", "password123")


def test_signup_without_tokens_or_confirmation_timestamps_is_pending() -> None:
    session = SupabaseAuthService._session_from_response(
        {"user": {"id": "user-id"}},
        require_tokens=False,
    )

    assert session.user_id == "user-id"
    assert session.access_token is None
    assert session.refresh_token is None
    assert session.email_confirmation_required is True


def test_signup_without_tokens_with_unconfirmed_timestamps_is_pending() -> None:
    session = SupabaseAuthService._session_from_response(
        {
            "user": {
                "id": "user-id",
                "email_confirmed_at": None,
                "confirmed_at": None,
            }
        },
        require_tokens=False,
    )

    assert session.email_confirmation_required is True


def test_signup_response_requires_user_id() -> None:
    with pytest.raises(SupabaseAuthError, match="Invalid authentication provider response"):
        SupabaseAuthService._session_from_response({"user": {}}, require_tokens=False)


@pytest.mark.parametrize(
    "response",
    [
        {"user": {"id": "user-id"}, "session": {"access_token": "access-token"}},
        {"user": {"id": "user-id"}, "session": {"access_token": 123}},
    ],
)
def test_authenticated_session_is_not_treated_as_pending_when_incomplete(response: dict) -> None:
    with pytest.raises(SupabaseAuthError, match="Invalid authentication provider response"):
        SupabaseAuthService._session_from_response(response, require_tokens=True)


def test_registration_logs_safe_success_stages_without_sensitive_values(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    class FakeResponse:
        content = b"provider response"
        status_code = 200

        @staticmethod
        def json() -> dict[str, object]:
            return {
                "user": {"id": "user-id"},
                "access_token": "access-token-secret",
                "refresh_token": "refresh-token-secret",
            }

    monkeypatch.setattr(
        "app.services.supabase_auth.httpx.post",
        lambda *_args, **_kwargs: FakeResponse(),
    )

    with caplog.at_level(logging.INFO, logger="app.services.supabase_auth"):
        SupabaseAuthService("https://example.supabase.co", "api-key-secret").register(
            "private@example.com",
            "password-secret",
        )

    assert "stage=signup_request_started" in caplog.text
    assert "stage=http_response_received status_code=200" in caplog.text
    assert "stage=response_json_parsed" in caplog.text
    assert "stage=user_id_validation_failed" not in caplog.text
    assert "stage=session_validation_passed" in caplog.text
    assert "stage=registration_completed" in caplog.text
    for sensitive_value in (
        "private@example.com",
        "password-secret",
        "access-token-secret",
        "refresh-token-secret",
        "api-key-secret",
    ):
        assert sensitive_value not in caplog.text


def test_registration_logs_sanitised_json_parse_failure(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    class FakeResponse:
        content = b"invalid response"
        status_code = 200

        @staticmethod
        def json() -> dict[str, object]:
            raise ValueError("password=private-value")

    monkeypatch.setattr(
        "app.services.supabase_auth.httpx.post",
        lambda *_args, **_kwargs: FakeResponse(),
    )

    with caplog.at_level(logging.INFO, logger="app.services.supabase_auth"):
        with pytest.raises(SupabaseAuthError):
            SupabaseAuthService("https://example.supabase.co", "safe-key").register(
                "private@example.com",
                "password-secret",
            )

    assert "stage=response_json_parse_failed" in caplog.text
    assert "exception_class=ValueError" in caplog.text
    assert "category=response_parsing" in caplog.text
    assert "password=private-value" not in caplog.text
    assert "private@example.com" not in caplog.text
    assert "password-secret" not in caplog.text


def test_registration_logs_user_id_validation_failure_without_response_data(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    class FakeResponse:
        content = b"provider response containing private data"
        status_code = 200

        @staticmethod
        def json() -> dict[str, object]:
            return {"user": {"email": "private@example.com"}}

    monkeypatch.setattr(
        "app.services.supabase_auth.httpx.post",
        lambda *_args, **_kwargs: FakeResponse(),
    )

    with caplog.at_level(logging.INFO, logger="app.services.supabase_auth"):
        with pytest.raises(SupabaseAuthError):
            SupabaseAuthService("https://example.supabase.co", "safe-key").register(
                "private@example.com",
                "password-secret",
            )

    assert "stage=user_id_validation_failed" in caplog.text
    assert "exception_class=SupabaseAuthError" in caplog.text
    assert "category=response_schema" in caplog.text
    assert "private@example.com" not in caplog.text
    assert "password-secret" not in caplog.text
