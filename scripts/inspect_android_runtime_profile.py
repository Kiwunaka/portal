from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


PROFILE_FINAL_TAGS = {
    "awg2_lab": "pokrov-awg2-lab",
    "awg31_lab": "pokrov-awg31-lab",
}
SUPPORTED_PROFILES = ("default", "awg2_lab", "awg31_lab")
DEFAULT_PACKAGE = "space.pokrov.pokrov_android_shell"
PREFERENCES_FILE = "pokrov_runtime_profile.xml"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect the exact Android runtime profile selected by POKROV without "
            "returning endpoints, identifiers or key material."
        )
    )
    parser.add_argument("--adb", required=True)
    parser.add_argument("--adb-serial", required=True)
    parser.add_argument("--package", default=DEFAULT_PACKAGE)
    parser.add_argument(
        "--expected-profile",
        choices=SUPPORTED_PROFILES,
        required=True,
    )
    parser.add_argument(
        "--wait-seconds",
        type=int,
        default=10,
        help="Wait up to this bounded interval for the app to stage its profile.",
    )
    parser.add_argument("--json-out", default="")
    return parser.parse_args()


def _run_adb(adb: Path, serial: str, *arguments: str) -> str:
    completed = subprocess.run(
        [str(adb), "-s", serial, *arguments],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
    )
    if completed.returncode != 0:
        raise RuntimeError("ADB runtime-profile readback failed")
    return completed.stdout


def _runtime_config_path(preferences_xml: str, package: str) -> str:
    try:
        root = ET.fromstring(preferences_xml)
    except ET.ParseError as exc:
        raise ValueError("Android runtime-profile preferences are invalid") from exc
    matches = [
        str(node.text or "").strip()
        for node in root.findall("string")
        if node.attrib.get("name") == "config_path"
    ]
    if len(matches) != 1 or not matches[0]:
        raise ValueError("Android runtime-profile path is unavailable")
    path = matches[0]
    expected_prefix = f"/data/user/0/{package}/files/pokrov-runtime/"
    if not path.startswith(expected_prefix) or path.endswith("/"):
        raise ValueError("Android runtime-profile path is outside the app runtime")
    return path


def _profile_kind(config: dict[str, Any]) -> tuple[str, bool]:
    route = config.get("route")
    route_final = str(route.get("final") or "") if isinstance(route, dict) else ""
    endpoints = config.get("endpoints")
    endpoint_rows = endpoints if isinstance(endpoints, list) else []
    awg_tags = {
        str(row.get("tag") or "")
        for row in endpoint_rows
        if isinstance(row, dict) and str(row.get("type") or "") == "awg"
    }
    for profile, final_tag in PROFILE_FINAL_TAGS.items():
        if route_final == final_tag and final_tag in awg_tags:
            return profile, True
    lab_markers = set(PROFILE_FINAL_TAGS.values())
    if route_final in lab_markers or awg_tags.intersection(lab_markers):
        return "invalid_lab_profile", False
    if any(
        isinstance(row, dict) and str(row.get("type") or "") == "awg"
        for row in endpoint_rows
    ):
        return "unknown_awg_profile", False
    return "default", True


def _contains_private_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).replace("-", "_").lower()
            if normalized in {"private_key", "privatekey"} and bool(child):
                return True
            if _contains_private_key(child):
                return True
    elif isinstance(value, list):
        return any(_contains_private_key(child) for child in value)
    return False


def _safe_type_counts(config: dict[str, Any], field: str) -> dict[str, int]:
    rows = config.get(field)
    counts: dict[str, int] = {}
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        item_type = str(row.get("type") or "unknown").strip().lower() or "unknown"
        counts[item_type] = counts.get(item_type, 0) + 1
    return dict(sorted(counts.items()))


def inspect_runtime_profile(config: dict[str, Any], expected_profile: str) -> dict[str, Any]:
    observed_profile, internally_consistent = _profile_kind(config)
    return {
        "schema_version": "pokrov-android-runtime-profile-readback-v1",
        "expected_profile": expected_profile,
        "observed_profile": observed_profile,
        "matches_expected_profile": (
            internally_consistent and observed_profile == expected_profile
        ),
        "profile_internally_consistent": internally_consistent,
        "endpoint_type_counts": _safe_type_counts(config, "endpoints"),
        "outbound_type_counts": _safe_type_counts(config, "outbounds"),
        "private_key_material_present": _contains_private_key(config),
        "raw_config_returned": False,
        "raw_endpoints_returned": False,
        "raw_identifiers_returned": False,
    }


def _emit_result(result: dict[str, Any], raw_output_path: str) -> None:
    encoded = json.dumps(result, indent=2, sort_keys=True)
    output_path = str(raw_output_path or "").strip()
    if output_path:
        target = Path(output_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
        try:
            temporary.write_text(encoded + "\n", encoding="utf-8")
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
    print(encoded)


def _load_runtime_config(
    adb: Path,
    serial: str,
    package: str,
    wait_seconds: int,
) -> dict[str, Any]:
    deadline = time.monotonic() + wait_seconds
    while True:
        try:
            preferences = _run_adb(
                adb,
                serial,
                "shell",
                "su",
                "0",
                "cat",
                f"/data/data/{package}/shared_prefs/{PREFERENCES_FILE}",
            )
            config_path = _runtime_config_path(preferences, package)
            raw_config = _run_adb(
                adb,
                serial,
                "shell",
                "su",
                "0",
                "cat",
                config_path,
            )
            config = json.loads(raw_config)
            if not isinstance(config, dict):
                raise ValueError("Android runtime profile root is invalid")
            return config
        except (RuntimeError, ValueError, json.JSONDecodeError):
            if time.monotonic() >= deadline:
                raise SystemExit(
                    "Android runtime profile was not staged before the bounded deadline"
                ) from None
            time.sleep(0.5)


def main() -> int:
    args = _parse_args()
    adb = Path(args.adb).resolve()
    if not adb.is_file():
        raise SystemExit("adb is missing")
    serial = str(args.adb_serial).strip()
    package = str(args.package).strip()
    if not serial or not package or any(value.isspace() for value in package):
        raise SystemExit("ADB serial or Android package is invalid")
    wait_seconds = int(args.wait_seconds)
    if wait_seconds < 0 or wait_seconds > 30:
        raise SystemExit("wait-seconds must be between 0 and 30")
    config = _load_runtime_config(adb, serial, package, wait_seconds)
    report = inspect_runtime_profile(config, str(args.expected_profile))
    _emit_result(report, args.json_out)
    return 0 if report["matches_expected_profile"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
