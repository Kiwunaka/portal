"""Transport materialization, previews and subscription rendering routes.

Loaded by the api composition root in source order. Public symbols are
re-exported for backwards compatibility.
"""

try:
    from .module_slices import bootstrap_slice
except ImportError:
    from module_slices import bootstrap_slice

bootstrap_slice(globals())

try:
    from .node_observability_sanitizer import (
        safe_error_kind,
        safe_hoster_asn,
        safe_hoster_family,
        safe_probe_classification,
        safe_probe_error_message,
        safe_probe_stage,
        sanitize_transport_health,
    )
except ImportError:
    from node_observability_sanitizer import (
        safe_error_kind,
        safe_hoster_asn,
        safe_hoster_family,
        safe_probe_classification,
        safe_probe_error_message,
        safe_probe_stage,
        sanitize_transport_health,
    )

def _transport_profiles_payload(node: Any) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for profile in node_transport_profiles(node, include_disabled=True):
        name = str(profile.get("name") or "").strip()
        if not name:
            continue
        out[name] = dict(profile)
    return out


def _node_transport_profile(node: Any, transport_profile: str | None) -> dict[str, Any]:
    return transport_profile_by_name(
        node,
        transport_profile or LEGACY_REALITY_FALLBACK,
        include_disabled=True,
        allow_operator_lab=True,
    )


def _node_outbound_from_transport_profile(*, user_uuid: str, node: Any, tag: str, transport_profile: str | None) -> dict[str, Any]:
    profile = _node_transport_profile(node, transport_profile)
    kind = str(profile.get("kind") or "reality").strip().lower()
    tls: dict[str, Any] = {
        "enabled": True,
        "server_name": str(profile.get("tls_server_name") or getattr(node, "reality_sni", "") or ""),
        "utls": {
            "enabled": True,
            "fingerprint": str(profile.get("fingerprint") or getattr(node, "fingerprint", "") or "firefox"),
        },
    }
    outbound: dict[str, Any] = {
        "type": "vless",
        "tag": tag,
        "server": str(profile.get("host") or getattr(node, "host", "") or ""),
        "server_port": int(profile.get("port") or getattr(node, "vless_port", 443) or 443),
        "uuid": user_uuid,
        "tls": tls,
        "packet_encoding": "xudp",
    }
    flow = str(profile.get("flow") or getattr(node, "flow", "") or "").strip()
    if flow:
        outbound["flow"] = flow

    if kind == "grpc":
        outbound["transport"] = {
            "type": "grpc",
            "service_name": str(profile.get("grpc_service_name") or "").strip(),
        }
        outbound.pop("flow", None)
        return outbound

    if kind == "xhttp":
        outbound["transport"] = {
            "type": "http",
            "path": str(profile.get("xhttp_path") or "/").strip() or "/",
        }
        outbound.pop("flow", None)
        return outbound

    tls["reality"] = {
        "enabled": True,
        "public_key": str(profile.get("reality_public_key") or getattr(node, "reality_pbk", "") or ""),
        "short_id": str(profile.get("reality_short_id") or getattr(node, "reality_sid", "") or ""),
    }
    return outbound


def _filter_nodes_for_transport_profile(
    *,
    nodes: list,
    rollout_config: dict[str, Any],
    transport_profile: str,
    apply_exclusions: bool = True,
) -> list:
    allowlist = set(transport_node_allowlist(rollout_config, transport_profile))
    excluded = set(transport_node_exclusions(rollout_config, transport_profile))
    out: list[Any] = []
    for node in nodes:
        code = str(getattr(node, "code", "") or "").strip().lower()
        base = _node_code_base(code)
        if allowlist and code not in allowlist and base not in allowlist:
            continue
        if apply_exclusions and excluded and (code in excluded or base in excluded):
            continue
        out.append(node)
    return out


def _ru_bridge_endpoints_for_node(
    *,
    node: Any,
    rollout_config: dict[str, Any],
    transport_profile: str,
) -> list[dict[str, Any]]:
    """Return only bridge endpoints that can back a real choice for this node."""

    if not ru_bridge_relay_enabled(rollout_config):
        return []
    raw_endpoints = ru_bridge_relay_endpoints(rollout_config)
    endpoints: list[dict[str, Any]] = []
    seen_ids = {"direct"}
    for raw_endpoint in raw_endpoints:
        endpoint_id = str(raw_endpoint.get("id") or "").strip().lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,63}", endpoint_id) or endpoint_id in seen_ids:
            continue
        label = " ".join(str(raw_endpoint.get("label") or "Белые списки").split())[:48].strip()
        endpoint = dict(raw_endpoint)
        endpoint["id"] = endpoint_id
        endpoint["label"] = label or "Белые списки"
        endpoints.append(endpoint)
        seen_ids.add(endpoint_id)
    if not endpoints:
        return []

    code = str(getattr(node, "code", "") or "").strip().lower()
    base = _node_code_base(code)
    allowlist = set(transport_node_allowlist(rollout_config, RU_BRIDGE_RELAY))
    excluded = set(transport_node_exclusions(rollout_config, RU_BRIDGE_RELAY))
    if allowlist and code not in allowlist and base not in allowlist:
        return []
    if code in excluded or base in excluded:
        return []

    requested_transport = str(transport_profile or LEGACY_REALITY_FALLBACK).strip()
    if requested_transport == RU_BRIDGE_RELAY:
        requested_transport = LEGACY_REALITY_FALLBACK
    if not _node_supports_transport_profile(node, requested_transport):
        return []
    return endpoints


def _managed_manifest_fallback_order(transport_profile: str) -> list[str]:
    primary = str(transport_profile or LEGACY_REALITY_FALLBACK).strip() or LEGACY_REALITY_FALLBACK
    order = [primary]
    if primary != LEGACY_REALITY_FALLBACK:
        order.append(LEGACY_REALITY_FALLBACK)
    return order


def _ru_bridge_outbound(
    *,
    user_uuid: str,
    rollout_config: dict[str, Any],
    tag: str = RU_BRIDGE_OUTBOUND_TAG,
    bridge: dict[str, Any] | None = None,
) -> dict[str, Any]:
    bridge = dict(bridge or ru_bridge_relay_config(rollout_config))
    tls_server_name = str(bridge.get("tls_server_name") or "www.yandex.ru").strip()
    return {
        "type": "vless",
        "tag": tag,
        "server": str(bridge.get("endpoint_host") or "176.123.166.119").strip(),
        "server_port": int(bridge.get("endpoint_port") or 443),
        "uuid": user_uuid,
        "flow": "xtls-rprx-vision",
        "packet_encoding": "xudp",
        "tls": {
            "enabled": True,
            "server_name": tls_server_name,
            "utls": {
                "enabled": True,
                "fingerprint": str(bridge.get("fingerprint") or "chrome").strip() or "chrome",
            },
            "reality": {
                "enabled": True,
                "public_key": str(bridge.get("reality_public_key") or "").strip(),
                "short_id": str(bridge.get("reality_short_id") or "").strip(),
            },
        },
    }


def _ru_bridge_endpoint_tag(index: int, endpoint: dict[str, Any]) -> str:
    if index <= 0:
        return RU_BRIDGE_OUTBOUND_TAG
    label = str(endpoint.get("label") or f"тип {index + 1}").strip()
    return f"POKROV мост {label}{HIDDIFY_HIDDEN_TAG_SUFFIX}"


def _synthetic_transport_node() -> Any:
    connect_host = public_connect_host()
    transport_profiles = [
        {
            "name": LEGACY_REALITY_FALLBACK,
            "enabled": True,
            "kind": "reality",
            "inbound_id": 1,
            "host": connect_host,
            "port": 443,
            "tls_server_name": connect_host,
            "reality_public_key": "",
            "reality_short_id": "",
            "fingerprint": "firefox",
            "flow": "xtls-rprx-vision",
        },
        {
            "name": "grpc_443_primary",
            "enabled": True,
            "kind": "grpc",
            "inbound_id": 2,
            "host": connect_host,
            "port": 443,
            "tls_server_name": f"grpc.{connect_host}",
            "fingerprint": "firefox",
            "grpc_service_name": "pokrov-grpc",
        },
        {
            "name": RESERVE_XHTTP_CDN,
            "enabled": True,
            "kind": "xhttp",
            "inbound_id": 4,
            "host": connect_host,
            "port": 443,
            "tls_server_name": f"cdn.{connect_host}",
            "fingerprint": "firefox",
            "xhttp_path": "/reserve-xhttp",
        },
        {
            "name": OPERATOR_LAB,
            "enabled": True,
            "kind": "xhttp",
            "inbound_id": 3,
            "host": connect_host,
            "port": 443,
            "tls_server_name": f"xhttp.{connect_host}",
            "fingerprint": "firefox",
            "xhttp_path": "/xhttp",
        },
    ]
    return SimpleNamespace(
        code="default",
        name="Default",
        host=connect_host,
        vless_port=443,
        reality_sni=connect_host,
        reality_pbk="",
        reality_sid="",
        fingerprint="firefox",
        flow="xtls-rprx-vision",
        inbound_id=1,
        transport_profiles_json=json.dumps(transport_profiles, ensure_ascii=False),
    )


