#!/usr/bin/env python3
"""Build, verify, and plan an allowlisted exact-candidate RU-origin bundle."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import zipfile
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_SCHEMA = "pokrov-ru-origin-probe-bundle-v1"
MANIFEST_NAME = "ru-origin-probe-bundle.json"
CANDIDATE6_SOURCE_REVISION = "5713324c1c0c2566befadf527bc09ec0ecf84a4e"
CANDIDATE8_SOURCE_REVISION = "241a83b4dca00799b39696a4ae0c3c97e087ec39"
CANDIDATE9_SOURCE_REVISION = "84687875916bbb35c0e28e0c2a8c7ea276753f31"
CANDIDATE10_SOURCE_REVISION = "209b8f40c36d95f2bbc67caa52a41ecb09f46720"
CANDIDATE16_SOURCE_REVISION = "719e23dc49407beb9ae30d98d17d4b73d18ae37c"
CANDIDATE21_SOURCE_REVISION = "e2608130e85d9a0f8fa4b920f46cf3d7679332c3"
APPROVED_SOURCE_REVISIONS = {
    CANDIDATE6_SOURCE_REVISION: "pokrov-1.2.0-candidate.6",
    CANDIDATE8_SOURCE_REVISION: "pokrov-1.2.0-candidate.8",
    CANDIDATE9_SOURCE_REVISION: "pokrov-1.2.0-candidate.9",
    CANDIDATE10_SOURCE_REVISION: "pokrov-1.2.0-candidate.10",
    CANDIDATE16_SOURCE_REVISION: "pokrov-1.2.0-candidate.16",
    CANDIDATE21_SOURCE_REVISION: "pokrov-1.2.0-candidate.21",
}
# Compatibility alias for older callers and retained candidate.6 fixtures.
EXPECTED_SOURCE_REVISION = CANDIDATE6_SOURCE_REVISION
REVISION_RE = re.compile(r"[0-9a-f]{40}\Z")
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")

SOURCE_MEMBERS: dict[str, dict[str, Any]] = {
    "scripts/ru_probe_runner.py": {
        "install_path": "/opt/pokrov/scripts/ru_probe_runner.py",
        "mode": "0755",
    },
    "scripts/ru_probe_uploader.py": {
        "install_path": "/opt/pokrov/scripts/ru_probe_uploader.py",
        "mode": "0755",
    },
    "scripts/internal_hmac_client.py": {
        "install_path": "/opt/pokrov/scripts/internal_hmac_client.py",
        "mode": "0644",
    },
    "portal_bot/internal_request_auth.py": {
        "install_path": "/opt/pokrov/portal_bot/internal_request_auth.py",
        "mode": "0644",
    },
    "scripts/node_dataplane_probe.py": {
        "install_path": "/opt/pokrov/scripts/node_dataplane_probe.py",
        "mode": "0644",
    },
    "portal_bot/ru_probe_contract.py": {
        "install_path": "/opt/pokrov/portal_bot/ru_probe_contract.py",
        "mode": "0644",
    },
    "infra/pokrov-ru-probe.service": {
        "install_path": "/etc/systemd/system/pokrov-ru-probe.service",
        "mode": "0644",
    },
    "infra/pokrov-ru-probe.timer": {
        "install_path": "/etc/systemd/system/pokrov-ru-probe.timer",
        "mode": "0644",
    },
    "infra/pokrov-ru-probe-uploader.service": {
        "install_path": "/etc/systemd/system/pokrov-ru-probe-uploader.service",
        "mode": "0644",
    },
    "infra/pokrov-ru-probe-uploader.timer": {
        "install_path": "/etc/systemd/system/pokrov-ru-probe-uploader.timer",
        "mode": "0644",
    },
}

RUNTIME_MATERIAL_NAMES = (
    "probe.env",
    "uploader.env",
    "hmac.key",
    "profiles.json",
)


class RuProbeBundleError(RuntimeError):
    """Raised when a bundle is incomplete, mutable, or not candidate-bound."""


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(dict(value), ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _validate_source_revision(value: str) -> str:
    revision = str(value or "").strip().lower()
    if REVISION_RE.fullmatch(revision) is None:
        raise RuProbeBundleError("source_revision_invalid")
    if revision not in APPROVED_SOURCE_REVISIONS:
        raise RuProbeBundleError("source_revision_not_approved_candidate")
    return revision


def _candidate_id(source_revision: str) -> str:
    revision = _validate_source_revision(source_revision)
    return APPROVED_SOURCE_REVISIONS[revision]


def _run_git(repo_root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuProbeBundleError("source_git_read_failed")
    return bytes(result.stdout)


def _source_epoch(repo_root: Path, revision: str) -> int:
    raw = _run_git(repo_root, "show", "-s", "--format=%ct", revision)
    try:
        value = int(raw.decode("ascii").strip())
    except (UnicodeError, ValueError) as exc:
        raise RuProbeBundleError("source_epoch_invalid") from exc
    if value <= 0:
        raise RuProbeBundleError("source_epoch_invalid")
    return value


def _git_blob(repo_root: Path, revision: str, path: str) -> bytes:
    value = _run_git(repo_root, "show", f"{revision}:{path}")
    if not value:
        raise RuProbeBundleError(f"source_member_empty:{path}")
    return value


def _validate_python_member(path: str, value: bytes) -> None:
    try:
        text = value.decode("utf-8")
    except UnicodeError as exc:
        raise RuProbeBundleError(f"source_member_not_utf8:{path}") from exc
    if text.startswith("\ufeff") or "\r" in text:
        raise RuProbeBundleError(f"source_member_not_canonical:{path}")
    try:
        compile(text, path, "exec")
    except SyntaxError as exc:
        raise RuProbeBundleError(f"source_member_not_python:{path}") from exc


def _validate_unit_contract(path: str, value: bytes) -> None:
    try:
        text = value.decode("utf-8")
    except UnicodeError as exc:
        raise RuProbeBundleError(f"unit_not_utf8:{path}") from exc
    required: list[str] = []
    if path.endswith(".service"):
        required.extend(
            [
                "User=pokrov-ru-probe",
                "Group=pokrov-ru-probe",
                "UMask=0077",
                "NoNewPrivileges=true",
                "ProtectSystem=strict",
                "ReadWritePaths=/var/lib/pokrov-ru-probe",
            ]
        )
    elif path.endswith("pokrov-ru-probe.timer"):
        required.extend(["OnCalendar=*-*-* 00,06,12,18:00:00", "Persistent=true"])
    elif path.endswith("pokrov-ru-probe-uploader.timer"):
        required.extend(["OnUnitActiveSec=15m", "Persistent=true"])
    if any(token not in text for token in required):
        raise RuProbeBundleError(f"unit_contract_mismatch:{path}")


def _validate_source_members(members: Mapping[str, bytes]) -> None:
    if set(members) != set(SOURCE_MEMBERS):
        raise RuProbeBundleError("source_member_set_mismatch")
    for path, value in members.items():
        if not isinstance(value, bytes) or not value:
            raise RuProbeBundleError(f"source_member_invalid:{path}")
        if path.endswith(".py"):
            _validate_python_member(path, value)
        else:
            _validate_unit_contract(path, value)
    hmac_client = members["scripts/internal_hmac_client.py"].decode("utf-8")
    if "from internal_request_auth import" not in hmac_client:
        raise RuProbeBundleError("internal_request_auth_dependency_missing")


def _manifest(
    *,
    source_revision: str,
    source_epoch: int,
    members: Mapping[str, bytes],
) -> dict[str, Any]:
    _validate_source_revision(source_revision)
    _validate_source_members(members)
    source_time = (
        datetime.fromtimestamp(source_epoch, tz=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )
    return {
        "schema_version": BUNDLE_SCHEMA,
        "state": "exact_candidate_source_no_runtime_material",
        "source": {
            "repository": "Kiwunaka/portal",
            "revision": source_revision,
            "source_epoch": source_epoch,
            "source_time_utc": source_time,
        },
        "members": {
            path: {
                "install_path": SOURCE_MEMBERS[path]["install_path"],
                "mode": SOURCE_MEMBERS[path]["mode"],
                "sha256": _sha256(value),
                "size_bytes": len(value),
            }
            for path, value in sorted(members.items())
        },
        "runtime": {
            "user": "pokrov-ru-probe",
            "config_root": "/etc/pokrov-ru-probe",
            "spool_root": "/var/lib/pokrov-ru-probe",
            "runtime_material_names": list(RUNTIME_MATERIAL_NAMES),
            "runner_schedule_utc": "00,06,12,18",
            "uploader_interval_minutes": 15,
        },
        "raw_runtime_material_included": False,
        "deployment_performed": False,
        "evidence_ceiling": "IMMUTABLE_LOCAL_BUNDLE_ONLY_UNTIL_AUTHORIZED_INSTALL_RUN_UPLOAD_AND_READBACK",
    }


def _zip_datetime(source_epoch: int) -> tuple[int, int, int, int, int, int]:
    dt = datetime.fromtimestamp(source_epoch, tz=timezone.utc)
    year = min(2107, max(1980, dt.year))
    return year, dt.month, dt.day, dt.hour, dt.minute, dt.second - dt.second % 2


def _zip_info(path: str, *, source_epoch: int, mode: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(path, _zip_datetime(source_epoch))
    info.create_system = 3
    info.external_attr = (int(mode, 8) & 0xFFFF) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    return info


def _write_bundle(
    output: Path,
    *,
    manifest: Mapping[str, Any],
    members: Mapping[str, bytes],
) -> None:
    source_epoch = int((manifest.get("source") or {}).get("source_epoch") or 0)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    try:
        with zipfile.ZipFile(
            temporary,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            archive.writestr(
                _zip_info(MANIFEST_NAME, source_epoch=source_epoch, mode="0644"),
                _canonical_json(manifest),
            )
            for path in sorted(members):
                archive.writestr(
                    _zip_info(
                        path,
                        source_epoch=source_epoch,
                        mode=str(SOURCE_MEMBERS[path]["mode"]),
                    ),
                    members[path],
                )
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)


def _safe_archive_name(name: str) -> bool:
    path = PurePosixPath(name)
    return bool(name and not path.is_absolute() and ".." not in path.parts)


def verify_bundle(path: Path) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(path, "r") as archive:
            infos = archive.infolist()
            names = [item.filename for item in infos]
            if len(names) != len(set(names)) or any(
                not _safe_archive_name(name) for name in names
            ):
                raise RuProbeBundleError("bundle_member_name_invalid")
            expected = {MANIFEST_NAME, *SOURCE_MEMBERS}
            if set(names) != expected:
                raise RuProbeBundleError("bundle_member_set_mismatch")
            manifest_raw = archive.read(MANIFEST_NAME)
            try:
                manifest = json.loads(manifest_raw.decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise RuProbeBundleError("bundle_manifest_invalid") from exc
            if not isinstance(manifest, dict):
                raise RuProbeBundleError("bundle_manifest_invalid")
            source = manifest.get("source")
            if (
                manifest.get("schema_version") != BUNDLE_SCHEMA
                or manifest.get("state") != "exact_candidate_source_no_runtime_material"
                or manifest.get("raw_runtime_material_included") is not False
                or manifest.get("deployment_performed") is not False
                or not isinstance(source, Mapping)
            ):
                raise RuProbeBundleError("bundle_manifest_contract_mismatch")
            _validate_source_revision(str(source.get("revision") or ""))
            source_epoch = int(source.get("source_epoch") or 0)
            declared = manifest.get("members")
            if not isinstance(declared, Mapping) or set(declared) != set(SOURCE_MEMBERS):
                raise RuProbeBundleError("bundle_manifest_members_invalid")
            members: dict[str, bytes] = {}
            for member_path, contract in SOURCE_MEMBERS.items():
                value = archive.read(member_path)
                row = declared.get(member_path)
                if not isinstance(row, Mapping):
                    raise RuProbeBundleError("bundle_manifest_members_invalid")
                info = archive.getinfo(member_path)
                actual_mode = f"{(info.external_attr >> 16) & 0o7777:04o}"
                if (
                    row.get("install_path") != contract["install_path"]
                    or row.get("mode") != contract["mode"]
                    or row.get("sha256") != _sha256(value)
                    or row.get("size_bytes") != len(value)
                    or actual_mode != contract["mode"]
                ):
                    raise RuProbeBundleError(f"bundle_member_digest_or_mode_mismatch:{member_path}")
                members[member_path] = value
            _validate_source_members(members)
            if source_epoch <= 0 or manifest_raw != _canonical_json(manifest):
                raise RuProbeBundleError("bundle_manifest_not_canonical")
            if any(name in names for name in RUNTIME_MATERIAL_NAMES):
                raise RuProbeBundleError("bundle_contains_runtime_material")
            return manifest
    except (OSError, zipfile.BadZipFile) as exc:
        raise RuProbeBundleError("bundle_invalid") from exc


def build_bundle(*, repo_root: Path, source_revision: str, output: Path) -> dict[str, Any]:
    revision = _validate_source_revision(source_revision)
    members = {
        path: _git_blob(repo_root, revision, path) for path in SOURCE_MEMBERS
    }
    manifest = _manifest(
        source_revision=revision,
        source_epoch=_source_epoch(repo_root, revision),
        members=members,
    )
    _write_bundle(output, manifest=manifest, members=members)
    verified = verify_bundle(output)
    return _report(path=output, manifest=verified, mode="BUILD")


def _report(*, path: Path, manifest: Mapping[str, Any], mode: str) -> dict[str, Any]:
    return {
        "schema_version": BUNDLE_SCHEMA,
        "mode": mode,
        "ok": True,
        "candidate_id": _candidate_id(
            str((manifest.get("source") or {}).get("revision") or "")
        ),
        "source_revision": (manifest.get("source") or {}).get("revision"),
        "member_count": len(SOURCE_MEMBERS),
        "bundle_size_bytes": path.stat().st_size,
        "bundle_sha256": _sha256(path.read_bytes()),
        "raw_runtime_material_included": False,
        "deployment_performed": False,
    }


def plan_bundle(*, path: Path, operation: str) -> dict[str, Any]:
    manifest = verify_bundle(path)
    if operation not in {"install", "rollback"}:
        raise RuProbeBundleError("operation_invalid")
    actions = (
        [
            "verify_exact_candidate_bundle_and_remote_identity",
            "verify_private_receipt_bound_runtime_material",
            "retain_previous_files_units_timer_states_and_spool_metadata",
            "install_unprivileged_user_exact_sources_units_and_private_config",
            "daemon_reload_and_verify_units_before_enabling_timers",
            "enable_timers_only_after_source_mode_and_config_readback",
            "manual_runner_uploader_heartbeat_and_admin_readback_remain_separate",
        ]
        if operation == "install"
        else [
            "stop_and_disable_probe_timers_without_deleting_spool",
            "retain_pending_blocked_quarantine_archive_and_manifest_cache",
            "restore_exact_receipt_bound_files_units_and_timer_states",
            "daemon_reload_and_verify_stale_or_missing_status_is_honest",
        ]
    )
    return {
        **_report(path=path, manifest=manifest, mode="PLAN"),
        "operation": operation,
        "ordered_actions": actions,
        "runtime_material_required": True,
        "manual_run_upload_heartbeat_admin_readback_required": True,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    build.add_argument("--source-revision", required=True)
    build.add_argument("--output", type=Path, required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--bundle", type=Path, required=True)
    plan = subparsers.add_parser("plan")
    plan.add_argument("--bundle", type=Path, required=True)
    plan.add_argument("--operation", choices=("install", "rollback"), required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "build":
            report = build_bundle(
                repo_root=args.repo_root.resolve(),
                source_revision=args.source_revision,
                output=args.output.resolve(),
            )
        elif args.command == "verify":
            path = args.bundle.resolve(strict=True)
            report = _report(path=path, manifest=verify_bundle(path), mode="VERIFY")
        else:
            path = args.bundle.resolve(strict=True)
            report = plan_bundle(path=path, operation=args.operation)
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (OSError, RuProbeBundleError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "schema_version": BUNDLE_SCHEMA,
                    "mode": str(getattr(args, "command", "ERROR")).upper(),
                    "ok": False,
                    "error": str(exc),
                    "raw_runtime_material_included": False,
                    "deployment_performed": False,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
