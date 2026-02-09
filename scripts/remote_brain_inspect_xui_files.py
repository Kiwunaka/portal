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
        cmds = [
            "ls -la /etc/x-ui || true",
            "find /etc/x-ui -maxdepth 2 -type f -printf '%p\\n' 2>/dev/null | sort | head -200 || true",
            "ls -la /usr/local/x-ui || true",
            "find /usr/local/x-ui -maxdepth 2 -type f -printf '%p\\n' 2>/dev/null | sort | head -200 || true",
            "(systemctl cat x-ui || true) | head -160",
            "echo '--- /etc/default/x-ui ---'; (cat /etc/default/x-ui 2>/dev/null || true) | head -200",
            "echo '--- /usr/local/x-ui/bin/config.json ---'; cat /usr/local/x-ui/bin/config.json 2>/dev/null || true",
            "echo '--- /usr/local/x-ui/bin/README.md (head) ---'; (sed -n '1,200p' /usr/local/x-ui/bin/README.md 2>/dev/null || true) | head -200",
            "grep -n -E 'subport|subPort|SubPort|SUB' /usr/local/x-ui/x-ui.sh 2>/dev/null | head -120 || true",
            "sed -n '740,860p' /usr/local/x-ui/x-ui.sh 2>/dev/null | head -160 || true",
            "grep -R --line-number -E 'subPort|subEnable|subListen|subDomain|subPath' /etc/x-ui /usr/local/x-ui 2>/dev/null | head -200 || true",
            "grep -R --line-number -E '\\b2096\\b' /etc/x-ui /usr/local/x-ui 2>/dev/null | head -200 || true",
        ]
        for c in cmds:
            print(f"== {c} ==")
            print(_run(ssh, c, timeout=120))
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
