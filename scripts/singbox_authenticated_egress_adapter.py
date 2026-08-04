#!/usr/bin/env python3
"""Authenticated VLESS/REALITY egress adapter backed by sing-box.

The CLI reads one bounded JSON request from stdin and writes one bounded JSON
response to stdout. Runtime credentials remain in a protected owner-managed
store and are written only to an ephemeral sing-box configuration.
"""

from __future__ import annotations

import ipaddress
import json
import os
import re
import secrets
import shutil
import signal
import socket
import ssl
import stat
import subprocess
import sys
import tempfile
import threading
import time
import uuid as uuid_module
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO, Callable, Mapping


DEFAULT_CONFIG_PATH = Path("/etc/pokrov/authenticated-egress-adapter.json")
MAX_REQUEST_BYTES = 16 * 1024
MAX_RUNTIME_CONFIG_BYTES = 64 * 1024
MAX_CREDENTIAL_STORE_BYTES = 128 * 1024
MAX_HTTP_HEADER_BYTES = 16 * 1024
MAX_HTTP_BODY_BYTES = 8 * 1024
MAX_PROFILES = 128
MAX_PORT_ATTEMPTS = 3
_UNIX_SOCKS_NAME = "authenticated-proxy.sock"

_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_HEADER_NAME_RE = re.compile(r"^[A-Za-z0-9!#$%&'*+.^_`|~-]{1,64}$")
_PUBLIC_KEY_RE = re.compile(r"^[A-Za-z0-9_-]{43}$")
_SHORT_ID_RE = re.compile(r"^[0-9a-f]{2,16}$")
_FINGERPRINTS = frozenset({"chrome", "edge", "firefox", "safari", "ios", "android", "random", "randomized"})
_REQUEST_FIELDS = {"schema_version", "node_code", "host", "port", "profile_id"}
_RESPONSE_FIELDS = {"schema_version", "profile_id", "status", "classification", "detail_code"}
_RUNTIME_FIELDS = {"schema_version", "core_path", "credential_store_path", "probe", "timeouts"}
_PROBE_FIELDS = {
    "hostname",
    "port",
    "path",
    "expected_status",
    "marker_header_name",
    "marker_header_value",
}
_TIMEOUT_FIELDS = {"total_seconds", "core_start_seconds", "connect_seconds", "io_seconds", "shutdown_seconds"}
_STORE_FIELDS = {"schema_version", "profiles"}
_PROFILE_FIELDS = {"node_code", "endpoint", "uuid", "flow", "reality"}
_ENDPOINT_FIELDS = {"host", "port"}
_REALITY_FIELDS = {"server_name", "public_key", "short_id", "fingerprint"}


class AdapterValidationError(ValueError):
    """Raised for invalid bounded adapter material without including values."""


@dataclass(frozen=True)
class ProbeTarget:
    hostname: str
    port: int
    path: str
    expected_status: int
    marker_header_name: str
    marker_header_value: str


@dataclass(frozen=True)
class Timeouts:
    total_seconds: float
    core_start_seconds: float
    connect_seconds: float
    io_seconds: float
    shutdown_seconds: float


@dataclass(frozen=True)
class RuntimeConfig:
    core_path: Path
    credential_store_path: Path
    probe: ProbeTarget
    timeouts: Timeouts


@dataclass(frozen=True)
class CanaryCredential:
    profile_id: str
    node_code: str
    host: str
    port: int
    uuid: str = field(repr=False)
    flow: str
    server_name: str
    public_key: str = field(repr=False)
    short_id: str = field(repr=False)
    fingerprint: str


@dataclass
class _OpenedPosixFile:
    fd: int
    initial_stat: os.stat_result
    directory_fds: list[int]
    directory_components: tuple[str, ...]
    filename: str


def _strict_json_loads(raw: bytes) -> object:
    def _object_from_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise AdapterValidationError("duplicate_json_key")
            result[key] = value
        return result

    def _reject_constant(_value: str) -> object:
        raise AdapterValidationError("non_finite_json_number")

    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_object_from_pairs,
            parse_constant=_reject_constant,
        )
    except UnicodeError as exc:
        raise AdapterValidationError("json_encoding_invalid") from exc


def _response(
    profile_id: str,
    *,
    status: str,
    classification: str,
    detail_code: str | None,
) -> dict[str, object]:
    safe_profile_id = profile_id if _CODE_RE.fullmatch(profile_id) else "invalid_request"
    safe_status = status if status in {"pass", "fail", "not_run"} else "not_run"
    safe_classification = classification if _CODE_RE.fullmatch(classification) else "adapter_internal_error"
    safe_detail = detail_code if detail_code is None or _CODE_RE.fullmatch(detail_code) else "adapter_internal_error"
    return {
        "schema_version": 1,
        "profile_id": safe_profile_id,
        "status": safe_status,
        "classification": safe_classification,
        "detail_code": safe_detail,
    }


def _fail(profile_id: str, code: str) -> dict[str, object]:
    return _response(profile_id, status="fail", classification=code, detail_code=code)


def _not_run(profile_id: str, code: str) -> dict[str, object]:
    return _response(profile_id, status="not_run", classification=code, detail_code=code)


