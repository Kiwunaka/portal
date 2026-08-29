from __future__ import annotations

import argparse
import base64
import hashlib
import ipaddress
import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

try:
    from node_access import DEFAULT_PASSWORDS, connect_node
    from remote_apply_transport_front import _normalize_server_name
except ImportError:  # pragma: no cover - package import for tests
    from .node_access import DEFAULT_PASSWORDS, connect_node
    from .remote_apply_transport_front import _normalize_server_name


REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = REPO_ROOT / "shared" / "contracts" / "network" / "smart-dns-policy.v1.json"
DEFAULT_BASE_CONFIG = REPO_ROOT / "infra" / "portal-transport-front.cfg"
DEFAULT_BASE_SERVICE = REPO_ROOT / "infra" / "portal-transport-front.service.pre-smart-dns-v1"
CANDIDATE_SERVICE = REPO_ROOT / "infra" / "portal-transport-front.service"
REPORT_SCHEMA = "pokrov-owned-smart-dns-frontend-migration-v1"
FRONTEND_CONFIG_PATH = "/etc/portal-transport-front.cfg"
FRONTEND_SERVICE = "portal-transport-front.service"
FRONTEND_SERVICE_PATH = "/etc/systemd/system/portal-transport-front.service"
SMART_DNS_SERVICE = "pokrov-smart-dns-lab.service"
SMART_DNS_CURRENT = "/opt/pokrov/smart-dns/current"
SMART_DNS_CONFIG = "/etc/pokrov-smart-dns/config.json"
SMART_DNS_BACKEND_HOST = "127.0.0.1"
SMART_DNS_BACKEND_PORT = 18443
BACKUP_ROOT = "/root/pokrov-smart-dns-frontend-backups"
STAGE_ROOT = "/root/pokrov-smart-dns-frontend-staging"
SAFE_SHA256_RE = re.compile(r"[0-9a-f]{64}")
SAFE_COMPONENT_RE = re.compile(r"[a-z0-9][a-z0-9_-]{0,31}")
SAFE_RECEIPT_RE = re.compile(r"[0-9]{8}T[0-9]{6}Z-[0-9]+-[0-9a-f]{12}")


_RUNTIME_TRANSFORM_HELPER = r'''
import argparse
import hashlib
import ipaddress
import json
import os
import re
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=("plan", "stage"), required=True)
parser.add_argument("--config", required=True)
parser.add_argument("--output", default="")
parser.add_argument("--expected-base", default="")
parser.add_argument("--expected-candidate", default="")
args = parser.parse_args()

def digest(value):
    return hashlib.sha256(value).hexdigest()

def domain(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 253 or value != value.lower() or value.endswith("."):
        return False
    labels = value.split(".")
    return len(labels) >= 2 and all(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", item) for item in labels)

def validate_base(raw):
    if not 1 <= len(raw) <= 256 * 1024:
        raise ValueError("base_size")
    text = raw.decode("utf-8")
    if "\r" in text:
        raise ValueError("base_cr")
    lines = text.splitlines()
    if sum(line.strip() == "frontend fe_transport_front" for line in lines) != 1:
        raise ValueError("frontend_identity")
    if sum(line.strip() == "bind :443" for line in lines) != 1:
        raise ValueError("frontend_bind")
    if sum(line.strip().startswith("default_backend ") for line in lines) != 1:
        raise ValueError("default_count")
    if "    default_backend be_legacy_reality_fallback" not in lines:
        raise ValueError("default_identity")
    if sum(line.strip() == "backend be_legacy_reality_fallback" for line in lines) != 1:
        raise ValueError("legacy_backend")
    lowered = text.lower()
    if "be_smart_dns" in lowered or "smart_dns" in lowered or ":18443" in text:
        raise ValueError("already_fronted")
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("server "):
            continue
        parts = stripped.split()
        if len(parts) < 3:
            raise ValueError("server_shape")
        host, separator, port = parts[2].rpartition(":")
        if not separator or not port.isdigit() or not ipaddress.ip_address(host.strip("[]")).is_loopback:
            raise ValueError("server_endpoint")
    return text

try:
    payload = json.load(sys.stdin)
    if set(payload) != {"doh_hostname", "suffixes"}:
        raise ValueError("payload_shape")
    doh = payload["doh_hostname"]
    suffixes = payload["suffixes"]
    if not domain(doh) or not isinstance(suffixes, list) or not suffixes or len(suffixes) > 128:
        raise ValueError("payload_values")
    if any(not domain(item) for item in suffixes) or suffixes != sorted(set(suffixes)):
        raise ValueError("payload_suffixes")
    with open(args.config, "rb") as handle:
        base = handle.read(256 * 1024 + 1)
    text = validate_base(base)
    if re.search(rf"req\.ssl_sni\s+-i\s+{re.escape(doh)}(?:\s|\}})", text, flags=re.IGNORECASE):
        raise ValueError("doh_conflict")
    if doh in suffixes or any(doh.endswith("." + suffix) for suffix in suffixes):
        raise ValueError("doh_overlap")
    routes = [f"    use_backend be_smart_dns if {{ req.ssl_sni -i {doh} }}"]
    for suffix in suffixes:
        routes.append(f"    use_backend be_smart_dns if {{ req.ssl_sni -i {suffix} }}")
        routes.append(f"    use_backend be_smart_dns if {{ req.ssl_sni -m end -i .{suffix} }}")
    marker = "    default_backend be_legacy_reality_fallback"
    candidate_text = text.replace(marker, "\n".join([*routes, marker]), 1).rstrip("\n")
    candidate_text += "\n\nbackend be_smart_dns\n    mode tcp\n    option tcp-check\n    server smart_dns 127.0.0.1:18443 check send-proxy-v2\n"
    candidate = candidate_text.encode("utf-8")
    base_sha = digest(base)
    candidate_sha = digest(candidate)
    validation = subprocess.run(
        ["haproxy", "-c", "-f", "/dev/stdin"],
        input=candidate,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0
    result = {
        "ok": True,
        "base_config_valid": True,
        "base_config_sha256": base_sha,
        "candidate_config_sha256": candidate_sha,
        "candidate_config_valid": validation,
    }
    if args.mode == "stage":
        if not validation or base_sha != args.expected_base or candidate_sha != args.expected_candidate:
            raise ValueError("stage_digest_or_validation")
        if not re.fullmatch(r"/root/pokrov-smart-dns-frontend-staging/[0-9]{8}T[0-9]{6}Z-[0-9]+-[0-9a-f]{12}/candidate\.cfg", args.output):
            raise ValueError("stage_path")
        descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(candidate)
                handle.flush()
                os.fsync(handle.fileno())
        except Exception:
            try:
                os.unlink(args.output)
            except OSError:
                pass
            raise
        result["staged"] = True
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
except Exception as exc:
    print(json.dumps({"ok": False, "error": type(exc).__name__}, sort_keys=True, separators=(",", ":")))
'''.strip()


class SmartDNSFrontendMigrationError(RuntimeError):
    """Raised when the frontend migration cannot prove its guard contract."""


def _q(value: str) -> str:
    return shlex.quote(str(value))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_text(path: Path) -> bytes:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise SmartDNSFrontendMigrationError("text_utf8_bom_forbidden")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SmartDNSFrontendMigrationError("text_utf8_invalid") from exc
    normalized = text.replace("\r\n", "\n")
    if "\r" in normalized:
        raise SmartDNSFrontendMigrationError("text_lone_carriage_return_forbidden")
    if not normalized.endswith("\n"):
        normalized += "\n"
    return normalized.encode("utf-8")


def _safe_component(value: str, *, label: str) -> str:
    normalized = str(value or "").strip().lower()
    if not SAFE_COMPONENT_RE.fullmatch(normalized):
        raise SmartDNSFrontendMigrationError(f"{label}_invalid")
    return normalized


