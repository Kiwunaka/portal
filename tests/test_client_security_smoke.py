import importlib.util
import sys
import unittest
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "client_security_smoke.py"
    spec = importlib.util.spec_from_file_location("client_security_smoke", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ClientSecuritySmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_product_contract_fails_when_public_scope_or_free_tier_drift(self) -> None:
        contract = {
            "brand": "POKROV",
            "client_strategy": "consumer-first",
            "identity_model": "app-first",
            "default_runtime_core": "sing-box",
            "advanced_fallback_core": "xray",
            "trial_days": 5,
            "telegram_bonus_days": 10,
            "public_scope": ["android", "windows", "ios"],
            "readiness_only_scope": ["macos"],
            "free_tier": {
                "node_pool": "pl-paid",
                "traffic_gb": 10,
                "speed_mbps": 100,
            },
            "monetization": {
                "in_app_purchases": True,
                "third_party_ads": True,
                "first_party_promos_only": False,
            },
            "public_routing_modes": ["full_tunnel"],
        }

        failures = self.module._product_contract_failures(contract)

        self.assertIn("product contract must keep public_scope limited to android and windows", failures)
        self.assertIn("product contract must keep readiness_only_scope limited to ios and macos", failures)
        self.assertIn("product contract must keep free_tier.node_pool as NL-free", failures)
        self.assertIn("product contract must keep monetization.in_app_purchases disabled", failures)
        self.assertIn(
            "product contract must keep public_routing_modes as all_except_ru, full_tunnel, selected_apps",
            failures,
        )

    def test_runtime_profile_accepts_canonical_pokrov_hosts(self) -> None:
        runtime_profile = {
            "brand": "POKROV",
            "default_runtime_core": "sing-box",
            "advanced_fallback_core": "xray",
            "free_tier": {
                "node_pool": "NL-free",
                "traffic_gb": 5,
                "speed_mbps": 50,
            },
            "official_surfaces": {
                "checkout": "https://pay.pokrov.space/checkout/",
                "api": "https://api.pokrov.space/",
                "connect": "https://connect.pokrov.space/",
            },
        }

        failures = self.module._runtime_profile_failures(runtime_profile)

        self.assertEqual(failures, [])

    def test_runtime_artifacts_fail_when_windows_helper_or_wrong_pin_is_declared(self) -> None:
        runtime_artifacts = {
            "libcore": {
                "repository": "other/repo",
                "release_tag": "v9.9.9",
                "assets": {
                    "android": {
                        "entry": "wrong.aar",
                        "sync_destination": "apps/android_shell/wrong",
                    },
                    "windows": {
                        "entry": "wrong.dll",
                        "helper": "HiddifyCli.exe",
                        "sync_destination": "apps/windows_shell/wrong",
                    },
                },
            }
        }

        failures = self.module._runtime_artifact_failures(runtime_artifacts)

        self.assertIn("runtime artifacts must stay pinned to hiddify/hiddify-core", failures)
        self.assertIn("runtime artifacts must stay pinned to libcore release v3.1.8", failures)
        self.assertIn("runtime artifacts must not declare a Windows helper binary", failures)
        self.assertIn("runtime artifacts must keep the Android libcore entry on libcore.aar", failures)

    def test_android_host_accepts_non_exported_special_use_vpn_service(self) -> None:
        manifest_text = """
<application android:label="POKROV">
  <service
      android:name=".PokrovRuntimeVpnService"
      android:exported="false"
      android:foregroundServiceType="specialUse"
      android:permission="android.permission.BIND_VPN_SERVICE" />
</application>
<uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE" />
"""
        build_gradle_text = """
android {
  namespace = "space.pokrov.pokrov_android_shell"
  defaultConfig {
    applicationId = "space.pokrov.pokrov_android_shell"
  }
  buildTypes {
    release {
      signingConfig = signingConfigs.debug
    }
  }
}
"""

        failures = self.module._android_host_failures(
            manifest_text=manifest_text,
            build_gradle_text=build_gradle_text,
        )

        self.assertEqual(failures, [])

    def test_windows_release_seed_fails_when_bridge_contract_leaks_back_in(self) -> None:
        windows_release = {
            "display_name": "POKROV VPN",
            "binary_name": "pokrov.exe",
            "bundle_root": "external/client-fork/app/build/windows",
            "artifact_root": "external/client-fork/app/out",
            "required_files": ["pokrov.exe"],
            "metadata": {
                "company_name": "POKROV VPN",
                "file_description": "POKROV VPN",
                "product_name": "POKROV VPN",
            },
            "runtime": {
                "platform": "windows",
                "artifact_directory": "external/client-fork/app/out",
                "core_binary": "other.dll",
                "helper_binary": "HiddifyCli.exe",
            },
        }

        failures = self.module._windows_release_failures(windows_release)

        self.assertIn("Windows release seed must keep display_name as POKROV", failures)
        self.assertIn("Windows release seed must keep binary_name as pokrov_windows_beta.exe", failures)
        self.assertIn("Windows release seed must keep artifact_root on apps/windows_shell/build/release_bundle", failures)
        self.assertIn("Windows release seed must not declare a Windows helper binary", failures)


if __name__ == "__main__":
    unittest.main()
