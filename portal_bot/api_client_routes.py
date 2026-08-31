"""Managed client feature/runtime routes and compatibility order helpers.

Loaded after the public/auth/session bootstrap slice. Public symbols are
re-exported for backwards compatibility.
"""

try:
    from .module_slices import bootstrap_slice
except ImportError:
    from module_slices import bootstrap_slice

bootstrap_slice(globals())
SMART_CONNECT_LATENCY_EVENT_NAME = "smart_connect_latency_sample"
MANAGED_PROFILE_SYNC_BUDGET_SECONDS = 7.0
MANAGED_PROFILE_PANEL_BUDGET_SECONDS = 8.0


def _managed_profile_runtime_fallback(*, panel_state: str, panel_error: str | None) -> dict[str, Any]:
    return {
        "panel_state": panel_state,
        "panel_error": panel_error,
        "known_nodes": 0,
        "active_nodes": 0,
        "enabled_nodes": 0,
        "active_connections": 0,
        "active_connections_source": "none",
        "active_users_estimate": 0,
        "active_users_source": "none",
        "traffic_up_bytes": 0,
        "traffic_down_bytes": 0,
        "traffic_total_bytes": 0,
        "last_online_at": None,
        "last_online_age_seconds": None,
        "status": "unknown",
    }


async def _managed_profile_panel_state(
    *,
    s,
    user: User,
    nodes: list[Node],
    panel_required: bool,
) -> tuple[bool, dict[str, Any]]:
    if not panel_required:
        return True, _managed_profile_runtime_fallback(
            panel_state="not_required",
            panel_error=None,
        )

    sync_task = asyncio.create_task(
        _sync_control_panel_access(
            user=user,
            timeout_seconds=MANAGED_PROFILE_SYNC_BUDGET_SECONDS,
        )
    )
    runtime_task = asyncio.create_task(
        _get_user_runtime_summary(s=s, user=user, nodes=nodes)
    )
    tasks = {sync_task, runtime_task}
    done, pending = await asyncio.wait(
        tasks,
        timeout=max(0.1, float(MANAGED_PROFILE_PANEL_BUDGET_SECONDS)),
    )
    for task in pending:
        task.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)

    sync_ok = False
    if sync_task in done and not sync_task.cancelled():
        try:
            sync_ok = bool(sync_task.result())
        except Exception:
            sync_ok = False

    runtime = _managed_profile_runtime_fallback(
        panel_state="timeout" if runtime_task in pending else "error",
        panel_error=(
            "panel_runtime_timeout"
            if runtime_task in pending
            else "panel_runtime_failed"
        ),
    )
    if runtime_task in done and not runtime_task.cancelled():
        try:
            candidate = runtime_task.result()
        except Exception:
            candidate = None
        if isinstance(candidate, dict):
            runtime = candidate
    return sync_ok, runtime


class NodeLatencyPointIn(BaseModel):
    node_code: str = Field(min_length=2, max_length=32)
    rtt_ms: int = Field(ge=1, le=60_000)


class NodeLatencySamplesIn(BaseModel):
    profile_revision: str | None = Field(default=None, max_length=128)
    transport_profile: str | None = Field(default=None, max_length=64)
    selected_node_code: str | None = Field(default=None, max_length=32)
    previous_node_code: str | None = Field(default=None, max_length=32)
    stickiness_applied: bool = False
    samples: list[NodeLatencyPointIn] = Field(default_factory=list, max_length=10)


class NodeSelectIn(BaseModel):
    mode: str = Field(default="auto", max_length=16)
    profile_revision: str | None = Field(default=None, max_length=128)
    transport_profile: str | None = Field(default=None, max_length=64)
    selected_node_code: str | None = Field(default=None, max_length=32)
    previous_node_code: str | None = Field(default=None, max_length=32)
    samples: list[NodeLatencyPointIn] = Field(default_factory=list, max_length=16)


class ClientRuntimeStatsIn(BaseModel):
    profile_revision: str | None = Field(default=None, max_length=128)
    selected_node_code: str | None = Field(default=None, max_length=32)
    runtime_phase: str | None = Field(default=None, max_length=32)
    connected: bool | None = None
    uptime_seconds: int | None = Field(default=None, ge=0, le=31_536_000)
    rtt_ms: int | None = Field(default=None, ge=0, le=60_000)
    rx_mbps: float | None = Field(default=None, ge=0)
    tx_mbps: float | None = Field(default=None, ge=0)
    error_code: str | None = Field(default=None, max_length=64)
    route_mode: str | None = Field(default=None, max_length=32)
    duration_ms: int | None = Field(default=None, ge=0, le=3_600_000)
    attempt_number: int | None = Field(default=None, ge=1, le=100)
    retryable: bool | None = None
    network_class: str | None = Field(default=None, max_length=24)


class ClientTelegramLinkEventIn(BaseModel):
    event_name: str = Field(min_length=1, max_length=32)


class AccountOnboardingStatusIn(BaseModel):
    status: str = Field(min_length=7, max_length=9)


class InternalNodeMetricsIn(BaseModel):
    sampled_at: datetime | None = None
    source: str = Field(default="node_agent", max_length=64)
    batch_id: str | None = Field(default=None, max_length=128)
    provisioned_clients_count: int | None = Field(default=None, ge=0)
    online_connections_hint: int | None = Field(default=None, ge=0)
    network_rx_mbps_1m: float | None = Field(default=None, ge=0)
    network_tx_mbps_1m: float | None = Field(default=None, ge=0)
    network_rx_mbps_5m: float | None = Field(default=None, ge=0)
    network_tx_mbps_5m: float | None = Field(default=None, ge=0)
    network_total_mbps: float | None = Field(default=None, ge=0)
    cpu_percent: float | None = Field(default=None, ge=0, le=100)
    memory_used_mb: int | None = Field(default=None, ge=0)
    memory_total_mb: int | None = Field(default=None, ge=0)
    tcp_retrans_percent: float | None = Field(default=None, ge=0)
    packet_loss_percent: float | None = Field(default=None, ge=0)
    dataplane_ok: bool | None = None
    dataplane_rtt_ms: int | None = Field(default=None, ge=0, le=60_000)
    meta: dict[str, Any] | None = None


def _node_capacity_policy_by_code(session) -> dict[str, Any]:
    try:
        rows = session.query(NodeCapacityPolicy).filter(NodeCapacityPolicy.is_enabled == True).all()
    except Exception:
        return {}
    return {
        str(getattr(row, "node_code", "") or "").strip().lower(): row
        for row in rows
        if str(getattr(row, "node_code", "") or "").strip()
    }


def _nodes_by_code(nodes: list[Any]) -> dict[str, Any]:
    return {
        str(getattr(node, "code", "") or "").strip().lower(): node
        for node in nodes
        if str(getattr(node, "code", "") or "").strip()
    }


def _smart_connect_latest_sample(session, *, user: User, install_id: str) -> dict[str, Any]:
    query = session.query(Event).filter(Event.tg_id == int(user.tg_id), Event.event_name == SMART_CONNECT_LATENCY_EVENT_NAME)
    if install_id:
        query = query.filter(Event.session_id == install_id)
    row = query.order_by(Event.created_at.desc(), Event.id.desc()).first()
    if not row:
        return {}
    try:
        payload = json.loads(str(getattr(row, "meta_json", "") or "{}"))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    payload.setdefault("created_at", _safe_iso(getattr(row, "created_at", None)))
    return payload


def _smart_connect_rejection_reason(
    node: Any,
    *,
    transport_profile: str,
    rollout_config: dict[str, Any],
    now: datetime,
    capacity_policy: Any | None = None,
) -> str | None:
    if CAPACITY_AWARE_NODE_SELECTION:
        capacity_reason = node_hard_reject_reason(
            node,
            policy=capacity_policy,
            now=now,
            stale_after_seconds=SMART_CONNECT_STALE_AFTER_SECONDS,
        )
        if capacity_reason:
            return capacity_reason
    if not bool(getattr(node, "enabled", True)):
        return "disabled"
    if not bool(getattr(node, "accepting_new_clients", True)):
        return "not_accepting_new_clients"
    if bool(getattr(node, "is_draining", False)):
        return "draining"
    if not bool(getattr(node, "is_healthy", True)):
        return "unhealthy"
    if node_is_stale(
        node, now=now, stale_after_seconds=SMART_CONNECT_STALE_AFTER_SECONDS
    ):
        return "stale"
    if AUTHENTICATED_EGRESS_ENFORCEMENT_ENABLED:
        if getattr(node, "authenticated_egress_ok", None) is not True:
            return (
                "authenticated_egress_failed"
                if getattr(node, "authenticated_egress_ok", None) is False
                else "authenticated_egress_unavailable"
            )
        authenticated_at = getattr(node, "last_authenticated_egress_at", None)
        if not isinstance(authenticated_at, datetime):
            return "authenticated_egress_unavailable"
        if (
            authenticated_at.tzinfo is not None
            and authenticated_at.utcoffset() is not None
        ):
            authenticated_at = authenticated_at.astimezone(timezone.utc).replace(
                tzinfo=None
            )
        if (now - authenticated_at).total_seconds() > SMART_CONNECT_STALE_AFTER_SECONDS:
            return "authenticated_egress_stale"
    if node_cpu_penalty(node) is None:
        return "cpu_hot"
    transport_value = str(transport_profile or "").strip()
    is_virtual_transport = transport_value in {RU_BRIDGE_RELAY, AWG2_LAB, AWG31_LAB, HY2_LAB}
    is_ru_bridge_relay = transport_value == RU_BRIDGE_RELAY
    required_transport = (
        LEGACY_REALITY_FALLBACK if is_virtual_transport else transport_profile
    )
    if not _node_supports_transport_profile(node, required_transport):
        return "transport_mismatch"
    filtered = _filter_nodes_for_transport_profile(
        nodes=[node],
        rollout_config=rollout_config,
        transport_profile=transport_profile,
        apply_exclusions=not is_ru_bridge_relay,
    )
    if not filtered:
        return "transport_allowlist_mismatch"
    return None


def _smart_connect_shortlist(
    *,
    session,
    user: User,
    nodes: list[Any],
    transport_profile: str,
    rollout_config: dict[str, Any],
    profile_revision: str,
    install_id: str,
    preferred_node_code: str = "",
) -> dict[str, Any]:
    now = _utcnow()
    policy_by_code = _node_capacity_policy_by_code(session)
    rejected_counts: dict[str, int] = {}
    eligible: list[Any] = []
    for node in nodes:
        code = str(getattr(node, "code", "") or "").strip().lower()
        reason = _smart_connect_rejection_reason(
            node,
            transport_profile=transport_profile,
            rollout_config=rollout_config,
            now=now,
            capacity_policy=policy_by_code.get(code),
        )
        if reason:
            rejected_counts[reason] = int(rejected_counts.get(reason, 0) or 0) + 1
            continue
        eligible.append(node)

    eligible = rank_nodes_for_app(eligible, policy_by_code=policy_by_code, now=now)
    requested_preferred_code = str(preferred_node_code or "").strip().lower()
    if requested_preferred_code:
        eligible = sorted(
            eligible,
            key=lambda node: (
                0
                if str(getattr(node, "code", "") or "").strip().lower()
                == requested_preferred_code
                else 1
            ),
        )
    shortlist_limit = 1 if user_uses_free_pool(user) else SMART_CONNECT_SHORTLIST_LIMIT
    shortlist_nodes = eligible[:shortlist_limit]
    shortlist_codes = [
        str(getattr(node, "code", "") or "").strip().lower() for node in shortlist_nodes
    ]
    latest_sample = _smart_connect_latest_sample(
        session, user=user, install_id=install_id
    )
    preferred_node_code = (
        str(latest_sample.get("selected_node_code") or "").strip().lower() or None
    )
    if preferred_node_code and preferred_node_code not in shortlist_codes:
        preferred_node_code = None

    shortlist_payload = []
    for index, node in enumerate(shortlist_nodes, start=1):
        code = str(getattr(node, "code", "") or "").strip().lower()
        transport = _node_transport_profile(
            node,
            LEGACY_REALITY_FALLBACK
            if transport_profile in {AWG2_LAB, AWG31_LAB, HY2_LAB}
            else transport_profile,
        )
        capacity = node_capacity_status(node, policy=policy_by_code.get(code), now=now)
        probe_host = str(
            transport.get("host") or getattr(node, "host", "") or ""
        ).strip()
        probe_port = int(
            transport.get("port") or getattr(node, "vless_port", 443) or 443
        )
        probe_payload = (
            {"host": probe_host, "port": probe_port}
            if transport_profile not in {AWG2_LAB, AWG31_LAB, HY2_LAB}
            and probe_host
            and probe_port > 0
            else None
        )
        shortlist_payload.append(
            {
                "code": code,
                "country": _node_country_name(code),
                "outbound_tag": _node_label_ru(
                    code, str(getattr(node, "name", "") or "")
                ),
                "rank": index,
                "probe": probe_payload,
                "rank_hint": {
                    "health_score": float(getattr(node, "health_score", 0.0) or 0.0),
                    "cpu_percent": float(getattr(node, "cpu_percent", 0.0) or 0.0),
                    "panel_latency_ms": _safe_ping(node),
                    "backend_penalty": int(node_backend_penalty(node) or 0),
                    "cpu_penalty": int(node_cpu_penalty(node) or 0),
                    "capacity_state": str(capacity.get("state") or "unknown"),
                    "capacity_score": float(capacity.get("score") or 0.0),
                    "tx_ratio": capacity.get("tx_ratio"),
                    "tx_mbps": capacity.get("tx_mbps"),
                    "provisioned_clients_count": int(
                        capacity.get("provisioned_clients_count") or 0
                    ),
                    "online_connections_hint": int(
                        capacity.get("online_connections_hint") or 0
                    ),
                    "sticky_preferred": bool(
                        preferred_node_code and preferred_node_code == code
                    ),
                },
            }
        )

    revision_seed = "|".join(
        [
            str(profile_revision or "").strip(),
            str(transport_profile or "").strip(),
            *(item["code"] for item in shortlist_payload),
        ]
    )
    shortlist_revision = (
        hashlib.sha256(revision_seed.encode("utf-8")).hexdigest()[:12]
        if revision_seed
        else ""
    )
    return {
        "eligible": bool(shortlist_payload),
        "fallback_required": not bool(shortlist_payload),
        "shortlist_reason": "eligible" if shortlist_payload else "no_eligible_nodes",
        "shortlist_limit": int(shortlist_limit),
        "shortlist_revision": shortlist_revision,
        "transport_profile": str(transport_profile or ""),
        "profile_revision": str(profile_revision or ""),
        "fallback_order": _managed_manifest_fallback_order(transport_profile),
        "shortlist": shortlist_payload,
        "stickiness": {
            "preferred_node_code": preferred_node_code,
            "threshold_percent": int(SMART_CONNECT_STICKINESS_THRESHOLD_PERCENT),
            "latest_sample_at": latest_sample.get("created_at"),
            "stickiness_applied": bool(latest_sample.get("stickiness_applied", False)),
        },
        "scoring": {
            "formula": "effective_score = rtt_ms + dataplane_rtt + cpu_penalty + backend_penalty + network_pressure",
            "cpu_penalty_buckets": [
                {"range": "<60", "penalty": 0},
                {"range": "60-74", "penalty": 20},
                {"range": "75-84", "penalty": 60},
                {"range": "85-89", "penalty": 120},
                {"range": ">=90", "penalty": "reject"},
            ],
            "backend_penalty_buckets": [
                {"range": ">=90", "penalty": 0},
                {"range": "75-89", "penalty": 30},
                {"range": "60-74", "penalty": 80},
                {"range": "<60", "penalty": 160},
            ],
            "stickiness_threshold_percent": int(
                SMART_CONNECT_STICKINESS_THRESHOLD_PERCENT
            ),
        },
        "rejected_counts": rejected_counts,
    }


def _client_user_session(request: Request, x_telegram_init_data: str) -> tuple[Any, User, dict[str, Any]]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        _maybe_downgrade_expired_to_free(s, user)
        _ensure_free_cycle_state_persisted(s, user)
        return s, user, auth_user
    except Exception:
        s.close()
        raise


def _client_authenticated_install_id(
    session: Any,
    *,
    user: User,
    auth_user: dict[str, Any],
    require_device: bool = False,
) -> str:
    """Resolve the install bound to the authenticated access token.

    Device-pairing sessions belong to an ``AccountDevice`` and must never
    inherit the legacy install id stored on whichever User row represents the
    canonical account. Legacy stateless tokens have no device claim and retain
    the bounded compatibility fallback only for non-secret compatibility
    surfaces. Secret-bearing managed lab profiles require an active device.
    """

    account_id = str(getattr(user, "account_id", "") or "").strip()
    device_id = str((auth_user or {}).get("device_id") or "").strip()
    if device_id:
        device = (
            session.query(AccountDevice)
            .filter(
                AccountDevice.id == device_id,
                AccountDevice.account_id == account_id,
                AccountDevice.state == "active",
                AccountDevice.revoked_at.is_(None),
            )
            .first()
        )
        install_id = str(getattr(device, "install_id", "") or "").strip()
        if install_id:
            return install_id
        raise HTTPException(status_code=403, detail="Authenticated device is unavailable")

    if require_device:
        raise HTTPException(status_code=403, detail="Authenticated device is required")
    return str(getattr(user, "app_install_id", "") or "").strip()


