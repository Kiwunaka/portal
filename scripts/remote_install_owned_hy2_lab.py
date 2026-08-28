from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

try:
    import build_owned_hy2_server_bundle as bundle_contract
    from node_access import DEFAULT_PASSWORDS, connect_node
except ImportError:  # pragma: no cover - package import for tests
    from . import build_owned_hy2_server_bundle as bundle_contract
    from .node_access import DEFAULT_PASSWORDS, connect_node


REPORT_SCHEMA = "pokrov-owned-hy2-remote-operation-v1"
DEFAULT_NODE_CODE = "de"
SERVICE_NAME = "pokrov-hy2-lab.service"
SERVICE_PATH = "/etc/systemd/system/pokrov-hy2-lab.service"
RELEASE_ROOT = "/opt/pokrov/hy2/releases"
CURRENT_POINTER = "/opt/pokrov/hy2/current"
CONFIG_ROOT = "/etc/pokrov-hy2"
CONFIG_PATH = f"{CONFIG_ROOT}/config.json"
CERT_PATH = f"{CONFIG_ROOT}/tls.crt"
KEY_PATH = f"{CONFIG_ROOT}/tls.key"
BACKUP_ROOT = "/root/pokrov-hy2-lab-backups"
STAGE_ROOT = "/root/pokrov-hy2-lab-staging"
RUNTIME_STAGE_ROOT = "/root/pokrov-hy2-runtime-staging"
LISTEN_PORT = 443
SAFE_SHA256_RE = re.compile(r"[0-9a-f]{64}")
SAFE_COMPONENT_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,31}")
SAFE_RECEIPT_RE = re.compile(r"[0-9]{8}T[0-9]{6}Z-[0-9]+-[0-9a-f]{12}")


class Hy2RemoteOperationError(RuntimeError):
    """Raised when a guarded remote HY2 operation cannot prove its contract."""


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
        raise Hy2RemoteOperationError(f"{label}_invalid")
    return normalized


def _release_id(bundle_sha256: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{now}-{os.getpid()}-{bundle_sha256[:12]}"


def _run(ssh: Any, command: str, *, label: str, timeout: int = 180) -> str:
    _stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="replace").strip()
    if code != 0:
        # Remote output may contain paths, endpoint data or service environment.
        # Keep failures machine-readable without reflecting it into logs.
        stderr.read()
        raise Hy2RemoteOperationError(f"{label}_failed:exit_{code}")
    stderr.read()
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
        raise Hy2RemoteOperationError(f"{label}_failed:exit_{code}")
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
        raise Hy2RemoteOperationError("owned_node_resolution_not_unique")
    return hosts[0]


def _brain_hy2_kill_switch(brain: Any) -> str:
    value = _psql(
        brain,
        "select coalesce(value_json::jsonb#>>'{hy2_lab,kill_switch_engaged}','') "
        "from app_settings where key='network_rollout_config';",
        label="brain_hy2_kill_switch_readback",
    ).strip().lower()
    return {"true": "engaged", "false": "disengaged"}.get(value, "unavailable")


def _auth_family(value: str) -> str:
    return "key" if str(value or "").startswith("key") else "password"


def _connect_owned(*, code: str, host: str, passwords: Path) -> tuple[Any, str]:
    try:
        return connect_node(code=code, host=host, passwords_path=passwords)
    except Exception as exc:
        raise Hy2RemoteOperationError(f"{code}_ssh_connect_failed") from exc


