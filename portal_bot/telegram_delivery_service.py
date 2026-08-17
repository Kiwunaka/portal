from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import dataclass
from typing import Any, Mapping

import aiohttp


TELEGRAM_DELIVERY_REASON_CODES = frozenset(
    {
        "sent",
        "blocked",
        "bot_not_started_or_chat_not_found",
        "account_deactivated",
        "rate_limited",
        "transient_provider",
        "delivery_uncertain",
        "internal",
        "unknown_safe",
    }
)


@dataclass(frozen=True)
class TelegramDeliveryResult:
    sent: bool
    reason_code: str
    retryable: bool
    duration_ms: int
    http_status: int | None = None
    telegram_error_code: int | None = None
    retry_after_seconds: int | None = None
    message_id: int | None = None
    provider_error_hash: str | None = None


def _bounded_int(value: object, *, minimum: int = 0, maximum: int = 2_147_483_647) -> int | None:
    if type(value) is not int:
        return None
    number = int(value)
    return number if minimum <= number <= maximum else None


def _error_hash(description: object) -> str | None:
    value = str(description or "").strip().lower()
    if not value:
        return None
    return hashlib.sha256(value[:1000].encode("utf-8", errors="replace")).hexdigest()


def normalize_telegram_failure(
    *,
    http_status: int | None,
    telegram_error_code: int | None,
    description: object,
) -> tuple[str, bool]:
    text = str(description or "").strip().lower()
    status = int(http_status or 0)
    error_code = int(telegram_error_code or 0)
    if "bot was blocked" in text or "blocked by the user" in text:
        return "blocked", False
    if "user is deactivated" in text or "user deactivated" in text:
        return "account_deactivated", False
    if (
        "chat not found" in text
        or "bot can't initiate conversation" in text
        or "bot was not started" in text
        or "user not found" in text
    ):
        return "bot_not_started_or_chat_not_found", False
    if status == 429 or error_code == 429:
        return "rate_limited", True
    if status >= 500 or error_code >= 500:
        return "transient_provider", False
    if status in {401, 404} and not text:
        return "internal", False
    return "unknown_safe", False


async def send_telegram_message(
    *,
    token: str,
    chat_id: int,
    text: str,
    parse_mode: str | None = None,
    reply_markup: Mapping[str, Any] | None = None,
    disable_web_page_preview: bool | None = None,
    timeout_seconds: float = 15.0,
) -> TelegramDeliveryResult:
    started = time.perf_counter()

    def duration_ms() -> int:
        return max(0, min(int((time.perf_counter() - started) * 1000), 3_600_000))

    normalized_token = str(token or "").strip()
    if not normalized_token:
        return TelegramDeliveryResult(
            sent=False,
            reason_code="internal",
            retryable=False,
            duration_ms=duration_ms(),
        )
    payload: dict[str, Any] = {"chat_id": int(chat_id), "text": str(text)}
    if parse_mode:
        payload["parse_mode"] = str(parse_mode)
    if reply_markup:
        payload["reply_markup"] = dict(reply_markup)
    if disable_web_page_preview is not None:
        payload["disable_web_page_preview"] = bool(disable_web_page_preview)
    endpoint = f"https://api.telegram.org/bot{normalized_token}/sendMessage"
    try:
        async with aiohttp.ClientSession() as client:
            async with client.post(
                endpoint,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=max(1.0, min(float(timeout_seconds), 30.0))),
            ) as response:
                try:
                    body = await response.json(content_type=None)
                except Exception:
                    body = {}
                body = body if isinstance(body, Mapping) else {}
                telegram_error_code = _bounded_int(body.get("error_code"), minimum=100, maximum=599)
                if response.status == 200 and body.get("ok") is True:
                    result = body.get("result") if isinstance(body.get("result"), Mapping) else {}
                    return TelegramDeliveryResult(
                        sent=True,
                        reason_code="sent",
                        retryable=False,
                        duration_ms=duration_ms(),
                        http_status=200,
                        message_id=_bounded_int(result.get("message_id"), minimum=1),
                    )
                parameters = body.get("parameters") if isinstance(body.get("parameters"), Mapping) else {}
                retry_after = _bounded_int(parameters.get("retry_after"), minimum=1, maximum=86_400)
                reason_code, retryable = normalize_telegram_failure(
                    http_status=int(response.status),
                    telegram_error_code=telegram_error_code,
                    description=body.get("description"),
                )
                return TelegramDeliveryResult(
                    sent=False,
                    reason_code=reason_code,
                    retryable=retryable,
                    duration_ms=duration_ms(),
                    http_status=int(response.status),
                    telegram_error_code=telegram_error_code,
                    retry_after_seconds=retry_after,
                    provider_error_hash=_error_hash(body.get("description")),
                )
    except (asyncio.TimeoutError, aiohttp.ClientError):
        return TelegramDeliveryResult(
            sent=False,
            reason_code="delivery_uncertain",
            retryable=False,
            duration_ms=duration_ms(),
        )
    except Exception:
        return TelegramDeliveryResult(
            sent=False,
            reason_code="internal",
            retryable=False,
            duration_ms=duration_ms(),
        )
