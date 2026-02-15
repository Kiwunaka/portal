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


def _upload_dir_recursive(sftp: paramiko.SFTPClient, local_dir: Path, remote_dir: str) -> None:
    for p in local_dir.rglob("*"):
        rel = p.relative_to(local_dir).as_posix()
        rp = f"{remote_dir.rstrip('/')}/{rel}"
        if p.is_dir():
            _sftp_mkdir_p(sftp, rp)
        else:
            _sftp_mkdir_p(sftp, posixpath.dirname(rp))
            sftp.put(str(p), rp)


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 300) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def main() -> int:
    ap = argparse.ArgumentParser(description="Deploy marketing/out + webapp/dist to brain and reload Caddy.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument(
        "--web-domain",
        default="portal-privacy.online",
        help="Public web domain for marketing + /webapp checks",
    )
    ap.add_argument(
        "--api-domain",
        default="kiwunaka.space",
        help="Public API domain for /api/health checks",
    )
    ap.add_argument(
        "--domain",
        default="",
        help="Deprecated alias for --web-domain (kept for backward compatibility)",
    )
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    args = ap.parse_args()

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_passwords(Path(args.passwords))
    if not pw:
        raise SystemExit("Missing brain password.")

    local_webapp = REPO_ROOT / "webapp" / "dist"
    local_mkt = REPO_ROOT / "marketing" / "out"
    if not local_webapp.exists():
        raise SystemExit(f"Missing webapp dist: {local_webapp}")
    if not local_mkt.exists():
        raise SystemExit(f"Missing marketing out: {local_mkt}")
    web_domain = (args.domain or "").strip() or (args.web_domain or "").strip()
    api_domain = (args.api_domain or "").strip()
    if not web_domain:
        raise SystemExit("Missing --web-domain")
    if not api_domain:
        raise SystemExit("Missing --api-domain")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(args.brain_ip, port=args.ssh_port, username=args.ssh_user, password=pw, timeout=30, banner_timeout=30, auth_timeout=30)
    try:
        # Ensure dirs and clean old content.
        _run(ssh, "mkdir -p /var/www/portal/webapp /var/www/portal/marketing", timeout=60)
        _run(ssh, "rm -rf /var/www/portal/webapp/* /var/www/portal/marketing/*", timeout=120)

        sftp = ssh.open_sftp()
        try:
            _upload_dir_recursive(sftp, local_webapp, "/var/www/portal/webapp")
            _upload_dir_recursive(sftp, local_mkt, "/var/www/portal/marketing")
        finally:
            sftp.close()

        _run(ssh, "systemctl reload caddy >/dev/null 2>&1 || systemctl restart caddy >/dev/null 2>&1 || true", timeout=60)

        # Quick smoke checks (through localhost resolve on standard HTTPS port).
        chk = [
            f"curl -fsS --insecure --resolve {api_domain}:443:127.0.0.1 https://{api_domain}/api/health | head -c 200 || true",
            f"curl -fsS --insecure --resolve {web_domain}:443:127.0.0.1 https://{web_domain}/ | head -c 80 || true",
            f"curl -fsS --insecure --resolve {web_domain}:443:127.0.0.1 https://{web_domain}/webapp/ | head -c 80 || true",
        ]
        for c in chk:
            _run(ssh, "DEBIAN_FRONTEND=noninteractive apt-get install -y curl >/dev/null 2>&1 || true", timeout=600)
            _, out, err = _run(ssh, c, timeout=30)
            print((out.strip() or err.strip()).strip())
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
