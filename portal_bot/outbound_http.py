from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Callable

import aiohttp


logger = logging.getLogger(__name__)

_OPERATION_RE = re.compile(r"^[a-z][a-z0-9_]{0,31}$")
_PAYMENT_PROVIDERS = ("lavatop", "cardlink", "pally", "platima", "freekassa")


class OutboundHttpError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class OutboundHttpPolicy:
    total_seconds: float
    connect_seconds: float
    sock_read_seconds: float
    pool_limit: int
    max_response_bytes: int

    def timeout(self) -> aiohttp.ClientTimeout:
        return aiohttp.ClientTimeout(
            total=self.total_seconds,
            connect=self.connect_seconds,
            sock_connect=self.connect_seconds,
            sock_read=self.sock_read_seconds,
        )


@dataclass(frozen=True)
class OutboundHttpResult:
    status: int
    body: dict[str, Any]


def _bounded_env_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    try:
        value = int(str(os.getenv(name) or default).strip())
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(value, maximum))


def payment_http_policies_from_env() -> dict[str, OutboundHttpPolicy]:
    connect_seconds = _bounded_env_int(
        "PAYMENT_HTTP_CONNECT_TIMEOUT_SECONDS", 5, minimum=1, maximum=15
    )
    sock_read_seconds = _bounded_env_int(
        "PAYMENT_HTTP_SOCK_READ_TIMEOUT_SECONDS", 15, minimum=1, maximum=60
    )
    pool_limit = _bounded_env_int("PAYMENT_HTTP_POOL_LIMIT", 20, minimum=1, maximum=100)
    max_response_bytes = _bounded_env_int(
        "PAYMENT_HTTP_MAX_RESPONSE_BYTES", 65536, minimum=1024, maximum=262144
    )
    total_names = {
        "lavatop": "LAVATOP_REQUEST_TIMEOUT_SECONDS",
        "cardlink": "CARDLINK_REQUEST_TIMEOUT_SECONDS",
        "pally": "PALLY_REQUEST_TIMEOUT_SECONDS",
        "platima": "PLATIMA_REQUEST_TIMEOUT_SECONDS",
        "freekassa": "FK_API_REQUEST_TIMEOUT_SECONDS",
    }
    policies: dict[str, OutboundHttpPolicy] = {}
    for provider in _PAYMENT_PROVIDERS:
        default_total = 25 if provider == "freekassa" else 30
        total_seconds = _bounded_env_int(
            total_names[provider], default_total, minimum=3, maximum=60
        )
        policies[provider] = OutboundHttpPolicy(
            total_seconds=float(total_seconds),
            connect_seconds=float(min(connect_seconds, total_seconds)),
            sock_read_seconds=float(min(sock_read_seconds, total_seconds)),
            pool_limit=pool_limit,
            max_response_bytes=max_response_bytes,
        )
    return policies


