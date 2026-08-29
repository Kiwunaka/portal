#!/usr/bin/env python3
"""Inspect the canonical RU-origin probe environment without mutating it."""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
from typing import Any, Mapping

from node_access import DEFAULT_PASSWORDS, connect_node
from node_inventory import DEFAULT_INVENTORY, inventory_ipv4_map
from ssh_host_keys import OpenSshConfigSession


REPO_ROOT = Path(__file__).resolve().parents[1]
FULL_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
UTC_TEXT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T[^ ]{1,48}$")
REMOTE_SCHEMA = "pokrov-ru-origin-environment-remote-v1"
REPORT_SCHEMA = "pokrov-ru-origin-environment-probe-v1"
NORMALIZATION_RULE = "CRLF_TO_LF_ONLY"

SOURCE_MAPPINGS = (
    ("scripts/ru_probe_runner.py", "/opt/pokrov/scripts/ru_probe_runner.py"),
    ("scripts/ru_probe_uploader.py", "/opt/pokrov/scripts/ru_probe_uploader.py"),
    ("scripts/internal_hmac_client.py", "/opt/pokrov/scripts/internal_hmac_client.py"),
    ("scripts/node_dataplane_probe.py", "/opt/pokrov/scripts/node_dataplane_probe.py"),
    ("portal_bot/ru_probe_contract.py", "/opt/pokrov/portal_bot/ru_probe_contract.py"),
    ("infra/pokrov-ru-probe.service", "/etc/systemd/system/pokrov-ru-probe.service"),
    ("infra/pokrov-ru-probe.timer", "/etc/systemd/system/pokrov-ru-probe.timer"),
    (
        "infra/pokrov-ru-probe-uploader.service",
        "/etc/systemd/system/pokrov-ru-probe-uploader.service",
    ),
    (
        "infra/pokrov-ru-probe-uploader.timer",
        "/etc/systemd/system/pokrov-ru-probe-uploader.timer",
    ),
)

REQUIRED_UNITS = (
    "pokrov-ru-probe.service",
    "pokrov-ru-probe.timer",
    "pokrov-ru-probe-uploader.service",
    "pokrov-ru-probe-uploader.timer",
)