def _parse_request(raw: bytes) -> tuple[dict[str, object] | None, str]:
    if not raw or len(raw) > MAX_REQUEST_BYTES:
        return None, "invalid_request"
    try:
        payload = _strict_json_loads(raw)
    except (AdapterValidationError, ValueError):
        return None, "invalid_request"
    profile_id = "invalid_request"
    if isinstance(payload, dict) and isinstance(payload.get("profile_id"), str):
        candidate = str(payload["profile_id"])
        if _CODE_RE.fullmatch(candidate):
            profile_id = candidate
    if not isinstance(payload, dict) or set(payload) != _REQUEST_FIELDS:
        return None, profile_id
    if payload.get("schema_version") != 1:
        return None, profile_id
    node_code = payload.get("node_code")
    host = payload.get("host")
    port = payload.get("port")
    request_profile_id = payload.get("profile_id")
    if (
        not isinstance(node_code, str)
        or _CODE_RE.fullmatch(node_code) is None
        or not isinstance(host, str)
        or not _valid_endpoint_host(host)
        or isinstance(port, bool)
        or not isinstance(port, int)
        or not 1 <= port <= 65535
        or not isinstance(request_profile_id, str)
        or _CODE_RE.fullmatch(request_profile_id) is None
    ):
        return None, profile_id
    return payload, profile_id


def _valid_endpoint_host(value: str) -> bool:
    if not value or len(value) > 253 or value != value.strip() or any(ord(ch) < 33 or ord(ch) > 126 for ch in value):
        return False
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        pass
    labels = value.rstrip(".").split(".")
    return bool(labels) and all(
        label
        and len(label) <= 63
        and label[0].isalnum()
        and label[-1].isalnum()
        and all(ch.isalnum() or ch == "-" for ch in label)
        for label in labels
    )


def _valid_dns_hostname(value: str) -> bool:
    if not _valid_endpoint_host(value) or value.endswith(".") or "." not in value:
        return False
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return True
    return False


def _secure_runtime_path(path: Path, *, executable: bool) -> bool:
    if not path.is_absolute():
        return False
    try:
        resolved = path.resolve(strict=True)
        path_stat = path.stat()
        path_lstat = path.lstat()
    except OSError:
        return False
    if not stat.S_ISREG(path_stat.st_mode):
        return False
    if os.name != "nt":
        get_euid = getattr(os, "geteuid", None)
        if (
            resolved != path
            or stat.S_ISLNK(path_lstat.st_mode)
            or get_euid is None
            or path_stat.st_uid not in {0, int(get_euid())}
            or path_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
        ):
            return False
    return not executable or os.access(path, os.X_OK)


def _same_file_identity(left: os.stat_result, right: os.stat_result) -> bool:
    return left.st_dev == right.st_dev and left.st_ino == right.st_ino


def _trusted_posix_file_stat(path_stat: os.stat_result) -> bool:
    get_euid = getattr(os, "geteuid", None)
    return bool(
        stat.S_ISREG(path_stat.st_mode)
        and get_euid is not None
        and path_stat.st_uid in {0, int(get_euid())}
        and not path_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
    )


def _open_posix_file(path: Path) -> _OpenedPosixFile:
    if not path.is_absolute() or path.anchor != "/":
        raise AdapterValidationError("runtime_path_unavailable")
    components = path.parts[1:]
    if not components or any(component in {"", ".", ".."} for component in components):
        raise AdapterValidationError("runtime_path_unavailable")

    close_on_exec = int(getattr(os, "O_CLOEXEC", 0))
    no_follow = int(getattr(os, "O_NOFOLLOW", 0))
    directory_flags = os.O_RDONLY | int(getattr(os, "O_DIRECTORY", 0)) | close_on_exec | no_follow
    file_flags = os.O_RDONLY | close_on_exec | no_follow
    directory_fds: list[int] = []
    file_fd = -1
    try:
        directory_fds.append(os.open("/", directory_flags))
        for component in components[:-1]:
            parent_fd = directory_fds[-1]
            child_fd = os.open(component, directory_flags, dir_fd=parent_fd)
            try:
                named_stat = os.stat(component, dir_fd=parent_fd, follow_symlinks=False)
                opened_stat = os.fstat(child_fd)
                if (
                    stat.S_ISLNK(named_stat.st_mode)
                    or not stat.S_ISDIR(opened_stat.st_mode)
                    or not _same_file_identity(named_stat, opened_stat)
                ):
                    raise AdapterValidationError("runtime_path_unavailable")
            except (AdapterValidationError, OSError):
                os.close(child_fd)
                raise
            directory_fds.append(child_fd)

        filename = components[-1]
        parent_fd = directory_fds[-1]
        file_fd = os.open(filename, file_flags, dir_fd=parent_fd)
        named_stat = os.stat(filename, dir_fd=parent_fd, follow_symlinks=False)
        opened_stat = os.fstat(file_fd)
        if (
            stat.S_ISLNK(named_stat.st_mode)
            or not _same_file_identity(named_stat, opened_stat)
            or not _trusted_posix_file_stat(opened_stat)
        ):
            raise AdapterValidationError("runtime_path_unavailable")
        return _OpenedPosixFile(
            fd=file_fd,
            initial_stat=opened_stat,
            directory_fds=directory_fds,
            directory_components=tuple(components[:-1]),
            filename=filename,
        )
    except (AdapterValidationError, OSError):
        if file_fd >= 0:
            os.close(file_fd)
        for directory_fd in reversed(directory_fds):
            os.close(directory_fd)
        raise AdapterValidationError("runtime_path_unavailable")


