from __future__ import annotations

import copy
import hashlib
import ipaddress
import json
import math
import re
import uuid
from datetime import datetime, timedelta, timezone


MANIFEST_SCHEMA_VERSION = 1
RUN_SCHEMA_VERSION = 2
MAX_RUN_TARGETS = 256
ALLOWED_ADDRESS_FAMILIES = ("ipv4", "ipv6")
ALLOWED_STAGES = (
    "dns",
    "tcp",
    "tls",
    "http_large_body",
    "transport_handshake",
)
ALLOWED_PROBE_MODES = (
    "google_https",
    "canonical_https_large_body",
    "delivery_tls",
    "xhttp_handshake",
    "hysteria_handshake",
)
ALLOWED_STAGE_STATUSES = ("pass", "fail", "not_run", "not_applicable")
ALLOWED_EXECUTION_STATUSES = (
    "completed",
    "partial",
    "runner_error",
    "blocked_by_access",
)
ALLOWED_TARGET_KINDS = (
    "environment",
    "canonical_public",
    "delivery_node",
    "reserve_xhttp",
    "reserve_hysteria",
    "diagnostic",
)
ALLOWED_SCOPES = ("release_required", "diagnostic")
ALLOWED_EVIDENCE_CODES = (
    "network_access_blocked",
    "probe_host_unavailable",
    "probe_host_credentials_missing",
    "probe_profile_unavailable",
)

_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_CODE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,127}$")
_TARGET_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:+-]{0,127}$")
_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)
_DNS_LABEL_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_SENSITIVE_DETAIL_RE = re.compile(
    r"(?ix)(?:"
    r"\bauthorization\b\s*['\"]?\s*:|"
    r"\bbearer\s+[A-Za-z0-9._~+/=-]+|"
    r"\b(?:api[_-]?key|access[_-]?key|client[_-]?secret|session[_-]?token|"
    r"refresh[_-]?token|panel[_-]?(?:pass|user)|password|passwd|secret|token|"
    r"private[_-]?key|reality[_-]?(?:pbk|sid)|uuid|subscription(?:[_-]?url)?|"
    r"sub[_-]?url)\b\s*['\"]?\s*[=:]|"
    r"(?:https?|vless|vmess|trojan|ss|hysteria2?|tuic|wireguard)://"
    r")"
)


class RuProbeContractError(ValueError):
    def __init__(self, code: str, *, path: str = "$", message: str | None = None) -> None:
        self.code = code
        self.path = path
        self.message = message or code
        super().__init__(f"{code} at {path}: {self.message}")


def _fail(code: str, path: str, message: str | None = None) -> None:
    raise RuProbeContractError(code, path=path, message=message)


def _validate_canonical_value(value: object, *, path: str, depth: int = 0) -> None:
    if depth > 64:
        _fail("non_canonical_value", path, "maximum JSON nesting exceeded")
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            _fail("non_canonical_value", path, "non-finite number")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_canonical_value(item, path=f"{path}[{index}]", depth=depth + 1)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                _fail("non_canonical_value", path, "object keys must be strings")
            _validate_canonical_value(item, path=f"{path}.{key}", depth=depth + 1)
        return
    _fail("non_canonical_value", path, f"unsupported type {type(value).__name__}")


def canonical_json_bytes(value: object) -> bytes:
    _validate_canonical_value(value, path="$")
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as exc:
        raise RuProbeContractError(
            "non_canonical_value", path="$", message="value is not canonical JSON"
        ) from exc


def _normalize_set_like(
    value: object,
    *,
    allowed: tuple[str, ...],
    path: str,
) -> list[str]:
    if not isinstance(value, list) or not value:
        _fail("invalid_set", path, "expected a non-empty array")
    if any(not isinstance(item, str) for item in value):
        _fail("invalid_set", path, "set-like values must be strings")
    if len(value) != len(set(value)):
        _fail("duplicate_set_value", path)
    unknown = set(value).difference(allowed)
    if unknown:
        _fail("unknown_set_value", path, f"unknown values: {sorted(unknown)!r}")
    return [item for item in allowed if item in value]


def _normalized_endpoint_for_hash(endpoint: dict[str, object]) -> dict[str, object]:
    if not isinstance(endpoint, dict):
        _fail("invalid_endpoint", "$.endpoint")
    normalized = copy.deepcopy(endpoint)
    if "address_families" in normalized:
        normalized["address_families"] = _normalize_set_like(
            normalized["address_families"],
            allowed=ALLOWED_ADDRESS_FAMILIES,
            path="$.endpoint.address_families",
        )
    return normalized


