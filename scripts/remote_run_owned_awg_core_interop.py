from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shlex
import stat
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any

from exact_git_snapshot import ExactGitSnapshotError, materialize_paths
from node_access import DEFAULT_PASSWORDS, connect_node


_REMOTE_ROOT_PATTERN = re.compile(r"^/tmp/pokrov-awg-ru-pi-[0-9a-f]{32}$")
_INTEROP_TEST_NAME = "TestOwnedAWGLabAuthenticatedEgress"
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
    parser.add_argument("--git-executable", required=True)
    parser.add_argument("--go-executable", required=True)
    parser.add_argument("--brain-ip", default="82.21.114.104")
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--known-hosts", required=True)
    parser.add_argument("--execution-ssh-alias", default="")
    parser.add_argument("--confirm-execution-ssh-alias", default="")
    parser.add_argument("--execution-ssh-config", default="")
    parser.add_argument("--ssh-executable", default="")
    parser.add_argument("--scp-executable", default="")
    parser.add_argument("--expected-core-revision", required=True)
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


def _interop_outcome(output: str, returncode: int) -> tuple[str, bool]:
    passed = bool(
        returncode == 0
        and re.search(rf"(?m)^=== RUN\s+{re.escape(_INTEROP_TEST_NAME)}$", output)
        and re.search(rf"(?m)^--- PASS: {re.escape(_INTEROP_TEST_NAME)}\b", output)
    )
    if returncode == 0 and not passed:
        return "failed_test_not_observed", False
    return _classify(output, returncode), passed


