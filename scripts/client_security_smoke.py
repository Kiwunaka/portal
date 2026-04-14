from __future__ import annotations

import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLIENT_ROOT = REPO_ROOT / "external" / "client-fork" / "app"

CONFIG_OPTIONS_PATH = CLIENT_ROOT / "lib" / "features" / "config_option" / "data" / "config_option_repository.dart"
CONFIG_OPTIONS_PAGE_PATH = CLIENT_ROOT / "lib" / "features" / "config_option" / "overview" / "config_options_page.dart"
ROUTING_ENUM_PATH = CLIENT_ROOT / "lib" / "singbox" / "model" / "singbox_config_enum.dart"
BOX_SERVICE_PATH = CLIENT_ROOT / "android" / "app" / "src" / "main" / "kotlin" / "com" / "hiddify" / "hiddify" / "bg" / "BoxService.kt"
METHOD_HANDLER_PATH = CLIENT_ROOT / "android" / "app" / "src" / "main" / "kotlin" / "com" / "hiddify" / "hiddify" / "MethodHandler.kt"
GO_DEFAULTS_PATH = CLIENT_ROOT / "libcore" / "config" / "hiddify_option.go"
ANALYTICS_CONTROLLER_PATH = CLIENT_ROOT / "lib" / "core" / "analytics" / "analytics_controller.dart"
APP_INFO_PATH = CLIENT_ROOT / "lib" / "core" / "model" / "app_info_entity.dart"
PROFILE_REPOSITORY_PATH = CLIENT_ROOT / "lib" / "features" / "profile" / "data" / "profile_repository.dart"
ANDROID_MANIFEST_PATH = CLIENT_ROOT / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
WINDOWS_EXE_CONFIG_PATH = CLIENT_ROOT / "windows" / "packaging" / "exe" / "make_config.yaml"
WINDOWS_MSIX_CONFIG_PATH = CLIENT_ROOT / "windows" / "packaging" / "msix" / "make_config.yaml"
WINDOWS_RUNNER_RC_PATH = CLIENT_ROOT / "windows" / "runner" / "Runner.rc"
WINDOWS_MAIN_CPP_PATH = CLIENT_ROOT / "windows" / "runner" / "main.cpp"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _pref_default(config_text: str, key: str) -> str | None:
    pattern = re.compile(
        r'PreferencesNotifier\.create<[^>]+>\(\s*"' + re.escape(key) + r'"\s*,\s*([^,\n]+)',
        re.MULTILINE,
    )
    match = pattern.search(config_text)
    if match is None:
        return None
    return match.group(1).strip()


