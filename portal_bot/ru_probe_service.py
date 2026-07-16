from __future__ import annotations

import copy
import ipaddress
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from models import Node, UserNode
from ru_probe_contract import (
    ALLOWED_ADDRESS_FAMILIES,
    ALLOWED_STAGES,
    MANIFEST_SCHEMA_VERSION,
    RuProbeContractError,
    canonical_json_bytes,
    endpoint_fingerprint,
    manifest_revision,
    validate_run_payload,
)


# One scheduled six-hour interval. Operators may shorten it, but an offline
# manifest never remains executable for more than one day.
DEFAULT_MANIFEST_MAX_CACHE_AGE_SECONDS = 6 * 60 * 60
MIN_MANIFEST_MAX_CACHE_AGE_SECONDS = 5 * 60
MAX_MANIFEST_MAX_CACHE_AGE_SECONDS = 24 * 60 * 60

_CANONICAL_CONFIG_ENV = "RU_PROBE_CANONICAL_TARGETS_JSON"
_RESERVE_CONFIG_ENV = "RU_PROBE_RESERVE_TARGETS_JSON"
_CACHE_AGE_ENV = "RU_PROBE_MANIFEST_MAX_CACHE_AGE_SECONDS"
_CODE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,127}$")
_TARGET_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:+-]{0,127}$")
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


class RuProbeConfigurationError(ValueError):
    def __init__(self, code: str, *, path: str = "$", message: str | None = None) -> None:
        self.code = code
        self.path = path
        self.message = message or code
        super().__init__(f"{code} at {path}: {self.message}")


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
    return {
        "target_id": target_id,
        "target_kind": target_kind,
        "scope": scope,
        "node_code": node_code,
        "endpoint": endpoint,
        "endpoint_fingerprint": endpoint_fingerprint(endpoint),
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
        port = int(node.vless_port or 443)
        if not 1 <= port <= 65535:
            _config_fail("invalid_endpoint", f"nodes[{node.id}].vless_port")
        sni = _safe_host(
            node.reality_sni,
            path=f"nodes[{node.id}].reality_sni",
            nullable=True,
        )
        endpoint = _endpoint(
            host=str(host),
            port=port,
            sni=str(sni) if sni is not None else None,
            address_families=list(ALLOWED_ADDRESS_FAMILIES),
            transport_profile="legacy_reality_fallback",
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


def _same_endpoint(left: dict[str, object], right: dict[str, object]) -> bool:
    left_copy = copy.deepcopy(left)
    right_copy = copy.deepcopy(right)
    for endpoint in (left_copy, right_copy):
        families = endpoint.get("address_families", [])
        endpoint["address_families"] = [
            family for family in ALLOWED_ADDRESS_FAMILIES if family in families
        ]
    return canonical_json_bytes(left_copy) == canonical_json_bytes(right_copy)


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
