from __future__ import annotations

import os
from pathlib import Path

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"


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


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 60) -> str:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    return out or err


def main() -> int:
    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_passwords(DEFAULT_PASSWORDS).get("brain", "")
    if not pw:
        raise SystemExit("Missing brain password.")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("82.21.114.104", port=29374, username="root", password=pw, timeout=30, banner_timeout=30, auth_timeout=30)
    try:
        print("== unit-files ==")
        print(_run(ssh, "systemctl list-unit-files | grep -Ei 'x-ui|3x|xui' || true"))
        print("== /etc/systemd/system matches ==")
        print(_run(ssh, "ls -la /etc/systemd/system | grep -Ei 'x-ui|3x|xui' || true"))
        print("== /etc/systemd/system head ==")
        print(_run(ssh, "ls -la /etc/systemd/system | head -40 || true"))
        print("== /lib/systemd/system matches ==")
        print(_run(ssh, "ls -la /lib/systemd/system | grep -Ei 'x-ui|3x|xui' || true"))
        print("== /usr/local/x-ui ==")
        print(_run(ssh, "ls -la /usr/local/x-ui 2>/dev/null || echo NO_DIR"))
        print("== units ==")
        print(_run(ssh, "systemctl list-units --all | grep -Ei 'x-ui|3x|xui' || true"))
        print("== processes ==")
        print(_run(ssh, "ps aux | grep -Ei 'x-ui|3x-ui|xray' | grep -v grep || true"))
        print("== ports ==")
        print(_run(ssh, "ss -tlnp | head -120"))
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
