from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from shared_surface_facts import get_product_facts
from transport_catalog import GRPC_443_PRIMARY, LEGACY_REALITY_FALLBACK, OPERATOR_LAB


NETWORK_ROLLOUT_CONFIG_KEY = "network_rollout_config"
_POLICY_OVERRIDE_KEYS = {
    "transport_profile",
    "dns_policy",
    "routing_mode_default",
    "ip_version_preference",
}


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
        "package_catalog_feed": {
            "version": _clean_text(versions.get("package_catalog_version"), fallback=version),
        },
        "routing_rules_feed": {
            "version": _clean_text(versions.get("ruleset_version"), fallback=version),
        },
        "support_recovery_order": [str(item) for item in recovery if _clean_text(item)],
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
    elif profile == OPERATOR_LAB:
        transport_kind = "xhttp"
        engine_hint = "xray"
    else:
        transport_kind = "reality"
        engine_hint = "singbox"
    return {
        "transport_kind": transport_kind,
        "engine_hint": engine_hint,
        "profile_revision": f"{_clean_text(version, fallback=_default_rollout_version())}:{profile}",
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
        "package_catalog_feed": {
            "version": _clean_text(package_catalog_feed.get("version"), fallback=defaults["package_catalog_feed"]["version"]),
        },
        "routing_rules_feed": {
            "version": _clean_text(routing_rules_feed.get("version"), fallback=defaults["routing_rules_feed"]["version"]),
        },
        "support_recovery_order": support_recovery_order,
    }


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
    if transport_profile not in {LEGACY_REALITY_FALLBACK, GRPC_443_PRIMARY, OPERATOR_LAB}:
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
    }


def transport_node_allowlist(config: dict[str, Any], transport_profile: str) -> list[str]:
    if _clean_text(transport_profile) != OPERATOR_LAB:
        return []
    operator_lab = dict(config.get("operator_lab") or {})
    return _normalize_string_list(operator_lab.get("allowlist_node_codes"), lower=True)
