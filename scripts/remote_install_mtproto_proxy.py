#!/usr/bin/env python3
from __future__ import annotations

"""
Install the owner-approved Telegram MTProto proxy exception on a node.

The proxy is deliberately kept outside the normal POKROV delivery pool. It is a
Telegram-only sidecar and does not host control-plane services. The 2026-04-24
live endpoint is the dedicated free node on TCP/9443; the mini attempt is
disabled because Telegram reachability from that host is degraded.
"""

import argparse
import hashlib
import io
import re
import secrets
import shlex
import sys
import urllib.request
from pathlib import Path

import paramiko
from ssh_host_keys import configure_ssh_host_key_policy


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from node_access import connect_node  # noqa: E402
from node_passwords import parse_passwords  # noqa: E402


DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
DEFAULT_HOST = "151.245.217.23"
DEFAULT_UNIT_NAME = "portal-mtproto"
DEFAULT_INSTALL_ROOT = "/opt/portal-mtproto"
DEFAULT_REPO_URL = "https://github.com/TelegramMessenger/MTProxy"


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 120) -> tuple[int, str, str]:
    _stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    return code, stdout.read().decode(errors="replace"), stderr.read().decode(errors="replace")


def _run_script(ssh: paramiko.SSHClient, script: str, *, timeout: int = 1800) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command("sudo -n bash -s", timeout=timeout)
    stdin.write(script)
    stdin.channel.shutdown_write()
    code = stdout.channel.recv_exit_status()
    return code, stdout.read().decode(errors="replace"), stderr.read().decode(errors="replace")


def _candidate_values_near_marker(path: Path, marker_patterns: list[str]) -> list[str]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    marker_idx: int | None = None
    compiled = [re.compile(pattern, flags=re.IGNORECASE) for pattern in marker_patterns]
    for idx, line in enumerate(lines):
        if any(pattern.search(line) for pattern in compiled):
            marker_idx = idx
            break
    if marker_idx is None:
        return []

    out: list[str] = []
    for raw in lines[marker_idx + 1 : marker_idx + 15]:
        value = raw.strip()
        if not value:
            continue
        if re.fullmatch(r"(\d{1,3}\.){3}\d{1,3}", value):
            continue
        if value.startswith(("ssh-ed25519 ", "ssh-rsa ", "PuTTY-User-Key-File-")):
            continue
        if "PRIVATE KEY" in value or "http://" in value or "https://" in value:
            continue
        out.append(value)
    return out


def _load_ssh_credentials(
    *,
    node_code: str,
    passwords_path: Path,
    ssh_user: str,
    ssh_password_env: str,
) -> tuple[str, str]:
    import os

    env_password = os.getenv(ssh_password_env, "").strip() if ssh_password_env else ""
    if env_password:
        return (ssh_user or "root"), env_password

    code = str(node_code or "").strip().lower()
    if code == "mini":
        values = _candidate_values_near_marker(passwords_path, [r"\b(ru sber|russia|rfmini)\b"])
        if len(values) >= 2:
            return (ssh_user or values[0]), values[1]

    password = parse_passwords(passwords_path, requested_codes=[code]).get(code, "").strip()
    if password:
        return (ssh_user or "root"), password
    raise RuntimeError(f"No SSH password material found for node {node_code}")


def _ssh_connect(*, host: str, port: int, user: str, password: str) -> paramiko.SSHClient:
    cli = paramiko.SSHClient()
    configure_ssh_host_key_policy(cli)
    cli.connect(
        host,
        port=port,
        username=user,
        password=password,
        timeout=30,
        banner_timeout=30,
        auth_timeout=30,
        allow_agent=False,
        look_for_keys=False,
    )
    transport = cli.get_transport()
    if transport:
        transport.set_keepalive(30)
    return cli


