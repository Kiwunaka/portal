from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "public_beta_external_access_preflight.py"
    spec = importlib.util.spec_from_file_location("public_beta_external_access_preflight", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_staged_payload(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "android": {
                    "play_url": "",
                    "apk_url": "https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/pokrov-android-universal.apk",
                },
                "windows": {
                    "exe_url": "https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/pokrov-windows-setup-x64.exe",
                },
                "docs_url": "https://pokrov.space/install/",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def _write_ru_payload(path: Path, *, status: str = "PASS", classification: str = "PASS") -> Path:
    path.write_text(
        json.dumps(
            {
                "timestamp_utc": "2026-05-08T00:00:00Z",
                "origin": "mini",
                "status": status,
                "classification": classification,
                "summary": "redacted RU-origin probe fixture",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def _write_ru_skip_evidence(path: Path, *, include_claim_guard: bool = True) -> Path:
    lines = [
        "# RU-Origin Skip Evidence",
        "",
        "RU_ORIGIN_SKIP_ACCEPTED=true",
        "RU_ORIGIN_SKIP_REASON=Operator allowed skipping RU-origin readiness for this beta pass when port 22 access remains blocked.",
    ]
    if include_claim_guard:
        lines.append("RU_ORIGIN_PUBLIC_CLAIMS_MUST_STATE_UNVERIFIED=true")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_client_build_evidence(path: Path, *, authenticode: str = "Valid", unsigned_risk_accepted: bool = False) -> Path:
    risk_line = "  - Unsigned beta risk accepted: `Accepted`" if unsigned_risk_accepted else ""
    path.write_text(
        "\n".join(
            [
                "# Client Build Evidence",
                "",
                "## Artifacts",
                "",
                "- Windows setup EXE: `pokrov-windows-beta-x64-0.2.0-beta.1-setup.exe`",
                f"  - Authenticode: `{authenticode}`",
                risk_line,
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _write_android_validation(path: Path, *, ok: bool = True) -> Path:
    path.write_text(
        json.dumps(
            {
                "ok": ok,
                "classification": "PASS" if ok else "BLOCKED_BY_ACCESS",
                "missing": [] if ok else ["physical adb serial"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def _write_android_operator_attestation(path: Path, *, include_claim_guard: bool = True) -> Path:
    lines = [
        "# Android Physical Audit Operator Attestation",
        "",
        "ANDROID_PHYSICAL_AUDIT_OPERATOR_OK=true",
        "ANDROID_PHYSICAL_AUDIT_SCOPE=physical_release_build_localhost_control_surface",
    ]
    if include_claim_guard:
        lines.append("ANDROID_PHYSICAL_AUDIT_PUBLIC_CLAIMS_MUST_STATE_OPERATOR_ATTESTED=true")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_artifact_staging_authorization(path: Path) -> Path:
    path.write_text(
        "\n".join(
            [
                "# Artifact Staging Authorization",
                "",
                "ARTIFACT STAGING GO FOR RUNTIME SMOKE",
                "NON-URL P0 GATES GREEN FOR ARTIFACT STAGING",
                "ONLY REMAINING P0 GATE: RUNTIME APP-DOWNLOAD URL SMOKE",
                "NO RUNTIME SYNC OR ANNOUNCEMENT",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _write_runtime_smoke(path: Path, *, passed: bool = True) -> Path:
    missing = [] if passed else ["android release URL is missing", "windows release URL is missing", "docs_url is missing"]
    path.write_text(
        json.dumps(
            {
                "ok": passed,
                "classification": "PASS" if passed else "BLOCKED_BY_ACCESS",
                "mode": "brain_runtime_app_download_smoke",
                "runtime_app_download_smoke_passed": passed,
                "checks": [
                    {"name": "api_client_apps_signed_init_data", "status": "PASS", "missing": []},
                    {
                        "name": "runtime_client_apps_release_handoff",
                        "status": "PASS" if passed else "BLOCKED_BY_ACCESS",
                        "missing": missing,
                    },
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


class PublicBetaExternalAccessPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_default_handoff_points_to_latest_public_beta_handoff(self) -> None:
        self.assertEqual(
            Path(self.module.DEFAULT_HANDOFF).as_posix(),
            "docs/audit-artifacts/public-beta-handoff-2026-05-08.md",
        )

    def test_default_runtime_smoke_points_to_latest_docs_default_probe(self) -> None:
        self.assertEqual(
            Path(self.module.DEFAULT_RUNTIME_APP_DOWNLOAD_SMOKE).as_posix(),
            "docs/audit-artifacts/runtime-app-download-smoke-brain-2026-05-09-docs-default.json",
        )

    def test_default_staged_apps_points_to_client_release_handoff(self) -> None:
        self.assertEqual(
            Path(self.module.DEFAULT_STAGED_APPS_JSON).as_posix(),
            "../POKROV-app/artifacts/releases/release-handoff.json",
        )

    def test_staged_apps_check_accepts_client_release_handoff_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            handoff = Path(temp_root) / "release-handoff.json"
            handoff.write_text(
                json.dumps(
                    {
                        "downloads": {
                            "android": {
                                "play_url": "",
                                "apk_url": "https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/pokrov-android-universal.apk",
                            },
                            "windows": {
                                "exe_url": "https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/pokrov-windows-setup-x64.exe",
                            },
                            "docs_url": "https://pokrov.space/install/",
                        },
                        "runtime_env": {
                            "APP_ANDROID_APK_URL": "https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/pokrov-android-universal.apk",
                            "APP_WINDOWS_EXE_URL": "https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/pokrov-windows-setup-x64.exe",
                            "APP_DOCS_URL": "https://pokrov.space/install/",
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            check = self.module._staged_apps_check(handoff)

        self.assertEqual(check["status"], "PASS")
        self.assertEqual(check["missing"], [])

    def test_public_claim_guardrails_are_russian(self) -> None:
        report = self.module.build_report(env={})

        guardrails = "\n".join(report["public_claim_guardrails"])
        self.assertIn("Не заявлять готовность RU-origin", guardrails)
        self.assertIn("Email-доставку", guardrails)
        self.assertIn("Lava.top", guardrails)
        self.assertNotIn("Do not claim RU-origin readiness", guardrails)
        self.assertNotIn("public copy may only say", guardrails)
        self.assertNotIn("Do not treat a Lava.top invoice probe", guardrails)

    def test_missing_env_is_blocked_without_leaking_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            handoff = root / "handoff.md"
            handoff.write_text("NO-GO for public beta publication.\n", encoding="utf-8")
            staged = _write_staged_payload(root / "apps.json")
            ru_origin = _write_ru_payload(root / "ru-origin.json")
            client_evidence = _write_client_build_evidence(root / "client-build.md")
            android_validation = _write_android_validation(root / "android-validation.json", ok=False)

            report = self.module.build_report(
                env={"GITHUB_TOKEN": "secret-github-token"},
                handoff_path=handoff,
                staged_apps_json=staged,
                ru_origin_json=ru_origin,
                client_build_evidence=client_evidence,
                android_audit_validation=android_validation,
            )

        self.assertFalse(report["ok"])
        self.assertFalse(report["safe_to_publish_public_beta"])
        self.assertFalse(report["ready_to_run_access_gated_smokes"])
        self.assertFalse(report["ready_to_run_email_post_deploy_probe"])
        self.assertFalse(report["ready_to_run_lavatop_post_deploy_probe"])
        self.assertEqual(report["classification"], "BLOCKED_BY_ACCESS")
        serialized = json.dumps(report, ensure_ascii=False)
        self.assertNotIn("secret-github-token", serialized)
        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(checks["runtime_app_download_smoke_env"]["status"], "BLOCKED_BY_ACCESS")
        self.assertEqual(checks["github_release_auth"]["status"], "PASS")
        self.assertEqual(checks["public_beta_handoff_policy"]["status"], "BLOCKED_BY_POLICY")

    def test_authenticated_gh_cli_allows_release_auth_without_env_token(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            handoff = root / "handoff.md"
            handoff.write_text("NO-GO for public beta publication.\n", encoding="utf-8")
            staged = _write_staged_payload(root / "apps.json")
            ru_origin = _write_ru_payload(root / "ru-origin.json")
            client_evidence = _write_client_build_evidence(root / "client-build.md")
            android_validation = _write_android_validation(root / "android-validation.json", ok=False)

            report = self.module.build_report(
                env={},
                handoff_path=handoff,
                staged_apps_json=staged,
                ru_origin_json=ru_origin,
                client_build_evidence=client_evidence,
                android_audit_validation=android_validation,
                gh_authenticated=True,
            )

        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(checks["github_release_auth"]["status"], "PASS")
        self.assertEqual(checks["github_release_auth"]["source"], "gh_cli_keyring")

    def test_brain_signed_runtime_smoke_can_replace_raw_init_data_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            handoff = root / "handoff.md"
            handoff.write_text("NO-GO for public beta publication.\n", encoding="utf-8")
            staged = _write_staged_payload(root / "apps.json")
            ru_origin = _write_ru_payload(root / "ru-origin.json")
            client_evidence = _write_client_build_evidence(root / "client-build.md")
            android_validation = _write_android_validation(root / "android-validation.json", ok=True)
            runtime_smoke = _write_runtime_smoke(root / "runtime-smoke.json", passed=True)

            report = self.module.build_report(
                env={
                    "GH_TOKEN": "secret-gh-token",
                    "EMAIL_PROBE_TO": "operator@example.test",
                    "LAVATOP_PROBE_EMAIL": "buyer@example.test",
                },
                handoff_path=handoff,
                staged_apps_json=staged,
                ru_origin_json=ru_origin,
                client_build_evidence=client_evidence,
                android_audit_validation=android_validation,
                runtime_app_download_smoke=runtime_smoke,
            )

        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(checks["runtime_app_download_smoke_env"]["status"], "PASS")
        self.assertEqual(checks["runtime_app_download_smoke_env"]["source"], str(runtime_smoke))
        self.assertTrue(report["ready_to_run_runtime_app_download_smoke"])
        serialized = json.dumps(report, ensure_ascii=False)
        self.assertNotIn("TELEGRAM_INIT_DATA", serialized)
        self.assertNotIn("secret-gh-token", serialized)

    def test_brain_signed_runtime_smoke_reports_runtime_link_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            handoff = root / "handoff.md"
            handoff.write_text("NO-GO for public beta publication.\n", encoding="utf-8")
            staged = _write_staged_payload(root / "apps.json")
            ru_origin = _write_ru_payload(root / "ru-origin.json")
            client_evidence = _write_client_build_evidence(root / "client-build.md")
            android_validation = _write_android_validation(root / "android-validation.json", ok=True)
            runtime_smoke = _write_runtime_smoke(root / "runtime-smoke.json", passed=False)

            report = self.module.build_report(
                env={
                    "GH_TOKEN": "secret-gh-token",
                    "EMAIL_PROBE_TO": "operator@example.test",
                    "LAVATOP_PROBE_EMAIL": "buyer@example.test",
                },
                handoff_path=handoff,
                staged_apps_json=staged,
                ru_origin_json=ru_origin,
                client_build_evidence=client_evidence,
                android_audit_validation=android_validation,
                runtime_app_download_smoke=runtime_smoke,
            )

        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(checks["runtime_app_download_smoke_env"]["status"], "BLOCKED_BY_ACCESS")
        self.assertIn("runtime APP_* sync approval", checks["runtime_app_download_smoke_env"]["missing"])
        self.assertIn(
            "runtime APP_ANDROID_APK_URL is not synced",
            checks["runtime_app_download_smoke_env"]["missing"],
        )
        self.assertIn(
            "runtime APP_WINDOWS_EXE_URL is not synced",
            checks["runtime_app_download_smoke_env"]["missing"],
        )
        self.assertNotIn("android release URL is missing", checks["runtime_app_download_smoke_env"]["missing"])
        self.assertNotIn("TELEGRAM_INIT_DATA", checks["runtime_app_download_smoke_env"]["missing"])

    def test_all_env_present_but_no_go_handoff_is_policy_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            handoff = root / "handoff.md"
            handoff.write_text("NO-GO for public beta publication.\n", encoding="utf-8")
            staged = _write_staged_payload(root / "apps.json")
            ru_origin = _write_ru_payload(root / "ru-origin.json")
            client_evidence = _write_client_build_evidence(root / "client-build.md")
            android_validation = _write_android_validation(root / "android-validation.json", ok=False)

            report = self.module.build_report(
                env={
                    "ANDROID_AUDIT_SERIAL": "R58N12345AB",
                    "TELEGRAM_INIT_DATA": "query_id=AAA&hash=secret",
                    "GH_TOKEN": "secret-gh-token",
                    "EMAIL_PROBE_TO": "operator@example.test",
                    "LAVATOP_PROBE_EMAIL": "buyer@example.test",
                },
                handoff_path=handoff,
                staged_apps_json=staged,
                ru_origin_json=ru_origin,
                client_build_evidence=client_evidence,
                android_audit_validation=android_validation,
            )

        self.assertFalse(report["ok"])
        self.assertTrue(report["ready_to_run_access_gated_smokes"])
        self.assertTrue(report["ready_to_run_runtime_app_download_smoke"])
        self.assertTrue(report["ready_to_run_email_post_deploy_probe"])
        self.assertTrue(report["ready_to_run_lavatop_post_deploy_probe"])
        self.assertFalse(report["safe_to_publish_public_beta"])
        self.assertEqual(report["classification"], "BLOCKED_BY_POLICY")
        serialized = json.dumps(report, ensure_ascii=False)
        self.assertNotIn("query_id=AAA", serialized)
        self.assertNotIn("secret-gh-token", serialized)

    def test_artifact_staging_authorization_does_not_count_as_public_go(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            handoff = root / "handoff.md"
            handoff.write_text("NO-GO for public beta publication.\n", encoding="utf-8")
            staging_auth = _write_artifact_staging_authorization(root / "artifact-staging.md")
            staged = _write_staged_payload(root / "apps.json")
            ru_origin = _write_ru_payload(root / "ru-origin.json")
            client_evidence = _write_client_build_evidence(root / "client-build.md")
            android_validation = _write_android_validation(root / "android-validation.json", ok=False)

            report = self.module.build_report(
                env={
                    "ANDROID_AUDIT_SERIAL": "R58N12345AB",
                    "TELEGRAM_INIT_DATA": "query_id=AAA&hash=secret",
                    "GITHUB_TOKEN": "secret-github-token",
                    "EMAIL_PROBE_TO": "operator@example.test",
                    "LAVATOP_PROBE_EMAIL": "buyer@example.test",
                },
                handoff_path=handoff,
                staged_apps_json=staged,
                ru_origin_json=ru_origin,
                client_build_evidence=client_evidence,
                android_audit_validation=android_validation,
                artifact_staging_authorization=staging_auth,
            )

        self.assertFalse(report["ok"])
        self.assertFalse(report["safe_to_publish_public_beta"])
        self.assertTrue(report["ready_to_run_access_gated_smokes"])
        self.assertEqual(report["classification"], "BLOCKED_BY_POLICY")
        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(checks["public_beta_handoff_policy"]["status"], "BLOCKED_BY_POLICY")
        self.assertEqual(checks["public_beta_handoff_policy"]["missing"], ["GO handoff for public publication"])
        self.assertIn("Separate artifact-staging authorization", checks["public_beta_handoff_policy"]["note"])
        serialized = json.dumps(report, ensure_ascii=False)
        self.assertNotIn("query_id=AAA", serialized)
        self.assertNotIn("secret-github-token", serialized)

    def test_go_handoff_and_inputs_pass_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            handoff = root / "handoff.md"
            handoff.write_text("GO for public beta publication.\n", encoding="utf-8")
            staged = _write_staged_payload(root / "apps.json")
            ru_origin = _write_ru_payload(root / "ru-origin.json")
            client_evidence = _write_client_build_evidence(root / "client-build.md")
            android_validation = _write_android_validation(root / "android-validation.json", ok=False)

            report = self.module.build_report(
                env={
                    "ANDROID_AUDIT_SERIAL": "R58N12345AB",
                    "TELEGRAM_INIT_DATA": "query_id=AAA&hash=secret",
                    "GITHUB_TOKEN": "secret-github-token",
                    "EMAIL_PROBE_TO": "operator@example.test",
                    "LAVATOP_PROBE_EMAIL": "buyer@example.test",
                },
                handoff_path=handoff,
                staged_apps_json=staged,
                ru_origin_json=ru_origin,
                client_build_evidence=client_evidence,
                android_audit_validation=android_validation,
            )

        self.assertTrue(report["ok"])
        self.assertTrue(report["ready_to_run_access_gated_smokes"])
        self.assertTrue(report["ready_to_run_runtime_app_download_smoke"])
        self.assertTrue(report["ready_to_run_email_post_deploy_probe"])
        self.assertTrue(report["ready_to_run_lavatop_post_deploy_probe"])
        self.assertTrue(report["safe_to_publish_public_beta"])
        self.assertEqual(report["classification"], "PASS")

    def test_email_post_deploy_probe_can_be_ready_without_lavatop_probe_env(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            handoff = root / "handoff.md"
            handoff.write_text("GO for public beta publication.\n", encoding="utf-8")
            staged = _write_staged_payload(root / "apps.json")
            ru_origin = _write_ru_payload(root / "ru-origin.json")
            client_evidence = _write_client_build_evidence(root / "client-build.md")
            android_validation = _write_android_validation(root / "android-validation.json", ok=False)

            report = self.module.build_report(
                env={
                    "ANDROID_AUDIT_SERIAL": "R58N12345AB",
                    "TELEGRAM_INIT_DATA": "query_id=AAA&hash=secret",
                    "GITHUB_TOKEN": "secret-github-token",
                    "EMAIL_PROBE_TO": "operator@example.test",
                },
                handoff_path=handoff,
                staged_apps_json=staged,
                ru_origin_json=ru_origin,
                client_build_evidence=client_evidence,
                android_audit_validation=android_validation,
            )

        self.assertFalse(report["ok"])
        self.assertEqual(report["classification"], "BLOCKED_BY_ACCESS")
        self.assertTrue(report["ready_to_run_runtime_app_download_smoke"])
        self.assertTrue(report["ready_to_run_email_post_deploy_probe"])
        self.assertFalse(report["ready_to_run_lavatop_post_deploy_probe"])
        self.assertFalse(report["ready_to_run_access_gated_smokes"])
        self.assertEqual(report["post_deploy_probe_modes"]["email_public_probe"], "READY")
        self.assertEqual(report["post_deploy_probe_modes"]["lavatop_invoice_probe"], "BLOCKED_BY_ACCESS")
        serialized = json.dumps(report, ensure_ascii=False)
        self.assertNotIn("query_id=AAA", serialized)
        self.assertNotIn("secret-github-token", serialized)

    def test_play_url_or_non_github_artifacts_block_staged_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            handoff = root / "handoff.md"
            handoff.write_text("GO for public beta publication.\n", encoding="utf-8")
            ru_origin = _write_ru_payload(root / "ru-origin.json")
            client_evidence = _write_client_build_evidence(root / "client-build.md")
            android_validation = _write_android_validation(root / "android-validation.json", ok=False)
            staged = root / "apps.json"
            staged.write_text(
                json.dumps(
                    {
                        "android": {"play_url": "https://play.google.com/store/apps/details?id=space.pokrov"},
                        "windows": {"exe_url": "https://example.test/pokrov.exe"},
                        "docs_url": "https://example.test/install/",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = self.module.build_report(
                env={
                    "ANDROID_AUDIT_SERIAL": "R58N12345AB",
                    "TELEGRAM_INIT_DATA": "query_id=AAA&hash=secret",
                    "GITHUB_TOKEN": "secret-github-token",
                    "EMAIL_PROBE_TO": "operator@example.test",
                    "LAVATOP_PROBE_EMAIL": "buyer@example.test",
                },
                handoff_path=handoff,
                staged_apps_json=staged,
                ru_origin_json=ru_origin,
                client_build_evidence=client_evidence,
                android_audit_validation=android_validation,
            )

        self.assertFalse(report["ok"])
        self.assertEqual(report["classification"], "BLOCKED_BY_ACCESS")
        checks = {check["name"]: check for check in report["checks"]}
        missing = "\n".join(checks["staged_client_apps_payload"]["missing"])
        self.assertIn("android.play_url must stay empty", missing)
        self.assertIn("android.apk_url GitHub Releases .apk", missing)
        self.assertIn("windows.exe_url GitHub Releases .exe", missing)
        self.assertIn("docs_url under https://pokrov.space/install/", missing)

    def test_ru_origin_failure_and_unsigned_windows_block_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            handoff = root / "handoff.md"
            handoff.write_text("GO for public beta publication.\n", encoding="utf-8")
            staged = _write_staged_payload(root / "apps.json")
            ru_origin = _write_ru_payload(
                root / "ru-origin.json",
                status="FAIL",
                classification="RU_ORIGIN_TELEGRAM_DEGRADED",
            )
            client_evidence = _write_client_build_evidence(root / "client-build.md", authenticode="NotSigned")
            android_validation = _write_android_validation(root / "android-validation.json", ok=False)

            report = self.module.build_report(
                env={
                    "ANDROID_AUDIT_SERIAL": "R58N12345AB",
                    "TELEGRAM_INIT_DATA": "query_id=AAA&hash=secret",
                    "GITHUB_TOKEN": "secret-github-token",
                    "EMAIL_PROBE_TO": "operator@example.test",
                    "LAVATOP_PROBE_EMAIL": "buyer@example.test",
                },
                handoff_path=handoff,
                staged_apps_json=staged,
                ru_origin_json=ru_origin,
                ru_origin_skip_evidence=root / "no-ru-skip.md",
                client_build_evidence=client_evidence,
                android_audit_validation=android_validation,
            )

        self.assertFalse(report["ok"])
        self.assertFalse(report["ready_to_run_access_gated_smokes"])
        self.assertFalse(report["safe_to_publish_public_beta"])
        self.assertEqual(report["classification"], "FAIL")
        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(checks["ru_origin_probe_evidence"]["status"], "FAIL")
        self.assertEqual(checks["windows_signing_or_unsigned_risk"]["status"], "EXTERNAL_DEPENDENCY")

    def test_ru_origin_operator_skip_from_env_is_release_ready_but_disclosed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            handoff = root / "handoff.md"
            handoff.write_text("GO for public beta publication.\n", encoding="utf-8")
            staged = _write_staged_payload(root / "apps.json")
            ru_origin = _write_ru_payload(
                root / "ru-origin.json",
                status="FAIL",
                classification="RU_ORIGIN_TELEGRAM_DEGRADED",
            )
            client_evidence = _write_client_build_evidence(root / "client-build.md")
            android_validation = _write_android_validation(root / "android-validation.json", ok=False)

            report = self.module.build_report(
                env={
                    "ANDROID_AUDIT_SERIAL": "R58N12345AB",
                    "TELEGRAM_INIT_DATA": "query_id=AAA&hash=secret",
                    "GITHUB_TOKEN": "secret-github-token",
                    "EMAIL_PROBE_TO": "operator@example.test",
                    "LAVATOP_PROBE_EMAIL": "buyer@example.test",
                    "RU_ORIGIN_SKIP_ACCEPTED": "true",
                },
                handoff_path=handoff,
                staged_apps_json=staged,
                ru_origin_json=ru_origin,
                client_build_evidence=client_evidence,
                android_audit_validation=android_validation,
            )

        self.assertTrue(report["ok"])
        self.assertTrue(report["ready_to_run_access_gated_smokes"])
        self.assertTrue(report["safe_to_publish_public_beta"])
        self.assertEqual(report["classification"], "PASS_WITH_ACCEPTED_SKIPS")
        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(checks["ru_origin_probe_evidence"]["status"], "SKIPPED_BY_OPERATOR")
        self.assertIn("Do not claim RU-origin readiness", checks["ru_origin_probe_evidence"]["note"])
        serialized = json.dumps(report, ensure_ascii=False)
        self.assertNotIn("query_id=AAA", serialized)
        self.assertNotIn("secret-github-token", serialized)

    def test_ru_origin_skip_evidence_allows_missing_probe_when_claim_guard_is_present(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            handoff = root / "handoff.md"
            handoff.write_text("GO for public beta publication.\n", encoding="utf-8")
            staged = _write_staged_payload(root / "apps.json")
            missing_ru_origin = root / "missing-ru-origin.json"
            ru_skip = _write_ru_skip_evidence(root / "ru-origin-skip.md")
            client_evidence = _write_client_build_evidence(root / "client-build.md")
            android_validation = _write_android_validation(root / "android-validation.json", ok=False)

            report = self.module.build_report(
                env={
                    "ANDROID_AUDIT_SERIAL": "R58N12345AB",
                    "TELEGRAM_INIT_DATA": "query_id=AAA&hash=secret",
                    "GITHUB_TOKEN": "secret-github-token",
                    "EMAIL_PROBE_TO": "operator@example.test",
                    "LAVATOP_PROBE_EMAIL": "buyer@example.test",
                },
                handoff_path=handoff,
                staged_apps_json=staged,
                ru_origin_json=missing_ru_origin,
                ru_origin_skip_evidence=ru_skip,
                client_build_evidence=client_evidence,
                android_audit_validation=android_validation,
            )

        self.assertTrue(report["ok"])
        self.assertEqual(report["classification"], "PASS_WITH_ACCEPTED_SKIPS")
        self.assertEqual(report["accepted_skips"], ["ru_origin_probe_evidence"])
        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(checks["ru_origin_probe_evidence"]["source"], str(ru_skip))

    def test_ru_origin_skip_evidence_without_claim_guard_is_not_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            handoff = root / "handoff.md"
            handoff.write_text("GO for public beta publication.\n", encoding="utf-8")
            staged = _write_staged_payload(root / "apps.json")
            missing_ru_origin = root / "missing-ru-origin.json"
            ru_skip = _write_ru_skip_evidence(root / "ru-origin-skip.md", include_claim_guard=False)
            client_evidence = _write_client_build_evidence(root / "client-build.md")
            android_validation = _write_android_validation(root / "android-validation.json", ok=False)

            report = self.module.build_report(
                env={
                    "ANDROID_AUDIT_SERIAL": "R58N12345AB",
                    "TELEGRAM_INIT_DATA": "query_id=AAA&hash=secret",
                    "GITHUB_TOKEN": "secret-github-token",
                    "EMAIL_PROBE_TO": "operator@example.test",
                    "LAVATOP_PROBE_EMAIL": "buyer@example.test",
                },
                handoff_path=handoff,
                staged_apps_json=staged,
                ru_origin_json=missing_ru_origin,
                ru_origin_skip_evidence=ru_skip,
                client_build_evidence=client_evidence,
                android_audit_validation=android_validation,
            )

        self.assertFalse(report["ok"])
        self.assertEqual(report["classification"], "BLOCKED_BY_ACCESS")
        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(checks["ru_origin_probe_evidence"]["status"], "BLOCKED_BY_ACCESS")
        self.assertIn("RU_ORIGIN_PUBLIC_CLAIMS_MUST_STATE_UNVERIFIED=true", checks["ru_origin_probe_evidence"]["missing"])

    def test_explicit_unsigned_windows_beta_risk_posture_allows_preflight_when_other_inputs_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            handoff = root / "handoff.md"
            handoff.write_text("GO for public beta publication.\n", encoding="utf-8")
            staged = _write_staged_payload(root / "apps.json")
            ru_origin = _write_ru_payload(root / "ru-origin.json")
            client_evidence = _write_client_build_evidence(root / "client-build.md", authenticode="NotSigned")
            android_validation = _write_android_validation(root / "android-validation.json", ok=False)

            report = self.module.build_report(
                env={
                    "ANDROID_AUDIT_SERIAL": "R58N12345AB",
                    "TELEGRAM_INIT_DATA": "query_id=AAA&hash=secret",
                    "GITHUB_TOKEN": "secret-github-token",
                    "EMAIL_PROBE_TO": "operator@example.test",
                    "LAVATOP_PROBE_EMAIL": "buyer@example.test",
                    "WINDOWS_UNSIGNED_BETA_RISK_ACCEPTED": "true",
                },
                handoff_path=handoff,
                staged_apps_json=staged,
                ru_origin_json=ru_origin,
                client_build_evidence=client_evidence,
                android_audit_validation=android_validation,
            )

        self.assertTrue(report["ok"])
        self.assertTrue(report["ready_to_run_access_gated_smokes"])
        self.assertTrue(report["safe_to_publish_public_beta"])
        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(checks["windows_signing_or_unsigned_risk"]["status"], "PASS")

    def test_retained_unsigned_windows_beta_risk_evidence_allows_preflight_when_other_inputs_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            handoff = root / "handoff.md"
            handoff.write_text("GO for public beta publication.\n", encoding="utf-8")
            staged = _write_staged_payload(root / "apps.json")
            ru_origin = _write_ru_payload(root / "ru-origin.json")
            client_evidence = _write_client_build_evidence(
                root / "client-build.md",
                authenticode="NotSigned",
                unsigned_risk_accepted=True,
            )
            android_validation = _write_android_validation(root / "android-validation.json", ok=False)

            report = self.module.build_report(
                env={
                    "ANDROID_AUDIT_SERIAL": "R58N12345AB",
                    "TELEGRAM_INIT_DATA": "query_id=AAA&hash=secret",
                    "GITHUB_TOKEN": "secret-github-token",
                    "EMAIL_PROBE_TO": "operator@example.test",
                    "LAVATOP_PROBE_EMAIL": "buyer@example.test",
                },
                handoff_path=handoff,
                staged_apps_json=staged,
                ru_origin_json=ru_origin,
                client_build_evidence=client_evidence,
                android_audit_validation=android_validation,
            )

        self.assertTrue(report["ok"])
        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(checks["windows_signing_or_unsigned_risk"]["status"], "PASS")

    def test_pass_android_validation_can_replace_live_serial_for_already_completed_physical_audit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            handoff = root / "handoff.md"
            handoff.write_text("GO for public beta publication.\n", encoding="utf-8")
            staged = _write_staged_payload(root / "apps.json")
            ru_origin = _write_ru_payload(root / "ru-origin.json")
            client_evidence = _write_client_build_evidence(root / "client-build.md")
            android_validation = _write_android_validation(root / "android-validation.json", ok=True)

            report = self.module.build_report(
                env={
                    "TELEGRAM_INIT_DATA": "query_id=AAA&hash=secret",
                    "GITHUB_TOKEN": "secret-github-token",
                    "EMAIL_PROBE_TO": "operator@example.test",
                    "LAVATOP_PROBE_EMAIL": "buyer@example.test",
                },
                handoff_path=handoff,
                staged_apps_json=staged,
                ru_origin_json=ru_origin,
                client_build_evidence=client_evidence,
                android_audit_validation=android_validation,
            )

        self.assertTrue(report["ok"])
        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(checks["android_physical_audit"]["status"], "PASS")
        self.assertEqual(checks["android_physical_audit"]["source"], str(android_validation))

    def test_android_operator_attestation_can_replace_raw_validation_when_claim_guard_is_present(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            handoff = root / "handoff.md"
            handoff.write_text("GO for public beta publication.\n", encoding="utf-8")
            staged = _write_staged_payload(root / "apps.json")
            ru_origin = _write_ru_payload(root / "ru-origin.json")
            client_evidence = _write_client_build_evidence(root / "client-build.md")
            android_validation = _write_android_validation(root / "android-validation.json", ok=False)
            android_operator = _write_android_operator_attestation(root / "android-operator.md")

            report = self.module.build_report(
                env={
                    "TELEGRAM_INIT_DATA": "query_id=AAA&hash=secret",
                    "GITHUB_TOKEN": "secret-github-token",
                    "EMAIL_PROBE_TO": "operator@example.test",
                    "LAVATOP_PROBE_EMAIL": "buyer@example.test",
                },
                handoff_path=handoff,
                staged_apps_json=staged,
                ru_origin_json=ru_origin,
                client_build_evidence=client_evidence,
                android_audit_validation=android_validation,
                android_operator_attestation=android_operator,
            )

        self.assertTrue(report["ok"])
        self.assertEqual(report["classification"], "PASS_WITH_ACCEPTED_SKIPS")
        self.assertEqual(report["accepted_operator_attestations"], ["android_physical_audit"])
        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(checks["android_physical_audit"]["status"], "OPERATOR_ATTESTED")
        self.assertEqual(checks["android_physical_audit"]["source"], str(android_operator))

    def test_android_operator_attestation_without_claim_guard_is_not_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            handoff = root / "handoff.md"
            handoff.write_text("GO for public beta publication.\n", encoding="utf-8")
            staged = _write_staged_payload(root / "apps.json")
            ru_origin = _write_ru_payload(root / "ru-origin.json")
            client_evidence = _write_client_build_evidence(root / "client-build.md")
            android_validation = _write_android_validation(root / "android-validation.json", ok=False)
            android_operator = _write_android_operator_attestation(root / "android-operator.md", include_claim_guard=False)

            report = self.module.build_report(
                env={
                    "TELEGRAM_INIT_DATA": "query_id=AAA&hash=secret",
                    "GITHUB_TOKEN": "secret-github-token",
                    "EMAIL_PROBE_TO": "operator@example.test",
                    "LAVATOP_PROBE_EMAIL": "buyer@example.test",
                },
                handoff_path=handoff,
                staged_apps_json=staged,
                ru_origin_json=ru_origin,
                client_build_evidence=client_evidence,
                android_audit_validation=android_validation,
                android_operator_attestation=android_operator,
            )

        self.assertFalse(report["ok"])
        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(checks["android_physical_audit"]["status"], "BLOCKED_BY_ACCESS")
        self.assertIn(
            "ANDROID_PHYSICAL_AUDIT_PUBLIC_CLAIMS_MUST_STATE_OPERATOR_ATTESTED=true",
            checks["android_physical_audit"]["missing"],
        )


if __name__ == "__main__":
    unittest.main()
