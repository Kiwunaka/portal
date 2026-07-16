from __future__ import annotations

import importlib.util
import io
import json
import os
import socket
import stat
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
PORTAL_DIR = REPO_ROOT / "portal_bot"
for import_path in (SCRIPTS_DIR, PORTAL_DIR):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from internal_request_auth import sign_internal_request  # noqa: E402
from ru_probe_contract import (  # noqa: E402
    ALLOWED_STAGES,
    canonical_json_bytes,
    endpoint_fingerprint,
    manifest_revision,
    validate_run_payload,
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def runner():
    return _load_module("ru_probe_runner_task7", SCRIPTS_DIR / "ru_probe_runner.py")


@pytest.fixture
def hmac_client():
    path = SCRIPTS_DIR / "internal_hmac_client.py"
    assert path.exists(), "Task 7 must provide the shared exact-byte HMAC client"
    return _load_module("internal_hmac_client_task7", path)


def _endpoint(
    *,
    mode: str = "delivery_tls",
    host: str = "203.0.113.20",
    sni: str | None = "front.example.net",
    profile: str = "legacy_reality_fallback",
    local_profile: str | None = None,
) -> dict[str, object]:
    return {
        "host": host,
        "port": 443,
        "sni": sni,
        "address_families": ["ipv4", "ipv6"],
        "transport_profile": profile,
        "probe_mode": mode,
        "http_path": (
            "/probe"
            if mode == "xhttp_handshake"
            else ("/" if mode in {"google_https", "canonical_https_large_body"} else None)
        ),
        "min_body_bytes": (
            65536 if mode in {"google_https", "canonical_https_large_body"} else None
        ),
        "local_probe_profile_id": local_profile,
    }


def _target(
    *,
    mode: str = "delivery_tls",
    target_id: str = "node:nl",
    target_kind: str = "delivery_node",
    node_code: str | None = "nl",
    profile: str = "legacy_reality_fallback",
    local_profile: str | None = None,
) -> dict[str, object]:
    endpoint = _endpoint(
        mode=mode,
        profile=profile,
        local_profile=local_profile,
        host=(
            "google.com"
            if mode == "google_https"
            else (
                "canonical.example.net"
                if mode == "canonical_https_large_body"
                else (
                    "reserve.example.net"
                    if mode in {"xhttp_handshake", "hysteria_handshake"}
                    else "203.0.113.20"
                )
            )
        ),
        sni=(
            "google.com"
            if mode == "google_https"
            else (
                "canonical.example.net"
                if mode == "canonical_https_large_body"
                else (
                    "reserve.example.net"
                    if mode in {"xhttp_handshake", "hysteria_handshake"}
                    else "front.example.net"
                )
            )
        ),
    )
    required_by_mode = {
        "google_https": ["dns", "tcp", "tls", "http_large_body"],
        "canonical_https_large_body": ["dns", "tcp", "tls", "http_large_body"],
        "delivery_tls": ["dns", "tcp", "tls"],
        "xhttp_handshake": ["dns", "tcp", "tls", "transport_handshake"],
        "hysteria_handshake": ["dns", "transport_handshake"],
    }
    return {
        "target_id": target_id,
        "target_kind": target_kind,
        "scope": "release_required",
        "node_code": node_code,
        "endpoint": endpoint,
        "endpoint_fingerprint": endpoint_fingerprint(endpoint),
        "required_stages": required_by_mode[mode],
    }


def _manifest(*, generated_at: datetime, target: dict[str, object] | None = None):
    targets = [target or _target()]
    return {
        "manifest_schema_version": 1,
        "manifest_revision": manifest_revision(targets),
        "generated_at": generated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "max_cache_age_seconds": 3600,
        "targets": targets,
    }


def _passing_dataplane_result() -> dict[str, object]:
    return {
        "ok": True,
        "stage": "reality_target",
        "error_kind": "",
        "error_message": "",
        "resolved_ips": ["203.0.113.20"],
        "latency_ms": 20,
        "tls_protocol": "TLSv1.3",
        "tls_cipher": "TLS_AES_256_GCM_SHA384",
        "connected_ip": "203.0.113.20",
    }


def _python_adapter_registry(
    profile_id: str,
    script: str,
) -> dict[str, object]:
    return {
        "profiles": {
            profile_id: {
                "executable": str(Path(sys.executable).resolve()),
                "argv": ["-c", script],
            }
        }
    }


def test_delivery_tcp_success_does_not_mask_tls_failure(runner) -> None:
    with mock.patch.object(
        runner.dataplane_probe,
        "probe_node_endpoint",
        return_value={
            "ok": False,
            "stage": "tls",
            "error_kind": "tls_handshake_failed",
            "error_message": "handshake failed",
            "resolved_ips": ["203.0.113.20"],
            "latency_ms": 20,
            "tls_protocol": "",
            "tls_cipher": "",
            "connected_ip": "203.0.113.20",
        },
    ):
        result = runner.run_manifest_target(
            _target(), timeout_sec=5.0, profile_registry={}
        )

    assert result["stages"]["tcp"]["status"] == "pass"
    assert result["stages"]["tls"]["status"] == "fail"


def test_delivery_forbidden_connected_family_cannot_pass_required_stages(
    runner,
) -> None:
    target = _target()
    target["endpoint"]["address_families"] = ["ipv4"]
    target["endpoint_fingerprint"] = endpoint_fingerprint(target["endpoint"])
    with (
        mock.patch.object(
            runner.dataplane_probe,
            "_resolve_dns",
            return_value={
                "resolved_ips": ["2001:db8::20"],
                "resolved_ipv4": [],
                "resolved_ipv6": ["2001:db8::20"],
            },
        ),
        mock.patch.object(
            runner.dataplane_probe,
            "probe_node_endpoint",
            return_value={
                **_passing_dataplane_result(),
                "resolved_ips": ["2001:db8::20"],
                "connected_ip": "2001:db8::20",
            },
        ),
    ):
        result = runner.run_manifest_target(
            target,
            timeout_sec=5.0,
            profile_registry={},
        )

    assert result["address_family_status"]["ipv4"] == "fail"
    assert result["address_family_status"]["ipv6"] == "not_applicable"
    assert result["stages"]["tcp"]["status"] != "pass"
    assert result["stages"]["tls"]["status"] != "pass"


def test_delivery_attempts_each_requested_family_and_reports_actual_outcome(
    runner,
) -> None:
    target = _target()
    calls: list[str] = []

    def probe(*, host, port, sni, timeout_sec):
        calls.append(host)
        if host == "203.0.113.20":
            return _passing_dataplane_result()
        return {
            "ok": False,
            "stage": "tls",
            "error_kind": "tls_handshake_failed",
            "error_message": "private",
            "resolved_ips": ["2001:db8::20"],
            "latency_ms": 25,
            "tls_protocol": "",
            "tls_cipher": "",
            "connected_ip": "2001:db8::20",
        }

    with (
        mock.patch.object(
            runner.dataplane_probe,
            "_resolve_dns",
            return_value={
                "resolved_ips": ["203.0.113.20", "2001:db8::20"],
                "resolved_ipv4": ["203.0.113.20"],
                "resolved_ipv6": ["2001:db8::20"],
            },
        ),
        mock.patch.object(
            runner.dataplane_probe,
            "probe_node_endpoint",
            side_effect=probe,
        ),
    ):
        result = runner.run_manifest_target(
            target,
            timeout_sec=5.0,
            profile_registry={},
        )

    assert set(calls) == {"203.0.113.20", "2001:db8::20"}
    assert result["address_family_status"] == {
        "ipv4": "pass",
        "ipv6": "fail",
    }
    assert result["stages"]["tls"]["status"] == "pass"


def test_udp_send_without_valid_protocol_response_is_not_hysteria_pass(runner) -> None:
    result = runner.transport_stage_from_adapter(
        "hysteria_handshake",
        {
            "handshake_status": "not_run",
            "classification": "viability_hint",
            "detail_code": "sent_no_response",
        },
    )
    assert result["status"] == "not_run"


def test_transport_pass_requires_valid_protocol_response_metadata(runner) -> None:
    result = runner.transport_stage_from_adapter(
        "hysteria_handshake",
        {
            "handshake_status": "pass",
            "classification": "ok",
            "detail_code": None,
        },
    )
    assert result["status"] == "fail"
    assert result["code"] == "adapter_malformed_response"


def test_large_body_probe_uses_get_and_reads_at_least_65536_bytes(runner) -> None:
    chunks = [b"a" * 32768, b"b" * 32768]

    class FakeResponse:
        status = 200

        def read(self, _size: int) -> bytes:
            return chunks.pop(0) if chunks else b""

    connection = mock.Mock()
    connection.getresponse.return_value = FakeResponse()
    with (
        mock.patch.object(
            runner.socket,
            "getaddrinfo",
            return_value=[
                (
                    socket.AF_INET,
                    socket.SOCK_STREAM,
                    socket.IPPROTO_TCP,
                    "",
                    ("203.0.113.20", 443),
                )
            ],
        ),
        mock.patch.object(
            runner, "_verified_https_connection", return_value=connection
        ),
    ):
        result = runner.probe_https_large_body(
            host="canonical.example.net",
            port=443,
            sni="canonical.example.net",
            path="/download",
            min_body_bytes=65536,
            address_families=["ipv4"],
            timeout_sec=5.0,
        )

    connection.request.assert_called_once()
    request_args, _ = connection.request.call_args
    assert request_args[0] == "GET"
    assert "HEAD" not in request_args
    assert result["body_bytes"] >= 65536
    assert result["stages"]["http_large_body"]["status"] == "pass"


def test_large_body_probe_connects_only_to_manifest_allowed_family(runner) -> None:
    response = mock.Mock(status=200)
    response.read.side_effect = [b"x" * 65536]
    connection = mock.Mock()
    connection.getresponse.return_value = response
    with (
        mock.patch.object(
            runner.socket,
            "getaddrinfo",
            return_value=[
                (
                    socket.AF_INET6,
                    socket.SOCK_STREAM,
                    socket.IPPROTO_TCP,
                    "",
                    ("2001:db8::20", 443, 0, 0),
                ),
                (
                    socket.AF_INET,
                    socket.SOCK_STREAM,
                    socket.IPPROTO_TCP,
                    "",
                    ("203.0.113.20", 443),
                ),
            ],
        ),
        mock.patch.object(
            runner,
            "_verified_https_connection",
            return_value=connection,
        ) as connection_factory,
    ):
        runner.probe_https_large_body(
            host="canonical.example.net",
            port=443,
            sni="canonical.example.net",
            path="/download",
            min_body_bytes=65536,
            address_families=["ipv4"],
            timeout_sec=5.0,
        )

    assert connection_factory.call_args.kwargs["host"] == "203.0.113.20"


def test_large_body_probe_attempts_each_requested_family(runner) -> None:
    calls: list[str] = []

    def connection_factory(*, host, port, sni, timeout_sec):
        calls.append(host)
        connection = mock.Mock()
        if ":" in host:
            connection.connect.side_effect = OSError("ipv6 unavailable")
            return connection
        response = mock.Mock(status=200)
        response.read.side_effect = [b"x" * 65536]
        connection.getresponse.return_value = response
        return connection

    with (
        mock.patch.object(
            runner.socket,
            "getaddrinfo",
            return_value=[
                (
                    socket.AF_INET,
                    socket.SOCK_STREAM,
                    socket.IPPROTO_TCP,
                    "",
                    ("203.0.113.20", 443),
                ),
                (
                    socket.AF_INET6,
                    socket.SOCK_STREAM,
                    socket.IPPROTO_TCP,
                    "",
                    ("2001:db8::20", 443, 0, 0),
                ),
            ],
        ),
        mock.patch.object(
            runner,
            "_verified_https_connection",
            side_effect=connection_factory,
        ),
    ):
        result = runner.probe_https_large_body(
            host="canonical.example.net",
            port=443,
            sni="canonical.example.net",
            path="/download",
            min_body_bytes=65536,
            address_families=["ipv4", "ipv6"],
            timeout_sec=5.0,
        )

    assert set(calls) == {"203.0.113.20", "2001:db8::20"}
    assert result["address_family_status"] == {
        "ipv4": "pass",
        "ipv6": "fail",
    }
    assert result["stages"]["http_large_body"]["status"] == "pass"


def test_https_probe_uses_default_verifying_tls_context(runner) -> None:
    context = mock.Mock()
    context.check_hostname = True
    context.verify_mode = runner.ssl.CERT_REQUIRED
    with mock.patch.object(runner.ssl, "create_default_context", return_value=context):
        connection = runner._verified_https_connection(
            host="203.0.113.20",
            port=443,
            sni="canonical.example.net",
            timeout_sec=5.0,
        )

    assert connection._context is context
    assert connection._manifest_server_hostname == "canonical.example.net"
    assert context.verify_mode != runner.ssl.CERT_NONE


def test_manifest_target_initializes_required_and_nonrequired_stages_strictly(
    runner,
) -> None:
    with mock.patch.object(
        runner.dataplane_probe,
        "probe_node_endpoint",
        return_value=_passing_dataplane_result(),
    ):
        result = runner.run_manifest_target(
            _target(), timeout_sec=5.0, profile_registry={}
        )

    assert set(result["stages"]) == set(ALLOWED_STAGES)
    assert result["stages"]["dns"]["status"] == "pass"
    assert result["stages"]["tcp"]["status"] == "pass"
    assert result["stages"]["tls"]["status"] == "pass"
    assert result["stages"]["http_large_body"]["status"] == "not_applicable"
    assert result["stages"]["transport_handshake"]["status"] == "not_applicable"


def test_required_stage_not_executed_by_probe_mode_remains_not_run(runner) -> None:
    target = _target(
        mode="canonical_https_large_body",
        target_id="canonical:sample",
        target_kind="canonical_public",
        node_code=None,
        profile="https",
    )
    target["required_stages"].append("transport_handshake")
    https_result = {
        "stages": {
            "dns": {"status": "pass", "latency_ms": 1, "code": None},
            "tcp": {"status": "pass", "latency_ms": 2, "code": None},
            "tls": {"status": "pass", "latency_ms": 3, "code": None},
            "http_large_body": {"status": "pass", "latency_ms": 4, "code": None},
            "transport_handshake": {
                "status": "not_applicable",
                "latency_ms": None,
                "code": None,
            },
        },
        "address_family_status": {"ipv4": "pass", "ipv6": "not_run"},
    }
    with mock.patch.object(
        runner,
        "probe_https_large_body",
        return_value=https_result,
    ):
        result = runner.run_manifest_target(
            target,
            timeout_sec=5.0,
            profile_registry={},
        )

    assert result["stages"]["transport_handshake"]["status"] == "not_run"


def test_manifest_endpoint_and_fingerprint_are_copied_exactly(runner) -> None:
    target = _target()
    with mock.patch.object(
        runner.dataplane_probe,
        "probe_node_endpoint",
        return_value=_passing_dataplane_result(),
    ):
        result = runner.run_manifest_target(
            target, timeout_sec=5.0, profile_registry={}
        )

    assert result["endpoint"] == target["endpoint"]
    assert result["endpoint"] is not target["endpoint"]
    assert result["endpoint_fingerprint"] == target["endpoint_fingerprint"]


def test_missing_profile_is_not_run_probe_material_unavailable(runner) -> None:
    target = _target(
        mode="hysteria_handshake",
        target_id="reserve:hysteria",
        target_kind="reserve_hysteria",
        node_code=None,
        profile="hysteria2",
        local_profile="reserve-hysteria",
    )
    with mock.patch.object(
        runner.dataplane_probe,
        "_resolve_dns",
        return_value={
            "resolved_ips": ["203.0.113.30"],
            "resolved_ipv4": ["203.0.113.30"],
            "resolved_ipv6": [],
        },
    ):
        result = runner.run_manifest_target(
            target, timeout_sec=5.0, profile_registry={}
        )

    transport = result["stages"]["transport_handshake"]
    assert transport["status"] == "not_run"
    assert transport["code"] == "probe_material_unavailable"
    assert result["transport"]["handshake_status"] == "not_run"


def test_xhttp_adapter_receives_selected_allowed_family_address(runner) -> None:
    target = _target(
        mode="xhttp_handshake",
        target_id="reserve:xhttp",
        target_kind="reserve_xhttp",
        node_code=None,
        profile="reserve_xhttp_cdn",
        local_profile="reserve-xhttp",
    )
    target["endpoint"]["address_families"] = ["ipv4"]
    target["endpoint_fingerprint"] = endpoint_fingerprint(target["endpoint"])
    adapter_endpoints: list[dict[str, object]] = []

    def adapter(mode, endpoint, **_kwargs):
        adapter_endpoints.append(endpoint)
        return {
            "schema_version": 1,
            "profile_id": "reserve-xhttp",
            "protocol": "xhttp",
            "handshake_status": "pass",
            "classification": "ok",
            "detail_code": None,
        }

    with (
        mock.patch.object(
            runner.dataplane_probe,
            "_resolve_dns",
            return_value={
                "resolved_ips": ["203.0.113.30"],
                "resolved_ipv4": ["203.0.113.30"],
                "resolved_ipv6": [],
            },
        ),
        mock.patch.object(
            runner.dataplane_probe,
            "probe_node_endpoint",
            return_value={
                **_passing_dataplane_result(),
                "resolved_ips": ["203.0.113.30"],
                "connected_ip": "203.0.113.30",
            },
        ),
        mock.patch.object(
            runner,
            "run_transport_adapter",
            side_effect=adapter,
        ),
    ):
        result = runner.run_manifest_target(
            target,
            timeout_sec=5.0,
            profile_registry={"profiles": {}},
        )

    assert result["stages"]["transport_handshake"]["status"] == "pass"
    assert adapter_endpoints[0]["host"] == "203.0.113.30"
    assert adapter_endpoints[0]["address_families"] == ["ipv4"]


def test_protocol_adapter_uses_safe_fixed_argv_and_validates_response(
    runner,
) -> None:
    endpoint = _endpoint(
        mode="hysteria_handshake",
        host="reserve.example.net",
        sni="reserve.example.net",
        profile="hysteria2",
        local_profile="reserve-hysteria",
    )
    response = {
        "schema_version": 1,
        "profile_id": "reserve-hysteria",
        "protocol": "hysteria2",
        "handshake_status": "pass",
        "classification": "ok",
        "detail_code": None,
    }
    expected_input = canonical_json_bytes(endpoint)
    response_bytes = canonical_json_bytes(response)
    script = (
        "import sys;"
        "payload=sys.stdin.buffer.read();"
        f"sys.exit(9) if payload!={expected_input!r} else None;"
        f"sys.stdout.buffer.write({response_bytes!r})"
    )
    registry = _python_adapter_registry("reserve-hysteria", script)
    real_popen = subprocess.Popen
    captured: dict[str, object] = {}
    events: list[str] = []

    def popen(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        events.append("popen")
        process = real_popen(command, **kwargs)
        if os.name == "nt":
            real_stdin = process.stdin
            assert real_stdin is not None

            class RecordingStdin:
                def write(self, data):
                    events.append("gate_write")
                    return real_stdin.write(data)

                def flush(self):
                    return real_stdin.flush()

                def close(self):
                    return real_stdin.close()

            process.stdin = RecordingStdin()
        return process

    if os.name == "nt":
        real_assign = runner._WindowsJobObject.assign
        real_bootstrap = runner._windows_adapter_bootstrap

        def assign(job, process):
            events.append("assign")
            return real_assign(job, process)

        def bootstrap(command, request_bytes):
            captured["adapter_command"] = command
            captured["adapter_input"] = request_bytes
            events.append("bootstrap")
            return real_bootstrap(command, request_bytes)

        with (
            mock.patch.object(runner.subprocess, "Popen", side_effect=popen),
            mock.patch.object(
                runner._WindowsJobObject,
                "assign",
                autospec=True,
                side_effect=assign,
            ),
            mock.patch.object(
                runner,
                "_windows_adapter_bootstrap",
                side_effect=bootstrap,
            ),
        ):
            result = runner.run_transport_adapter(
                "hysteria_handshake",
                endpoint,
                profile_registry=registry,
                timeout_sec=5.0,
            )
    else:
        with mock.patch.object(runner.subprocess, "Popen", side_effect=popen):
            result = runner.run_transport_adapter(
                "hysteria_handshake",
                endpoint,
                profile_registry=registry,
                timeout_sec=5.0,
            )

    assert result == response
    command = captured["command"]
    kwargs = captured["kwargs"]
    assert kwargs["shell"] is False
    assert kwargs["stdin"] is subprocess.PIPE
    assert kwargs["stdout"] is subprocess.PIPE
    assert kwargs["stderr"] is subprocess.PIPE
    if os.name == "nt":
        assert kwargs["creationflags"] & subprocess.CREATE_NEW_PROCESS_GROUP
        assert command == [
            str(Path(sys.executable).resolve()),
            "-I",
            "-c",
            runner._WINDOWS_ADAPTER_WRAPPER,
        ]
        assert captured["adapter_command"] == [
            str(Path(sys.executable).resolve()),
            "-c",
            script,
        ]
        assert captured["adapter_input"] == expected_input
        assert events.index("assign") < events.index("gate_write")
    else:
        assert kwargs["start_new_session"] is True
        assert command == [str(Path(sys.executable).resolve()), "-c", script]


def test_protocol_adapter_accepts_chunked_partial_stdout(
    runner,
) -> None:
    endpoint = _endpoint(
        mode="xhttp_handshake",
        profile="reserve_xhttp_cdn",
        local_profile="reserve-xhttp",
    )
    expected = {
        "schema_version": 1,
        "profile_id": "reserve-xhttp",
        "protocol": "xhttp",
        "handshake_status": "pass",
        "classification": "ok",
        "detail_code": None,
    }
    response_bytes = canonical_json_bytes(expected)
    script = "\n".join(
        [
            "import sys,time",
            "sys.stdin.buffer.read()",
            f"payload={response_bytes!r}",
            "for offset in range(0,len(payload),7):",
            "    sys.stdout.buffer.write(payload[offset:offset+7])",
            "    sys.stdout.buffer.flush()",
            "    time.sleep(0.002)",
        ]
    )

    response = runner.run_transport_adapter(
        "xhttp_handshake",
        endpoint,
        profile_registry=_python_adapter_registry("reserve-xhttp", script),
        timeout_sec=5.0,
    )

    assert response == expected


@pytest.mark.skipif(
    os.name != "nt",
    reason="Windows handle-leak regression",
)
def test_protocol_adapter_normal_exit_does_not_leak_process_handles(
    runner,
) -> None:
    import ctypes
    import gc
    from ctypes import wintypes

    endpoint = _endpoint(
        mode="xhttp_handshake",
        profile="reserve_xhttp_cdn",
        local_profile="reserve-xhttp",
    )
    response = {
        "schema_version": 1,
        "profile_id": "reserve-xhttp",
        "protocol": "xhttp",
        "handshake_status": "pass",
        "classification": "ok",
        "detail_code": None,
    }
    script = (
        "import sys;"
        "sys.stdin.buffer.read();"
        f"sys.stdout.buffer.write({canonical_json_bytes(response)!r})"
    )
    registry = _python_adapter_registry("reserve-xhttp", script)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    get_current_process = kernel32.GetCurrentProcess
    get_current_process.restype = wintypes.HANDLE
    get_process_handle_count = kernel32.GetProcessHandleCount
    get_process_handle_count.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.DWORD),
    ]
    get_process_handle_count.restype = wintypes.BOOL

    def handle_count() -> int:
        count = wintypes.DWORD()
        assert get_process_handle_count(
            get_current_process(),
            ctypes.byref(count),
        )
        return int(count.value)

    assert runner.run_transport_adapter(
        "xhttp_handshake",
        endpoint,
        profile_registry=registry,
        timeout_sec=5.0,
    ) == response
    gc.collect()
    before = handle_count()
    for _ in range(8):
        assert runner.run_transport_adapter(
            "xhttp_handshake",
            endpoint,
            profile_registry=registry,
            timeout_sec=5.0,
        ) == response
    gc.collect()
    time.sleep(0.05)
    after = handle_count()

    assert after <= before + 2


