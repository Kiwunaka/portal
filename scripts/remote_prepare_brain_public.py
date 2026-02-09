from __future__ import annotations

"""
Prepare the brain node to take over the public domain:
- portal-api behind Caddy on :2096 (keeps existing subscription URLs working)
- marketing site on :443
- Telegram WebApp on :443 at /webapp/

This script does NOT touch the old production services (read-only fetch of cert + .env),
and it does NOT start the Telegram bot on brain (to avoid token conflicts before cutover).

Required (old server; to fetch cert + env):
- OLD_SSH_HOST, OLD_SSH_PASS
Optional:
- OLD_SSH_PORT (default 29374)
- OLD_SSH_USER (default root)

Brain auth:
- NODE_PASS_BRAIN env var, or PASSWORDS.txt must contain BRAINnode password.
"""

import argparse
import os
import posixpath
import re
from pathlib import Path

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"


def _require_env(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        raise SystemExit(f"Missing required env var: {name}")
    return v


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


def _ssh_connect(ip: str, *, user: str, port: int, password: str) -> paramiko.SSHClient:
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(ip, port=port, username=user, password=password, timeout=30, banner_timeout=30, auth_timeout=30)
    t = cli.get_transport()
    if t:
        t.set_keepalive(30)
    return cli


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 600) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def _sftp_mkdir_p(sftp: paramiko.SFTPClient, remote_dir: str) -> None:
    parts: list[str] = []
    cur = remote_dir
    while cur not in {"", "/"}:
        parts.append(cur)
        cur = posixpath.dirname(cur)
    for d in reversed(parts):
        try:
            sftp.stat(d)
        except IOError:
            try:
                sftp.mkdir(d)
            except IOError:
                pass


def _sftp_put_file(sftp: paramiko.SFTPClient, local_path: Path, remote_path: str) -> None:
    _sftp_mkdir_p(sftp, posixpath.dirname(remote_path))
    sftp.put(str(local_path), remote_path)


def _sftp_put_text(sftp: paramiko.SFTPClient, remote_path: str, content: str) -> None:
    _sftp_mkdir_p(sftp, posixpath.dirname(remote_path))
    with sftp.file(remote_path, "w") as f:
        f.write(content)


def _upload_dir_recursive(sftp: paramiko.SFTPClient, local_dir: Path, remote_dir: str) -> None:
    for p in local_dir.rglob("*"):
        rel = p.relative_to(local_dir).as_posix()
        rp = f"{remote_dir.rstrip('/')}/{rel}"
        if p.is_dir():
            _sftp_mkdir_p(sftp, rp)
        else:
            _sftp_put_file(sftp, p, rp)


def _split_pem_bundle(pem: str) -> tuple[str, str]:
    # Extract key + cert chain from a single bundle.
    blocks = re.findall(r"-----BEGIN [^-]+-----.*?-----END [^-]+-----", pem, flags=re.S)
    keys = [b for b in blocks if "PRIVATE KEY" in b]
    certs = [b for b in blocks if "CERTIFICATE" in b]
    if not keys or not certs:
        raise ValueError("Failed to parse PEM bundle (need key + certs).")
    priv = keys[0].strip() + "\n"
    fullchain = "\n".join(c.strip() for c in certs).strip() + "\n"
    return priv, fullchain


def _load_old_cert_and_env(old: paramiko.SSHClient) -> tuple[str, str, str]:
    sftp = old.open_sftp()
    try:
        # Prefer the known bundle path used by existing scripts.
        cand = "/root/certs_keep/ssl/haproxy.pem"
        try:
            with sftp.file(cand, "r") as f:
                pem = f.read().decode("utf-8", errors="replace")
        except IOError:
            # Fallback: already extracted certs
            with sftp.file("/root/portal_bot/certs/privkey.pem", "r") as f:
                priv = f.read().decode("utf-8", errors="replace")
            with sftp.file("/root/portal_bot/certs/fullchain.pem", "r") as f:
                fullchain = f.read().decode("utf-8", errors="replace")
            pem = ""

        env_txt = ""
        try:
            with sftp.file("/root/portal_bot/.env", "r") as f:
                env_txt = f.read().decode("utf-8", errors="replace")
        except IOError:
            env_txt = ""

        if pem:
            priv, fullchain = _split_pem_bundle(pem)
        return priv, fullchain, env_txt
    finally:
        sftp.close()


