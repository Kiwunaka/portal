from __future__ import annotations

import copy
import base64
import ipaddress
import json
import os
import re
import struct
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from models import (
    Node,
    RuProbeRun,
    RuProbeTargetResult,
    RuProbeUploaderHeartbeat,
    UserNode,
)
from ru_probe_contract import (
    ALLOWED_ADDRESS_FAMILIES,
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
from transport_catalog import enabled_transport_profiles


# One scheduled six-hour interval. Operators may shorten it, but an offline
# manifest never remains executable for more than one day.
DEFAULT_MANIFEST_MAX_CACHE_AGE_SECONDS = 6 * 60 * 60
MIN_MANIFEST_MAX_CACHE_AGE_SECONDS = 5 * 60
MAX_MANIFEST_MAX_CACHE_AGE_SECONDS = 24 * 60 * 60
DEFAULT_RU_PROBE_RETENTION_DAYS = 180
MIN_RU_PROBE_RETENTION_DAYS = 1
MAX_RU_PROBE_RETENTION_DAYS = 3650
RU_RUN_STALE_AFTER_SECONDS = 7 * 60 * 60
RU_UPLOADER_HEARTBEAT_STALE_AFTER_SECONDS = 45 * 60
RU_HISTORY_DEFAULT_LIMIT = 50
RU_HISTORY_MAX_LIMIT = 200

_CANONICAL_CONFIG_ENV = "RU_PROBE_CANONICAL_TARGETS_JSON"
_RESERVE_CONFIG_ENV = "RU_PROBE_RESERVE_TARGETS_JSON"
_CACHE_AGE_ENV = "RU_PROBE_MANIFEST_MAX_CACHE_AGE_SECONDS"
_RETENTION_DAYS_ENV = "RU_PROBE_RETENTION_DAYS"
_CODE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,127}$")
_TARGET_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:+-]{0,127}$")
_HEARTBEAT_HOST_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")
_UTC_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)
_DNS_LABEL_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")
_SECRET_FIELD_RE = re.compile(
    r"(?i)(?:secret|password|passwd|token|credential|private|reality[_-]?(?:pbk|sid)|"
    r"panel[_-]?(?:user|pass)|subscription|client[_-]?uuid|profile[_-]?material)"
)
_SECRET_VALUE_RE = re.compile(r"(?i)(?:vless|hysteria2?)://|authorization\s*:")

_CANONICAL_FIELDS = {
    "target_id",
    "host",
    "port",
    "sni",
    "address_families",
    "transport_profile",
    "http_path",
    "min_body_bytes",
}
_RESERVE_FIELDS = {
    "target_id",
    "probe_mode",
    "host",
    "port",
    "sni",
    "address_families",
    "transport_profile",
    "local_probe_profile_id",
    "http_path",
}
_HEARTBEAT_FIELDS = {
    "schema_version",
    "probe_host_id",
    "observed_at",
    "service_version",
    "pending_count",
    "blocked_count",
    "quarantine_count",
    "oldest_pending_at",
    "archive_write_ok",
    "disk_free_bytes",
    "disk_state",
    "last_error_code",
}
_HEARTBEAT_DISK_STATES = frozenset({"ok", "low", "critical", "unknown"})
_HEARTBEAT_LAST_ERROR_CODES = frozenset(
    {
        "archive_write_failed",
        "artifact_hash_mismatch",
        "artifact_invalid",
        "blocked_key",
        "disk_critical",
        "disk_low",
        "heartbeat_failed",
        "invalid_success_response",
        "network_error",
        "quarantine_present",
        "response_too_large",
        "spool_recovery_failed",
        "spool_transition_failed",
        "unexpected_response",
    }
)


class RuProbeConfigurationError(ValueError):
    def __init__(self, code: str, *, path: str = "$", message: str | None = None) -> None:
        self.code = code
        self.path = path
        self.message = message or code
        super().__init__(f"{code} at {path}: {self.message}")


class RuProbeServiceError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = str(code)
        super().__init__(self.code)


class RuProbePayloadConflict(RuProbeServiceError):
    def __init__(self) -> None:
        super().__init__("payload_conflict")


class RuProbeReadModelError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = str(code)
        super().__init__(self.code)


@dataclass(frozen=True)
class DeliveryNodeScopeDecision:
    included: bool
    reason: str


@dataclass(frozen=True)
class EvaluatedRuTargetResult:
    target_id: str
    target_kind: str
    scope: str
    node_code: str | None
    endpoint: dict[str, object]
    endpoint_fingerprint: str
    observed_at: datetime
    overall_status: str
    current_eligible: bool
    ineligible_reason: str | None
    reason_code: str | None
    detail: str | None
    stages: dict[str, dict[str, object]]
    address_family_status: dict[str, str]
    transport: dict[str, object]


@dataclass(frozen=True)
class EvaluatedRuRun:
    run_id: str
    schema_version: int
    origin: str
    probe_host_id: str
    probe_host_label: str
    probe_public_ip: str | None
    runner_version: str
    started_at: datetime
    finished_at: datetime
    manifest_revision: str
    execution_status: str
    evidence_code: str | None
    environment_verdict: str
    release_verdict: str
    current_eligible: bool
    ineligible_reason: str | None
    google_reachable: bool
    xhttp_alive: bool
    hysteria_alive: bool
    server_reason: str | None
    server_summary: str
    target_results: tuple[EvaluatedRuTargetResult, ...]
    validated_payload: dict[str, object]


@dataclass(frozen=True)
class StoredRuRun:
    run_db_id: int
    run_id: str
    created: bool
    current_eligible: bool


@dataclass(frozen=True)
class ValidatedRuHeartbeat:
    probe_host_id: str
    observed_at: datetime
    service_version: str
    pending_count: int
    blocked_count: int
    quarantine_count: int
    oldest_pending_at: datetime | None
    archive_write_ok: bool
    disk_free_bytes: int | None
    disk_state: str
    last_error_code: str | None


@dataclass(frozen=True)
class StoredRuHeartbeat:
    created: bool


def _config_fail(code: str, path: str, message: str | None = None) -> None:
    raise RuProbeConfigurationError(code, path=path, message=message)