def endpoint_fingerprint(endpoint: dict[str, object]) -> str:
    normalized = _normalized_endpoint_for_hash(endpoint)
    return hashlib.sha256(canonical_json_bytes(normalized)).hexdigest()


def manifest_revision(targets: list[dict[str, object]]) -> str:
    if not isinstance(targets, list):
        _fail("invalid_targets", "$.targets")
    normalized_targets: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, target in enumerate(targets):
        path = f"$.targets[{index}]"
        if not isinstance(target, dict):
            _fail("invalid_target", path)
        target_id = target.get("target_id")
        if not isinstance(target_id, str) or not target_id:
            _fail("invalid_target_id", f"{path}.target_id")
        if target_id in seen:
            _fail("duplicate_target_id", f"{path}.target_id")
        seen.add(target_id)
        normalized = copy.deepcopy(target)
        if "endpoint" in normalized:
            normalized["endpoint"] = _normalized_endpoint_for_hash(normalized["endpoint"])
        if "required_stages" in normalized:
            normalized["required_stages"] = _normalize_set_like(
                normalized["required_stages"],
                allowed=ALLOWED_STAGES,
                path=f"{path}.required_stages",
            )
        normalized_targets.append(normalized)
    normalized_targets.sort(key=lambda item: str(item["target_id"]))
    preimage = {
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "targets": normalized_targets,
    }
    return hashlib.sha256(canonical_json_bytes(preimage)).hexdigest()


def _require_object(
    value: object,
    *,
    path: str,
    required: set[str],
    optional: set[str] | None = None,
) -> dict[str, object]:
    if not isinstance(value, dict):
        _fail("invalid_object", path)
    allowed = required | (optional or set())
    unknown = set(value).difference(allowed)
    if unknown:
        _fail("unknown_field", f"{path}.{sorted(unknown)[0]}")
    missing = required.difference(value)
    if missing:
        _fail("missing_field", f"{path}.{sorted(missing)[0]}")
    return value


def _require_string(
    value: object,
    *,
    path: str,
    minimum: int = 1,
    maximum: int,
    code: str,
) -> str:
    if not isinstance(value, str) or not minimum <= len(value) <= maximum:
        _fail(code, path)
    if _CONTROL_RE.search(value):
        _fail(code, path)
    return value


def _validate_code(
    value: object,
    *,
    path: str,
    maximum: int = 64,
    nullable: bool = False,
    target_id: bool = False,
) -> str | None:
    if value is None and nullable:
        return None
    text = _require_string(
        value, path=path, maximum=maximum, code="invalid_code"
    )
    pattern = _TARGET_ID_RE if target_id else _CODE_RE
    if not pattern.fullmatch(text):
        _fail("invalid_code", path)
    return text


def _validate_hash(value: object, *, path: str) -> str:
    if not isinstance(value, str) or not _HASH_RE.fullmatch(value):
        _fail("invalid_hash", path)
    return value


def _validate_host(value: object, *, path: str, sni: bool = False) -> str:
    text = _require_string(
        value,
        path=path,
        maximum=253,
        code="invalid_sni" if sni else "invalid_host",
    )
    error_code = "invalid_sni" if sni else "invalid_host"
    if any(marker in text for marker in ("://", "/", "@", "?", "#")):
        _fail(error_code, path)
    try:
        parsed_ip = ipaddress.ip_address(text)
    except ValueError:
        parsed_ip = None
    if parsed_ip is not None:
        if sni:
            _fail(error_code, path)
        return text
    if text.endswith(".") or len(text) > 253:
        _fail(error_code, path)
    labels = text.split(".")
    if len(labels) < 2 or any(not _DNS_LABEL_RE.fullmatch(label) for label in labels):
        _fail(error_code, path)
    return text.lower()


def _validate_timestamp(value: object, *, path: str) -> datetime:
    if not isinstance(value, str) or not _TIMESTAMP_RE.fullmatch(value):
        _fail("invalid_timestamp", path)
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise RuProbeContractError("invalid_timestamp", path=path) from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        _fail("invalid_timestamp", path)
    return parsed.astimezone(timezone.utc)


