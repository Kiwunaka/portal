from __future__ import annotations

import argparse
import os
from pathlib import Path

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"

SERVICE_TEXT = """[Unit]
Description=Portal worker (background jobs)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/portal_bot
EnvironmentFile=-/root/portal_bot/.env
ExecStart=/root/portal_bot/venv/bin/python /root/portal_bot/worker.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""


def _parse_password(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in raw.splitlines()]
    for i, ln in enumerate(lines):
        if "BRAINnode" not in ln:
            continue
        for j in range(i + 1, min(i + 30, len(lines))):
            v = lines[j].strip()
            if v and not v.startswith("ssh-ed25519 "):
                return v
    return ""


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 120) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def _put_text(sftp: paramiko.SFTPClient, remote_path: str, content: str) -> None:
    with sftp.file(remote_path, "w") as f:
        f.write(content)


def main() -> int:
    ap = argparse.ArgumentParser(description="Install and enable portal-worker.service on brain.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument(
        "--ensure-embedded-off",
        action="store_true",
        help="Set WORKER_EMBEDDED=false in /root/portal_bot/.env to avoid duplicate jobs.",
    )
    args = ap.parse_args()

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_password(Path(args.passwords))
    if not pw:
        raise SystemExit("Missing brain password.")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        args.brain_ip,
        port=args.ssh_port,
        username=args.ssh_user,
        password=pw,
        timeout=30,
        banner_timeout=30,
        auth_timeout=30,
    )
    try:
        code, _, _ = _run(ssh, "test -f /root/portal_bot/worker.py", timeout=30)
        if code != 0:
            raise SystemExit("Missing /root/portal_bot/worker.py on remote host.")
        code, _, _ = _run(ssh, "test -x /root/portal_bot/venv/bin/python", timeout=30)
        if code != 0:
            raise SystemExit("Missing /root/portal_bot/venv/bin/python on remote host.")

        if args.ensure_embedded_off:
            _run(
                ssh,
                (
                    "if grep -q '^WORKER_EMBEDDED=' /root/portal_bot/.env; then "
                    "  sed -i 's/^WORKER_EMBEDDED=.*/WORKER_EMBEDDED=false/' /root/portal_bot/.env; "
                    "else "
                    "  printf '\\nWORKER_EMBEDDED=false\\n' >> /root/portal_bot/.env; "
                    "fi"
                ),
                timeout=30,
            )

        sftp = ssh.open_sftp()
        try:
            _put_text(sftp, "/etc/systemd/system/portal-worker.service", SERVICE_TEXT)
        finally:
            sftp.close()

        _run(ssh, "systemctl daemon-reload", timeout=60)
        _run(ssh, "systemctl enable portal-worker", timeout=60)
        _run(ssh, "systemctl restart portal-worker", timeout=60)

        _, out_active, err_active = _run(ssh, "systemctl is-active portal-worker || true", timeout=30)
        print(f"portal-worker: {(out_active.strip() or err_active.strip()).strip()}")

        _, out_env, _ = _run(ssh, "grep -E '^WORKER_EMBEDDED=' /root/portal_bot/.env || true", timeout=30)
        if out_env.strip():
            print(out_env.strip())

        _, out_status, _ = _run(ssh, "systemctl status portal-worker --no-pager -l | head -n 20 || true", timeout=60)
        print(out_status.encode("ascii", "ignore").decode())
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