def _rewrite_env(env_txt: str, *, public_api_base: str, webapp_url: str) -> str:
    lines = [ln.rstrip("\n") for ln in env_txt.splitlines()]
    kv: dict[str, str] = {}
    out_lines: list[str] = []

    for ln in lines:
        if not ln.strip() or ln.lstrip().startswith("#") or "=" not in ln:
            out_lines.append(ln)
            continue
        k, v = ln.split("=", 1)
        k = k.strip()
        kv[k] = v
        out_lines.append(ln)

    def upsert(key: str, value: str) -> None:
        nonlocal out_lines
        if any(l.startswith(f"{key}=") for l in out_lines):
            out_lines = [f"{key}={value}" if l.startswith(f"{key}=") else l for l in out_lines]
        else:
            out_lines.append(f"{key}={value}")

    upsert("DATABASE_URL", "sqlite:////root/portal_bot/portal.db")
    upsert("PUBLIC_API_BASE_URL", public_api_base)
    upsert("WEBAPP_URL", webapp_url)

    # Ensure unix newlines
    return "\n".join(out_lines).strip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", required=True, help="public domain, e.g. kiwunaka.space")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--brain-ssh-port", type=int, default=29374)
    ap.add_argument("--brain-ssh-user", default="root")
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--no-copy-env", action="store_true", help="do not copy .env from old server")
    args = ap.parse_args()

    old_host = _require_env("OLD_SSH_HOST")
    old_pass = _require_env("OLD_SSH_PASS")
    old_port = int(os.getenv("OLD_SSH_PORT", "29374"))
    old_user = os.getenv("OLD_SSH_USER", "root")

    brain_pass = os.getenv("NODE_PASS_BRAIN", "").strip()
    if not brain_pass:
        brain_pass = _parse_passwords(Path(args.passwords)).get("brain", "")
    if not brain_pass:
        raise SystemExit("Missing brain password (set NODE_PASS_BRAIN or add to PASSWORDS.txt).")

    # Fetch cert + env from old server (read-only).
    old = _ssh_connect(old_host, user=old_user, port=old_port, password=old_pass)
    try:
        priv, fullchain, env_txt = _load_old_cert_and_env(old)
    finally:
        old.close()

    # Prepare brain.
    brain = _ssh_connect(args.brain_ip, user=args.brain_ssh_user, port=args.brain_ssh_port, password=brain_pass)
    try:
        # Base packages
        cmds = [
            "DEBIAN_FRONTEND=noninteractive apt-get update -y",
            "DEBIAN_FRONTEND=noninteractive apt-get install -y curl ca-certificates ufw gnupg debian-keyring debian-archive-keyring apt-transport-https",
        ]
        for c in cmds:
            code, out, err = _run(brain, c, timeout=1800)
            if code != 0:
                raise RuntimeError(f"Remote command failed: {c}\n{err.strip()}")

        # Install Caddy from the official repo (apt may not have it by default).
        code, out, err = _run(brain, "command -v caddy >/dev/null 2>&1; echo $?", timeout=60)
        need_caddy = (out.strip().splitlines()[-1] if out.strip() else "1") != "0"
        if need_caddy:
            install_caddy = [
                "curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --batch --yes --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg",
                "curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list",
                "DEBIAN_FRONTEND=noninteractive apt-get update -y",
                "DEBIAN_FRONTEND=noninteractive apt-get install -y caddy",
            ]
            for c in install_caddy:
                code, out, err = _run(brain, c, timeout=1800)
                if code != 0:
                    raise RuntimeError(f"Remote command failed: {c}\n{err.strip()}")

        # Firewall: allow 80/443/8444/2096 (8444 kept for backward-compat if old WebApp used it)
        _run(brain, "ufw allow 80/tcp >/dev/null 2>&1 || true", timeout=60)
        _run(brain, "ufw allow 443/tcp >/dev/null 2>&1 || true", timeout=60)
        _run(brain, "ufw allow 8444/tcp >/dev/null 2>&1 || true", timeout=60)
        _run(brain, "ufw allow 2096/tcp >/dev/null 2>&1 || true", timeout=60)
        _run(brain, "ufw --force enable >/dev/null 2>&1 || true", timeout=60)

        # Ensure cert dir readable by caddy user.
        _run(brain, "mkdir -p /etc/caddy/certs && chown -R caddy:caddy /etc/caddy/certs && chmod 750 /etc/caddy/certs", timeout=60)

        # Upload cert files (caddy must be able to read them)
        sftp = brain.open_sftp()
        try:
            _sftp_put_text(sftp, "/etc/caddy/certs/privkey.pem", priv)
            _sftp_put_text(sftp, "/etc/caddy/certs/fullchain.pem", fullchain)
            # Upload static sites
            _run(brain, "mkdir -p /var/www/portal/webapp /var/www/portal/marketing", timeout=60)
            # Upload webapp/dist
            local_webapp = REPO_ROOT / "webapp" / "dist"
            if not (local_webapp / "index.html").exists():
                raise SystemExit("webapp/dist missing; build it locally first.")
            _upload_dir_recursive(sftp, local_webapp, "/var/www/portal/webapp")

            # Upload marketing/out (static export)
            local_mkt = REPO_ROOT / "marketing" / "out"
            if not (local_mkt / "index.html").exists():
                raise SystemExit("marketing/out missing; build it locally first.")
            _upload_dir_recursive(sftp, local_mkt, "/var/www/portal/marketing")

            # Optionally copy env (no printing)
            if not args.no_copy_env and env_txt.strip():
                public_api_base = f"https://{args.domain}:2096"
                webapp_url = f"https://{args.domain}/webapp/"
                rewritten = _rewrite_env(env_txt, public_api_base=public_api_base, webapp_url=webapp_url)
                _sftp_put_text(sftp, "/root/portal_bot/.env", rewritten)
        finally:
            sftp.close()

        # Fix permissions after upload.
        _run(
            brain,
            "chown caddy:caddy /etc/caddy/certs/privkey.pem /etc/caddy/certs/fullchain.pem && chmod 640 /etc/caddy/certs/privkey.pem /etc/caddy/certs/fullchain.pem",
            timeout=60,
        )

        # portal-api: bind localhost:8080 (Caddy does TLS + keeps public port 2096)
        portal_api_service = """[Unit]
Description=Portal API (FastAPI)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/portal_bot
EnvironmentFile=-/root/portal_bot/.env
ExecStart=/root/portal_bot/venv/bin/python -m uvicorn api:app --host 127.0.0.1 --port 8080
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""

        portal_bot_service = """[Unit]