REMOTE_SCRIPT = r"""
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import stat
import subprocess

request = REQUEST


def sha256(value):
    return hashlib.sha256(value).hexdigest()


def command(argv):
    try:
        result = subprocess.run(argv, check=False, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return 255, ""
    return int(result.returncode), str(result.stdout or "").strip()


def safe_state(value, allowed):
    return value if value in allowed else "unknown"


files = []
for row in request.get("files", []):
    index = int(row["index"])
    path = str(row["path"])
    try:
        metadata = os.lstat(path)
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            files.append({"index": index, "exists": True, "readable": False})
            continue
        with open(path, "rb") as handle:
            value = handle.read()
    except (OSError, IOError):
        files.append({"index": index, "exists": os.path.exists(path), "readable": False})
        continue
    files.append(
        {
            "index": index,
            "exists": True,
            "readable": True,
            "raw_sha256": sha256(value),
            "normalized_sha256": sha256(value.replace(b"\r\n", b"\n")),
            "mode": format(stat.S_IMODE(metadata.st_mode), "03o"),
        }
    )


units = {}
for unit in request.get("units", []):
    _, load = command(["systemctl", "show", unit, "--property=LoadState", "--value"])
    _, active = command(["systemctl", "is-active", unit])
    _, enabled = command(["systemctl", "is-enabled", unit])
    _, result = command(["systemctl", "show", unit, "--property=Result", "--value"])
    units[unit] = {
        "load": safe_state(load, {"loaded", "not-found", "masked"}),
        "active": safe_state(active, {"active", "inactive", "failed", "activating", "deactivating"}),
        "enabled": safe_state(enabled, {"enabled", "disabled", "static", "masked", "indirect"}),
        "result": safe_state(result, {"success", "exit-code", "signal", "timeout", "start-limit-hit"}),
    }


def metadata(path, *, directory=False):
    try:
        value = os.stat(path, follow_symlinks=False)
    except OSError:
        return {"exists": False, "metadata_available": False, "mode": "", "private": False}
    expected_type = stat.S_ISDIR(value.st_mode) if directory else stat.S_ISREG(value.st_mode)
    mode = stat.S_IMODE(value.st_mode)
    return {
        "exists": bool(expected_type),
        "metadata_available": True,
        "mode": format(mode, "03o"),
        "private": bool(expected_type and mode & 0o077 == 0),
    }


config = {
    "probe_env": metadata("/etc/pokrov-ru-probe/probe.env"),
    "uploader_env": metadata("/etc/pokrov-ru-probe/uploader.env"),
    "hmac_key": metadata("/etc/pokrov-ru-probe/hmac.key"),
    "profiles": metadata("/etc/pokrov-ru-probe/profiles.json"),
}
spool = metadata("/var/lib/pokrov-ru-probe", directory=True)
counts = {}
for state_name in ("pending", "blocked", "quarantine", "archive"):
    state_path = os.path.join("/var/lib/pokrov-ru-probe", state_name)
    if not spool["exists"]:
        counts[state_name] = None
        continue
    try:
        names = os.listdir(state_path)
    except OSError:
        counts[state_name] = None
        continue
    counts[state_name] = sum(
        1
        for name in names
        if name.endswith(".json")
        and not name.endswith((".reason.json", ".retry.json"))
        and not name.startswith(".")
    )
spool["counts"] = counts


latest = {
    "available": False,
    "schema_version": None,
    "origin_ru": False,
    "run_id_sha256": "",
    "manifest_revision": "",
    "finished_at": "",
    "age_seconds": None,
    "execution_status": "",
    "evidence_code": "",
    "target_count": 0,
    "stage_status_counts": {"pass": 0, "fail": 0, "not_run": 0},
}
archive_path = "/var/lib/pokrov-ru-probe/archive"
try:
    archive_metadata = os.lstat(archive_path)
    if stat.S_ISLNK(archive_metadata.st_mode) or not stat.S_ISDIR(archive_metadata.st_mode):
        raise OSError("archive is not a real directory")
    candidates = [
        os.path.join(archive_path, name)
        for name in os.listdir(archive_path)
        if name.endswith(".json") and not name.startswith(".")
    ]
    latest_path = max(candidates, key=os.path.getmtime) if candidates else ""
    if latest_path:
        with open(latest_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        run_id = str(payload.get("run_id") or "")
        finished_at = str(payload.get("finished_at") or "")
        age_seconds = None
        try:
            finished = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
            age_seconds = max(0, int((datetime.now(timezone.utc) - finished).total_seconds()))
        except (TypeError, ValueError):
            pass
        status_counts = {"pass": 0, "fail": 0, "not_run": 0}
        targets = payload.get("targets") if isinstance(payload.get("targets"), list) else []
        for target in targets:
            stages = target.get("stages") if isinstance(target, dict) else None
            if not isinstance(stages, dict):
                continue
            for stage in stages.values():
                status_value = stage.get("status") if isinstance(stage, dict) else None
                if status_value in status_counts:
                    status_counts[status_value] += 1
        manifest_revision = str(payload.get("manifest_revision") or "")
        latest = {
            "available": True,
            "schema_version": payload.get("schema_version"),
            "origin_ru": payload.get("origin") == "ru",
            "run_id_sha256": sha256(run_id.encode("utf-8")) if run_id else "",
            "manifest_revision": manifest_revision if re.fullmatch(r"[0-9a-f]{64}", manifest_revision) else "",
            "finished_at": finished_at if re.fullmatch(r"\d{4}-\d{2}-\d{2}T[^ ]+", finished_at) else "",
            "age_seconds": age_seconds,
            "execution_status": safe_state(str(payload.get("execution_status") or ""), {"complete", "partial", "runner_error"}),
            "evidence_code": safe_state(str(payload.get("evidence_code") or ""), {"", "network_access_blocked", "probe_host_unavailable", "probe_host_credentials_missing", "probe_profile_unavailable"}),
            "target_count": len(targets),
            "stage_status_counts": status_counts,
        }
except (OSError, ValueError, TypeError, json.JSONDecodeError):
    pass


_, ntp = command(["timedatectl", "show", "--property=NTPSynchronized", "--value"])
print(
    json.dumps(
        {
            "schema": "pokrov-ru-origin-environment-remote-v1",
            "files": files,
            "units": units,
            "config": config,
            "spool": spool,
            "latest_archive": latest,
            "clock": {"ntp_synchronized": safe_state(ntp, {"yes", "no"})},
        },
        separators=(",", ":"),
        sort_keys=True,
    )
)
"""


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _normalize_crlf(value: bytes) -> bytes:
    return value.replace(b"\r\n", b"\n")


