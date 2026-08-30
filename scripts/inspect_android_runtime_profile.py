from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import threading
import time
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from typing import Any


PROFILE_FINAL_TAGS = {
    "awg2_lab": "pokrov-awg2-lab",
    "awg31_lab": "pokrov-awg31-lab",
}
SUPPORTED_PROFILES = ("default", "awg2_lab", "awg31_lab")
DEFAULT_PACKAGE = "space.pokrov.pokrov_android_shell"
PREFERENCES_FILE = "pokrov_runtime_profile.xml"
MAX_PREFERENCES_BYTES = 64 * 1024
MAX_RUNTIME_CONFIG_BYTES = 64 * 1024
MAX_ADB_STDERR_BYTES = 64 * 1024
_PACKAGE_PATTERN = re.compile(
    r"^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+$"
)
_DEVICE_PATH_PATTERN = re.compile(r"^/[A-Za-z0-9._/-]+$")


class RuntimeProfileBoundaryError(RuntimeError):
    pass


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


def _run_bounded_process(
    command: list[str],
    *,
    stdout_limit: int,
    stderr_limit: int,
    timeout: int,
) -> tuple[int, bytes, bytes]:
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        raise RuntimeError("ADB runtime-profile process could not start") from exc

    overflow = threading.Event()
    stdout_chunks: list[bytes] = []
    stderr_chunks: list[bytes] = []

    def _read_bounded(
        stream: Any,
        limit: int,
        chunks: list[bytes],
    ) -> None:
        total = 0
        while True:
            chunk = stream.read(8192)
            if not chunk:
                return
            remaining = limit - total
            if remaining > 0:
                retained = chunk[:remaining]
                chunks.append(retained)
                total += len(retained)
            if len(chunk) > remaining:
                overflow.set()
                try:
                    process.kill()
                except OSError:
                    pass
                return

    assert process.stdout is not None and process.stderr is not None
    readers = (
        threading.Thread(
            target=_read_bounded,
            args=(process.stdout, stdout_limit, stdout_chunks),
            daemon=True,
        ),
        threading.Thread(
            target=_read_bounded,
            args=(process.stderr, stderr_limit, stderr_chunks),
            daemon=True,
        ),
    )
    for reader in readers:
        reader.start()

    timed_out = False
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        process.wait(timeout=2)
    finally:
        for reader in readers:
            reader.join(timeout=2)
        process.stdout.close()
        process.stderr.close()

    if any(reader.is_alive() for reader in readers):
        raise RuntimeError("ADB runtime-profile output drain timed out")
    if overflow.is_set():
        raise RuntimeProfileBoundaryError("ADB runtime-profile output exceeded its limit")
    if timed_out:
        raise RuntimeError("ADB runtime-profile readback timed out")
    return process.returncode, b"".join(stdout_chunks), b"".join(stderr_chunks)


def _run_adb(
    adb: Path,
    serial: str,
    *arguments: str,
    stdout_limit: int,
    boundary_returncodes: frozenset[int] = frozenset(),
) -> bytes:
    returncode, stdout, _stderr = _run_bounded_process(
        [str(adb), "-s", serial, *arguments],
        stdout_limit=stdout_limit,
        stderr_limit=MAX_ADB_STDERR_BYTES,
        timeout=20,
    )
    if returncode in boundary_returncodes:
        raise RuntimeProfileBoundaryError("ADB runtime-profile boundary validation failed")
    if returncode != 0:
        raise RuntimeError("ADB runtime-profile readback failed")
    return stdout


def _valid_package(package: str) -> bool:
    return _PACKAGE_PATTERN.fullmatch(package) is not None


def _runtime_root(package: str) -> str:
    if not _valid_package(package):
        raise RuntimeProfileBoundaryError("Android package is invalid")
    return f"/data/user/0/{package}/files/pokrov-runtime"


def _validated_runtime_path(path: str, package: str) -> str:
    runtime_root = PurePosixPath(_runtime_root(package))
    if (
        not path
        or _DEVICE_PATH_PATTERN.fullmatch(path) is None
        or "//" in path
        or any(part in {"", ".", ".."} for part in path.split("/")[1:])
    ):
        raise RuntimeProfileBoundaryError(
            "Android runtime-profile path is outside the app runtime"
        )
    candidate = PurePosixPath(path)
    try:
        relative = candidate.relative_to(runtime_root)
    except ValueError as exc:
        raise RuntimeProfileBoundaryError(
            "Android runtime-profile path is outside the app runtime"
        ) from exc
    if relative == PurePosixPath("."):
        raise RuntimeProfileBoundaryError(
            "Android runtime-profile path is outside the app runtime"
        )
    return str(candidate)


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
    return _validated_runtime_path(matches[0], package)


def _read_remote_file(
    adb: Path,
    serial: str,
    path: str,
    canonical_root: str,
    maximum_bytes: int,
    *,
    exact_target: bool,
) -> str:
    if (
        _DEVICE_PATH_PATTERN.fullmatch(path) is None
        or _DEVICE_PATH_PATTERN.fullmatch(canonical_root) is None
    ):
        raise RuntimeProfileBoundaryError("Android runtime-profile device path is invalid")
    alternate_root = canonical_root.replace("/data/user/0/", "/data/data/", 1)
    if alternate_root == canonical_root:
        raise RuntimeProfileBoundaryError("Android runtime-profile root is invalid")
    target_guard = (
        f'[ "$target_real" = "$root_real/{shlex.quote(PurePosixPath(path).name)}" ] || exit 61; '
        if exact_target
        else 'case "$target_real" in "$root_real"/*) ;; *) exit 61 ;; esac; '
    )
    remote_script = (
        "set -eu; "
        f"root={shlex.quote(canonical_root)}; "
        f"alternate_root={shlex.quote(alternate_root)}; "
        f"target={shlex.quote(path)}; "
        'root_real="$(toybox realpath "$root")" || exit 10; '
        'case "$root_real" in "$root"|"$alternate_root") ;; *) exit 61 ;; esac; '
        'exec 3<"$target" || exit 1; '
        'target_real="$(toybox realpath "/proc/$$/fd/3")" || exit 61; '
        + target_guard
        + '[ -f "/proc/$$/fd/3" ] || exit 61; '
        + f"toybox head -c {maximum_bytes + 1} <&3"
    )
    raw = _run_adb(
        adb,
        serial,
        "shell",
        f"su 0 sh -c {shlex.quote(remote_script)}",
        stdout_limit=maximum_bytes + 1,
        boundary_returncodes=frozenset({61, 126, 127}),
    )
    if len(raw) > maximum_bytes:
        raise RuntimeProfileBoundaryError("Android runtime-profile file exceeded its limit")
    try:
        return raw.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise ValueError("Android runtime-profile file is not UTF-8") from exc


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
            preferences = _read_remote_file(
                adb,
                serial,
                f"/data/user/0/{package}/shared_prefs/{PREFERENCES_FILE}",
                f"/data/user/0/{package}/shared_prefs",
                MAX_PREFERENCES_BYTES,
                exact_target=True,
            )
            config_path = _runtime_config_path(preferences, package)
            raw_config = _read_remote_file(
                adb,
                serial,
                config_path,
                _runtime_root(package),
                MAX_RUNTIME_CONFIG_BYTES,
                exact_target=False,
            )
            config = json.loads(raw_config)
            if not isinstance(config, dict):
                raise ValueError("Android runtime profile root is invalid")
            return config
        except RuntimeProfileBoundaryError:
            raise SystemExit(
                "Android runtime profile failed containment or size validation"
            ) from None
        except (RuntimeError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
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
    if not serial or not _valid_package(package):
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
