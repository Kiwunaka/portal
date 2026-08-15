from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts import emergency_core_probe_adapter as adapter


EXPECTED_BODY = b"POKROV emergency probe payload v1\n"


def _request(*, transport: str = "tcp") -> dict[str, object]:
    outbound: dict[str, object] = {
        "type": "vless",
        "server": "reserve.example.test",
        "server_port": 443,
        "uuid": "11111111-1111-4111-8111-111111111111",
        "packet_encoding": "xudp",
        "tls": {
            "enabled": True,
            "server_name": "cover.example.test",
            "utls": {"enabled": True, "fingerprint": "chrome"},
            "reality": {
                "enabled": True,
                "public_key": "B" * 43,
                "short_id": "a1b2",
            },
        },
    }
    if transport == "grpc":
        outbound["transport"] = {"type": "grpc", "service_name": "pokrov.test"}
    else:
        outbound["flow"] = "xtls-rprx-vision"
    return {
        "schema_version": adapter.PROBE_SCHEMA,
        "stable_id": "emg_" + ("a" * 24),
        "probe_url": "https://api.pokrov.space/api/emergency-probe/payload-v1",
        "expected_payload_sha256": hashlib.sha256(EXPECTED_BODY).hexdigest(),
        "outbound": outbound,
    }


class _FakeRuntime:
    def __init__(self) -> None:
        self.events: list[str] = []

    def setup(self, _root: Path) -> None:
        self.events.append("setup")

    def secure_file(self, path: Path) -> None:
        assert path.stat().st_size > 0
        self.events.append("secure")

    def start(self, _config_path: Path) -> None:
        self.events.append("start")

    def stop(self) -> None:
        self.events.append("stop")

    def close(self) -> None:
        self.events.append("close")


@pytest.mark.parametrize("transport", ["tcp", "grpc"])
def test_adapter_returns_only_safe_exact_core_result(monkeypatch, transport: str) -> None:
    runtime = _FakeRuntime()
    monkeypatch.setattr(adapter, "_wait_for_listener", lambda _port: None)

    result = adapter.run_adapter(
        _request(transport=transport),
        core_path=Path("synthetic-pokrov-core.dll"),
        runtime_factory=lambda _path: runtime,
        probe=lambda _port, _url, _timeout: (EXPECTED_BODY, "FR"),
    )

    assert result["authenticated"] is True
    assert result["payload_ok"] is True
    assert result["exit_country"] == "FR"
    assert result["verification_source"] == "exact_core_1_0_3"
    assert set(result) == {
        "schema_version",
        "stable_id",
        "authenticated",
        "payload_ok",
        "payload_sha256",
        "exit_country",
        "latency_ms",
        "verified_at",
        "verification_source",
        "error_code",
    }
    assert "reserve.example.test" not in repr(result)
    assert runtime.events == ["setup", "secure", "start", "stop", "close"]


def test_validate_only_cannot_be_mistaken_for_probe_pass(monkeypatch) -> None:
    runtime = _FakeRuntime()
    monkeypatch.setattr(adapter, "_wait_for_listener", lambda _port: None)

    result = adapter.run_adapter(
        _request(),
        core_path=Path("synthetic-pokrov-core.dll"),
        validate_only=True,
        runtime_factory=lambda _path: runtime,
        probe=lambda *_args: pytest.fail("validate-only must not send traffic"),
    )

    assert result == {
        "schema_version": adapter.VALIDATION_SCHEMA,
        "stable_id": "emg_" + ("a" * 24),
        "runtime_accepted": True,
        "core_sha256": adapter.PINNED_CORE_SHA256,
    }
    assert "authenticated" not in result
    assert runtime.events == ["setup", "secure", "start", "stop", "close"]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda outbound: outbound.update({"tag": "attacker"}),
        lambda outbound: outbound.update({"detour": "attacker"}),
        lambda outbound: outbound.update({"warp": {"enabled": True}}),
        lambda outbound: outbound.update({"flow": "xtls-rprx-vision", "transport": {"type": "grpc"}}),
    ],
)
def test_request_rejects_source_routes_warp_and_grpc_flow(mutation) -> None:
    request = _request()
    outbound = request["outbound"]
    assert isinstance(outbound, dict)
    mutation(outbound)

    with pytest.raises(adapter.AdapterFailure, match="outbound_shape_invalid"):
        adapter._validate_request(request)


def test_config_has_one_loopback_inbound_and_no_source_owned_route() -> None:
    request = _request(transport="grpc")
    outbound = request["outbound"]
    assert isinstance(outbound, dict)

    config = adapter._build_config(outbound, listen_port=32123)

    assert config["inbounds"] == [
        {
            "type": "mixed",
            "tag": "emergency-probe-in",
            "listen": "127.0.0.1",
            "listen_port": 32123,
        }
    ]
    assert config["route"]["final"] == "emergency-probe-out"
    assert config["outbounds"][0]["tag"] == "emergency-probe-out"
    assert config["outbounds"][0]["transport"] == {
        "type": "grpc",
        "service_name": "pokrov.test",
    }
    assert "detour" not in config["outbounds"][0]


def test_probe_requires_owned_non_ru_country_header(monkeypatch) -> None:
    class _Response:
        status = 200

        def __init__(self, _socket) -> None:
            pass

        def begin(self) -> None:
            pass

        def read(self, _size: int) -> bytes:
            return EXPECTED_BODY

        def getheader(self, name: str, default: str = "") -> str:
            if name == adapter.PAYLOAD_SCHEMA_HEADER:
                return adapter.PAYLOAD_SCHEMA_VALUE
            return default

    class _TLS:
        def sendall(self, _payload: bytes) -> None:
            pass

        def close(self) -> None:
            pass

    class _SSLContext:
        def wrap_socket(self, _raw, *, server_hostname: str):
            assert server_hostname == adapter.CONTROLLED_HOST
            return _TLS()

    class _Raw:
        def close(self) -> None:
            pass

    monkeypatch.setattr(adapter, "_connect_socks5", lambda *_args: _Raw())
    monkeypatch.setattr(adapter.ssl, "create_default_context", lambda: _SSLContext())
    monkeypatch.setattr(adapter.http.client, "HTTPResponse", _Response)

    with pytest.raises(adapter.AdapterFailure, match="probe_country_unavailable"):
        adapter._probe_through_socks(
            12345,
            "https://api.pokrov.space/api/emergency-probe/payload-v1",
        )
