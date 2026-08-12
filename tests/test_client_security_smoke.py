import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


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

    def test_client_root_resolver_selects_the_main_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace_root = Path(tmp)
            platform_root = workspace_root / "VPN"
            client_repo = workspace_root / "POKROV-app"
            main_worktree = client_repo / ".worktrees" / "final-client-integration"
            (client_repo / ".git").mkdir(parents=True)
            git_results = (
                subprocess.CompletedProcess(args=[], returncode=0, stdout=f"{platform_root / '.git'}\n"),
                subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout=(
                        f"worktree {client_repo}\n"
                        "branch refs/heads/codex/client-work\n\n"
                        f"worktree {main_worktree}\n"
                        "branch refs/heads/main\n"
                    ),
                ),
            )
            with patch.dict(self.module.os.environ, {"POKROV_APP_ROOT": ""}, clear=False):
                with patch.object(self.module.subprocess, "run", side_effect=git_results):
                    resolved = self.module._resolve_client_root(platform_root / ".worktrees" / "integration")

        self.assertEqual(resolved, main_worktree.resolve())

    def test_product_contract_fails_when_public_scope_or_free_tier_drift(self) -> None:
        contract = {
            "brand": "POKROV",
            "client_strategy": "consumer-first",
            "identity_model": "app-first",
            "default_runtime_core": "sing-box",
            "advanced_fallback_core": "xray",
            "trial_days": 5,
            "telegram_bonus_days": 5,
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
        self.assertIn("product contract must keep free_tier disabled", failures)
        self.assertIn("product contract must mark free_tier retired_pending_replacement", failures)
        self.assertIn("product contract must not publish a free_tier node_pool", failures)
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
                "enabled": False,
                "status": "retired_pending_replacement",
                "node_pool": None,
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
            "core": {
                "repository": "other/repo",
                "release_tag": "v9.9.9",
                "source_commit": "wrong",
                "activation_state": "inactive",
                "artifact_provenance": {},
                "desktop_abi": {},
                "assets": {
                    "android": {
                        "entry": "wrong.aar",
                        "size": 1,
                        "sha256": "wrong",
                        "sync_destination": "apps/android_shell/wrong",
                    },
                    "windows": {
                        "entry": "wrong.dll",
                        "size": 1,
                        "sha256": "wrong",
                        "helper": "HiddifyCli.exe",
                        "sync_destination": "apps/windows_shell/wrong",
                    },
                },
            }
        }

        failures = self.module._runtime_artifact_failures(runtime_artifacts)

        self.assertIn("runtime artifacts must stay pinned to Kiwunaka/POKROV-core", failures)
        self.assertIn("runtime artifacts must stay pinned to POKROV Core v1.0.2", failures)
        self.assertIn("runtime artifacts must not declare a Windows helper binary", failures)
        self.assertIn("runtime artifacts must pin the reviewed Android POKROV Core AAR", failures)

    def test_runtime_artifacts_accept_reviewed_pokrov_core_contract(self) -> None:
        runtime_artifacts = {
            "core": {
                "repository": self.module.POKROV_CORE_REPOSITORY,
                "release_tag": self.module.POKROV_CORE_RELEASE_TAG,
                "source_commit": self.module.POKROV_CORE_SOURCE_COMMIT,
                "activation_state": "active",
                "artifact_provenance": {
                    "status": "clean_reproducible_release",
                    "vcs_stamp": "disabled_for_reproducible_release_artifacts",
                    "source_identity": "annotated_release_tag_and_github_release_commit",
                    "release_url": self.module.POKROV_CORE_RELEASE_URL,
                    "reproducible_build": {
                        "android": {
                            "size": self.module.ANDROID_CORE_SIZE,
                            "sha256": self.module.ANDROID_CORE_SHA256,
                        },
                        "windows": {
                            "size": self.module.WINDOWS_CORE_SIZE,
                            "sha256": self.module.WINDOWS_CORE_SHA256,
                        },
                        "libcronet_sha256": self.module.WINDOWS_CRONET_SHA256,
                    },
                    "promotion_rule": "accept_exact_v1.0.2_release_artifacts",
                },
                "desktop_abi": {
                    "name": "pokrov-core",
                    "version": 2,
                    "required_symbol": "pokrovCoreAbiVersion",
                    "secure_file_symbol": "pokrovSecureFile",
                },
                "assets": {
                    "android": {
                        "entry": "pokrov-core.aar",
                        "size": self.module.ANDROID_CORE_SIZE,
                        "sha256": self.module.ANDROID_CORE_SHA256,
                        "sync_destination": "apps/android_shell/android/app/libs",
                    },
                    "windows": {
                        "entry": "pokrov-core.dll",
                        "size": self.module.WINDOWS_CORE_SIZE,
                        "sha256": self.module.WINDOWS_CORE_SHA256,
                        "sync_destination": "apps/windows_shell/windows/runner/resources/runtime",
                        "runtime_dependencies": ["libcronet.dll"],
                        "runtime_dependency_size": {
                            "libcronet.dll": self.module.WINDOWS_CRONET_SIZE,
                        },
                        "runtime_dependency_sha256": {
                            "libcronet.dll": self.module.WINDOWS_CRONET_SHA256,
                        },
                    },
                },
            }
        }

        failures = self.module._runtime_artifact_failures(runtime_artifacts)

        self.assertEqual(failures, [])

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
  packaging {
    jniLibs {
      keepDebugSymbols += ["**/libpokrov-core.so"]
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
