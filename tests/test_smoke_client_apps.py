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
            "android": {"play_url": "", "apk_url": "https://downloads.example.com/pokrov-vpn-android.apk", "mirror_url": ""},
            "windows": {"exe_url": "https://downloads.example.com/pokrov-vpn-windows.exe", "mirror_url": ""},
            "docs_url": "https://pokrov.space/install/",
        }

        failures = self.module._release_handoff_failures(payload)

        self.assertEqual(failures, [])

    def test_provider_readiness_requires_at_least_one_enabled_provider(self) -> None:
        failures = self.module._provider_readiness_failures({"providers": []})
        self.assertEqual(failures, ["no enabled RUB payment providers"])

    def test_provider_readiness_accepts_configured_provider_catalog(self) -> None:
        failures = self.module._provider_readiness_failures(
            {
                "providers": [
                    {"code": "cardlink", "label": "Cardlink", "enabled": True},
                ]
            }
        )
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
