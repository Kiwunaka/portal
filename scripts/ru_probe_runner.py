from __future__ import annotations

import argparse
import base64
import copy
import http.client
import ipaddress
import json
import os
import re
import secrets
import signal
import socket
import ssl
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PORTAL_DIR = SCRIPT_DIR.parent / "portal_bot"
for import_path in (SCRIPT_DIR, PORTAL_DIR):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

import internal_hmac_client  # noqa: E402
import node_dataplane_probe as dataplane_probe  # noqa: E402
import ru_probe_uploader  # noqa: E402
from ru_probe_contract import (  # noqa: E402
    ALLOWED_ADDRESS_FAMILIES,
    ALLOWED_PROBE_MODES,
    ALLOWED_STAGES,
    MANIFEST_SCHEMA_VERSION,
    MAX_RUN_TARGETS,
    RuProbeContractError,
    canonical_json_bytes,
    endpoint_fingerprint,
    manifest_revision,
    validate_manifest_endpoint,
    validate_run_payload,
)


RUNNER_VERSION = "2.0"
MANIFEST_PATH = "/api/internal/probes/ru-origin/manifest"
DEFAULT_API_BASE_URL = "https://api.pokrov.space"
DEFAULT_KEY_ID = "ru-mini-v1"
DEFAULT_SECRET_FILE = Path("/etc/pokrov-ru-probe/hmac.key")
DEFAULT_MANIFEST_CACHE = Path("/var/lib/pokrov-ru-probe/manifest-cache.json")
DEFAULT_SPOOL_ROOT = Path("/var/lib/pokrov-ru-probe")
DEFAULT_PROFILE_REGISTRY = Path("/etc/pokrov-ru-probe/profiles.json")
DEFAULT_TIMEOUT_SEC = 10.0
MAX_MANIFEST_BYTES = 1024 * 1024
MAX_PROFILE_REGISTRY_BYTES = 64 * 1024
MAX_ADAPTER_STDOUT_BYTES = 64 * 1024
MAX_ADAPTER_STDERR_BYTES = 8 * 1024
MAX_MANIFEST_FUTURE_SKEW_SECONDS = 5 * 60
_WINDOWS_ADAPTER_WRAPPER = "\n".join(
    [
        "import base64,json,subprocess,sys",
        "try:",
        "    payload=json.loads(sys.stdin.buffer.read().decode('utf-8'))",
        "    command=payload['command']",
        "    request=base64.b64decode(payload['request_b64'],validate=True)",
        "    child=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=sys.stdout.buffer,stderr=sys.stderr.buffer,shell=False,close_fds=True)",
        "    child.communicate(request)",
        "    raise SystemExit(child.returncode)",
        "except SystemExit:",
        "    raise",
        "except BaseException:",
        "    raise SystemExit(127)",
    ]
)
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_PROFILE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_CODE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,63}$")
_TARGET_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:+-]{0,127}$")
_MANIFEST_KEYS = {
    "manifest_schema_version",
    "manifest_revision",
    "generated_at",
    "max_cache_age_seconds",
    "targets",
}
_MANIFEST_TARGET_KEYS = {
    "target_id",
    "target_kind",
    "scope",
    "node_code",
    "endpoint",
    "endpoint_fingerprint",
    "required_stages",
}
_TARGET_KINDS = {
    "environment",
    "canonical_public",
    "delivery_node",
    "reserve_xhttp",
    "reserve_hysteria",
    "diagnostic",
}
_PROTOCOL_BY_MODE = {
    "xhttp_handshake": "xhttp",
    "hysteria_handshake": "hysteria2",
}
_PRIVATE_WRITE_LOCKS: dict[str, threading.Lock] = {}
_PRIVATE_WRITE_LOCKS_GUARD = threading.Lock()


class ManifestError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = str(code)
        super().__init__(self.code)


class ManifestCacheUnavailable(ManifestError):
    pass


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate JSON member")
        result[name] = value
    return result


