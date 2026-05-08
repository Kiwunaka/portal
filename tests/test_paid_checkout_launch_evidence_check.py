from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "paid_checkout_launch_evidence_check.py"
    spec = importlib.util.spec_from_file_location("paid_checkout_launch_evidence_check", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


class PaidCheckoutLaunchEvidenceCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_current_blocked_readiness_keeps_paid_checkout_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            readiness = _write_json(
                root / "payment-email-readiness.json",
                {
                    "classification": "BLOCKED_BY_ACCESS",
                    "safe_to_enable_paid_checkout": False,
                    "checks": [
                        {
                            "name": "lavatop_invoice_credentials",
                            "status": "BLOCKED_BY_ACCESS",
                            "missing": ["LAVATOP_API_KEY"],
                            "note": "secret value super-secret-api-key must not leak",
                        },
                        {"name": "lavatop_provider_acceptance", "status": "EXTERNAL_DEPENDENCY"},
                    ],
                },
            )

            report = self.module.build_report(readiness_json=readiness, evidence_json=None)

        self.assertFalse(report["ok"])
        self.assertFalse(report["safe_to_enable_paid_checkout"])
        self.assertEqual(report["classification"], "BLOCKED_BY_ACCESS")
        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(checks["payment_email_readiness"]["status"], "BLOCKED_BY_ACCESS")
        self.assertEqual(checks["lavatop_live_invoice_creation"]["status"], "BLOCKED_BY_ACCESS")
        self.assertEqual(checks["lavatop_provider_acceptance"]["status"], "EXTERNAL_DEPENDENCY")
        self.assertNotIn("super-secret-api-key", json.dumps(report, ensure_ascii=False))

    def test_full_redacted_launch_evidence_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            readiness = _write_json(
                root / "payment-email-readiness.json",
                {
                    "classification": "PASS",
                    "safe_to_enable_paid_checkout": True,
                    "checks": [
                        {"name": "lavatop_invoice_credentials", "status": "PASS"},
                        {"name": "lavatop_webhook_auth", "status": "PASS"},
                        {"name": "lavatop_provider_acceptance", "status": "PASS"},
                        {"name": "email_public_mode", "status": "PASS"},
                        {"name": "email_delivery_webhook", "status": "PASS"},
                    ],
                },
            )
            evidence = _write_json(
                root / "paid-checkout-evidence.json",
                {
                    "checks": [
                        {"name": "lavatop_live_invoice_creation", "status": "PASS", "secret": "do-not-print"},
                        {"name": "lavatop_authenticated_success_webhook", "status": "PASS"},
                        {"name": "lavatop_webhook_replay_idempotency", "status": "PASS"},
                        {"name": "lavatop_failed_payment_no_fulfillment", "status": "PASS"},
                        {"name": "lavatop_manual_review_mismatch", "status": "PASS"},
                        {"name": "lavatop_reconciliation_procedure", "status": "PASS"},
                        {"name": "paid_access_key_email_delivery", "status": "PASS"},
                    ]
                },
            )

            report = self.module.build_report(readiness_json=readiness, evidence_json=evidence)

        self.assertTrue(report["ok"])
        self.assertTrue(report["safe_to_enable_paid_checkout"])
        self.assertEqual(report["classification"], "PASS")
        self.assertTrue(all(check["status"] == "PASS" for check in report["checks"]))
        self.assertNotIn("do-not-print", json.dumps(report, ensure_ascii=False))

    def test_invalid_or_missing_evidence_status_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            readiness = _write_json(
                root / "payment-email-readiness.json",
                {
                    "classification": "PASS",
                    "safe_to_enable_paid_checkout": True,
                    "checks": [{"name": "lavatop_provider_acceptance", "status": "PASS"}],
                },
            )
            evidence = _write_json(
                root / "paid-checkout-evidence.json",
                {"checks": [{"name": "lavatop_live_invoice_creation", "status": "PASS"}]},
            )

            report = self.module.build_report(readiness_json=readiness, evidence_json=evidence)

        self.assertFalse(report["ok"])
        self.assertEqual(report["classification"], "BLOCKED_BY_ACCESS")
        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(checks["lavatop_authenticated_success_webhook"]["status"], "BLOCKED_BY_ACCESS")
        self.assertIn("lavatop_authenticated_success_webhook evidence", checks["lavatop_authenticated_success_webhook"]["missing"])


if __name__ == "__main__":
    unittest.main()
