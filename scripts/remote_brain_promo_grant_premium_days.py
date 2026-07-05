from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta, timezone
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


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 300) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def main() -> int:
    ap = argparse.ArgumentParser(description="Promo: grant PAID access for N days to all users except manual ones.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--db", default="/root/portal_bot/portal.db")
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--restart", default="portal-api,portal-bot")
    args = ap.parse_args()

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_passwords(Path(args.passwords))
    if not pw:
        raise SystemExit("Missing brain password.")

    expiry = datetime.now(timezone.utc) + timedelta(days=int(args.days))
    expiry_str = expiry.replace(tzinfo=None).isoformat(sep=" ", timespec="seconds")

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_path = f"/root/backups/portal.db.promo-{ts}.db"

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
        _run(ssh, "DEBIAN_FRONTEND=noninteractive apt-get update -y >/dev/null 2>&1 || true", timeout=900)
        _run(ssh, "DEBIAN_FRONTEND=noninteractive apt-get install -y sqlite3 >/dev/null 2>&1 || true", timeout=900)
        _run(ssh, "mkdir -p /root/backups", timeout=60)

        # Backup first (cheap and safe).
        code, out, err = _run(ssh, f"sqlite3 {args.db} \".backup {backup_path}\"", timeout=120)
        if code != 0:
            raise SystemExit(err.strip() or out.strip() or "backup failed")

        # Apply promo:
        # - Exclude manual accounts (they are special/pinned to old configs).
        # - Activate everyone else + set expiry.
        # - Upgrade FREE -> PAID for the promo period.
        promo_sql = (
            "update users "
            f"set is_active=1, expiry_at='{expiry_str}', "
            "sub_type=(case when upper(coalesce(sub_type,''))='FREE' then 'PAID' else sub_type end) "
            "where lower(coalesce(sub_type,''))!='manual';"
            "select 'users_total=' || count(*) from users;"
            "select 'users_manual=' || count(*) from users where lower(coalesce(sub_type,''))='manual';"
            "select 'users_free=' || count(*) from users where upper(coalesce(sub_type,''))='FREE';"
            "select 'users_active=' || count(*) from users where is_active=1;"
        )
        cmd = f"sqlite3 {args.db} \"{promo_sql}\""
        code, out, err = _run(ssh, cmd, timeout=120)
        if code != 0:
            raise SystemExit(err.strip() or out.strip() or "promo update failed")
        print(out.strip())
        print(f"expiry_at_utc={expiry_str}")
        print(f"backup={backup_path}")

        for unit in [u.strip() for u in (args.restart or '').split(',') if u.strip()]:
            _run(ssh, f"systemctl restart {unit} >/dev/null 2>&1 || true", timeout=60)
            _, out, err = _run(ssh, f"systemctl is-active {unit} || true", timeout=30)
            print(f"{unit}: {(out.strip() or err.strip()).strip()}")

        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())

