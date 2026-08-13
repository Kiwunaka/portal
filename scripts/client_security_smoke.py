from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _resolve_client_root(platform_checkout: Path) -> Path:
    override = os.getenv("POKROV_APP_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()

    common_dir = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=platform_checkout,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    client_repo = Path(common_dir).resolve().parent.parent / "POKROV-app"
    if not (client_repo / ".git").exists():
        return client_repo

    worktrees = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=client_repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    for block in worktrees.strip().split("\n\n"):
        fields = dict(line.split(" ", 1) for line in block.splitlines() if " " in line)
        if fields.get("branch") == "refs/heads/main" and fields.get("worktree"):
            return Path(fields["worktree"]).resolve()
    return client_repo


CLIENT_ROOT = _resolve_client_root(REPO_ROOT)

PRODUCT_CONTRACT_PATH = CLIENT_ROOT / "config" / "product-contract.seed.json"
RUNTIME_PROFILE_PATH = CLIENT_ROOT / "config" / "runtime-profile.seed.json"
RUNTIME_ARTIFACTS_PATH = CLIENT_ROOT / "config" / "runtime-artifacts.seed.json"
WINDOWS_RELEASE_CONFIG_PATH = CLIENT_ROOT / "config" / "windows-release.seed.json"
ANDROID_MANIFEST_PATH = CLIENT_ROOT / "apps" / "android_shell" / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
ANDROID_BUILD_GRADLE_PATH = CLIENT_ROOT / "apps" / "android_shell" / "android" / "app" / "build.gradle"
ANDROID_CORE_PATH = CLIENT_ROOT / "apps" / "android_shell" / "android" / "app" / "libs" / "pokrov-core.aar"
WINDOWS_RUNTIME_ROOT = CLIENT_ROOT / "apps" / "windows_shell" / "windows" / "runner" / "resources" / "runtime"
WINDOWS_CORE_PATH = WINDOWS_RUNTIME_ROOT / "pokrov-core.dll"
WINDOWS_CRONET_PATH = WINDOWS_RUNTIME_ROOT / "libcronet.dll"

POKROV_CORE_REPOSITORY = "Kiwunaka/POKROV-core"
POKROV_CORE_RELEASE_TAG = "v1.0.3"
POKROV_CORE_RELEASE_URL = "https://github.com/Kiwunaka/pokrov-core/releases/tag/v1.0.3"
POKROV_CORE_SOURCE_COMMIT = "69a74545101708e56183c92e31f2b4c7b2509884"
ANDROID_CORE_SIZE = 106861671
ANDROID_CORE_SHA256 = "6e6f3b688fe415c9392e19aa4f8660885316897cfc369cf8c3ff3d01100ee14f"
WINDOWS_CORE_SIZE = 55134208
WINDOWS_CORE_SHA256 = "7cc83854fc4022b759e9de3d0942b90a24c859cfd51e3231d04e7c7a6b7d5054"
WINDOWS_CRONET_SIZE = 8596992
WINDOWS_CRONET_SHA256 = "8ef1f8bbde77f954af1ae47bee1819ac8dc2354bb0e1d4baba3dad9e58d7a6f7"


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
    if int(contract.get("telegram_bonus_days", 0)) != 5:
        failures.append("product contract must keep the Telegram bonus at 5 days")

    public_scope = list(contract.get("public_scope") or [])
    if public_scope != ["android", "windows"]:
        failures.append("product contract must keep public_scope limited to android and windows")

    readiness_only_scope = list(contract.get("readiness_only_scope") or [])
    if readiness_only_scope != ["ios", "macos"]:
        failures.append("product contract must keep readiness_only_scope limited to ios and macos")

    free_tier = dict(contract.get("free_tier") or {})
    if free_tier.get("enabled") is not False:
        failures.append("product contract must keep free_tier disabled")
    if free_tier.get("status") != "retired_pending_replacement":
        failures.append("product contract must mark free_tier retired_pending_replacement")
    if free_tier.get("node_pool") is not None:
        failures.append("product contract must not publish a free_tier node_pool")

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
    if free_tier.get("enabled") is not False:
        failures.append("runtime profile must keep free_tier disabled")
    if free_tier.get("status") != "retired_pending_replacement":
        failures.append("runtime profile must mark free_tier retired_pending_replacement")
    if free_tier.get("node_pool") is not None:
        failures.append("runtime profile must not publish a free_tier node_pool")

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

    core = dict(runtime_artifacts.get("core") or {})
    if core.get("repository") != POKROV_CORE_REPOSITORY:
        failures.append(f"runtime artifacts must stay pinned to {POKROV_CORE_REPOSITORY}")
    if core.get("release_tag") != POKROV_CORE_RELEASE_TAG:
        failures.append(f"runtime artifacts must stay pinned to POKROV Core {POKROV_CORE_RELEASE_TAG}")
    if core.get("source_commit") != POKROV_CORE_SOURCE_COMMIT:
        failures.append("runtime artifacts must pin the reviewed POKROV Core source commit")
    if core.get("activation_state") != "active":
        failures.append("runtime artifacts must keep POKROV Core active")

    provenance = dict(core.get("artifact_provenance") or {})
    reproducible_build = dict(provenance.get("reproducible_build") or {})
    reproducible_android = dict(reproducible_build.get("android") or {})
    reproducible_windows = dict(reproducible_build.get("windows") or {})
    if (
        provenance.get("status") != "clean_reproducible_release"
        or provenance.get("vcs_stamp") != "disabled_for_reproducible_release_artifacts"
        or provenance.get("source_identity") != "annotated_release_tag_and_github_release_commit"
        or provenance.get("release_url") != POKROV_CORE_RELEASE_URL
        or int(reproducible_android.get("size") or 0) != ANDROID_CORE_SIZE
        or reproducible_android.get("sha256") != ANDROID_CORE_SHA256
        or int(reproducible_windows.get("size") or 0) != WINDOWS_CORE_SIZE
        or reproducible_windows.get("sha256") != WINDOWS_CORE_SHA256
        or reproducible_build.get("libcronet_sha256") != WINDOWS_CRONET_SHA256
        or provenance.get("promotion_rule") != "accept_exact_v1.0.3_release_artifacts"
    ):
        failures.append("runtime artifacts must pin the clean reproducible POKROV Core release provenance")

    desktop_abi = dict(core.get("desktop_abi") or {})
    if (
        desktop_abi.get("name") != "pokrov-core"
        or int(desktop_abi.get("version") or 0) != 2
        or desktop_abi.get("required_symbol") != "pokrovCoreAbiVersion"
        or desktop_abi.get("secure_file_symbol") != "pokrovSecureFile"
    ):
        failures.append("runtime artifacts must keep the POKROV Core desktop ABI 2 contract")

    assets = dict(core.get("assets") or {})
    windows = dict(assets.get("windows") or {})
    if (
        windows.get("entry") != "pokrov-core.dll"
        or int(windows.get("size") or 0) != WINDOWS_CORE_SIZE
        or windows.get("sha256") != WINDOWS_CORE_SHA256
    ):
        failures.append("runtime artifacts must pin the reviewed Windows POKROV Core DLL")
    if "helper" in windows:
        failures.append("runtime artifacts must not declare a Windows helper binary")
    if windows.get("sync_destination") != "apps/windows_shell/windows/runner/resources/runtime":
        failures.append(
            "runtime artifacts must sync the Windows POKROV Core payload into apps/windows_shell/windows/runner/resources/runtime"
        )
    if "libcronet.dll" not in list(windows.get("runtime_dependencies") or []):
        failures.append("runtime artifacts must keep libcronet.dll as a Windows runtime dependency")
    dependency_sizes = dict(windows.get("runtime_dependency_size") or {})
    dependency_hashes = dict(windows.get("runtime_dependency_sha256") or {})
    if (
        int(dependency_sizes.get("libcronet.dll") or 0) != WINDOWS_CRONET_SIZE
        or dependency_hashes.get("libcronet.dll") != WINDOWS_CRONET_SHA256
    ):
        failures.append("runtime artifacts must pin the reviewed libcronet.dll identity")

    android = dict(assets.get("android") or {})
    if (
        android.get("entry") != "pokrov-core.aar"
        or int(android.get("size") or 0) != ANDROID_CORE_SIZE
        or android.get("sha256") != ANDROID_CORE_SHA256
    ):
        failures.append("runtime artifacts must pin the reviewed Android POKROV Core AAR")
    if android.get("sync_destination") != "apps/android_shell/android/app/libs":
        failures.append("runtime artifacts must sync the Android POKROV Core payload into apps/android_shell/android/app/libs")

    return failures


def _artifact_file_failures(
    path: Path,
    *,
    label: str,
    expected_size: int,
    expected_sha256: str,
) -> list[str]:
    if not path.is_file():
        return [f"{label} is missing: {path}"]
    if path.stat().st_size != expected_size:
        return [f"{label} size does not match the reviewed runtime artifact"]
    with path.open("rb") as source:
        actual_sha256 = hashlib.file_digest(source, "sha256").hexdigest()
    if actual_sha256 != expected_sha256:
        return [f"{label} SHA-256 does not match the reviewed runtime artifact"]
    return []


def _runtime_file_failures() -> list[str]:
    failures: list[str] = []
    failures.extend(
        _artifact_file_failures(
            ANDROID_CORE_PATH,
            label="Android POKROV Core AAR",
            expected_size=ANDROID_CORE_SIZE,
            expected_sha256=ANDROID_CORE_SHA256,
        )
    )
    failures.extend(
        _artifact_file_failures(
            WINDOWS_CORE_PATH,
            label="Windows POKROV Core DLL",
            expected_size=WINDOWS_CORE_SIZE,
            expected_sha256=WINDOWS_CORE_SHA256,
        )
    )
    failures.extend(
        _artifact_file_failures(
            WINDOWS_CRONET_PATH,
            label="Windows libcronet.dll",
            expected_size=WINDOWS_CRONET_SIZE,
            expected_sha256=WINDOWS_CRONET_SHA256,
        )
    )
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
    if 'keepDebugSymbols += ["**/libpokrov-core.so"]' not in build_gradle_text:
        failures.append("Android packaging must preserve the exact published POKROV Core ELF identity")

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
        "pokrov-core.dll",
        "libcronet.dll",
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
    if runtime.get("core_binary") != "pokrov-core.dll":
        failures.append("Windows release seed must keep runtime.core_binary as pokrov-core.dll")
    if runtime.get("release_tag") != POKROV_CORE_RELEASE_TAG:
        failures.append(f"Windows release seed must keep runtime.release_tag as {POKROV_CORE_RELEASE_TAG}")
    if int(runtime.get("desktop_abi") or 0) != 2:
        failures.append("Windows release seed must keep runtime.desktop_abi as 2")
    if "libcronet.dll" not in list(runtime.get("runtime_dependencies") or []):
        failures.append("Windows release seed must keep libcronet.dll as a runtime dependency")
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
        ANDROID_CORE_PATH,
        WINDOWS_CORE_PATH,
        WINDOWS_CRONET_PATH,
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
    failures.extend(_runtime_file_failures())
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