def test_profile_registry_file_can_directly_map_allowlisted_profile_ids(
    runner,
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "profiles.json"
    registry_path.write_text(
        json.dumps(
            {
                "reserve-hysteria": {
                    "executable": "/usr/local/libexec/pokrov-hysteria-probe",
                    "argv": ["--probe"],
                }
            }
        ),
        encoding="utf-8",
    )

    registry = runner.load_profile_registry(registry_path)

    assert set(registry["profiles"]) == {"reserve-hysteria"}
    assert registry["profiles"]["reserve-hysteria"]["argv"] == ["--probe"]


@pytest.mark.parametrize(
    ("script", "expected_code"),
    [
        (
            "import sys;sys.stdin.buffer.read();sys.stdout.write('not-json')",
            "adapter_malformed_response",
        ),
        (
            "import sys;sys.stdin.buffer.read();sys.exit(2)",
            "adapter_exit_nonzero",
        ),
    ],
)
def test_protocol_adapter_malformed_or_failed_process_is_fail(
    runner,
    script: str,
    expected_code: str,
) -> None:
    endpoint = _endpoint(
        mode="xhttp_handshake",
        profile="reserve_xhttp_cdn",
        local_profile="reserve-xhttp",
    )
    response = runner.run_transport_adapter(
        "xhttp_handshake",
        endpoint,
        profile_registry=_python_adapter_registry("reserve-xhttp", script),
        timeout_sec=5.0,
    )

    stage = runner.transport_stage_from_adapter("xhttp_handshake", response)
    assert stage["status"] == "fail"
    assert stage["code"] == expected_code


@pytest.mark.parametrize("stream_name", ["stdout", "stderr"])
def test_protocol_adapter_stops_on_stream_overflow_before_timeout(
    runner,
    stream_name: str,
) -> None:
    endpoint = _endpoint(
        mode="xhttp_handshake",
        profile="reserve_xhttp_cdn",
        local_profile="reserve-xhttp",
    )
    stream = "sys.stdout.buffer" if stream_name == "stdout" else "sys.stderr.buffer"
    script = (
        "import sys,time;"
        "sys.stdin.buffer.read();"
        f"{stream}.write(b'x'*131072);"
        f"{stream}.flush();"
        "time.sleep(10)"
    )

    started = time.monotonic()
    response = runner.run_transport_adapter(
        "xhttp_handshake",
        endpoint,
        profile_registry=_python_adapter_registry("reserve-xhttp", script),
        timeout_sec=1.0,
    )
    elapsed = time.monotonic() - started

    assert response["handshake_status"] == "fail"
    assert response["detail_code"] == "adapter_output_too_large"
    assert elapsed < 1.0


def test_protocol_adapter_timeout_kills_spawned_process_tree(
    runner,
    tmp_path: Path,
) -> None:
    endpoint = _endpoint(
        mode="xhttp_handshake",
        profile="reserve_xhttp_cdn",
        local_profile="reserve-xhttp",
    )
    ready = tmp_path / "timeout-child-ready.txt"
    sentinel = tmp_path / "orphan.txt"
    child = (
        "import os,pathlib,time;"
        "p=pathlib.Path;"
        "p(os.environ['P7TR']).write_text('ready',encoding='utf-8');"
        "time.sleep(1.4);"
        "p(os.environ['P7TS']).write_text('orphan',encoding='utf-8')"
    )
    script = "\n".join(
        [
            "import os,pathlib,subprocess,sys,time",
            "sys.stdin.buffer.read()",
            f"subprocess.Popen([sys.executable,'-c',{child!r}])",
            "ready=pathlib.Path(os.environ['P7TR'])",
            "deadline=time.monotonic()+2.0",
            "while not ready.exists() and time.monotonic()<deadline:",
            "    time.sleep(0.01)",
            "time.sleep(10)",
        ]
    )

    with mock.patch.dict(
        os.environ,
        {"P7TR": str(ready), "P7TS": str(sentinel)},
    ):
        response = runner.run_transport_adapter(
            "xhttp_handshake",
            endpoint,
            profile_registry=_python_adapter_registry("reserve-xhttp", script),
            timeout_sec=1.0,
        )
    deadline = time.monotonic() + 1.8
    while time.monotonic() < deadline and not sentinel.exists():
        time.sleep(0.05)

    assert ready.exists(), "adapter child must start before timeout"
    assert response["detail_code"] == "adapter_timeout"
    assert not sentinel.exists()


@pytest.mark.skipif(
    os.name != "nt",
    reason="Windows Job Object regression",
)
@pytest.mark.parametrize("stream_name", ["stdout", "stderr"])
def test_protocol_adapter_overflow_kills_child_after_parent_exits(
    runner,
    tmp_path: Path,
    stream_name: str,
) -> None:
    endpoint = _endpoint(
        mode="xhttp_handshake",
        profile="reserve_xhttp_cdn",
        local_profile="reserve-xhttp",
    )
    ready = tmp_path / f"{stream_name}-child-ready.txt"
    sentinel = tmp_path / f"{stream_name}-orphan.txt"
    child = (
        "import os,pathlib,time;"
        "p=pathlib.Path;"
        "p(os.environ['P7R']).write_text('ready',encoding='utf-8');"
        "time.sleep(0.8);"
        "p(os.environ['P7S']).write_text('orphan',encoding='utf-8')"
    )
    stream = "sys.stdout.buffer" if stream_name == "stdout" else "sys.stderr.buffer"
    script = "\n".join(
        [
            "import os,pathlib,subprocess,sys,time",
            "sys.stdin.buffer.read()",
            f"subprocess.Popen([sys.executable,'-c',{child!r}])",
            "ready=pathlib.Path(os.environ['P7R'])",
            "deadline=time.monotonic()+2.0",
            "while not ready.exists() and time.monotonic()<deadline:",
            "    time.sleep(0.01)",
            f"{stream}.write(b'x'*131072)",
            f"{stream}.flush()",
            "os._exit(0)",
        ]
    )

    with mock.patch.dict(
        os.environ,
        {"P7R": str(ready), "P7S": str(sentinel)},
    ):
        response = runner.run_transport_adapter(
            "xhttp_handshake",
            endpoint,
            profile_registry=_python_adapter_registry("reserve-xhttp", script),
            timeout_sec=2.0,
        )
    deadline = time.monotonic() + 1.5
    while time.monotonic() < deadline and not sentinel.exists():
        time.sleep(0.05)

    assert ready.exists(), (
        "adapter child must start before overflow; "
        f"response={response!r}"
    )
    assert response["detail_code"] == "adapter_output_too_large"
    assert not sentinel.exists()


def test_manifest_cache_is_atomic_mode_0600_and_freshness_bounded(
    runner, tmp_path: Path
) -> None:
    generated_at = datetime(2026, 7, 16, 8, 0, tzinfo=timezone.utc)
    manifest = _manifest(generated_at=generated_at)
    cache = tmp_path / "manifest-cache.json"

    runner.write_manifest_cache(cache, manifest)

    assert json.loads(cache.read_text(encoding="utf-8")) == manifest
    if os.name != "nt":
        assert stat.S_IMODE(cache.stat().st_mode) == 0o600
    assert not list(tmp_path.glob("*.tmp"))
    assert (
        runner.load_cached_manifest(
            cache, now=generated_at + timedelta(seconds=3600)
        )["manifest_revision"]
        == manifest["manifest_revision"]
    )
    with pytest.raises(runner.ManifestCacheUnavailable):
        runner.load_cached_manifest(
            cache, now=generated_at + timedelta(seconds=3601)
        )


def test_manifest_cache_rejects_materially_future_generated_at(
    runner,
    tmp_path: Path,
) -> None:
    observed_at = datetime(2026, 7, 16, 8, 0, tzinfo=timezone.utc)
    manifest = _manifest(
        generated_at=observed_at + timedelta(minutes=6),
    )
    cache = tmp_path / "manifest-cache.json"
    runner.write_manifest_cache(cache, manifest)

    with pytest.raises(runner.ManifestCacheUnavailable) as error:
        runner.load_cached_manifest(cache, now=observed_at)

    assert error.value.code == "manifest_cache_from_future"


def test_corrupt_manifest_cache_is_unavailable(runner, tmp_path: Path) -> None:
    cache = tmp_path / "manifest-cache.json"
    cache.write_bytes(b'{"manifest_schema_version":1')
    cache.chmod(0o600)

    with pytest.raises(runner.ManifestCacheUnavailable):
        runner.load_cached_manifest(
            cache,
            now=datetime(2026, 7, 16, 8, 0, tzinfo=timezone.utc),
        )


def test_manifest_cache_concurrent_writers_never_share_temp_file(
    runner,
    tmp_path: Path,
) -> None:
    generated_at = datetime(2026, 7, 16, 8, 0, tzinfo=timezone.utc)
    manifests = [
        _manifest(generated_at=generated_at),
        _manifest(generated_at=generated_at + timedelta(seconds=1)),
    ]
    cache = tmp_path / "manifest-cache.json"
    workers = 16
    barrier = threading.Barrier(workers)

    def write(index: int) -> None:
        barrier.wait()
        runner.write_manifest_cache(cache, manifests[index % 2])

    errors: list[BaseException] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(write, index) for index in range(workers)]
        for future in futures:
            try:
                future.result()
            except BaseException as exc:  # pragma: no cover - assertion evidence
                errors.append(exc)

    assert errors == []
    final = runner.load_cached_manifest(
        cache,
        now=generated_at + timedelta(seconds=2),
    )
    assert final in manifests
    assert not list(tmp_path.glob("*.tmp"))


