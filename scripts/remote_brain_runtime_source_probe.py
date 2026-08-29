from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from node_access import connect_node
from remote_deploy_brain_portal_code import DEFAULT_PASSWORDS, REPO_ROOT, iter_upload_mappings
from ssh_host_keys import OpenSshConfigSession


FULL_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
NORMALIZATION_RULE = "CRLF_TO_LF_ONLY"
REMOTE_HASH_SCHEMA = "pokrov-brain-runtime-source-hashes-v1"


REMOTE_HASH_SCRIPT = r"""
import hashlib
import json
import sys

request = json.load(sys.stdin)
rows = []
for item in request.get("rows", []):
    index = int(item["index"])
    target = str(item["remote_target"])
    try:
        with open(target, "rb") as remote_file:
            value = remote_file.read()
    except (OSError, IOError):
        rows.append({"index": index, "readable": False})
        continue
    rows.append(
        {
            "index": index,
            "readable": True,
            "raw_sha256": hashlib.sha256(value).hexdigest(),
            "normalized_sha256": hashlib.sha256(value.replace(b"\r\n", b"\n")).hexdigest(),
        }
    )
json.dump({"schema": "pokrov-brain-runtime-source-hashes-v1", "rows": rows}, sys.stdout)
"""


def _resolve_source_revision(repo_root: Path, value: str) -> str:
    revision = str(value or "").strip().lower()
    if not FULL_COMMIT_RE.fullmatch(revision):
        raise ValueError("--source-revision must be a full 40-character lowercase Git commit")
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--verify", f"{revision}^{{commit}}"],
        check=False,
        capture_output=True,
        text=True,
    )
    resolved = result.stdout.strip().lower()
    if result.returncode != 0 or resolved != revision:
        raise ValueError("--source-revision is not an exact commit in the platform repository")
    return revision