def _validated_local_bundle(
    raw_path: str | Path,
) -> tuple[Path, dict[str, Any], dict[str, bytes], str]:
    path = Path(raw_path).resolve(strict=True)
    manifest, contents = bundle_contract._validated_bundle(path)
    digest = _sha256_file(path)
    install = manifest.get("install") or {}
    runtime = manifest.get("runtime") or {}
    if (
        install.get("service_name") != SERVICE_NAME
        or install.get("service_path") != SERVICE_PATH
        or install.get("release_root") != RELEASE_ROOT
        or install.get("current_pointer") != CURRENT_POINTER
        or install.get("config_path") != CONFIG_PATH
        or install.get("enable_by_default") is not False
        or runtime.get("listen_port") != LISTEN_PORT
        or runtime.get("single_port") is not True
        or runtime.get("port_hopping") is not False
    ):
        raise Hy2RemoteOperationError("bundle_remote_install_contract_mismatch")
    return path, manifest, contents, digest


def _parse_probe(raw: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in raw.splitlines():
        if "=" not in line:
            raise Hy2RemoteOperationError("remote_preflight_shape_invalid")
        key, value = line.split("=", 1)
        if not re.fullmatch(r"[a-z0-9_]+", key) or not re.fullmatch(
            r"[A-Za-z0-9_.:-]+", value
        ):
            raise Hy2RemoteOperationError("remote_preflight_value_invalid")
        parsed[key] = value
    return parsed


def _runtime_contract_check(config_path: str) -> str:
    validator = f"""
import json
import sys

try:
    with open(sys.argv[1], encoding="utf-8") as handle:
        config = json.load(handle)
    inbounds = config.get("inbounds")
    inbound = inbounds[0] if isinstance(inbounds, list) and len(inbounds) == 1 else None
    users = inbound.get("users") if isinstance(inbound, dict) else None
    user = users[0] if isinstance(users, list) and len(users) == 1 else None
    tls = inbound.get("tls") if isinstance(inbound, dict) else None
    obfs = inbound.get("obfs") if isinstance(inbound, dict) else None
    outbounds = config.get("outbounds")
    route = config.get("route")
    serialized = json.dumps(config, sort_keys=True)
    ok = (
        isinstance(inbound, dict)
        and inbound.get("type") == "hysteria2"
        and inbound.get("tag") == "pokrov-hy2-lab-in"
        and inbound.get("listen") == "0.0.0.0"
        and inbound.get("listen_port") == {LISTEN_PORT}
        and isinstance(inbound.get("up_mbps"), int)
        and 1 <= inbound["up_mbps"] <= 1000
        and isinstance(inbound.get("down_mbps"), int)
        and 1 <= inbound["down_mbps"] <= 1000
        and inbound.get("ignore_client_bandwidth") is False
        and isinstance(user, dict)
        and 1 <= len(str(user.get("name") or "")) <= 64
        and 16 <= len(str(user.get("password") or "")) <= 128
        and isinstance(obfs, dict)
        and obfs.get("type") == "salamander"
        and 16 <= len(str(obfs.get("password") or "")) <= 128
        and isinstance(tls, dict)
        and tls.get("enabled") is True
        and tls.get("min_version") == "1.3"
        and tls.get("alpn") == ["h3"]
        and tls.get("certificate_path") == "{CERT_PATH}"
        and tls.get("key_path") == "{KEY_PATH}"
        and isinstance(outbounds, list)
        and outbounds == [
            {{"type": "direct", "tag": "direct"}},
            {{"type": "block", "tag": "block"}},
        ]
        and route == {{"auto_detect_interface": True, "final": "direct"}}
        and "server_ports" not in serialized
        and "hop_interval" not in serialized
        and "hysteria2://" not in serialized
        and "hy2://" not in serialized
        and "POKROV_" not in serialized
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


def _preflight_command(*, release_dir: str, runtime_material_dir: str) -> str:
    targets = {
        "release": release_dir,
        "current": CURRENT_POINTER,
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
        "emit_bool sha256sum 'command -v sha256sum >/dev/null 2>&1'",
        "emit_bool runuser 'command -v runuser >/dev/null 2>&1'",
        "emit_bool python3 'command -v python3 >/dev/null 2>&1'",
        "emit_bool ufw_installed 'command -v ufw >/dev/null 2>&1'",
        "emit_bool ufw_active \"ufw status 2>/dev/null | grep -q '^Status: active$'\"",
        f"emit_bool ufw_rule_present \"ufw status 2>/dev/null | grep -Eq '^[[:space:]]*{LISTEN_PORT}/udp[[:space:]]+ALLOW'\"",
        f"emit_bool udp_busy \"ss -H -lun 'sport = :{LISTEN_PORT}' 2>/dev/null | grep -q .\"",
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
            f"emit_bool runtime_cert_present 'test -f {_q(runtime_material_dir + '/tls.crt')}'",
            f"emit_bool runtime_key_present 'test -f {_q(runtime_material_dir + '/tls.key')}'",
            f"emit_bool runtime_dir_root_only \"test \"$(stat -c %u {_q(runtime_material_dir)} 2>/dev/null || printf x)\" = 0 && ! find {_q(runtime_material_dir)} -maxdepth 0 -perm /077 -print -quit 2>/dev/null | grep -q .\"",
            f"emit_bool runtime_files_root_owned \"test \"$(stat -c %u {_q(runtime_material_dir + '/config.json')} 2>/dev/null || printf x)\" = 0 && test \"$(stat -c %u {_q(runtime_material_dir + '/tls.crt')} 2>/dev/null || printf x)\" = 0 && test \"$(stat -c %u {_q(runtime_material_dir + '/tls.key')} 2>/dev/null || printf x)\" = 0\"",
            f"emit_bool runtime_secrets_private \"! find {_q(runtime_material_dir + '/config.json')} {_q(runtime_material_dir + '/tls.key')} -perm /077 -print -quit 2>/dev/null | grep -q .\"",
            f"emit_bool runtime_placeholders_absent \"! grep -Fq 'POKROV_' {_q(runtime_material_dir + '/config.json')} 2>/dev/null\"",
            f"emit_bool runtime_final_paths_bound \"grep -Fq {_q(CERT_PATH)} {_q(runtime_material_dir + '/config.json')} 2>/dev/null && grep -Fq {_q(KEY_PATH)} {_q(runtime_material_dir + '/config.json')} 2>/dev/null\"",
            f"emit_bool runtime_contract_valid {_q(_runtime_contract_check(runtime_material_dir + '/config.json'))}",
        ]
    )
    return "\n".join(lines)


def _remote_preflight(
    node: Any, *, release_dir: str, runtime_material_dir: str
) -> dict[str, Any]:
    values = _parse_probe(
        _run(
            node,
            _preflight_command(
                release_dir=release_dir, runtime_material_dir=runtime_material_dir
            ),
            label="remote_preflight",
            timeout=90,
        )
    )
    required = {
        "root",
        "systemd",
        "ss",
        "sha256sum",
        "runuser",
        "python3",
        "ufw_installed",
        "ufw_active",
        "ufw_rule_present",
        "udp_busy",
        "release_present",
        "current_present",
        "config_present",
        "cert_present",
        "key_present",
        "unit_present",
        "service_state",
        "service_enabled",
        "runtime_dir_present",
        "runtime_config_present",
        "runtime_cert_present",
        "runtime_key_present",
        "runtime_dir_root_only",
        "runtime_files_root_owned",
        "runtime_secrets_private",
        "runtime_placeholders_absent",
        "runtime_final_paths_bound",
        "runtime_contract_valid",
    }
    if set(values) != required:
        raise Hy2RemoteOperationError("remote_preflight_fields_invalid")
    bool_keys = required - {"service_state", "service_enabled"}
    if any(values[key] not in {"yes", "no"} for key in bool_keys):
        raise Hy2RemoteOperationError("remote_preflight_boolean_invalid")
    occupied = [
        label
        for label in ("release", "current", "config", "cert", "key", "unit")
        if values[f"{label}_present"] == "yes"
    ]
    runtime_ready = all(
        values[key] == "yes"
        for key in (
            "runtime_dir_present",
            "runtime_config_present",
            "runtime_cert_present",
            "runtime_key_present",
            "runtime_dir_root_only",
            "runtime_files_root_owned",
            "runtime_secrets_private",
            "runtime_placeholders_absent",
            "runtime_final_paths_bound",
            "runtime_contract_valid",
        )
    )
    return {
        "root": values["root"] == "yes",
        "required_tools": all(
            values[key] == "yes"
            for key in ("systemd", "ss", "sha256sum", "runuser", "python3")
        ),
        "ufw_installed": values["ufw_installed"] == "yes",
        "ufw_active": values["ufw_active"] == "yes",
        "ufw_rule_present": values["ufw_rule_present"] == "yes",
        "udp_443": "busy" if values["udp_busy"] == "yes" else "free",
        "occupied_targets": occupied,
        "service_state": values["service_state"],
        "service_enabled": values["service_enabled"],
        "runtime_material_ready": runtime_ready,
        "runtime_material_returned": False,
    }


def _assert_fresh_install_preflight(preflight: Mapping[str, Any]) -> None:
    if not preflight.get("root") or not preflight.get("required_tools"):
        raise Hy2RemoteOperationError("install_host_requirements_not_met")
    if not preflight.get("ufw_installed") or not preflight.get("ufw_active"):
        raise Hy2RemoteOperationError("install_requires_active_ufw")
    if preflight.get("ufw_rule_present"):
        raise Hy2RemoteOperationError("install_udp_firewall_rule_already_present")
    if preflight.get("udp_443") != "free":
        raise Hy2RemoteOperationError("install_udp_443_occupied")
    if preflight.get("occupied_targets"):
        raise Hy2RemoteOperationError("install_target_already_present")
    if preflight.get("service_state") not in {"inactive", "unknown"}:
        raise Hy2RemoteOperationError("install_service_not_inactive")
    if not preflight.get("runtime_material_ready"):
        raise Hy2RemoteOperationError("install_runtime_material_not_ready")


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
    records = {str(item["path"]): item for item in manifest["files"]}
    checks = ["set -e"]
    for member in contents:
        record = records[member]
        remote_path = f"{stage_dir}/{member}"
        checks.append(
            f"test \"$(stat -c %s {_q(remote_path)})\" = {_q(str(record['size_bytes']))}"
        )
        checks.append(
            f"test \"$(sha256sum {_q(remote_path)} | awk '{{print $1}}')\" = {_q(str(record['sha256']))}"
        )
    _run(node, "\n".join(checks), label="stage_digest_readback", timeout=240)


def _backup_command(
    *, backup_dir: str, bundle_sha256: str, node_code: str
) -> str:
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
        f"systemctl is-active {_q(SERVICE_NAME)} > {_q(backup_dir + '/service-active')} 2>/dev/null || printf 'inactive\\n' > {_q(backup_dir + '/service-active')}",
        f"systemctl is-enabled {_q(SERVICE_NAME)} > {_q(backup_dir + '/service-enabled')} 2>/dev/null || printf 'disabled\\n' > {_q(backup_dir + '/service-enabled')}",
        f"if id -u pokrov-hy2 >/dev/null 2>&1; then printf 'present\\n' > {_q(backup_dir + '/user-state')}; else printf 'missing\\n' > {_q(backup_dir + '/user-state')}; fi",
        f"if getent group pokrov-hy2 >/dev/null 2>&1; then printf 'present\\n' > {_q(backup_dir + '/group-state')}; else printf 'missing\\n' > {_q(backup_dir + '/group-state')}; fi",
        f"if ufw status 2>/dev/null | grep -Eq '^[[:space:]]*{LISTEN_PORT}/udp[[:space:]]+ALLOW'; then printf 'present\\n' > {_q(backup_dir + '/ufw-rule-state')}; else printf 'missing\\n' > {_q(backup_dir + '/ufw-rule-state')}; fi",
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


def _install_command(
    *,
    stage_dir: str,
    release_dir: str,
    runtime_material_dir: str,
    backup_dir: str,
    manifest: Mapping[str, Any],
) -> str:
    records = {str(item["path"]): item for item in manifest["files"]}
    lines = [
        "set -e",
        "getent group pokrov-hy2 >/dev/null 2>&1 || groupadd --system pokrov-hy2",
        "id -u pokrov-hy2 >/dev/null 2>&1 || useradd --system --gid pokrov-hy2 --home-dir /nonexistent --shell /usr/sbin/nologin pokrov-hy2",
        f"install -d -o root -g root -m 0755 {_q(release_dir)}",
    ]
    for member, record in sorted(records.items()):
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
            f"install -d -o root -g pokrov-hy2 -m 0750 {_q(CONFIG_ROOT)}",
            f"install -o root -g pokrov-hy2 -m 0640 {_q(runtime_material_dir + '/config.json')} {_q(CONFIG_PATH)}",
            f"install -o root -g pokrov-hy2 -m 0644 {_q(runtime_material_dir + '/tls.crt')} {_q(CERT_PATH)}",
            f"install -o root -g pokrov-hy2 -m 0640 {_q(runtime_material_dir + '/tls.key')} {_q(KEY_PATH)}",
            f"install -o root -g root -m 0644 {_q(stage_dir + '/systemd/pokrov-hy2-lab.service')} {_q(SERVICE_PATH)}",
            "systemctl daemon-reload",
            f"runuser -u pokrov-hy2 -- {_q(release_dir + '/' + bundle_contract.BINARY_MEMBER)} check -c {_q(CONFIG_PATH)} >/dev/null",
            f"ufw allow {LISTEN_PORT}/udp comment 'POKROV HY2 lab' >/dev/null",
            f"systemctl start {_q(SERVICE_NAME)}",
            f"test \"$(systemctl is-active {_q(SERVICE_NAME)})\" = active",
            f"ss -H -lun 'sport = :{LISTEN_PORT}' | grep -q .",
            f"systemctl enable {_q(SERVICE_NAME)} >/dev/null",
            f"test \"$(systemctl is-enabled {_q(SERVICE_NAME)})\" = enabled",
            f"test \"$(readlink -f {_q(CURRENT_POINTER)})\" = {_q(release_dir)}",
            f"printf 'installed\\n' > {_q(backup_dir + '/receipt-state')}",
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
) -> str:
    lines = [
        "set -e",
        f"test -d {_q(backup_dir)}",
        f"test \"$(stat -c %u {_q(backup_dir)})\" = 0",
        f"grep -qx {_q(bundle_sha256)} {_q(backup_dir + '/bundle-sha256')}",
        f"grep -qx {_q(node_code)} {_q(backup_dir + '/node-code')}",
    ]
    if require_current_release:
        lines.append(
            f"test \"$(readlink -f {_q(CURRENT_POINTER)})\" = {_q(release_dir)}"
        )
    lines.extend(
        [
            f"systemctl disable --now {_q(SERVICE_NAME)} >/dev/null 2>&1 || true",
            f"listener_after_stop=free; if ss -H -lun 'sport = :{LISTEN_PORT}' | grep -q .; then listener_after_stop=busy; fi",
            f"if grep -qx missing {_q(backup_dir + '/ufw-rule-state')}; then ufw --force delete allow {LISTEN_PORT}/udp >/dev/null 2>&1 || true; fi",
        ]
    )
    lines.extend(
        _restore_target_lines(backup_dir=backup_dir, name="current", target=CURRENT_POINTER)
    )
    lines.extend(
        _restore_target_lines(backup_dir=backup_dir, name="config", target=CONFIG_PATH)
    )
    lines.extend(_restore_target_lines(backup_dir=backup_dir, name="cert", target=CERT_PATH))
    lines.extend(_restore_target_lines(backup_dir=backup_dir, name="key", target=KEY_PATH))
    lines.extend(_restore_target_lines(backup_dir=backup_dir, name="unit", target=SERVICE_PATH))
    lines.extend(
        [
            "systemctl daemon-reload",
            f"if grep -qx enabled {_q(backup_dir + '/service-enabled')}; then systemctl enable {_q(SERVICE_NAME)} >/dev/null; fi",
            f"if grep -qx active {_q(backup_dir + '/service-active')}; then systemctl start {_q(SERVICE_NAME)}; fi",
            f"if grep -qx missing {_q(backup_dir + '/user-state')}; then userdel pokrov-hy2 >/dev/null 2>&1 || true; fi",
            f"if grep -qx missing {_q(backup_dir + '/group-state')}; then groupdel pokrov-hy2 >/dev/null 2>&1 || true; fi",
            f"if ! grep -qx active {_q(backup_dir + '/service-active')}; then test \"$listener_after_stop\" = free; ! ss -H -lun 'sport = :{LISTEN_PORT}' | grep -q .; fi",
            f"printf 'rolled_back\\n' > {_q(backup_dir + '/receipt-state')}",
            # The failed immutable release is deliberately retained for evidence.
            f"test -d {_q(release_dir)} || true",
        ]
    )
    return "\n".join(lines)


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
    parser = argparse.ArgumentParser(
        description="Guarded PLAN/APPLY/ROLLBACK for the owned POKROV HY2 lab."
    )
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--brain-host", required=True)
    parser.add_argument("--node-code", default=DEFAULT_NODE_CODE)
    parser.add_argument("--known-hosts", required=True)
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--operation", choices=("install", "rollback"), default="install")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--runtime-material-dir", default="")
    parser.add_argument("--receipt-id", default="")
    parser.add_argument("--confirm-bundle-sha256", default="")
    parser.add_argument("--confirm-source-revision", default="")
    parser.add_argument("--confirm-node-code", default="")
    parser.add_argument("--confirm-runtime-material-ready", default="")
    parser.add_argument("--json-out", default="")
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        node_code = _safe_component(args.node_code, label="node_code")
        bundle_path, manifest, contents, bundle_sha256 = _validated_local_bundle(args.bundle)
        source_revision = str(manifest["source"]["revision"]).lower()
        release_dir = f"{RELEASE_ROOT}/{bundle_sha256}"
        runtime_material_dir = str(args.runtime_material_dir or "").strip()
        if not runtime_material_dir:
            runtime_material_dir = f"{RUNTIME_STAGE_ROOT}/{bundle_sha256}"
        if runtime_material_dir != f"{RUNTIME_STAGE_ROOT}/{bundle_sha256}":
            raise Hy2RemoteOperationError("runtime_material_dir_not_receipt_bound")
        known_hosts = Path(args.known_hosts).resolve(strict=True)
        passwords = Path(args.passwords).resolve()
        if not known_hosts.is_file():
            raise Hy2RemoteOperationError("known_hosts_missing")

        os.environ["POKROV_SSH_KNOWN_HOSTS"] = str(known_hosts)
        os.environ["POKROV_SSH_TRUST_ON_FIRST_USE"] = "0"
        brain, brain_auth = _connect_owned(
            code="brain", host=str(args.brain_host), passwords=passwords
        )
        node = None
        try:
            host = _resolve_node_host(brain, node_code)
            kill_switch = _brain_hy2_kill_switch(brain)
            node, node_auth = _connect_owned(
                code=node_code, host=host, passwords=passwords
            )
            preflight = _remote_preflight(
                node,
                release_dir=release_dir,
                runtime_material_dir=runtime_material_dir,
            )
            report: dict[str, Any] = {
                "schema_version": REPORT_SCHEMA,
                "mode": "APPLY" if args.apply else "PLAN",
                "operation": args.operation,
                "node_code": node_code,
                "bundle_sha256": bundle_sha256,
                "bundle_size_bytes": bundle_path.stat().st_size,
                "source_revision": source_revision,
                "contract_sha256": manifest["contract_sha256"],
                "known_hosts_sha256": _sha256_file(known_hosts),
                "brain_auth_method": _auth_family(brain_auth),
                "node_auth_method": _auth_family(node_auth),
                "brain_hy2_kill_switch": kill_switch,
                "preflight": preflight,
                "mutation_performed": False,
                "raw_host_returned": False,
                "raw_runtime_material_returned": False,
                "external_handshake": "NOT_RUN",
            }
            if not args.apply:
                report["plan"] = bundle_contract.plan_bundle(
                    bundle=bundle_path,
                    operation=args.operation,
                    node_code=node_code,
                )
                _write_report(report, args.json_out)
                print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
                return 0

            if str(args.confirm_bundle_sha256).strip().lower() != bundle_sha256:
                raise Hy2RemoteOperationError("confirm_bundle_sha256_mismatch")
            if str(args.confirm_source_revision).strip().lower() != source_revision:
                raise Hy2RemoteOperationError("confirm_source_revision_mismatch")
            if str(args.confirm_node_code).strip().lower() != node_code:
                raise Hy2RemoteOperationError("confirm_node_code_mismatch")
            if kill_switch != "engaged":
                raise Hy2RemoteOperationError("brain_hy2_kill_switch_not_engaged")

            if args.operation == "install":
                if str(args.confirm_runtime_material_ready).strip() != "RUNTIME_MATERIAL_READY":
                    raise Hy2RemoteOperationError("runtime_material_confirmation_missing")
                _assert_fresh_install_preflight(preflight)
                receipt_id = _release_id(bundle_sha256)
                backup_dir = f"{BACKUP_ROOT}/{receipt_id}"
                stage_dir = f"{STAGE_ROOT}/{receipt_id}"
                backup_ready = False
                try:
                    _stage_bundle(
                        node,
                        stage_dir=stage_dir,
                        manifest=manifest,
                        contents=contents,
                    )
                    _run(
                        node,
                        _backup_command(
                            backup_dir=backup_dir,
                            bundle_sha256=bundle_sha256,
                            node_code=node_code,
                        ),
                        label="receipt_backup",
                    )
                    backup_ready = True
                    _run(
                        node,
                        _install_command(
                            stage_dir=stage_dir,
                            release_dir=release_dir,
                            runtime_material_dir=runtime_material_dir,
                            backup_dir=backup_dir,
                            manifest=manifest,
                        ),
                        label="install_apply",
                        timeout=300,
                    )
                except Exception:
                    if backup_ready:
                        _run(
                            node,
                            _rollback_command(
                                backup_dir=backup_dir,
                                bundle_sha256=bundle_sha256,
                                node_code=node_code,
                                release_dir=release_dir,
                                require_current_release=False,
                            ),
                            label="automatic_rollback",
                            timeout=240,
                        )
                    raise
                finally:
                    _run_allow_failure(node, f"rm -rf -- {_q(stage_dir)}", timeout=90)
                report.update(
                    {
                        "mutation_performed": True,
                        "receipt_id": receipt_id,
                        "service_active": True,
                        "service_enabled": True,
                        "udp_443_listener": True,
                        "automatic_rollback_armed": True,
                    }
                )
            else:
                receipt_id = str(args.receipt_id or "").strip()
                if not SAFE_RECEIPT_RE.fullmatch(receipt_id):
                    raise Hy2RemoteOperationError("receipt_id_invalid")
                backup_dir = f"{BACKUP_ROOT}/{receipt_id}"
                _run(
                    node,
                    _rollback_command(
                        backup_dir=backup_dir,
                        bundle_sha256=bundle_sha256,
                        node_code=node_code,
                        release_dir=release_dir,
                        require_current_release=True,
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
        print(
            f"owned HY2 remote operation failed: {type(exc).__name__}: {str(exc)[:300]}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
