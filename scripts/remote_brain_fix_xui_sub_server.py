from __future__ import annotations

import os
import time
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


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 120) -> tuple[int, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    return code, (out or err)


def main() -> int:
    try:
        import sys

        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_passwords(DEFAULT_PASSWORDS)
    if not pw:
        raise SystemExit("Missing brain password.")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("82.21.114.104", port=29374, username="root", password=pw, timeout=30, banner_timeout=30, auth_timeout=30)
    try:
        ts = time.strftime("%Y%m%d-%H%M%S")

        # Make sure sqlite3 exists, then snapshot the DB.
        _run(ssh, "DEBIAN_FRONTEND=noninteractive apt-get update -y >/dev/null 2>&1 || true", timeout=600)
        _run(ssh, "DEBIAN_FRONTEND=noninteractive apt-get install -y sqlite3 >/dev/null 2>&1 || true", timeout=600)
        code, out = _run(ssh, f"cp /etc/x-ui/x-ui.db /etc/x-ui/x-ui.db.bak-{ts}", timeout=60)
        if code != 0:
            raise SystemExit(f"DB backup failed: {out}")

        # Disable x-ui's built-in subscription server (it defaults to :2096 and conflicts with our portal).
        sql = (
            "BEGIN;"
            "DELETE FROM settings WHERE key IN ('subEnable','subPort');"
            "INSERT INTO settings(key,value) VALUES('subEnable','false');"
            "INSERT INTO settings(key,value) VALUES('subPort','2097');"
            "COMMIT;"
        )
        code, out = _run(ssh, f"sqlite3 /etc/x-ui/x-ui.db \"{sql}\"", timeout=30)
        if code != 0:
            raise SystemExit(f"sqlite update failed: {out}")

        _run(ssh, "systemctl daemon-reload >/dev/null 2>&1 || true", timeout=60)
        _run(ssh, "systemctl restart x-ui || true", timeout=60)
        _, active = _run(ssh, "systemctl is-active x-ui || true", timeout=30)
        print(f"x-ui active: {active.strip()}")
        _, listen = _run(ssh, "ss -tlnp | grep -E ':(2096|2097|34137)\\b' || true", timeout=30)
        print(listen.strip())

        # Show effective settings keys (only the relevant ones).
        _, s = _run(
            ssh,
            "sqlite3 /etc/x-ui/x-ui.db \"select key,value from settings where key in ('webPort','webBasePath','subEnable','subPort') order by key;\"",
            timeout=30,
        )
        print(s.strip())
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())

