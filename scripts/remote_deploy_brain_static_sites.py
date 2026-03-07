from __future__ import annotations

import argparse
import os
import posixpath
import sys
from datetime import datetime, timezone
from pathlib import Path

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from node_access import connect_node


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


def _safe_print(text: str) -> None:
    """
    Print remote output without crashing on terminal encoding mismatches
    (e.g. BOM or UTF-8 symbols on legacy cp1251 console).
    """
    line = str(text or "").replace("\ufeff", "").strip()
    if not line:
        return
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        sys.stdout.buffer.write((line + "\n").encode(encoding, errors="replace"))
    except Exception:
        print(line.encode("utf-8", errors="replace").decode("utf-8", errors="replace"))


def _release_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def main() -> int:
    ap = argparse.ArgumentParser(description="Deploy marketing/out + webapp/out to brain and reload Caddy.")
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

    local_webapp = REPO_ROOT / "webapp" / "out"
    local_mkt = REPO_ROOT / "marketing" / "out"
    if not local_webapp.exists():
        raise SystemExit(f"Missing webapp out: {local_webapp}")
    if not local_mkt.exists():
        raise SystemExit(f"Missing marketing out: {local_mkt}")
    web_domain = (args.domain or "").strip() or (args.web_domain or "").strip()
    api_domain = (args.api_domain or "").strip()
    if not web_domain:
        raise SystemExit("Missing --web-domain")
    if not api_domain:
        raise SystemExit("Missing --api-domain")

    ssh, auth_method = connect_node(
        code="brain",
        host=args.brain_ip,
        user=args.ssh_user,
        port=args.ssh_port,
        passwords_path=Path(args.passwords),
    )
    try:
        _safe_print(f"brain auth: {auth_method}")
        release_id = _release_id()
        remote_root = "/var/www/portal"
        releases_root = f"{remote_root}/releases"
        remote_release = f"{releases_root}/{release_id}"
        remote_webapp = f"{remote_release}/webapp"
        remote_marketing = f"{remote_release}/marketing"

        # Upload into a versioned release directory first, then switch symlinks.
        _run(ssh, f"mkdir -p {remote_webapp} {remote_marketing}", timeout=60)

        sftp = ssh.open_sftp()
        try:
            _upload_dir_recursive(sftp, local_webapp, remote_webapp)
            _upload_dir_recursive(sftp, local_mkt, remote_marketing)
        finally:
            sftp.close()

        # Validate release payload before switching public paths.
        checks = [
            f"test -f {remote_webapp}/index.html",
            f"test -f {remote_marketing}/index.html",
            f"test -f {remote_marketing}/checkout/index.html",
            f"test -f {remote_marketing}/fk-verify.html",
        ]
        for check in checks:
            code, _out, _err = _run(ssh, check, timeout=30)
            if code != 0:
                raise SystemExit(f"Release payload validation failed: {check}")

        switch_cmd = f"""
set -euo pipefail
mkdir -p {releases_root}
mkdir -p {remote_root}/legacy_backups

if [ -e {remote_root}/webapp ] && [ ! -L {remote_root}/webapp ]; then
  mv {remote_root}/webapp {remote_root}/legacy_backups/webapp-$(date +%s)
fi
if [ -e {remote_root}/marketing ] && [ ! -L {remote_root}/marketing ]; then
  mv {remote_root}/marketing {remote_root}/legacy_backups/marketing-$(date +%s)
fi

ln -sfn {remote_webapp} {remote_root}/webapp.next
mv -T {remote_root}/webapp.next {remote_root}/webapp
ln -sfn {remote_marketing} {remote_root}/marketing.next
mv -T {remote_root}/marketing.next {remote_root}/marketing

find {releases_root} -mindepth 1 -maxdepth 1 -type d | sort | head -n -5 | xargs -r rm -rf
"""
        code, out, err = _run(ssh, switch_cmd, timeout=120)
        if code != 0:
            raise SystemExit(f"Failed to switch static release:\n{out}\n{err}")

        _run(ssh, "systemctl reload caddy >/dev/null 2>&1 || systemctl restart caddy >/dev/null 2>&1 || true", timeout=60)
        _run(ssh, "DEBIAN_FRONTEND=noninteractive apt-get install -y curl >/dev/null 2>&1 || true", timeout=600)

        # Quick smoke checks (through localhost resolve on standard HTTPS port).
        chk = [
            f"curl -fsS --insecure --resolve {api_domain}:443:127.0.0.1 https://{api_domain}/api/health | head -c 200 || true",
            f"curl -fsS --insecure --resolve {web_domain}:443:127.0.0.1 https://{web_domain}/ | head -c 80 || true",
            f"curl -fsS --insecure --resolve {web_domain}:443:127.0.0.1 https://{web_domain}/webapp/ | head -c 80 || true",
            f"curl -fsS --insecure --resolve {web_domain}:443:127.0.0.1 https://{web_domain}/fk-verify.html | head -c 80 || true",
            f"curl -fsS --insecure --resolve {web_domain}:443:127.0.0.1 https://{web_domain}/fk-payment-theme.css | head -c 120 || true",
        ]
        for c in chk:
            _, out, err = _run(ssh, c, timeout=30)
            _safe_print(out.strip() or err.strip())
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
