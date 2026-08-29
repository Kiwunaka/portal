from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shlex
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import x25519

from node_access import DEFAULT_PASSWORDS, connect_node


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_REVISION = "01ce413ad55758345fe1e4ab5c4a44ce3b03b6c2"
NODE_CODE = "de"
SERVER_GO_TAG = "v3.1.20260814"
SERVER_GO_COMMIT = "1b86b2ae0e493e7ea93f8c1a0f0cb6735b1551f1"
TOOLS_TAG = "v3.1.20260812"
TOOLS_COMMIT = "ee0f0a9aa34ff0a0da4b3433b9512781cfe02843"
AWG2_INTERFACE = "pokrovawg2"
AWG31_INTERFACE = "pokrovawg31"
AWG2_PORT = 4500
AWG31_PORT = 3478
AWG2_SERVER_RECORD = "de-awg2-20260827-01"
AWG31_SERVER_RECORD = "de-awg31-20260828-03-randomized-trailers"
AWG31_GENERATION = "awg31-lab-v3-randomized-trailers"
AWG31_ENDPOINT_REVISION = "awg31-v1"
AWG31_VARIANT = "randomized_trailers_v1"
AWG31_VARIANT_DROPIN = (
    f"/etc/systemd/system/pokrov-awg-lab@{AWG31_INTERFACE}.service.d/variant.conf"
)
PACKAGE_NAME = "space.pokrov.pokrov_android_shell"
SERVER_BINARY_TARGET = f"/usr/local/libexec/pokrov/amneziawg-go-{SERVER_GO_TAG}"
AWG_TARGET = "/usr/local/bin/awg"
AWG_QUICK_TARGET = "/usr/local/bin/awg-quick"
UNIT_TARGET = "/etc/systemd/system/pokrov-awg-lab@.service"
CONFIG_ROOT = "/etc/amnezia/amneziawg"
SAFE_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ActivationError(RuntimeError):
    pass


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_remote(ssh: Any, command: str, *, timeout: int = 120) -> str:
    _stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", "replace").strip()
    err = stderr.read().decode("utf-8", "replace").strip()
    if code != 0:
        raise ActivationError((err or out or f"remote exit={code}")[:1200])
    return out


def _run_remote_allow_failure(ssh: Any, command: str, *, timeout: int = 120) -> None:
    try:
        _run_remote(ssh, command, timeout=timeout)
    except Exception:
        return


def _psql(ssh: Any, sql: str) -> str:
    stdin, stdout, stderr = ssh.exec_command(
        "runuser -u postgres -- psql -d portal -At", timeout=60
    )
    stdin.write(sql + "\n")
    stdin.channel.shutdown_write()
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", "replace").strip()
    err = stderr.read().decode("utf-8", "replace").strip()
    if code != 0:
        raise ActivationError((err or "psql failed")[:1200])
    return out


def _sftp_write(sftp: Any, remote_path: str, value: bytes, mode: int) -> None:
    temp_path = f"{remote_path}.next-{os.getpid()}"
    try:
        with sftp.open(temp_path, "wb") as handle:
            handle.write(value)
            handle.flush()
        sftp.chmod(temp_path, mode)
        sftp.posix_rename(temp_path, remote_path)
    except Exception:
        try:
            sftp.remove(temp_path)
        except Exception:
            pass
        raise