def _validate_nullable_detail(value: object, *, path: str) -> str | None:
    if value is None:
        return None
    detail = _require_string(
        value,
        path=path,
        minimum=0,
        maximum=500,
        code="invalid_detail",
    )
    if _SENSITIVE_DETAIL_RE.search(detail):
        _fail("sensitive_detail", path)
    return detail


def _validate_endpoint(value: object, *, path: str) -> dict[str, object]:
    endpoint = _require_object(
        value,
        path=path,
        required={
            "host",
            "port",
            "sni",
            "address_families",
            "transport_profile",
            "probe_mode",
            "http_path",
            "min_body_bytes",
            "local_probe_profile_id",
        },
    )
    _validate_host(endpoint["host"], path=f"{path}.host")
    port = endpoint["port"]
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        _fail("invalid_port", f"{path}.port")
    if endpoint["sni"] is not None:
        _validate_host(endpoint["sni"], path=f"{path}.sni", sni=True)
    _normalize_set_like(
        endpoint["address_families"],
        allowed=ALLOWED_ADDRESS_FAMILIES,
        path=f"{path}.address_families",
    )
    _validate_code(
        endpoint["transport_profile"],
        path=f"{path}.transport_profile",
        maximum=64,
    )
    mode = endpoint["probe_mode"]
    if mode not in ALLOWED_PROBE_MODES:
        _fail("invalid_probe_mode", f"{path}.probe_mode")
    http_path = endpoint["http_path"]
    if http_path is not None:
        http_path = _require_string(
            http_path,
            path=f"{path}.http_path",
            maximum=256,
            code="invalid_path",
        )
        if not http_path.startswith("/") or _SENSITIVE_DETAIL_RE.search(http_path):
            _fail("invalid_path", f"{path}.http_path")
    min_body = endpoint["min_body_bytes"]
    if min_body is not None and (
        isinstance(min_body, bool)
        or not isinstance(min_body, int)
        or not 1 <= min_body <= 16 * 1024 * 1024
    ):
        _fail("invalid_body_size", f"{path}.min_body_bytes")
    local_profile = _validate_code(
        endpoint["local_probe_profile_id"],
        path=f"{path}.local_probe_profile_id",
        maximum=64,
        nullable=True,
    )
    if mode in {"google_https", "canonical_https_large_body"}:
        if http_path is None or min_body is None or min_body < 65536:
            _fail("invalid_http_probe", path)
        if local_profile is not None:
            _fail("unexpected_probe_profile", f"{path}.local_probe_profile_id")
    elif mode == "delivery_tls":
        if http_path is not None or min_body is not None or local_profile is not None:
            _fail("invalid_delivery_endpoint", path)
    elif mode == "xhttp_handshake":
        if http_path is None or min_body is not None or local_profile is None:
            _fail("invalid_transport_endpoint", path)
    elif mode == "hysteria_handshake":
        if http_path is not None or min_body is not None or local_profile is None:
            _fail("invalid_transport_endpoint", path)
    return endpoint


def validate_manifest_endpoint(endpoint: object) -> dict[str, object]:
    validated = _validate_endpoint(endpoint, path="$.endpoint")
    return json.loads(canonical_json_bytes(validated).decode("utf-8"))


def _validate_stage(value: object, *, path: str) -> dict[str, object]:
    stage = _require_object(
        value,
        path=path,
        required={"status", "latency_ms", "code"},
    )
    status = stage["status"]
    if status not in ALLOWED_STAGE_STATUSES:
        _fail("invalid_stage_status", f"{path}.status")
    latency = stage["latency_ms"]
    if latency is not None and (
        isinstance(latency, bool)
        or not isinstance(latency, int)
        or not 0 <= latency <= 3_600_000
    ):
        _fail("invalid_latency", f"{path}.latency_ms")
    if status in {"not_run", "not_applicable"} and latency is not None:
        _fail("invalid_latency", f"{path}.latency_ms")
    _validate_code(stage["code"], path=f"{path}.code", maximum=64, nullable=True)
    return stage


