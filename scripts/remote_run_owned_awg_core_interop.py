from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any

from node_access import DEFAULT_PASSWORDS, connect_node


_REMOTE_HELPER = r'''
import base64
import json
import os
import subprocess
import sys

profile = str(json.loads(sys.stdin.read())["profile"])
if profile not in {"awg2_lab", "awg31_lab"}:
    raise SystemExit("profile invalid")

pid = subprocess.check_output(
    ["systemctl", "show", "portal-api", "-p", "MainPID", "--value"],
    text=True,
).strip()
with open(f"/proc/{pid}/environ", "rb") as handle:
    for item in handle.read().split(b"\0"):
        if b"=" in item:
            key, value = item.split(b"=", 1)
            os.environ[key.decode("utf-8", "replace")] = value.decode("utf-8", "replace")

os.chdir("/root/portal_bot")
sys.path.insert(0, "/root/portal_bot")
from awg2_lab_service import _decrypt_endpoint as decrypt_awg2
from awg31_lab_service import _decrypt_endpoint as decrypt_awg31
from db import SessionLocal
from models import Awg2LabMaterial, Awg31LabMaterial

with SessionLocal() as session:
    if profile == "awg2_lab":
        row = (
            session.query(Awg2LabMaterial)
            .filter(Awg2LabMaterial.is_active.is_(True))
            .filter(Awg2LabMaterial.state == "ready")
            .order_by(Awg2LabMaterial.provisioned_at.desc(), Awg2LabMaterial.id.desc())
            .first()
        )
        endpoint = None if row is None else decrypt_awg2(row.endpoint_ciphertext)
    else:
        row = (
            session.query(Awg31LabMaterial)
            .filter(Awg31LabMaterial.is_active.is_(True))
            .filter(Awg31LabMaterial.state == "ready")
            .order_by(Awg31LabMaterial.provisioned_at.desc(), Awg31LabMaterial.id.desc())
            .first()
        )
        endpoint = None if row is None else decrypt_awg31(row.endpoint_ciphertext)
if not isinstance(endpoint, dict):
    raise SystemExit("owned AWG material unavailable")
raw = json.dumps(endpoint, separators=(",", ":"), sort_keys=True).encode()
print(base64.b64encode(raw).decode())
'''


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the secret-safe Core interop test against one owned AWG lab."
    )
    parser.add_argument("profile", choices=("awg2_lab", "awg31_lab"))
    parser.add_argument("--core-worktree", required=True)
    parser.add_argument("--go-executable", required=True)
    parser.add_argument("--brain-ip", default="82.21.114.104")
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--known-hosts", required=True)
    parser.add_argument("--json-out", default="")
    return parser.parse_args()


def _load_material(brain: Any, profile: str) -> bytes:
    command = "/root/portal_bot/venv/bin/python -c " + shlex.quote(_REMOTE_HELPER)
    stdin, stdout, stderr = brain.exec_command(command, timeout=120)
    stdin.write(json.dumps({"profile": profile}, separators=(",", ":")))
    stdin.channel.shutdown_write()
    code = stdout.channel.recv_exit_status()
    encoded = stdout.read().decode("ascii", "strict").strip()
    error = stderr.read().decode("utf-8", "replace").strip()
    if code != 0:
        raise RuntimeError((error or "owned AWG material read failed")[:240])
    raw = base64.b64decode(encoded, validate=True)
    if not 1 <= len(raw) <= 64 * 1024:
        raise RuntimeError("owned AWG material size invalid")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict) or not parsed.get("private_key") or not parsed.get("peers"):
        raise RuntimeError("owned AWG material shape invalid")
    return raw


def _classify(output: str, returncode: int) -> str:
    if returncode == 0:
        return "passed"
    markers = (
        ("before an outer packet was emitted", "failed_before_outer_packet"),
        ("after an outer packet write error", "failed_outer_write"),
        ("because no outer response was received", "failed_no_outer_response"),
        ("after outer responses were received", "failed_after_outer_response"),
        ("owned AWG TLS egress failed", "failed_tls"),
        ("owned AWG TCP egress failed", "failed_tcp"),
    )
    for marker, category in markers:
        if marker in output:
            return category
    return "failed_other"


def _emit_result(result: dict[str, Any], raw_output_path: str) -> None:
    encoded = json.dumps(result, sort_keys=True)
    output_path = str(raw_output_path or "").strip()
    if output_path:
        target = Path(output_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


def main() -> int:
    args = _parse_args()
    core_worktree = Path(args.core_worktree).resolve()
    module_root = core_worktree / "engine" / "sing-box"
    go_executable = Path(args.go_executable).resolve()
    known_hosts = Path(args.known_hosts).resolve()
    passwords = Path(args.passwords).resolve()
    if not (module_root / "go.mod").is_file() or not go_executable.is_file():
        raise SystemExit("Core worktree or Go executable is invalid")
    if not known_hosts.is_file() or not passwords.is_file():
        raise SystemExit("SSH trust or authentication input is missing")

    os.environ["POKROV_SSH_KNOWN_HOSTS"] = str(known_hosts)
    brain, _auth = connect_node(
        code="brain",
        host=str(args.brain_ip),
        passwords_path=passwords,
    )
    material = bytearray()
    try:
        material = bytearray(_load_material(brain, str(args.profile)))
    finally:
        brain.close()

    material_sha256 = hashlib.sha256(material).hexdigest()
    environment = os.environ.copy()
    environment["POKROV_OWNED_AWG_ENDPOINT_B64"] = base64.b64encode(material).decode("ascii")
    environment["GOFLAGS"] = "-buildvcs=false"
    try:
        completed = subprocess.run(
            [
                str(go_executable),
                "test",
                "./protocol/awg",
                "-run",
                "^TestOwnedAWGLabAuthenticatedEgress$",
                "-count=1",
                "-timeout=70s",
            ],
            cwd=module_root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
        combined = completed.stdout + "\n" + completed.stderr
        outcome = _classify(combined, completed.returncode)
    finally:
        environment.pop("POKROV_OWNED_AWG_ENDPOINT_B64", None)
        for index in range(len(material)):
            material[index] = 0

    _emit_result(
        {
            "schema_version": "pokrov-owned-awg-core-interop-v1",
            "profile": str(args.profile),
            "outcome": outcome,
            "passed": completed.returncode == 0,
            "material_sha256": material_sha256,
            "raw_material_returned": False,
        },
        args.json_out,
    )
    return 0 if completed.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
