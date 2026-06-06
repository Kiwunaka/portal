from __future__ import annotations

import argparse
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


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 120) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def main() -> int:
    ap = argparse.ArgumentParser(description="Patch brain Caddyfile so WebApp can call /api same-origin on :8444.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--domain", default="pokrov.space")
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--api-upstream", default="127.0.0.1:8080")
    ap.add_argument("--webapp-root", default="/var/www/portal/webapp")
    ap.add_argument("--marketing-root", default="/var/www/portal/marketing")
    args = ap.parse_args()

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_passwords(Path(args.passwords))
    if not pw:
        raise SystemExit("Missing brain password.")

    caddyfile = f"""{{
  servers {{
    protocols h1 h2
  }}
}}

{args.domain}:8444 {{
  tls /etc/caddy/certs/fullchain.pem /etc/caddy/certs/privkey.pem

  encode gzip
  header Alt-Svc "clear"

  # Keep WebApp same-origin with the API to avoid CORS issues in Telegram.
  # NOTE: use `handle` (not `handle_path`) so upstream keeps the `/api/...` prefix.
  handle /api/* {{
    reverse_proxy {args.api_upstream}
  }}
  handle /s8Kx2mP7qR4wT/* {{
    reverse_proxy {args.api_upstream}
  }}

  handle_path /webapp/* {{
    root * {args.webapp_root}
    file_server
  }}

  handle {{
    root * {args.marketing_root}
    file_server
  }}
}}

{args.domain}:2096 {{
  tls /etc/caddy/certs/fullchain.pem /etc/caddy/certs/privkey.pem
  reverse_proxy {args.api_upstream}
}}
"""

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
        sftp = ssh.open_sftp()
        try:
            with sftp.file("/etc/caddy/Caddyfile", "w") as f:
                f.write(caddyfile)
        finally:
            sftp.close()

        code, out, err = _run(ssh, "systemctl restart caddy", timeout=120)
        if code != 0:
            raise SystemExit(err.strip() or out.strip() or "failed to restart caddy")

        _, out, err = _run(
            ssh,
            f"curl -fsS --insecure --resolve {args.domain}:8444:127.0.0.1 https://{args.domain}:8444/api/health || true",
            timeout=30,
        )
        print((out.strip() or err.strip()).strip())
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
