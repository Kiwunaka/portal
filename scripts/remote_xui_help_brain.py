from __future__ import annotations

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
    configure_ssh_host_key_policy(ssh)
    ssh.connect("82.21.114.104", port=29374, username="root", password=pw, timeout=30, banner_timeout=30, auth_timeout=30)
    try:
        print("== global help (-h) ==")
        print(_run(ssh, "/usr/local/x-ui/x-ui -h 2>&1 | head -260 || true", timeout=60))
        print("== run help ==")
        print(_run(ssh, "/usr/local/x-ui/x-ui run -h 2>&1 | head -260 || true", timeout=60))
        print("== /usr/local/x-ui/x-ui (no args) ==")
        print(_run(ssh, "/usr/local/x-ui/x-ui 2>&1 | head -200 || true", timeout=60))
        print("== setting help ==")
        print(_run(ssh, "/usr/local/x-ui/x-ui setting -h 2>&1 | head -200 || true", timeout=60))
        print("== setting show ==")
        print(_run(ssh, "/usr/local/x-ui/x-ui setting -show true 2>&1 | head -120 || true", timeout=60))
        print("== version ==")
        print(_run(ssh, "/usr/local/x-ui/x-ui -v 2>/dev/null || /usr/local/x-ui/x-ui version 2>/dev/null || true", timeout=30))
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
