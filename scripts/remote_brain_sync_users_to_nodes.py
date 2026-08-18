from __future__ import annotations

import argparse
import os
from pathlib import Path

import paramiko

from ssh_host_keys import configure_ssh_host_key_policy


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
APPLY_CONFIRMATION = "RECONCILE_TRIAL_PAID_PENDING"


def _parse_passwords(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [line.strip() for line in raw.splitlines()]
    for index, line in enumerate(lines):
        if "BRAINnode" not in line:
            continue
        for candidate in lines[index + 1 : index + 30]:
            if candidate and not candidate.startswith(("ssh-ed25519 ", "ssh-rsa ")):
                return candidate
    return ""


def _run(ssh: paramiko.SSHClient, command: str, *, timeout: int = 600) -> tuple[int, str, str]:
    _stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    return (
        code,
        stdout.read().decode(errors="replace"),
        stderr.read().decode(errors="replace"),
    )


SYNC_SNIPPET = r"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess


def load_service_env(service='portal-api'):
    pid = subprocess.check_output(
        ['systemctl', 'show', service, '-p', 'MainPID', '--value'],
        text=True,
    ).strip()
    if not pid or pid == '0':
        raise SystemExit(f'{service} has no MainPID')
    for item in open(f'/proc/{pid}/environ', 'rb').read().split(b'\0'):
        if item and b'=' in item:
            key, value = item.split(b'=', 1)
            os.environ[key.decode()] = value.decode(errors='replace')


load_service_env(os.getenv('PORTAL_ENV_SERVICE', 'portal-api'))

from control_panel import ControlPanel
from db import SessionLocal, init_db
from models import User
from node_policy import effective_user_access_status


def _eligible_user(user) -> bool:
    return (
        int(getattr(user, 'tg_id', 0) or 0) > 0
        and not bool(getattr(user, 'is_manual', False))
        and str(getattr(user, 'sub_type', '') or '').strip().upper() != 'MANUAL'
    )


async def main() -> int:
    init_db()
    session = SessionLocal()
    try:
        users = [
            user
            for user in session.query(User).order_by(User.created_at.asc()).all()
            if _eligible_user(user)
        ]
        requested_tg_id = int(os.getenv('SYNC_TG_ID', '0') or 0)
        if requested_tg_id:
            users = [user for user in users if int(user.tg_id) == requested_tg_id]
    finally:
        session.close()

    status_counts = {'TRIAL': 0, 'PAID': 0, 'PENDING': 0}
    for user in users:
        status_counts[effective_user_access_status(user)] += 1
    apply = os.getenv('SYNC_APPLY', '0') == '1'
    if not apply:
        print(json.dumps({
            'ok': True,
            'mode': 'dry_run',
            'users': len(users),
            'status_counts': status_counts,
            'mutations': 0,
        }, sort_keys=True))
        return 0

    concurrency = max(1, min(int(os.getenv('SYNC_CONCURRENCY', '6') or 6), 8))
    passes = max(1, min(int(os.getenv('SYNC_PASSES', '2') or 2), 5))
    panel = ControlPanel(concurrency=concurrency)
    complete = 0
    nodes_attempted = 0
    pending_users = list(users)
    try:
        nodes = await panel.refresh()
        node_codes = [
            str(getattr(node, 'code', '') or '').strip()
            for node in nodes
            if str(getattr(node, 'code', '') or '').strip()
        ]
        if not node_codes:
            raise SystemExit('No enabled nodes are available.')
        for _attempt in range(passes):
            retry_users = []
            for user in pending_users:
                status = effective_user_access_status(user)
                sub_id = str(getattr(user, 'sub_token', '') or user.tg_id)
                if status in {'TRIAL', 'PAID'}:
                    results = await panel.ensure_user_on_all_nodes(
                        tg_id=int(user.tg_id),
                        client_uuid=str(user.uuid or ''),
                        email=str(user.email or f'User_{int(user.tg_id)}'),
                        sub_id=sub_id,
                        enable=True,
                        only_node_codes=None,
                    )
                else:
                    results = await panel.set_existing_user_enabled_on_nodes(
                        tg_id=int(user.tg_id),
                        node_codes=node_codes,
                        enable=False,
                        sub_id=sub_id,
                    )
                nodes_attempted += len(results)
                if results and all(bool(value) for value in results.values()):
                    complete += 1
                else:
                    retry_users.append(user)
            pending_users = retry_users
            if not pending_users:
                break
    finally:
        await panel.close()

    partial = len(pending_users)
    print(json.dumps({
        'ok': partial == 0,
        'mode': 'apply',
        'users': len(users),
        'status_counts': status_counts,
        'complete_users': complete,
        'partial_users': partial,
        'nodes_attempted': nodes_attempted,
        'passes': passes,
        'concurrency': concurrency,
    }, sort_keys=True))
    return 0 if partial == 0 else 1


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit or reconcile production users to TRIAL/PAID/PENDING node access. "
            "Dry-run is the default."
        )
    )
    parser.add_argument("--brain-ip", required=True)
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--concurrency", type=int, default=6)
    parser.add_argument("--passes", type=int, default=2)
    parser.add_argument("--tg-id", type=int, default=0, help="Limit reconciliation to one exact user.")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args()

    if args.apply and args.confirm != APPLY_CONFIRMATION:
        raise SystemExit(f"--apply requires --confirm {APPLY_CONFIRMATION}")

    password = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_passwords(Path(args.passwords))
    if not password:
        raise SystemExit("Missing brain password.")

    ssh = paramiko.SSHClient()
    configure_ssh_host_key_policy(ssh)
    ssh.connect(
        args.brain_ip,
        port=args.ssh_port,
        username=args.ssh_user,
        password=password,
        timeout=30,
        banner_timeout=30,
        auth_timeout=30,
    )
    try:
        code, _out, error = _run(
            ssh,
            "test -x /root/portal_bot/venv/bin/python",
            timeout=60,
        )
        if code != 0:
            raise SystemExit(error.strip() or "Production Python environment is unavailable.")

        sftp = ssh.open_sftp()
        try:
            with sftp.file("/root/portal_bot/portal_sync_users_to_nodes.py", "w") as handle:
                handle.write(SYNC_SNIPPET.strip() + "\n")
        finally:
            sftp.close()

        env = (
            f"export SYNC_APPLY={'1' if args.apply else '0'} "
            f"SYNC_TG_ID={int(args.tg_id)} "
            f"SYNC_CONCURRENCY={max(1, min(int(args.concurrency), 8))} "
            f"SYNC_PASSES={max(1, min(int(args.passes), 5))};"
        )
        command = (
            f"cd /root/portal_bot && {env} "
            "/root/portal_bot/venv/bin/python /root/portal_bot/portal_sync_users_to_nodes.py"
        )
        code, out, error = _run(ssh, command, timeout=3600)
        if out.strip():
            print(out.strip())
        if code != 0:
            raise SystemExit(error.strip() or f"reconciliation failed rc={code}")
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
