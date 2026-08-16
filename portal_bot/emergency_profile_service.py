"""Signed client leases and exact reserve-first sing-box chains."""

from __future__ import annotations

import copy
import hashlib
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit

try:
    from emergency_catalog_service import (
        MIN_ACTIVE_ENDPOINTS,
        MAX_ACTIVE_ENDPOINTS,
        SUPPORTED_CHAIN_MODES,
    )
    from emergency_eligibility_service import EmergencyEligibility
except ImportError:  # pragma: no cover - package import
    from .emergency_catalog_service import (
        MIN_ACTIVE_ENDPOINTS,
        MAX_ACTIVE_ENDPOINTS,
        SUPPORTED_CHAIN_MODES,
    )
    from .emergency_eligibility_service import EmergencyEligibility


CATALOG_PAYLOAD_TYPE = "pokrov.emergency.catalog"
PROFILE_PAYLOAD_TYPE = "pokrov.emergency.profile"
DISCLOSURE_REVISION = "2026-08-15.1"
OFFLINE_LEASE_MAX_AGE = timedelta(days=7)
CATALOG_REFRESH_AFTER = timedelta(hours=6)
ROUTE_SCOPE = "all_except_ru"
RULESET_HOST = "connect.pokrov.space"
RULESET_PATH = "/rules/geoip-ru.srs"
EMERGENCY_DNS_URL = "https://1.1.1.1/dns-query"

RESERVE_TAG = "POKROV emergency reserve"
OWNED_RU_TAG = "POKROV owned RU"
OWNED_FOREIGN_TAG = "POKROV owned foreign"

_STABLE_ID_RE = re.compile(r"^emg_[a-f0-9]{24}$")
_CATALOG_VERSION_RE = re.compile(r"^emg-[a-f0-9]{32}$")


