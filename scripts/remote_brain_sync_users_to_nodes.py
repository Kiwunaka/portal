from __future__ import annotations

import argparse
import os
from pathlib import Path

import paramiko
from ssh_host_keys import configure_ssh_host_key_policy


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"


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


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 600) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


SYNC_SNIPPET = r"""
import asyncio, os
from datetime import datetime
from db import SessionLocal, init_db
from models import User
from nodes_repo import enabled_nodes
from panel_client import PanelClient

async def main():
    init_db()
    s = SessionLocal()
    try:
        nodes = enabled_nodes(s)
        all_users = (
            s.query(User)
            .order_by(User.created_at.asc())
            .all()
        )
    finally:
        s.close()

    if not nodes:
        print('No nodes in DB.')
        return 2
    has_free_pool = any('free' in ((getattr(n, 'code', '') or '').lower()) for n in nodes)
    if not has_free_pool:
        print('warning: no enabled free-pool nodes detected; FREE users will remain without node assignments')

    panels = [PanelClient(n) for n in nodes]
    try:
        for p in panels:
            await p.login()

        sem = asyncio.Semaphore(int(os.getenv('SYNC_CONCURRENCY', '6')))
        max_passes = int(os.getenv('SYNC_PASSES', '2'))

        async def sync_one(p, u):
            async with sem:
                sub_id = u.sub_token or str(u.tg_id)
                return await p.ensure_client(
                    tg_id=u.tg_id,
                    client_uuid=u.uuid,
                    email=u.email,
                    sub_id=sub_id,
                    enable=bool(u.is_active),
                )

        any_fail = 0
        for p in panels:
            code = (p.node.code or '').lower().strip()
            is_free_node = 'free' in code
            if is_free_node:
                # Dedicated FREE pools receive only FREE users.
                target = [u for u in all_users if (u.sub_type or '').upper() == 'FREE']
            else:
                # Other countries are PAID-only.
                target = [u for u in all_users if (u.sub_type or '').upper() != 'FREE']

            pending = list(target)
            ok = 0
            for attempt in range(1, max_passes + 1):
                if not pending:
                    break
                results = await asyncio.gather(*(sync_one(p, u) for u in pending))
                next_pending = []
                for u, r in zip(pending, results):
                    if r:
                        ok += 1
                    else:
                        next_pending.append(u)
                pending = next_pending
                if pending and attempt < max_passes:
                    await asyncio.sleep(1.0)
            fail = len(pending)
            any_fail += fail
            mode = "free" if is_free_node else "paid"
            print(f'node={p.node.code} mode={mode}: ok={ok} fail={fail}')
            if pending:
                preview = ",".join(str(u.tg_id) for u in pending[:20])
                print(f'node={p.node.code}: failed_tg_ids={preview}')
        return 0 if any_fail == 0 else 1
    finally:
        for p in panels:
            await p.close()

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Run sync of users->nodes directly on brain (no DB upload).")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--passes", type=int, default=2)
    args = ap.parse_args()

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_passwords(Path(args.passwords))
    if not pw:
        raise SystemExit("Missing brain password.")

    ssh = paramiko.SSHClient()
    configure_ssh_host_key_policy(ssh)
    ssh.connect(
        args.brain_ip,
        port=args.ssh_port,
        username=args.ssh_user,
        password=pw,
        timeout=30,
        banner_timeout=30,
        auth_timeout=30,
    )
    try:
        # Ensure venv exists; don't reinstall deps unless missing.
        _run(ssh, "test -x /root/portal_bot/venv/bin/python || (cd /root/portal_bot && python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt)", timeout=1800)

        # Upload sync script to avoid quoting/escaping issues with `python -c`.
        sftp = ssh.open_sftp()
        try:
            with sftp.file("/root/portal_bot/portal_sync_users_to_nodes.py", "w") as f:
                f.write(SYNC_SNIPPET.strip() + "\n")
        finally:
            sftp.close()

        env = f"DATABASE_URL=sqlite:////root/portal_bot/portal.db SYNC_CONCURRENCY={int(args.concurrency)} SYNC_PASSES={int(args.passes)}"
        cmd = f"cd /root/portal_bot && {env} . venv/bin/activate && python /root/portal_bot/portal_sync_users_to_nodes.py"
        code, out, err = _run(ssh, cmd, timeout=3600)
        if out.strip():
            print(out.strip())
        if code != 0:
            raise SystemExit(err.strip() or f"sync failed rc={code}")
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
