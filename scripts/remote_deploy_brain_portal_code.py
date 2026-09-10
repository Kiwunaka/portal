from __future__ import annotations

import argparse
import os
import posixpath
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
DEFAULT_RESTART_UNITS = (
    "portal-api",
    "portal-bot",
    "portal-helpbot",
    "portal-feedbackbot",
    "portal-worker",
)
REMOTE_PORTAL_ROOT = "/root/portal_bot"
REMOTE_SHARED_ROOT = "/root/shared"
REMOTE_COPY_ROOT = "/root/copy"
REMOTE_STAGE_ROOT = "/root/portal_bot.deploy-staging"
REMOTE_BACKUP_ROOT = "/root/portal_bot.deploy-backups"
EXECUTABLE_PORTAL_TARGETS = frozenset(
    {"/root/portal_bot/emergency_linux_probe_adapter.py"}
)
DEFAULT_BACKUP_RETENTION_COUNT = 5
POST_RESTART_SETTLE_SECONDS = 12
POST_RESTART_HEALTH_ATTEMPTS = 12
POST_RESTART_HEALTH_URL = "https://api.pokrov.space/api/health"
SYSTEMD_UNIT_RE = re.compile(r"^[A-Za-z0-9_.@:-]+$")
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from node_access import connect_node


def _parse_passwords(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in raw.splitlines()]
    for i, ln in enumerate(lines):
        if "BRAINnode" in ln:
            for j in range(i + 1, min(i + 30, len(lines))):
                v = lines[j].strip()
                if v and not v.startswith("ssh-ed25519 "):
                    return v
    return ""


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 120) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def _print_remote_result(label: str, code: int, out: str, err: str) -> None:
    message = (out.strip() or err.strip()).strip()
    if message:
        print(f"{label}: {message}")
    else:
        print(f"{label}: exit={code}")


def _run_checked(ssh: paramiko.SSHClient, cmd: str, *, label: str, timeout: int = 120) -> bool:
    code, out, err = _run(ssh, cmd, timeout=timeout)
    if code == 0:
        return True
    _print_remote_result(label, code, out, err)
    return False


def _q(value: str) -> str:
    return shlex.quote(str(value))


def _install_mode(target: str) -> str:
    return "0755" if str(target) in EXECUTABLE_PORTAL_TARGETS else "0644"


def _release_id() -> str:
    return f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{os.getpid()}"


def _parse_restart_units(value: str) -> list[str]:
    units = [item.strip() for item in str(value or "").split(",") if item.strip()]
    for unit in units:
        if not SYSTEMD_UNIT_RE.fullmatch(unit):
            raise SystemExit(f"unsafe systemd unit name in --restart: {unit!r}")
    return units


def _stage_target_for(live_target: str, stage_root: str) -> str:
    target = str(live_target)
    for live_root, stage_name in (
        (REMOTE_PORTAL_ROOT, "portal_bot"),
        (REMOTE_SHARED_ROOT, "shared"),
        (REMOTE_COPY_ROOT, "copy"),
    ):
        prefix = f"{live_root}/"
        if target.startswith(prefix):
            relative = target[len(prefix) :]
            if not relative or relative.startswith("../") or "/../" in relative:
                raise ValueError(f"unsafe deploy target: {live_target}")
            return f"{stage_root}/{stage_name}/{relative}"
    raise ValueError(f"unsupported deploy target: {live_target}")


def _build_prepare_command(
    mappings: list[tuple[Path, str]],
    stage_root: str,
    backup_root: str,
) -> str:
    directories = {
        REMOTE_PORTAL_ROOT,
        REMOTE_SHARED_ROOT,
        REMOTE_COPY_ROOT,
        backup_root,
    }
    for _source, target in mappings:
        directories.add(posixpath.dirname(_stage_target_for(target, stage_root)))
    return "mkdir -p " + " ".join(_q(path) for path in sorted(directories))


def _build_backup_command(targets: list[str], backup_root: str) -> str:
    lines = [
        "set -e",
        f"mkdir -p {_q(backup_root)}",
    ]
    for target in targets:
        backup_parent = f"{backup_root}{posixpath.dirname(target)}"
        lines.extend(
            [
                f"if [ -e {_q(target)} ]; then",
                f"  mkdir -p {_q(backup_parent)}",
                f"  cp -a {_q(target)} {_q(backup_parent)}/",
                "fi",
            ]
        )
    return "\n".join(lines)


