from __future__ import annotations

import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLIENT_ROOT = REPO_ROOT / "external" / "client-fork" / "app"

CONFIG_OPTIONS_PATH = CLIENT_ROOT / "lib" / "features" / "config_option" / "data" / "config_option_repository.dart"
ROUTING_ENUM_PATH = CLIENT_ROOT / "lib" / "singbox" / "model" / "singbox_config_enum.dart"
BOX_SERVICE_PATH = CLIENT_ROOT / "android" / "app" / "src" / "main" / "kotlin" / "com" / "hiddify" / "hiddify" / "bg" / "BoxService.kt"
METHOD_HANDLER_PATH = CLIENT_ROOT / "android" / "app" / "src" / "main" / "kotlin" / "com" / "hiddify" / "hiddify" / "MethodHandler.kt"
CORE_SERVICE_PATH = CLIENT_ROOT / "lib" / "singbox" / "service" / "core_singbox_service.dart"


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


def _security_default_failures(config_text: str) -> list[str]:
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

    return failures


def _routing_preset_failures(enum_text: str, config_text: str) -> list[str]:
    failures: list[str] = []

    if "allExceptRu" not in enum_text:
        failures.append("RoutingMode must include allExceptRu")

    if "RoutingMode.allExceptRu" not in config_text:
        failures.append("buildRoutingRules must handle RoutingMode.allExceptRu")
        return failures

    if "geoip:private" not in config_text:
        failures.append("RoutingMode.allExceptRu must bypass geoip:private")

    if "geoip:ru" not in config_text:
        failures.append("RoutingMode.allExceptRu must bypass geoip:ru")

    if "domain:.ru" not in config_text:
        failures.append("RoutingMode.allExceptRu must bypass domain:.ru")

    if "RuleOutbound.bypass" not in config_text:
        failures.append("RoutingMode.allExceptRu must use RuleOutbound.bypass for direct traffic")

    return failures


def _control_surface_observations(
    *,
    box_service_text: str,
    method_handler_text: str,
    core_service_text: str,
) -> list[str]:
    observations: list[str] = []

    if "CommandServer(" in box_service_text:
        observations.append(
            "android libbox CommandServer is present and requires release-build localhost audit"
        )

    if "newStandaloneCommandClient" in method_handler_text:
        observations.append("android/libbox standalone command client calls are present")

    if "ClientChannel(" in core_service_text and "'localhost'" in core_service_text:
        observations.append("localhost gRPC channel is present in core sing-box service")

    return observations


def _check_required_files() -> list[str]:
    missing: list[str] = []
    for path in [
        CONFIG_OPTIONS_PATH,
        ROUTING_ENUM_PATH,
        BOX_SERVICE_PATH,
        METHOD_HANDLER_PATH,
        CORE_SERVICE_PATH,
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
    box_service_text = _read_text(BOX_SERVICE_PATH)
    method_handler_text = _read_text(METHOD_HANDLER_PATH)
    core_service_text = _read_text(CORE_SERVICE_PATH)

    failures.extend(_security_default_failures(config_text))
    failures.extend(_routing_preset_failures(enum_text, config_text))
    observations = _control_surface_observations(
        box_service_text=box_service_text,
        method_handler_text=method_handler_text,
        core_service_text=core_service_text,
    )

    print(f"[check] config options: {CONFIG_OPTIONS_PATH.relative_to(REPO_ROOT)}")
    print(f"[check] routing enum: {ROUTING_ENUM_PATH.relative_to(REPO_ROOT)}")
    print(f"[check] android control surfaces: {BOX_SERVICE_PATH.relative_to(REPO_ROOT)}")
    print(f"[check] android method handler: {METHOD_HANDLER_PATH.relative_to(REPO_ROOT)}")
    print(f"[check] core service transport: {CORE_SERVICE_PATH.relative_to(REPO_ROOT)}")

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
