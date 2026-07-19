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
    read_bounded_provider_json,
)


logger = logging.getLogger(__name__)

_RETRYABLE_HTTP_STATUSES = frozenset({429, 502, 503, 504})
_MAX_TOOL_CALLS = 4
_MAX_CONTENT_CHARS = 16_000
_MAX_TOOL_ARGUMENT_CHARS = 1_200


@dataclass(frozen=True, slots=True)
class ProviderUsage:
    prompt_tokens: int | None
    completion_tokens: int | None
    cached_tokens: int | None


@dataclass(frozen=True, slots=True)
class ToolCall:
    call_id: str
    name: str
    arguments_json: str


@dataclass(frozen=True, slots=True)
class ModelTurn:
    content: str | None
    finish_reason: str
    tool_calls: tuple[ToolCall, ...]
    normalized_assistant_message: Mapping[str, object]
    usage: ProviderUsage
    latency_ms: int


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
    if type(value) is not int or value < 0:
        return None
    return value


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


def _normalize_tool_calls(raw_value: object, *, status: int) -> tuple[tuple[ToolCall, ...], list[dict[str, object]]]:
    if raw_value is None:
        return (), []
    if not isinstance(raw_value, list) or len(raw_value) > _MAX_TOOL_CALLS:
        _raise_provider_error(retryable=False, code="provider_tool_calls_invalid", status=status)
    parsed: list[ToolCall] = []
    normalized: list[dict[str, object]] = []
    for raw_call in raw_value:
        if not isinstance(raw_call, Mapping):
            _raise_provider_error(retryable=False, code="provider_tool_call_invalid", status=status)
        function = raw_call.get("function")
        call_id = raw_call.get("id")
        call_type = raw_call.get("type")
        if not isinstance(function, Mapping):
            _raise_provider_error(retryable=False, code="provider_tool_call_invalid", status=status)
        name = function.get("name")
        arguments = function.get("arguments")
        if (
            call_type != "function"
            or not isinstance(call_id, str)
            or not 1 <= len(call_id) <= 128
            or not isinstance(name, str)
            or not 1 <= len(name) <= 64
            or not isinstance(arguments, str)
            or len(arguments) > _MAX_TOOL_ARGUMENT_CHARS
        ):
            _raise_provider_error(retryable=False, code="provider_tool_call_invalid", status=status)
        parsed.append(ToolCall(call_id=call_id, name=name, arguments_json=arguments))
        normalized.append(
            {
                "id": call_id,
                "type": "function",
                "function": {"name": name, "arguments": arguments},
            }
        )
    return tuple(parsed), normalized


def _normalize_turn(payload: object, *, status: int, latency_ms: int) -> ModelTurn:
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
    if (
        not isinstance(finish_reason, str)
        or not 1 <= len(finish_reason) <= 64
        or not isinstance(message, Mapping)
    ):
        _raise_provider_error(retryable=False, code="provider_choice_invalid", status=status)
    content = message.get("content")
    if content is not None and (not isinstance(content, str) or len(content) > _MAX_CONTENT_CHARS):
        _raise_provider_error(retryable=False, code="provider_content_invalid", status=status)
    tool_calls, normalized_calls = _normalize_tool_calls(message.get("tool_calls"), status=status)
    if content is None and not tool_calls:
        _raise_provider_error(retryable=False, code="provider_message_empty", status=status)
    normalized_message: dict[str, object] = {"role": "assistant", "content": content}
    if normalized_calls:
        normalized_message["tool_calls"] = normalized_calls
    return ModelTurn(
        content=content,
        finish_reason=finish_reason,
        tool_calls=tool_calls,
        normalized_assistant_message=normalized_message,
        usage=_usage(payload),
        latency_ms=latency_ms,
    )


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
        timeout_seconds = _validated_timeout(request_timeout, maximum=20.0)
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
            "model": self.config.model,
            "messages": [dict(item) for item in messages],
            "reasoning_effort": self.config.reasoning_effort,
            "temperature": 0.2,
            "max_tokens": self.config.max_output_tokens,
            "n": 1,
            "response_format": {"type": "json_object"},
        }
        serialized = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        request_limit = min(self.config.max_context_chars, 30_000)
        if len(serialized) > request_limit:
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

        elapsed = self.monotonic() - started
        latency_ms = max(0, int(round(elapsed * 1000)))
        return _normalize_synthesis_turn(
            response_payload,
            status=status,
            latency_ms=latency_ms,
        )

    async def complete(
        self,
        *,
        messages: Sequence[Mapping[str, object]],
        tools: Sequence[Mapping[str, object]],
        tool_choice: str,
        request_timeout: float,
    ) -> ModelTurn:
        try:
            timeout_seconds = float(request_timeout)
        except (TypeError, ValueError):
            _raise_provider_error(retryable=False, code="provider_timeout_invalid", status=0)
        if (
            not math.isfinite(timeout_seconds)
            or not 0.1 <= timeout_seconds <= 12.0
            or tool_choice not in {"auto", "none"}
            or not self.config.api_key
            or not self.config.api_base_url
            or not self.config.model
        ):
            _raise_provider_error(retryable=False, code="provider_request_invalid", status=0)

        payload = {
            "model": self.config.model,
            "messages": [dict(item) for item in messages],
            "tools": [dict(item) for item in tools],
            "tool_choice": tool_choice,
            "max_tokens": self.config.max_output_tokens,
            "n": 1,
            "reasoning_effort": self.config.reasoning_effort,
        }
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
                async with session.post(url, headers=headers, json=payload) as response:
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
        except aiohttp.ClientError:
            _raise_provider_error(retryable=True, code="provider_transport_error", status=status)
        except OSError:
            _raise_provider_error(retryable=True, code="provider_transport_error", status=status)
        except _ProviderResponseTooLarge:
            _raise_provider_error(retryable=False, code="provider_response_too_large", status=status)
        except (UnicodeDecodeError, ValueError, TypeError):
            _raise_provider_error(retryable=False, code="provider_response_invalid", status=status)
        except Exception:
            _raise_provider_error(retryable=False, code="provider_request_error", status=status)

        elapsed = self.monotonic() - started
        latency_ms = max(0, int(round(elapsed * 1000)))
        return _normalize_turn(response_payload, status=status, latency_ms=latency_ms)
