from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CLIENT_ROOT = Path("C:/Users/kiwun/Documents/ai/POKROV-app")
CLIENT_ROOT = Path(os.getenv("POKROV_APP_ROOT", str(DEFAULT_CLIENT_ROOT)))

PRODUCT_CONTRACT_PATH = CLIENT_ROOT / "config" / "product-contract.seed.json"
RUNTIME_PROFILE_PATH = CLIENT_ROOT / "config" / "runtime-profile.seed.json"
RUNTIME_ARTIFACTS_PATH = CLIENT_ROOT / "config" / "runtime-artifacts.seed.json"
WINDOWS_RELEASE_CONFIG_PATH = CLIENT_ROOT / "config" / "windows-release.seed.json"
ANDROID_MANIFEST_PATH = CLIENT_ROOT / "apps" / "android_shell" / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
ANDROID_BUILD_GRADLE_PATH = CLIENT_ROOT / "apps" / "android_shell" / "android" / "app" / "build.gradle"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(_read_text(path))


def _product_contract_failures(contract: dict[str, object]) -> list[str]:
    failures: list[str] = []

    if contract.get("brand") != "POKROV":
        failures.append("product contract must keep brand as POKROV")
    if contract.get("client_strategy") != "consumer-first":
        failures.append("product contract must keep client_strategy as consumer-first")
    if contract.get("identity_model") != "app-first":
        failures.append("product contract must keep identity_model as app-first")
    if contract.get("default_runtime_core") != "sing-box":
        failures.append("product contract must keep default_runtime_core as sing-box")
    if contract.get("advanced_fallback_core") != "xray":
        failures.append("product contract must keep advanced_fallback_core as xray")
    if int(contract.get("trial_days", 0)) != 5:
        failures.append("product contract must keep the trial at 5 days")
    if int(contract.get("telegram_bonus_days", 0)) != 10:
        failures.append("product contract must keep the Telegram bonus at 10 days")

    public_scope = list(contract.get("public_scope") or [])
    if public_scope != ["android", "windows"]:
        failures.append("product contract must keep public_scope limited to android and windows")

    readiness_only_scope = list(contract.get("readiness_only_scope") or [])
    if readiness_only_scope != ["ios", "macos"]:
        failures.append("product contract must keep readiness_only_scope limited to ios and macos")

    free_tier = dict(contract.get("free_tier") or {})
    if free_tier.get("node_pool") != "NL-free":
        failures.append("product contract must keep free_tier.node_pool as NL-free")
    if int(free_tier.get("traffic_gb", 0)) != 5:
        failures.append("product contract must keep free_tier.traffic_gb at 5")
    if int(free_tier.get("speed_mbps", 0)) != 50:
        failures.append("product contract must keep free_tier.speed_mbps at 50")

    monetization = dict(contract.get("monetization") or {})
    if monetization.get("in_app_purchases") is not False:
        failures.append("product contract must keep monetization.in_app_purchases disabled")
    if monetization.get("third_party_ads") is not False:
        failures.append("product contract must keep monetization.third_party_ads disabled")
    if monetization.get("first_party_promos_only") is not True:
        failures.append("product contract must keep monetization.first_party_promos_only enabled")

    public_routing_modes = list(contract.get("public_routing_modes") or [])
    if public_routing_modes != ["all_except_ru", "full_tunnel", "selected_apps"]:
        failures.append(
            "product contract must keep public_routing_modes as all_except_ru, full_tunnel, selected_apps"
        )

    return failures


