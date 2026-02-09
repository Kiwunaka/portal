from __future__ import annotations

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


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 120) -> str:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    return out or err


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
        print("== tables ==")
        print(_run(ssh, "sqlite3 /etc/x-ui/x-ui.db \"select name from sqlite_master where type='table' order by name;\" | head -200", timeout=60))
        print("== settings table ==")
        print(_run(ssh, "sqlite3 /etc/x-ui/x-ui.db \"select key,value from settings order by key;\" 2>/dev/null || true", timeout=60))
        print("== settings schema ==")
        print(_run(ssh, "sqlite3 /etc/x-ui/x-ui.db \"pragma table_info(settings);\" 2>/dev/null || true", timeout=60))
        print("== users schema ==")
        print(_run(ssh, "sqlite3 /etc/x-ui/x-ui.db \"pragma table_info(users);\" 2>/dev/null || true", timeout=60))
        print("== sub server fields (if present) ==")
        print(
            _run(
                ssh,
                "sqlite3 /etc/x-ui/x-ui.db \"select subEnable,subPort,subListen,subDomain,subPath from users limit 1;\" 2>/dev/null || true",
                timeout=60,
            )
        )
        # Look for a config table that might contain subPort.
        print("== likely config rows (grep sub) ==")
        print(_run(ssh, "sqlite3 /etc/x-ui/x-ui.db \"select name from sqlite_master where type='table' and name like '%setting%';\" 2>/dev/null || true", timeout=60))
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