def _client_telemetry_identity(
    session: Any,
    *,
    user: User,
    auth_user: dict[str, Any],
    request: Request,
) -> tuple[str | None, dict[str, Any]]:
    install_id = _client_authenticated_install_id(
        session,
        user=user,
        auth_user=auth_user,
    )
    candidates = install_hmac_candidates(install_id)
    candidate = candidates[0] if candidates else None
    device_id = str((auth_user or {}).get("device_id") or "").strip()
    device = None
    if device_id:
        device = (
            session.query(AccountDevice)
            .filter(
                AccountDevice.id == device_id,
                AccountDevice.account_id == str(getattr(user, "account_id", "") or "").strip(),
            )
            .first()
        )
    _path, ua_platform, ua_version = _safe_client_request_identity(request)
    platform = str(getattr(device, "platform", "") or ua_platform or "unknown").strip().lower()[:24]
    app_version = str(getattr(device, "app_version", "") or ua_version or "unknown").strip()[:32]
    return (
        str(candidate.install_hmac) if candidate is not None else None,
        {
            "platform": platform or "unknown",
            "app_version": app_version or "unknown",
            "install_hmac_version": int(candidate.version) if candidate is not None else None,
        },
    )


def _client_event_meta(value: dict[str, Any] | None) -> str:
    return json.dumps(dict(value or {}), ensure_ascii=False, separators=(",", ":"))[:4000]