def test_private_output_concurrent_writers_leave_one_exact_artifact(
    runner,
    tmp_path: Path,
) -> None:
    output = tmp_path / "run.json"
    candidates = [b'{"run_id":"a"}', b'{"run_id":"b"}']
    workers = 16
    barrier = threading.Barrier(workers)

    def write(index: int) -> None:
        barrier.wait()
        runner._write_private_bytes(output, candidates[index % 2])

    errors: list[BaseException] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(write, index) for index in range(workers)]
        for future in futures:
            try:
                future.result()
            except BaseException as exc:  # pragma: no cover - assertion evidence
                errors.append(exc)

    assert errors == []
    assert output.read_bytes() in candidates
    assert not list(tmp_path.glob("*.tmp"))


def test_fetch_manifest_signs_get_with_empty_body_and_preserves_revision(
    runner, tmp_path: Path
) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0)
    manifest = _manifest(generated_at=generated_at)
    response = SimpleNamespace(
        status=200,
        body=canonical_json_bytes(manifest),
        headers={},
    )
    cache = tmp_path / "manifest-cache.json"
    with mock.patch.object(
        runner.internal_hmac_client, "signed_request", return_value=response
    ) as signed:
        result = runner.fetch_manifest(
            api_base_url="https://api.example.net",
            key_id="ru-mini-v1",
            secret_file=tmp_path / "hmac.key",
            manifest_cache=cache,
            timeout_sec=5.0,
            now=generated_at,
        )

    _, kwargs = signed.call_args
    assert kwargs["method"] == "GET"
    assert kwargs["path"] == "/api/internal/probes/ru-origin/manifest"
    assert kwargs["raw_body"] == b""
    assert result["manifest_revision"] == manifest["manifest_revision"]
    assert json.loads(cache.read_text(encoding="utf-8"))["manifest_revision"] == (
        manifest["manifest_revision"]
    )