def _emit_result(result: dict[str, Any], raw_output_path: str) -> None:
    encoded = json.dumps(result, sort_keys=True)
    output_path = str(raw_output_path or "").strip()
    if output_path:
        target = Path(output_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


def _validated_executable(raw_path: str, label: str) -> Path:
    candidate = Path(str(raw_path).strip()).expanduser()
    if not candidate.is_absolute():
        raise RuntimeError(f"{label} executable path must be absolute")
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise RuntimeError(f"{label} executable is unavailable") from exc
    if not resolved.is_file():
        raise RuntimeError(f"{label} executable is unavailable")
    return resolved


def _file_sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _git_environment() -> dict[str, str]:
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    environment.update(
        {
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
        }
    )
    return environment


def _git_command(git_executable: Path, *arguments: str) -> list[str]:
    return [
        str(git_executable),
        "-c",
        "core.fsmonitor=false",
        "-c",
        f"core.hooksPath={os.devnull}",
        *arguments,
    ]


def _exact_core_revision(
    git_executable: Path,
    core_worktree: Path,
    expected_revision: str,
) -> str:
    expected = str(expected_revision).strip().lower()
    if re.fullmatch(r"[0-9a-f]{40}", expected) is None:
        raise RuntimeError("Core source revision confirmation is invalid")
    top_level = subprocess.run(
        _git_command(git_executable, "rev-parse", "--show-toplevel"),
        cwd=core_worktree,
        capture_output=True,
        env=_git_environment(),
        text=True,
        timeout=15,
        check=False,
    )
    if top_level.returncode != 0:
        raise RuntimeError("Core repository root is unavailable")
    try:
        actual_top_level = Path(top_level.stdout.strip()).resolve(strict=True)
        requested_top_level = core_worktree.resolve(strict=True)
    except OSError as exc:
        raise RuntimeError("Core repository root is unavailable") from exc
    if actual_top_level != requested_top_level:
        raise RuntimeError("Core worktree is not the repository root")
    completed = subprocess.run(
        _git_command(git_executable, "rev-parse", "HEAD"),
        cwd=core_worktree,
        capture_output=True,
        env=_git_environment(),
        text=True,
        timeout=15,
        check=False,
    )
    revision = completed.stdout.strip().lower()
    if completed.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise RuntimeError("Core source revision is unavailable")
    if revision != expected:
        raise RuntimeError("Core source revision confirmation mismatch")
    tracked_module = subprocess.run(
        _git_command(
            git_executable,
            "cat-file",
            "-e",
            f"{revision}:engine/sing-box/go.mod",
        ),
        cwd=core_worktree,
        capture_output=True,
        env=_git_environment(),
        text=True,
        timeout=15,
        check=False,
    )
    if tracked_module.returncode != 0:
        raise RuntimeError("Core module is not tracked at the confirmed revision")
    return revision


def _ssh_base(
    ssh_executable: Path,
    alias: str,
    config: Path,
    known_hosts: Path,
) -> list[str]:
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", alias):
        raise RuntimeError("execution SSH alias is invalid")
    if not config.is_file() or not known_hosts.is_file():
        raise RuntimeError("execution SSH trust input is missing")
    return [
        str(ssh_executable),
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


def _scp_base(
    scp_executable: Path,
    ssh_executable: Path,
    config: Path,
    known_hosts: Path,
) -> list[str]:
    return [
        str(scp_executable),
        "-S",
        str(ssh_executable),
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


def _materialize_core_module(
    git_executable: Path,
    core_worktree: Path,
    revision: str,
    destination: Path,
) -> Path:
    source_root = destination / "source"
    try:
        materialize_paths(
            git_executable,
            core_worktree,
            revision,
            source_root,
            ("engine/sing-box",),
        )
    except ExactGitSnapshotError as exc:
        raise RuntimeError(
            "confirmed Core module snapshot could not be created"
        ) from exc
    module_root = source_root / "engine" / "sing-box"
    if not (module_root / "go.mod").is_file():
        raise RuntimeError("confirmed Core module snapshot is incomplete")
    return module_root


def _go_build_environment(go_executable: Path, *, target: str) -> dict[str, str]:
    environment: dict[str, str] = {
        "CGO_ENABLED": "0",
        "GOENV": "off",
        "GOFLAGS": "-buildvcs=false -mod=readonly",
        "GOPROXY": "off",
        "GOSUMDB": "off",
        "GOTOOLCHAIN": "local",
        "GOWORK": "off",
        "PATH": str(go_executable.parent),
    }
    for name in (
        "APPDATA",
        "HOME",
        "LOCALAPPDATA",
        "SYSTEMDRIVE",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "USERPROFILE",
    ):
        value = os.environ.get(name)
        if value:
            environment[name] = value
    if target == "linux_arm64":
        environment.update({"GOARCH": "arm64", "GOOS": "linux"})
    elif target != "local":
        raise RuntimeError("interop build target is invalid")
    return environment


def _validate_local_replacements(
    go_executable: Path,
    module_root: Path,
    snapshot_root: Path,
    environment: dict[str, str],
) -> None:
    edited = _run_process(
        [str(go_executable), "mod", "edit", "-json"],
        cwd=module_root,
        environment=environment,
        timeout=30,
    )
    if edited.returncode != 0:
        raise RuntimeError("confirmed Core module replacements are unavailable")
    try:
        payload = json.loads(edited.stdout)
    except ValueError as exc:
        raise RuntimeError("confirmed Core module replacements are invalid") from exc
    replacements = payload.get("Replace") if isinstance(payload, dict) else None
    for replacement in replacements if isinstance(replacements, list) else []:
        new = replacement.get("New") if isinstance(replacement, dict) else None
        if not isinstance(new, dict) or str(new.get("Version") or ""):
            continue
        raw_path = str(new.get("Path") or "").strip()
        if not raw_path:
            raise RuntimeError("confirmed Core module replacement is invalid")
        candidate = (module_root / raw_path).resolve()
        if not candidate.is_relative_to(snapshot_root.resolve()) or not candidate.exists():
            raise RuntimeError("confirmed Core module replacement escapes the snapshot")


def _prepare_interop_binary(
    go_executable: Path,
    module_root: Path,
    snapshot_root: Path,
    output_path: Path,
    *,
    target: str,
) -> str:
    environment = _go_build_environment(go_executable, target=target)
    _validate_local_replacements(
        go_executable,
        module_root,
        snapshot_root,
        environment,
    )
    verified = _run_process(
        [str(go_executable), "mod", "verify"],
        cwd=module_root,
        environment=environment,
        timeout=300,
    )
    if verified.returncode != 0:
        raise RuntimeError("confirmed Core module cache verification failed")
    built = _run_process(
        [
            str(go_executable),
            "test",
            "-c",
            "-o",
            str(output_path),
            "./protocol/awg",
        ],
        cwd=module_root,
        environment=environment,
        timeout=900,
    )
    if built.returncode != 0 or not output_path.is_file():
        raise RuntimeError("confirmed Core interop binary build failed")
    digest = _file_sha256(output_path)
    output_path.chmod(
        output_path.stat().st_mode
        & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
    )
    return digest


def _validate_local_interop_binary(binary: Path, expected_sha256: str) -> None:
    if _file_sha256(binary) != expected_sha256:
        raise RuntimeError("local interop binary digest changed before validation")
    listed = _run_process(
        [str(binary), "-test.list", f"^{_INTEROP_TEST_NAME}$"],
        environment={key: value for key, value in os.environ.items() if not key.startswith("POKROV_")},
        timeout=30,
    )
    if listed.returncode != 0 or listed.stdout.splitlines() != [_INTEROP_TEST_NAME]:
        raise RuntimeError("confirmed Core interop test is not registered")
    if _file_sha256(binary) != expected_sha256:
        raise RuntimeError("local interop binary digest changed during validation")


def _run_local_interop(
    binary: Path,
    binary_sha256: str,
    material: bytearray,
) -> tuple[str, bool, dict[str, Any]]:
    environment = os.environ.copy()
    environment["POKROV_OWNED_AWG_ENDPOINT_B64"] = base64.b64encode(material).decode("ascii")
    try:
        completed = _run_process(
            [
                str(binary),
                "-test.run",
                "^TestOwnedAWGLabAuthenticatedEgress$",
                "-test.count=1",
                "-test.timeout=70s",
                "-test.v",
            ],
            environment=environment,
            timeout=90,
        )
        combined = completed.stdout + "\n" + completed.stderr
        outcome, passed = _interop_outcome(combined, completed.returncode)
        if _file_sha256(binary) != binary_sha256:
            outcome, passed = "failed_binary_identity", False
        return (
            outcome,
            passed,
            {
                "execution_origin": "current",
                "execution_architecture": "local",
                "execution_host_class": "operator_workstation",
                "binary_sha256": binary_sha256,
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
    ssh_executable: Path,
    scp_executable: Path,
    expected_core_revision: str,
    actual_core_revision: str,
    local_binary: Path,
    binary_sha256: str,
    material: bytearray,
) -> tuple[str, bool, dict[str, Any]]:
    if alias != confirmed_alias:
        raise RuntimeError("execution SSH alias confirmation mismatch")
    if not re.fullmatch(r"[0-9a-f]{40}", expected_core_revision) or (
        actual_core_revision != expected_core_revision
    ):
        raise RuntimeError("Core source revision confirmation mismatch")
    if not str(ssh_config) or not local_binary.is_file():
        raise RuntimeError("RU Pi execution inputs are unavailable")
    if _file_sha256(local_binary) != binary_sha256:
        raise RuntimeError("RU Pi interop binary digest changed before transfer")

    ssh_base = _ssh_base(ssh_executable, alias, ssh_config, known_hosts)
    preflight = _run_process(ssh_base + [_RU_PI_PREFLIGHT], timeout=20)
    if preflight.returncode != 0 or preflight.stdout.strip() != _RU_PI_PREFLIGHT_MARKER:
        raise RuntimeError("RU Pi execution preflight failed")

    remote_root = _remote_root()
    remote_binary = f"{remote_root}/owned-awg.test"
    remote_created = False
    cleanup_ok = False
    completed: subprocess.CompletedProcess[str] | None = None
    try:
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
            _scp_base(
                scp_executable,
                ssh_executable,
                ssh_config,
                known_hosts,
            )
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

        listed = _run_process(
            ssh_base
            + [
                shlex.quote(remote_binary)
                + " -test.list '^"
                + _INTEROP_TEST_NAME
                + "$'"
            ],
            timeout=30,
        )
        if listed.returncode != 0 or listed.stdout.splitlines() != [_INTEROP_TEST_NAME]:
            raise RuntimeError("RU Pi interop test is not registered")

        remote_command = (
            "set -eu; umask 077; "
            "IFS= read -r POKROV_OWNED_AWG_ENDPOINT_B64; "
            "export POKROV_OWNED_AWG_ENDPOINT_B64; "
            "exec "
            + shlex.quote(remote_binary)
            + " -test.run '^TestOwnedAWGLabAuthenticatedEgress$'"
            " -test.count=1 -test.timeout=70s -test.v"
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
    outcome, passed = _interop_outcome(combined, completed.returncode)
    return outcome, passed, details


def main() -> int:
    args = _parse_args()
    core_worktree = Path(args.core_worktree).resolve()
    module_root = core_worktree / "engine" / "sing-box"
    try:
        git_executable = _validated_executable(args.git_executable, "Git")
        go_executable = _validated_executable(args.go_executable, "Go")
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from None
    known_hosts = Path(args.known_hosts).resolve()
    passwords = Path(args.passwords).resolve()
    if not (module_root / "go.mod").is_file():
        raise SystemExit("Core worktree is invalid")
    if not known_hosts.is_file() or not passwords.is_file():
        raise SystemExit("SSH trust or authentication input is missing")
    ssh_executable: Path | None = None
    scp_executable: Path | None = None
    ssh_config: Path | None = None
    temp_root = (
        Path(args.temp_root).expanduser().resolve()
        if args.temp_root
        else Path(tempfile.gettempdir()).resolve()
    )
    if not temp_root.is_dir():
        raise SystemExit("local execution temp root is unavailable")
    if args.execution_ssh_alias:
        if not all(
            (
                args.execution_ssh_config,
                args.temp_root,
                args.ssh_executable,
                args.scp_executable,
            )
        ):
            raise SystemExit(
                "RU Pi execution requires explicit SSH config, temp root, SSH and SCP executables"
            )
        try:
            ssh_executable = _validated_executable(args.ssh_executable, "SSH")
            scp_executable = _validated_executable(args.scp_executable, "SCP")
        except RuntimeError as exc:
            raise SystemExit(str(exc)) from None
        ssh_config = Path(args.execution_ssh_config).expanduser().resolve()
    execution_tool_paths = {
        "git": git_executable,
        "go": go_executable,
    }
    if ssh_executable is not None and scp_executable is not None:
        execution_tool_paths.update({"ssh": ssh_executable, "scp": scp_executable})
    execution_tool_sha256 = {
        name: _file_sha256(path) for name, path in execution_tool_paths.items()
    }

    actual_core_revision = _exact_core_revision(
        git_executable,
        core_worktree,
        str(args.expected_core_revision),
    )
    if _file_sha256(git_executable) != execution_tool_sha256["git"]:
        raise SystemExit("Git executable identity changed during Core validation")
    if args.execution_ssh_alias:
        if str(args.execution_ssh_alias) != str(args.confirm_execution_ssh_alias):
            raise SystemExit("execution SSH alias confirmation mismatch")
        assert ssh_executable is not None and scp_executable is not None
        assert ssh_config is not None
        _ssh_base(
            ssh_executable,
            str(args.execution_ssh_alias),
            ssh_config,
            known_hosts,
        )

    with tempfile.TemporaryDirectory(
        prefix="pokrov-awg-confirmed-core-",
        dir=temp_root,
    ) as raw_temp:
        operation_root = Path(raw_temp)
        confirmed_module_root = _materialize_core_module(
            git_executable,
            core_worktree,
            actual_core_revision,
            operation_root,
        )
        if _file_sha256(git_executable) != execution_tool_sha256["git"]:
            raise SystemExit("Git executable identity changed during Core snapshot")
        remote_mode = bool(args.execution_ssh_alias)
        binary_name = "owned-awg.test" if remote_mode or os.name != "nt" else "owned-awg.test.exe"
        local_binary = operation_root / binary_name
        binary_sha256 = _prepare_interop_binary(
            go_executable,
            confirmed_module_root,
            operation_root / "source",
            local_binary,
            target="linux_arm64" if remote_mode else "local",
        )
        if _file_sha256(go_executable) != execution_tool_sha256["go"]:
            raise SystemExit("Go executable identity changed during Core build")
        if not remote_mode:
            _validate_local_interop_binary(local_binary, binary_sha256)

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
            if remote_mode:
                assert ssh_executable is not None and scp_executable is not None
                assert ssh_config is not None
                details = _run_ru_pi_interop(
                    alias=str(args.execution_ssh_alias),
                    confirmed_alias=str(args.confirm_execution_ssh_alias),
                    ssh_config=ssh_config,
                    known_hosts=known_hosts,
                    ssh_executable=ssh_executable,
                    scp_executable=scp_executable,
                    expected_core_revision=str(args.expected_core_revision).lower(),
                    actual_core_revision=actual_core_revision,
                    local_binary=local_binary,
                    binary_sha256=binary_sha256,
                    material=material,
                )
                outcome, passed, execution = details
            else:
                outcome, passed, execution = _run_local_interop(
                    local_binary,
                    binary_sha256,
                    material,
                )
        finally:
            for index in range(len(material)):
                material[index] = 0

        for name, path in execution_tool_paths.items():
            if _file_sha256(path) != execution_tool_sha256[name]:
                raise SystemExit(f"{name.upper()} executable identity changed during execution")

    result = {
        "schema_version": "pokrov-owned-awg-core-interop-v3",
        "profile": str(args.profile),
        "outcome": outcome,
        "passed": passed,
        "core_revision": actual_core_revision,
        "material_sha256": material_sha256,
        "execution_tool_sha256": execution_tool_sha256,
        "raw_material_returned": False,
        "runtime_mutated": False,
        "server_mutated": False,
        **execution,
    }
    _emit_result(result, args.json_out)
    return 0 if passed and execution.get("temporary_remote_state_removed") is not False else 1


if __name__ == "__main__":
    raise SystemExit(main())
