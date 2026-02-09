from __future__ import annotations

import argparse
import os
from pathlib import Path

import paramiko


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


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 120) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def main() -> int:
    ap = argparse.ArgumentParser(description="Sanity-check nodes table fields without leaking secrets.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--db", default="/root/portal_bot/portal.db")
    args = ap.parse_args()

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_passwords(Path(args.passwords))
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
        _run(ssh, "DEBIAN_FRONTEND=noninteractive apt-get install -y sqlite3 >/dev/null 2>&1 || true", timeout=900)
        sql = (
            "select code,"
            " vless_port,"
            " inbound_id,"
            " length(coalesce(panel_base_url,'')) as base_len,"
            " length(coalesce(panel_path,'')) as path_len,"
            " length(coalesce(panel_user,'')) as user_len,"
            " length(coalesce(panel_pass,'')) as pass_len"
            " from nodes where code in ('pl','pl_free','free') order by code;"
        )
        cmd = f"sqlite3 {args.db} \"{sql}\""
        code, out, err = _run(ssh, cmd, timeout=60)
        if code != 0:
            raise SystemExit(err.strip() or out.strip())
        print(out.strip())
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
