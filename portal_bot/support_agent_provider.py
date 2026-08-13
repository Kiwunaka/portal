from __future__ import annotations

import asyncio
import json
import logging
import math
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

import aiohttp

from support_ai_service import (
    SupportAIConfig,
    _ProviderResponseTooLarge,
    provider_generation_controls,
    provider_response_controls,
    provider_timeout_ceiling,
    provider_wire_model,
    read_bounded_provider_json,
)


logger = logging.getLogger(__name__)

_RETRYABLE_HTTP_STATUSES = frozenset({429, 502, 503, 504})
_MAX_CONTENT_CHARS = 16_000


@dataclass(frozen=True, slots=True)
class ProviderUsage:
    prompt_tokens: int | None
    completion_tokens: int | None
    cached_tokens: int | None


@dataclass(frozen=True, slots=True)
class SynthesisTurn:
    content: str
    finish_reason: str
    usage: ProviderUsage
    latency_ms: int


class ProviderCallError(RuntimeError):
    def __init__(self, *, retryable: bool, code: str, status: int) -> None:
        super().__init__(code)
        self.retryable = bool(retryable)
        self.code = code
        self.status = status


def _raise_provider_error(*, retryable: bool, code: str, status: int) -> None:
    logger.warning("support agent provider failed code=%s status=%s", code, status)
    raise ProviderCallError(retryable=retryable, code=code, status=status)


def _safe_status(value: object) -> int:
    try:
        status = int(value)
    except (TypeError, ValueError):
        return 0
    return status if 100 <= status <= 599 else 0


def _optional_usage_int(value: object) -> int | None:
    return value if type(value) is int and value >= 0 else None


def _usage(payload: Mapping[str, object]) -> ProviderUsage:
    raw_usage = payload.get("usage")
    if not isinstance(raw_usage, Mapping):
        return ProviderUsage(prompt_tokens=None, completion_tokens=None, cached_tokens=None)
    details = raw_usage.get("prompt_tokens_details")
    nested_cached = details.get("cached_tokens") if isinstance(details, Mapping) else None
    cached_tokens = _optional_usage_int(nested_cached)
    if cached_tokens is None:
        cached_tokens = _optional_usage_int(raw_usage.get("cached_tokens"))
    return ProviderUsage(
        prompt_tokens=_optional_usage_int(raw_usage.get("prompt_tokens")),
        completion_tokens=_optional_usage_int(raw_usage.get("completion_tokens")),
        cached_tokens=cached_tokens,
    )


def _validated_timeout(value: object, *, maximum: float) -> float:
    try:
        timeout_seconds = float(value)
    except (TypeError, ValueError):
        _raise_provider_error(retryable=False, code="provider_request_invalid", status=0)
    if not math.isfinite(timeout_seconds) or not 0.1 <= timeout_seconds <= maximum:
        _raise_provider_error(retryable=False, code="provider_request_invalid", status=0)
    return timeout_seconds


def _normalize_synthesis_turn(
    payload: object,
    *,
    status: int,
    latency_ms: int,
) -> SynthesisTurn:
    if not isinstance(payload, Mapping):
        _raise_provider_error(retryable=False, code="provider_response_invalid", status=status)
    choices = payload.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        _raise_provider_error(retryable=False, code="provider_choice_count_invalid", status=status)
    choice = choices[0]
    if not isinstance(choice, Mapping):
        _raise_provider_error(retryable=False, code="provider_choice_invalid", status=status)
    finish_reason = choice.get("finish_reason")
    message = choice.get("message")
    if finish_reason != "stop" or not isinstance(message, Mapping):
        _raise_provider_error(retryable=False, code="provider_choice_invalid", status=status)
    if message.get("tool_calls") not in (None, []):
        _raise_provider_error(retryable=False, code="provider_tool_calls_invalid", status=status)
    content = message.get("content")
    if (
        not isinstance(content, str)
        or not content.strip()
        or len(content) > _MAX_CONTENT_CHARS
    ):
        _raise_provider_error(retryable=False, code="provider_content_invalid", status=status)
    return SynthesisTurn(
        content=content,
        finish_reason=finish_reason,
        usage=_usage(payload),
        latency_ms=latency_ms,
    )


