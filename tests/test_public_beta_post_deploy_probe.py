from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class FakeCompletedProcess:
    def __init__(self, returncode: int = 0) -> None:
        self.returncode = returncode
        self.stdout = ""
        self.stderr = ""


def _load_module():
    module_path = REPO_ROOT / "scripts" / "public_beta_post_deploy_probe.py"
    spec = importlib.util.spec_from_file_location("public_beta_post_deploy_probe", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _runtime_payload(path: str) -> dict[str, object]:
    if path == "/api/auth/email/status":
        return {
            "enabled": True,
            "public_enabled": True,
            "delivery_url_configured": True,
            "delivery_secret_configured": True,
            "debug_echo": False,
        }
    if path == "/api/payments/providers":
        return {
            "provider_count": 0,
            "providers": [],
            "blocked_reason": "paid_checkout_launch_evidence_missing",
        }
    raise AssertionError(path)


def test_dry_run_reads_live_runtime_status_but_blocks_mutating_probes() -> None:
    module = _load_module()

    report = module.build_report(
        api_base_url="https://api.pokrov.space",
        env={
            "EMAIL_DELIVERY_WEBHOOK_SECRET": "super-secret-email-token",
            "LAVATOP_API_KEY": "super-secret-lavatop-token",
        },
        live=False,
        runtime_fetcher=_runtime_payload,
        command_runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected command")),
    )

    checks = {check["name"]: check for check in report["checks"]}
    encoded = json.dumps(report, ensure_ascii=False)
    assert report["ok"] is False
    assert report["classification"] == module.BLOCKED_BY_ACCESS
    assert report["email_public_runtime_config_passed"] is True
    assert report["email_live_delivery_probe_passed"] is False
    assert report["lavatop_live_invoice_probe_passed"] is False
    assert report["post_deploy_probe_modes"]["email_public_runtime"] == module.PASS
    assert report["post_deploy_probe_modes"]["email_live_delivery"] == module.BLOCKED_BY_ACCESS
    assert report["safe_to_keep_email_public"] is True
    assert report["safe_to_enable_paid_checkout"] is False
    assert checks["email_public_runtime_config"]["status"] == module.PASS
    assert checks["payment_provider_catalog"]["status"] == module.BLOCKED_BY_ACCESS
    assert checks["email_delivery_verify"]["status"] == module.BLOCKED_BY_ACCESS
    assert checks["lavatop_live_invoice_creation"]["status"] == module.BLOCKED_BY_ACCESS
    assert "super-secret-email-token" not in encoded
    assert "super-secret-lavatop-token" not in encoded


def test_live_mode_runs_email_and_invoice_probes_when_access_inputs_exist() -> None:
    module = _load_module()
    commands: list[list[str]] = []

    def fake_runner(cmd: list[str], *, env: dict[str, str]):
        commands.append(cmd)
        assert env["EMAIL_DELIVERY_WEBHOOK_SECRET"] == "super-secret-email-token"
        assert env["LAVATOP_API_KEY"] == "super-secret-lavatop-token"
        return FakeCompletedProcess(0)

    report = module.build_report(
        api_base_url="https://api.pokrov.space",
        env={
            "EMAIL_PROBE_TO": "operator@example.test",
            "EMAIL_DELIVERY_WEBHOOK_URL": "https://relay.pokrov.test/send",
            "EMAIL_DELIVERY_WEBHOOK_SECRET": "super-secret-email-token",
            "LAVATOP_PROBE_EMAIL": "buyer@example.test",
            "LAVATOP_API_KEY": "super-secret-lavatop-token",
            "LAVATOP_OFFER_ID_START_99": "offer-secret",
        },
        live=True,
        runtime_fetcher=lambda path: {
            "/api/auth/email/status": {
                "enabled": True,
                "public_enabled": True,
                "delivery_url_configured": True,
                "delivery_secret_configured": True,
                "debug_echo": False,
            },
            "/api/payments/providers": {
                "providers": [{"provider": "lavatop", "enabled": True}],
            },
        }[path],
        command_runner=fake_runner,
        paid_evidence_report={
            "classification": module.PASS,
            "safe_to_enable_paid_checkout": True,
            "checks": [],
        },
    )

    checks = {check["name"]: check for check in report["checks"]}
    assert checks["email_delivery_verify"]["status"] == module.PASS
    assert checks["email_delivery_reset"]["status"] == module.PASS
    assert checks["email_delivery_payment_access_key"]["status"] == module.PASS
    assert checks["lavatop_live_invoice_creation"]["status"] == module.PASS
    assert report["email_public_runtime_config_passed"] is True
    assert report["email_live_delivery_probe_passed"] is True
    assert report["lavatop_live_invoice_probe_passed"] is True
    assert report["safe_to_keep_email_public"] is True
    assert report["safe_to_enable_paid_checkout"] is True
    assert [cmd[1] for cmd in commands].count("scripts/email_delivery_probe.py") == 3
    assert [cmd[1] for cmd in commands].count("scripts/lavatop_invoice_probe.py") == 1
    assert "offer-secret" not in json.dumps(report, ensure_ascii=False)


def test_payment_provider_catalog_accepts_live_api_provider_shape_without_enabled_flag() -> None:
    module = _load_module()

    report = module.build_report(
        api_base_url="https://api.pokrov.space",
        env={},
        live=False,
        runtime_fetcher=lambda path: {
            "/api/auth/email/status": {
                "enabled": True,
                "public_enabled": True,
                "delivery_url_configured": True,
                "delivery_secret_configured": True,
                "debug_echo": False,
            },
            "/api/payments/providers": {
                "ok": True,
                "blocked": False,
                "providers": [{"code": "lavatop", "label": "Lava.top"}],
            },
        }[path],
        command_runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected command")),
        brain_live_probe_report={
            "checks": [
                {"name": "email_delivery_verify", "status": "PASS", "missing": [], "source": "brain:portal-api"},
                {"name": "email_delivery_reset", "status": "PASS", "missing": [], "source": "brain:portal-api"},
                {"name": "email_delivery_payment_access_key", "status": "PASS", "missing": [], "source": "brain:portal-api"},
                {"name": "lavatop_live_invoice_creation", "status": "PASS", "missing": [], "source": "brain:portal-api"},
            ]
        },
        paid_evidence_report={
            "classification": module.PASS,
            "safe_to_enable_paid_checkout": True,
            "checks": [],
        },
    )

    checks = {check["name"]: check for check in report["checks"]}
    assert checks["payment_provider_catalog"]["status"] == module.PASS
    assert report["safe_to_enable_paid_checkout"] is True


def test_brain_live_probe_report_can_prove_email_without_local_secrets() -> None:
    module = _load_module()

    report = module.build_report(
        api_base_url="https://api.pokrov.space",
        env={},
        live=False,
        runtime_fetcher=_runtime_payload,
        command_runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected local command")),
        brain_live_probe_report={
            "mode": "brain_post_deploy_live_probe",
            "safe_to_keep_email_public": True,
            "email_public_probe_can_be_evaluated_independently": True,
            "lavatop_invoice_probe_passed": False,
            "checks": [
                {
                    "name": "email_delivery_verify",
                    "status": "PASS",
                    "missing": [],
                    "note": "sent",
                    "source": "brain:portal-api",
                    "http_status": 202,
                    "stdout": "secret stdout must not leak",
                },
                {
                    "name": "email_delivery_reset",
                    "status": "PASS",
                    "missing": [],
                    "note": "sent",
                    "source": "brain:portal-api",
                    "http_status": 202,
                },
                {
                    "name": "email_delivery_payment_access_key",
                    "status": "PASS",
                    "missing": [],
                    "note": "sent",
                    "source": "brain:portal-api",
                    "http_status": 202,
                    "body": "relay-secret-response",
                },
                {
                    "name": "lavatop_live_invoice_creation",
                    "status": "BLOCKED_BY_ACCESS",
                    "missing": ["lavatop_probe_email"],
                    "note": "buyer missing",
                    "source": "brain:portal-api",
                },
            ],
        },
    )

    checks = {check["name"]: check for check in report["checks"]}
    encoded = json.dumps(report, ensure_ascii=False)
    assert report["ok"] is False
    assert report["classification"] == module.BLOCKED_BY_ACCESS
    assert report["email_live_delivery_probe_passed"] is True
    assert report["lavatop_live_invoice_probe_passed"] is False
    assert report["post_deploy_probe_modes"]["email_live_delivery"] == module.PASS
    assert report["post_deploy_probe_modes"]["lavatop_invoice"] == module.BLOCKED_BY_ACCESS
    assert report["safe_to_keep_email_public"] is True
    assert report["safe_to_enable_paid_checkout"] is False
    assert checks["email_delivery_verify"]["status"] == module.PASS
    assert checks["email_delivery_verify"]["source"] == "brain:portal-api"
    assert checks["email_delivery_payment_access_key"]["status"] == module.PASS
    assert checks["lavatop_live_invoice_creation"]["missing"] == ["lavatop_probe_email"]
    assert "secret stdout" not in encoded
    assert "relay-secret-response" not in encoded


def test_main_writes_redacted_json_and_returns_blocked_when_access_is_missing(tmp_path: Path) -> None:
    module = _load_module()
    output = tmp_path / "post-deploy.json"

    code = module.main(
        [
            "--output",
            str(output),
            "--offline",
        ]
    )

    report = json.loads(output.read_text(encoding="utf-8"))
    assert code == 2
    assert report["classification"] == module.BLOCKED_BY_ACCESS
    assert report["mode"] == "public_beta_post_deploy_probe"


def test_main_accepts_redacted_brain_live_probe_json(tmp_path: Path) -> None:
    module = _load_module()
    output = tmp_path / "post-deploy.json"
    brain_live = tmp_path / "brain-live.json"
    brain_live.write_text(
        json.dumps(
            {
                "mode": "brain_post_deploy_live_probe",
                "safe_to_keep_email_public": True,
                "checks": [
                    {"name": "email_delivery_verify", "status": "PASS", "missing": [], "source": "brain:portal-api"},
                    {"name": "email_delivery_reset", "status": "PASS", "missing": [], "source": "brain:portal-api"},
                    {
                        "name": "email_delivery_payment_access_key",
                        "status": "PASS",
                        "missing": [],
                        "source": "brain:portal-api",
                        "raw_body": "must-not-leak",
                    },
                    {
                        "name": "lavatop_live_invoice_creation",
                        "status": "BLOCKED_BY_ACCESS",
                        "missing": ["lavatop_probe_email"],
                        "source": "brain:portal-api",
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    code = module.main(
        [
            "--output",
            str(output),
            "--offline",
            "--brain-live-probe-json",
            str(brain_live),
        ]
    )

    report = json.loads(output.read_text(encoding="utf-8"))
    encoded = json.dumps(report, ensure_ascii=False)
    assert code == 2
    assert report["safe_to_keep_email_public"] is False
    assert report["post_deploy_probe_modes"]["email_public_runtime"] == module.BLOCKED_BY_ACCESS
    assert report["email_live_delivery_probe_passed"] is True
    assert report["lavatop_live_invoice_probe_passed"] is False
    assert report["inputs"]["brain_live_probe_json"] == str(brain_live)
    assert "must-not-leak" not in encoded