def test_fetch_manifest_uses_only_fresh_cache_on_network_error(
    runner, tmp_path: Path
) -> None:
    generated_at = datetime(2026, 7, 16, 8, 0, tzinfo=timezone.utc)
    manifest = _manifest(generated_at=generated_at)
    cache = tmp_path / "manifest-cache.json"
    runner.write_manifest_cache(cache, manifest)
    with mock.patch.object(
        runner.internal_hmac_client,
        "signed_request",
        side_effect=OSError("network unavailable"),
    ):
        cached = runner.fetch_manifest(
            api_base_url="https://api.example.net",
            key_id="ru-mini-v1",
            secret_file=tmp_path / "hmac.key",
            manifest_cache=cache,
            timeout_sec=5.0,
            now=generated_at + timedelta(minutes=59),
        )
        assert cached["manifest_revision"] == manifest["manifest_revision"]
        with pytest.raises(runner.ManifestCacheUnavailable):
            runner.fetch_manifest(
                api_base_url="https://api.example.net",
                key_id="ru-mini-v1",
                secret_file=tmp_path / "hmac.key",
                manifest_cache=cache,
                timeout_sec=5.0,
                now=generated_at + timedelta(hours=2),
            )


@pytest.mark.parametrize("status_code", [301, 302, 303, 307, 308])
def test_signed_request_redirect_handler_rejects_every_redirect_without_copying(
    hmac_client,
    status_code: int,
) -> None:
    handler_type = getattr(hmac_client, "_RejectRedirectHandler", None)
    assert handler_type is not None
    request = urllib.request.Request(
        "https://api.example.net/api/internal/probes/ru-origin/runs",
        data=b'{"private":"body"}',
        headers={
            "X-Internal-Key-Id": "ru-mini-v1",
            "X-Internal-Signature": "a" * 64,
        },
        method="POST",
    )

    redirected = handler_type().redirect_request(
        request,
        io.BytesIO(b""),
        status_code,
        "redirect",
        {"Location": "http://evil.example/collect"},
        "http://evil.example/collect",
    )

    assert redirected is None


