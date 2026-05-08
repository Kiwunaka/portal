from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "payment_email_readiness_smoke.py"
    spec = importlib.util.spec_from_file_location("payment_email_readiness_smoke", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_missing_payment_email_env_is_blocked_without_secret_leakage() -> None:
    module = _load_module()

    report = module.build_report(
        env={
            "LAVATOP_API_KEY": "super-secret-api-key",
            "LAVATOP_WEBHOOK_API_KEY": "",
            "EMAIL_DELIVERY_WEBHOOK_SECRET": "super-secret-email-secret",
        },
        plan_code="start_99",
    )

    assert report["ok"] is False
    assert report["safe_to_enable_paid_checkout"] is False
    assert report["classification"] == "BLOCKED_BY_ACCESS"
    serialized = module.json.dumps(report, ensure_ascii=False)
    assert "super-secret" not in serialized
    checks = {check["name"]: check for check in report["checks"]}
    assert checks["lavatop_invoice_credentials"]["status"] == "BLOCKED_BY_ACCESS"
    assert "LAVATOP_OFFER_ID_START_99 or LAVATOP_OFFER_ID" in checks["lavatop_invoice_credentials"]["missing"]
    assert checks["lavatop_webhook_auth"]["status"] == "BLOCKED_BY_ACCESS"
    assert checks["email_delivery_webhook"]["status"] == "BLOCKED_BY_ACCESS"


def test_ready_payment_email_env_passes_without_exposing_values() -> None:
    module = _load_module()

    report = module.build_report(
        env={
            "LAVATOP_API_KEY": "live-api-key",
            "LAVATOP_OFFER_ID_START_99": "offer-start",
            "LAVATOP_WEBHOOK_BASIC_USERNAME": "merchant",
            "LAVATOP_WEBHOOK_BASIC_PASSWORD": "webhook-password",
            "EMAIL_AUTH_PUBLIC_ENABLED": "true",
            "EMAIL_AUTH_DEBUG_ECHO": "false",
            "EMAIL_DELIVERY_WEBHOOK_URL": "https://relay.pokrov.test/send",
            "EMAIL_DELIVERY_WEBHOOK_SECRET": "email-secret",
            "LAVATOP_PROVIDER_ACCEPTANCE_CONFIRMED": "true",
        },
        plan_code="start_99",
    )

    assert report["ok"] is True
    assert report["safe_to_enable_paid_checkout"] is True
    assert report["classification"] == "PASS"
    assert all(check["status"] == "PASS" for check in report["checks"])
    serialized = module.json.dumps(report, ensure_ascii=False)
    assert "live-api-key" not in serialized
    assert "webhook-password" not in serialized
    assert "email-secret" not in serialized


def test_email_delivery_webhook_requires_secret() -> None:
    module = _load_module()

    report = module.build_report(
        env={
            "LAVATOP_API_KEY": "live-api-key",
            "LAVATOP_OFFER_ID_START_99": "offer-start",
            "LAVATOP_WEBHOOK_API_KEY": "webhook-key",
            "EMAIL_AUTH_PUBLIC_ENABLED": "true",
            "EMAIL_AUTH_DEBUG_ECHO": "false",
            "EMAIL_DELIVERY_WEBHOOK_URL": "https://relay.pokrov.test/send",
            "LAVATOP_PROVIDER_ACCEPTANCE_CONFIRMED": "true",
        },
        plan_code="start_99",
    )

    assert report["ok"] is False
    assert report["safe_to_enable_paid_checkout"] is False
    assert report["classification"] == "BLOCKED_BY_ACCESS"
    checks = {check["name"]: check for check in report["checks"]}
    assert checks["email_delivery_webhook"]["status"] == "BLOCKED_BY_ACCESS"
    assert "EMAIL_DELIVERY_WEBHOOK_SECRET" in checks["email_delivery_webhook"]["missing"]


def test_provider_acceptance_is_external_dependency() -> None:
    module = _load_module()

    report = module.build_report(
        env={
            "LAVATOP_API_KEY": "live-api-key",
            "LAVATOP_OFFER_ID": "offer-default",
            "LAVATOP_WEBHOOK_API_KEY": "webhook-key",
            "EMAIL_AUTH_PUBLIC_ENABLED": "true",
            "EMAIL_AUTH_DEBUG_ECHO": "false",
            "EMAIL_DELIVERY_WEBHOOK_URL": "https://relay.pokrov.test/send",
            "EMAIL_DELIVERY_WEBHOOK_SECRET": "email-secret",
        },
        plan_code="3_months",
    )

    assert report["ok"] is False
    assert report["safe_to_enable_paid_checkout"] is False
    assert report["classification"] == "EXTERNAL_DEPENDENCY"
    checks = {check["name"]: check for check in report["checks"]}
    assert checks["lavatop_provider_acceptance"]["status"] == "EXTERNAL_DEPENDENCY"