class EmergencyProfileError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _parse_iso_z(value: object, *, code: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
    except ValueError as exc:
        raise EmergencyProfileError(code) from exc
    if parsed.tzinfo is None:
        raise EmergencyProfileError(code)
    return parsed.astimezone(timezone.utc)


def _iso_z(value: datetime) -> str:
    return _aware_utc(value).isoformat(timespec="seconds").replace("+00:00", "Z")


def emergency_device_binding(install_id: str) -> str:
    value = str(install_id or "").strip()
    if not 8 <= len(value) <= 128:
        raise EmergencyProfileError("install_id_invalid")
    return hashlib.sha256(
        b"pokrov-emergency-device-binding-v1\0" + value.encode("utf-8")
    ).hexdigest()


def _lease_expiry(
    *,
    now: datetime,
    catalog_expiry: datetime,
    access_expiry: datetime | None,
    eligibility_expiry: datetime | None,
) -> datetime:
    if access_expiry is None or eligibility_expiry is None:
        raise EmergencyProfileError("offline_lease_boundary_missing")
    candidates = (
        _aware_utc(now) + OFFLINE_LEASE_MAX_AGE,
        _aware_utc(catalog_expiry),
        _aware_utc(access_expiry),
        _aware_utc(eligibility_expiry),
    )
    value = min(candidates)
    if value <= _aware_utc(now):
        raise EmergencyProfileError("offline_lease_expired")
    return value


def _verification_level(source: object) -> str:
    normalized = str(source or "").strip().lower()
    if normalized == "real_bs":
        return "real_bs"
    if normalized == "synthetic_bs":
        return "synthetic_bs"
    return "ordinary"


def build_safe_catalog_payload(
    *,
    catalog: Mapping[str, Any],
    endpoint_rows: Mapping[str, Any],
    install_id: str,
    access_state: str,
    access_expiry: datetime | None,
    eligibility: EmergencyEligibility,
    supported_modes: Sequence[str],
    now: datetime | None = None,
) -> dict[str, Any]:
    current = _aware_utc(now or datetime.now(timezone.utc))
    catalog_version = str(catalog.get("catalog_version") or "")
    if _CATALOG_VERSION_RE.fullmatch(catalog_version) is None:
        raise EmergencyProfileError("catalog_revision_invalid")
    catalog_expiry = _parse_iso_z(catalog.get("expires_at"), code="catalog_expiry_invalid")
    offline_expiry = _lease_expiry(
        now=current,
        catalog_expiry=catalog_expiry,
        access_expiry=access_expiry,
        eligibility_expiry=eligibility.valid_until,
    )
    modes = tuple(mode for mode in SUPPORTED_CHAIN_MODES if mode in set(supported_modes))
    if "reserve_direct" not in modes:
        raise EmergencyProfileError("reserve_direct_unavailable")

    raw_items = catalog.get("endpoints")
    if not isinstance(raw_items, list) or not MIN_ACTIVE_ENDPOINTS <= len(raw_items) <= MAX_ACTIVE_ENDPOINTS:
        raise EmergencyProfileError("catalog_endpoint_count_invalid")
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for ordinal, raw_item in enumerate(raw_items, start=1):
        if not isinstance(raw_item, dict):
            raise EmergencyProfileError("catalog_endpoint_invalid")
        stable_id = str(raw_item.get("stable_id") or "")
        if _STABLE_ID_RE.fullmatch(stable_id) is None or stable_id in seen:
            raise EmergencyProfileError("catalog_endpoint_identity_invalid")
        seen.add(stable_id)
        row = endpoint_rows.get(stable_id)
        if row is None:
            raise EmergencyProfileError("catalog_endpoint_status_missing")
        verified_at = _aware_utc(getattr(row, "verified_at", None)) if getattr(row, "verified_at", None) else None
        probe_state = str(getattr(row, "probe_state", "") or "")
        if probe_state != "healthy" or verified_at is None:
            status = "unavailable"
        elif verified_at < current - timedelta(hours=24):
            status = "stale"
        else:
            status = "working"
        items.append(
            {
                "id": stable_id,
                "ordinal": ordinal,
                "country_code": str(getattr(row, "exit_country", "") or "").upper(),
                "transport": str(raw_item.get("transport") or ""),
                "status": status,
                "latency_ms": int(getattr(row, "latency_ms", 0) or 0) or None,
                "latency_source": "server_probe",
                "checked_at": _iso_z(verified_at) if verified_at else None,
                "verification": _verification_level(getattr(row, "verification_source", "")),
                "verification_at": _iso_z(verified_at) if verified_at else None,
                "modes": list(modes),
            }
        )

    return {
        "type": CATALOG_PAYLOAD_TYPE,
        "schema_version": 1,
        "catalog_revision": catalog_version,
        "issued_at": _iso_z(current),
        "refresh_after": _iso_z(min(current + CATALOG_REFRESH_AFTER, offline_expiry)),
        "valid_until": _iso_z(catalog_expiry),
        "offline_valid_until": _iso_z(offline_expiry),
        "device_binding": emergency_device_binding(install_id),
        "access": {
            "state": str(access_state or "").strip().lower(),
            "expires_at": _iso_z(_aware_utc(access_expiry)) if access_expiry else None,
        },
        "eligibility": {
            "eligible": bool(eligibility.eligible),
            "source": eligibility.source,
            "country_code": eligibility.country_code,
            "valid_until": _iso_z(_aware_utc(eligibility.valid_until)) if eligibility.valid_until else None,
        },
        "disclosure_revision": DISCLOSURE_REVISION,
        "items": items,
    }


def _proxy_outbound(value: Mapping[str, Any], *, tag: str, detour: str = "") -> dict[str, Any]:
    outbound = copy.deepcopy(dict(value))
    if outbound.get("type") != "vless":
        raise EmergencyProfileError("profile_outbound_type_invalid")
    if not str(outbound.get("server") or "").strip():
        raise EmergencyProfileError("profile_outbound_server_invalid")
    try:
        port = int(outbound.get("server_port"))
    except (TypeError, ValueError) as exc:
        raise EmergencyProfileError("profile_outbound_port_invalid") from exc
    if not 1 <= port <= 65535 or not str(outbound.get("uuid") or "").strip():
        raise EmergencyProfileError("profile_outbound_identity_invalid")
    tls = outbound.get("tls")
    if not isinstance(tls, dict) or tls.get("enabled") is not True:
        raise EmergencyProfileError("profile_outbound_tls_invalid")
    transport = outbound.get("transport")
    if isinstance(transport, dict) and transport.get("type") == "grpc" and "flow" in outbound:
        raise EmergencyProfileError("grpc_flow_forbidden")
    outbound["tag"] = tag
    outbound.pop("domain_resolver", None)
    if detour:
        outbound["detour"] = detour
    else:
        outbound.pop("detour", None)
    return outbound


def build_emergency_singbox_config(
    *,
    reserve_outbound: Mapping[str, Any],
    chain_mode: str,
    foreign_outbound: Mapping[str, Any] | None = None,
    ru_outbound: Mapping[str, Any] | None = None,
    ruleset_base_url: str = "https://connect.pokrov.space/rules",
) -> dict[str, Any]:
    mode = str(chain_mode or "").strip().lower()
    if mode not in SUPPORTED_CHAIN_MODES:
        raise EmergencyProfileError("chain_mode_invalid")

    reserve = _proxy_outbound(reserve_outbound, tag=RESERVE_TAG)
    outbounds: list[dict[str, Any]] = [reserve]
    final_tag = RESERVE_TAG
    if mode == "reserve_foreign":
        if foreign_outbound is None:
            raise EmergencyProfileError("owned_foreign_unavailable")
        outbounds.append(
            _proxy_outbound(foreign_outbound, tag=OWNED_FOREIGN_TAG, detour=RESERVE_TAG)
        )
        final_tag = OWNED_FOREIGN_TAG
    elif mode == "reserve_ru_foreign":
        if ru_outbound is None:
            raise EmergencyProfileError("owned_ru_unavailable")
        if foreign_outbound is None:
            raise EmergencyProfileError("owned_foreign_unavailable")
        outbounds.append(_proxy_outbound(ru_outbound, tag=OWNED_RU_TAG, detour=RESERVE_TAG))
        outbounds.append(
            _proxy_outbound(foreign_outbound, tag=OWNED_FOREIGN_TAG, detour=OWNED_RU_TAG)
        )
        final_tag = OWNED_FOREIGN_TAG

    base_url = str(ruleset_base_url or "").strip().rstrip("/")
    if not base_url.startswith("https://"):
        raise EmergencyProfileError("ruleset_base_url_invalid")
    outbounds.extend(
        [
            {"type": "direct", "tag": "direct"},
            {"type": "block", "tag": "block"},
            {"type": "dns", "tag": "dns-out"},
        ]
    )
    config: dict[str, Any] = {
        "log": {"level": "warn", "timestamp": True},
        "dns": {
            "servers": [
                {"tag": "bootstrap", "address": "local"},
                {
                    "tag": "emergency-dns",
                    "address": EMERGENCY_DNS_URL,
                    "detour": final_tag,
                },
            ],
            "final": "emergency-dns",
        },
        "inbounds": [],
        "outbounds": outbounds,
        "route": {
            "rule_set": [
                {
                    "type": "remote",
                    "tag": "geoip-ru",
                    "format": "binary",
                    "url": f"{base_url}/geoip-ru.srs",
                    "update_interval": "1d",
                    "download_detour": final_tag,
                }
            ],
            "rules": [
                {"rule_set": ["geoip-ru"], "outbound": "direct"},
                {"protocol": "dns", "outbound": "dns-out"},
                {"ip_is_private": True, "outbound": "direct"},
            ],
            "auto_detect_interface": True,
            "default_domain_resolver": {"server": "bootstrap", "strategy": "prefer_ipv4"},
            "final": final_tag,
        },
        "experimental": {"cache_file": {"enabled": True}},
        "_meta": {
            "title": "POKROV Emergency",
            "emergency": True,
            "chain_mode": mode,
            "route_scope": ROUTE_SCOPE,
            "quick_settings_eligible": False,
            "warp": False,
        },
    }
    validate_emergency_singbox_config(config, expected_chain_mode=mode)
    return config


def validate_emergency_singbox_config(
    config: Mapping[str, Any],
    *,
    expected_chain_mode: str | None = None,
) -> None:
    if not isinstance(config, Mapping):
        raise EmergencyProfileError("profile_config_invalid")
    outbounds = config.get("outbounds")
    if not isinstance(outbounds, list):
        raise EmergencyProfileError("profile_outbounds_invalid")
    proxy_tags: set[str] = set()
    detours: dict[str, str] = {}
    all_tags: set[str] = set()
    auxiliary_outbounds: dict[str, str] = {}
    for raw in outbounds:
        if not isinstance(raw, dict):
            raise EmergencyProfileError("profile_outbound_invalid")
        tag = str(raw.get("tag") or "")
        if not tag or tag in all_tags:
            raise EmergencyProfileError("profile_outbound_tag_invalid")
        all_tags.add(tag)
        if raw.get("type") == "vless":
            if not str(raw.get("server") or "").strip():
                raise EmergencyProfileError("profile_outbound_server_invalid")
            try:
                port = int(raw.get("server_port"))
            except (TypeError, ValueError) as exc:
                raise EmergencyProfileError("profile_outbound_port_invalid") from exc
            tls = raw.get("tls")
            reality = tls.get("reality") if isinstance(tls, dict) else None
            if (
                not 1 <= port <= 65535
                or not str(raw.get("uuid") or "").strip()
                or not isinstance(tls, dict)
                or tls.get("enabled") is not True
                or not isinstance(reality, dict)
                or reality.get("enabled") is not True
                or tls.get("insecure") is True
            ):
                raise EmergencyProfileError("profile_outbound_identity_invalid")
            proxy_tags.add(tag)
            detour = str(raw.get("detour") or "")
            if detour:
                detours[tag] = detour
            if detour and "domain_resolver" in raw:
                raise EmergencyProfileError("detoured_outbound_local_resolver_forbidden")
        else:
            auxiliary_outbounds[tag] = str(raw.get("type") or "")
    for source, target in detours.items():
        if source == target or target not in proxy_tags:
            raise EmergencyProfileError("profile_detour_invalid")
    for start in detours:
        seen: set[str] = set()
        cursor = start
        depth = 1
        while cursor in detours:
            if cursor in seen:
                raise EmergencyProfileError("profile_detour_cycle")
            seen.add(cursor)
            cursor = detours[cursor]
            depth += 1
            if depth > 3:
                raise EmergencyProfileError("profile_detour_depth_exceeded")
    route = config.get("route")
    final_tag = str(route.get("final") or "") if isinstance(route, dict) else ""
    if final_tag not in proxy_tags:
        raise EmergencyProfileError("profile_final_invalid")

    meta = config.get("_meta")
    mode = str(expected_chain_mode or "").strip().lower()
    if not mode and isinstance(meta, dict):
        mode = str(meta.get("chain_mode") or "").strip().lower()
    expected_topology = {
        "reserve_direct": ({RESERVE_TAG}, {}, RESERVE_TAG),
        "reserve_foreign": (
            {RESERVE_TAG, OWNED_FOREIGN_TAG},
            {OWNED_FOREIGN_TAG: RESERVE_TAG},
            OWNED_FOREIGN_TAG,
        ),
        "reserve_ru_foreign": (
            {RESERVE_TAG, OWNED_RU_TAG, OWNED_FOREIGN_TAG},
            {OWNED_RU_TAG: RESERVE_TAG, OWNED_FOREIGN_TAG: OWNED_RU_TAG},
            OWNED_FOREIGN_TAG,
        ),
    }
    topology = expected_topology.get(mode)
    if topology is None:
        raise EmergencyProfileError("profile_chain_mode_invalid")
    expected_proxies, expected_detours, expected_final = topology
    if (
        proxy_tags != expected_proxies
        or detours != expected_detours
        or auxiliary_outbounds
        != {"direct": "direct", "block": "block", "dns-out": "dns"}
        or final_tag != expected_final
        or not isinstance(meta, dict)
        or meta.get("emergency") is not True
        or str(meta.get("chain_mode") or "").strip().lower() != mode
        or meta.get("route_scope") != ROUTE_SCOPE
        or meta.get("quick_settings_eligible") is not False
        or meta.get("warp") is not False
    ):
        raise EmergencyProfileError("profile_topology_invalid")

    rule_sets = route.get("rule_set") if isinstance(route, dict) else None
    rules = route.get("rules") if isinstance(route, dict) else None
    expected_rules = [
        {"rule_set": ["geoip-ru"], "outbound": "direct"},
        {"protocol": "dns", "outbound": "dns-out"},
        {"ip_is_private": True, "outbound": "direct"},
    ]
    if (
        not isinstance(rule_sets, list)
        or len(rule_sets) != 1
        or rules != expected_rules
    ):
        raise EmergencyProfileError("profile_ru_route_invalid")
    rule_set = rule_sets[0]
    if not isinstance(rule_set, dict):
        raise EmergencyProfileError("profile_ru_route_invalid")
    try:
        rule_url = urlsplit(str(rule_set.get("url") or ""))
    except ValueError as exc:
        raise EmergencyProfileError("profile_ru_route_invalid") from exc
    if (
        rule_set.get("type") != "remote"
        or rule_set.get("tag") != "geoip-ru"
        or rule_set.get("format") != "binary"
        or rule_set.get("download_detour") != expected_final
        or rule_url.scheme != "https"
        or rule_url.hostname != RULESET_HOST
        or rule_url.port not in {None, 443}
        or rule_url.username
        or rule_url.password
        or rule_url.query
        or rule_url.fragment
        or rule_url.path != RULESET_PATH
    ):
        raise EmergencyProfileError("profile_ru_route_invalid")

    dns = config.get("dns")
    dns_servers = dns.get("servers") if isinstance(dns, dict) else None
    if (
        not isinstance(dns, dict)
        or dns.get("final") != "emergency-dns"
        or dns_servers
        != [
            {"tag": "bootstrap", "address": "local"},
            {
                "tag": "emergency-dns",
                "address": EMERGENCY_DNS_URL,
                "detour": expected_final,
            },
        ]
    ):
        raise EmergencyProfileError("profile_dns_route_invalid")

    def has_forbidden_warp(value: object, *, allow_meta_flag: bool = False) -> bool:
        if isinstance(value, dict):
            for key, child in value.items():
                normalized = str(key).strip().lower()
                if normalized == "warp":
                    if allow_meta_flag and child is False:
                        continue
                    return True
                if has_forbidden_warp(
                    child,
                    allow_meta_flag=allow_meta_flag or normalized == "_meta",
                ):
                    return True
        elif isinstance(value, list):
            return any(has_forbidden_warp(item, allow_meta_flag=allow_meta_flag) for item in value)
        return False

    if has_forbidden_warp(dict(config)):
        raise EmergencyProfileError("profile_warp_forbidden")


def build_profile_payload(
    *,
    catalog_revision: str,
    reserve_id: str,
    chain_mode: str,
    install_id: str,
    access_state: str,
    access_expiry: datetime | None,
    eligibility: EmergencyEligibility,
    catalog_expiry: datetime,
    config_payload: Mapping[str, Any],
    now: datetime | None = None,
) -> dict[str, Any]:
    current = _aware_utc(now or datetime.now(timezone.utc))
    if _CATALOG_VERSION_RE.fullmatch(str(catalog_revision or "")) is None:
        raise EmergencyProfileError("catalog_revision_invalid")
    if _STABLE_ID_RE.fullmatch(str(reserve_id or "")) is None:
        raise EmergencyProfileError("reserve_id_invalid")
    validate_emergency_singbox_config(
        config_payload,
        expected_chain_mode=str(chain_mode or "").strip().lower(),
    )
    offline_expiry = _lease_expiry(
        now=current,
        catalog_expiry=catalog_expiry,
        access_expiry=access_expiry,
        eligibility_expiry=eligibility.valid_until,
    )
    revision_seed = (
        f"{catalog_revision}\0{reserve_id}\0{chain_mode}\0"
        f"{emergency_device_binding(install_id)}\0{_iso_z(current)}"
    ).encode("utf-8")
    return {
        "type": PROFILE_PAYLOAD_TYPE,
        "schema_version": 1,
        "catalog_revision": catalog_revision,
        "profile_revision": "emgp-" + hashlib.sha256(revision_seed).hexdigest()[:24],
        "issued_at": _iso_z(current),
        "offline_valid_until": _iso_z(offline_expiry),
        "device_binding": emergency_device_binding(install_id),
        "reserve_id": reserve_id,
        "chain_mode": chain_mode,
        "route_scope": ROUTE_SCOPE,
        "access_state": str(access_state or "").strip().lower(),
        "access_expires_at": _iso_z(_aware_utc(access_expiry)) if access_expiry else None,
        "eligibility_valid_until": (
            _iso_z(_aware_utc(eligibility.valid_until)) if eligibility.valid_until else None
        ),
        "warp": False,
        "quick_settings_eligible": False,
        "config_format": "singbox-json",
        "config_payload": copy.deepcopy(dict(config_payload)),
    }
