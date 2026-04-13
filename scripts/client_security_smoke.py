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

    if "RoutingMode.values" in config_page_text and ".visibleChoices(" not in config_page_text:
        failures.append(
            "public routing picker must use RoutingMode.visibleChoices to keep blockedOnly internal by default"
        )

    if ".visibleChoices(" not in config_page_text:
        failures.append("public routing picker must filter routing presets before rendering choices")

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

    failures.extend(_security_default_failures(config_text, go_defaults_text))
    failures.extend(_analytics_default_failures(analytics_text))
    failures.extend(_routing_preset_failures(enum_text, config_text))
    failures.extend(_public_routing_surface_failures(config_page_text))
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
