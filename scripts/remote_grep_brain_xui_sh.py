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


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 60) -> str:
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
        print("== 2096 ==")
        print(_run(ssh, "grep -n '2096' /usr/local/x-ui/x-ui.sh | head -50 || true", timeout=30))
        print("== sub ==")
        print(_run(ssh, "grep -ni 'sub' /usr/local/x-ui/x-ui.sh | head -80 || true", timeout=30))
        print("== subport/SUB ==")
        print(_run(ssh, "grep -ni 'subport\\|subPort\\|SUB' /usr/local/x-ui/x-ui.sh | head -120 || true", timeout=30))
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
