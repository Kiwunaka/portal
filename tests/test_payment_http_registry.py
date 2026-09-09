from __future__ import annotations

import asyncio
import importlib
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_ROOT = REPO_ROOT / "portal_bot"
if str(PORTAL_ROOT) not in sys.path:
    sys.path.insert(0, str(PORTAL_ROOT))

from outbound_http import (  # noqa: E402
    OutboundHttpError,
    OutboundHttpPolicy,
    PaymentHttpRegistry,
    payment_http_policies_from_env,
)


class _FakeContent:
    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = list(chunks)

    async def iter_chunked(self, _size: int):
        for chunk in self._chunks:
            yield chunk


class _FakeResponse:
    def __init__(self, *, status: int, chunks: list[bytes]) -> None:
        self.status = status
        self.content = _FakeContent(chunks)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class _FakeSession:
    def __init__(self, responses: list[_FakeResponse], **kwargs) -> None:
        self.responses = responses
        self.kwargs = kwargs
        self.closed = False
        self.posts: list[tuple[str, dict]] = []

    def post(self, url: str, **kwargs):
        self.posts.append((url, kwargs))
        return self.responses.pop(0)

    async def close(self) -> None:
        self.closed = True


def _policy(*, max_response_bytes: int = 1024) -> OutboundHttpPolicy:
    return OutboundHttpPolicy(
        total_seconds=12,
        connect_seconds=3,
        sock_read_seconds=7,
        pool_limit=4,
        max_response_bytes=max_response_bytes,
    )


def test_payment_http_policy_env_is_bounded_and_provider_specific(monkeypatch) -> None:
    monkeypatch.setenv("PAYMENT_HTTP_CONNECT_TIMEOUT_SECONDS", "999")
    monkeypatch.setenv("PAYMENT_HTTP_SOCK_READ_TIMEOUT_SECONDS", "0")
    monkeypatch.setenv("PAYMENT_HTTP_POOL_LIMIT", "999")
    monkeypatch.setenv("PAYMENT_HTTP_MAX_RESPONSE_BYTES", "1")
    monkeypatch.setenv("LAVATOP_REQUEST_TIMEOUT_SECONDS", "7")
    monkeypatch.setenv("CARDLINK_REQUEST_TIMEOUT_SECONDS", "13")

    policies = payment_http_policies_from_env()

    assert set(policies) == {"lavatop", "cardlink", "pally", "platima", "freekassa"}
    assert policies["lavatop"].total_seconds == 7
    assert policies["cardlink"].total_seconds == 13
    assert policies["lavatop"].connect_seconds == 7
    assert policies["lavatop"].sock_read_seconds == 1
    assert policies["lavatop"].pool_limit == 100
    assert policies["lavatop"].max_response_bytes == 1024


def test_registry_lifecycle_reuses_sessions_and_emits_safe_telemetry() -> None:
    body = json.dumps({"paymentUrl": "https://checkout.example/pay/1"}).encode()
    responses = [
        _FakeResponse(status=201, chunks=[body]),
        _FakeResponse(status=201, chunks=[body]),
    ]
    sessions: list[_FakeSession] = []
    connectors: list[dict] = []
    telemetry: list[dict[str, int | str]] = []

    def connector_factory(**kwargs):
        connectors.append(dict(kwargs))
        return object()

    def session_factory(**kwargs):
        session = _FakeSession(responses, **kwargs)
        sessions.append(session)
        return session

    registry = PaymentHttpRegistry(
        policies={"lavatop": _policy()},
        session_factory=session_factory,
        connector_factory=connector_factory,
        telemetry_sink=telemetry.append,
    )

    async def run() -> None:
        await registry.start()
        await registry.start()
        for _ in range(2):
            result = await registry.post_object(
                provider="lavatop",
                operation="create_invoice",
                url="https://provider.example/invoice?token=must-not-escape",
                headers={"Authorization": "must-not-escape"},
                json_body={"secret": "must-not-escape"},
            )
            assert result.status == 201
        await registry.close()

    asyncio.run(run())

    assert len(sessions) == 1
    assert len(sessions[0].posts) == 2
    assert sessions[0].closed is True
    assert connectors == [{"limit": 4, "limit_per_host": 4, "ttl_dns_cache": 300}]
    assert telemetry == [
        {
            "provider": "lavatop",
            "operation": "create_invoice",
            "status": 201,
            "latency_ms": telemetry[0]["latency_ms"],
            "result_code": "ok",
        },
        {
            "provider": "lavatop",
            "operation": "create_invoice",
            "status": 201,
            "latency_ms": telemetry[1]["latency_ms"],
            "result_code": "ok",
        },
    ]
    serialized = json.dumps(
        {"events": telemetry, "snapshot": registry.telemetry_snapshot()}
    )
    assert "must-not-escape" not in serialized
    assert "url" not in serialized.lower()
    assert registry.started is False


