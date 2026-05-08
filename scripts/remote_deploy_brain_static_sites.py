from __future__ import annotations

import argparse
import os
import posixpath
import shlex
import sys
import tarfile
import tempfile
import time
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


def _dir_stats(local_dir: Path) -> tuple[int, int]:
    files = 0
    total_bytes = 0
    for p in local_dir.rglob("*"):
        if p.is_file():
            files += 1
            total_bytes += p.stat().st_size
    return files, total_bytes


def _format_bytes(value: int) -> str:
    amount = float(value)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if amount < 1024 or unit == "GiB":
            return f"{amount:.1f} {unit}" if unit != "B" else f"{int(amount)} B"
        amount /= 1024
    return f"{int(value)} B"


def _build_static_bundle(local_dir: Path, bundle_path: Path, *, label: str) -> None:
    total_files, total_bytes = _dir_stats(local_dir)
    started = time.monotonic()
    _safe_print(f"[bundle] {label}: {total_files} files, {_format_bytes(total_bytes)}")
    with tarfile.open(bundle_path, "w:gz") as tar:
        for p in sorted(local_dir.rglob("*")):
            arcname = p.relative_to(local_dir).as_posix()
            tar.add(str(p), arcname=arcname, recursive=False)
    elapsed = int(time.monotonic() - started)
    _safe_print(f"[bundle] {label}: {_format_bytes(bundle_path.stat().st_size)} in {elapsed}s")


def _deploy_static_bundle(
    ssh: paramiko.SSHClient,
    sftp: paramiko.SFTPClient,
    bundle_path: Path,
    *,
    label: str,
    remote_dir: str,
    release_id: str,
) -> None:
    started = time.monotonic()
    remote_tar = f"/tmp/portal-static-{release_id}-{label}.tar.gz"
    _safe_print(f"[upload] {label}: {_format_bytes(bundle_path.stat().st_size)} -> {remote_tar}")
    sftp.put(str(bundle_path), remote_tar)
    _safe_print(f"[extract] {label}: {remote_dir}")
    cmd = (
        "set -euo pipefail; "
        f"rm -rf {shlex.quote(remote_dir)}; "
        f"mkdir -p {shlex.quote(remote_dir)}; "
        f"tar -xzf {shlex.quote(remote_tar)} -C {shlex.quote(remote_dir)}; "
        f"rm -f {shlex.quote(remote_tar)}"
    )
    code, out, err = _run(ssh, cmd, timeout=600)
    if code != 0:
        raise SystemExit(f"Failed to extract {label} bundle:\n{out}\n{err}")
    elapsed = int(time.monotonic() - started)
    _safe_print(f"[deploy] {label}: complete in {elapsed}s")


def _release_payload_validation_checks(*, remote_webapp: str, remote_marketing: str) -> list[str]:
    return [
        f"test -f {shlex.quote(remote_webapp)}/index.html",
        f"test -f {shlex.quote(remote_marketing)}/index.html",
        f"test -f {shlex.quote(remote_marketing)}/checkout/index.html",
        f"test ! -e {shlex.quote(remote_marketing)}/fk-verify.html",
        f"test ! -e {shlex.quote(remote_marketing)}/fk-payment-theme.css",
    ]


def _local_static_output_validation_failures(*, local_webapp: Path, local_marketing: Path) -> list[str]:
    failures: list[str] = []
    for required in (
        local_webapp / "index.html",
        local_marketing / "index.html",
        local_marketing / "checkout" / "index.html",
    ):
        if not required.is_file():
            failures.append(f"missing local static file: {required}")
    for forbidden in (
        local_marketing / "fk-verify.html",
        local_marketing / "fk-payment-theme.css",
    ):
        if forbidden.exists():
            failures.append(f"forbidden legacy payment static file is present: {forbidden}")
    return failures


def _curl_head_command(url: str, *, host: str, bytes_count: int = 120) -> str:
    return (
        "curl -fsS --insecure "
        f"--resolve {shlex.quote(f'{host}:443:127.0.0.1')} "
        f"{shlex.quote(url)} | head -c {int(bytes_count)}"
    )


def _curl_expect_missing_command(url: str, *, host: str, label: str) -> str:
    return (
        "body_file=/tmp/portal_static_missing_check.$$; "
        "cleanup() { rm -f \"$body_file\"; }; "
        "trap cleanup EXIT; "
        "code=$(curl -k -sS -o \"$body_file\" -w \"%{http_code}\" "
        f"--resolve {shlex.quote(f'{host}:443:127.0.0.1')} {shlex.quote(url)} 2>/dev/null || true); "
        "case \"$code\" in "
        "404|410) "
        f"echo {shlex.quote(label + ' absent status=')}\"$code\"; exit 0 ;; "
        "000) "
        f"echo {shlex.quote(label + ' probe_failed status=')}\"$code\"; exit 22 ;; "
        "esac; "
        "if grep -Eiq 'FreeKassa|freekassa|payment-page-global|fk-payment-theme' \"$body_file\"; then "
        f"echo {shlex.quote(label + ' legacy_static_present status=')}\"$code marker=legacy_text\"; exit 23; "
        "fi; "
        "body_compact=$(tr -d '\\r\\n\\t ' < \"$body_file\"); "
        "if printf '%s' \"$body_compact\" | grep -Eq '^[0-9a-fA-F]{32,128}$'; then "
        f"echo {shlex.quote(label + ' legacy_static_present status=')}\"$code marker=hex_verify\"; exit 23; "
        "fi; "
        f"echo {shlex.quote(label + ' absent_or_fallback status=')}\"$code\"; exit 0"
    )


