from __future__ import annotations

import json
from typing import Any


LEGACY_REALITY_FALLBACK = "legacy_reality_fallback"
GRPC_443_PRIMARY = "grpc_443_primary"
RESERVE_XHTTP_CDN = "reserve_xhttp_cdn"
RU_BRIDGE_RELAY = "ru_bridge_relay"
OPERATOR_LAB = "operator_lab"
AWG2_LAB = "awg2_lab"
AWG31_LAB = "awg31_lab"

_PROFILE_ORDER = {
    LEGACY_REALITY_FALLBACK: 0,
    GRPC_443_PRIMARY: 1,
    RESERVE_XHTTP_CDN: 2,
    RU_BRIDGE_RELAY: 3,
    OPERATOR_LAB: 4,
    AWG2_LAB: 5,
    AWG31_LAB: 6,
}


def _clean_text(value: Any, *, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def _as_int(value: Any, *, fallback: int = 0) -> int:
    try:
        return int(value or 0)
    except Exception:
        return fallback


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = _clean_text(value).lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return False


def _normalize_kind(value: Any, *, default: str) -> str:
    kind = _clean_text(value, fallback=default).lower()
    if kind in {"reality", "grpc", "xhttp"}:
        return kind
    if "grpc" in kind:
        return "grpc"
    if "http" in kind:
        return "xhttp"
    return "reality"


def _normalize_path(value: Any, *, fallback: str = "/") -> str:
    path = _clean_text(value, fallback=fallback)
    if not path:
        return fallback
    if not path.startswith("/"):
        return f"/{path}"
    return path


def _legacy_transport_profile(node: Any) -> dict[str, Any]:
    inbound_id = _as_int(getattr(node, "inbound_id", 0), fallback=0)
    return {
        "name": LEGACY_REALITY_FALLBACK,
        "enabled": inbound_id > 0,
        "kind": "reality",
        "inbound_id": inbound_id,
        "host": _clean_text(getattr(node, "host", "")),
        "port": max(1, _as_int(getattr(node, "vless_port", 443), fallback=443)),
        "tls_server_name": _clean_text(getattr(node, "reality_sni", "")),
        "reality_public_key": _clean_text(getattr(node, "reality_pbk", "")),
        "reality_short_id": _clean_text(getattr(node, "reality_sid", "")),
        "fingerprint": _clean_text(getattr(node, "fingerprint", ""), fallback="firefox"),
        "flow": _clean_text(getattr(node, "flow", ""), fallback="xtls-rprx-vision"),
    }


def _normalize_profile(node: Any, profile: dict[str, Any]) -> dict[str, Any] | None:
    name = _clean_text(profile.get("name"))
    if not name:
        return None
    # AWG lab material is device-bound and encrypted in generation-specific
    # tables. It must never be accepted from the shared node transport catalog.
    if name in {AWG2_LAB, AWG31_LAB}:
        return None

    legacy = _legacy_transport_profile(node)
    kind = _normalize_kind(
        profile.get("kind"),
        default=("reality" if name == LEGACY_REALITY_FALLBACK else "grpc"),
    )

    normalized = {
        "name": name,
        "enabled": bool(profile.get("enabled", legacy["enabled"] if name == LEGACY_REALITY_FALLBACK else False)),
        "kind": kind,
        "inbound_id": max(0, _as_int(profile.get("inbound_id"), fallback=(legacy["inbound_id"] if name == LEGACY_REALITY_FALLBACK else 0))),
        "host": _clean_text(profile.get("host"), fallback=legacy["host"]),
        "port": max(1, _as_int(profile.get("port"), fallback=legacy["port"])),
        "tls_server_name": _clean_text(profile.get("tls_server_name"), fallback=legacy["tls_server_name"]),
        "fingerprint": _clean_text(profile.get("fingerprint"), fallback=legacy["fingerprint"]),
        "flow": _clean_text(profile.get("flow"), fallback=(legacy["flow"] if kind == "reality" else "")),
    }
    if kind == "reality":
        normalized["reality_public_key"] = _clean_text(profile.get("reality_public_key"), fallback=legacy["reality_public_key"])
        normalized["reality_short_id"] = _clean_text(profile.get("reality_short_id"), fallback=legacy["reality_short_id"])
    if kind == "grpc":
        normalized["grpc_service_name"] = _clean_text(profile.get("grpc_service_name"))
    if kind == "xhttp":
        normalized["xhttp_path"] = _normalize_path(profile.get("xhttp_path"))
    return normalized


def _load_raw_profiles(node: Any) -> list[dict[str, Any]]:
    raw = _clean_text(getattr(node, "transport_profiles_json", ""))
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except Exception:
        return []
    if isinstance(parsed, list):
        return [dict(item) for item in parsed if isinstance(item, dict)]
    if isinstance(parsed, dict):
        rows: list[dict[str, Any]] = []
        for key, value in parsed.items():
            if not isinstance(value, dict):
                continue
            row = dict(value)
            row.setdefault("name", _clean_text(key))
            rows.append(row)
        return rows
    return []


def node_transport_profiles(node: Any, *, include_disabled: bool = True) -> list[dict[str, Any]]:
    rows = _load_raw_profiles(node)
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()

    for raw in rows:
        profile = _normalize_profile(node, raw)
        if not profile:
            continue
        name = str(profile["name"])
        if name in seen:
            continue
        seen.add(name)
        normalized.append(profile)

    if LEGACY_REALITY_FALLBACK not in seen:
        normalized.insert(0, _legacy_transport_profile(node))

    normalized.sort(key=lambda item: (_PROFILE_ORDER.get(str(item.get("name") or ""), 99), str(item.get("name") or "")))
    if include_disabled:
        return normalized
    return [item for item in normalized if bool(item.get("enabled"))]


def has_explicit_transport_profile(node: Any, name: str | None) -> bool:
    """Whether the raw catalog, rather than legacy synthesis, names a profile."""
    requested = _clean_text(name, fallback=LEGACY_REALITY_FALLBACK)
    return any(_clean_text(row.get("name")) == requested for row in _load_raw_profiles(node))


def enabled_transport_profiles(node: Any, *, include_operator_lab: bool = False) -> list[dict[str, Any]]:
    profiles = node_transport_profiles(node, include_disabled=False)
    if include_operator_lab:
        return profiles
    return [item for item in profiles if str(item.get("name") or "") != OPERATOR_LAB]


def transport_profile_by_name(
    node: Any,
    name: str | None,
    *,
    include_disabled: bool = False,
    allow_operator_lab: bool = False,
) -> dict[str, Any]:
    requested = _clean_text(name, fallback=LEGACY_REALITY_FALLBACK)
    # Search the complete catalog first.  An explicit disabled profile is
    # authoritative and must not be mistaken for a missing profile, otherwise
    # legacy synthesis can silently re-enable it from compatibility fields.
    profiles = node_transport_profiles(node, include_disabled=True)
    for profile in profiles:
        if str(profile.get("name") or "") != requested:
            continue
        if not allow_operator_lab and requested == OPERATOR_LAB:
            break
        return profile

    for profile in profiles:
        if str(profile.get("name") or "") != LEGACY_REALITY_FALLBACK:
            continue
        return profile

    return _legacy_transport_profile(node)


def transport_inbound_ids(
    node: Any,
    *,
    include_disabled: bool = False,
    include_operator_lab: bool = False,
) -> list[int]:
    profiles = node_transport_profiles(node, include_disabled=include_disabled)
    out: list[int] = []
    seen: set[int] = set()
    for profile in profiles:
        if not include_operator_lab and str(profile.get("name") or "") == OPERATOR_LAB:
            continue
        inbound_id = max(0, _as_int(profile.get("inbound_id"), fallback=0))
        if inbound_id <= 0 or inbound_id in seen:
            continue
        if not include_disabled and not bool(profile.get("enabled")):
            continue
        seen.add(inbound_id)
        out.append(inbound_id)
    return out