def _pref_block(config_text: str, key: str) -> str | None:
    pattern = re.compile(
        r'PreferencesNotifier\.create<[^>]+>\(\s*"'
        + re.escape(key)
        + r'"\s*,.*?\n\s*\);',
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(config_text)
    if match is None:
        return None
    return match.group(0)


def _security_default_failures(config_text: str, go_defaults_text: str) -> list[str]:
    failures: list[str] = []

    enable_clash_api_default = _pref_default(config_text, "enable-clash-api")
    if enable_clash_api_default is None:
        failures.append("enable-clash-api preference is missing")
    elif enable_clash_api_default != "false":
        failures.append("enable-clash-api must default to false")

    allow_lan_default = _pref_default(config_text, "allow-connection-from-lan")
    if allow_lan_default is None:
        failures.append("allow-connection-from-lan preference is missing")
    elif allow_lan_default != "false":
        failures.append("allow-connection-from-lan must default to false")

    if "applyReleaseLocalSurfacePolicy(" not in config_text:
        failures.append("Android release config must apply local surface sanitization before startup")

    go_expectations = {
        "MixedPort:": "MixedPort:      0",
        "TProxyPort:": "TProxyPort:     0",
        "LocalDnsPort:": "LocalDnsPort:   0",
        "EnableClashApi:": "EnableClashApi: false",
    }
    for label, snippet in go_expectations.items():
        if snippet not in go_defaults_text:
            failures.append(f"{label.rstrip(':')} must default to a release-safe value in libcore")

    return failures


def _analytics_default_failures(analytics_text: str) -> list[str]:
    failures: list[str] = []

    if "getBool(enableAnalyticsPrefKey) ?? false" not in analytics_text:
        failures.append("analytics must default to disabled until the user explicitly opts in")

    return failures


def _routing_default_failures(config_text: str) -> list[str]:
    failures: list[str] = []

    routing_mode_default = _pref_default(config_text, "routing-mode")
    if routing_mode_default is None:
        failures.append("routing-mode preference is missing")
    elif routing_mode_default != "RoutingMode.allExceptRu":
        failures.append("routing-mode must default to RoutingMode.allExceptRu for the consumer path")

    remote_dns_default = _pref_default(config_text, "remote-dns-address")
    if remote_dns_default is None:
        failures.append("remote-dns-address preference is missing")
    elif not remote_dns_default.startswith(('"https://', "'https://")):
        failures.append("remote-dns-address must default to a tunneled DoH endpoint instead of udp://1.1.1.1")

    direct_dns_block = _pref_block(config_text, "direct-dns-address")
    if direct_dns_block is None:
        failures.append("direct-dns-address preference is missing")
    elif re.search(r'RoutingMode\.allExceptRu\s*=>\s*["\']local["\']', direct_dns_block) is None:
        failures.append("direct-dns-address must default to local for split-direct routing")

    return failures


def _routing_preset_failures(enum_text: str, config_text: str) -> list[str]:
    failures: list[str] = []

    if "allExceptRu" not in enum_text:
        failures.append("RoutingMode must include allExceptRu")
    if "blockedOnly" not in enum_text:
        failures.append("RoutingMode must include blockedOnly")

    if "RoutingMode.allExceptRu" not in config_text:
        failures.append("buildRoutingRules must handle RoutingMode.allExceptRu")
    if "RoutingMode.blockedOnly" not in config_text:
        failures.append("buildRoutingRules must handle RoutingMode.blockedOnly")

    if "geoip:private" not in config_text:
        failures.append("RoutingMode.allExceptRu must bypass geoip:private")

    if "geoip:ru" not in config_text:
        failures.append("RoutingMode.allExceptRu must bypass geoip:ru")

    if "domain:.ru" not in config_text:
        failures.append("RoutingMode.allExceptRu must bypass domain:.ru")

    if "RuleOutbound.bypass" not in config_text:
        failures.append("RoutingMode.allExceptRu must use RuleOutbound.bypass for direct traffic")

    if "kBlockedOnlyRuleSetUrl" not in config_text:
        failures.append("RoutingMode.blockedOnly must use a first-class blocked-destination ruleset")

    if "ruleSetUrl: kBlockedOnlyRuleSetUrl" not in config_text:
        failures.append("RoutingMode.blockedOnly must proxy through the blocked-destination ruleset")

    return failures


def _public_routing_surface_failures(config_page_text: str) -> list[str]:
    failures: list[str] = []
    uses_filtered_choices = (
        ".visibleChoices(" in config_page_text
        or "consumerRoutingChoices(" in config_page_text
    )

    if "RoutingMode.values" in config_page_text and not uses_filtered_choices:
        failures.append(
            "public routing picker must use RoutingMode.visibleChoices to keep blockedOnly internal by default"
        )

    if not uses_filtered_choices:
        failures.append("public routing picker must filter routing presets before rendering choices")

    return failures


def _contains_legacy_identity(text: str) -> bool:
    lowered = text.casefold()
    return any(token in lowered for token in ("clash", "v2ray", "v2rayng", "sing-box", "singbox"))


def _identity_failures(app_info_text: str, profile_text: str) -> list[str]:
    failures: list[str] = []

    if _contains_legacy_identity(app_info_text):
        failures.append("app user agent must not mention clash/v2ray/sing-box")

    profile_user_agent_match = re.search(
        r'userAgent\s*:\s*configs\.useXrayCoreWhenPossible\s*\?\s*(.+?)\s*:\s*null',
        profile_text,
        re.MULTILINE | re.DOTALL,
    )
    if profile_user_agent_match is None:
        return failures

    profile_user_agent = profile_user_agent_match.group(1).strip()
    if _contains_legacy_identity(profile_user_agent) or "pokrov" not in profile_user_agent.casefold():
        failures.append("compatibility profile downloads must use a first-party user agent")

    return failures


def _packaging_branding_failures(
    *,
    manifest_text: str,
    exe_config_text: str,
    msix_text: str,
    runner_rc_text: str,
    main_cpp_text: str,
) -> list[str]:
    failures: list[str] = []

    if 'android:label="POKROV"' not in manifest_text:
        failures.append("Android launcher label must be POKROV")
    if 'android:scheme="pokrov"' not in manifest_text:
        failures.append("Android manifest must register pokrov:// as the canonical app link scheme")

    if re.search(r"^\s*display_name:\s*POKROV\s*$", exe_config_text, flags=re.MULTILINE) is None:
        failures.append("Windows exe package display_name must be POKROV")
    if "output_base_file_name: pokrov-windows-setup-x64" not in exe_config_text:
        failures.append("Windows exe package output filename must drop vpn wording")

    if re.search(r"^\s*display_name:\s*POKROV\s*$", msix_text, flags=re.MULTILINE) is None:
        failures.append("Windows msix display_name must be POKROV")
    if re.search(r"^\s*protocol_activation:\s*pokrov\s*$", msix_text, flags=re.MULTILINE) is None:
        failures.append("Windows msix protocol activation must use pokrov")

    required_runner_values = (
        'VALUE "CompanyName", "POKROV"',
        'VALUE "FileDescription", "POKROV"',
        'VALUE "ProductName", "POKROV"',
    )
    if any(value not in runner_rc_text for value in required_runner_values):
        failures.append("Windows runner resources must use POKROV for CompanyName/FileDescription/ProductName")

    if 'window.Create(L"POKROV"' not in main_cpp_text:
        failures.append("Windows main window title must be POKROV")

    return failures


def _control_surface_observations(
    *,
    box_service_text: str,
    method_handler_text: str,
) -> list[str]:
    observations: list[str] = []

    command_server_guarded = "CommandServer(" in box_service_text and "BuildConfig.DEBUG" in box_service_text
    if "CommandServer(" in box_service_text and not command_server_guarded:
        observations.append(
            "android libbox CommandServer is present and requires release-build localhost audit"
        )

    standalone_client_guarded = "newStandaloneCommandClient" in method_handler_text and "BuildConfig.DEBUG" in method_handler_text
    if "newStandaloneCommandClient" in method_handler_text and not standalone_client_guarded:
        observations.append("android/libbox standalone command client calls are present")

    return observations


def _check_required_files() -> list[str]:
    missing: list[str] = []
    for path in [
        CONFIG_OPTIONS_PATH,
        CONFIG_OPTIONS_PAGE_PATH,
        ROUTING_ENUM_PATH,
        BOX_SERVICE_PATH,
        METHOD_HANDLER_PATH,
        GO_DEFAULTS_PATH,
        ANALYTICS_CONTROLLER_PATH,
        APP_INFO_PATH,
        PROFILE_REPOSITORY_PATH,
        ANDROID_MANIFEST_PATH,
        WINDOWS_EXE_CONFIG_PATH,
        WINDOWS_MSIX_CONFIG_PATH,
        WINDOWS_RUNNER_RC_PATH,
        WINDOWS_MAIN_CPP_PATH,
    ]:
        if not path.exists():
            missing.append(f"required client file is missing: {path.relative_to(REPO_ROOT)}")
    return missing


def main() -> int:
    failures = _check_required_files()
    if failures:
        for failure in failures:
            print(f"[fail] {failure}")
        return 2

    config_text = _read_text(CONFIG_OPTIONS_PATH)
    enum_text = _read_text(ROUTING_ENUM_PATH)
    config_page_text = _read_text(CONFIG_OPTIONS_PAGE_PATH)
    box_service_text = _read_text(BOX_SERVICE_PATH)
    method_handler_text = _read_text(METHOD_HANDLER_PATH)
    go_defaults_text = _read_text(GO_DEFAULTS_PATH)
    analytics_text = _read_text(ANALYTICS_CONTROLLER_PATH)
    app_info_text = _read_text(APP_INFO_PATH)
    profile_text = _read_text(PROFILE_REPOSITORY_PATH)
    manifest_text = _read_text(ANDROID_MANIFEST_PATH)
    exe_config_text = _read_text(WINDOWS_EXE_CONFIG_PATH)
    msix_text = _read_text(WINDOWS_MSIX_CONFIG_PATH)
    runner_rc_text = _read_text(WINDOWS_RUNNER_RC_PATH)
    main_cpp_text = _read_text(WINDOWS_MAIN_CPP_PATH)

    failures.extend(_security_default_failures(config_text, go_defaults_text))
    failures.extend(_analytics_default_failures(analytics_text))
    failures.extend(_routing_default_failures(config_text))
    failures.extend(_routing_preset_failures(enum_text, config_text))
    failures.extend(_public_routing_surface_failures(config_page_text))
    failures.extend(_identity_failures(app_info_text, profile_text))
    failures.extend(
        _packaging_branding_failures(
            manifest_text=manifest_text,
            exe_config_text=exe_config_text,
            msix_text=msix_text,
            runner_rc_text=runner_rc_text,
            main_cpp_text=main_cpp_text,
        )
    )
    observations = _control_surface_observations(
        box_service_text=box_service_text,
        method_handler_text=method_handler_text,
    )

    print(f"[check] config options: {CONFIG_OPTIONS_PATH.relative_to(REPO_ROOT)}")
    print(f"[check] config options page: {CONFIG_OPTIONS_PAGE_PATH.relative_to(REPO_ROOT)}")
    print(f"[check] routing enum: {ROUTING_ENUM_PATH.relative_to(REPO_ROOT)}")
    print(f"[check] android control surfaces: {BOX_SERVICE_PATH.relative_to(REPO_ROOT)}")
    print(f"[check] android method handler: {METHOD_HANDLER_PATH.relative_to(REPO_ROOT)}")
    print(f"[check] libcore defaults: {GO_DEFAULTS_PATH.relative_to(REPO_ROOT)}")
    print(f"[check] analytics defaults: {ANALYTICS_CONTROLLER_PATH.relative_to(REPO_ROOT)}")
    print(f"[check] app identity: {APP_INFO_PATH.relative_to(REPO_ROOT)}")
    print(f"[check] profile identity: {PROFILE_REPOSITORY_PATH.relative_to(REPO_ROOT)}")
    print(f"[check] Android manifest: {ANDROID_MANIFEST_PATH.relative_to(REPO_ROOT)}")
    print(f"[check] Windows exe package: {WINDOWS_EXE_CONFIG_PATH.relative_to(REPO_ROOT)}")
    print(f"[check] Windows msix package: {WINDOWS_MSIX_CONFIG_PATH.relative_to(REPO_ROOT)}")
    print(f"[check] Windows runner resources: {WINDOWS_RUNNER_RC_PATH.relative_to(REPO_ROOT)}")
    print(f"[check] Windows main window: {WINDOWS_MAIN_CPP_PATH.relative_to(REPO_ROOT)}")

    for observation in observations:
        print(f"[observe] {observation}")

    if failures:
        for failure in failures:
            print(f"[fail] {failure}")
        return 2

    print("[pass] client security smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
