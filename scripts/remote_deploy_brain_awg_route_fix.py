from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from node_access import connect_node
from remote_brain_runtime_source_probe import _compare_bytes, _git_blob, _safe_auth_method
from remote_deploy_brain_portal_code import (
    DEFAULT_BACKUP_RETENTION_COUNT,
    DEFAULT_PASSWORDS,
    REMOTE_BACKUP_ROOT,
    REMOTE_STAGE_ROOT,
    REPO_ROOT,
    _build_backup_command,
    _build_backup_prune_command,
    _build_clean_restart_command,
    _build_post_restart_verify_command,
    _build_prepare_command,
    _build_restore_command,
    _q,
    _release_id,
    _run,
    _run_checked,
    iter_upload_mappings,
)


EXPECTED_BRAIN_IP = "82.21.114.104"
EXPECTED_SSH_PORT = 29374
EXPECTED_LIVE_REVISION = "e5ef03ac7ab013d8810cc9c6ea9ccc40cebd11db"
EXPECTED_CANDIDATE_REVISION = "83502f1cb9a54ce7ae088a36ed2f9e696c90d841"
TARGET_RELATIVE_PATH = "portal_bot/api_client_routes.py"
TARGET_REMOTE_PATH = "/root/portal_bot/api_client_routes.py"
RESTART_UNIT = "portal-api"
APPLY_CONFIRMATION = "AWG_ONE_FILE_83502F1_PORTAL_API"
EXPECTED_PAYLOAD_COUNT = 193
EXPECTED_LIVE_TARGET_SHA256 = (
    "a6ad4c9153c0ba9ffde677b6ea8709b3ba44c1540f4af15cae25f66465cae08c"
)
EXPECTED_CANDIDATE_TARGET_SHA256 = (
    "ba6cbb3613028aad059bf0ebb81e77a819bbd2440743e33f79b845c4560107fa"
)


def _normalize(value: bytes) -> bytes:
    return value.replace(b"\r\n", b"\n")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(_normalize(value)).hexdigest()


def _source_payload(repo_root: Path, revision: str) -> list[tuple[str, str, bytes]]:
    payload: list[tuple[str, str, bytes]] = []
    for source_path, remote_target in iter_upload_mappings(repo_root):
        relative_path = source_path.relative_to(repo_root).as_posix()
        payload.append(
            (relative_path, remote_target, _git_blob(repo_root, revision, relative_path))
        )
    return payload


def _semantic_delta_targets(
    live_payload: list[tuple[str, str, bytes]],
    candidate_payload: list[tuple[str, str, bytes]],
) -> list[str]:
    live = {(relative, target): _normalize(value) for relative, target, value in live_payload}
    candidate = {
        (relative, target): _normalize(value)
        for relative, target, value in candidate_payload
    }
    if live.keys() != candidate.keys():
        raise ValueError("live and candidate deploy payload shapes differ")
    return [
        relative
        for (relative, target), value in candidate.items()
        if value != live[(relative, target)]
    ]