@pytest.mark.parametrize(
    ("method", "raw_body"),
    [
        ("GET", b""),
        ("POST", b'{"schema_version":2}'),
    ],
)
def test_signed_request_uses_no_redirect_opener(
    hmac_client,
    tmp_path: Path,
    method: str,
    raw_body: bytes,
) -> None:
    secret_file = tmp_path / "hmac.key"
    secret_file.write_bytes(b"0123456789abcdef0123456789abcdef")
    secret_file.chmod(0o600)

    class RedirectResponse:
        def open(self, request, *, timeout):
            raise urllib.error.HTTPError(
                request.full_url,
                302,
                "redirect",
                {"Location": "http://evil.example/collect"},
                io.BytesIO(b"redirect"),
            )

    built_handlers: list[object] = []

    def build_opener(*handlers):
        built_handlers.extend(handlers)
        return RedirectResponse()

    with (
        mock.patch.object(
            hmac_client.urllib.request,
            "build_opener",
            side_effect=build_opener,
        ),
        mock.patch.object(
            hmac_client.urllib.request,
            "urlopen",
            side_effect=AssertionError("default redirecting opener used"),
        ),
    ):
        response = hmac_client.signed_request(
            api_base_url="https://api.example.net",
            method=method,
            path="/api/internal/probes/ru-origin/runs",
            key_id="ru-mini-v1",
            secret_file=secret_file,
            raw_body=raw_body,
            timeout_sec=5.0,
        )

    assert response.status == 302
    assert len(built_handlers) == 1
    assert isinstance(built_handlers[0], hmac_client._RejectRedirectHandler)


