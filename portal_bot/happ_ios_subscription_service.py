"""Pure HAPP iOS XRAY JSON-array subscription rendering.

The route owns authentication, entitlement, ranking, and RU-bridge eligibility.
This module receives only already-authorized, normalized material and never
queries the database or reads deployment configuration.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Any, Mapping, Sequence


HAPP_IOS_REMARKS_MAX_LENGTH = 30
HAPP_IOS_DESCRIPTION_MAX_LENGTH = 30


@dataclass(frozen=True)
class HappIOSRenderResult:
    profiles: list[dict[str, Any]]
    exclusions: list[dict[str, str]]


def _clean_text(value: Any, *, limit: int = 512) -> str:
    return " ".join(str(value or "").split())[:limit].strip()


def _safe_code(value: Any) -> str:
    cleaned = re.sub(r"[^a-z0-9._-]+", "", str(value or "").strip().lower())
    return cleaned[:64] or "unknown"


def _valid_host(value: Any) -> bool:
    host = _clean_text(value, limit=253)
    return bool(host) and "://" not in host and not any(ch in host for ch in "/\\?#")


def _valid_port(value: Any) -> bool:
    try:
        port = int(value)
    except (TypeError, ValueError):
        return False
    return 1 <= port <= 65535


def _normalized_reality_material(raw: Mapping[str, Any]) -> dict[str, Any] | None:
    required_text_fields = (
        "host",
        "tls_server_name",
        "reality_public_key",
        "reality_short_id",
    )
    if not _valid_host(raw.get("host")) or not _valid_port(raw.get("port")):
        return None
    if any(not _clean_text(raw.get(field)) for field in required_text_fields[1:]):
        return None
    return {
        "host": _clean_text(raw.get("host"), limit=253),
        "port": int(raw.get("port")),
        "tls_server_name": _clean_text(raw.get("tls_server_name"), limit=253),
        "reality_public_key": _clean_text(raw.get("reality_public_key"), limit=512),
        "reality_short_id": _clean_text(raw.get("reality_short_id"), limit=128),
        "fingerprint": _clean_text(raw.get("fingerprint"), limit=32) or "chrome",
        "flow": _clean_text(raw.get("flow"), limit=64),
    }


def _xray_vless_reality_outbound(
    *,
    user_uuid: str,
    material: Mapping[str, Any],
    tag: str,
    proxy_tag: str = "",
) -> dict[str, Any]:
    user: dict[str, Any] = {
        "id": user_uuid,
        "encryption": "none",
    }
    flow = _clean_text(material.get("flow"), limit=64)
    if flow:
        user["flow"] = flow

    outbound: dict[str, Any] = {
        "tag": tag,
        "protocol": "vless",
        "settings": {
            "vnext": [
                {
                    "address": str(material["host"]),
                    "port": int(material["port"]),
                    "users": [user],
                }
            ]
        },
        "streamSettings": {
            "network": "raw",
            "security": "reality",
            "realitySettings": {
                "fingerprint": str(material["fingerprint"]),
                "serverName": str(material["tls_server_name"]),
                "publicKey": str(material["reality_public_key"]),
                "shortId": str(material["reality_short_id"]),
                "spiderX": "/",
            },
        },
        "mux": {"enabled": False},
    }
    if proxy_tag:
        outbound["proxySettings"] = {
            "tag": proxy_tag,
            "transportLayer": True,
        }
    return outbound


def _xray_inbounds() -> list[dict[str, Any]]:
    sniffing = {
        "enabled": True,
        "destOverride": ["http", "tls", "quic"],
    }
    return [
        {
            "tag": "socks",
            "port": 10808,
            "listen": "127.0.0.1",
            "protocol": "socks",
            "settings": {"udp": True},
            "sniffing": dict(sniffing),
        },
        {
            "tag": "http",
            "port": 10809,
            "listen": "127.0.0.1",
            "protocol": "http",
            "sniffing": dict(sniffing),
        },
    ]


def _xray_dns() -> dict[str, Any]:
    # An IP-based non-local DoH endpoint avoids bootstrap recursion. Its tag is
    # routed through the selected proxy below, including the RU bridge chain.
    return {
        "servers": [
            {
                "address": "https://1.1.1.1/dns-query",
                "tag": "dns-remote",
            }
        ],
        "queryStrategy": "UseIPv4",
    }


def _xray_routing() -> dict[str, Any]:
    return {
        "domainStrategy": "AsIs",
        "rules": [
            {
                "type": "field",
                "inboundTag": ["dns-remote"],
                "outboundTag": "proxy",
            },
            {
                "type": "field",
                "ip": ["geoip:private"],
                "outboundTag": "direct",
            },
            {
                "type": "field",
                "domain": ["geosite:private"],
                "outboundTag": "direct",
            },
        ],
    }


def _bounded_title(base_label: str, mode_label: str) -> str:
    mode = _clean_text(mode_label, limit=HAPP_IOS_REMARKS_MAX_LENGTH)
    suffix = f" · {mode}" if mode else ""
    available = max(1, HAPP_IOS_REMARKS_MAX_LENGTH - len(suffix))
    base = _clean_text(base_label, limit=available) or "POKROV"
    return f"{base[:available]}{suffix}"[:HAPP_IOS_REMARKS_MAX_LENGTH]


def _bridge_short_label(label: str, index: int) -> str:
    match = re.search(r"(?:тип|type)\s*(\d+)", label, flags=re.IGNORECASE)
    if match:
        return f"БС {match.group(1)}"
    return "БС" if index == 0 else f"БС {index + 1}"


def _profile_config(
    *,
    user_uuid: str,
    remarks: str,
    description: str,
    destination: Mapping[str, Any],
    bridge: Mapping[str, Any] | None,
) -> dict[str, Any]:
    outbounds = [
        _xray_vless_reality_outbound(
            user_uuid=user_uuid,
            material=destination,
            tag="proxy",
            proxy_tag="bridge" if bridge is not None else "",
        )
    ]
    if bridge is not None:
        outbounds.append(
            _xray_vless_reality_outbound(
                user_uuid=user_uuid,
                material=bridge,
                tag="bridge",
            )
        )
    outbounds.extend(
        [
            {"tag": "direct", "protocol": "freedom"},
            {"tag": "block", "protocol": "blackhole"},
        ]
    )
    return {
        "remarks": remarks,
        "meta": {
            "serverDescription": _clean_text(
                description,
                limit=HAPP_IOS_DESCRIPTION_MAX_LENGTH,
            )
        },
        "log": {"loglevel": "warning"},
        "dns": _xray_dns(),
        "routing": _xray_routing(),
        "inbounds": _xray_inbounds(),
        "outbounds": outbounds,
    }


def render_happ_ios_profiles(
    *,
    user_uuid: str,
    destinations: Sequence[Mapping[str, Any]],
) -> HappIOSRenderResult:
    """Render deterministic direct and eligible RU-bridge XRAY profiles.

    ``destinations`` is already ordered and authorized by the subscription
    route. Each item may contain a ``bridges`` list with normalized endpoints.
    Invalid material is omitted fail-closed and reported without raw values.
    """

    try:
        normalized_uuid = str(uuid.UUID(str(user_uuid)))
    except (TypeError, ValueError, AttributeError):
        return HappIOSRenderResult(
            profiles=[],
            exclusions=[{"node_code": "all", "mode": "all", "reason": "invalid_user_uuid"}],
        )

    profiles: list[dict[str, Any]] = []
    exclusions: list[dict[str, str]] = []
    seen_remarks: set[str] = set()
    for raw_destination in destinations:
        code = _safe_code(raw_destination.get("code"))
        label = _clean_text(raw_destination.get("label"), limit=64) or code.upper()
        destination = _normalized_reality_material(raw_destination)
        if destination is None:
            exclusions.append(
                {"node_code": code, "mode": "direct", "reason": "invalid_destination"}
            )
            continue

        direct_remarks = _bounded_title(label, "Обычный")
        if direct_remarks in seen_remarks:
            direct_remarks = _bounded_title(f"{label} {code.upper()}", "Обычный")
        seen_remarks.add(direct_remarks)
        profiles.append(
            _profile_config(
                user_uuid=normalized_uuid,
                remarks=direct_remarks,
                description="Прямое подключение",
                destination=destination,
                bridge=None,
            )
        )

        raw_bridges = raw_destination.get("bridges")
        if not isinstance(raw_bridges, Sequence) or isinstance(raw_bridges, (str, bytes)):
            raw_bridges = []
        for index, raw_bridge in enumerate(raw_bridges):
            if not isinstance(raw_bridge, Mapping):
                exclusions.append(
                    {"node_code": code, "mode": "bridge", "reason": "invalid_bridge"}
                )
                continue
            bridge_id = _safe_code(raw_bridge.get("id"))
            bridge = _normalized_reality_material(raw_bridge)
            if bridge is None:
                exclusions.append(
                    {
                        "node_code": code,
                        "mode": bridge_id,
                        "reason": "invalid_bridge",
                    }
                )
                continue
            bridge_label = _clean_text(raw_bridge.get("label"), limit=48) or "Белые списки"
            short_label = _bridge_short_label(bridge_label, index)
            remarks = _bounded_title(label, short_label)
            if remarks in seen_remarks:
                remarks = _bounded_title(f"{label} {code.upper()}", short_label)
            seen_remarks.add(remarks)
            profiles.append(
                _profile_config(
                    user_uuid=normalized_uuid,
                    remarks=remarks,
                    description=bridge_label,
                    destination=destination,
                    bridge=bridge,
                )
            )

    return HappIOSRenderResult(profiles=profiles, exclusions=exclusions)
