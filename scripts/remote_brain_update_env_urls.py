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


def _rewrite_env(
    text: str,
    *,
    public_api_base: str,
    webapp_url: str,
    public_api_domain: str,
    public_web_domain: str,
    telegram_oauth_client_id: str,
    telegram_oauth_redirect_uri: str,
    telegram_oauth_client_secret: str,
) -> str:
    lines = text.splitlines()
    out: list[str] = []
    seen_api = False
    seen_web = False
    seen_api_domain = False
    seen_web_domain = False
    seen_host_domain = False
    seen_oauth_client_id = False
    seen_oauth_redirect_uri = False
    seen_oauth_client_secret = False
    for ln in lines:
        if ln.strip().startswith("PUBLIC_API_BASE_URL="):
            out.append(f"PUBLIC_API_BASE_URL={public_api_base}")
            seen_api = True
            continue
        if ln.strip().startswith("WEBAPP_URL="):
            out.append(f"WEBAPP_URL={webapp_url}")
            seen_web = True
            continue
        if ln.strip().startswith("PUBLIC_API_DOMAIN="):
            out.append(f"PUBLIC_API_DOMAIN={public_api_domain}")
            seen_api_domain = True
            continue
        if ln.strip().startswith("PUBLIC_WEB_DOMAIN="):
            out.append(f"PUBLIC_WEB_DOMAIN={public_web_domain}")
            seen_web_domain = True
            continue
        if ln.strip().startswith("HOST_DOMAIN="):
            out.append(f"HOST_DOMAIN={public_api_domain}")
            seen_host_domain = True
            continue
        if ln.strip().startswith("TELEGRAM_OAUTH_CLIENT_ID="):
            out.append(f"TELEGRAM_OAUTH_CLIENT_ID={telegram_oauth_client_id}")
            seen_oauth_client_id = True
            continue
        if ln.strip().startswith("TELEGRAM_OAUTH_REDIRECT_URI="):
            out.append(f"TELEGRAM_OAUTH_REDIRECT_URI={telegram_oauth_redirect_uri}")
            seen_oauth_redirect_uri = True
            continue
        if telegram_oauth_client_secret and ln.strip().startswith("TELEGRAM_OAUTH_CLIENT_SECRET="):
            out.append(f"TELEGRAM_OAUTH_CLIENT_SECRET={telegram_oauth_client_secret}")
            seen_oauth_client_secret = True
            continue
        out.append(ln)
    if not seen_api:
        out.append(f"PUBLIC_API_BASE_URL={public_api_base}")
    if not seen_web:
        out.append(f"WEBAPP_URL={webapp_url}")
    if not seen_api_domain:
        out.append(f"PUBLIC_API_DOMAIN={public_api_domain}")
    if not seen_web_domain:
        out.append(f"PUBLIC_WEB_DOMAIN={public_web_domain}")
    if not seen_host_domain:
        out.append(f"HOST_DOMAIN={public_api_domain}")
    if telegram_oauth_client_id and not seen_oauth_client_id:
        out.append(f"TELEGRAM_OAUTH_CLIENT_ID={telegram_oauth_client_id}")
    if telegram_oauth_redirect_uri and not seen_oauth_redirect_uri:
        out.append(f"TELEGRAM_OAUTH_REDIRECT_URI={telegram_oauth_redirect_uri}")
    if telegram_oauth_client_secret and not seen_oauth_client_secret:
        out.append(f"TELEGRAM_OAUTH_CLIENT_SECRET={telegram_oauth_client_secret}")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Update /root/portal_bot/.env URLs on brain without printing secrets.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--api-domain", default="api.pokrov.space")
    ap.add_argument("--web-domain", default="pokrov.space")
    ap.add_argument("--public-api-port", type=int, default=443)
    ap.add_argument("--webapp-port", type=int, default=443)
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    args = ap.parse_args()

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_passwords(Path(args.passwords))
    if not pw:
        raise SystemExit("Missing brain password.")

    api_domain = str(args.api_domain).strip()
    web_domain = str(args.web_domain).strip()
    api_port = int(args.public_api_port)
    web_port = int(args.webapp_port)
    public_api_base = f"https://{api_domain}" if api_port == 443 else f"https://{api_domain}:{api_port}"
    webapp_url = f"https://app.pokrov.space/" if web_port == 443 else f"https://app.pokrov.space:{web_port}/"
    telegram_oauth_client_id = (os.getenv("TELEGRAM_OAUTH_CLIENT_ID") or "").strip()
    telegram_oauth_redirect_uri = (os.getenv("TELEGRAM_OAUTH_REDIRECT_URI") or webapp_url).strip()
    telegram_oauth_client_secret = (os.getenv("TELEGRAM_OAUTH_CLIENT_SECRET") or "").strip()

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
            updated = _rewrite_env(
                raw,
                public_api_base=public_api_base,
                webapp_url=webapp_url,
                public_api_domain=api_domain,
                public_web_domain=web_domain,
                telegram_oauth_client_id=telegram_oauth_client_id,
                telegram_oauth_redirect_uri=telegram_oauth_redirect_uri,
                telegram_oauth_client_secret=telegram_oauth_client_secret,
            )
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