def test_secret_reader_rejects_symlink(hmac_client, tmp_path: Path) -> None:
    target = tmp_path / "real.key"
    target.write_bytes(b"0123456789abcdef0123456789abcdef")
    target.chmod(0o600)
    link = tmp_path / "hmac.key"
    try:
        link.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"symlink unavailable on this host: {exc}")

    with pytest.raises(hmac_client.InternalHmacClientError) as error:
        hmac_client.read_secret_file(link)

    assert error.value.code == "secret_file_symlink"


@pytest.mark.skipif(
    os.name != "nt",
    reason="Windows reparse-point regression",
)
def test_secret_reader_rejects_raced_symlink_to_same_file(
    hmac_client,
    tmp_path: Path,
) -> None:
    secret = b"0123456789abcdef0123456789abcdef"
    secret_file = tmp_path / "hmac.key"
    backup_file = tmp_path / "hmac-backup.key"
    secret_file.write_bytes(secret)
    secret_file.chmod(0o600)
    symlink_probe = tmp_path / "symlink-probe.key"
    try:
        symlink_probe.symlink_to(secret_file)
    except OSError as exc:
        pytest.skip(f"symlink unavailable on this host: {exc}")
    else:
        symlink_probe.unlink()

    def replace_path_with_same_file_symlink() -> None:
        os.replace(secret_file, backup_file)
        secret_file.symlink_to(backup_file)

    windows_open = getattr(
        hmac_client,
        "_open_windows_secret_descriptor",
        None,
    )
    if callable(windows_open):
        def racing_windows_open(path):
            replace_path_with_same_file_symlink()
            return windows_open(path)

        patcher = mock.patch.object(
            hmac_client,
            "_open_windows_secret_descriptor",
            side_effect=racing_windows_open,
        )
    else:
        real_open = os.open

        def racing_os_open(path, flags, mode=0o777):
            replace_path_with_same_file_symlink()
            return real_open(path, flags, mode)

        patcher = mock.patch.object(
            hmac_client.os,
            "open",
            side_effect=racing_os_open,
        )

    with patcher:
        with pytest.raises(hmac_client.InternalHmacClientError) as error:
            hmac_client.read_secret_file(secret_file)

    assert secret_file.is_symlink(), "race must replace the opened path"
    assert backup_file.stat().st_ino == secret_file.stat().st_ino
    assert error.value.code == "secret_file_symlink"


def test_secret_reader_contains_posix_nofollow_guard() -> None:
    source = (SCRIPTS_DIR / "internal_hmac_client.py").read_text(encoding="utf-8")
    assert "O_NOFOLLOW" in source


def test_secret_reader_handles_bounded_partial_descriptor_reads(
    hmac_client,
    tmp_path: Path,
) -> None:
    secret = b"0123456789abcdef0123456789abcdef"
    secret_file = tmp_path / "hmac.key"
    secret_file.write_bytes(secret)
    secret_file.chmod(0o600)
    with mock.patch.object(
        hmac_client.os,
        "read",
        side_effect=[secret[:8], secret[8:], b""],
    ):
        loaded = hmac_client.read_secret_file(secret_file)

    assert loaded == secret


def test_shared_hmac_client_signs_exact_get_and_refreshes_nonce(
    hmac_client, tmp_path: Path
) -> None:
    secret = b"0123456789abcdef0123456789abcdef"
    secret_file = tmp_path / "hmac.key"
    secret_file.write_bytes(secret)
    secret_file.chmod(0o600)
    with (
        mock.patch.object(hmac_client.time, "time", side_effect=[1784160000, 1784160001]),
        mock.patch.object(
            hmac_client.secrets,
            "token_urlsafe",
            side_effect=["nonce-one", "nonce-two"],
        ),
    ):
        first = hmac_client.build_signed_headers(
            secret=secret,
            key_id="ru-mini-v1",
            method="GET",
            path="/api/internal/probes/ru-origin/manifest",
            raw_body=b"",
        )
        second = hmac_client.build_signed_headers(
            secret=secret,
            key_id="ru-mini-v1",
            method="GET",
            path="/api/internal/probes/ru-origin/manifest",
            raw_body=b"",
        )

    assert first["X-Internal-Timestamp"] == "1784160000"
    assert first["X-Internal-Nonce"] == "nonce-one"
    assert second["X-Internal-Timestamp"] == "1784160001"
    assert second["X-Internal-Nonce"] == "nonce-two"
    assert first["X-Internal-Signature"] == sign_internal_request(
        secret,
        "GET",
        "/api/internal/probes/ru-origin/manifest",
        "1784160000",
        "nonce-one",
        b"",
    )
    assert first["X-Internal-Signature"] != second["X-Internal-Signature"]
    assert hmac_client.read_secret_file(secret_file) == secret