class PaymentHttpRegistry:
    def __init__(
        self,
        *,
        policies: dict[str, OutboundHttpPolicy] | None = None,
        session_factory: Callable[..., aiohttp.ClientSession] = aiohttp.ClientSession,
        connector_factory: Callable[..., aiohttp.BaseConnector] = aiohttp.TCPConnector,
        telemetry_sink: Callable[[dict[str, int | str]], None] | None = None,
    ) -> None:
        self._policies = dict(policies or payment_http_policies_from_env())
        self._session_factory = session_factory
        self._connector_factory = connector_factory
        self._telemetry_sink = telemetry_sink
        self._sessions: dict[str, aiohttp.ClientSession] = {}
        self._metrics: dict[tuple[str, str, int, str], list[int]] = {}

    @property
    def started(self) -> bool:
        return bool(self._sessions)

    async def start(self) -> None:
        if self._sessions:
            return
        created: dict[str, aiohttp.ClientSession] = {}
        try:
            for provider, policy in self._policies.items():
                connector = self._connector_factory(
                    limit=policy.pool_limit,
                    limit_per_host=policy.pool_limit,
                    ttl_dns_cache=300,
                )
                created[provider] = self._session_factory(
                    timeout=policy.timeout(),
                    connector=connector,
                )
        except Exception:
            for session in created.values():
                await session.close()
            raise
        self._sessions = created

    async def close(self) -> None:
        sessions = list(self._sessions.values())
        self._sessions = {}
        for session in sessions:
            await session.close()

    async def __aenter__(self) -> PaymentHttpRegistry:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    def telemetry_snapshot(self) -> list[dict[str, int | str]]:
        rows: list[dict[str, int | str]] = []
        for (provider, operation, status, result_code), values in sorted(self._metrics.items()):
            rows.append(
                {
                    "provider": provider,
                    "operation": operation,
                    "status": status,
                    "result_code": result_code,
                    "count": values[0],
                    "latency_total_ms": values[1],
                    "latency_max_ms": values[2],
                }
            )
        return rows

    def _record(
        self,
        *,
        provider: str,
        operation: str,
        status: int,
        result_code: str,
        latency_ms: int,
    ) -> None:
        key = (provider, operation, max(0, int(status)), result_code)
        metric = self._metrics.setdefault(key, [0, 0, 0])
        metric[0] += 1
        metric[1] += max(0, int(latency_ms))
        metric[2] = max(metric[2], max(0, int(latency_ms)))
        event: dict[str, int | str] = {
            "provider": provider,
            "operation": operation,
            "status": key[2],
            "latency_ms": max(0, int(latency_ms)),
            "result_code": result_code,
        }
        logger.info(
            "outbound_http provider=%s operation=%s status=%s latency_ms=%s result_code=%s",
            provider,
            operation,
            key[2],
            event["latency_ms"],
            result_code,
        )
        if self._telemetry_sink is not None:
            try:
                self._telemetry_sink(dict(event))
            except Exception:
                logger.warning("outbound_http telemetry_sink_failed")

    async def post_object(
        self,
        *,
        provider: str,
        operation: str,
        url: str,
        headers: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
        form_body: Any | None = None,
    ) -> OutboundHttpResult:
        provider_key = str(provider or "").strip().lower()
        operation_key = str(operation or "").strip().lower()
        if provider_key not in self._policies or not _OPERATION_RE.fullmatch(operation_key):
            raise OutboundHttpError("request_policy_unknown")
        session = self._sessions.get(provider_key)
        if session is None:
            raise OutboundHttpError("client_not_started")
        if json_body is not None and form_body is not None:
            raise OutboundHttpError("request_body_conflict")

        policy = self._policies[provider_key]
        started_at = time.perf_counter()
        status = 0
        result_code = "client_error"
        try:
            kwargs: dict[str, Any] = {"headers": dict(headers or {})}
            if json_body is not None:
                kwargs["json"] = json_body
            if form_body is not None:
                kwargs["data"] = form_body
            async with session.post(url, **kwargs) as response:
                status = max(0, int(response.status))
                body = await _read_bounded_json_object(
                    response,
                    max_bytes=policy.max_response_bytes,
                )
            result_code = "ok" if status < 400 else "http_error"
            return OutboundHttpResult(status=status, body=body)
        except OutboundHttpError as exc:
            result_code = exc.code
            raise
        except TimeoutError as exc:
            result_code = "timeout"
            raise OutboundHttpError(result_code) from exc
        except aiohttp.ClientError as exc:
            result_code = "client_error"
            raise OutboundHttpError(result_code) from exc
        finally:
            self._record(
                provider=provider_key,
                operation=operation_key,
                status=status,
                result_code=result_code,
                latency_ms=int((time.perf_counter() - started_at) * 1000),
            )


async def _read_bounded_json_object(response: Any, *, max_bytes: int) -> dict[str, Any]:
    raw = bytearray()
    async for chunk in response.content.iter_chunked(min(8192, max_bytes + 1)):
        raw.extend(chunk)
        if len(raw) > max_bytes:
            raise OutboundHttpError("response_too_large")
    try:
        body = json.loads(bytes(raw).decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OutboundHttpError("response_invalid_json") from exc
    if not isinstance(body, dict):
        raise OutboundHttpError("response_not_object")
    return body
