from __future__ import annotations

from portal_bot.telegram_delivery_service import normalize_telegram_failure


def test_normalizes_terminal_recipient_failures_without_raw_text() -> None:
    assert normalize_telegram_failure(
        http_status=403,
        telegram_error_code=403,
        description="Forbidden: bot was blocked by the user",
    ) == ("blocked", False)
    assert normalize_telegram_failure(
        http_status=400,
        telegram_error_code=400,
        description="Bad Request: chat not found",
    ) == ("bot_not_started_or_chat_not_found", False)
    assert normalize_telegram_failure(
        http_status=403,
        telegram_error_code=403,
        description="Forbidden: user is deactivated",
    ) == ("account_deactivated", False)


def test_only_explicit_rate_limit_is_automatically_retryable() -> None:
    assert normalize_telegram_failure(
        http_status=429,
        telegram_error_code=429,
        description="Too Many Requests",
    ) == ("rate_limited", True)
    assert normalize_telegram_failure(
        http_status=502,
        telegram_error_code=502,
        description="Bad Gateway",
    ) == ("transient_provider", False)
