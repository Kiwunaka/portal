#!/usr/bin/env python3
"""Guarded PLAN/APPLY/ROLLBACK for the owned POKROV Smart DNS lab."""

from __future__ import annotations

import argparse
import base64
import hashlib
import ipaddress
import json
import os
import re
import shlex
import socket
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

try:
    import build_owned_smart_dns_server_bundle as bundle_contract
    from node_access import DEFAULT_PASSWORDS, connect_node
except ImportError:  # pragma: no cover - package import for tests
    from . import build_owned_smart_dns_server_bundle as bundle_contract
    from .node_access import DEFAULT_PASSWORDS, connect_node


REPORT_SCHEMA = "pokrov-owned-smart-dns-remote-operation-v4"
SERVICE_NAME = "pokrov-smart-dns-lab.service"
SERVICE_PATH = "/etc/systemd/system/pokrov-smart-dns-lab.service"
RELEASE_ROOT = "/opt/pokrov/smart-dns/releases"
CURRENT_POINTER = "/opt/pokrov/smart-dns/current"
CONFIG_ROOT = "/etc/pokrov-smart-dns"
CONFIG_PATH = f"{CONFIG_ROOT}/config.json"
TLS_ROOT = f"{CONFIG_ROOT}/tls"
CERT_PATH = f"{TLS_ROOT}/fullchain.pem"
KEY_PATH = f"{TLS_ROOT}/privkey.pem"
BACKUP_ROOT = "/root/pokrov-smart-dns-lab-backups"
STAGE_ROOT = "/root/pokrov-smart-dns-lab-staging"
RUNTIME_STAGE_ROOT = "/root/pokrov-smart-dns-runtime-staging"
DEDICATED_LISTENER_MODE = "dedicated"
FRONTED_LISTENER_MODE = "fronted"
LISTENER_MODES = (DEDICATED_LISTENER_MODE, FRONTED_LISTENER_MODE)
DEDICATED_LISTEN_PORT = 443
FRONTED_LISTEN_HOST = "127.0.0.1"
FRONTED_LISTEN_PORT = 18443
# Retained for callers that still name the original dedicated listener constant.
LISTEN_PORT = DEDICATED_LISTEN_PORT
SAFE_COMPONENT_RE = re.compile(r"[a-z0-9][a-z0-9_-]{0,31}")
SAFE_RECEIPT_RE = re.compile(r"[0-9]{8}T[0-9]{6}Z-[0-9]+-[0-9a-f]{12}")


class SmartDNSRemoteOperationError(RuntimeError):
    """Raised when the guarded operation cannot prove its contract."""


def _q(value: str) -> str:
    return shlex.quote(str(value))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_component(value: str, *, label: str) -> str:
    normalized = str(value or "").strip().lower()
    if not SAFE_COMPONENT_RE.fullmatch(normalized):
        raise SmartDNSRemoteOperationError(f"{label}_invalid")
    return normalized


def _release_id(bundle_sha256: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{now}-{os.getpid()}-{bundle_sha256[:12]}"


def _listener_spec(listener_mode: str) -> dict[str, Any]:
    mode = str(listener_mode or "").strip().lower()
    if mode == DEDICATED_LISTENER_MODE:
        return {
            "mode": mode,
            "listen": f"0.0.0.0:{DEDICATED_LISTEN_PORT}",
            "port": DEDICATED_LISTEN_PORT,
            "accept_proxy_protocol_v2": False,
            "firewall_managed": True,
        }
    if mode == FRONTED_LISTENER_MODE:
        return {
            "mode": mode,
            "listen": f"{FRONTED_LISTEN_HOST}:{FRONTED_LISTEN_PORT}",
            "port": FRONTED_LISTEN_PORT,
            "accept_proxy_protocol_v2": True,
            "firewall_managed": False,
        }
    raise SmartDNSRemoteOperationError("listener_mode_invalid")


def _run(ssh: Any, command: str, *, label: str, timeout: int = 180) -> str:
    _stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="replace").strip()
    stderr.read()
    if code != 0:
        raise SmartDNSRemoteOperationError(f"{label}_failed:exit_{code}")
    return out


def _run_allow_failure(ssh: Any, command: str, *, timeout: int = 180) -> None:
    try:
        _run(ssh, command, label="best_effort", timeout=timeout)
    except Exception:
        return


def _psql(ssh: Any, sql: str, *, label: str) -> str:
    stdin, stdout, stderr = ssh.exec_command(
        "runuser -u postgres -- psql -d portal -At", timeout=60
    )
    stdin.write(sql + "\n")
    stdin.channel.shutdown_write()
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="replace").strip()
    stderr.read()
    if code != 0:
        raise SmartDNSRemoteOperationError(f"{label}_failed:exit_{code}")
    return out


def _resolve_node_host(brain: Any, node_code: str) -> str:
    node = _safe_component(node_code, label="node_code")
    raw = _psql(
        brain,
        "select host from nodes "
        f"where code='{node}' and enabled=true order by id limit 2;",
        label="node_resolution",
    )
    hosts = [line.strip() for line in raw.splitlines() if line.strip()]
    if len(hosts) != 1:
        raise SmartDNSRemoteOperationError("owned_node_resolution_not_unique")
    return hosts[0]


def _resolve_unique_public_ipv4(host: str) -> str:
    try:
        addresses = {
            ipaddress.ip_address(item[4][0]).compressed
            for item in socket.getaddrinfo(host, None, socket.AF_INET)
            if ipaddress.ip_address(item[4][0]).is_global
        }
    except (OSError, ValueError) as exc:
        raise SmartDNSRemoteOperationError("owned_node_public_ipv4_unavailable") from exc
    if len(addresses) != 1:
        raise SmartDNSRemoteOperationError("owned_node_public_ipv4_not_unique")
    return next(iter(addresses))


def _auth_family(value: str) -> str:
    return "key" if str(value or "").startswith("key") else "password"


def _connect_owned(*, code: str, host: str, passwords: Path) -> tuple[Any, str]:
    try:
        return connect_node(code=code, host=host, passwords_path=passwords)
    except Exception as exc:
        raise SmartDNSRemoteOperationError(f"{code}_ssh_connect_failed") from exc


