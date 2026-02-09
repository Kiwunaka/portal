from __future__ import annotations

"""
Stop the Telegram bot on the OLD server (production) without touching x-ui / user traffic.

This script only manages systemd units and reads status/logs.
It does not edit any files on the old server.

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
        # Determine unit name (portal-bot is expected).
        candidates = ["portal-bot", "portal-bot.service", "bot", "bot.service"]
        unit = ""
        for c in candidates:
            code, out, err = _run(ssh, f"systemctl status {c} --no-pager >/dev/null 2>&1; echo $?", timeout=30)
            if out.strip().endswith("0") or out.strip().endswith("3"):  # 3 = inactive but exists
                unit = c.replace(".service", "")
                break
        if not unit:
            # last resort: search by name
            code, out, err = _run(ssh, "systemctl list-unit-files | grep -E '^portal-bot\\.service' || true", timeout=30)
            if out.strip():
                unit = "portal-bot"

        if not unit:
            raise SystemExit("Could not find portal-bot systemd unit on old server.")

        _run(ssh, f"systemctl stop {unit}", timeout=60)
        code, out, err = _run(ssh, f"systemctl is-active {unit} || true", timeout=30)
        state = (out.strip() or err.strip()).strip()
        print(f"{unit}: {state}")
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())