def _runtime_profile_failures(runtime_profile: dict[str, object]) -> list[str]:
    failures: list[str] = []

    if runtime_profile.get("brand") != "POKROV":
        failures.append("runtime profile must keep brand as POKROV")
    if runtime_profile.get("default_runtime_core") != "sing-box":
        failures.append("runtime profile must keep default_runtime_core as sing-box")
    if runtime_profile.get("advanced_fallback_core") != "xray":
        failures.append("runtime profile must keep advanced_fallback_core as xray")

    free_tier = dict(runtime_profile.get("free_tier") or {})
    if free_tier.get("node_pool") != "NL-free":
        failures.append("runtime profile must keep free_tier.node_pool as NL-free")
    if int(free_tier.get("traffic_gb", 0)) != 5:
        failures.append("runtime profile must keep free_tier.traffic_gb at 5")
    if int(free_tier.get("speed_mbps", 0)) != 50:
        failures.append("runtime profile must keep free_tier.speed_mbps at 50")

    official_surfaces = dict(runtime_profile.get("official_surfaces") or {})
    if official_surfaces.get("checkout") != "https://pay.pokrov.space/checkout/":
        failures.append("runtime profile must keep checkout on https://pay.pokrov.space/checkout/")
    if official_surfaces.get("api") != "https://api.pokrov.space/":
        failures.append("runtime profile must keep api on https://api.pokrov.space/")
    if official_surfaces.get("connect") != "https://connect.pokrov.space/":
        failures.append("runtime profile must keep connect on https://connect.pokrov.space/")

    return failures


def _runtime_artifact_failures(runtime_artifacts: dict[str, object]) -> list[str]:
    failures: list[str] = []

    libcore = dict(runtime_artifacts.get("libcore") or {})
    if libcore.get("repository") != "hiddify/hiddify-core":
        failures.append("runtime artifacts must stay pinned to hiddify/hiddify-core")
    if libcore.get("release_tag") != "v3.1.8":
        failures.append("runtime artifacts must stay pinned to libcore release v3.1.8")

    assets = dict(libcore.get("assets") or {})
    windows = dict(assets.get("windows") or {})
    if windows.get("entry") != "libcore.dll":
        failures.append("runtime artifacts must keep the Windows libcore entry on libcore.dll")
    if "helper" in windows:
        failures.append("runtime artifacts must not declare a Windows helper binary")
    if windows.get("sync_destination") != "apps/windows_shell/windows/runner/resources/runtime":
        failures.append(
            "runtime artifacts must sync the Windows libcore payload into apps/windows_shell/windows/runner/resources/runtime"
        )

    android = dict(assets.get("android") or {})
    if android.get("entry") != "libcore.aar":
        failures.append("runtime artifacts must keep the Android libcore entry on libcore.aar")
    if android.get("sync_destination") != "apps/android_shell/android/app/libs":
        failures.append("runtime artifacts must sync the Android libcore payload into apps/android_shell/android/app/libs")

    return failures


def _android_host_failures(*, manifest_text: str, build_gradle_text: str) -> list[str]:
    failures: list[str] = []

    if 'android:label="POKROV"' not in manifest_text:
        failures.append("Android launcher label must be POKROV")
    if 'android:name=".PokrovRuntimeVpnService"' not in manifest_text:
        failures.append("Android manifest must declare PokrovRuntimeVpnService")
    if 'android:exported="false"' not in manifest_text:
        failures.append("Android VPN service must stay non-exported")
    if 'android:permission="android.permission.BIND_VPN_SERVICE"' not in manifest_text:
        failures.append("Android VPN service must require android.permission.BIND_VPN_SERVICE")
    if "android.permission.FOREGROUND_SERVICE_SPECIAL_USE" not in manifest_text:
        failures.append("Android manifest must keep the special-use foreground-service permission")
    if 'android:foregroundServiceType="specialUse"' not in manifest_text:
        failures.append("Android VPN service must keep foregroundServiceType as specialUse")

    if re.search(r'applicationId\s*=\s*"space\.pokrov\.pokrov_android_shell"', build_gradle_text) is None:
        failures.append("Android build.gradle must keep applicationId on space.pokrov.pokrov_android_shell")
    if re.search(r'namespace\s*=\s*"space\.pokrov\.pokrov_android_shell"', build_gradle_text) is None:
        failures.append("Android build.gradle must keep namespace on space.pokrov.pokrov_android_shell")
    if 'signingConfig = signingConfigs.debug' not in build_gradle_text:
        failures.append("Android release build.gradle must still make the debug-signing alpha state explicit")

    return failures