def _resolve_source_revision(repo_root: Path, value: str) -> str:
    revision = str(value or "").strip()
    if FULL_COMMIT_RE.fullmatch(revision) is None:
        raise ValueError("--source-revision must be a full lowercase Git commit")
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--verify", f"{revision}^{{commit}}"],
        check=False,
        capture_output=True,
        text=True,
    )
    resolved = result.stdout.strip().lower()
    if result.returncode != 0 or resolved != revision:
        raise ValueError("--source-revision is not an exact local commit")
    return revision


def _git_blob(repo_root: Path, revision: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{revision}:{path}"],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise ValueError(f"source revision does not contain required path: {path}")
    return result.stdout


def _remote_command(request: Mapping[str, Any]) -> str:
    request_b64 = base64.b64encode(
        json.dumps(request, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).decode("ascii")
    script_b64 = base64.b64encode(REMOTE_SCRIPT.encode("utf-8")).decode("ascii")
    code = (
        "import base64,json;"
        f'REQUEST=json.loads(base64.b64decode("{request_b64}"));'
        f'exec(base64.b64decode("{script_b64}"))'
    )
    return "python3 -c " + shlex.quote(code)


def _execute(session: Any, command: str, *, timeout: int = 120) -> tuple[int, str]:
    if isinstance(session, OpenSshConfigSession):
        result = session.run(command, timeout=timeout)
        return int(result.returncode), str(result.stdout or "")
    _stdin, stdout, _stderr = session.exec_command(command, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    return int(code), stdout.read().decode("utf-8", errors="replace")


def _probe(session: Any, request: Mapping[str, Any]) -> dict[str, Any]:
    code, output = _execute(session, _remote_command(request), timeout=180)
    if code != 0:
        raise RuntimeError("RU-origin environment probe failed before structured output")
    try:
        response = json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError("RU-origin environment probe returned invalid JSON") from exc
    if not isinstance(response, dict) or response.get("schema") != REMOTE_SCHEMA:
        raise RuntimeError("RU-origin environment probe returned an invalid schema")
    return response


def _safe_mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _safe_state(value: object, allowed: set[str]) -> str:
    text = str(value or "")
    return text if text in allowed else "unknown"


def _safe_hash(value: object) -> str:
    text = str(value or "")
    return text if SHA256_RE.fullmatch(text) is not None else ""


def _safe_nonnegative_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _build_report(
    *,
    source_revision: str,
    auth_method: str,
    source_payload: list[tuple[str, bytes]],
    response: Mapping[str, Any],
    checked_at: str | None = None,
) -> dict[str, Any]:
    raw_files = response.get("files")
    if not isinstance(raw_files, list) or len(raw_files) != len(source_payload):
        raise ValueError("remote file result is incomplete")
    by_index: dict[int, dict[str, Any]] = {}
    for raw in raw_files:
        if not isinstance(raw, Mapping):
            raise ValueError("remote file row is invalid")
        try:
            index = int(raw["index"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("remote file row index is invalid") from exc
        if index in by_index or not 0 <= index < len(source_payload):
            raise ValueError("remote file row index is invalid")
        by_index[index] = dict(raw)
    if len(by_index) != len(source_payload):
        raise ValueError("remote file result is incomplete")

    files: list[dict[str, Any]] = []
    for index, (source_path, source_bytes) in enumerate(source_payload):
        remote = by_index[index]
        raw_match = remote.get("raw_sha256") == _sha256(source_bytes)
        normalized_match = remote.get("normalized_sha256") == _sha256(_normalize_crlf(source_bytes))
        classification = (
            "EXACT_BYTES"
            if raw_match
            else "CRLF_ONLY_DIFFERENCE"
            if normalized_match
            else "NOT_INSTALLED"
            if remote.get("exists") is not True
            else "UNREADABLE"
            if remote.get("readable") is not True
            else "CONTENT_MISMATCH"
        )
        files.append(
            {
                "source_path": source_path,
                "raw_match": raw_match,
                "crlf_normalized_match": normalized_match,
                "classification": classification,
            }
        )

    units = _safe_mapping(response.get("units"))
    config = _safe_mapping(response.get("config"))
    spool = _safe_mapping(response.get("spool"))
    latest = _safe_mapping(response.get("latest_archive"))
    clock = _safe_mapping(response.get("clock"))
    unit_rows = {
        unit: {
            "load": _safe_state(_safe_mapping(units.get(unit)).get("load"), {"loaded", "not-found", "masked"}),
            "active": _safe_state(
                _safe_mapping(units.get(unit)).get("active"),
                {"active", "inactive", "failed", "activating", "deactivating"},
            ),
            "enabled": _safe_state(
                _safe_mapping(units.get(unit)).get("enabled"),
                {"enabled", "disabled", "static", "masked", "indirect"},
            ),
            "result": _safe_state(
                _safe_mapping(units.get(unit)).get("result"),
                {"success", "exit-code", "signal", "timeout", "start-limit-hit"},
            ),
        }
        for unit in REQUIRED_UNITS
    }
    config_rows = {
        name: {
            "exists": _safe_mapping(config.get(name)).get("exists") is True,
            "metadata_available": _safe_mapping(config.get(name)).get("metadata_available") is True,
            "private": _safe_mapping(config.get(name)).get("private") is True,
        }
        for name in ("probe_env", "uploader_env", "hmac_key", "profiles")
    }
    spool_counts = _safe_mapping(spool.get("counts"))
    spool_row = {
        "exists": spool.get("exists") is True,
        "metadata_available": spool.get("metadata_available") is True,
        "private": spool.get("private") is True,
        "counts": {
            state: _safe_nonnegative_int(spool_counts.get(state))
            for state in ("pending", "blocked", "quarantine", "archive")
        },
    }

    files_exact = all(row["crlf_normalized_match"] for row in files)
    timers_ready = all(
        unit_rows[unit]["load"] == "loaded"
        and unit_rows[unit]["active"] == "active"
        and unit_rows[unit]["enabled"] == "enabled"
        for unit in ("pokrov-ru-probe.timer", "pokrov-ru-probe-uploader.timer")
    )
    configs_ready = all(row["exists"] and row["metadata_available"] and row["private"] for row in config_rows.values())
    spool_ready = spool_row["exists"] and spool_row["metadata_available"] and spool_row["private"]
    ntp_ready = clock.get("ntp_synchronized") == "yes"
    environment_present = any(row["classification"] != "NOT_INSTALLED" for row in files) or any(
        row["load"] != "not-found" for row in unit_rows.values()
    ) or any(row["exists"] for row in config_rows.values()) or spool_row["exists"]
    ready_for_manual_owner_run = files_exact and timers_ready and configs_ready and spool_ready and ntp_ready
    latest_age = _safe_nonnegative_int(latest.get("age_seconds"))
    if not environment_present:
        classification = "MANUAL_OWNER_TEST_ENVIRONMENT_NOT_INSTALLED"
    elif not ready_for_manual_owner_run:
        classification = "MANUAL_OWNER_TEST_ENVIRONMENT_INCOMPLETE"
    elif latest.get("available") is not True or latest_age is None or latest_age > 25200:
        classification = "MANUAL_OWNER_TEST_FRESH_RUN_REQUIRED"
    else:
        classification = "MANUAL_OWNER_TEST_SERVER_READBACK_REQUIRED"

    latest_finished_at = str(latest.get("finished_at") or "")
    if UTC_TEXT_RE.fullmatch(latest_finished_at) is None:
        latest_finished_at = ""
    latest_stage_counts = _safe_mapping(latest.get("stage_status_counts"))

    return {
        "schema_version": REPORT_SCHEMA,
        "checked_at": checked_at or datetime.now(timezone.utc).isoformat(),
        "origin": "ru",
        "probe_host_class": "canonical_ru_sandbox",
        "source_revision": source_revision,
        "mode": "READ_ONLY_REMOTE_HASHES_AND_STATE",
        "auth_method": "ssh_config" if auth_method == "ssh_config" else "key" if auth_method.startswith("key") else "password",
        "classification": classification,
        "ru_origin_status": "MANUAL_OWNER_TEST",
        "ru_origin_passed": False,
        "probe_completed": True,
        "ready_for_manual_owner_run": ready_for_manual_owner_run,
        "source_files": files,
        "source_summary": {
            "required": len(files),
            "normalized_match_count": sum(1 for row in files if row["crlf_normalized_match"]),
            "not_installed_count": sum(1 for row in files if row["classification"] == "NOT_INSTALLED"),
            "mismatch_or_unreadable_count": sum(
                1
                for row in files
                if row["classification"] not in {"EXACT_BYTES", "CRLF_ONLY_DIFFERENCE", "NOT_INSTALLED"}
            ),
        },
        "units": unit_rows,
        "config": config_rows,
        "spool": spool_row,
        "latest_archive": {
            "available": latest.get("available") is True,
            "schema_version": latest.get("schema_version"),
            "origin_ru": latest.get("origin_ru") is True,
            "run_id_sha256": _safe_hash(latest.get("run_id_sha256")),
            "manifest_revision": _safe_hash(latest.get("manifest_revision")),
            "finished_at": latest_finished_at,
            "age_seconds": latest_age,
            "execution_status": _safe_state(latest.get("execution_status"), {"complete", "partial", "runner_error"}),
            "evidence_code": _safe_state(
                latest.get("evidence_code"),
                {
                    "",
                    "network_access_blocked",
                    "probe_host_unavailable",
                    "probe_host_credentials_missing",
                    "probe_profile_unavailable",
                },
            ),
            "target_count": _safe_nonnegative_int(latest.get("target_count")) or 0,
            "stage_status_counts": {
                state: _safe_nonnegative_int(latest_stage_counts.get(state)) or 0
                for state in ("pass", "fail", "not_run")
            },
        },
        "clock": {"ntp_synchronized": str(clock.get("ntp_synchronized") or "unknown")},
        "server_readback_performed": False,
        "heartbeat_readback_performed": False,
        "remote_content_retained": False,
        "runtime_mutated": False,
        "ok": ready_for_manual_owner_run,
    }


def _blocked_report(source_revision: str, *, checked_at: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": REPORT_SCHEMA,
        "checked_at": checked_at or datetime.now(timezone.utc).isoformat(),
        "origin": "ru",
        "probe_host_class": "canonical_ru_sandbox",
        "source_revision": source_revision,
        "mode": "READ_ONLY_REMOTE_HASHES_AND_STATE",
        "auth_method": "none",
        "classification": "BLOCKED_BY_ACCESS",
        "ru_origin_status": "BLOCKED_BY_ACCESS",
        "ru_origin_passed": False,
        "probe_completed": False,
        "ready_for_manual_owner_run": False,
        "server_readback_performed": False,
        "heartbeat_readback_performed": False,
        "remote_content_retained": False,
        "runtime_mutated": False,
        "ok": False,
    }


def _harness_error_report(source_revision: str, *, checked_at: str | None = None) -> dict[str, Any]:
    report = _blocked_report(source_revision, checked_at=checked_at)
    report.update(
        {
            "classification": "MANUAL_OWNER_TEST_HARNESS_ERROR",
            "ru_origin_status": "MANUAL_OWNER_TEST",
        }
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--node-code", default="mini")
    parser.add_argument("--node-host", default="")
    parser.add_argument("--inventory", default=str(DEFAULT_INVENTORY))
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--ssh-config-alias", default="")
    parser.add_argument("--ssh-config", default="")
    parser.add_argument("--json-out", default="")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    try:
        source_revision = _resolve_source_revision(repo_root, args.source_revision)
        source_payload = [
            (source_path, _git_blob(repo_root, source_revision, source_path))
            for source_path, _remote_path in SOURCE_MAPPINGS
        ]
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    request = {
        "schema": REMOTE_SCHEMA,
        "files": [
            {"index": index, "path": remote_path}
            for index, (_source_path, remote_path) in enumerate(SOURCE_MAPPINGS)
        ],
        "units": list(REQUIRED_UNITS),
    }
    session: Any | None = None
    try:
        if args.ssh_config_alias:
            session = OpenSshConfigSession(
                alias=args.ssh_config_alias,
                config_path=Path(args.ssh_config).expanduser() if args.ssh_config else None,
            )
            auth_method = "ssh_config"
        else:
            inventory = inventory_ipv4_map(Path(args.inventory))
            node_code = str(args.node_code or "mini").strip().lower()
            node_host = str(args.node_host or "").strip() or inventory.get(node_code, "")
            if not node_host:
                raise RuntimeError("RU-origin node is absent from the selected inventory")
            session, auth_method = connect_node(
                code=node_code,
                host=node_host,
                user=args.ssh_user,
                port=int(args.ssh_port),
                passwords_path=Path(args.passwords),
                key_dir=Path(args.passwords).parent,
            )
    except Exception:
        report = _blocked_report(source_revision)
    else:
        try:
            response = _probe(session, request)
            report = _build_report(
                source_revision=source_revision,
                auth_method=auth_method,
                source_payload=source_payload,
                response=response,
            )
        except Exception:
            report = _harness_error_report(source_revision)
    finally:
        if session is not None:
            session.close()

    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.json_out:
        output_path = Path(args.json_out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(encoded, encoding="utf-8")
        print(output_path)
    else:
        print(encoded, end="")
    return 0 if report["ready_for_manual_owner_run"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
