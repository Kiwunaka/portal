from __future__ import annotations

import argparse
import os
from pathlib import Path

import paramiko


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
    ap = argparse.ArgumentParser(description="Check subscription Profile-Update-Interval header.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--domain", default="api.pokrov.space")
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    args = ap.parse_args()

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_password(Path(args.passwords))
    if not pw:
        raise SystemExit("Missing brain password.")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
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
        cmd = (
            "TOK=$(runuser -u postgres -- psql -d portal -tAc "
            "\"select sub_token from users where is_active=true and sub_token is not null order by created_at asc limit 1\" "
            "2>/dev/null | tr -d '[:space:]'); "
            "if [ -z \"$TOK\" ]; then echo no_token; exit 2; fi; "
            f"curl -k -sI --resolve {args.domain}:443:127.0.0.1 https://{args.domain}/s8Kx2mP7qR4wT/$TOK | grep -i '^Profile-Update-Interval:' || true"
        )
        _, out, err = _run(ssh, cmd, timeout=120)
        print((out.strip() or err.strip()).strip())
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