def _connect_for_install(
    *,
    node_code: str,
    host: str,
    port: int,
    ssh_user: str,
    passwords_path: Path,
    ssh_password_env: str,
) -> paramiko.SSHClient:
    code = str(node_code or "").strip().lower()
    # The mini host's local PASSWORDS block uses a non-root SSH user that the
    # shared node_access parser does not model, so keep its compatibility path.
    if code == "mini" and not str(ssh_user or "").strip():
        user, password = _load_ssh_credentials(
            node_code=code,
            passwords_path=passwords_path,
            ssh_user="",
            ssh_password_env=ssh_password_env,
        )
        return _ssh_connect(host=host, port=port, user=user, password=password)

    ssh, _auth_method = connect_node(
        code=code,
        host=host,
        user=str(ssh_user or "root").strip(),
        port=int(port),
        passwords_path=passwords_path,
    )
    return ssh


def _normalize_secret(value: str) -> str:
    secret = str(value or "").strip().lower()
    if secret.startswith("dd") and len(secret) == 34:
        secret = secret[2:]
    if not re.fullmatch(r"[0-9a-f]{32}", secret):
        raise ValueError("MTProto secret must be 32 hex chars, optionally prefixed with dd for links")
    return secret


def mtproto_links(*, host: str, port: int, secret: str, random_padding: bool = True) -> tuple[str, str]:
    normalized_secret = _normalize_secret(secret)
    link_secret = f"dd{normalized_secret}" if random_padding else normalized_secret
    tg_link = f"tg://proxy?server={host}&port={int(port)}&secret={link_secret}"
    https_link = f"https://t.me/proxy?server={host}&port={int(port)}&secret={link_secret}"
    return tg_link, https_link


def render_service_unit(*, unit_name: str = DEFAULT_UNIT_NAME, install_root: str = DEFAULT_INSTALL_ROOT) -> str:
    return f"""[Unit]
Description=POKROV Telegram MTProto proxy
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
EnvironmentFile=/etc/{unit_name}.env
WorkingDirectory={install_root}
ExecStart=/usr/bin/unshare --fork --pid --mount-proc {install_root}/start.sh
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
"""


def render_refresh_service(*, unit_name: str = DEFAULT_UNIT_NAME, install_root: str = DEFAULT_INSTALL_ROOT) -> str:
    command = (
        "set -euo pipefail; "
        f"curl -4 -fsSL https://core.telegram.org/getProxySecret -o {install_root}/proxy-secret.tmp; "
        f"mv {install_root}/proxy-secret.tmp {install_root}/proxy-secret; "
        f"curl -4 -fsSL https://core.telegram.org/getProxyConfig -o {install_root}/proxy-multi.conf.tmp; "
        f"mv {install_root}/proxy-multi.conf.tmp {install_root}/proxy-multi.conf; "
        f"systemctl try-restart {unit_name}.service"
    )
    return f"""[Unit]
Description=Refresh POKROV MTProto proxy Telegram config
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/bin/bash -lc {shlex.quote(command)}
"""


def render_refresh_timer(*, unit_name: str = DEFAULT_UNIT_NAME) -> str:
    return f"""[Unit]
Description=Daily refresh for POKROV MTProto proxy config

[Timer]
OnCalendar=daily
RandomizedDelaySec=30m
Persistent=true

[Install]
WantedBy=timers.target
"""


def render_env(
    *,
    advertised_host: str,
    listen_port: int,
    stats_port: int,
    workers: int,
    secret: str,
    tg_link: str,
    https_link: str,
) -> str:
    return "\n".join(
        [
            f"MTPROTO_ADVERTISED_HOST={advertised_host}",
            f"MTPROTO_LISTEN_PORT={int(listen_port)}",
            f"MTPROTO_STATS_PORT={int(stats_port)}",
            f"MTPROTO_WORKERS={int(workers)}",
            f"MTPROTO_SECRET={_normalize_secret(secret)}",
            f"MTPROTO_TG_LINK={tg_link}",
            f"MTPROTO_HTTPS_LINK={https_link}",
            "",
        ]
    )


