from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

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
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def getcode(self) -> int:
        return self.status

    def read(self, _: int) -> bytes:
        return b"{}"


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
            opener=lambda *_args, **_kwargs: _Response(),
        )


def test_state_changing_probe_requires_explicit_flag() -> None:
    with pytest.raises(MODULE.ContractError, match="explicit authorization flag"):
        MODULE.collect(
            contract_path=CONTRACT_PATH,
            budget_id="api.client_start_trial_ms",
            base_url="https://example.test",
            origin="staging",
            network_profile="controlled",
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
            opener=lambda *_args, **_kwargs: _Response(),
        )


def test_public_probe_collects_required_samples_without_payloads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []

    def opener(request, **kwargs):
        calls.append((request.full_url, dict(request.header_items()), kwargs))
        return _Response()

    monkeypatch.setattr(MODULE, "_git_identity", lambda _: ("a" * 40, "dirty"))
    evidence, summary = MODULE.collect(
        contract_path=CONTRACT_PATH,
        budget_id="api.health.current_origin_ms",
        base_url="https://health.example.test",
        origin="current",
        network_profile="controlled-wired",
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
        opener=opener,
    )

    assert len(calls) == 55
    assert calls[0][0] == "https://health.example.test/api/health"
    assert "Authorization" not in dict(calls[0][1])
    assert len(evidence["measurements"][0]["samples"]) == 50
    assert summary["results"][0]["sample_count"] == 50
    assert summary["results"][0]["gate_status"] == "PASS"
