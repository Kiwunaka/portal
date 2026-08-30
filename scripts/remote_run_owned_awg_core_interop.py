from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shlex
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any

from node_access import DEFAULT_PASSWORDS, connect_node


_REMOTE_ROOT_PATTERN = re.compile(r"^/tmp/pokrov-awg-ru-pi-[0-9a-f]{32}$")
_RU_PI_PREFLIGHT_MARKER = (
    "pokrov-ru-pi-preflight-v1|aarch64|raspberry_pi_4|direct_default_route"
)
_RU_PI_PREFLIGHT = r'''
set -eu
[ "$(uname -m)" = "aarch64" ]
model="$(tr -d '\000' </proc/device-tree/model)"
case "$model" in
  *"Raspberry Pi 4"*) ;;
  *) exit 41 ;;
esac
default_route="$(ip route show default 2>/dev/null | head -n 1)"
[ -n "$default_route" ]
case "$default_route" in
  *" dev tun"*|*" dev wg"*|*" dev awg"*|*" dev warp"*|*" dev tailscale"*) exit 42 ;;
esac
printf 'pokrov-ru-pi-preflight-v1|aarch64|raspberry_pi_4|direct_default_route\n'
'''


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
    parser.add_argument("--execution-ssh-alias", default="")
    parser.add_argument("--confirm-execution-ssh-alias", default="")
    parser.add_argument("--execution-ssh-config", default="")
    parser.add_argument("--expected-core-revision", default="")
    parser.add_argument("--temp-root", default="")
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