def _single_quote(value: str) -> str:
    return "'" + str(value).replace("'", "'\"'\"'") + "'"


def render_install_script(
    *,
    repo_url: str,
    install_root: str,
    unit_name: str,
    env_body: str,
    service_body: str,
    refresh_service_body: str,
    refresh_timer_body: str,
    stop_services: list[str],
    allow_ufw: bool,
    enable_refresh_timer: bool,
    prefetched_proxy_secret_path: str = "",
    prefetched_proxy_config_path: str = "",
) -> str:
    stop_services_literal = " ".join(shlex.quote(item) for item in stop_services if item.strip())
    stop_service_commands = (
        f"""for svc in {stop_services_literal}; do
  if systemctl list-unit-files "$svc.service" >/dev/null 2>&1; then
    systemctl disable --now "$svc.service" >/dev/null 2>&1 || true
  fi
done"""
        if stop_services_literal
        else ":"
    )
    refresh_timer_commands = (
        'systemctl enable "$unit_name-config-refresh.timer" >/dev/null\n'
        'systemctl restart "$unit_name-config-refresh.timer"'
        if enable_refresh_timer
        else 'systemctl disable --now "$unit_name-config-refresh.timer" >/dev/null 2>&1 || true'
    )
    proxy_secret_fetch = (
        f"install -m 0644 {shlex.quote(prefetched_proxy_secret_path)} \"$install_root/proxy-secret\"\n"
        f"rm -f {shlex.quote(prefetched_proxy_secret_path)}"
        if prefetched_proxy_secret_path
        else 'curl -4 -fsSL https://core.telegram.org/getProxySecret -o "$install_root/proxy-secret.tmp"\n'
        'mv "$install_root/proxy-secret.tmp" "$install_root/proxy-secret"'
    )
    proxy_config_fetch = (
        f"install -m 0644 {shlex.quote(prefetched_proxy_config_path)} \"$install_root/proxy-multi.conf\"\n"
        f"rm -f {shlex.quote(prefetched_proxy_config_path)}"
        if prefetched_proxy_config_path
        else 'curl -4 -fsSL https://core.telegram.org/getProxyConfig -o "$install_root/proxy-multi.conf.tmp"\n'
        'mv "$install_root/proxy-multi.conf.tmp" "$install_root/proxy-multi.conf"'
    )
    return f"""set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
install_root={shlex.quote(install_root)}
repo_url={shlex.quote(repo_url)}
repo_dir="$install_root/MTProxy"
unit_name={shlex.quote(unit_name)}

apt-get update -y
apt-get install -y git curl ca-certificates build-essential libssl-dev zlib1g-dev xxd util-linux
install -d -m 0755 "$install_root"

if [ ! -d "$repo_dir/.git" ]; then
  rm -rf "$repo_dir"
  git clone --depth 1 "$repo_url" "$repo_dir"
else
  git -C "$repo_dir" fetch --depth 1 origin master
  git -C "$repo_dir" reset --hard origin/master
fi

make -C "$repo_dir" clean >/dev/null 2>&1 || true
make -C "$repo_dir" -j"$(nproc)"
install -m 0755 "$repo_dir/objs/bin/mtproto-proxy" "$install_root/mtproto-proxy"
cat >"$install_root/start.sh" <<'EOF_START'
#!/usr/bin/env bash
set -euo pipefail
exec __INSTALL_ROOT__/mtproto-proxy \
  -u nobody \
  -p "${{MTPROTO_STATS_PORT}}" \
  -H "${{MTPROTO_LISTEN_PORT}}" \
  -S "${{MTPROTO_SECRET}}" \
  --aes-pwd __INSTALL_ROOT__/proxy-secret \
  __INSTALL_ROOT__/proxy-multi.conf \
  -M "${{MTPROTO_WORKERS}}"
EOF_START
sed -i "s#__INSTALL_ROOT__#$install_root#g" "$install_root/start.sh"
chmod 0755 "$install_root/start.sh"

{proxy_secret_fetch}
{proxy_config_fetch}

cat >"/etc/$unit_name.env" <<'EOF_ENV'
{env_body.rstrip()}
EOF_ENV
chmod 600 "/etc/$unit_name.env"

cat >"/etc/systemd/system/$unit_name.service" <<'EOF_SERVICE'
{service_body.rstrip()}
EOF_SERVICE

cat >"/etc/systemd/system/$unit_name-config-refresh.service" <<'EOF_REFRESH_SERVICE'
{refresh_service_body.rstrip()}
EOF_REFRESH_SERVICE

cat >"/etc/systemd/system/$unit_name-config-refresh.timer" <<'EOF_REFRESH_TIMER'
{refresh_timer_body.rstrip()}
EOF_REFRESH_TIMER

. "/etc/$unit_name.env"

{stop_service_commands}

if command -v ufw >/dev/null 2>&1 && ufw status | grep -q '^Status: active'; then
  {"ufw allow ${MTPROTO_LISTEN_PORT}/tcp comment 'POKROV MTProto proxy' || true" if allow_ufw else ":"}
fi

systemctl daemon-reload
systemctl enable "$unit_name.service" >/dev/null
systemctl restart "$unit_name.service"
{refresh_timer_commands}
systemctl is-active --quiet "$unit_name.service"
ss -tlnp | grep -E "[:.]${{MTPROTO_LISTEN_PORT}}\\b" || true
"""


