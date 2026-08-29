#!/usr/bin/env python3
"""Guarded PLAN/APPLY/ROLLBACK for the exact candidate.6 RU-origin probe."""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import sys
from typing import Any, Mapping
import zipfile

try:
    import build_ru_origin_probe_bundle as bundle_contract
    from node_access import DEFAULT_PASSWORDS, connect_node
    from node_inventory import DEFAULT_INVENTORY, inventory_ipv4_map
    from ssh_host_keys import DEFAULT_KNOWN_HOSTS, OpenSshConfigSession
except ImportError:  # pragma: no cover - package import for tests
    from . import build_ru_origin_probe_bundle as bundle_contract
    from .node_access import DEFAULT_PASSWORDS, connect_node
    from .node_inventory import DEFAULT_INVENTORY, inventory_ipv4_map
    from .ssh_host_keys import DEFAULT_KNOWN_HOSTS, OpenSshConfigSession


REPORT_SCHEMA = "pokrov-ru-origin-probe-remote-operation-v1"
DEFAULT_NODE_CODE = "mini"
RUNTIME_USER = "pokrov-ru-probe"
CONFIG_ROOT = "/etc/pokrov-ru-probe"
SPOOL_ROOT = "/var/lib/pokrov-ru-probe"
BACKUP_ROOT = "/root/pokrov-ru-probe-backups"
STAGE_ROOT = "/var/tmp/pokrov-ru-probe-staging"
SERVICE_NAMES = (
    "pokrov-ru-probe.service",
    "pokrov-ru-probe-uploader.service",
)
TIMER_NAMES = (
    "pokrov-ru-probe.timer",
    "pokrov-ru-probe-uploader.timer",
)
UNIT_NAMES = (*SERVICE_NAMES, *TIMER_NAMES)
RUNTIME_FILES = {
    "probe.env": (f"{CONFIG_ROOT}/probe.env", "0640"),
    "uploader.env": (f"{CONFIG_ROOT}/uploader.env", "0640"),
    "hmac.key": (f"{CONFIG_ROOT}/hmac.key", "0640"),
    "profiles.json": (f"{CONFIG_ROOT}/profiles.json", "0640"),
}
SAFE_COMPONENT_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,31}\Z")
SAFE_RECEIPT_RE = re.compile(r"[0-9]{8}T[0-9]{6}Z-[0-9]+-[0-9a-f]{12}\Z")
ENV_KEY_RE = re.compile(r"[A-Z][A-Z0-9_]{0,63}\Z")
PROFILE_ID_RE = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}\Z")
SAFE_REMOTE_VALUE_RE = re.compile(r"[A-Za-z0-9_.:-]{1,64}\Z")
SECRET_NAME_RE = re.compile(r"(?:SECRET|PASSWORD|TOKEN|PRIVATE_KEY|HMAC)", re.I)
EXPECTED_ENV = {
    "POKROV_API_BASE_URL": "https://api.pokrov.space",
    "POKROV_KEY_ID": "ru-mini-v1",
    "POKROV_PROBE_HOST_ID": "mini",
}


class RuProbeRemoteOperationError(RuntimeError):
    """Raised when a guarded RU-origin operation cannot prove its contract."""


def _q(value: str) -> str:
    return shlex.quote(str(value))


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_component(value: str, *, label: str) -> str:
    normalized = str(value or "").strip().lower()
    if SAFE_COMPONENT_RE.fullmatch(normalized) is None:
        raise RuProbeRemoteOperationError(f"{label}_invalid")
    return normalized


