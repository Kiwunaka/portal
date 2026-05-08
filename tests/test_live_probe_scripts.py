from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str):
    module_path = REPO_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run_main(module, argv: list[str], env: dict[str, str]) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with (
        patch.object(sys, "argv", argv),
        patch.dict(os.environ, env, clear=True),
        patch.object(module.urllib.request, "urlopen", side_effect=AssertionError("unexpected network request")),
        contextlib.redirect_stdout(stdout),
        contextlib.redirect_stderr(stderr),
    ):
        code = module.main()
    return code, stdout.getvalue(), stderr.getvalue()


def test_email_delivery_probe_dry_run_is_non_mutating_and_redacted() -> None:
    module = _load_module("email_delivery_probe")

    code, stdout, stderr = _run_main(
        module,
        ["email_delivery_probe.py", "--kind", "payment_access_key", "--email", "operator@example.test"],
        {
            "EMAIL_DELIVERY_WEBHOOK_URL": "https://relay.pokrov.test/send",
            "EMAIL_DELIVERY_WEBHOOK_SECRET": "super-secret-email-relay-token",
        },
    )

    report = json.loads(stdout)
    assert code == 0
    assert stderr == ""
    assert report["dry_run"] is True
    assert report["url_configured"] is True
    assert report["payload"]["kind"] == "payment_access_key"
    assert "super-secret-email-relay-token" not in stdout


def test_email_delivery_probe_live_without_url_stops_before_network() -> None:
    module = _load_module("email_delivery_probe")

    code, stdout, stderr = _run_main(module, ["email_delivery_probe.py", "--live"], {})

    assert code == 2
    assert stdout == ""
    assert "EMAIL_DELIVERY_WEBHOOK_URL is not configured" in stderr


def test_lavatop_invoice_probe_dry_run_redacts_api_key_and_offer_id() -> None:
    module = _load_module("lavatop_invoice_probe")

    code, stdout, stderr = _run_main(
        module,
        ["lavatop_invoice_probe.py", "--plan-code", "start_99", "--email", "operator@example.test"],
        {
            "LAVATOP_API_KEY": "super-secret-lavatop-api-key",
            "LAVATOP_OFFER_ID_START_99": "super-secret-offer-id",
            "LAVATOP_DYNAMIC_AMOUNT_ENABLED": "true",
        },
    )

    report = json.loads(stdout)
    assert code == 0
    assert stderr == ""
    assert report["dry_run"] is True
    assert report["api_key_configured"] is True
    assert report["payload"]["offerId"] == "configured"
    assert report["payload"]["amount"] == 99.0
    assert "super-secret-lavatop-api-key" not in stdout
    assert "super-secret-offer-id" not in stdout


def test_lavatop_invoice_probe_live_without_credentials_stops_before_network() -> None:
    module = _load_module("lavatop_invoice_probe")

    code, stdout, stderr = _run_main(
        module,
        ["lavatop_invoice_probe.py", "--plan-code", "start_99", "--live"],
        {"LAVATOP_API_KEY": "super-secret-lavatop-api-key"},
    )

    assert code == 2
    assert stdout == ""
    assert "LAVATOP_API_KEY and LAVATOP_OFFER_ID(_PLAN) are required" in stderr
    assert "super-secret-lavatop-api-key" not in stderr
