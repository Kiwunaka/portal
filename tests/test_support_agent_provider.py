import asyncio
import json
import logging
import sys
from pathlib import Path

import aiohttp
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))

SAFE_TWO_MESSAGES = (
    {"role": "system", "content": "stable"},
    {"role": "user", "content": "volatile"},
)
SAFE_RESPONSE = {
    "choices": [
        {
            "finish_reason": "stop",
            "message": {
                "content": '{"schema_version":"1","status":"answer","reply":"Ответ."}',
            },
        }
    ],
    "usage": {"prompt_tokens": 50, "completion_tokens": 10, "cached_tokens": 40},
}


class _FakeContent:
    def __init__(self, body: bytes) -> None:
        self._body = body
        self._position = 0

    async def read(self, size: int) -> bytes:
        if self._position >= len(self._body):
            return b""
        chunk = self._body[self._position : self._position + max(1, size)]
        self._position += len(chunk)
        return chunk


class _FakeResponse:
    def __init__(
        self,
        status: int,
        payload: object,
        *,
        raw_body: bytes | None = None,
        content_length: int | None = None,
    ) -> None:
        self.status = status
        body = raw_body if raw_body is not None else json.dumps(payload).encode("utf-8")
        self.content_length = len(body) if content_length is None else content_length
        self.content = _FakeContent(body)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeSession:
    def __init__(self, owner: "_FakeSessionFactory") -> None:
        self.owner = owner

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def post(self, url, *, headers, json):
        self.owner.posts.append({"url": url, "headers": headers, "json": json})
        if self.owner.post_error is not None:
            raise self.owner.post_error
        return self.owner.response


class _FakeSessionFactory:
    def __init__(
        self,
        *,
        status: int = 200,
        payload: object | None = None,
        raw_body: bytes | None = None,
        content_length: int | None = None,
        post_error: BaseException | None = None,
    ) -> None:
        self.response = _FakeResponse(
            status,
            {} if payload is None else payload,
            raw_body=raw_body,
            content_length=content_length,
        )
        self.post_error = post_error
        self.posts: list[dict[str, object]] = []
        self.timeout = None

    def __call__(self, *, timeout):
        self.timeout = timeout
        return _FakeSession(self)


def _config():
    from support_ai_service import SupportAIConfig

    return SupportAIConfig(
        enabled=True,
        api_key="sk-test-key",
        api_base_url="https://enterprise.xcody.dev/v1",
        model="minimax-m3",
        reasoning_effort="medium",
        timeout_seconds=20.0,
        max_context_chars=30_000,
        max_output_tokens=1_200,
    )


def _adapter_with_response(payload: object, *, clock=None):
    from support_agent_provider import XCodyChatAdapter

    factory = _FakeSessionFactory(payload=payload)
    return (
        XCodyChatAdapter(config=_config(), session_factory=factory, monotonic=clock),
        factory,
    )


def test_exact_xcody_synthesis_payload_and_normalized_usage() -> None:
    ticks = iter((10.0, 10.123))
    adapter, factory = _adapter_with_response(
        {
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": '{"schema_version":"1","status":"answer","reply":"Ответ."}',
                    },
                }
            ],
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 10,
                "cached_tokens": 7,
                "prompt_tokens_details": {"cached_tokens": 40},
            },
        },
        clock=lambda: next(ticks),
    )

    turn = asyncio.run(
        adapter.complete_synthesis(messages=SAFE_TWO_MESSAGES, request_timeout=20.0)
    )

    assert factory.posts == [
        {
            "url": "https://enterprise.xcody.dev/v1/chat/completions",
            "headers": {
                "Authorization": "Bearer sk-test-key",
                "Content-Type": "application/json",
            },
            "json": {
                "model": "minimax-m3",
                "messages": [
                    {"role": "system", "content": "stable"},
                    {"role": "user", "content": "volatile"},
                ],
                "reasoning_effort": "medium",
                "temperature": 0.2,
                "max_tokens": 1_200,
                "n": 1,
                "response_format": {"type": "json_object"},
            },
        }
    ]
    assert turn.finish_reason == "stop"
    assert turn.usage.prompt_tokens == 50
    assert turn.usage.completion_tokens == 10
    assert turn.usage.cached_tokens == 40
    assert turn.latency_ms == 123
    assert factory.timeout.total == 20.0


@pytest.mark.parametrize(
    "message",
    (
        {"content": None},
        {"content": "", "tool_calls": []},
        {"content": "Ответ", "tool_calls": [{"id": "x"}]},
    ),
)
def test_normalizer_rejects_empty_or_tool_output(message: object) -> None:
    from support_agent_provider import ProviderCallError

    adapter, _ = _adapter_with_response(
        {"choices": [{"finish_reason": "stop", "message": message}]}
    )
    with pytest.raises(ProviderCallError):
        asyncio.run(
            adapter.complete_synthesis(messages=SAFE_TWO_MESSAGES, request_timeout=20.0)
        )