def _utc_z(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        _config_fail("invalid_now", "$.now", "timezone-aware datetime required")
    return (
        value.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _safe_code(
    value: object, *, path: str, maximum: int = 64, target_id: bool = False
) -> str:
    pattern = _TARGET_ID_RE if target_id else _CODE_RE
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= maximum
        or not pattern.fullmatch(value)
    ):
        _config_fail("invalid_code", path)
    return value


def _safe_host(value: object, *, path: str, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not 1 <= len(value) <= 253:
        _config_fail("invalid_endpoint", path)
    if any(marker in value for marker in ("://", "/", "@", "?", "#")):
        _config_fail("invalid_endpoint", path)
    try:
        ipaddress.ip_address(value)
        return value
    except ValueError:
        pass
    labels = value.split(".")
    if len(labels) < 2 or any(not _DNS_LABEL_RE.fullmatch(label) for label in labels):
        _config_fail("invalid_endpoint", path)
    return value.lower()


def _safe_families(value: object, *, path: str) -> list[str]:
    if not isinstance(value, list) or not value:
        _config_fail("invalid_address_families", path)
    if any(item not in ALLOWED_ADDRESS_FAMILIES for item in value):
        _config_fail("invalid_address_families", path)
    if len(value) != len(set(value)):
        _config_fail("duplicate_address_family", path)
    return [item for item in ALLOWED_ADDRESS_FAMILIES if item in value]


def _safe_path(value: object, *, path: str, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= 256
        or not value.startswith("/")
        or _SECRET_VALUE_RE.search(value)
    ):
        _config_fail("invalid_endpoint", path)
    return value


def _strict_config_rows(name: str) -> list[dict[str, object]] | None:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return None
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise RuProbeConfigurationError("invalid_json", path=name) from exc
    if not isinstance(value, list) or not 1 <= len(value) <= 64:
        _config_fail("invalid_config_shape", name)
    rows: list[dict[str, object]] = []
    for index, item in enumerate(value):
        path = f"{name}[{index}]"
        if not isinstance(item, dict):
            _config_fail("invalid_config_shape", path)
        for key, field_value in item.items():
            if not isinstance(key, str):
                _config_fail("invalid_config_shape", path)
            if _SECRET_FIELD_RE.search(key):
                _config_fail("secret_field", f"{path}.{key}")
            if isinstance(field_value, str) and _SECRET_VALUE_RE.search(field_value):
                _config_fail("secret_value", f"{path}.{key}")
        rows.append(dict(item))
    return rows


def _endpoint(
    *,
    host: str,
    port: int,
    sni: str | None,
    address_families: list[str],
    transport_profile: str,
    probe_mode: str,
    http_path: str | None,
    min_body_bytes: int | None,
    local_probe_profile_id: str | None,
) -> dict[str, object]:
    return {
        "host": host,
        "port": port,
        "sni": sni,
        "address_families": address_families,
        "transport_profile": transport_profile,
        "probe_mode": probe_mode,
        "http_path": http_path,
        "min_body_bytes": min_body_bytes,
        "local_probe_profile_id": local_probe_profile_id,
    }


def _target(
    *,
    target_id: str,
    target_kind: str,
    scope: str,
    node_code: str | None,
    endpoint: dict[str, object],
    required_stages: list[str],
) -> dict[str, object]:
    try:
        validated_endpoint = validate_manifest_endpoint(endpoint)
    except RuProbeContractError as exc:
        raise RuProbeConfigurationError(
            exc.code, path=exc.path, message=exc.message
        ) from exc
    return {
        "target_id": target_id,
        "target_kind": target_kind,
        "scope": scope,
        "node_code": node_code,
        "endpoint": validated_endpoint,
        "endpoint_fingerprint": endpoint_fingerprint(validated_endpoint),
        "required_stages": [stage for stage in ALLOWED_STAGES if stage in required_stages],
    }


def _google_target() -> dict[str, object]:
    return _target(
        target_id="environment:google",
        target_kind="environment",
        scope="release_required",
        node_code=None,
        endpoint=_endpoint(
            host="google.com",
            port=443,
            sni="google.com",
            address_families=list(ALLOWED_ADDRESS_FAMILIES),
            transport_profile="https",
            probe_mode="google_https",
            http_path="/",
            min_body_bytes=65536,
            local_probe_profile_id=None,
        ),
        required_stages=["dns", "tcp", "tls", "http_large_body"],
    )


def _canonical_config_targets() -> list[dict[str, object]]:
    configured = _strict_config_rows(_CANONICAL_CONFIG_ENV)
    if configured is None:
        configured = [
            {"target_id": f"canonical:{host}", "host": host}
            for host in ("pokrov.space", "app.pokrov.space", "api.pokrov.space")
        ]
    targets: list[dict[str, object]] = []
    for index, item in enumerate(configured):
        path = f"{_CANONICAL_CONFIG_ENV}[{index}]"
        unknown = set(item).difference(_CANONICAL_FIELDS)
        if unknown:
            _config_fail("unknown_field", f"{path}.{sorted(unknown)[0]}")
        if not {"target_id", "host"}.issubset(item):
            _config_fail("missing_field", path)
        target_id = _safe_code(
            item["target_id"], path=f"{path}.target_id", maximum=128, target_id=True
        )
        host = _safe_host(item["host"], path=f"{path}.host")
        port = item.get("port", 443)
        if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
            _config_fail("invalid_endpoint", f"{path}.port")
        sni = _safe_host(item.get("sni", host), path=f"{path}.sni", nullable=False)
        families = _safe_families(
            item.get("address_families", list(ALLOWED_ADDRESS_FAMILIES)),
            path=f"{path}.address_families",
        )
        profile = _safe_code(
            item.get("transport_profile", "https"),
            path=f"{path}.transport_profile",
        )
        http_path = _safe_path(item.get("http_path", "/"), path=f"{path}.http_path")
        min_body = item.get("min_body_bytes", 65536)
        if min_body != 65536:
            _config_fail("invalid_body_size", f"{path}.min_body_bytes")
        targets.append(
            _target(
                target_id=target_id,
                target_kind="canonical_public",
                scope="release_required",
                node_code=None,
                endpoint=_endpoint(
                    host=str(host),
                    port=port,
                    sni=str(sni),
                    address_families=families,
                    transport_profile=profile,
                    probe_mode="canonical_https_large_body",
                    http_path=http_path,
                    min_body_bytes=65536,
                    local_probe_profile_id=None,
                ),
                required_stages=["dns", "tcp", "tls", "http_large_body"],
            )
        )
    return targets


def _reserve_config_targets() -> list[dict[str, object]]:
    configured = _strict_config_rows(_RESERVE_CONFIG_ENV)
    if configured is None:
        return []
    targets: list[dict[str, object]] = []
    for index, item in enumerate(configured):
        path = f"{_RESERVE_CONFIG_ENV}[{index}]"
        unknown = set(item).difference(_RESERVE_FIELDS)
        if unknown:
            _config_fail("unknown_field", f"{path}.{sorted(unknown)[0]}")
        required = {
            "target_id",
            "probe_mode",
            "host",
            "transport_profile",
            "local_probe_profile_id",
        }
        if not required.issubset(item):
            _config_fail("missing_field", path)
        mode = item["probe_mode"]
        if mode not in {"xhttp_handshake", "hysteria_handshake"}:
            _config_fail("invalid_probe_mode", f"{path}.probe_mode")
        target_id = _safe_code(
            item["target_id"], path=f"{path}.target_id", maximum=128, target_id=True
        )
        host = _safe_host(item["host"], path=f"{path}.host")
        port = item.get("port", 443)
        if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
            _config_fail("invalid_endpoint", f"{path}.port")
        sni = _safe_host(item.get("sni", host), path=f"{path}.sni", nullable=True)
        families = _safe_families(
            item.get("address_families", list(ALLOWED_ADDRESS_FAMILIES)),
            path=f"{path}.address_families",
        )
        profile = _safe_code(
            item["transport_profile"], path=f"{path}.transport_profile"
        )
        local_profile = _safe_code(
            item["local_probe_profile_id"], path=f"{path}.local_probe_profile_id"
        )
        if mode == "xhttp_handshake":
            http_path = _safe_path(item.get("http_path", "/"), path=f"{path}.http_path")
            target_kind = "reserve_xhttp"
            required_stages = ["dns", "tcp", "tls", "transport_handshake"]
        else:
            if item.get("http_path") is not None:
                _config_fail("invalid_endpoint", f"{path}.http_path")
            http_path = None
            target_kind = "reserve_hysteria"
            required_stages = ["dns", "transport_handshake"]
        targets.append(
            _target(
                target_id=target_id,
                target_kind=target_kind,
                scope="release_required",
                node_code=None,
                endpoint=_endpoint(
                    host=str(host),
                    port=port,
                    sni=str(sni) if sni is not None else None,
                    address_families=families,
                    transport_profile=profile,
                    probe_mode=str(mode),
                    http_path=http_path,
                    min_body_bytes=None,
                    local_probe_profile_id=local_profile,
                ),
                required_stages=required_stages,
            )
        )
    return targets


def _cache_age_seconds() -> int:
    raw = (os.environ.get(_CACHE_AGE_ENV) or "").strip()
    if not raw:
        return DEFAULT_MANIFEST_MAX_CACHE_AGE_SECONDS
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuProbeConfigurationError("invalid_cache_age", path=_CACHE_AGE_ENV) from exc
    if not MIN_MANIFEST_MAX_CACHE_AGE_SECONDS <= value <= MAX_MANIFEST_MAX_CACHE_AGE_SECONDS:
        _config_fail("invalid_cache_age", _CACHE_AGE_ENV)
    return value


def classify_delivery_node_scope(
    node, *, mapped_client_count: int
) -> DeliveryNodeScopeDecision:
    if bool(node.enabled):
        return DeliveryNodeScopeDecision(included=True, reason="enabled")
    if bool(node.is_draining):
        return DeliveryNodeScopeDecision(included=True, reason="draining")
    if int(mapped_client_count or 0) > 0:
        return DeliveryNodeScopeDecision(included=True, reason="mapped_clients")
    if int(node.provisioned_clients_count or 0) > 0:
        return DeliveryNodeScopeDecision(included=True, reason="provisioned_clients")
    return DeliveryNodeScopeDecision(included=False, reason="not_in_scope")


def _delivery_transport_profile_name(node) -> str:
    profiles = enabled_transport_profiles(node)
    if not profiles:
        _config_fail(
            "no_active_transport_profile",
            f"nodes[{getattr(node, 'id', None)}].transport_profiles",
        )
    return _safe_code(
        profiles[0].get("name"),
        path=f"nodes[{getattr(node, 'id', None)}].transport_profiles[0].name",
        maximum=64,
    )


def _delivery_targets(session) -> list[dict[str, object]]:
    nodes = session.query(Node).order_by(Node.code.asc()).all()
    node_ids = [int(node.id) for node in nodes if node.id is not None]
    mapped_counts: dict[int, int] = {}
    if node_ids:
        mapped_counts = {
            int(node_id): int(count)
            for node_id, count in (
                session.query(UserNode.node_id, func.count(UserNode.id))
                .filter(UserNode.node_id.in_(node_ids))
                .group_by(UserNode.node_id)
                .all()
            )
        }
    targets: list[dict[str, object]] = []
    for node in nodes:
        mapped_count = mapped_counts.get(int(node.id), 0) if node.id is not None else 0
        scope_decision = classify_delivery_node_scope(
            node, mapped_client_count=mapped_count
        )
        if not scope_decision.included:
            continue
        code = _safe_code(node.code, path=f"nodes[{node.id}].code", maximum=20)
        host = _safe_host(node.host, path=f"nodes[{node.id}].host")
        raw_port = node.vless_port
        port = 443 if raw_port is None else raw_port
        if (
            isinstance(port, bool)
            or not isinstance(port, int)
            or not 1 <= port <= 65535
        ):
            _config_fail("invalid_endpoint", f"nodes[{node.id}].vless_port")
        sni = _safe_host(
            node.reality_sni,
            path=f"nodes[{node.id}].reality_sni",
            nullable=True,
        )
        transport_profile = _delivery_transport_profile_name(node)
        endpoint = _endpoint(
            host=str(host),
            port=port,
            sni=str(sni) if sni is not None else None,
            address_families=list(ALLOWED_ADDRESS_FAMILIES),
            transport_profile=transport_profile,
            probe_mode="delivery_tls",
            http_path=None,
            min_body_bytes=None,
            local_probe_profile_id=None,
        )
        targets.append(
            _target(
                target_id=f"node:{code}",
                target_kind="delivery_node",
                scope="release_required",
                node_code=code,
                endpoint=endpoint,
                required_stages=["dns", "tcp", "tls"],
            )
        )
    return targets


def build_ru_manifest(session, *, now: datetime) -> dict[str, object]:
    generated_at = _utc_z(now)
    targets = [
        _google_target(),
        *_canonical_config_targets(),
        *_delivery_targets(session),
        *_reserve_config_targets(),
    ]
    if len(targets) > MAX_RUN_TARGETS:
        _config_fail("too_many_targets", "$.targets")
    targets.sort(key=lambda item: str(item["target_id"]))
    seen: set[str] = set()
    for target in targets:
        target_id = str(target["target_id"])
        if target_id in seen:
            _config_fail("duplicate_target_id", f"targets.{target_id}")
        seen.add(target_id)
    return {
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "manifest_revision": manifest_revision(targets),
        "generated_at": generated_at,
        "max_cache_age_seconds": _cache_age_seconds(),
        "targets": targets,
    }


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)


def _normalized_utc(value: datetime, *, path: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise RuProbeContractError("invalid_timestamp", path=path)
    return value.astimezone(timezone.utc)


def _database_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _same_endpoint(left: dict[str, object], right: dict[str, object]) -> bool:
    return canonical_json_bytes(left) == canonical_json_bytes(right)


def _stage_verdict(
    target: dict[str, object], required_stages: list[str]
) -> tuple[str, str | None]:
    for stage_name in required_stages:
        status = str(target["stages"][stage_name]["status"])
        if status == "not_applicable":
            return "failed", "required_stage_not_applicable"
        if status == "fail":
            return "failed", "required_stage_failed"
        if status == "not_run":
            return "incomplete", "required_stage_not_run"
    return "pass", None


def _bounded_summary(value: str, *, maximum: int = 500) -> str:
    return value[:maximum]


def _result_from_target(
    target: dict[str, object],
    *,
    observed_at: datetime,
    overall_status: str,
    current_eligible: bool,
    ineligible_reason: str | None,
    reason_code: str | None,
) -> EvaluatedRuTargetResult:
    detail = target.get("detail")
    return EvaluatedRuTargetResult(
        target_id=str(target["target_id"]),
        target_kind=str(target["target_kind"]),
        scope=str(target["scope"]),
        node_code=str(target["node_code"]) if target["node_code"] is not None else None,
        endpoint=copy.deepcopy(target["endpoint"]),
        endpoint_fingerprint=str(target["endpoint_fingerprint"]),
        observed_at=observed_at,
        overall_status=overall_status,
        current_eligible=current_eligible,
        ineligible_reason=ineligible_reason,
        reason_code=reason_code,
        detail=str(detail)[:500] if detail is not None else None,
        stages=copy.deepcopy(target["stages"]),
        address_family_status=copy.deepcopy(target["address_family_status"]),
        transport=copy.deepcopy(target["transport"]),
    )


def evaluate_ru_run(
    session, payload: dict[str, object], *, now: datetime
) -> EvaluatedRuRun:
    if now.tzinfo is None or now.utcoffset() is None:
        raise RuProbeContractError("invalid_now", path="$.now")
    validated = validate_run_payload(payload)
    finished_at = _parse_utc(str(validated["finished_at"]))
    started_at = _parse_utc(str(validated["started_at"]))
    normalized_now = now.astimezone(timezone.utc)
    if finished_at > normalized_now + timedelta(minutes=5):
        raise RuProbeContractError("future_timestamp", path="$.finished_at")

    current_manifest = build_ru_manifest(session, now=normalized_now)
    expected_targets = {
        str(target["target_id"]): target for target in current_manifest["targets"]
    }
    required_ids = {
        target_id
        for target_id, target in expected_targets.items()
        if target["scope"] == "release_required"
    }
    reported_targets = {
        str(target["target_id"]): target for target in validated["targets"]
    }

    revision_current = (
        validated["manifest_revision"] == current_manifest["manifest_revision"]
    )
    if revision_current:
        unknown_release = sorted(
            target_id
            for target_id, target in reported_targets.items()
            if target["scope"] == "release_required" and target_id not in expected_targets
        )
        if unknown_release:
            raise RuProbeContractError(
                "unknown_release_target",
                path="$.targets",
                message=unknown_release[0],
            )

    identity_current = revision_current
    if identity_current:
        for target_id, reported in reported_targets.items():
            expected = expected_targets.get(target_id)
            if expected is None and reported["scope"] == "diagnostic":
                continue
            if expected is None:
                identity_current = False
                break
            if (
                reported["target_kind"] != expected["target_kind"]
                or reported["scope"] != expected["scope"]
                or reported["node_code"] != expected["node_code"]
                or reported["endpoint_fingerprint"] != expected["endpoint_fingerprint"]
                or not _same_endpoint(reported["endpoint"], expected["endpoint"])
            ):
                identity_current = False
                break

    missing_ids = required_ids.difference(reported_targets)
    execution_status = str(validated["execution_status"])
    if not revision_current or not identity_current:
        run_reason = "superseded_manifest"
        release_verdict = "superseded_manifest"
        run_current_eligible = False
    elif missing_ids:
        run_reason = "missing_required_target"
        release_verdict = "incomplete"
        run_current_eligible = False
    elif execution_status == "blocked_by_access":
        run_reason = str(validated["evidence_code"])
        release_verdict = "blocked_by_access"
        run_current_eligible = False
    elif execution_status == "partial":
        run_reason = "partial_execution"
        release_verdict = "incomplete"
        run_current_eligible = False
    elif execution_status == "runner_error":
        run_reason = "runner_error"
        release_verdict = "incomplete"
        run_current_eligible = False
    else:
        run_reason = None
        release_verdict = "pass"
        run_current_eligible = True

    raw_statuses: dict[str, tuple[str, str | None]] = {}
    for target_id, target in reported_targets.items():
        expected = expected_targets.get(target_id)
        if expected is not None:
            required_stages = list(expected["required_stages"])
        else:
            required_stages = [
                stage
                for stage in ALLOWED_STAGES
                if target["stages"][stage]["status"] != "not_applicable"
            ]
        raw_statuses[target_id] = _stage_verdict(target, required_stages)

    google_status = raw_statuses.get("environment:google")
    google_reachable = google_status is not None and google_status[0] == "pass"
    environment_verdict = (
        "available"
        if google_reachable
        else ("unavailable" if google_status is not None else "unknown")
    )

    target_results: list[EvaluatedRuTargetResult] = []
    for target_id in sorted(reported_targets):
        target = reported_targets[target_id]
        raw_status, raw_reason = raw_statuses[target_id]
        is_diagnostic = target["scope"] == "diagnostic"
        if not revision_current or (not identity_current and not is_diagnostic):
            overall_status = "superseded_manifest"
            eligible = False
            ineligible_reason = "superseded_manifest"
            reason_code = "superseded_manifest"
        elif is_diagnostic:
            overall_status = raw_status
            eligible = False
            ineligible_reason = "diagnostic_only"
            reason_code = raw_reason
        elif not google_reachable and target["target_kind"] == "delivery_node":
            overall_status = "unavailable_probe_host"
            eligible = run_current_eligible
            ineligible_reason = None if eligible else run_reason
            reason_code = "google_unavailable"
        else:
            overall_status = raw_status
            eligible = run_current_eligible
            ineligible_reason = None if eligible else run_reason
            reason_code = raw_reason
        target_results.append(
            _result_from_target(
                target,
                observed_at=finished_at,
                overall_status=overall_status,
                current_eligible=eligible,
                ineligible_reason=ineligible_reason,
                reason_code=reason_code,
            )
        )

    xhttp_alive = any(
        target_id in expected_targets
        and expected_targets[target_id]["target_kind"] == "reserve_xhttp"
        and target["scope"] == "release_required"
        and target["endpoint_fingerprint"]
        == expected_targets[target_id]["endpoint_fingerprint"]
        and target["stages"]["transport_handshake"]["status"] == "pass"
        for target_id, target in reported_targets.items()
    )
    hysteria_alive = any(
        target_id in expected_targets
        and expected_targets[target_id]["target_kind"] == "reserve_hysteria"
        and target["scope"] == "release_required"
        and target["endpoint_fingerprint"]
        == expected_targets[target_id]["endpoint_fingerprint"]
        and target["stages"]["transport_handshake"]["status"] == "pass"
        for target_id, target in reported_targets.items()
    )

    if run_current_eligible:
        required_results = [
            item for item in target_results if item.target_id in required_ids
        ]
        if not google_reachable:
            release_verdict = "fail"
            run_reason = "google_unavailable"
        elif any(item.overall_status == "failed" for item in required_results):
            release_verdict = "fail"
            run_reason = "required_target_failed"
        elif any(item.overall_status != "pass" for item in required_results):
            release_verdict = "incomplete"
            run_reason = "required_target_incomplete"
        else:
            release_verdict = "pass"
            run_reason = None

    if release_verdict == "pass":
        server_reason = None
        server_summary = "Текущий RU manifest выполнен полностью: все обязательные цели прошли."
    elif release_verdict == "superseded_manifest":
        server_reason = "superseded_manifest"
        server_summary = "Запуск относится к устаревшему manifest или endpoint."
    elif release_verdict == "blocked_by_access":
        server_reason = str(validated["evidence_code"])
        server_summary = "Подписанный запуск заблокирован подтверждённым отсутствием доступа."
    elif release_verdict == "incomplete":
        server_reason = run_reason or "incomplete"
        server_summary = "Запуск RU-пробы неполный и не может дать текущий PASS."
    else:
        server_reason = run_reason or "required_target_failed"
        server_summary = "Одна или несколько обязательных RU-проверок не прошли."

    return EvaluatedRuRun(
        run_id=str(validated["run_id"]),
        schema_version=int(validated["schema_version"]),
        origin=str(validated["origin"]),
        probe_host_id=str(validated["probe_host"]["id"]),
        probe_host_label=str(validated["probe_host"]["label"]),
        probe_public_ip=(
            str(validated["probe_host"]["public_ip"])
            if validated["probe_host"]["public_ip"] is not None
            else None
        ),
        runner_version=str(validated["runner_version"]),
        started_at=started_at,
        finished_at=finished_at,
        manifest_revision=str(validated["manifest_revision"]),
        execution_status=execution_status,
        evidence_code=(
            str(validated["evidence_code"])
            if validated["evidence_code"] is not None
            else None
        ),
        environment_verdict=environment_verdict,
        release_verdict=release_verdict,
        current_eligible=run_current_eligible,
        ineligible_reason=None if run_current_eligible else run_reason,
        google_reachable=google_reachable,
        xhttp_alive=xhttp_alive,
        hysteria_alive=hysteria_alive,
        server_reason=server_reason[:64] if server_reason is not None else None,
        server_summary=_bounded_summary(server_summary),
        target_results=tuple(target_results),
        validated_payload=validated,
    )


def _retention_days() -> int:
    raw = (os.environ.get(_RETENTION_DAYS_ENV) or "").strip()
    if not raw:
        return DEFAULT_RU_PROBE_RETENTION_DAYS
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuProbeConfigurationError(
            "invalid_retention_days",
            path=_RETENTION_DAYS_ENV,
        ) from exc
    if not MIN_RU_PROBE_RETENTION_DAYS <= value <= MAX_RU_PROBE_RETENTION_DAYS:
        _config_fail("invalid_retention_days", _RETENTION_DAYS_ENV)
    return value


def _is_run_id_integrity_error(error: IntegrityError) -> bool:
    original = getattr(error, "orig", None)
    diagnostic = getattr(original, "diag", None)
    constraint_name = getattr(diagnostic, "constraint_name", None)
    if constraint_name is not None:
        return constraint_name == "uq_ru_probe_runs_run_id"
    return str(original) == "UNIQUE constraint failed: ru_probe_runs.run_id"


def _is_heartbeat_identity_integrity_error(error: IntegrityError) -> bool:
    original = getattr(error, "orig", None)
    diagnostic = getattr(original, "diag", None)
    constraint_name = getattr(diagnostic, "constraint_name", None)
    if constraint_name is not None:
        return constraint_name == "uq_ru_probe_uploader_heartbeat_host_observed"
    return str(original) == (
        "UNIQUE constraint failed: ru_probe_uploader_heartbeats.probe_host_id, "
        "ru_probe_uploader_heartbeats.observed_at"
    )


def _existing_run_result(
    row: RuProbeRun,
    *,
    artifact_sha256: str,
) -> StoredRuRun:
    if row.artifact_sha256 != artifact_sha256:
        raise RuProbePayloadConflict()
    return StoredRuRun(
        run_db_id=int(row.id),
        run_id=str(row.run_id),
        created=False,
        current_eligible=bool(row.current_eligible),
    )


def _run_row_and_targets(
    evaluated: EvaluatedRuRun,
    *,
    artifact_sha256: str,
    ingest_key_id: str,
    received_at: datetime,
    outside_retention_window: bool,
) -> tuple[RuProbeRun, list[RuProbeTargetResult]]:
    run_current_eligible = (
        bool(evaluated.current_eligible) and not outside_retention_window
    )
    run_ineligible_reason = (
        "outside_retention_window"
        if outside_retention_window
        else evaluated.ineligible_reason
    )
    run = RuProbeRun(
        run_id=evaluated.run_id,
        schema_version=evaluated.schema_version,
        origin=evaluated.origin,
        probe_host_id=evaluated.probe_host_id,
        probe_host_label=evaluated.probe_host_label,
        probe_public_ip=evaluated.probe_public_ip,
        runner_version=evaluated.runner_version,
        started_at=evaluated.started_at,
        finished_at=evaluated.finished_at,
        received_at=received_at,
        manifest_revision=evaluated.manifest_revision,
        execution_status=evaluated.execution_status,
        evidence_code=evaluated.evidence_code,
        environment_verdict=evaluated.environment_verdict,
        release_verdict=evaluated.release_verdict,
        current_eligible=run_current_eligible,
        ineligible_reason=run_ineligible_reason,
        google_reachable=evaluated.google_reachable,
        xhttp_alive=evaluated.xhttp_alive,
        hysteria_alive=evaluated.hysteria_alive,
        server_reason=evaluated.server_reason,
        server_summary=evaluated.server_summary,
        artifact_sha256=artifact_sha256,
        ingest_key_id=ingest_key_id,
        retention_hold=False,
        retention_hold_reason=None,
        retention_held_at=None,
    )
    targets: list[RuProbeTargetResult] = []
    for evaluated_target in evaluated.target_results:
        endpoint = evaluated_target.endpoint
        stages = evaluated_target.stages
        outside_required = (
            outside_retention_window
            and evaluated_target.scope == "release_required"
        )
        target_current_eligible = (
            bool(evaluated_target.current_eligible)
            and not outside_retention_window
        )
        target_ineligible_reason = (
            "outside_retention_window"
            if outside_required
            else evaluated_target.ineligible_reason
        )
        targets.append(
            RuProbeTargetResult(
                target_id=evaluated_target.target_id,
                target_kind=evaluated_target.target_kind,
                scope=evaluated_target.scope,
                node_code=evaluated_target.node_code,
                endpoint_fingerprint=evaluated_target.endpoint_fingerprint,
                endpoint_host=str(endpoint["host"]),
                endpoint_port=int(endpoint["port"]),
                endpoint_sni=(
                    str(endpoint["sni"]) if endpoint["sni"] is not None else None
                ),
                requested_address_families_json=copy.deepcopy(
                    endpoint["address_families"]
                ),
                transport_metadata_json={
                    "address_family_status": copy.deepcopy(
                        evaluated_target.address_family_status
                    ),
                    "transport": copy.deepcopy(evaluated_target.transport),
                },
                transport_profile=str(endpoint["transport_profile"]),
                probe_mode=str(endpoint["probe_mode"]),
                http_path=(
                    str(endpoint["http_path"])
                    if endpoint["http_path"] is not None
                    else None
                ),
                min_body_bytes=(
                    int(endpoint["min_body_bytes"])
                    if endpoint["min_body_bytes"] is not None
                    else None
                ),
                local_probe_profile_id=(
                    str(endpoint["local_probe_profile_id"])
                    if endpoint["local_probe_profile_id"] is not None
                    else None
                ),
                observed_at=evaluated_target.observed_at,
                overall_status=evaluated_target.overall_status,
                current_eligible=target_current_eligible,
                ineligible_reason=target_ineligible_reason,
                dns_status=str(stages["dns"]["status"]),
                dns_latency_ms=stages["dns"]["latency_ms"],
                tcp_status=str(stages["tcp"]["status"]),
                tcp_latency_ms=stages["tcp"]["latency_ms"],
                tls_status=str(stages["tls"]["status"]),
                tls_latency_ms=stages["tls"]["latency_ms"],
                http_large_body_status=str(stages["http_large_body"]["status"]),
                http_large_body_latency_ms=stages["http_large_body"]["latency_ms"],
                transport_handshake_status=str(
                    stages["transport_handshake"]["status"]
                ),
                transport_handshake_latency_ms=stages["transport_handshake"][
                    "latency_ms"
                ],
                ipv4_status=str(evaluated_target.address_family_status["ipv4"]),
                ipv6_status=str(evaluated_target.address_family_status["ipv6"]),
                reported_transport_handshake_status=str(
                    evaluated_target.transport["handshake_status"]
                ),
                reported_transport_classification=str(
                    evaluated_target.transport["classification"]
                ),
                server_reason_code=evaluated_target.reason_code,
                server_detail=evaluated_target.detail,
            )
        )
    return run, targets


def store_evaluated_ru_run(
    session,
    evaluated: EvaluatedRuRun,
    *,
    artifact_sha256: str,
    ingest_key_id: str,
    received_at: datetime,
) -> StoredRuRun:
    if not isinstance(evaluated, EvaluatedRuRun):
        raise TypeError("evaluated must be EvaluatedRuRun")
    if not isinstance(artifact_sha256, str) or re.fullmatch(
        r"[0-9a-f]{64}", artifact_sha256
    ) is None:
        raise ValueError("invalid artifact_sha256")
    if (
        not isinstance(ingest_key_id, str)
        or not 1 <= len(ingest_key_id) <= 128
        or _TARGET_ID_RE.fullmatch(ingest_key_id) is None
    ):
        raise ValueError("invalid ingest_key_id")
    normalized_received_at = _normalized_utc(
        received_at,
        path="$.received_at",
    )
    existing = (
        session.query(RuProbeRun)
        .filter(RuProbeRun.run_id == evaluated.run_id)
        .one_or_none()
    )
    if existing is not None:
        return _existing_run_result(existing, artifact_sha256=artifact_sha256)

    outside_retention_window = evaluated.finished_at < (
        normalized_received_at - timedelta(days=_retention_days())
    )
    run, target_rows = _run_row_and_targets(
        evaluated,
        artifact_sha256=artifact_sha256,
        ingest_key_id=ingest_key_id,
        received_at=normalized_received_at,
        outside_retention_window=outside_retention_window,
    )
    try:
        with session.begin_nested():
            session.add(run)
            session.flush()
            for target_row in target_rows:
                target_row.run_db_id = int(run.id)
            session.add_all(target_rows)
            session.flush()
    except IntegrityError as error:
        if not _is_run_id_integrity_error(error):
            raise
        session.expire_all()
        winner = (
            session.query(RuProbeRun)
            .filter(RuProbeRun.run_id == evaluated.run_id)
            .one_or_none()
        )
        if winner is None:
            raise
        return _existing_run_result(winner, artifact_sha256=artifact_sha256)
    return StoredRuRun(
        run_db_id=int(run.id),
        run_id=evaluated.run_id,
        created=True,
        current_eligible=bool(run.current_eligible),
    )


def _heartbeat_fail(code: str, path: str) -> None:
    raise RuProbeContractError(code, path=path)


def _heartbeat_timestamp(value: object, *, path: str) -> datetime:
    if not isinstance(value, str) or _UTC_TIMESTAMP_RE.fullmatch(value) is None:
        _heartbeat_fail("invalid_timestamp", path)
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)
    except (ValueError, OverflowError):
        _heartbeat_fail("invalid_timestamp", path)
    raise AssertionError("unreachable")


def _heartbeat_count(value: object, *, path: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 10_000_000
    ):
        _heartbeat_fail("invalid_count", path)
    return value


def validate_ru_heartbeat(
    payload: object,
    *,
    now: datetime,
) -> ValidatedRuHeartbeat:
    normalized_now = _normalized_utc(now, path="$.now")
    if not isinstance(payload, dict) or set(payload) != _HEARTBEAT_FIELDS:
        _heartbeat_fail("invalid_heartbeat", "$")
    if type(payload["schema_version"]) is not int:
        _heartbeat_fail("invalid_schema_version", "$.schema_version")
    if payload["schema_version"] != 1:
        _heartbeat_fail("unsupported_schema_version", "$.schema_version")
    probe_host_id = payload["probe_host_id"]
    if (
        not isinstance(probe_host_id, str)
        or _HEARTBEAT_HOST_RE.fullmatch(probe_host_id) is None
    ):
        _heartbeat_fail("invalid_probe_host_id", "$.probe_host_id")
    observed_at = _heartbeat_timestamp(
        payload["observed_at"],
        path="$.observed_at",
    )
    if observed_at > normalized_now + timedelta(minutes=5):
        _heartbeat_fail("future_timestamp", "$.observed_at")
    service_version = payload["service_version"]
    if (
        not isinstance(service_version, str)
        or not 1 <= len(service_version) <= 64
        or any(
            ord(character) < 33 or ord(character) > 126
            for character in service_version
        )
    ):
        _heartbeat_fail("invalid_service_version", "$.service_version")
    pending_count = _heartbeat_count(
        payload["pending_count"],
        path="$.pending_count",
    )
    blocked_count = _heartbeat_count(
        payload["blocked_count"],
        path="$.blocked_count",
    )
    quarantine_count = _heartbeat_count(
        payload["quarantine_count"],
        path="$.quarantine_count",
    )
    oldest_pending_raw = payload["oldest_pending_at"]
    oldest_pending_at = (
        None
        if oldest_pending_raw is None
        else _heartbeat_timestamp(
            oldest_pending_raw,
            path="$.oldest_pending_at",
        )
    )
    if pending_count == 0 and oldest_pending_at is not None:
        _heartbeat_fail("invalid_oldest_pending", "$.oldest_pending_at")
    if pending_count > 0 and oldest_pending_at is None:
        _heartbeat_fail("invalid_oldest_pending", "$.oldest_pending_at")
    if oldest_pending_at is not None and oldest_pending_at > observed_at:
        _heartbeat_fail("invalid_oldest_pending", "$.oldest_pending_at")
    archive_write_ok = payload["archive_write_ok"]
    if not isinstance(archive_write_ok, bool):
        _heartbeat_fail("invalid_archive_state", "$.archive_write_ok")
    disk_free_bytes = payload["disk_free_bytes"]
    if disk_free_bytes is not None and (
        isinstance(disk_free_bytes, bool)
        or not isinstance(disk_free_bytes, int)
        or not 0 <= disk_free_bytes <= 9_223_372_036_854_775_807
    ):
        _heartbeat_fail("invalid_disk_free", "$.disk_free_bytes")
    disk_state = payload["disk_state"]
    if not isinstance(disk_state, str) or disk_state not in _HEARTBEAT_DISK_STATES:
        _heartbeat_fail("invalid_disk_state", "$.disk_state")
    if disk_state == "unknown" and disk_free_bytes is not None:
        _heartbeat_fail("invalid_disk_state", "$.disk_free_bytes")
    if disk_state != "unknown" and disk_free_bytes is None:
        _heartbeat_fail("invalid_disk_state", "$.disk_free_bytes")
    last_error_code = payload["last_error_code"]
    if last_error_code is not None and (
        not isinstance(last_error_code, str)
        or last_error_code not in _HEARTBEAT_LAST_ERROR_CODES
    ):
        _heartbeat_fail("invalid_last_error_code", "$.last_error_code")
    return ValidatedRuHeartbeat(
        probe_host_id=probe_host_id,
        observed_at=observed_at,
        service_version=service_version,
        pending_count=pending_count,
        blocked_count=blocked_count,
        quarantine_count=quarantine_count,
        oldest_pending_at=oldest_pending_at,
        archive_write_ok=archive_write_ok,
        disk_free_bytes=disk_free_bytes,
        disk_state=disk_state,
        last_error_code=last_error_code,
    )


def _heartbeat_matches(
    row: RuProbeUploaderHeartbeat,
    heartbeat: ValidatedRuHeartbeat,
) -> bool:
    return (
        row.probe_host_id == heartbeat.probe_host_id
        and _database_utc(row.observed_at) == heartbeat.observed_at
        and row.service_version == heartbeat.service_version
        and int(row.pending_count) == heartbeat.pending_count
        and int(row.blocked_count) == heartbeat.blocked_count
        and int(row.quarantine_count) == heartbeat.quarantine_count
        and _database_utc(row.oldest_pending_at) == heartbeat.oldest_pending_at
        and bool(row.archive_write_ok) is heartbeat.archive_write_ok
        and row.disk_free_bytes == heartbeat.disk_free_bytes
        and row.disk_state == heartbeat.disk_state
        and row.last_error_code == heartbeat.last_error_code
    )


def _existing_heartbeat_result(
    row: RuProbeUploaderHeartbeat,
    *,
    heartbeat: ValidatedRuHeartbeat,
) -> StoredRuHeartbeat:
    if not _heartbeat_matches(row, heartbeat):
        raise RuProbePayloadConflict()
    return StoredRuHeartbeat(created=False)


def store_ru_heartbeat(
    session,
    heartbeat: ValidatedRuHeartbeat,
    *,
    received_at: datetime,
    ingest_key_id: str,
) -> StoredRuHeartbeat:
    if not isinstance(heartbeat, ValidatedRuHeartbeat):
        raise TypeError("heartbeat must be ValidatedRuHeartbeat")
    normalized_received_at = _normalized_utc(
        received_at,
        path="$.received_at",
    )
    if (
        not isinstance(ingest_key_id, str)
        or not 1 <= len(ingest_key_id) <= 128
        or _TARGET_ID_RE.fullmatch(ingest_key_id) is None
    ):
        raise ValueError("invalid ingest_key_id")
    existing = (
        session.query(RuProbeUploaderHeartbeat)
        .filter(
            RuProbeUploaderHeartbeat.probe_host_id == heartbeat.probe_host_id,
            RuProbeUploaderHeartbeat.observed_at == heartbeat.observed_at,
        )
        .one_or_none()
    )
    if existing is not None:
        return _existing_heartbeat_result(existing, heartbeat=heartbeat)

    row = RuProbeUploaderHeartbeat(
        probe_host_id=heartbeat.probe_host_id,
        observed_at=heartbeat.observed_at,
        received_at=normalized_received_at,
        service_version=heartbeat.service_version,
        pending_count=heartbeat.pending_count,
        blocked_count=heartbeat.blocked_count,
        quarantine_count=heartbeat.quarantine_count,
        oldest_pending_at=heartbeat.oldest_pending_at,
        archive_write_ok=heartbeat.archive_write_ok,
        disk_free_bytes=heartbeat.disk_free_bytes,
        disk_state=heartbeat.disk_state,
        last_error_code=heartbeat.last_error_code,
        ingest_key_id=ingest_key_id,
    )
    try:
        with session.begin_nested():
            session.add(row)
            session.flush()
    except IntegrityError as error:
        if not _is_heartbeat_identity_integrity_error(error):
            raise
        session.expire_all()
        winner = (
            session.query(RuProbeUploaderHeartbeat)
            .filter(
                RuProbeUploaderHeartbeat.probe_host_id
                == heartbeat.probe_host_id,
                RuProbeUploaderHeartbeat.observed_at == heartbeat.observed_at,
            )
            .one_or_none()
        )
        if winner is None:
            raise
        return _existing_heartbeat_result(winner, heartbeat=heartbeat)
    return StoredRuHeartbeat(created=True)


def _read_model_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _read_model_iso(value: datetime | None) -> str | None:
    normalized = _read_model_utc(value)
    if normalized is None:
        return None
    return normalized.isoformat().replace("+00:00", "Z")


def _read_model_now(value: datetime) -> datetime:
    normalized = _read_model_utc(value)
    if normalized is None:
        raise RuProbeReadModelError("invalid_now")
    return normalized


def _read_model_age_seconds(*, now: datetime, sampled_at: datetime | None) -> int | None:
    normalized = _read_model_utc(sampled_at)
    if normalized is None:
        return None
    return max(0, int((now - normalized).total_seconds()))


def _target_result_summary(row: RuProbeTargetResult) -> dict[str, object]:
    metadata = (
        copy.deepcopy(row.transport_metadata_json)
        if isinstance(row.transport_metadata_json, dict)
        else {}
    )
    address_family_status = metadata.get("address_family_status")
    if not isinstance(address_family_status, dict):
        address_family_status = {
            "ipv4": str(row.ipv4_status or "not_run"),
            "ipv6": str(row.ipv6_status or "not_run"),
        }
    transport = metadata.get("transport")
    if not isinstance(transport, dict):
        transport = {
            "handshake_status": str(
                row.reported_transport_handshake_status or "not_run"
            ),
            "classification": str(
                row.reported_transport_classification or "unknown"
            ),
        }
    return {
        "target_id": str(row.target_id or ""),
        "target_kind": str(row.target_kind or ""),
        "scope": str(row.scope or ""),
        "node_code": str(row.node_code or "") or None,
        "observed_at": _read_model_iso(row.observed_at),
        "overall_status": str(row.overall_status or ""),
        "current_eligible": bool(row.current_eligible),
        "ineligible_reason": str(row.ineligible_reason or "") or None,
        "reason_code": str(row.server_reason_code or "") or None,
        "stages": {
            "dns": {
                "status": str(row.dns_status or "not_run"),
                "latency_ms": row.dns_latency_ms,
            },
            "tcp": {
                "status": str(row.tcp_status or "not_run"),
                "latency_ms": row.tcp_latency_ms,
            },
            "tls": {
                "status": str(row.tls_status or "not_run"),
                "latency_ms": row.tls_latency_ms,
            },
            "http_large_body": {
                "status": str(row.http_large_body_status or "not_run"),
                "latency_ms": row.http_large_body_latency_ms,
            },
            "transport_handshake": {
                "status": str(row.transport_handshake_status or "not_run"),
                "latency_ms": row.transport_handshake_latency_ms,
            },
        },
        "address_family_status": {
            "ipv4": str(address_family_status.get("ipv4") or "not_run"),
            "ipv6": str(address_family_status.get("ipv6") or "not_run"),
        },
        "transport": {
            "profile": str(row.transport_profile or ""),
            "probe_mode": str(row.probe_mode or ""),
            "handshake_status": str(
                transport.get("handshake_status")
                or row.reported_transport_handshake_status
                or "not_run"
            ),
            "classification": str(
                transport.get("classification")
                or row.reported_transport_classification
                or "unknown"
            ),
        },
    }


def _run_summary(
    row: RuProbeRun | None,
    *,
    targets: list[RuProbeTargetResult] | None = None,
) -> dict[str, object] | None:
    if row is None:
        return None
    payload: dict[str, object] = {
        "run_db_id": int(row.id),
        "run_id": str(row.run_id or ""),
        "origin": str(row.origin or ""),
        "probe_host_id": str(row.probe_host_id or ""),
        "probe_host_label": str(row.probe_host_label or ""),
        "runner_version": str(row.runner_version or ""),
        "started_at": _read_model_iso(row.started_at),
        "finished_at": _read_model_iso(row.finished_at),
        "received_at": _read_model_iso(row.received_at),
        "manifest_revision": str(row.manifest_revision or ""),
        "execution_status": str(row.execution_status or ""),
        "evidence_code": str(row.evidence_code or "") or None,
        "environment_verdict": str(row.environment_verdict or ""),
        "release_verdict": str(row.release_verdict or ""),
        "current_eligible": bool(row.current_eligible),
        "ineligible_reason": str(row.ineligible_reason or "") or None,
        "google_reachable": row.google_reachable,
        "xhttp_alive": row.xhttp_alive,
        "hysteria_alive": row.hysteria_alive,
        "server_reason": str(row.server_reason or "") or None,
        "server_summary": str(row.server_summary or "") or None,
    }
    if targets is not None:
        payload["targets"] = [_target_result_summary(target) for target in targets]
    return payload


def _ru_status_from_target(value: str) -> tuple[str, str]:
    normalized = str(value or "").strip().lower()
    if normalized == "pass":
        return "ok", "target_pass"
    if normalized == "failed":
        return "failed", "target_failed"
    if normalized == "incomplete":
        return "degraded", "target_incomplete"
    if normalized == "unavailable_probe_host":
        return "unavailable", "google_unavailable"
    if normalized == "superseded_manifest":
        return "degraded", "superseded_manifest"
    return "degraded", "target_unknown"


def _ru_source_row(
    *,
    status: str,
    sampled_at: datetime | None,
    now: datetime,
    threshold_seconds: int,
    reason_code: str,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "status": status,
        "sampled_at": _read_model_iso(sampled_at),
        "age_seconds": _read_model_age_seconds(now=now, sampled_at=sampled_at),
        "threshold_seconds": int(threshold_seconds),
        "reason_code": reason_code,
    }
    if extra:
        payload.update(extra)
    return payload


def get_latest_ru_status(session, *, now: datetime) -> dict[str, object]:
    normalized_now = _read_model_now(now)
    latest_received = (
        session.query(RuProbeRun)
        .order_by(RuProbeRun.received_at.desc(), RuProbeRun.id.desc())
        .first()
    )
    latest_eligible = (
        session.query(RuProbeRun)
        .filter(RuProbeRun.current_eligible == True)
        .order_by(RuProbeRun.finished_at.desc(), RuProbeRun.id.desc())
        .first()
    )
    target_rows: list[RuProbeTargetResult] = []
    if latest_eligible is not None:
        target_rows = (
            session.query(RuProbeTargetResult)
            .filter(RuProbeTargetResult.run_db_id == int(latest_eligible.id))
            .order_by(RuProbeTargetResult.target_id.asc(), RuProbeTargetResult.id.asc())
            .all()
        )
    target_by_node = {
        str(row.node_code or "").strip().lower(): row
        for row in target_rows
        if str(row.node_code or "").strip()
        and str(row.target_kind or "") == "delivery_node"
    }
    known_nodes = session.query(Node).order_by(Node.code.asc(), Node.id.asc()).all()
    sampled_at = (
        _read_model_utc(latest_eligible.finished_at)
        if latest_eligible is not None
        else None
    )
    age_seconds = _read_model_age_seconds(
        now=normalized_now,
        sampled_at=sampled_at,
    )
    stale = bool(
        age_seconds is not None and age_seconds > RU_RUN_STALE_AFTER_SECONDS
    )

    if latest_eligible is None:
        overall_status = "missing"
        overall_reason = "eligible_run_missing"
    elif stale:
        overall_status = "stale"
        overall_reason = "eligible_run_stale"
    elif str(latest_eligible.environment_verdict or "") == "unavailable":
        overall_status = "unavailable"
        overall_reason = "google_unavailable"
    elif str(latest_eligible.release_verdict or "") == "pass":
        overall_status = "ok"
        overall_reason = "current_ru_run"
    elif str(latest_eligible.release_verdict or "") == "fail":
        overall_status = "failed"
        overall_reason = str(latest_eligible.server_reason or "") or "release_failed"
    else:
        overall_status = "degraded"
        overall_reason = (
            str(latest_eligible.server_reason or "")
            or str(latest_eligible.ineligible_reason or "")
            or "release_incomplete"
        )

    environment_verdict = (
        str(latest_eligible.environment_verdict or "")
        if latest_eligible is not None
        else "unknown"
    )
    if latest_eligible is None:
        environment_status = "missing"
        environment_reason = "eligible_run_missing"
    elif stale:
        environment_status = "stale"
        environment_reason = "eligible_run_stale"
    elif environment_verdict == "available":
        environment_status = "ok"
        environment_reason = "google_available"
    elif environment_verdict == "unavailable":
        environment_status = "unavailable"
        environment_reason = "google_unavailable"
    else:
        environment_status = "missing"
        environment_reason = "environment_unknown"
    environment = _ru_source_row(
        status=environment_status,
        sampled_at=sampled_at,
        now=normalized_now,
        threshold_seconds=RU_RUN_STALE_AFTER_SECONDS,
        reason_code=environment_reason,
        extra={"verdict": environment_verdict},
    )

    nodes: list[dict[str, object]] = []
    for node in known_nodes:
        code = str(node.code or "").strip().lower()
        target = target_by_node.get(code)
        if latest_eligible is None:
            node_status = "missing"
            node_reason = "eligible_run_missing"
        elif stale and target is not None:
            node_status = "stale"
            node_reason = "eligible_run_stale"
        elif environment_verdict == "unavailable":
            node_status = "unavailable"
            node_reason = "google_unavailable"
        elif target is None:
            node_status = "missing"
            node_reason = "target_not_in_run"
        else:
            node_status, node_reason = _ru_status_from_target(
                str(target.overall_status or "")
            )
            if target.server_reason_code:
                node_reason = str(target.server_reason_code)
        row = _ru_source_row(
            status=node_status,
            sampled_at=sampled_at if target is not None else None,
            now=normalized_now,
            threshold_seconds=RU_RUN_STALE_AFTER_SECONDS,
            reason_code=node_reason,
            extra={
                "node_code": code,
                "run_id": str(latest_eligible.run_id)
                if latest_eligible is not None and target is not None
                else None,
                "target": _target_result_summary(target)
                if target is not None
                else None,
            },
        )
        nodes.append(row)

    reserve: dict[str, dict[str, object]] = {}
    for key, target_kind in (
        ("xhttp", "reserve_xhttp"),
        ("hysteria", "reserve_hysteria"),
    ):
        target = next(
            (
                row
                for row in target_rows
                if str(row.target_kind or "") == target_kind
            ),
            None,
        )
        if latest_eligible is None or target is None:
            reserve_status = "missing"
            reserve_reason = "reserve_target_missing"
            reserve_sampled_at = None
        elif stale:
            reserve_status = "stale"
            reserve_reason = "eligible_run_stale"
            reserve_sampled_at = sampled_at
        else:
            reserve_status, reserve_reason = _ru_status_from_target(
                str(target.overall_status or "")
            )
            reserve_sampled_at = sampled_at
        reserve[key] = _ru_source_row(
            status=reserve_status,
            sampled_at=reserve_sampled_at,
            now=normalized_now,
            threshold_seconds=RU_RUN_STALE_AFTER_SECONDS,
            reason_code=reserve_reason,
            extra={
                "alive": (
                    bool(latest_eligible.xhttp_alive)
                    if key == "xhttp" and latest_eligible is not None
                    else bool(latest_eligible.hysteria_alive)
                    if latest_eligible is not None
                    else None
                )
            },
        )

    latest_eligible_summary = _run_summary(
        latest_eligible,
        targets=target_rows if latest_eligible is not None else None,
    )
    return {
        "ok": True,
        "generated_at": _read_model_iso(normalized_now),
        "status": overall_status,
        "sampled_at": _read_model_iso(sampled_at),
        "age_seconds": age_seconds,
        "threshold_seconds": RU_RUN_STALE_AFTER_SECONDS,
        "reason_code": overall_reason,
        "environment_verdict": environment_verdict,
        "environment": environment,
        "reserve": reserve,
        "latest_received_attempt": _run_summary(latest_received),
        "latest_eligible_run": latest_eligible_summary,
        "eligible_run": latest_eligible_summary,
        "nodes": nodes,
    }


def _encode_history_cursor(*, finished_at: datetime, row_id: int) -> str:
    normalized = _read_model_utc(finished_at)
    if normalized is None or int(row_id) <= 0:
        raise RuProbeReadModelError("invalid_cursor")
    micros = int(normalized.timestamp() * 1_000_000)
    raw = struct.pack(">qQ", micros, int(row_id))
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_history_cursor(value: str) -> tuple[datetime, int]:
    raw_value = str(value or "").strip()
    if not raw_value or len(raw_value) > 128 or re.fullmatch(
        r"[A-Za-z0-9_-]+", raw_value
    ) is None:
        raise RuProbeReadModelError("invalid_cursor")
    try:
        padding = "=" * (-len(raw_value) % 4)
        raw = base64.urlsafe_b64decode(raw_value + padding)
        if len(raw) != 16:
            raise ValueError("wrong cursor length")
        micros, row_id = struct.unpack(">qQ", raw)
        if row_id <= 0:
            raise ValueError("invalid row id")
        finished_at = datetime.fromtimestamp(
            micros / 1_000_000,
            tz=timezone.utc,
        )
    except (ValueError, OverflowError, struct.error) as exc:
        raise RuProbeReadModelError("invalid_cursor") from exc
    return finished_at, int(row_id)


def _history_filter_datetime(
    value: datetime | None,
    *,
    code: str,
) -> datetime | None:
    if value is None:
        return None
    normalized = _read_model_utc(value)
    if normalized is None:
        raise RuProbeReadModelError(code)
    return normalized


def get_ru_run_history(
    session,
    *,
    node_code: str | None = None,
    from_at: datetime | None = None,
    to_at: datetime | None = None,
    verdict: str | None = None,
    limit: int = RU_HISTORY_DEFAULT_LIMIT,
    cursor: str | None = None,
) -> dict[str, object]:
    try:
        normalized_limit = int(limit)
    except (TypeError, ValueError) as exc:
        raise RuProbeReadModelError("invalid_limit") from exc
    if not 1 <= normalized_limit <= RU_HISTORY_MAX_LIMIT:
        raise RuProbeReadModelError("invalid_limit")
    normalized_from = _history_filter_datetime(from_at, code="invalid_from")
    normalized_to = _history_filter_datetime(to_at, code="invalid_to")
    if (
        normalized_from is not None
        and normalized_to is not None
        and normalized_from > normalized_to
    ):
        raise RuProbeReadModelError("invalid_range")
    normalized_verdict = str(verdict or "").strip().lower()
    allowed_verdicts = {
        "",
        "pass",
        "fail",
        "incomplete",
        "superseded_manifest",
        "blocked_by_access",
    }
    if normalized_verdict not in allowed_verdicts:
        raise RuProbeReadModelError("invalid_verdict")
    wanted_node = str(node_code or "").strip().lower()
    if len(wanted_node) > 32:
        raise RuProbeReadModelError("invalid_node_code")

    query = session.query(RuProbeRun)
    if wanted_node:
        run_ids = (
            session.query(RuProbeTargetResult.run_db_id)
            .filter(func.lower(RuProbeTargetResult.node_code) == wanted_node)
            .distinct()
        )
        query = query.filter(RuProbeRun.id.in_(run_ids))
    if normalized_from is not None:
        query = query.filter(RuProbeRun.finished_at >= normalized_from)
    if normalized_to is not None:
        query = query.filter(RuProbeRun.finished_at <= normalized_to)
    if normalized_verdict:
        query = query.filter(RuProbeRun.release_verdict == normalized_verdict)
    if cursor:
        cursor_finished_at, cursor_id = _decode_history_cursor(cursor)
        query = query.filter(
            (RuProbeRun.finished_at < cursor_finished_at)
            | (
                (RuProbeRun.finished_at == cursor_finished_at)
                & (RuProbeRun.id < cursor_id)
            )
        )
    rows = (
        query.order_by(RuProbeRun.finished_at.desc(), RuProbeRun.id.desc())
        .limit(normalized_limit + 1)
        .all()
    )
    has_more = len(rows) > normalized_limit
    page_rows = rows[:normalized_limit]
    run_ids = [int(row.id) for row in page_rows]
    targets_by_run: dict[int, list[RuProbeTargetResult]] = {
        run_id: [] for run_id in run_ids
    }
    if run_ids:
        targets = (
            session.query(RuProbeTargetResult)
            .filter(RuProbeTargetResult.run_db_id.in_(run_ids))
            .order_by(
                RuProbeTargetResult.run_db_id.asc(),
                RuProbeTargetResult.target_id.asc(),
                RuProbeTargetResult.id.asc(),
            )
            .all()
        )
        for target in targets:
            if wanted_node and str(target.node_code or "").strip().lower() != wanted_node:
                continue
            targets_by_run.setdefault(int(target.run_db_id), []).append(target)
    items = [
        _run_summary(row, targets=targets_by_run.get(int(row.id), []))
        for row in page_rows
    ]
    next_cursor = None
    if has_more and page_rows:
        boundary = page_rows[-1]
        next_cursor = _encode_history_cursor(
            finished_at=boundary.finished_at,
            row_id=int(boundary.id),
        )
    return {
        "items": items,
        "next_cursor": next_cursor,
        "limit": normalized_limit,
    }


def get_ru_uploader_status(session, *, now: datetime) -> dict[str, object]:
    normalized_now = _read_model_now(now)
    heartbeat = (
        session.query(RuProbeUploaderHeartbeat)
        .order_by(
            RuProbeUploaderHeartbeat.observed_at.desc(),
            RuProbeUploaderHeartbeat.id.desc(),
        )
        .first()
    )
    if heartbeat is None:
        return {
            "ok": True,
            "generated_at": _read_model_iso(normalized_now),
            "status": "missing",
            "sampled_at": None,
            "age_seconds": None,
            "threshold_seconds": RU_UPLOADER_HEARTBEAT_STALE_AFTER_SECONDS,
            "reason_code": "uploader_heartbeat_missing",
            "heartbeat": None,
        }
    observed_at = _read_model_utc(heartbeat.observed_at)
    age_seconds = _read_model_age_seconds(
        now=normalized_now,
        sampled_at=observed_at,
    )
    stale = bool(
        age_seconds is not None
        and age_seconds > RU_UPLOADER_HEARTBEAT_STALE_AFTER_SECONDS
    )
    return {
        "ok": True,
        "generated_at": _read_model_iso(normalized_now),
        "status": "stale" if stale else "ok",
        "sampled_at": _read_model_iso(observed_at),
        "age_seconds": age_seconds,
        "threshold_seconds": RU_UPLOADER_HEARTBEAT_STALE_AFTER_SECONDS,
        "reason_code": (
            "uploader_heartbeat_stale" if stale else "uploader_heartbeat_fresh"
        ),
        "heartbeat": {
            "probe_host_id": str(heartbeat.probe_host_id or ""),
            "observed_at": _read_model_iso(heartbeat.observed_at),
            "received_at": _read_model_iso(heartbeat.received_at),
            "service_version": str(heartbeat.service_version or ""),
            "pending_count": int(heartbeat.pending_count or 0),
            "blocked_count": int(heartbeat.blocked_count or 0),
            "quarantine_count": int(heartbeat.quarantine_count or 0),
            "oldest_pending_at": _read_model_iso(heartbeat.oldest_pending_at),
            "archive_write_ok": bool(heartbeat.archive_write_ok),
            "disk_free_bytes": (
                int(heartbeat.disk_free_bytes)
                if heartbeat.disk_free_bytes is not None
                else None
            ),
            "disk_state": str(heartbeat.disk_state or "unknown"),
            "last_error_code": str(heartbeat.last_error_code or "") or None,
        },
    }
