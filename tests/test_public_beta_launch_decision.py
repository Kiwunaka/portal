from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "public_beta_launch_decision.py"
    spec = importlib.util.spec_from_file_location("public_beta_launch_decision", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_gate(path: Path, *, gate_set: str, brain: bool = False, status: str = "PASS") -> Path:
    lines = [
        "# Release Gate Report",
        "",
        "- Generated at: `2026-05-08 02:00:00`",
        f"- Status: `{status}`",
        f"- Gate set: `{gate_set}`",
        f"- Brain IP supplied: `{'yes' if brain else 'no'}`",
        "",
        "## Evidence Classification",
        "",
        "| Evidence | Scope | Status | Notes |",
        "|---|---|---|---|",
        f"| current-origin check | local {gate_set} gate set | PASS | ok |",
    ]
    if brain:
        lines.append(
            "| brain-origin check | `scripts/verify_brain_ready.py` plus node predeploy readiness | PASS | ok |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_brain_static_verify(path: Path, *, status: str = "PASS_STATIC_NO_GO") -> Path:
    path.write_text(
        "\n".join(
            [
                "# Brain-Origin Static Deploy Verify 2026-05-09",
                "",
                f"Status: `{status}`",
                "",
                "- No runtime `APP_*` sync was performed.",
                "- Paid checkout remained closed.",
                "- Telegram announcement was not posted.",
                "- `https://app.pokrov.space/release-status.json`: `NO_GO`, `safe_to_publish_public_beta=false`",
                "",
                "Until that happens, public beta remains `NO_GO`.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _write_bom_json(path: Path, payload: dict) -> Path:
    path.write_bytes(("\ufeff" + json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return path


def _write_reachability(path: Path, *, ok: bool = True) -> Path:
    if ok:
        text = "\n".join(
            [
                "[OK] staged /api/client/apps payload loaded from apps.json",
                "[OK] release handoff URLs are present",
                "[OK] android.apk_url: HEAD 200 -> https://github.com/example/app/releases/download/v0.2.0/pokrov.apk",
                "[OK] windows.exe_url: HEAD 200 -> https://github.com/example/app/releases/download/v0.2.0/pokrov.exe",
                "[OK] docs_url: HEAD 200 -> https://pokrov.space/install/",
                "[OK] smoke completed",
            ]
        )
    else:
        text = "\n".join(
            [
                "Expected NO-GO evidence. NOT_PUBLISHED.",
                "[OK] release handoff URLs are present",
                "[FAIL] android.apk_url: HEAD failed with 404 ('')",
                "[FAIL] windows.exe_url: HEAD failed with 404 ('')",
                "[OK] docs_url: HEAD 200 -> https://pokrov.space/install/",
            ]
        )
    path.write_text(text + "\n", encoding="utf-8")
    return path


def _write_post_deploy_probe(
    path: Path,
    *,
    ok: bool = True,
    email_runtime: bool = True,
    live_delivery: bool = True,
    invoice: bool = True,
) -> Path:
    payload = {
        "ok": ok,
        "classification": "PASS" if ok else "BLOCKED_BY_ACCESS",
        "mode": "public_beta_post_deploy_probe",
        "email_public_runtime_config_passed": email_runtime,
        "email_live_delivery_probe_passed": live_delivery,
        "lavatop_live_invoice_probe_passed": invoice,
        "safe_to_keep_email_public": email_runtime,
        "safe_to_enable_paid_checkout": ok and email_runtime and live_delivery and invoice,
        "post_deploy_probe_modes": {
            "email_public_runtime": "PASS" if email_runtime else "BLOCKED_BY_ACCESS",
            "email_live_delivery": "PASS" if live_delivery else "BLOCKED_BY_ACCESS",
            "lavatop_invoice": "PASS" if invoice else "BLOCKED_BY_ACCESS",
        },
    }
    return _write_json(path, payload)


def _write_runtime_sync_guard(path: Path) -> Path:
    path.write_text(
        "\n".join(
            [
                "# Runtime Link Sync Guard Evidence",
                "",
                "- Decision: `NO RUNTIME SYNC`",
                "- Classification: `BLOCKED_BY_ACCESS`",
                "",
                "Dry-run command:",
                "`python scripts\\remote_brain_apply_release_handoff.py --brain-ip 82.21.114.104 --metadata-file docs\\audit-artifacts\\staged-client-apps-2026-05-07.json --dry-run`",
                "",
                "- No SSH connection, env write, or service restart was performed.",
                "",
                "Blocked mutation command:",
                "`python scripts\\remote_brain_apply_release_handoff.py --brain-ip 82.21.114.104 --metadata-file docs\\audit-artifacts\\staged-client-apps-2026-05-07.json`",
                "",
                "- Message: `GO evidence file is required for runtime APP_* sync`",
                "",
                "- `OPERATOR_APPROVED_RUNTIME_LINK_SYNC=true`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return path


class PublicBetaLaunchDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_default_external_preflight_uses_current_20260509_artifact(self) -> None:
        expected = Path("docs/audit-artifacts/public-beta-external-access-preflight-2026-05-09.json")

        self.assertEqual(self.module.DEFAULT_EXTERNAL_PREFLIGHT_JSON, expected)
        report = self.module.build_report()
        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(checks["external_access_preflight"]["source"], str(expected))
        self.assertNotIn("docs_url is missing", "\n".join(checks["external_access_preflight"]["missing"]))
        self.assertIn("runtime APP_ANDROID_APK_URL is not synced", checks["external_access_preflight"]["missing"])
        self.assertIn("runtime APP_WINDOWS_EXE_URL is not synced", checks["external_access_preflight"]["missing"])
        self.assertNotIn("android release URL is missing", checks["external_access_preflight"]["missing"])

    def test_default_post_deploy_probe_uses_current_20260514_artifact(self) -> None:
        expected = Path("docs/audit-artifacts/public-beta-post-deploy-probe-2026-05-14.json")

        self.assertEqual(self.module.DEFAULT_POST_DEPLOY_PROBE, expected)
        report = self.module.build_report()
        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(checks["post_deploy_payment_email_probe"]["source"], str(expected))

    def test_default_brain_static_verify_uses_current_20260509_artifact(self) -> None:
        expected = Path("docs/audit-artifacts/brain-origin-verify-2026-05-09.md")

        self.assertEqual(self.module.DEFAULT_BRAIN_STATIC_VERIFY, expected)
        report = self.module.build_report()
        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(checks["brain_origin_static_deploy_verify"]["source"], str(expected))
        self.assertEqual(checks["brain_origin_static_deploy_verify"]["status"], "PASS")
        self.assertIn("runtime links", checks["brain_origin_static_deploy_verify"]["note"])

    def test_current_artifacts_remain_no_go(self) -> None:
        report = self.module.build_report()

        self.assertFalse(report["ok"])
        self.assertEqual(report["verdict"], "NO_GO")
        self.assertFalse(report["safe_to_publish_public_beta"])
        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(checks["runtime_link_sync_guard"]["status"], "PASS")
        self.assertIn("does not authorize runtime APP_* sync", checks["runtime_link_sync_guard"]["note"])
        self.assertEqual(checks["brain_origin_static_deploy_verify"]["status"], "PASS")
        self.assertEqual(checks["public_beta_handoff_policy"]["status"], "BLOCKED_BY_POLICY")
        self.assertEqual(checks["completion_audit_verdict"]["status"], "BLOCKED_BY_POLICY")
        self.assertIn(checks["external_access_preflight"]["status"], {"BLOCKED_BY_ACCESS", "FAIL"})
        self.assertEqual(checks["post_deploy_payment_email_probe"]["status"], "BLOCKED_BY_ACCESS")
        self.assertIn("email live delivery proof", checks["post_deploy_payment_email_probe"]["missing"])
        self.assertIn("Lava.top live invoice proof", checks["post_deploy_payment_email_probe"]["missing"])
        self.assertNotIn("PASSWORDS.txt", json.dumps(report, ensure_ascii=False))

    def test_all_green_evidence_allows_go(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "handoff.md").write_text("GO for public beta publication.\n", encoding="utf-8")
            (root / "completion.md").write_text("GOAL COMPLETE. Public beta publication is GO.\n", encoding="utf-8")
            _write_json(
                root / "external.json",
                {"ok": True, "classification": "PASS", "safe_to_publish_public_beta": True, "checks": []},
            )
            _write_gate(root / "full.md", gate_set="default")
            _write_gate(root / "quick.md", gate_set="quick")
            _write_gate(root / "brain.md", gate_set="quick", brain=True)
            _write_json(
                root / "paid.json",
                {"ok": True, "classification": "PASS", "safe_to_enable_paid_checkout": True, "checks": []},
            )
            _write_json(
                root / "email.json",
                {
                    "enabled": True,
                    "public_enabled": True,
                    "delivery_configured": True,
                    "delivery_secret_configured": True,
                    "debug_echo": False,
                },
            )
            _write_json(
                root / "payment.json",
                {
                    "ok": True,
                    "blocked": False,
                    "provider_count": 1,
                    "provider_codes": ["lavatop"],
                },
            )

            report = self.module.build_report(
                handoff=root / "handoff.md",
                completion_audit=root / "completion.md",
                external_preflight_json=root / "external.json",
                full_gate=root / "full.md",
                quick_gate=root / "quick.md",
                brain_gate=root / "brain.md",
                brain_static_verify=_write_brain_static_verify(root / "brain-static.md"),
                paid_checkout_evidence=root / "paid.json",
                live_email_status=root / "email.json",
                live_payment_status=root / "payment.json",
                post_deploy_probe=_write_post_deploy_probe(root / "post.json"),
                staged_reachability=_write_reachability(root / "reachability.md"),
                runtime_sync_guard=_write_runtime_sync_guard(root / "runtime-sync-guard.md"),
            )

        self.assertTrue(report["ok"])
        self.assertEqual(report["verdict"], "GO")
        self.assertEqual(report["classification"], "PASS")
        self.assertTrue(report["safe_to_publish_public_beta"])

    def test_external_preflight_with_operator_skip_allows_go_with_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "handoff.md").write_text("GO for public beta publication.\n", encoding="utf-8")
            (root / "completion.md").write_text("GOAL COMPLETE. Public beta publication is GO.\n", encoding="utf-8")
            _write_json(
                root / "external.json",
                {
                    "ok": True,
                    "classification": "PASS_WITH_ACCEPTED_SKIPS",
                    "safe_to_publish_public_beta": True,
                    "accepted_skips": ["ru_origin_probe_evidence"],
                    "checks": [
                        {
                            "name": "ru_origin_probe_evidence",
                            "status": "SKIPPED_BY_OPERATOR",
                            "missing": [],
                            "note": "Do not claim RU-origin readiness.",
                        }
                    ],
                },
            )
            _write_gate(root / "full.md", gate_set="default")
            _write_gate(root / "quick.md", gate_set="quick")
            _write_gate(root / "brain.md", gate_set="quick", brain=True)
            _write_json(
                root / "paid.json",
                {"ok": True, "classification": "PASS", "safe_to_enable_paid_checkout": True, "checks": []},
            )
            _write_json(
                root / "email.json",
                {
                    "enabled": True,
                    "public_enabled": True,
                    "delivery_configured": True,
                    "delivery_secret_configured": True,
                    "debug_echo": False,
                },
            )
            _write_json(
                root / "payment.json",
                {
                    "ok": True,
                    "blocked": False,
                    "provider_count": 1,
                    "provider_codes": ["lavatop"],
                },
            )

            report = self.module.build_report(
                handoff=root / "handoff.md",
                completion_audit=root / "completion.md",
                external_preflight_json=root / "external.json",
                full_gate=root / "full.md",
                quick_gate=root / "quick.md",
                brain_gate=root / "brain.md",
                paid_checkout_evidence=root / "paid.json",
                live_email_status=root / "email.json",
                live_payment_status=root / "payment.json",
                post_deploy_probe=_write_post_deploy_probe(root / "post.json"),
                staged_reachability=_write_reachability(root / "reachability.md"),
                runtime_sync_guard=_write_runtime_sync_guard(root / "runtime-sync-guard.md"),
            )

        self.assertTrue(report["ok"])
        self.assertEqual(report["verdict"], "GO")
        self.assertEqual(report["classification"], "PASS_WITH_ACCEPTED_SKIPS")
        self.assertIn("RU-origin не проверялся", "\n".join(report["safe_public_claims"]))
        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(checks["external_access_preflight"]["status"], "PASS_WITH_ACCEPTED_SKIPS")

    def test_missing_brain_origin_evidence_keeps_no_go_even_when_status_line_says_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "handoff.md").write_text("GO for public beta publication.\n", encoding="utf-8")
            (root / "completion.md").write_text("GOAL COMPLETE. Public beta publication is GO.\n", encoding="utf-8")
            _write_gate(root / "full.md", gate_set="default")
            _write_gate(root / "quick.md", gate_set="quick")
            _write_gate(root / "brain.md", gate_set="quick", brain=False)
            _write_json(root / "external.json", {"ok": True, "classification": "PASS", "safe_to_publish_public_beta": True})
            _write_json(root / "paid.json", {"ok": True, "classification": "PASS", "safe_to_enable_paid_checkout": True})
            _write_json(
                root / "email.json",
                {"enabled": True, "public_enabled": True, "delivery_configured": True, "delivery_secret_configured": True, "debug_echo": False},
            )
            _write_json(
                root / "payment.json",
                {"ok": True, "blocked": False, "provider_count": 1, "provider_codes": ["lavatop"]},
            )

            report = self.module.build_report(
                handoff=root / "handoff.md",
                completion_audit=root / "completion.md",
                external_preflight_json=root / "external.json",
                full_gate=root / "full.md",
                quick_gate=root / "quick.md",
                brain_gate=root / "brain.md",
                paid_checkout_evidence=root / "paid.json",
                live_email_status=root / "email.json",
                live_payment_status=root / "payment.json",
                post_deploy_probe=_write_post_deploy_probe(root / "post.json"),
                staged_reachability=_write_reachability(root / "reachability.md"),
                runtime_sync_guard=_write_runtime_sync_guard(root / "runtime-sync-guard.md"),
            )

        self.assertFalse(report["ok"])
        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(checks["brain_origin_quick_gate"]["status"], "FAIL")
        self.assertIn("Brain IP supplied", "\n".join(checks["brain_origin_quick_gate"]["missing"]))

    def test_pass_classification_without_safe_flags_is_not_trusted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "handoff.md").write_text("GO for public beta publication.\n", encoding="utf-8")
            (root / "completion.md").write_text("GOAL COMPLETE. Public beta publication is GO.\n", encoding="utf-8")
            _write_gate(root / "full.md", gate_set="default")
            _write_gate(root / "quick.md", gate_set="quick")
            _write_gate(root / "brain.md", gate_set="quick", brain=True)
            _write_json(root / "external.json", {"ok": True, "classification": "PASS", "safe_to_publish_public_beta": False})
            _write_json(root / "paid.json", {"ok": True, "classification": "PASS", "safe_to_enable_paid_checkout": False})
            _write_json(
                root / "email.json",
                {"enabled": True, "public_enabled": True, "delivery_configured": True, "delivery_secret_configured": True, "debug_echo": False},
            )
            _write_json(
                root / "payment.json",
                {"ok": True, "blocked": False, "provider_count": 2, "provider_codes": ["lavatop"]},
            )

            report = self.module.build_report(
                handoff=root / "handoff.md",
                completion_audit=root / "completion.md",
                external_preflight_json=root / "external.json",
                full_gate=root / "full.md",
                quick_gate=root / "quick.md",
                brain_gate=root / "brain.md",
                paid_checkout_evidence=root / "paid.json",
                live_email_status=root / "email.json",
                live_payment_status=root / "payment.json",
                post_deploy_probe=_write_post_deploy_probe(root / "post.json"),
                staged_reachability=_write_reachability(root / "reachability.md"),
            )

        checks = {check["name"]: check for check in report["checks"]}
        self.assertFalse(report["ok"])
        self.assertEqual(checks["external_access_preflight"]["status"], "FAIL")
        self.assertEqual(checks["paid_checkout_launch_evidence"]["status"], "FAIL")
        self.assertEqual(checks["live_payment_provider_status"]["status"], "FAIL")
        self.assertIn("provider_count must be 1", checks["live_payment_provider_status"]["missing"])

    def test_unreachable_staged_release_assets_keep_no_go(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "handoff.md").write_text("GO for public beta publication.\n", encoding="utf-8")
            (root / "completion.md").write_text("GOAL COMPLETE. Public beta publication is GO.\n", encoding="utf-8")
            _write_gate(root / "full.md", gate_set="default")
            _write_gate(root / "quick.md", gate_set="quick")
            _write_gate(root / "brain.md", gate_set="quick", brain=True)
            _write_json(root / "external.json", {"ok": True, "classification": "PASS", "safe_to_publish_public_beta": True})
            _write_json(root / "paid.json", {"ok": True, "classification": "PASS", "safe_to_enable_paid_checkout": True})
            _write_json(
                root / "email.json",
                {"enabled": True, "public_enabled": True, "delivery_configured": True, "delivery_secret_configured": True, "debug_echo": False},
            )
            _write_json(
                root / "payment.json",
                {"ok": True, "blocked": False, "provider_count": 1, "provider_codes": ["lavatop"]},
            )

            report = self.module.build_report(
                handoff=root / "handoff.md",
                completion_audit=root / "completion.md",
                external_preflight_json=root / "external.json",
                full_gate=root / "full.md",
                quick_gate=root / "quick.md",
                brain_gate=root / "brain.md",
                paid_checkout_evidence=root / "paid.json",
                live_email_status=root / "email.json",
                live_payment_status=root / "payment.json",
                post_deploy_probe=_write_post_deploy_probe(root / "post.json"),
                staged_reachability=_write_reachability(root / "reachability.md", ok=False),
            )

        checks = {check["name"]: check for check in report["checks"]}
        self.assertFalse(report["ok"])
        self.assertEqual(checks["staged_client_apps_reachability"]["status"], "BLOCKED_BY_ACCESS")
        self.assertIn("android.apk_url", "\n".join(checks["staged_client_apps_reachability"]["missing"]))
        self.assertNotIn("[OK] android.apk_url:", checks["staged_client_apps_reachability"]["missing"])
        self.assertNotIn("[OK] windows.exe_url:", checks["staged_client_apps_reachability"]["missing"])

    def test_blocked_live_payment_and_email_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "handoff.md").write_text("NO-GO for public beta publication.\n", encoding="utf-8")
            (root / "completion.md").write_text("GOAL NOT COMPLETE. Public beta publication remains NO-GO.\n", encoding="utf-8")
            _write_gate(root / "full.md", gate_set="default")
            _write_gate(root / "quick.md", gate_set="quick")
            _write_gate(root / "brain.md", gate_set="quick", brain=True)
            _write_json(root / "external.json", {"ok": False, "classification": "BLOCKED_BY_ACCESS", "checks": []})
            _write_json(root / "paid.json", {"ok": False, "classification": "BLOCKED_BY_ACCESS", "checks": []})
            _write_json(
                root / "email.json",
                {"enabled": False, "public_enabled": False, "delivery_configured": True, "delivery_secret_configured": True, "debug_echo": False, "blocked_reasons": ["public_email_disabled"]},
            )
            _write_json(
                root / "payment.json",
                {"ok": False, "blocked": True, "provider_count": 0, "provider_codes": [], "blocked_reasons": ["paid_checkout_launch_evidence_missing"]},
            )

            report = self.module.build_report(
                handoff=root / "handoff.md",
                completion_audit=root / "completion.md",
                external_preflight_json=root / "external.json",
                full_gate=root / "full.md",
                quick_gate=root / "quick.md",
                brain_gate=root / "brain.md",
                paid_checkout_evidence=root / "paid.json",
                live_email_status=root / "email.json",
                live_payment_status=root / "payment.json",
                post_deploy_probe=_write_post_deploy_probe(root / "post.json", ok=False, live_delivery=False, invoice=False),
                staged_reachability=_write_reachability(root / "reachability.md"),
            )

        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(report["verdict"], "NO_GO")
        self.assertEqual(checks["live_email_auth_status"]["status"], "BLOCKED_BY_ACCESS")
        self.assertEqual(checks["live_payment_provider_status"]["status"], "BLOCKED_BY_ACCESS")
        self.assertEqual(checks["post_deploy_payment_email_probe"]["status"], "BLOCKED_BY_ACCESS")
        self.assertIn("public_email_disabled", checks["live_email_auth_status"]["missing"])
        self.assertIn("paid_checkout_launch_evidence_missing", checks["live_payment_provider_status"]["missing"])
        self.assertNotIn("provider_count must be 1", checks["live_payment_provider_status"]["missing"])
        self.assertIn("email live delivery proof", checks["post_deploy_payment_email_probe"]["missing"])

    def test_live_payment_status_accepts_raw_provider_catalog_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "handoff.md").write_text("GO for public beta publication.\n", encoding="utf-8")
            (root / "completion.md").write_text("GOAL COMPLETE. Public beta publication is GO.\n", encoding="utf-8")
            _write_gate(root / "full.md", gate_set="default")
            _write_gate(root / "quick.md", gate_set="quick")
            _write_gate(root / "brain.md", gate_set="quick", brain=True)
            _write_json(root / "external.json", {"ok": True, "classification": "PASS", "safe_to_publish_public_beta": True})
            _write_json(root / "paid.json", {"ok": True, "classification": "PASS", "safe_to_enable_paid_checkout": True})
            _write_json(
                root / "email.json",
                {"enabled": True, "public_enabled": True, "delivery_configured": True, "delivery_secret_configured": True, "debug_echo": False},
            )
            _write_json(
                root / "payment.json",
                {
                    "ok": True,
                    "blocked": False,
                    "providers": [{"code": "lavatop", "title": "Lava.top"}],
                },
            )

            report = self.module.build_report(
                handoff=root / "handoff.md",
                completion_audit=root / "completion.md",
                external_preflight_json=root / "external.json",
                full_gate=root / "full.md",
                quick_gate=root / "quick.md",
                brain_gate=root / "brain.md",
                paid_checkout_evidence=root / "paid.json",
                live_email_status=root / "email.json",
                live_payment_status=root / "payment.json",
                post_deploy_probe=_write_post_deploy_probe(root / "post.json"),
                staged_reachability=_write_reachability(root / "reachability.md"),
                runtime_sync_guard=_write_runtime_sync_guard(root / "runtime-sync-guard.md"),
            )

        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(checks["live_payment_provider_status"]["status"], "PASS")
        self.assertNotIn("provider_count must be 1", checks["live_payment_provider_status"]["missing"])

    def test_safe_claim_describes_runtime_sync_before_live_smoke(self) -> None:
        report = self.module.build_report()

        safe_claims = "\n".join(report["safe_public_claims"])
        self.assertIn(
            "GitHub Releases можно описывать только как предварительные артефакты для проверки, пока ссылки загрузки не авторизованы, не синхронизированы и не прошли живую контрольную проверку.",
            safe_claims,
        )
        self.assertNotIn("synced after live smoke", safe_claims)
        self.assertNotIn("POKROV is in public-beta preparation.", safe_claims)
        self.assertNotIn("Do not claim RU-origin readiness", safe_claims)

    def test_live_email_status_without_relay_secret_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "handoff.md").write_text("GO for public beta publication.\n", encoding="utf-8")
            (root / "completion.md").write_text("GOAL COMPLETE. Public beta publication is GO.\n", encoding="utf-8")
            _write_gate(root / "full.md", gate_set="default")
            _write_gate(root / "quick.md", gate_set="quick")
            _write_gate(root / "brain.md", gate_set="quick", brain=True)
            _write_json(root / "external.json", {"ok": True, "classification": "PASS", "safe_to_publish_public_beta": True})
            _write_json(root / "paid.json", {"ok": True, "classification": "PASS", "safe_to_enable_paid_checkout": True})
            _write_json(
                root / "email.json",
                {
                    "enabled": True,
                    "public_enabled": True,
                    "delivery_configured": True,
                    "delivery_secret_configured": False,
                    "debug_echo": False,
                    "blocked_reasons": [],
                },
            )
            _write_json(
                root / "payment.json",
                {"ok": True, "blocked": False, "provider_count": 1, "provider_codes": ["lavatop"]},
            )

            report = self.module.build_report(
                handoff=root / "handoff.md",
                completion_audit=root / "completion.md",
                external_preflight_json=root / "external.json",
                full_gate=root / "full.md",
                quick_gate=root / "quick.md",
                brain_gate=root / "brain.md",
                paid_checkout_evidence=root / "paid.json",
                live_email_status=root / "email.json",
                live_payment_status=root / "payment.json",
                post_deploy_probe=_write_post_deploy_probe(root / "post.json"),
                staged_reachability=_write_reachability(root / "reachability.md"),
            )

        checks = {check["name"]: check for check in report["checks"]}
        self.assertFalse(report["ok"])
        self.assertEqual(checks["live_email_auth_status"]["status"], "BLOCKED_BY_ACCESS")
        self.assertIn("delivery_webhook_secret_missing", checks["live_email_auth_status"]["missing"])

    def test_utf8_bom_live_status_json_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "handoff.md").write_text("GO for public beta publication.\n", encoding="utf-8")
            (root / "completion.md").write_text("GOAL COMPLETE. Public beta publication is GO.\n", encoding="utf-8")
            _write_gate(root / "full.md", gate_set="default")
            _write_gate(root / "quick.md", gate_set="quick")
            _write_gate(root / "brain.md", gate_set="quick", brain=True)
            _write_json(root / "external.json", {"ok": True, "classification": "PASS", "safe_to_publish_public_beta": True})
            _write_json(root / "paid.json", {"ok": True, "classification": "PASS", "safe_to_enable_paid_checkout": True})
            _write_bom_json(
                root / "email.json",
                {"enabled": True, "public_enabled": True, "delivery_configured": True, "delivery_secret_configured": True, "debug_echo": False},
            )
            _write_bom_json(
                root / "payment.json",
                {"ok": True, "blocked": False, "provider_count": 1, "provider_codes": ["lavatop"]},
            )

            report = self.module.build_report(
                handoff=root / "handoff.md",
                completion_audit=root / "completion.md",
                external_preflight_json=root / "external.json",
                full_gate=root / "full.md",
                quick_gate=root / "quick.md",
                brain_gate=root / "brain.md",
                paid_checkout_evidence=root / "paid.json",
                live_email_status=root / "email.json",
                live_payment_status=root / "payment.json",
                post_deploy_probe=_write_post_deploy_probe(root / "post.json"),
                staged_reachability=_write_reachability(root / "reachability.md"),
            )

        self.assertTrue(report["ok"])


if __name__ == "__main__":
    unittest.main()
