from __future__ import annotations

import argparse
import json
import posixpath
import re
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
REQUIRED_LOCAL_STATIC_FILES = (
    ("webapp", "index.html"),
    ("adminapp", "index.html"),
    ("adminapp", "__build.json"),
    ("adminapp", "__routes.json"),
    ("marketing", "index.html"),
    ("marketing", "checkout", "index.html"),
)
ADMINAPP_BUILD_SCHEMA = "pokrov-operator-build-v1"
ADMINAPP_ROUTE_SCHEMA = "pokrov-operator-route-manifest-v1"
ADMINAPP_IDENTITY = "pokrov-operator-center"
FORBIDDEN_LEGACY_MARKETING_STATIC_FILES = (
    "fk-verify.html",
    "fk-payment-theme.css",
)
FORBIDDEN_STATIC_CONTENT = (
    "http://127.0.0.1:3107",
    "https://127.0.0.1:3107",
    "http://localhost:3107",
    "https://localhost:3107",
)
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))



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


_NEXT_STATIC_REF_RE = re.compile(
    r"(?P<url>/_next/static/[^\"'\\\s<>?#]+)"
    r"(?:\?(?P<query>[^\"'\\\s<>#]*))?"
    r"(?P<fragment>#[^\"'\\\s<>]*)?"
)


def _strip_next_static_cache_busting(local_dir: Path, *, label: str) -> None:
    """Remove only the legacy `v` query field from exported Next static refs.

    Next chunk filenames are content-hashed and HTML is revalidated, so a
    release-id query is redundant and can desynchronize runtime chunk identity
    during soft navigation. Unrelated query fields and fragments are preserved.
    """
    touched = 0
    for html_path in sorted(local_dir.rglob("*.html")):
        raw = html_path.read_text(encoding="utf-8", errors="replace")

        def repl(match: re.Match[str]) -> str:
            url = match.group("url")
            query = str(match.group("query") or "")
            fragment = str(match.group("fragment") or "")
            kept = [part for part in query.split("&") if part and part.split("=", 1)[0] != "v"]
            return f"{url}{'?' + '&'.join(kept) if kept else ''}{fragment}"

        updated = _NEXT_STATIC_REF_RE.sub(repl, raw)
        if updated == raw:
            continue
        html_path.write_text(updated, encoding="utf-8")
        touched += 1
    _safe_print(f"[cache-normalize] {label}: {touched} html files")


def _local_static_output_validation_failures(*, local_webapp: Path, local_adminapp: Path, local_marketing: Path) -> list[str]:
    roots = {
        "webapp": local_webapp,
        "adminapp": local_adminapp,
        "marketing": local_marketing,
    }
    failures: list[str] = []
    for parts in REQUIRED_LOCAL_STATIC_FILES:
        root_key, *relative_parts = parts
        expected = roots[root_key].joinpath(*relative_parts)
        if not expected.is_file():
            failures.append(f"missing local static file: {expected}")
    for file_name in FORBIDDEN_LEGACY_MARKETING_STATIC_FILES:
        forbidden = local_marketing / file_name
        if forbidden.exists():
            failures.append(f"forbidden legacy payment static file is present: {forbidden}")
    build_path = local_adminapp / "__build.json"
    routes_path = local_adminapp / "__routes.json"
    if build_path.is_file() and routes_path.is_file():
        try:
            build = json.loads(build_path.read_text(encoding="utf-8"))
            routes = json.loads(routes_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError) as exc:
            failures.append(f"invalid adminapp build identity JSON: {type(exc).__name__}")
        else:
            if build.get("schema") != ADMINAPP_BUILD_SCHEMA:
                failures.append("invalid adminapp build schema")
            if build.get("app") != ADMINAPP_IDENTITY:
                failures.append("invalid adminapp application identity")
            if build.get("canonical_domain") != "admin.pokrov.space":
                failures.append("invalid adminapp canonical domain")
            if not str(build.get("frontend_commit") or "").strip():
                failures.append("missing adminapp frontend commit")
            expected_api_schema = str(build.get("expected_api_schema") or "")
            if not re.fullmatch(r"admin-v2\.[0-9]+", expected_api_schema):
                failures.append("invalid adminapp expected API schema")
            if routes.get("schema") != ADMINAPP_ROUTE_SCHEMA:
                failures.append("invalid adminapp route manifest schema")
            if routes.get("app") != ADMINAPP_IDENTITY:
                failures.append("invalid adminapp route application identity")
            if routes.get("manifest_hash") != build.get("route_manifest_hash"):
                failures.append("adminapp build/route manifest hash mismatch")
            if not str(build.get("cutover_matrix_hash") or "").strip():
                failures.append("missing adminapp cutover matrix hash")
            if routes.get("cutover_matrix_hash") != build.get("cutover_matrix_hash"):
                failures.append("adminapp build/route cutover matrix hash mismatch")
            if len(routes.get("workspaces") or []) != 7:
                failures.append("adminapp route manifest must declare seven workspaces")
        try:
            admin_index = (local_adminapp / "index.html").read_text(encoding="utf-8", errors="replace")
        except OSError:
            admin_index = ""
        if "POKROV API superadmin v1" in admin_index:
            failures.append("forbidden legacy admin shell identity is present")
    for label, root in roots.items():
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            try:
                raw = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for needle in FORBIDDEN_STATIC_CONTENT:
                if needle in raw:
                    failures.append(f"forbidden dev API origin {needle!r} in {label} static file: {path}")
                    break
    return failures