@pytest.mark.parametrize(
    ("chunks", "code"),
    [
        ([b"x" * 1025], "response_too_large"),
        ([b"not-json"], "response_invalid_json"),
        ([b"[]"], "response_not_object"),
    ],
)
def test_registry_rejects_unbounded_or_malformed_response(chunks, code) -> None:
    responses = [_FakeResponse(status=200, chunks=chunks)]
    telemetry: list[dict[str, int | str]] = []
    session = _FakeSession(responses)
    registry = PaymentHttpRegistry(
        policies={"lavatop": _policy(max_response_bytes=1024)},
        session_factory=lambda **_kwargs: session,
        connector_factory=lambda **_kwargs: object(),
        telemetry_sink=telemetry.append,
    )

    async def run() -> None:
        await registry.start()
        with pytest.raises(OutboundHttpError, match=code):
            await registry.post_object(
                provider="lavatop",
                operation="create_invoice",
                url="https://provider.example/invoice",
            )
        await registry.close()

    asyncio.run(run())
    assert telemetry[0]["result_code"] == code
    assert set(telemetry[0]) == {
        "provider",
        "operation",
        "status",
        "latency_ms",
        "result_code",
    }


def test_payment_provider_surface_has_no_per_request_session_or_raw_body_log() -> None:
    provider_source = (PORTAL_ROOT / "payment_providers.py").read_text(encoding="utf-8")
    route_source = (PORTAL_ROOT / "api_client_routes.py").read_text(encoding="utf-8")
    api_source = (PORTAL_ROOT / "api.py").read_text(encoding="utf-8")
    freekassa_helper = api_source.split("async def _freekassa_api_request", 1)[1].split(
        "async def _telegram_send_message", 1
    )[0]

    assert "ClientSession(" not in provider_source
    assert "raw[:" not in provider_source
    assert "body=%s" not in provider_source
    assert "ClientSession(" not in freekassa_helper
    assert "body=%s" not in freekassa_helper
    assert "http_registry=getattr(request.app.state" in route_source
    assert "lifespan=_api_lifespan" in api_source


def test_api_lifespan_starts_and_closes_payment_registry(monkeypatch) -> None:
    from fastapi.testclient import TestClient

    api = importlib.import_module("api")
    events: list[str] = []

    class FakeRegistry:
        async def start(self) -> None:
            events.append("start")

        async def close(self) -> None:
            events.append("close")

    monkeypatch.setattr(api, "PaymentHttpRegistry", FakeRegistry)
    with TestClient(api.app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["payment_db"]["active"] >= 0
        assert all(
            type(value) is int for value in response.json()["payment_db"].values()
        )
        assert isinstance(api.app.state.payment_http_registry, FakeRegistry)
        monitor = api.app.state.event_loop_lag_monitor
        lag = response.json()["event_loop_lag"]
        assert set(lag) == {
            "status", "interval_ms", "samples", "last_lag_ms", "max_lag_ms", "lag_total_ms"
        }
        assert lag["interval_ms"] == 1000
        assert lag["status"] in {"warming_up", "collecting"}
        assert events == ["start"]

    assert api.app.state.payment_http_registry is None
    assert api.app.state.event_loop_lag_monitor is None
    assert monitor.snapshot()["status"] == "stopped"
    assert events == ["start", "close"]
