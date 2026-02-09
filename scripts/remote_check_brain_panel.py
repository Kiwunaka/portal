from __future__ import annotations

"""
Check brain node 3x-ui panel process and local port/path availability.
"""

import json
import os
from pathlib import Path

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]


def _parse_brain_pw() -> str:
    p = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
    if not p.exists():
        return ""
    lines = [l.strip() for l in p.read_text(encoding="utf-8", errors="replace").splitlines()]
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
    facts_path = REPO_ROOT / "node_facts-20260207-004104.json"
    d = json.loads(facts_path.read_text(encoding="utf-8", errors="replace"))
    r = next(x for x in d.get("results", []) if x.get("code") == "brain")
    panel_port = int(r["panel_port"])
    panel_path = str(r["panel_path"])

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_brain_pw()
    if not pw:
        raise SystemExit("Missing brain password.")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("82.21.114.104", port=29374, username="root", password=pw, timeout=30, banner_timeout=30, auth_timeout=30)
    try:
        print("[x-ui]", _run(ssh, "systemctl is-active x-ui || true"))
        print("[panel_port_listen]", _run(ssh, f"ss -tlnp | grep -E ':{panel_port}\\b' || true"))
        print("[curl_root]", _run(ssh, f"curl -fsS http://127.0.0.1:{panel_port}/ 2>/dev/null | head -3 || true"))
        print("[curl_login]", _run(ssh, f"curl -fsS http://127.0.0.1:{panel_port}/{panel_path}/login 2>/dev/null | head -3 || true"))
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())

