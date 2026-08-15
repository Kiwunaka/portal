from __future__ import annotations

import hashlib
from contextlib import contextmanager
from pathlib import Path

import pytest

from portal_bot import emergency_linux_probe_adapter as adapter


EXPECTED_BODY = b"POKROV emergency probe payload v1\n"
STABLE_ID = "emg_" + ("a" * 24)


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
        "stable_id": STABLE_ID,
        "probe_url": "https://api.pokrov.space/api/emergency-probe/payload-v1",
        "expected_payload_sha256": hashlib.sha256(EXPECTED_BODY).hexdigest(),
        "outbound": outbound,
    }


@pytest.mark.parametrize("transport", ["tcp", "grpc"])
def test_adapter_returns_only_safe_pinned_engine_result(transport: str) -> None:
    events: list[tuple[str, object]] = []

    @contextmanager
    def runtime_session(*, engine_path: Path, outbound):
        events.append(("engine", engine_path))
        events.append(("outbound", outbound))
        yield 32123

    result = adapter.run_adapter(
        _request(transport=transport),
        runtime_session=runtime_session,
        probe=lambda port, _url, _timeout: (
            EXPECTED_BODY,
            "DE" if port == 32123 else "ZZ",
        ),
    )

    assert result["stable_id"] == STABLE_ID
    assert result["authenticated"] is True
    assert result["payload_ok"] is True
    assert result["exit_country"] == "DE"
    assert result["verification_source"] == "exact_core_1_13_0_linux"
    assert len(result["verification_source"]) <= 32
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
    assert events[0] == ("engine", adapter.PINNED_ENGINE_PATH)


@pytest.mark.parametrize(
    "stable_id",
    ["a" * 64, "emg_short", "emg_" + ("g" * 24)],
)
def test_adapter_rejects_noncanonical_stable_ids(stable_id: str) -> None:
    request = _request()
    request["stable_id"] = stable_id

    with pytest.raises(adapter.AdapterFailure, match="stable_id_invalid"):
        adapter._validate_request(request)


def test_config_has_one_loopback_inbound_and_no_source_route() -> None:
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
    assert config["outbounds"][0]["transport"] == {
        "type": "grpc",
        "service_name": "pokrov.test",
    }
    assert "detour" not in config["outbounds"][0]


def test_engine_pin_rejects_wrong_size_before_execution(tmp_path, monkeypatch) -> None:
    candidate = tmp_path / adapter.PINNED_ENGINE_PATH.name
    candidate.write_bytes(b"not-the-engine")
    monkeypatch.setattr(adapter, "PINNED_ENGINE_PATH", candidate.resolve())

    with pytest.raises(adapter.AdapterFailure, match="engine_artifact_mismatch"):
        adapter._validate_engine(candidate)


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
            if name == adapter.COUNTRY_HEADER:
                return "RU"
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