def _exact_core_revision(core_worktree: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=core_worktree,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    revision = completed.stdout.strip().lower()
    if completed.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise RuntimeError("Core source revision is unavailable")
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=core_worktree,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    if status.returncode != 0 or status.stdout.strip():
        raise RuntimeError("Core worktree has tracked changes")
    return revision


def _ssh_base(alias: str, config: Path, known_hosts: Path) -> list[str]:
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", alias):
        raise RuntimeError("execution SSH alias is invalid")
    if not config.is_file() or not known_hosts.is_file():
        raise RuntimeError("execution SSH trust input is missing")
    return [
        "ssh.exe",
        "-F",
        str(config),
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        f"UserKnownHostsFile={known_hosts}",
        alias,
    ]


def _scp_base(config: Path, known_hosts: Path) -> list[str]:
    return [
        "scp.exe",
        "-F",
        str(config),
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        f"UserKnownHostsFile={known_hosts}",
    ]


def _run_process(
    command: list[str],
    *,
    cwd: Path | None = None,
    environment: dict[str, str] | None = None,
    input_text: str | None = None,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _run_local_interop(
    go_executable: Path,
    module_root: Path,
    material: bytearray,
) -> tuple[str, bool, dict[str, Any]]:
    environment = os.environ.copy()
    environment["POKROV_OWNED_AWG_ENDPOINT_B64"] = base64.b64encode(material).decode("ascii")
    environment["GOFLAGS"] = "-buildvcs=false"
    try:
        completed = _run_process(
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
            environment=environment,
            timeout=90,
        )
        combined = completed.stdout + "\n" + completed.stderr
        return (
            _classify(combined, completed.returncode),
            completed.returncode == 0,
            {
                "execution_origin": "current",
                "execution_architecture": "local",
                "execution_host_class": "operator_workstation",
                "temporary_remote_state_removed": None,
            },
        )
    finally:
        environment.pop("POKROV_OWNED_AWG_ENDPOINT_B64", None)


def _remote_root() -> str:
    value = f"/tmp/pokrov-awg-ru-pi-{uuid.uuid4().hex}"
    if not _REMOTE_ROOT_PATTERN.fullmatch(value):
        raise RuntimeError("remote execution root is invalid")
    return value


def _run_ru_pi_interop(
    *,
    alias: str,
    confirmed_alias: str,
    ssh_config: Path,
    known_hosts: Path,
    expected_core_revision: str,
    actual_core_revision: str,
    temp_root: Path,
    go_executable: Path,
    module_root: Path,
    material: bytearray,
) -> tuple[str, bool, dict[str, Any]]:
    if alias != confirmed_alias:
        raise RuntimeError("execution SSH alias confirmation mismatch")
    if not re.fullmatch(r"[0-9a-f]{40}", expected_core_revision) or (
        actual_core_revision != expected_core_revision
    ):
        raise RuntimeError("Core source revision confirmation mismatch")
    if not str(ssh_config) or not str(temp_root):
        raise RuntimeError("RU Pi execution paths are required")
    if not temp_root.is_dir():
        raise RuntimeError("local execution temp root is unavailable")

    ssh_base = _ssh_base(alias, ssh_config, known_hosts)
    preflight = _run_process(ssh_base + [_RU_PI_PREFLIGHT], timeout=20)
    if preflight.returncode != 0 or preflight.stdout.strip() != _RU_PI_PREFLIGHT_MARKER:
        raise RuntimeError("RU Pi execution preflight failed")

    remote_root = _remote_root()
    remote_binary = f"{remote_root}/owned-awg.test"
    remote_created = False
    cleanup_ok = False
    binary_sha256 = ""
    completed: subprocess.CompletedProcess[str] | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="pokrov-awg-ru-pi-", dir=temp_root) as raw_temp:
            local_binary = Path(raw_temp) / "owned-awg.test"
            build_environment = os.environ.copy()
            build_environment.update(
                {
                    "CGO_ENABLED": "0",
                    "GOARCH": "arm64",
                    "GOFLAGS": "-buildvcs=false",
                    "GOOS": "linux",
                }
            )
            build = _run_process(
                [
                    str(go_executable),
                    "test",
                    "-c",
                    "-o",
                    str(local_binary),
                    "./protocol/awg",
                ],
                cwd=module_root,
                environment=build_environment,
                timeout=900,
            )
            if build.returncode != 0 or not local_binary.is_file():
                raise RuntimeError("RU Pi interop binary build failed")
            with local_binary.open("rb") as binary_stream:
                binary_sha256 = hashlib.file_digest(binary_stream, "sha256").hexdigest()

            create = _run_process(
                ssh_base
                + [
                    "set -eu; umask 077; install -d -m 0700 "
                    + shlex.quote(remote_root)
                ],
                timeout=20,
            )
            if create.returncode != 0:
                raise RuntimeError("RU Pi temporary root creation failed")
            remote_created = True

            copy = _run_process(
                _scp_base(ssh_config, known_hosts)
                + [str(local_binary), f"{alias}:{remote_binary}"],
                timeout=180,
            )
            if copy.returncode != 0:
                raise RuntimeError("RU Pi interop binary transfer failed")

            verify = _run_process(
                ssh_base
                + [
                    "set -eu; chmod 0700 "
                    + shlex.quote(remote_binary)
                    + "; sha256sum "
                    + shlex.quote(remote_binary)
                    + " | cut -d' ' -f1"
                ],
                timeout=30,
            )
            if verify.returncode != 0 or verify.stdout.strip() != binary_sha256:
                raise RuntimeError("RU Pi interop binary digest mismatch")

            remote_command = (
                "set -eu; umask 077; "
                "IFS= read -r POKROV_OWNED_AWG_ENDPOINT_B64; "
                "export POKROV_OWNED_AWG_ENDPOINT_B64; "
                "exec "
                + shlex.quote(remote_binary)
                + " -test.run '^TestOwnedAWGLabAuthenticatedEgress$'"
                " -test.count=1 -test.timeout=70s"
            )
            completed = _run_process(
                ssh_base + [remote_command],
                input_text=base64.b64encode(material).decode("ascii") + "\n",
                timeout=100,
            )
    finally:
        if remote_created and _REMOTE_ROOT_PATTERN.fullmatch(remote_root):
            cleanup = _run_process(
                ssh_base
                + [
                    "set -eu; rm -rf -- "
                    + shlex.quote(remote_root)
                    + "; test ! -e "
                    + shlex.quote(remote_root)
                ],
                timeout=30,
            )
            cleanup_ok = cleanup.returncode == 0

    details = {
        "execution_origin": "ru",
        "execution_architecture": "linux_arm64",
        "execution_host_class": "owned_raspberry_pi_4",
        "direct_default_route_preflight": True,
        "binary_sha256": binary_sha256,
        "temporary_remote_state_removed": cleanup_ok,
    }
    if not cleanup_ok:
        return "failed_cleanup", False, details
    if completed is None:
        return "failed_other", False, details
    combined = completed.stdout + "\n" + completed.stderr
    return _classify(combined, completed.returncode), completed.returncode == 0, details


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
    if args.execution_ssh_alias and (
        not args.execution_ssh_config or not args.temp_root
    ):
        raise SystemExit("RU Pi execution requires explicit SSH config and temp root")

    actual_core_revision = _exact_core_revision(core_worktree)

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
    try:
        if args.execution_ssh_alias:
            details = _run_ru_pi_interop(
                alias=str(args.execution_ssh_alias),
                confirmed_alias=str(args.confirm_execution_ssh_alias),
                ssh_config=Path(args.execution_ssh_config).expanduser().resolve(),
                known_hosts=known_hosts,
                expected_core_revision=str(args.expected_core_revision).lower(),
                actual_core_revision=actual_core_revision,
                temp_root=Path(args.temp_root).expanduser().resolve(),
                go_executable=go_executable,
                module_root=module_root,
                material=material,
            )
            outcome, passed, execution = details
        else:
            outcome, passed, execution = _run_local_interop(
                go_executable,
                module_root,
                material,
            )
    finally:
        for index in range(len(material)):
            material[index] = 0

    result = {
        "schema_version": "pokrov-owned-awg-core-interop-v2",
        "profile": str(args.profile),
        "outcome": outcome,
        "passed": passed,
        "core_revision": actual_core_revision,
        "material_sha256": material_sha256,
        "raw_material_returned": False,
        "runtime_mutated": False,
        "server_mutated": False,
        **execution,
    }
    _emit_result(result, args.json_out)
    return 0 if passed and execution.get("temporary_remote_state_removed") is not False else 1


if __name__ == "__main__":
    raise SystemExit(main())
