"""Short-lived, account/device-bound observations of the client's access network.

The native client chooses a non-VPN network. That routing claim is diagnostic,
not entitlement or abuse authority. Only the receiving server supplies the IP.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from antiabuse_privacy_service import record_antiabuse_event
from emergency_geoip_service import geoip2, lookup_country_code, request_public_ip
from models import AntiAbuseEvent

EVENT_KIND = "client_network_context"
NETWORK_CLASSES = frozenset({"cellular", "wifi", "ethernet", "other", "unknown"})


def _label(value: Any, limit: int = 80) -> str | None:
    text = str(value or "").strip()
    if not text or len(text) > limit or not re.fullmatch(r"[\w .()+'-]+", text):
        return None
    return text


def approximate_region(ip: str | None) -> tuple[str | None, str | None]:
    if not ip:
        return None, None
    country = lookup_country_code(ip)
    city_db = str(os.getenv("CLIENT_NETWORK_GEOIP_CITY_DB_PATH", "")).strip()
    if not city_db:
        return country, None
    try:
        with geoip2.database.Reader(city_db) as reader:
            record = reader.city(ip)
        code = str(record.country.iso_code or "").upper()
        return (
            code if re.fullmatch(r"[A-Z]{2}", code) else country,
            _label(record.subdivisions.most_specific.name, 120),
        )
    except Exception:
        # No remote lookup, GPS, city coordinates or exception payloads.
        return country, None


def record_network_context(
    session, *, request, account_id: str, device_id: str, install_id: str,
    network_class: str, carrier: str | None, direct_observation: bool,
    platform: str, app_version: str, profile_revision: str | None,
    runtime_phase: str | None,
) -> bool:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    recent = session.query(AntiAbuseEvent.id).filter(
        AntiAbuseEvent.event_kind == EVENT_KIND,
        AntiAbuseEvent.account_id == account_id,
        AntiAbuseEvent.device_id == device_id,
        AntiAbuseEvent.occurred_at > now - timedelta(seconds=30),
    ).first()
    if recent is not None:
        return False
    network = network_class if network_class in NETWORK_CLASSES else "unknown"
    ip = request_public_ip(request) if direct_observation and network != "unknown" else None
    country, region = approximate_region(ip)
    record_antiabuse_event(
        session, event_kind=EVENT_KIND, source="client_network",
        occurred_at=now, account_id=account_id, device_id=device_id,
        install_id=install_id, raw_ip=ip,
        metadata={
            "network_class": network,
            "carrier": _label(carrier) if network == "cellular" else None,
            "country_code": country, "region": region,
            "origin_status": "observed" if ip else "unavailable",
            "source": "android_bound_nonvpn" if direct_observation else "client_transport_unavailable",
            "platform": _label(platform, 24), "app_version": _label(app_version, 32),
            "profile_revision": _label(profile_revision, 128),
            "runtime_phase": _label(runtime_phase, 32),
        },
    )
    return True


def recent_network_context(session, *, account_id: str, now: datetime | None = None) -> list[dict[str, Any]]:
    if not account_id:
        return []
    current = now or datetime.now(timezone.utc).replace(tzinfo=None)
    rows = session.query(AntiAbuseEvent).filter(
        AntiAbuseEvent.event_kind == EVENT_KIND,
        AntiAbuseEvent.account_id == account_id,
        AntiAbuseEvent.occurred_at > current - timedelta(hours=72),
        AntiAbuseEvent.metadata_json.is_not(None),
    ).order_by(AntiAbuseEvent.occurred_at.desc()).limit(100).all()
    result = []
    seen = set()
    for row in rows:
        if row.device_id in seen:
            continue
        seen.add(row.device_id)
        try:
            meta = json.loads(row.metadata_json or "{}")
        except (TypeError, ValueError):
            continue
        if not isinstance(meta, dict):
            continue
        raw_ip = row.raw_ip if row.raw_ip_expires_at and row.raw_ip_expires_at > current else None
        result.append({
            "device_id": row.device_id,
            "observed_at": row.occurred_at.isoformat() + "Z",
            "origin_status": "observed" if raw_ip else "unavailable",
            "public_ip": raw_ip,
            "network_class": meta.get("network_class") if meta.get("network_class") in NETWORK_CLASSES else "unknown",
            **{key: _label(meta.get(key), limit) for key, limit in (
                ("carrier", 80), ("country_code", 2), ("region", 120),
                ("source", 40), ("platform", 24), ("app_version", 32),
                ("profile_revision", 128), ("runtime_phase", 32),
            )},
        })
        if len(result) >= 20:
            break
    return result