def _validate_backup_retention_count(value: int) -> int:
    retain_count = int(value)
    if not 1 <= retain_count <= 50:
        raise SystemExit("--backup-retain-count must be between 1 and 50")
    return retain_count


def _build_backup_prune_command(retain_count: int) -> str:
    keep = _validate_backup_retention_count(retain_count)
    root_q = _q(REMOTE_BACKUP_ROOT)
    return "\n".join(
        [
            "set -e",
            f"root={root_q}",
            f'test "$root" = {root_q}',
            'test -d "$root" || exit 0',
            'find "$root" -mindepth 1 -maxdepth 1 -type d -printf \'%f\\n\' |',
            "  grep -E '^[0-9]{8}T[0-9]{6}Z-[0-9]+$' |",
            "  LC_ALL=C sort |",
            f"  head -n -{keep} |",
            "  while IFS= read -r name; do",
            '    test -n "$name" || continue',
            '    rm -rf -- "$root/$name"',
            "  done",
        ]
    )


def _build_preflight_command(stage_root: str) -> str:
    portal_stage = f"{stage_root}/portal_bot"
    json_check = (
        "import json, pathlib; "
        f"root=pathlib.Path({stage_root!r}); "
        "[json.load(p.open(encoding='utf-8')) for p in sorted(root.rglob('*.json'))]"
    )
    return "\n".join(
        [
            "set -e",
            "PY=/root/portal_bot/venv/bin/python",
            'if [ ! -x "$PY" ]; then PY=python3; fi',
            f"cd {_q(portal_stage)}",
            '$PY -m compileall -q .',
            f"python3 -c {_q(json_check)} >/tmp/portal_shared_json_preflight.log",
        ]
    )


def _build_stage_requirements_command(stage_root: str) -> str:
    requirements = f"{stage_root}/portal_bot/requirements.txt"
    venv = f"{stage_root}/venv"
    return "\n".join(
        [
            "set -e",
            f"if [ -f {_q(requirements)} ]; then",
            f"  python3 -m venv {_q(venv)}",
            f"  {_q(f'{venv}/bin/python')} -m pip install -r {_q(requirements)} >/tmp/portal_requirements_stage.log 2>&1",
            "fi",
        ]
    )


def _build_stage_runtime_import_command(stage_root: str) -> str:
    portal_stage = f"{stage_root}/portal_bot"
    python = f"{stage_root}/venv/bin/python"
    import_check = (
        "import admin_v2.roles; "
        "import operator_observability_service; "
        "assert operator_observability_service._KNOWN_ERROR_CODES"
    )
    pi_check = (
        "import hashlib,pathlib; "
        "p=pathlib.Path('support_pi/package-lock.json'); "
        "assert not p.exists() or hashlib.sha256(p.read_bytes().replace(b'\\r\\n',b'\\n')).hexdigest() == "
        "pathlib.Path('/root/portal_bot/support_pi/installed-lock.sha256').read_text().strip(), "
        "'support pi dependencies must be prepared for this lock before deployment'"
    )
    return "\n".join(
        [
            "set -e",
            f"test -x {_q(python)}",
            f"cd {_q(portal_stage)}",
            f"PYTHONPATH={_q(portal_stage)} {_q(python)} -c {_q(import_check)}",
            f"{_q(python)} -c {_q(pi_check)}",
            "if [ -f support_pi/runner.mjs ]; then /opt/pokrov-support-node/bin/node --check support_pi/runner.mjs; fi",
        ]
    )


def _build_live_requirements_command(stage_root: str) -> str:
    requirements = f"{stage_root}/portal_bot/requirements.txt"
    live_python = f"{REMOTE_PORTAL_ROOT}/venv/bin/python"
    return "\n".join(
        [
            "set -e",
            f"if [ -f {_q(requirements)} ]; then",
            f"  test -x {_q(live_python)} || python3 -m venv {_q(f'{REMOTE_PORTAL_ROOT}/venv')}",
            f"  {_q(live_python)} -m pip install -r {_q(requirements)} >/tmp/portal_requirements.log 2>&1",
            "fi",
        ]
    )


def _build_promote_command(mappings: list[tuple[Path, str]], stage_root: str) -> str:
    lines = [
        "set -e",
        f"mkdir -p {_q(REMOTE_PORTAL_ROOT)} {_q(REMOTE_SHARED_ROOT)} {_q(REMOTE_COPY_ROOT)}",
    ]
    for _source, target in mappings:
        stage_target = _stage_target_for(target, stage_root)
        lines.append(
            f"install -D -m {_install_mode(target)} {_q(stage_target)} {_q(target)}"
        )
    return "\n".join(lines)