def _validate_target(value: object, *, path: str) -> dict[str, object]:
    target = _require_object(
        value,
        path=path,
        required={
            "target_id",
            "target_kind",
            "scope",
            "node_code",
            "endpoint",
            "endpoint_fingerprint",
            "stages",
            "address_family_status",
            "transport",
            "detail_code",
            "detail",
        },
    )
    target_id = _validate_code(
        target["target_id"], path=f"{path}.target_id", maximum=128, target_id=True
    )
    target_kind = target["target_kind"]
    if target_kind not in ALLOWED_TARGET_KINDS:
        _fail("invalid_target_kind", f"{path}.target_kind")
    scope = target["scope"]
    if scope not in ALLOWED_SCOPES:
        _fail("invalid_scope", f"{path}.scope")
    node_code = _validate_code(
        target["node_code"], path=f"{path}.node_code", maximum=20, nullable=True
    )
    endpoint = _validate_endpoint(target["endpoint"], path=f"{path}.endpoint")
    reported_fingerprint = _validate_hash(
        target["endpoint_fingerprint"], path=f"{path}.endpoint_fingerprint"
    )
    if reported_fingerprint != endpoint_fingerprint(endpoint):
        _fail("endpoint_fingerprint_mismatch", f"{path}.endpoint_fingerprint")

    if target_kind == "delivery_node":
        if node_code is None or endpoint["probe_mode"] != "delivery_tls":
            _fail("invalid_target_identity", path)
        if scope == "release_required" and target_id != f"node:{node_code}":
            _fail("invalid_target_identity", f"{path}.target_id")
    elif target_kind == "environment":
        if node_code is not None or endpoint["probe_mode"] != "google_https":
            _fail("invalid_target_identity", path)
    elif target_kind == "canonical_public":
        if node_code is not None or endpoint["probe_mode"] != "canonical_https_large_body":
            _fail("invalid_target_identity", path)
    elif target_kind == "reserve_xhttp":
        if node_code is not None or endpoint["probe_mode"] != "xhttp_handshake":
            _fail("invalid_target_identity", path)
    elif target_kind == "reserve_hysteria":
        if node_code is not None or endpoint["probe_mode"] != "hysteria_handshake":
            _fail("invalid_target_identity", path)

    stages = _require_object(
        target["stages"], path=f"{path}.stages", required=set(ALLOWED_STAGES)
    )
    for stage_name in ALLOWED_STAGES:
        _validate_stage(stages[stage_name], path=f"{path}.stages.{stage_name}")

    family_status = _require_object(
        target["address_family_status"],
        path=f"{path}.address_family_status",
        required=set(ALLOWED_ADDRESS_FAMILIES),
    )
    requested_families = set(endpoint["address_families"])
    for family in ALLOWED_ADDRESS_FAMILIES:
        status = family_status[family]
        if status not in ALLOWED_STAGE_STATUSES:
            _fail("invalid_stage_status", f"{path}.address_family_status.{family}")
        if family not in requested_families and status != "not_applicable":
            _fail("invalid_family_status", f"{path}.address_family_status.{family}")

    transport = _require_object(
        target["transport"],
        path=f"{path}.transport",
        required={"profile_code", "handshake_status", "classification", "detail_code"},
    )
    profile_code = _validate_code(
        transport["profile_code"], path=f"{path}.transport.profile_code", maximum=64
    )
    if profile_code != endpoint["transport_profile"]:
        _fail("transport_profile_mismatch", f"{path}.transport.profile_code")
    handshake_status = transport["handshake_status"]
    if handshake_status not in ALLOWED_STAGE_STATUSES:
        _fail("invalid_stage_status", f"{path}.transport.handshake_status")
    if handshake_status != stages["transport_handshake"]["status"]:
        _fail("transport_status_mismatch", f"{path}.transport.handshake_status")
    _validate_code(
        transport["classification"],
        path=f"{path}.transport.classification",
        maximum=64,
    )
    _validate_code(
        transport["detail_code"],
        path=f"{path}.transport.detail_code",
        maximum=64,
        nullable=True,
    )
    _validate_code(
        target["detail_code"], path=f"{path}.detail_code", maximum=64, nullable=True
    )
    _validate_nullable_detail(target["detail"], path=f"{path}.detail")
    return target


