from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "brain_payment_email_readiness.py"
    spec = importlib.util.spec_from_file_location("brain_payment_email_readiness", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_sanitize_env_for_report_keeps_presence_without_secret_values() -> None:
    module = _load_module()

    sanitized = module.sanitize_env_for_report(
        {
            "LAVATOP_API_KEY": "live-secret",
            "LAVATOP_OFFER_ID_START_99": "offer-secret",
            "LAVATOP_WEBHOOK_API_KEY": "webhook-secret",
            "EMAIL_DELIVERY_WEBHOOK_URL": "https://relay.example/send",
            "EMAIL_DELIVERY_WEBHOOK_SECRET": "relay-secret",
            "EMAIL_AUTH_PUBLIC_ENABLED": "false",
            "EMAIL_AUTH_DEBUG_ECHO": "false",
            "LAVATOP_PROVIDER_ACCEPTANCE_CONFIRMED": "false",
        },
        plan_code="start_99",
    )

    assert sanitized["LAVATOP_API_KEY"] == "present"
    assert sanitized["LAVATOP_OFFER_ID_START_99"] == "present"
    assert sanitized["EMAIL_DELIVERY_WEBHOOK_URL"] == "present"
    assert sanitized["EMAIL_DELIVERY_WEBHOOK_SECRET"] == "present"
    assert sanitized["EMAIL_AUTH_PUBLIC_ENABLED"] == "false"
    serialized = module.json.dumps(sanitized)
    assert "live-secret" not in serialized
    assert "offer-secret" not in serialized
    assert "relay-secret" not in serialized
    assert "relay.example" not in serialized


def test_brain_readiness_report_preserves_blocked_email_public_mode() -> None:
    module = _load_module()

    report = module.build_brain_readiness_report(
        raw_env={
            "LAVATOP_API_KEY": "live-secret",
            "LAVATOP_OFFER_ID_START_99": "offer-secret",
            "LAVATOP_WEBHOOK_API_KEY": "webhook-secret",
            "EMAIL_DELIVERY_WEBHOOK_URL": "https://relay.example/send",
            "EMAIL_DELIVERY_WEBHOOK_SECRET": "relay-secret",
            "EMAIL_AUTH_PUBLIC_ENABLED": "false",
            "EMAIL_AUTH_DEBUG_ECHO": "false",
        },
        source_unit="portal-api",
        pid_present=True,
        plan_code="start_99",
    )

    assert report["ok"] is False
    assert report["classification"] == "BLOCKED_BY_ACCESS"
    assert report["mode"] == "brain_proc_env_readiness"
    checks = {check["name"]: check for check in report["checks"]}
    assert checks["lavatop_invoice_credentials"]["status"] == "PASS"
    assert checks["lavatop_webhook_auth"]["status"] == "PASS"
    assert checks["email_delivery_webhook"]["status"] == "PASS"
    assert checks["email_public_mode"]["status"] == "BLOCKED_BY_ACCESS"


def test_missing_brain_pid_is_blocked_by_access() -> None:
    module = _load_module()

    report = module.build_brain_readiness_report(
        raw_env={},
        source_unit="portal-api",
        pid_present=False,
        plan_code="start_99",
    )

    assert report["ok"] is False
    assert report["classification"] == "BLOCKED_BY_ACCESS"
    assert report["checks"][0]["name"] == "brain_source_unit_pid"


def test_brain_post_deploy_report_whitelists_remote_output() -> None:
    module = _load_module()

    report = module.build_brain_post_deploy_report(
        remote_payload={
            "checks": [
                {
                    "name": "email_delivery_verify",
                    "status": "PASS",
                    "missing": [],
                    "note": "sent",
                    "source": "brain",
                    "http_status": 202,
                    "body": "secret response body",
                    "stdout": "secret stdout",
                },
                {
                    "name": "email_delivery_reset",
                    "status": "PASS",
                    "missing": [],
                    "note": "sent",
                    "source": "brain",
                    "http_status": 202,
                },
                {
                    "name": "email_delivery_payment_access_key",
                    "status": "PASS",
                    "missing": [],
                    "note": "sent",
                    "source": "brain",
                    "http_status": 202,
                },
                {
                    "name": "lavatop_live_invoice_creation",
                    "status": "PASS",
                    "missing": [],
                    "note": "created",
                    "source": "brain",
                    "http_status": 201,
                    "invoice_url": "https://pay.example/secret-invoice",
                },
            ],
            "env": {"LAVATOP_API_KEY": "live-secret", "EMAIL_DELIVERY_WEBHOOK_SECRET": "relay-secret"},
        },
        source_unit="portal-api",
        plan_code="start_99",
    )

    encoded = module.json.dumps(report, ensure_ascii=False)
    assert report["ok"] is True
    assert report["classification"] == "PASS"
    assert report["post_deploy_probe_mode"] == "email_and_lavatop_probe_passed"
    assert report["safe_to_keep_email_public"] is True
    assert report["email_public_probe_can_be_evaluated_independently"] is True
    assert report["lavatop_invoice_probe_passed"] is True
    assert report["safe_to_enable_paid_checkout"] is False
    assert "live-secret" not in encoded
    assert "relay-secret" not in encoded
    assert "secret response body" not in encoded
    assert "secret stdout" not in encoded
    assert "secret-invoice" not in encoded


def test_brain_post_deploy_email_probe_can_pass_while_lavatop_stays_blocked() -> None:
    module = _load_module()

    report = module.build_brain_post_deploy_report(
        remote_payload={
            "checks": [
                {
                    "name": "email_delivery_verify",
                    "status": "PASS",
                    "missing": [],
                    "note": "sent",
                    "source": "brain",
                    "http_status": 202,
                },
                {
                    "name": "email_delivery_reset",
                    "status": "PASS",
                    "missing": [],
                    "note": "sent",
                    "source": "brain",
                    "http_status": 202,
                },
                {
                    "name": "email_delivery_payment_access_key",
                    "status": "PASS",
                    "missing": [],
                    "note": "sent",
                    "source": "brain",
                    "http_status": 202,
                },
                {
                    "name": "lavatop_live_invoice_creation",
                    "status": "BLOCKED_BY_ACCESS",
                    "missing": ["lavatop_probe_email"],
                    "note": "probe buyer missing",
                    "source": "brain",
                },
            ],
        },
        source_unit="portal-api",
        plan_code="start_99",
    )

    assert report["ok"] is False
    assert report["classification"] == "BLOCKED_BY_ACCESS"
    assert report["post_deploy_probe_mode"] == "email_probe_passed_lavatop_pending"
    assert report["safe_to_keep_email_public"] is True
    assert report["email_public_probe_can_be_evaluated_independently"] is True
    assert report["lavatop_invoice_probe_passed"] is False
    assert report["safe_to_enable_paid_checkout"] is False


def test_brain_post_deploy_script_requires_probe_recipients_without_embedding_secrets() -> None:
    module = _load_module()

    script = module._remote_post_deploy_probe_script(
        unit="portal-api",
        plan_code="start_99",
        email_probe_to="operator@example.test",
        lavatop_probe_email="buyer@example.test",
    )

    assert "operator@example.test" in script
    assert "buyer@example.test" in script
    assert "EMAIL_DELIVERY_WEBHOOK_SECRET" in script
    assert "LAVATOP_API_KEY" in script
    assert "response.read" not in script
    assert "secret response body" not in script