def _record_client_event(
    s,
    *,
    user: User,
    event_name: str,
    source: str = "app",
    session_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> None:
    observed_at = _utcnow()
    safe_meta = dict(meta or {})
    error_code = str(safe_meta.get("error_code") or "").strip().lower()
    platform = str(safe_meta.get("platform") or "").strip().lower()
    app_version = str(safe_meta.get("app_version") or "").strip()
    retryable = safe_meta.get("retryable")
    attempt_number = safe_meta.get("attempt_number")
    duration_ms = safe_meta.get("duration_ms")
    network_class = str(safe_meta.get("network_class") or "").strip().lower()
    s.add(
        Event(
            tg_id=int(user.tg_id),
            event_name=str(event_name or "").strip()[:64],
            schema_version=1,
            event_id=str(uuid.uuid4()),
            source=str(source or "app").strip()[:32] or "app",
            session_id=(str(session_id or getattr(user, "app_install_id", "") or "").strip()[:64] or None),
            account_id=str(getattr(user, "account_id", "") or "").strip()[:36] or None,
            platform=platform[:24] or None,
            app_version=app_version[:32] or None,
            surface="app",
            subsystem="runtime" if safe_meta.get("runtime_phase") else None,
            stage=str(safe_meta.get("runtime_phase") or "").strip().lower()[:64] or None,
            result=(
                "success"
                if safe_meta.get("connected") is True
                else "failure"
                if error_code
                else "reported"
            ),
            error_category="runtime" if error_code else None,
            error_code=error_code[:64] or None,
            retryable=bool(retryable) if isinstance(retryable, bool) else None,
            attempt_number=(
                max(1, min(int(attempt_number), 100))
                if isinstance(attempt_number, int)
                else None
            ),
            duration_ms=(
                max(0, min(int(duration_ms), 3_600_000))
                if isinstance(duration_ms, int)
                else None
            ),
            network_class=(
                network_class[:24]
                if re.fullmatch(r"[a-z0-9_.-]{1,24}", network_class)
                else None
            ),
            occurred_at=observed_at,
            received_at=observed_at,
            clock_skew_state="ok",
            meta_json=safe_event_meta_json(safe_meta),
            created_at=observed_at,
        )
    )


def _node_country_code(code: str) -> str:
    base = _node_code_base(code)
    if base == "brain":
        return "de"
    return base or "xx"


def _node_city_name(code: str, fallback_name: str = "") -> str:
    raw = str(code or "").strip().lower()
    parts = [part for part in re.split(r"[-_.]+", raw) if part]
    city_key = parts[1] if len(parts) > 1 and parts[1] != "free" else parts[0] if parts else ""
    cities = {
        "ams": "Amsterdam",
        "nl": "Amsterdam",
        "fra": "Frankfurt",
        "de": "Frankfurt",
        "hel": "Helsinki",
        "fi": "Helsinki",
        "waw": "Warsaw",
        "pl": "Warsaw",
        "lon": "London",
        "gb": "London",
        "uk": "London",
        "nyc": "New York",
        "us": "New York",
        "mil": "Milan",
        "it": "Milan",
        "par": "Paris",
        "fr": "Paris",
        "ru": "Moscow",
    }
    if "free" in raw:
        return cities.get(_node_country_code(raw), "Free node")
    if city_key in cities:
        return cities[city_key]
    cleaned = str(fallback_name or raw or "Node").strip()
    return cleaned[:1].upper() + cleaned[1:] if cleaned else "Node"


def _node_health_ratio(node: Any) -> float:
    try:
        raw = float(getattr(node, "health_score", 0.0) or 0.0)
    except Exception:
        raw = 0.0
    if raw > 1:
        raw = raw / 100.0
    return round(max(0.0, min(raw, 1.0)), 3)


def _node_load_ratio(node: Any) -> float:
    try:
        raw = float(getattr(node, "cpu_percent", 0.0) or 0.0) / 100.0
    except Exception:
        raw = 0.0
    return round(max(0.0, min(raw, 1.0)), 3)


def _node_client_latency_ms(node: Any) -> int | None:
    """Prefer dataplane RTT; panel login latency is only a fallback."""
    for attribute in ("dataplane_rtt_ms", "panel_latency_ms"):
        raw = getattr(node, attribute, None)
        try:
            value = int(raw) if raw is not None else None
        except (TypeError, ValueError):
            value = None
        if value is not None and value >= 0:
            return value
    return None


def _node_matches_query(*, node: Any, country: str, city: str, query: str) -> bool:
    q = str(query or "").strip().lower()
    if not q:
        return True
    haystack = " ".join(
        [
            str(getattr(node, "code", "") or ""),
            str(getattr(node, "name", "") or ""),
            country,
            city,
        ]
    ).lower()
    return q in haystack


def _client_subscription_lane(access_state: str) -> str:
    mapping = {
        "trial_premium": "trialPremium",
        "bonus_premium": "bonusPremium",
        "paid_unlimited": "paidUnlimited",
        "free_monthly": "freeMonthly",
        "free_soft_mode": "freeSoftMode",
    }
    return mapping.get(str(access_state or "").strip().lower(), "expiredOrBlocked")


def _client_days_left(expiry: datetime | None, *, now: datetime | None = None) -> int:
    if not expiry:
        return 0
    current = now or _utcnow()
    seconds = (expiry - current).total_seconds()
    if seconds <= 0:
        return 0
    return int((seconds + 86399) // 86400)


def _client_subscription_plans(s) -> list[dict[str, Any]]:
    plans: list[dict[str, Any]] = []
    for plan in _plan_catalog_payload(s=s, only_active=True):
        code = str(plan.get("code") or "").strip().lower()
        if not code or code == "trial":
            continue
        amount_rub = int(plan.get("amount_rub") or 0)
        days = max(1, int(plan.get("days") or 30))
        title = str(plan.get("label") or "").strip() or (f"{days} days" if days != 30 else "1 month")
        price = f"{amount_rub} ₽" if amount_rub > 0 else ""
        plans.append(
            {
                "id": code,
                "title": title,
                "price": price,
                "days": days,
                "deviceLimit": max(1, int(plan.get("device_limit") or 1)),
                "badge": str(plan.get("badge") or "").strip() or None,
            }
        )
    return plans


def _client_notification_read_ids(s, *, user: User) -> set[str]:
    rows = (
        s.query(Event)
        .filter(Event.tg_id == int(user.tg_id))
        .filter(Event.event_name == "client_notification_read")
        .order_by(Event.created_at.desc(), Event.id.desc())
        .limit(200)
        .all()
    )
    out: set[str] = set()
    for row in rows:
        try:
            payload = json.loads(str(row.meta_json or "{}"))
        except Exception:
            payload = {}
        for item in list((payload or {}).get("ids") or []):
            value = str(item or "").strip()
            if value:
                out.add(value)
    return out


def _client_notification_dismissed_ids(s, *, user: User) -> set[str]:
    rows = (
        s.query(Event)
        .filter(Event.tg_id == int(user.tg_id))
        .filter(Event.event_name == "client_notification_dismissed")
        .order_by(Event.created_at.desc(), Event.id.desc())
        .limit(200)
        .all()
    )
    out: set[str] = set()
    for row in rows:
        try:
            payload = json.loads(str(row.meta_json or "{}"))
        except Exception:
            payload = {}
        for item in list((payload or {}).get("ids") or []):
            value = str(item or "").strip()
            if value:
                out.add(value)
    return out


def _client_notification_items(
    *,
    user: User,
    access_policy: dict[str, Any],
    read_ids: set[str],
    incidents: list[ServiceIncident] | None = None,
    live_updates: list[LiveUpdate] | None = None,
    compensation_grants: list[EntitlementGrant] | None = None,
    program_applications: list[ProgramApplication] | None = None,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    current_now = now or _utcnow()
    items: list[dict[str, Any]] = []
    for incident in list(incidents or [])[:10]:
        notification_id = f"incident.{incident.id}"
        items.append(
            {
                "id": notification_id,
                "kind": "incident",
                "title": str(incident.title or "Инцидент сервиса").strip(),
                "body": str(incident.summary or "Проверяем состояние сервиса.").strip(),
                "createdAt": _safe_iso(incident.started_at or incident.created_at or _utcnow()),
                "ctaLabel": "Статус защиты",
                "ctaHref": f"{_public_webapp_url().rstrip('/')}/protection/",
                "read": notification_id in read_ids,
            }
        )
    for grant in list(compensation_grants or [])[:10]:
        try:
            metadata = json.loads(str(grant.metadata_json or "{}"))
        except Exception:
            metadata = {}
        notification_id = f"compensation.{grant.id}"
        title = str((metadata or {}).get("incident_title") or "Компенсация за инцидент").strip()
        days = max(0, int(grant.duration_days or 0))
        items.append(
            {
                "id": notification_id,
                "kind": "compensation",
                "title": title,
                "body": f"Начислили {days} дн. после подтверждённого инцидента.",
                "createdAt": _safe_iso(grant.created_at or _utcnow()),
                "ctaLabel": "Открыть кабинет",
                "ctaHref": _public_webapp_url(),
                "read": notification_id in read_ids,
            }
        )
    for update in list(live_updates or [])[:10]:
        notification_id = f"release.{update.id}"
        update_href = _build_tg_post_link(
            channel_username=getattr(update, "channel_username", None),
            post_id=getattr(update, "post_id", None),
            fallback_link=str(update.link or "").strip(),
        )
        items.append(
            {
                "id": notification_id,
                "kind": "release",
                "title": str(update.title or "Обновление POKROV").strip(),
                "body": str(update.summary or "Доступно новое обновление.").strip(),
                "createdAt": _safe_iso(update.published_at or update.created_at or _utcnow()),
                "ctaLabel": "Подробнее",
                "ctaHref": update_href or None,
                "read": notification_id in read_ids,
            }
        )
    access_state = str(access_policy.get("access_state") or "").strip().lower()
    expiry_at = getattr(user, "expiry_at", None)
    access_kind = {
        "trial_premium": "trial",
        "bonus_premium": "bonus",
        "paid_unlimited": "paid",
    }.get(access_state)
    if not access_kind:
        plan_code = str(getattr(user, "current_plan_code", "") or "").strip().lower()
        sub_type = str(getattr(user, "sub_type", "") or "").strip().upper()
        if plan_code == "trial" or sub_type.startswith("TRIAL"):
            access_kind = "trial"
        elif plan_code in {"channel_bonus", "bonus"} or sub_type.startswith("BONUS"):
            access_kind = "bonus"
        elif expiry_at is not None:
            access_kind = "paid"
    access_stage = ""
    if expiry_at is not None and access_kind:
        delta = expiry_at - current_now
        if access_kind == "paid" and timedelta(days=2) < delta <= timedelta(days=3):
            access_stage = "t3"
        elif timedelta(hours=20) < delta <= timedelta(hours=28):
            access_stage = "t1"
        elif timedelta(hours=-1) <= delta <= timedelta(hours=1):
            access_stage = "t0"
    if access_stage and access_kind and expiry_at is not None:
        notification_id = f"access.{access_kind}.{access_stage}.{expiry_at.date().isoformat()}"
        if access_stage == "t3":
            title = "Доступ закончится через 3 дня"
            body = "Продлите заранее, если хотите сохранить подключение без паузы."
        elif access_stage == "t1":
            title = "Пробный период закончится завтра" if access_kind == "trial" else "До окончания доступа 1 день"
            body = "Выберите подходящий срок — автосписаний нет."
        elif expiry_at > current_now:
            title = "Доступ заканчивается сегодня"
            body = "Продлить можно в кабинете. Автосписаний нет."
        else:
            title = "Доступ закончился"
            body = "Выберите срок, чтобы снова подключить POKROV."
        items.append(
            {
                "id": notification_id,
                "kind": "access",
                "title": title,
                "body": body,
                "createdAt": _safe_iso(expiry_at),
                "ctaLabel": "Выбрать срок",
                "ctaHref": _public_webapp_url(),
                "read": notification_id in read_ids,
            }
        )
    program_titles = {
        "competitor_switch": "Переход от другого VPN",
        "research": "Исследование POKROV",
        "team_pack": "Набор для команды",
    }
    status_bodies = {
        "submitted": "Заявка принята и ждёт проверки.",
        "under_review": "Оператор проверяет заявку.",
        "approved": "Заявка одобрена. Детали доступны в кабинете.",
        "rejected": "Проверка завершена без начисления.",
        "rewarded": "Проверка завершена, подтверждённая награда начислена.",
        "cancelled": "Заявка отменена.",
    }
    for application in list(program_applications or [])[:10]:
        status = str(application.status or "submitted").strip().lower()
        notification_id = f"program.{application.id}.{status}"
        days = max(0, int(application.reward_days or 0))
        body = status_bodies.get(status, "Статус заявки изменился.")
        if status == "rewarded" and days:
            body = f"Проверка завершена: начислено {days} дн."
        items.append(
            {
                "id": notification_id,
                "kind": "program",
                "title": program_titles.get(str(application.kind or ""), "Заявка POKROV"),
                "body": body,
                "createdAt": _safe_iso(application.updated_at or application.created_at or _utcnow()),
                "ctaLabel": "Открыть заявки",
                "ctaHref": f"{_public_webapp_url().rstrip('/')}/programs/",
                "read": notification_id in read_ids,
            }
        )
    return sorted(
        items,
        key=lambda item: str(item.get("createdAt") or ""),
        reverse=True,
    )[:30]


ASSISTANT_DIAGNOSTIC_KEYS = frozenset(
    {
        "account_access_state",
        "account_days_left",
        "account_device_count",
        "account_plan",
        "account_telegram_linked",
        "public_promo_state",
        "public_promo_codes",
        "app_version",
        "panel_active_connections",
        "panel_last_online_age_seconds",
        "panel_runtime_state",
        "platform",
        "route_mode",
        "connection_status",
        "connection_active",
        "current_location_label",
        "enhanced_protection_state",
        "enhanced_protection_consent",
        "enhanced_protection_available",
        "telegram_bonus_state",
    }
)


def _admit_support_assistant_diagnostics(raw_value: Any) -> dict[str, str | int | bool | None]:
    if not isinstance(raw_value, dict) or len(raw_value) > 20:
        raise HTTPException(status_code=422, detail="Invalid safe diagnostics")
    admitted: dict[str, str | int | bool | None] = {}
    for key in ASSISTANT_DIAGNOSTIC_KEYS:
        if key not in raw_value:
            continue
        value = raw_value[key]
        if isinstance(value, str):
            if len(value) > 512 or any(ord(char) < 32 and char not in "\t\n\r" for char in value):
                raise HTTPException(status_code=422, detail="Invalid safe diagnostics")
            admitted[key] = value
        elif type(value) in {int, bool} or value is None:
            admitted[key] = value
        else:
            raise HTTPException(status_code=422, detail="Invalid safe diagnostics")
    serialized = json.dumps(admitted, ensure_ascii=False, separators=(",", ":"))
    if len(serialized) > 4096:
        raise HTTPException(status_code=422, detail="Invalid safe diagnostics")
    return admitted


def _support_assistant_promo_snapshot(*, s, user: User) -> dict[str, str | None]:
    """List only live segment-matched campaign codes for this account."""

    try:
        now = _utcnow()
        campaigns = (
            s.query(IncentiveCampaign)
            .filter(func.lower(IncentiveCampaign.campaign_type) == "promo")
            .filter(IncentiveCampaign.is_active == True)
            .order_by(IncentiveCampaign.id.desc())
            .limit(24)
            .all()
        )
        active_capacity_units = active_entitlement_capacity_units(s, now=now)
        codes: list[str] = []
        for campaign in campaigns:
            policy = evaluate_campaign_policy(
                campaign,
                active_units=active_capacity_units,
                now=now,
            )
            if not bool(policy.get("activation_allowed")):
                continue
            if campaign.starts_at and campaign.starts_at > now:
                continue
            if campaign.ends_at and campaign.ends_at <= now:
                continue
            maximum = int(campaign.max_activations or -1)
            if maximum >= 0 and int(campaign.activations_count or 0) >= maximum:
                continue
            if not _campaign_segment_match(
                user=user, segment=str(campaign.segment or "all_active")
            ):
                continue
            code = str(campaign.target_value or "").strip().upper()
            if not re.fullmatch(r"[A-Z0-9][A-Z0-9_-]{1,19}", code) or code in codes:
                continue
            promo = (
                s.query(PromoCode).filter(func.upper(PromoCode.code) == code).first()
            )
            if promo is None:
                continue
            if int(promo.uses_left or 0) == 0:
                continue
            if promo.expires_at and promo.expires_at <= now:
                continue
            if str(promo.promo_type or "").strip().lower() not in {"days", "discount"}:
                continue
            if int(promo.value or 0) <= 0:
                continue
            used = (
                s.query(PromoUsage.id)
                .filter(
                    PromoUsage.tg_id == int(user.tg_id),
                    func.upper(PromoUsage.promo_code) == code,
                )
                .first()
            )
            if used is not None:
                continue
            codes.append(code)
            if len(codes) >= 3:
                break
        return {
            "public_promo_state": "available" if codes else "none",
            "public_promo_codes": ",".join(codes) or None,
        }
    except Exception:
        logger.warning("support assistant promo snapshot lookup failed")
        return {"public_promo_state": "unavailable", "public_promo_codes": None}


async def _support_assistant_account_diagnostics(*, s, user: User) -> dict[str, str | int | bool | None]:
    """Return a same-account, identifier-free snapshot for the support agent."""
    runtime: dict[str, Any]
    try:
        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        runtime = await _get_user_runtime_summary(s=s, user=user, nodes=nodes_for_user)
    except Exception:
        logger.warning("support assistant account snapshot panel lookup failed")
        runtime = {"panel_state": "error", "status": "unknown", "traffic_total_bytes": 0}

    access_policy = _build_reconciled_access_policy(
        session=s,
        user=user,
        used_bytes=int(runtime.get("traffic_total_bytes", 0) or 0),
        source="support_assistant_runtime",
    )
    access_state = str(access_policy.get("access_state") or "expired_or_blocked").strip().lower()
    days_left = _client_days_left(getattr(user, "expiry_at", None))
    if access_state == "trial_premium":
        days_left = min(days_left, int(APP_TRIAL_DEFAULT_DAYS))

    plan_code = re.sub(
        r"[^a-z0-9_.:-]+",
        "_",
        str(getattr(user, "current_plan_code", "") or "").strip().lower(),
    )[:64]
    account_id = str(getattr(user, "account_id", "") or "").strip()
    device_count = 0
    if account_id:
        device_count = int(
            s.query(func.count(AccountDevice.id))
            .filter(
                AccountDevice.account_id == account_id,
                AccountDevice.state == "active",
                AccountDevice.revoked_at.is_(None),
            )
            .scalar()
            or 0
        )

    linked_telegram_id = _linked_telegram_id(user)
    telegram_linked = bool(
        linked_telegram_id
        or (not _is_app_or_email_account(user) and int(getattr(user, "tg_id", 0) or 0) > 0)
    )
    channel_status = channel_bonus_service.channel_bonus_status(s, user=user)
    if bool(channel_status.get("claimed")):
        telegram_bonus_state = "claimed"
    elif not bool(getattr(user, "tos_accepted", False)):
        telegram_bonus_state = "tos_required"
    elif str(getattr(user, "sub_type", "") or "").strip().upper() == "MANUAL":
        telegram_bonus_state = "unavailable"
    else:
        telegram_bonus_state = "available"

    panel_state = str(runtime.get("panel_state") or "error").strip().lower()
    panel_runtime_state = (
        str(runtime.get("status") or "unknown").strip().lower()
        if panel_state == "ok"
        else "unavailable"
    )
    last_online_age = runtime.get("last_online_age_seconds")
    return {
        "account_access_state": access_state,
        "account_days_left": max(0, int(days_left)),
        "account_device_count": max(0, device_count),
        "account_plan": plan_code or None,
        "account_telegram_linked": telegram_linked,
        "panel_active_connections": max(0, int(runtime.get("active_connections", 0) or 0)),
        "panel_last_online_age_seconds": (
            max(0, int(last_online_age)) if last_online_age is not None else None
        ),
        "panel_runtime_state": panel_runtime_state,
        "telegram_bonus_state": telegram_bonus_state,
        **_support_assistant_promo_snapshot(s=s, user=user),
    }


def _client_location_variants(
    *,
    node: Any,
    rollout_config: dict[str, Any],
    transport_profile: str,
) -> list[dict[str, str]]:
    variants = [
        {
            "id": "direct",
            "label": "Обычный",
            "description": "Прямое подключение",
        }
    ]
    seen_ids = {"direct"}
    for endpoint in _ru_bridge_endpoints_for_node(
        node=node,
        rollout_config=rollout_config,
        transport_profile=transport_profile,
    ):
        endpoint_id = str(endpoint.get("id") or "").strip().lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,63}", endpoint_id) or endpoint_id in seen_ids:
            continue
        label = " ".join(str(endpoint.get("label") or "Белые списки").split())[:48].strip()
        if not label:
            label = "Белые списки"
        variants.append(
            {
                "id": endpoint_id,
                "label": label,
                "description": "Для ограниченных сетей",
            }
        )
        seen_ids.add(endpoint_id)
    return variants


@app.get("/api/client/locations")
async def client_locations_catalog(
    request: Request,
    platform: str = Query(default="", max_length=32),
    q: str = Query(default="", max_length=80),
    x_telegram_init_data: str = Header(default=""),
    x_portal_carrier: str = Header(default=""),
) -> dict[str, Any]:
    del platform
    s, user, auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        rollout_config = load_network_rollout_config(session=s)
        install_id = _client_authenticated_install_id(s, user=user, auth_user=auth_user)
        client_policy = app_first_service.build_client_policy(
            session=s,
            user=user,
            install_id=install_id,
            carrier=_request_carrier_header(x_portal_carrier),
            rollout_config=rollout_config,
        )
        transport_profile = str(client_policy.get("transport_profile") or LEGACY_REALITY_FALLBACK).strip() or LEGACY_REALITY_FALLBACK
        all_nodes = enabled_nodes(s)
        free_pool_code = canonical_free_node_code(all_nodes, access_role=user_free_access_role(user))
        nodes_for_user = _nodes_for_user(user, all_nodes, session=s)
        smart_connect = _smart_connect_shortlist(
            session=s,
            user=user,
            nodes=nodes_for_user,
            transport_profile=transport_profile,
            rollout_config=rollout_config,
            profile_revision=str(client_policy.get("profile_revision") or ""),
            install_id=install_id,
        )

        grouped: dict[str, dict[str, Any]] = {}
        now = _utcnow()
        query = str(q or "").strip().lower()
        for node in nodes_for_user:
            reason = _smart_connect_rejection_reason(
                node,
                transport_profile=transport_profile,
                rollout_config=rollout_config,
                now=now,
            )
            if reason:
                continue
            code = str(getattr(node, "code", "") or "").strip().lower()
            if not code:
                continue
            country_code = _node_country_code(code)
            country = _node_country_name(code)
            city = _node_city_name(code, str(getattr(node, "name", "") or ""))
            if not _node_matches_query(node=node, country=country, city=city, query=query):
                continue
            transport = _node_transport_profile(node, transport_profile)
            probe_host = str(transport.get("host") or getattr(node, "host", "") or "").strip()
            probe_port = int(transport.get("port") or getattr(node, "vless_port", 443) or 443)
            city_row = {
                "code": code,
                "city": city,
                "country": country,
                "countryCode": country_code,
                "healthScore": _node_health_ratio(node),
                "latencyMs": _node_client_latency_ms(node),
                "latencySource": "brain",
                "premium": not node_is_free(node),
                "load": _node_load_ratio(node),
                "measuredAt": _safe_iso(getattr(node, "last_health_at", None)),
                "variants": _client_location_variants(
                    node=node,
                    rollout_config=rollout_config,
                    transport_profile=transport_profile,
                ),
                "probe": (
                    {"host": probe_host, "port": probe_port}
                    if probe_host and 0 < probe_port <= 65535
                    else None
                ),
            }
            bucket = grouped.setdefault(
                country_code,
                {"code": country_code, "country": country, "cities": []},
            )
            bucket["cities"].append(city_row)

        countries = list(grouped.values())
        for country in countries:
            country["cities"].sort(key=lambda item: (item.get("premium") is False, item.get("latencyMs") or 999999, item.get("city") or ""))
        countries.sort(key=lambda item: str(item.get("country") or ""))
        all_codes = [city["code"] for country in countries for city in country["cities"]]
        preferred_code = str((smart_connect.get("stickiness") or {}).get("preferred_node_code") or "").strip().lower()
        current_code = preferred_code if preferred_code in all_codes else (all_codes[0] if all_codes else None)
        return {
            "auto": {
                "enabled": bool(smart_connect.get("eligible")),
                "currentCode": current_code,
            },
            "countries": countries,
            "freePoolCode": str(free_pool_code or "").strip().lower() or None,
            "query": query,
            "search": {
                "matched": len(all_codes),
                "source": "nodes",
                "interactive": True,
            },
            "profileRevision": str(client_policy.get("profile_revision") or ""),
            "transportProfile": transport_profile,
        }
    finally:
        s.close()


@app.get("/api/client/subscription")
async def client_subscription(request: Request, x_telegram_init_data: str = Header(default="")) -> dict[str, Any]:
    s, user, _auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        runtime = await _get_user_runtime_summary(s=s, user=user, nodes=nodes_for_user)
        access_policy = _build_reconciled_access_policy(
            session=s,
            user=user,
            used_bytes=int(runtime.get("traffic_total_bytes", 0) or 0),
            source="client_subscription_runtime",
        )
        access_state = str(access_policy.get("access_state") or "")
        expiry = getattr(user, "expiry_at", None)
        days_left = _client_days_left(expiry)
        if access_state == "trial_premium":
            days_left = min(days_left, int(APP_TRIAL_DEFAULT_DAYS))
        linked_telegram_id = _linked_telegram_id(user)
        telegram_native = bool(
            not _is_app_or_email_account(user)
            and int(getattr(user, "tg_id", 0) or 0) > 0
        )
        telegram_linked = bool(linked_telegram_id or telegram_native)
        telegram_username = str(
            getattr(
                user,
                "username" if telegram_native else "linked_telegram_username",
                "",
            )
            or ""
        ).strip()
        email_identity = _verified_email_identity_for_account_family(s, user=user)
        return {
            "lane": _client_subscription_lane(access_state),
            "accessState": access_state,
            "expiresAt": _safe_iso(expiry),
            "daysLeft": days_left,
            "autoRenew": False,
            "renewUrl": _checkout_url_for_user(tg_id=int(user.tg_id), source="app"),
            "plans": _client_subscription_plans(s),
            "trafficPolicy": dict(access_policy.get("traffic_policy") or {}),
            "usage": {
                "trafficUsedBytes": int(runtime.get("traffic_total_bytes", 0) or 0),
                "activeConnections": int(runtime.get("active_connections", 0) or 0),
                "lastOnlineAt": runtime.get("last_online_at"),
                "source": (
                    "panel_runtime"
                    if runtime.get("panel_state") == "ok"
                    else "unavailable"
                ),
            },
            "currentPlanCode": str(getattr(user, "current_plan_code", "") or "").strip() or None,
            "identities": {
                "telegram": {
                    "linked": telegram_linked,
                    "username": telegram_username or None,
                    "source": "native" if telegram_native else ("linked" if linked_telegram_id else None),
                },
                "email": {
                    "linked": email_identity is not None,
                    "address": (
                        str(getattr(email_identity, "email", "") or "").strip() or None
                        if email_identity is not None
                        else None
                    ),
                    "verified": bool(email_identity and getattr(email_identity, "is_verified", False)),
                },
            },
        }
    finally:
        s.close()


def _device_pairing_http_error(exc: device_pairing_service.DevicePairingError) -> HTTPException:
    status_by_code = {
        "pairing_not_configured": 503,
        "pairing_not_found": 404,
        "pairing_code_invalid": 400,
        "pairing_code_expired": 410,
        "pairing_code_used": 409,
        "device_invalid": 400,
        "device_already_registered": 409,
        "device_identity_conflict": 409,
        "device_limit_reached": 409,
        "account_not_found": 409,
    }
    message_by_code = {
        "pairing_not_configured": "Привязка устройств пока не настроена.",
        "pairing_not_found": "Код привязки не найден.",
        "pairing_code_invalid": "Код не подошёл. Проверьте восемь символов.",
        "pairing_code_expired": "Код истёк. Создайте новый на уже связанном устройстве.",
        "pairing_code_used": "Этот код уже использован или отменён.",
        "device_invalid": "Не удалось определить новое устройство.",
        "device_already_registered": "Это устройство уже связано. Используйте восстановление доступа.",
        "device_identity_conflict": "Это устройство связано с другим аккаунтом.",
        "device_limit_reached": "Лимит устройств исчерпан. Сначала отвяжите старое устройство.",
        "account_not_found": "Аккаунт для привязки недоступен.",
    }
    code = str(exc.code or "pairing_failed")
    return HTTPException(
        status_code=int(status_by_code.get(code, 400)),
        detail={"code": code, "message": message_by_code.get(code, "Не удалось привязать устройство.")},
    )


@app.post("/api/client/device-pairing/codes")
async def client_device_pairing_issue(
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        _enforce_beta_rate_limit("device_pairing_issue", request, identity=f"account:{user.account_id}")
        now = _utcnow()
        issued = device_pairing_service.issue_pairing_code(
            s,
            account_id=str(user.account_id or ""),
            issued_by_session_id=str(auth_user.get("session_id") or "") or None,
            now=now,
        )
        _record_client_event(
            s,
            user=user,
            event_name="device_pairing_code_issued",
            meta={"pairing_id": str(issued.row.id), "expires_at": _safe_iso(issued.row.expires_at)},
        )
        s.commit()
        manual_code = str(issued.code)
        return {
            "ok": True,
            "pairing": {
                **device_pairing_service.pairing_code_public_payload(issued.row),
                "code": manual_code,
                "pairing_uri": f"pokrov://pair?code={urlencode({'code': manual_code}).split('=', 1)[-1]}",
                "ttl_seconds": int((issued.row.expires_at - now).total_seconds()),
            },
        }
    except device_pairing_service.DevicePairingError as exc:
        s.rollback()
        raise _device_pairing_http_error(exc) from exc
    finally:
        s.close()


@app.get("/api/client/device-pairing/codes")
async def client_device_pairing_codes(
    request: Request,
    x_telegram_init_data: str = Header(default=""),
    limit: int = Query(default=10, ge=1, le=25),
) -> dict[str, Any]:
    s, user, _auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        rows = device_pairing_service.list_pairing_codes(
            s,
            account_id=str(user.account_id or ""),
            now=_utcnow(),
            limit=limit,
        )
        s.commit()
        return {"ok": True, "items": [device_pairing_service.pairing_code_public_payload(row) for row in rows]}
    except device_pairing_service.DevicePairingError as exc:
        s.rollback()
        raise _device_pairing_http_error(exc) from exc
    finally:
        s.close()


@app.delete("/api/client/device-pairing/codes/{pairing_id}")
async def client_device_pairing_cancel(
    pairing_id: str,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, _auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        row = device_pairing_service.cancel_pairing_code(
            s,
            account_id=str(user.account_id or ""),
            pairing_id=pairing_id,
            now=_utcnow(),
        )
        s.commit()
        return {"ok": True, "pairing": device_pairing_service.pairing_code_public_payload(row)}
    except device_pairing_service.DevicePairingError as exc:
        s.rollback()
        raise _device_pairing_http_error(exc) from exc
    finally:
        s.close()


@app.post("/api/client/device-pairing/claim")
async def client_device_pairing_claim(payload: ClientDevicePairingClaimIn, request: Request) -> dict[str, Any]:
    code_fp = hashlib.sha256(str(payload.code or "").strip().upper().encode("utf-8")).hexdigest()[:24]
    install_fp = hashlib.sha256(str(payload.install_id or "").strip().encode("utf-8")).hexdigest()[:24]
    _enforce_beta_rate_limit("device_pairing_claim_ip", request)
    _enforce_beta_rate_limit("device_pairing_claim", request, identity=f"{code_fp}:{install_fp}")
    now = _utcnow()
    s = SessionLocal()
    try:
        claimed = device_pairing_service.claim_pairing_code(
            s,
            code=payload.code,
            install_id=payload.install_id,
            device_name=payload.device_name,
            platform=payload.platform,
            os_version=payload.os_version,
            app_version=payload.app_version,
            locale=payload.locale,
            time_zone=payload.time_zone,
            device_limit_resolver=_plan_device_limit,
            now=now,
        )
        owner = (
            s.query(User)
            .filter(User.account_id == str(claimed.row.account_id))
            .order_by(User.tg_id.asc())
            .first()
        )
        if owner is not None:
            _record_client_event(
                s,
                user=owner,
                event_name="device_pairing_claimed",
                session_id=str(payload.install_id),
                meta={"pairing_id": str(claimed.row.id), "platform": str(payload.platform)},
            )
        session_payload = claimed.session.response_payload(now=now)
        session_payload["scope"] = "client"
        s.commit()
        return {
            "ok": True,
            "token": claimed.session.access_token,
            "session_token": claimed.session.access_token,
            "access_token": claimed.session.access_token,
            "refresh_token": claimed.session.refresh_token,
            "token_type": "Bearer",
            "expires_in": session_payload["expires_in"],
            "refresh_expires_in": session_payload["refresh_expires_in"],
            "canonical_account_id": claimed.session.account_id,
            "session": session_payload,
        }
    except device_pairing_service.DevicePairingError as exc:
        s.rollback()
        raise _device_pairing_http_error(exc) from exc
    finally:
        s.close()


@app.get("/api/client/programs")
async def client_programs(request: Request, x_telegram_init_data: str = Header(default="")) -> dict[str, Any]:
    s, user, _auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        rows = program_application_service.list_account_applications(
            s,
            account_id=str(user.account_id or ""),
        )
        return {
            "ok": True,
            "capabilities": _public_program_capabilities(),
            "applications": [program_application_service.application_payload(row) for row in rows],
        }
    finally:
        s.close()


@app.post("/api/client/programs/applications")
async def client_program_application_create(
    payload: ProgramApplicationCreateIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, _auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        _enforce_beta_rate_limit("program_application", request, identity=f"account:{user.account_id}")
        row = program_application_service.submit_application(
            s,
            user=user,
            kind=payload.kind,
            source_name=payload.source_name,
            seats=payload.seats,
            summary=payload.summary,
            contact=payload.contact,
            now=_utcnow(),
        )
        _record_client_event(
            s,
            user=user,
            event_name="program_application_submitted",
            meta={"application_id": str(row.id), "kind": str(row.kind)},
        )
        s.commit()
        return {"ok": True, "application": program_application_service.application_payload(row)}
    except program_application_service.ProgramApplicationError as exc:
        s.rollback()
        status = 409 if exc.code == "program_application_pending" else 400
        raise HTTPException(status_code=status, detail={"code": exc.code, "message": exc.message}) from exc
    finally:
        s.close()


@app.delete("/api/client/programs/applications/{application_id}")
async def client_program_application_cancel(
    application_id: str,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, _auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        row = program_application_service.cancel_application(
            s,
            account_id=str(user.account_id or ""),
            application_id=application_id,
            now=_utcnow(),
        )
        s.commit()
        return {"ok": True, "application": program_application_service.application_payload(row)}
    except program_application_service.ProgramApplicationError as exc:
        s.rollback()
        raise HTTPException(status_code=404, detail={"code": exc.code, "message": exc.message}) from exc
    finally:
        s.close()


@app.patch("/api/client/devices/current")
async def client_device_metadata_update(
    payload: AppDeviceMetadataIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        now = _utcnow()
        account_id = str(auth_user.get("account_id") or getattr(user, "account_id", "") or "").strip()
        current_registry_id = str(auth_user.get("device_id") or "").strip()
        current_install_id = str(getattr(user, "app_install_id", "") or "").strip()
        device = None
        if account_id and current_registry_id:
            device = (
                s.query(AccountDevice)
                .filter(
                    AccountDevice.account_id == account_id,
                    AccountDevice.id == current_registry_id,
                )
                .first()
            )
        if device is None and account_id and current_install_id:
            device = (
                s.query(AccountDevice)
                .filter(
                    AccountDevice.account_id == account_id,
                    AccountDevice.install_id == current_install_id,
                )
                .first()
            )

        label = app_first_service.normalize_app_device_name(payload.device_name)
        platform = str(payload.platform or "device").strip().lower()[:32] or "device"
        os_version = str(payload.os_version or "").strip()[:64] or None
        app_version = str(payload.app_version or "").strip()[:32] or None
        user.app_device_name = label
        user.app_platform = platform
        user.app_os_version = os_version
        user.app_version = app_version
        user.app_last_seen_at = now
        if device is not None:
            device.label = label
            device.platform = platform
            device.os_version = os_version
            device.app_version = app_version
            device.last_seen_at = now
        s.commit()
        return {"ok": True}
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


@app.get("/api/client/devices")
async def client_devices(request: Request, x_telegram_init_data: str = Header(default="")) -> dict[str, Any]:
    s, user, auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        rows = []
        account_id = str(getattr(user, "account_id", "") or "").strip()
        current_registry_id = str(auth_user.get("device_id") or "").strip()
        devices = (
            s.query(AccountDevice)
            .filter(AccountDevice.account_id == account_id)
            .order_by(AccountDevice.created_at.asc(), AccountDevice.id.asc())
            .all()
            if account_id
            else []
        )
        for device in devices:
            active = str(device.state or "").strip().lower() == "active" and device.revoked_at is None
            rows.append(
                {
                    "id": str(device.install_id),
                    "registryId": str(device.id),
                    "label": _normalize_app_device_name(device.label),
                    "platform": str(device.platform or "device"),
                    "osVersion": str(device.os_version or "").strip() or None,
                    "appVersion": str(device.app_version or "").strip() or None,
                    "lastSeen": _safe_iso(device.last_seen_at),
                    "current": bool(
                        str(device.id) == current_registry_id
                        if current_registry_id
                        else str(device.install_id) == str(getattr(user, "app_install_id", "") or "")
                    ),
                    "active": active,
                    "state": str(device.state or "active"),
                    "revokedAt": _safe_iso(device.revoked_at),
                }
            )
        if not rows:
            for item in _build_app_device_rows(user):
                rows.append(
                    {
                        "id": str(item.get("id") or ""),
                        "registryId": None,
                        "label": str(item.get("name") or "Current device"),
                        "platform": str(item.get("platform") or "device"),
                        "osVersion": item.get("os_version"),
                        "appVersion": item.get("app_version"),
                        "lastSeen": item.get("last_seen_at"),
                        "current": bool(item.get("is_current")),
                        "active": bool(item.get("is_active")),
                        "state": "legacy",
                        "revokedAt": None,
                    }
                )
        return {"items": rows, "limit": _plan_device_limit(user)}
    finally:
        s.close()


@app.delete("/api/client/devices/{device_id}")
async def client_device_revoke(device_id: str, request: Request, x_telegram_init_data: str = Header(default="")) -> dict[str, Any]:
    s, user, auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        target = str(device_id or "").strip()
        if not target:
            raise HTTPException(status_code=404, detail="Device not found")
        account_id = str(auth_user.get("account_id") or getattr(user, "account_id", "") or "").strip()
        actor_session_id = str(auth_user.get("session_id") or "").strip()
        device = (
            s.query(AccountDevice)
            .filter(
                AccountDevice.account_id == account_id,
                or_(AccountDevice.id == target, AccountDevice.install_id == target),
            )
            .first()
            if account_id
            else None
        )
        if device is None:
            raise HTTPException(status_code=404, detail="Device not found")
        if not actor_session_id:
            raise HTTPException(
                status_code=409,
                detail={"code": "cannot_revoke_current_device", "message": "Current device cannot revoke itself."},
            )
        try:
            revoked = auth_session_service.revoke_device(
                s,
                account_id=account_id,
                device_id=str(device.id),
                actor_session_id=actor_session_id,
                now=_utcnow(),
            )
            s.commit()
        except auth_session_service.AuthSessionError as exc:
            s.rollback()
            raise _auth_session_http_exception(exc) from exc
        return {
            "ok": True,
            "device": {
                "id": str(revoked.install_id),
                "registryId": str(revoked.id),
                "active": False,
                "state": str(revoked.state or "revoked"),
                "revokedAt": _safe_iso(revoked.revoked_at),
            },
        }
    finally:
        s.close()


@app.get("/api/client/notifications")
async def client_notifications(
    request: Request,
    after: str = Query(default="", max_length=128),
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    del after
    s, user, _auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        runtime = await _get_user_runtime_summary(s=s, user=user, nodes=nodes_for_user)
        access_policy = _build_reconciled_access_policy(
            session=s,
            user=user,
            used_bytes=int(runtime.get("traffic_total_bytes", 0) or 0),
            source="client_notifications_runtime",
        )
        read_ids = _client_notification_read_ids(s, user=user)
        dismissed_ids = _client_notification_dismissed_ids(s, user=user)
        incidents = (
            s.query(ServiceIncident)
            .filter(ServiceIncident.status == "confirmed")
            .order_by(ServiceIncident.started_at.desc())
            .limit(10)
            .all()
        )
        live_updates = (
            s.query(LiveUpdate)
            .filter(LiveUpdate.is_active == True)
            .order_by(LiveUpdate.sort_order.asc(), LiveUpdate.id.desc())
            .limit(10)
            .all()
        )
        account_id = str(getattr(user, "account_id", "") or "").strip()
        compensation_grants = (
            s.query(EntitlementGrant)
            .filter(
                EntitlementGrant.account_id == account_id,
                EntitlementGrant.source == "incident_compensation",
                EntitlementGrant.status == "active",
            )
            .order_by(EntitlementGrant.created_at.desc())
            .limit(10)
            .all()
            if account_id
            else []
        )
        program_applications = (
            s.query(ProgramApplication)
            .filter(ProgramApplication.account_id == account_id)
            .order_by(ProgramApplication.updated_at.desc(), ProgramApplication.created_at.desc())
            .limit(10)
            .all()
            if account_id
            else []
        )
        items = _client_notification_items(
            user=user,
            access_policy=access_policy,
            read_ids=read_ids,
            incidents=incidents,
            live_updates=live_updates,
            compensation_grants=compensation_grants,
            program_applications=program_applications,
        )
        items = [item for item in items if str(item.get("id") or "") not in dismissed_ids]
        return {
            "items": items,
            "nextCursor": None,
            "unreadCount": sum(1 for item in items if not bool(item.get("read"))),
        }
    finally:
        s.close()


@app.post("/api/client/notifications/read")
async def client_notifications_read(
    payload: ClientNotificationsReadIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, _auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        ids = []
        for item in list(payload.ids or [])[:100]:
            value = str(item or "").strip()
            if value and value not in ids:
                ids.append(value[:128])
        _record_client_event(
            s,
            user=user,
            event_name="client_notification_read",
            meta={"ids": ids},
        )
        s.commit()
        return {"ok": True, "accepted": len(ids), "ignored": []}
    finally:
        s.close()


@app.post("/api/client/notifications/dismiss")
async def client_notifications_dismiss(
    payload: ClientNotificationsReadIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, _auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        ids = []
        for item in list(payload.ids or [])[:100]:
            value = str(item or "").strip()
            if value and value not in ids:
                ids.append(value[:128])
        _record_client_event(
            s,
            user=user,
            event_name="client_notification_dismissed",
            meta={"ids": ids},
        )
        s.commit()
        return {"ok": True, "accepted": len(ids), "ignored": []}
    finally:
        s.close()


@app.post("/api/client/push/register")
async def client_push_register(
    payload: ClientPushRegisterIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, _auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        platform = re.sub(r"[^a-z0-9_.:-]+", "_", str(payload.platform or "").strip().lower())[:32]
        provider = re.sub(r"[^a-z0-9_.:-]+", "_", str(payload.provider or "").strip().lower())[:32]
        token = str(payload.token or "").strip()
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        _record_client_event(
            s,
            user=user,
            event_name="client_push_register",
            session_id=str(getattr(user, "app_install_id", "") or ""),
            meta={
                "platform": platform,
                "provider": provider,
                "token_hash": token_hash,
                "token_last4": token[-4:],
            },
        )
        s.commit()
        return {"ok": True, "platform": platform, "provider": provider, "tokenHash": token_hash}
    finally:
        s.close()


@app.post("/api/client/support/assistant")
async def client_support_assistant(
    payload: ClientSupportAssistantIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, _auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        if str(payload.scope or "").strip().casefold() != "support":
            raise HTTPException(status_code=422, detail="Invalid assistant scope")
        ticket_id = int(payload.ticket_id or payload.ticketId or 0)
        if ticket_id:
            ticket = get_ticket_by_id(s, ticket_id)
            if not ticket:
                raise HTTPException(status_code=404, detail="Ticket not found")
            if int(ticket.user_tg_id) != int(user.tg_id):
                raise HTTPException(status_code=403, detail="Access denied")
        diagnostics = _admit_support_assistant_diagnostics(payload.safeDiagnostics)
        diagnostics.update(await _support_assistant_account_diagnostics(s=s, user=user))
        message = str(payload.message or "").strip()
        supplied_session_id = payload.assistant_session_id or payload.assistantSessionId
        owner_id = str(getattr(user, "account_id", "") or "").strip() or f"tg:{int(user.tg_id)}"
        result = await SUPPORT_AGENT_SERVICE.generate(
            surface="app",
            authenticated_owner_id=owner_id,
            message=message,
            assistant_session_id=supplied_session_id,
            ticket_id=ticket_id or None,
            safe_diagnostics=diagnostics,
        )
        reply = str(result.reply or "").strip() or support_fallback_reply(message)

        if ticket_id and reply:
            add_ticket_message(
                s,
                ticket_id=ticket_id,
                sender_tg_id=0,
                sender_role="assistant",
                body=reply[:2000],
            )

        _record_client_event(
            s,
            user=user,
            event_name="client_support_assistant",
            source="app",
            meta={
                "scope": "support",
                "source": result.source,
                "ticket_id": ticket_id or None,
                "should_escalate": bool(result.should_escalate),
                "diagnostics_keys": sorted(diagnostics),
            },
        )
        s.commit()
        return {
            "reply": reply,
            "assistantSessionId": result.assistant_session_id,
            "suggestedActions": list(result.suggested_actions),
            "shouldEscalate": bool(result.should_escalate),
            "source": result.source,
        }
    finally:
        s.close()


@app.get("/api/client/profile/managed")
async def client_managed_profile(
    request: Request,
    selected_node_code: str = Query(default="", max_length=32),
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
        _ensure_free_cycle_state_persisted(s, user)
        rollout_config = load_network_rollout_config(session=s)
        install_id = _client_authenticated_install_id(s, user=user, auth_user=auth_user)
        client_policy = app_first_service.build_client_policy(
            session=s,
            user=user,
            install_id=install_id,
            carrier=_request_carrier_header(x_portal_carrier),
            rollout_config=rollout_config,
        )
        transport_profile = (
            str(
                client_policy.get("transport_profile") or LEGACY_REALITY_FALLBACK
            ).strip()
            or LEGACY_REALITY_FALLBACK
        )
        is_owned_transport_lab = transport_profile in {AWG2_LAB, AWG31_LAB, HY2_LAB}
        if is_owned_transport_lab:
            install_id = _client_authenticated_install_id(
                s,
                user=user,
                auth_user=auth_user,
                require_device=True,
            )
        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        requested_node_code = str(selected_node_code or "").strip().lower()
        smart_connect = None
        if is_owned_transport_lab:
            requested_node_code = ""
        else:
            smart_connect = _smart_connect_shortlist(
                session=s,
                user=user,
                nodes=nodes_for_user,
                transport_profile=transport_profile,
                rollout_config=rollout_config,
                profile_revision=str(client_policy.get("profile_revision") or ""),
                install_id=install_id,
                preferred_node_code=requested_node_code,
            )
        sync_ok, runtime = await _managed_profile_panel_state(
            s=s,
            user=user,
            nodes=nodes_for_user,
            panel_required=not is_owned_transport_lab,
        )
        if not sync_ok:
            logger.warning(
                "managed profile panel sync returned false tg_id=%s plan=%s sub_type=%s",
                int(user.tg_id),
                str(getattr(user, "current_plan_code", "") or ""),
                str(getattr(user, "sub_type", "") or ""),
            )
        access_policy = _build_reconciled_access_policy(
            session=s,
            user=user,
            used_bytes=int(runtime.get("traffic_total_bytes", 0) or 0),
            source="managed_profile_runtime",
        )
        effective_nodes = []
        if not is_owned_transport_lab:
            effective_nodes = _effective_transport_nodes(
                nodes=nodes_for_user,
                rollout_config=rollout_config,
                transport_profile=transport_profile,
            )
            effective_by_code = _nodes_by_code(effective_nodes)
            shortlist_codes = [
                str(item.get("code") or "").strip().lower()
                for item in smart_connect.get("shortlist") or []
                if str(item.get("code") or "").strip()
            ]
            effective_nodes = [
                effective_by_code[code]
                for code in shortlist_codes
                if code in effective_by_code
            ]
            if not effective_nodes:
                raise HTTPException(status_code=503, detail="No eligible nodes")
            if requested_node_code not in set(shortlist_codes):
                requested_node_code = ""
            ranked_effective_nodes = rank_nodes_for_app(
                effective_nodes,
                policy_by_code=_node_capacity_policy_by_code(s),
                now=_utcnow(),
            )
            effective_nodes = _prefer_smart_connect_node_order(
                nodes=ranked_effective_nodes,
                preferred_node_code=requested_node_code
                or str(
                    (smart_connect.get("stickiness") or {}).get("preferred_node_code")
                    or ""
                ),
            )
            if requested_node_code:
                smart_connect["selected_node_code"] = requested_node_code
        config_format, config_payload = _managed_manifest_payload(
            user=user,
            nodes=effective_nodes,
            title="POKROV",
            transport_profile=transport_profile,
            rollout_config=rollout_config,
            session=s,
            install_id=install_id,
        )
        return {
            "version": str(rollout_config.get("version") or ""),
            "profile_revision": str(client_policy.get("profile_revision") or ""),
            "transport_profile": transport_profile,
            "transport_kind": str(client_policy.get("transport_kind") or ""),
            "engine_hint": str(client_policy.get("engine_hint") or ""),
            "config_format": config_format,
            "config_payload": config_payload,
            "fallback_order": _managed_manifest_fallback_order(transport_profile),
            "support_context": dict(client_policy.get("support_context") or {}),
            "subscription_url": build_subscription_url(
                str(getattr(user, "sub_token", "") or "")
            ),
            "smart_connect": smart_connect,
            "warp_policy": managed_warp_policy_for_user(
                s,
                user=user,
                install_id=install_id,
                rollout_config=rollout_config,
            ),
            "linked_identities": _linked_identities_payload(
                s=s, user=user, auth_user=auth_user
            ),
            "access": {
                **access_policy,
                "sub_type": str(getattr(user, "sub_type", "") or ""),
                "current_plan_code": str(getattr(user, "current_plan_code", "") or ""),
                "expiry_at": _safe_iso(getattr(user, "expiry_at", None)),
            },
            "free_caps": _free_caps_payload(user=user, access_policy=access_policy),
            "redeem_eligibility": _redeem_eligibility_payload(
                user=user, access_policy=access_policy
            ),
            "promo_slots": _promo_slots_payload_for_surface(
                s=s,
                surface="app",
                access_state=str(access_policy.get("access_state") or ""),
                user=user,
            ),
            "hidden_transport_matrix": _hidden_transport_matrix_payload(
                nodes=nodes_for_user, client_policy=client_policy
            ),
            "location_matrix": _location_matrix_payload(
                user=user, nodes=nodes_for_user, client_policy=client_policy
            ),
            "provisioning": {
                "status": "ready" if sync_ok else "pending_sync",
                "sync_ok": bool(sync_ok),
                "managed_profile_path": "/api/client/profile/managed",
            },
        }
    finally:
        s.close()


@app.get("/api/client/promo-slots")
async def client_promo_slots(
    request: Request,
    surface: str = Query(default="app", min_length=2, max_length=32),
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        _maybe_downgrade_expired_to_free(s, user)
        _ensure_free_cycle_state_persisted(s, user)
        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        runtime = await _get_user_runtime_summary(s=s, user=user, nodes=nodes_for_user)
        access_policy = _build_reconciled_access_policy(
            session=s,
            user=user,
            used_bytes=int(runtime.get("traffic_total_bytes", 0) or 0),
            source="promo_runtime",
        )
        return _promo_slots_payload_for_surface(
            s=s,
            surface=str(surface or "app").strip().lower(),
            access_state=str(access_policy.get("access_state") or ""),
            user=user,
        )
    finally:
        s.close()


def _best_rtt_by_code(samples: list[NodeLatencyPointIn], *, allowed_codes: set[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for sample in list(samples or [])[:16]:
        code = str(sample.node_code or "").strip().lower()
        if not code or (allowed_codes and code not in allowed_codes):
            continue
        value = int(sample.rtt_ms)
        current = out.get(code)
        if current is None or value < current:
            out[code] = value
    return out


@app.get("/api/client/nodes/candidates")
async def client_nodes_candidates(
    request: Request,
    profile_revision: str = Query(default="", max_length=128),
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
        _ensure_free_cycle_state_persisted(s, user)
        rollout_config = load_network_rollout_config(session=s)
        install_id = _client_authenticated_install_id(s, user=user, auth_user=auth_user)
        client_policy = app_first_service.build_client_policy(
            session=s,
            user=user,
            install_id=install_id,
            carrier=_request_carrier_header(x_portal_carrier),
            rollout_config=rollout_config,
        )
        resolved_profile = str(transport_profile or client_policy.get("transport_profile") or LEGACY_REALITY_FALLBACK).strip()
        resolved_profile = resolved_profile or LEGACY_REALITY_FALLBACK
        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        smart_connect = _smart_connect_shortlist(
            session=s,
            user=user,
            nodes=nodes_for_user,
            transport_profile=resolved_profile,
            rollout_config=rollout_config,
            profile_revision=str(profile_revision or client_policy.get("profile_revision") or ""),
            install_id=install_id,
        )
        return {
            "ok": True,
            "strategy": "capacity_rtt_sticky",
            "ttl_seconds": int(os.getenv("SMART_CONNECT_CANDIDATE_TTL_SECONDS", "120")),
            "probe_timeout_ms": int(os.getenv("SMART_CONNECT_PROBE_TIMEOUT_MS", "1500")),
            "profile_revision": str(profile_revision or client_policy.get("profile_revision") or ""),
            "transport_profile": resolved_profile,
            "shortlist": list(smart_connect.get("shortlist") or []),
            "stickiness": dict(smart_connect.get("stickiness") or {}),
            "fallback_order": list(smart_connect.get("fallback_order") or []),
            "rejected_counts": dict(smart_connect.get("rejected_counts") or {}),
        }
    finally:
        s.close()


@app.post("/api/client/nodes/select")
async def client_nodes_select(
    payload: NodeSelectIn,
    request: Request,
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
        install_id = _client_authenticated_install_id(s, user=user, auth_user=auth_user)
        if not install_id:
            raise HTTPException(status_code=400, detail="install_id is required")
        if str(os.getenv("APP_NODES_SELECT_ENDPOINT", "true")).strip().lower() in {"0", "false", "no", "off"}:
            return {
                "ok": True,
                "enabled": False,
                "selected_node_code": None,
                "reason": "feature_disabled",
                "stickiness_applied": False,
                "accepted_samples": [],
            }

        rollout_config = load_network_rollout_config(session=s)
        client_policy = app_first_service.build_client_policy(
            session=s,
            user=user,
            install_id=install_id,
            carrier=_request_carrier_header(x_portal_carrier),
            rollout_config=rollout_config,
        )
        resolved_profile = str(payload.transport_profile or client_policy.get("transport_profile") or LEGACY_REALITY_FALLBACK).strip()
        resolved_profile = resolved_profile or LEGACY_REALITY_FALLBACK
        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        effective_nodes = _effective_transport_nodes(
            nodes=nodes_for_user,
            rollout_config=rollout_config,
            transport_profile=resolved_profile,
        )
        mode = str(payload.mode or "auto").strip().lower()
        selected_node_code = str(payload.selected_node_code or "").strip().lower()
        smart_connect = _smart_connect_shortlist(
            session=s,
            user=user,
            nodes=nodes_for_user,
            transport_profile=resolved_profile,
            rollout_config=rollout_config,
            profile_revision=str(payload.profile_revision or client_policy.get("profile_revision") or ""),
            install_id=install_id,
            preferred_node_code=selected_node_code if mode == "manual" else "",
        )
        shortlist_codes = {
            str(item.get("code") or "").strip().lower()
            for item in smart_connect.get("shortlist") or []
            if str(item.get("code") or "").strip()
        }
        effective_by_code = _nodes_by_code(effective_nodes)
        if not shortlist_codes:
            raise HTTPException(status_code=503, detail="No eligible nodes")
        previous_node_code = str(payload.previous_node_code or "").strip().lower()
        policy_by_code = _node_capacity_policy_by_code(s)
        rtt_by_code = _best_rtt_by_code(payload.samples, allowed_codes=shortlist_codes)
        accepted_samples = [
            {"node_code": code, "rtt_ms": int(value)}
            for code, value in sorted(rtt_by_code.items())
        ]

        candidate_codes = shortlist_codes
        if mode == "manual":
            if selected_node_code not in candidate_codes:
                raise HTTPException(status_code=400, detail="selected node is not eligible")
            winner = selected_node_code
            stickiness_applied = False
            reason = "manual_preference"
        else:
            candidate_nodes = [effective_by_code[code] for code in candidate_codes if code in effective_by_code]
            ranked = rank_nodes_for_app(
                candidate_nodes,
                client_rtt_by_code=rtt_by_code,
                policy_by_code=policy_by_code,
                now=_utcnow(),
            )
            if not ranked:
                raise HTTPException(status_code=503, detail="No eligible nodes")
            winner = str(getattr(ranked[0], "code", "") or "").strip().lower()
            stickiness_applied = False
            reason = "best_capacity_rtt"
            if previous_node_code and previous_node_code in candidate_codes and previous_node_code in effective_by_code:
                previous_node = effective_by_code[previous_node_code]
                winner_node = effective_by_code.get(winner)
                prev_reject = node_hard_reject_reason(previous_node, policy=policy_by_code.get(previous_node_code), now=_utcnow())
                if not prev_reject and winner_node is not None:
                    prev_score = node_selection_score(
                        previous_node,
                        policy=policy_by_code.get(previous_node_code),
                        client_rtt_ms=rtt_by_code.get(previous_node_code),
                    )
                    winner_score = node_selection_score(
                        winner_node,
                        policy=policy_by_code.get(winner),
                        client_rtt_ms=rtt_by_code.get(winner),
                    )
                    if prev_score > 0:
                        improvement_percent = max(0.0, (prev_score - winner_score) / prev_score * 100.0)
                        if improvement_percent < float(SMART_CONNECT_STICKINESS_THRESHOLD_PERCENT):
                            winner = previous_node_code
                            stickiness_applied = True
                            reason = "sticky_previous"

        event_meta = {
            "install_id": install_id,
            "mode": mode,
            "profile_revision": str(payload.profile_revision or client_policy.get("profile_revision") or ""),
            "transport_profile": resolved_profile,
            "selected_node_code": winner,
            "requested_node_code": selected_node_code or None,
            "previous_node_code": previous_node_code or None,
            "stickiness_applied": bool(stickiness_applied),
            "reason": reason,
            "samples": accepted_samples,
            "carrier": _request_carrier_header(x_portal_carrier) or None,
            "platform": str(getattr(user, "app_platform", "") or "").strip() or None,
        }
        _record_client_event(
            s,
            user=user,
            event_name="smart_connect_node_select",
            source="app",
            session_id=install_id,
            meta=event_meta,
        )
        s.commit()
        managed_profile_url = "/api/client/profile/managed"
        if winner:
            managed_profile_url = f"{managed_profile_url}?{urlencode({'selected_node_code': winner})}"
        return {
            "ok": True,
            "selected_node_code": winner,
            "previous_node_code": previous_node_code or None,
            "stickiness_applied": bool(stickiness_applied),
            "reason": reason,
            "requires_profile_refresh": bool(winner and winner != previous_node_code),
            "managed_profile_url": managed_profile_url,
            "profile_revision": str(payload.profile_revision or client_policy.get("profile_revision") or ""),
            "transport_profile": resolved_profile,
            "accepted_samples": len(accepted_samples),
        }
    finally:
        s.close()


@app.post("/api/client/runtime/stats")
async def client_runtime_stats(
    payload: ClientRuntimeStatsIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        session_id, identity_meta = _client_telemetry_identity(
            s,
            user=user,
            auth_user=auth_user,
            request=request,
        )
        runtime_phase = str(payload.runtime_phase or "").strip().lower()
        error_code = str(payload.error_code or "").strip().lower()
        if runtime_phase and not re.fullmatch(r"[a-z0-9_.-]{1,32}", runtime_phase):
            raise HTTPException(status_code=422, detail="Invalid runtime phase")
        if error_code and not re.fullmatch(r"[a-z0-9_.-]{1,64}", error_code):
            raise HTTPException(status_code=422, detail="Invalid error code")
        event_name = "client_runtime_stats"
        if bool(payload.connected):
            event_name = "connected_ok"
        elif error_code:
            event_name = error_code
        elif runtime_phase == "connect_requested":
            event_name = "clicked_connect"
        elif runtime_phase in {
            "app_opened",
            "update_available",
            "update_download_started",
            "update_installer_opened",
        }:
            event_name = runtime_phase
        _record_client_event(
            s,
            user=user,
            event_name=event_name,
            source="app",
            session_id=session_id or "unavailable",
            meta={
                **identity_meta,
                "profile_revision": str(payload.profile_revision or "") or None,
                "selected_node_code": str(payload.selected_node_code or "").strip().lower() or None,
                "runtime_phase": runtime_phase or None,
                "connected": payload.connected,
                "uptime_seconds": payload.uptime_seconds,
                "rtt_ms": payload.rtt_ms,
                "rx_mbps": payload.rx_mbps,
                "tx_mbps": payload.tx_mbps,
                "error_code": error_code or None,
                "route_mode": str(payload.route_mode or "").strip().lower() or None,
                "duration_ms": payload.duration_ms,
                "attempt_number": payload.attempt_number,
                "retryable": payload.retryable,
                "network_class": str(payload.network_class or "").strip().lower() or None,
            },
        )
        if bool(payload.connected):
            account_id = str(auth_user.get("account_id") or getattr(user, "account_id", "") or "").strip()
            if account_id:
                account_experience_service.record_first_connection_reported(
                    s,
                    account_id=account_id,
                )
        s.commit()
        return {"ok": True}
    finally:
        s.close()


@app.post("/api/account/experience/onboarding")
async def account_onboarding_status(
    payload: AccountOnboardingStatusIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        account_id = str(auth_user.get("account_id") or getattr(user, "account_id", "") or "").strip()
        if not account_id:
            raise HTTPException(status_code=409, detail="Account foundation is not ready")
        try:
            account_experience_service.set_onboarding_status(
                s,
                account_id=account_id,
                status=payload.status,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        experience = account_experience_service.build_experience_snapshot(
            s,
            account_id=account_id,
            app_identity_known=bool(str(getattr(user, "app_install_id", "") or "").strip()),
        )
        s.commit()
        return {"ok": True, "experience": experience}
    finally:
        s.close()


def _node_metrics_secret(node: Node | None = None) -> str:
    return (
        str(os.getenv("NODE_AGENT_METRICS_SECRET") or "").strip()
        or str(getattr(node, "observer_push_secret", "") or "").strip()
    )


async def _require_node_metrics_signature(request: Request, *, node: Node | None) -> None:
    secret = _node_metrics_secret(node)
    if not secret:
        raise HTTPException(status_code=503, detail="node metrics secret is not configured")
    timestamp = str(request.headers.get("X-POKROV-Timestamp") or "").strip()
    signature = str(request.headers.get("X-POKROV-Signature") or "").strip().lower()
    if not timestamp or not signature:
        raise HTTPException(status_code=401, detail="missing node metrics signature")
    try:
        ts_value = int(timestamp)
    except Exception:
        raise HTTPException(status_code=401, detail="invalid node metrics timestamp")
    if abs(int(time.time()) - ts_value) > int(os.getenv("NODE_AGENT_METRICS_MAX_SKEW_SECONDS", "120")):
        raise HTTPException(status_code=401, detail="stale node metrics signature")
    body = await request.body()
    messages = [
        timestamp.encode("utf-8") + b"." + body,
        body + b"." + timestamp.encode("utf-8"),
        body,
    ]
    valid = any(
        hmac.compare_digest(
            hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest().lower(),
            signature,
        )
        for message in messages
    )
    if not valid:
        raise HTTPException(status_code=401, detail="invalid node metrics signature")


def _apply_node_metric_payload(node: Node, payload: InternalNodeMetricsIn, *, policy: Any | None = None) -> dict[str, Any]:
    sampled_at = payload.sampled_at or _utcnow()
    provisioned = int(payload.provisioned_clients_count if payload.provisioned_clients_count is not None else getattr(node, "provisioned_clients_count", 0) or 0)
    online_hint = int(payload.online_connections_hint if payload.online_connections_hint is not None else getattr(node, "online_connections_hint", 0) or 0)
    tx_1m = payload.network_tx_mbps_1m
    tx_5m = payload.network_tx_mbps_5m
    rx_1m = payload.network_rx_mbps_1m
    rx_5m = payload.network_rx_mbps_5m
    total_mbps = payload.network_total_mbps
    if total_mbps is None:
        total_mbps = float((tx_1m or tx_5m or 0.0) + (rx_1m or rx_5m or 0.0))

    node.provisioned_clients_count = provisioned
    node.active_clients = provisioned
    node.online_connections_hint = online_hint
    node.network_tx_mbps_1m = tx_1m
    node.network_tx_mbps_5m = tx_5m
    node.network_rx_mbps_1m = rx_1m
    node.network_rx_mbps_5m = rx_5m
    node.network_total_mbps = total_mbps
    if tx_1m is not None:
        node.network_tx_mbps = tx_1m
    if rx_1m is not None:
        node.network_rx_mbps = rx_1m
    if payload.cpu_percent is not None:
        node.cpu_percent = payload.cpu_percent
    if payload.memory_used_mb is not None:
        node.memory_used_mb = payload.memory_used_mb
    if payload.memory_total_mb is not None:
        node.memory_total_mb = payload.memory_total_mb
    node.tcp_retrans_percent = payload.tcp_retrans_percent
    node.packet_loss_percent = payload.packet_loss_percent
    node.dataplane_ok = payload.dataplane_ok
    node.dataplane_rtt_ms = payload.dataplane_rtt_ms
    node.last_health_at = sampled_at
    node.last_ok_at = sampled_at if payload.dataplane_ok is not False else getattr(node, "last_ok_at", None)
    node.is_healthy = payload.dataplane_ok is not False
    capacity = node_capacity_status(node, policy=policy, now=sampled_at)
    node.capacity_score = float(capacity.get("score") or 0.0)
    node.capacity_state = str(capacity.get("state") or "unknown")
    node.capacity_reject_reason = str(capacity.get("reject_reason") or "") or None
    return capacity


def _int_metric(value: Any, default: int = 0) -> int:
    try:
        return max(0, int(value))
    except Exception:
        return int(default)


def _float_metric(value: Any, default: float = 0.0) -> float:
    try:
        return max(0.0, float(value))
    except Exception:
        return float(default)


def _key_pressure_state(
    *,
    traffic_gb_24h: float,
    peak_tx_mbps: float,
    distinct_source_ips_24h: int,
    distinct_asns_24h: int,
    distinct_countries_24h: int,
    node_count_24h: int,
) -> tuple[str, float, list[str], bool]:
    score = 0.0
    reasons: list[str] = []

    if peak_tx_mbps >= 120.0:
        score += 45.0
        reasons.append("peak_tx_mbps>=120")
    elif peak_tx_mbps >= 60.0:
        score += 25.0
        reasons.append("peak_tx_mbps>=60")

    if traffic_gb_24h >= 300.0:
        score += 45.0
        reasons.append("traffic_gb_24h>=300")
    elif traffic_gb_24h >= 100.0:
        score += 28.0
        reasons.append("traffic_gb_24h>=100")
    elif traffic_gb_24h >= 30.0:
        score += 12.0
        reasons.append("traffic_gb_24h>=30")

    if distinct_source_ips_24h >= 20:
        score += 30.0
        reasons.append("distinct_source_ips_24h>=20")
    elif distinct_source_ips_24h >= 8:
        score += 15.0
        reasons.append("distinct_source_ips_24h>=8")

    if distinct_asns_24h >= 5:
        score += 25.0
        reasons.append("distinct_asns_24h>=5")
    elif distinct_asns_24h >= 3:
        score += 12.0
        reasons.append("distinct_asns_24h>=3")

    if distinct_countries_24h >= 4:
        score += 25.0
        reasons.append("distinct_countries_24h>=4")
    elif distinct_countries_24h >= 2:
        score += 10.0
        reasons.append("distinct_countries_24h>=2")

    if node_count_24h >= 4:
        score += 20.0
        reasons.append("node_count_24h>=4")
    elif node_count_24h >= 2:
        score += 8.0
        reasons.append("node_count_24h>=2")

    traffic_pressure = peak_tx_mbps >= 20.0 or traffic_gb_24h >= 20.0
    if not traffic_pressure and score > 35.0:
        score = 35.0
        reasons.append("churn_without_traffic_pressure_capped")

    if score >= 100.0:
        state = "fair_use" if KEY_PRESSURE_FAIR_USE_ROUTING else "suspected_shared"
    elif score >= 75.0:
        state = "suspected_shared"
    elif score >= 45.0:
        state = "heavy"
    elif score >= 20.0:
        state = "warm"
    else:
        state = "ok"
    return state, round(score, 3), reasons, state in {"heavy", "suspected_shared", "fair_use"}


def _upsert_key_pressure_state(
    s,
    *,
    key_id: int | None,
    tg_id: int | None,
    node_code: str,
    panel_email: str,
    item: dict[str, Any],
    total_bytes: int,
    source_ip_hashes: list[Any],
) -> None:
    if not KEY_PRESSURE_SCORING or not key_id:
        return
    ips_24h = _int_metric(item.get("distinct_source_ips_24h"), len(source_ip_hashes))
    ips_1h = _int_metric(item.get("distinct_source_ips_1h"), min(ips_24h, len(source_ip_hashes)))
    asns_raw = item.get("source_asns") if isinstance(item.get("source_asns"), list) else []
    countries_raw = item.get("source_countries") if isinstance(item.get("source_countries"), list) else []
    asns_24h = _int_metric(item.get("distinct_asns_24h"), len({str(v) for v in asns_raw if str(v).strip()}))
    countries_24h = _int_metric(
        item.get("distinct_countries_24h"),
        len({str(v).upper() for v in countries_raw if str(v).strip()}),
    )
    node_count_24h = _int_metric(item.get("node_count_24h"), 1)
    traffic_gb_24h = _float_metric(item.get("traffic_gb_24h"), float(total_bytes) / 1024.0 / 1024.0 / 1024.0)
    peak_tx_mbps = _float_metric(item.get("peak_tx_mbps"), 0.0)
    state, score, reasons, manual_review = _key_pressure_state(
        traffic_gb_24h=traffic_gb_24h,
        peak_tx_mbps=peak_tx_mbps,
        distinct_source_ips_24h=ips_24h,
        distinct_asns_24h=asns_24h,
        distinct_countries_24h=countries_24h,
        node_count_24h=node_count_24h,
    )
    row = s.get(KeyPressureState, int(key_id))
    if row is None:
        row = KeyPressureState(key_id=int(key_id))
        s.add(row)
    row.tg_id = tg_id or None
    row.node_code = str(node_code or "")[:32] or None
    row.panel_email = str(panel_email or "")[:100] or None
    row.state = state
    row.pressure_score = float(score)
    row.reasons_json = json.dumps(reasons, ensure_ascii=False, separators=(",", ":"))[:2000]
    row.distinct_source_ips_1h = int(ips_1h)
    row.distinct_source_ips_24h = int(ips_24h)
    row.node_count_24h = int(node_count_24h)
    row.traffic_gb_24h = float(round(traffic_gb_24h, 6))
    row.manual_review_required = bool(manual_review)
    row.updated_at = _utcnow()


@app.post("/api/internal/nodes/{node_code}/metrics")
async def internal_node_metrics(
    node_code: str,
    payload: InternalNodeMetricsIn,
    request: Request,
) -> dict[str, Any]:
    wanted = str(node_code or "").strip().lower()
    if not wanted:
        raise HTTPException(status_code=400, detail="node_code is required")
    s = SessionLocal()
    try:
        node = s.query(Node).filter(func.lower(Node.code) == wanted).first()
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        await _require_node_metrics_signature(request, node=node)
        policy = s.query(NodeCapacityPolicy).filter(func.lower(NodeCapacityPolicy.node_code) == wanted).first()
        capacity = _apply_node_metric_payload(node, payload, policy=policy)
        safe_meta = sanitize_runtime_metric_meta(payload.meta)
        sampled_at = payload.sampled_at or _utcnow()
        metric = NodeRuntimeMetric(
            node_code=wanted,
            sampled_at=sampled_at,
            source=str(payload.source or "node_agent").strip()[:64] or "node_agent",
            batch_id=str(payload.batch_id or "").strip()[:128] or None,
            provisioned_clients_count=int(getattr(node, "provisioned_clients_count", 0) or 0),
            online_connections_hint=int(getattr(node, "online_connections_hint", 0) or 0),
            network_rx_mbps_1m=payload.network_rx_mbps_1m,
            network_tx_mbps_1m=payload.network_tx_mbps_1m,
            network_rx_mbps_5m=payload.network_rx_mbps_5m,
            network_tx_mbps_5m=payload.network_tx_mbps_5m,
            network_total_mbps=getattr(node, "network_total_mbps", None),
            cpu_percent=getattr(node, "cpu_percent", None),
            memory_used_mb=getattr(node, "memory_used_mb", None),
            memory_total_mb=getattr(node, "memory_total_mb", None),
            tcp_retrans_percent=payload.tcp_retrans_percent,
            packet_loss_percent=payload.packet_loss_percent,
            dataplane_ok=payload.dataplane_ok,
            dataplane_rtt_ms=payload.dataplane_rtt_ms,
            capacity_score=float(capacity.get("score") or 0.0),
            capacity_state=str(capacity.get("state") or "unknown"),
            reject_reason=str(capacity.get("reject_reason") or "") or None,
            meta_json=json.dumps(safe_meta, ensure_ascii=False, separators=(",", ":")),
        )
        s.add(metric)
        s.commit()
        return {"ok": True, "node_code": wanted, "capacity": capacity}
    finally:
        s.close()


@app.post("/api/internal/nodes/{node_code}/xray-stats")
async def internal_node_xray_stats(node_code: str, request: Request) -> dict[str, Any]:
    wanted = str(node_code or "").strip().lower()
    if not wanted:
        raise HTTPException(status_code=400, detail="node_code is required")
    s = SessionLocal()
    try:
        node = s.query(Node).filter(func.lower(Node.code) == wanted).first()
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        await _require_node_metrics_signature(request, node=node)
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        rows = list(payload.get("keys") or payload.get("clients") or [])
        if not isinstance(rows, list):
            rows = []
        bucket_at = _utcnow().replace(second=0, microsecond=0)
        accepted = 0
        for item in rows[:500]:
            if not isinstance(item, dict):
                continue
            panel_email = str(item.get("panel_email") or item.get("email") or "").strip()
            key_uuid = str(item.get("key_uuid") or item.get("uuid") or "").strip()
            key_row = None
            if panel_email:
                key_row = (
                    s.query(AccessKey)
                    .filter(func.lower(AccessKey.node_code) == wanted)
                    .filter(func.lower(AccessKey.panel_email) == panel_email.lower())
                    .first()
                )
            if not key_row and key_uuid:
                key_row = s.query(AccessKey).filter(AccessKey.key_uuid == key_uuid).first()
            tg_id = int(getattr(key_row, "tg_id", 0) or int(item.get("tg_id") or 0))
            upload_bytes = int(item.get("upload_bytes") or item.get("up") or 0)
            download_bytes = int(item.get("download_bytes") or item.get("down") or 0)
            total_bytes = int(item.get("total_bytes") or upload_bytes + download_bytes)
            key_id = int(getattr(key_row, "id", 0) or 0) or None
            window_seconds = int(item.get("window_seconds") or payload.get("window_seconds") or 300)
            rollup = None
            if key_id:
                rollup = (
                    s.query(KeyUsageRollup)
                    .filter(KeyUsageRollup.key_id == key_id)
                    .filter(KeyUsageRollup.node_code == wanted)
                    .filter(KeyUsageRollup.window_bucket_at == bucket_at)
                    .filter(KeyUsageRollup.window_seconds == window_seconds)
                    .first()
                )
            if rollup is None:
                rollup = KeyUsageRollup(
                    key_id=key_id,
                    node_code=wanted,
                    window_bucket_at=bucket_at,
                    window_seconds=window_seconds,
                )
                s.add(rollup)
            rollup.tg_id = tg_id or None
            rollup.panel_email = panel_email or None
            rollup.upload_bytes = max(0, upload_bytes)
            rollup.download_bytes = max(0, download_bytes)
            rollup.total_bytes = max(0, total_bytes)
            rollup.peak_tx_mbps = float(item.get("peak_tx_mbps")) if item.get("peak_tx_mbps") is not None else None
            rollup.observations = int(item.get("observations") or 1)
            rollup.source = str(payload.get("source") or "xray_stats").strip()[:64] or "xray_stats"
            source_ip_hashes = item.get("source_ip_hashes") or item.get("source_ips") or []
            if isinstance(source_ip_hashes, list):
                for raw_hash in source_ip_hashes[:50]:
                    source_hash = hashlib.sha256(str(raw_hash).encode("utf-8")).hexdigest() if len(str(raw_hash)) != 64 else str(raw_hash)
                    observation = None
                    if key_id:
                        observation = (
                            s.query(KeySourceObservation)
                            .filter(KeySourceObservation.key_id == key_id)
                            .filter(KeySourceObservation.node_code == wanted)
                            .filter(KeySourceObservation.source_ip_hash == source_hash[:64])
                            .filter(KeySourceObservation.window_bucket_at == bucket_at)
                            .first()
                        )
                    if observation is None:
                        observation = KeySourceObservation(
                            key_id=key_id,
                            node_code=wanted,
                            source_ip_hash=source_hash[:64],
                            window_bucket_at=bucket_at,
                            first_seen_at=bucket_at,
                            hit_count=0,
                        )
                        s.add(observation)
                    observation.tg_id = tg_id or None
                    observation.panel_email = panel_email or None
                    observation.source_asn = str(item.get("source_asn") or "")[:32] or None
                    observation.source_country = str(item.get("source_country") or "")[:8] or None
                    observation.last_seen_at = _utcnow()
                    observation.hit_count = int(observation.hit_count or 0) + 1
            _upsert_key_pressure_state(
                s,
                key_id=key_id,
                tg_id=tg_id or None,
                node_code=wanted,
                panel_email=panel_email,
                item=item,
                total_bytes=max(0, total_bytes),
                source_ip_hashes=source_ip_hashes if isinstance(source_ip_hashes, list) else [],
            )
            if tg_id:
                observed_user = s.query(User).filter(User.tg_id == int(tg_id)).first()
                if observed_user is not None:
                    reconcile_free_profile_usage(
                        s,
                        user=observed_user,
                        used_bytes=max(0, total_bytes),
                        source="node_xray_stats",
                        now=_utcnow(),
                    )
            accepted += 1
        s.commit()
        return {"ok": True, "node_code": wanted, "accepted": accepted}
    finally:
        s.close()


@app.post("/api/client/nodes/latency-samples")
async def client_nodes_latency_samples(
    payload: NodeLatencySamplesIn,
    request: Request,
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
        install_id = _client_authenticated_install_id(s, user=user, auth_user=auth_user)
        if not install_id:
            raise HTTPException(status_code=400, detail="install_id is required")

        rollout_config = load_network_rollout_config(session=s)
        client_policy = app_first_service.build_client_policy(
            session=s,
            user=user,
            install_id=install_id or None,
            carrier=_request_carrier_header(x_portal_carrier),
            rollout_config=rollout_config,
        )
        transport_profile = (
            str(payload.transport_profile or client_policy.get("transport_profile") or LEGACY_REALITY_FALLBACK).strip()
            or LEGACY_REALITY_FALLBACK
        )
        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        smart_connect = _smart_connect_shortlist(
            session=s,
            user=user,
            nodes=nodes_for_user,
            transport_profile=transport_profile,
            rollout_config=rollout_config,
            profile_revision=str(payload.profile_revision or client_policy.get("profile_revision") or ""),
            install_id=install_id,
        )
        allowed_codes = {
            str(item.get("code") or "").strip().lower()
            for item in smart_connect.get("shortlist") or []
            if str(item.get("code") or "").strip()
        }
        accepted_samples: list[dict[str, int | str]] = []
        for sample in list(payload.samples or [])[:10]:
            code = str(sample.node_code or "").strip().lower()
            if not code or (allowed_codes and code not in allowed_codes):
                continue
            accepted_samples.append({"node_code": code, "rtt_ms": int(sample.rtt_ms)})

        selected_node_code = str(payload.selected_node_code or "").strip().lower()
        if selected_node_code and allowed_codes and selected_node_code not in allowed_codes:
            selected_node_code = ""
        previous_node_code = str(payload.previous_node_code or "").strip().lower()
        if previous_node_code and allowed_codes and previous_node_code not in allowed_codes:
            previous_node_code = ""

        event_meta = {
            "install_id": install_id,
            "profile_revision": str(payload.profile_revision or client_policy.get("profile_revision") or ""),
            "transport_profile": transport_profile,
            "selected_node_code": selected_node_code or None,
            "previous_node_code": previous_node_code or None,
            "stickiness_applied": bool(payload.stickiness_applied),
            "carrier": _request_carrier_header(x_portal_carrier) or None,
            "platform": str(getattr(user, "app_platform", "") or "").strip() or None,
            "samples": accepted_samples,
        }
        s.add(
            Event(
                tg_id=int(user.tg_id),
                event_name=SMART_CONNECT_LATENCY_EVENT_NAME,
                source="app",
                session_id=install_id,
                meta_json=json.dumps(event_meta, ensure_ascii=False),
                created_at=_utcnow(),
            )
        )
        s.commit()
        return {
            "ok": True,
            "accepted_samples": len(accepted_samples),
            "preferred_node_code": selected_node_code or None,
        }
    finally:
        s.close()


def _client_warp_context(request: Request, x_telegram_init_data: str) -> tuple[Any, User, str, dict[str, Any]]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    user = s.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        s.close()
        raise HTTPException(status_code=404, detail="User not found")
    install_id = _client_authenticated_install_id(s, user=user, auth_user=auth_user)
    rollout_config = load_network_rollout_config(session=s)
    policy = public_warp_policy_for_user(
        s,
        user=user,
        install_id=install_id,
        rollout_config=rollout_config,
    )
    return s, user, install_id, policy


def _warp_env_int(
    name: str,
    *,
    default: int,
    minimum: int = 0,
    maximum: int = 1_000_000,
) -> int:
    try:
        value = int(str(os.getenv(name) or "").strip() or default)
    except Exception:
        value = default
    return max(minimum, min(maximum, value))


def _warp_event_count(
    session,
    *,
    user: User,
    install_id: str | None,
    event_name: str,
    window_seconds: int,
) -> int:
    since = _utcnow() - timedelta(seconds=max(1, int(window_seconds)))
    query = (
        session.query(func.count(WarpEvent.id))
        .filter(WarpEvent.tg_id == int(user.tg_id))
        .filter(WarpEvent.event_name == str(event_name))
        .filter(WarpEvent.created_at >= since)
    )
    clean_install = str(install_id or "").strip()
    if clean_install:
        query = query.filter(WarpEvent.install_id == clean_install)
    return int(query.scalar() or 0)


def _warp_rate_limit_detail(*, code: str, limit: int, window_seconds: int) -> dict[str, Any]:
    return {
        "code": code,
        "limit": int(limit),
        "window_seconds": int(window_seconds),
        "retry_after_seconds": int(window_seconds),
        "message": "WARP action is rate limited. Try again later.",
    }


def _warp_material_provision_limit() -> tuple[int, int]:
    return (
        _warp_env_int(
            "WARP_MATERIAL_PROVISION_LIMIT_PER_HOUR",
            default=6,
            minimum=0,
            maximum=1000,
        ),
        3600,
    )


def _warp_rotation_limit() -> tuple[int, int]:
    return (
        _warp_env_int(
            "WARP_ROTATION_LIMIT_PER_HOUR",
            default=3,
            minimum=0,
            maximum=1000,
        ),
        3600,
    )


def _warp_not_ready_detail(status: dict[str, Any]) -> dict[str, Any]:
    return {
        "code": "warp_not_runtime_ready",
        "state": str(status.get("state") or "not_ready"),
        "policy_state": str(status.get("policy_state") or ""),
        "message": "Extended protection is not ready for this device yet.",
    }


@app.get("/api/client/warp/status")
async def client_warp_status(request: Request, x_telegram_init_data: str = Header(default="")) -> dict[str, Any]:
    s, user, install_id, policy = _client_warp_context(request, x_telegram_init_data)
    try:
        return build_warp_status(s, user=user, install_id=install_id, policy=policy)
    finally:
        s.close()


@app.post("/api/client/warp/consent")
async def client_warp_consent(
    payload: ClientWarpConsentIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, install_id, policy = _client_warp_context(request, x_telegram_init_data)
    try:
        status = build_warp_status(s, user=user, install_id=install_id, policy=policy)
        if not bool(status.get("runtime_ready")):
            raise HTTPException(status_code=409, detail=_warp_not_ready_detail(status))
        if not payload.consent:
            record_warp_event(
                s,
                user=user,
                install_id=install_id,
                policy=policy,
                event_name="revoke",
                state="revoked",
                reason_code=payload.reason_code or "consent_declined",
                consented=False,
                meta={"source": "app_consent", "action": "decline"},
            )
        else:
            record_warp_event(
                s,
                user=user,
                install_id=install_id,
                policy=policy,
                event_name="consent",
                state="consented",
                reason_code=payload.reason_code or "user_consented",
                consented=True,
                meta={"source": "app_consent", "action": "accept"},
            )
        s.commit()
        return build_warp_status(s, user=user, install_id=install_id, policy=policy)
    finally:
        s.close()


@app.post("/api/client/warp/revoke")
async def client_warp_revoke(
    payload: ClientWarpActionIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, install_id, policy = _client_warp_context(request, x_telegram_init_data)
    try:
        status = build_warp_status(s, user=user, install_id=install_id, policy=policy)
        record_warp_event(
            s,
            user=user,
            install_id=install_id,
            policy=policy,
            event_name="revoke",
            state="revoked",
            reason_code=payload.reason_code or "user_disabled",
            consented=False,
            meta={"source": "app_action", "previous_state": status.get("state")},
        )
        revoke_warp_material(s, user=user, install_id=install_id)
        s.commit()
        return build_warp_status(s, user=user, install_id=install_id, policy=policy)
    finally:
        s.close()


@app.post("/api/client/warp/rotate")
async def client_warp_rotate(
    payload: ClientWarpActionIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, install_id, policy = _client_warp_context(request, x_telegram_init_data)
    try:
        status = build_warp_status(s, user=user, install_id=install_id, policy=policy)
        if not bool(status.get("runtime_ready")):
            raise HTTPException(status_code=409, detail=_warp_not_ready_detail(status))
        limit, window_seconds = _warp_rotation_limit()
        if limit and _warp_event_count(
            s,
            user=user,
            install_id=install_id,
            event_name="rotate_requested",
            window_seconds=window_seconds,
        ) >= limit:
            record_warp_event(
                s,
                user=user,
                install_id=install_id,
                policy=policy,
                event_name="rotate_rate_limited",
                state="rate_limited",
                reason_code=payload.reason_code or "rotation_limit",
                consented=bool(status.get("consented")),
                meta={"source": "app_action", "previous_state": status.get("state")},
            )
            s.commit()
            raise HTTPException(
                status_code=429,
                detail=_warp_rate_limit_detail(
                    code="warp_rotation_rate_limited",
                    limit=limit,
                    window_seconds=window_seconds,
                ),
            )
        record_warp_event(
            s,
            user=user,
            install_id=install_id,
            policy=policy,
            event_name="rotate_requested",
            state="rotation_requested",
            reason_code=payload.reason_code or "user_requested",
            consented=bool(status.get("consented")),
            meta={"source": "app_action", "previous_state": status.get("state")},
        )
        mark_warp_material_rotation_requested(s, user=user, install_id=install_id)
        s.commit()
        return build_warp_status(s, user=user, install_id=install_id, policy=policy)
    finally:
        s.close()


@app.post("/api/client/warp/events")
async def client_warp_events(
    payload: ClientWarpRuntimeEventIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    s, user, install_id, policy = _client_warp_context(request, x_telegram_init_data)
    try:
        status = build_warp_status(s, user=user, install_id=install_id, policy=policy)
        event_meta = dict(payload.meta or {})
        if payload.message:
            event_meta["message"] = payload.message
        record_warp_event(
            s,
            user=user,
            install_id=install_id,
            policy=policy,
            event_name=payload.event_name,
            state=payload.state or str(status.get("state") or "not_ready"),
            reason_code=payload.reason_code,
            consented=bool(status.get("consented")),
            meta=event_meta,
        )
        s.commit()
        return {"ok": True, **build_warp_status(s, user=user, install_id=install_id, policy=policy)}
    finally:
        s.close()


@app.post("/api/client/telegram/link")
async def client_telegram_link_start(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    s, user, auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        linked_id = _linked_telegram_id(user)
        telegram_native = bool(
            not _is_app_or_email_account(user)
            and int(getattr(user, "tg_id", 0) or 0) > 0
        )
        linked_username = str(
            getattr(
                user,
                "username" if telegram_native else "linked_telegram_username",
                "",
            )
            or ""
        ).strip()
        start_code = ""
        if not linked_id and not telegram_native:
            start_code = app_first_service.create_app_telegram_start_code(
                s,
                account_tg_id=int(user.tg_id),
                now=_utcnow(),
            )
        session_id, identity_meta = _client_telemetry_identity(
            s,
            user=user,
            auth_user=auth_user,
            request=request,
        )
        _record_client_event(
            s,
            user=user,
            event_name="app_telegram_link_requested",
            source="app",
            session_id=session_id or "unavailable",
            meta={**identity_meta, "linked": bool(linked_id or telegram_native)},
        )
        s.commit()
        bot_username = (BOT_USERNAME or "pokrov_vpnbot").lstrip("@")
        channel_username = (PUBLIC_CHANNEL or "").lstrip("@").strip()
        return {
            "ok": True,
            "linked": bool(linked_id or telegram_native),
            "linked_telegram_id": linked_id or (int(user.tg_id) if telegram_native else None),
            "linked_telegram_username": linked_username or None,
            "start_code": start_code,
            "bot_url": f"https://t.me/{bot_username}?start={start_code}" if start_code else f"https://t.me/{bot_username}",
            "channel_url": f"https://t.me/{channel_username}" if channel_username else None,
        }
    finally:
        s.close()


@app.post("/api/client/telegram/link/events")
async def client_telegram_link_event(
    payload: ClientTelegramLinkEventIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, bool]:
    allowed = {"handoff_opened", "handoff_open_failed", "verify_requested"}
    event_name = str(payload.event_name or "").strip().lower()
    if event_name not in allowed:
        raise HTTPException(status_code=422, detail="Unsupported Telegram link event")
    s, user, auth_user = _client_user_session(request, x_telegram_init_data)
    try:
        session_id, identity_meta = _client_telemetry_identity(
            s,
            user=user,
            auth_user=auth_user,
            request=request,
        )
        _enforce_beta_rate_limit(
            "client_diagnostic_event",
            request,
            identity=session_id or str(user.tg_id),
        )
        _record_client_event(
            s,
            user=user,
            event_name=f"app_telegram_link_{event_name}",
            source="app",
            session_id=session_id or "unavailable",
            meta=identity_meta,
        )
        s.commit()
        return {"ok": True}
    finally:
        s.close()


def _normalize_lavatop_payment_method(raw: str | None) -> tuple[str, str, str]:
    method = str(raw or "").strip().lower()
    if not method:
        return "", "", ""
    aliases = {
        "sbp": "sbp",
        "сбп": "sbp",
        "pay2me_sbp": "sbp",
        "card": "card",
        "cards": "card",
        "bank_card": "card",
        "bankcard": "card",
        "mir": "card",
        "карта": "card",
        "карты": "card",
    }
    method = aliases.get(method, method)
    capabilities = {
        str(item.get("code") or ""): bool(item.get("available"))
        for item in payment_method_capabilities("lavatop")
    }
    if method in capabilities and not capabilities[method]:
        raise HTTPException(
            status_code=409, detail="Payment method is temporarily unavailable"
        )
    if method == "sbp":
        return "sbp", "PAY2ME", "SBP"
    if method == "card":
        return "card", "SMART_GLOCAL", "CARD"
    raise HTTPException(status_code=400, detail="Unsupported payment method")


def _prepare_rub_order_db(
    *,
    provider: str,
    normalized_tg_id: int,
    buyer_email_norm: str,
    source: str,
    plan_code: str,
    campaign: str,
    promo_code: str,
    currency: str,
    payment_method_choice: str,
    lavatop_payment_provider: str,
    lavatop_payment_method: str,
    consume_pending_discount: bool,
    acquisition_handle: str | None,
    offer_token: str | None,
) -> dict[str, Any]:
    s = SessionLocal()
    try:
        expire_failed_commercial_reservations(s, now=_utcnow(), limit=100)
        plan = _resolve_plan_config(s=s, code=plan_code)
        if not plan:
            raise HTTPException(status_code=400, detail="Unknown plan for RUB checkout")
        user = None
        if normalized_tg_id > 0:
            user = s.query(User).filter(User.tg_id == int(normalized_tg_id)).first()
        if normalized_tg_id > 0 and not user:
            raise HTTPException(status_code=404, detail="User not found")
        acquisition_handoff = None
        acquisition_row = None
        attribution_snapshot = None
        if acquisition_handle and not offer_token:
            try:
                acquisition_handoff, acquisition_row, attribution_snapshot = (
                    consume_acquisition_handoff(
                        s,
                        raw_handle=acquisition_handle,
                        expected_purpose="checkout",
                        bound_tg_id=(
                            int(normalized_tg_id) if normalized_tg_id > 0 else None
                        ),
                        bound_account_id=(
                            str(getattr(user, "account_id", "") or "") or None
                        )
                        if user
                        else None,
                        now=_utcnow(),
                    )
                )
            except AcquisitionError as exc:
                raise HTTPException(
                    status_code=exc.status_code, detail=exc.code
                ) from exc
            source = str(
                attribution_snapshot["last"].get("source") or source or "unknown"
            )[:32]
            campaign = str(attribution_snapshot["last"].get("campaign") or "")[:64]
        normalized_plan_code = str(plan.get("code") or plan_code).strip().lower()
        if not public_provider_is_configured_for_plan(provider, normalized_plan_code):
            raise HTTPException(
                status_code=503,
                detail=f"{provider} plan is not configured for public RUB checkout",
            )
        _ensure_start99_available_for_order(
            s=s,
            user=user,
            buyer_email_norm=buyer_email_norm,
            plan_code=normalized_plan_code,
        )
        base_amount = max(0, int(plan.get("amount_rub") or 0))
        discount_allowed = normalized_plan_code != "start_99"
        requested_promo = (promo_code or "").strip().upper()[:32]
        effective_promo = ""
        pending_code = (
            (getattr(user, "pending_discount_code", "") or "").strip().upper()[:20]
            if user
            else ""
        )
        pending_pct = int(getattr(user, "pending_discount_pct", 0) or 0) if user else 0
        direct_discount_pct = 0
        direct_discount_code = ""
        direct_discount_source = ""
        referral_discount_eligible = bool(
            discount_allowed
            and user
            and getattr(user, "referrer_id", None)
            and not _has_successful_provider_payment(s=s, user=user)
        )
        working_amount = int(base_amount)
        if referral_discount_eligible and working_amount > 0:
            working_amount = max(1, int(round(working_amount * 0.8)))
        if discount_allowed and pending_pct > 0:
            working_amount, _ = _price_with_pending_discount(
                amount_rub=working_amount,
                pending_pct=pending_pct,
            )
            if pending_code:
                effective_promo = pending_code[:32]
        elif discount_allowed and requested_promo:
            direct_discount_pct, direct_discount_code, direct_discount_source = (
                _checkout_discount_code_preview_pct(
                    s=s,
                    promo_code=requested_promo,
                )
            )
            if direct_discount_pct > 0:
                working_amount, _ = _price_with_pending_discount(
                    amount_rub=working_amount,
                    pending_pct=direct_discount_pct,
                )
                effective_promo = direct_discount_code[:32]
        final_amount = max(1, int(working_amount)) if base_amount > 0 else 0
        discount_applied = bool(base_amount > 0 and final_amount < base_amount)
        discount_pct = (
            int(round((1.0 - (float(final_amount) / float(base_amount))) * 100))
            if discount_applied
            else 0
        )
        order_prefix = "fk" if provider == "freekassa" else provider[:12]
        order_subject = str(normalized_tg_id if normalized_tg_id > 0 else "public")
        order_id = f"{order_prefix}_{source}_{order_subject}_{int(time.time())}_{secrets.token_hex(4)}"
        commercial_lineage = None
        commercial_acquisition_session_id = None
        if offer_token:
            try:
                binding = bind_commercial_offer_to_order(
                    s,
                    offer_token=offer_token,
                    provider=provider,
                    candidate_order_id=order_id,
                    plan_code=normalized_plan_code,
                    currency=(currency or "RUB").strip().upper()[:16] or "RUB",
                    tg_id=(int(normalized_tg_id) if normalized_tg_id > 0 else None),
                    account_id=(str(getattr(user, "account_id", "") or "") or None)
                    if user
                    else None,
                    acquisition_handle=acquisition_handle,
                    now=_utcnow(),
                )
            except CommercialOrderBindingError as exc:
                if exc.code == "offer_token_expired":
                    s.commit()
                raise HTTPException(
                    status_code=exc.status_code, detail=exc.code
                ) from exc
            order_id = str(binding["order_id"])
            commercial_lineage = dict(binding["lineage"])
            commercial_acquisition_session_id = binding.get("acquisition_session_id")
            attribution_snapshot = binding.get("attribution_snapshot")
            if attribution_snapshot:
                source = str(
                    attribution_snapshot["last"].get("source") or source or "unknown"
                )[:32]
                campaign = str(attribution_snapshot["last"].get("campaign") or "")[:64]
            else:
                campaign = str(binding["campaign_key"])
            base_amount = int(binding["base_amount_rub"])
            final_amount = int(binding["final_amount_rub"])
            requested_promo = str(binding["promo_code"])
            effective_promo = requested_promo
            pending_code = ""
            direct_discount_pct = 0
            direct_discount_code = ""
            direct_discount_source = "commercial_offer"
            referral_discount_eligible = False
            discount_applied = final_amount < base_amount
            discount_pct = int(
                round((1.0 - (float(final_amount) / float(base_amount))) * 100)
            )
        amount_rub = float(final_amount)
        duration_days = max(1, int(plan.get("duration_days") or plan.get("days") or 30))
        entitlement_snapshot = {
            "plan_code": normalized_plan_code,
            "duration_days": duration_days,
            "amount_rub": f"{Decimal(str(amount_rub)):.2f}",
            "currency": (currency or "RUB").strip().upper()[:16] or "RUB",
            "source": str(source or "").strip().lower(),
        }
        plan_label = str(
            plan.get("label") or RUB_PLAN_LABELS.get(plan_code) or plan_code
        ).strip()
        fulfillment_mode = (
            "account_extend" if normalized_tg_id > 0 else "access_key_email"
        )
        created_at = _utcnow()
        intent = build_payment_order_intent(
            order_id=order_id,
            provider=provider,
            tg_id=int(normalized_tg_id) if normalized_tg_id > 0 else None,
            buyer_email=buyer_email_norm or None,
            plan_code=normalized_plan_code,
            source=source,
            amount=amount_rub,
            currency=(currency or "RUB").strip().upper()[:16] or "RUB",
            entitlement_snapshot=entitlement_snapshot,
            commercial_offer=commercial_lineage,
        )
        ext, order_created = persist_local_order_intent(
            s,
            intent=intent,
            metadata={
                "source": source,
                "campaign": campaign,
                "attribution_snapshot": attribution_snapshot,
                "requested_promo_code": requested_promo or None,
                "promo_code": effective_promo,
                "tg_id": int(normalized_tg_id) if normalized_tg_id > 0 else None,
                "buyer_email": buyer_email_norm or None,
                "plan_code": normalized_plan_code,
                "provider": provider,
                "payment_method": payment_method_choice or None,
                "lavatop_payment_provider": lavatop_payment_provider or None,
                "lavatop_payment_method": lavatop_payment_method or None,
                "plan_label": plan_label,
                "entitlement_snapshot": entitlement_snapshot,
                "fulfillment": {"mode": fulfillment_mode, "status": "pending_payment"},
                "pricing": {
                    "base_amount_rub": int(base_amount),
                    "final_amount_rub": int(final_amount),
                    "discount_pct": int(discount_pct),
                    "discount_applied": bool(discount_applied),
                    "pending_discount_code": pending_code or None,
                    "direct_discount_pct": int(direct_discount_pct),
                    "direct_discount_code": direct_discount_code or None,
                    "direct_discount_source": direct_discount_source or None,
                    "referral_discount_eligible": bool(referral_discount_eligible),
                },
            },
            serialize_meta=_serialize_external_order_meta,
            created_at=created_at,
            campaign=campaign,
            acquisition_session_id=(
                str(acquisition_row.id)
                if acquisition_row is not None
                else (
                    str(commercial_acquisition_session_id)
                    if commercial_acquisition_session_id
                    else None
                )
            ),
            promo_code=effective_promo or None,
        )
        if acquisition_handoff is not None and order_created:
            acquisition_handoff.bound_order_id = order_id
        if normalized_tg_id <= 0 and order_created:
            ensure_pending_claim(
                s,
                provider=provider,
                order_id=order_id,
                buyer_email=buyer_email_norm,
                plan_code=normalized_plan_code,
                duration_days=duration_days,
                now=ext.created_at,
            )
        if user and order_created and consume_pending_discount and discount_applied:
            user.pending_discount_pct = None
            user.pending_discount_code = None
            user.pending_discount_set_at = None
        s.commit()
        return {
            "source": source,
            "campaign": campaign,
            "normalized_plan_code": normalized_plan_code,
            "base_amount": base_amount,
            "final_amount": final_amount,
            "discount_pct": discount_pct,
            "discount_applied": discount_applied,
            "requested_promo": requested_promo,
            "effective_promo": effective_promo,
            "pending_code": pending_code,
            "direct_discount_pct": direct_discount_pct,
            "direct_discount_code": direct_discount_code,
            "direct_discount_source": direct_discount_source,
            "referral_discount_eligible": referral_discount_eligible,
            "amount_rub": amount_rub,
            "entitlement_snapshot": entitlement_snapshot,
            "order_id": order_id,
            "plan_label": plan_label,
            "fulfillment_mode": fulfillment_mode,
            "intent": intent,
        }
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def _record_rub_order_failure_db(*, provider: str, order_id: str, intent: Any) -> None:
    s = SessionLocal()
    try:
        row = (
            s.query(ExternalOrder)
            .filter(
                ExternalOrder.provider == provider, ExternalOrder.order_id == order_id
            )
            .first()
        )
        if row is not None:
            record_provider_checkout_failure(
                row,
                intent=intent,
                error_code="provider_checkout_error",
                serialize_meta=_serialize_external_order_meta,
            )
            s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def _record_rub_order_checkout_db(
    *,
    provider: str,
    order_id: str,
    intent: Any,
    payment_url: str,
    remote_response: dict[str, Any],
    metadata_update: dict[str, Any],
) -> str:
    s = SessionLocal()
    try:
        row = (
            s.query(ExternalOrder)
            .filter(
                ExternalOrder.provider == provider, ExternalOrder.order_id == order_id
            )
            .first()
        )
        if row is None:
            raise RuntimeError("local_payment_order_missing")
        record_provider_checkout(
            row,
            intent=intent,
            payment_url=payment_url,
            remote_response=remote_response,
            metadata_update=metadata_update,
            serialize_meta=_serialize_external_order_meta,
        )
        local_status = str(row.status or "pending")
        s.commit()
        return local_status
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def _payment_return_status_db(*, return_token: str) -> dict[str, Any]:
    session = SessionLocal()
    try:
        return payment_return_status(session, token=return_token, now=_utcnow())
    finally:
        session.close()


def _start99_eligibility_db(
    *, tg_id: int, ticket_payload: dict[str, Any]
) -> dict[str, Any]:
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        eligible = not _has_successful_provider_payment(s=s, user=user)
        replacement_ticket = None
        if not eligible:
            replacement_ticket = _create_checkout_ticket(
                tg_id=tg_id,
                plan_code="1_month",
                promo_code=_sanitize_deeplink_token(
                    str(ticket_payload.get("promo_code") or ""),
                    max_len=20,
                    uppercase=True,
                ),
                campaign_key=_sanitize_deeplink_token(
                    str(ticket_payload.get("campaign_key") or ""),
                    max_len=64,
                    uppercase=False,
                ),
                source=str(ticket_payload.get("source") or "bot").strip().lower(),
            )
        return {
            "known": True,
            "eligible": eligible,
            "reason": None if eligible else "start_99_already_used",
            "replacement_plan": "1_month",
            "replacement_checkout_ticket": replacement_ticket,
        }
    finally:
        s.close()


def _freekassa_order_context_db(
    *,
    order_id: str,
    actor_tg_id: int,
    request_source: str,
) -> tuple[str, str]:
    s = SessionLocal()
    try:
        row = (
            s.query(ExternalOrder)
            .filter(
                ExternalOrder.provider == "freekassa",
                ExternalOrder.order_id == str(order_id),
            )
            .first()
        )
        if not row:
            raise HTTPException(status_code=404, detail="Order not found")
        if int(row.tg_id or 0) != int(actor_tg_id) and not _is_admin_tg(actor_tg_id):
            raise HTTPException(status_code=403, detail="Access denied")
        local_status = str(row.status or "")
        source = str(row.source or "").strip().lower() or request_source
        return local_status, source
    finally:
        s.close()


def _freekassa_refund_context_db(*, order_id: str) -> tuple[float, str]:
    s = SessionLocal()
    try:
        row = (
            s.query(ExternalOrder)
            .filter(
                ExternalOrder.provider == "freekassa",
                ExternalOrder.order_id == str(order_id),
            )
            .first()
        )
        if not row:
            raise HTTPException(status_code=404, detail="Order not found")
        return float(row.amount or 0.0), str(row.source or "site")
    finally:
        s.close()


async def _rub_create_order_internal(
    *,
    request: Request,
    provider: str,
    tg_id: int | None,
    source: str,
    plan_code: str,
    campaign: str = "",
    promo_code: str = "",
    currency: str = "RUB",
    buyer_email: str | None = None,
    payment_method: str | None = None,
    consume_pending_discount: bool = False,
    acquisition_handle: str | None = None,
    offer_token: str | None = None,
    return_surface: str = "marketing",
) -> RubOrderActionOut:
    _ensure_checkout_runtime_ready()
    provider = _normalize_provider(provider)
    if not provider:
        enabled_codes = [
            str(row.get("code") or "") for row in enabled_public_provider_catalog()
        ]
        provider = str(enabled_codes[0] if enabled_codes else "").strip().lower()
    if not provider:
        raise HTTPException(
            status_code=503, detail="No RUB payment providers are enabled"
        )
    if provider not in PAYMENT_PROVIDER_WHITELIST:
        raise HTTPException(status_code=400, detail="Unsupported payment provider")
    _ensure_checkout_provider_enabled(provider)
    if provider != "freekassa" and not provider_is_configured(provider):
        raise HTTPException(status_code=503, detail=f"{provider} is not configured")
    payment_method_choice, lavatop_payment_provider, lavatop_payment_method = (
        "",
        "",
        "",
    )
    if provider == "lavatop":
        payment_method_choice, lavatop_payment_provider, lavatop_payment_method = (
            _normalize_lavatop_payment_method(payment_method)
        )
    normalized_tg_id = int(tg_id or 0)
    buyer_email_norm = ""
    if normalized_tg_id <= 0:
        try:
            buyer_email_norm = validate_email_input(str(buyer_email or ""))
        except InvalidEmailInputError as exc:
            raise HTTPException(
                status_code=400, detail="Valid buyer_email is required"
            ) from exc
    prepared = await run_payment_db_use_case(
        "order_prepare",
        _prepare_rub_order_db,
        provider=provider,
        normalized_tg_id=normalized_tg_id,
        buyer_email_norm=buyer_email_norm,
        source=source,
        plan_code=plan_code,
        campaign=campaign,
        promo_code=promo_code,
        currency=currency,
        payment_method_choice=payment_method_choice,
        lavatop_payment_provider=lavatop_payment_provider,
        lavatop_payment_method=lavatop_payment_method,
        consume_pending_discount=consume_pending_discount,
        acquisition_handle=acquisition_handle,
        offer_token=offer_token,
    )
    source = str(prepared["source"])
    campaign = str(prepared["campaign"])
    normalized_plan_code = str(prepared["normalized_plan_code"])
    base_amount = int(prepared["base_amount"])
    final_amount = int(prepared["final_amount"])
    discount_pct = int(prepared["discount_pct"])
    discount_applied = bool(prepared["discount_applied"])
    requested_promo = str(prepared["requested_promo"])
    effective_promo = str(prepared["effective_promo"])
    pending_code = str(prepared["pending_code"])
    direct_discount_pct = int(prepared["direct_discount_pct"])
    direct_discount_code = str(prepared["direct_discount_code"])
    direct_discount_source = str(prepared["direct_discount_source"])
    referral_discount_eligible = bool(prepared["referral_discount_eligible"])
    amount_rub = float(prepared["amount_rub"])
    entitlement_snapshot = dict(prepared["entitlement_snapshot"])
    order_id = str(prepared["order_id"])
    plan_label = str(prepared["plan_label"])
    fulfillment_mode = str(prepared["fulfillment_mode"])
    intent = prepared["intent"]
    payment_return_token = issue_payment_return_token(
        provider=provider,
        order_id=order_id,
        surface=return_surface,
    )

    req_data = {
        "provider": provider,
        "amount": float(amount_rub),
        "currency": "RUB",
        "tg_id": int(normalized_tg_id) if normalized_tg_id > 0 else None,
        "buyer_email": buyer_email_norm or None,
        "plan_code": normalized_plan_code,
        "plan_label": plan_label,
        "campaign": campaign or "",
        "requested_promo_code": requested_promo or "",
        "promo_code": effective_promo or "",
        "source": source,
        "payment_method": payment_method_choice or "",
        "lavatop_payment_provider": lavatop_payment_provider or "",
        "lavatop_payment_method": lavatop_payment_method or "",
        "discount_pct": int(discount_pct),
        "base_amount_rub": int(base_amount),
        "final_amount_rub": int(final_amount),
        "referral_discount_eligible": bool(referral_discount_eligible),
    }
    try:
        if provider == "freekassa":
            payment_url = _build_freekassa_payment_url(
                source=source,
                order_id=order_id,
                amount_rub=amount_rub,
                currency="RUB",
                tg_id=int(normalized_tg_id),
                plan_code=normalized_plan_code,
                campaign=campaign or "",
                promo_code=effective_promo or "",
            )
            remote_response: dict[str, Any] = {}
        else:
            payment = await create_rub_payment(
                http_registry=getattr(request.app.state, "payment_http_registry", None),
                provider=provider,
                order_id=order_id,
                amount_rub=amount_rub,
                currency="RUB",
                description=f"POKROV {plan_label}",
                success_url=_pay_success_url(provider, return_surface=return_surface),
                fail_url=_pay_fail_url(provider, return_surface=return_surface),
                result_url=_provider_result_url(provider),
                refund_url=_provider_refund_url(provider),
                chargeback_url=_provider_chargeback_url(provider),
                logo_url=(os.getenv("PAYMENT_LOGO_URL") or "").strip(),
                custom={
                    **(
                        {"tg_id": int(normalized_tg_id)} if normalized_tg_id > 0 else {}
                    ),
                    **({"email": buyer_email_norm} if buyer_email_norm else {}),
                    "plan_code": normalized_plan_code,
                    "provider": provider,
                    "source": source,
                    "campaign": campaign or "",
                    "promo_code": effective_promo or "",
                    "payment_method": payment_method_choice or "",
                    "lavatop_payment_provider": lavatop_payment_provider or "",
                    "lavatop_payment_method": lavatop_payment_method or "",
                },
            )
            payment_url = str(payment.get("payment_url") or "").strip()
            remote_response = dict(payment.get("remote") or {})
    except Exception:
        try:
            await run_payment_db_use_case(
                "order_record_failure",
                _record_rub_order_failure_db,
                provider=provider,
                order_id=order_id,
                intent=intent,
            )
        except Exception:
            logger.exception(
                "payment_checkout_failure_state_write_failed provider=%s", provider
            )
        raise

    local_status = await run_payment_db_use_case(
        "order_record_checkout",
        _record_rub_order_checkout_db,
        provider=provider,
        order_id=order_id,
        intent=intent,
        payment_url=payment_url,
        remote_response=remote_response,
        metadata_update={
            "request": req_data,
            "entitlement_snapshot": entitlement_snapshot,
            "pricing": {
                "base_amount_rub": int(base_amount),
                "final_amount_rub": int(final_amount),
                "discount_pct": int(discount_pct),
                "discount_applied": bool(discount_applied),
                "requested_promo_code": requested_promo or None,
                "promo_code": effective_promo or None,
                "pending_discount_code": pending_code or None,
                "direct_discount_pct": int(direct_discount_pct),
                "direct_discount_code": direct_discount_code or None,
                "direct_discount_source": direct_discount_source or None,
            },
            "fulfillment": {
                "mode": fulfillment_mode,
                "status": "pending_payment",
                "buyer_email": buyer_email_norm or None,
            },
            "payment_method": {
                "choice": payment_method_choice or None,
                "lavatop_payment_provider": lavatop_payment_provider or None,
                "lavatop_payment_method": lavatop_payment_method or None,
            },
        },
    )

    return RubOrderActionOut(
        ok=True,
        provider=provider,
        provider_label=(
            PROVIDER_META.get(provider).label
            if provider in PROVIDER_META
            else provider.title()
        ),
        order_id=order_id,
        payment_url=payment_url or None,
        amount_rub=float(amount_rub),
        currency="RUB",
        status=local_status,
        widget_enabled=bool(CHECKOUT_WIDGET_ENABLED),
        discount_applied=bool(discount_applied),
        base_amount_rub=float(base_amount),
        discount_pct=int(discount_pct),
        payment_return_token=payment_return_token,
    )


@app.get("/api/public/promo-media/{asset_id}")
async def public_promo_media(asset_id: str) -> FileResponse:
    path = _promo_media_path(asset_id)
    mime = _PROMO_MEDIA_SUFFIX_MIME.get(path.suffix.lower())
    if not mime:
        raise HTTPException(status_code=404, detail="Promo media not found")
    return FileResponse(
        path,
        media_type=mime,
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "X-Content-Type-Options": "nosniff",
            "Content-Disposition": f'inline; filename="{path.name}"',
        },
    )


# Payment HTTP routes register next through the ordered api_payment_routes slice.