def validate_run_payload(payload: object) -> dict[str, object]:
    envelope = _require_object(
        payload,
        path="$",
        required={
            "schema_version",
            "run_id",
            "origin",
            "probe_host",
            "runner_version",
            "manifest_revision",
            "started_at",
            "finished_at",
            "execution_status",
            "evidence_code",
            "targets",
        },
        optional={
            "ok",
            "google_reachable",
            "xhttp_alive",
            "hysteria_alive",
            "classifications",
        },
    )
    if envelope["schema_version"] != RUN_SCHEMA_VERSION:
        _fail("unsupported_schema_version", "$.schema_version")
    run_id = envelope["run_id"]
    if not isinstance(run_id, str):
        _fail("invalid_run_id", "$.run_id")
    try:
        uuid.UUID(run_id)
    except (ValueError, AttributeError) as exc:
        raise RuProbeContractError("invalid_run_id", path="$.run_id") from exc
    if envelope["origin"] != "ru":
        _fail("invalid_origin", "$.origin")
    probe_host = _require_object(
        envelope["probe_host"],
        path="$.probe_host",
        required={"id", "label", "public_ip"},
    )
    _validate_code(probe_host["id"], path="$.probe_host.id", maximum=64)
    _require_string(
        probe_host["label"],
        path="$.probe_host.label",
        maximum=100,
        code="invalid_label",
    )
    if probe_host["public_ip"] is not None:
        value = probe_host["public_ip"]
        if not isinstance(value, str):
            _fail("invalid_ip", "$.probe_host.public_ip")
        try:
            ipaddress.ip_address(value)
        except ValueError as exc:
            raise RuProbeContractError("invalid_ip", path="$.probe_host.public_ip") from exc
    _validate_code(envelope["runner_version"], path="$.runner_version", maximum=32)
    _validate_hash(envelope["manifest_revision"], path="$.manifest_revision")
    started_at = _validate_timestamp(envelope["started_at"], path="$.started_at")
    finished_at = _validate_timestamp(envelope["finished_at"], path="$.finished_at")
    if started_at > finished_at:
        _fail("invalid_time_range", "$.finished_at")
    if finished_at - started_at > timedelta(minutes=60):
        _fail("run_too_long", "$.finished_at")
    if finished_at > datetime.now(timezone.utc) + timedelta(minutes=5):
        _fail("future_timestamp", "$.finished_at")
    execution_status = envelope["execution_status"]
    if execution_status not in ALLOWED_EXECUTION_STATUSES:
        _fail("invalid_execution_status", "$.execution_status")
    evidence_code = envelope["evidence_code"]
    if execution_status == "blocked_by_access":
        if evidence_code not in ALLOWED_EVIDENCE_CODES:
            _fail("invalid_evidence_code", "$.evidence_code")
    elif evidence_code is not None:
        _fail("unexpected_evidence_code", "$.evidence_code")

    targets = envelope["targets"]
    if not isinstance(targets, list):
        _fail("invalid_targets", "$.targets")
    if not targets:
        _fail("missing_target", "$.targets")
    if len(targets) > MAX_RUN_TARGETS:
        _fail("too_many_targets", "$.targets")
    seen_target_ids: set[str] = set()
    validated_targets: list[dict[str, object]] = []
    for index, target in enumerate(targets):
        validated_target = _validate_target(target, path=f"$.targets[{index}]")
        target_id = str(validated_target["target_id"])
        if target_id in seen_target_ids:
            _fail("duplicate_target_id", f"$.targets[{index}].target_id")
        seen_target_ids.add(target_id)
        validated_targets.append(validated_target)

    for key in ("ok", "google_reachable", "xhttp_alive", "hysteria_alive"):
        if key in envelope and not isinstance(envelope[key], bool):
            _fail("invalid_diagnostic_aggregate", f"$.{key}")
    if "classifications" in envelope:
        classifications = envelope["classifications"]
        if not isinstance(classifications, list) or len(classifications) > 256:
            _fail("invalid_classifications", "$.classifications")
        seen_classifications: set[str] = set()
        for index, classification in enumerate(classifications):
            code = _validate_code(
                classification,
                path=f"$.classifications[{index}]",
                maximum=64,
            )
            if code in seen_classifications:
                _fail("duplicate_classification", f"$.classifications[{index}]")
            seen_classifications.add(str(code))

    if execution_status == "blocked_by_access":
        for index, target in enumerate(validated_targets):
            if any(stage["status"] == "pass" for stage in target["stages"].values()):
                _fail("blocked_target_pass", f"$.targets[{index}].stages")
            if any(status == "pass" for status in target["address_family_status"].values()):
                _fail("blocked_target_pass", f"$.targets[{index}].address_family_status")
            if target["transport"]["handshake_status"] == "pass":
                _fail("blocked_target_pass", f"$.targets[{index}].transport")

    return json.loads(canonical_json_bytes(envelope).decode("utf-8"))