def test_shared_hmac_get_sends_no_body_and_never_exposes_secret(
    hmac_client, tmp_path: Path
) -> None:
    secret = b"0123456789abcdef0123456789abcdef"
    secret_file = tmp_path / "hmac.key"
    secret_file.write_bytes(secret)
    secret_file.chmod(0o600)
    captured: dict[str, object] = {}

    class FakeResponse:
        status = 200
        headers = {}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _size: int = -1) -> bytes:
            return b"{}"

    def fake_urlopen(request, *, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse()

    class FakeOpener:
        open = staticmethod(fake_urlopen)

    with mock.patch.object(
        hmac_client.urllib.request,
        "build_opener",
        return_value=FakeOpener(),
    ):
        response = hmac_client.signed_request(
            api_base_url="https://api.example.net",
            method="GET",
            path="/api/internal/probes/ru-origin/manifest",
            key_id="ru-mini-v1",
            secret_file=secret_file,
            raw_body=b"",
            timeout_sec=5.0,
        )

    request = captured["request"]
    assert request.method == "GET"
    assert request.data is None
    assert response.body == b"{}"
    assert secret not in repr(request.headers).encode("utf-8")
    assert secret not in response.body


def test_shared_hmac_post_signs_and_sends_exact_body_bytes(
    hmac_client,
    tmp_path: Path,
) -> None:
    secret = b"0123456789abcdef0123456789abcdef"
    secret_file = tmp_path / "hmac.key"
    secret_file.write_bytes(secret)
    secret_file.chmod(0o600)
    raw_body = b'{ "schema_version": 2, "label": "\xd0\x9c\xd0\xb8\xd0\xbd\xd0\xb8" }\n'
    captured: dict[str, object] = {}

    class FakeResponse:
        status = 201
        headers = {}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _size: int = -1) -> bytes:
            return b'{"code":"created"}'

    def fake_urlopen(request, *, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse()

    class FakeOpener:
        open = staticmethod(fake_urlopen)

    with (
        mock.patch.object(hmac_client.time, "time", return_value=1784160000),
        mock.patch.object(
            hmac_client.secrets,
            "token_urlsafe",
            return_value="post-nonce",
        ),
        mock.patch.object(
            hmac_client.urllib.request,
            "build_opener",
            return_value=FakeOpener(),
        ),
    ):
        response = hmac_client.signed_request(
            api_base_url="https://api.example.net",
            method="POST",
            path="/api/internal/probes/ru-origin/runs",
            key_id="ru-mini-v1",
            secret_file=secret_file,
            raw_body=raw_body,
            timeout_sec=5.0,
        )

    request = captured["request"]
    assert request.method == "POST"
    assert request.data == raw_body
    assert request.headers["X-internal-signature"] == sign_internal_request(
        secret,
        "POST",
        "/api/internal/probes/ru-origin/runs",
        "1784160000",
        "post-nonce",
        raw_body,
    )
    assert response.status == 201


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/internal/probes/ru-origin/manifest"),
        ("GET", "//api//internal/probes/ru-origin/manifest"),
    ],
)
def test_shared_hmac_client_rejects_noncanonical_method_or_path_before_network(
    hmac_client,
    tmp_path: Path,
    method: str,
    path: str,
) -> None:
    secret_file = tmp_path / "hmac.key"
    secret_file.write_bytes(b"0123456789abcdef0123456789abcdef")
    secret_file.chmod(0o600)
    with mock.patch.object(hmac_client.urllib.request, "urlopen") as urlopen:
        with pytest.raises(hmac_client.InternalHmacClientError):
            hmac_client.signed_request(
                api_base_url="https://api.example.net",
                method=method,
                path=path,
                key_id="ru-mini-v1",
                secret_file=secret_file,
                raw_body=b"",
                timeout_sec=5.0,
            )
    urlopen.assert_not_called()


def test_runner_builds_schema_v2_envelope_accepted_by_server_contract(
    runner,
) -> None:
    target = _target()
    generated_at = datetime.now(timezone.utc).replace(microsecond=0)
    manifest = _manifest(generated_at=generated_at, target=target)
    started_at = generated_at - timedelta(minutes=2)
    finished_at = generated_at - timedelta(minutes=1)
    with mock.patch.object(
        runner.dataplane_probe,
        "probe_node_endpoint",
        return_value=_passing_dataplane_result(),
    ):
        payload = runner.run_manifest(
            manifest,
            probe_host_id="mini",
            probe_host_label="Мини",
            probe_public_ip="203.0.113.10",
            profile_registry={},
            timeout_sec=5.0,
            started_at=started_at,
            finished_at=finished_at,
        )

    validated = validate_run_payload(payload)
    assert validated["schema_version"] == 2
    assert validated["origin"] == "ru"
    assert validated["runner_version"] == "2.0"
    assert validated["execution_status"] == "completed"
    assert validated["manifest_revision"] == manifest["manifest_revision"]


def test_all_five_probe_modes_produce_one_valid_schema_v2_envelope(runner) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0)
    targets = [
        _target(
            mode="google_https",
            target_id="environment:google",
            target_kind="environment",
            node_code=None,
            profile="https",
        ),
        _target(
            mode="canonical_https_large_body",
            target_id="canonical:sample",
            target_kind="canonical_public",
            node_code=None,
            profile="https",
        ),
        _target(),
        _target(
            mode="xhttp_handshake",
            target_id="reserve:xhttp",
            target_kind="reserve_xhttp",
            node_code=None,
            profile="reserve_xhttp_cdn",
            local_profile="reserve-xhttp",
        ),
        _target(
            mode="hysteria_handshake",
            target_id="reserve:hysteria",
            target_kind="reserve_hysteria",
            node_code=None,
            profile="hysteria2",
            local_profile="reserve-hysteria",
        ),
    ]
    manifest = {
        "manifest_schema_version": 1,
        "manifest_revision": manifest_revision(targets),
        "generated_at": generated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "max_cache_age_seconds": 3600,
        "targets": targets,
    }
    https_result = {
        "stages": {
            "dns": {"status": "pass", "latency_ms": 1, "code": None},
            "tcp": {"status": "pass", "latency_ms": 2, "code": None},
            "tls": {"status": "pass", "latency_ms": 3, "code": None},
            "http_large_body": {"status": "pass", "latency_ms": 4, "code": None},
            "transport_handshake": {
                "status": "not_applicable",
                "latency_ms": None,
                "code": None,
            },
        },
        "address_family_status": {"ipv4": "pass", "ipv6": "not_run"},
    }

    def adapter(mode, endpoint, **_kwargs):
        return {
            "schema_version": 1,
            "profile_id": endpoint["local_probe_profile_id"],
            "protocol": (
                "xhttp" if mode == "xhttp_handshake" else "hysteria2"
            ),
            "handshake_status": "pass",
            "classification": "ok",
            "detail_code": None,
        }

    with (
        mock.patch.object(
            runner,
            "probe_https_large_body",
            return_value=https_result,
        ),
        mock.patch.object(
            runner.dataplane_probe,
            "probe_node_endpoint",
            return_value=_passing_dataplane_result(),
        ),
        mock.patch.object(
            runner.dataplane_probe,
            "_resolve_dns",
            return_value={"resolved_ips": ["203.0.113.30"]},
        ),
        mock.patch.object(
            runner,
            "run_transport_adapter",
            side_effect=adapter,
        ),
    ):
        payload = runner.run_manifest(
            manifest,
            probe_host_id="mini",
            probe_host_label="Мини",
            probe_public_ip="203.0.113.10",
            profile_registry={"profiles": {}},
            timeout_sec=5.0,
            started_at=generated_at - timedelta(minutes=2),
            finished_at=generated_at - timedelta(minutes=1),
        )

    validated = validate_run_payload(payload)
    assert validated["execution_status"] == "completed"
    assert {
        target["endpoint"]["probe_mode"] for target in validated["targets"]
    } == {
        "google_https",
        "canonical_https_large_body",
        "delivery_tls",
        "xhttp_handshake",
        "hysteria_handshake",
    }


