from __future__ import annotations

"""
Deploy minimal control-plane code + DB to the brain node and sync all users to all enabled nodes.

This does NOT start the Telegram bot and does NOT touch the old production server.

Prereqs:
- Fresh Ubuntu brain node with password SSH access.
- Worker nodes already bootstrapped and their panel ports allowlisted to brain IP.
"""

import argparse
import io
import os
import posixpath
import re
from pathlib import Path

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"


SYNC_SCRIPT = """from __future__ import annotations

import asyncio
import os
import time

from db import SessionLocal, init_db
from models import User
from nodes_repo import enabled_nodes
from panel_client import PanelClient


async def main() -> int:
    init_db()
    s = SessionLocal()
    try:
        nodes = enabled_nodes(s)
        users = s.query(User).order_by(User.created_at.asc()).all()
    finally:
        s.close()

    if not nodes:
        print("No nodes in DB (nodes table empty).")
        return 2

    panels = [PanelClient(n) for n in nodes]
    try:
        for p in panels:
            ok = await p.login()
            if not ok:
                print(f"WARNING: login failed node={p.node.code}")

        sem = asyncio.Semaphore(int(os.getenv("SYNC_CONCURRENCY", "4")))
        max_passes = int(os.getenv("SYNC_PASSES", "3"))

        async def sync_one(p: PanelClient, u: User) -> bool:
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
            pending = list(users)
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
                    # Panels sometimes drop requests under concurrency; retry after a short pause.
                    await asyncio.sleep(1.0)
            fail = len(pending)
            any_fail += fail
            print(f"node={p.node.code}: ok={ok} fail={fail}")
        # If any node had failures, treat as error.
        return 0 if any_fail == 0 else 1
    finally:
        for p in panels:
            await p.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
"""


def _parse_passwords(path: Path) -> dict[str, str]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in raw.splitlines()]
    out: dict[str, str] = {}
    markers = {"brain": "BRAINnode", "us": "USnode", "pl": "PLnode", "it": "ITnode", "free": "Free Node"}
    for code, marker in markers.items():
        try:
            idx = next(i for i, ln in enumerate(lines) if marker in ln)
        except StopIteration:
            continue
        pw = ""
        for j in range(idx + 1, min(idx + 12, len(lines))):
            ln = lines[j]
            if not ln or ln.startswith("ssh-ed25519 "):
                continue
            pw = ln
            break
        if pw:
            out[code] = pw
    return out


def _sftp_mkdir_p(sftp: paramiko.SFTPClient, remote_dir: str) -> None:
    parts: list[str] = []
    cur = remote_dir
    while cur not in {"", "/"}:
        parts.append(cur)
        cur = posixpath.dirname(cur)
    for d in reversed(parts):
        try:
            sftp.stat(d)
        except IOError:
            try:
                sftp.mkdir(d)
            except IOError:
                pass


def _sftp_put_file(sftp: paramiko.SFTPClient, local_path: Path, remote_path: str) -> None:
    _sftp_mkdir_p(sftp, posixpath.dirname(remote_path))
    sftp.put(str(local_path), remote_path)


def _sftp_put_text(sftp: paramiko.SFTPClient, remote_path: str, content: str) -> None:
    _sftp_mkdir_p(sftp, posixpath.dirname(remote_path))
    with sftp.file(remote_path, "w") as f:
        f.write(content)


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 600) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--db", default=str(REPO_ROOT / "portal.db.cluster.db"))
    ap.add_argument("--concurrency", type=int, default=4)
    args = ap.parse_args()

    pw = os.getenv("NODE_PASS_BRAIN", "").strip()
    if not pw:
        pw = _parse_passwords(Path(args.passwords)).get("brain", "")
    if not pw:
        raise SystemExit("Missing brain password (set NODE_PASS_BRAIN or add to PASSWORDS.txt).")

    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"DB file not found: {db_path}")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(args.brain_ip, port=args.ssh_port, username=args.ssh_user, password=pw, timeout=30, banner_timeout=30, auth_timeout=30)
    try:
        # Ensure python/venv on the node
        cmds = [
            "DEBIAN_FRONTEND=noninteractive apt-get update -y",
            "DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv python3-pip ca-certificates",
            "mkdir -p /root/portal_bot",
        ]
        for c in cmds:
            code, out, err = _run(ssh, c, timeout=900)
            if code != 0:
                raise RuntimeError(f"Remote command failed: {c}\n{err.strip()}")

        sftp = ssh.open_sftp()
        try:
            # Upload portal_bot code (only *.py + requirements.txt)
            local_portal = REPO_ROOT / "portal_bot"
            for p in sorted(local_portal.glob("*.py")):
                _sftp_put_file(sftp, p, f"/root/portal_bot/{p.name}")
            _sftp_put_file(sftp, local_portal / "requirements.txt", "/root/portal_bot/requirements.txt")
            _sftp_put_file(sftp, db_path, "/root/portal_bot/portal.db")
            _sftp_put_text(sftp, "/root/portal_bot/sync_users_to_nodes.py", SYNC_SCRIPT)
        finally:
            sftp.close()

        # Install deps in venv
        code, out, err = _run(
            ssh,
            "cd /root/portal_bot && (test -d venv || python3 -m venv venv) && . venv/bin/activate && pip install -r requirements.txt",
            timeout=1800,
        )
        if code != 0:
            raise RuntimeError(f"pip install failed: {err.strip()}")

        # Run sync
        env = f"DATABASE_URL=sqlite:////root/portal_bot/portal.db SYNC_CONCURRENCY={int(args.concurrency)}"
        code, out, err = _run(
            ssh,
            f"cd /root/portal_bot && {env} . venv/bin/activate && python3 sync_users_to_nodes.py",
            timeout=3600,
        )
        print(out.strip())
        if code != 0:
            print(err.strip())
            raise SystemExit(code)
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