def _windows_release_failures(windows_release: dict[str, object]) -> list[str]:
    failures: list[str] = []

    if windows_release.get("display_name") != "POKROV":
        failures.append("Windows release seed must keep display_name as POKROV")
    if windows_release.get("binary_name") != "pokrov_windows_beta.exe":
        failures.append("Windows release seed must keep binary_name as pokrov_windows_beta.exe")
    if windows_release.get("bundle_root") != "apps/windows_shell/build/windows/x64/runner/Release":
        failures.append("Windows release seed must keep bundle_root on apps/windows_shell/build/windows/x64/runner/Release")
    if windows_release.get("artifact_root") != "apps/windows_shell/build/release_bundle":
        failures.append("Windows release seed must keep artifact_root on apps/windows_shell/build/release_bundle")

    required_files = list(windows_release.get("required_files") or [])
    for required_path in (
        "pokrov_windows_beta.exe",
        "flutter_windows.dll",
        "libcore.dll",
        "data/app.so",
        "data/icudtl.dat",
    ):
        if required_path not in required_files:
            failures.append(f"Windows release seed must include required file {required_path}")

    metadata = dict(windows_release.get("metadata") or {})
    if metadata.get("file_description") != "POKROV":
        failures.append("Windows release seed must keep metadata.file_description as POKROV")
    if metadata.get("product_name") != "POKROV":
        failures.append("Windows release seed must keep metadata.product_name as POKROV")
    if metadata.get("company_name") != "space.pokrov":
        failures.append("Windows release seed must keep metadata.company_name as space.pokrov")

    runtime = dict(windows_release.get("runtime") or {})
    if runtime.get("platform") != "windows":
        failures.append("Windows release seed must keep runtime.platform as windows")
    if runtime.get("artifact_directory") != "apps/windows_shell/windows/runner/resources/runtime":
        failures.append(
            "Windows release seed must keep runtime.artifact_directory on apps/windows_shell/windows/runner/resources/runtime"
        )
    if runtime.get("core_binary") != "libcore.dll":
        failures.append("Windows release seed must keep runtime.core_binary as libcore.dll")
    if "helper_binary" in runtime:
        failures.append("Windows release seed must not declare a Windows helper binary")

    return failures


def _check_required_files() -> list[str]:
    missing: list[str] = []
    for path in (
        PRODUCT_CONTRACT_PATH,
        RUNTIME_PROFILE_PATH,
        RUNTIME_ARTIFACTS_PATH,
        WINDOWS_RELEASE_CONFIG_PATH,
        ANDROID_MANIFEST_PATH,
        ANDROID_BUILD_GRADLE_PATH,
    ):
        if not path.exists():
            missing.append(f"required client file is missing: {path}")
    return missing


def main() -> int:
    failures = _check_required_files()
    if failures:
        for failure in failures:
            print(f"[fail] {failure}")
        return 2

    product_contract = _read_json(PRODUCT_CONTRACT_PATH)
    runtime_profile = _read_json(RUNTIME_PROFILE_PATH)
    runtime_artifacts = _read_json(RUNTIME_ARTIFACTS_PATH)
    windows_release = _read_json(WINDOWS_RELEASE_CONFIG_PATH)
    manifest_text = _read_text(ANDROID_MANIFEST_PATH)
    build_gradle_text = _read_text(ANDROID_BUILD_GRADLE_PATH)

    failures.extend(_product_contract_failures(product_contract))
    failures.extend(_runtime_profile_failures(runtime_profile))
    failures.extend(_runtime_artifact_failures(runtime_artifacts))
    failures.extend(
        _android_host_failures(
            manifest_text=manifest_text,
            build_gradle_text=build_gradle_text,
        )
    )
    failures.extend(_windows_release_failures(windows_release))

    print(f"[check] product contract: {PRODUCT_CONTRACT_PATH}")
    print(f"[check] runtime profile: {RUNTIME_PROFILE_PATH}")
    print(f"[check] runtime artifacts: {RUNTIME_ARTIFACTS_PATH}")
    print(f"[check] Android manifest: {ANDROID_MANIFEST_PATH}")
    print(f"[check] Android build.gradle: {ANDROID_BUILD_GRADLE_PATH}")
    print(f"[check] Windows release seed: {WINDOWS_RELEASE_CONFIG_PATH}")

    if failures:
        for failure in failures:
            print(f"[fail] {failure}")
        return 2

    print("[pass] client security smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
