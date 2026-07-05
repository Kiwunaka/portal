from __future__ import annotations

import argparse
import os
import shlex
from pathlib import Path

import paramiko
from ssh_host_keys import configure_ssh_host_key_policy


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"


def _parse_password(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in raw.splitlines()]
    for i, ln in enumerate(lines):
        if "BRAINnode" not in ln:
            continue
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


def main() -> int:
    ap = argparse.ArgumentParser(description="Inspect user/payment state on brain postgres.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--tg-id", type=int, required=True)
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--db-name", default="portal")
    args = ap.parse_args()

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_password(Path(args.passwords))
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
        tid = int(args.tg_id)
        db_arg = shlex.quote(str(args.db_name))
        queries = [
            (
                "user",
                (
                    "select tg_id, username, sub_type, is_active, expiry_at, stars_paid, first_purchase_done, "
                    "channel_bonus_claimed_at, channel_bonus_active, channel_bonus_expires_at "
                    f"from users where tg_id={tid};"
                ),
            ),
            (
                "pay_attempts",
                (
                    "select id, source, plan_code, amount_stars, currency, status, "
                    "coalesce(invoice_payload,'') as invoice_payload, started_at, paid_at, updated_at "
                    f"from pay_attempts where tg_id={tid} order by id desc limit 20;"
                ),
            ),
            (
                "events",
                (
                    "select id, event_name, source, created_at, left(coalesce(meta_json,''), 220) as meta_json "
                    f"from events where tg_id={tid} order by id desc limit 30;"
                ),
            ),
        ]
        for label, sql in queries:
            print(f"\n=== {label} ===")
            cmd = (
                f"runuser -u postgres -- psql -d {db_arg} -P pager=off "
                f"-c \"{sql}\" 2>/dev/null || true"
            )
            _, out, err = _run(ssh, cmd, timeout=120)
            print((out.strip() or err.strip()).strip())
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