def _build_restore_command(targets: list[str], backup_root: str) -> str:
    lines = ["set -e"]
    for target in targets:
        backup_target = f"{backup_root}{target}"
        lines.extend(
            [
                f"if [ -e {_q(backup_target)} ]; then",
                f"  install -D -m {_install_mode(target)} {_q(backup_target)} {_q(target)}",
                "else",
                f"  rm -f {_q(target)}",
                "fi",
            ]
        )
    return "\n".join(lines)


def _build_post_restart_verify_command(restart_units: list[str]) -> str:
    lines = [
        "set -e",
        f"sleep {POST_RESTART_SETTLE_SECONDS}",
    ]
    for unit in restart_units:
        unit_q = _q(unit)
        lines.extend(
            [
                f"state=$(systemctl is-active {unit_q} 2>/dev/null || true)",
                f"restarts=$(systemctl show {unit_q} -p NRestarts --value 2>/dev/null || true)",
                f"printf '%s state=%s restarts=%s\\n' {unit_q} \"$state\" \"$restarts\"",
                'test "$state" = active',
                'test "$restarts" = 0',
            ]
        )
    lines.extend(
        [
            "health_ok=0",
            f"for attempt in $(seq 1 {POST_RESTART_HEALTH_ATTEMPTS}); do",
            f"  if curl -fsS --max-time 10 {_q(POST_RESTART_HEALTH_URL)} >/dev/null; then health_ok=1; break; fi",
            "  sleep 2",
            "done",
            'test "$health_ok" = 1',
            "printf 'api_health=PASS\\n'",
        ]
    )
    return "\n".join(lines)


def _build_clean_restart_command(unit: str) -> str:
    unit_q = _q(unit)
    return f"systemctl reset-failed {unit_q} && systemctl restart {unit_q}"


def _restore_previous_release(
    ssh: paramiko.SSHClient,
    *,
    targets: list[str],
    backup_root: str,
    restart_units: list[str],
    reason: str,
) -> bool:
    print(f"[rollback] {reason}; restoring previous backend files from {backup_root}")
    if not _run_checked(
        ssh,
        _build_restore_command(targets, backup_root),
        label="rollback restore previous backend files",
        timeout=300,
    ):
        return False

    for unit in restart_units:
        if not _run_checked(
            ssh,
            _build_clean_restart_command(unit),
            label=f"{unit} rollback restart",
            timeout=60,
        ):
            return False
    return _run_checked(
        ssh,
        _build_post_restart_verify_command(restart_units),
        label="rollback delayed service verification",
        timeout=180,
    )


def _tracked_repo_paths(repo_root: Path, *pathspecs: str) -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "-z", "--", *pathspecs],
        check=True,
        capture_output=True,
    )
    return [repo_root / value.decode("utf-8") for value in result.stdout.split(b"\0") if value]


def iter_upload_mappings(repo_root: Path) -> list[tuple[Path, str]]:
    mappings: list[tuple[Path, str]] = []
    for path in _tracked_repo_paths(repo_root, "portal_bot"):
        relative = path.relative_to(repo_root / "portal_bot")
        if path.suffix == ".py" and (not relative.parts or relative.parts[0] != "tests"):
            mappings.append((path, f"{REMOTE_PORTAL_ROOT}/{relative.as_posix()}"))
        elif relative.as_posix() == "requirements.txt":
            mappings.append((path, f"{REMOTE_PORTAL_ROOT}/requirements.txt"))
        elif relative.as_posix() in {"support_pi/runner.mjs", "support_pi/package.json", "support_pi/package-lock.json"}:
            mappings.append((path, f"{REMOTE_PORTAL_ROOT}/{relative.as_posix()}"))

    for source_name, target_name in (
        ("authenticated_egress_probe.py", "authenticated_egress_probe.py"),
        ("collect_node_metrics.py", "collect_node_metrics.py"),
        ("node_dataplane_probe.py", "node_dataplane_probe.py"),
        ("singbox_authenticated_egress_adapter.py", "singbox_authenticated_egress_adapter.py"),
    ):
        source = repo_root / "scripts" / source_name
        if source.exists():
            mappings.append((source, f"/root/portal_bot/{target_name}"))

    for source in _tracked_repo_paths(repo_root, "shared"):
        if source.suffix == ".json":
            relative = source.relative_to(repo_root / "shared").as_posix()
            mappings.append((source, f"{REMOTE_SHARED_ROOT}/{relative}"))

    copy_catalog = repo_root / "copy" / "catalog.ru.json"
    if copy_catalog in _tracked_repo_paths(repo_root, "copy/catalog.ru.json"):
        mappings.append((copy_catalog, f"{REMOTE_COPY_ROOT}/catalog.ru.json"))

    return sorted(mappings, key=lambda item: item[1])


