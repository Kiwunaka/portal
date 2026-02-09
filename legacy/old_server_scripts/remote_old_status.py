from __future__ import annotations

"""
Check OLD server status (read-only).

Required env:
- OLD_SSH_HOST
- OLD_SSH_PASS
Optional:
- OLD_SSH_PORT (default 29374)
- OLD_SSH_USER (default root)
"""

import os

import paramiko


def _require_env(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        raise SystemExit(f"Missing required env var: {name}")
    return v


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 60) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def main() -> int:
    host = _require_env("OLD_SSH_HOST")
    password = _require_env("OLD_SSH_PASS")
    port = int(os.getenv("OLD_SSH_PORT", "29374"))
    user = os.getenv("OLD_SSH_USER", "root")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=user, password=password, timeout=30, banner_timeout=30, auth_timeout=30)
    try:
        cmds = {
            "x-ui": "systemctl is-active x-ui 2>/dev/null || echo unknown",
            "portal-api": "systemctl is-active portal-api 2>/dev/null || echo unknown",
            "portal-bot": "systemctl is-active portal-bot 2>/dev/null; true",
            "listen": "ss -tlnp | grep -E ':(443|2096|8444)\\b' || true",
        }
        for k, c in cmds.items():
            code, out, err = _run(ssh, c, timeout=60)
            val = (out.strip() or err.strip()).strip()
            print(f"[{k}] {val}")
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
