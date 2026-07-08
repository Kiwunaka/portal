from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from shared_surface_facts import get_product_facts
from transport_catalog import GRPC_443_PRIMARY, LEGACY_REALITY_FALLBACK, OPERATOR_LAB, RESERVE_XHTTP_CDN, RU_BRIDGE_RELAY


NETWORK_ROLLOUT_CONFIG_KEY = "network_rollout_config"
_POLICY_OVERRIDE_KEYS = {
    "transport_profile",
    "dns_policy",
    "routing_mode_default",
    "ip_version_preference",
}
_WARP_POLICY_KEY = "warp_policy"
_WARP_MODES = {"proxy_over_warp", "warp_over_proxy"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _clean_text(value: Any, *, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


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


def _normalize_string_list(values: Any, *, lower: bool = False) -> list[str]:
    if not isinstance(values, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in values:
        text = _clean_text(item)
        if not text:
            continue
        if lower:
            text = text.lower()
        if text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _normalize_int_list(values: Any) -> list[int]:
    if not isinstance(values, list):
        return []
    out: list[int] = []
    seen: set[int] = set()
    for item in values:
        try:
            value = int(item)
        except Exception:
            continue
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _safe_json_loads(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    text = _clean_text(value)
    if not text:
        return {}
    try:
        import json

        return json.loads(text)
    except Exception:
        return {}


def _default_rollout_version() -> str:
    product_facts = get_product_facts()
    versions = product_facts.get("versions", {}) if isinstance(product_facts, dict) else {}
    return _clean_text(
        versions.get("package_catalog_version") or versions.get("ruleset_version"),
        fallback="2026-04-13",
    )


def default_network_rollout_config() -> dict[str, Any]:
    product_facts = get_product_facts()
    versions = product_facts.get("versions", {}) if isinstance(product_facts, dict) else {}
    version = _default_rollout_version()
    recovery = versions.get("support_recovery_order")
    if not isinstance(recovery, list) or not recovery:
        recovery = ["app", "web", "telegram"]
    return {
        "version": version,
        "defaults": {
            "routing_mode_default": "all_except_ru",
            "transport_profile": LEGACY_REALITY_FALLBACK,
            "dns_policy": "ru_direct_split",
            "ip_version_preference": "ipv4_only",
        },
        "carrier_overrides": {},
        "cohort_overrides": {},
        "operator_lab": {
            "enabled": False,
            "allowlist_install_ids": [],
            "allowlist_tg_ids": [],
            "allowlist_node_codes": [],
            "expires_at": None,
        },
        "reserve_xhttp_cdn": {
            "enabled": False,
            "allowlist_node_codes": [],
            "xhttp_path": "/reserve-xhttp",
            "tls_server_name": "cdn.connect.pokrov.space",
        },
        RU_BRIDGE_RELAY: {
            "enabled": False,
            "endpoint_host": "176.123.166.119",
            "endpoint_port": 443,
            "tls_server_name": "www.yandex.ru",
            "reality_public_key": "",
            "reality_short_id": "",
            "fingerprint": "chrome",
            "allowlist_node_codes": [],
            "excluded_node_codes": ["us"],
            "urltest_url": "https://www.gstatic.com/generate_204",
            "urltest_interval": "10m",
            "urltest_tolerance": 80,
        },
        "package_catalog_feed": {
            "version": _clean_text(versions.get("package_catalog_version"), fallback=version),
        },
        "routing_rules_feed": {
            "version": _clean_text(versions.get("ruleset_version"), fallback=version),
        },
        "support_recovery_order": [str(item) for item in recovery if _clean_text(item)],
        _WARP_POLICY_KEY: _normalize_warp_policy({}),
    }


def _normalize_policy_patch(payload: Any, *, defaults: dict[str, Any]) -> dict[str, Any]:
    src = payload if isinstance(payload, dict) else {}
    out = {
        "transport_profile": _clean_text(src.get("transport_profile"), fallback=defaults["transport_profile"]),
        "dns_policy": _clean_text(src.get("dns_policy"), fallback=defaults["dns_policy"]),
        "routing_mode_default": _clean_text(src.get("routing_mode_default"), fallback=defaults["routing_mode_default"]),
        "ip_version_preference": _clean_text(src.get("ip_version_preference"), fallback=defaults["ip_version_preference"]),
    }
    return {key: value for key, value in out.items() if key in _POLICY_OVERRIDE_KEYS and _clean_text(value)}


def _transport_metadata(transport_profile: str, *, version: str) -> dict[str, str]:
    profile = _clean_text(transport_profile, fallback=LEGACY_REALITY_FALLBACK)
    if profile == GRPC_443_PRIMARY:
        transport_kind = "grpc"
        engine_hint = "singbox"
    elif profile in {OPERATOR_LAB, RESERVE_XHTTP_CDN}:
        transport_kind = "xhttp"
        engine_hint = "xray"
    elif profile == RU_BRIDGE_RELAY:
        transport_kind = "ru_bridge"
        engine_hint = "singbox"
    else:
        transport_kind = "reality"
        engine_hint = "singbox"
    return {
        "transport_kind": transport_kind,
        "engine_hint": engine_hint,
        "profile_revision": f"{_clean_text(version, fallback=_default_rollout_version())}:{profile}",
    }


def _normalize_warp_wireguard_config(value: Any) -> dict[str, str] | str:
    if isinstance(value, str):
        return _clean_text(value)
    if not isinstance(value, dict):
        return {}
    aliases = {
        "private-key": ("private-key", "private_key", "privateKey"),
        "local-address-ipv4": ("local-address-ipv4", "local_address_ipv4", "localAddressIpv4", "localAddressIPv4"),
        "local-address-ipv6": ("local-address-ipv6", "local_address_ipv6", "localAddressIpv6", "localAddressIPv6"),
        "peer-public-key": ("peer-public-key", "peer_public_key", "peerPublicKey"),
        "client-id": ("client-id", "client_id", "clientId"),
    }
    out: dict[str, str] = {}
    for canonical, keys in aliases.items():
        for key in keys:
            text = _clean_text(value.get(key))
            if text:
                out[canonical] = text
                break
    return out


def _warp_wireguard_config_available(value: dict[str, str] | str) -> bool:
    if isinstance(value, str):
        return bool(_clean_text(value))
    return bool(value)


def _normalize_warp_account(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    account_id = _clean_text(value.get("account-id") or value.get("account_id") or value.get("accountId"))
    access_token = _clean_text(value.get("access-token") or value.get("access_token") or value.get("accessToken"))
    out: dict[str, str] = {}
    if account_id:
        out["account-id"] = account_id
    if access_token:
        out["access-token"] = access_token
    return out


def _normalize_warp_policy(value: Any, *, include_secrets: bool = False) -> dict[str, Any]:
    src = value if isinstance(value, dict) else {}
    mode = _clean_text(src.get("mode"), fallback="proxy_over_warp")
    if mode not in _WARP_MODES:
        mode = "proxy_over_warp"
    source = _clean_text(src.get("source"), fallback="backend_managed")
    wireguard_config = _normalize_warp_wireguard_config(
        src.get("wireguard_config") or src.get("wireguardConfig") or src.get("wireguard-config")
    )
    account = _normalize_warp_account(src.get("account"))
    enabled = _as_bool(src.get("enabled"))
    wireguard_available = _warp_wireguard_config_available(wireguard_config)
    runtime_ready = enabled and wireguard_available
    state = _clean_text(src.get("state"))
    if runtime_ready:
        state = state or "ready"
    elif enabled:
        state = "waiting_for_backend_provisioning" if not state or state == "ready" else state
    else:
        state = "disabled_until_runtime_proof" if not state or state == "ready" else state

    out: dict[str, Any] = {
        "enabled": enabled,
        "runtime_ready": runtime_ready,
        "state": state,
        "mode": mode,
        "source": source,
        "wireguard_config_available": wireguard_available,
    }
    if include_secrets and runtime_ready:
        out["wireguard_config"] = wireguard_config
        if account:
            out["account"] = account
    return out


def _normalize_ru_bridge_endpoint(value: Any, *, fallback: dict[str, Any], index: int) -> dict[str, Any]:
    src = value if isinstance(value, dict) else {}
    try:
        endpoint_port = int(src.get("endpoint_port") or src.get("port") or fallback["endpoint_port"])
    except Exception:
        endpoint_port = int(fallback["endpoint_port"])
    label_default = "Белые списки" if index == 0 else f"Белые списки тип {index + 1}"
    endpoint_id_default = "mini" if index == 0 else f"bridge_{index + 1}"
    return {
        "id": _clean_text(src.get("id") or src.get("code"), fallback=endpoint_id_default).lower(),
        "label": _clean_text(src.get("label"), fallback=label_default),
        "enabled": _as_bool(src.get("enabled")) if "enabled" in src else True,
        "endpoint_host": _clean_text(src.get("endpoint_host") or src.get("host"), fallback=fallback["endpoint_host"]),
        "endpoint_port": max(1, min(65535, endpoint_port)),
        "tls_server_name": _clean_text(src.get("tls_server_name"), fallback=fallback["tls_server_name"]),
        "reality_public_key": _clean_text(src.get("reality_public_key") or src.get("public_key")),
        "reality_short_id": _clean_text(src.get("reality_short_id") or src.get("short_id")),
        "fingerprint": _clean_text(src.get("fingerprint"), fallback=fallback["fingerprint"]),
    }


def normalized_network_rollout_config(payload: Any) -> dict[str, Any]:
    defaults = default_network_rollout_config()
    src = payload if isinstance(payload, dict) else {}
    normalized_defaults = _normalize_policy_patch(src.get("defaults"), defaults=defaults["defaults"])
    carrier_overrides_src = src.get("carrier_overrides")
    carrier_overrides: dict[str, dict[str, Any]] = {}
    if isinstance(carrier_overrides_src, dict):
        for key, value in carrier_overrides_src.items():
            name = _clean_text(key).lower()
            if not name:
                continue
            carrier_overrides[name] = _normalize_policy_patch(value, defaults=normalized_defaults)

    cohort_overrides_src = src.get("cohort_overrides")
    cohort_overrides: dict[str, dict[str, Any]] = {}
    if isinstance(cohort_overrides_src, dict):
        for key, value in cohort_overrides_src.items():
            name = _clean_text(key)
            if not name or not isinstance(value, dict):
                continue
            row = _normalize_policy_patch(value, defaults=normalized_defaults)
            row["install_ids"] = _normalize_string_list(value.get("install_ids"))
            row["tg_ids"] = _normalize_int_list(value.get("tg_ids"))
            row["linked_tg_ids"] = _normalize_int_list(value.get("linked_tg_ids"))
            row["platforms"] = _normalize_string_list(value.get("platforms"), lower=True)
            cohort_overrides[name] = row

    operator_lab_src = src.get("operator_lab")
    operator_lab = {
        "enabled": _as_bool((operator_lab_src or {}).get("enabled")) if isinstance(operator_lab_src, dict) else False,
        "allowlist_install_ids": _normalize_string_list((operator_lab_src or {}).get("allowlist_install_ids")),
        "allowlist_tg_ids": _normalize_int_list((operator_lab_src or {}).get("allowlist_tg_ids")),
        "allowlist_node_codes": _normalize_string_list((operator_lab_src or {}).get("allowlist_node_codes"), lower=True),
        "expires_at": _clean_text((operator_lab_src or {}).get("expires_at")) or None,
    }
    reserve_xhttp_src = src.get(RESERVE_XHTTP_CDN)
    reserve_xhttp_cdn = {
        "enabled": _as_bool((reserve_xhttp_src or {}).get("enabled")) if isinstance(reserve_xhttp_src, dict) else False,
        "allowlist_node_codes": _normalize_string_list((reserve_xhttp_src or {}).get("allowlist_node_codes"), lower=True),
        "xhttp_path": _clean_text((reserve_xhttp_src or {}).get("xhttp_path"), fallback="/reserve-xhttp") or "/reserve-xhttp",
        "tls_server_name": _clean_text((reserve_xhttp_src or {}).get("tls_server_name"), fallback="cdn.connect.pokrov.space")
        or "cdn.connect.pokrov.space",
    }
    ru_bridge_src = src.get(RU_BRIDGE_RELAY)
    default_ru_bridge = defaults[RU_BRIDGE_RELAY]
    try:
        endpoint_port = int((ru_bridge_src or {}).get("endpoint_port") or default_ru_bridge["endpoint_port"])
    except Exception:
        endpoint_port = int(default_ru_bridge["endpoint_port"])
    try:
        urltest_tolerance = int((ru_bridge_src or {}).get("urltest_tolerance") or default_ru_bridge["urltest_tolerance"])
    except Exception:
        urltest_tolerance = int(default_ru_bridge["urltest_tolerance"])
    bridge_base = {
        "endpoint_host": _clean_text((ru_bridge_src or {}).get("endpoint_host"), fallback=default_ru_bridge["endpoint_host"]),
        "endpoint_port": max(1, min(65535, endpoint_port)),
        "tls_server_name": _clean_text((ru_bridge_src or {}).get("tls_server_name"), fallback=default_ru_bridge["tls_server_name"]),
        "fingerprint": _clean_text((ru_bridge_src or {}).get("fingerprint"), fallback=default_ru_bridge["fingerprint"]),
    }
    raw_endpoints = (ru_bridge_src or {}).get("endpoints") if isinstance(ru_bridge_src, dict) else None
    endpoints: list[dict[str, Any]] = []
    if isinstance(raw_endpoints, list):
        for idx, raw_endpoint in enumerate(raw_endpoints):
            endpoint = _normalize_ru_bridge_endpoint(raw_endpoint, fallback=bridge_base, index=idx)
            if endpoint["id"] and endpoint["endpoint_host"]:
                endpoints.append(endpoint)
    if not endpoints:
        endpoints = [
            _normalize_ru_bridge_endpoint(
                {
                    **bridge_base,
                    "id": "mini",
                    "label": "Белые списки",
                    "enabled": True,
                    "reality_public_key": (ru_bridge_src or {}).get("reality_public_key") if isinstance(ru_bridge_src, dict) else "",
                    "reality_short_id": (ru_bridge_src or {}).get("reality_short_id") if isinstance(ru_bridge_src, dict) else "",
                },
                fallback=bridge_base,
                index=0,
            )
        ]
    primary_endpoint = endpoints[0]
    ru_bridge_relay = {
        "enabled": _as_bool((ru_bridge_src or {}).get("enabled")) if isinstance(ru_bridge_src, dict) else False,
        "endpoint_host": primary_endpoint["endpoint_host"],
        "endpoint_port": primary_endpoint["endpoint_port"],
        "tls_server_name": primary_endpoint["tls_server_name"],
        "reality_public_key": primary_endpoint["reality_public_key"],
        "reality_short_id": primary_endpoint["reality_short_id"],
        "fingerprint": primary_endpoint["fingerprint"],
        "allowlist_node_codes": _normalize_string_list((ru_bridge_src or {}).get("allowlist_node_codes"), lower=True),
        "excluded_node_codes": _normalize_string_list((ru_bridge_src or {}).get("excluded_node_codes"), lower=True)
        or list(default_ru_bridge["excluded_node_codes"]),
        "urltest_url": _clean_text((ru_bridge_src or {}).get("urltest_url"), fallback=default_ru_bridge["urltest_url"]),
        "urltest_interval": _clean_text((ru_bridge_src or {}).get("urltest_interval"), fallback=default_ru_bridge["urltest_interval"]),
        "urltest_tolerance": max(0, urltest_tolerance),
        "endpoints": endpoints,
    }

    package_catalog_feed = src.get("package_catalog_feed") if isinstance(src.get("package_catalog_feed"), dict) else {}
    routing_rules_feed = src.get("routing_rules_feed") if isinstance(src.get("routing_rules_feed"), dict) else {}
    support_recovery_order = _normalize_string_list(src.get("support_recovery_order"))
    if not support_recovery_order:
        support_recovery_order = list(defaults["support_recovery_order"])

    return {
        "version": _clean_text(src.get("version"), fallback=defaults["version"]),
        "defaults": normalized_defaults,
        "carrier_overrides": carrier_overrides,
        "cohort_overrides": cohort_overrides,
        "operator_lab": operator_lab,
        RESERVE_XHTTP_CDN: reserve_xhttp_cdn,
        RU_BRIDGE_RELAY: ru_bridge_relay,
        "package_catalog_feed": {
            "version": _clean_text(package_catalog_feed.get("version"), fallback=defaults["package_catalog_feed"]["version"]),
        },
        "routing_rules_feed": {
            "version": _clean_text(routing_rules_feed.get("version"), fallback=defaults["routing_rules_feed"]["version"]),
        },
        "support_recovery_order": support_recovery_order,
        _WARP_POLICY_KEY: _normalize_warp_policy(src.get(_WARP_POLICY_KEY), include_secrets=True),
    }


def managed_warp_policy(config: dict[str, Any]) -> dict[str, Any]:
    return _normalize_warp_policy((config or {}).get(_WARP_POLICY_KEY), include_secrets=True)


def public_warp_policy(config: dict[str, Any]) -> dict[str, Any]:
    return _normalize_warp_policy((config or {}).get(_WARP_POLICY_KEY), include_secrets=False)


def load_network_rollout_config(*, session=None) -> dict[str, Any]:
    from db import SessionLocal
    from models import AppSetting

    own_session = session is None
    s = session or SessionLocal()
    try:
        row = s.query(AppSetting).filter(AppSetting.key == NETWORK_ROLLOUT_CONFIG_KEY).first()
        raw = _safe_json_loads(getattr(row, "value_json", None) if row else None)
        return normalized_network_rollout_config(raw)
    except Exception:
        return normalized_network_rollout_config({})
    finally:
        if own_session:
            s.close()


def operator_lab_access(
    config: dict[str, Any],
    *,
    install_id: str = "",
    tg_ids: list[int] | None = None,
    now: datetime | None = None,
) -> bool:
    operator_lab = dict(config.get("operator_lab") or {})
    if not _as_bool(operator_lab.get("enabled")):
        return False

    expires_at = _clean_text(operator_lab.get("expires_at"))
    if expires_at:
        try:
            deadline = datetime.fromisoformat(expires_at.replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)
            if (now or _utcnow()) > deadline:
                return False
        except Exception:
            return False

    allowed_installs = set(_normalize_string_list(operator_lab.get("allowlist_install_ids")))
    allowed_tg_ids = set(_normalize_int_list(operator_lab.get("allowlist_tg_ids")))
    install_value = _clean_text(install_id)
    tg_values = {int(value) for value in (tg_ids or [])}
    return bool((install_value and install_value in allowed_installs) or (allowed_tg_ids and tg_values.intersection(allowed_tg_ids)))


def reserve_xhttp_cdn_enabled(config: dict[str, Any]) -> bool:
    reserve = dict(config.get(RESERVE_XHTTP_CDN) or {})
    return _as_bool(reserve.get("enabled"))


def ru_bridge_relay_enabled(config: dict[str, Any]) -> bool:
    bridge = dict(config.get(RU_BRIDGE_RELAY) or {})
    if not _as_bool(bridge.get("enabled")):
        return False
    endpoints = bridge.get("endpoints")
    if isinstance(endpoints, list):
        return any(
            bool(item.get("enabled", True)) and bool(_clean_text(item.get("reality_public_key")))
            for item in endpoints
            if isinstance(item, dict)
        )
    return bool(_clean_text(bridge.get("reality_public_key")))


def ru_bridge_relay_config(config: dict[str, Any]) -> dict[str, Any]:
    return dict(normalized_network_rollout_config(config).get(RU_BRIDGE_RELAY) or {})


def ru_bridge_relay_endpoints(config: dict[str, Any]) -> list[dict[str, Any]]:
    bridge = ru_bridge_relay_config(config)
    endpoints = bridge.get("endpoints")
    if not isinstance(endpoints, list):
        endpoints = [bridge]
    out: list[dict[str, Any]] = []
    for idx, item in enumerate(endpoints):
        if not isinstance(item, dict):
            continue
        endpoint = dict(item)
        if not endpoint.get("enabled", True):
            continue
        if not _clean_text(endpoint.get("reality_public_key")):
            continue
        endpoint.setdefault("id", "mini" if idx == 0 else f"bridge_{idx + 1}")
        endpoint.setdefault("label", "Белые списки" if idx == 0 else f"Белые списки тип {idx + 1}")
        out.append(endpoint)
    return out


def _cohort_matches(rule: dict[str, Any], *, install_id: str, tg_ids: list[int], platform: str) -> bool:
    install_ids = set(_normalize_string_list(rule.get("install_ids")))
    rule_tg_ids = set(_normalize_int_list(rule.get("tg_ids")))
    linked_tg_ids = set(_normalize_int_list(rule.get("linked_tg_ids")))
    platforms = set(_normalize_string_list(rule.get("platforms"), lower=True))

    criteria_used = False
    if install_ids:
        criteria_used = True
        if install_id in install_ids:
            return True
    if rule_tg_ids:
        criteria_used = True
        if set(tg_ids).intersection(rule_tg_ids):
            return True
    if linked_tg_ids:
        criteria_used = True
        if set(tg_ids).intersection(linked_tg_ids):
            return True
    if platforms:
        criteria_used = True
        if platform and platform in platforms:
            return True
    return False if criteria_used else False


def resolved_client_policy(
    *,
    session=None,
    user: Any = None,
    install_id: str | None = None,
    carrier: str | None = None,
    rollout_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    product_facts = get_product_facts()
    config = normalized_network_rollout_config(rollout_config or load_network_rollout_config(session=session))
    resolved = dict(config.get("defaults") or default_network_rollout_config()["defaults"])
    carrier_key = _clean_text(carrier).lower()
    if carrier_key:
        resolved.update(dict((config.get("carrier_overrides") or {}).get(carrier_key) or {}))

    install_value = _clean_text(install_id or getattr(user, "app_install_id", ""))
    platform = _clean_text(getattr(user, "app_platform", ""), fallback=_clean_text(getattr(user, "platform", ""))).lower()
    tg_ids: list[int] = []
    for raw in (
        getattr(user, "tg_id", None),
        getattr(user, "linked_telegram_id", None),
    ):
        try:
            value = int(raw)
        except Exception:
            continue
        if value not in tg_ids:
            tg_ids.append(value)
    for rule in (config.get("cohort_overrides") or {}).values():
        if not isinstance(rule, dict):
            continue
        if _cohort_matches(rule, install_id=install_value, tg_ids=tg_ids, platform=platform):
            resolved.update({key: value for key, value in rule.items() if key in _POLICY_OVERRIDE_KEYS and _clean_text(value)})

    transport_profile = _clean_text(resolved.get("transport_profile"), fallback=LEGACY_REALITY_FALLBACK)
    if transport_profile == OPERATOR_LAB and not operator_lab_access(config, install_id=install_value, tg_ids=tg_ids):
        transport_profile = LEGACY_REALITY_FALLBACK
    if transport_profile == RESERVE_XHTTP_CDN and not reserve_xhttp_cdn_enabled(config):
        transport_profile = LEGACY_REALITY_FALLBACK
    if transport_profile == RU_BRIDGE_RELAY and not ru_bridge_relay_enabled(config):
        transport_profile = LEGACY_REALITY_FALLBACK
    if transport_profile not in {LEGACY_REALITY_FALLBACK, GRPC_443_PRIMARY, RESERVE_XHTTP_CDN, RU_BRIDGE_RELAY, OPERATOR_LAB}:
        transport_profile = LEGACY_REALITY_FALLBACK
    transport_meta = _transport_metadata(transport_profile, version=_clean_text(config.get("version"), fallback=_default_rollout_version()))

    versions = product_facts.get("versions", {}) if isinstance(product_facts, dict) else {}
    package_version = _clean_text(
        ((config.get("package_catalog_feed") or {}).get("version")),
        fallback=_clean_text(versions.get("package_catalog_version"), fallback=config["version"]),
    )
    ruleset_version = _clean_text(
        ((config.get("routing_rules_feed") or {}).get("version")),
        fallback=_clean_text(versions.get("ruleset_version"), fallback=config["version"]),
    )
    support_recovery_order = _normalize_string_list(config.get("support_recovery_order"))
    if not support_recovery_order:
        support_recovery_order = ["app", "web", "telegram"]

    routing_mode = _clean_text(resolved.get("routing_mode_default"), fallback="all_except_ru")
    dns_policy = _clean_text(resolved.get("dns_policy"), fallback="ru_direct_split")
    ip_version_preference = _clean_text(resolved.get("ip_version_preference"), fallback="ipv4_only")
    return {
        "routing_mode_default": routing_mode,
        "transport_profile": transport_profile,
        "transport_kind": transport_meta["transport_kind"],
        "engine_hint": transport_meta["engine_hint"],
        "profile_revision": transport_meta["profile_revision"],
        "dns_policy": dns_policy,
        "package_catalog_version": package_version,
        "ruleset_version": ruleset_version,
        "support_context": {
            "transport": transport_profile,
            "routing_mode": routing_mode,
            "ip_version_preference": ip_version_preference,
        },
        "support_recovery_order": support_recovery_order,
        _WARP_POLICY_KEY: public_warp_policy(config),
    }


def transport_node_allowlist(config: dict[str, Any], transport_profile: str) -> list[str]:
    if _clean_text(transport_profile) == RESERVE_XHTTP_CDN:
        reserve = dict(config.get(RESERVE_XHTTP_CDN) or {})
        if not _as_bool(reserve.get("enabled")):
            return []
        return _normalize_string_list(reserve.get("allowlist_node_codes"), lower=True)
    if _clean_text(transport_profile) == RU_BRIDGE_RELAY:
        bridge = dict(config.get(RU_BRIDGE_RELAY) or {})
        if not _as_bool(bridge.get("enabled")):
            return []
        return _normalize_string_list(bridge.get("allowlist_node_codes"), lower=True)
    if _clean_text(transport_profile) != OPERATOR_LAB:
        return []
    operator_lab = dict(config.get("operator_lab") or {})
    return _normalize_string_list(operator_lab.get("allowlist_node_codes"), lower=True)


def transport_node_exclusions(config: dict[str, Any], transport_profile: str) -> list[str]:
    if _clean_text(transport_profile) != RU_BRIDGE_RELAY:
        return []
    bridge = dict(config.get(RU_BRIDGE_RELAY) or {})
    return _normalize_string_list(bridge.get("excluded_node_codes"), lower=True)
