from __future__ import annotations

import importlib.util
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sys
from pathlib import Path
from threading import Thread

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))


def _load_module():
    module_path = SCRIPTS_ROOT / "api_latency_probe.py"
    spec = importlib.util.spec_from_file_location("api_latency_probe", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MODULE = _load_module()
CONTRACT_PATH = (
    REPO_ROOT
    / "shared"
    / "contracts"
    / "performance"
    / "performance-budgets.v1.json"
)


class _Response:
    status_code = 200

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def iter_bytes(self):
        yield b"{}"


class _Client:
    def __init__(self, calls: list[tuple]) -> None:
        self.calls = calls

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def stream(self, method, target, *, content, headers):
        self.calls.append((method, target, content, dict(headers)))
        return _Response()


def test_base_url_rejects_credentials_and_insecure_remote_http() -> None:
    with pytest.raises(MODULE.ContractError, match="credentials"):
        MODULE._validate_base_url(
            "https://user:pass@example.test", allow_http_localhost=False
        )
    with pytest.raises(MODULE.ContractError, match="must use HTTPS"):
        MODULE._validate_base_url(
            "http://example.test", allow_http_localhost=False
        )
    assert MODULE._validate_base_url(
        "http://127.0.0.1:8080", allow_http_localhost=True
    ).endswith("/")


def test_current_origin_budget_rejects_substitute_origin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(MODULE, "_git_identity", lambda _: ("a" * 40, "clean"))
    with pytest.raises(MODULE.ContractError, match="requires --origin current"):
        MODULE.collect(
            contract_path=CONTRACT_PATH,
            budget_id="api.health.current_origin_ms",
            base_url="https://example.test",
            origin="brain",
            network_profile="controlled",
            source_address=None,
            candidate_label="candidate",
            release_version="1.2.0",
            repo_root=REPO_ROOT,
            authorization_env=None,
            body_file=None,
            allow_state_changing_probe=False,
            allow_http_localhost=False,
            timeout_seconds=1,
            sample_count=None,
            warmup_count=None,
            client_factory=lambda **_kwargs: _Client([]),
        )


def test_state_changing_probe_requires_explicit_flag() -> None:
    with pytest.raises(MODULE.ContractError, match="explicit authorization flag"):
        MODULE.collect(
            contract_path=CONTRACT_PATH,
            budget_id="api.client_start_trial_ms",
            base_url="https://example.test",
            origin="staging",
            network_profile="controlled",
            source_address=None,
            candidate_label="candidate",
            release_version="1.2.0",
            repo_root=REPO_ROOT,
            authorization_env="POKROV_TEST_TOKEN",
            body_file=None,
            allow_state_changing_probe=False,
            allow_http_localhost=False,
            timeout_seconds=1,
            sample_count=None,
            warmup_count=None,
            client_factory=lambda **_kwargs: _Client([]),
        )


def test_public_probe_collects_required_samples_without_payloads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []

    client = _Client(calls)

    monkeypatch.setattr(MODULE, "_git_identity", lambda _: ("a" * 40, "dirty"))
    evidence, summary = MODULE.collect(
        contract_path=CONTRACT_PATH,
        budget_id="api.health.current_origin_ms",
        base_url="https://health.example.test",
        origin="current",
        network_profile="controlled-wired",
        source_address=None,
        candidate_label="local-probe",
        release_version="1.2.0",
        repo_root=REPO_ROOT,
        authorization_env=None,
        body_file=None,
        allow_state_changing_probe=False,
        allow_http_localhost=False,
        timeout_seconds=1,
        sample_count=None,
        warmup_count=None,
        client_factory=lambda **_kwargs: client,
    )

    assert len(calls) == 55
    assert calls[0][0] == "GET"
    assert calls[0][1] == "https://health.example.test/api/health"
    assert calls[0][2] is None
    assert "Authorization" not in calls[0][3]
    assert len(evidence["measurements"][0]["samples"]) == 50
    assert summary["results"][0]["sample_count"] == 50
    assert summary["results"][0]["gate_status"] == "PASS"


def test_source_address_validation_is_literal_local_and_bounded() -> None:
    assert MODULE._validate_source_address("127.0.0.1") == "127.0.0.1"
    with pytest.raises(MODULE.ContractError, match="literal IPv4 or IPv6"):
        MODULE._validate_source_address("localhost")
    with pytest.raises(MODULE.ContractError, match="unspecified or multicast"):
        MODULE._validate_source_address("0.0.0.0")
    with pytest.raises(MODULE.ContractError, match="unspecified or multicast"):
        MODULE._validate_source_address("224.0.0.1")


def test_source_bound_probe_uses_direct_client_and_records_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []
    client = _Client(calls)

    def build_probe_client(*, source_address: str, timeout_seconds: float):
        assert source_address == "127.0.0.1"
        assert timeout_seconds == 1
        return client

    monkeypatch.setattr(
        MODULE,
        "_build_probe_client",
        build_probe_client,
    )
    monkeypatch.setattr(MODULE, "_git_identity", lambda _: ("b" * 40, "clean"))

    evidence, summary = MODULE.collect(
        contract_path=CONTRACT_PATH,
        budget_id="api.health.current_origin_ms",
        base_url="https://health.example.test",
        origin="current",
        network_profile="controlled-wired",
        source_address="127.0.0.1",
        candidate_label="local-probe",
        release_version="1.2.0",
        repo_root=REPO_ROOT,
        authorization_env=None,
        body_file=None,
        allow_state_changing_probe=False,
        allow_http_localhost=False,
        timeout_seconds=1,
        sample_count=None,
        warmup_count=None,
    )

    assert len(calls) == 55
    assert evidence["environment"]["source_address"] == "127.0.0.1"
    assert (
        evidence["environment"]["proxy_policy"]
        == "disabled_for_source_bound_probe"
    )
    assert (
        evidence["environment"]["connection_policy"]
        == "persistent_http1_keep_alive"
    )
    assert evidence["environment"]["collector_version"] == "1.2.0"
    assert summary["results"][0]["gate_status"] == "PASS"


def test_warmups_and_samples_share_one_real_loopback_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class CountingServer(ThreadingHTTPServer):
        daemon_threads = True

        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.accepted_connections = 0
            self.request_count = 0

        def get_request(self):
            request, address = super().get_request()
            self.accepted_connections += 1
            return request, address

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_GET(self) -> None:
            self.server.request_count += 1
            body = b"{}"
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args) -> None:
            return

    server = CountingServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setattr(MODULE, "_git_identity", lambda _: ("c" * 40, "clean"))
    try:
        evidence, summary = MODULE.collect(
            contract_path=CONTRACT_PATH,
            budget_id="api.health.current_origin_ms",
            base_url=f"http://127.0.0.1:{server.server_port}",
            origin="current",
            network_profile="loopback-keep-alive",
            source_address="127.0.0.1",
            candidate_label="local-probe",
            release_version="1.2.0",
            repo_root=REPO_ROOT,
            authorization_env=None,
            body_file=None,
            allow_state_changing_probe=False,
            allow_http_localhost=True,
            timeout_seconds=1,
            sample_count=None,
            warmup_count=None,
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert server.request_count == 55
    assert server.accepted_connections == 1
    assert len(evidence["measurements"][0]["samples"]) == 50
    assert summary["results"][0]["gate_status"] == "PASS"