def _post_deploy_smoke_commands(*, web_domain: str, api_domain: str) -> list[str]:
    return [
        _curl_head_command(f"https://{api_domain}/api/health", host=api_domain, bytes_count=200),
        _curl_head_command(f"https://{web_domain}/", host=web_domain, bytes_count=80),
        _curl_head_command("https://app.pokrov.space/", host="app.pokrov.space", bytes_count=80),
        _curl_expect_missing_command(
            f"https://{web_domain}/fk-verify.html",
            host=web_domain,
            label="/fk-verify.html",
        ),
        _curl_expect_missing_command(
            f"https://{web_domain}/fk-payment-theme.css",
            host=web_domain,
            label="/fk-payment-theme.css",
        ),
        _curl_head_command("https://pay.pokrov.space/checkout/", host="pay.pokrov.space", bytes_count=120),
    ]


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
        sys.stdout.flush()
    except Exception:
        print(line.encode("utf-8", errors="replace").decode("utf-8", errors="replace"), flush=True)


def _release_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def main() -> int:
    ap = argparse.ArgumentParser(description="Deploy marketing/out + webapp/out to brain and reload Caddy.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument(
        "--web-domain",
        default="pokrov.space",
        help="Public web domain for marketing + /webapp checks",
    )
    ap.add_argument(
        "--api-domain",
        default="api.pokrov.space",
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
    ap.add_argument(
        "--plan-only",
        action="store_true",
        help="Validate and bundle local static outputs, print the remote plan, then exit before SSH/upload/symlink changes.",
    )
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
    local_failures = _local_static_output_validation_failures(local_webapp=local_webapp, local_marketing=local_mkt)
    if local_failures:
        raise SystemExit("Local static output validation failed:\n" + "\n".join(f"- {failure}" for failure in local_failures))

    release_id = _release_id()
    remote_root = "/var/www/portal"
    releases_root = f"{remote_root}/releases"
    remote_release = f"{releases_root}/{release_id}"
    remote_webapp = f"{remote_release}/webapp"
    remote_marketing = f"{remote_release}/marketing"

    if args.plan_only:
        _safe_print(f"plan-only: release_id={release_id}")
        _safe_print(f"plan-only: local webapp={local_webapp}")
        _safe_print(f"plan-only: local marketing={local_mkt}")
        _safe_print(f"plan-only: remote webapp={remote_webapp}")
        _safe_print(f"plan-only: remote marketing={remote_marketing}")
        with tempfile.TemporaryDirectory(prefix="pokrov-static-plan-") as temp_root:
            temp_dir = Path(temp_root)
            _build_static_bundle(local_webapp, temp_dir / f"webapp-{release_id}.tar.gz", label="webapp")
            _build_static_bundle(local_mkt, temp_dir / f"marketing-{release_id}.tar.gz", label="marketing")
        _safe_print("plan-only: release payload validation checks")
        for check in _release_payload_validation_checks(remote_webapp=remote_webapp, remote_marketing=remote_marketing):
            _safe_print(f"plan-only: {check}")
        _safe_print("plan-only: post-deploy smoke checks")
        for check in _post_deploy_smoke_commands(web_domain=web_domain, api_domain=api_domain):
            _safe_print(f"plan-only: {check}")
        _safe_print("plan-only: no SSH/upload/symlink/reload commands executed")
        return 0

    ssh, auth_method = connect_node(
        code="brain",
        host=args.brain_ip,
        user=args.ssh_user,
        port=args.ssh_port,
        passwords_path=Path(args.passwords),
    )
    try:
        _safe_print(f"brain auth: {auth_method}")

        # Upload into a versioned release directory first, then switch symlinks.
        _run(ssh, f"mkdir -p {remote_webapp} {remote_marketing}", timeout=60)

        with tempfile.TemporaryDirectory(prefix="pokrov-static-") as temp_root:
            temp_dir = Path(temp_root)
            webapp_bundle = temp_dir / f"webapp-{release_id}.tar.gz"
            marketing_bundle = temp_dir / f"marketing-{release_id}.tar.gz"
            _build_static_bundle(local_webapp, webapp_bundle, label="webapp")
            _build_static_bundle(local_mkt, marketing_bundle, label="marketing")

            sftp = ssh.open_sftp()
            try:
                _deploy_static_bundle(ssh, sftp, webapp_bundle, label="webapp", remote_dir=remote_webapp, release_id=release_id)
                _deploy_static_bundle(ssh, sftp, marketing_bundle, label="marketing", remote_dir=remote_marketing, release_id=release_id)
            finally:
                sftp.close()

        # Validate release payload before switching public paths.
        for check in _release_payload_validation_checks(remote_webapp=remote_webapp, remote_marketing=remote_marketing):
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
        for c in _post_deploy_smoke_commands(web_domain=web_domain, api_domain=api_domain):
            code, out, err = _run(ssh, c, timeout=30)
            _safe_print(out.strip() or err.strip())
            if code != 0:
                raise SystemExit(f"Post-deploy static smoke failed: {c}")
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
