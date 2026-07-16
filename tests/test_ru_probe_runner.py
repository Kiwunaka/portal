from __future__ import annotations

import importlib.util
import json
import os
import socket
import stat
import subprocess
import sys
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


def test_protocol_adapter_uses_safe_fixed_argv_and_validates_response(
    runner, tmp_path: Path
) -> None:
    executable = tmp_path / ("probe.exe" if os.name == "nt" else "probe")
    executable.write_bytes(b"synthetic executable")
    executable.chmod(0o700)
    endpoint = _endpoint(
        mode="hysteria_handshake",
        host="reserve.example.net",
        sni="reserve.example.net",
        profile="hysteria2",
        local_profile="reserve-hysteria",
    )
    registry = {
        "profiles": {
            "reserve-hysteria": {
                "executable": str(executable.resolve()),
                "argv": ["--mode", "probe"],
            }
        }
    }
    response = {
        "schema_version": 1,
        "profile_id": "reserve-hysteria",
        "protocol": "hysteria2",
        "handshake_status": "pass",
        "classification": "ok",
        "detail_code": None,
    }
    completed = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=canonical_json_bytes(response),
        stderr=b"",
    )
    with mock.patch.object(runner.subprocess, "run", return_value=completed) as run:
        result = runner.run_transport_adapter(
            "hysteria_handshake",
            endpoint,
            profile_registry=registry,
            timeout_sec=5.0,
        )

    assert result == response
    _, kwargs = run.call_args
    assert kwargs["shell"] is False
    assert kwargs["check"] is False
    assert kwargs["capture_output"] is True
    assert kwargs["input"] == canonical_json_bytes(endpoint)
    assert kwargs["timeout"] == 5.0
    assert run.call_args.args[0] == [
        str(executable.resolve()),
        "--mode",
        "probe",
    ]


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
    ("completed", "expected_code"),
    [
        (
            subprocess.CompletedProcess(
                args=[], returncode=0, stdout=b"not-json", stderr=b""
            ),
            "adapter_malformed_response",
        ),
        (
            subprocess.CompletedProcess(args=[], returncode=2, stdout=b"", stderr=b"x"),
            "adapter_exit_nonzero",
        ),
    ],
)
def test_protocol_adapter_malformed_or_failed_process_is_fail(
    runner, tmp_path: Path, completed, expected_code: str
) -> None:
    executable = tmp_path / ("probe.exe" if os.name == "nt" else "probe")
    executable.write_bytes(b"synthetic executable")
    executable.chmod(0o700)
    endpoint = _endpoint(
        mode="xhttp_handshake",
        profile="reserve_xhttp_cdn",
        local_profile="reserve-xhttp",
    )
    registry = {
        "profiles": {
            "reserve-xhttp": {
                "executable": str(executable.resolve()),
                "argv": [],
            }
        }
    }
    with mock.patch.object(runner.subprocess, "run", return_value=completed):
        response = runner.run_transport_adapter(
            "xhttp_handshake",
            endpoint,
            profile_registry=registry,
            timeout_sec=5.0,
        )

    stage = runner.transport_stage_from_adapter("xhttp_handshake", response)
    assert stage["status"] == "fail"
    assert stage["code"] == expected_code


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

    with mock.patch.object(hmac_client.urllib.request, "urlopen", fake_urlopen):
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

    with (
        mock.patch.object(hmac_client.time, "time", return_value=1784160000),
        mock.patch.object(
            hmac_client.secrets,
            "token_urlsafe",
            return_value="post-nonce",
        ),
        mock.patch.object(hmac_client.urllib.request, "urlopen", fake_urlopen),
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
        "probe_node_endpoint",
        return_value={
            "ok": False,
            "stage": "dns",
            "error_kind": "dns_lookup_failed",
            "error_message": "private provider text",
            "resolved_ips": [],
            "latency_ms": None,
            "tls_protocol": "",
            "tls_cipher": "",
            "connected_ip": "",
        },
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