def _release_payload_validation_checks(*, remote_webapp: str, remote_adminapp: str, remote_marketing: str) -> list[str]:
    checks = [
        f"test -f {remote_webapp}/index.html",
        f"test -f {remote_adminapp}/index.html",
        f"test -f {remote_adminapp}/__build.json",
        f"test -f {remote_adminapp}/__routes.json",
        f"grep -Fq '\"app\": \"{ADMINAPP_IDENTITY}\"' {remote_adminapp}/__build.json",
        f"grep -Fq '\"schema\": \"{ADMINAPP_ROUTE_SCHEMA}\"' {remote_adminapp}/__routes.json",
        f"test -f {remote_marketing}/index.html",
        f"test -f {remote_marketing}/checkout/index.html",
    ]
    checks.extend(
        f"test ! -e {remote_marketing}/{file_name}"
        for file_name in FORBIDDEN_LEGACY_MARKETING_STATIC_FILES
    )
    return checks


def _post_deploy_smoke_commands(*, web_domain: str, api_domain: str, admin_domain: str) -> list[str]:
    def resolved_curl(domain: str, path: str, extra: str = "head -c 120 || true") -> str:
        return f"curl -fsS --insecure --resolve {domain}:443:127.0.0.1 https://{domain}{path} | {extra}"

    legacy_checks = []
    for file_name in FORBIDDEN_LEGACY_MARKETING_STATIC_FILES:
        path = f"/{file_name}"
        temp_path = f"/tmp/pokrov-{file_name}.smoke"
        legacy_checks.append(
            "status=$("
            f"curl -ksS -o {shlex.quote(temp_path)} -w '%{{http_code}}' "
            f"--resolve {shlex.quote(web_domain)}:443:127.0.0.1 "
            f"https://{shlex.quote(web_domain)}{path}"
            "); "
            "if [ \"$status\" = \"404\" ] || [ \"$status\" = \"410\" ]; then "
            "echo absent_or_fallback; "
            f"elif grep -Eq '^[0-9a-fA-F]{{32,128}}$|payment-page-global' {shlex.quote(temp_path)}; then "
            "echo legacy_static_present; "
            "else echo absent_or_fallback; "
            "fi; "
            f"rm -f {shlex.quote(temp_path)}"
        )

    return [
        resolved_curl(api_domain, "/api/health", "head -c 200 || true"),
        resolved_curl(web_domain, "/", "head -c 80 || true"),
        resolved_curl("app.pokrov.space", "/", "head -c 80 || true"),
        resolved_curl(admin_domain, "/", "head -c 80 || true"),
        resolved_curl(admin_domain, "/__build.json", f"grep -Fq '\"app\": \"{ADMINAPP_IDENTITY}\"' && echo operator_build_ok"),
        resolved_curl(admin_domain, "/__routes.json", f"grep -Fq '\"schema\": \"{ADMINAPP_ROUTE_SCHEMA}\"' && echo operator_routes_ok"),
        *legacy_checks,
        resolved_curl("pay.pokrov.space", "/checkout/", "head -c 120 || true"),
    ]


def _build_local_static_bundles(*, local_webapp: Path, local_adminapp: Path, local_marketing: Path, release_id: str) -> None:
    with tempfile.TemporaryDirectory(prefix="pokrov-static-") as temp_root:
        temp_dir = Path(temp_root)
        webapp_bundle = temp_dir / f"webapp-{release_id}.tar.gz"
        adminapp_bundle = temp_dir / f"adminapp-{release_id}.tar.gz"
        marketing_bundle = temp_dir / f"marketing-{release_id}.tar.gz"
        _strip_next_static_cache_busting(local_webapp, label="webapp")
        _strip_next_static_cache_busting(local_adminapp, label="adminapp")
        _strip_next_static_cache_busting(local_marketing, label="marketing")
        _build_static_bundle(local_webapp, webapp_bundle, label="webapp")
        _build_static_bundle(local_adminapp, adminapp_bundle, label="adminapp")
        _build_static_bundle(local_marketing, marketing_bundle, label="marketing")


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