def _opened_posix_path_is_current(opened: _OpenedPosixFile) -> bool:
    try:
        for index, component in enumerate(opened.directory_components):
            named_stat = os.stat(
                component,
                dir_fd=opened.directory_fds[index],
                follow_symlinks=False,
            )
            descriptor_stat = os.fstat(opened.directory_fds[index + 1])
            if (
                stat.S_ISLNK(named_stat.st_mode)
                or not stat.S_ISDIR(descriptor_stat.st_mode)
                or not _same_file_identity(named_stat, descriptor_stat)
            ):
                return False
        named_file_stat = os.stat(
            opened.filename,
            dir_fd=opened.directory_fds[-1],
            follow_symlinks=False,
        )
        descriptor_file_stat = os.fstat(opened.fd)
    except OSError:
        return False
    return (
        not stat.S_ISLNK(named_file_stat.st_mode)
        and _same_file_identity(named_file_stat, descriptor_file_stat)
        and _trusted_posix_file_stat(descriptor_file_stat)
    )


def _read_posix_file(path: Path, *, max_bytes: int) -> bytes:
    opened = _open_posix_file(path)
    try:
        if not 1 <= opened.initial_stat.st_size <= max_bytes:
            raise AdapterValidationError("runtime_document_invalid")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(opened.fd, min(64 * 1024, max_bytes + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > max_bytes:
                raise AdapterValidationError("runtime_document_invalid")
        final_stat = os.fstat(opened.fd)
        unchanged = (
            _same_file_identity(opened.initial_stat, final_stat)
            and opened.initial_stat.st_size == final_stat.st_size == total
            and opened.initial_stat.st_mtime_ns == final_stat.st_mtime_ns
            and opened.initial_stat.st_ctime_ns == final_stat.st_ctime_ns
        )
        if not unchanged or not _opened_posix_path_is_current(opened):
            raise AdapterValidationError("runtime_path_unavailable")
        return b"".join(chunks)
    except OSError as exc:
        raise AdapterValidationError("runtime_path_unavailable") from exc
    finally:
        os.close(opened.fd)
        for directory_fd in reversed(opened.directory_fds):
            os.close(directory_fd)


def _read_secure_json(path: Path, *, max_bytes: int) -> object:
    if os.name != "nt":
        raw = _read_posix_file(path, max_bytes=max_bytes)
    else:
        if not _secure_runtime_path(path, executable=False):
            raise AdapterValidationError("runtime_path_unavailable")
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise AdapterValidationError("runtime_path_unavailable") from exc
    if not raw or len(raw) > max_bytes:
        raise AdapterValidationError("runtime_document_invalid")
    try:
        return _strict_json_loads(raw)
    except (AdapterValidationError, ValueError) as exc:
        raise AdapterValidationError("runtime_document_invalid") from exc


def _strict_float(value: object, *, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AdapterValidationError("timeout_invalid")
    parsed = float(value)
    if not minimum <= parsed <= maximum:
        raise AdapterValidationError("timeout_invalid")
    return parsed


def _load_runtime_config(path: Path) -> RuntimeConfig:
    payload = _read_secure_json(path, max_bytes=MAX_RUNTIME_CONFIG_BYTES)
    if not isinstance(payload, dict) or set(payload) != _RUNTIME_FIELDS or payload.get("schema_version") != 1:
        raise AdapterValidationError("adapter_config_invalid")
    core_path = payload.get("core_path")
    store_path = payload.get("credential_store_path")
    probe = payload.get("probe")
    timeouts = payload.get("timeouts")
    if not isinstance(core_path, str) or not isinstance(store_path, str):
        raise AdapterValidationError("adapter_config_invalid")
    if len(core_path) > 512 or len(store_path) > 512:
        raise AdapterValidationError("adapter_config_invalid")
    if not isinstance(probe, dict) or set(probe) != _PROBE_FIELDS:
        raise AdapterValidationError("adapter_config_invalid")
    if not isinstance(timeouts, dict) or set(timeouts) != _TIMEOUT_FIELDS:
        raise AdapterValidationError("adapter_config_invalid")

    hostname = probe.get("hostname")
    port = probe.get("port")
    path_value = probe.get("path")
    expected_status = probe.get("expected_status")
    header_name = probe.get("marker_header_name")
    header_value = probe.get("marker_header_value")
    if (
        not isinstance(hostname, str)
        or not _valid_dns_hostname(hostname)
        or isinstance(port, bool)
        or not isinstance(port, int)
        or not 1 <= port <= 65535
        or not isinstance(path_value, str)
        or not path_value.startswith("/")
        or len(path_value) > 256
        or any(ord(ch) < 33 or ord(ch) > 126 for ch in path_value)
        or "#" in path_value
        or isinstance(expected_status, bool)
        or not isinstance(expected_status, int)
        or not 200 <= expected_status <= 299
        or not isinstance(header_name, str)
        or _HEADER_NAME_RE.fullmatch(header_name) is None
        or not isinstance(header_value, str)
        or not 1 <= len(header_value) <= 128
        or any(ord(ch) < 32 or ord(ch) > 126 for ch in header_value)
    ):
        raise AdapterValidationError("adapter_config_invalid")

    parsed_timeouts = Timeouts(
        total_seconds=_strict_float(timeouts.get("total_seconds"), minimum=2.0, maximum=60.0),
        core_start_seconds=_strict_float(timeouts.get("core_start_seconds"), minimum=0.1, maximum=15.0),
        connect_seconds=_strict_float(timeouts.get("connect_seconds"), minimum=0.1, maximum=15.0),
        io_seconds=_strict_float(timeouts.get("io_seconds"), minimum=0.1, maximum=15.0),
        shutdown_seconds=_strict_float(timeouts.get("shutdown_seconds"), minimum=0.1, maximum=5.0),
    )
    if parsed_timeouts.core_start_seconds >= parsed_timeouts.total_seconds:
        raise AdapterValidationError("adapter_config_invalid")

    parsed_core_path = Path(core_path)
    parsed_store_path = Path(store_path)
    if not parsed_core_path.is_absolute() or not parsed_store_path.is_absolute():
        raise AdapterValidationError("adapter_config_invalid")
    return RuntimeConfig(
        core_path=parsed_core_path,
        credential_store_path=parsed_store_path,
        probe=ProbeTarget(
            hostname=hostname,
            port=port,
            path=path_value,
            expected_status=expected_status,
            marker_header_name=header_name,
            marker_header_value=header_value,
        ),
        timeouts=parsed_timeouts,
    )


def _canonical_uuid(value: object) -> str | None:
    if not isinstance(value, str) or len(value) != 36:
        return None
    try:
        parsed = uuid_module.UUID(value)
    except ValueError:
        return None
    return value if str(parsed) == value.lower() else None


def _load_credential(path: Path, *, profile_id: str) -> CanaryCredential:
    payload = _read_secure_json(path, max_bytes=MAX_CREDENTIAL_STORE_BYTES)
    if not isinstance(payload, dict) or set(payload) != _STORE_FIELDS or payload.get("schema_version") != 1:
        raise AdapterValidationError("probe_material_invalid")
    profiles = payload.get("profiles")
    if not isinstance(profiles, dict) or not 1 <= len(profiles) <= MAX_PROFILES:
        raise AdapterValidationError("probe_material_invalid")
    if any(not isinstance(key, str) or _CODE_RE.fullmatch(key) is None for key in profiles):
        raise AdapterValidationError("probe_material_invalid")
    entry = profiles.get(profile_id)
    if not isinstance(entry, dict) or set(entry) != _PROFILE_FIELDS:
        raise AdapterValidationError("probe_material_invalid")
    endpoint = entry.get("endpoint")
    reality = entry.get("reality")
    if not isinstance(endpoint, dict) or set(endpoint) != _ENDPOINT_FIELDS:
        raise AdapterValidationError("probe_material_invalid")
    if not isinstance(reality, dict) or set(reality) != _REALITY_FIELDS:
        raise AdapterValidationError("probe_material_invalid")

    node_code = entry.get("node_code")
    host = endpoint.get("host")
    port = endpoint.get("port")
    user_uuid = _canonical_uuid(entry.get("uuid"))
    flow = entry.get("flow")
    server_name = reality.get("server_name")
    public_key = reality.get("public_key")
    short_id = reality.get("short_id")
    fingerprint = reality.get("fingerprint")
    if (
        not isinstance(node_code, str)
        or _CODE_RE.fullmatch(node_code) is None
        or not isinstance(host, str)
        or not _valid_endpoint_host(host)
        or isinstance(port, bool)
        or not isinstance(port, int)
        or not 1 <= port <= 65535
        or user_uuid is None
        or flow != "xtls-rprx-vision"
        or not isinstance(server_name, str)
        or not _valid_dns_hostname(server_name)
        or not isinstance(public_key, str)
        or _PUBLIC_KEY_RE.fullmatch(public_key) is None
        or not isinstance(short_id, str)
        or _SHORT_ID_RE.fullmatch(short_id) is None
        or len(short_id) % 2 != 0
        or not isinstance(fingerprint, str)
        or fingerprint not in _FINGERPRINTS
    ):
        raise AdapterValidationError("probe_material_invalid")
    return CanaryCredential(
        profile_id=profile_id,
        node_code=node_code,
        host=host,
        port=port,
        uuid=user_uuid,
        flow=flow,
        server_name=server_name,
        public_key=public_key,
        short_id=short_id,
        fingerprint=fingerprint,
    )


def _build_singbox_config(credential: CanaryCredential, *, socks_port: int) -> dict[str, object]:
    config: dict[str, object] = {
        "log": {"disabled": True},
        "inbounds": [
            {
                "type": "socks",
                "tag": "authenticated-probe-in",
                "listen": "127.0.0.1",
                "listen_port": socks_port,
            }
        ],
        "outbounds": [
            {
                "type": "vless",
                "tag": "authenticated-egress",
                "server": credential.host,
                "server_port": credential.port,
                "uuid": credential.uuid,
                "flow": credential.flow,
                "packet_encoding": "xudp",
                "tls": {
                    "enabled": True,
                    "server_name": credential.server_name,
                    "utls": {"enabled": True, "fingerprint": credential.fingerprint},
                    "reality": {
                        "enabled": True,
                        "public_key": credential.public_key,
                        "short_id": credential.short_id,
                    },
                },
            }
        ],
        "route": {"final": "authenticated-egress"},
    }
    if not _validate_generated_config(config, socks_port=socks_port):
        raise AdapterValidationError("generated_config_invalid")
    return config


def _validate_generated_config(config: object, *, socks_port: int) -> bool:
    if not isinstance(config, dict) or set(config) != {"log", "inbounds", "outbounds", "route"}:
        return False
    if config.get("log") != {"disabled": True} or config.get("route") != {"final": "authenticated-egress"}:
        return False
    inbounds = config.get("inbounds")
    outbounds = config.get("outbounds")
    if not isinstance(inbounds, list) or len(inbounds) != 1:
        return False
    if not isinstance(outbounds, list) or len(outbounds) != 1:
        return False
    inbound = inbounds[0]
    outbound = outbounds[0]
    if not isinstance(inbound, dict) or inbound != {
        "type": "socks",
        "tag": "authenticated-probe-in",
        "listen": "127.0.0.1",
        "listen_port": socks_port,
    }:
        return False
    if (
        not isinstance(outbound, dict)
        or outbound.get("type") != "vless"
        or outbound.get("tag") != "authenticated-egress"
    ):
        return False
    forbidden_types = {"direct", "block", "urltest", "selector"}
    if any(
        item.get("type") in forbidden_types
        for item in outbounds
        if isinstance(item, dict)
    ):
        return False
    tls = outbound.get("tls")
    if not isinstance(tls, dict) or tls.get("enabled") is not True:
        return False
    reality = tls.get("reality")
    return isinstance(reality, dict) and reality.get("enabled") is True


def _fixed_subprocess_env() -> dict[str, str]:
    if os.name == "nt":
        return {"PATH": r"C:\Windows\System32", "SystemRoot": r"C:\Windows"}
    return {
        "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }


def _choose_loopback_port() -> int:
    """Return a candidate port; ownership is proven after the child binds it.

    Reserving a port in the adapter and closing it before sing-box starts is
    inherently racy.  A candidate therefore has no security meaning by
    itself: every use is gated on the child's live listener ownership.
    """

    return 49152 + secrets.randbelow(16384)


def _secure_runtime_directory(path: Path) -> bool:
    try:
        path_stat = path.stat()
        path_lstat = path.lstat()
    except OSError:
        return False
    if not stat.S_ISDIR(path_stat.st_mode) or stat.S_ISLNK(path_lstat.st_mode):
        return False
    if os.name != "nt":
        get_euid = getattr(os, "geteuid", None)
        if (
            get_euid is None
            or path_stat.st_uid not in {0, int(get_euid())}
            or path_stat.st_mode & (stat.S_IRWXG | stat.S_IRWXO)
        ):
            return False
    return True


def _create_unix_socks_listener(runtime_dir: Path) -> tuple[socket.socket, Path]:
    """Create the adapter-owned endpoint used for the one marker request."""

    if os.name == "nt" or not hasattr(socket, "AF_UNIX") or not _secure_runtime_directory(runtime_dir):
        raise AdapterValidationError("runtime_unavailable")
    endpoint = runtime_dir / _UNIX_SOCKS_NAME
    try:
        endpoint.lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise AdapterValidationError("runtime_unavailable") from exc
    else:
        raise AdapterValidationError("runtime_unavailable")
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        listener.bind(str(endpoint))
        os.chmod(endpoint, 0o600)
        endpoint_stat = endpoint.lstat()
        if (
            not stat.S_ISSOCK(endpoint_stat.st_mode)
            or endpoint_stat.st_uid != os.geteuid()
            or endpoint_stat.st_mode & (stat.S_IRWXG | stat.S_IRWXO)
        ):
            raise AdapterValidationError("runtime_unavailable")
        listener.listen(1)
        return listener, endpoint
    except Exception:
        listener.close()
        try:
            endpoint.unlink()
        except OSError:
            pass
        raise


def _process_owns_loopback_listener(process: subprocess.Popen[bytes], *, port: int) -> bool:
    """Prove that the live child, not another local process, owns the listener."""

    if os.name == "nt" or process.poll() is not None or not isinstance(process.pid, int) or process.pid <= 0:
        return False
    try:
        socket_inodes = {
            link[8:-1]
            for descriptor in (Path("/proc") / str(process.pid) / "fd").iterdir()
            if (link := os.readlink(descriptor)).startswith("socket:[") and link.endswith("]")
        }
        if not socket_inodes:
            return False
        expected_address = f"0100007F:{port:04X}"
        for line in (Path("/proc/net/tcp").read_text(encoding="ascii")).splitlines()[1:]:
            fields = line.split()
            if len(fields) >= 10 and fields[1] == expected_address and fields[3] == "0A" and fields[9] in socket_inodes:
                return True
    except (OSError, UnicodeError):
        return False
    return False


def _write_ephemeral_config(runtime_dir: Path, config: Mapping[str, object], *, attempt: int) -> Path:
    runtime_dir.chmod(0o700)
    config_path = runtime_dir / f"sing-box-{attempt}.json"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(config_path, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            fd = -1
            json.dump(config, handle, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    finally:
        if fd >= 0:
            os.close(fd)
    config_path.chmod(0o600)
    return config_path


def _start_core(core_path: Path, config_path: Path) -> subprocess.Popen[bytes]:
    kwargs: dict[str, object] = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "env": _fixed_subprocess_env(),
        "close_fds": True,
    }
    if os.name == "nt":
        kwargs["creationflags"] = int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    else:
        kwargs["start_new_session"] = True
    return subprocess.Popen([str(core_path), "run", "-c", str(config_path)], **kwargs)


def _terminate_process(process: subprocess.Popen[bytes], *, timeout_seconds: float) -> None:
    if process.poll() is not None:
        return
    try:
        if os.name != "nt" and process.pid:
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
        process.wait(timeout=timeout_seconds)
        return
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        if os.name != "nt" and process.pid:
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait(timeout=timeout_seconds)
    except (OSError, subprocess.TimeoutExpired):
        return


def _remaining(deadline: float, *, clock: Callable[[], float]) -> float:
    remaining = deadline - clock()
    if remaining <= 0:
        raise TimeoutError
    return remaining


def _wait_for_child_listener(
    process: subprocess.Popen[bytes],
    *,
    port: int,
    deadline: float,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    while True:
        if process.poll() is not None:
            return "core_start_failed"
        remaining = deadline - clock()
        if remaining <= 0:
            return "proxy_unavailable"
        if _process_owns_loopback_listener(process, port=port):
            return ""
        sleep(min(0.05, remaining))


def _connect_unix_socket(endpoint: Path, *, timeout: float) -> socket.socket:
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client.settimeout(timeout)
        client.connect(str(endpoint))
        return client
    except Exception:
        client.close()
        raise


class _UnixSocksBridge:
    """One-shot private UDS to child-owned loopback SOCKS bridge."""

    def __init__(
        self,
        listener: socket.socket,
        *,
        process: subprocess.Popen[bytes],
        port: int,
        deadline: float,
        clock: Callable[[], float],
    ) -> None:
        self._listener = listener
        self._process = process
        self._port = port
        self._deadline = deadline
        self._clock = clock
        self._thread = threading.Thread(target=self._serve_one, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def close(self) -> None:
        try:
            self._listener.close()
        except OSError:
            pass
        self._thread.join(timeout=0.5)

    def _serve_one(self) -> None:
        client: socket.socket | None = None
        upstream: socket.socket | None = None
        try:
            remaining = _remaining(self._deadline, clock=self._clock)
            self._listener.settimeout(min(0.5, remaining))
            client, _ = self._listener.accept()
            if not _process_owns_loopback_listener(self._process, port=self._port):
                return
            upstream = socket.create_connection(("127.0.0.1", self._port), timeout=min(0.5, remaining))
            client.setblocking(False)
            upstream.setblocking(False)
            self._relay(client, upstream)
        except (OSError, TimeoutError):
            return
        finally:
            if upstream is not None:
                upstream.close()
            if client is not None:
                client.close()

    def _relay(self, client: socket.socket, upstream: socket.socket) -> None:
        import select

        streams = {client: upstream, upstream: client}
        while streams:
            remaining = self._deadline - self._clock()
            if remaining <= 0:
                return
            readable, _, _ = select.select(list(streams), [], [], min(0.2, remaining))
            for source in readable:
                payload = source.recv(4096)
                if not payload:
                    return
                destination = streams[source]
                destination.sendall(payload)


def _start_unix_socks_bridge(
    listener: socket.socket,
    *,
    process: subprocess.Popen[bytes],
    port: int,
    deadline: float,
    clock: Callable[[], float],
) -> _UnixSocksBridge:
    bridge = _UnixSocksBridge(listener, process=process, port=port, deadline=deadline, clock=clock)
    bridge.start()
    return bridge


def _set_stream_timeout(
    stream: object,
    *,
    deadline: float,
    timeout_cap: float,
    clock: Callable[[], float],
) -> None:
    stream.settimeout(min(timeout_cap, _remaining(deadline, clock=clock)))  # type: ignore[attr-defined]


def _recv_exact(
    stream: object,
    size: int,
    *,
    deadline: float | None = None,
    timeout_cap: float = 1.0,
    clock: Callable[[], float] = time.monotonic,
) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        if deadline is not None:
            _set_stream_timeout(stream, deadline=deadline, timeout_cap=timeout_cap, clock=clock)
        chunk = stream.recv(remaining)  # type: ignore[attr-defined]
        if not chunk:
            raise OSError("short_read")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _socks_connect(
    stream: object,
    *,
    hostname: str,
    port: int,
    deadline: float,
    timeout_cap: float,
    clock: Callable[[], float],
) -> None:
    encoded_host = hostname.encode("ascii")
    if not 1 <= len(encoded_host) <= 255:
        raise OSError("host_invalid")
    _set_stream_timeout(stream, deadline=deadline, timeout_cap=timeout_cap, clock=clock)
    stream.sendall(b"\x05\x01\x00")  # type: ignore[attr-defined]
    if _recv_exact(stream, 2, deadline=deadline, timeout_cap=timeout_cap, clock=clock) != b"\x05\x00":
        raise OSError("socks_auth_failed")
    _set_stream_timeout(stream, deadline=deadline, timeout_cap=timeout_cap, clock=clock)
    stream.sendall(  # type: ignore[attr-defined]
        b"\x05\x01\x00\x03" + bytes([len(encoded_host)]) + encoded_host + int(port).to_bytes(2, "big")
    )
    reply = _recv_exact(stream, 4, deadline=deadline, timeout_cap=timeout_cap, clock=clock)
    if reply[:3] != b"\x05\x00\x00":
        raise OSError("socks_connect_failed")
    address_type = reply[3]
    if address_type == 1:
        address_length = 4
    elif address_type == 3:
        address_length = _recv_exact(
            stream,
            1,
            deadline=deadline,
            timeout_cap=timeout_cap,
            clock=clock,
        )[0]
    elif address_type == 4:
        address_length = 16
    else:
        raise OSError("socks_reply_invalid")
    _recv_exact(
        stream,
        address_length + 2,
        deadline=deadline,
        timeout_cap=timeout_cap,
        clock=clock,
    )


def _read_http_response(
    stream: object,
    *,
    target: ProbeTarget,
    deadline: float | None = None,
    timeout_cap: float = 1.0,
    clock: Callable[[], float] = time.monotonic,
) -> bool:
    buffer = bytearray()
    while b"\r\n\r\n" not in buffer:
        if deadline is not None:
            _set_stream_timeout(stream, deadline=deadline, timeout_cap=timeout_cap, clock=clock)
        chunk = stream.recv(4096)  # type: ignore[attr-defined]
        if not chunk:
            return False
        buffer.extend(chunk)
        if len(buffer) > MAX_HTTP_HEADER_BYTES:
            return False
    raw_headers, initial_body = bytes(buffer).split(b"\r\n\r\n", 1)
    if len(initial_body) > MAX_HTTP_BODY_BYTES:
        return False
    try:
        lines = raw_headers.decode("iso-8859-1").split("\r\n")
    except UnicodeError:
        return False
    status_parts = lines[0].split(" ", 2) if lines else []
    if len(status_parts) < 2 or status_parts[0] not in {"HTTP/1.0", "HTTP/1.1"}:
        return False
    try:
        status_code = int(status_parts[1])
    except ValueError:
        return False
    marker_values: list[str] = []
    content_length: int | None = None
    transfer_encoding_seen = False
    for line in lines[1:]:
        if ":" not in line:
            return False
        name, value = line.split(":", 1)
        normalized_name = name.strip().lower()
        normalized_value = value.strip()
        if normalized_name == target.marker_header_name.lower():
            marker_values.append(normalized_value)
        if normalized_name == "content-length":
            if content_length is not None:
                return False
            try:
                content_length = int(normalized_value)
            except ValueError:
                return False
        if normalized_name == "transfer-encoding":
            transfer_encoding_seen = True
    if status_code != target.expected_status or marker_values != [target.marker_header_value]:
        return False
    if transfer_encoding_seen:
        return False
    if status_code in {204, 304} or 100 <= status_code < 200:
        return not initial_body and content_length in {None, 0}
    if content_length is not None:
        if not 0 <= content_length <= MAX_HTTP_BODY_BYTES or len(initial_body) > content_length:
            return False
        remaining = content_length - len(initial_body)
        if remaining:
            _recv_exact(
                stream,
                remaining,
                deadline=deadline,
                timeout_cap=timeout_cap,
                clock=clock,
            )
        return True
    total = len(initial_body)
    while True:
        if deadline is not None:
            _set_stream_timeout(stream, deadline=deadline, timeout_cap=timeout_cap, clock=clock)
        chunk = stream.recv(min(4096, MAX_HTTP_BODY_BYTES + 1 - total))  # type: ignore[attr-defined]
        if not chunk:
            return True
        total += len(chunk)
        if total > MAX_HTTP_BODY_BYTES:
            return False


def _probe_through_socks(
    *,
    socks_endpoint: Path,
    target: ProbeTarget,
    deadline: float,
    connect_timeout: float,
    io_timeout: float,
    clock: Callable[[], float] = time.monotonic,
    connection_factory: Callable[..., socket.socket] = _connect_unix_socket,
    ssl_context_factory: Callable[[], ssl.SSLContext] = ssl.create_default_context,
) -> str:
    try:
        connect_budget = min(connect_timeout, _remaining(deadline, clock=clock))
        raw_socket = connection_factory(socks_endpoint, timeout=connect_budget)
    except TimeoutError:
        return "timeout"
    except OSError:
        return "proxy_connect_failed"
    try:
        with raw_socket:
            raw_socket.settimeout(min(io_timeout, _remaining(deadline, clock=clock)))
            try:
                _socks_connect(
                    raw_socket,
                    hostname=target.hostname,
                    port=target.port,
                    deadline=deadline,
                    timeout_cap=io_timeout,
                    clock=clock,
                )
            except TimeoutError:
                return "timeout"
            except OSError:
                return "proxy_connect_failed"
            try:
                context = ssl_context_factory()
                tls_socket = context.wrap_socket(raw_socket, server_hostname=target.hostname)
            except TimeoutError:
                return "timeout"
            except (ssl.SSLError, ssl.CertificateError, OSError):
                return "tls_failed"
            with tls_socket:
                tls_socket.settimeout(min(io_timeout, _remaining(deadline, clock=clock)))
                http_host = target.hostname if target.port == 443 else f"{target.hostname}:{target.port}"
                request = (
                    f"GET {target.path} HTTP/1.1\r\n"
                    f"Host: {http_host}\r\n"
                    "Accept: */*\r\n"
                    "Connection: close\r\n"
                    "User-Agent: pokrov-authenticated-egress/1\r\n\r\n"
                ).encode("ascii")
                try:
                    _set_stream_timeout(
                        tls_socket,
                        deadline=deadline,
                        timeout_cap=io_timeout,
                        clock=clock,
                    )
                    tls_socket.sendall(request)
                    return (
                        ""
                        if _read_http_response(
                            tls_socket,
                            target=target,
                            deadline=deadline,
                            timeout_cap=io_timeout,
                            clock=clock,
                        )
                        else "probe_response_invalid"
                    )
                except TimeoutError:
                    return "timeout"
                except OSError:
                    return "probe_response_invalid"
    except TimeoutError:
        return "timeout"


def _binding_matches(request: Mapping[str, object], credential: CanaryCredential) -> bool:
    return (
        request.get("profile_id") == credential.profile_id
        and request.get("node_code") == credential.node_code
        and request.get("host") == credential.host
        and request.get("port") == credential.port
    )


def handle_request(
    raw_request: bytes,
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    runtime_parent: Path | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> dict[str, object]:
    """Handle one strict request without exposing credential material."""

    request, profile_id = _parse_request(raw_request)
    if request is None:
        return _not_run(profile_id, "request_invalid")
    try:
        runtime = _load_runtime_config(config_path)
    except AdapterValidationError:
        return _not_run(profile_id, "adapter_config_invalid")
    if not _secure_runtime_path(runtime.core_path, executable=True):
        return _not_run(profile_id, "core_unavailable")
    try:
        credential = _load_credential(runtime.credential_store_path, profile_id=profile_id)
    except AdapterValidationError:
        return _not_run(profile_id, "probe_material_invalid")
    if not _binding_matches(request, credential):
        return _not_run(profile_id, "probe_material_invalid")

    deadline = clock() + runtime.timeouts.total_seconds
    fixed_runtime_parent = runtime_parent or (
        Path(r"C:\Windows\Temp") if os.name == "nt" else Path("/run/pokrov-authenticated-egress")
    )
    try:
        if not _secure_runtime_directory(fixed_runtime_parent):
            raise OSError
        runtime_dir = Path(
            tempfile.mkdtemp(
                prefix="pokrov-authenticated-egress-",
                dir=str(fixed_runtime_parent),
            )
        )
        runtime_dir.chmod(0o700)
        if not _secure_runtime_directory(runtime_dir):
            raise OSError
    except OSError:
        return _not_run(profile_id, "runtime_unavailable")
    try:
        last_error = "core_start_failed"
        for attempt in range(1, MAX_PORT_ATTEMPTS + 1):
            if clock() >= deadline:
                return _fail(profile_id, "timeout")
            process: subprocess.Popen[bytes] | None = None
            listener: socket.socket | None = None
            bridge: _UnixSocksBridge | None = None
            endpoint: Path | None = None
            try:
                socks_port = _choose_loopback_port()
                generated = _build_singbox_config(credential, socks_port=socks_port)
                config_file = _write_ephemeral_config(runtime_dir, generated, attempt=attempt)
                listener, endpoint = _create_unix_socks_listener(runtime_dir)
                process = _start_core(runtime.core_path, config_file)
            except AdapterValidationError:
                return _not_run(profile_id, "runtime_unavailable")
            except OSError:
                return _not_run(profile_id, "core_unavailable")
            try:
                ready_deadline = min(deadline, clock() + runtime.timeouts.core_start_seconds)
                last_error = _wait_for_child_listener(process, port=socks_port, deadline=ready_deadline, clock=clock)
                if last_error:
                    continue
                if endpoint is None or listener is None:
                    return _not_run(profile_id, "runtime_unavailable")
                bridge = _start_unix_socks_bridge(
                    listener,
                    process=process,
                    port=socks_port,
                    deadline=deadline,
                    clock=clock,
                )
                probe_error = _probe_through_socks(
                    socks_endpoint=endpoint,
                    target=runtime.probe,
                    deadline=deadline,
                    connect_timeout=runtime.timeouts.connect_seconds,
                    io_timeout=runtime.timeouts.io_seconds,
                    clock=clock,
                )
                if probe_error:
                    return _fail(profile_id, probe_error)
                if not _process_owns_loopback_listener(process, port=socks_port):
                    return _fail(profile_id, "proxy_ownership_lost")
                return _response(
                    profile_id,
                    status="pass",
                    classification="authenticated_egress",
                    detail_code=None,
                )
            finally:
                if bridge is not None:
                    bridge.close()
                elif listener is not None:
                    listener.close()
                if endpoint is not None:
                    try:
                        endpoint.unlink()
                    except FileNotFoundError:
                        pass
                    except OSError:
                        pass
                if process is not None:
                    _terminate_process(process, timeout_seconds=runtime.timeouts.shutdown_seconds)
        return _fail(profile_id, "timeout" if clock() >= deadline else last_error)
    finally:
        shutil.rmtree(runtime_dir, ignore_errors=True)


def _read_stdin(stream: BinaryIO) -> bytes:
    return stream.read(MAX_REQUEST_BYTES + 1)


def main(argv: list[str] | None = None) -> int:
    """Run the fixed-path stdin/stdout adapter CLI."""

    os.environ.clear()
    os.environ.update(_fixed_subprocess_env())
    args = list(sys.argv[1:] if argv is None else argv)
    if args:
        response = _not_run("invalid_request", "request_invalid")
    else:
        raw_request = b""
        try:
            raw_request = _read_stdin(sys.stdin.buffer)
            response = handle_request(raw_request)
        except Exception:
            _request, profile_id = _parse_request(raw_request)
            response = _not_run(profile_id, "adapter_internal_error")
    serialized = json.dumps(response, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    sys.stdout.write(serialized + "\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
