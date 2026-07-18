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
        timeout_seconds=12.0,
        max_output_tokens=700,
    )


def _complete(factory: _FakeSessionFactory, *, clock=None):
    from support_agent_provider import XCodyChatAdapter

    adapter = XCodyChatAdapter(config=_config(), session_factory=factory, monotonic=clock)
    return asyncio.run(
        adapter.complete(
            messages=(
                {"role": "system", "content": "stable"},
                {"role": "user", "content": "question"},
            ),
            tools=(
                {
                    "type": "function",
                    "function": {
                        "name": "search_support_docs",
                        "parameters": {"type": "object", "additionalProperties": False},
                    },
                },
            ),
            tool_choice="auto",
            request_timeout=3.5,
        )
    )


def test_exact_xcody_request_and_final_answer_normalization() -> None:
    payload = {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": '{"status":"answer"}'},
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "cached_tokens": 7,
            "prompt_tokens_details": {"cached_tokens": 81},
        },
    }
    factory = _FakeSessionFactory(payload=payload)
    ticks = iter((10.0, 10.123))

    turn = _complete(factory, clock=lambda: next(ticks))

    assert turn.content == '{"status":"answer"}'
    assert turn.finish_reason == "stop"
    assert turn.tool_calls == ()
    assert turn.normalized_assistant_message == {
        "role": "assistant",
        "content": '{"status":"answer"}',
    }
    assert turn.usage.prompt_tokens == 100
    assert turn.usage.completion_tokens == 20
    assert turn.usage.cached_tokens == 81
    assert turn.latency_ms == 123
    assert factory.timeout.total == 3.5
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
                    {"role": "user", "content": "question"},
                ],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "search_support_docs",
                            "parameters": {"type": "object", "additionalProperties": False},
                        },
                    }
                ],
                "tool_choice": "auto",
                "max_tokens": 700,
                "n": 1,
                "reasoning_effort": "medium",
            },
        }
    ]


def test_one_function_call_and_top_level_cached_tokens_are_normalized() -> None:
    raw_tool_call = {
        "id": "call_1",
        "type": "function",
        "function": {"name": "search_support_docs", "arguments": '{"query":"dns"}'},
    }
    factory = _FakeSessionFactory(
        payload={
            "choices": [
                {
                    "finish_reason": "tool_calls",
                    "message": {"content": None, "tool_calls": [raw_tool_call]},
                }
            ],
            "usage": {"cached_tokens": 44},
        }
    )

    turn = _complete(factory)

    assert turn.content is None
    assert len(turn.tool_calls) == 1
    assert turn.tool_calls[0].call_id == "call_1"
    assert turn.tool_calls[0].name == "search_support_docs"
    assert turn.tool_calls[0].arguments_json == '{"query":"dns"}'
    assert turn.normalized_assistant_message == {
        "role": "assistant",
        "content": None,
        "tool_calls": [raw_tool_call],
    }
    assert turn.usage.cached_tokens == 44
    assert turn.usage.prompt_tokens is None
    assert turn.usage.completion_tokens is None


def test_provider_requires_exactly_one_choice() -> None:
    from support_agent_provider import ProviderCallError

    factory = _FakeSessionFactory(payload={"choices": []})

    with pytest.raises(ProviderCallError) as caught:
        _complete(factory)

    assert caught.value.code == "provider_choice_count_invalid"
    assert caught.value.retryable is False
    assert caught.value.status == 200


@pytest.mark.parametrize(
    ("status", "retryable"),
    ((400, False), (401, False), (403, False), (429, True), (502, True), (503, True), (504, True)),
)
def test_http_status_classification(status: int, retryable: bool) -> None:
    from support_agent_provider import ProviderCallError

    with pytest.raises(ProviderCallError) as caught:
        _complete(_FakeSessionFactory(status=status, payload={"private": "must-not-be-read"}))

    assert caught.value.code == "provider_http_error"
    assert caught.value.status == status
    assert caught.value.retryable is retryable


@pytest.mark.parametrize(
    ("error", "code"),
    (
        (asyncio.TimeoutError("private prompt"), "provider_timeout"),
        (aiohttp.ClientConnectionError("private prompt"), "provider_transport_error"),
    ),
)
def test_timeout_and_transport_failures_are_retryable(error: BaseException, code: str) -> None:
    from support_agent_provider import ProviderCallError

    with pytest.raises(ProviderCallError) as caught:
        _complete(_FakeSessionFactory(post_error=error))

    assert caught.value.code == code
    assert caught.value.status == 0
    assert caught.value.retryable is True


def test_oversized_response_and_logs_do_not_expose_provider_body(caplog) -> None:
    from support_agent_provider import ProviderCallError

    secret = "vless://private-profile sk-private-token hidden reasoning"
    factory = _FakeSessionFactory(
        raw_body=secret.encode("utf-8"),
        content_length=1_000_000,
    )
    caplog.set_level(logging.WARNING, logger="support_agent_provider")

    with pytest.raises(ProviderCallError) as caught:
        _complete(factory)

    assert caught.value.code == "provider_response_too_large"
    assert caught.value.retryable is False
    assert caught.value.status == 200
    assert "provider_response_too_large" in caplog.text
    assert secret not in caplog.text
    assert "sk-test-key" not in caplog.text