class XCodyChatAdapter:
    def __init__(
        self,
        *,
        config: SupportAIConfig,
        session_factory: Any | None = None,
        monotonic: Callable[[], float] | None = None,
    ) -> None:
        self.config = config
        self.session_factory = session_factory or aiohttp.ClientSession
        self.monotonic = monotonic or time.monotonic

    async def complete_synthesis(
        self,
        *,
        messages: Sequence[Mapping[str, object]],
        request_timeout: float,
    ) -> SynthesisTurn:
        timeout_seconds = _validated_timeout(
            request_timeout,
            maximum=provider_timeout_ceiling(self.config.api_base_url),
        )
        if (
            len(messages) != 2
            or any(not isinstance(item, Mapping) for item in messages)
            or [item.get("role") for item in messages] != ["system", "user"]
            or any(set(item) != {"role", "content"} for item in messages)
            or any(
                not isinstance(item.get("content"), str) or not item.get("content")
                for item in messages
            )
            or not isinstance(self.config.api_key, str)
            or not self.config.api_key
            or not isinstance(self.config.api_base_url, str)
            or not self.config.api_base_url
            or not isinstance(self.config.model, str)
            or not self.config.model
            or not isinstance(self.config.reasoning_effort, str)
            or not self.config.reasoning_effort
            or type(self.config.max_output_tokens) is not int
            or not 1 <= self.config.max_output_tokens <= 1_200
            or type(self.config.max_context_chars) is not int
            or self.config.max_context_chars < 1_000
        ):
            _raise_provider_error(retryable=False, code="provider_request_invalid", status=0)
        payload = {
            "model": provider_wire_model(self.config),
            "messages": [dict(item) for item in messages],
            "temperature": 0.2,
            "n": 1,
            **provider_response_controls(self.config),
            **provider_generation_controls(self.config),
        }
        serialized = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        if len(serialized) > min(self.config.max_context_chars, 30_000):
            _raise_provider_error(
                retryable=False,
                code="provider_request_too_large",
                status=0,
            )
        return await self._post_synthesis(payload, timeout_seconds)

    async def _post_synthesis(
        self,
        payload: Mapping[str, object],
        timeout_seconds: float,
    ) -> SynthesisTurn:
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.config.api_base_url.rstrip('/')}/chat/completions"
        timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        started = self.monotonic()
        status = 0
        try:
            async with self.session_factory(timeout=timeout) as session:
                async with session.post(url, headers=headers, json=dict(payload)) as response:
                    status = _safe_status(getattr(response, "status", 0))
                    if status >= 400:
                        _raise_provider_error(
                            retryable=status in _RETRYABLE_HTTP_STATUSES,
                            code="provider_http_error",
                            status=status,
                        )
                    response_payload = await read_bounded_provider_json(response)
        except ProviderCallError:
            raise
        except (asyncio.TimeoutError, TimeoutError):
            _raise_provider_error(retryable=True, code="provider_timeout", status=status)
        except (aiohttp.ClientError, OSError):
            _raise_provider_error(retryable=True, code="provider_transport_error", status=status)
        except _ProviderResponseTooLarge:
            _raise_provider_error(
                retryable=False,
                code="provider_response_too_large",
                status=status,
            )
        except (UnicodeDecodeError, ValueError, TypeError):
            _raise_provider_error(retryable=False, code="provider_response_invalid", status=status)
        except Exception:
            _raise_provider_error(retryable=False, code="provider_request_error", status=status)

        latency_ms = max(0, int(round((self.monotonic() - started) * 1000)))
        return _normalize_synthesis_turn(
            response_payload,
            status=status,
            latency_ms=latency_ms,
        )
