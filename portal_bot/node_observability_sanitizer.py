"""Bounded, non-sensitive node-observability payloads.

Node-agent metadata and legacy probe records are diagnostic evidence, not a
transport inventory.  Retained/read payloads therefore contain only stable
codes, booleans, and bounded numeric values.
"""

from __future__ import annotations

import json
import re
from typing import Any


TRANSPORT_HEALTH_KEYS = ("dns_resolution", "tcp_connect", "tls_handshake", "reality_target")
TRANSPORT_HEALTH_STATES = frozenset({"healthy", "degraded", "unavailable", "unknown"})
PANEL_STATES = frozenset({"healthy", "failed", "unavailable", "error", "unknown"})
PROBE_STAGES = frozenset(
    {
        "panel_login",
        "panel_status",
        "panel_inbound_lookup",
        "dns",
        "tcp_connect",
        "tls_sni",
        "reality_target",
        "authenticated_egress",
        "collector",
        "probe",
    }
)
ERROR_KINDS = frozenset(
    {
        "",
        "panel_login_failed",
        "panel_probe_failed",
        "inbound_not_found",
        "dns_lookup_failed",
        "tcp_connect_failed",
        "tcp_connect_timeout",
        "tls_handshake_failed",
        "reality_target_mismatch",
        "reality_target_unavailable",
        "probe_failed",
        "prerequisite_failed",
        "authenticated_egress_probe_failed",
        "authenticated_egress_failed",
        "authenticated_egress_unavailable",
        "probe_material_unavailable",
        "probe_material_invalid",
        "probe_material_expired",
        "adapter_timeout",
        "adapter_execution_failed",
        "adapter_output_too_large",
        "adapter_malformed_response",
        "adapter_response_mismatch",
        "adapter_invalid_pass",
        "collector_timeout",
        "collector_exception",
    }
)
PROBE_CLASSIFICATIONS = frozenset(
    {
        "healthy",
        "dns_failure",
        "transport_failure",
        "provider_specific_path",
        "probe_failed",
        "authenticated_egress",
        "authenticated_egress_unavailable",
        "collector_unavailable",
    }
)
TARGET_SEMANTICS = frozenset({"telegram_app_path", "telegram_web_path", "generic_path"})
METRICS_STATES = frozenset({"complete", "missing", "unavailable", "unknown"})
HOSTER_FAMILIES = frozenset(
    {"hetzner", "digitalocean", "vultr", "ovh", "leaseweb", "aws", "google", "azure", "oracle", "contabo", "linode", "netcup", "timeweb"}
)
_ASN_RE = re.compile(r"^AS[0-9]{1,8}$")


def _code(value: object, allowed: frozenset[str], fallback: str = "") -> str:
    candidate = str(value or "").strip().lower()
    return candidate if candidate in allowed else fallback


def safe_error_kind(value: object, fallback: str = "") -> str:
    return _code(value, ERROR_KINDS, fallback)


def safe_probe_stage(value: object, fallback: str = "") -> str:
    candidate = str(value or "").strip().lower()
    if candidate.startswith("tcp_"):
        candidate = "tcp_connect"
    return candidate if candidate in PROBE_STAGES else fallback


def safe_probe_classification(value: object, fallback: str = "") -> str:
    return _code(value, PROBE_CLASSIFICATIONS, fallback)


def safe_hoster_family(value: object) -> str | None:
    candidate = str(value or "").strip().lower()
    return candidate if candidate in HOSTER_FAMILIES else None


def safe_hoster_asn(value: object) -> str | None:
    candidate = str(value or "").strip().upper()
    return candidate if _ASN_RE.fullmatch(candidate) else None


def safe_probe_error_message(error_kind: object) -> str | None:
    """A message field is retained only as its stable error code."""

    return safe_error_kind(error_kind) or None


def _bounded_nonnegative_int(value: object, *, maximum: int = 60_000) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return max(0, min(number, maximum))


def _safe_transport_state(value: object) -> str:
    return _code(value, TRANSPORT_HEALTH_STATES, "unknown")


