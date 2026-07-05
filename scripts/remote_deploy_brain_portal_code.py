from __future__ import annotations

import argparse
import os
import posixpath
import re
import shlex
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
)
REMOTE_PORTAL_ROOT = "/root/portal_bot"
REMOTE_SHARED_ROOT = "/root/shared"
REMOTE_STAGE_ROOT = "/root/portal_bot.deploy-staging"
REMOTE_BACKUP_ROOT = "/root/portal_bot.deploy-backups"
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
    if target.startswith(f"{REMOTE_PORTAL_ROOT}/"):
        return f"{stage_root}/portal_bot/{posixpath.basename(target)}"
    if target.startswith(f"{REMOTE_SHARED_ROOT}/"):
        return f"{stage_root}/shared/{posixpath.basename(target)}"
    raise ValueError(f"unsupported deploy target: {live_target}")


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


def _build_preflight_command(stage_root: str) -> str:
    portal_stage = f"{stage_root}/portal_bot"
    shared_stage = f"{stage_root}/shared"
    json_check = (
        "import json, pathlib; "
        f"root=pathlib.Path({shared_stage!r}); "
        "[json.load(p.open(encoding='utf-8')) for p in sorted(root.glob('*.json'))]"
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
        f"mkdir -p {_q(REMOTE_PORTAL_ROOT)} {_q(REMOTE_SHARED_ROOT)}",
    ]
    for _source, target in mappings:
        stage_target = _stage_target_for(target, stage_root)
        lines.append(f"install -D -m 0644 {_q(stage_target)} {_q(target)}")
    return "\n".join(lines)


def _build_restore_command(targets: list[str], backup_root: str) -> str:
    lines = ["set -e"]
    for target in targets:
        backup_target = f"{backup_root}{target}"
        lines.extend(
            [
                f"if [ -e {_q(backup_target)} ]; then",
                f"  install -D -m 0644 {_q(backup_target)} {_q(target)}",
                "else",
                f"  rm -f {_q(target)}",
                "fi",
            ]
        )
    return "\n".join(lines)


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

    ok = True
    for unit in restart_units:
        restart_ok = _run_checked(ssh, f"systemctl restart {_q(unit)}", label=f"{unit} rollback restart", timeout=60)
        code, out, err = _run(ssh, f"systemctl is-active {_q(unit)}", timeout=30)
        status = (out.strip() or err.strip()).strip()
        print(f"{unit} rollback: {status}")
        if not restart_ok or code != 0 or status != "active":
            if code != 0 or status != "active":
                _print_remote_result(f"{unit} rollback status", code, out, err)
            ok = False
    return ok


def iter_upload_mappings(repo_root: Path) -> list[tuple[Path, str]]:
    mappings: list[tuple[Path, str]] = []
    for path in sorted((repo_root / "portal_bot").glob("*.py")):
        mappings.append((path, f"/root/portal_bot/{path.name}"))

    requirements = repo_root / "portal_bot" / "requirements.txt"
    if requirements.exists():
        mappings.append((requirements, "/root/portal_bot/requirements.txt"))

    for source_name, target_name in (
        ("collect_node_metrics.py", "collect_node_metrics.py"),
        ("node_dataplane_probe.py", "node_dataplane_probe.py"),
    ):
        source = repo_root / "scripts" / source_name
        if source.exists():
            mappings.append((source, f"/root/portal_bot/{target_name}"))

    for shared_name in (
        "product-facts.json",
        "public-urls.json",
        "design-tokens.json",
        "tariff-catalog.json",
        "access-matrix.json",
        "promo-slots.json",
        "support-ai-knowledge.json",
    ):
        source = repo_root / "shared" / shared_name
        if source.exists():
            mappings.append((source, f"/root/shared/{shared_name}"))

    return mappings


def main() -> int:
    ap = argparse.ArgumentParser(description="Deploy portal_bot/*.py to brain and restart portal-api/portal-bot.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument(
        "--restart",
        default=",".join(DEFAULT_RESTART_UNITS),
        help="comma-separated systemd units to restart",
    )
    args = ap.parse_args()
    restart_units = _parse_restart_units(args.restart)
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
            (
                f"mkdir -p {_q(REMOTE_PORTAL_ROOT)} {_q(REMOTE_SHARED_ROOT)} "
                f"{_q(f'{stage_root}/portal_bot')} {_q(f'{stage_root}/shared')} {_q(backup_root)}"
            ),
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
            restart_ok = _run_checked(ssh, f"systemctl restart {_q(unit)}", label=f"{unit} restart", timeout=60)
            code, out, err = _run(ssh, f"systemctl is-active {_q(unit)}", timeout=30)
            status = (out.strip() or err.strip()).strip()
            print(f"{unit}: {status}")
            if not restart_ok or code != 0 or status != "active":
                if code != 0 or status != "active":
                    _print_remote_result(f"{unit} status", code, out, err)
                _restore_previous_release(
                    ssh,
                    targets=targets,
                    backup_root=backup_root,
                    restart_units=restart_units,
                    reason=f"{unit} failed after deploy",
                )
                return 1
        _run(ssh, f"rm -rf {_q(stage_root)}", timeout=60)
        print(f"backend backup retained: {backup_root}")
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
