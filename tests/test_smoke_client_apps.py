import importlib.util
import sys
import unittest
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "smoke_client_apps.py"
    spec = importlib.util.spec_from_file_location("smoke_client_apps", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SmokeClientAppsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_release_handoff_failures_require_android_windows_and_docs(self) -> None:
        payload = {
            "android": {"play_url": "", "apk_url": "", "mirror_url": ""},
            "windows": {"exe_url": "", "mirror_url": ""},
            "docs_url": "",
        }

        failures = self.module._release_handoff_failures(payload)

        self.assertIn("android release URL is missing", failures)
        self.assertIn("windows release URL is missing", failures)
        self.assertIn("docs_url is missing", failures)

    def test_release_handoff_failures_accept_primary_release_urls(self) -> None:
        payload = {
            "android": {
                "play_url": "",
                "apk_url": "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.apk",
                "mirror_url": "",
            },
            "windows": {
                "exe_url": "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.exe",
                "mirror_url": "",
            },
            "docs_url": "https://pokrov.space/install/",
        }

        failures = self.module._release_handoff_failures(payload)

        self.assertEqual(failures, [])

    def test_load_apps_json_accepts_staged_payload(self) -> None:
        payload_path = Path(self.id().replace(".", "_") + ".json")
        try:
            payload_path.write_text(
                """
{
  "android": {"play_url": "", "apk_url": "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.apk"},
  "windows": {"exe_url": "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.exe"},
  "docs_url": "https://pokrov.space/install/"
}
""".strip(),
                encoding="utf-8",
            )

            payload = self.module._load_apps_json(str(payload_path))
        finally:
            payload_path.unlink(missing_ok=True)

        self.assertEqual(payload["android"]["play_url"], "")
        self.assertEqual(self.module._release_handoff_failures(payload), [])

    def test_load_apps_json_accepts_client_release_handoff_payload(self) -> None:
        payload_path = Path(self.id().replace(".", "_") + ".json")
        try:
            payload_path.write_text(
                """
{
  "downloads": {
    "android": {"play_url": "", "apk_url": "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.apk"},
    "windows": {"exe_url": "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.exe"},
    "docs_url": "https://pokrov.space/install/"
  },
  "runtime_env": {
    "APP_ANDROID_PLAY_URL": "",
    "APP_ANDROID_APK_URL": "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.apk",
    "APP_ANDROID_MIRROR_URL": "",
    "APP_WINDOWS_EXE_URL": "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.exe",
    "APP_WINDOWS_MIRROR_URL": "",
    "APP_DOCS_URL": "https://pokrov.space/install/"
  }
}
""".strip(),
                encoding="utf-8",
            )

            payload = self.module._load_apps_json(str(payload_path))
        finally:
            payload_path.unlink(missing_ok=True)

        self.assertEqual(payload["android"]["apk_url"], "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.apk")
        self.assertEqual(payload["windows"]["exe_url"], "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.exe")
        self.assertEqual(self.module._release_handoff_failures(payload), [])

    def test_load_apps_json_rejects_non_object_payload(self) -> None:
        payload_path = Path(self.id().replace(".", "_") + ".json")
        try:
            payload_path.write_text("[]", encoding="utf-8")

            with self.assertRaises(ValueError):
                self.module._load_apps_json(str(payload_path))
        finally:
            payload_path.unlink(missing_ok=True)

    def test_policy_only_mode_skips_network_url_probes(self) -> None:
        payload_path = Path(self.id().replace(".", "_") + ".json")
        original_argv = sys.argv[:]
        original_probe = self.module._probe_artifact
        try:
            payload_path.write_text(
                """
{
  "android": {"play_url": "", "apk_url": "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.apk"},
  "windows": {"exe_url": "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.exe"},
  "docs_url": "https://pokrov.space/install/"
}
""".strip(),
                encoding="utf-8",
            )

            def _fail_probe(*_args, **_kwargs):
                raise AssertionError("policy-only mode must not probe staged URLs")

            self.module._probe_artifact = _fail_probe
            sys.argv = [
                "smoke_client_apps.py",
                "--apps-json",
                str(payload_path),
                "--require-release-handoff",
                "--policy-only",
            ]

            self.assertEqual(self.module.main(), 0)
        finally:
            self.module._probe_artifact = original_probe
            sys.argv = original_argv
            payload_path.unlink(missing_ok=True)

    def test_release_handoff_failures_reject_play_only_outside_store_beta(self) -> None:
        payload = {
            "android": {"play_url": "https://play.google.com/store/apps/details?id=space.pokrov.app", "apk_url": "", "mirror_url": ""},
            "windows": {
                "exe_url": "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.exe",
                "mirror_url": "",
            },
            "docs_url": "https://pokrov.space/install/",
        }

        failures = self.module._release_handoff_failures(payload)

        self.assertIn("android Play URL must be empty for outside-store public beta", failures)
        self.assertIn("android release URL is missing", failures)

    def test_release_handoff_failures_reject_non_github_or_wrong_role_urls(self) -> None:
        payload = {
            "android": {"play_url": "", "apk_url": "https://downloads.example.com/pokrov.apk", "mirror_url": ""},
            "windows": {"exe_url": "https://connect.pokrov.space/pokrov.exe", "mirror_url": ""},
            "docs_url": "https://pay.pokrov.space/checkout/",
        }

        failures = self.module._release_handoff_failures(payload)
        joined = "\n".join(failures)

        self.assertIn("android.apk_url must point to a GitHub Releases .apk artifact", joined)
        self.assertIn("windows.exe_url must point to a GitHub Releases .exe artifact", joined)
        self.assertIn("docs_url must point to https://pokrov.space/install/", joined)

    def test_release_handoff_failures_reject_wrong_artifact_extensions(self) -> None:
        payload = {
            "android": {
                "play_url": "",
                "apk_url": "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.zip",
                "mirror_url": "",
            },
            "windows": {
                "exe_url": "https://github.com/pokrov-space/pokrov-app/releases/download/v0.3.0/pokrov.msix",
                "mirror_url": "",
            },
            "docs_url": "https://pokrov.space/install/",
        }

        failures = self.module._release_handoff_failures(payload)
        joined = "\n".join(failures)

        self.assertIn("android.apk_url must point to a GitHub Releases .apk artifact", joined)
        self.assertIn("windows.exe_url must point to a GitHub Releases .exe artifact", joined)

    def test_provider_readiness_accepts_blocked_checkout_with_reasons(self) -> None:
        failures = self.module._provider_readiness_failures(
            {
                "ok": False,
                "blocked": True,
                "providers": [],
                "blocked_reasons": ["paid_checkout_launch_evidence_not_green"],
            }
        )
        self.assertEqual(failures, [])

    def test_provider_readiness_rejects_blocked_catalog_with_visible_providers(self) -> None:
        failures = self.module._provider_readiness_failures(
            {
                "ok": False,
                "blocked": True,
                "providers": [{"code": "lavatop", "label": "Lava.top"}],
                "blocked_reasons": ["paid_checkout_launch_evidence_not_green"],
            }
        )
        self.assertEqual(failures, ["blocked RUB payment provider catalog must not expose providers"])

    def test_provider_readiness_rejects_blocked_catalog_without_reasons(self) -> None:
        failures = self.module._provider_readiness_failures(
            {
                "ok": False,
                "blocked": True,
                "providers": [],
                "blocked_reasons": [],
            }
        )
        self.assertEqual(failures, ["blocked RUB payment provider catalog must include blocked_reasons"])

    def test_provider_readiness_requires_at_least_one_enabled_provider_when_unblocked(self) -> None:
        failures = self.module._provider_readiness_failures({"providers": []})
        self.assertEqual(failures, ["no enabled RUB payment providers"])

    def test_provider_readiness_accepts_lavatop_only_when_unblocked(self) -> None:
        failures = self.module._provider_readiness_failures(
            {
                "ok": True,
                "blocked": False,
                "providers": [
                    {"code": "lavatop", "label": "Lava.top", "enabled": True},
                ],
            }
        )
        self.assertEqual(failures, [])

    def test_provider_readiness_rejects_non_lavatop_unblocked_catalog(self) -> None:
        failures = self.module._provider_readiness_failures(
            {
                "ok": True,
                "blocked": False,
                "providers": [
                    {"code": "cardlink", "label": "Cardlink", "enabled": True},
                ]
            }
        )
        self.assertEqual(failures, ["public beta paid checkout must expose only Lava.top; got cardlink"])

    def test_provider_readiness_rejects_disabled_non_lavatop_unblocked_catalog(self) -> None:
        failures = self.module._provider_readiness_failures(
            {
                "ok": True,
                "blocked": False,
                "providers": [
                    {"code": "lavatop", "label": "Lava.top", "enabled": True},
                    {"code": "freekassa", "label": "FreeKassa", "enabled": False},
                ],
            }
        )
        self.assertEqual(failures, ["public beta paid checkout must expose only Lava.top; got lavatop, freekassa"])

    def test_provider_readiness_rejects_disabled_lavatop_when_unblocked(self) -> None:
        failures = self.module._provider_readiness_failures(
            {
                "ok": True,
                "blocked": False,
                "providers": [
                    {"code": "lavatop", "label": "Lava.top", "enabled": False},
                ],
            }
        )
        self.assertEqual(failures, ["public beta Lava.top provider must be enabled"])


if __name__ == "__main__":
    unittest.main()