def _validated_local_bundle(
    raw_path: str | Path,
    listener_mode: str = DEDICATED_LISTENER_MODE,
) -> tuple[Path, dict[str, Any], dict[str, bytes], str]:
    _listener_spec(listener_mode)
    try:
        path = Path(raw_path).resolve(strict=True)
    except OSError as exc:
        raise SmartDNSRemoteOperationError("bundle_missing") from exc
    manifest = bundle_contract.verify_bundle(path)
    with zipfile.ZipFile(path, "r") as archive:
        contents = {
            name: archive.read(name)
            for name in archive.namelist()
            if name != bundle_contract.MANIFEST_NAME
        }
    contract = json.loads(contents["contract/bundle-contract.json"])
    dedicated_template = json.loads(contents["config/config.template.json"])
    fronted_template = json.loads(contents["config/config.fronted.template.json"])
    install = contract.get("install") or {}
    runtime = contract.get("runtime") or {}
    listener_modes = runtime.get("listener_modes") or {}
    dedicated_contract = listener_modes.get(DEDICATED_LISTENER_MODE) or {}
    fronted_contract = listener_modes.get(FRONTED_LISTENER_MODE) or {}
    if (
        install.get("service_name") != SERVICE_NAME
        or install.get("service_path") != SERVICE_PATH
        or install.get("release_root") != RELEASE_ROOT
        or install.get("current_pointer") != CURRENT_POINTER
        or install.get("config_path") != CONFIG_PATH
        or install.get("enable_by_default") is not False
        or runtime.get("listen_protocol") != "tcp"
        or runtime.get("proxy_ipv4_requires_unique_owned_public_ipv4") is not True
        or runtime.get("doh_path") != "/dns-query"
        or runtime.get("recursive_dns") is not False
        or runtime.get("application_tls") != "opaque_passthrough"
        or set(listener_modes) != set(LISTENER_MODES)
        or dedicated_contract.get("listen_scope")
        != "wildcard_or_expected_owned_public_ipv4"
        or dedicated_contract.get("listen_port") != DEDICATED_LISTEN_PORT
        or dedicated_contract.get("proxy_protocol_v2") is not False
        or dedicated_contract.get("firewall") != "managed_ufw_allow_tcp_443"
        or dedicated_contract.get("deploy_supported_by_current_installer") is not True
        or fronted_contract.get("listen_scope") != "explicit_loopback_unprivileged_port"
        or fronted_contract.get("listen_host") != FRONTED_LISTEN_HOST
        or fronted_contract.get("listen_port") != FRONTED_LISTEN_PORT
        or fronted_contract.get("proxy_protocol_v2") is not True
        or fronted_contract.get("firewall") != "not_managed"
        or fronted_contract.get("public_frontend")
        != "reviewed_owned_haproxy_tcp_443_sni_mux"
        or fronted_contract.get("frontend_backend_transport") != "send-proxy-v2"
        or fronted_contract.get("deploy_supported_by_current_installer") is not True
        or dedicated_template.get("listen") != f"0.0.0.0:{DEDICATED_LISTEN_PORT}"
        or dedicated_template.get("accept_proxy_protocol_v2") is not False
        or fronted_template.get("listen")
        != f"{FRONTED_LISTEN_HOST}:{FRONTED_LISTEN_PORT}"
        or fronted_template.get("accept_proxy_protocol_v2") is not True
    ):
        raise SmartDNSRemoteOperationError("bundle_remote_install_contract_mismatch")
    return path, manifest, contents, _sha256_file(path)