def _audit_payload(sftp: Any, payload: list[tuple[str, str, bytes]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relative_path, remote_target, source_bytes in payload:
        try:
            with sftp.open(remote_target, "rb") as remote_file:
                remote_bytes = remote_file.read()
        except (OSError, IOError):
            rows.append(
                {
                    "source_path": relative_path,
                    "remote_target": remote_target,
                    "raw_match": False,
                    "crlf_normalized_match": False,
                    "classification": "REMOTE_UNREADABLE",
                }
            )
            continue
        rows.append(
            {
                "source_path": relative_path,
                "remote_target": remote_target,
                **_compare_bytes(source_bytes, remote_bytes),
            }
        )
    return rows


def _mismatch_rows(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "source_path": str(row["source_path"]),
            "remote_target": str(row["remote_target"]),
            "classification": str(row["classification"]),
        }
        for row in rows
        if row.get("crlf_normalized_match") is not True
    ]


def _candidate_target_blob(payload: list[tuple[str, str, bytes]]) -> bytes:
    matches = [
        value
        for relative, target, value in payload
        if relative == TARGET_RELATIVE_PATH and target == TARGET_REMOTE_PATH
    ]
    if len(matches) != 1:
        raise ValueError("candidate payload does not contain the exact AWG route target")
    if _sha256(matches[0]) != EXPECTED_CANDIDATE_TARGET_SHA256:
        raise ValueError("candidate AWG route target digest does not match the reviewed bytes")
    return matches[0]


def _live_target_blob(payload: list[tuple[str, str, bytes]]) -> bytes:
    matches = [
        value
        for relative, target, value in payload
        if relative == TARGET_RELATIVE_PATH and target == TARGET_REMOTE_PATH
    ]
    if len(matches) != 1:
        raise ValueError("live payload does not contain the exact AWG route target")
    if _sha256(matches[0]) != EXPECTED_LIVE_TARGET_SHA256:
        raise ValueError("live AWG route target digest does not match the reviewed bytes")
    return matches[0]


def _validate_static_scope(
    live_payload: list[tuple[str, str, bytes]],
    candidate_payload: list[tuple[str, str, bytes]],
) -> bytes:
    if len(live_payload) != EXPECTED_PAYLOAD_COUNT or len(candidate_payload) != EXPECTED_PAYLOAD_COUNT:
        raise ValueError(f"expected exactly {EXPECTED_PAYLOAD_COUNT} deploy payload files")
    deltas = _semantic_delta_targets(live_payload, candidate_payload)
    if deltas != [TARGET_RELATIVE_PATH]:
        raise ValueError(f"expected one AWG route delta, got: {deltas}")
    _live_target_blob(live_payload)
    return _candidate_target_blob(candidate_payload)


def _validate_apply_confirmation(args: argparse.Namespace) -> None:
    if args.brain_ip != EXPECTED_BRAIN_IP:
        raise ValueError("AWG one-file deploy is pinned to the canonical Brain host")
    if args.ssh_port != EXPECTED_SSH_PORT:
        raise ValueError("AWG one-file deploy is pinned to the canonical Brain SSH port")
    if not args.apply:
        return
    if args.confirm != APPLY_CONFIRMATION:
        raise ValueError(f"--apply requires --confirm {APPLY_CONFIRMATION}")
    if args.ssh_user != "root":
        raise ValueError("AWG one-file deploy apply requires the root operator account")


def _build_target_preflight_command(stage_root: str) -> str:
    stage_target = f"{stage_root}/{TARGET_RELATIVE_PATH}"
    return "\n".join(
        [
            "set -e",
            "PY=/root/portal_bot/venv/bin/python",
            'test -x "$PY"',
            f'"$PY" -m py_compile {_q(stage_target)}',
        ]
    )


def _build_guarded_promote_command(stage_root: str) -> str:
    stage_target = f"{stage_root}/{TARGET_RELATIVE_PATH}"
    digest_check = (
        "import hashlib,pathlib; "
        f"value=pathlib.Path({TARGET_REMOTE_PATH!r}).read_bytes().replace(b'\\r\\n',b'\\n'); "
        f"assert hashlib.sha256(value).hexdigest()=={EXPECTED_LIVE_TARGET_SHA256!r}"
    )
    return "\n".join(
        [
            "set -e",
            f"python3 -c {_q(digest_check)}",
            f"install -D -m 0644 {_q(stage_target)} {_q(TARGET_REMOTE_PATH)}",
        ]
    )


def _write_report(path: str, report: dict[str, Any]) -> None:
    if not str(path or "").strip():
        return
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _base_report(*, auth_method: str, mode: str) -> dict[str, Any]:
    return {
        "schema_version": "pokrov-brain-awg-route-one-file-deploy-v1",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "origin": "brain",
        "mode": mode,
        "brain_ip": EXPECTED_BRAIN_IP,
        "expected_live_revision": EXPECTED_LIVE_REVISION,
        "candidate_revision": EXPECTED_CANDIDATE_REVISION,
        "target": TARGET_RELATIVE_PATH,
        "remote_target": TARGET_REMOTE_PATH,
        "expected_live_target_sha256": EXPECTED_LIVE_TARGET_SHA256,
        "candidate_target_sha256": EXPECTED_CANDIDATE_TARGET_SHA256,
        "restart_units": [RESTART_UNIT],
        "payload_count": EXPECTED_PAYLOAD_COUNT,
        "auth_method": _safe_auth_method(auth_method),
        "remote_content_retained": False,
        "runtime_mutated": False,
        "rollback_attempted": False,
        "ok": False,
    }


def _restore_and_audit(
    ssh: Any,
    *,
    backup_root: str,
    live_payload: list[tuple[str, str, bytes]],
    reason: str,
) -> bool:
    targets = [TARGET_REMOTE_PATH]
    if not _run_checked(
        ssh,
        _build_restore_command(targets, backup_root),
        label=f"rollback AWG route target: {reason}",
        timeout=120,
    ):
        return False
    if not _run_checked(
        ssh,
        _build_clean_restart_command(RESTART_UNIT),
        label=f"{RESTART_UNIT} rollback restart",
        timeout=60,
    ):
        return False
    if not _run_checked(
        ssh,
        _build_post_restart_verify_command([RESTART_UNIT]),
        label="rollback delayed service verification",
        timeout=180,
    ):
        return False
    sftp = ssh.open_sftp()
    try:
        return not _mismatch_rows(_audit_payload(sftp, live_payload))
    finally:
        sftp.close()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Plan or apply the exact one-file Brain control-plane fix required "
            "before the owned AWG2/AWG3.1 device matrix."
        )
    )
    parser.add_argument("--brain-ip", default=EXPECTED_BRAIN_IP)
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=EXPECTED_SSH_PORT)
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--json-out", default="")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", default="")
    parser.add_argument(
        "--backup-retain-count",
        type=int,
        default=DEFAULT_BACKUP_RETENTION_COUNT,
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        _validate_apply_confirmation(args)
        live_payload = _source_payload(REPO_ROOT, EXPECTED_LIVE_REVISION)
        candidate_payload = _source_payload(REPO_ROOT, EXPECTED_CANDIDATE_REVISION)
        candidate_target = _validate_static_scope(live_payload, candidate_payload)
        _build_backup_prune_command(args.backup_retain_count)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    ssh, auth_method = connect_node(
        code="brain",
        host=args.brain_ip,
        user=args.ssh_user,
        port=args.ssh_port,
        passwords_path=Path(args.passwords),
    )
    report = _base_report(auth_method=auth_method, mode="APPLY" if args.apply else "PLAN")
    try:
        sftp = ssh.open_sftp()
        try:
            live_rows = _audit_payload(sftp, live_payload)
        finally:
            sftp.close()
        live_mismatches = _mismatch_rows(live_rows)
        report["predeploy_normalized_match_count"] = len(live_rows) - len(live_mismatches)
        report["predeploy_mismatches"] = live_mismatches
        if live_mismatches:
            print(
                "AWG one-file predeploy: FAIL "
                f"({len(live_rows) - len(live_mismatches)}/{len(live_rows)} live baseline matches)"
            )
            _write_report(args.json_out, report)
            return 1

        if not args.apply:
            report["ok"] = True
            print(
                "AWG one-file predeploy: PLAN_READY "
                f"({len(live_rows)}/{len(live_rows)} live baseline matches; runtime_mutated=false)"
            )
            _write_report(args.json_out, report)
            return 0

        release_id = _release_id()
        stage_root = f"{REMOTE_STAGE_ROOT}/{release_id}"
        backup_root = f"{REMOTE_BACKUP_ROOT}/{release_id}"
        mapping = [(REPO_ROOT / TARGET_RELATIVE_PATH, TARGET_REMOTE_PATH)]
        if not _run_checked(
            ssh,
            _build_prepare_command(mapping, stage_root, backup_root),
            label="prepare AWG one-file staging",
            timeout=60,
        ):
            _write_report(args.json_out, report)
            return 1
        if not _run_checked(
            ssh,
            _build_backup_command([TARGET_REMOTE_PATH], backup_root),
            label="backup current AWG route target",
            timeout=120,
        ):
            _write_report(args.json_out, report)
            return 1

        stage_target = f"{stage_root}/{TARGET_RELATIVE_PATH}"
        sftp = ssh.open_sftp()
        try:
            with sftp.open(stage_target, "wb") as staged_file:
                staged_file.write(candidate_target)
        finally:
            sftp.close()
        if not _run_checked(
            ssh,
            _build_target_preflight_command(stage_root),
            label="preflight staged AWG route target",
            timeout=120,
        ):
            _write_report(args.json_out, report)
            return 1

        sftp = ssh.open_sftp()
        try:
            prepromote_rows = _audit_payload(sftp, live_payload)
        finally:
            sftp.close()
        prepromote_mismatches = _mismatch_rows(prepromote_rows)
        report["prepromote_normalized_match_count"] = len(prepromote_rows) - len(
            prepromote_mismatches
        )
        report["prepromote_mismatches"] = prepromote_mismatches
        if prepromote_mismatches:
            _write_report(args.json_out, report)
            return 1

        report["runtime_mutated"] = True
        if not _run_checked(
            ssh,
            _build_guarded_promote_command(stage_root),
            label="promote AWG route target",
            timeout=120,
        ):
            report["rollback_attempted"] = True
            report["rollback_ok"] = _restore_and_audit(
                ssh,
                backup_root=backup_root,
                live_payload=live_payload,
                reason="promotion failed",
            )
            _write_report(args.json_out, report)
            return 1
        if not _run_checked(
            ssh,
            _build_clean_restart_command(RESTART_UNIT),
            label=f"{RESTART_UNIT} restart",
            timeout=60,
        ) or not _run_checked(
            ssh,
            _build_post_restart_verify_command([RESTART_UNIT]),
            label="delayed AWG route health verification",
            timeout=180,
        ):
            report["rollback_attempted"] = True
            report["rollback_ok"] = _restore_and_audit(
                ssh,
                backup_root=backup_root,
                live_payload=live_payload,
                reason="restart or health verification failed",
            )
            _write_report(args.json_out, report)
            return 1

        sftp = ssh.open_sftp()
        try:
            candidate_rows = _audit_payload(sftp, candidate_payload)
        finally:
            sftp.close()
        candidate_mismatches = _mismatch_rows(candidate_rows)
        report["postdeploy_normalized_match_count"] = len(candidate_rows) - len(candidate_mismatches)
        report["postdeploy_mismatches"] = candidate_mismatches
        if candidate_mismatches:
            report["rollback_attempted"] = True
            report["rollback_ok"] = _restore_and_audit(
                ssh,
                backup_root=backup_root,
                live_payload=live_payload,
                reason="candidate source readback failed",
            )
            _write_report(args.json_out, report)
            return 1

        _run(ssh, f"rm -rf {_q(stage_root)}", timeout=60)
        if not _run_checked(
            ssh,
            _build_backup_prune_command(args.backup_retain_count),
            label="prune old backend backups",
            timeout=120,
        ):
            print("[warn] AWG route deploy succeeded but backup retention failed")
        report["ok"] = True
        report["backup_root"] = backup_root
        print(
            "AWG one-file deploy: PASS "
            f"({len(candidate_rows)}/{len(candidate_rows)} candidate source matches; "
            f"restart={RESTART_UNIT})"
        )
        _write_report(args.json_out, report)
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