def _effective_transport_nodes(*, nodes: list[Any], transport_profile: str, rollout_config: dict[str, Any]) -> list[Any]:
    requested = str(transport_profile or LEGACY_REALITY_FALLBACK).strip() or LEGACY_REALITY_FALLBACK
    filtered = _filter_nodes_for_transport_profile(
        nodes=nodes,
        rollout_config=rollout_config,
        transport_profile=transport_profile,
        apply_exclusions=str(transport_profile or "").strip() != RU_BRIDGE_RELAY,
    )
    if str(transport_profile or "").strip() == RU_BRIDGE_RELAY:
        return [
            node
            for node in filtered
            if _node_supports_transport_profile(node, LEGACY_REALITY_FALLBACK)
        ]
    supporting = [
        node for node in filtered if _node_supports_transport_profile(node, transport_profile)
    ]
    if supporting:
        return supporting
    # An explicit requested profile is authoritative even when disabled.  Do
    # not replace it with synthetic compatibility material; synthesis is only
    # for catalogs that genuinely omit the requested transport everywhere.
    if any(has_explicit_transport_profile(node, requested) for node in filtered):
        return []
    if requested == LEGACY_REALITY_FALLBACK and filtered:
        return filtered
    return [_synthetic_transport_node()]


def _prefer_smart_connect_node_order(*, nodes: list[Any], preferred_node_code: str) -> list[Any]:
    preferred = str(preferred_node_code or "").strip().lower()
    if not preferred or len(nodes) < 2:
        return nodes
    ordered = list(nodes)
    ordered.sort(
        key=lambda node: (
            0
            if str(getattr(node, "code", "") or "").strip().lower() == preferred
            else 1
        )
    )
    return ordered


def _xray_multi_node_config(*, user_uuid: str, nodes: list, title: str, transport_profile: str) -> dict[str, Any]:
    outbounds: list[dict[str, Any]] = []
    selector_tag = "pokrov-selector"
    for node in nodes:
        profile = _node_transport_profile(node, transport_profile)
        tag = str(getattr(node, "code", "") or getattr(node, "name", "") or "node").strip() or "node"
        outbounds.append(
            {
                "tag": tag,
                "protocol": "vless",
                "settings": {
                    "vnext": [
                        {
                            "address": str(profile.get("host") or getattr(node, "host", "") or ""),
                            "port": int(profile.get("port") or getattr(node, "vless_port", 443) or 443),
                            "users": [{"id": user_uuid, "encryption": "none"}],
                        }
                    ]
                },
                "streamSettings": {
                    "network": "xhttp",
                    "security": "tls",
                    "tlsSettings": {
                        "serverName": str(profile.get("tls_server_name") or getattr(node, "reality_sni", "") or ""),
                    },
                    "xhttpSettings": {
                        "path": str(profile.get("xhttp_path") or "/").strip() or "/",
                    },
                },
            }
        )

    return {
        "log": {"loglevel": "warning"},
        "routing": {"domainStrategy": "AsIs"},
        "outbounds": [
            {
                "tag": selector_tag,
                "protocol": "selector",
                "settings": {"actors": [item["tag"] for item in outbounds]},
            },
            *outbounds,
        ],
        "_meta": {"title": title},
    }


