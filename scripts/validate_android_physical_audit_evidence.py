from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PASS = "PASS"
FAIL = "FAIL"
BLOCKED_BY_ACCESS = "BLOCKED_BY_ACCESS"
DEFAULT_PACKAGE = "space.pokrov.pokrov_android_shell"
DEFAULT_OUTPUT = Path("docs/audit-artifacts/android-physical-audit-evidence-validation-2026-05-08.json")


def _load_payload(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Android audit evidence file not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Android audit evidence file is not valid JSON: {path}: {exc}")
    if not isinstance(payload, dict):
        raise SystemExit("Android audit evidence JSON must be an object.")
    return payload


def _is_physical_serial(serial: str) -> bool:
    value = str(serial or "").strip().lower()
    if not value:
        return False
    if value.startswith("emulator-") or value in {"localhost", "127.0.0.1"}:
        return False
    if re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}:\d+", value):
        return False
    return True


def _phase_list(payload: dict[str, Any], name: str) -> list[Any]:
    value = payload.get(name)
    return value if isinstance(value, list) else []


def validate_payload(payload: dict[str, Any], *, expected_package: str = DEFAULT_PACKAGE) -> dict[str, Any]:
    missing: list[str] = []
    warnings: list[str] = []

    serial = str(payload.get("serial") or "").strip()
    if not _is_physical_serial(serial):
        missing.append("physical adb serial (not emulator-*, localhost, or tcpip serial)")

    package_name = str(payload.get("package_name") or "").strip()
    if package_name != expected_package:
        missing.append(f"package_name={expected_package}")

    failures = payload.get("failures")
    if not isinstance(failures, list):
        missing.append("failures list")
    elif failures:
        missing.append("failures=[]")

    package_evidence = payload.get("package_evidence")
    if not isinstance(package_evidence, dict):
        missing.append("package_evidence from --require-release-build")
        package_evidence = {}
    else:
        if str(package_evidence.get("package_name") or "").strip() != expected_package:
            missing.append(f"package_evidence.package_name={expected_package}")
        if package_evidence.get("debuggable") is not False:
            missing.append("package_evidence.debuggable=false")
        if not str(package_evidence.get("version_name") or "").strip():
            missing.append("package_evidence.version_name")
        if not str(package_evidence.get("version_code") or "").strip():
            missing.append("package_evidence.version_code")
        if not str(package_evidence.get("release_evidence") or "").strip():
            missing.append("package_evidence.release_evidence")

    metadata = payload.get("audit_metadata")
    if not isinstance(metadata, dict):
        missing.append("audit_metadata from current android_localhost_audit.py")
        metadata = {}
    else:
        if metadata.get("require_release_build") is not True:
            missing.append("audit_metadata.require_release_build=true")
        if metadata.get("release_evidence_present") is not True:
            missing.append("audit_metadata.release_evidence_present=true")
        if metadata.get("after_connect_observed") is not True or int(metadata.get("connect_wait_sec") or 0) <= 0:
            missing.append("audit_metadata.after_connect_observed=true with connect_wait_sec>0")
        if metadata.get("after_disconnect_observed") is not True or int(metadata.get("disconnect_wait_sec") or 0) <= 0:
            missing.append("audit_metadata.after_disconnect_observed=true with disconnect_wait_sec>0")

    for phase in ["baseline", "after_launch", "after_connect", "after_disconnect", "probes"]:
        if not isinstance(payload.get(phase), list):
            missing.append(f"{phase} list")

    if not _phase_list(payload, "after_connect") and not _phase_list(payload, "probes"):
        warnings.append("after_connect captured no listeners/probes; accepted only because metadata proves the phase was observed")
    if not _phase_list(payload, "after_disconnect") and not _phase_list(payload, "probes"):
        warnings.append("after_disconnect captured no listeners/probes; accepted only because metadata proves the phase was observed")

    classification = PASS if not missing else BLOCKED_BY_ACCESS
    return {
        "ok": classification == PASS,
        "classification": classification,
        "mode": "android_physical_audit_evidence_validation",
        "expected_package": expected_package,
        "serial": serial,
        "missing": missing,
        "warnings": warnings,
        "summary": {
            "package_name": package_name,
            "version_name": package_evidence.get("version_name", ""),
            "version_code": package_evidence.get("version_code", ""),
            "debuggable": package_evidence.get("debuggable", None),
            "failures_count": len(failures) if isinstance(failures, list) else None,
            "baseline_listeners": len(_phase_list(payload, "baseline")),
            "after_launch_listeners": len(_phase_list(payload, "after_launch")),
            "after_connect_listeners": len(_phase_list(payload, "after_connect")),
            "after_disconnect_listeners": len(_phase_list(payload, "after_disconnect")),
            "probes": len(_phase_list(payload, "probes")),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate retained Android physical release-build localhost/control-surface audit evidence.",
    )
    parser.add_argument("evidence_json", help="JSON output from scripts/android_localhost_audit.py.")
    parser.add_argument("--expected-package", default=DEFAULT_PACKAGE)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)

    report = validate_payload(_load_payload(Path(args.evidence_json)), expected_package=args.expected_package)
    report["source"] = str(Path(args.evidence_json))
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