@pytest.mark.parametrize(
    "messages",
    (
        ({"role": "user", "content": "one"},),
        (
            {"role": "system", "content": "stable", "name": "extra"},
            {"role": "user", "content": "volatile"},
        ),
        (
            {"role": "user", "content": "wrong"},
            {"role": "system", "content": "order"},
        ),
    ),
)
def test_request_layout_is_closed_and_rejected_before_post(messages) -> None:
    from support_agent_provider import ProviderCallError

    adapter, factory = _adapter_with_response(SAFE_RESPONSE)
    with pytest.raises(ProviderCallError, match="provider_request_invalid"):
        asyncio.run(adapter.complete_synthesis(messages=messages, request_timeout=20.0))
    assert factory.posts == []


def test_timeout_and_complete_payload_bounds_are_enforced_before_post() -> None:
    from support_agent_provider import ProviderCallError

    adapter, factory = _adapter_with_response(SAFE_RESPONSE)
    with pytest.raises(ProviderCallError, match="provider_request_invalid"):
        asyncio.run(
            adapter.complete_synthesis(messages=SAFE_TWO_MESSAGES, request_timeout=20.1)
        )
    oversized = (
        {"role": "system", "content": "stable"},
        {"role": "user", "content": "я" * 30_000},
    )
    with pytest.raises(ProviderCallError, match="provider_request_too_large"):
        asyncio.run(adapter.complete_synthesis(messages=oversized, request_timeout=20.0))
    assert factory.posts == []


@pytest.mark.parametrize(
    ("status", "retryable"),
    ((400, False), (401, False), (403, False), (429, True), (502, True), (503, True), (504, True)),
)
def test_http_status_is_captured_without_reading_response_body(
    status: int,
    retryable: bool,
    caplog,
) -> None:
    from support_agent_provider import ProviderCallError, XCodyChatAdapter

    secret = "upstream private payload sk-do-not-log"
    factory = _FakeSessionFactory(status=status, raw_body=secret.encode("utf-8"))
    adapter = XCodyChatAdapter(config=_config(), session_factory=factory)
    caplog.set_level(logging.WARNING, logger="support_agent_provider")

    with pytest.raises(ProviderCallError) as caught:
        asyncio.run(
            adapter.complete_synthesis(messages=SAFE_TWO_MESSAGES, request_timeout=20.0)
        )

    assert caught.value.code == "provider_http_error"
    assert caught.value.status == status
    assert caught.value.retryable is retryable
    assert factory.response.content._position == 0
    assert secret not in caplog.text
    assert "sk-test-key" not in caplog.text


@pytest.mark.parametrize(
    ("error", "code"),
    (
        (asyncio.TimeoutError("private prompt"), "provider_timeout"),
        (aiohttp.ClientConnectionError("private prompt"), "provider_transport_error"),
    ),
)
def test_timeout_and_transport_failures_are_fixed_and_retryable(
    error: BaseException,
    code: str,
) -> None:
    from support_agent_provider import ProviderCallError, XCodyChatAdapter

    adapter = XCodyChatAdapter(
        config=_config(),
        session_factory=_FakeSessionFactory(post_error=error),
    )
    with pytest.raises(ProviderCallError) as caught:
        asyncio.run(
            adapter.complete_synthesis(messages=SAFE_TWO_MESSAGES, request_timeout=20.0)
        )
    assert caught.value.code == code
    assert caught.value.status == 0
    assert caught.value.retryable is True


@pytest.mark.parametrize(
    "payload",
    (
        {"choices": []},
        {"choices": [{"finish_reason": "length", "message": {"content": "Ответ"}}]},
        {"choices": [{"finish_reason": "stop", "message": []}]},
    ),
)
def test_response_requires_exactly_one_stopped_text_choice(payload: object) -> None:
    from support_agent_provider import ProviderCallError

    adapter, _ = _adapter_with_response(payload)
    with pytest.raises(ProviderCallError):
        asyncio.run(
            adapter.complete_synthesis(messages=SAFE_TWO_MESSAGES, request_timeout=20.0)
        )


def test_oversized_response_and_logs_do_not_expose_provider_body(caplog) -> None:
    from support_agent_provider import ProviderCallError, XCodyChatAdapter

    secret = "vless://private-profile sk-private-token hidden reasoning"
    factory = _FakeSessionFactory(
        raw_body=secret.encode("utf-8"),
        content_length=1_000_000,
    )
    adapter = XCodyChatAdapter(config=_config(), session_factory=factory)
    caplog.set_level(logging.WARNING, logger="support_agent_provider")

    with pytest.raises(ProviderCallError) as caught:
        asyncio.run(
            adapter.complete_synthesis(messages=SAFE_TWO_MESSAGES, request_timeout=20.0)
        )

    assert caught.value.code == "provider_response_too_large"
    assert caught.value.retryable is False
    assert secret not in caplog.text
    assert "sk-test-key" not in caplog.text