def _utc_text(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timezone-aware datetime required")
    return (
        value.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _parse_utc(value: object) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ManifestError("invalid_manifest_timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ManifestError("invalid_manifest_timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ManifestError("invalid_manifest_timestamp")
    return parsed.astimezone(timezone.utc)


def _require_code(
    value: object,
    *,
    target_id: bool = False,
    maximum: int = 64,
    nullable: bool = False,
) -> str | None:
    if value is None and nullable:
        return None
    pattern = _TARGET_ID_RE if target_id else _CODE_RE
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= maximum
        or pattern.fullmatch(value) is None
    ):
        raise ManifestError("invalid_manifest_code")
    return value


def validate_manifest(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != _MANIFEST_KEYS:
        raise ManifestError("invalid_manifest_shape")
    if value["manifest_schema_version"] != MANIFEST_SCHEMA_VERSION:
        raise ManifestError("unsupported_manifest_schema")
    revision = value["manifest_revision"]
    if not isinstance(revision, str) or _HASH_RE.fullmatch(revision) is None:
        raise ManifestError("invalid_manifest_revision")
    _parse_utc(value["generated_at"])
    max_age = value["max_cache_age_seconds"]
    if (
        isinstance(max_age, bool)
        or not isinstance(max_age, int)
        or not 300 <= max_age <= 24 * 60 * 60
    ):
        raise ManifestError("invalid_manifest_cache_age")
    targets = value["targets"]
    if (
        not isinstance(targets, list)
        or not targets
        or len(targets) > MAX_RUN_TARGETS
    ):
        raise ManifestError("invalid_manifest_targets")

    validated_targets: list[dict[str, object]] = []
    seen: set[str] = set()
    for raw_target in targets:
        if not isinstance(raw_target, dict) or set(raw_target) != _MANIFEST_TARGET_KEYS:
            raise ManifestError("invalid_manifest_target")
        target_id = _require_code(
            raw_target["target_id"], target_id=True, maximum=128
        )
        if target_id in seen:
            raise ManifestError("duplicate_manifest_target")
        seen.add(str(target_id))
        if raw_target["target_kind"] not in _TARGET_KINDS:
            raise ManifestError("invalid_manifest_target_kind")
        if raw_target["scope"] not in {"release_required", "diagnostic"}:
            raise ManifestError("invalid_manifest_scope")
        _require_code(raw_target["node_code"], maximum=20, nullable=True)
        try:
            validate_manifest_endpoint(raw_target["endpoint"])
        except RuProbeContractError as exc:
            raise ManifestError(exc.code) from exc
        reported_fingerprint = raw_target["endpoint_fingerprint"]
        if (
            not isinstance(reported_fingerprint, str)
            or _HASH_RE.fullmatch(reported_fingerprint) is None
            or reported_fingerprint != endpoint_fingerprint(raw_target["endpoint"])
        ):
            raise ManifestError("endpoint_fingerprint_mismatch")
        required_stages = raw_target["required_stages"]
        if (
            not isinstance(required_stages, list)
            or not required_stages
            or any(stage not in ALLOWED_STAGES for stage in required_stages)
            or len(required_stages) != len(set(required_stages))
        ):
            raise ManifestError("invalid_required_stages")
        validated_targets.append(copy.deepcopy(raw_target))
    if manifest_revision(validated_targets) != revision:
        raise ManifestError("manifest_revision_mismatch")
    return copy.deepcopy(value)


def _decode_manifest(raw: bytes) -> dict[str, object]:
    if not raw or len(raw) > MAX_MANIFEST_BYTES:
        raise ManifestError("invalid_manifest_size")
    try:
        decoded = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_json_object,
        )
    except (UnicodeError, ValueError) as exc:
        raise ManifestError("invalid_manifest_json") from exc
    return validate_manifest(decoded)


def _fsync_directory(directory: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        descriptor = os.open(str(directory), flags)
    except OSError:
        if os.name == "nt":
            return
        raise
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _private_write_lock(path: Path) -> threading.Lock:
    key = str(path.resolve())
    with _PRIVATE_WRITE_LOCKS_GUARD:
        return _PRIVATE_WRITE_LOCKS.setdefault(key, threading.Lock())


def _replace_private_file(source: Path, destination: Path) -> None:
    deadline = time.monotonic() + 2.0
    while True:
        try:
            os.replace(source, destination)
            return
        except PermissionError:
            if os.name != "nt" or time.monotonic() >= deadline:
                raise
            time.sleep(0.01)


def _write_private_bytes(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    descriptor: int | None = None
    try:
        for _attempt in range(16):
            candidate = path.with_name(
                f".{path.name}.{os.getpid()}.{secrets.token_hex(8)}.tmp"
            )
            try:
                descriptor = os.open(
                    str(candidate),
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o600,
                )
            except FileExistsError:
                continue
            temporary = candidate
            break
        if descriptor is None or temporary is None:
            raise OSError("private temporary file unavailable")
        os.chmod(temporary, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        with _private_write_lock(path):
            _replace_private_file(temporary, path)
            temporary = None
            _fsync_directory(path.parent)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


def write_manifest_cache(path: str | Path, manifest: dict[str, object]) -> None:
    validated = validate_manifest(manifest)
    _write_private_bytes(Path(path), canonical_json_bytes(validated))


def load_cached_manifest(
    path: str | Path,
    *,
    now: datetime,
) -> dict[str, object]:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ManifestCacheUnavailable("invalid_cache_clock")
    cache_path = Path(path)
    try:
        with cache_path.open("rb") as handle:
            raw = handle.read(MAX_MANIFEST_BYTES + 1)
        manifest = _decode_manifest(raw)
        generated_at = _parse_utc(manifest["generated_at"])
        normalized_now = now.astimezone(timezone.utc)
        if generated_at > normalized_now + timedelta(
            seconds=MAX_MANIFEST_FUTURE_SKEW_SECONDS
        ):
            raise ManifestCacheUnavailable("manifest_cache_from_future")
        expires_at = generated_at + timedelta(
            seconds=int(manifest["max_cache_age_seconds"])
        )
        if normalized_now > expires_at:
            raise ManifestCacheUnavailable("manifest_cache_stale")
        return manifest
    except ManifestCacheUnavailable:
        raise
    except (ManifestError, OSError) as exc:
        raise ManifestCacheUnavailable("manifest_cache_unavailable") from exc


def fetch_manifest(
    *,
    api_base_url: str,
    key_id: str,
    secret_file: str | Path,
    manifest_cache: str | Path,
    timeout_sec: float,
    now: datetime | None = None,
) -> dict[str, object]:
    observed_now = now or datetime.now(timezone.utc)
    try:
        response = internal_hmac_client.signed_request(
            api_base_url=api_base_url,
            method="GET",
            path=MANIFEST_PATH,
            key_id=key_id,
            secret_file=secret_file,
            raw_body=b"",
            timeout_sec=timeout_sec,
        )
    except (OSError, TimeoutError):
        return load_cached_manifest(manifest_cache, now=observed_now)
    if not 200 <= int(response.status) < 300:
        raise ManifestError("manifest_http_error")
    manifest = _decode_manifest(response.body)
    write_manifest_cache(manifest_cache, manifest)
    return manifest


def _stage(
    status: str,
    *,
    latency_ms: int | None = None,
    code: str | None = None,
) -> dict[str, object]:
    return {
        "status": status,
        "latency_ms": latency_ms,
        "code": code,
    }


def _safe_result_code(value: object, fallback: str) -> str:
    if isinstance(value, str) and _CODE_RE.fullmatch(value) is not None:
        return value
    return fallback


def _family_for_ip(value: object) -> str | None:
    try:
        parsed = ipaddress.ip_address(str(value))
    except ValueError:
        return None
    return "ipv4" if parsed.version == 4 else "ipv6"


def _family_status(
    requested: list[str],
    resolved_ips: list[str],
    *,
    dns_status: str,
) -> dict[str, str]:
    present = {
        family
        for family in (_family_for_ip(address) for address in resolved_ips)
        if family is not None
    }
    result: dict[str, str] = {}
    for family in ALLOWED_ADDRESS_FAMILIES:
        if family not in requested:
            result[family] = "not_applicable"
        elif dns_status == "not_run":
            result[family] = "not_run"
        elif dns_status == "fail":
            result[family] = "fail"
        else:
            result[family] = "pass" if family in present else "fail"
    return result


class _ManifestHTTPSConnection(http.client.HTTPSConnection):
    def __init__(
        self,
        *,
        host: str,
        port: int,
        server_hostname: str,
        timeout: float,
        context: ssl.SSLContext,
    ) -> None:
        super().__init__(host=host, port=port, timeout=timeout, context=context)
        self._manifest_server_hostname = server_hostname

    def connect(self) -> None:
        http.client.HTTPConnection.connect(self)
        if self.sock is None:  # pragma: no cover - defensive invariant
            raise OSError("tcp connection unavailable")
        self.sock = self._context.wrap_socket(
            self.sock,
            server_hostname=self._manifest_server_hostname,
        )


def _verified_https_connection(
    *,
    host: str,
    port: int,
    sni: str,
    timeout_sec: float,
) -> _ManifestHTTPSConnection:
    context = ssl.create_default_context()
    return _ManifestHTTPSConnection(
        host=host,
        port=port,
        server_hostname=sni,
        timeout=timeout_sec,
        context=context,
    )


def _probe_https_address(
    *,
    address: str,
    port: int,
    sni: str,
    path: str,
    min_body_bytes: int,
    timeout_sec: float,
) -> dict[str, object]:
    stages = {
        "tcp": _stage("not_run"),
        "tls": _stage("not_run"),
        "http_large_body": _stage("not_run"),
    }
    result: dict[str, object] = {
        "stages": stages,
        "http_status": None,
        "body_bytes": 0,
    }
    connection = None
    connected = False
    connect_started = time.perf_counter()
    try:
        connection = _verified_https_connection(
            host=address,
            port=port,
            sni=sni,
            timeout_sec=timeout_sec,
        )
        connection.connect()
        connected = True
        connect_latency = int((time.perf_counter() - connect_started) * 1000)
        stages["tcp"] = _stage("pass", latency_ms=connect_latency)
        stages["tls"] = _stage("pass", latency_ms=connect_latency)
        connection.request(
            "GET",
            path,
            body=None,
            headers={
                "Host": sni,
                "User-Agent": "pokrov-ru-probe/2.0",
                "Accept": "*/*",
                "Connection": "close",
            },
        )
        response = connection.getresponse()
        result["http_status"] = int(response.status)
        if not 200 <= int(response.status) < 400:
            stages["http_large_body"] = _stage(
                "fail",
                code="http_status_unaccepted",
            )
            return result
        required_bytes = max(65536, int(min_body_bytes))
        body_bytes = 0
        http_started = time.perf_counter()
        while body_bytes < required_bytes:
            chunk = response.read(min(64 * 1024, required_bytes - body_bytes))
            if not chunk:
                break
            body_bytes += len(chunk)
        result["body_bytes"] = body_bytes
        http_latency = int((time.perf_counter() - http_started) * 1000)
        stages["http_large_body"] = _stage(
            "pass" if body_bytes >= required_bytes else "fail",
            latency_ms=http_latency,
            code=None if body_bytes >= required_bytes else "http_body_too_short",
        )
        return result
    except ssl.SSLError:
        stages["tcp"] = _stage("pass")
        stages["tls"] = _stage("fail", code="tls_handshake_failed")
        return result
    except (TimeoutError, socket.timeout):
        if connected:
            stages["http_large_body"] = _stage("fail", code="http_timeout")
        else:
            stages["tcp"] = _stage("fail", code="tcp_connect_timeout")
        return result
    except http.client.HTTPException:
        stages["http_large_body"] = _stage("fail", code="http_protocol_error")
        return result
    except OSError:
        if connected:
            stages["http_large_body"] = _stage("fail", code="http_request_failed")
        else:
            stages["tcp"] = _stage("fail", code="tcp_connect_failed")
        return result
    finally:
        if connection is not None:
            connection.close()


def _https_attempt_score(attempt: dict[str, object]) -> int:
    stages = attempt["stages"]
    if stages["http_large_body"]["status"] in {"pass", "fail"}:
        return 3
    if stages["tls"]["status"] in {"pass", "fail"}:
        return 2
    if stages["tcp"]["status"] in {"pass", "fail"}:
        return 1
    return 0


def probe_https_large_body(
    *,
    host: str,
    port: int,
    sni: str,
    path: str,
    min_body_bytes: int,
    address_families: list[str],
    timeout_sec: float,
) -> dict[str, object]:
    stages = {
        "dns": _stage("not_run"),
        "tcp": _stage("not_run"),
        "tls": _stage("not_run"),
        "http_large_body": _stage("not_run"),
        "transport_handshake": _stage("not_applicable"),
    }
    result: dict[str, object] = {
        "stages": stages,
        "address_family_status": {
            family: (
                "not_run" if family in address_families else "not_applicable"
            )
            for family in ALLOWED_ADDRESS_FAMILIES
        },
        "resolved_ips": [],
        "http_status": None,
        "body_bytes": 0,
    }
    dns_started = time.perf_counter()
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except (socket.gaierror, OSError):
        stages["dns"] = _stage("fail", code="dns_lookup_failed")
        result["address_family_status"] = _family_status(
            address_families,
            [],
            dns_status="fail",
        )
        return result
    addresses: dict[str, list[str]] = {
        family: [] for family in ALLOWED_ADDRESS_FAMILIES
    }
    for info in infos:
        address = str(info[4][0])
        family = _family_for_ip(address)
        if (
            family in address_families
            and address
            and address not in addresses[family]
        ):
            addresses[family].append(address)
    resolved_ips = [
        address
        for family in address_families
        for address in addresses[family]
    ]
    if not resolved_ips:
        stages["dns"] = _stage("fail", code="dns_lookup_failed")
        result["address_family_status"] = _family_status(
            address_families,
            [],
            dns_status="fail",
        )
        return result
    result["resolved_ips"] = resolved_ips
    stages["dns"] = _stage(
        "pass",
        latency_ms=int((time.perf_counter() - dns_started) * 1000),
    )

    family_attempts: dict[str, dict[str, object]] = {}
    for family in address_families:
        if not addresses[family]:
            result["address_family_status"][family] = "fail"
            continue
        attempts = [
            _probe_https_address(
                address=address,
                port=port,
                sni=sni,
                path=path,
                min_body_bytes=min_body_bytes,
                timeout_sec=timeout_sec,
            )
            for address in addresses[family]
        ]
        selected = next(
            (
                attempt
                for attempt in attempts
                if attempt["stages"]["http_large_body"]["status"] == "pass"
            ),
            max(attempts, key=_https_attempt_score),
        )
        family_attempts[family] = selected
        statuses = {
            selected["stages"][stage_name]["status"]
            for stage_name in ("tcp", "tls", "http_large_body")
        }
        if selected["stages"]["http_large_body"]["status"] == "pass":
            family_status = "pass"
        elif "fail" in statuses:
            family_status = "fail"
        else:
            family_status = "not_run"
        result["address_family_status"][family] = family_status

    selected_attempt = next(
        (
            family_attempts[family]
            for family in address_families
            if family in family_attempts
            and family_attempts[family]["stages"]["http_large_body"]["status"]
            == "pass"
        ),
        (
            max(family_attempts.values(), key=_https_attempt_score)
            if family_attempts
            else None
        ),
    )
    if selected_attempt is not None:
        for stage_name in ("tcp", "tls", "http_large_body"):
            stages[stage_name] = selected_attempt["stages"][stage_name]
        result["http_status"] = selected_attempt["http_status"]
        result["body_bytes"] = selected_attempt["body_bytes"]
    return result


def _empty_target_result(target: dict[str, object]) -> dict[str, object]:
    required = set(target["required_stages"])
    endpoint = target["endpoint"]
    stages = {
        stage_name: _stage(
            "not_run" if stage_name in required else "not_applicable"
        )
        for stage_name in ALLOWED_STAGES
    }
    return {
        "target_id": target["target_id"],
        "target_kind": target["target_kind"],
        "scope": target["scope"],
        "node_code": target["node_code"],
        "endpoint": copy.deepcopy(endpoint),
        "endpoint_fingerprint": target["endpoint_fingerprint"],
        "stages": stages,
        "address_family_status": {
            family: (
                "not_run"
                if family in endpoint["address_families"]
                else "not_applicable"
            )
            for family in ALLOWED_ADDRESS_FAMILIES
        },
        "transport": {
            "profile_code": endpoint["transport_profile"],
            "handshake_status": stages["transport_handshake"]["status"],
            "classification": (
                "not_run"
                if stages["transport_handshake"]["status"] == "not_run"
                else "not_applicable"
            ),
            "detail_code": None,
        },
        "detail_code": None,
        "detail": None,
    }


def _apply_dataplane_result(
    result: dict[str, object],
    endpoint: dict[str, object],
    payload: dict[str, object],
) -> None:
    stages = result["stages"]
    resolved_ips = [
        str(address)
        for address in payload.get("resolved_ips", [])
        if _family_for_ip(address) is not None
    ]
    error_kind = _safe_result_code(
        payload.get("error_kind"),
        "delivery_probe_failed",
    )
    source_stage = str(payload.get("stage") or "")
    if resolved_ips:
        stages["dns"] = _stage("pass")
    else:
        stages["dns"] = _stage("fail", code="dns_lookup_failed")
    result["address_family_status"] = _family_status(
        list(endpoint["address_families"]),
        resolved_ips,
        dns_status=str(stages["dns"]["status"]),
    )
    if stages["dns"]["status"] != "pass":
        return

    latency = payload.get("latency_ms")
    latency_ms = (
        int(latency)
        if isinstance(latency, (int, float)) and not isinstance(latency, bool)
        else None
    )
    tcp_reached = (
        latency_ms is not None
        or bool(payload.get("tls_protocol"))
        or source_stage in {"tls", "tls_sni", "reality_target"}
        or error_kind in {"tls_handshake_failed", "reality_target_mismatch"}
    )
    if tcp_reached:
        stages["tcp"] = _stage("pass", latency_ms=latency_ms)
    elif source_stage.startswith("tcp") or error_kind.startswith("tcp_"):
        stages["tcp"] = _stage("fail", code=error_kind)
    else:
        stages["tcp"] = _stage("not_run", code="tcp_not_observed")

    if stages["tcp"]["status"] != "pass":
        return
    if bool(payload.get("ok")):
        stages["tls"] = _stage("pass", latency_ms=latency_ms)
    else:
        stages["tls"] = _stage(
            "fail",
            latency_ms=latency_ms,
            code=_safe_result_code(
                payload.get("error_kind"),
                "tls_handshake_failed",
            ),
        )


def _dataplane_attempt_score(result: dict[str, object]) -> int:
    stages = result["stages"]
    if stages["tls"]["status"] in {"pass", "fail"}:
        return 3
    if stages["tcp"]["status"] in {"pass", "fail"}:
        return 2
    if stages["dns"]["status"] in {"pass", "fail"}:
        return 1
    return 0


def _dataplane_attempt(
    endpoint: dict[str, object],
    payload: dict[str, object],
) -> dict[str, object]:
    attempt: dict[str, object] = {
        "stages": {
            "dns": _stage("not_run"),
            "tcp": _stage("not_run"),
            "tls": _stage("not_run"),
            "http_large_body": _stage("not_applicable"),
            "transport_handshake": _stage("not_applicable"),
        },
        "address_family_status": {
            family: (
                "not_run"
                if family in endpoint["address_families"]
                else "not_applicable"
            )
            for family in ALLOWED_ADDRESS_FAMILIES
        },
    }
    _apply_dataplane_result(attempt, endpoint, payload)
    return attempt


def _probe_delivery_families(
    result: dict[str, object],
    endpoint: dict[str, object],
    *,
    timeout_sec: float,
) -> tuple[str | None, str | None]:
    requested_families = list(endpoint["address_families"])
    try:
        dns = dataplane_probe._resolve_dns(
            str(endpoint["host"]),
            int(endpoint["port"]),
        )
    except (OSError, RuntimeError):
        result["stages"]["dns"] = _stage("fail", code="dns_lookup_failed")
        result["address_family_status"] = _family_status(
            requested_families,
            [],
            dns_status="fail",
        )
        return None, None
    resolved_by_family: dict[str, list[str]] = {
        family: [] for family in ALLOWED_ADDRESS_FAMILIES
    }
    for raw_address in dns.get("resolved_ips", []):
        address = str(raw_address)
        family = _family_for_ip(address)
        if (
            family in requested_families
            and address not in resolved_by_family[family]
        ):
            resolved_by_family[family].append(address)
    if not any(resolved_by_family[family] for family in requested_families):
        result["stages"]["dns"] = _stage(
            "fail",
            code="dns_requested_family_unavailable",
        )
        result["address_family_status"] = {
            family: (
                "fail" if family in requested_families else "not_applicable"
            )
            for family in ALLOWED_ADDRESS_FAMILIES
        }
        return None, None

    family_attempts: dict[str, tuple[str, dict[str, object]]] = {}
    family_status = {
        family: (
            "not_run" if family in requested_families else "not_applicable"
        )
        for family in ALLOWED_ADDRESS_FAMILIES
    }
    for family in requested_families:
        addresses = resolved_by_family[family]
        if not addresses:
            family_status[family] = "fail"
            continue
        attempts: list[tuple[str, dict[str, object]]] = []
        for address in addresses:
            payload = dataplane_probe.probe_node_endpoint(
                host=address,
                port=int(endpoint["port"]),
                sni=(
                    str(endpoint["sni"])
                    if endpoint["sni"] is not None
                    else None
                ),
                timeout_sec=timeout_sec,
            )
            connected_ip = str(payload.get("connected_ip") or "")
            connected_family = _family_for_ip(connected_ip)
            reached_connection = (
                bool(payload.get("ok"))
                or payload.get("latency_ms") is not None
                or bool(payload.get("tls_protocol"))
            )
            if reached_connection and connected_family != family:
                payload = {
                    **payload,
                    "ok": False,
                    "stage": "tcp_forbidden_family",
                    "error_kind": "forbidden_address_family",
                    "resolved_ips": [address],
                    "latency_ms": None,
                    "tls_protocol": "",
                    "connected_ip": connected_ip,
                }
            else:
                payload = {**payload, "resolved_ips": [address]}
            attempts.append((address, _dataplane_attempt(endpoint, payload)))
        selected = next(
            (
                attempt
                for attempt in attempts
                if attempt[1]["stages"]["tls"]["status"] == "pass"
            ),
            max(attempts, key=lambda item: _dataplane_attempt_score(item[1])),
        )
        family_attempts[family] = selected
        statuses = {
            selected[1]["stages"][stage_name]["status"]
            for stage_name in ("dns", "tcp", "tls")
        }
        if selected[1]["stages"]["tls"]["status"] == "pass":
            family_status[family] = "pass"
        elif "fail" in statuses:
            family_status[family] = "fail"
        else:
            family_status[family] = "not_run"

    selected_family = next(
        (
            family
            for family in requested_families
            if family in family_attempts
            and family_attempts[family][1]["stages"]["tls"]["status"] == "pass"
        ),
        None,
    )
    if selected_family is None and family_attempts:
        selected_family = max(
            family_attempts,
            key=lambda family: _dataplane_attempt_score(
                family_attempts[family][1]
            ),
        )
    result["address_family_status"] = family_status
    if selected_family is None:
        result["stages"]["dns"] = _stage(
            "fail",
            code="dns_requested_family_unavailable",
        )
        return None, None
    selected_address, selected_attempt = family_attempts[selected_family]
    for stage_name in ("dns", "tcp", "tls"):
        result["stages"][stage_name] = selected_attempt["stages"][stage_name]
    if selected_attempt["stages"]["tls"]["status"] != "pass":
        return None, None
    return selected_address, selected_family


def _adapter_result(
    *,
    profile_id: str,
    protocol: str,
    status: str,
    classification: str,
    detail_code: str | None,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "profile_id": profile_id,
        "protocol": protocol,
        "handshake_status": status,
        "classification": classification,
        "detail_code": detail_code,
    }


def _adapter_failure(
    endpoint: dict[str, object],
    mode: str,
    *,
    status: str,
    code: str,
) -> dict[str, object]:
    profile_id = endpoint.get("local_probe_profile_id")
    return _adapter_result(
        profile_id=(
            str(profile_id)
            if isinstance(profile_id, str) and profile_id
            else "unavailable"
        ),
        protocol=_PROTOCOL_BY_MODE.get(mode, "unknown"),
        status=status,
        classification=(
            "probe_material_unavailable"
            if status == "not_run"
            else "adapter_failure"
        ),
        detail_code=code,
    )


class _WindowsJobObject:
    def __init__(self) -> None:
        import ctypes
        from ctypes import wintypes

        class BasicLimitInformation(ctypes.Structure):
            _fields_ = [
                ("per_process_user_time_limit", ctypes.c_longlong),
                ("per_job_user_time_limit", ctypes.c_longlong),
                ("limit_flags", wintypes.DWORD),
                ("minimum_working_set_size", ctypes.c_size_t),
                ("maximum_working_set_size", ctypes.c_size_t),
                ("active_process_limit", wintypes.DWORD),
                ("affinity", ctypes.c_size_t),
                ("priority_class", wintypes.DWORD),
                ("scheduling_class", wintypes.DWORD),
            ]

        class IoCounters(ctypes.Structure):
            _fields_ = [
                ("read_operation_count", ctypes.c_ulonglong),
                ("write_operation_count", ctypes.c_ulonglong),
                ("other_operation_count", ctypes.c_ulonglong),
                ("read_transfer_count", ctypes.c_ulonglong),
                ("write_transfer_count", ctypes.c_ulonglong),
                ("other_transfer_count", ctypes.c_ulonglong),
            ]

        class ExtendedLimitInformation(ctypes.Structure):
            _fields_ = [
                ("basic_limit_information", BasicLimitInformation),
                ("io_info", IoCounters),
                ("process_memory_limit", ctypes.c_size_t),
                ("job_memory_limit", ctypes.c_size_t),
                ("peak_process_memory_used", ctypes.c_size_t),
                ("peak_job_memory_used", ctypes.c_size_t),
            ]

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        create_job_object = kernel32.CreateJobObjectW
        create_job_object.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        create_job_object.restype = wintypes.HANDLE
        set_information = kernel32.SetInformationJobObject
        set_information.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        set_information.restype = wintypes.BOOL
        assign_process = kernel32.AssignProcessToJobObject
        assign_process.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        assign_process.restype = wintypes.BOOL
        terminate_job = kernel32.TerminateJobObject
        terminate_job.argtypes = [wintypes.HANDLE, wintypes.UINT]
        terminate_job.restype = wintypes.BOOL
        close_handle = kernel32.CloseHandle
        close_handle.argtypes = [wintypes.HANDLE]
        close_handle.restype = wintypes.BOOL

        handle = create_job_object(None, None)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = ExtendedLimitInformation()
        limits.basic_limit_information.limit_flags = 0x00002000
        if not set_information(
            handle,
            9,
            ctypes.byref(limits),
            ctypes.sizeof(limits),
        ):
            error = ctypes.get_last_error()
            close_handle(handle)
            raise ctypes.WinError(error)
        self._ctypes = ctypes
        self._wintypes = wintypes
        self._assign_process = assign_process
        self._terminate_job = terminate_job
        self._close_handle = close_handle
        self._handle = handle

    def assign(self, process: subprocess.Popen[bytes]) -> None:
        if self._handle is None:
            raise OSError("job object is closed")
        if not self._assign_process(
            self._handle,
            self._wintypes.HANDLE(int(process._handle)),
        ):
            raise self._ctypes.WinError(self._ctypes.get_last_error())

    def terminate(self) -> None:
        if self._handle is not None:
            self._terminate_job(self._handle, 1)

    def close(self) -> None:
        if self._handle is not None:
            self._close_handle(self._handle)
            self._handle = None


def _windows_adapter_bootstrap(
    command: list[str],
    request_bytes: bytes,
) -> bytes:
    return json.dumps(
        {
            "command": command,
            "request_b64": base64.b64encode(request_bytes).decode("ascii"),
        },
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _start_adapter_process(
    command: list[str],
    *,
    request_bytes: bytes,
) -> tuple[
    subprocess.Popen[bytes],
    _WindowsJobObject | None,
    bytes,
]:
    popen_kwargs: dict[str, object] = {
        "stdin": subprocess.PIPE,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "shell": False,
        "close_fds": True,
    }
    if os.name != "nt":
        popen_kwargs["start_new_session"] = True
        return (
            subprocess.Popen(command, **popen_kwargs),
            None,
            request_bytes,
        )

    job = _WindowsJobObject()
    process = None
    try:
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        process = subprocess.Popen(
            [str(Path(sys.executable).resolve()), "-I", "-c", _WINDOWS_ADAPTER_WRAPPER],
            **popen_kwargs,
        )
        job.assign(process)
        return (
            process,
            job,
            _windows_adapter_bootstrap(command, request_bytes),
        )
    except BaseException:
        if process is not None:
            try:
                process.kill()
                process.wait(timeout=5.0)
            except (OSError, subprocess.SubprocessError):
                pass
        job.close()
        raise


def _read_bounded_pipe(
    pipe,
    *,
    limit: int,
    chunks: list[bytes],
    overflow: threading.Event,
) -> None:
    total = 0
    discarding = False
    try:
        while True:
            chunk = pipe.read(8192)
            if not chunk:
                return
            if discarding:
                continue
            remaining = limit - total
            if len(chunk) > remaining:
                if remaining:
                    chunks.append(chunk[:remaining])
                    total += remaining
                overflow.set()
                discarding = True
            else:
                chunks.append(chunk)
                total += len(chunk)
    except (OSError, ValueError):
        return
    finally:
        try:
            pipe.close()
        except OSError:
            pass


def _terminate_adapter_process(
    process: subprocess.Popen[bytes],
    windows_job: _WindowsJobObject | None,
) -> None:
    if windows_job is not None:
        windows_job.terminate()
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if process.poll() is None:
        try:
            process.kill()
        except OSError:
            pass
    try:
        process.wait(timeout=5.0)
    except (OSError, subprocess.TimeoutExpired):
        pass


def _run_bounded_adapter_process(
    command: list[str],
    *,
    request_bytes: bytes,
    timeout_sec: float,
) -> tuple[str, int | None, bytes, bytes]:
    process, windows_job, process_input = _start_adapter_process(
        command,
        request_bytes=request_bytes,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    assert process.stderr is not None
    overflow = threading.Event()
    stdout_chunks: list[bytes] = []
    stderr_chunks: list[bytes] = []
    readers = [
        threading.Thread(
            target=_read_bounded_pipe,
            kwargs={
                "pipe": process.stdout,
                "limit": MAX_ADAPTER_STDOUT_BYTES,
                "chunks": stdout_chunks,
                "overflow": overflow,
            },
            daemon=True,
        ),
        threading.Thread(
            target=_read_bounded_pipe,
            kwargs={
                "pipe": process.stderr,
                "limit": MAX_ADAPTER_STDERR_BYTES,
                "chunks": stderr_chunks,
                "overflow": overflow,
            },
            daemon=True,
        ),
    ]
    for reader in readers:
        reader.start()
    try:
        process.stdin.write(process_input)
        process.stdin.flush()
    except (BrokenPipeError, OSError):
        pass
    finally:
        try:
            process.stdin.close()
        except OSError:
            pass

    deadline = time.monotonic() + float(timeout_sec)
    outcome = "ok"
    while True:
        if overflow.is_set():
            outcome = "overflow"
            _terminate_adapter_process(process, windows_job)
            break
        readers_done = all(not reader.is_alive() for reader in readers)
        if process.poll() is not None and readers_done:
            break
        if time.monotonic() >= deadline:
            outcome = "timeout"
            _terminate_adapter_process(process, windows_job)
            break
        overflow.wait(0.01)

    for reader in readers:
        reader.join(timeout=1.0)
    if any(reader.is_alive() for reader in readers):
        _terminate_adapter_process(process, windows_job)
        outcome = "timeout" if outcome == "ok" else outcome
        for reader in readers:
            reader.join(timeout=1.0)
    try:
        return (
            outcome,
            process.poll(),
            b"".join(stdout_chunks),
            b"".join(stderr_chunks),
        )
    finally:
        if windows_job is not None:
            windows_job.close()


def run_transport_adapter(
    mode: str,
    endpoint: dict[str, object],
    *,
    profile_registry: dict[str, object],
    timeout_sec: float,
) -> dict[str, object]:
    expected_protocol = _PROTOCOL_BY_MODE.get(mode)
    profile_id = endpoint.get("local_probe_profile_id")
    if (
        expected_protocol is None
        or not isinstance(profile_id, str)
        or _PROFILE_ID_RE.fullmatch(profile_id) is None
    ):
        return _adapter_failure(
            endpoint,
            mode,
            status="not_run",
            code="probe_material_unavailable",
        )
    profiles = profile_registry.get("profiles")
    if not isinstance(profiles, dict):
        profiles = profile_registry
    entry = profiles.get(profile_id) if isinstance(profiles, dict) else None
    if not isinstance(entry, dict) or set(entry) != {"executable", "argv"}:
        return _adapter_failure(
            endpoint,
            mode,
            status="not_run",
            code="probe_material_unavailable",
        )
    executable = entry.get("executable")
    argv = entry.get("argv")
    if not isinstance(executable, str):
        return _adapter_failure(
            endpoint,
            mode,
            status="not_run",
            code="probe_material_unavailable",
        )
    executable_path = Path(executable)
    if (
        not executable_path.is_absolute()
        or not executable_path.is_file()
        or not os.access(executable_path, os.X_OK)
    ):
        return _adapter_failure(
            endpoint,
            mode,
            status="not_run",
            code="probe_material_unavailable",
        )
    if (
        not isinstance(argv, list)
        or len(argv) > 32
        or any(
            not isinstance(argument, str)
            or not argument
            or len(argument) > 512
            or "\x00" in argument
            for argument in argv
        )
    ):
        return _adapter_failure(
            endpoint,
            mode,
            status="not_run",
            code="probe_material_unavailable",
        )
    command = [str(executable_path.resolve()), *argv]
    try:
        outcome, return_code, stdout, _stderr = _run_bounded_adapter_process(
            command,
            request_bytes=canonical_json_bytes(endpoint),
            timeout_sec=float(timeout_sec),
        )
    except OSError:
        return _adapter_failure(
            endpoint,
            mode,
            status="not_run",
            code="probe_material_unavailable",
        )
    if outcome == "overflow":
        return _adapter_failure(
            endpoint,
            mode,
            status="fail",
            code="adapter_output_too_large",
        )
    if outcome == "timeout":
        return _adapter_failure(
            endpoint,
            mode,
            status="fail",
            code="adapter_timeout",
        )
    if return_code != 0:
        return _adapter_failure(
            endpoint,
            mode,
            status="fail",
            code="adapter_exit_nonzero",
        )
    try:
        response = json.loads(
            stdout.decode("utf-8"),
            object_pairs_hook=_unique_json_object,
        )
    except (UnicodeError, ValueError):
        return _adapter_failure(
            endpoint,
            mode,
            status="fail",
            code="adapter_malformed_response",
        )
    expected_keys = {
        "schema_version",
        "profile_id",
        "protocol",
        "handshake_status",
        "classification",
        "detail_code",
    }
    if (
        not isinstance(response, dict)
        or set(response) != expected_keys
        or response["schema_version"] != 1
        or response["profile_id"] != profile_id
        or response["protocol"] != expected_protocol
        or response["handshake_status"] not in {"pass", "fail", "not_run"}
        or not isinstance(response["classification"], str)
        or _CODE_RE.fullmatch(response["classification"]) is None
        or (
            response["detail_code"] is not None
            and (
                not isinstance(response["detail_code"], str)
                or _CODE_RE.fullmatch(response["detail_code"]) is None
            )
        )
    ):
        return _adapter_failure(
            endpoint,
            mode,
            status="fail",
            code="adapter_malformed_response",
        )
    return response


def transport_stage_from_adapter(
    mode: str,
    adapter_result: dict[str, object],
) -> dict[str, object]:
    if mode not in _PROTOCOL_BY_MODE:
        return _stage("fail", code="unsupported_probe_mode")
    status = adapter_result.get("handshake_status")
    classification = adapter_result.get("classification")
    detail_code = adapter_result.get("detail_code")
    if status not in {"pass", "fail", "not_run"}:
        return _stage("fail", code="adapter_malformed_response")
    if status == "pass" and (
        adapter_result.get("schema_version") != 1
        or adapter_result.get("protocol") != _PROTOCOL_BY_MODE[mode]
        or not isinstance(adapter_result.get("profile_id"), str)
        or _PROFILE_ID_RE.fullmatch(str(adapter_result["profile_id"])) is None
    ):
        return _stage("fail", code="adapter_malformed_response")
    if status == "pass" and classification == "viability_hint":
        return _stage(
            "not_run",
            code=_safe_result_code(
                detail_code,
                "protocol_response_missing",
            ),
        )
    return _stage(
        str(status),
        code=(
            None
            if status == "pass"
            else _safe_result_code(
                detail_code,
                "transport_handshake_failed"
                if status == "fail"
                else "probe_material_unavailable",
            )
        ),
    )


def _apply_adapter_result(
    result: dict[str, object],
    mode: str,
    adapter_response: dict[str, object],
) -> None:
    stage = transport_stage_from_adapter(mode, adapter_response)
    result["stages"]["transport_handshake"] = stage
    result["transport"] = {
        "profile_code": result["endpoint"]["transport_profile"],
        "handshake_status": stage["status"],
        "classification": _safe_result_code(
            adapter_response.get("classification"),
            "adapter_failure",
        ),
        "detail_code": stage["code"],
    }


def _run_hysteria_target(
    result: dict[str, object],
    endpoint: dict[str, object],
    *,
    profile_registry: dict[str, object],
    timeout_sec: float,
) -> None:
    requested_families = [
        family
        for family in ALLOWED_ADDRESS_FAMILIES
        if family in endpoint["address_families"]
    ]
    try:
        dns = dataplane_probe._resolve_dns(
            str(endpoint["host"]),
            int(endpoint["port"]),
        )
    except (OSError, RuntimeError):
        result["stages"]["dns"] = _stage("fail", code="dns_lookup_failed")
        result["address_family_status"] = _family_status(
            requested_families,
            [],
            dns_status="fail",
        )
        result["stages"]["transport_handshake"] = _stage(
            "not_run",
            code="prerequisite_failed",
        )
        result["transport"]["handshake_status"] = "not_run"
        result["transport"]["classification"] = "prerequisite_failed"
        result["transport"]["detail_code"] = "prerequisite_failed"
        return

    resolved_by_family: dict[str, list[str]] = {
        family: [] for family in ALLOWED_ADDRESS_FAMILIES
    }
    for raw_address in dns.get("resolved_ips", []):
        address = str(raw_address)
        family = _family_for_ip(address)
        if (
            family in requested_families
            and address not in resolved_by_family[family]
        ):
            resolved_by_family[family].append(address)
    for family in requested_families:
        resolved_by_family[family].sort(
            key=lambda address: int(ipaddress.ip_address(address))
        )

    if not any(resolved_by_family[family] for family in requested_families):
        result["stages"]["dns"] = _stage(
            "fail",
            code="dns_requested_family_unavailable",
        )
        result["address_family_status"] = {
            family: (
                "fail" if family in requested_families else "not_applicable"
            )
            for family in ALLOWED_ADDRESS_FAMILIES
        }
        result["stages"]["transport_handshake"] = _stage(
            "not_run",
            code="prerequisite_failed",
        )
        result["transport"]["handshake_status"] = "not_run"
        result["transport"]["classification"] = "prerequisite_failed"
        result["transport"]["detail_code"] = "prerequisite_failed"
        return

    result["stages"]["dns"] = _stage("pass")
    family_status = {
        family: (
            "not_run" if family in requested_families else "not_applicable"
        )
        for family in ALLOWED_ADDRESS_FAMILIES
    }
    attempts: list[
        tuple[str, dict[str, object], dict[str, object]]
    ] = []
    for family in requested_families:
        addresses = resolved_by_family[family]
        if not addresses:
            family_status[family] = "fail"
            continue
        adapter_endpoint = copy.deepcopy(endpoint)
        adapter_endpoint["host"] = addresses[0]
        adapter_endpoint["address_families"] = [family]
        response = run_transport_adapter(
            "hysteria_handshake",
            adapter_endpoint,
            profile_registry=profile_registry,
            timeout_sec=timeout_sec,
        )
        stage = transport_stage_from_adapter("hysteria_handshake", response)
        family_status[family] = str(stage["status"])
        attempts.append((family, stage, response))

    result["address_family_status"] = family_status
    selected_attempt = next(
        (
            attempt
            for desired_status in ("pass", "fail", "not_run")
            for attempt in attempts
            if attempt[1]["status"] == desired_status
        ),
        None,
    )
    if selected_attempt is None:
        result["stages"]["transport_handshake"] = _stage(
            "not_run",
            code="prerequisite_failed",
        )
        result["transport"]["handshake_status"] = "not_run"
        result["transport"]["classification"] = "prerequisite_failed"
        result["transport"]["detail_code"] = "prerequisite_failed"
        return
    _apply_adapter_result(
        result,
        "hysteria_handshake",
        selected_attempt[2],
    )


def run_manifest_target(
    target: dict[str, object],
    *,
    timeout_sec: float,
    profile_registry: dict[str, object],
) -> dict[str, object]:
    endpoint = target["endpoint"]
    mode = endpoint["probe_mode"]
    if mode not in ALLOWED_PROBE_MODES:
        raise ManifestError("unsupported_probe_mode")
    result = _empty_target_result(target)
    if mode in {"google_https", "canonical_https_large_body"}:
        https_result = probe_https_large_body(
            host=str(endpoint["host"]),
            port=int(endpoint["port"]),
            sni=str(endpoint["sni"] or endpoint["host"]),
            path=str(endpoint["http_path"]),
            min_body_bytes=int(endpoint["min_body_bytes"]),
            address_families=list(endpoint["address_families"]),
            timeout_sec=timeout_sec,
        )
        for stage_name in ("dns", "tcp", "tls", "http_large_body"):
            result["stages"][stage_name] = https_result["stages"][stage_name]
        result["address_family_status"] = https_result["address_family_status"]
    elif mode in {"delivery_tls", "xhttp_handshake"}:
        selected_address, selected_family = _probe_delivery_families(
            result,
            endpoint,
            timeout_sec=timeout_sec,
        )
        if mode == "xhttp_handshake":
            if selected_address is not None and selected_family is not None:
                adapter_endpoint = copy.deepcopy(endpoint)
                adapter_endpoint["host"] = selected_address
                adapter_endpoint["address_families"] = [selected_family]
                response = run_transport_adapter(
                    mode,
                    adapter_endpoint,
                    profile_registry=profile_registry,
                    timeout_sec=timeout_sec,
                )
                _apply_adapter_result(result, mode, response)
            else:
                result["stages"]["transport_handshake"] = _stage(
                    "not_run",
                    code="prerequisite_failed",
                )
                result["transport"]["handshake_status"] = "not_run"
                result["transport"]["classification"] = "prerequisite_failed"
                result["transport"]["detail_code"] = "prerequisite_failed"
    else:
        _run_hysteria_target(
            result,
            endpoint,
            profile_registry=profile_registry,
            timeout_sec=timeout_sec,
        )

    required = list(target["required_stages"])
    failed_code = next(
        (
            result["stages"][stage]["code"]
            for stage in required
            if result["stages"][stage]["status"] == "fail"
            and result["stages"][stage]["code"] is not None
        ),
        None,
    )
    not_run_code = next(
        (
            result["stages"][stage]["code"]
            for stage in required
            if result["stages"][stage]["status"] == "not_run"
            and result["stages"][stage]["code"] is not None
        ),
        None,
    )
    result["detail_code"] = failed_code or not_run_code
    return result


def _runner_error_target(target: dict[str, object]) -> dict[str, object]:
    result = _empty_target_result(target)
    required = set(target["required_stages"])
    for stage_name in required:
        result["stages"][stage_name] = _stage(
            "not_run",
            code="runner_error",
        )
    if "transport_handshake" in required:
        result["transport"] = {
            "profile_code": result["endpoint"]["transport_profile"],
            "handshake_status": "not_run",
            "classification": "runner_error",
            "detail_code": "runner_error",
        }
    result["detail_code"] = "runner_error"
    return result


def run_manifest(
    manifest: dict[str, object],
    *,
    probe_host_id: str,
    probe_host_label: str,
    probe_public_ip: str | None,
    profile_registry: dict[str, object],
    timeout_sec: float,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
) -> dict[str, object]:
    validated_manifest = validate_manifest(manifest)
    observed_start = started_at or datetime.now(timezone.utc)
    results: list[dict[str, object]] = []
    target_runner_error = False
    for target in validated_manifest["targets"]:
        try:
            result = run_manifest_target(
                target,
                timeout_sec=timeout_sec,
                profile_registry=profile_registry,
            )
        except Exception:
            if target["scope"] == "release_required":
                target_runner_error = True
            result = _runner_error_target(target)
        results.append(result)
    observed_finish = finished_at or datetime.now(timezone.utc)
    required_not_run = any(
        any(
            result["stages"][stage]["status"] == "not_run"
            for stage in target["required_stages"]
        )
        and not any(
            result["stages"][stage]["status"] == "fail"
            for stage in target["required_stages"]
        )
        for target, result in zip(validated_manifest["targets"], results)
        if target["scope"] == "release_required"
    )
    payload = {
        "schema_version": 2,
        "run_id": str(uuid.uuid4()),
        "origin": "ru",
        "probe_host": {
            "id": probe_host_id,
            "label": probe_host_label,
            "public_ip": probe_public_ip or None,
        },
        "runner_version": RUNNER_VERSION,
        "manifest_revision": validated_manifest["manifest_revision"],
        "started_at": _utc_text(observed_start),
        "finished_at": _utc_text(observed_finish),
        "execution_status": (
            "runner_error"
            if target_runner_error
            else ("partial" if required_not_run else "completed")
        ),
        "evidence_code": None,
        "targets": results,
    }
    return validate_run_payload(payload)


def load_profile_registry(path: str | Path) -> dict[str, object]:
    registry_path = Path(path)
    try:
        with registry_path.open("rb") as handle:
            raw = handle.read(MAX_PROFILE_REGISTRY_BYTES + 1)
        if not raw or len(raw) > MAX_PROFILE_REGISTRY_BYTES:
            raise ValueError
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_json_object,
        )
        if not isinstance(payload, dict):
            raise ValueError
        profiles = (
            payload["profiles"]
            if set(payload) == {"profiles"} and isinstance(payload["profiles"], dict)
            else payload
        )
        if (
            not isinstance(profiles, dict)
            or len(profiles) > 128
            or any(_PROFILE_ID_RE.fullmatch(profile_id) is None for profile_id in profiles)
            or any(
                not isinstance(entry, dict)
                or set(entry) != {"executable", "argv"}
                for entry in profiles.values()
            )
        ):
            raise ValueError
        return {"profiles": profiles}
    except (OSError, UnicodeError, ValueError):
        return {"profiles": {}}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run manifest-driven RU-origin checks and emit payload schema v2."
    )
    parser.add_argument("--api-base-url", default=DEFAULT_API_BASE_URL)
    parser.add_argument("--key-id", default=DEFAULT_KEY_ID)
    parser.add_argument("--secret-file", default=str(DEFAULT_SECRET_FILE))
    parser.add_argument("--manifest-cache", default=str(DEFAULT_MANIFEST_CACHE))
    parser.add_argument("--spool-root", default=str(DEFAULT_SPOOL_ROOT))
    parser.add_argument("--probe-host-id", default="mini")
    parser.add_argument("--probe-host-label", default="mini")
    parser.add_argument("--probe-public-ip", default="")
    parser.add_argument("--profile-registry", default=str(DEFAULT_PROFILE_REGISTRY))
    parser.add_argument("--timeout-sec", type=float, default=DEFAULT_TIMEOUT_SEC)
    parser.add_argument("--out", default="")
    return parser


def write_run_artifact(
    payload: dict[str, object],
    *,
    spool_root: str | Path,
    out_path: str | Path | None,
) -> Path:
    raw = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    if out_path is not None:
        destination = Path(out_path)
        _write_private_bytes(destination, raw)
        return destination
    run_id = payload.get("run_id")
    if not isinstance(run_id, str):
        raise ValueError("run_id_required")
    return ru_probe_uploader.write_pending_artifact(
        spool_root,
        run_id,
        raw,
    )


def main() -> int:
    args = build_parser().parse_args()
    try:
        manifest = fetch_manifest(
            api_base_url=str(args.api_base_url),
            key_id=str(args.key_id),
            secret_file=Path(args.secret_file),
            manifest_cache=Path(args.manifest_cache),
            timeout_sec=float(args.timeout_sec),
        )
        payload = run_manifest(
            manifest,
            probe_host_id=str(args.probe_host_id),
            probe_host_label=str(args.probe_host_label),
            probe_public_ip=str(args.probe_public_ip or "") or None,
            profile_registry=load_profile_registry(Path(args.profile_registry)),
            timeout_sec=float(args.timeout_sec),
        )
    except (
        ManifestError,
        RuProbeContractError,
        internal_hmac_client.InternalHmacClientError,
        OSError,
        ValueError,
    ) as exc:
        code = getattr(exc, "code", "runner_error")
        print(str(code), file=sys.stderr)
        return 1
    try:
        artifact_path = write_run_artifact(
            payload,
            spool_root=Path(args.spool_root),
            out_path=Path(args.out) if args.out else None,
        )
    except (OSError, ValueError, ru_probe_uploader.SpoolError) as exc:
        code = getattr(exc, "code", "artifact_write_failed")
        print(str(code), file=sys.stderr)
        return 1
    print(str(artifact_path))
    return 0 if payload["execution_status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