def _adminapp_rollback_command(
    *,
    remote_root: str,
    expected_current_route_hash: str,
    expected_current_cutover_hash: str,
    expected_rollback_route_hash: str,
    expected_rollback_cutover_hash: str,
) -> str:
    hashes = (
        expected_current_route_hash,
        expected_current_cutover_hash,
        expected_rollback_route_hash,
        expected_rollback_cutover_hash,
    )
    if any(not re.fullmatch(r"[0-9a-f]{64}", value or "") for value in hashes):
        raise ValueError("adminapp rollback requires exact lowercase SHA-256 fingerprints")
    root = str(remote_root or "").rstrip("/")
    if not root.startswith("/") or root in {"", "/"}:
        raise ValueError("adminapp rollback remote root is invalid")
    releases_root = f"{root}/releases"
    validate = (
        "import json,sys; p=json.load(open(sys.argv[1],encoding='utf-8')); "
        "assert p.get('route_manifest_hash')==sys.argv[2]; "
        "assert p.get('cutover_matrix_hash')==sys.argv[3]"
    )
    return f"""
set -euo pipefail
current=$(readlink -f {shlex.quote(root + '/adminapp')})
rollback=$(readlink -f {shlex.quote(root + '/adminapp.rollback')})
case "$current" in {shlex.quote(releases_root)}/*/adminapp) ;; *) exit 41 ;; esac
case "$rollback" in {shlex.quote(releases_root)}/*/adminapp) ;; *) exit 42 ;; esac
test "$current" != "$rollback"
python3 -c {shlex.quote(validate)} "$current/__build.json" {shlex.quote(expected_current_route_hash)} {shlex.quote(expected_current_cutover_hash)}
python3 -c {shlex.quote(validate)} "$rollback/__build.json" {shlex.quote(expected_rollback_route_hash)} {shlex.quote(expected_rollback_cutover_hash)}
ln -sfn "$rollback" {shlex.quote(root + '/adminapp.next')}
mv -T {shlex.quote(root + '/adminapp.next')} {shlex.quote(root + '/adminapp')}
ln -sfn "$current" {shlex.quote(root + '/adminapp.rollback.next')}
mv -T {shlex.quote(root + '/adminapp.rollback.next')} {shlex.quote(root + '/adminapp.rollback')}
test "$(readlink -f {shlex.quote(root + '/adminapp')})" = "$rollback"
python3 -c {shlex.quote(validate)} {shlex.quote(root + '/adminapp/__build.json')} {shlex.quote(expected_rollback_route_hash)} {shlex.quote(expected_rollback_cutover_hash)}
""".strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="Deploy marketing/out + webapp/out + adminapp/out to brain and reload Caddy.")
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
        "--admin-domain",
        default="admin.pokrov.space",
        help="Public admin domain for adminapp checks",
    )
    ap.add_argument(
        "--domain",
        default="",
        help="Deprecated alias for --web-domain (kept for backward compatibility)",
    )
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--plan-only", action="store_true", help="Validate and bundle local static outputs without SSH.")
    ap.add_argument("--rollback-adminapp", action="store_true", help="Atomically switch adminapp to the retained rollback bundle.")
    ap.add_argument("--confirm-adminapp-rollback", default="")
    ap.add_argument("--expected-current-route-hash", default="")
    ap.add_argument("--expected-current-cutover-hash", default="")
    ap.add_argument("--expected-rollback-route-hash", default="")
    ap.add_argument("--expected-rollback-cutover-hash", default="")
    args = ap.parse_args()

    if args.rollback_adminapp:
        if args.plan_only:
            raise SystemExit("--rollback-adminapp and --plan-only are mutually exclusive")
        if args.confirm_adminapp_rollback != "ROLLBACK_ADMINAPP":
            raise SystemExit("adminapp rollback requires --confirm-adminapp-rollback ROLLBACK_ADMINAPP")
        try:
            rollback_command = _adminapp_rollback_command(
                remote_root="/var/www/portal",
                expected_current_route_hash=args.expected_current_route_hash,
                expected_current_cutover_hash=args.expected_current_cutover_hash,
                expected_rollback_route_hash=args.expected_rollback_route_hash,
                expected_rollback_cutover_hash=args.expected_rollback_cutover_hash,
            )
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        from node_access import connect_node

        ssh, auth_method = connect_node(
            code="brain",
            host=args.brain_ip,
            user=args.ssh_user,
            port=args.ssh_port,
            passwords_path=Path(args.passwords),
        )
        try:
            _safe_print(f"brain auth: {auth_method}")
            code, out, err = _run(ssh, rollback_command, timeout=120)
            if code != 0:
                raise SystemExit(f"Adminapp rollback failed:\n{out}\n{err}")
            _safe_print("adminapp rollback pointer switched and exact fingerprints revalidated")
            return 0
        finally:
            ssh.close()

    local_webapp = REPO_ROOT / "webapp" / "out"
    local_adminapp = REPO_ROOT / "adminapp" / "out"
    local_mkt = REPO_ROOT / "marketing" / "out"
    local_failures = _local_static_output_validation_failures(
        local_webapp=local_webapp,
        local_adminapp=local_adminapp,
        local_marketing=local_mkt,
    )
    if local_failures:
        raise SystemExit("\n".join(local_failures))
    web_domain = (args.domain or "").strip() or (args.web_domain or "").strip()
    api_domain = (args.api_domain or "").strip()
    admin_domain = (args.admin_domain or "").strip()
    if not web_domain:
        raise SystemExit("Missing --web-domain")
    if not api_domain:
        raise SystemExit("Missing --api-domain")
    if not admin_domain:
        raise SystemExit("Missing --admin-domain")

    release_id = _release_id()
    if args.plan_only:
        _build_local_static_bundles(
            local_webapp=local_webapp,
            local_adminapp=local_adminapp,
            local_marketing=local_mkt,
            release_id=release_id,
        )
        _safe_print("[plan-only] local static bundles validated and built; SSH deploy skipped")
        return 0

    from node_access import connect_node

    ssh, auth_method = connect_node(
        code="brain",
        host=args.brain_ip,
        user=args.ssh_user,
        port=args.ssh_port,
        passwords_path=Path(args.passwords),
    )
    try:
        _safe_print(f"brain auth: {auth_method}")
        remote_root = "/var/www/portal"
        releases_root = f"{remote_root}/releases"
        remote_release = f"{releases_root}/{release_id}"
        remote_webapp = f"{remote_release}/webapp"
        remote_adminapp = f"{remote_release}/adminapp"
        remote_marketing = f"{remote_release}/marketing"

        # Upload into a versioned release directory first, then switch symlinks.
        _run(ssh, f"mkdir -p {remote_webapp} {remote_adminapp} {remote_marketing}", timeout=60)

        with tempfile.TemporaryDirectory(prefix="pokrov-static-") as temp_root:
            temp_dir = Path(temp_root)
            webapp_bundle = temp_dir / f"webapp-{release_id}.tar.gz"
            adminapp_bundle = temp_dir / f"adminapp-{release_id}.tar.gz"
            marketing_bundle = temp_dir / f"marketing-{release_id}.tar.gz"
            _strip_next_static_cache_busting(local_webapp, label="webapp")
            _strip_next_static_cache_busting(local_adminapp, label="adminapp")
            _strip_next_static_cache_busting(local_mkt, label="marketing")
            _build_static_bundle(local_webapp, webapp_bundle, label="webapp")
            _build_static_bundle(local_adminapp, adminapp_bundle, label="adminapp")
            _build_static_bundle(local_mkt, marketing_bundle, label="marketing")

            sftp = ssh.open_sftp()
            try:
                _deploy_static_bundle(ssh, sftp, webapp_bundle, label="webapp", remote_dir=remote_webapp, release_id=release_id)
                _deploy_static_bundle(ssh, sftp, adminapp_bundle, label="adminapp", remote_dir=remote_adminapp, release_id=release_id)
                _deploy_static_bundle(ssh, sftp, marketing_bundle, label="marketing", remote_dir=remote_marketing, release_id=release_id)
            finally:
                sftp.close()

        # Validate release payload before switching public paths.
        for check in _release_payload_validation_checks(
            remote_webapp=remote_webapp,
            remote_adminapp=remote_adminapp,
            remote_marketing=remote_marketing,
        ):
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
if [ -e {remote_root}/adminapp ] && [ ! -L {remote_root}/adminapp ]; then
  mv {remote_root}/adminapp {remote_root}/legacy_backups/adminapp-$(date +%s)
fi
if [ -L {remote_root}/adminapp ]; then
  previous_adminapp=$(readlink -f {remote_root}/adminapp)
  case "$previous_adminapp" in
    {releases_root}/*)
      ln -sfn "$previous_adminapp" {remote_root}/adminapp.rollback.next
      mv -T {remote_root}/adminapp.rollback.next {remote_root}/adminapp.rollback
      ;;
  esac
fi

ln -sfn {remote_webapp} {remote_root}/webapp.next
mv -T {remote_root}/webapp.next {remote_root}/webapp
ln -sfn {remote_adminapp} {remote_root}/adminapp.next
mv -T {remote_root}/adminapp.next {remote_root}/adminapp
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
        for c in _post_deploy_smoke_commands(web_domain=web_domain, api_domain=api_domain, admin_domain=admin_domain):
            _, out, err = _run(ssh, c, timeout=30)
            _safe_print(out.strip() or err.strip())
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