Description=Portal Bot (Telegram)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/portal_bot
EnvironmentFile=-/root/portal_bot/.env
ExecStart=/root/portal_bot/venv/bin/python bot.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""

        caddyfile_site = f"""{args.domain}:443 {{
  tls /etc/caddy/certs/fullchain.pem /etc/caddy/certs/privkey.pem

  encode gzip

  @webapp path /webapp/*
  handle @webapp {{
    handle_path /webapp/* {{
      root * /var/www/portal/webapp
      file_server
    }}
  }}

  handle {{
    root * /var/www/portal/marketing
    file_server
  }}
}}
"""

        caddyfile_webapp_compat = f"""{args.domain}:8444 {{
  tls /etc/caddy/certs/fullchain.pem /etc/caddy/certs/privkey.pem

  encode gzip

  handle_path /webapp/* {{
    root * /var/www/portal/webapp
    file_server
  }}

  handle {{
    root * /var/www/portal/marketing
    file_server
  }}
}}
"""

        caddyfile_api = f"""{args.domain}:2096 {{
  tls /etc/caddy/certs/fullchain.pem /etc/caddy/certs/privkey.pem
  reverse_proxy 127.0.0.1:8080
}}
"""
        caddyfile = caddyfile_site + "\n" + caddyfile_webapp_compat + "\n" + caddyfile_api

        # Install services + caddyfile
        _run(brain, "mkdir -p /etc/systemd/system", timeout=60)
        sftp = brain.open_sftp()
        try:
            _sftp_put_text(sftp, "/etc/systemd/system/portal-api.service", portal_api_service)
            _sftp_put_text(sftp, "/etc/systemd/system/portal-bot.service", portal_bot_service)
            _sftp_put_text(sftp, "/etc/caddy/Caddyfile", caddyfile)
        finally:
            sftp.close()

        _run(brain, "systemctl daemon-reload", timeout=60)
        _run(brain, "systemctl enable portal-api", timeout=60)
        _run(brain, "systemctl restart portal-api", timeout=120)
        _run(brain, "systemctl restart caddy", timeout=120)

        # Make sure bot is not running yet
        _run(brain, "systemctl stop portal-bot >/dev/null 2>&1 || true", timeout=60)
        _run(brain, "systemctl disable portal-bot >/dev/null 2>&1 || true", timeout=60)

        # Quick health check locally (through Caddy on localhost via resolve)
        # Note: we bypass DNS by forcing resolve to 127.0.0.1.
        _run(brain, "DEBIAN_FRONTEND=noninteractive apt-get install -y curl >/dev/null 2>&1 || true", timeout=600)
        chk = f"curl -fsS --insecure --resolve {args.domain}:2096:127.0.0.1 https://{args.domain}:2096/api/health || true"
        code, out, err = _run(brain, chk, timeout=30)
        # Print only minimal signal
        print(out.strip())
        return 0
    finally:
        brain.close()


if __name__ == "__main__":
    raise SystemExit(main())