def main() -> int:
    ap = argparse.ArgumentParser(description="Deploy the tracked Portal backend runtime payload to brain.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument(
        "--restart",
        default=",".join(DEFAULT_RESTART_UNITS),
        help="comma-separated systemd units to restart",
    )
    ap.add_argument(
        "--backup-retain-count",
        type=int,
        default=DEFAULT_BACKUP_RETENTION_COUNT,
        help="number of successful backend rollback snapshots to retain",
    )
    args = ap.parse_args()
    restart_units = _parse_restart_units(args.restart)
    backup_retain_count = _validate_backup_retention_count(args.backup_retain_count)
    release_id = _release_id()
    stage_root = f"{REMOTE_STAGE_ROOT}/{release_id}"
    backup_root = f"{REMOTE_BACKUP_ROOT}/{release_id}"
    mappings = iter_upload_mappings(REPO_ROOT)
    targets = [target for _source, target in mappings]

    ssh, auth_method = connect_node(
        code="brain",
        host=args.brain_ip,
        user=args.ssh_user,
        port=args.ssh_port,
        passwords_path=Path(args.passwords),
    )
    try:
        print(f"brain auth: {auth_method}")
        if not _run_checked(
            ssh,
            _build_prepare_command(mappings, stage_root, backup_root),
            label="prepare remote dirs",
            timeout=60,
        ):
            return 1
        if not _run_checked(
            ssh,
            _build_backup_command(targets, backup_root),
            label="backup current backend files",
            timeout=300,
        ):
            return 1

        sftp = ssh.open_sftp()
        try:
            for source, target in mappings:
                sftp.put(str(source), _stage_target_for(target, stage_root))
        finally:
            sftp.close()

        if not _run_checked(
            ssh,
            _build_preflight_command(stage_root),
            label="preflight staged backend files",
            timeout=300,
        ):
            return 1

        if not _run_checked(
            ssh,
            _build_stage_requirements_command(stage_root),
            label="preflight staged portal requirements",
            timeout=1800,
        ):
            return 1

        if not _run_checked(
            ssh,
            _build_stage_runtime_import_command(stage_root),
            label="preflight staged runtime imports",
            timeout=120,
        ):
            return 1

        if not _run_checked(
            ssh,
            _build_live_requirements_command(stage_root),
            label="install portal requirements",
            timeout=1800,
        ):
            return 1

        if not _run_checked(
            ssh,
            _build_promote_command(mappings, stage_root),
            label="promote staged backend files",
            timeout=300,
        ):
            _run_checked(
                ssh,
                _build_restore_command(targets, backup_root),
                label="restore previous backend files after promote failure",
                timeout=300,
            )
            return 1

        for unit in restart_units:
            if not _run_checked(
                ssh,
                _build_clean_restart_command(unit),
                label=f"{unit} restart",
                timeout=60,
            ):
                _restore_previous_release(
                    ssh,
                    targets=targets,
                    backup_root=backup_root,
                    restart_units=restart_units,
                    reason=f"{unit} restart command failed after deploy",
                )
                return 1
        if not _run_checked(
            ssh,
            _build_post_restart_verify_command(restart_units),
            label="delayed backend health verification",
            timeout=180,
        ):
            _restore_previous_release(
                ssh,
                targets=targets,
                backup_root=backup_root,
                restart_units=restart_units,
                reason="backend failed delayed health verification",
            )
            return 1
        _run(ssh, f"rm -rf {_q(stage_root)}", timeout=60)
        print(f"backend backup retained: {backup_root}")
        if not _run_checked(
            ssh,
            _build_backup_prune_command(backup_retain_count),
            label="prune old backend backups",
            timeout=120,
        ):
            print("[warn] backend deploy succeeded but rollback-backup retention failed")
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