def _redact_runtime_output(text: str) -> str:
    lines: list[str] = []
    for line in str(text or "").splitlines():
        if "MTPROTO_SECRET" in line or "MTPROTO_TG_LINK" in line or "MTPROTO_HTTPS_LINK" in line:
            continue
        lines.append(line)
    return "\n".join(lines)


def _fetch_public_bytes(url: str, *, timeout: int = 30) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "POKROV-ops/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _upload_bytes(ssh: paramiko.SSHClient, *, data: bytes, remote_path: str) -> None:
    sftp = ssh.open_sftp()
    try:
        with sftp.file(remote_path, "wb") as handle:
            handle.write(data)
    finally:
        sftp.close()


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Install a Telegram MTProto proxy sidecar on a node.")
    parser.add_argument("--node-code", default="free")
    parser.add_argument("--node-host", default=DEFAULT_HOST)
    parser.add_argument("--ssh-user", default="", help="SSH user. For mini, omitted means read it from the local passwords file.")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--ssh-password-env", default="NODE_PASS_FREE")
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--listen-port", type=int, default=9443)
    parser.add_argument("--stats-port", type=int, default=8888)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--secret", default="", help="Optional 32-hex MTProto secret. Omit to generate one.")
    parser.add_argument("--no-random-padding", action="store_true")
    parser.add_argument("--install-root", default=DEFAULT_INSTALL_ROOT)
    parser.add_argument("--repo-url", default=DEFAULT_REPO_URL)
    parser.add_argument("--unit-name", default=DEFAULT_UNIT_NAME)
    parser.add_argument("--stop-service", action="append", default=[], help="Systemd service to disable before binding the MTProto TCP port.")
    parser.add_argument(
        "--prefetch-telegram-config",
        action="store_true",
        help="Fetch proxy-secret/proxy-multi.conf locally and upload them when the target host cannot reach core.telegram.org.",
    )
    parser.add_argument(
        "--enable-refresh-timer",
        action="store_true",
        help="Enable daily Telegram config refresh from the target host. Leave off when the host cannot reach core.telegram.org.",
    )
    parser.add_argument("--no-ufw-allow", action="store_true")
    parser.add_argument("--render-only", action="store_true")
    parser.add_argument("--print-link", action="store_true", help="Print the generated proxy links. Avoid this in logs.")
    args = parser.parse_args()

    secret = _normalize_secret(args.secret or secrets.token_hex(16))
    tg_link, https_link = mtproto_links(
        host=str(args.node_host).strip(),
        port=int(args.listen_port),
        secret=secret,
        random_padding=not args.no_random_padding,
    )
    env_body = render_env(
        advertised_host=str(args.node_host).strip(),
        listen_port=int(args.listen_port),
        stats_port=int(args.stats_port),
        workers=max(1, int(args.workers)),
        secret=secret,
        tg_link=tg_link,
        https_link=https_link,
    )
    service_body = render_service_unit(unit_name=args.unit_name, install_root=args.install_root.rstrip("/"))
    refresh_service_body = render_refresh_service(unit_name=args.unit_name, install_root=args.install_root.rstrip("/"))
    refresh_timer_body = render_refresh_timer(unit_name=args.unit_name)
    remote_prefetch_dir = f"/tmp/{args.unit_name}-prefetch-{secrets.token_hex(8)}"
    prefetched_proxy_secret_path = f"{remote_prefetch_dir}/proxy-secret" if args.prefetch_telegram_config else ""
    prefetched_proxy_config_path = f"{remote_prefetch_dir}/proxy-multi.conf" if args.prefetch_telegram_config else ""
    install_script = render_install_script(
        repo_url=args.repo_url,
        install_root=args.install_root.rstrip("/"),
        unit_name=args.unit_name,
        env_body=env_body,
        service_body=service_body,
        refresh_service_body=refresh_service_body,
        refresh_timer_body=refresh_timer_body,
        stop_services=[str(item).strip() for item in args.stop_service or [] if str(item).strip()],
        allow_ufw=not args.no_ufw_allow,
        enable_refresh_timer=bool(args.enable_refresh_timer),
        prefetched_proxy_secret_path=prefetched_proxy_secret_path,
        prefetched_proxy_config_path=prefetched_proxy_config_path,
    )

    if args.render_only:
        print(install_script)
        return 0

    ssh = _connect_for_install(
        node_code=str(args.node_code).strip().lower(),
        host=str(args.node_host).strip(),
        port=int(args.ssh_port),
        ssh_user=str(args.ssh_user or "").strip(),
        passwords_path=Path(args.passwords),
        ssh_password_env=str(args.ssh_password_env or "").strip(),
    )
    try:
        code, out, err = _run(ssh, "sudo -n true", timeout=30)
        if code != 0:
            raise RuntimeError("remote user does not have passwordless sudo; aborting before install")

        if args.prefetch_telegram_config:
            proxy_secret = _fetch_public_bytes("https://core.telegram.org/getProxySecret")
            proxy_config = _fetch_public_bytes("https://core.telegram.org/getProxyConfig")
            _run(ssh, f"mkdir -p {shlex.quote(remote_prefetch_dir)} && chmod 700 {shlex.quote(remote_prefetch_dir)}", timeout=30)
            _upload_bytes(ssh, data=proxy_secret, remote_path=prefetched_proxy_secret_path)
            _upload_bytes(ssh, data=proxy_config, remote_path=prefetched_proxy_config_path)

        code, out, err = _run_script(ssh, install_script, timeout=2400)
        if code != 0:
            raise RuntimeError((err or out or "remote MTProto install failed").strip())

        link_hash = hashlib.sha256(https_link.encode("utf-8")).hexdigest()[:16]
        print(f"node={args.node_code} host={args.node_host} unit={args.unit_name} status=installed")
        print(f"listen=tcp/{int(args.listen_port)} stats=127.0.0.1:{int(args.stats_port)} link_sha256={link_hash}")
        if args.print_link:
            print(f"mtproto_tg_link={tg_link}")
            print(f"mtproto_https_link={https_link}")
        redacted = _redact_runtime_output(out)
        if redacted.strip():
            print(redacted.strip())
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