def _git_blob(repo_root: Path, revision: str, relative_path: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{revision}:{relative_path}"],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise ValueError(f"source revision does not contain deploy payload path: {relative_path}")
    return result.stdout


def _normalize_crlf(value: bytes) -> bytes:
    return value.replace(b"\r\n", b"\n")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _compare_bytes(source: bytes, remote: bytes) -> dict[str, Any]:
    raw_match = source == remote
    normalized_match = _normalize_crlf(source) == _normalize_crlf(remote)
    if raw_match:
        classification = "EXACT_BYTES"
    elif normalized_match:
        classification = "CRLF_ONLY_DIFFERENCE"
    else:
        classification = "CONTENT_MISMATCH"
    return {
        "raw_match": raw_match,
        "crlf_normalized_match": normalized_match,
        "classification": classification,
    }


def _safe_auth_method(value: str) -> str:
    if str(value or "") == "ssh_config":
        return "ssh_config"
    return "key" if str(value or "").startswith("key") else "password"


def _build_report(
    *,
    source_revision: str,
    auth_method: str,
    rows: list[dict[str, Any]],
    checked_at: str | None = None,
    mode: str = "READ_ONLY_SFTP",
) -> dict[str, Any]:
    raw_match_count = sum(1 for row in rows if row.get("raw_match") is True)
    normalized_match_count = sum(1 for row in rows if row.get("crlf_normalized_match") is True)
    crlf_only_count = sum(1 for row in rows if row.get("classification") == "CRLF_ONLY_DIFFERENCE")
    mismatches = [
        {
            "source_path": row["source_path"],
            "remote_target": row["remote_target"],
            "classification": row["classification"],
        }
        for row in rows
        if row.get("crlf_normalized_match") is not True
    ]
    return {
        "schema_version": "pokrov-brain-runtime-source-probe-v1",
        "checked_at": checked_at or datetime.now(timezone.utc).isoformat(),
        "origin": "brain",
        "mode": mode,
        "source_revision": source_revision,
        "payload_selection": "remote_deploy_brain_portal_code.iter_upload_mappings",
        "payload_count": len(rows),
        "raw_match_count": raw_match_count,
        "crlf_only_difference_count": crlf_only_count,
        "normalized_match_count": normalized_match_count,
        "normalization_rule": NORMALIZATION_RULE,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "exact_source_semantic_bytes_match": bool(rows) and not mismatches,
        "auth_method": _safe_auth_method(auth_method),
        "remote_content_retained": False,
        "runtime_mutated": False,
        "ok": bool(rows) and not mismatches,
    }


def _remote_hash_command() -> str:
    encoded = base64.b64encode(REMOTE_HASH_SCRIPT.encode("utf-8")).decode("ascii")
    code = f'import base64;exec(base64.b64decode("{encoded}"))'
    return "python3 -c " + shlex.quote(code)


def _probe_via_ssh_config_alias(
    *,
    alias: str,
    source_payload: list[tuple[str, str, bytes]],
    ssh_config: Path | None = None,
    timeout: int = 180,
) -> list[dict[str, Any]]:
    session = OpenSshConfigSession(alias=alias, config_path=ssh_config)

    request_rows = [
        {
            "index": index,
            "remote_target": remote_target,
            "source_raw_sha256": _sha256(source_bytes),
            "source_normalized_sha256": _sha256(_normalize_crlf(source_bytes)),
        }
        for index, (_relative_path, remote_target, source_bytes) in enumerate(source_payload)
    ]
    result = session.run(
        _remote_hash_command(),
        input_text=json.dumps({"schema": REMOTE_HASH_SCHEMA, "rows": request_rows}),
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError("SSH-config source probe failed before structured output")
    try:
        response = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("SSH-config source probe returned invalid JSON") from exc
    if response.get("schema") != REMOTE_HASH_SCHEMA or not isinstance(response.get("rows"), list):
        raise RuntimeError("SSH-config source probe returned an invalid schema")

    remote_by_index: dict[int, dict[str, Any]] = {}
    for remote_row in response["rows"]:
        if not isinstance(remote_row, dict):
            raise RuntimeError("SSH-config source probe returned a malformed row")
        try:
            index = int(remote_row["index"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError("SSH-config source probe returned a malformed row index") from exc
        if index in remote_by_index or index < 0 or index >= len(source_payload):
            raise RuntimeError("SSH-config source probe returned an invalid row index")
        remote_by_index[index] = remote_row
    if len(remote_by_index) != len(source_payload):
        raise RuntimeError("SSH-config source probe returned an incomplete row set")

    rows: list[dict[str, Any]] = []
    for index, (relative_path, remote_target, source_bytes) in enumerate(source_payload):
        remote_row = remote_by_index[index]
        if remote_row.get("readable") is not True:
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
        raw_match = str(remote_row.get("raw_sha256") or "") == _sha256(source_bytes)
        normalized_match = str(remote_row.get("normalized_sha256") or "") == _sha256(
            _normalize_crlf(source_bytes)
        )
        classification = (
            "EXACT_BYTES" if raw_match else "CRLF_ONLY_DIFFERENCE" if normalized_match else "CONTENT_MISMATCH"
        )
        rows.append(
            {
                "source_path": relative_path,
                "remote_target": remote_target,
                "raw_match": raw_match,
                "crlf_normalized_match": normalized_match,
                "classification": classification,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare the live Brain backend payload with exact Git blobs without mutating runtime state."
    )
    connection = parser.add_mutually_exclusive_group(required=True)
    connection.add_argument("--brain-ip")
    connection.add_argument("--ssh-config-alias")
    parser.add_argument("--ssh-config", default="")
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args()

    try:
        source_revision = _resolve_source_revision(REPO_ROOT, args.source_revision)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    mappings = iter_upload_mappings(REPO_ROOT)
    source_payload: list[tuple[str, str, bytes]] = []
    for source_path, remote_target in mappings:
        relative_path = source_path.relative_to(REPO_ROOT).as_posix()
        try:
            source_bytes = _git_blob(REPO_ROOT, source_revision, relative_path)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        source_payload.append((relative_path, remote_target, source_bytes))

    if args.ssh_config_alias:
        try:
            rows = _probe_via_ssh_config_alias(
                alias=args.ssh_config_alias,
                source_payload=source_payload,
                ssh_config=Path(args.ssh_config).expanduser() if args.ssh_config else None,
            )
        except (RuntimeError, ValueError) as exc:
            raise SystemExit(str(exc)) from exc
        auth_method = "ssh_config"
        mode = "READ_ONLY_SSH_HASHES"
    else:
        ssh, auth_method = connect_node(
            code="brain",
            host=args.brain_ip,
            user=args.ssh_user,
            port=args.ssh_port,
            passwords_path=Path(args.passwords),
        )
        rows = []
        try:
            sftp = ssh.open_sftp()
            try:
                for relative_path, remote_target, source_bytes in source_payload:
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
            finally:
                sftp.close()
        finally:
            ssh.close()
        mode = "READ_ONLY_SFTP"

    report = _build_report(
        source_revision=source_revision,
        auth_method=auth_method,
        rows=rows,
        mode=mode,
    )
    output_path = Path(args.json_out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    status = "PASS" if report["ok"] else "FAIL"
    print(
        f"brain runtime source probe: {status} "
        f"({report['normalized_match_count']}/{report['payload_count']} semantic byte matches; "
        f"normalization={NORMALIZATION_RULE})"
    )
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