def _parse_probe(raw: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in raw.splitlines():
        if "=" not in line:
            raise SmartDNSRemoteOperationError("remote_preflight_shape_invalid")
        key, value = line.split("=", 1)
        if not re.fullmatch(r"[a-z0-9_]+", key) or not re.fullmatch(
            r"[A-Za-z0-9_.:-]+", value
        ):
            raise SmartDNSRemoteOperationError("remote_preflight_value_invalid")
        parsed[key] = value
    return parsed


def _tcp_443_bind_scope(values: Mapping[str, str]) -> str:
    busy = values.get("tcp_busy") == "yes"
    wildcard = values.get("tcp_wildcard_busy") == "yes"
    expected = values.get("tcp_expected_ipv4_busy") == "yes"
    if not busy:
        if wildcard or expected:
            raise SmartDNSRemoteOperationError("remote_preflight_tcp_scope_invalid")
        return "free"
    if wildcard and expected:
        return "wildcard_and_expected_address"
    if wildcard:
        return "wildcard"
    if expected:
        return "expected_address"
    return "other_address_only"


def _address_reuse_followup(*, bind_scope: str, expected_ipv4_assigned: bool) -> str:
    if not expected_ipv4_assigned:
        return "BLOCKED_EXPECTED_IPV4_NOT_ASSIGNED"
    if bind_scope == "other_address_only":
        return "POTENTIAL_REQUIRES_SEPARATE_ADDRESS_SPECIFIC_GUARD"
    if bind_scope == "free":
        return "NOT_NEEDED_PORT_FREE"
    return "BLOCKED_CURRENT_BIND_SCOPE"


_ADDRESS_AVAILABILITY_HELPER = r"""
import ipaddress
import json
import subprocess
import sys

expected = ipaddress.ip_address(sys.argv[1]).compressed
if not ipaddress.ip_address(expected).is_global:
    raise SystemExit(2)

def run(*args):
    return subprocess.run(
        args,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout

rows = json.loads(run("ip", "-j", "-4", "addr", "show", "scope", "global"))
assigned = {
    ipaddress.ip_address(info["local"]).compressed
    for row in rows
    for info in row.get("addr_info", [])
    if info.get("family") == "inet"
    and info.get("scope") == "global"
    and ipaddress.ip_address(info["local"]).is_global
}

def local_endpoints(raw):
    for line in raw.splitlines():
        parts = line.split()
        if len(parts) >= 4:
            yield parts[3]

wildcard = False
for local in local_endpoints(run("ss", "-H", "-ltn", "sport = :443")):
    address, separator, port = local.rpartition(":")
    if separator == ":" and port == "443" and address in {
        "*", "0.0.0.0", "[::]", "::"
    }:
        wildcard = True

bound = set()
for local in local_endpoints(run("ss", "-H", "-ltn4", "sport = :443")):
    address, separator, port = local.rpartition(":")
    if separator != ":" or port != "443" or address in {"*", "0.0.0.0"}:
        continue
    try:
        candidate = ipaddress.ip_address(address).compressed
    except ValueError:
        continue
    if candidate in assigned:
        bound.add(candidate)

unclaimed = set() if wildcard else assigned - bound
bucket = "none" if not unclaimed else "one" if len(unclaimed) == 1 else "multiple"
print("tcp_wildcard_busy=" + ("yes" if wildcard else "no"))
print("tcp_expected_ipv4_busy=" + ("yes" if expected in bound else "no"))
print("expected_ipv4_assigned=" + ("yes" if expected in assigned else "no"))
print("global_ipv4_multiple=" + ("yes" if len(assigned) > 1 else "no"))
print("unclaimed_global_ipv4=" + bucket)
""".strip()


def _address_availability_command(expected_proxy_ipv4: str) -> str:
    try:
        expected = ipaddress.ip_address(expected_proxy_ipv4).compressed
    except ValueError as exc:
        raise SmartDNSRemoteOperationError("expected_proxy_ipv4_invalid") from exc
    if not ipaddress.ip_address(expected).is_global:
        raise SmartDNSRemoteOperationError("expected_proxy_ipv4_not_public")
    encoded = base64.b64encode(
        _ADDRESS_AVAILABILITY_HELPER.encode("utf-8")
    ).decode("ascii")
    return (
        "python3 -c "
        + _q(f"import base64;exec(base64.b64decode('{encoded}'))")
        + " "
        + _q(expected)
    )


def _runtime_contract_check(
    config_path: str,
    expected_proxy_ipv4: str,
    listener_mode: str = DEDICATED_LISTENER_MODE,
) -> str:
    listener = _listener_spec(listener_mode)
    allowed_listens = (
        [f"0.0.0.0:{DEDICATED_LISTEN_PORT}", f"{expected_proxy_ipv4}:{DEDICATED_LISTEN_PORT}"]
        if listener_mode == DEDICATED_LISTENER_MODE
        else [str(listener["listen"])]
    )
    validator = f"""
import ipaddress
import json
import re
import sys

def public(value):
    try:
        address = ipaddress.ip_address(value)
        return address.is_global
    except ValueError:
        return False

def domain(value):
    text = str(value or "")
    return bool(len(text) <= 253 and re.fullmatch(r"(?i)(?=.{{1,253}}$)(?:[a-z0-9](?:[a-z0-9-]{{0,61}}[a-z0-9])?\\.)+[a-z0-9](?:[a-z0-9-]{{0,61}}[a-z0-9])?", text))

try:
    with open(sys.argv[1], encoding="utf-8") as handle:
        config = json.load(handle)
    upstream = config.get("upstream_dot")
    limits = config.get("limits")
    upstream_ip, separator, upstream_port = str((upstream or {{}}).get("address") or "").rpartition(":")
    ok = (
        set(config) == {{"listen", "accept_proxy_protocol_v2", "doh_hostname", "proxy_ipv4", "policy_path", "tls_certificate_path", "tls_private_key_path", "upstream_dot", "limits"}}
        and config.get("listen") in {allowed_listens!r}
        and config.get("accept_proxy_protocol_v2") is {listener["accept_proxy_protocol_v2"]!r}
        and domain(config.get("doh_hostname"))
        and config.get("proxy_ipv4") == "{expected_proxy_ipv4}"
        and public(config.get("proxy_ipv4"))
        and config.get("policy_path") == "{CURRENT_POINTER}/share/smart-dns-policy.v1.json"
        and config.get("tls_certificate_path") == "{CERT_PATH}"
        and config.get("tls_private_key_path") == "{KEY_PATH}"
        and isinstance(upstream, dict)
        and set(upstream) == {{"address", "server_name"}}
        and separator == ":" and upstream_port == "853"
        and public(upstream_ip) and upstream_ip != "{expected_proxy_ipv4}"
        and domain(upstream.get("server_name"))
        and limits == {{
            "max_concurrent_connections": 2048,
            "max_connections_per_ip": 24,
            "max_doh_requests_per_minute": 120,
            "max_tracked_source_ips": 16384,
            "max_dns_message_bytes": 4096,
            "max_client_hello_bytes": 65535,
            "handshake_timeout_seconds": 5,
            "connect_timeout_seconds": 5,
            "idle_timeout_seconds": 90,
            "max_connection_seconds": 3600,
            "max_bytes_per_direction": 536870912,
        }}
        and "POKROV_" not in json.dumps(config, sort_keys=True)
    )
except Exception:
    ok = False
raise SystemExit(0 if ok else 1)
""".strip()
    encoded = base64.b64encode(validator.encode("utf-8")).decode("ascii")
    return (
        "python3 -c "
        + _q(f"import base64;exec(base64.b64decode('{encoded}'))")
        + " "
        + _q(config_path)
    )


def _preflight_command(
    *,
    release_dir: str,
    runtime_material_dir: str,
    expected_proxy_ipv4: str,
    listener_mode: str = DEDICATED_LISTENER_MODE,
) -> str:
    _listener_spec(listener_mode)
    targets = {
        "release": release_dir,
        "current": CURRENT_POINTER,
        "config_root": CONFIG_ROOT,
        "tls_root": TLS_ROOT,
        "config": CONFIG_PATH,
        "cert": CERT_PATH,
        "key": KEY_PATH,
        "unit": SERVICE_PATH,
    }
    lines = [
        "set -u",
        "emit_bool() { if eval \"$2\"; then printf '%s=yes\\n' \"$1\"; else printf '%s=no\\n' \"$1\"; fi; }",
        "emit_bool root 'test \"$(id -u)\" = 0'",
        "emit_bool systemd 'command -v systemctl >/dev/null 2>&1'",
        "emit_bool ss 'command -v ss >/dev/null 2>&1'",
        "emit_bool ip 'command -v ip >/dev/null 2>&1'",
        "emit_bool sha256sum 'command -v sha256sum >/dev/null 2>&1'",
        "emit_bool runuser 'command -v runuser >/dev/null 2>&1'",
        "emit_bool python3 'command -v python3 >/dev/null 2>&1'",
        "emit_bool curl 'command -v curl >/dev/null 2>&1'",
        "emit_bool ufw_installed 'command -v ufw >/dev/null 2>&1'",
        "emit_bool ufw_active \"ufw status 2>/dev/null | grep -q '^Status: active$'\"",
        f"emit_bool ufw_rule_present \"ufw status 2>/dev/null | grep -Eq '^[[:space:]]*{DEDICATED_LISTEN_PORT}/tcp[[:space:]]+ALLOW'\"",
        f"emit_bool tcp_busy \"ss -H -ltn 'sport = :{DEDICATED_LISTEN_PORT}' 2>/dev/null | grep -q .\"",
        f"emit_bool fronted_tcp_busy \"ss -H -ltn 'sport = :{FRONTED_LISTEN_PORT}' 2>/dev/null | grep -q .\"",
        _address_availability_command(expected_proxy_ipv4),
    ]
    for label, path in targets.items():
        lines.append(
            f"emit_bool {label}_present 'test -e {_q(path)} || test -L {_q(path)}'"
        )
    lines.extend(
        [
            f"service_active=$(systemctl is-active {_q(SERVICE_NAME)} 2>/dev/null || true)",
            "case \"$service_active\" in active|inactive|failed|activating|deactivating|unknown) ;; *) service_active=other ;; esac",
            "printf 'service_state=%s\\n' \"${service_active:-unknown}\"",
            f"service_enabled=$(systemctl is-enabled {_q(SERVICE_NAME)} 2>/dev/null || true)",
            "case \"$service_enabled\" in enabled|disabled|static|indirect|masked|not-found) ;; *) service_enabled=other ;; esac",
            "printf 'service_enabled=%s\\n' \"${service_enabled:-not-found}\"",
            f"emit_bool runtime_dir_present 'test -d {_q(runtime_material_dir)}'",
            f"emit_bool runtime_config_present 'test -f {_q(runtime_material_dir + '/config.json')}'",
            f"emit_bool runtime_cert_present 'test -f {_q(runtime_material_dir + '/fullchain.pem')}'",
            f"emit_bool runtime_key_present 'test -f {_q(runtime_material_dir + '/privkey.pem')}'",
            f"emit_bool runtime_dir_root_only \"test \"$(stat -c %u {_q(runtime_material_dir)} 2>/dev/null || printf x)\" = 0 && ! find {_q(runtime_material_dir)} -maxdepth 0 -perm /077 -print -quit 2>/dev/null | grep -q .\"",
            f"emit_bool runtime_files_root_owned \"test \"$(stat -c %u {_q(runtime_material_dir + '/config.json')} 2>/dev/null || printf x)\" = 0 && test \"$(stat -c %u {_q(runtime_material_dir + '/fullchain.pem')} 2>/dev/null || printf x)\" = 0 && test \"$(stat -c %u {_q(runtime_material_dir + '/privkey.pem')} 2>/dev/null || printf x)\" = 0\"",
            f"emit_bool runtime_secrets_private \"! find {_q(runtime_material_dir + '/config.json')} {_q(runtime_material_dir + '/privkey.pem')} -perm /077 -print -quit 2>/dev/null | grep -q .\"",
            f"emit_bool runtime_placeholders_absent \"! grep -Fq 'POKROV_' {_q(runtime_material_dir + '/config.json')} 2>/dev/null\"",
            f"emit_bool runtime_final_paths_bound \"grep -Fq {_q(CURRENT_POINTER + '/share/smart-dns-policy.v1.json')} {_q(runtime_material_dir + '/config.json')} 2>/dev/null && grep -Fq {_q(CERT_PATH)} {_q(runtime_material_dir + '/config.json')} 2>/dev/null && grep -Fq {_q(KEY_PATH)} {_q(runtime_material_dir + '/config.json')} 2>/dev/null\"",
            f"emit_bool runtime_contract_valid {_q(_runtime_contract_check(runtime_material_dir + '/config.json', expected_proxy_ipv4, listener_mode))}",
        ]
    )
    return "\n".join(lines)


def _remote_preflight(
    node: Any,
    *,
    release_dir: str,
    runtime_material_dir: str,
    expected_proxy_ipv4: str,
    listener_mode: str = DEDICATED_LISTENER_MODE,
) -> dict[str, Any]:
    listener = _listener_spec(listener_mode)
    values = _parse_probe(
        _run(
            node,
            _preflight_command(
                release_dir=release_dir,
                runtime_material_dir=runtime_material_dir,
                expected_proxy_ipv4=expected_proxy_ipv4,
                listener_mode=listener_mode,
            ),
            label="remote_preflight",
            timeout=90,
        )
    )
    required = {
        "root", "systemd", "ss", "ip", "sha256sum", "runuser", "python3", "curl",
        "ufw_installed", "ufw_active", "ufw_rule_present", "tcp_busy",
        "fronted_tcp_busy",
        "tcp_wildcard_busy", "tcp_expected_ipv4_busy",
        "expected_ipv4_assigned", "global_ipv4_multiple",
        "unclaimed_global_ipv4",
        "release_present", "current_present", "config_root_present",
        "tls_root_present", "config_present", "cert_present", "key_present",
        "unit_present", "service_state", "service_enabled",
        "runtime_dir_present", "runtime_config_present", "runtime_cert_present",
        "runtime_key_present", "runtime_dir_root_only", "runtime_files_root_owned",
        "runtime_secrets_private", "runtime_placeholders_absent",
        "runtime_final_paths_bound", "runtime_contract_valid",
    }
    if set(values) != required:
        raise SmartDNSRemoteOperationError("remote_preflight_fields_invalid")
    bool_keys = required - {
        "service_state", "service_enabled", "unclaimed_global_ipv4"
    }
    if any(values[key] not in {"yes", "no"} for key in bool_keys):
        raise SmartDNSRemoteOperationError("remote_preflight_boolean_invalid")
    if values["unclaimed_global_ipv4"] not in {"none", "one", "multiple"}:
        raise SmartDNSRemoteOperationError("remote_preflight_address_bucket_invalid")
    occupied = [
        label
        for label in (
            "release", "current", "config_root", "tls_root", "config", "cert",
            "key", "unit",
        )
        if values[f"{label}_present"] == "yes"
    ]
    runtime_ready = all(
        values[key] == "yes"
        for key in (
            "runtime_dir_present", "runtime_config_present", "runtime_cert_present",
            "runtime_key_present", "runtime_dir_root_only", "runtime_files_root_owned",
            "runtime_secrets_private", "runtime_placeholders_absent",
            "runtime_final_paths_bound", "runtime_contract_valid",
        )
    )
    bind_scope = _tcp_443_bind_scope(values)
    expected_ipv4_assigned = values["expected_ipv4_assigned"] == "yes"
    required_tool_keys = (
        "systemd",
        "ss",
        "ip",
        "sha256sum",
        "runuser",
        "python3",
        *(
            ("curl",)
            if listener_mode == DEDICATED_LISTENER_MODE
            else ()
        ),
    )
    dedicated_listener_state = "busy" if values["tcp_busy"] == "yes" else "free"
    fronted_listener_state = (
        "busy" if values["fronted_tcp_busy"] == "yes" else "free"
    )
    selected_listener_state = (
        dedicated_listener_state
        if listener_mode == DEDICATED_LISTENER_MODE
        else fronted_listener_state
    )
    return {
        "listener_mode": listener_mode,
        "listener_contract": (
            "dedicated_public_tcp_443"
            if listener_mode == DEDICATED_LISTENER_MODE
            else "fronted_loopback_proxy_v2_tcp_18443"
        ),
        "selected_listener": selected_listener_state,
        "selected_listener_port": listener["port"],
        "root": values["root"] == "yes",
        "required_tools": all(
            values[key] == "yes" for key in required_tool_keys
        ),
        "ufw_installed": values["ufw_installed"] == "yes",
        "ufw_active": values["ufw_active"] == "yes",
        "ufw_rule_present": values["ufw_rule_present"] == "yes",
        "tcp_443": dedicated_listener_state,
        "loopback_tcp_18443": fronted_listener_state,
        "tcp_443_bind_scope": bind_scope,
        "expected_ipv4_assigned": expected_ipv4_assigned,
        "multiple_global_ipv4_assigned": values["global_ipv4_multiple"] == "yes",
        "unclaimed_global_ipv4": values["unclaimed_global_ipv4"],
        "address_reuse_followup": (
            _address_reuse_followup(
                bind_scope=bind_scope,
                expected_ipv4_assigned=expected_ipv4_assigned,
            )
            if listener_mode == DEDICATED_LISTENER_MODE
            else "NOT_APPLICABLE_FRONTED_MODE"
        ),
        "occupied_targets": occupied,
        "service_state": values["service_state"],
        "service_enabled": values["service_enabled"],
        "runtime_material_ready": runtime_ready,
        "runtime_material_returned": False,
    }


def _assert_fresh_install_preflight(
    preflight: Mapping[str, Any],
    listener_mode: str = DEDICATED_LISTENER_MODE,
) -> None:
    _listener_spec(listener_mode)
    if not preflight.get("root") or not preflight.get("required_tools"):
        raise SmartDNSRemoteOperationError("install_host_requirements_not_met")
    if listener_mode == DEDICATED_LISTENER_MODE:
        if not preflight.get("ufw_installed") or not preflight.get("ufw_active"):
            raise SmartDNSRemoteOperationError("install_requires_active_ufw")
        if preflight.get("ufw_rule_present"):
            raise SmartDNSRemoteOperationError("install_tcp_firewall_rule_already_present")
        if preflight.get("tcp_443") != "free":
            raise SmartDNSRemoteOperationError("install_tcp_443_occupied")
    elif preflight.get("loopback_tcp_18443") != "free":
        raise SmartDNSRemoteOperationError("install_fronted_loopback_listener_occupied")
    if preflight.get("occupied_targets"):
        raise SmartDNSRemoteOperationError("install_target_already_present")
    if preflight.get("service_state") not in {"inactive", "unknown"}:
        raise SmartDNSRemoteOperationError("install_service_not_inactive")
    if not preflight.get("runtime_material_ready"):
        raise SmartDNSRemoteOperationError("install_runtime_material_not_ready")


def _remote_write(sftp: Any, path: str, value: bytes, mode: int) -> None:
    temporary = f"{path}.next-{os.getpid()}"
    try:
        with sftp.open(temporary, "wb") as handle:
            handle.write(value)
            handle.flush()
        sftp.chmod(temporary, mode)
        sftp.posix_rename(temporary, path)
    except Exception:
        try:
            sftp.remove(temporary)
        except Exception:
            pass
        raise


def _stage_bundle(
    node: Any,
    *,
    stage_dir: str,
    manifest: Mapping[str, Any],
    contents: Mapping[str, bytes],
) -> None:
    directories = sorted(
        {
            str(PurePosixPath(member).parent)
            for member in contents
            if str(PurePosixPath(member).parent) != "."
        }
    )
    _run(
        node,
        "set -e; install -d -m 0700 "
        + " ".join(_q(f"{stage_dir}/{directory}") for directory in (".", *directories)),
        label="stage_prepare",
    )
    sftp = node.open_sftp()
    try:
        for member, value in contents.items():
            mode = 0o755 if member == bundle_contract.BINARY_MEMBER else 0o600
            _remote_write(sftp, f"{stage_dir}/{member}", value, mode)
    finally:
        sftp.close()
    checks = ["set -e"]
    for member, record in manifest["members"].items():
        remote_path = f"{stage_dir}/{member}"
        checks.append(f"test \"$(stat -c %s {_q(remote_path)})\" = {_q(str(record['size']))}")
        checks.append(
            f"test \"$(sha256sum {_q(remote_path)} | awk '{{print $1}}')\" = {_q(str(record['sha256']))}"
        )
    _run(node, "\n".join(checks), label="stage_digest_readback", timeout=240)


def _backup_command(
    *,
    backup_dir: str,
    bundle_sha256: str,
    node_code: str,
    listener_mode: str = DEDICATED_LISTENER_MODE,
) -> str:
    listener = _listener_spec(listener_mode)
    targets = {
        "current": CURRENT_POINTER,
        "config": CONFIG_PATH,
        "cert": CERT_PATH,
        "key": KEY_PATH,
        "unit": SERVICE_PATH,
    }
    lines = [
        "set -e",
        f"install -d -m 0700 {_q(backup_dir)}",
        f"printf '%s\\n' {_q(bundle_sha256)} > {_q(backup_dir + '/bundle-sha256')}",
        f"printf '%s\\n' {_q(node_code)} > {_q(backup_dir + '/node-code')}",
        f"printf '%s\\n' {_q(listener_mode)} > {_q(backup_dir + '/listener-mode')}",
        f"systemctl is-active {_q(SERVICE_NAME)} > {_q(backup_dir + '/service-active')} 2>/dev/null || printf 'inactive\\n' > {_q(backup_dir + '/service-active')}",
        f"systemctl is-enabled {_q(SERVICE_NAME)} > {_q(backup_dir + '/service-enabled')} 2>/dev/null || printf 'disabled\\n' > {_q(backup_dir + '/service-enabled')}",
        f"if id -u pokrov-smart-dns >/dev/null 2>&1; then printf 'present\\n' > {_q(backup_dir + '/user-state')}; else printf 'missing\\n' > {_q(backup_dir + '/user-state')}; fi",
        f"if getent group pokrov-smart-dns >/dev/null 2>&1; then printf 'present\\n' > {_q(backup_dir + '/group-state')}; else printf 'missing\\n' > {_q(backup_dir + '/group-state')}; fi",
        (
            f"if ufw status 2>/dev/null | grep -Eq '^[[:space:]]*{DEDICATED_LISTEN_PORT}/tcp[[:space:]]+ALLOW'; then printf 'present\\n' > {_q(backup_dir + '/ufw-rule-state')}; else printf 'missing\\n' > {_q(backup_dir + '/ufw-rule-state')}; fi"
            if listener["firewall_managed"]
            else f"printf 'not_managed\\n' > {_q(backup_dir + '/ufw-rule-state')}"
        ),
    ]
    for name, target in targets.items():
        saved = f"{backup_dir}/{name}"
        lines.extend(
            [
                f"if test -e {_q(target)} || test -L {_q(target)}; then",
                f"  cp -a {_q(target)} {_q(saved)}",
                f"  printf 'present\\n' > {_q(backup_dir + '/' + name + '-state')}",
                "else",
                f"  printf 'missing\\n' > {_q(backup_dir + '/' + name + '-state')}",
                "fi",
            ]
        )
    lines.extend(
        [
            f"printf 'prepared\\n' > {_q(backup_dir + '/receipt-state')}",
            f"chmod -R go-rwx {_q(backup_dir)}",
        ]
    )
    return "\n".join(lines)


_FRONTED_DOH_PROBE_HELPER = r"""
import json
import socket
import ssl
import struct
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    hostname = json.load(handle)["doh_hostname"]

signature = b"\r\n\r\n\x00\r\nQUIT\n"
header = struct.pack(
    "!12sBBH4s4sHH",
    signature,
    0x21,
    0x11,
    12,
    socket.inet_aton("192.0.2.10"),
    socket.inet_aton("127.0.0.1"),
    54321,
    18443,
)
raw = socket.create_connection(("127.0.0.1", 18443), timeout=10)
try:
    raw.sendall(header)
    context = ssl.create_default_context()
    with context.wrap_socket(raw, server_hostname=hostname) as connection:
        connection.settimeout(10)
        request = (
            "GET /dns-query HTTP/1.1\r\n"
            f"Host: {hostname}\r\n"
            "Connection: close\r\n\r\n"
        ).encode("ascii")
        connection.sendall(request)
        response = connection.recv(128)
finally:
    raw.close()

if not response.startswith((b"HTTP/1.1 400 ", b"HTTP/2 400 ")):
    raise SystemExit(1)
""".strip()


def _fronted_doh_probe_command() -> str:
    encoded = base64.b64encode(_FRONTED_DOH_PROBE_HELPER.encode("utf-8")).decode(
        "ascii"
    )
    return (
        "python3 -c "
        + _q(f"import base64;exec(base64.b64decode('{encoded}'))")
        + " "
        + _q(CONFIG_PATH)
    )


def _listener_started_commands(listener_mode: str) -> list[str]:
    if listener_mode == DEDICATED_LISTENER_MODE:
        return [
            f"ss -H -ltn 'sport = :{DEDICATED_LISTEN_PORT}' | grep -q .",
            f"doh_host=$(python3 -c {_q('import json;print(json.load(open(\"' + CONFIG_PATH + '\",encoding=\"utf-8\"))[\"doh_hostname\"])')})",
            f"test \"$(curl --silent --show-error --output /dev/null --write-out '%{{http_code}}' --http1.1 --resolve \"$doh_host:{DEDICATED_LISTEN_PORT}:127.0.0.1\" \"https://$doh_host/dns-query\")\" = 400",
        ]
    _listener_spec(listener_mode)
    return [
        f"test \"$(ss -H -ltn 'sport = :{FRONTED_LISTEN_PORT}' | wc -l)\" = 1",
        f"ss -H -ltn4 'sport = :{FRONTED_LISTEN_PORT}' | awk '$4 == \"{FRONTED_LISTEN_HOST}:{FRONTED_LISTEN_PORT}\" {{ found = 1 }} END {{ exit(found ? 0 : 1) }}'",
        _fronted_doh_probe_command(),
    ]


def _install_command(
    *,
    stage_dir: str,
    release_dir: str,
    runtime_material_dir: str,
    backup_dir: str,
    manifest: Mapping[str, Any],
    listener_mode: str = DEDICATED_LISTENER_MODE,
) -> str:
    listener = _listener_spec(listener_mode)
    lines = [
        "set -e",
        "getent group pokrov-smart-dns >/dev/null 2>&1 || groupadd --system pokrov-smart-dns",
        "id -u pokrov-smart-dns >/dev/null 2>&1 || useradd --system --gid pokrov-smart-dns --home-dir /nonexistent --shell /usr/sbin/nologin pokrov-smart-dns",
        f"install -d -o root -g root -m 0755 {_q(release_dir)}",
    ]
    for member, record in sorted(manifest["members"].items()):
        mode = "0755" if member == bundle_contract.BINARY_MEMBER else "0644"
        source = f"{stage_dir}/{member}"
        target = f"{release_dir}/{member}"
        lines.append(f"install -D -o root -g root -m {mode} {_q(source)} {_q(target)}")
        lines.append(
            f"test \"$(sha256sum {_q(target)} | awk '{{print $1}}')\" = {_q(str(record['sha256']))}"
        )
    next_pointer = f"{CURRENT_POINTER}.next-{os.getpid()}"
    lines.extend(
        [
            f"ln -s {_q(release_dir)} {_q(next_pointer)}",
            f"mv -Tf {_q(next_pointer)} {_q(CURRENT_POINTER)}",
            f"install -d -o root -g pokrov-smart-dns -m 0750 {_q(CONFIG_ROOT)} {_q(TLS_ROOT)}",
            f"install -o root -g pokrov-smart-dns -m 0640 {_q(runtime_material_dir + '/config.json')} {_q(CONFIG_PATH)}",
            f"install -o root -g pokrov-smart-dns -m 0644 {_q(runtime_material_dir + '/fullchain.pem')} {_q(CERT_PATH)}",
            f"install -o root -g pokrov-smart-dns -m 0640 {_q(runtime_material_dir + '/privkey.pem')} {_q(KEY_PATH)}",
            f"install -o root -g root -m 0644 {_q(stage_dir + '/systemd/pokrov-smart-dns-lab.service')} {_q(SERVICE_PATH)}",
            "systemctl daemon-reload",
            f"runuser -u pokrov-smart-dns -- {_q(release_dir + '/' + bundle_contract.BINARY_MEMBER)} -config {_q(CONFIG_PATH)} -check >/dev/null",
            f"systemctl start {_q(SERVICE_NAME)}",
            f"test \"$(systemctl is-active {_q(SERVICE_NAME)})\" = active",
            *_listener_started_commands(listener_mode),
            *(
                [
                    f"ufw allow {DEDICATED_LISTEN_PORT}/tcp comment 'POKROV Smart DNS lab' >/dev/null"
                ]
                if listener["firewall_managed"]
                else []
            ),
            f"systemctl enable {_q(SERVICE_NAME)} >/dev/null",
            f"test \"$(systemctl is-enabled {_q(SERVICE_NAME)})\" = enabled",
            f"test \"$(readlink -f {_q(CURRENT_POINTER)})\" = {_q(release_dir)}",
            f"printf 'applied\\n' > {_q(backup_dir + '/receipt-state')}",
        ]
    )
    return "\n".join(lines)


def _restore_target_lines(*, backup_dir: str, name: str, target: str) -> list[str]:
    saved = f"{backup_dir}/{name}"
    state = f"{backup_dir}/{name}-state"
    return [
        f"rm -f {_q(target)}",
        f"if grep -qx present {_q(state)}; then cp -a {_q(saved)} {_q(target)}; fi",
    ]


def _rollback_command(
    *,
    backup_dir: str,
    bundle_sha256: str,
    node_code: str,
    release_dir: str,
    require_current_release: bool = False,
    listener_mode: str = DEDICATED_LISTENER_MODE,
) -> str:
    listener = _listener_spec(listener_mode)
    listen_port = int(listener["port"])
    lines = [
        "set -e",
        f"test -d {_q(backup_dir)}",
        f"test \"$(stat -c %u {_q(backup_dir)})\" = 0",
        f"grep -qx {_q(bundle_sha256)} {_q(backup_dir + '/bundle-sha256')}",
        f"grep -qx {_q(node_code)} {_q(backup_dir + '/node-code')}",
        f"grep -qx {_q(listener_mode)} {_q(backup_dir + '/listener-mode')}",
    ]
    if require_current_release:
        lines.extend(
            [
                f"grep -qx applied {_q(backup_dir + '/receipt-state')}",
                f"test \"$(readlink -f {_q(CURRENT_POINTER)})\" = {_q(release_dir)}",
            ]
        )
    else:
        lines.append(
            f"grep -Eq '^(prepared|applied)$' {_q(backup_dir + '/receipt-state')}"
        )
    lines.extend(
        [
            f"systemctl disable --now {_q(SERVICE_NAME)} >/dev/null 2>&1 || true",
            f"listener_after_stop=free; if ss -H -ltn 'sport = :{listen_port}' | grep -q .; then listener_after_stop=busy; fi",
            *(
                [
                    f"if grep -qx missing {_q(backup_dir + '/ufw-rule-state')}; then ufw --force delete allow {DEDICATED_LISTEN_PORT}/tcp >/dev/null 2>&1 || true; fi"
                ]
                if listener["firewall_managed"]
                else [f"grep -qx not_managed {_q(backup_dir + '/ufw-rule-state')}"]
            ),
        ]
    )
    for name, target in (
        ("current", CURRENT_POINTER), ("config", CONFIG_PATH), ("cert", CERT_PATH),
        ("key", KEY_PATH), ("unit", SERVICE_PATH),
    ):
        lines.extend(_restore_target_lines(backup_dir=backup_dir, name=name, target=target))
    lines.extend(
        [
            f"rmdir {_q(TLS_ROOT)} >/dev/null 2>&1 || true",
            f"rmdir {_q(CONFIG_ROOT)} >/dev/null 2>&1 || true",
            "systemctl daemon-reload",
            f"if grep -qx enabled {_q(backup_dir + '/service-enabled')}; then systemctl enable {_q(SERVICE_NAME)} >/dev/null; fi",
            f"if grep -qx active {_q(backup_dir + '/service-active')}; then systemctl start {_q(SERVICE_NAME)}; fi",
            f"if grep -qx missing {_q(backup_dir + '/user-state')}; then userdel pokrov-smart-dns >/dev/null 2>&1 || true; fi",
            f"if grep -qx missing {_q(backup_dir + '/group-state')}; then groupdel pokrov-smart-dns >/dev/null 2>&1 || true; fi",
            f"if ! grep -qx active {_q(backup_dir + '/service-active')}; then test \"$listener_after_stop\" = free; ! ss -H -ltn 'sport = :{listen_port}' | grep -q .; fi",
            f"printf 'rolled_back\\n' > {_q(backup_dir + '/receipt-state')}",
            f"test -d {_q(release_dir)} || true",
        ]
    )
    return "\n".join(lines)


def _plan(
    *,
    operation: str,
    node_code: str,
    listener_mode: str = DEDICATED_LISTENER_MODE,
) -> dict[str, Any]:
    _listener_spec(listener_mode)
    install_verification = (
        [
            "start_and_verify_local_tls_doh_before_firewall_open",
            "open_tcp_443_then_enable_service",
        ]
        if listener_mode == DEDICATED_LISTENER_MODE
        else [
            "start_and_verify_proxy_v2_tls_doh_before_frontend_migration",
            "retain_loopback_only_firewall_unchanged_then_enable_service",
        ]
    )
    actions = (
        [
            "verify_exact_bundle_and_runtime_contract",
            "retain_root_only_pre_mutation_receipt",
            "stage_and_digest_read_back_bundle",
            "install_immutable_release_and_root_owned_runtime_material",
            *install_verification,
        ]
        if operation == "install"
        else [
            "require_client_selection_disabled",
            "bind_exact_receipt_and_current_release",
            "stop_service_and_verify_selected_listener_absent",
            "restore_receipt_bound_targets_and_firewall",
            "retain_failed_immutable_release",
        ]
    )
    return {
        "operation": operation,
        "node_code": node_code,
        "listener_mode": listener_mode,
        "ordered_actions": actions,
        "mutation_performed": False,
        "secrets_returned": False,
    }


def _write_report(report: Mapping[str, Any], raw_path: str) -> None:
    value = str(raw_path or "").strip()
    if not value:
        return
    path = Path(value).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(report), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--brain-host", required=True)
    parser.add_argument("--node-code", required=True)
    parser.add_argument("--known-hosts", required=True)
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--operation", choices=("install", "rollback"), default="install")
    parser.add_argument(
        "--listener-mode", choices=LISTENER_MODES, default=DEDICATED_LISTENER_MODE
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--runtime-material-dir", default="")
    parser.add_argument("--receipt-id", default="")
    parser.add_argument("--confirm-bundle-sha256", default="")
    parser.add_argument("--confirm-source-revision", default="")
    parser.add_argument("--confirm-node-code", default="")
    parser.add_argument("--confirm-dedicated-node", default="")
    parser.add_argument("--confirm-fronted-listener", default="")
    parser.add_argument("--confirm-client-selection-disabled", default="")
    parser.add_argument("--confirm-runtime-material-ready", default="")
    parser.add_argument("--json-out", default="")
    return parser


def main() -> int:
    args = _parser().parse_args()
    failure_context: dict[str, Any] = {
        "receipt_id": "",
        "receipt_created": False,
        "mutation_attempted": False,
        "automatic_rollback_status": "NOT_ARMED",
    }
    try:
        node_code = _safe_component(args.node_code, label="node_code")
        listener_mode = str(args.listener_mode)
        _listener_spec(listener_mode)
        bundle_path, manifest, contents, bundle_sha256 = _validated_local_bundle(
            args.bundle, listener_mode
        )
        source_revision = str((manifest.get("created_from") or {}).get("revision") or "").lower()
        if not re.fullmatch(r"[0-9a-f]{40}", source_revision):
            raise SmartDNSRemoteOperationError("bundle_source_revision_invalid")
        release_dir = f"{RELEASE_ROOT}/{bundle_sha256}"
        runtime_material_dir = str(args.runtime_material_dir or "").strip()
        if not runtime_material_dir:
            runtime_material_dir = f"{RUNTIME_STAGE_ROOT}/{bundle_sha256}"
        if runtime_material_dir != f"{RUNTIME_STAGE_ROOT}/{bundle_sha256}":
            raise SmartDNSRemoteOperationError("runtime_material_dir_not_receipt_bound")
        try:
            known_hosts = Path(args.known_hosts).resolve(strict=True)
        except OSError as exc:
            raise SmartDNSRemoteOperationError("known_hosts_missing") from exc
        passwords = Path(args.passwords).resolve()
        if not known_hosts.is_file():
            raise SmartDNSRemoteOperationError("known_hosts_missing")

        os.environ["POKROV_SSH_KNOWN_HOSTS"] = str(known_hosts)
        os.environ["POKROV_SSH_TRUST_ON_FIRST_USE"] = "0"
        brain, brain_auth = _connect_owned(
            code="brain", host=str(args.brain_host), passwords=passwords
        )
        node = None
        try:
            host = _resolve_node_host(brain, node_code)
            expected_proxy_ipv4 = _resolve_unique_public_ipv4(host)
            node, node_auth = _connect_owned(code=node_code, host=host, passwords=passwords)
            preflight = _remote_preflight(
                node,
                release_dir=release_dir,
                runtime_material_dir=runtime_material_dir,
                expected_proxy_ipv4=expected_proxy_ipv4,
                listener_mode=listener_mode,
            )
            report: dict[str, Any] = {
                "schema_version": REPORT_SCHEMA,
                "mode": "APPLY" if args.apply else "PLAN",
                "operation": args.operation,
                "node_code": node_code,
                "listener_mode": listener_mode,
                "bundle_sha256": bundle_sha256,
                "bundle_size_bytes": bundle_path.stat().st_size,
                "source_revision": source_revision,
                "policy_sha256": manifest["policy_sha256"],
                "known_hosts_sha256": _sha256_file(known_hosts),
                "brain_auth_method": _auth_family(brain_auth),
                "node_auth_method": _auth_family(node_auth),
                "owned_public_ipv4_unique": True,
                "preflight": preflight,
                "mutation_performed": False,
                "raw_host_returned": False,
                "raw_runtime_material_returned": False,
                "live_dns": "NOT_RUN",
                "external_service_access": "NOT_RUN",
            }
            if not args.apply:
                report["plan"] = _plan(
                    operation=args.operation,
                    node_code=node_code,
                    listener_mode=listener_mode,
                )
                _write_report(report, args.json_out)
                print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
                return 0

            if str(args.confirm_bundle_sha256).strip().lower() != bundle_sha256:
                raise SmartDNSRemoteOperationError("confirm_bundle_sha256_mismatch")
            if str(args.confirm_source_revision).strip().lower() != source_revision:
                raise SmartDNSRemoteOperationError("confirm_source_revision_mismatch")
            if str(args.confirm_node_code).strip().lower() != node_code:
                raise SmartDNSRemoteOperationError("confirm_node_code_mismatch")
            if listener_mode == DEDICATED_LISTENER_MODE:
                if (
                    str(args.confirm_dedicated_node).strip()
                    != "DEDICATED_SMART_DNS_NODE"
                ):
                    raise SmartDNSRemoteOperationError(
                        "dedicated_node_confirmation_missing"
                    )
            elif (
                str(args.confirm_fronted_listener).strip()
                != "FRONTED_LOOPBACK_PROXY_V2"
            ):
                raise SmartDNSRemoteOperationError(
                    "fronted_listener_confirmation_missing"
                )
            if (
                str(args.confirm_client_selection_disabled).strip()
                != "SMART_DNS_CLIENT_SELECTION_DISABLED"
            ):
                raise SmartDNSRemoteOperationError("client_selection_disable_confirmation_missing")

            if args.operation == "install":
                if str(args.confirm_runtime_material_ready).strip() != "RUNTIME_MATERIAL_READY":
                    raise SmartDNSRemoteOperationError("runtime_material_confirmation_missing")
                _assert_fresh_install_preflight(preflight, listener_mode)
                receipt_id = _release_id(bundle_sha256)
                failure_context["receipt_id"] = receipt_id
                backup_dir = f"{BACKUP_ROOT}/{receipt_id}"
                stage_dir = f"{STAGE_ROOT}/{receipt_id}"
                backup_ready = False
                try:
                    failure_context["mutation_attempted"] = True
                    _stage_bundle(node, stage_dir=stage_dir, manifest=manifest, contents=contents)
                    _run(
                        node,
                        _backup_command(
                            backup_dir=backup_dir,
                            bundle_sha256=bundle_sha256,
                            node_code=node_code,
                            listener_mode=listener_mode,
                        ),
                        label="receipt_backup",
                    )
                    backup_ready = True
                    failure_context["receipt_created"] = True
                    failure_context["automatic_rollback_status"] = "ARMED"
                    _run(
                        node,
                        _install_command(
                            stage_dir=stage_dir,
                            release_dir=release_dir,
                            runtime_material_dir=runtime_material_dir,
                            backup_dir=backup_dir,
                            manifest=manifest,
                            listener_mode=listener_mode,
                        ),
                        label="install_apply",
                        timeout=300,
                    )
                except Exception:
                    if backup_ready:
                        try:
                            _run(
                                node,
                                _rollback_command(
                                    backup_dir=backup_dir,
                                    bundle_sha256=bundle_sha256,
                                    node_code=node_code,
                                    release_dir=release_dir,
                                    require_current_release=False,
                                    listener_mode=listener_mode,
                                ),
                                label="automatic_rollback",
                                timeout=240,
                            )
                            failure_context["automatic_rollback_status"] = "PASS"
                        except Exception:
                            failure_context["automatic_rollback_status"] = "FAIL"
                            raise
                    raise
                finally:
                    _run_allow_failure(node, f"rm -rf -- {_q(stage_dir)}", timeout=90)
                report.update(
                    {
                        "mutation_performed": True,
                        "receipt_id": receipt_id,
                        "service_active": True,
                        "service_enabled": True,
                        "selected_listener": True,
                        "selected_listener_contract": (
                            "dedicated_public_tcp_443"
                            if listener_mode == DEDICATED_LISTENER_MODE
                            else "fronted_loopback_proxy_v2_tcp_18443"
                        ),
                        "public_firewall_mutated": (
                            listener_mode == DEDICATED_LISTENER_MODE
                        ),
                        "local_tls_doh_probe": "PASS_HTTP_400_INVALID_DNS",
                        "automatic_rollback_armed": True,
                    }
                )
            else:
                receipt_id = str(args.receipt_id or "").strip()
                if not SAFE_RECEIPT_RE.fullmatch(receipt_id):
                    raise SmartDNSRemoteOperationError("receipt_id_invalid")
                failure_context["receipt_id"] = receipt_id
                failure_context["mutation_attempted"] = True
                backup_dir = f"{BACKUP_ROOT}/{receipt_id}"
                _run(
                    node,
                    _rollback_command(
                        backup_dir=backup_dir,
                        bundle_sha256=bundle_sha256,
                        node_code=node_code,
                        release_dir=release_dir,
                        require_current_release=True,
                        listener_mode=listener_mode,
                    ),
                    label="explicit_rollback",
                    timeout=240,
                )
                report.update(
                    {
                        "mutation_performed": True,
                        "receipt_id": receipt_id,
                        "rollback_completed": True,
                        "failed_release_retained": True,
                    }
                )
            _write_report(report, args.json_out)
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        finally:
            if node is not None:
                node.close()
            brain.close()
    except Exception as exc:
        code = (
            str(exc).split(":", 1)[0][:160]
            if isinstance(exc, SmartDNSRemoteOperationError)
            else type(exc).__name__
        )
        failure_report = {
            "schema_version": REPORT_SCHEMA,
            "mode": "ERROR",
            "operation": str(getattr(args, "operation", "unknown")),
            "listener_mode": str(getattr(args, "listener_mode", "unknown")),
            "error_code": code,
            "receipt_id": failure_context["receipt_id"] or None,
            "receipt_created": failure_context["receipt_created"],
            "mutation_attempted": failure_context["mutation_attempted"],
            "automatic_rollback_status": failure_context[
                "automatic_rollback_status"
            ],
            "raw_host_returned": False,
            "raw_runtime_material_returned": False,
        }
        try:
            _write_report(
                failure_report, str(getattr(args, "json_out", "") or "")
            )
        except Exception:
            pass
        receipt_suffix = (
            f" receipt_id={failure_context['receipt_id']}"
            if failure_context["receipt_id"]
            else ""
        )
        rollback_suffix = (
            " automatic_rollback_status="
            + str(failure_context["automatic_rollback_status"])
        )
        print(
            f"owned Smart DNS remote operation failed: {type(exc).__name__}: "
            f"{code}{receipt_suffix}{rollback_suffix}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
