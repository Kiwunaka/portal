from __future__ import annotations

"""
Read-only inventory of a few old-server paths.

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


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 120) -> tuple[int, str, str]:
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
        paths = ["/root/certs_keep", "/root/portal_bot", "/root/backups", "/root"]
        for p in paths:
            print(f"== {p} ==")
            code, out, err = _run(ssh, f"ls -la {p} 2>/dev/null | head -80 || echo MISSING", timeout=60)
            print((out.strip() or err.strip()).strip())
            print()

        # Sizes (best-effort).
        print("== Sizes ==")
        code, out, err = _run(
            ssh,
            "du -sh /root/certs_keep /root/portal_bot /root/backups 2>/dev/null || true",
            timeout=60,
        )
        print((out.strip() or err.strip()).strip())
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())

