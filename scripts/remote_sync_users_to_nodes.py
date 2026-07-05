from __future__ import annotations

"""
Deploy minimal control-plane code + DB to the brain node and reconcile users to desired node pools.

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
from ssh_host_keys import configure_ssh_host_key_policy


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"


SYNC_SCRIPT = """from __future__ import annotations

import asyncio
import os

from db import SessionLocal, init_db
from models import User
from node_policy import canonical_free_node_code, paid_pool_nodes, user_uses_free_pool
from nodes_repo import enabled_nodes
from panel_client import PanelClient


def _node_code(node) -> str:
    return str(getattr(node, "code", "") or "").strip().lower()


def _desired_codes_for_user(user: User, nodes: list) -> set[str]:
    if not bool(getattr(user, "is_active", True)):
        return set()
    if user_uses_free_pool(user):
        code = str(canonical_free_node_code(nodes) or "").strip().lower()
        return {code} if code else set()
    return {_node_code(node) for node in paid_pool_nodes(nodes) if _node_code(node)}


async def _disable_existing(panel: PanelClient, user: User) -> bool:
    found = await panel.find_clients_by_identity(
        tg_id=int(user.tg_id),
        client_uuid=str(user.uuid or ""),
        email=str(user.email or ""),
        include_disabled=True,
    )
    if not found:
        return True
    ok_all = True
    sub_id = str(getattr(user, "sub_token", "") or user.tg_id)
    for inbound_id, client in found:
        flow = panel._managed_flow_for_inbound(int(inbound_id))
        try:
            ok = await panel.update_client_enable(
                dict(client),
                False,
                sub_id=sub_id,
                inbound_id=int(inbound_id),
                flow=flow,
            )
        except TypeError:
            ok = await panel.update_client_enable(dict(client), False, sub_id=sub_id)
        ok_all = ok_all and bool(ok)
    return ok_all


async def main() -> int:
    init_db()
    s = SessionLocal()
    try:
        nodes = [node for node in enabled_nodes(s) if _node_code(node)]
        users = s.query(User).order_by(User.created_at.asc()).all()
    finally:
        s.close()

    if not nodes:
        print("No nodes in DB (nodes table empty).")
        return 2

    desired_by_tg = {int(user.tg_id): _desired_codes_for_user(user, nodes) for user in users}
    panels = [PanelClient(n) for n in nodes]
    try:
        for p in panels:
            ok = await p.login()
            if not ok:
                print(f"WARNING: login failed node={p.node.code}")

        sem = asyncio.Semaphore(max(1, min(int(os.getenv("SYNC_CONCURRENCY", "2")), 8)))
        max_passes = int(os.getenv("SYNC_PASSES", "3"))

        async def reconcile_one(p: PanelClient, u: User) -> bool:
            async with sem:
                code = _node_code(p.node)
                desired_codes = desired_by_tg.get(int(u.tg_id), set())
                if code not in desired_codes:
                    return await _disable_existing(p, u)
                sub_id = str(getattr(u, "sub_token", "") or u.tg_id)
                return await p.ensure_client(
                    tg_id=int(u.tg_id),
                    client_uuid=str(u.uuid or ""),
                    email=str(u.email or ""),
                    sub_id=sub_id,
                    enable=True,
                )

        any_fail = 0
        for p in panels:
            pending = [u for u in users if str(getattr(u, "uuid", "") or "").strip()]
            ok = 0
            for attempt in range(1, max_passes + 1):
                if not pending:
                    break
                results = await asyncio.gather(*(reconcile_one(p, u) for u in pending))
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
            desired_count = sum(1 for u in users if _node_code(p.node) in desired_by_tg.get(int(u.tg_id), set()))
            print(f"node={p.node.code}: desired={desired_count} reconciled={ok} fail={fail}")
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
    configure_ssh_host_key_policy(ssh)
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