def _load_emulator_identity(adb: Path, serial: str) -> tuple[str, str]:
    state = subprocess.run(
        [str(adb), "-s", serial, "get-state"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.strip()
    if state != "device":
        raise ActivationError(f"ADB target {serial} is not ready")
    remote_state = f"/data/user/0/{PACKAGE_NAME}/files/app-first-session-android.json"
    result = subprocess.run(
        [
            str(adb),
            "-s",
            serial,
            "exec-out",
            f"su -c 'cat {remote_state}'",
        ],
        check=True,
        capture_output=True,
    )
    try:
        payload = json.loads(result.stdout.decode("utf-8"))
    except Exception as exc:
        raise ActivationError("LDPlayer app-first state is unreadable") from exc
    install_id = str(payload.get("install_id") or "").strip()
    account_id = str(payload.get("account_id") or "").strip()
    if not install_id or not account_id:
        raise ActivationError("LDPlayer install/account identity is incomplete")
    return install_id, account_id


def _resolve_target_user(brain: Any, install_id: str) -> int:
    escaped = install_id.replace("'", "''")
    raw = _psql(
        brain,
        (
            "select u.tg_id from users u "
            "where u.app_install_id='"
            + escaped
            + "' order by u.app_last_seen_at desc nulls last limit 1;"
        ),
    )
    if not raw.isdigit() or int(raw) <= 0:
        raise ActivationError("LDPlayer install is not bound to one positive user")
    return int(raw)


def _entitlement_extension_needed(brain: Any, install_id: str) -> bool:
    escaped = install_id.replace("'", "''")
    raw = _psql(
        brain,
        (
            "select case when is_active and expiry_at > now() + interval '12 hours' "
            "then 'ready' else 'extend' end from users where app_install_id='"
            + escaped
            + "' limit 1;"
        ),
    )
    if raw not in {"ready", "extend"}:
        raise ActivationError("LDPlayer entitlement state is unreadable")
    return raw == "extend"


def _node_host(brain: Any) -> str:
    host = _psql(
        brain,
        f"select host from nodes where code='{NODE_CODE}' and enabled=true limit 1;",
    ).strip()
    if not host:
        raise ActivationError(f"enabled node {NODE_CODE} is missing")
    return host


def _private_and_public_key() -> tuple[str, str]:
    private_key = x25519.X25519PrivateKey.generate()
    private_raw = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_raw = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return (
        base64.b64encode(private_raw).decode("ascii"),
        base64.b64encode(public_raw).decode("ascii"),
    )


def _endpoint_material(
    node_address: str,
) -> tuple[dict[str, Any], dict[str, Any], str, str]:
    awg2_server_private, awg2_server_public = _private_and_public_key()
    awg2_client_private, awg2_client_public = _private_and_public_key()
    awg31_server_private, awg31_server_public = _private_and_public_key()
    awg31_client_private, awg31_client_public = _private_and_public_key()
    header_key = base64.b64encode(os.urandom(32)).decode("ascii")

    awg2_endpoint = {
        "useIntegratedTun": False,
        "private_key": awg2_client_private,
        "address": ["10.203.20.2/32"],
        "mtu": 1408,
        "jc": 4,
        "jmin": 40,
        "jmax": 70,
        "s1": 0,
        "s2": 0,
        "s3": 0,
        "s4": 0,
        "h1": "1000001",
        "h2": "1000002",
        "h3": "1000003",
        "h4": "1000004",
        "peers": [
            {
                "address": node_address,
                "port": AWG2_PORT,
                "public_key": awg2_server_public,
                "allowed_ips": ["0.0.0.0/0"],
                "persistent_keepalive_interval": 25,
            }
        ],
    }
    awg31_endpoint = {
        "useIntegratedTun": False,
        "contract_id": "pokrov.awg31.endpoint.v1",
        "private_key": awg31_client_private,
        "address": ["10.203.31.2/32"],
        "mtu": 1408,
        "jc": 6,
        "jmin": 48,
        "jmax": 96,
        "s1": 16,
        "s2": 16,
        "s3": 16,
        "s4": 16,
        "h1": "1100001-1100099",
        "h2": "1200001-1200099",
        "h3": "1300001-1300099",
        "h4": "1400001-1400099",
        "i1": "",
        "i2": "",
        "i3": "",
        "i4": "",
        "i5": "",
        "header_protection_key": header_key,
        # Randomized trailers vary the handshake-response length. Content
        # padding varies transport packets after the handshake completes.
        "content_padding_addition": "64-512",
        "rekey_after_time": "120",
        "rekey_timeout": "5",
        "reject_after_time": "180",
        "keepalive_timeout": "10",
        "max_handshake_attempts": "18",
        "random_trailers": True,
        "peers": [
            {
                "address": node_address,
                "port": AWG31_PORT,
                "public_key": awg31_server_public,
                "allowed_ips": ["0.0.0.0/0"],
                "persistent_keepalive_interval_range": "25",
            }
        ],
    }
    awg2_server = _server_config(
        interface=AWG2_INTERFACE,
        private_key=awg2_server_private,
        client_public_key=awg2_client_public,
        address="10.203.20.1/24",
        client_address="10.203.20.2/32",
        port=AWG2_PORT,
        reply_source=node_address,
        fields=(
            "Jc = 0\nJmin = 0\nJmax = 0\nS1 = 0\nS2 = 0\nS3 = 0\nS4 = 0\n"
            "H1 = 1000001\nH2 = 1000002\nH3 = 1000003\nH4 = 1000004"
        ),
    )
    awg31_server = _server_config(
        interface=AWG31_INTERFACE,
        private_key=awg31_server_private,
        client_public_key=awg31_client_public,
        address="10.203.31.1/24",
        client_address="10.203.31.2/32",
        port=AWG31_PORT,
        reply_source=node_address,
        fields=(
            "Jc = 0\nJmin = 0\nJmax = 0\nS1 = 16\nS2 = 16\nS3 = 16\nS4 = 16\n"
            "H1 = 1100001-1100099\nH2 = 1200001-1200099\n"
            "H3 = 1300001-1300099\nH4 = 1400001-1400099\n"
            f"HeaderProtectionKey = {header_key}"
        ),
    )
    return awg2_endpoint, awg31_endpoint, awg2_server, awg31_server


def _server_config(
    *,
    interface: str,
    private_key: str,
    client_public_key: str,
    address: str,
    client_address: str,
    port: int,
    reply_source: str,
    fields: str,
) -> str:
    reply_post_up, reply_post_down = _reply_source_policy_lines(
        interface, port, reply_source
    )
    reply_lines = "\n".join(
        [
            *(f"PostUp = {line}" for line in reply_post_up),
            *(f"PostDown = {line}" for line in reply_post_down),
        ]
    )
    return f"""[Interface]
PrivateKey = {private_key}
Address = {address}
ListenPort = {port}
MTU = 1408
Table = off
{fields}
PostUp = iptables -C FORWARD -i %i -o eth0 -j ACCEPT || iptables -A FORWARD -i %i -o eth0 -j ACCEPT
PostUp = iptables -C FORWARD -i eth0 -o %i -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT || iptables -A FORWARD -i eth0 -o %i -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
PostUp = iptables -t nat -C POSTROUTING -s {address.rsplit(".", 1)[0]}.0/24 -o eth0 -j MASQUERADE || iptables -t nat -A POSTROUTING -s {address.rsplit(".", 1)[0]}.0/24 -o eth0 -j MASQUERADE
{reply_lines}
PostDown = iptables -D FORWARD -i %i -o eth0 -j ACCEPT 2>/dev/null || true
PostDown = iptables -D FORWARD -i eth0 -o %i -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || true
PostDown = iptables -t nat -D POSTROUTING -s {address.rsplit(".", 1)[0]}.0/24 -o eth0 -j MASQUERADE 2>/dev/null || true

[Peer]
PublicKey = {client_public_key}
AllowedIPs = {client_address}
"""


def _reply_source_policy_lines(
    interface: str, port: int, reply_source: str
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    reply_comment = f"POKROV owned {interface} reply source"
    reply_rule = (
        f"iptables -t nat -C POSTROUTING -o eth0 -p udp -m udp --sport {port} "
        f"-m comment --comment '{reply_comment}' -j SNAT --to-source {reply_source}"
    )
    reply_add = reply_rule.replace(" -C POSTROUTING ", " -I POSTROUTING 1 ")
    reply_delete = reply_rule.replace(" -C POSTROUTING ", " -D POSTROUTING ")
    priority = 10_000 + port
    table = 20_000 + port
    gateway = (
        "$(ip -4 route show table main default | awk 'NR==1 { "
        'for(i=1;i<=NF;i++) if($i=="via") { print $(i+1); exit } }\')'
    )
    route_up = (
        f'gateway={gateway}; test -n "$gateway"; ip -4 route replace table {table} '
        f'default via "$gateway" dev eth0 src {reply_source}'
    )
    rule_up = (
        f"ip -4 rule show | grep -Eq '^{priority}:.*ipproto udp.*sport {port}.*lookup {table}' "
        f"|| ip -4 rule add priority {priority} ipproto udp sport {port} lookup {table}"
    )
    rule_down = f"ip -4 rule del priority {priority} 2>/dev/null || true"
    route_down = f"ip -4 route flush table {table}; ip -4 route flush cache"
    return (
        (route_up, rule_up, f"{reply_rule} || {reply_add}"),
        (f"{reply_delete} 2>/dev/null || true", rule_down, route_down),
    )


def _unit_content() -> bytes:
    return f"""[Unit]
Description=POKROV owned AWG lab via awg-quick for %I
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
Environment=WG_QUICK_USERSPACE_IMPLEMENTATION={SERVER_BINARY_TARGET}
ExecStart={AWG_QUICK_TARGET} up %i
ExecStop={AWG_QUICK_TARGET} down %i
ExecReload=/bin/bash -c 'exec {AWG_TARGET} syncconf %i <(exec {AWG_QUICK_TARGET} strip %i)'

[Install]
WantedBy=multi-user.target
""".encode("utf-8")


def _awg31_variant_dropin_content() -> bytes:
    return f"""[Service]
ExecStartPost={AWG_TARGET} set %i content-padding-addition 64-512 random-trailers on
""".encode("utf-8")


def _server_preflight(node: Any) -> dict[str, Any]:
    occupied: list[str] = []
    for path in (
        SERVER_BINARY_TARGET,
        AWG_TARGET,
        AWG_QUICK_TARGET,
        UNIT_TARGET,
        AWG31_VARIANT_DROPIN,
        f"{CONFIG_ROOT}/{AWG2_INTERFACE}.conf",
        f"{CONFIG_ROOT}/{AWG31_INTERFACE}.conf",
    ):
        state = _run_remote(
            node,
            f"if test -e {shlex.quote(path)}; then printf present; else printf absent; fi",
        )
        if state == "present":
            occupied.append(path)
    ports = {
        str(port): _run_remote(
            node,
            f"if ss -H -lun 'sport = :{port}' | grep -q .; then printf busy; else printf free; fi",
        )
        for port in (AWG2_PORT, AWG31_PORT)
    }
    return {"occupied_paths": occupied, "udp_ports": ports}


def _rollback_node(node: Any) -> None:
    for interface in (AWG31_INTERFACE, AWG2_INTERFACE):
        _run_remote_allow_failure(
            node,
            f"systemctl disable --now pokrov-awg-lab@{interface}.service",
        )
    targets = (
        f"{CONFIG_ROOT}/{AWG2_INTERFACE}.conf",
        f"{CONFIG_ROOT}/{AWG31_INTERFACE}.conf",
        UNIT_TARGET,
        SERVER_BINARY_TARGET,
        AWG_TARGET,
        AWG_QUICK_TARGET,
        AWG31_VARIANT_DROPIN,
    )
    _run_remote_allow_failure(
        node,
        "rm -f " + " ".join(shlex.quote(path) for path in targets),
    )
    _run_remote_allow_failure(node, "systemctl daemon-reload")


def _deploy_node(
    node: Any,
    *,
    server_binary: Path,
    tools_archive: Path,
    tools_sha256: str,
    awg2_server: str,
    awg31_server: str,
) -> dict[str, Any]:
    release_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stage = f"/root/pokrov-awg-lab-staging/{release_id}-{os.getpid()}"
    _run_remote(
        node, f"install -d -m 0700 {shlex.quote(stage)} {shlex.quote(stage + '/tools')}"
    )
    try:
        return _deploy_node_staged(
            node,
            stage=stage,
            server_binary=server_binary,
            tools_archive=tools_archive,
            tools_sha256=tools_sha256,
            awg2_server=awg2_server,
            awg31_server=awg31_server,
        )
    finally:
        _run_remote_allow_failure(node, f"rm -rf -- {shlex.quote(stage)}")


def _deploy_node_staged(
    node: Any,
    *,
    stage: str,
    server_binary: Path,
    tools_archive: Path,
    tools_sha256: str,
    awg2_server: str,
    awg31_server: str,
) -> dict[str, Any]:
    sftp = node.open_sftp()
    try:
        binary_remote = f"{stage}/amneziawg-go"
        tools_remote = f"{stage}/tools.tar"
        sftp.put(str(server_binary), binary_remote)
        sftp.chmod(binary_remote, 0o700)
        sftp.put(str(tools_archive), tools_remote)
        sftp.chmod(tools_remote, 0o600)
    finally:
        sftp.close()
    binary_sha256 = _sha256_file(server_binary)
    remote_hashes = _run_remote(
        node,
        f"sha256sum {shlex.quote(binary_remote)} {shlex.quote(tools_remote)}",
    )
    if binary_sha256 not in remote_hashes or tools_sha256 not in remote_hashes:
        raise ActivationError("uploaded AWG source/binary hash mismatch")
    _run_remote(
        node,
        f"tar -xf {shlex.quote(tools_remote)} -C {shlex.quote(stage + '/tools')}",
    )
    _run_remote(
        node,
        (
            f"make -C {shlex.quote(stage + '/tools/src')} "
            "WITH_WGQUICK=yes WITH_SYSTEMDUNITS=no WITH_BASHCOMPLETION=no"
        ),
        timeout=300,
    )
    _run_remote(
        node,
        (
            "install -d -m 0755 /usr/local/libexec/pokrov /usr/local/bin "
            f"&& install -m 0755 {shlex.quote(binary_remote)} {shlex.quote(SERVER_BINARY_TARGET)} "
            f"&& install -m 0755 {shlex.quote(stage + '/tools/src/wg')} {shlex.quote(AWG_TARGET)} "
            f"&& tr -d '\\r' < {shlex.quote(stage + '/tools/src/wg-quick/linux.bash')} > {shlex.quote(AWG_QUICK_TARGET)} "
            f"&& chmod 0755 {shlex.quote(AWG_QUICK_TARGET)} "
            f"&& install -d -m 0700 {shlex.quote(CONFIG_ROOT)}"
        ),
    )
    _run_remote(
        node,
        f"test -x {shlex.quote(AWG_QUICK_TARGET)} && "
        f"head -n 1 {shlex.quote(AWG_QUICK_TARGET)} | grep -qx '#!/bin/bash'",
    )
    _run_remote(
        node,
        "install -d -m 0755 " + shlex.quote(AWG31_VARIANT_DROPIN.rsplit("/", 1)[0]),
    )
    sftp = node.open_sftp()
    try:
        _sftp_write(sftp, UNIT_TARGET, _unit_content(), 0o644)
        _sftp_write(
            sftp,
            AWG31_VARIANT_DROPIN,
            _awg31_variant_dropin_content(),
            0o644,
        )
        _sftp_write(
            sftp,
            f"{CONFIG_ROOT}/{AWG2_INTERFACE}.conf",
            awg2_server.encode("utf-8"),
            0o600,
        )
        _sftp_write(
            sftp,
            f"{CONFIG_ROOT}/{AWG31_INTERFACE}.conf",
            awg31_server.encode("utf-8"),
            0o600,
        )
    finally:
        sftp.close()
    _run_remote(node, "systemctl daemon-reload")
    for interface in (AWG2_INTERFACE, AWG31_INTERFACE):
        _run_remote(
            node,
            f"systemctl enable --now pokrov-awg-lab@{interface}.service",
            timeout=120,
        )
    checks: dict[str, Any] = {}
    for interface, port in (
        (AWG2_INTERFACE, AWG2_PORT),
        (AWG31_INTERFACE, AWG31_PORT),
    ):
        active = _run_remote(
            node, f"systemctl is-active pokrov-awg-lab@{interface}.service"
        )
        listen_port = _run_remote(node, f"{AWG_TARGET} show {interface} listen-port")
        interface_up = _run_remote(
            node,
            f"if ip link show dev {interface} | grep -Eq 'state (UNKNOWN|UP)'; then printf yes; else printf no; fi",
        )
        socket_ready = _run_remote(
            node,
            f"if ss -H -lun 'sport = :{port}' | grep -q .; then printf yes; else printf no; fi",
        )
        checks[interface] = {
            "service_active": active == "active",
            "listen_port_match": listen_port == str(port),
            "interface_up": interface_up == "yes",
            "udp_socket_ready": socket_ready == "yes",
        }
    if not all(all(values.values()) for values in checks.values()):
        raise ActivationError("AWG lab service readback failed")
    return {
        "server_binary_sha256": binary_sha256,
        "tools_archive_sha256": tools_sha256,
        "checks": checks,
    }


def _ensure_brain_material_secrets(brain: Any) -> str:
    env_path = "/root/portal_bot/.env"
    backup_path = (
        env_path
        + ".awg-lab-backup-"
        + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    )
    sftp = brain.open_sftp()
    try:
        with sftp.open(env_path, "rb") as handle:
            original = handle.read()
        text = original.decode("utf-8")
        lines = text.splitlines()
        changed = False
        for name in ("AWG2_LAB_MATERIAL_SECRET", "AWG31_LAB_MATERIAL_SECRET"):
            secret = (
                base64.urlsafe_b64encode(os.urandom(48)).decode("ascii").rstrip("=")
            )
            matched = False
            for index, line in enumerate(lines):
                if line.startswith(name + "="):
                    matched = True
                    if not line.split("=", 1)[1].strip():
                        lines[index] = f"{name}={secret}"
                        changed = True
                    break
            if not matched:
                lines.append(f"{name}={secret}")
                changed = True
        if changed:
            _sftp_write(sftp, backup_path, original, 0o600)
            _sftp_write(
                sftp,
                env_path,
                ("\n".join(lines).rstrip("\n") + "\n").encode("utf-8"),
                0o600,
            )
        else:
            backup_path = ""
    finally:
        sftp.close()
    try:
        _run_remote(brain, "systemctl restart portal-api", timeout=120)
        _run_remote(
            brain,
            "for attempt in $(seq 1 30); do "
            "if curl -fsS --max-time 5 https://api.pokrov.space/api/health >/dev/null; "
            "then printf ready; exit 0; fi; sleep 2; done; exit 1",
            timeout=75,
        )
        presence = _run_remote(
            brain,
            "pid=$(systemctl show portal-api -p MainPID --value); "
            "for name in AWG2_LAB_MATERIAL_SECRET AWG31_LAB_MATERIAL_SECRET; do "
            "tr '\\0' '\\n' < /proc/$pid/environ | cut -d= -f1 | grep -qx \"$name\" || exit 1; done; printf ready",
        )
        if presence != "ready":
            raise ActivationError("portal-api did not load AWG material secrets")
    except Exception:
        if backup_path:
            _run_remote_allow_failure(
                brain, f"cp -f {shlex.quote(backup_path)} {shlex.quote(env_path)}"
            )
            _run_remote_allow_failure(brain, "systemctl restart portal-api")
        raise
    return backup_path


_REMOTE_ADMIN_HELPER = r"""
import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone

payload = json.loads(sys.stdin.read())
pid = subprocess.check_output(
    ["systemctl", "show", "portal-api", "-p", "MainPID", "--value"], text=True
).strip()
with open(f"/proc/{pid}/environ", "rb") as handle:
    env = {}
    for item in handle.read().split(b"\0"):
        if b"=" in item:
            key, value = item.split(b"=", 1)
            env[key.decode("utf-8", "replace")] = value.decode("utf-8", "replace")
bot_token = env.get("BOT_TOKEN", "").strip()
admin_id = env.get("ADMIN_ID", "").strip()
if not bot_token or not admin_id.isdigit():
    raise SystemExit("portal admin runtime identity unavailable")

params = {
    "auth_date": str(int(time.time())),
    "query_id": "POKROVAWG31LAB",
    "user": json.dumps(
        {"id": int(admin_id), "first_name": "POKROV", "username": "operator"},
        separators=(",", ":"),
    ),
}
check = "\n".join(f"{key}={value}" for key, value in sorted(params.items()))
secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
params["hash"] = hmac.new(secret_key, check.encode(), hashlib.sha256).hexdigest()
init_data = urllib.parse.urlencode(params)
base_url = "https://api.pokrov.space"

def request(method, path, body=None, headers=None):
    data = None if body is None else json.dumps(body, separators=(",", ":")).encode()
    merged = {
        "X-Telegram-Init-Data": init_data,
        "User-Agent": "pokrov-awg-lab-operator/1",
    }
    if data is not None:
        merged["Content-Type"] = "application/json"
    merged.update(headers or {})
    req = urllib.request.Request(base_url + path, data=data, headers=merged, method=method)
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            raw = response.read()
            return json.loads(raw.decode()) if raw else {}
    except urllib.error.HTTPError as exc:
        marker = "unknown"
        try:
            error_payload = json.loads(exc.read().decode("utf-8", "replace"))
            detail = error_payload.get("detail") if isinstance(error_payload, dict) else None
            if isinstance(detail, dict):
                marker = str(detail.get("code") or detail.get("error") or "object")
            elif isinstance(detail, list):
                parts = []
                for item in detail[:4]:
                    if not isinstance(item, dict):
                        continue
                    error_type = str(item.get("type") or "validation")
                    location = item.get("loc") if isinstance(item.get("loc"), list) else []
                    safe_location = ".".join(
                        "index" if isinstance(value, int) else str(value) for value in location
                    )
                    parts.append(f"{error_type}@{safe_location}")
                marker = ",".join(parts) or "validation"
        except Exception:
            marker = "unreadable"
        marker = re.sub(r"[^A-Za-z0-9_.@,-]", "_", marker)[:240]
        safe_path = re.sub(r"/users/[^/]+", "/users/{id}", path)
        raise RuntimeError(
            f"admin api {method} {safe_path} failed HTTP {exc.code} detail={marker}"
        ) from None

def guarded(action, target_type, target_id, method, path, body):
    prepared = request(
        "POST",
        "/api/admin/action-intents",
        {"action": action, "target": {"type": target_type, "id": str(target_id)}, "payload": body},
    )
    challenge = str(prepared.get("confirmation_challenge") or "")
    intent_id = str(prepared.get("intent_id") or "")
    if not challenge or not intent_id:
        raise RuntimeError(f"intent prepare failed for {action}")
    return request(
        method,
        path,
        body,
        {
            "X-Admin-Intent-Id": intent_id,
            "X-Admin-Idempotency-Key": str(uuid.uuid4()),
            "X-Admin-Confirmation-SHA256": hashlib.sha256(challenge.encode()).hexdigest(),
        },
    )

tg_id = int(payload["tg_id"])
install_id = str(payload["install_id"])
extend_entitlement = bool(payload["extend_entitlement"])
awg2 = payload["awg2_endpoint"]
awg31 = payload["awg31_endpoint"]
expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat().replace("+00:00", "Z")

if extend_entitlement:
    guarded(
        "user.extend", "user", tg_id, "POST", f"/api/admin/users/{tg_id}/manual/extend",
        {"days": 1, "delta_days": 1, "allow_deactivate": False},
    )
guarded(
    "awg2_lab_material.replace", "awg2_lab_material", tg_id, "PUT",
    "/api/admin/client/awg2-lab/material",
    {
        "tg_id": tg_id,
        "install_id": install_id,
        "generation": "awg2-lab-v1",
        "endpoint_revision": "awg2-v1",
        "server_record_id": "de-awg2-20260827-01",
        "node_code": "de",
        "endpoint": awg2,
    },
)
guarded(
    "awg31_lab_material.replace", "awg31_lab_material", tg_id, "PUT",
    "/api/admin/client/awg31-lab/material",
    {
        "tg_id": tg_id,
        "install_id": install_id,
        "generation": "awg31-lab-v3-randomized-trailers",
        "endpoint_revision": "awg31-v1",
        "server_record_id": "de-awg31-20260828-03-randomized-trailers",
        "node_code": "de",
        "endpoint": awg31,
    },
)
current = request("GET", "/api/admin/network-rollout-config")["network_rollout_config"]
cohorts = dict(current.get("cohort_overrides") or {})
cohorts["candidate4-awg-lab"] = {
    "transport_profile": "awg31_lab",
    "install_ids": [install_id],
    "tg_ids": [tg_id],
    "linked_tg_ids": [],
    "platforms": ["android"],
}
current["cohort_overrides"] = cohorts
current["awg2_lab"] = {
    "enabled": True,
    "kill_switch_engaged": False,
    "allowlist_install_ids": [install_id],
    "allowlist_tg_ids": [tg_id],
    "allowlist_node_codes": ["de"],
    "allowed_platforms": ["android", "windows"],
    "expires_at": expires_at,
    "contract_id": "pokrov.awg2.endpoint.v1",
    "contract_sha256": "c473c411025825bfef5a76c64990c5c921e9658b3581210d3a86d72e454fdea8",
    "generation": "awg2-lab-v1",
    "endpoint_revision": "awg2-v1",
    "server_record_id": "de-awg2-20260827-01",
    "server_owner": "pokrov",
    "server_state": "ready",
    "material_max_age_hours": 168,
}
current["awg31_lab"] = {
    "enabled": True,
    "kill_switch_engaged": False,
    "allowlist_install_ids": [install_id],
    "allowlist_tg_ids": [tg_id],
    "allowlist_node_codes": ["de"],
    "allowed_platforms": ["android", "windows"],
    "expires_at": expires_at,
    "contract_id": "pokrov.awg31.endpoint.v1",
    "contract_sha256": "1bb49b61549ba7c4a3c2d56df445e919ebb1ed12d42e04b0cb3c915d23240818",
    "generation": "awg31-lab-v3-randomized-trailers",
    "endpoint_revision": "awg31-v1",
    "server_record_id": "de-awg31-20260828-03-randomized-trailers",
    "server_owner": "pokrov",
    "server_state": "ready",
    "material_max_age_hours": 168,
}
guarded(
    "network_rollout_config.update", "config", "network-rollout", "PUT",
    "/api/admin/network-rollout-config", current,
)
print(json.dumps({
    "entitlement_extended": extend_entitlement,
    "entitlement_already_ready": not extend_entitlement,
    "awg2_material_provisioned": True,
    "awg31_material_provisioned": True,
    "selected_profile": "awg31_lab",
    "awg31_variant": "randomized_trailers_v1",
    "rollout_expires_at": expires_at,
}))
"""


def _activate_control_plane(
    brain: Any,
    *,
    tg_id: int,
    install_id: str,
    extend_entitlement: bool,
    awg2_endpoint: dict[str, Any],
    awg31_endpoint: dict[str, Any],
) -> dict[str, Any]:
    encoded_helper = base64.b64encode(_REMOTE_ADMIN_HELPER.encode("utf-8")).decode(
        "ascii"
    )
    command = "python3 -c " + shlex.quote(
        "import base64;exec(base64.b64decode(" + repr(encoded_helper) + "))"
    )
    stdin, stdout, stderr = brain.exec_command(command, timeout=420)
    request = {
        "tg_id": tg_id,
        "install_id": install_id,
        "extend_entitlement": extend_entitlement,
        "awg2_endpoint": awg2_endpoint,
        "awg31_endpoint": awg31_endpoint,
    }
    stdin.write(json.dumps(request, separators=(",", ":")))
    stdin.channel.shutdown_write()
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", "replace").strip()
    err = stderr.read().decode("utf-8", "replace").strip()
    if code != 0:
        raise ActivationError((err or "guarded control-plane activation failed")[:1200])
    result = json.loads(out)
    if result.get("selected_profile") != "awg31_lab":
        raise ActivationError("guarded rollout did not select AWG 3.1")
    return result


def _safe_live_readback(brain: Any) -> dict[str, Any]:
    raw = _psql(
        brain,
        """
select json_build_object(
  'awg2_active_materials',(select count(*) from awg2_lab_materials where is_active and state='ready'),
  'awg31_active_materials',(select count(*) from awg31_lab_materials where is_active and state='ready'),
  'awg2_enabled',coalesce((value_json::jsonb#>>'{awg2_lab,enabled}')::boolean,false),
  'awg2_kill_switch',coalesce((value_json::jsonb#>>'{awg2_lab,kill_switch_engaged}')::boolean,true),
  'awg31_enabled',coalesce((value_json::jsonb#>>'{awg31_lab,enabled}')::boolean,false),
  'awg31_kill_switch',coalesce((value_json::jsonb#>>'{awg31_lab,kill_switch_engaged}')::boolean,true),
  'selected_awg31',coalesce(value_json::jsonb#>>'{cohort_overrides,candidate4-awg-lab,transport_profile}','')='awg31_lab'
)::text from app_settings where key='network_rollout_config';
""".strip(),
    )
    if not raw:
        raise ActivationError("network rollout readback is missing")
    return json.loads(raw)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Guarded activation of isolated POKROV AWG2/AWG3.1 labs on the owned DE node."
    )
    parser.add_argument("--brain-ip", default="82.21.114.104")
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--known-hosts", required=True)
    parser.add_argument("--adb", required=True)
    parser.add_argument("--adb-serial", default="emulator-5554")
    parser.add_argument("--server-binary", required=True)
    parser.add_argument("--server-binary-sha256", required=True)
    parser.add_argument("--tools-archive", required=True)
    parser.add_argument("--tools-archive-sha256", required=True)
    parser.add_argument("--confirm-source-revision", default="")
    parser.add_argument("--confirm-node", default="")
    parser.add_argument("--confirm-install-sha256", default="")
    parser.add_argument("--json-out", default="")
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    server_binary = Path(args.server_binary).resolve()
    tools_archive = Path(args.tools_archive).resolve()
    adb = Path(args.adb).resolve()
    known_hosts = Path(args.known_hosts).resolve()
    for path, label in (
        (server_binary, "server binary"),
        (tools_archive, "tools archive"),
        (adb, "adb"),
        (known_hosts, "known_hosts"),
    ):
        if not path.is_file():
            raise SystemExit(f"{label} is missing: {path}")
    server_sha256 = _sha256_file(server_binary)
    tools_sha256 = _sha256_file(tools_archive)
    expected_server = str(args.server_binary_sha256).strip().lower()
    expected_tools = str(args.tools_archive_sha256).strip().lower()
    if (
        not SAFE_SHA256_RE.fullmatch(expected_server)
        or server_sha256 != expected_server
    ):
        raise SystemExit("server binary SHA-256 confirmation failed")
    if not SAFE_SHA256_RE.fullmatch(expected_tools) or tools_sha256 != expected_tools:
        raise SystemExit("tools archive SHA-256 confirmation failed")
    head = (
        subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        .stdout.strip()
        .lower()
    )
    if head != SOURCE_REVISION:
        raise SystemExit(
            "operator script must run from the exact candidate.4 platform base"
        )

    install_id, _account_id = _load_emulator_identity(adb, str(args.adb_serial))
    install_sha256 = hashlib.sha256(install_id.encode("utf-8")).hexdigest()
    passwords = Path(args.passwords).resolve()
    os.environ["POKROV_SSH_KNOWN_HOSTS"] = str(known_hosts)
    brain, brain_auth = connect_node(
        code="brain", host=str(args.brain_ip), passwords_path=passwords
    )
    node = None
    node_deployed = False
    try:
        tg_id = _resolve_target_user(brain, install_id)
        extend_entitlement = _entitlement_extension_needed(brain, install_id)
        host = _node_host(brain)
        node_address = socket.gethostbyname(host)
        node, node_auth = connect_node(
            code=NODE_CODE, host=host, passwords_path=passwords
        )
        preflight = _server_preflight(node)
        report: dict[str, Any] = {
            "schema_version": "pokrov-owned-awg-lab-activation-v1",
            "mode": "APPLY" if args.apply else "PLAN",
            "source_revision": SOURCE_REVISION,
            "node_code": NODE_CODE,
            "server_go_tag": SERVER_GO_TAG,
            "server_go_commit": SERVER_GO_COMMIT,
            "tools_tag": TOOLS_TAG,
            "tools_commit": TOOLS_COMMIT,
            "awg31_variant": AWG31_VARIANT,
            "server_binary_sha256": server_sha256,
            "tools_archive_sha256": tools_sha256,
            "known_hosts_sha256": _sha256_file(known_hosts),
            "adb_target_supplied": bool(str(args.adb_serial).strip()),
            "install_id_sha256": install_sha256,
            "brain_auth_method": "key"
            if str(brain_auth).startswith("key")
            else "password",
            "node_auth_method": "key"
            if str(node_auth).startswith("key")
            else "password",
            "preflight": preflight,
            "secrets_retained_in_report": False,
            "raw_identifiers_returned": False,
        }
        if preflight["occupied_paths"]:
            raise ActivationError("owned AWG lab target paths are already occupied")
        if any(value != "free" for value in preflight["udp_ports"].values()):
            raise ActivationError("owned AWG lab UDP port is already occupied")
        if not args.apply:
            _write_report(report, args.json_out)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0
        if str(args.confirm_source_revision).strip().lower() != SOURCE_REVISION:
            raise ActivationError("--confirm-source-revision mismatch")
        if str(args.confirm_node).strip().lower() != NODE_CODE:
            raise ActivationError("--confirm-node mismatch")
        if str(args.confirm_install_sha256).strip().lower() != install_sha256:
            raise ActivationError("--confirm-install-sha256 mismatch")

        awg2_endpoint, awg31_endpoint, awg2_server, awg31_server = _endpoint_material(
            node_address
        )
        try:
            report["dataplane"] = _deploy_node(
                node,
                server_binary=server_binary,
                tools_archive=tools_archive,
                tools_sha256=tools_sha256,
                awg2_server=awg2_server,
                awg31_server=awg31_server,
            )
            node_deployed = True
            backup_path = _ensure_brain_material_secrets(brain)
        except Exception:
            _rollback_node(node)
            raise
        report["brain_secret_backup_created"] = bool(backup_path)
        report["control_plane"] = _activate_control_plane(
            brain,
            tg_id=tg_id,
            install_id=install_id,
            extend_entitlement=extend_entitlement,
            awg2_endpoint=awg2_endpoint,
            awg31_endpoint=awg31_endpoint,
        )
        report["readback"] = _safe_live_readback(brain)
        report["ok"] = bool(
            report["readback"].get("awg2_active_materials")
            and report["readback"].get("awg31_active_materials")
            and report["readback"].get("awg2_enabled")
            and not report["readback"].get("awg2_kill_switch")
            and report["readback"].get("awg31_enabled")
            and not report["readback"].get("awg31_kill_switch")
            and report["readback"].get("selected_awg31")
        )
        if not report["ok"]:
            raise ActivationError("post-activation safe readback failed")
        _write_report(report, args.json_out)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        if node_deployed:
            # A successful dataplane remains isolated if a later guarded API step
            # fails because the rollout update is deliberately last.
            pass
        print(
            f"owned AWG lab activation failed: {type(exc).__name__}: {str(exc)[:600]}",
            file=sys.stderr,
        )
        return 1
    finally:
        if node is not None:
            node.close()
        brain.close()


def _write_report(report: dict[str, Any], raw_path: str) -> None:
    path = str(raw_path or "").strip()
    if not path:
        return
    output = Path(path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    raise SystemExit(main())