def test_failed_required_stage_is_completed_even_when_dependents_are_not_run(
    runner,
) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0)
    manifest = _manifest(generated_at=generated_at)
    with mock.patch.object(
        runner.dataplane_probe,
        "_resolve_dns",
        side_effect=OSError("private provider text"),
    ):
        payload = runner.run_manifest(
            manifest,
            probe_host_id="mini",
            probe_host_label="Мини",
            probe_public_ip=None,
            profile_registry={},
            timeout_sec=5.0,
            started_at=generated_at - timedelta(minutes=2),
            finished_at=generated_at - timedelta(minutes=1),
        )

    assert payload["execution_status"] == "completed"
    assert payload["targets"][0]["stages"]["dns"]["status"] == "fail"
    assert payload["targets"][0]["stages"]["tcp"]["status"] == "not_run"


def test_diagnostic_exception_stays_local_to_diagnostic_target(runner) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0)
    release_target = _target()
    diagnostic_target = _target(
        target_id="diagnostic:delivery",
        target_kind="diagnostic",
        node_code=None,
    )
    diagnostic_target["scope"] = "diagnostic"
    targets = [release_target, diagnostic_target]
    manifest = {
        "manifest_schema_version": 1,
        "manifest_revision": manifest_revision(targets),
        "generated_at": generated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "max_cache_age_seconds": 3600,
        "targets": targets,
    }
    with mock.patch.object(
        runner.dataplane_probe,
        "probe_node_endpoint",
        return_value=_passing_dataplane_result(),
    ):
        release_result = runner.run_manifest_target(
            release_target,
            timeout_sec=5.0,
            profile_registry={},
        )

    with mock.patch.object(
        runner,
        "run_manifest_target",
        side_effect=[
            release_result,
            RuntimeError("private diagnostic adapter state"),
        ],
    ):
        payload = runner.run_manifest(
            manifest,
            probe_host_id="mini",
            probe_host_label="Мини",
            probe_public_ip=None,
            profile_registry={},
            timeout_sec=5.0,
            started_at=generated_at - timedelta(minutes=2),
            finished_at=generated_at - timedelta(minutes=1),
        )

    assert payload["execution_status"] == "completed"
    diagnostic = next(
        target
        for target in payload["targets"]
        if target["scope"] == "diagnostic"
    )
    assert diagnostic["detail_code"] == "runner_error"
    assert "private diagnostic adapter state" not in json.dumps(
        payload,
        ensure_ascii=False,
    )


def test_diagnostic_required_not_run_does_not_make_release_partial(runner) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0)
    release_target = _target()
    diagnostic_target = _target(
        mode="hysteria_handshake",
        target_id="diagnostic:hysteria",
        target_kind="diagnostic",
        node_code=None,
        profile="hysteria2",
        local_profile="diagnostic-hysteria",
    )
    diagnostic_target["scope"] = "diagnostic"
    targets = [release_target, diagnostic_target]
    manifest = {
        "manifest_schema_version": 1,
        "manifest_revision": manifest_revision(targets),
        "generated_at": generated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "max_cache_age_seconds": 3600,
        "targets": targets,
    }
    with (
        mock.patch.object(
            runner.dataplane_probe,
            "_resolve_dns",
            return_value={
                "resolved_ips": ["203.0.113.20"],
                "resolved_ipv4": ["203.0.113.20"],
                "resolved_ipv6": [],
            },
        ),
        mock.patch.object(
            runner.dataplane_probe,
            "probe_node_endpoint",
            return_value=_passing_dataplane_result(),
        ),
    ):
        payload = runner.run_manifest(
            manifest,
            probe_host_id="mini",
            probe_host_label="Мини",
            probe_public_ip=None,
            profile_registry={"profiles": {}},
            timeout_sec=5.0,
            started_at=generated_at - timedelta(minutes=2),
            finished_at=generated_at - timedelta(minutes=1),
        )

    assert payload["execution_status"] == "completed"
    diagnostic = next(
        target
        for target in payload["targets"]
        if target["scope"] == "diagnostic"
    )
    assert diagnostic["stages"]["transport_handshake"]["status"] == "not_run"


def test_runner_emits_valid_runner_error_envelope_on_target_exception(runner) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0)
    manifest = _manifest(generated_at=generated_at)
    with mock.patch.object(
        runner,
        "run_manifest_target",
        side_effect=RuntimeError("synthetic provider payload must stay private"),
    ):
        payload = runner.run_manifest(
            manifest,
            probe_host_id="mini",
            probe_host_label="Мини",
            probe_public_ip=None,
            profile_registry={},
            timeout_sec=5.0,
            started_at=generated_at - timedelta(minutes=2),
            finished_at=generated_at - timedelta(minutes=1),
        )

    validated = validate_run_payload(payload)
    assert validated["execution_status"] == "runner_error"
    assert all(
        stage["status"] != "pass"
        for stage in validated["targets"][0]["stages"].values()
    )
    assert "synthetic provider payload" not in json.dumps(
        validated,
        ensure_ascii=False,
    )


def test_unexpected_hysteria_dns_adapter_error_is_runner_error(runner) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0)
    target = _target(
        mode="hysteria_handshake",
        target_id="reserve:hysteria",
        target_kind="reserve_hysteria",
        node_code=None,
        profile="hysteria2",
        local_profile="reserve-hysteria",
    )
    manifest = _manifest(generated_at=generated_at, target=target)
    with mock.patch.object(
        runner.dataplane_probe,
        "_resolve_dns",
        side_effect=ValueError("unexpected private adapter state"),
    ):
        payload = runner.run_manifest(
            manifest,
            probe_host_id="mini",
            probe_host_label="Мини",
            probe_public_ip=None,
            profile_registry={"profiles": {}},
            timeout_sec=5.0,
            started_at=generated_at - timedelta(minutes=2),
            finished_at=generated_at - timedelta(minutes=1),
        )

    assert payload["execution_status"] == "runner_error"
    assert "unexpected private adapter state" not in json.dumps(
        payload,
        ensure_ascii=False,
    )


def test_sample_is_valid_redacted_schema_v2_artifact() -> None:
    sample = json.loads(
        (SCRIPTS_DIR / "ru_probe_sample.json").read_text(encoding="utf-8")
    )
    validated = validate_run_payload(sample)
    assert validated["schema_version"] == 2
    serialized = json.dumps(validated, ensure_ascii=False).lower()
    assert "203.0.113." in serialized
    for forbidden in ("password", "secret", "token", "subscription_url"):
        assert forbidden not in serialized
