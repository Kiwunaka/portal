from __future__ import annotations

import argparse
import os
import posixpath
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


def _rewrite_env(text: str, *, public_api_base: str, webapp_url: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    seen_api = False
    seen_web = False
    for ln in lines:
        if ln.strip().startswith("PUBLIC_API_BASE_URL="):
            out.append(f"PUBLIC_API_BASE_URL={public_api_base}")
            seen_api = True
            continue
        if ln.strip().startswith("WEBAPP_URL="):
            out.append(f"WEBAPP_URL={webapp_url}")
            seen_web = True
            continue
        out.append(ln)
    if not seen_api:
        out.append(f"PUBLIC_API_BASE_URL={public_api_base}")
    if not seen_web:
        out.append(f"WEBAPP_URL={webapp_url}")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Update /root/portal_bot/.env URLs on brain without printing secrets.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--domain", required=True)
    ap.add_argument("--public-api-port", type=int, default=2096)
    ap.add_argument("--webapp-port", type=int, default=8444)
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    args = ap.parse_args()

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_passwords(Path(args.passwords))
    if not pw:
        raise SystemExit("Missing brain password.")

    public_api_base = f"https://{args.domain}:{int(args.public_api_port)}"
    webapp_url = f"https://{args.domain}:{int(args.webapp_port)}/webapp/"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(args.brain_ip, port=args.ssh_port, username=args.ssh_user, password=pw, timeout=30, banner_timeout=30, auth_timeout=30)
    try:
        sftp = ssh.open_sftp()
        try:
            rp = "/root/portal_bot/.env"
            try:
                with sftp.file(rp, "r") as f:
                    raw = f.read().decode("utf-8", errors="replace")
            except IOError:
                raw = ""
            updated = _rewrite_env(raw, public_api_base=public_api_base, webapp_url=webapp_url)
            with sftp.file(rp, "w") as f:
                f.write(updated.encode("utf-8"))
        finally:
            sftp.close()

        # Restart portal-api to pick up env changes (safe even if already running).
        _run(ssh, "systemctl restart portal-api >/dev/null 2>&1 || true", timeout=60)
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())