def sanitize_transport_health(value: object) -> dict[str, object]:
    """Parse a current or legacy record into the safe retained schema."""

    raw: dict[str, Any]
    if isinstance(value, dict):
        raw = value
    elif isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            parsed = {}
        raw = parsed if isinstance(parsed, dict) else {}
    else:
        raw = {}

    panel_state = _code(raw.get("panel_state"), PANEL_STATES, "unknown")
    dataplane_state = _code(raw.get("dataplane_state"), PANEL_STATES, "unknown")
    authenticated_state = _code(raw.get("authenticated_egress_state"), PANEL_STATES, "unknown")
    panel_error_kind = safe_error_kind(raw.get("panel_error_kind"))
    dataplane_error_kind = safe_error_kind(raw.get("dataplane_error_kind"))
    authenticated_error_kind = safe_error_kind(raw.get("authenticated_egress_error_kind"))
    root_cause = (
        panel_error_kind
        or dataplane_error_kind
        or authenticated_error_kind
        or ("edge_reachability_healthy" if dataplane_state == "healthy" else "")
        or None
    )
    payload: dict[str, object] = {
        key: _safe_transport_state(raw.get(key)) for key in TRANSPORT_HEALTH_KEYS
    }
    payload.update(
        {
            "panel_state": panel_state,
            "panel_stage": safe_probe_stage(raw.get("panel_stage")) or None,
            "panel_error_kind": panel_error_kind or None,
            "panel_error_message": safe_probe_error_message(panel_error_kind),
            "dataplane_state": dataplane_state,
            "dataplane_stage": safe_probe_stage(raw.get("dataplane_stage")) or None,
            "dataplane_error_kind": dataplane_error_kind or None,
            "dataplane_error_message": safe_probe_error_message(dataplane_error_kind),
            "edge_reachability_state": dataplane_state,
            "authenticated_egress_state": authenticated_state,
            "authenticated_egress_error_kind": authenticated_error_kind or None,
            "metrics_state": _code(raw.get("metrics_state"), METRICS_STATES, "unknown"),
            "root_cause_summary": root_cause,
            "root_cause_detail": root_cause,
        }
    )
    target_semantics = _code(raw.get("target_semantics"), TARGET_SEMANTICS)
    if target_semantics:
        payload["target_semantics"] = target_semantics
    return payload


def sanitize_runtime_metric_meta(value: object) -> dict[str, object]:
    """Allowlist signed node-agent metadata; reject arbitrary nesting."""

    raw = value if isinstance(value, dict) else {}
    result: dict[str, object] = {}
    for key in ("panel_state", "dataplane_state", "edge_reachability_state", "authenticated_egress_state"):
        state = _code(raw.get(key), PANEL_STATES)
        if state:
            result[key] = state
    for key in ("probe_stage",):
        stage = safe_probe_stage(raw.get(key))
        if stage:
            result[key] = stage
    for key in ("probe_error_kind", "authenticated_egress_error_kind"):
        error_kind = safe_error_kind(raw.get(key))
        if error_kind:
            result[key] = error_kind
    classification = safe_probe_classification(raw.get("probe_classification"))
    if classification:
        result["probe_classification"] = classification
    metrics_state = _code(raw.get("metrics_state"), METRICS_STATES)
    if metrics_state:
        result["metrics_state"] = metrics_state
    for key in ("edge_reachability_ok", "authenticated_egress_ok", "dataplane_ok", "target_ok", "target_check_available"):
        if isinstance(raw.get(key), bool):
            result[key] = raw[key]
    for key in ("latency_ms", "dataplane_rtt_ms"):
        number = _bounded_nonnegative_int(raw.get(key))
        if number is not None:
            result[key] = number
    transport = raw.get("transport_health")
    if isinstance(transport, dict):
        result["transport_health"] = {
            key: _safe_transport_state(transport.get(key)) for key in TRANSPORT_HEALTH_KEYS
        }
    return result