def _release_id(candidate_sha256: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{now}-{os.getpid()}-{candidate_sha256[:12]}"


def _load_policy_suffixes(path: Path = POLICY_PATH) -> tuple[list[str], str]:
    raw = _canonical_text(path)
    try:
        policy = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SmartDNSFrontendMigrationError("policy_json_invalid") from exc
    if (
        not isinstance(policy, dict)
        or policy.get("schema_version") != "pokrov-smart-dns-policy-v1"
        or policy.get("state") != "owner_lab_default_off"
        or policy.get("matching") != "exact_or_child_domain"
        or policy.get("application_tls") != "opaque_passthrough"
        or policy.get("recursive_dns") is not False
    ):
        raise SmartDNSFrontendMigrationError("policy_contract_invalid")
    groups = policy.get("groups")
    if not isinstance(groups, dict) or set(groups) != {"ai", "gaming_services"}:
        raise SmartDNSFrontendMigrationError("policy_groups_invalid")
    suffixes: list[str] = []
    seen: set[str] = set()
    for group in ("ai", "gaming_services"):
        values = groups.get(group)
        if not isinstance(values, list) or not values or len(values) > 64:
            raise SmartDNSFrontendMigrationError("policy_group_values_invalid")
        for value in values:
            try:
                normalized = _normalize_server_name(value)
            except ValueError as exc:
                raise SmartDNSFrontendMigrationError("policy_suffix_invalid") from exc
            if normalized != value or normalized in seen:
                raise SmartDNSFrontendMigrationError("policy_suffix_not_unique_canonical")
            seen.add(normalized)
            suffixes.append(normalized)
    return sorted(suffixes), _sha256_bytes(raw)


def _normalize_doh_hostname(value: str) -> str:
    try:
        return _normalize_server_name(value)
    except ValueError as exc:
        raise SmartDNSFrontendMigrationError("doh_hostname_invalid") from exc


def _validate_base_config(value: bytes) -> str:
    if len(value) == 0 or len(value) > 256 * 1024:
        raise SmartDNSFrontendMigrationError("base_config_size_invalid")
    try:
        text = value.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SmartDNSFrontendMigrationError("base_config_utf8_invalid") from exc
    if "\r" in text:
        raise SmartDNSFrontendMigrationError("base_config_not_lf_canonical")
    lines = text.splitlines()
    if sum(line.strip() == "frontend fe_transport_front" for line in lines) != 1:
        raise SmartDNSFrontendMigrationError("base_frontend_identity_invalid")
    if sum(line.strip() == "bind :443" for line in lines) != 1:
        raise SmartDNSFrontendMigrationError("base_frontend_bind_invalid")
    if sum(line.strip().startswith("default_backend ") for line in lines) != 1:
        raise SmartDNSFrontendMigrationError("base_default_backend_count_invalid")
    if "    default_backend be_legacy_reality_fallback" not in lines:
        raise SmartDNSFrontendMigrationError("base_default_backend_invalid")
    if sum(line.strip() == "backend be_legacy_reality_fallback" for line in lines) != 1:
        raise SmartDNSFrontendMigrationError("base_legacy_backend_invalid")
    lowered = text.lower()
    if "be_smart_dns" in lowered or "smart_dns" in lowered or f":{SMART_DNS_BACKEND_PORT}" in text:
        raise SmartDNSFrontendMigrationError("base_smart_dns_route_already_present")
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("server "):
            continue
        parts = stripped.split()
        if len(parts) < 3:
            raise SmartDNSFrontendMigrationError("base_backend_server_invalid")
        endpoint = parts[2]
        host, separator, raw_port = endpoint.rpartition(":")
        if not separator or not raw_port.isdigit():
            raise SmartDNSFrontendMigrationError("base_backend_endpoint_invalid")
        try:
            address = ipaddress.ip_address(host.strip("[]"))
        except ValueError as exc:
            raise SmartDNSFrontendMigrationError("base_backend_host_invalid") from exc
        if not address.is_loopback:
            raise SmartDNSFrontendMigrationError("base_backend_not_loopback")
    return text


def _validate_candidate_service(value: bytes) -> None:
    try:
        text = value.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SmartDNSFrontendMigrationError("candidate_service_utf8_invalid") from exc
    required = (
        "ExecStart=/usr/sbin/haproxy -W -db -f /etc/portal-transport-front.cfg -p /run/portal-transport-front.pid",
        "ExecReload=/usr/sbin/haproxy -c -f /etc/portal-transport-front.cfg",
        "ExecReload=/bin/kill -USR2 $MAINPID",
        "KillMode=mixed",
        "NoNewPrivileges=true",
    )
    if "\r" in text or any(text.count(line) != 1 for line in required):
        raise SmartDNSFrontendMigrationError("candidate_service_reload_contract_invalid")


def build_candidate_config(
    *,
    base_config: bytes,
    doh_hostname: str,
    policy_path: Path = POLICY_PATH,
) -> tuple[bytes, dict[str, Any]]:
    base_text = _validate_base_config(base_config)
    doh = _normalize_doh_hostname(doh_hostname)
    suffixes, policy_sha256 = _load_policy_suffixes(policy_path)
    if re.search(
        rf"req\.ssl_sni\s+-i\s+{re.escape(doh)}(?:\s|\}})",
        base_text,
        flags=re.IGNORECASE,
    ):
        raise SmartDNSFrontendMigrationError("doh_hostname_conflicts_with_base_route")
    if doh in suffixes or any(doh.endswith("." + suffix) for suffix in suffixes):
        raise SmartDNSFrontendMigrationError("doh_hostname_overlaps_application_policy")

    route_lines = [f"    use_backend be_smart_dns if {{ req.ssl_sni -i {doh} }}"]
    for suffix in suffixes:
        route_lines.extend(
            [
                f"    use_backend be_smart_dns if {{ req.ssl_sni -i {suffix} }}",
                f"    use_backend be_smart_dns if {{ req.ssl_sni -m end -i .{suffix} }}",
            ]
        )
    marker = "    default_backend be_legacy_reality_fallback"
    candidate = base_text.replace(marker, "\n".join([*route_lines, marker]), 1).rstrip("\n")
    candidate += (
        "\n\nbackend be_smart_dns\n"
        "    mode tcp\n"
        "    option tcp-check\n"
        f"    server smart_dns {SMART_DNS_BACKEND_HOST}:{SMART_DNS_BACKEND_PORT} check send-proxy-v2\n"
    )
    encoded = candidate.encode("utf-8")
    metadata = {
        "policy_sha256": policy_sha256,
        "application_suffix_count": len(suffixes),
        "exact_sni_route_count": len(suffixes) + 1,
        "child_sni_route_count": len(suffixes),
        "backend_port": SMART_DNS_BACKEND_PORT,
        "proxy_protocol": "v2",
    }
    return encoded, metadata


def _run(ssh: Any, command: str, *, label: str, timeout: int = 180) -> str:
    _stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    output = stdout.read().decode("utf-8", errors="replace").strip()
    stderr.read()
    if code != 0:
        raise SmartDNSFrontendMigrationError(f"{label}_failed_exit_{code}")
    return output


def _run_allow_failure(ssh: Any, command: str, *, timeout: int = 180) -> None:
    try:
        _run(ssh, command, label="best_effort", timeout=timeout)
    except Exception:
        return


def _runtime_transform(
    ssh: Any,
    *,
    payload: Mapping[str, Any],
    mode: str,
    output_path: str = "",
    expected_base_sha256: str = "",
    expected_candidate_sha256: str = "",
) -> dict[str, Any]:
    encoded = base64.b64encode(_RUNTIME_TRANSFORM_HELPER.encode("utf-8")).decode("ascii")
    command = (
        f"python3 -c \"$(printf %s {_q(encoded)} | base64 -d)\""
        f" --mode {_q(mode)} --config {_q(FRONTEND_CONFIG_PATH)}"
    )
    if mode == "stage":
        command += (
            f" --output {_q(output_path)}"
            f" --expected-base {_q(expected_base_sha256)}"
            f" --expected-candidate {_q(expected_candidate_sha256)}"
        )
    stdin, stdout, stderr = ssh.exec_command(command, timeout=90)
    stdin.write(json.dumps(dict(payload), ensure_ascii=True, separators=(",", ":")))
    stdin.channel.shutdown_write()
    code = stdout.channel.recv_exit_status()
    raw = stdout.read().decode("utf-8", errors="replace").strip()
    stderr.read()
    if code != 0:
        raise SmartDNSFrontendMigrationError("runtime_transform_failed")
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SmartDNSFrontendMigrationError("runtime_transform_output_invalid") from exc
    if not isinstance(result, dict) or result.get("ok") is not True:
        raise SmartDNSFrontendMigrationError("runtime_transform_rejected")
    required = {
        "ok",
        "base_config_valid",
        "base_config_sha256",
        "candidate_config_sha256",
        "candidate_config_valid",
    }
    if mode == "stage":
        required.add("staged")
    if set(result) != required:
        raise SmartDNSFrontendMigrationError("runtime_transform_fields_invalid")
    if (
        result["base_config_valid"] is not True
        or not SAFE_SHA256_RE.fullmatch(str(result["base_config_sha256"]))
        or not SAFE_SHA256_RE.fullmatch(str(result["candidate_config_sha256"]))
        or not isinstance(result["candidate_config_valid"], bool)
        or (mode == "stage" and result.get("staged") is not True)
    ):
        raise SmartDNSFrontendMigrationError("runtime_transform_contract_invalid")
    return result


def _psql(ssh: Any, sql: str, *, label: str) -> str:
    stdin, stdout, stderr = ssh.exec_command(
        "runuser -u postgres -- psql -d portal -At", timeout=60
    )
    stdin.write(sql + "\n")
    stdin.channel.shutdown_write()
    code = stdout.channel.recv_exit_status()
    output = stdout.read().decode("utf-8", errors="replace").strip()
    stderr.read()
    if code != 0:
        raise SmartDNSFrontendMigrationError(f"{label}_failed_exit_{code}")
    return output


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
        raise SmartDNSFrontendMigrationError("owned_node_resolution_not_unique")
    return hosts[0]


def _connect_owned(*, code: str, host: str, passwords: Path) -> tuple[Any, str]:
    try:
        return connect_node(code=code, host=host, passwords_path=passwords)
    except Exception as exc:
        raise SmartDNSFrontendMigrationError(f"{code}_ssh_connect_failed") from exc


def _auth_family(value: str) -> str:
    return "key" if str(value or "").startswith("key") else "password"


def _parse_probe(raw: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in raw.splitlines():
        if "=" not in line:
            raise SmartDNSFrontendMigrationError("remote_preflight_shape_invalid")
        key, value = line.split("=", 1)
        if (
            not re.fullmatch(r"[a-z0-9_]+", key)
            or not re.fullmatch(r"[A-Za-z0-9_.:-]+", value)
            or key in parsed
        ):
            raise SmartDNSFrontendMigrationError("remote_preflight_value_invalid")
        parsed[key] = value
    return parsed


def _preflight_command() -> str:
    fronted_validator = (
        "import json,sys;"
        "c=json.load(open(sys.argv[1],encoding='utf-8'));"
        "assert c.get('listen')=='127.0.0.1:18443';"
        "assert c.get('accept_proxy_protocol_v2') is True"
    )
    return "\n".join(
        [
            "set -eu",
            "emit_bool() { if sh -c \"$2\" >/dev/null 2>&1; then printf '%s=yes\\n' \"$1\"; else printf '%s=no\\n' \"$1\"; fi; }",
            "emit_state() { value=$(systemctl is-$1 \"$2\" 2>/dev/null || true); case \"$value\" in active|inactive|failed|unknown|enabled|disabled|static|indirect|masked|not-found) ;; *) value=other ;; esac; printf '%s=%s\\n' \"$3\" \"${value:-not-found}\"; }",
            "emit_bool haproxy_present 'command -v haproxy'",
            "emit_bool systemd_present 'command -v systemctl'",
            "emit_bool effective_uid_root 'test \"$(id -u)\" = 0'",
            "emit_bool python3_present 'command -v python3'",
            "emit_bool base64_present 'command -v base64'",
            "emit_bool curl_present 'command -v curl'",
            f"emit_bool config_present 'test -f {_q(FRONTEND_CONFIG_PATH)}'",
            f"if test -f {_q(FRONTEND_CONFIG_PATH)}; then printf 'config_sha256=%s\\n' \"$(sha256sum {_q(FRONTEND_CONFIG_PATH)} | cut -d' ' -f1)\"; else printf 'config_sha256=missing\\n'; fi",
            f"emit_bool service_unit_present 'test -f {_q(FRONTEND_SERVICE_PATH)}'",
            f"if test -f {_q(FRONTEND_SERVICE_PATH)}; then printf 'service_unit_sha256=%s\\n' \"$(sha256sum {_q(FRONTEND_SERVICE_PATH)} | cut -d' ' -f1)\"; else printf 'service_unit_sha256=missing\\n'; fi",
            f"emit_bool service_reload_signal_present \"grep -Fqx 'ExecReload=/bin/kill -USR2 \\$MAINPID' {_q(FRONTEND_SERVICE_PATH)}\"",
            f"emit_bool frontend_config_valid 'haproxy -c -f {_q(FRONTEND_CONFIG_PATH)}'",
            f"emit_state active {_q(FRONTEND_SERVICE)} frontend_state",
            f"emit_state enabled {_q(FRONTEND_SERVICE)} frontend_enabled",
            "emit_bool public_443_listening \"ss -H -ltn 'sport = :443' | grep -q .\"",
            f"emit_state active {_q(SMART_DNS_SERVICE)} smart_dns_state",
            f"emit_state enabled {_q(SMART_DNS_SERVICE)} smart_dns_enabled",
            f"emit_bool smart_dns_fronted_config_valid {_q('python3 -c ' + _q(fronted_validator) + ' ' + _q(SMART_DNS_CONFIG))}",
            f"emit_bool smart_dns_loopback_listener \"ss -H -ltn 'sport = :{SMART_DNS_BACKEND_PORT}' | grep -Eq '127\\.0\\.0\\.1:{SMART_DNS_BACKEND_PORT}|\\[::1\\]:{SMART_DNS_BACKEND_PORT}'\"",
            f"emit_bool smart_dns_nonloopback_listener \"ss -H -ltn 'sport = :{SMART_DNS_BACKEND_PORT}' | grep -Ev '127\\.0\\.0\\.1:{SMART_DNS_BACKEND_PORT}|\\[::1\\]:{SMART_DNS_BACKEND_PORT}' | grep -q .\"",
            f"release=$(readlink -f {_q(SMART_DNS_CURRENT)} 2>/dev/null | xargs -r basename || true); case \"$release\" in ''|*[!0-9a-f]* ) release=missing ;; esac; if test \"${{#release}}\" -ne 64; then release=missing; fi; printf 'smart_dns_release_sha256=%s\\n' \"$release\"",
            f"emit_bool smart_dns_route_present \"grep -Eq 'be_smart_dns|:{SMART_DNS_BACKEND_PORT}([[:space:]]|$)' {_q(FRONTEND_CONFIG_PATH)}\"",
        ]
    )


def _remote_preflight(ssh: Any) -> dict[str, Any]:
    values = _parse_probe(
        _run(ssh, _preflight_command(), label="remote_preflight", timeout=90)
    )
    required = {
        "haproxy_present",
        "systemd_present",
        "effective_uid_root",
        "python3_present",
        "base64_present",
        "curl_present",
        "config_present",
        "config_sha256",
        "service_unit_present",
        "service_unit_sha256",
        "service_reload_signal_present",
        "frontend_config_valid",
        "frontend_state",
        "frontend_enabled",
        "public_443_listening",
        "smart_dns_state",
        "smart_dns_enabled",
        "smart_dns_fronted_config_valid",
        "smart_dns_loopback_listener",
        "smart_dns_nonloopback_listener",
        "smart_dns_release_sha256",
        "smart_dns_route_present",
    }
    if set(values) != required:
        raise SmartDNSFrontendMigrationError("remote_preflight_fields_invalid")
    for key in (
        "haproxy_present",
        "systemd_present",
        "effective_uid_root",
        "python3_present",
        "base64_present",
        "curl_present",
        "config_present",
        "service_unit_present",
        "service_reload_signal_present",
        "frontend_config_valid",
        "public_443_listening",
        "smart_dns_loopback_listener",
        "smart_dns_nonloopback_listener",
        "smart_dns_route_present",
        "smart_dns_fronted_config_valid",
    ):
        if values[key] not in {"yes", "no"}:
            raise SmartDNSFrontendMigrationError("remote_preflight_boolean_invalid")
    config_sha = values["config_sha256"]
    service_sha = values["service_unit_sha256"]
    release_sha = values["smart_dns_release_sha256"]
    if config_sha != "missing" and not SAFE_SHA256_RE.fullmatch(config_sha):
        raise SmartDNSFrontendMigrationError("remote_config_sha256_invalid")
    if release_sha != "missing" and not SAFE_SHA256_RE.fullmatch(release_sha):
        raise SmartDNSFrontendMigrationError("remote_release_sha256_invalid")
    if service_sha != "missing" and not SAFE_SHA256_RE.fullmatch(service_sha):
        raise SmartDNSFrontendMigrationError("remote_service_sha256_invalid")
    return {
        "haproxy_present": values["haproxy_present"] == "yes",
        "systemd_present": values["systemd_present"] == "yes",
        "effective_uid_root": values["effective_uid_root"] == "yes",
        "python3_present": values["python3_present"] == "yes",
        "base64_present": values["base64_present"] == "yes",
        "curl_present": values["curl_present"] == "yes",
        "config_present": values["config_present"] == "yes",
        "config_sha256": config_sha,
        "service_unit_present": values["service_unit_present"] == "yes",
        "service_unit_sha256": service_sha,
        "service_reload_signal_present": values["service_reload_signal_present"] == "yes",
        "frontend_config_valid": values["frontend_config_valid"] == "yes",
        "frontend_state": values["frontend_state"],
        "frontend_enabled": values["frontend_enabled"],
        "public_443_listening": values["public_443_listening"] == "yes",
        "smart_dns_state": values["smart_dns_state"],
        "smart_dns_enabled": values["smart_dns_enabled"],
        "smart_dns_fronted_config_valid": values["smart_dns_fronted_config_valid"]
        == "yes",
        "smart_dns_loopback_listener": values["smart_dns_loopback_listener"] == "yes",
        "smart_dns_nonloopback_listener": values["smart_dns_nonloopback_listener"] == "yes",
        "smart_dns_release_sha256": release_sha,
        "smart_dns_route_present": values["smart_dns_route_present"] == "yes",
    }


def _receipt_preflight_command(backup_dir: str) -> str:
    metadata = {
        "base_config_sha256": "base-sha256",
        "candidate_config_sha256": "candidate-sha256",
        "base_service_sha256": "base-service-sha256",
        "candidate_service_sha256": "candidate-service-sha256",
        "smart_dns_release_sha256": "smart-dns-release-sha256",
        "receipt_node_code": "node-code",
        "receipt_state": "receipt-state",
    }
    lines = [
        "set -eu",
        f"test -d {_q(backup_dir)}",
        f"test ! -L {_q(backup_dir)}",
        f"test \"$(stat -c %u {_q(backup_dir)})\" = 0",
        f"printf 'backup_dir_mode=%s\\n' \"$(stat -c %a {_q(backup_dir)})\"",
    ]
    for output_name, file_name in metadata.items():
        path = backup_dir + "/" + file_name
        lines.extend(
            [
                f"test -f {_q(path)}",
                f"test ! -L {_q(path)}",
                f"test \"$(stat -c %u {_q(path)})\" = 0",
                f"IFS= read -r value < {_q(path)}; printf '{output_name}=%s\\n' \"$value\"",
            ]
        )
    for name, file_name in (
        ("backup_config_sha256", "frontend.cfg"),
        ("backup_service_sha256", "frontend.service"),
    ):
        path = backup_dir + "/" + file_name
        lines.extend(
            [
                f"test -f {_q(path)}",
                f"test ! -L {_q(path)}",
                f"test \"$(stat -c %u {_q(path)})\" = 0",
                f"printf '{name}=%s\\n' \"$(sha256sum {_q(path)} | cut -d' ' -f1)\"",
            ]
        )
    lines.append(
        f"if haproxy -c -f {_q(backup_dir + '/frontend.cfg')} >/dev/null 2>&1; then printf 'backup_config_valid=yes\\n'; else printf 'backup_config_valid=no\\n'; fi"
    )
    return "\n".join(lines)


def _remote_receipt_preflight(ssh: Any, backup_dir: str) -> dict[str, Any]:
    values = _parse_probe(
        _run(
            ssh,
            _receipt_preflight_command(backup_dir),
            label="receipt_preflight",
            timeout=90,
        )
    )
    required = {
        "backup_dir_mode",
        "base_config_sha256",
        "candidate_config_sha256",
        "base_service_sha256",
        "candidate_service_sha256",
        "smart_dns_release_sha256",
        "receipt_node_code",
        "receipt_state",
        "backup_config_sha256",
        "backup_service_sha256",
        "backup_config_valid",
    }
    if set(values) != required:
        raise SmartDNSFrontendMigrationError("receipt_preflight_fields_invalid")
    for key in (
        "base_config_sha256",
        "candidate_config_sha256",
        "base_service_sha256",
        "candidate_service_sha256",
        "smart_dns_release_sha256",
        "backup_config_sha256",
        "backup_service_sha256",
    ):
        if not SAFE_SHA256_RE.fullmatch(values[key]):
            raise SmartDNSFrontendMigrationError("receipt_sha256_invalid")
    if values["backup_dir_mode"] != "700":
        raise SmartDNSFrontendMigrationError("receipt_directory_mode_invalid")
    if values["backup_config_valid"] not in {"yes", "no"}:
        raise SmartDNSFrontendMigrationError("receipt_config_validity_invalid")
    receipt_node = _safe_component(values["receipt_node_code"], label="receipt_node_code")
    if receipt_node != values["receipt_node_code"]:
        raise SmartDNSFrontendMigrationError("receipt_node_code_not_canonical")
    if values["receipt_state"] not in {"prepared", "applied", "rolled_back"}:
        raise SmartDNSFrontendMigrationError("receipt_state_invalid")
    if (
        values["backup_config_sha256"] != values["base_config_sha256"]
        or values["backup_service_sha256"] != values["base_service_sha256"]
    ):
        raise SmartDNSFrontendMigrationError("receipt_backup_digest_mismatch")
    return {
        "base_config_sha256": values["base_config_sha256"],
        "candidate_config_sha256": values["candidate_config_sha256"],
        "base_service_sha256": values["base_service_sha256"],
        "candidate_service_sha256": values["candidate_service_sha256"],
        "smart_dns_release_sha256": values["smart_dns_release_sha256"],
        "node_code": receipt_node,
        "state": values["receipt_state"],
        "backup_config_valid": values["backup_config_valid"] == "yes",
    }


def _assert_install_preflight(
    preflight: Mapping[str, Any],
    *,
    base_sha256: str,
    base_service_sha256: str,
    smart_dns_release_sha256: str,
    candidate_valid: bool,
) -> None:
    checks = {
        "haproxy_missing": preflight.get("haproxy_present") is not True,
        "systemd_missing": preflight.get("systemd_present") is not True,
        "effective_uid_not_root": preflight.get("effective_uid_root") is not True,
        "python3_missing": preflight.get("python3_present") is not True,
        "base64_missing": preflight.get("base64_present") is not True,
        "curl_missing": preflight.get("curl_present") is not True,
        "frontend_config_missing": preflight.get("config_present") is not True,
        "frontend_config_drift": preflight.get("config_sha256") != base_sha256,
        "frontend_service_unit_missing": preflight.get("service_unit_present") is not True,
        "frontend_service_unit_drift": preflight.get("service_unit_sha256")
        != base_service_sha256,
        "frontend_config_invalid": preflight.get("frontend_config_valid") is not True,
        "frontend_not_active": preflight.get("frontend_state") != "active",
        "public_443_missing": preflight.get("public_443_listening") is not True,
        "smart_dns_not_active": preflight.get("smart_dns_state") != "active",
        "smart_dns_fronted_config_invalid": preflight.get("smart_dns_fronted_config_valid")
        is not True,
        "smart_dns_loopback_missing": preflight.get("smart_dns_loopback_listener") is not True,
        "smart_dns_nonloopback_present": preflight.get("smart_dns_nonloopback_listener") is True,
        "smart_dns_release_mismatch": preflight.get("smart_dns_release_sha256")
        != smart_dns_release_sha256,
        "smart_dns_route_already_present": preflight.get("smart_dns_route_present") is True,
        "candidate_config_invalid": candidate_valid is not True,
    }
    for error, blocked in checks.items():
        if blocked:
            raise SmartDNSFrontendMigrationError(error)


def _assert_rollback_preflight(
    preflight: Mapping[str, Any],
    receipt: Mapping[str, Any],
    *,
    node_code: str,
) -> None:
    checks = {
        "haproxy_missing": preflight.get("haproxy_present") is not True,
        "systemd_missing": preflight.get("systemd_present") is not True,
        "effective_uid_not_root": preflight.get("effective_uid_root") is not True,
        "frontend_config_missing": preflight.get("config_present") is not True,
        "frontend_service_unit_missing": preflight.get("service_unit_present") is not True,
        "frontend_config_not_receipt_candidate": preflight.get("config_sha256")
        != receipt.get("candidate_config_sha256"),
        "frontend_service_not_receipt_candidate": preflight.get("service_unit_sha256")
        != receipt.get("candidate_service_sha256"),
        "frontend_config_invalid": preflight.get("frontend_config_valid") is not True,
        "frontend_not_active": preflight.get("frontend_state") != "active",
        "public_443_missing": preflight.get("public_443_listening") is not True,
        "receipt_node_mismatch": receipt.get("node_code") != node_code,
        "receipt_not_applied": receipt.get("state") != "applied",
        "receipt_backup_config_invalid": receipt.get("backup_config_valid") is not True,
        "smart_dns_release_mismatch": preflight.get("smart_dns_release_sha256")
        != receipt.get("smart_dns_release_sha256"),
    }
    for error, blocked in checks.items():
        if blocked:
            raise SmartDNSFrontendMigrationError(error)


def _remote_write(ssh: Any, path: str, value: bytes, mode: int) -> None:
    sftp = ssh.open_sftp()
    try:
        with sftp.file(path, "wb") as handle:
            handle.write(value)
        sftp.chmod(path, mode)
    finally:
        sftp.close()


def _backup_command(
    *,
    backup_dir: str,
    base_sha256: str,
    candidate_sha256: str,
    base_service_sha256: str,
    candidate_service_sha256: str,
    smart_dns_release_sha256: str,
    node_code: str,
) -> str:
    fields = {
        "base-sha256": base_sha256,
        "candidate-sha256": candidate_sha256,
        "base-service-sha256": base_service_sha256,
        "candidate-service-sha256": candidate_service_sha256,
        "smart-dns-release-sha256": smart_dns_release_sha256,
        "node-code": node_code,
        "receipt-state": "prepared",
    }
    lines = [
        "set -eu",
        f"test ! -e {_q(backup_dir)}",
        f"install -d -o root -g root -m 0700 {_q(backup_dir)}",
        f"cp --preserve=mode,ownership,timestamps -- {_q(FRONTEND_CONFIG_PATH)} {_q(backup_dir + '/frontend.cfg')}",
        f"cp --preserve=mode,ownership,timestamps -- {_q(FRONTEND_SERVICE_PATH)} {_q(backup_dir + '/frontend.service')}",
        f"test \"$(sha256sum {_q(backup_dir + '/frontend.cfg')} | cut -d' ' -f1)\" = {_q(base_sha256)}",
        f"test \"$(sha256sum {_q(backup_dir + '/frontend.service')} | cut -d' ' -f1)\" = {_q(base_service_sha256)}",
    ]
    for name, value in fields.items():
        lines.append(f"printf '%s\\n' {_q(value)} > {_q(backup_dir + '/' + name)}")
    return "\n".join(lines)


def _apply_command(
    *,
    stage_config_path: str,
    stage_service_path: str,
    backup_dir: str,
    base_sha256: str,
    candidate_sha256: str,
    base_service_sha256: str,
    candidate_service_sha256: str,
    smart_dns_release_sha256: str,
    node_code: str,
    doh_hostname: str,
) -> str:
    next_config_path = FRONTEND_CONFIG_PATH + ".pokrov-next"
    next_service_path = FRONTEND_SERVICE_PATH + ".pokrov-next"
    return "\n".join(
        [
            "set -eu",
            f"test \"$(sha256sum {_q(FRONTEND_CONFIG_PATH)} | cut -d' ' -f1)\" = {_q(base_sha256)}",
            f"test \"$(sha256sum {_q(FRONTEND_SERVICE_PATH)} | cut -d' ' -f1)\" = {_q(base_service_sha256)}",
            f"test \"$(sha256sum {_q(stage_config_path)} | cut -d' ' -f1)\" = {_q(candidate_sha256)}",
            f"test \"$(sha256sum {_q(stage_service_path)} | cut -d' ' -f1)\" = {_q(candidate_service_sha256)}",
            f"grep -qx {_q(base_sha256)} {_q(backup_dir + '/base-sha256')}",
            f"grep -qx {_q(candidate_sha256)} {_q(backup_dir + '/candidate-sha256')}",
            f"grep -qx {_q(base_service_sha256)} {_q(backup_dir + '/base-service-sha256')}",
            f"grep -qx {_q(candidate_service_sha256)} {_q(backup_dir + '/candidate-service-sha256')}",
            f"grep -qx {_q(smart_dns_release_sha256)} {_q(backup_dir + '/smart-dns-release-sha256')}",
            f"grep -qx {_q(node_code)} {_q(backup_dir + '/node-code')}",
            f"grep -qx prepared {_q(backup_dir + '/receipt-state')}",
            f"test \"$(basename \"$(readlink -f {_q(SMART_DNS_CURRENT)})\")\" = {_q(smart_dns_release_sha256)}",
            f"systemctl is-active --quiet {_q(SMART_DNS_SERVICE)}",
            f"ss -H -ltn 'sport = :{SMART_DNS_BACKEND_PORT}' | grep -Eq '127\\.0\\.0\\.1:{SMART_DNS_BACKEND_PORT}|\\[::1\\]:{SMART_DNS_BACKEND_PORT}'",
            f"config_mode=$(stat -c %a {_q(FRONTEND_CONFIG_PATH)}); config_uid=$(stat -c %u {_q(FRONTEND_CONFIG_PATH)}); config_gid=$(stat -c %g {_q(FRONTEND_CONFIG_PATH)})",
            f"install -o \"$config_uid\" -g \"$config_gid\" -m \"$config_mode\" -- {_q(stage_config_path)} {_q(next_config_path)}",
            f"install -o root -g root -m 0644 -- {_q(stage_service_path)} {_q(next_service_path)}",
            f"haproxy -c -f {_q(next_config_path)} >/dev/null",
            f"mv -Tf -- {_q(next_service_path)} {_q(FRONTEND_SERVICE_PATH)}",
            "systemctl daemon-reload",
            f"mv -Tf -- {_q(next_config_path)} {_q(FRONTEND_CONFIG_PATH)}",
            f"main_pid=$(systemctl show {_q(FRONTEND_SERVICE)} -p MainPID --value); case \"$main_pid\" in ''|*[!0-9]*) exit 1 ;; esac; test \"$main_pid\" -gt 1; /bin/kill -USR2 \"$main_pid\"",
            "sleep 1",
            f"systemctl is-active --quiet {_q(FRONTEND_SERVICE)}",
            f"test \"$(sha256sum {_q(FRONTEND_CONFIG_PATH)} | cut -d' ' -f1)\" = {_q(candidate_sha256)}",
            f"test \"$(sha256sum {_q(FRONTEND_SERVICE_PATH)} | cut -d' ' -f1)\" = {_q(candidate_service_sha256)}",
            "ss -H -ltn 'sport = :443' | grep -q .",
            f"test \"$(curl --silent --show-error --output /dev/null --write-out '%{{http_code}}' --http1.1 --connect-timeout 3 --max-time 8 --resolve {_q(doh_hostname + ':443:127.0.0.1')} {_q('https://' + doh_hostname + '/dns-query')})\" = 400",
            f"printf 'applied\\n' > {_q(backup_dir + '/receipt-state')}",
        ]
    )


def _rollback_command(
    *,
    backup_dir: str,
    base_sha256: str,
    candidate_sha256: str,
    base_service_sha256: str,
    candidate_service_sha256: str,
    smart_dns_release_sha256: str,
    node_code: str,
    require_candidate_current: bool,
) -> str:
    next_config_path = FRONTEND_CONFIG_PATH + ".pokrov-rollback-next"
    next_service_path = FRONTEND_SERVICE_PATH + ".pokrov-rollback-next"
    lines = [
        "set -eu",
        f"test -d {_q(backup_dir)}",
        f"test \"$(stat -c %u {_q(backup_dir)})\" = 0",
        f"grep -qx {_q(base_sha256)} {_q(backup_dir + '/base-sha256')}",
        f"grep -qx {_q(candidate_sha256)} {_q(backup_dir + '/candidate-sha256')}",
        f"grep -qx {_q(base_service_sha256)} {_q(backup_dir + '/base-service-sha256')}",
        f"grep -qx {_q(candidate_service_sha256)} {_q(backup_dir + '/candidate-service-sha256')}",
        f"grep -qx {_q(smart_dns_release_sha256)} {_q(backup_dir + '/smart-dns-release-sha256')}",
        f"grep -qx {_q(node_code)} {_q(backup_dir + '/node-code')}",
        f"test \"$(sha256sum {_q(backup_dir + '/frontend.cfg')} | cut -d' ' -f1)\" = {_q(base_sha256)}",
        f"test \"$(sha256sum {_q(backup_dir + '/frontend.service')} | cut -d' ' -f1)\" = {_q(base_service_sha256)}",
    ]
    if require_candidate_current:
        lines.append(f"grep -qx applied {_q(backup_dir + '/receipt-state')}")
        lines.append(
            f"test \"$(basename \"$(readlink -f {_q(SMART_DNS_CURRENT)})\")\" = {_q(smart_dns_release_sha256)}"
        )
        lines.append(
            f"test \"$(sha256sum {_q(FRONTEND_CONFIG_PATH)} | cut -d' ' -f1)\" = {_q(candidate_sha256)}"
        )
        lines.append(
            f"test \"$(sha256sum {_q(FRONTEND_SERVICE_PATH)} | cut -d' ' -f1)\" = {_q(candidate_service_sha256)}"
        )
    else:
        lines.append(
            f"receipt_state=$(cat {_q(backup_dir + '/receipt-state')}); case \"$receipt_state\" in prepared|applied) ;; *) exit 1 ;; esac"
        )
        lines.append(
            f"current_config_sha=$(sha256sum {_q(FRONTEND_CONFIG_PATH)} | cut -d' ' -f1); case \"$current_config_sha\" in {_q(base_sha256)}|{_q(candidate_sha256)}) ;; *) exit 1 ;; esac"
        )
        lines.append(
            f"current_service_sha=$(sha256sum {_q(FRONTEND_SERVICE_PATH)} | cut -d' ' -f1); case \"$current_service_sha\" in {_q(base_service_sha256)}|{_q(candidate_service_sha256)}) ;; *) exit 1 ;; esac"
        )
    lines.extend(
        [
            f"config_mode=$(stat -c %a {_q(backup_dir + '/frontend.cfg')}); config_uid=$(stat -c %u {_q(backup_dir + '/frontend.cfg')}); config_gid=$(stat -c %g {_q(backup_dir + '/frontend.cfg')})",
            f"install -o \"$config_uid\" -g \"$config_gid\" -m \"$config_mode\" -- {_q(backup_dir + '/frontend.cfg')} {_q(next_config_path)}",
            f"install -o root -g root -m 0644 -- {_q(backup_dir + '/frontend.service')} {_q(next_service_path)}",
            f"haproxy -c -f {_q(next_config_path)} >/dev/null",
            f"mv -Tf -- {_q(next_service_path)} {_q(FRONTEND_SERVICE_PATH)}",
            "systemctl daemon-reload",
            f"mv -Tf -- {_q(next_config_path)} {_q(FRONTEND_CONFIG_PATH)}",
            f"main_pid=$(systemctl show {_q(FRONTEND_SERVICE)} -p MainPID --value); case \"$main_pid\" in ''|*[!0-9]*) exit 1 ;; esac; test \"$main_pid\" -gt 1; /bin/kill -USR2 \"$main_pid\"",
            "sleep 1",
            f"systemctl is-active --quiet {_q(FRONTEND_SERVICE)}",
            f"test \"$(sha256sum {_q(FRONTEND_CONFIG_PATH)} | cut -d' ' -f1)\" = {_q(base_sha256)}",
            f"test \"$(sha256sum {_q(FRONTEND_SERVICE_PATH)} | cut -d' ' -f1)\" = {_q(base_service_sha256)}",
            "ss -H -ltn 'sport = :443' | grep -q .",
            f"printf 'rolled_back\\n' > {_q(backup_dir + '/receipt-state')}",
        ]
    )
    return "\n".join(lines)


def _write_report(report: Mapping[str, Any], raw_path: str) -> None:
    value = str(raw_path or "").strip()
    if not value:
        return
    path = Path(value).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".tmp-{os.getpid()}")
    temp.write_text(
        json.dumps(dict(report), ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temp, path)


def _write_candidate_config(value: bytes, raw_path: str) -> None:
    path = Path(str(raw_path or "").strip()).resolve()
    try:
        path.relative_to(REPO_ROOT)
    except ValueError:
        pass
    else:
        raise SmartDNSFrontendMigrationError("candidate_config_output_must_be_outside_repository")
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".tmp-{os.getpid()}")
    temp.write_bytes(value)
    os.replace(temp, path)


def _plan_actions(operation: str) -> list[str]:
    if operation == "install":
        return [
            "verify_local_canonical_policy_and_known_base_config",
            "read_sanitized_remote_frontend_and_backend_state",
            "validate_candidate_haproxy_config_through_remote_stdin_without_persistence",
            "require_exact_base_candidate_backend_release_node_and_owner_confirmations",
            "retain_root_only_pre_mutation_frontend_receipt",
            "atomically_replace_and_reload_frontend_config",
            "verify_frontend_service_config_digest_public_listener_and_backend_state",
            "automatically_restore_receipt_on_failed_apply",
        ]
    return [
        "verify_exact_receipt_base_candidate_backend_release_and_node",
        "require_client_selection_disabled_and_owner_rollback_confirmation",
        "restore_receipt_owned_frontend_config",
        "validate_reload_and_exact_base_digest",
        "retain_smart_dns_release_and_receipt_evidence",
    ]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Guarded PLAN/APPLY/ROLLBACK for fronting the owned Smart DNS lab behind an existing HAProxy TCP/443 service."
    )
    parser.add_argument("--brain-host", default="")
    parser.add_argument("--node-code", default="")
    parser.add_argument("--known-hosts", default="")
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--base-config", default=str(DEFAULT_BASE_CONFIG))
    parser.add_argument("--base-service", default=str(DEFAULT_BASE_SERVICE))
    parser.add_argument("--doh-hostname", default="")
    parser.add_argument("--operation", choices=("install", "rollback"), default="install")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--candidate-config-out", default="")
    parser.add_argument("--receipt-id", default="")
    parser.add_argument("--confirm-base-config-sha256", default="")
    parser.add_argument("--confirm-candidate-config-sha256", default="")
    parser.add_argument("--confirm-base-service-sha256", default="")
    parser.add_argument("--confirm-candidate-service-sha256", default="")
    parser.add_argument("--confirm-smart-dns-release-sha256", default="")
    parser.add_argument("--confirm-node-code", default="")
    parser.add_argument("--confirm-client-selection-disabled", default="")
    parser.add_argument("--confirm-external-mutation", default="")
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
    requested_receipt_id = ""
    try:
        if args.offline and (args.apply or args.operation != "install"):
            raise SmartDNSFrontendMigrationError("offline_mode_plan_install_only")
        if args.operation == "install":
            if not str(args.doh_hostname or "").strip():
                raise SmartDNSFrontendMigrationError("doh_hostname_missing")
            base_path = Path(args.base_config).resolve(strict=True)
            base = _canonical_text(base_path)
            base_service = _canonical_text(Path(args.base_service).resolve(strict=True))
            candidate_service = _canonical_text(CANDIDATE_SERVICE)
            _validate_candidate_service(candidate_service)
            candidate, metadata = build_candidate_config(
                base_config=base,
                doh_hostname=args.doh_hostname,
            )
            normalized_doh = _normalize_doh_hostname(args.doh_hostname)
            policy_suffixes, policy_sha256 = _load_policy_suffixes()
            if policy_sha256 != metadata["policy_sha256"]:
                raise SmartDNSFrontendMigrationError("policy_digest_internal_mismatch")
            runtime_payload = {
                "doh_hostname": normalized_doh,
                "suffixes": policy_suffixes,
            }
            fixture_base_sha256 = _sha256_bytes(base)
            fixture_candidate_sha256 = _sha256_bytes(candidate)
            fixture_base_service_sha256 = _sha256_bytes(base_service)
            fixture_candidate_service_sha256 = _sha256_bytes(candidate_service)
            base_service_sha256 = fixture_base_service_sha256
            candidate_service_sha256 = fixture_candidate_service_sha256
        else:
            requested_receipt_id = str(args.receipt_id or "").strip()
            if not SAFE_RECEIPT_RE.fullmatch(requested_receipt_id):
                raise SmartDNSFrontendMigrationError("receipt_id_invalid")
            failure_context["receipt_id"] = requested_receipt_id
            base = b""
            candidate = b""
            base_service = b""
            candidate_service = b""
            normalized_doh = ""
            runtime_payload = {}
            metadata = {
                "backend_port": SMART_DNS_BACKEND_PORT,
                "proxy_protocol": "v2",
            }
            fixture_base_sha256 = "NOT_LOADED_ROLLBACK"
            fixture_candidate_sha256 = "NOT_LOADED_ROLLBACK"
            fixture_base_service_sha256 = "NOT_LOADED_ROLLBACK"
            fixture_candidate_service_sha256 = "NOT_LOADED_ROLLBACK"
            base_service_sha256 = "NOT_LOADED_ROLLBACK"
            candidate_service_sha256 = "NOT_LOADED_ROLLBACK"
        if args.offline:
            if not str(args.candidate_config_out or "").strip():
                raise SmartDNSFrontendMigrationError("offline_candidate_config_output_required")
            _write_candidate_config(candidate, args.candidate_config_out)
            report = {
                "schema_version": REPORT_SCHEMA,
                "mode": "OFFLINE_PLAN",
                "operation": "install",
                "target_selected": False,
                "base_config_sha256": fixture_base_sha256,
                "candidate_config_sha256": fixture_candidate_sha256,
                "base_service_sha256": base_service_sha256,
                "candidate_service_sha256": candidate_service_sha256,
                "policy_sha256": metadata["policy_sha256"],
                "application_suffix_count": metadata["application_suffix_count"],
                "exact_sni_route_count": metadata["exact_sni_route_count"],
                "child_sni_route_count": metadata["child_sni_route_count"],
                "backend_port": metadata["backend_port"],
                "proxy_protocol": metadata["proxy_protocol"],
                "candidate_config_written": True,
                "candidate_config_valid": "NOT_RUN_REMOTE_HAPROXY",
                "mutation_performed": False,
                "raw_hostname_returned": False,
                "raw_config_returned": False,
                "plan": _plan_actions("install"),
            }
            _write_report(report, args.json_out)
            print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
            return 0

        node_code = _safe_component(args.node_code, label="node_code")
        if not str(args.brain_host or "").strip():
            raise SmartDNSFrontendMigrationError("brain_host_missing")
        if not str(args.known_hosts or "").strip():
            raise SmartDNSFrontendMigrationError("known_hosts_missing")
        known_hosts = Path(args.known_hosts).resolve(strict=True)
        passwords = Path(args.passwords).resolve()
        if not known_hosts.is_file():
            raise SmartDNSFrontendMigrationError("known_hosts_missing")

        os.environ["POKROV_SSH_KNOWN_HOSTS"] = str(known_hosts)
        os.environ["POKROV_SSH_TRUST_ON_FIRST_USE"] = "0"
        brain, brain_auth = _connect_owned(
            code="brain", host=str(args.brain_host), passwords=passwords
        )
        node = None
        try:
            host = _resolve_node_host(brain, node_code)
            node, node_auth = _connect_owned(code=node_code, host=host, passwords=passwords)
            preflight = _remote_preflight(node)
            runtime_transform: dict[str, Any] | None = None
            receipt: dict[str, Any] | None = None
            receipt_id = requested_receipt_id
            backup_dir = ""
            if args.operation == "install":
                if preflight["haproxy_present"] and preflight["config_present"]:
                    runtime_transform = _runtime_transform(
                        node,
                        payload=runtime_payload,
                        mode="plan",
                    )
                    if runtime_transform["base_config_sha256"] != preflight["config_sha256"]:
                        raise SmartDNSFrontendMigrationError("runtime_base_digest_readback_mismatch")
                    base_sha256 = str(runtime_transform["base_config_sha256"])
                    candidate_sha256 = str(runtime_transform["candidate_config_sha256"])
                    candidate_valid = bool(runtime_transform["candidate_config_valid"])
                else:
                    base_sha256 = str(preflight["config_sha256"])
                    candidate_sha256 = "missing"
                    candidate_valid = False
                smart_dns_release_sha256 = str(preflight["smart_dns_release_sha256"])
            else:
                backup_dir = f"{BACKUP_ROOT}/{receipt_id}"
                receipt = _remote_receipt_preflight(node, backup_dir)
                base_sha256 = str(receipt["base_config_sha256"])
                candidate_sha256 = str(receipt["candidate_config_sha256"])
                base_service_sha256 = str(receipt["base_service_sha256"])
                candidate_service_sha256 = str(receipt["candidate_service_sha256"])
                smart_dns_release_sha256 = str(receipt["smart_dns_release_sha256"])
                candidate_valid = bool(
                    preflight["frontend_config_valid"]
                    and preflight["config_sha256"] == candidate_sha256
                )
            report: dict[str, Any] = {
                "schema_version": REPORT_SCHEMA,
                "mode": "APPLY" if args.apply else "PLAN",
                "operation": args.operation,
                "node_code": node_code,
                "base_config_sha256": base_sha256,
                "candidate_config_sha256": candidate_sha256,
                "base_service_sha256": base_service_sha256,
                "candidate_service_sha256": candidate_service_sha256,
                "known_hosts_sha256": _sha256_file(known_hosts),
                "brain_auth_method": _auth_family(brain_auth),
                "node_auth_method": _auth_family(node_auth),
                "backend_port": metadata["backend_port"],
                "proxy_protocol": metadata["proxy_protocol"],
                "candidate_config_valid": candidate_valid,
                "runtime_base_config_valid": bool(
                    runtime_transform and runtime_transform["base_config_valid"]
                ),
                "preflight": preflight,
                "mutation_performed": False,
                "raw_host_returned": False,
                "raw_config_returned": False,
                "raw_runtime_material_returned": False,
                "external_access": "NOT_RUN",
            }
            if args.operation == "install":
                report.update(
                    {
                        "repository_fixture_base_config_sha256": fixture_base_sha256,
                        "repository_fixture_candidate_config_sha256": fixture_candidate_sha256,
                        "repository_fixture_base_service_sha256": fixture_base_service_sha256,
                        "repository_fixture_candidate_service_sha256": fixture_candidate_service_sha256,
                        "policy_sha256": metadata["policy_sha256"],
                        "application_suffix_count": metadata["application_suffix_count"],
                        "exact_sni_route_count": metadata["exact_sni_route_count"],
                        "child_sni_route_count": metadata["child_sni_route_count"],
                        "repository_fixture_matches_runtime": preflight["config_sha256"]
                        == fixture_base_sha256,
                        "baseline_service_matches": preflight["service_unit_sha256"]
                        == base_service_sha256,
                    }
                )
            else:
                report["repository_fixtures_loaded"] = False
            if receipt is not None:
                report.update(
                    {
                        "receipt_id": receipt_id,
                        "receipt_state": receipt["state"],
                        "receipt_node_matches": receipt["node_code"] == node_code,
                        "current_candidate_config_matches": preflight["config_sha256"]
                        == candidate_sha256,
                        "current_candidate_service_matches": preflight["service_unit_sha256"]
                        == candidate_service_sha256,
                        "receipt_backup_config_valid": receipt["backup_config_valid"],
                    }
                )
            if not args.apply:
                report["plan"] = _plan_actions(args.operation)
                _write_report(report, args.json_out)
                print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
                return 0

            confirmed_base = str(args.confirm_base_config_sha256).strip().lower()
            confirmed_candidate = str(args.confirm_candidate_config_sha256).strip().lower()
            confirmed_base_service = str(args.confirm_base_service_sha256).strip().lower()
            confirmed_candidate_service = str(args.confirm_candidate_service_sha256).strip().lower()
            confirmed_release = str(args.confirm_smart_dns_release_sha256).strip().lower()
            if confirmed_base != base_sha256:
                raise SmartDNSFrontendMigrationError("confirm_base_config_sha256_mismatch")
            if confirmed_candidate != candidate_sha256:
                raise SmartDNSFrontendMigrationError("confirm_candidate_config_sha256_mismatch")
            if confirmed_base_service != base_service_sha256:
                raise SmartDNSFrontendMigrationError("confirm_base_service_sha256_mismatch")
            if confirmed_candidate_service != candidate_service_sha256:
                raise SmartDNSFrontendMigrationError("confirm_candidate_service_sha256_mismatch")
            if not SAFE_SHA256_RE.fullmatch(confirmed_release):
                raise SmartDNSFrontendMigrationError("confirm_smart_dns_release_sha256_invalid")
            if confirmed_release != smart_dns_release_sha256:
                raise SmartDNSFrontendMigrationError("confirm_smart_dns_release_sha256_mismatch")
            if str(args.confirm_node_code).strip().lower() != node_code:
                raise SmartDNSFrontendMigrationError("confirm_node_code_mismatch")
            if str(args.confirm_client_selection_disabled).strip() != "CLIENT_SELECTION_DISABLED":
                raise SmartDNSFrontendMigrationError("client_selection_disable_confirmation_missing")

            if args.operation == "install":
                if str(args.confirm_external_mutation).strip() != "FRONTEND_MUTATION_AUTHORIZED":
                    raise SmartDNSFrontendMigrationError("frontend_mutation_confirmation_missing")
                _assert_install_preflight(
                    preflight,
                    base_sha256=base_sha256,
                    base_service_sha256=base_service_sha256,
                    smart_dns_release_sha256=confirmed_release,
                    candidate_valid=candidate_valid,
                )
                receipt_id = _release_id(candidate_sha256)
                failure_context["receipt_id"] = receipt_id
                backup_dir = f"{BACKUP_ROOT}/{receipt_id}"
                stage_dir = f"{STAGE_ROOT}/{receipt_id}"
                stage_config_path = f"{stage_dir}/candidate.cfg"
                stage_service_path = f"{stage_dir}/candidate.service"
                backup_ready = False
                try:
                    _run(
                        node,
                        f"test ! -e {_q(stage_dir)}; install -d -o root -g root -m 0700 {_q(stage_dir)}",
                        label="stage_prepare",
                    )
                    staged = _runtime_transform(
                        node,
                        payload=runtime_payload,
                        mode="stage",
                        output_path=stage_config_path,
                        expected_base_sha256=base_sha256,
                        expected_candidate_sha256=candidate_sha256,
                    )
                    if staged["candidate_config_sha256"] != candidate_sha256:
                        raise SmartDNSFrontendMigrationError("staged_candidate_digest_mismatch")
                    _remote_write(node, stage_service_path, candidate_service, 0o600)
                    _run(
                        node,
                        _backup_command(
                            backup_dir=backup_dir,
                            base_sha256=base_sha256,
                            candidate_sha256=candidate_sha256,
                            base_service_sha256=base_service_sha256,
                            candidate_service_sha256=candidate_service_sha256,
                            smart_dns_release_sha256=confirmed_release,
                            node_code=node_code,
                        ),
                        label="receipt_backup",
                    )
                    backup_ready = True
                    failure_context["receipt_created"] = True
                    failure_context["automatic_rollback_status"] = "ARMED"
                    failure_context["mutation_attempted"] = True
                    _run(
                        node,
                        _apply_command(
                            stage_config_path=stage_config_path,
                            stage_service_path=stage_service_path,
                            backup_dir=backup_dir,
                            base_sha256=base_sha256,
                            candidate_sha256=candidate_sha256,
                            base_service_sha256=base_service_sha256,
                            candidate_service_sha256=candidate_service_sha256,
                            smart_dns_release_sha256=confirmed_release,
                            node_code=node_code,
                            doh_hostname=normalized_doh,
                        ),
                        label="frontend_apply",
                    )
                except Exception:
                    if backup_ready:
                        try:
                            _run(
                                node,
                                _rollback_command(
                                    backup_dir=backup_dir,
                                    base_sha256=base_sha256,
                                    candidate_sha256=candidate_sha256,
                                    base_service_sha256=base_service_sha256,
                                    candidate_service_sha256=candidate_service_sha256,
                                    smart_dns_release_sha256=confirmed_release,
                                    node_code=node_code,
                                    require_candidate_current=False,
                                ),
                                label="automatic_rollback",
                            )
                            failure_context["automatic_rollback_status"] = "PASS"
                        except Exception:
                            failure_context["automatic_rollback_status"] = "FAIL"
                            raise
                    raise
                finally:
                    _run_allow_failure(
                        node,
                        f"rm -f -- {_q(stage_config_path)} {_q(stage_service_path)}",
                    )
                    _run_allow_failure(node, f"rmdir -- {_q(stage_dir)}")
                report.update(
                    {
                        "mutation_performed": True,
                        "receipt_id": receipt_id,
                        "frontend_reloaded": True,
                        "automatic_rollback_armed": True,
                    }
                )
            else:
                if str(args.confirm_external_mutation).strip() != "FRONTEND_ROLLBACK_AUTHORIZED":
                    raise SmartDNSFrontendMigrationError("frontend_rollback_confirmation_missing")
                if receipt is None:
                    raise SmartDNSFrontendMigrationError("receipt_preflight_missing")
                _assert_rollback_preflight(preflight, receipt, node_code=node_code)
                _run(
                    node,
                    _rollback_command(
                        backup_dir=backup_dir,
                        base_sha256=base_sha256,
                        candidate_sha256=candidate_sha256,
                        base_service_sha256=base_service_sha256,
                        candidate_service_sha256=candidate_service_sha256,
                        smart_dns_release_sha256=confirmed_release,
                        node_code=node_code,
                        require_candidate_current=True,
                    ),
                    label="explicit_rollback",
                )
                report.update(
                    {
                        "mutation_performed": True,
                        "receipt_id": receipt_id,
                        "rollback_completed": True,
                        "smart_dns_release_retained": True,
                    }
                )
            _write_report(report, args.json_out)
            print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
            return 0
        finally:
            if node is not None:
                node.close()
            brain.close()
    except Exception as exc:
        code = str(exc).split(":", 1)[0][:160]
        failure_report = {
            "schema_version": REPORT_SCHEMA,
            "mode": "ERROR",
            "operation": str(getattr(args, "operation", "unknown")),
            "error_code": code,
            "receipt_id": failure_context["receipt_id"] or None,
            "receipt_created": failure_context["receipt_created"],
            "mutation_attempted": failure_context["mutation_attempted"],
            "automatic_rollback_status": failure_context["automatic_rollback_status"],
            "raw_host_returned": False,
            "raw_config_returned": False,
            "raw_runtime_material_returned": False,
        }
        try:
            _write_report(failure_report, str(getattr(args, "json_out", "") or ""))
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
            f"owned Smart DNS frontend migration failed: {type(exc).__name__}: {code}{receipt_suffix}{rollback_suffix}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