def _managed_manifest_payload(
    *,
    user: User,
    nodes: list,
    title: str,
    transport_profile: str,
    rollout_config: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    effective_rollout_config = normalized_network_rollout_config(rollout_config or {})
    if str(transport_profile or "").strip() in {OPERATOR_LAB, RESERVE_XHTTP_CDN}:
        return (
            "xray-json",
            _xray_multi_node_config(
                user_uuid=str(user.uuid),
                nodes=nodes,
                title=title,
                transport_profile=transport_profile,
            ),
        )

    if str(transport_profile or "").strip() == RU_BRIDGE_RELAY:
        return (
            "singbox-json",
            _singbox_ru_bridge_config(
                user_uuid=str(user.uuid),
                nodes=nodes,
                title=title,
                rollout_config=effective_rollout_config,
            ),
        )

    if user_uses_free_pool(user):
        return (
            "singbox-json",
            _singbox_free_allowlist_config(
                user_uuid=str(user.uuid),
                nodes=nodes,
                title=title,
                transport_profile=transport_profile,
            ),
        )
    return (
        "singbox-json",
        _singbox_multi_node_config(
            user_uuid=str(user.uuid),
            nodes=nodes,
            title=title,
            transport_profile=transport_profile,
            rollout_config=effective_rollout_config,
        ),
    )


def _generate_vless_link(*, user_uuid: str, node, name: str) -> str:
    import urllib.parse

    profile = _node_transport_profile(node, LEGACY_REALITY_FALLBACK)
    params = {
        "type": "tcp",
        "security": "reality",
        "pbk": profile.get("reality_public_key") or getattr(node, "reality_pbk", ""),
        "fp": profile.get("fingerprint") or getattr(node, "fingerprint", ""),
        "sni": profile.get("tls_server_name") or getattr(node, "reality_sni", ""),
        "sid": profile.get("reality_short_id") or getattr(node, "reality_sid", ""),
        "spx": "/",
        "flow": profile.get("flow") or getattr(node, "flow", ""),
    }
    query = "&".join([f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in params.items()])
    safe_name = urllib.parse.quote(name)
    host = str(profile.get("host") or getattr(node, "host", "") or "")
    port = int(profile.get("port") or getattr(node, "vless_port", 443) or 443)
    return f"vless://{user_uuid}@{host}:{port}?{query}#{safe_name}"


def _node_label_ru(code: str, fallback_name: str = "") -> str:
    """
    Human-friendly labels for clients (Hiddify/sing-box).
    Tags/fragments are often shown directly in apps, so we prefer short Russian names + flags.
    """
    code_raw = (code or "").strip()
    if "free" in code_raw.lower():
        return "🇳🇱 NL Free"
    base = _node_code_base(code_raw)
    flags = {"pl": "🇵🇱", "it": "🇮🇹", "us": "🇺🇸", "nl": "🇳🇱", "brain": "🇩🇪", "de": "🇩🇪", "ru": "🇷🇺"}
    names = {
        "pl": "Польша",
        "it": "Италия",
        "us": "США",
        "nl": "Нидерланды",
        "brain": "Германия",
        "de": "Германия",
        "ru": "Россия",
    }
    flag = flags.get(base, "🏳️")
    nm = names.get(base, fallback_name or (base.upper() if base else (code_raw or "Node")))
    variant = ""
    lowered = code_raw.lower()
    if base and lowered.startswith(base):
        suffix = code_raw[len(base) :].lstrip("._- ").strip()
        if suffix:
            parts = [part for part in re.split(r"[._-]+", suffix) if part]
            variant = " ".join(part.upper() if part.isdigit() else part.capitalize() for part in parts)
    return f"{flag} {nm} {variant}".strip()


def _singbox_rule_set_base_url() -> str:
    configured = str(os.getenv("SINGBOX_RULESET_BASE_URL", "") or "").strip()
    if configured:
        return configured.rstrip("/")
    return f"{public_connect_base_url().rstrip('/')}/rules"


def _singbox_remote_rule_sets() -> list[dict[str, Any]]:
    base_url = _singbox_rule_set_base_url()
    return [
        {
            "type": "remote",
            "tag": "geoip-ru",
            "format": "binary",
            "url": f"{base_url}/geoip-ru.srs",
            "update_interval": "1d",
            "download_detour": "direct",
        },
        {
            "type": "remote",
            "tag": "geosite-category-ads-all",
            "format": "binary",
            "url": f"{base_url}/adblock.srs",
            "update_interval": "1d",
            "download_detour": "direct",
        },
    ]


def _steam_direct_domain_suffixes() -> list[str]:
    # Based on the official community Steam domain list plus the CDN hosts we
    # observed in production traffic. Keeping this local avoids a hard runtime
    # dependency on third-party list availability inside client configs.
    return [
        "a4e8s8k3.map2.ssl.hwcdn.net",
        "edge.steam-dns.top.comcast.net",
        "f3b7q2p3.ssl.hwcdn.net",
        "playartifact.com",
        "s.team",
        "steam-api.com",
        "steam-chat.com",
        "steam.apac.qtlglb.com",
        "steam.cdn.on.net",
        "steam.cdn.orcon.net.nz",
        "steam.cdn.slingshot.co.nz",
        "steam.cdn.webra.ru",
        "steam.eca.qtlglb.com",
        "steam.naeu.qtlglb.com",
        "steam.ru.qtlglb.com",
        "steam.tv",
        "steamcloudsweden.blob.core.windows.net",
        "steamcommunity-a.akamaihd.net",
        "steamcommunity-a.akamaihd.net.edgesuite.net",
        "steamcommunity.com",
        "steamcontent.com",
        "steamdeck.com",
        "steamgames.com",
        "steampipe-kr.akamaized.net",
        "steampipe-partner.akamaized.net",
        "steampipe.akamaized.net",
        "steampowered.com",
        "steamserver.net",
        "steamstatic.com",
        "steamstore-a.akamaihd.net",
        "steamusercontent-a.akamaihd.net",
        "steamusercontent.com",
        "steamuserimages-a.akamaihd.net",
        "steamvideo-a.akamaihd.net",
        "steambroadcast.akamaized.net",
        "steamcdn-a.akamaihd.net",
        "steammobile.akamaized.net",
        "underlords.com",
        "valvesoftware.com",
    ]


def _steam_direct_process_names() -> list[str]:
    return [
        "steam.exe",
        "steamservice.exe",
        "steamwebhelper.exe",
        "steam",
        "steamservice",
        "steamwebhelper",
    ]


def _singbox_common_route_rules(
    *,
    selector_tag: str,
    youtube_direct: bool = False,
    torrent_outbound: str | None = None,
) -> list[dict[str, Any]]:
    youtube_domain_suffix = [
        "youtube.com",
        "youtu.be",
        "ytimg.com",
        "googlevideo.com",
        "youtubei.googleapis.com",
        "yt3.ggpht.com",
    ]
    torrent_target = str(torrent_outbound or "").strip() or "direct"
    rules: list[dict[str, Any]] = [
        {"protocol": "bittorrent", "outbound": torrent_target},
        {"rule_set": ["geoip-ru"], "outbound": "direct"},
        {"process_name": _steam_direct_process_names(), "outbound": "direct"},
        {"domain_suffix": _steam_direct_domain_suffixes(), "outbound": "direct"},
    ]
    if youtube_direct:
        rules.append({"domain_suffix": youtube_domain_suffix, "outbound": "direct"})
    rules.extend(
        [
            {"protocol": "dns", "outbound": "dns-out"},
            {"rule_set": ["geosite-category-ads-all"], "outbound": "block"},
            {"ip_is_private": True, "outbound": "direct"},
        ]
    )
    return rules


def _singbox_tunneled_dns(selector_tag: str) -> dict[str, Any]:
    return {
        "servers": [
            {"tag": "bootstrap", "address": "local"},
            {"tag": "google", "address": "8.8.8.8", "detour": selector_tag},
        ],
        "final": "google",
    }


def _singbox_default_domain_resolver() -> dict[str, str]:
    # Node and direct rule-set hostnames must resolve before the selected
    # tunnel exists. Content DNS remains on the tunneled resolver above.
    return {"server": "bootstrap", "strategy": "prefer_ipv4"}


def _singbox_multi_node_config(
    *,
    user_uuid: str,
    nodes: list,
    title: str,
    transport_profile: str = LEGACY_REALITY_FALLBACK,
    rollout_config: dict[str, Any] | None = None,
) -> dict:
    outbounds = []
    selector_opts = []
    ru_torrent_outbounds: list[str] = []
    selector_tag = "🌍 Страны"
    used_bridge_endpoints_by_id: dict[str, dict[str, Any]] = {}

    for n in nodes:
        tag = _node_label_ru(getattr(n, "code", ""), getattr(n, "name", ""))
        code = str(getattr(n, "code", "") or "").strip().lower()
        base = _node_code_base(code)
        node_bridge_endpoints = _ru_bridge_endpoints_for_node(
            node=n,
            rollout_config=rollout_config or {},
            transport_profile=transport_profile,
        )
        has_bridge_choice = bool(node_bridge_endpoints)
        keep_direct_visible = (
            not has_bridge_choice
            or code in RU_BRIDGE_SELECTOR_DIRECT_CODES
            or base in RU_BRIDGE_SELECTOR_DIRECT_CODES
        )
        if keep_direct_visible:
            selector_opts.append(tag)
        direct_outbound = _node_outbound_from_transport_profile(
            user_uuid=user_uuid,
            node=n,
            tag=tag,
            transport_profile=transport_profile,
        )
        outbounds.append(direct_outbound)
        if base == "ru":
            ru_torrent_outbounds.append(tag)

        if has_bridge_choice:
            for idx, endpoint in enumerate(node_bridge_endpoints):
                bridge_label = str(endpoint.get("label") or ("Белые списки" if idx == 0 else f"Белые списки тип {idx + 1}")).strip()
                bridge_node_tag = f"{tag} · {bridge_label}"
                bridged_outbound = dict(direct_outbound)
                bridged_outbound["tag"] = bridge_node_tag
                bridged_outbound["detour"] = _ru_bridge_endpoint_tag(idx, endpoint)
                outbounds.append(bridged_outbound)
                selector_opts.append(bridge_node_tag)
                used_bridge_endpoints_by_id.setdefault(str(endpoint.get("id") or ""), endpoint)

    selector_default = selector_opts[0] if selector_opts else "direct"
    torrent_outbound_tag = ""
    if ru_torrent_outbounds:
        torrent_outbound_tag = f"POKROV торренты RU{HIDDIFY_HIDDEN_TAG_SUFFIX}"
        outbounds.append(
            {
                "type": "selector",
                "tag": torrent_outbound_tag,
                "outbounds": ru_torrent_outbounds,
                "default": ru_torrent_outbounds[0],
            }
        )
    used_bridge_endpoints = list(used_bridge_endpoints_by_id.values())
    if used_bridge_endpoints:
        for idx, endpoint in enumerate(used_bridge_endpoints):
            outbounds.append(
                _ru_bridge_outbound(
                    user_uuid=user_uuid,
                    rollout_config=rollout_config or {},
                    tag=_ru_bridge_endpoint_tag(idx, endpoint),
                    bridge=endpoint,
                )
            )
    outbounds.extend(
        [
            {
                "type": "selector",
                "tag": selector_tag,
                "outbounds": selector_opts,
                "default": selector_default,
            },
            {"type": "direct", "tag": "direct"},
            {"type": "block", "tag": "block"},
            {"type": "dns", "tag": "dns-out"},
        ]
    )

    meta: dict[str, Any] = {"title": title}
    if used_bridge_endpoints:
        meta["ru_bridge"] = {
            "enabled": True,
            "excluded_node_codes": sorted(transport_node_exclusions(rollout_config or {}, RU_BRIDGE_RELAY)),
            "endpoints": [{"id": item.get("id"), "label": item.get("label")} for item in used_bridge_endpoints],
        }

    return {
        "log": {"level": "warn", "timestamp": True},
        "dns": _singbox_tunneled_dns(selector_tag),
        "inbounds": [],
        "outbounds": outbounds,
        "route": {
            "rule_set": _singbox_remote_rule_sets(),
            "rules": _singbox_common_route_rules(selector_tag=selector_tag, torrent_outbound=torrent_outbound_tag),
            "auto_detect_interface": True,
            "default_domain_resolver": _singbox_default_domain_resolver(),
            "final": selector_tag,
        },
        "experimental": {
            "cache_file": {"enabled": True},
        },
        "_meta": meta,
    }


def _singbox_ru_bridge_config(
    *,
    user_uuid: str,
    nodes: list,
    title: str,
    rollout_config: dict[str, Any],
) -> dict:
    bridge = ru_bridge_relay_config(rollout_config)
    selector_tag = "🌍 Страны"

    outbounds = []
    selector_opts = []
    ru_torrent_outbounds: list[str] = []
    used_bridge_endpoints_by_id: dict[str, dict[str, Any]] = {}

    ordered_nodes = sorted(
        enumerate(nodes),
        key=lambda item: (
            not bool(
                _ru_bridge_endpoints_for_node(
                    node=item[1],
                    rollout_config=rollout_config,
                    transport_profile=RU_BRIDGE_RELAY,
                )
            ),
            item[0],
        ),
    )
    for _idx, n in ordered_nodes:
        label = _node_label_ru(getattr(n, "code", ""), getattr(n, "name", ""))
        code = str(getattr(n, "code", "") or "").strip().lower()
        base = _node_code_base(code)
        selector_opts.append(label)

        country_opts: list[str] = []
        normal_tag = f"{label} · Обычный"
        direct_outbound = _node_outbound_from_transport_profile(
            user_uuid=user_uuid,
            node=n,
            tag=normal_tag,
            transport_profile=LEGACY_REALITY_FALLBACK,
        )
        outbounds.append(direct_outbound)
        country_opts.append(normal_tag)
        if base == "ru":
            ru_torrent_outbounds.append(normal_tag)
        node_bridge_endpoints = _ru_bridge_endpoints_for_node(
            node=n,
            rollout_config=rollout_config,
            transport_profile=RU_BRIDGE_RELAY,
        )
        if not node_bridge_endpoints:
            outbounds.append(
                {
                    "type": "selector",
                    "tag": label,
                    "outbounds": country_opts,
                    "default": normal_tag,
                }
            )
            continue

        for idx, endpoint in enumerate(node_bridge_endpoints):
            bridge_label = str(endpoint.get("label") or ("Белые списки" if idx == 0 else f"Белые списки тип {idx + 1}")).strip()
            bridge_node_tag = f"{label} · {bridge_label}"
            bridged_outbound = dict(direct_outbound)
            bridged_outbound["tag"] = bridge_node_tag
            bridged_outbound["detour"] = _ru_bridge_endpoint_tag(idx, endpoint)
            outbounds.append(bridged_outbound)
            country_opts.append(bridge_node_tag)
            used_bridge_endpoints_by_id.setdefault(str(endpoint.get("id") or ""), endpoint)
        outbounds.append(
            {
                "type": "selector",
                "tag": label,
                "outbounds": country_opts,
                "default": normal_tag,
            }
        )

    selector_default = selector_opts[0] if selector_opts else "direct"
    torrent_outbound_tag = ""
    if ru_torrent_outbounds:
        torrent_outbound_tag = f"POKROV торренты RU{HIDDIFY_HIDDEN_TAG_SUFFIX}"
        outbounds.append(
            {
                "type": "selector",
                "tag": torrent_outbound_tag,
                "outbounds": ru_torrent_outbounds,
                "default": ru_torrent_outbounds[0],
            }
        )
    used_bridge_endpoints = list(used_bridge_endpoints_by_id.values())
    outbounds.extend(
        [
            *[
                _ru_bridge_outbound(
                    user_uuid=user_uuid,
                    rollout_config=rollout_config,
                    tag=_ru_bridge_endpoint_tag(idx, endpoint),
                    bridge=endpoint,
                )
                for idx, endpoint in enumerate(used_bridge_endpoints)
            ],
            {
                "type": "selector",
                "tag": selector_tag,
                "outbounds": selector_opts,
                "default": selector_default,
            },
            {"type": "direct", "tag": "direct"},
            {"type": "block", "tag": "block"},
            {"type": "dns", "tag": "dns-out"},
        ]
    )

    return {
        "log": {"level": "warn", "timestamp": True},
        "dns": _singbox_tunneled_dns(selector_tag),
        "inbounds": [],
        "outbounds": outbounds,
        "route": {
            "rule_set": _singbox_remote_rule_sets(),
            "rules": _singbox_common_route_rules(selector_tag=selector_tag, torrent_outbound=torrent_outbound_tag),
            "auto_detect_interface": True,
            "default_domain_resolver": _singbox_default_domain_resolver(),
            "final": selector_tag,
        },
        "experimental": {"cache_file": {"enabled": True}},
        "_meta": {
            "title": title,
            "ru_bridge": {
                "enabled": bool(used_bridge_endpoints),
                "excluded_node_codes": bridge.get("excluded_node_codes", []),
                "endpoints": [{"id": item.get("id"), "label": item.get("label")} for item in used_bridge_endpoints],
            },
        },
    }


def _singbox_free_allowlist_config(
    *,
    user_uuid: str,
    nodes: list,
    title: str,
    transport_profile: str = LEGACY_REALITY_FALLBACK,
) -> dict:
    """
    Dedicated free-pool config.
    Split-routing defaults are the same as paid:
    - RU direct
    - torrents direct
    - Steam downloads direct
    - everything else via selected outbound
    Additionally for free tier:
    - YouTube direct
    """
    selector_tag = "🌍 Страны"

    outbounds = []
    for n in nodes:
        outbounds.append(
            _node_outbound_from_transport_profile(
                user_uuid=user_uuid,
                node=n,
                tag=_node_label_ru(n.code, n.name),
                transport_profile=transport_profile,
            )
        )

    selector_opts = [o["tag"] for o in outbounds]
    selector_default = selector_opts[0] if selector_opts else "direct"
    outbounds.append(
        {
            "type": "selector",
            "tag": selector_tag,
            "outbounds": selector_opts,
            "default": selector_default,
        }
    )
    outbounds.extend(
        [
            {"type": "direct", "tag": "direct"},
            {"type": "block", "tag": "block"},
            {"type": "dns", "tag": "dns-out"},
        ]
    )

    return {
        "log": {"level": "warn", "timestamp": True},
        "dns": _singbox_tunneled_dns(selector_tag),
        "inbounds": [],
        "outbounds": outbounds,
        "route": {
            "rule_set": _singbox_remote_rule_sets(),
            "rules": _singbox_common_route_rules(selector_tag=selector_tag, youtube_direct=True),
            "auto_detect_interface": True,
            "default_domain_resolver": _singbox_default_domain_resolver(),
            "final": selector_tag,
        },
        "experimental": {"cache_file": {"enabled": True}},
        "_meta": {"title": title},
    }


def _node_accepts_new_clients(node: Any) -> bool:
    return bool(getattr(node, "enabled", True)) and bool(getattr(node, "accepting_new_clients", True)) and not bool(
        getattr(node, "is_draining", False)
    )


def _subscription_excluded_codes() -> set[str]:
    return {
        token.strip().lower()
        for token in str(os.getenv("SUBSCRIPTION_EXCLUDE_NODE_CODES", "") or "").split(",")
        if token.strip()
    }


def _node_allowed_for_plan(
    user: User,
    node: Any,
    *,
    excluded_codes: set[str] | None = None,
    free_code: str | None = None,
) -> bool:
    code = str(getattr(node, "code", "") or "").strip().lower()
    if not code:
        return False
    base = _node_code_base(code)
    excluded = excluded_codes or set()
    if code in excluded or base in excluded:
        return False

    if user_uses_free_pool(user):
        return bool(free_code) and code == str(free_code).strip().lower()

    return node_access_role(node) == PAID_ROLE


def _mapped_nodes_for_user(session, user: User, nodes: list) -> list:
    node_by_id = {int(getattr(node, "id", 0) or 0): node for node in nodes if getattr(node, "id", None) is not None}
    rows = (
        session.query(UserNode)
        .filter(UserNode.tg_id == int(user.tg_id))
        .order_by(UserNode.created_at.asc(), UserNode.id.asc())
        .all()
    )
    out: list[Any] = []
    seen: set[str] = set()
    excluded_codes = _subscription_excluded_codes()
    free_code = str(
        canonical_free_node_code(nodes, access_role=user_free_access_role(user)) or ""
    ).strip().lower()
    for row in rows:
        node = node_by_id.get(int(getattr(row, "node_id", 0) or 0))
        if not node:
            continue
        code = str(getattr(node, "code", "") or "").strip().lower()
        if not code or code in seen:
            continue
        if code in excluded_codes or _node_code_base(code) in excluded_codes:
            continue
        if user_uses_free_pool(user):
            if not free_code or code != free_code:
                continue
        elif not _node_allowed_for_plan(user, node, excluded_codes=excluded_codes, free_code=free_code):
            continue
        seen.add(code)
        out.append(node)
    return out


def _fallback_nodes_for_user(user: User, nodes: list) -> list:
    """
    Per-plan node visibility.
    - FREE: dedicated free pool only.
    - PAID: all enabled paid-role nodes.
    """
    if not nodes:
        return nodes

    excluded_codes = _subscription_excluded_codes()

    def _apply_node_filters(pool: list) -> list:
        # 1) Drop explicitly excluded nodes/country-bases from subscription output.
        filtered = list(pool)
        if excluded_codes:
            filtered = []
            for node in pool:
                code = str(getattr(node, "code", "") or "").strip().lower()
                if not code:
                    continue
                base = _node_code_base(code)
                if code in excluded_codes or base in excluded_codes:
                    continue
                filtered.append(node)
            # Backward-compatible fallback: keep original pool if filter removes everything.
            if not filtered:
                filtered = list(pool)

        return filtered

    candidate_nodes = [node for node in nodes if _node_accepts_new_clients(node)]
    if not candidate_nodes:
        candidate_nodes = list(nodes)

    if not user_uses_free_pool(user):
        paid = [n for n in candidate_nodes if node_access_role(n) == PAID_ROLE]
        return _apply_node_filters(paid)

    free_role = user_free_access_role(user)
    free_code = str(
        canonical_free_node_code(candidate_nodes, access_role=free_role)
        or canonical_free_node_code(nodes, access_role=free_role)
        or ""
    ).strip().lower()
    free_nodes = [n for n in candidate_nodes if str(getattr(n, "code", "") or "").strip().lower() == free_code]
    return _apply_node_filters(free_nodes)


def _nodes_for_user(user: User, nodes: list, session=None) -> list:
    # UserNode is retained as provisioning/history evidence. Runtime candidate
    # visibility follows the current product pool policy instead.
    return _fallback_nodes_for_user(user, nodes)


def _provisioned_node_codes_for_user(session, user: User, nodes: list) -> set[str]:
    node_by_id = {int(getattr(node, "id", 0) or 0): node for node in nodes if getattr(node, "id", None) is not None}
    codes: set[str] = set()
    for row in session.query(UserNode).filter(UserNode.tg_id == int(user.tg_id)).all():
        node = node_by_id.get(int(getattr(row, "node_id", 0) or 0))
        code = str(getattr(node, "code", "") or "").strip().lower() if node else ""
        if code:
            codes.add(code)
    for row in (
        session.query(AccessKey.node_code)
        .filter(AccessKey.tg_id == int(user.tg_id))
        .filter(AccessKey.state.in_(["active", "rotation_requested"]))
        .filter(AccessKey.node_code.isnot(None))
        .all()
    ):
        code = str(getattr(row, "node_code", "") or row[0] or "").strip().lower()
        if code:
            codes.add(code)
    return codes


def _subscription_nodes_for_user(user: User, nodes: list, session) -> list:
    # UserNode/AccessKey rows are provisioning evidence, not a subscription
    # allowlist. Panel reconciliation can succeed before local evidence is fully
    # backfilled, so filtering here would silently collapse paid subscriptions
    # to a stale subset of nodes.
    return _fallback_nodes_for_user(user, nodes)


def _serialize_admin_node(
    n: Node,
    *,
    mapped_users: int = 0,
    network_peak_mbps_24h: float | None = None,
    online_keys_now: int = 0,
    online_connections_now: int = 0,
    alert_kinds: list[str] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or _utcnow()
    last_sample_at = getattr(n, "last_health_at", None) or getattr(n, "last_probe_at", None)
    resolved_alert_kinds = sorted(
        {str(kind) for kind in list(alert_kinds or []) if str(kind or "").strip()}
    )
    memory_used_mb, memory_total_mb = _nullable_node_memory_value(
        used_mb=getattr(n, "memory_used_mb", None),
        total_mb=getattr(n, "memory_total_mb", None),
    )
    disk_used_gb, disk_total_gb, disk_free_gb = _nullable_node_disk_value(
        used_gb=getattr(n, "disk_used_gb", None),
        total_gb=getattr(n, "disk_total_gb", None),
        free_gb=getattr(n, "disk_free_gb", None),
    )
    (
        network_rx_bytes_total,
        network_tx_bytes_total,
        network_rx_mbps,
        network_tx_mbps,
        network_total_mbps,
    ) = _nullable_node_network_value(
        rx_bytes_total=getattr(n, "network_rx_bytes_total", None),
        tx_bytes_total=getattr(n, "network_tx_bytes_total", None),
        rx_mbps=getattr(n, "network_rx_mbps", None),
        tx_mbps=getattr(n, "network_tx_mbps", None),
        total_mbps=getattr(n, "network_total_mbps", None),
    )
    network_port_capacity_mbps = float(NODE_METRICS_PORT_CAPACITY_MBPS or 0.0)
    network_utilization_percent = _network_utilization_percent(network_total_mbps)
    network_peak_utilization_percent_24h = _network_utilization_percent(network_peak_mbps_24h)
    transport_health = sanitize_transport_health(
        getattr(n, "transport_health_json", None)
    )
    last_probe_error_kind = safe_error_kind(getattr(n, "last_probe_error_kind", ""))
    transport_profiles = _transport_profiles_payload(n)
    return {
        "code": n.code,
        "name": n.name,
        "country_code": _node_country_code(str(n.code or "")).upper(),
        "enabled": bool(n.enabled),
        "accepting_new_clients": bool(getattr(n, "accepting_new_clients", True)),
        "is_draining": bool(getattr(n, "is_draining", False)),
        "mapped_users": int(mapped_users),
        "online_keys_now": int(online_keys_now),
        "online_connections_now": int(online_connections_now),
        "is_healthy": bool(getattr(n, "is_healthy", True)),
        "health_score": float(getattr(n, "health_score", 0.0) or 0.0),
        "panel_latency_ms": getattr(n, "panel_latency_ms", None),
        "panel_error_rate": float(getattr(n, "panel_error_rate", 0.0) or 0.0),
        "active_clients": int(getattr(n, "active_clients", 0) or 0),
        "provisioned_clients_count": int(getattr(n, "provisioned_clients_count", getattr(n, "active_clients", 0)) or 0),
        "online_connections_hint": int(getattr(n, "online_connections_hint", 0) or 0),
        "cpu_percent": float(getattr(n, "cpu_percent", 0.0) or 0.0),
        "memory_used_mb": memory_used_mb,
        "memory_total_mb": memory_total_mb,
        "disk_used_gb": disk_used_gb,
        "disk_total_gb": disk_total_gb,
        "disk_free_gb": disk_free_gb,
        "network_rx_bytes_total": network_rx_bytes_total,
        "network_tx_bytes_total": network_tx_bytes_total,
        "network_rx_mbps": network_rx_mbps,
        "network_tx_mbps": network_tx_mbps,
        "network_total_mbps": network_total_mbps,
        "network_rx_mbps_1m": getattr(n, "network_rx_mbps_1m", None),
        "network_tx_mbps_1m": getattr(n, "network_tx_mbps_1m", None),
        "network_rx_mbps_5m": getattr(n, "network_rx_mbps_5m", None),
        "network_tx_mbps_5m": getattr(n, "network_tx_mbps_5m", None),
        "tcp_retrans_percent": getattr(n, "tcp_retrans_percent", None),
        "packet_loss_percent": getattr(n, "packet_loss_percent", None),
        "edge_reachability_ok": getattr(n, "edge_reachability_ok", None),
        "authenticated_egress_ok": getattr(n, "authenticated_egress_ok", None),
        "dataplane_ok": getattr(n, "dataplane_ok", None),
        "dataplane_rtt_ms": getattr(n, "dataplane_rtt_ms", None),
        "capacity_state": str(getattr(n, "capacity_state", "") or "unknown"),
        "capacity_score": getattr(n, "capacity_score", None),
        "capacity_reject_reason": str(getattr(n, "capacity_reject_reason", "") or "") or None,
        "capacity_tx_ratio": node_tx_ratio(n),
        "capacity_tx_mbps": node_tx_mbps(n),
        "network_peak_mbps_24h": float(network_peak_mbps_24h) if network_peak_mbps_24h is not None else None,
        "network_port_capacity_mbps": network_port_capacity_mbps if network_port_capacity_mbps > 0 else None,
        "network_utilization_percent": network_utilization_percent if network_total_mbps is not None else None,
        "network_peak_utilization_percent_24h": (
            network_peak_utilization_percent_24h if network_peak_mbps_24h is not None else None
        ),
        "last_ok_at": _safe_iso(getattr(n, "last_ok_at", None)),
        "last_health_at": _safe_iso(getattr(n, "last_health_at", None)),
        "freshness_status": "stale" if "stale_metrics" in resolved_alert_kinds else "fresh",
        "freshness_age_seconds": int((now - last_sample_at).total_seconds()) if last_sample_at else None,
        "alerts": _legacy_node_alerts(resolved_alert_kinds),
        "alert_kinds": resolved_alert_kinds,
        "last_probe_stage": safe_probe_stage(getattr(n, "last_probe_stage", "")) or None,
        "last_probe_error_kind": last_probe_error_kind or None,
        "last_probe_error_message": safe_probe_error_message(last_probe_error_kind),
        "hoster_family": safe_hoster_family(getattr(n, "hoster_family", "")),
        "hoster_asn": safe_hoster_asn(getattr(n, "hoster_asn", "")),
        "ipv4_health": str(getattr(n, "ipv4_health", "") or "") or None,
        "ipv6_health": str(getattr(n, "ipv6_health", "") or "") or None,
        "probe_classification": safe_probe_classification(
            getattr(n, "last_probe_classification", "")
        )
        or None,
        "transport_health": transport_health,
        "transport_profiles": transport_profiles,
        "observer_last_push_at": _safe_iso(getattr(n, "observer_last_push_at", None)),
        "observer_unmatched_count": int(getattr(n, "observer_unmatched_count", 0) or 0),
        "observer_parse_error_count": int(getattr(n, "observer_parse_error_count", 0) or 0),
        "observer_is_stale": bool(_observer_is_stale(n, now=now)),
        "weight": int(getattr(n, "weight", 0) or 0),
    }


def _target_node_codes_for_resync(session, user: User, source_code: str, nodes: list) -> list[str]:
    source_code = str(source_code or "").strip().lower()
    out: list[str] = []
    seen: set[str] = set()

    for node in _mapped_nodes_for_user(session, user, nodes):
        code = str(getattr(node, "code", "") or "").strip().lower()
        if not code or code == source_code or code in seen:
            continue
        seen.add(code)
        out.append(code)

    for node in _fallback_nodes_for_user(user, nodes):
        code = str(getattr(node, "code", "") or "").strip().lower()
        if not code or code == source_code or code in seen:
            continue
        seen.add(code)
        out.append(code)

    return out


def _token_fingerprint(token: str) -> str:
    text = str(token or "").strip()
    if not text:
        return "empty"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _resolve_subscription_client_format(
    *,
    format_hint: str,
    user_agent: str,
    is_connect_request: bool,
    sub_type: str,
) -> str:
    hint = str(format_hint or "").strip().lower()
    if hint in {"smart", "json", "singbox"}:
        return "singbox"
    if hint == "clash":
        return "clash"
    if hint in {"happ", "happ_plain", "happ-plain"}:
        return "happ"
    if hint in {"vless", "raw"}:
        return "vless_raw"
    if hint in {"plain", "legacy"}:
        return "plain_base64"
    ua = str(user_agent or "").lower()
    if "happ" in ua:
        return "happ"
    is_smart_client = any(x in ua for x in ["hiddify", "dart", "sing-box", "nekobox"])
    if str(sub_type or "").upper() == "FREE" or is_smart_client or is_connect_request:
        return "singbox"
    return "vless_raw"


def _subscription_singbox_config(
    *,
    user_uuid: str,
    sub_type: str,
    nodes: list[Any],
    transport_profile: str,
    rollout_config: dict[str, Any],
) -> dict[str, Any]:
    if transport_profile == RU_BRIDGE_RELAY:
        return _singbox_ru_bridge_config(
            user_uuid=user_uuid,
            nodes=nodes,
            title="POKROV",
            rollout_config=rollout_config,
        )
    if str(sub_type or "").upper() == "FREE":
        return _singbox_free_allowlist_config(
            user_uuid=user_uuid,
            nodes=nodes,
            title="POKROV (Free)",
            transport_profile=transport_profile,
        )
    return _singbox_multi_node_config(
        user_uuid=user_uuid,
        nodes=nodes,
        title="POKROV",
        transport_profile=transport_profile,
        rollout_config=rollout_config,
    )


def _happ_subscription_text(*, singbox_config: dict[str, Any], vless_links: list[str]) -> str:
    lines = [
        "#subscription-auto-update-enable: 1",
        "#subscription-auto-update-open-enable: 1",
        "#subscriptions-collapse: 0",
        "#subscriptions-expand-now: 1",
        "#ping-type: proxy",
        "#check-url-via-proxy: https://cp.cloudflare.com/generate_204",
        "#custom-tunnel-config: "
        + json.dumps(singbox_config, ensure_ascii=False, separators=(",", ":")),
    ]
    lines.extend([line for line in vless_links if str(line or "").strip()])
    return "\n".join(lines) + "\n"


def _subscription_no_cache_headers(headers: dict[str, str]) -> dict[str, str]:
    out = dict(headers)
    out["Cache-Control"] = "no-store, no-cache, max-age=0"
    out["Pragma"] = "no-cache"
    out["X-Content-Type-Options"] = "nosniff"
    return out


def _rank_subscription_nodes(
    *,
    session,
    nodes: list[Any],
    transport_profile: str,
    rollout_config: dict[str, Any],
) -> tuple[list[Any], list[dict[str, Any]]]:
    effective = _effective_transport_nodes(
        nodes=nodes,
        rollout_config=rollout_config,
        transport_profile=transport_profile,
    )
    policy_by_code = _node_capacity_policy_by_code(session)
    ordered = rank_nodes_for_subscription(effective, policy_by_code=policy_by_code, now=_utcnow())
    ordered_codes = {
        str(getattr(node, "code", "") or "").strip().lower()
        for node in ordered
        if str(getattr(node, "code", "") or "").strip()
    }
    excluded: list[dict[str, Any]] = []
    for node in effective:
        code = str(getattr(node, "code", "") or "").strip().lower()
        if not code or code in ordered_codes:
            continue
        excluded.append(
            {
                "code": code,
                "reason": node_hard_reject_reason(node, policy=policy_by_code.get(code), now=_utcnow()) or "not_ranked",
            }
        )
    return ordered, excluded


_PAID_LEGACY_RECOVERY_TELEMETRY_REASONS = frozenset({"stale", "missing_telemetry"})


def _paid_legacy_recovery_nodes(
    *,
    session,
    nodes: list[Any],
    rollout_config: dict[str, Any],
) -> list[Any]:
    """Return only safe paid manual-recovery Reality nodes with stale telemetry."""
    policy_by_code = _node_capacity_policy_by_code(session)
    candidates = _filter_nodes_for_transport_profile(
        nodes=nodes,
        rollout_config=rollout_config,
        transport_profile=LEGACY_REALITY_FALLBACK,
        apply_exclusions=True,
    )
    allowed: list[Any] = []
    for node in candidates:
        if not _node_supports_transport_profile(node, LEGACY_REALITY_FALLBACK):
            continue
        code = str(getattr(node, "code", "") or "").strip().lower()
        reason = node_hard_reject_reason(
            node,
            policy=policy_by_code.get(code),
            now=_utcnow(),
        )
        if reason in _PAID_LEGACY_RECOVERY_TELEMETRY_REASONS:
            allowed.append(node)
    return rank_nodes_legacy(allowed)


def _clash_subscription_config(*, user_uuid: str, nodes: list[Any], title: str, transport_profile: str) -> str:
    lines = [
        "mixed-port: 7890",
        "allow-lan: false",
        "mode: rule",
        "log-level: warning",
        "proxies:",
    ]
    proxy_names: list[str] = []
    for node in nodes:
        code = str(getattr(node, "code", "") or getattr(node, "name", "") or "node").strip()
        if not code:
            continue
        name = _node_label_ru(code, str(getattr(node, "name", "") or code))
        proxy_names.append(name)
        profile = _node_transport_profile(node, transport_profile)
        lines.extend(
            [
                f"  - name: {json.dumps(name, ensure_ascii=False)}",
                "    type: vless",
                f"    server: {json.dumps(str(profile.get('host') or getattr(node, 'host', '') or ''), ensure_ascii=False)}",
                f"    port: {int(profile.get('port') or getattr(node, 'vless_port', 443) or 443)}",
                f"    uuid: {json.dumps(user_uuid, ensure_ascii=False)}",
                "    udp: true",
                "    tls: true",
                f"    servername: {json.dumps(str(profile.get('tls_server_name') or getattr(node, 'reality_sni', '') or ''), ensure_ascii=False)}",
                f"    flow: {json.dumps(str(profile.get('flow') or getattr(node, 'flow', '') or ''), ensure_ascii=False)}",
                f"    client-fingerprint: {json.dumps(str(profile.get('fingerprint') or getattr(node, 'fingerprint', '') or 'firefox'), ensure_ascii=False)}",
                "    reality-opts:",
                f"      public-key: {json.dumps(str(profile.get('reality_public_key') or getattr(node, 'reality_pbk', '') or ''), ensure_ascii=False)}",
                f"      short-id: {json.dumps(str(profile.get('reality_short_id') or getattr(node, 'reality_sid', '') or ''), ensure_ascii=False)}",
            ]
        )
    lines.extend(["proxy-groups:", f"  - name: {json.dumps(title, ensure_ascii=False)}", "    type: select", "    proxies:"])
    for name in proxy_names:
        lines.append(f"      - {json.dumps(name, ensure_ascii=False)}")
    lines.extend(["rules:", f"  - MATCH,{title}"])
    return "\n".join(lines) + "\n"


def _record_subscription_render(
    *,
    user: User,
    token_fp: str,
    lookup_mode: str,
    client_format: str,
    user_agent: str,
    request_host: str,
    node_codes: list[str],
    excluded_nodes: list[dict[str, Any]],
    response_status: int,
    content_text: str,
    profile_revision: str,
) -> None:
    s = SessionLocal()
    try:
        fetch = SubscriptionFetchEvent(
            tg_id=int(user.tg_id),
            token_fp=str(token_fp or "")[:32],
            lookup_mode=str(lookup_mode or "")[:32],
            client_format=str(client_format or "")[:32],
            user_agent_hash=hashlib.sha256(str(user_agent or "").encode("utf-8")).hexdigest() if user_agent else None,
            request_host=str(request_host or "")[:255] or None,
            selected_nodes_json=json.dumps(node_codes, ensure_ascii=False, separators=(",", ":"))[:4000],
            excluded_nodes_json=json.dumps(excluded_nodes, ensure_ascii=False, separators=(",", ":"))[:4000],
            response_status=int(response_status),
            created_at=_utcnow(),
        )
        s.add(fetch)
        s.flush()
        s.add(
            RenderedSubscriptionSnapshot(
                fetch_event_id=int(fetch.id),
                tg_id=int(user.tg_id),
                profile_revision=str(profile_revision or "")[:128] or None,
                client_format=str(client_format or "")[:32],
                node_order_json=json.dumps(node_codes, ensure_ascii=False, separators=(",", ":"))[:4000],
                excluded_nodes_json=json.dumps(excluded_nodes, ensure_ascii=False, separators=(",", ":"))[:4000],
                content_sha256=hashlib.sha256(str(content_text or "").encode("utf-8")).hexdigest(),
                created_at=_utcnow(),
            )
        )
        s.commit()
    except Exception:
        s.rollback()
        logger.exception("failed to record subscription render tg_id=%s format=%s", int(user.tg_id), client_format)
    finally:
        s.close()


async def _notify_admin_on_subscription_fallback(*, user_tg_id: int, token_fp: str) -> None:
    admin_id = int(Settings.ADMIN_ID or 0)
    if admin_id <= 0:
        return
    day_key = _utcnow().strftime("%Y%m%d")
    campaign_key = f"sub_token_fallback:{int(user_tg_id)}:{day_key}"

    s = SessionLocal()
    try:
        if not _mark_campaign_once(s, tg_id=admin_id, campaign_key=campaign_key):
            return
        s.commit()
    except Exception:
        s.rollback()
        return
    finally:
        s.close()

    try:
        track_event(
            tg_id=int(user_tg_id),
            event_name="subscription_numeric_fallback",
            source="subscription",
            meta={"token_fp": token_fp},
        )
    except Exception:
        logger.exception("failed to track subscription numeric fallback tg_id=%s", int(user_tg_id))

    text = (
        "⚠️ Обнаружен fallback подписки по `tg_id`.\n"
        f"user_id: `{int(user_tg_id)}`\n"
        f"token_fp: `{token_fp}`\n\n"
        "Рекомендуется регенерация sub_token и проверка синка subId в панели."
    )
    await _telegram_send_message(chat_id=admin_id, text=text)


@app.get("/api/client/subscription/preview")
async def client_subscription_preview(
    request: Request,
    format: str = Query(default="", alias="format"),
    transport_profile: str = Query(default="", max_length=64),
    x_telegram_init_data: str = Header(default=""),
    x_portal_carrier: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        _maybe_downgrade_expired_to_free(s, user)
        rollout_config = load_network_rollout_config(session=s)
        client_policy = app_first_service.build_client_policy(
            session=s,
            user=user,
            install_id=str(getattr(user, "app_install_id", "") or "").strip() or None,
            carrier=_request_carrier_header(x_portal_carrier),
            rollout_config=rollout_config,
        )
        resolved_profile = str(transport_profile or client_policy.get("transport_profile") or LEGACY_REALITY_FALLBACK).strip()
        resolved_profile = resolved_profile or LEGACY_REALITY_FALLBACK
        nodes = enabled_nodes(s)
        nodes_for_user = _subscription_nodes_for_user(user, nodes, session=s)
        ranked, excluded = _rank_subscription_nodes(
            session=s,
            nodes=nodes_for_user,
            rollout_config=rollout_config,
            transport_profile=resolved_profile,
        )
        request_host = str(request.url.hostname or request.headers.get("host") or "").split(":", 1)[0].strip().lower()
        client_format = _resolve_subscription_client_format(
            format_hint=str(format or "").strip().lower(),
            user_agent=request.headers.get("user-agent", ""),
            is_connect_request=bool(request_host and request_host == public_connect_host()),
            sub_type=str(user.sub_type or ""),
        )
        return {
            "ok": True,
            "client_format": client_format,
            "transport_profile": resolved_profile,
            "profile_revision": str(client_policy.get("profile_revision") or ""),
            "node_order": [str(getattr(node, "code", "") or "").strip().lower() for node in ranked],
            "excluded_nodes": excluded,
            "dynamic_ordering": bool(SUBSCRIPTION_DYNAMIC_ORDERING),
            "hard_exclusion": bool(SUBSCRIPTION_EXCLUDE_HARD_REJECT),
            "subscription_url_available": bool(str(getattr(user, "sub_token", "") or "").strip()),
        }
    finally:
        s.close()


@app.get("/api/admin/subscription/preview")
async def admin_subscription_preview(
    request: Request,
    tg_id: int = Query(gt=0),
    format: str = Query(default="", alias="format"),
    transport_profile: str = Query(default="", max_length=64),
    x_telegram_init_data: str = Header(default=""),
    x_portal_carrier: str = Header(default=""),
) -> dict[str, Any]:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        _maybe_downgrade_expired_to_free(s, user)
        rollout_config = load_network_rollout_config(session=s)
        client_policy = app_first_service.build_client_policy(
            session=s,
            user=user,
            install_id=str(getattr(user, "app_install_id", "") or "").strip() or None,
            carrier=_request_carrier_header(x_portal_carrier),
            rollout_config=rollout_config,
        )
        resolved_profile = str(transport_profile or client_policy.get("transport_profile") or LEGACY_REALITY_FALLBACK).strip()
        resolved_profile = resolved_profile or LEGACY_REALITY_FALLBACK
        nodes = enabled_nodes(s)
        nodes_for_user = _subscription_nodes_for_user(user, nodes, session=s)
        ranked, excluded = _rank_subscription_nodes(
            session=s,
            nodes=nodes_for_user,
            rollout_config=rollout_config,
            transport_profile=resolved_profile,
        )
        request_host = str(request.url.hostname or request.headers.get("host") or "").split(":", 1)[0].strip().lower()
        client_format = _resolve_subscription_client_format(
            format_hint=str(format or "").strip().lower(),
            user_agent=request.headers.get("user-agent", ""),
            is_connect_request=bool(request_host and request_host == public_connect_host()),
            sub_type=str(user.sub_type or ""),
        )
        token_text = str(getattr(user, "sub_token", "") or "").strip()
        return {
            "ok": True,
            "tg_id": int(user.tg_id),
            "sub_type": str(getattr(user, "sub_type", "") or ""),
            "client_format": client_format,
            "transport_profile": resolved_profile,
            "profile_revision": str(client_policy.get("profile_revision") or ""),
            "node_order": [str(getattr(node, "code", "") or "").strip().lower() for node in ranked],
            "excluded_nodes": excluded,
            "dynamic_ordering": bool(SUBSCRIPTION_DYNAMIC_ORDERING),
            "hard_exclusion": bool(SUBSCRIPTION_EXCLUDE_HARD_REJECT),
            "subscription_url_available": bool(token_text),
            "token_fp": _token_fingerprint(token_text) if token_text else None,
        }
    finally:
        s.close()


@app.api_route("/s8Kx2mP7qR4wT/{token}", methods=["GET", "HEAD"])
async def subscription(token: str, request: Request, format: str = Query(default="", alias="format")):
    """
    Multi-node subscription endpoint.
    - token is usually `sub_token`
    - legacy fallback: if token is numeric, treat it as `tg_id`
    """
    token_text = str(token or "").strip()
    token_fp = _token_fingerprint(token_text)
    _enforce_beta_rate_limit("subscription_fetch_ip", request)
    _enforce_beta_rate_limit("subscription_fetch", request, identity=f"token:{token_fp}")
    nodes_for_user: list[Any] = []
    rollout_config = normalized_network_rollout_config({})
    carrier = _request_carrier_header(request.headers.get("X-Portal-Carrier"))
    client_policy = resolved_client_policy(rollout_config=rollout_config, carrier=carrier)
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(sub_token=token_text).first()
        lookup_mode = "sub_token"
        if not user and token_text.isdigit():
            if SUBSCRIPTION_NUMERIC_FALLBACK_ENABLED:
                user = s.query(User).filter_by(tg_id=int(token_text)).first()
                if user:
                    lookup_mode = "tg_id_fallback"
            else:
                logger.warning(
                    "subscription numeric fallback disabled token_fp=%s token_len=%s",
                    token_fp,
                    len(token_text),
                )
        if not user:
            logger.warning("subscription lookup failed token_fp=%s token_len=%s", token_fp, len(token_text))
            _record_security_event(
                "subscription_lookup_failed",
                scope="subscription_fetch",
                fingerprint=token_fp,
                client_ip=_request_client_ip(request),
                reason="unknown_token",
                meta={"token_len": len(token_text)},
            )
            raise HTTPException(status_code=404, detail="User not found")

        _maybe_downgrade_expired_to_free(s, user)

        if not user.is_active:
            logger.info(
                "subscription inactive response token_fp=%s tg_id=%s lookup_mode=%s",
                token_fp,
                int(user.tg_id),
                lookup_mode,
            )
            return Response(content="", media_type="text/plain")

        nodes = enabled_nodes(s)
        nodes_for_user = _subscription_nodes_for_user(user, nodes, session=s)
        rollout_config = load_network_rollout_config(session=s)
        client_policy = app_first_service.build_client_policy(
            session=s,
            user=user,
            install_id=str(getattr(user, "app_install_id", "") or "").strip() or None,
            carrier=carrier,
            rollout_config=rollout_config,
        )
    finally:
        s.close()

    user_agent = request.headers.get("user-agent", "").lower()
    format_hint = str(format or "").strip().lower()
    request_host = str(request.url.hostname or request.headers.get("host") or "").split(":", 1)[0].strip().lower()
    connect_host = public_connect_host()
    is_connect_request = bool(request_host and request_host == connect_host)
    client_format = _resolve_subscription_client_format(
        format_hint=format_hint,
        user_agent=user_agent,
        is_connect_request=is_connect_request,
        sub_type=str(user.sub_type or ""),
    )
    logger.info(
        "subscription resolved token_fp=%s tg_id=%s lookup_mode=%s client_format=%s format_hint=%s host=%s connect_host=%s",
        token_fp,
        int(user.tg_id),
        lookup_mode,
        client_format,
        format_hint or "-",
        request_host or "-",
        bool(is_connect_request),
    )
    if lookup_mode == "tg_id_fallback":
        logger.warning(
            "subscription fallback detected token_fp=%s tg_id=%s action=%s",
            token_fp,
            int(user.tg_id),
            "notify_admin_once_per_day",
        )
        await _notify_admin_on_subscription_fallback(user_tg_id=int(user.tg_id), token_fp=token_fp)

    header_expire = int(user.expiry_at.timestamp()) if user.expiry_at else 0
    total_bytes = _gb_to_bytes(_plan_total_gb(user))
    headers = {
        "Subscription-Userinfo": f"upload=0; download=0; total={total_bytes}; expire={header_expire}",
        "Profile-Update-Interval": str(int(PROFILE_UPDATE_INTERVAL_HOURS)),
        "Content-Disposition": 'attachment; filename="POKROV_Subscription"',
    }
    headers = _subscription_no_cache_headers(headers)
    smart_transport_profile = str(client_policy.get("transport_profile") or LEGACY_REALITY_FALLBACK)
    ranking_session = SessionLocal()
    try:
        smart_nodes_for_user, smart_excluded_nodes = _rank_subscription_nodes(
            session=ranking_session,
            nodes=nodes_for_user,
            rollout_config=rollout_config,
            transport_profile=smart_transport_profile,
        )
        legacy_nodes_for_user, legacy_excluded_nodes = _rank_subscription_nodes(
            session=ranking_session,
            nodes=nodes_for_user,
            rollout_config=rollout_config,
            transport_profile=LEGACY_REALITY_FALLBACK,
        )
        # Smart delivery must fail closed when no eligible node remains.  The
        # explicit legacy/manual formats are a recovery compatibility path,
        # however, so a missing/stale observability sample must not turn their
        # otherwise transport-ready Reality links into an empty 200 response.
        # Keep the same transport/rollout filtering; only skip dynamic hard
        # rejection for this legacy rendering fallback.
        if not legacy_nodes_for_user and str(user.sub_type or "").upper() != "FREE":
            legacy_nodes_for_user = _paid_legacy_recovery_nodes(
                session=ranking_session,
                nodes=nodes_for_user,
                rollout_config=rollout_config,
            )
    finally:
        ranking_session.close()

    # Explicit plain requests must stay on the legacy/manual path even for FREE accounts.
    if client_format == "singbox":
        if (user.sub_type or "").upper() == "FREE" and not smart_nodes_for_user:
            # Dedicated free pool is required for FREE users.
            return Response(content="", media_type="text/plain", status_code=503)

        cfg = _subscription_singbox_config(
            user_uuid=user.uuid,
            sub_type=str(user.sub_type or ""),
            nodes=smart_nodes_for_user,
            transport_profile=smart_transport_profile,
            rollout_config=rollout_config,
        )
        headers["Content-Disposition"] = 'attachment; filename="POKROV.json"'
        headers["Profile-Title"] = "POKROV"
        content_text = json.dumps(cfg, indent=2)
        _record_subscription_render(
            user=user,
            token_fp=token_fp,
            lookup_mode=lookup_mode,
            client_format=client_format,
            user_agent=user_agent,
            request_host=request_host,
            node_codes=[str(getattr(n, "code", "") or "").strip().lower() for n in smart_nodes_for_user],
            excluded_nodes=smart_excluded_nodes,
            response_status=200,
            content_text=content_text,
            profile_revision=str(client_policy.get("profile_revision") or ""),
        )
        if request.method == "HEAD":
            return Response(content="", media_type="application/json", headers=headers)
        return Response(content=content_text, media_type="application/json", headers=headers)

    links = []
    if (user.sub_type or "").upper() == "FREE" and not legacy_nodes_for_user:
        return Response(content="", media_type="text/plain", status_code=503)
    for n in legacy_nodes_for_user:
        links.append(_generate_vless_link(user_uuid=user.uuid, node=n, name=_node_label_ru(n.code, n.name)))
    raw = "\n".join(links)
    if client_format == "happ":
        if (user.sub_type or "").upper() == "FREE" and not smart_nodes_for_user:
            return Response(content="", media_type="text/plain", status_code=503)

        # Happ is an explicit manual compatibility format.  Keep its embedded
        # tunnel config aligned with the legacy VLESS fallback for paid users
        # when dynamic smart ranking has no telemetry-eligible node.
        happ_nodes_for_user = smart_nodes_for_user or legacy_nodes_for_user
        happ_transport_profile = (
            smart_transport_profile
            if smart_nodes_for_user
            else LEGACY_REALITY_FALLBACK
        )
        cfg = _subscription_singbox_config(
            user_uuid=user.uuid,
            sub_type=str(user.sub_type or ""),
            nodes=happ_nodes_for_user,
            transport_profile=happ_transport_profile,
            rollout_config=rollout_config,
        )
        content_text = _happ_subscription_text(singbox_config=cfg, vless_links=links)
        headers["Content-Disposition"] = 'attachment; filename="POKROV_Happ_Subscription"'
        headers["Profile-Title"] = "POKROV"
        headers["subscriptions-collapse"] = "0"
        headers["subscriptions-expand-now"] = "1"
        headers["subscription-auto-update-enable"] = "1"
        headers["subscription-auto-update-open-enable"] = "1"
        headers["ping-type"] = "proxy"
        headers["check-url-via-proxy"] = "https://cp.cloudflare.com/generate_204"
        _record_subscription_render(
            user=user,
            token_fp=token_fp,
            lookup_mode=lookup_mode,
            client_format=client_format,
            user_agent=user_agent,
            request_host=request_host,
            node_codes=[str(getattr(n, "code", "") or "").strip().lower() for n in happ_nodes_for_user],
            excluded_nodes=smart_excluded_nodes,
            response_status=200,
            content_text=content_text,
            profile_revision=str(client_policy.get("profile_revision") or ""),
        )
        if request.method == "HEAD":
            return Response(content="", media_type="text/plain", headers=headers)
        return Response(content=content_text, media_type="text/plain", headers=headers)

    if client_format == "clash":
        content_text = _clash_subscription_config(
            user_uuid=str(user.uuid or ""),
            nodes=legacy_nodes_for_user,
            title="POKROV",
            transport_profile=LEGACY_REALITY_FALLBACK,
        )
        headers["Content-Disposition"] = 'attachment; filename="POKROV.yaml"'
        _record_subscription_render(
            user=user,
            token_fp=token_fp,
            lookup_mode=lookup_mode,
            client_format=client_format,
            user_agent=user_agent,
            request_host=request_host,
            node_codes=[str(getattr(n, "code", "") or "").strip().lower() for n in legacy_nodes_for_user],
            excluded_nodes=legacy_excluded_nodes,
            response_status=200,
            content_text=content_text,
            profile_revision=str(client_policy.get("profile_revision") or ""),
        )
        if request.method == "HEAD":
            return Response(content="", media_type="text/yaml", headers=headers)
        return Response(content=content_text, media_type="text/yaml", headers=headers)

    content_text = raw if client_format == "vless_raw" else base64.b64encode(raw.encode("utf-8")).decode("ascii")
    _record_subscription_render(
        user=user,
        token_fp=token_fp,
        lookup_mode=lookup_mode,
        client_format=client_format,
        user_agent=user_agent,
        request_host=request_host,
        node_codes=[str(getattr(n, "code", "") or "").strip().lower() for n in legacy_nodes_for_user],
        excluded_nodes=legacy_excluded_nodes,
        response_status=200,
        content_text=content_text,
        profile_revision=str(client_policy.get("profile_revision") or ""),
    )
    if request.method == "HEAD":
        return Response(content="", media_type="text/plain", headers=headers)
    return Response(content=content_text, media_type="text/plain", headers=headers)