def _receipt_id(bundle_sha256: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{now}-{os.getpid()}-{bundle_sha256[:12]}"


def _validated_local_bundle(
    raw_path: str | Path,
) -> tuple[Path, dict[str, Any], dict[str, bytes], str]:
    try:
        path = Path(raw_path).resolve(strict=True)
        manifest = bundle_contract.verify_bundle(path)
        with zipfile.ZipFile(path, "r") as archive:
            contents = {
                member: archive.read(member) for member in bundle_contract.SOURCE_MEMBERS
            }
    except (OSError, KeyError, zipfile.BadZipFile, bundle_contract.RuProbeBundleError) as exc:
        raise RuProbeRemoteOperationError("bundle_validation_failed") from exc
    digest = _sha256_file(path)
    if (
        str((manifest.get("source") or {}).get("revision") or "")
        != bundle_contract.EXPECTED_SOURCE_REVISION
        or set(contents) != set(bundle_contract.SOURCE_MEMBERS)
    ):
        raise RuProbeRemoteOperationError("bundle_remote_install_contract_mismatch")
    return path, manifest, contents, digest


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _validate_env_file(value: bytes, *, name: str) -> int:
    if not value or len(value) > 16 * 1024:
        raise RuProbeRemoteOperationError(f"runtime_{name}_size_invalid")
    try:
        text = value.decode("utf-8")
    except UnicodeError as exc:
        raise RuProbeRemoteOperationError(f"runtime_{name}_not_utf8") from exc
    if text.startswith("\ufeff") or "\r" in text or "\x00" in text:
        raise RuProbeRemoteOperationError(f"runtime_{name}_not_canonical")
    keys: set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line or line.startswith("export "):
            raise RuProbeRemoteOperationError(f"runtime_{name}_syntax_invalid")
        key, raw_value = line.split("=", 1)
        if (
            ENV_KEY_RE.fullmatch(key) is None
            or key in keys
            or SECRET_NAME_RE.search(key) is not None
            or not raw_value
            or len(raw_value) > 2048
            or raw_value != raw_value.strip()
        ):
            raise RuProbeRemoteOperationError(f"runtime_{name}_contract_invalid")
        keys.add(key)
    if keys != set(EXPECTED_ENV):
        raise RuProbeRemoteOperationError(f"runtime_{name}_key_set_invalid")
    for key, expected in EXPECTED_ENV.items():
        marker = f"{key}={expected}"
        if marker not in text.splitlines():
            raise RuProbeRemoteOperationError(f"runtime_{name}_value_invalid")
    return len(keys)


def _validate_profile_registry(value: bytes) -> int:
    if not value or len(value) > 64 * 1024:
        raise RuProbeRemoteOperationError("runtime_profiles_size_invalid")
    try:
        payload = json.loads(
            value.decode("utf-8"), object_pairs_hook=_unique_json_object
        )
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise RuProbeRemoteOperationError("runtime_profiles_invalid") from exc
    if not isinstance(payload, dict):
        raise RuProbeRemoteOperationError("runtime_profiles_invalid")
    profiles = (
        payload.get("profiles")
        if set(payload) == {"profiles"} and isinstance(payload.get("profiles"), dict)
        else payload
    )
    if not isinstance(profiles, dict) or not 1 <= len(profiles) <= 128:
        raise RuProbeRemoteOperationError("runtime_profiles_invalid")
    forbidden = ("\x00", "\n", "\r", ";", "&&", "||", "`", "$(", "://")
    for profile_id, entry in profiles.items():
        if (
            not isinstance(profile_id, str)
            or PROFILE_ID_RE.fullmatch(profile_id) is None
            or not isinstance(entry, dict)
            or set(entry) != {"executable", "argv"}
        ):
            raise RuProbeRemoteOperationError("runtime_profiles_invalid")
        executable = entry.get("executable")
        argv = entry.get("argv")
        if (
            not isinstance(executable, str)
            or not PurePosixPath(executable).is_absolute()
            or len(executable) > 512
            or not isinstance(argv, list)
            or len(argv) > 32
        ):
            raise RuProbeRemoteOperationError("runtime_profiles_invalid")
        for argument in argv:
            if (
                not isinstance(argument, str)
                or not argument
                or len(argument) > 512
                or any(token in argument for token in forbidden)
                or SECRET_NAME_RE.search(argument) is not None
            ):
                raise RuProbeRemoteOperationError("runtime_profiles_invalid")
    return len(profiles)


def _validated_runtime_material(
    raw_dir: str | Path,
) -> tuple[Path, dict[str, bytes], dict[str, Any]]:
    unresolved_root = Path(raw_dir)
    if unresolved_root.is_symlink():
        raise RuProbeRemoteOperationError("runtime_material_dir_invalid")
    try:
        root = unresolved_root.resolve(strict=True)
    except OSError as exc:
        raise RuProbeRemoteOperationError("runtime_material_dir_missing") from exc
    if not root.is_dir() or root.is_symlink():
        raise RuProbeRemoteOperationError("runtime_material_dir_invalid")
    names = {item.name for item in root.iterdir()}
    if names != set(RUNTIME_FILES):
        raise RuProbeRemoteOperationError("runtime_material_file_set_invalid")
    values: dict[str, bytes] = {}
    for name in RUNTIME_FILES:
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise RuProbeRemoteOperationError(f"runtime_{name}_not_regular")
        values[name] = path.read_bytes()
    for name in ("probe.env", "uploader.env"):
        values[name] = values[name].replace(b"\r\n", b"\n")
    probe_keys = _validate_env_file(values["probe.env"], name="probe_env")
    uploader_keys = _validate_env_file(values["uploader.env"], name="uploader_env")
    secret_size = len(values["hmac.key"])
    if not 16 <= secret_size <= 512 or b"\x00" in values["hmac.key"]:
        raise RuProbeRemoteOperationError("runtime_hmac_key_invalid")
    profile_count = _validate_profile_registry(values["profiles.json"])
    summary = {
        "supplied": True,
        "file_count": len(values),
        "environment_key_count": probe_keys + uploader_keys,
        "hmac_length_valid": True,
        "profile_count": profile_count,
        "raw_runtime_material_returned": False,
        "runtime_material_hashes_returned": False,
    }
    return root, values, summary


def _run(session: Any, command: str, *, label: str, timeout: int = 180) -> str:
    try:
        if isinstance(session, OpenSshConfigSession):
            result = session.run(command, timeout=timeout)
            code = int(result.returncode)
            output = str(result.stdout or "").strip()
        else:
            _stdin, stdout, stderr = session.exec_command(command, timeout=timeout)
            code = int(stdout.channel.recv_exit_status())
            output = stdout.read().decode("utf-8", errors="replace").strip()
            stderr.read()
    except Exception as exc:
        raise RuProbeRemoteOperationError(f"{label}_transport_failed") from exc
    if code != 0:
        raise RuProbeRemoteOperationError(f"{label}_failed_exit_{code}")
    return output


def _run_allow_failure(session: Any, command: str, *, timeout: int = 180) -> None:
    try:
        _run(session, command, label="best_effort", timeout=timeout)
    except Exception:
        return


def _as_root(command: str, *, use_sudo: bool) -> str:
    return f"sudo -n sh -c {_q(command)}" if use_sudo else command


def _remote_write(session: Any, path: str, value: bytes, mode: int) -> None:
    temporary = f"{path}.tmp-{os.getpid()}"
    if isinstance(session, OpenSshConfigSession):
        helper = (
            "import base64,os,sys;"
            "p=sys.argv[1];t=sys.argv[2];m=int(sys.argv[3],8);"
            "v=base64.b64decode(sys.stdin.buffer.read(),validate=True);"
            "f=open(t,'wb');f.write(v);f.flush();os.fsync(f.fileno());f.close();"
            "os.chmod(t,m);os.replace(t,p)"
        )
        command = (
            f"python3 -c {_q(helper)} {_q(path)} {_q(temporary)} {_q(format(mode, '04o'))}"
        )
        try:
            result = session.run(
                command,
                timeout=180,
                input_text=base64.b64encode(value).decode("ascii"),
            )
        except Exception as exc:
            raise RuProbeRemoteOperationError("stage_write_transport_failed") from exc
        if result.returncode != 0:
            raise RuProbeRemoteOperationError("stage_write_failed")
        return
    sftp = session.open_sftp()
    try:
        handle = sftp.file(temporary, "wb")
        try:
            handle.write(value)
            handle.flush()
        finally:
            handle.close()
        sftp.chmod(temporary, mode)
        sftp.posix_rename(temporary, path)
    except Exception as exc:
        try:
            sftp.remove(temporary)
        except Exception:
            pass
        raise RuProbeRemoteOperationError("stage_write_failed") from exc
    finally:
        sftp.close()


def _parse_probe(raw: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in raw.splitlines():
        if "=" not in line:
            raise RuProbeRemoteOperationError("remote_preflight_shape_invalid")
        key, value = line.split("=", 1)
        if (
            not re.fullmatch(r"[a-z0-9_]+", key)
            or SAFE_REMOTE_VALUE_RE.fullmatch(value) is None
            or key in parsed
        ):
            raise RuProbeRemoteOperationError("remote_preflight_value_invalid")
        parsed[key] = value
    return parsed


def _preflight_command() -> str:
    targets = [
        *(str(row["install_path"]) for row in bundle_contract.SOURCE_MEMBERS.values()),
        *(path for path, _mode in RUNTIME_FILES.values()),
    ]
    lines = [
        "set -u",
        "emit_bool() { if eval \"$2\"; then printf '%s=yes\\n' \"$1\"; else printf '%s=no\\n' \"$1\"; fi; }",
        "emit_bool root 'test \"$(id -u)\" = 0'",
        "emit_bool sudo_nopasswd 'command -v sudo >/dev/null 2>&1 && sudo -n true >/dev/null 2>&1'",
        "emit_bool systemd 'command -v systemctl >/dev/null 2>&1'",
        "emit_bool python3 'command -v python3 >/dev/null 2>&1'",
        "emit_bool sha256sum 'command -v sha256sum >/dev/null 2>&1'",
        "emit_bool install 'command -v install >/dev/null 2>&1'",
        "emit_bool runuser 'command -v runuser >/dev/null 2>&1'",
        f"emit_bool user_present 'id -u {_q(RUNTIME_USER)} >/dev/null 2>&1'",
        f"emit_bool group_present 'getent group {_q(RUNTIME_USER)} >/dev/null 2>&1'",
        f"emit_bool spool_present 'test -d {_q(SPOOL_ROOT)} && ! test -L {_q(SPOOL_ROOT)}'",
        f"emit_bool spool_private \"test -d {_q(SPOOL_ROOT)} && ! find {_q(SPOOL_ROOT)} -maxdepth 0 -perm /077 -print -quit 2>/dev/null | grep -q .\"",
        "installed_target_count=0",
    ]
    for path in targets:
        lines.append(
            f"if test -e {_q(path)} || test -L {_q(path)}; then installed_target_count=$((installed_target_count+1)); fi"
        )
    lines.append("printf 'installed_target_count=%s\\n' \"$installed_target_count\"")
    for unit in UNIT_NAMES:
        key = unit.replace("-", "_").replace(".", "_")
        lines.extend(
            [
                f"state=$(systemctl is-active {_q(unit)} 2>/dev/null || true)",
                "case \"$state\" in '') state=unknown ;; active|inactive|failed|activating|deactivating|unknown) ;; *) state=other ;; esac",
                f"printf '{key}_active=%s\\n' \"${{state:-unknown}}\"",
                f"state=$(systemctl is-enabled {_q(unit)} 2>/dev/null || true)",
                "case \"$state\" in '') state=not-found ;; enabled|disabled|static|indirect|masked|not-found) ;; *) state=other ;; esac",
                f"printf '{key}_enabled=%s\\n' \"${{state:-not-found}}\"",
            ]
        )
    for state in ("pending", "blocked", "quarantine", "archive"):
        lines.append(
            f"count=$(find {_q(SPOOL_ROOT + '/' + state)} -maxdepth 1 -type f -name '*.json' 2>/dev/null | wc -l | tr -d ' '); case \"$count\" in ''|*[!0-9]*) count=0 ;; esac; printf 'spool_{state}_count=%s\\n' \"$count\""
        )
    return "\n".join(lines)


def _remote_preflight(session: Any) -> dict[str, Any]:
    values = _parse_probe(
        _run(session, _preflight_command(), label="remote_preflight", timeout=90)
    )
    bool_keys = {
        "root", "sudo_nopasswd", "systemd", "python3", "sha256sum", "install", "runuser",
        "user_present", "group_present", "spool_present", "spool_private",
    }
    state_keys = {
        unit.replace("-", "_").replace(".", "_") + suffix
        for unit in UNIT_NAMES
        for suffix in ("_active", "_enabled")
    }
    count_keys = {
        "installed_target_count", "spool_pending_count", "spool_blocked_count",
        "spool_quarantine_count", "spool_archive_count",
    }
    if set(values) != bool_keys | state_keys | count_keys:
        raise RuProbeRemoteOperationError("remote_preflight_fields_invalid")
    if any(values[key] not in {"yes", "no"} for key in bool_keys):
        raise RuProbeRemoteOperationError("remote_preflight_boolean_invalid")
    if any(not values[key].isdigit() for key in count_keys):
        raise RuProbeRemoteOperationError("remote_preflight_count_invalid")
    units = {
        unit: {
            "active": values[unit.replace("-", "_").replace(".", "_") + "_active"],
            "enabled": values[unit.replace("-", "_").replace(".", "_") + "_enabled"],
        }
        for unit in UNIT_NAMES
    }
    return {
        "root": values["root"] == "yes",
        "sudo_nopasswd": values["sudo_nopasswd"] == "yes",
        "privileged": values["root"] == "yes" or values["sudo_nopasswd"] == "yes",
        "required_tools": all(
            values[key] == "yes"
            for key in ("systemd", "python3", "sha256sum", "install", "runuser")
        ),
        "runtime_user_present": values["user_present"] == "yes",
        "runtime_group_present": values["group_present"] == "yes",
        "spool_present": values["spool_present"] == "yes",
        "spool_private": values["spool_private"] == "yes",
        "installed_target_count": int(values["installed_target_count"]),
        "unit_states": units,
        "spool_counts": {
            state: int(values[f"spool_{state}_count"])
            for state in ("pending", "blocked", "quarantine", "archive")
        },
        "raw_paths_returned": False,
        "raw_runtime_material_returned": False,
    }


def _assert_fresh_install_preflight(preflight: Mapping[str, Any]) -> None:
    if not preflight.get("privileged") or not preflight.get("required_tools"):
        raise RuProbeRemoteOperationError("install_host_requirements_not_met")
    if int(preflight.get("installed_target_count") or 0) != 0:
        raise RuProbeRemoteOperationError("install_targets_not_empty")
    unit_states = preflight.get("unit_states")
    if not isinstance(unit_states, Mapping):
        raise RuProbeRemoteOperationError("install_unit_state_missing")
    for state in unit_states.values():
        if not isinstance(state, Mapping):
            raise RuProbeRemoteOperationError("install_unit_state_invalid")
        if state.get("active") not in {"inactive", "failed", "unknown"}:
            raise RuProbeRemoteOperationError("install_unit_already_active")
        if state.get("enabled") not in {"disabled", "not-found", "masked"}:
            raise RuProbeRemoteOperationError("install_unit_already_enabled")
    if preflight.get("spool_present") and not preflight.get("spool_private"):
        raise RuProbeRemoteOperationError("install_existing_spool_not_private")


def _stage_payload(
    session: Any,
    *,
    stage_dir: str,
    manifest: Mapping[str, Any],
    contents: Mapping[str, bytes],
    runtime_material: Mapping[str, bytes],
) -> None:
    directories = {
        str(PurePosixPath(member).parent)
        for member in contents
        if str(PurePosixPath(member).parent) != "."
    }
    _run(
        session,
        "set -e; test ! -e " + _q(stage_dir) + "; install -d -m 0700 "
        + " ".join(
            _q(f"{stage_dir}/{directory}")
            for directory in (".", *sorted(directories), "runtime")
        ),
        label="stage_prepare",
    )
    for member, value in contents.items():
        mode = int(str(bundle_contract.SOURCE_MEMBERS[member]["mode"]), 8)
        _remote_write(session, f"{stage_dir}/{member}", value, mode)
    for name, value in runtime_material.items():
        _remote_write(session, f"{stage_dir}/runtime/{name}", value, 0o600)
    checks = ["set -e"]
    declared = manifest.get("members") or {}
    for member in sorted(contents):
        record = declared[member]
        path = f"{stage_dir}/{member}"
        checks.extend(
            [
                f"test \"$(stat -c %s {_q(path)})\" = {_q(str(record['size_bytes']))}",
                f"test \"$(sha256sum {_q(path)} | awk '{{print $1}}')\" = {_q(str(record['sha256']))}",
            ]
        )
    for name, value in runtime_material.items():
        path = f"{stage_dir}/runtime/{name}"
        checks.extend(
            [
                f"test \"$(stat -c %s {_q(path)})\" = {_q(str(len(value)))}",
                f"test \"$(sha256sum {_q(path)} | awk '{{print $1}}')\" = {_q(_sha256(value))}",
            ]
        )
    _run(session, "\n".join(checks), label="stage_digest_readback", timeout=240)


def _all_targets() -> list[tuple[str, str]]:
    targets = [
        (f"source-{index:02d}", str(contract["install_path"]))
        for index, (_member, contract) in enumerate(
            sorted(bundle_contract.SOURCE_MEMBERS.items())
        )
    ]
    targets.extend(
        (f"runtime-{index:02d}", path)
        for index, (_name, (path, _mode)) in enumerate(sorted(RUNTIME_FILES.items()))
    )
    return targets


def _backup_command(
    *, backup_dir: str, bundle_sha256: str, source_revision: str, node_code: str
) -> str:
    lines = [
        "set -e",
        f"install -d -m 0700 {_q(backup_dir + '/files')}",
        f"printf '%s\\n' {_q(bundle_sha256)} > {_q(backup_dir + '/bundle-sha256')}",
        f"printf '%s\\n' {_q(source_revision)} > {_q(backup_dir + '/source-revision')}",
        f"printf '%s\\n' {_q(node_code)} > {_q(backup_dir + '/node-code')}",
        f"if id -u {_q(RUNTIME_USER)} >/dev/null 2>&1; then printf 'present\\n' > {_q(backup_dir + '/user-state')}; else printf 'missing\\n' > {_q(backup_dir + '/user-state')}; fi",
        f"if getent group {_q(RUNTIME_USER)} >/dev/null 2>&1; then printf 'present\\n' > {_q(backup_dir + '/group-state')}; else printf 'missing\\n' > {_q(backup_dir + '/group-state')}; fi",
    ]
    for unit in UNIT_NAMES:
        key = unit.replace(".", "-")
        lines.extend(
            [
                f"systemctl is-active {_q(unit)} > {_q(backup_dir + '/' + key + '-active')} 2>/dev/null || printf 'inactive\\n' > {_q(backup_dir + '/' + key + '-active')}",
                f"systemctl is-enabled {_q(unit)} > {_q(backup_dir + '/' + key + '-enabled')} 2>/dev/null || printf 'disabled\\n' > {_q(backup_dir + '/' + key + '-enabled')}",
            ]
        )
    for name, target in _all_targets():
        saved = f"{backup_dir}/files/{name}"
        state = f"{backup_dir}/files/{name}-state"
        lines.append(
            f"if test -e {_q(target)} || test -L {_q(target)}; then cp -a {_q(target)} {_q(saved)}; printf 'present\\n' > {_q(state)}; else printf 'missing\\n' > {_q(state)}; fi"
        )
    lines.extend(
        [
            f"printf 'prepared\\n' > {_q(backup_dir + '/receipt-state')}",
            f"chmod -R go-rwx {_q(backup_dir)}",
        ]
    )
    return "\n".join(lines)


def _profile_remote_validator(path: str) -> str:
    helper = """
import json,os,sys
try:
    with open(sys.argv[1], encoding="utf-8") as handle:
        payload=json.load(handle)
    profiles=payload.get("profiles") if isinstance(payload,dict) and set(payload)=={"profiles"} else payload
    ok=isinstance(profiles,dict) and 1 <= len(profiles) <= 128
    if ok:
        for entry in profiles.values():
            if not isinstance(entry,dict) or set(entry)!={"executable","argv"}:
                ok=False;break
            executable=entry.get("executable")
            argv=entry.get("argv")
            if not isinstance(executable,str) or not os.path.isabs(executable) or not os.path.isfile(executable) or not os.access(executable,os.X_OK):
                ok=False;break
            if not isinstance(argv,list) or len(argv)>32 or any(not isinstance(v,str) or not v or len(v)>512 or "\\x00" in v for v in argv):
                ok=False;break
except Exception:
    ok=False
raise SystemExit(0 if ok else 1)
""".strip()
    encoded = base64.b64encode(helper.encode("utf-8")).decode("ascii")
    launcher = f"import base64;exec(base64.b64decode('{encoded}'))"
    return f"python3 -c {_q(launcher)} {_q(path)}"


def _install_command(
    *, stage_dir: str, backup_dir: str, manifest: Mapping[str, Any]
) -> str:
    declared = manifest.get("members") or {}
    lines = [
        "set -e",
        f"getent group {_q(RUNTIME_USER)} >/dev/null 2>&1 || groupadd --system {_q(RUNTIME_USER)}",
        f"id -u {_q(RUNTIME_USER)} >/dev/null 2>&1 || useradd --system --gid {_q(RUNTIME_USER)} --home-dir /nonexistent --shell /usr/sbin/nologin {_q(RUNTIME_USER)}",
        "install -d -o root -g root -m 0755 /opt/pokrov /opt/pokrov/scripts /opt/pokrov/portal_bot",
        f"install -d -o root -g {_q(RUNTIME_USER)} -m 0750 {_q(CONFIG_ROOT)}",
        f"install -d -o {_q(RUNTIME_USER)} -g {_q(RUNTIME_USER)} -m 0700 {_q(SPOOL_ROOT)}",
    ]
    for state in ("pending", "blocked", "quarantine", "archive"):
        lines.append(
            f"install -d -o {_q(RUNTIME_USER)} -g {_q(RUNTIME_USER)} -m 0700 {_q(SPOOL_ROOT + '/' + state)}"
        )
    for member, contract in sorted(bundle_contract.SOURCE_MEMBERS.items()):
        source = f"{stage_dir}/{member}"
        target = str(contract["install_path"])
        mode = str(contract["mode"])
        lines.extend(
            [
                f"install -D -o root -g root -m {mode} {_q(source)} {_q(target)}",
                f"test \"$(sha256sum {_q(target)} | awk '{{print $1}}')\" = {_q(str(declared[member]['sha256']))}",
            ]
        )
    for name, (target, mode) in sorted(RUNTIME_FILES.items()):
        lines.append(
            f"install -o root -g {_q(RUNTIME_USER)} -m {mode} {_q(stage_dir + '/runtime/' + name)} {_q(target)}"
        )
    python_members = [
        str(contract["install_path"])
        for member, contract in bundle_contract.SOURCE_MEMBERS.items()
        if member.endswith(".py")
    ]
    compile_helper = "import ast,sys;[ast.parse(open(p,encoding='utf-8').read(),filename=p) for p in sys.argv[1:]]"
    lines.extend(
        [
            "systemctl daemon-reload",
            "if command -v systemd-analyze >/dev/null 2>&1; then systemd-analyze verify "
            + " ".join(_q(unit) for unit in UNIT_NAMES)
            + " >/dev/null 2>&1; fi",
            "PYTHONDONTWRITEBYTECODE=1 python3 -c " + _q(compile_helper) + " "
            + " ".join(_q(path) for path in python_members),
            f"test \"$(stat -c %a {_q(CONFIG_ROOT + '/hmac.key')})\" = 640",
            f"test \"$(stat -c %U {_q(CONFIG_ROOT + '/hmac.key')})\" = root",
            f"test \"$(stat -c %G {_q(CONFIG_ROOT + '/hmac.key')})\" = {_q(RUNTIME_USER)}",
            f"test \"$(stat -c %a {_q(SPOOL_ROOT)})\" = 700",
            _profile_remote_validator(f"{CONFIG_ROOT}/profiles.json"),
            f"runuser -u {_q(RUNTIME_USER)} -- env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B /opt/pokrov/scripts/ru_probe_runner.py --help >/dev/null",
            f"runuser -u {_q(RUNTIME_USER)} -- env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B /opt/pokrov/scripts/ru_probe_uploader.py --help >/dev/null",
        ]
    )
    for timer in TIMER_NAMES:
        lines.append(f"systemctl enable {_q(timer)} >/dev/null")
    for timer in TIMER_NAMES:
        lines.extend(
            [
                f"systemctl start {_q(timer)}",
                f"test \"$(systemctl is-active {_q(timer)})\" = active",
                f"test \"$(systemctl is-enabled {_q(timer)})\" = enabled",
            ]
        )
    lines.append(f"printf 'installed\\n' > {_q(backup_dir + '/receipt-state')}")
    return "\n".join(lines)


def _restore_target_lines(*, backup_dir: str, name: str, target: str) -> list[str]:
    saved = f"{backup_dir}/files/{name}"
    state = f"{backup_dir}/files/{name}-state"
    return [
        f"rm -f -- {_q(target)}",
        f"if grep -qx present {_q(state)}; then cp -a {_q(saved)} {_q(target)}; fi",
    ]


def _rollback_command(
    *, backup_dir: str, bundle_sha256: str, source_revision: str, node_code: str
) -> str:
    lines = [
        "set -e",
        f"test -d {_q(backup_dir)}",
        f"test \"$(stat -c %u {_q(backup_dir)})\" = 0",
        f"grep -qx {_q(bundle_sha256)} {_q(backup_dir + '/bundle-sha256')}",
        f"grep -qx {_q(source_revision)} {_q(backup_dir + '/source-revision')}",
        f"grep -qx {_q(node_code)} {_q(backup_dir + '/node-code')}",
    ]
    for timer in TIMER_NAMES:
        lines.append(f"systemctl disable --now {_q(timer)} >/dev/null 2>&1 || true")
    for service in SERVICE_NAMES:
        lines.append(f"systemctl stop {_q(service)} >/dev/null 2>&1 || true")
    for name, target in _all_targets():
        lines.extend(_restore_target_lines(backup_dir=backup_dir, name=name, target=target))
    lines.extend(
        [
            "systemctl daemon-reload",
            # User/group stay so preserved spool evidence never becomes orphaned.
            f"if test -e {_q(SPOOL_ROOT)}; then test -d {_q(SPOOL_ROOT)} && ! test -L {_q(SPOOL_ROOT)}; fi",
        ]
    )
    for timer in TIMER_NAMES:
        key = timer.replace(".", "-")
        lines.extend(
            [
                f"if grep -qx enabled {_q(backup_dir + '/' + key + '-enabled')}; then systemctl enable {_q(timer)} >/dev/null; fi",
                f"if grep -qx active {_q(backup_dir + '/' + key + '-active')}; then systemctl start {_q(timer)}; fi",
            ]
        )
    lines.append(f"printf 'rolled_back\\n' > {_q(backup_dir + '/receipt-state')}")
    return "\n".join(lines)


def _cleanup_stage_command(stage_dir: str) -> str:
    if not stage_dir.startswith(STAGE_ROOT + "/"):
        raise RuProbeRemoteOperationError("stage_path_invalid")
    return (
        "set -e; stage=" + _q(stage_dir) + "; case \"$stage\" in "
        + _q(STAGE_ROOT + "/") + "*) ;; *) exit 91 ;; esac; test \"$stage\" != "
        + _q(STAGE_ROOT) + "; rm -rf -- \"$stage\""
    )


def _assert_apply_confirmations(
    args: argparse.Namespace,
    *,
    bundle_sha256: str,
    source_revision: str,
    node_code: str,
) -> None:
    if str(args.confirm_external_mutation).strip() != "AUTHORIZED_RU_HOST_MUTATION":
        raise RuProbeRemoteOperationError("external_mutation_confirmation_missing")
    if str(args.confirm_bundle_sha256).strip().lower() != bundle_sha256:
        raise RuProbeRemoteOperationError("confirm_bundle_sha256_mismatch")
    if str(args.confirm_source_revision).strip().lower() != source_revision:
        raise RuProbeRemoteOperationError("confirm_source_revision_mismatch")
    if str(args.confirm_node_code).strip().lower() != node_code:
        raise RuProbeRemoteOperationError("confirm_node_code_mismatch")
    if str(args.confirm_spool_preservation).strip() != "PRESERVE_RU_PROBE_SPOOL":
        raise RuProbeRemoteOperationError("spool_preservation_confirmation_missing")
    if args.operation == "install":
        if str(args.confirm_runtime_material_ready).strip() != "RUNTIME_MATERIAL_READY":
            raise RuProbeRemoteOperationError("runtime_material_confirmation_missing")
        if str(args.confirm_timer_activation).strip() != "ACTIVATE_RU_PROBE_TIMERS":
            raise RuProbeRemoteOperationError("timer_activation_confirmation_missing")


def _connect(args: argparse.Namespace, node_code: str) -> tuple[Any, str]:
    try:
        if args.ssh_config_alias:
            return (
                OpenSshConfigSession(
                    alias=args.ssh_config_alias,
                    config_path=Path(args.ssh_config).expanduser() if args.ssh_config else None,
                ),
                "ssh_config",
            )
        inventory = inventory_ipv4_map(Path(args.inventory))
        host = str(args.node_host or "").strip() or inventory.get(node_code, "")
        if not host:
            raise RuProbeRemoteOperationError("node_inventory_entry_missing")
        known_hosts = Path(args.known_hosts).resolve(strict=True)
        if not known_hosts.is_file():
            raise RuProbeRemoteOperationError("known_hosts_not_file")
        os.environ["POKROV_SSH_KNOWN_HOSTS"] = str(known_hosts)
        os.environ["POKROV_SSH_TRUST_ON_FIRST_USE"] = "0"
        session, auth = connect_node(
            code=node_code,
            host=host,
            user=args.ssh_user,
            port=int(args.ssh_port),
            passwords_path=Path(args.passwords),
            key_dir=Path(args.passwords).parent,
        )
        return session, "key" if str(auth).startswith("key") else "password"
    except RuProbeRemoteOperationError:
        raise
    except Exception as exc:
        raise RuProbeRemoteOperationError("node_ssh_connect_failed") from exc


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
    parser.add_argument("--node-code", default=DEFAULT_NODE_CODE)
    parser.add_argument("--node-host", default="")
    parser.add_argument("--inventory", default=str(DEFAULT_INVENTORY))
    parser.add_argument("--known-hosts", default=str(DEFAULT_KNOWN_HOSTS))
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--ssh-config-alias", default="")
    parser.add_argument("--ssh-config", default="")
    parser.add_argument("--operation", choices=("install", "rollback"), default="install")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--runtime-material-dir", default="")
    parser.add_argument("--receipt-id", default="")
    parser.add_argument("--confirm-external-mutation", default="")
    parser.add_argument("--confirm-bundle-sha256", default="")
    parser.add_argument("--confirm-source-revision", default="")
    parser.add_argument("--confirm-node-code", default="")
    parser.add_argument("--confirm-runtime-material-ready", default="")
    parser.add_argument("--confirm-spool-preservation", default="")
    parser.add_argument("--confirm-timer-activation", default="")
    parser.add_argument("--json-out", default="")
    return parser


def main() -> int:
    args = _parser().parse_args()
    session: Any | None = None
    try:
        node_code = _safe_component(args.node_code, label="node_code")
        bundle_path, manifest, contents, bundle_sha256 = _validated_local_bundle(args.bundle)
        source_revision = str((manifest.get("source") or {}).get("revision") or "")
        session, auth_method = _connect(args, node_code)
        preflight = _remote_preflight(session)
        runtime_summary: dict[str, Any] = {
            "supplied": False,
            "raw_runtime_material_returned": False,
            "runtime_material_hashes_returned": False,
        }
        runtime_material: dict[str, bytes] = {}
        if str(args.runtime_material_dir or "").strip():
            _runtime_root, runtime_material, runtime_summary = _validated_runtime_material(
                args.runtime_material_dir
            )
        report: dict[str, Any] = {
            "schema_version": REPORT_SCHEMA,
            "mode": "APPLY" if args.apply else "PLAN",
            "operation": args.operation,
            "node_code": node_code,
            "bundle_sha256": bundle_sha256,
            "bundle_size_bytes": bundle_path.stat().st_size,
            "source_revision": source_revision,
            "auth_method": auth_method,
            "preflight": preflight,
            "runtime_material": runtime_summary,
            "mutation_performed": False,
            "raw_host_returned": False,
            "raw_runtime_material_returned": False,
            "manual_runner_uploader_heartbeat_admin_readback": "NOT_RUN",
            "ru_origin_verdict": "MANUAL_OWNER_TEST",
        }
        if not args.apply:
            report["plan"] = bundle_contract.plan_bundle(
                path=bundle_path, operation=args.operation
            )
            _write_report(report, args.json_out)
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 0

        _assert_apply_confirmations(
            args,
            bundle_sha256=bundle_sha256,
            source_revision=source_revision,
            node_code=node_code,
        )
        if args.operation == "install":
            if not runtime_material:
                raise RuProbeRemoteOperationError("runtime_material_not_supplied")
            _assert_fresh_install_preflight(preflight)
            use_sudo = not bool(preflight.get("root"))
            receipt_id = _receipt_id(bundle_sha256)
            backup_dir = f"{BACKUP_ROOT}/{receipt_id}"
            stage_dir = f"{STAGE_ROOT}/{receipt_id}"
            backup_ready = False
            try:
                _stage_payload(
                    session,
                    stage_dir=stage_dir,
                    manifest=manifest,
                    contents=contents,
                    runtime_material=runtime_material,
                )
                _run(
                    session,
                    _as_root(
                        _backup_command(
                            backup_dir=backup_dir,
                            bundle_sha256=bundle_sha256,
                            source_revision=source_revision,
                            node_code=node_code,
                        ),
                        use_sudo=use_sudo,
                    ),
                    label="receipt_backup",
                )
                backup_ready = True
                _run(
                    session,
                    _as_root(
                        _install_command(
                            stage_dir=stage_dir,
                            backup_dir=backup_dir,
                            manifest=manifest,
                        ),
                        use_sudo=use_sudo,
                    ),
                    label="install_apply",
                    timeout=360,
                )
            except Exception:
                if backup_ready:
                    _run(
                        session,
                        _as_root(
                            _rollback_command(
                                backup_dir=backup_dir,
                                bundle_sha256=bundle_sha256,
                                source_revision=source_revision,
                                node_code=node_code,
                            ),
                            use_sudo=use_sudo,
                        ),
                        label="automatic_rollback",
                        timeout=300,
                    )
                raise
            finally:
                _run_allow_failure(session, _cleanup_stage_command(stage_dir), timeout=120)
            report.update(
                {
                    "mutation_performed": True,
                    "receipt_id": receipt_id,
                    "timers_enabled": True,
                    "timers_active": True,
                    "spool_preserved": True,
                    "automatic_rollback_armed": True,
                }
            )
        else:
            receipt_id = str(args.receipt_id or "").strip()
            if SAFE_RECEIPT_RE.fullmatch(receipt_id) is None:
                raise RuProbeRemoteOperationError("receipt_id_invalid")
            if not preflight.get("privileged"):
                raise RuProbeRemoteOperationError("rollback_host_privilege_unavailable")
            _run(
                session,
                _as_root(
                    _rollback_command(
                        backup_dir=f"{BACKUP_ROOT}/{receipt_id}",
                        bundle_sha256=bundle_sha256,
                        source_revision=source_revision,
                        node_code=node_code,
                    ),
                    use_sudo=not bool(preflight.get("root")),
                ),
                label="explicit_rollback",
                timeout=300,
            )
            report.update(
                {
                    "mutation_performed": True,
                    "receipt_id": receipt_id,
                    "rollback_completed": True,
                    "spool_preserved": True,
                    "runtime_user_retained_for_spool": True,
                }
            )
        _write_report(report, args.json_out)
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except RuProbeRemoteOperationError as exc:
        print(f"RU-origin remote operation failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"RU-origin remote operation failed: {type(exc).__name__}", file=sys.stderr)
        return 1
    finally:
        if session is not None:
            session.close()


if __name__ == "__main__":
    raise SystemExit(main())
