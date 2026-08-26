"""User-facing dashboard, rewards, redemption, feedback and support routes.

Loaded by the api composition root in source order. Public symbols are
re-exported for backwards compatibility.
"""

try:
    from .module_slices import bootstrap_slice
except ImportError:
    from module_slices import bootstrap_slice

bootstrap_slice(globals())

def _sample_memory_percent(sample: NodeHealthSample | None) -> float:
    if not sample:
        return 0.0
    total = float(getattr(sample, "memory_total_mb", 0) or 0.0)
    if total <= 0:
        return 0.0
    used = float(getattr(sample, "memory_used_mb", 0) or 0.0)
    return round((used / total) * 100.0, 2)


def _sample_disk_percent(sample: NodeHealthSample | None) -> float:
    if not sample:
        return 0.0
    total = float(getattr(sample, "disk_total_gb", 0.0) or 0.0)
    if total <= 0:
        return 0.0
    used = float(getattr(sample, "disk_used_gb", 0.0) or 0.0)
    return round((used / total) * 100.0, 2)


def _network_utilization_percent(total_mbps: object) -> float:
    current = float(total_mbps or 0.0)
    capacity = float(NODE_METRICS_PORT_CAPACITY_MBPS or 0.0)
    if current <= 0 or capacity <= 0:
        return 0.0
    return round((current / capacity) * 100.0, 2)


def _observer_is_stale(node: Node, *, now: datetime) -> bool:
    last_push_at = getattr(node, "observer_last_push_at", None)
    configured = bool(str(getattr(node, "observer_push_secret", "") or "").strip())
    if not configured and not last_push_at:
        return False
    if not last_push_at:
        return True
    return int((now - last_push_at).total_seconds()) > observer_stale_after_seconds()


def _legacy_node_alert_kind(kind: str) -> str:
    mapping = {
        "cpu_high": "high_cpu",
        "memory_high": "high_memory",
        "disk_high": "high_disk",
        "network_high": "high_network",
        "latency_high": "high_latency",
        "error_rate_high": "high_error_rate",
        "client_density_high": "high_client_density",
        "observer_push_stale": "observer_push_stale",
        "stale_metrics": "stale_metrics",
    }
    return mapping.get(str(kind or ""), str(kind or ""))


def _legacy_node_alerts(kinds: list[str]) -> list[str]:
    return sorted({_legacy_node_alert_kind(kind) for kind in kinds if str(kind or "").strip()})


def _nullable_node_memory_value(*, used_mb: object, total_mb: object) -> tuple[int | None, int | None]:
    total = int(total_mb or 0)
    if total <= 0:
        return None, None
    return int(used_mb or 0), total


def _nullable_node_disk_value(*, used_gb: object, total_gb: object, free_gb: object) -> tuple[float | None, float | None, float | None]:
    total = float(total_gb or 0.0)
    if total <= 0:
        return None, None, None
    return float(used_gb or 0.0), total, float(free_gb or 0.0)


def _nullable_node_network_value(
    *,
    rx_bytes_total: object,
    tx_bytes_total: object,
    rx_mbps: object,
    tx_mbps: object,
    total_mbps: object,
) -> tuple[int | None, int | None, float | None, float | None, float | None]:
    rx_total = int(rx_bytes_total) if rx_bytes_total is not None else None
    tx_total = int(tx_bytes_total) if tx_bytes_total is not None else None
    rx_rate = float(rx_mbps) if rx_mbps is not None else None
    tx_rate = float(tx_mbps) if tx_mbps is not None else None
    total_rate = float(total_mbps) if total_mbps is not None else None
    if total_rate is None and (rx_rate is not None or tx_rate is not None):
        total_rate = float(rx_rate or 0.0) + float(tx_rate or 0.0)
    return rx_total, tx_total, rx_rate, tx_rate, total_rate


@app.get("/api/admin/metrics/status")
async def admin_metrics_status(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data, request=request)
    stale_after_seconds = max(300, int(os.getenv("NODE_METRICS_STALE_AFTER_SECONDS", "900")))
    now = _utcnow()
    s = SessionLocal()
    try:
        return _ops_build_admin_metrics_status_snapshot(
            s=s,
            now=now,
            stale_after_seconds=stale_after_seconds,
        )
    finally:
        s.close()


@app.get("/api/admin/funnel/summary")
async def admin_funnel_summary(
    x_telegram_init_data: str = Header(default=""),
    from_: str = Query(default="", alias="from"),
    to: str = Query(default="", alias="to"),
) -> dict:
    _require_admin(x_telegram_init_data)
    from_dt, to_dt = _admin_metrics_range(from_, to, max_days=90)
    s = SessionLocal()
    try:
        return _admin_funnel_summary_payload(s=s, from_dt=from_dt, to_dt=to_dt)
    finally:
        s.close()


def _parse_admin_datetime(value: str | None) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def _admin_metrics_range(from_value: str | None, to_value: str | None, *, max_days: int = 120) -> tuple[datetime, datetime]:
    now = _utcnow()
    to_dt = _parse_admin_datetime(to_value) or now
    from_dt = _parse_admin_datetime(from_value) or (to_dt - timedelta(days=13))
    if from_dt > to_dt:
        from_dt, to_dt = to_dt, from_dt
    if (to_dt - from_dt).days > max_days:
        from_dt = to_dt - timedelta(days=max_days)
    from_dt = from_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    to_dt = to_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    return from_dt, to_dt


def _pct(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(float(part) / float(total) * 100.0, 1)


def _funnel_stage_row(key: str, label: str, entered: int, reached_next: int) -> dict[str, Any]:
    entered = max(0, int(entered or 0))
    reached_next = max(0, int(reached_next or 0))
    return {
        "key": key,
        "label": label,
        "entered": entered,
        "reached_next": reached_next,
        "dropped": max(0, entered - reached_next),
        "conversion_pct": _pct(reached_next, entered),
    }


def _admin_product_observability_payload(*, s, from_dt: datetime, to_dt: datetime) -> dict[str, Any]:
    range_filter = (Event.created_at >= from_dt, Event.created_at <= to_dt)
    error_filter = or_(Event.result == "failure", Event.error_code.isnot(None))
    total_events = int(s.query(func.count(Event.id)).filter(*range_filter).scalar() or 0)
    failed_events = int(
        s.query(func.count(Event.id)).filter(*range_filter).filter(error_filter).scalar() or 0
    )
    retryable_failures = int(
        s.query(func.count(Event.id))
        .filter(*range_filter)
        .filter(error_filter, Event.retryable == True)
        .scalar()
        or 0
    )
    successful_events = int(
        s.query(func.count(Event.id))
        .filter(*range_filter, Event.result == "success")
        .scalar()
        or 0
    )
    skewed_events = int(
        s.query(func.count(Event.id))
        .filter(*range_filter)
        .filter(Event.clock_skew_state.in_(["client_late", "client_future"]))
        .scalar()
        or 0
    )
    latest_event_at = s.query(func.max(Event.received_at)).filter(*range_filter).scalar()

    active_from = min(to_dt, _utcnow()) - timedelta(days=7)
    active_identities = {
        (f"account:{account_id}" if account_id else f"telegram:{int(tg_id)}")
        for account_id, tg_id in (
            s.query(Event.account_id, Event.tg_id)
            .filter(Event.created_at >= active_from, Event.created_at <= to_dt)
            .filter(Event.event_name == "connected_ok")
            .filter(or_(Event.result.is_(None), Event.result == "success"))
            .distinct()
            .all()
        )
        if account_id or (tg_id is not None and int(tg_id) > 0)
    }

    def grouped_rows(column: Any, *, errors_only: bool = False, limit: int = 10) -> list[dict[str, Any]]:
        query = (
            s.query(column, func.count(Event.id), func.max(Event.received_at))
            .filter(*range_filter)
            .filter(column.isnot(None), column != "")
        )
        if errors_only:
            query = query.filter(error_filter)
        rows = (
            query.group_by(column)
            .order_by(func.count(Event.id).desc(), column.asc())
            .limit(limit)
            .all()
        )
        return [
            {
                "key": str(key or "unknown")[:64],
                "count": int(count or 0),
                "latest_at": _safe_iso(latest_at),
            }
            for key, count, latest_at in rows
        ]

    version_rows = (
        s.query(
            Event.platform,
            Event.app_version,
            func.count(Event.id),
            func.count(func.distinct(Event.tg_id)),
            func.max(Event.received_at),
        )
        .filter(*range_filter)
        .filter(Event.platform.isnot(None), Event.app_version.isnot(None))
        .group_by(Event.platform, Event.app_version)
        .order_by(func.count(Event.id).desc(), Event.platform.asc(), Event.app_version.desc())
        .limit(20)
        .all()
    )
    return {
        "summary": {
            "events": total_events,
            "successes": successful_events,
            "failures": failed_events,
            "retryable_failures": retryable_failures,
            "active_users_7d": len(active_identities),
            "clock_skewed": skewed_events,
            "latest_event_at": _safe_iso(latest_event_at),
        },
        "errors": grouped_rows(Event.error_code, errors_only=True),
        "error_categories": grouped_rows(Event.error_category, errors_only=True),
        "stages": grouped_rows(Event.stage, errors_only=True),
        "subsystems": grouped_rows(Event.subsystem, errors_only=True),
        "network_classes": grouped_rows(Event.network_class),
        "versions": [
            {
                "platform": str(platform or "unknown")[:24],
                "app_version": str(app_version or "unknown")[:32],
                "events": int(events or 0),
                "users": int(users or 0),
                "latest_at": _safe_iso(latest_at),
            }
            for platform, app_version, events, users, latest_at in version_rows
        ],
    }


def _admin_funnel_summary_payload(*, s, from_dt: datetime, to_dt: datetime) -> dict[str, Any]:
    cohort = (
        s.query(AcquisitionSession)
        .filter(AcquisitionSession.first_touch_at >= from_dt, AcquisitionSession.first_touch_at <= to_dt)
        .all()
    )
    cohort_ids = {str(row.id) for row in cohort}
    hash_to_id = {str(row.session_key_hash): str(row.id) for row in cohort}

    entry_ids: set[str] = set()
    resolved_ids: set[str] = set()
    checkout_ids: set[str] = set()
    paid_ids: set[str] = set()
    connected_ids: set[str] = set()

    if hash_to_id:
        entry_hashes = {
            str(value)
            for (value,) in (
                s.query(FunnelEvent.session_id)
                .filter(FunnelEvent.session_id.in_(sorted(hash_to_id)))
                .filter(FunnelEvent.created_at <= to_dt)
                .filter(FunnelEvent.event_name.in_(["download_click", "bot_open_intent"]))
                .distinct()
                .all()
            )
        }
        entry_ids.update(hash_to_id[value] for value in entry_hashes if value in hash_to_id)

    handoffs = []
    if cohort_ids:
        handoffs = (
            s.query(AcquisitionHandoff)
            .filter(AcquisitionHandoff.acquisition_session_id.in_(sorted(cohort_ids)))
            .filter(AcquisitionHandoff.created_at <= to_dt)
            .all()
        )
    entry_purposes = {"android_install", "windows_install", "account_continue", "telegram_continue"}
    for row in handoffs:
        session_id = str(row.acquisition_session_id)
        if row.purpose in entry_purposes:
            entry_ids.add(session_id)
            if row.consumed_at is not None and row.consumed_at <= to_dt:
                resolved_ids.add(session_id)
        elif row.purpose == "checkout" and row.consumed_at is not None and row.consumed_at <= to_dt:
            checkout_ids.add(session_id)

    external_orders = []
    pay_attempts = []
    if cohort_ids:
        external_orders = (
            s.query(ExternalOrder)
            .filter(ExternalOrder.acquisition_session_id.in_(sorted(cohort_ids)))
            .filter(ExternalOrder.created_at <= to_dt)
            .all()
        )
        pay_attempts = (
            s.query(PayAttempt)
            .filter(PayAttempt.acquisition_session_id.in_(sorted(cohort_ids)))
            .filter(PayAttempt.started_at <= to_dt)
            .all()
        )
    for row in external_orders:
        session_id = str(row.acquisition_session_id or "")
        checkout_ids.add(session_id)
        if str(row.status or "").lower() == "paid" and row.paid_at is not None and row.paid_at <= to_dt:
            paid_ids.add(session_id)
    for row in pay_attempts:
        session_id = str(row.acquisition_session_id or "")
        checkout_ids.add(session_id)
        if str(row.status or "").lower() == "paid" and row.paid_at is not None and row.paid_at <= to_dt:
            paid_ids.add(session_id)

    bound_account_ids = {str(row.bound_account_id) for row in cohort if row.bound_account_id}
    connection_times: dict[str, list[datetime]] = {}
    if bound_account_ids:
        for row in s.query(AccountExperienceState).filter(AccountExperienceState.account_id.in_(sorted(bound_account_ids))).all():
            values = [value for value in (row.first_connection_reported_at, row.first_connection_verified_at) if value is not None]
            if values:
                connection_times.setdefault(str(row.account_id), []).extend(values)
        for account_id, observed_at in (
            s.query(ConnectionEvidence.account_id, ConnectionEvidence.observed_at)
            .filter(ConnectionEvidence.account_id.in_(sorted(bound_account_ids)))
            .filter(ConnectionEvidence.observed_at <= to_dt)
            .all()
        ):
            if observed_at is not None:
                connection_times.setdefault(str(account_id), []).append(observed_at)
    for row in cohort:
        account_id = str(row.bound_account_id or "")
        if any(row.first_touch_at <= value <= to_dt for value in connection_times.get(account_id, [])):
            connected_ids.add(str(row.id))

    entry_ids &= cohort_ids
    resolved_ids &= entry_ids
    checkout_ids &= resolved_ids
    paid_ids &= checkout_ids
    connected_ids &= paid_ids

    acquisition_stages = [
        _funnel_stage_row("visit_to_entry", "Первый визит → скачивание или бот", len(cohort_ids), len(entry_ids)),
        _funnel_stage_row("entry_to_bound", "Скачивание/бот → подтверждённый вход", len(entry_ids), len(resolved_ids)),
        _funnel_stage_row("bound_to_checkout", "Вход → начало оплаты", len(resolved_ids), len(checkout_ids)),
        _funnel_stage_row("checkout_to_paid", "Начали оплату → оплатили", len(checkout_ids), len(paid_ids)),
        _funnel_stage_row("paid_to_connected", "Оплатили → подключились", len(paid_ids), len(connected_ids)),
    ]

    source_rows: list[dict[str, Any]] = []
    for source in sorted({str(row.first_source or "unknown") for row in cohort}):
        source_ids = {str(row.id) for row in cohort if str(row.first_source or "unknown") == source}
        source_rows.append(
            {
                "source": source,
                "sessions": len(source_ids),
                "entry_intents": len(source_ids & entry_ids),
                "resolved_entries": len(source_ids & resolved_ids),
                "checkouts": len(source_ids & checkout_ids),
                "paid": len(source_ids & paid_ids),
                "connected": len(source_ids & connected_ids),
            }
        )
    source_rows.sort(key=lambda row: (-int(row["sessions"]), str(row["source"])))

    product_open_users = {
        int(value)
        for (value,) in (
            s.query(Event.tg_id)
            .filter(Event.created_at >= from_dt, Event.created_at <= to_dt)
            .filter(Event.event_name.in_(["opened_webapp", "deep_link_opened"]))
            .distinct()
            .all()
        )
        if value is not None and int(value) > 0
    }
    product_open_users.update(
        int(value)
        for (value,) in (
            s.query(User.tg_id)
            .filter(User.app_last_seen_at >= from_dt, User.app_last_seen_at <= to_dt)
            .distinct()
            .all()
        )
        if value is not None and int(value) > 0
    )

    checkout_users = {
        int(value)
        for (value,) in (
            s.query(Event.tg_id)
            .filter(Event.created_at >= from_dt, Event.created_at <= to_dt)
            .filter(Event.event_name.in_(["clicked_pay", "pay_started"]))
            .distinct()
            .all()
        )
        if value is not None and int(value) > 0
    }
    checkout_users.update(
        int(value)
        for (value,) in s.query(PayAttempt.tg_id).filter(PayAttempt.started_at >= from_dt, PayAttempt.started_at <= to_dt).distinct().all()
        if value is not None and int(value) > 0
    )
    checkout_users.update(
        int(value)
        for (value,) in s.query(ExternalOrder.tg_id).filter(ExternalOrder.created_at >= from_dt, ExternalOrder.created_at <= to_dt).distinct().all()
        if value is not None and int(value) > 0
    )

    paid_users = {
        int(value)
        for (value,) in (
            s.query(Event.tg_id)
            .filter(Event.created_at >= from_dt, Event.created_at <= to_dt)
            .filter(Event.event_name.in_(["paid", "renewed"]))
            .distinct()
            .all()
        )
        if value is not None and int(value) > 0
    }
    paid_users.update(
        int(value)
        for (value,) in (
            s.query(PayAttempt.tg_id)
            .filter(PayAttempt.paid_at >= from_dt, PayAttempt.paid_at <= to_dt)
            .filter(func.lower(func.coalesce(PayAttempt.status, "")) == "paid")
            .distinct()
            .all()
        )
        if value is not None and int(value) > 0
    )
    paid_users.update(
        int(value)
        for (value,) in (
            s.query(ExternalOrder.tg_id)
            .filter(ExternalOrder.paid_at >= from_dt, ExternalOrder.paid_at <= to_dt)
            .filter(func.lower(func.coalesce(ExternalOrder.status, "")) == "paid")
            .distinct()
            .all()
        )
        if value is not None and int(value) > 0
    )

    connected_users = {
        int(value)
        for (value,) in (
            s.query(Event.tg_id)
            .filter(Event.created_at >= from_dt, Event.created_at <= to_dt)
            .filter(Event.event_name == "connected_ok")
            .distinct()
            .all()
        )
        if value is not None and int(value) > 0
    }
    product_account_ids = {
        str(value)
        for (value,) in (
            s.query(AccountExperienceState.account_id)
            .filter(
                or_(
                    and_(AccountExperienceState.first_connection_reported_at >= from_dt, AccountExperienceState.first_connection_reported_at <= to_dt),
                    and_(AccountExperienceState.first_connection_verified_at >= from_dt, AccountExperienceState.first_connection_verified_at <= to_dt),
                )
            )
            .distinct()
            .all()
        )
        if value
    }
    product_account_ids.update(
        str(value)
        for (value,) in (
            s.query(ConnectionEvidence.account_id)
            .filter(ConnectionEvidence.observed_at >= from_dt, ConnectionEvidence.observed_at <= to_dt)
            .distinct()
            .all()
        )
        if value
    )
    if product_account_ids:
        connected_users.update(
            int(value)
            for (value,) in s.query(User.tg_id).filter(User.account_id.in_(sorted(product_account_ids))).distinct().all()
            if value is not None and int(value) > 0
        )

    product_checkout_users = product_open_users & checkout_users
    product_paid_users = product_checkout_users & paid_users
    product_connected_users = product_paid_users & connected_users
    product_stages = [
        _funnel_stage_row("open_to_checkout", "Открыли продукт → начали оплату", len(product_open_users), len(product_checkout_users)),
        _funnel_stage_row("checkout_to_paid", "Начали оплату → оплатили", len(product_checkout_users), len(product_paid_users)),
        _funnel_stage_row("paid_to_connected", "Оплатили → подключились", len(product_paid_users), len(product_connected_users)),
    ]

    return {
        "period": {"from": from_dt.date().isoformat(), "to": to_dt.date().isoformat()},
        "acquisition": {
            "cohort": "first_touch_in_period",
            "totals": {
                "sessions": len(cohort_ids),
                "entry_intents": len(entry_ids),
                "resolved_entries": len(resolved_ids),
                "checkouts": len(checkout_ids),
                "paid": len(paid_ids),
                "connected": len(connected_ids),
            },
            "stages": acquisition_stages,
            "drop_reasons": [
                {"reason": "Не скачали приложение и не открыли бота", "count": acquisition_stages[0]["dropped"]},
                {"reason": "Не подтвердили вход из приложения или бота", "count": acquisition_stages[1]["dropped"]},
                {"reason": "Не начали оплату", "count": acquisition_stages[2]["dropped"]},
                {"reason": "Оплата не подтверждена", "count": acquisition_stages[3]["dropped"]},
                {"reason": "Первое подключение не подтверждено", "count": acquisition_stages[4]["dropped"]},
            ],
            "by_source": source_rows[:20],
        },
        "product": {
            "cohort": "known_user_open_in_period",
            "totals": {
                "opened": len(product_open_users),
                "checkouts": len(product_checkout_users),
                "paid": len(product_paid_users),
                "connected": len(product_connected_users),
            },
            "stages": product_stages,
            "drop_reasons": [
                {"reason": "Открыли продукт, но не начали оплату", "count": product_stages[0]["dropped"]},
                {"reason": "Начали оплату, но не оплатили", "count": product_stages[1]["dropped"]},
                {"reason": "Оплатили, но подключение не подтверждено", "count": product_stages[2]["dropped"]},
            ],
            "observability": _admin_product_observability_payload(
                s=s,
                from_dt=from_dt,
                to_dt=to_dt,
            ),
        },
        "notes": [
            "Acquisition — first-touch cohort по хэшированному first-party session ID; downstream считается только по серверно связанному handoff, order/pay attempt и account.",
            "Product — distinct known users; пересекающиеся события, попытки и заказы объединяются, а не складываются.",
            "Raw URL, referrer path, IP, user-agent, session hash, Telegram ID и account ID в ответ не попадают.",
        ],
    }


def _date_key(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    return text[:10]


def _quality_badge(status: str) -> str:
    status_norm = str(status or "").strip().lower()
    if status_norm in {"fresh", "ok"}:
        return "good"
    if status_norm == "missing":
        return "bad"
    return "warn"


@app.get("/api/admin/nodes/traffic")
async def admin_nodes_traffic(
    x_telegram_init_data: str = Header(default=""),
    from_: str = Query(default="", alias="from"),
    to: str = Query(default="", alias="to"),
) -> dict:
    _require_admin(x_telegram_init_data)
    from_dt, to_dt = _admin_metrics_range(from_, to)
    s = SessionLocal()
    try:
        rows = (
            s.query(
                func.date(NodeHealthSample.sampled_at).label("day"),
                NodeHealthSample.node_code.label("node_code"),
                func.max(NodeHealthSample.active_clients).label("devices"),
                (
                    func.max(func.coalesce(NodeHealthSample.total_traffic_bytes, 0))
                    - func.min(func.coalesce(NodeHealthSample.total_traffic_bytes, 0))
                ).label("traffic_bytes"),
            )
            .filter(NodeHealthSample.sampled_at >= from_dt, NodeHealthSample.sampled_at <= to_dt)
            .group_by(func.date(NodeHealthSample.sampled_at), NodeHealthSample.node_code)
            .order_by(func.date(NodeHealthSample.sampled_at).asc(), NodeHealthSample.node_code.asc())
            .all()
        )
        payload_rows = []
        for row in rows:
            day_key = _date_key(getattr(row, "day", None))
            if not day_key:
                continue
            traffic_bytes = int(getattr(row, "traffic_bytes", 0) or 0)
            payload_rows.append(
                {
                    "date": day_key,
                    "node_code": str(getattr(row, "node_code", "") or ""),
                    "devices": int(getattr(row, "devices", 0) or 0),
                    "traffic_bytes": max(0, traffic_bytes),
                    "traffic_gb": round(max(0, traffic_bytes) / float(1024**3), 3),
                }
            )
        return {
            "from": from_dt.date().isoformat(),
            "to": to_dt.date().isoformat(),
            "rows": payload_rows,
        }
    finally:
        s.close()


@app.get("/api/admin/metrics/timeseries")
async def admin_metrics_timeseries(
    x_telegram_init_data: str = Header(default=""),
    from_: str = Query(default="", alias="from"),
    to: str = Query(default="", alias="to"),
) -> dict:
    _require_admin(x_telegram_init_data)
    from_dt, to_dt = _admin_metrics_range(from_, to)

    days: list[str] = []
    cursor = from_dt.date()
    to_day = to_dt.date()
    while cursor <= to_day:
        days.append(cursor.isoformat())
        cursor = cursor + timedelta(days=1)

    s = SessionLocal()
    try:
        registration_rows = (
            s.query(func.date(User.created_at).label("day"), func.count(User.tg_id).label("value"))
            .filter(User.created_at.isnot(None), User.created_at >= from_dt, User.created_at <= to_dt)
            .group_by(func.date(User.created_at))
            .all()
        )
        registrations_map = {_date_key(getattr(row, "day", None)): int(getattr(row, "value", 0) or 0) for row in registration_rows}

        churn_rows = (
            s.query(func.date(Event.created_at).label("day"), func.count(func.distinct(Event.tg_id)).label("value"))
            .filter(Event.created_at >= from_dt, Event.created_at <= to_dt)
            .filter(Event.event_name == "expired")
            .group_by(func.date(Event.created_at))
            .all()
        )
        churn_map = {_date_key(getattr(row, "day", None)): int(getattr(row, "value", 0) or 0) for row in churn_rows}

        stars_rows = (
            s.query(func.date(PayAttempt.paid_at).label("day"), func.sum(PayAttempt.amount_stars).label("value"))
            .filter(PayAttempt.paid_at.isnot(None), PayAttempt.paid_at >= from_dt, PayAttempt.paid_at <= to_dt)
            .filter(func.lower(func.coalesce(PayAttempt.status, "")) == "paid")
            .group_by(func.date(PayAttempt.paid_at))
            .all()
        )
        stars_map = {_date_key(getattr(row, "day", None)): int(getattr(row, "value", 0) or 0) for row in stars_rows}

        rub_rows = (
            s.query(func.date(ExternalOrder.paid_at).label("day"), func.sum(ExternalOrder.amount).label("value"))
            .filter(ExternalOrder.paid_at.isnot(None), ExternalOrder.paid_at >= from_dt, ExternalOrder.paid_at <= to_dt)
            .filter(func.lower(func.coalesce(ExternalOrder.status, "")) == "paid")
            .filter(func.upper(func.coalesce(ExternalOrder.currency, "RUB")) == "RUB")
            .group_by(func.date(ExternalOrder.paid_at))
            .all()
        )
        rub_map = {_date_key(getattr(row, "day", None)): round(float(getattr(row, "value", 0.0) or 0.0), 2) for row in rub_rows}

        node_rows = (
            s.query(
                func.date(NodeHealthSample.sampled_at).label("day"),
                NodeHealthSample.node_code.label("node_code"),
                func.max(NodeHealthSample.active_clients).label("devices"),
                (
                    func.max(func.coalesce(NodeHealthSample.total_traffic_bytes, 0))
                    - func.min(func.coalesce(NodeHealthSample.total_traffic_bytes, 0))
                ).label("traffic_bytes"),
            )
            .filter(NodeHealthSample.sampled_at >= from_dt, NodeHealthSample.sampled_at <= to_dt)
            .group_by(func.date(NodeHealthSample.sampled_at), NodeHealthSample.node_code)
            .all()
        )
        nodes_by_day: dict[str, dict[str, dict[str, Any]]] = {}
        for row in node_rows:
            day_key = _date_key(getattr(row, "day", None))
            if not day_key:
                continue
            node_code = str(getattr(row, "node_code", "") or "")
            if not node_code:
                continue
            day_bucket = nodes_by_day.setdefault(day_key, {})
            traffic_bytes = int(getattr(row, "traffic_bytes", 0) or 0)
            day_bucket[node_code] = {
                "devices": int(getattr(row, "devices", 0) or 0),
                "traffic_bytes": max(0, traffic_bytes),
                "traffic_gb": round(max(0, traffic_bytes) / float(1024**3), 3),
            }

        points = [
            {
                "date": day,
                "registrations": int(registrations_map.get(day, 0)),
                "churn": int(churn_map.get(day, 0)),
                "revenue_stars": int(stars_map.get(day, 0)),
                "revenue_rub": float(rub_map.get(day, 0.0)),
                "nodes": nodes_by_day.get(day, {}),
            }
            for day in days
        ]

        return {
            "from": from_dt.date().isoformat(),
            "to": to_dt.date().isoformat(),
            "points": points,
        }
    finally:
        s.close()


@app.get("/api/reviews")
async def featured_reviews() -> dict:
    s = SessionLocal()
    try:
        rows = s.query(Review).filter_by(is_featured=True).order_by(Review.created_at.desc()).limit(10).all()
        reviews = []
        for row in rows:
            text_value = _normalize_feedback_text(row.text, max_len=500)
            if not text_value:
                continue
            reviews.append(
                {
                    "username": _mask_public_username(row.username),
                    "rating": int(row.rating or 0),
                    "text": text_value,
                    "date": row.created_at.strftime("%d.%m.%Y") if row.created_at else "",
                }
            )
        return {
            "reviews": reviews,
            "updated_at": _utcnow().isoformat() + "Z",
        }
    finally:
        s.close()


@app.get("/api/public/social-proof")
async def public_social_proof(response: Response) -> dict:
    """
    Public aggregate counter for marketing surfaces.
    No personal data is exposed.
    """
    s = SessionLocal()
    try:
        total_users = int(s.query(func.count(User.tg_id)).scalar() or 0)
        active_users = int(s.query(func.count(User.tg_id)).filter(User.is_active == True).scalar() or 0)
        paid_users = int(s.query(func.count(User.tg_id)).filter(func.upper(User.sub_type) == "PAID").scalar() or 0)
        connected_users = max(total_users, active_users)
        response.headers["Cache-Control"] = "public, max-age=60"
        return {
            "connected_users": int(connected_users),
            "total_users": int(total_users),
            "active_users": int(active_users),
            "paid_users": int(paid_users),
            "updated_at": _utcnow().isoformat(),
        }
    finally:
        s.close()


@app.post("/api/events")
async def api_track_event(payload: EventIn, request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    _enforce_beta_rate_limit("events", request, identity=f"tg:{tg_id}")
    event_name = (payload.event_name or "").strip()
    if event_name not in EVENT_WHITELIST:
        raise HTTPException(status_code=400, detail="Unsupported event name")
    event_meta = dict(payload.meta or {})
    if event_name.startswith("promo_"):
        lineage_session = SessionLocal()
        try:
            lineage = validate_commercial_promo_event_lineage(
                lineage_session,
                tg_id=tg_id,
                meta=event_meta,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        finally:
            lineage_session.close()
        if lineage is not None:
            event_meta.update(lineage)
    event_id = track_event(
        tg_id=tg_id,
        event_name=event_name,
        source=(payload.source or "webapp"),
        session_id=payload.session_id,
        meta=event_meta,
        event_id=payload.event_id,
        occurred_at=payload.occurred_at,
        account_id=str(auth_user.get("account_id") or "") or None,
        device_id=str(auth_user.get("device_id") or "") or None,
        platform=payload.platform,
        app_version=payload.app_version,
        build_number=payload.build_number,
        surface=payload.surface or payload.source,
        subsystem=payload.subsystem,
        stage=payload.stage,
        result=payload.result,
        error_category=payload.error_category,
        error_code=payload.error_code,
        retryable=payload.retryable,
        attempt_number=payload.attempt_number,
        retry_after_seconds=payload.retry_after_seconds,
        duration_ms=payload.duration_ms,
        trace_id=payload.trace_id,
        network_class=payload.network_class,
    )
    return {"ok": bool(event_id), "event_id": event_id}


@app.post("/api/funnel/events")
async def api_track_funnel_event(payload: FunnelEventIn, request: Request) -> dict:
    _enforce_beta_rate_limit("events", request, identity=str(payload.session_id or "").strip()[:96])
    event_name = _clean_funnel_slug(payload.event_name, default="")
    if event_name not in FUNNEL_EVENT_WHITELIST:
        raise HTTPException(status_code=400, detail="Unsupported funnel event")
    stage = _clean_funnel_slug(payload.stage, default="site_visit")
    if stage not in FUNNEL_STAGE_WHITELIST:
        raise HTTPException(status_code=400, detail="Unsupported funnel stage")
    session_id = _clean_public_text(payload.session_id, max_len=96)
    if len(session_id) < 8:
        raise HTTPException(status_code=400, detail="Invalid session id")
    touch = normalize_acquisition_touch(
        source=payload.source,
        channel=payload.channel,
        campaign=payload.campaign,
        content=payload.utm_content,
        referral=payload.ref,
        entry_route=payload.entry_route or payload.path or "/",
        referrer=payload.referrer,
    )
    s = SessionLocal()
    try:
        _, row = record_funnel_event(
            s,
            raw_session_id=session_id,
            event_name=event_name,
            stage=stage,
            touch=touch,
            meta=payload.meta,
            now=_utcnow(),
        )
        s.commit()
        event_id = int(row.id)
    except AcquisitionError as exc:
        s.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.code) from exc
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
    return {"ok": True, "event_id": event_id}


@app.post("/api/acquisition/handoffs")
async def api_create_acquisition_handoff(payload: AcquisitionHandoffCreateIn, request: Request) -> dict:
    session_id = _clean_public_text(payload.session_id, max_len=96)
    _enforce_beta_rate_limit("events", request, identity=f"handoff:{session_id}")
    touch = normalize_acquisition_touch(
        source=payload.source,
        channel=payload.channel,
        campaign=payload.campaign,
        content=payload.utm_content,
        referral=payload.ref,
        entry_route=payload.entry_route or "/",
        referrer=payload.referrer,
    )
    s = SessionLocal()
    try:
        handle, handoff = create_acquisition_handoff(
            s,
            raw_session_id=session_id,
            touch=touch,
            purpose=payload.purpose,
            asset=payload.asset,
            now=_utcnow(),
        )
        s.commit()
        return {
            "ok": True,
            "handle": handle,
            "purpose": handoff.purpose,
            "expires_at": handoff.expires_at.isoformat() if handoff.expires_at else None,
        }
    except AcquisitionError as exc:
        s.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.code) from exc
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


@app.post("/api/acquisition/handoffs/consume")
async def api_consume_acquisition_handoff(
    payload: AcquisitionHandoffConsumeIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    purpose = clean_acquisition_slug(payload.purpose, max_len=32)
    if purpose not in {"android_install", "windows_install", "account_continue", "telegram_continue"}:
        raise HTTPException(status_code=400, detail="invalid_handoff_purpose")
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == tg_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        consume_acquisition_handoff(
            s,
            raw_handle=payload.handle,
            expected_purpose=purpose,
            bound_tg_id=tg_id,
            bound_account_id=str(getattr(user, "account_id", "") or "") or None,
            now=_utcnow(),
        )
        s.commit()
        return {"ok": True, "bound": True}
    except AcquisitionError as exc:
        s.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.code) from exc
    except HTTPException:
        s.rollback()
        raise
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


@app.post("/api/connect/confirm")
async def api_connect_confirm(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    event_id = track_event(tg_id=tg_id, event_name="connected_ok", source="webapp")
    return {"ok": bool(event_id), "event_id": event_id}


@app.post("/api/pay/attempts/start")
async def api_pay_attempt_start(payload: PayAttemptStartIn, request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    plan_code = (payload.plan_code or "").strip().lower()
    if plan_code not in API_PLAN_PRICES:
        raise HTTPException(status_code=400, detail="Unknown plan")
    price = int(API_PLAN_PRICES[plan_code])
    row = start_attempt(
        tg_id=tg_id,
        source=(payload.source or "webapp"),
        plan_code=plan_code,
        amount_stars=price,
        offer_id=payload.offer_id,
        currency="XTR",
    )
    if not row:
        raise HTTPException(status_code=500, detail="Unable to create pay attempt")
    bot_link = f"https://t.me/{BOT_USERNAME}?start=pay" if BOT_USERNAME else ""
    track_event(
        tg_id=tg_id,
        event_name="clicked_pay",
        source=(payload.source or "webapp"),
        meta={"attempt_id": int(row.id), "plan_code": plan_code, "price_stars": price, "offer_id": payload.offer_id},
    )
    return {"ok": True, "attempt_id": int(row.id), "plan_code": plan_code, "amount_stars": price, "pay_url": bot_link}


@app.get("/api/offers/active")
async def api_active_offer(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    return {"offer": _active_offer_payload(tg_id)}


@app.post("/api/offers/{offer_id}/accept")
async def api_accept_offer(offer_id: int, request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    ok = accept_offer(offer_id=int(offer_id), tg_id=tg_id)
    if ok:
        track_event(tg_id=tg_id, event_name="clicked_pay", source="offer", meta={"offer_id": int(offer_id)})
    return {"ok": bool(ok)}


@app.get("/api/points")
async def api_points(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    avail, expiring_soon = available_points(tg_id=tg_id)
    tier = referral_tier_snapshot(tg_id=tg_id)
    max_preview = preview_redeemable_points(tg_id=tg_id, plan_price_stars=API_PLAN_PRICES["1_month"], first_purchase_discount_pct=0.20)
    return {
        "tg_id": tg_id,
        "available_points": int(avail),
        "expiring_soon_points": int(expiring_soon),
        "monthly_cap": int(POINTS_MONTHLY_CAP),
        "points_expiry_days": int(POINTS_EXPIRY_DAYS),
        "tier": tier,
        "preview": {
            "plan_price_stars": API_PLAN_PRICES["1_month"],
            "redeemable_points": int(max_preview.redeemable_points),
            "max_points_by_plan_cap": int(max_preview.max_points_by_plan_cap),
            "max_points_by_total_cap": int(max_preview.max_points_by_total_cap),
        },
    }


@app.get("/api/network/probe")
async def api_network_probe(size_mb: int = Query(default=2, ge=1, le=3)) -> Response:
    size = int(size_mb) * 1024 * 1024
    payload = b"0" * size
    return Response(
        content=payload,
        media_type="application/octet-stream",
        headers={
            "Cache-Control": "no-store",
            "Content-Length": str(size),
            "X-Probe-Size-MB": str(int(size_mb)),
        },
    )


@app.get("/api/user/{tg_id}")
async def user_data(
    tg_id: int,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
    x_portal_carrier: str = Header(default=""),
) -> dict:
    auth_user = _require_user_access(target_tg_id=tg_id, x_telegram_init_data=x_telegram_init_data, request=request)

    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        downgraded = _maybe_downgrade_expired_to_free(s, user)
        if downgraded:
            try:
                s.refresh(user)
            except Exception:
                pass
        _ensure_free_cycle_state_persisted(s, user)

        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        subscription_url = ""
        if user.sub_token:
            subscription_url = build_subscription_url(str(user.sub_token or ""))

        # active check (DB-first)
        is_active = bool(user.is_active)
        if user.expiry_at and user.expiry_at < _utcnow():
            is_active = False

        # optional legacy usage
        usage = await _get_panel_usage_legacy(tg_id)
        if usage and not usage.get("enable", True):
            is_active = False

        segment = _plan_segment(user)
        family_slots = _family_slots_for_user(s, tg_id)
        points_available, points_expiring_soon = available_points(tg_id=tg_id)
        runtime = await _get_user_runtime_summary(s=s, user=user, nodes=nodes_for_user)
        runtime_used_bytes = int(runtime.get("traffic_total_bytes", 0) or 0)
        legacy_used_bytes = int(usage["used_bytes"] or 0) if usage else 0
        traffic_source = "panel_runtime" if runtime.get("panel_state") == "ok" and (runtime_used_bytes > 0 or int(runtime.get("known_nodes", 0) or 0) > 0) else "legacy_panel" if usage else "unavailable"
        used_bytes = runtime_used_bytes if traffic_source == "panel_runtime" else legacy_used_bytes
        access_policy = _build_reconciled_access_policy(
            session=s,
            user=user,
            used_bytes=used_bytes,
            source=traffic_source,
        )
        setattr(user, "_free_soft_mode_active", bool(access_policy["soft_mode_active"]))
        total_gb = _plan_total_gb(user)
        used_gb = round((used_bytes / (1024**3)), 3) if used_bytes else 0
        policy_remaining_gb = access_policy.get("traffic_remaining_gb")
        remaining_gb = float(policy_remaining_gb) if policy_remaining_gb is not None else 0.0
        referral_code = (user.referral_code or "").strip()
        channel_link = f"https://t.me/{PUBLIC_CHANNEL}" if PUBLIC_CHANNEL else ""
        support_link = f"https://t.me/{SUPPORT_USERNAME}" if SUPPORT_USERNAME else ""
        role_admin = _auth_user_can_admin_account(auth_user=auth_user, user=user)
        channel_claimed_at = _safe_iso(getattr(user, "channel_bonus_claimed_at", None))
        opening_bonus_claimed = _has_campaign_mark(
            s,
            tg_id=tg_id,
            campaign_key=OPENING_PREMIUM_CAMPAIGN_KEY,
        )
        can_claim_channel_bonus = bool(
            PUBLIC_CHANNEL
            and not channel_claimed_at
            and not opening_bonus_claimed
            and bool(getattr(user, "tos_accepted", False))
            and (user.sub_type or "").upper() != "MANUAL"
        )
        free_speed_kbps = _effective_free_speed_kbps(user)
        free_speed_mbps = int(round((free_speed_kbps * 8) / 1000)) if (user.sub_type or "").upper() == "FREE" else None
        is_channel_subscriber = _user_has_channel_subscriber_mark(user)
        speed_bump_active = bool(
            CHANNEL_SPEED_BUMP_ENABLED
            and (user.sub_type or "").upper() == "FREE"
            and free_speed_kbps < int(FREE_SPEED_LIMIT_KBPS)
        )
        devices_payload = _build_app_device_rows(user)
        account_id = str(auth_user.get("account_id") or getattr(user, "account_id", "") or "").strip()
        experience = account_experience_service.build_experience_snapshot(
            s,
            account_id=account_id,
            app_identity_known=bool(str(getattr(user, "app_install_id", "") or "").strip()),
        )
        client_policy = app_first_service.build_client_policy(
            session=s,
            user=user,
            install_id=str(getattr(user, "app_install_id", "") or "").strip() or None,
            carrier=_request_carrier_header(x_portal_carrier),
        )
        linked_identities = _linked_identities_payload(s=s, user=user, auth_user=auth_user)
        linked_email_payload = linked_identities.get("email") if isinstance(linked_identities, dict) else None

        return {
            "tg_id": tg_id,
            "username": user.username or auth_user.get("username"),
            "account_id": str(tg_id),
            "display_name": str(getattr(user, "display_name", "") or "").strip() or None,
            "email": (linked_email_payload or {}).get("email") if isinstance(linked_email_payload, dict) else None,
            "device_name": _normalize_app_device_name(
                getattr(user, "app_device_name", None) or getattr(user, "display_name", None),
            ),
            "subscription_url": subscription_url,
            "is_active": is_active,
            "is_admin": role_admin,
            "sub_type": user.sub_type,
            "current_plan_code": str(getattr(user, "current_plan_code", "") or ""),
            "access_state": str(access_policy["access_state"]),
            "segment": segment,
            "expiry_at": user.expiry_at.isoformat() if user.expiry_at else None,
            "traffic_policy": access_policy["traffic_policy"],
            "traffic_limit_gb": access_policy["traffic_limit_gb"],
            "traffic_remaining_gb": access_policy["traffic_remaining_gb"],
            "next_reset_at": access_policy["next_reset_at"],
            "soft_mode_active": bool(access_policy["soft_mode_active"]),
            "free_profile_state": str(access_policy["free_profile_state"]),
            "free_profile_active_role": str(access_policy["free_profile_active_role"]),
            "free_profile_job_id": access_policy.get("free_profile_job_id"),
            "free_profile_error_code": access_policy.get("free_profile_error_code"),
            "limits": {
                "device_limit": _plan_device_limit(user) + family_slots,
                "total_gb": total_gb,
                "speed_mbps": free_speed_mbps,
            },
            "family_slots": int(family_slots),
            "nodes": [
                {"code": n.code, "name": n.name, "host": n.host, "port": n.vless_port, "enabled": True}
                for n in nodes_for_user
            ],
            "devices": devices_payload,
            "last_ip": str(getattr(user, "app_last_ip", "") or "").strip() or None,
            "linked_telegram": {
                "id": _linked_telegram_id(user) or None,
                "username": str(getattr(user, "linked_telegram_username", "") or "").strip() or None,
            },
            "client_policy": client_policy,
            "linked_identities": linked_identities,
            "free_caps": _free_caps_payload(user=user, access_policy=access_policy),
            "redeem_eligibility": _redeem_eligibility_payload(user=user, access_policy=access_policy),
            "promo_slots": _promo_slots_payload_for_surface(
                s=s,
                surface="webapp",
                access_state=str(access_policy.get("access_state") or ""),
                user=user,
            ),
            "hidden_transport_matrix": _hidden_transport_matrix_payload(nodes=nodes_for_user, client_policy=client_policy),
            "location_matrix": _location_matrix_payload(user=user, nodes=nodes_for_user, client_policy=client_policy),
            "sync": {
                "app_identity_known": bool(str(getattr(user, "app_install_id", "") or "").strip()),
                "telegram_linked": bool(_linked_telegram_id(user)),
                "subscription_ready": bool(str(getattr(user, "sub_token", "") or "").strip()),
                "device_count": int(len(devices_payload)),
                "connected_once": experience["first_connection"]["state"] != "none",
                "first_connected_at": (
                    experience["first_connection"]["verified_at"]
                    or experience["first_connection"]["reported_at"]
                ),
            },
            "experience": experience,
            "traffic": {
                "used_gb": used_gb,
                "used_bytes": int(used_bytes),
                "total_gb": total_gb,
                "remaining_gb": remaining_gb,
                "source": traffic_source,
                "policy": access_policy["traffic_policy"],
            },
            "connections": {
                "status": str(runtime.get("status") or "unknown"),
                "active_connections": int(runtime.get("active_connections", 0) or 0),
                "active_users_estimate": int(runtime.get("active_users_estimate", runtime.get("active_connections", 0)) or 0),
                "active_users_source": str(
                    runtime.get("active_users_source") or runtime.get("active_connections_source") or "none"
                ),
                "active_nodes": int(runtime.get("active_nodes", 0) or 0),
                "known_nodes": int(runtime.get("known_nodes", 0) or 0),
                "last_online_at": runtime.get("last_online_at"),
                "last_online_age_seconds": runtime.get("last_online_age_seconds"),
                "source": "panel_runtime" if runtime.get("panel_state") == "ok" else "unavailable",
            },
            "support": {
                "username": SUPPORT_USERNAME,
                "link": support_link,
                "new_ticket_link": f"{support_link}?start=ticket_new" if support_link else "",
            },
            "bonuses": {
                "wheel": {
                    "last_spin_at": _safe_iso(user.last_wheel_spin),
                    "streak_months": int(user.streak_months or 0),
                },
                "referral_count": int(user.referral_count or 0),
                "channel_bonus": {
                    "premium_days": int(CHANNEL_PREMIUM_DAYS),
                    "claimed_at": channel_claimed_at,
                    "can_claim": can_claim_channel_bonus,
                },
                "opening_bonus": {
                    "premium_days": int(OPENING_PREMIUM_DAYS),
                    "claimed": bool(opening_bonus_claimed),
                },
            },
            "points": {
                "available": int(points_available),
                "expiring_soon": int(points_expiring_soon),
                "monthly_cap": 300,
                "expires_days": 90,
            },
            "referral": {
                "code": referral_code,
                "link": (
                    f"https://t.me/{BOT_USERNAME}?start=ref_{referral_code}"
                    if referral_code and BOT_USERNAME
                    else ""
                ),
                "bonus_days": REFERRAL_BONUS_DAYS,
            },
            "channel": {
                "username": PUBLIC_CHANNEL,
                "link": channel_link,
                "subscriber": bool(is_channel_subscriber),
                "speed_bump_active": speed_bump_active,
            },
            "actions": {
                "open_helpbot": support_link,
                "open_channel": channel_link,
                "pay_via_bot": _checkout_url_for_user(
                    tg_id=tg_id,
                    plan_code=str(getattr(user, "current_plan_code", "") or ""),
                    source="bot",
                ),
            },
            "active_offer": _active_offer_payload(tg_id),
            "free_cycle": {
                "next_reset_at": _safe_iso(getattr(user, "free_cycle_next_reset_at", None))
                if (user.sub_type or "").upper() == "FREE"
                else None,
            },
            "features": {
                "haptic": bool(WEBAPP_ENABLE_HAPTIC),
                "lottie": bool(WEBAPP_ENABLE_LOTTIE),
            },
        }
    finally:
        s.close()


@app.get("/api/dashboard")
async def dashboard_snapshot(
    request: Request,
    x_telegram_init_data: str = Header(default=""),
    x_portal_carrier: str = Header(default=""),
) -> DashboardResponse:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        _maybe_downgrade_expired_to_free(s, user)
        _ensure_free_cycle_state_persisted(s, user)
        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        runtime = await _get_user_runtime_summary(s=s, user=user, nodes=nodes_for_user)
        usage = await _get_panel_usage_legacy(tg_id)
        runtime_used_bytes = int(runtime.get("traffic_total_bytes", 0) or 0)
        legacy_used_bytes = int(usage["used_bytes"] or 0) if usage else 0
        traffic_source = "panel_runtime" if runtime.get("panel_state") == "ok" and (runtime_used_bytes > 0 or int(runtime.get("known_nodes", 0) or 0) > 0) else "legacy_panel" if usage else "unavailable"
        used_bytes = runtime_used_bytes if traffic_source == "panel_runtime" else legacy_used_bytes
        access_policy = _build_reconciled_access_policy(
            session=s,
            user=user,
            used_bytes=used_bytes,
            source=traffic_source,
        )
        setattr(user, "_free_soft_mode_active", bool(access_policy["soft_mode_active"]))
        total_gb = float(_plan_total_gb(user))
        used_gb = round((used_bytes / (1024**3)), 3) if used_bytes else 0.0
        policy_remaining_gb = access_policy.get("traffic_remaining_gb")
        remaining = float(policy_remaining_gb) if policy_remaining_gb is not None else 0.0
        expiry = user.expiry_at
        active = bool(user.is_active and expiry and expiry > _utcnow())
        segment = _plan_segment(user)
        family_slots = _family_slots_for_user(s, tg_id)
        points_available, points_expiring_soon = available_points(tg_id=tg_id)
        sub_url = ""
        if user.sub_token:
            sub_url = build_subscription_url(str(user.sub_token or ""))
        client_policy = app_first_service.build_client_policy(
            session=s,
            user=user,
            install_id=str(getattr(user, "app_install_id", "") or "").strip() or None,
            carrier=_request_carrier_header(x_portal_carrier),
        )

        return DashboardResponse(
            tg_id=tg_id,
            sub_type=str(user.sub_type or ""),
            current_plan_code=str(getattr(user, "current_plan_code", "") or ""),
            access_state=str(access_policy["access_state"]),
            is_active=active,
            expiry_at=_safe_iso(expiry),
            used_gb=float(used_gb),
            total_gb=float(total_gb),
            remaining_gb=float(remaining),
            traffic_policy=access_policy["traffic_policy"],
            traffic_limit_gb=access_policy["traffic_limit_gb"],
            traffic_remaining_gb=access_policy["traffic_remaining_gb"],
            next_reset_at=access_policy["next_reset_at"],
            soft_mode_active=bool(access_policy["soft_mode_active"]),
            free_profile_state=str(access_policy["free_profile_state"]),
            free_profile_active_role=str(access_policy["free_profile_active_role"]),
            free_profile_job_id=access_policy.get("free_profile_job_id"),
            free_profile_error_code=access_policy.get("free_profile_error_code"),
            active_sessions=int(runtime.get("active_connections", 0) or 0),
            active_sessions_source=str(runtime.get("active_connections_source") or "none"),
            device_limit=int(_plan_device_limit(user) + family_slots),
            speed_limit_mbps=(
                int(round((_effective_free_speed_kbps(user) * 8) / 1000))
                if (user.sub_type or "").upper() == "FREE"
                else None
            ),
            free_next_reset_at=(
                _safe_iso(getattr(user, "free_cycle_next_reset_at", None))
                if (user.sub_type or "").upper() == "FREE"
                else None
            ),
            family_slots=int(family_slots),
            subscription_url=sub_url,
            segment=segment,
            client_policy=client_policy,
            linked_identities=_linked_identities_payload(s=s, user=user, auth_user=auth_user),
            free_caps=_free_caps_payload(user=user, access_policy=access_policy),
            redeem_eligibility=_redeem_eligibility_payload(user=user, access_policy=access_policy),
            promo_slots=_promo_slots_payload_for_surface(
                s=s,
                surface="webapp",
                access_state=str(access_policy.get("access_state") or ""),
                user=user,
            ),
            hidden_transport_matrix=_hidden_transport_matrix_payload(nodes=nodes_for_user, client_policy=client_policy),
            location_matrix=_location_matrix_payload(user=user, nodes=nodes_for_user, client_policy=client_policy),
            connection_snapshot={
                "status": str(runtime.get("status") or "unknown"),
                "active_connections": int(runtime.get("active_connections", 0) or 0),
                "active_users_estimate": int(runtime.get("active_users_estimate", runtime.get("active_connections", 0)) or 0),
                "active_users_source": str(
                    runtime.get("active_users_source") or runtime.get("active_connections_source") or "none"
                ),
                "active_nodes": int(runtime.get("active_nodes", 0) or 0),
                "known_nodes": int(runtime.get("known_nodes", 0) or 0),
                "last_online_at": runtime.get("last_online_at"),
                "last_online_age_seconds": runtime.get("last_online_age_seconds"),
                "source": "panel_runtime" if runtime.get("panel_state") == "ok" else "unavailable",
            },
            active_offer=_active_offer_payload(tg_id),
            points={
                "available": int(points_available),
                "expiring_soon": int(points_expiring_soon),
                "monthly_cap": 300,
                "expires_days": 90,
            },
            features={"haptic": bool(WEBAPP_ENABLE_HAPTIC), "lottie": bool(WEBAPP_ENABLE_LOTTIE)},
        )
    finally:
        s.close()


def _release_manifest_identity() -> ClientReleaseManifestIdentity | None:
    schema_version = int(getattr(Settings, "APP_RELEASE_SCHEMA_VERSION", 0) or 0)
    candidate_label = str(
        getattr(Settings, "APP_RELEASE_CANDIDATE_LABEL", "") or ""
    ).strip()
    handoff_sha256 = str(
        getattr(Settings, "APP_RELEASE_HANDOFF_SHA256", "") or ""
    ).strip().lower()
    artifact_set_sha256 = str(
        getattr(Settings, "APP_RELEASE_ARTIFACT_SET_SHA256", "") or ""
    ).strip().lower()
    core_version = str(
        getattr(Settings, "APP_RELEASE_CORE_VERSION", "") or ""
    ).strip()
    core_desktop_abi = int(
        getattr(Settings, "APP_RELEASE_CORE_DESKTOP_ABI", 0) or 0
    )
    core_android_package = str(
        getattr(Settings, "APP_RELEASE_CORE_ANDROID_PACKAGE", "") or ""
    ).strip()
    release_version = str(
        getattr(Settings, "APP_ANDROID_VERSION", "") or ""
    ).strip()
    if (
        schema_version != 2
        or re.fullmatch(r"pokrov-[0-9]+\.[0-9]+\.[0-9]+[A-Za-z0-9._+-]*", candidate_label)
        is None
        or re.fullmatch(r"[0-9a-f]{64}", handoff_sha256) is None
        or re.fullmatch(r"[0-9a-f]{64}", artifact_set_sha256) is None
        or re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?", core_version)
        is None
        or core_desktop_abi < 1
        or core_android_package != "space.pokrov.core"
        or str(getattr(Settings, "APP_WINDOWS_VERSION", "") or "").strip()
        != release_version
        or candidate_label != f"pokrov-{release_version}"
    ):
        return None
    return ClientReleaseManifestIdentity(
        schema_version=2,
        candidate_label=candidate_label,
        handoff_sha256=handoff_sha256,
        artifact_set_sha256=artifact_set_sha256,
        core_version=core_version,
        core_desktop_abi=core_desktop_abi,
        core_android_package=core_android_package,
    )


def _build_client_apps_response(
    *,
    platform: str,
    current_version: str,
    channel: str,
    android_abi: str = "",
) -> ClientAppsResponse:
    release_channel = str(
        channel or getattr(Settings, "APP_RELEASE_CHANNEL", "stable") or "stable"
    ).strip().lower() or "stable"
    requested_platform = str(platform or "").strip().lower()
    android_url = _safe_public_url(Settings.APP_ANDROID_APK_URL)
    android_arm64_url = _safe_public_url(getattr(Settings, "APP_ANDROID_APK_ARM64_URL", ""))
    android_armeabi_v7a_url = _safe_public_url(getattr(Settings, "APP_ANDROID_APK_ARMEABI_V7A_URL", ""))
    android_x86_64_url = _safe_public_url(getattr(Settings, "APP_ANDROID_APK_X86_64_URL", ""))
    android_universal_url = _safe_public_url(getattr(Settings, "APP_ANDROID_APK_UNIVERSAL_URL", ""))
    windows_url = _safe_public_url(Settings.APP_WINDOWS_EXE_URL)
    rollout_session = SessionLocal()
    try:
        try:
            android_rollout = public_client_rollout_policy(
                rollout_session,
                platform="android",
                configured_version=getattr(Settings, "APP_ANDROID_VERSION", ""),
                configured_min_supported_version=getattr(
                    Settings, "APP_ANDROID_MIN_SUPPORTED_VERSION", ""
                ),
            )
            windows_rollout = public_client_rollout_policy(
                rollout_session,
                platform="windows",
                configured_version=getattr(Settings, "APP_WINDOWS_VERSION", ""),
                configured_min_supported_version=getattr(
                    Settings, "APP_WINDOWS_MIN_SUPPORTED_VERSION", ""
                ),
            )
        except OperatorReleaseError:
            android_rollout = {
                "rollout_percent": 0,
                "min_supported_version": getattr(
                    Settings, "APP_ANDROID_MIN_SUPPORTED_VERSION", ""
                ),
            }
            windows_rollout = {
                "rollout_percent": 0,
                "min_supported_version": getattr(
                    Settings, "APP_WINDOWS_MIN_SUPPORTED_VERSION", ""
                ),
            }
    finally:
        rollout_session.close()
    android_variants = [
        ClientAndroidApkVariant(
            abi="arm64-v8a",
            label="Android ARM64",
            url=android_arm64_url,
            sha256=str(getattr(Settings, "APP_ANDROID_ARM64_SHA256", "") or "").strip(),
            size=max(0, int(getattr(Settings, "APP_ANDROID_ARM64_SIZE_BYTES", 0) or 0)),
        ),
        ClientAndroidApkVariant(
            abi="armeabi-v7a",
            label="Android ARMv7",
            url=android_armeabi_v7a_url,
            sha256=str(getattr(Settings, "APP_ANDROID_ARMEABI_V7A_SHA256", "") or "").strip(),
            size=max(0, int(getattr(Settings, "APP_ANDROID_ARMEABI_V7A_SIZE_BYTES", 0) or 0)),
        ),
        ClientAndroidApkVariant(
            abi="universal",
            label="Android Universal",
            url=android_universal_url,
            sha256=str(getattr(Settings, "APP_ANDROID_UNIVERSAL_SHA256", "") or "").strip(),
            size=max(0, int(getattr(Settings, "APP_ANDROID_UNIVERSAL_SIZE_BYTES", 0) or 0)),
        ),
        ClientAndroidApkVariant(
            abi="x86_64",
            label="Android x86_64",
            url=android_x86_64_url,
            sha256=str(getattr(Settings, "APP_ANDROID_X86_64_SHA256", "") or "").strip(),
            size=max(0, int(getattr(Settings, "APP_ANDROID_X86_64_SIZE_BYTES", 0) or 0)),
        ),
    ]
    android_variants = [variant for variant in android_variants if variant.url]
    requested_android_abi = str(android_abi or "").strip().lower()
    selected_android_variant = next(
        (
            variant
            for variant in android_variants
            if variant.abi
            == (requested_android_abi or "arm64-v8a")
            and variant.abi != "universal"
        ),
        None,
    )
    selected_android_url = selected_android_variant.url if selected_android_variant else ""
    selected_android_sha256 = selected_android_variant.sha256 if selected_android_variant else ""
    selected_android_size = selected_android_variant.size if selected_android_variant else 0
    if not requested_android_abi and not selected_android_url:
        selected_android_url = android_url or _safe_public_url(Settings.APP_ANDROID_MIRROR_URL)
        selected_android_sha256 = str(getattr(Settings, "APP_ANDROID_SHA256", "") or "").strip()
        selected_android_size = max(0, int(getattr(Settings, "APP_ANDROID_SIZE_BYTES", 0) or 0))
    android_update = _client_app_update_info(
        platform="android",
        requested_platform=requested_platform,
        current_version=current_version,
        channel=release_channel,
        latest_version=getattr(Settings, "APP_ANDROID_VERSION", ""),
        min_supported_version=str(android_rollout["min_supported_version"]),
        url=selected_android_url,
        sha256=selected_android_sha256,
        size=selected_android_size,
        release_notes=getattr(Settings, "APP_ANDROID_RELEASE_NOTES", ""),
        release_notes_url=getattr(Settings, "APP_ANDROID_RELEASE_NOTES_URL", ""),
        published_at=getattr(Settings, "APP_ANDROID_PUBLISHED_AT", ""),
        rollout_percent=int(android_rollout["rollout_percent"]),
    )
    compatibility_android_url = (
        selected_android_url
        if requested_android_abi
        else selected_android_url or android_url
    )
    compatibility_android_sha256 = (
        selected_android_sha256
        if requested_android_abi or selected_android_url
        else str(getattr(Settings, "APP_ANDROID_SHA256", "") or "").strip()
    )
    compatibility_android_size = (
        selected_android_size
        if requested_android_abi or selected_android_url
        else max(0, int(getattr(Settings, "APP_ANDROID_SIZE_BYTES", 0) or 0))
    )
    windows_update = _client_app_update_info(
        platform="windows",
        requested_platform=requested_platform,
        current_version=current_version,
        channel=release_channel,
        latest_version=getattr(Settings, "APP_WINDOWS_VERSION", ""),
        min_supported_version=str(windows_rollout["min_supported_version"]),
        url=windows_url or _safe_public_url(Settings.APP_WINDOWS_MIRROR_URL),
        sha256=getattr(Settings, "APP_WINDOWS_SHA256", ""),
        size=int(getattr(Settings, "APP_WINDOWS_SIZE_BYTES", 0) or 0),
        release_notes=getattr(Settings, "APP_WINDOWS_RELEASE_NOTES", ""),
        release_notes_url=getattr(Settings, "APP_WINDOWS_RELEASE_NOTES_URL", ""),
        published_at=getattr(Settings, "APP_WINDOWS_PUBLISHED_AT", ""),
        rollout_percent=int(windows_rollout["rollout_percent"]),
    )
    return ClientAppsResponse(
        android=ClientAndroidApps(
            # Direct distribution is outside app stores; keep the compatibility field empty.
            play_url="",
            apk_url=compatibility_android_url,
            mirror_url=_safe_public_url(Settings.APP_ANDROID_MIRROR_URL),
            apk_variants=android_variants,
            version=str(getattr(Settings, "APP_ANDROID_VERSION", "") or "").strip(),
            sha256=compatibility_android_sha256,
            size=compatibility_android_size,
            release_notes=str(getattr(Settings, "APP_ANDROID_RELEASE_NOTES", "") or "").strip()[:1000],
            release_notes_url=_safe_public_url(getattr(Settings, "APP_ANDROID_RELEASE_NOTES_URL", "")),
            published_at=str(getattr(Settings, "APP_ANDROID_PUBLISHED_AT", "") or "").strip(),
            update=android_update,
        ),
        windows=ClientWindowsApps(
            exe_url=windows_url,
            mirror_url=_safe_public_url(Settings.APP_WINDOWS_MIRROR_URL),
            version=str(getattr(Settings, "APP_WINDOWS_VERSION", "") or "").strip(),
            sha256=str(getattr(Settings, "APP_WINDOWS_SHA256", "") or "").strip(),
            size=max(0, int(getattr(Settings, "APP_WINDOWS_SIZE_BYTES", 0) or 0)),
            release_notes=str(getattr(Settings, "APP_WINDOWS_RELEASE_NOTES", "") or "").strip()[:1000],
            release_notes_url=_safe_public_url(getattr(Settings, "APP_WINDOWS_RELEASE_NOTES_URL", "")),
            published_at=str(getattr(Settings, "APP_WINDOWS_PUBLISHED_AT", "") or "").strip(),
            update=windows_update,
        ),
        release_manifest=_release_manifest_identity(),
        docs_url=_safe_public_url(Settings.APP_DOCS_URL),
        updated_at=f"{_utcnow().replace(microsecond=0).isoformat()}Z",
        update_check={
            "requested_platform": requested_platform or None,
            "android_abi": requested_android_abi or None,
            "current_version": str(current_version or "").strip() or None,
            "channel": release_channel,
            "mode": "prompt",
            "silent_update": False,
        },
    )


_PUBLIC_CLIENT_ASSET_FILENAMES = {
    "arm64-v8a": "pokrov-android-arm64-v8a.apk",
    "armeabi-v7a": "pokrov-android-armeabi-v7a.apk",
    "universal": "pokrov-android-universal.apk",
    "x86_64": "pokrov-android-x86_64.apk",
    "windows": "pokrov-windows-setup-x64.exe",
}


def _safe_public_client_asset_url(value: str, *, expected_filename: str) -> str:
    raw = str(value or "").strip()
    try:
        parsed = urlparse(raw)
    except ValueError:
        return ""
    parts = parsed.path.split("/")
    if (
        parsed.scheme != "https"
        or (parsed.hostname or "").lower() != "github.com"
        or parsed.port is not None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or len(parts) != 7
        or parts[1:5] != ["Kiwunaka", "pokrov", "releases", "download"]
        or not re.fullmatch(r"v[0-9A-Za-z][0-9A-Za-z._-]{0,63}", parts[5])
        or parts[6] != expected_filename
    ):
        return ""
    return raw


def _safe_public_release_notes_url(value: str) -> str:
    raw = str(value or "").strip()
    try:
        parsed = urlparse(raw)
    except ValueError:
        return ""
    parts = parsed.path.split("/")
    if (
        parsed.scheme != "https"
        or (parsed.hostname or "").lower() != "github.com"
        or parsed.port is not None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or len(parts) != 6
        or parts[1:5] != ["Kiwunaka", "pokrov", "releases", "tag"]
        or not re.fullmatch(r"v[0-9A-Za-z][0-9A-Za-z._-]{0,63}", parts[5])
    ):
        return ""
    return raw


def _safe_public_release_sha256(value: str) -> str:
    raw = str(value or "").strip().upper()
    return raw if re.fullmatch(r"[0-9A-F]{64}", raw) else ""


def _safe_public_release_size(value: int) -> int:
    size = max(0, int(value or 0))
    return size if size <= 10 * 1024 * 1024 * 1024 else 0


def _public_client_apps_projection(
    source: ClientAppsResponse,
    *,
    android_abi: str = "",
) -> ClientAppsResponse:
    variants: list[ClientAndroidApkVariant] = []
    for variant in source.android.apk_variants:
        expected_filename = _PUBLIC_CLIENT_ASSET_FILENAMES.get(str(variant.abi))
        if not expected_filename:
            continue
        url = _safe_public_client_asset_url(variant.url, expected_filename=expected_filename)
        sha256 = _safe_public_release_sha256(variant.sha256)
        size = _safe_public_release_size(variant.size)
        if not url or not sha256 or not size:
            continue
        variants.append(
            ClientAndroidApkVariant(
                abi=variant.abi,
                label=variant.label,
                url=url,
                sha256=sha256,
                size=size,
            )
        )
    requested_android_abi = str(android_abi or "").strip().lower()
    primary = next(
        (
            variant
            for variant in variants
            if variant.abi == (requested_android_abi or "arm64-v8a")
            and variant.abi != "universal"
        ),
        None,
    )

    windows_url = _safe_public_client_asset_url(
        source.windows.exe_url,
        expected_filename=_PUBLIC_CLIENT_ASSET_FILENAMES["windows"],
    )
    windows_sha256 = _safe_public_release_sha256(source.windows.sha256)
    windows_size = _safe_public_release_size(source.windows.size)
    if not windows_url or not windows_sha256 or not windows_size:
        windows_url = ""
        windows_sha256 = ""
        windows_size = 0

    android_url = primary.url if primary else ""
    android_sha256 = primary.sha256 if primary else ""
    android_size = primary.size if primary else 0
    android_update = source.android.update
    windows_update = source.windows.update
    return ClientAppsResponse(
        android=ClientAndroidApps(
            play_url="",
            apk_url=android_url,
            mirror_url="",
            apk_variants=variants,
            version=source.android.version,
            sha256=android_sha256,
            size=android_size,
            release_notes=source.android.release_notes,
            release_notes_url=_safe_public_release_notes_url(source.android.release_notes_url),
            published_at=source.android.published_at,
            update=ClientAppUpdateInfo(
                platform=android_update.platform,
                channel=android_update.channel,
                latest_version=android_update.latest_version,
                min_supported_version=android_update.min_supported_version,
                update_policy=android_update.update_policy if android_url else "none",
                url=android_url,
                sha256=android_sha256,
                size=android_size,
                release_notes=android_update.release_notes,
                release_notes_url=_safe_public_release_notes_url(android_update.release_notes_url),
                published_at=android_update.published_at,
                rollout_percent=android_update.rollout_percent,
                force_after=None,
            ),
        ),
        windows=ClientWindowsApps(
            exe_url=windows_url,
            mirror_url="",
            version=source.windows.version,
            sha256=windows_sha256,
            size=windows_size,
            release_notes=source.windows.release_notes,
            release_notes_url=_safe_public_release_notes_url(source.windows.release_notes_url),
            published_at=source.windows.published_at,
            update=ClientAppUpdateInfo(
                platform=windows_update.platform,
                channel=windows_update.channel,
                latest_version=windows_update.latest_version,
                min_supported_version=windows_update.min_supported_version,
                update_policy=windows_update.update_policy if windows_url else "none",
                url=windows_url,
                sha256=windows_sha256,
                size=windows_size,
                release_notes=windows_update.release_notes,
                release_notes_url=_safe_public_release_notes_url(windows_update.release_notes_url),
                published_at=windows_update.published_at,
                rollout_percent=windows_update.rollout_percent,
                force_after=None,
            ),
        ),
        release_manifest=source.release_manifest,
        docs_url=(
            source.docs_url
            if source.docs_url in {"https://pokrov.space/install/", "https://www.pokrov.space/install/"}
            else ""
        ),
        updated_at=source.updated_at,
        update_check=source.update_check,
    )


@app.get("/api/client/apps")
async def client_apps(
    request: Request,
    platform: str = Query(default="", max_length=16),
    current_version: str = Query(default="", max_length=48),
    channel: str = Query(default="", max_length=32),
    android_abi: str = Query(default="", max_length=16),
    x_telegram_init_data: str = Header(default=""),
) -> ClientAppsResponse:
    _require_auth_user(x_telegram_init_data, request=request)
    return _build_client_apps_response(
        platform=platform,
        current_version=current_version,
        channel=channel,
        android_abi=android_abi,
    )


@app.get("/api/public/client-apps")
async def public_client_apps(
    response: Response,
    platform: str = Query(default="", max_length=16),
    current_version: str = Query(default="", max_length=48),
    channel: str = Query(default="", max_length=32),
    android_abi: str = Query(default="", max_length=16),
) -> ClientAppsResponse:
    response.headers["Cache-Control"] = "public, max-age=300, stale-if-error=3600"
    return _public_client_apps_projection(
        _build_client_apps_response(
            platform=platform,
            current_version=current_version,
            channel=channel,
            android_abi=android_abi,
        ),
        android_abi=android_abi,
    )


def _current_download_target(kind: str) -> str:
    targets = {
        "android-arm64": getattr(Settings, "APP_ANDROID_APK_ARM64_URL", ""),
        "android-armv7": getattr(Settings, "APP_ANDROID_APK_ARMEABI_V7A_URL", ""),
        "android-universal": getattr(Settings, "APP_ANDROID_APK_UNIVERSAL_URL", ""),
        "android-x86_64": getattr(Settings, "APP_ANDROID_APK_X86_64_URL", ""),
        "windows-x64": getattr(Settings, "APP_WINDOWS_EXE_URL", ""),
    }
    target = _safe_public_url(targets.get(str(kind), ""))
    if not target:
        raise HTTPException(status_code=503, detail="Download temporarily unavailable")
    return target


@app.get("/api/public/downloads/{kind}")
async def public_current_download(kind: str) -> RedirectResponse:
    if kind not in {
        "android-arm64",
        "android-armv7",
        "android-universal",
        "android-x86_64",
        "windows-x64",
    }:
        raise HTTPException(status_code=404, detail="Download not found")
    response = RedirectResponse(_current_download_target(kind), status_code=307)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/api/nodes/status")
async def nodes_status(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        rows = _nodes_for_user(user, enabled_nodes(s), session=s)
        payload: list[dict[str, Any]] = []
        for n in rows:
            ping = _safe_ping(n)
            payload.append(
                NodeStatusResponse(
                    code=str(getattr(n, "code", "")),
                    country=_node_country_name(str(getattr(n, "code", ""))),
                    host=str(getattr(n, "host", "")),
                    ping_ms=ping,
                    port_open=bool(getattr(n, "is_healthy", True)),
                    dns_sni_status="ok" if bool(getattr(n, "is_healthy", True)) else "degraded",
                    is_healthy=bool(getattr(n, "is_healthy", True)),
                    updated_at=_safe_iso(getattr(n, "last_health_at", None)),
                ).model_dump()
            )
        return {"nodes": payload}
    finally:
        s.close()


@app.post("/api/nodes/diagnostics/run")
async def nodes_run_diagnostics(request: Request, x_telegram_init_data: str = Header(default="")) -> NodeDiagnosticsResponse:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    now_ts = time.time()
    last_ts = _diag_rate_limit.get(tg_id, 0.0)
    if now_ts - last_ts < 8.0:
        raise HTTPException(status_code=429, detail="Too many diagnostics requests")
    _diag_rate_limit[tg_id] = now_ts

    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        nodes = _nodes_for_user(user, enabled_nodes(s), session=s)
        healthy = [n for n in nodes if bool(getattr(n, "is_healthy", True))]
    finally:
        s.close()

    ok = bool(healthy) if nodes else False
    return NodeDiagnosticsResponse(
        ok=ok,
        checked_at=_utcnow().isoformat(),
        dns_status="ok" if ok else "degraded",
        sni_status="ok" if ok else "degraded",
        summary="All checks passed" if ok else "Some nodes are degraded",
    )


@app.get("/api/bonuses")
async def bonuses(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        tier = referral_tier_snapshot(tg_id=tg_id)
        channel_status = channel_bonus_service.channel_bonus_status(s, user=user)
        return {
            "tg_id": tg_id,
            "referral_count": int(user.referral_count or 0),
            "referral_code": user.referral_code or "",
            "referral_bonus_days": REFERRAL_BONUS_DAYS,
            "streak_months": int(user.streak_months or 0),
            "last_wheel_spin": _safe_iso(user.last_wheel_spin),
            "channel_bonus_premium_days": int(CHANNEL_PREMIUM_DAYS),
            "channel_bonus_claimed_at": _safe_iso(getattr(user, "channel_bonus_claimed_at", None)),
            "channel": {
                "offer_days": int(channel_status["offer_days"]),
                "claimed_days": int(channel_status["claimed_days"]),
                "claimed": bool(channel_status["claimed"]),
                "claimed_at": _safe_iso(channel_status["claimed_at"]),
                "channel_username": PUBLIC_CHANNEL,
            },
            "opening_bonus_premium_days": int(OPENING_PREMIUM_DAYS),
            "opening_bonus_claimed": _has_campaign_mark(s, tg_id=tg_id, campaign_key=OPENING_PREMIUM_CAMPAIGN_KEY),
            "channel_username": PUBLIC_CHANNEL,
            "points_tier": tier,
        }
    finally:
        s.close()


def _bonus_referral_summary_payload(*, s, user: User, tg_id: int) -> dict[str, Any]:
    referral_code = str(user.referral_code or "").strip()
    referral_link = (
        f"https://t.me/{BOT_USERNAME}?start=ref_{referral_code}"
        if referral_code and BOT_USERNAME
        else ""
    )
    tier = referral_tier_snapshot(tg_id=tg_id)
    account_id = str(user.account_id or "").strip()
    relationships = (
        s.query(ReferralRelationship)
        .filter(ReferralRelationship.referrer_account_id == account_id)
        .order_by(ReferralRelationship.created_at.desc())
        .limit(50)
        .all()
        if account_id
        else []
    )
    activated_count = sum(1 for row in relationships if row.friend_granted_at is not None)
    paid_count = sum(1 for row in relationships if row.first_payment_at is not None)
    rewarded_count = sum(1 for row in relationships if row.referrer_granted_at is not None)
    invited_count = max(int(user.referral_count or 0), len(relationships))
    history: list[dict[str, Any]] = []
    for row in relationships[:20]:
        status = "invited"
        if str(row.review_status or "").strip().lower() not in {"", "clear"}:
            status = "review"
        if row.friend_granted_at is not None:
            status = "activated"
        if row.first_payment_at is not None:
            status = "hold" if row.hold_until is not None and row.referrer_granted_at is None else "paid"
        if row.referrer_granted_at is not None:
            status = "rewarded"
        history.append(
            {
                "id": str(row.id),
                "status": status,
                "created_at": _safe_iso(row.created_at),
                "activated_at": _safe_iso(row.friend_granted_at),
                "paid_at": _safe_iso(row.first_payment_at),
                "hold_until": _safe_iso(row.hold_until),
                "rewarded_at": _safe_iso(row.referrer_granted_at),
            }
        )
    return {
        "ok": True,
        "tg_id": tg_id,
        "count": int(user.referral_count or 0),
        "code": referral_code,
        "link": referral_link,
        "bonus_days": REFERRAL_BONUS_DAYS,
        "tier": tier,
        "referral_count": int(user.referral_count or 0),
        "referral_code": referral_code,
        "referral_bonus_days": REFERRAL_BONUS_DAYS,
        "points_tier": tier,
        "conversion": {
            "invited": invited_count,
            "activated": activated_count,
            "paid": paid_count,
            "rewarded": rewarded_count,
            "activation_pct": round((activated_count / invited_count) * 100, 1) if invited_count else 0.0,
            "paid_pct": round((paid_count / invited_count) * 100, 1) if invited_count else 0.0,
        },
        "history": history,
        "privacy": "Имена и аккаунты приглашённых не показываются.",
    }


def _ensure_paid_referral_code_for_summary(*, s, user: User) -> str:
    existing = str(user.referral_code or "").strip()
    if existing:
        return existing
    reward_access = evaluate_active_paid(
        s,
        account_id=str(user.account_id or ""),
        now=_reward_now(),
    )
    if not reward_access.eligible:
        return ""
    code = ensure_referral_code(s=s, user=user)
    s.commit()
    return code


def _bonus_feature_disabled_detail(*, feature: str) -> dict[str, Any]:
    return {
        "code": "bonus_feature_disabled",
        "feature": feature,
        "message": "Feature is disabled until the public app contract and rollout flag are ready",
    }


def _bonus_wheel_config(*, s) -> dict[str, Any] | None:
    row = s.query(AppSetting).filter(AppSetting.key == "wheel_config").first()
    if row is None or not str(row.value_json or "").strip():
        return None
    try:
        raw = json.loads(str(row.value_json))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {"preset": "invalid"}
    return dict(raw) if isinstance(raw, dict) else {"preset": "invalid"}


def _reward_http_error(exc: RewardDomainError) -> HTTPException:
    if isinstance(exc, RewardForbidden):
        return HTTPException(
            status_code=403,
            detail={"code": "active_paid_required"},
        )
    if isinstance(exc, RewardConflict):
        return HTTPException(
            status_code=409,
            detail={
                "code": exc.code,
                "next_spin_at": _safe_iso(exc.next_allowed_at),
                "last_reward_days": exc.last_reward_days,
                "last_discount_pct": exc.last_discount_pct,
            },
        )
    if isinstance(exc, RewardDisabled):
        return HTTPException(
            status_code=403,
            detail={"code": "bonus_feature_disabled", "feature": exc.feature},
        )
    return HTTPException(
        status_code=503,
        detail={"code": "reward_state_unavailable"},
    )


def _ensure_achievement(*, s, tg_id: int, achievement_id: str, now: datetime) -> None:
    aid = str(achievement_id or "").strip()[:50]
    if not aid:
        return
    exists = (
        s.query(Achievement.id)
        .filter(Achievement.tg_id == int(tg_id), Achievement.achievement_id == aid)
        .first()
    )
    if not exists:
        s.add(Achievement(tg_id=int(tg_id), achievement_id=aid, unlocked_at=now))


def _bonus_achievements_payload(
    *,
    s,
    user: User,
    tg_id: int,
    calendar_state: CalendarState,
) -> dict[str, Any]:
    custom_rows = (
        s.query(Achievement)
        .filter(Achievement.tg_id == int(tg_id))
        .order_by(Achievement.unlocked_at.asc(), Achievement.id.asc())
        .limit(50)
        .all()
    )
    custom_ids = {str(row.achievement_id or "") for row in custom_rows}
    experience = account_experience_service.build_experience_snapshot(
        s,
        account_id=str(user.account_id or ""),
        app_identity_known=bool(str(getattr(user, "app_install_id", "") or "").strip()),
    )
    first_tunnel = str((experience.get("first_connection") or {}).get("state") or "") == "verified"
    active_device_count = int(
        s.query(func.count(AccountDevice.id))
        .filter(
            AccountDevice.account_id == str(user.account_id or ""),
            AccountDevice.state == "active",
            AccountDevice.revoked_at.is_(None),
        )
        .scalar()
        or 0
    )
    routing_lesson = (
        s.query(Event.id)
        .filter(
            Event.tg_id == int(tg_id),
            Event.event_name == "routing_lesson_completed",
        )
        .first()
        is not None
    )
    quality_feedback = (
        s.query(ProgramApplication.id)
        .filter(
            ProgramApplication.account_id == str(user.account_id or ""),
            ProgramApplication.kind == "research",
            ProgramApplication.status.in_(("approved", "rewarded")),
        )
        .first()
        is not None
    )
    items = [
        {"id": "first_launch", "title": "Добро пожаловать", "description": "Вы запустили POKROV.", "unlocked": bool(getattr(user, "is_app_user", False))},
        {"id": "first_tunnel", "title": "Под защитой", "description": "Первое защищённое подключение.", "unlocked": first_tunnel},
        {"id": "second_device", "title": "Свои устройства", "description": "POKROV работает на двух устройствах.", "unlocked": active_device_count >= 2},
        {"id": "telegram_bonus", "title": "Вместе с POKROV", "description": "Получен бонус за Telegram-канал.", "unlocked": bool(getattr(user, "channel_bonus_claimed_at", None))},
        {"id": "first_wheel", "title": "Первая удача", "description": "Получен первый приз в рулетке.", "unlocked": "first_wheel" in custom_ids},
        {
            "id": "first_checkin",
            "title": "Первая отметка",
            "description": "Первая отметка сохранена.",
            "unlocked": bool(calendar_state.achievements.get("first_checkin")),
        },
        {
            "id": "streak_7",
            "title": "7 отметок",
            "description": "Семь отметок подряд.",
            "unlocked": bool(calendar_state.achievements.get("streak_7")),
        },
        {"id": "first_referral", "title": "Первый друг", "description": "Друг оплатил POKROV по вашему приглашению.", "unlocked": bool(int(getattr(user, "referral_count", 0) or 0) > 0)},
    ]
    quests = [
        {
            "id": "first_tunnel",
            "title": "Подключиться первый раз",
            "description": "Подключите VPN и дождитесь подтверждённого состояния.",
            "progress": 1 if first_tunnel else 0,
            "target": 1,
            "completed": first_tunnel,
            "verification": "connection_evidence",
            "action_href": "/protection/",
        },
        {
            "id": "second_device",
            "title": "Добавить второе устройство",
            "description": "Свяжите ещё одно своё устройство по одноразовому коду.",
            "progress": min(active_device_count, 2),
            "target": 2,
            "completed": active_device_count >= 2,
            "verification": "active_account_devices",
            "action_href": "/devices/",
        },
        {
            "id": "routing_lesson",
            "title": "Разобраться в маршрутах",
            "description": "Пройдите короткую инструкцию и проверьте решение для адреса.",
            "progress": 1 if routing_lesson else 0,
            "target": 1,
            "completed": routing_lesson,
            "verification": "routing_lesson_completed",
            "action_href": "/guides/#route-smart",
        },
        {
            "id": "quality_feedback",
            "title": "Помочь исследованию",
            "description": "Отправьте полезный отчёт; выполнение подтверждает оператор, оценка 5★ не требуется.",
            "progress": 1 if quality_feedback else 0,
            "target": 1,
            "completed": quality_feedback,
            "verification": "approved_research_application",
            "action_href": "/programs/",
        },
    ]
    return {
        "enabled": True,
        "ledger_ready": True,
        "unlocked_count": len([item for item in items if item["unlocked"]]),
        "items": items,
        "quests": quests,
        "quest_rewards_enabled": False,
        "reward_policy": "Полезные действия учитываются без автоматической денежной награды.",
    }


def _bonus_history_payload(*, s, user: User, tg_id: int, limit: int = 20) -> dict[str, Any]:
    max_items = max(1, min(int(limit or 20), 50))
    rows: list[tuple[datetime, int, dict[str, Any]]] = []

    def add_item(occurred_at: datetime | None, priority: int, payload: dict[str, Any]) -> None:
        if not occurred_at:
            return
        item = {
            "occurred_at": _safe_iso(occurred_at),
            **payload,
        }
        rows.append((occurred_at, priority, item))

    for usage, promo in (
        s.query(PromoUsage, PromoCode)
        .outerjoin(PromoCode, func.upper(PromoCode.code) == func.upper(PromoUsage.promo_code))
        .filter(PromoUsage.tg_id == int(tg_id))
        .order_by(PromoUsage.used_at.desc(), PromoUsage.id.desc())
        .limit(max_items)
        .all()
    ):
        promo_type = str(getattr(promo, "promo_type", "") or "").strip().lower()
        promo_value = int(getattr(promo, "value", 0) or 0)
        item = {
            "kind": "promo",
            "source": "promo",
            "title": "Промокод активирован",
            "code_preview": _access_key_safe_meta(str(usage.promo_code or "")).get("code_preview"),
            "days": promo_value if promo_type == "days" else 0,
            "discount_pct": promo_value if promo_type == "discount" else 0,
        }
        add_item(getattr(usage, "used_at", None), 30, item)

    try:
        reward_entries = get_reward_history(
            s,
            account_id=str(user.account_id or ""),
            limit=max_items,
        )
    except ValueError:
        reward_entries = []
    for entry in reward_entries:
        reward_key = str(entry.metadata.get("reward_key") or "")
        feature = str(entry.metadata.get("feature") or "")
        discount_pct = int(entry.metadata.get("discount_pct") or 0)
        is_wheel = entry.source == "bonus_wheel" or feature == "wheel" or reward_key.startswith("wheel_")
        is_calendar = (
            entry.source == "bonus_calendar"
            or feature == "calendar"
            or reward_key.startswith("calendar_")
        )
        add_item(
            entry.committed_at,
            28 if is_wheel else 26,
            {
                "kind": (
                    "wheel_spin"
                    if is_wheel
                    else "calendar_checkin" if is_calendar else "legacy_reward_claim"
                ),
                "source": entry.source,
                "title": (
                    "Рулетка: скидка получена"
                    if is_wheel and discount_pct > 0
                    else "Рулетка: бонус получен"
                    if is_wheel
                    else "Активность отмечена" if is_calendar else "Бонус получен"
                ),
                "days": int(entry.reward_days),
                "discount_pct": discount_pct,
                "durable_id": entry.durable_id,
            },
        )

    channel_status = channel_bonus_service.channel_bonus_status(s, user=user)
    add_item(
        channel_status["claimed_at"],
        20,
        {
            "kind": "telegram_channel",
            "source": "telegram",
            "title": "Telegram-бонус получен",
            "days": int(channel_status["claimed_days"]),
            "channel_username": PUBLIC_CHANNEL,
        },
    )

    opening_send = (
        s.query(CampaignSend)
        .filter(CampaignSend.tg_id == int(tg_id))
        .filter(CampaignSend.campaign_key == str(OPENING_PREMIUM_CAMPAIGN_KEY))
        .order_by(CampaignSend.sent_at.desc(), CampaignSend.id.desc())
        .first()
    )
    if opening_send:
        add_item(
            getattr(opening_send, "sent_at", None),
            10,
            {
                "kind": "opening_bonus",
                "source": "app",
                "title": "Стартовый бонус получен",
                "days": int(OPENING_PREMIUM_DAYS),
            },
        )

    rows.sort(key=lambda row: (row[0], row[1]), reverse=True)
    items = [item for _, _, item in rows[:max_items]]
    return {
        "ok": True,
        "tg_id": int(tg_id),
        "items": items,
        "limit": max_items,
        "next_cursor": None,
    }


def _bonus_wheel_state_payload(
    *,
    s,
    user: User,
    now: datetime | None = None,
    wheel_state: WheelState | None = None,
) -> dict[str, Any]:
    current_now = now or _reward_now()
    rollout_flag_enabled = bool(BONUS_WHEEL_ENABLED)
    config_payload = _bonus_wheel_config(s=s)
    state = wheel_state or get_wheel_state(
        s,
        account_id=str(user.account_id or ""),
        enabled=rollout_flag_enabled,
        config_payload=config_payload,
        now=current_now,
    )
    display_sectors: list[dict[str, Any]] = []
    config_preset: str | None = None
    if state.reason != "wheel_config_invalid":
        try:
            parsed_config = parse_paid_weekly_config(
                config_payload or {},
                explicit=config_payload is not None,
            )
            config_preset = parsed_config.preset
            display_sectors = [
                {
                    "key": outcome.key,
                    "kind": outcome.kind,
                    "value": int(outcome.value),
                    "label": (
                        f"+{int(outcome.value)} дн."
                        if outcome.kind == "days"
                        else f"−{int(outcome.value)}%"
                    ),
                }
                for outcome in parsed_config.outcomes
            ]
        except RewardDomainError:
            display_sectors = []
    if not rollout_flag_enabled:
        public_state = "disabled_until_feature_flag"
    elif state.reason == "wheel_config_invalid":
        public_state = "unavailable"
    elif not state.eligible:
        public_state = "ineligible"
    elif state.can_spin:
        public_state = "ready"
    else:
        public_state = "cooldown"
    return {
        "ok": True,
        "enabled": bool(state.enabled),
        "eligible": bool(state.eligible),
        "reason": str(state.reason),
        "state": public_state,
        "feature_flag": "BONUS_WHEEL_ENABLED",
        "feature_flag_enabled": rollout_flag_enabled,
        "spin_endpoint": "/api/bonuses/wheel/spin",
        "last_spin_at": _safe_iso(state.last_spin_at),
        "can_spin": bool(state.can_spin),
        "next_spin_at": _safe_iso(state.next_spin_at),
        "cooldown_hours": int(state.cooldown_hours),
        "last_reward_days": state.last_reward_days,
        "last_discount_pct": state.last_discount_pct,
        "last_reward_kind": (
            "discount"
            if state.last_discount_pct
            else "days" if state.last_reward_days else None
        ),
        "sync_state": str(state.sync_state),
        "sectors": [int(days) for days in state.sectors],
        "discount_sectors": [int(value) for value in state.discount_sectors],
        "display_sectors": display_sectors,
        "ledger_ready": True,
        "config_preset": config_preset,
    }


def _bonus_calendar_state_payload(
    *,
    s,
    user: User,
    now: datetime | None = None,
    calendar_state: CalendarState | None = None,
) -> dict[str, Any]:
    current_now = now or _reward_now()
    rollout_flag_enabled = bool(BONUS_CALENDAR_ENABLED)
    state = calendar_state or get_calendar_state(
        s,
        account_id=str(user.account_id or ""),
        enabled=rollout_flag_enabled,
        now=current_now,
    )
    if not rollout_flag_enabled:
        public_state = "disabled_until_feature_flag"
    elif not state.eligible:
        public_state = "ineligible"
    elif state.checked_in_today:
        public_state = "checked_in_today"
    else:
        public_state = "ready"
    checked_dates = (
        [
            (state.cycle_started_on + timedelta(days=offset)).isoformat()
            for offset in range(int(state.cycle_day))
        ]
        if state.cycle_started_on is not None
        else []
    )
    return {
        "ok": True,
        "enabled": bool(state.enabled),
        "eligible": bool(state.eligible),
        "reason": str(state.reason),
        "state": public_state,
        "feature_flag": "BONUS_CALENDAR_ENABLED",
        "feature_flag_enabled": rollout_flag_enabled,
        "checkin_endpoint": "/api/bonuses/calendar/checkin",
        "checked_in_today": bool(state.checked_in_today),
        "can_checkin": bool(state.enabled and state.eligible and not state.checked_in_today),
        "cycle_started_on": state.cycle_started_on.isoformat() if state.cycle_started_on else None,
        "calendar_cycle_day": int(state.cycle_day),
        "cycle_day": int(state.cycle_day),
        "next_milestone": state.next_milestone,
        "reward_days": int(BONUS_CALENDAR_REWARD_DAYS),
        "checked_dates": checked_dates,
        "streak_months": int(state.cycle_day),
        "streak_last_check_at": checked_dates[-1] if checked_dates else None,
        "achievements": dict(state.achievements),
        "sync_state": str(state.sync_state),
        "ledger_ready": True,
    }


def _bonus_summary_payload(*, s, user: User, tg_id: int) -> dict[str, Any]:
    now = _reward_now()
    reward_access = evaluate_active_paid(
        s,
        account_id=str(user.account_id or ""),
        now=now,
    )
    referral = _bonus_referral_summary_payload(s=s, user=user, tg_id=tg_id)
    history = _bonus_history_payload(s=s, user=user, tg_id=tg_id, limit=20)
    wheel_state = get_wheel_state(
        s,
        account_id=str(user.account_id or ""),
        enabled=bool(BONUS_WHEEL_ENABLED),
        config_payload=_bonus_wheel_config(s=s),
        now=now,
    )
    calendar_state = get_calendar_state(
        s,
        account_id=str(user.account_id or ""),
        enabled=bool(BONUS_CALENDAR_ENABLED),
        now=now,
    )
    wheel = _bonus_wheel_state_payload(s=s, user=user, now=now, wheel_state=wheel_state)
    calendar = _bonus_calendar_state_payload(s=s, user=user, now=now, calendar_state=calendar_state)
    achievements = _bonus_achievements_payload(
        s=s,
        user=user,
        tg_id=tg_id,
        calendar_state=calendar_state,
    )
    channel_status = channel_bonus_service.channel_bonus_status(s, user=user)
    channel_claimed_at = _safe_iso(channel_status["claimed_at"])
    opening_claimed = _has_campaign_mark(
        s,
        tg_id=tg_id,
        campaign_key=OPENING_PREMIUM_CAMPAIGN_KEY,
    )
    channel_claimed = bool(channel_status["claimed"])
    channel_claimable = bool(
        not channel_claimed
        and bool(getattr(user, "tos_accepted", False))
        and str(getattr(user, "sub_type", "") or "").strip().upper() != "MANUAL"
        and not opening_claimed
    )
    if channel_claimed:
        channel_reason = "already_claimed"
    elif not bool(getattr(user, "tos_accepted", False)):
        channel_reason = "tos_required"
    elif str(getattr(user, "sub_type", "") or "").strip().upper() == "MANUAL":
        channel_reason = "manual_account"
    elif opening_claimed:
        channel_reason = "opening_bonus_conflict"
    else:
        channel_reason = "eligible"
    if reward_access.eligible:
        reward_message = "Бонусы доступны."
    elif channel_claimed:
        reward_message = (
            "Telegram-бонус уже получен. Рулетка, календарь и реферальные "
            "начисления откроются после первой оплаты."
        )
    elif channel_claimable:
        reward_message = (
            f"Telegram-бонус +{int(CHANNEL_PREMIUM_DAYS)} дней доступен сейчас. "
            "Рулетка, календарь и реферальные начисления откроются после первой оплаты."
        )
    else:
        reward_message = (
            "Рулетка, календарь и реферальные начисления откроются после первой оплаты."
        )
    return {
        "ok": True,
        "tg_id": tg_id,
        "reward_access": {
            "eligible": bool(reward_access.eligible),
            "state": "paid" if reward_access.eligible else "paid_required",
            "reason": str(reward_access.reason),
            "message": reward_message,
        },
        "referral_count": int(user.referral_count or 0),
        "referral_code": str(user.referral_code or "").strip(),
        "referral_bonus_days": REFERRAL_BONUS_DAYS,
        "streak_months": int(calendar_state.cycle_day),
        "last_wheel_spin": _safe_iso(wheel_state.last_spin_at),
        "channel_bonus_premium_days": int(CHANNEL_PREMIUM_DAYS),
        "channel_bonus_claimed_at": channel_claimed_at,
        "opening_bonus_premium_days": int(OPENING_PREMIUM_DAYS),
        "opening_bonus_claimed": bool(opening_claimed),
        "channel_username": PUBLIC_CHANNEL,
        "points_tier": referral["tier"],
        "referral": referral,
        "channel_bonus": {
            "premium_days": int(CHANNEL_PREMIUM_DAYS),
            "offer_days": int(channel_status["offer_days"]),
            "claimed_days": int(channel_status["claimed_days"]),
            "claimed": channel_claimed,
            "claimed_at": channel_claimed_at,
            "channel_username": PUBLIC_CHANNEL,
            "eligible": channel_claimed or channel_claimable,
            "can_claim": channel_claimable,
            "reason": channel_reason,
        },
        "opening_bonus": {
            "premium_days": int(OPENING_PREMIUM_DAYS),
            "claimed": bool(opening_claimed),
        },
        "promo": {
            "redeem_supported": True,
            "redeem_endpoint": "/api/bonuses/promo/redeem",
            "unified_redeem_supported": True,
            "pending_discount_pct": int(user.pending_discount_pct or 0),
            "pending_discount_code": str(user.pending_discount_code or "").strip().upper(),
        },
        "history": {
            "enabled": True,
            "endpoint": "/api/bonuses/history",
            "recent_count": len(history["items"]),
            "next_cursor": history.get("next_cursor"),
        },
        "wheel": wheel,
        "calendar": calendar,
        "achievements": achievements,
    }


@app.get("/api/bonuses/summary")
async def bonuses_summary(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        _ensure_paid_referral_code_for_summary(s=s, user=user)
        return _bonus_summary_payload(s=s, user=user, tg_id=tg_id)
    finally:
        s.close()


@app.get("/api/bonuses/referral/summary")
async def bonuses_referral_summary(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        _ensure_paid_referral_code_for_summary(s=s, user=user)
        return _bonus_referral_summary_payload(s=s, user=user, tg_id=tg_id)
    finally:
        s.close()


@app.get("/api/bonuses/history")
async def bonuses_history(
    request: Request,
    x_telegram_init_data: str = Header(default=""),
    limit: int = Query(default=20, ge=1, le=50),
) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return _bonus_history_payload(s=s, user=user, tg_id=tg_id, limit=limit)
    finally:
        s.close()


@app.get("/api/bonuses/wheel/state")
async def bonuses_wheel_state(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return _bonus_wheel_state_payload(s=s, user=user)
    finally:
        s.close()


@app.post("/api/bonuses/wheel/spin")
async def bonuses_wheel_spin(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        now = _reward_now()
        mutation = spin_wheel(
            s,
            account_id=str(user.account_id or ""),
            enabled=bool(BONUS_WHEEL_ENABLED),
            config_payload=_bonus_wheel_config(s=s),
            now=now,
        )
        _ensure_achievement(s=s, tg_id=tg_id, achievement_id="first_wheel", now=now)
        s.commit()
        wheel_state = _bonus_wheel_state_payload(s=s, user=user, now=now)
        summary = _bonus_summary_payload(s=s, user=user, tg_id=tg_id)
        expiry_at = _safe_iso(getattr(user, "expiry_at", None))
    except RewardDomainError as exc:
        s.rollback()
        raise _reward_http_error(exc) from None
    except IntegrityError:
        s.rollback()
        raise HTTPException(status_code=503, detail={"code": "reward_state_unavailable"}) from None
    finally:
        s.close()
    _track_bonus_event(
        tg_id=tg_id,
        event_name="wheel_reward_claimed",
        meta={
            "reward_days": int(mutation.reward_days),
            "reward_kind": mutation.reward_kind,
            "reward_value": int(mutation.reward_value),
            "discount_pct": int(mutation.discount_pct),
            "grant_id": mutation.grant_id,
            "sync_state": mutation.sync_state,
        },
    )
    return {
        "ok": True,
        "feature": "wheel",
        "reward_days": int(mutation.reward_days),
        "reward_kind": mutation.reward_kind,
        "reward_value": int(mutation.reward_value),
        "discount_pct": int(mutation.discount_pct),
        "sector_key": mutation.sector_key,
        "grant_id": mutation.grant_id,
        "sync_state": str(mutation.sync_state),
        "state": wheel_state,
        "expiry_at": expiry_at,
        "sync_ok": mutation.sync_state == "synced",
        "summary": summary,
    }


@app.get("/api/bonuses/calendar")
async def bonuses_calendar(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return _bonus_calendar_state_payload(s=s, user=user)
    finally:
        s.close()


@app.post("/api/bonuses/calendar/checkin")
async def bonuses_calendar_checkin(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        now = _reward_now()
        mutation = checkin_calendar(
            s,
            account_id=str(user.account_id or ""),
            enabled=bool(BONUS_CALENDAR_ENABLED),
            now=now,
        )
        if mutation.achievements.get("first_checkin"):
            _ensure_achievement(s=s, tg_id=tg_id, achievement_id="first_checkin", now=now)
        if mutation.achievements.get("streak_7"):
            _ensure_achievement(s=s, tg_id=tg_id, achievement_id="streak_7", now=now)
        s.commit()
        calendar_state = _bonus_calendar_state_payload(s=s, user=user, now=now)
        summary = _bonus_summary_payload(s=s, user=user, tg_id=tg_id)
        expiry_at = _safe_iso(getattr(user, "expiry_at", None))
    except RewardDomainError as exc:
        s.rollback()
        raise _reward_http_error(exc) from None
    except IntegrityError:
        s.rollback()
        raise HTTPException(status_code=503, detail={"code": "reward_state_unavailable"}) from None
    finally:
        s.close()
    _track_bonus_event(
        tg_id=tg_id,
        event_name="calendar_reward_claimed",
        meta={
            "reward_days": int(mutation.reward_days),
            "grant_id": mutation.grant_id,
            "calendar_cycle_day": int(mutation.calendar_cycle_day),
            "already_checked_in": bool(mutation.already_checked_in),
            "sync_state": mutation.sync_state,
        },
    )
    return {
        "ok": True,
        "feature": "calendar",
        "reward_days": int(mutation.reward_days),
        "grant_id": mutation.grant_id,
        "sync_state": str(mutation.sync_state),
        "already_checked_in": bool(mutation.already_checked_in),
        "calendar_cycle_started_on": (
            mutation.calendar_cycle_started_on.isoformat()
            if mutation.calendar_cycle_started_on
            else None
        ),
        "calendar_cycle_day": int(mutation.calendar_cycle_day),
        "streak_months": int(mutation.calendar_cycle_day),
        "state": calendar_state,
        "expiry_at": expiry_at,
        "sync_ok": mutation.sync_state == "synced",
        "summary": summary,
    }


@app.post("/api/channel/subscriber/check")
async def channel_subscriber_check(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    if not PUBLIC_CHANNEL:
        raise HTTPException(status_code=400, detail="Public channel is not configured")

    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        channel_status = channel_bonus_service.channel_bonus_status(s, user=user)
    finally:
        s.close()

    return await channel_bonus_service.build_channel_subscriber_check_response(
        user=user,
        channel_username=PUBLIC_CHANNEL,
        bonus_days=CHANNEL_PREMIUM_DAYS,
        claimed_days=int(channel_status["claimed_days"]),
        claimed_at=channel_status["claimed_at"],
        is_channel_member=_is_channel_member,
    )


@app.post("/api/bonuses/channel/claim")
async def claim_channel_bonus(request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    if not PUBLIC_CHANNEL:
        raise HTTPException(status_code=400, detail="Public channel is not configured")

    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        result = await channel_bonus_service.claim_channel_bonus(
            s=s,
            user=user,
            tg_id=tg_id,
            public_channel=PUBLIC_CHANNEL,
            bonus_days=CHANNEL_PREMIUM_DAYS,
            opening_bonus_campaign_key=OPENING_PREMIUM_CAMPAIGN_KEY,
            subscriber_campaign_key=CHANNEL_SUBSCRIBER_CAMPAIGN_KEY,
            points_expiry_days=POINTS_EXPIRY_DAYS,
            is_channel_member=_is_channel_member,
            sync_user_after_paid_bonus=_sync_user_after_paid_bonus,
        )
        return result
    finally:
        s.close()


@app.post("/api/promo/redeem")
async def promo_redeem(payload: PromoRedeemIn, request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    code = (payload.code or "").strip().upper()
    if not code:
        _track_bonus_event(tg_id=tg_id, event_name="promo_redeem_denied", meta={"reason": "empty_code"})
        raise HTTPException(status_code=400, detail="Promo code is required")

    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            _track_bonus_event(tg_id=tg_id, event_name="promo_redeem_denied", meta={**_access_key_safe_meta(code), "reason": "user_not_found"})
            raise HTTPException(status_code=404, detail="User not found")
        if not bool(getattr(user, "tos_accepted", False)):
            _track_bonus_event(tg_id=tg_id, event_name="promo_redeem_denied", meta={**_access_key_safe_meta(code), "reason": "tos_required"})
            raise HTTPException(status_code=400, detail="Сначала примите оферту в боте (/start)")
        promo = s.query(PromoCode).filter(func.upper(PromoCode.code) == code).first()
        if not promo:
            _track_bonus_event(tg_id=tg_id, event_name="promo_redeem_denied", meta={**_access_key_safe_meta(code), "reason": "not_found"})
            raise HTTPException(status_code=404, detail="Promo not found")
        active_campaigns_for_code = (
            s.query(func.count(IncentiveCampaign.id))
            .filter(func.lower(IncentiveCampaign.campaign_type) == "promo")
            .filter(func.upper(IncentiveCampaign.target_value) == code)
            .filter(IncentiveCampaign.is_active == True)
            .scalar()
            or 0
        )
        campaign = _campaign_lookup(
            s=s,
            campaign_type="promo",
            target_value=code,
            user=user,
            now=_utcnow(),
        )
        if int(active_campaigns_for_code) > 0 and campaign is None:
            _track_bonus_event(
                tg_id=tg_id,
                event_name="promo_redeem_denied",
                meta={**_access_key_safe_meta(code), "reason": "campaign_restriction_mismatch"},
            )
            raise HTTPException(status_code=403, detail="Promo campaign restrictions mismatch for this user")
        uses_left = int(promo.uses_left or 0)
        if uses_left == 0:
            _track_bonus_event(tg_id=tg_id, event_name="promo_redeem_denied", meta={**_access_key_safe_meta(code), "reason": "exhausted"})
            raise HTTPException(status_code=400, detail="Promo exhausted")
        if promo.expires_at and promo.expires_at < _utcnow():
            _track_bonus_event(tg_id=tg_id, event_name="promo_redeem_denied", meta={**_access_key_safe_meta(code), "reason": "expired"})
            raise HTTPException(status_code=400, detail="Promo expired")
        used = s.query(PromoUsage).filter_by(tg_id=tg_id, promo_code=promo.code).first()
        if used:
            _track_bonus_event(tg_id=tg_id, event_name="promo_redeem_denied", meta={**_access_key_safe_meta(code), "reason": "already_redeemed"})
            raise HTTPException(status_code=400, detail="Promo already redeemed")

        promo_type = (promo.promo_type or "").strip().lower()
        value = int(promo.value or 0)
        if promo_type not in {"days", "discount"} or value <= 0:
            _track_bonus_event(tg_id=tg_id, event_name="promo_redeem_denied", meta={**_access_key_safe_meta(code), "reason": "invalid_value"})
            raise HTTPException(status_code=400, detail="Promo has invalid value")
        applied_days = 0
        pending_discount_pct = 0
        if promo_type == "days":
            now = _utcnow()
            if user.expiry_at and user.expiry_at > now:
                user.expiry_at = user.expiry_at + timedelta(days=value)
            else:
                user.expiry_at = now + timedelta(days=value)
            user.is_active = True
            user.sub_type = "PAID"
            user.current_plan_code = "promo_grant"
            applied_days = value
        elif promo_type == "discount":
            user.pending_discount_pct = max(1, min(95, int(value)))
            user.pending_discount_code = str(promo.code or "").strip().upper()[:20]
            user.pending_discount_set_at = _utcnow()
            pending_discount_pct = int(user.pending_discount_pct or 0)

        if uses_left > 0:
            updated = (
                s.query(PromoCode)
                .filter(PromoCode.id == promo.id, PromoCode.uses_left > 0)
                .update({PromoCode.uses_left: PromoCode.uses_left - 1}, synchronize_session=False)
            )
            if int(updated or 0) != 1:
                s.rollback()
                raise HTTPException(status_code=400, detail="Promo exhausted")
            s.flush()
            s.refresh(promo)

        s.add(PromoUsage(tg_id=tg_id, promo_code=promo.code))
        _campaign_consume(s=s, row=campaign)
        try:
            s.commit()
        except IntegrityError:
            s.rollback()
            _track_bonus_event(tg_id=tg_id, event_name="promo_redeem_denied", meta={**_access_key_safe_meta(code), "reason": "already_redeemed"})
            raise HTTPException(status_code=400, detail="Promo already redeemed")
        _track_bonus_event(
            tg_id=tg_id,
            event_name="promo_redeemed",
            meta={
                **_access_key_safe_meta(str(promo.code or "")),
                "promo_type": promo_type,
                "value": int(value),
                "applied_days": int(applied_days),
                "pending_discount_pct": int(pending_discount_pct),
            },
        )
        return {
            "ok": True,
            "code": promo.code,
            "promo_type": promo_type,
            "value": value,
            "applied_days": applied_days,
            "pending_discount_pct": int(pending_discount_pct),
            "uses_left": int(promo.uses_left or 0),
        }
    finally:
        s.close()


@app.post("/api/bonuses/promo/redeem")
async def bonuses_promo_redeem(payload: PromoRedeemIn, request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    result = await promo_redeem(payload, request, x_telegram_init_data)
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if user:
            result["summary"] = _bonus_summary_payload(s=s, user=user, tg_id=tg_id)
    finally:
        s.close()
    return result


@app.post("/api/gift/redeem")
async def gift_redeem(payload: GiftRedeemIn, request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    code = str(payload.code or "").strip().upper()
    if not code:
        _track_bonus_event(tg_id=tg_id, event_name="gift_redeem_denied", meta={"reason": "invalid_code"})
    if code:
        s = SessionLocal()
        try:
            user = s.query(User).filter(User.tg_id == int(tg_id)).first()
            card = s.query(GiftCard).filter(func.upper(GiftCard.code) == code).first()
            if user and card:
                card_type = str(card.card_type or "").strip().upper()
                active_campaigns_for_type = (
                    s.query(func.count(IncentiveCampaign.id))
                    .filter(func.lower(IncentiveCampaign.campaign_type) == "gift")
                    .filter(func.upper(IncentiveCampaign.target_value) == card_type)
                    .filter(IncentiveCampaign.is_active == True)
                    .scalar()
                    or 0
                )
                campaign = _campaign_lookup(
                    s=s,
                    campaign_type="gift",
                    target_value=card_type,
                    user=user,
                    now=_utcnow(),
                )
                if int(active_campaigns_for_type) > 0 and campaign is None:
                    _track_bonus_event(
                        tg_id=tg_id,
                        event_name="gift_redeem_denied",
                        meta={**_access_key_safe_meta(code), "card_type": card_type, "reason": "campaign_restriction_mismatch"},
                    )
                    raise HTTPException(status_code=403, detail="Gift campaign restrictions mismatch for this user")
        finally:
            s.close()
    result = await redeem_gift_card_service(code=payload.code, recipient_tg_id=tg_id, require_tos=True)
    if result.get("ok"):
        card_type = str(result.get("card_type") or "").strip().upper()
        if card_type:
            s2 = SessionLocal()
            try:
                user2 = s2.query(User).filter(User.tg_id == int(tg_id)).first()
                if user2:
                    campaign2 = _campaign_lookup(s=s2, campaign_type="gift", target_value=card_type, user=user2, now=_utcnow())
                    _campaign_consume(s=s2, row=campaign2)
                    s2.commit()
            except Exception:
                s2.rollback()
            finally:
                s2.close()
        track_event(
            tg_id=tg_id,
            event_name="gift_redeemed",
            source="webapp",
            meta={
                **_access_key_safe_meta(code),
                "card_type": result.get("card_type"),
                "days": result.get("days"),
                "sync_ok": result.get("sync_ok"),
            },
        )
        return result

    error = str(result.get("error") or "redeem_failed")
    message = str(result.get("message") or "Не удалось активировать код")
    _track_bonus_event(tg_id=tg_id, event_name="gift_redeem_denied", meta={**_access_key_safe_meta(code), "reason": error})
    status_map = {
        "invalid_code": 400,
        "not_found": 404,
        "already_redeemed": 400,
        "self_redeem": 400,
        "tos_required": 400,
    }
    raise HTTPException(status_code=status_map.get(error, 400), detail=message)


@app.get("/api/access-keys/status/{key}")
async def access_key_status(key: str, request: Request) -> dict[str, Any]:
    _enforce_beta_rate_limit("access_key_status", request)
    code = str(key or "").strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Access key is required")
    s = SessionLocal()
    try:
        card = s.query(GiftCard).filter(func.upper(GiftCard.code) == code).first()
        if not card:
            raise HTTPException(status_code=404, detail="Access key not found")
        payload = _access_key_status_payload(s=s, card=card)
        if payload.get("kind") == "unknown":
            raise HTTPException(status_code=400, detail="Access key type is not supported")
        return payload
    finally:
        s.close()


async def _redeem_access_key_for_auth_user(
    *,
    key: str,
    request: Request,
    auth_user: dict[str, Any],
    event_source: str,
    enforce_rate_limit: bool = True,
) -> dict[str, Any]:
    tg_id = int(auth_user.get("id", 0))
    if enforce_rate_limit:
        _enforce_beta_rate_limit("access_key_redeem", request, identity=f"tg:{tg_id}")
    code = str(key or "").strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Access key is required")

    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        card = s.query(GiftCard).filter(func.upper(GiftCard.code) == code).first()
        if not card:
            raise HTTPException(status_code=404, detail="Access key not found")
        payment_claim = (
            s.query(PaymentEntitlementClaim)
            .filter(PaymentEntitlementClaim.fallback_gift_card_id == int(card.id))
            .one_or_none()
        )
        if card.redeemed_by is not None and (
            payment_claim is None or int(card.redeemed_by) != int(tg_id)
        ):
            raise HTTPException(status_code=400, detail="Access key already redeemed")
        if int(card.created_by or 0) == int(tg_id):
            raise HTTPException(status_code=400, detail="You cannot redeem your own key")
        if not bool(getattr(user, "tos_accepted", False)):
            raise HTTPException(status_code=400, detail="Accept terms before redeeming a key")

        now = _utcnow()
        if payment_claim is not None:
            ensure_user_account_foundation(s, user, now=now)
            s.flush()
            payment_result = redeem_payment_fallback(
                s,
                gift_card_id=int(card.id),
                account_id=str(user.account_id),
                legacy_tg_id=int(tg_id),
                now=now,
            )
            if payment_result.code not in {"fulfilled", "already_fulfilled"}:
                s.commit()
                status_code = 409 if payment_result.code in {"account_conflict", "manual_review"} else 400
                raise HTTPException(status_code=status_code, detail="Payment access key is not redeemable")
            applied = {
                "current_plan_code": str(user.current_plan_code or payment_claim.plan_code),
                "expiry_at": _safe_iso(user.expiry_at),
            }
        else:
            meta = _access_key_meta_from_card_type(s=s, card_type=str(card.card_type or ""))
            if not meta:
                raise HTTPException(status_code=400, detail="Access key type is not supported")
            applied = _apply_access_key_to_user(user=user, meta=meta, now=now)
            updated = (
                s.query(GiftCard)
                .filter(GiftCard.id == int(card.id), GiftCard.redeemed_by.is_(None))
                .update(
                    {
                        GiftCard.redeemed_by: int(tg_id),
                        GiftCard.redeemed_at: now,
                    },
                    synchronize_session=False,
                )
            )
            if int(updated or 0) != 1:
                s.rollback()
                raise HTTPException(status_code=400, detail="Access key already redeemed")

        s.commit()
        s.refresh(user)
        card = s.query(GiftCard).filter(GiftCard.id == int(card.id)).first() or card
        nodes = enabled_nodes(s)
        nodes_for_user = _nodes_for_user(user, nodes, session=s)
        client_policy = app_first_service.build_client_policy(
            session=s,
            user=user,
            install_id=str(getattr(user, "app_install_id", "") or "").strip() or None,
        )
        access_policy = _build_access_policy(user=user, used_bytes=0)
        linked_identities = _linked_identities_payload(s=s, user=user, auth_user=auth_user)
        promo_slots = _promo_slots_payload_for_surface(
            s=s,
            surface="webapp",
            access_state=str(access_policy.get("access_state") or ""),
            user=user,
        )
        key_status = _access_key_status_payload(s=s, card=card)
    except HTTPException:
        s.rollback()
        raise
    except Exception:
        s.rollback()
        safe_code = _access_key_safe_meta(code)
        logger.error(
            "access key redeem failed code=access_key_redeem_failed correlation=%s",
            safe_code.get("code_fp"),
        )
        raise HTTPException(status_code=500, detail="Failed to redeem access key")
    finally:
        s.close()

    sync_ok = await _sync_control_panel_access(user=user)
    try:
        track_event(
            tg_id=int(tg_id),
            event_name="access_key_redeemed",
            source=event_source,
            meta={
                **_access_key_safe_meta(code),
                "plan_code": (key_status.get("plan") or {}).get("code"),
                "sync_ok": bool(sync_ok),
            },
        )
    except Exception:
        logger.exception("failed to track access_key_redeemed tg_id=%s", int(tg_id))

    return {
        "ok": True,
        "key": code,
        "status": key_status,
        "plan": key_status.get("plan"),
        "access": {
            **access_policy,
            "sub_type": str(getattr(user, "sub_type", "") or ""),
            "current_plan_code": applied.get("current_plan_code"),
            "expiry_at": applied.get("expiry_at"),
        },
        "linked_identities": linked_identities,
        "free_caps": _free_caps_payload(user=user, access_policy=access_policy),
        "redeem_eligibility": _redeem_eligibility_payload(user=user, access_policy=access_policy),
        "promo_slots": promo_slots,
        "hidden_transport_matrix": _hidden_transport_matrix_payload(nodes=nodes_for_user, client_policy=client_policy),
        "location_matrix": _location_matrix_payload(user=user, nodes=nodes_for_user, client_policy=client_policy),
        "provisioning": {
            "sync_ok": bool(sync_ok),
            "managed_profile_path": "/api/client/profile/managed",
            "dashboard_path": "/api/dashboard",
        },
    }


@app.post("/api/access-keys/redeem")
async def access_key_redeem(
    payload: AccessKeyRedeemIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    return await _redeem_access_key_for_auth_user(
        key=payload.key,
        request=request,
        auth_user=auth_user,
        event_source="webapp",
    )


@app.post("/api/redeem")
async def unified_redeem(
    payload: UnifiedRedeemIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    _enforce_beta_rate_limit("unified_redeem", request, identity=f"tg:{tg_id}")
    code = str(payload.code or "").strip()
    if not code:
        raise HTTPException(
            status_code=400,
            detail={"code": "redeem_code_required", "message": "Activation code is required."},
        )
    if _looks_like_subscription_or_proxy_link(code):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "subscription_link_not_redeem_code",
                "message": "Raw subscription links are not redeem codes. Use account recovery or manual import instead.",
                "manual_import_allowed": True,
            },
        )

    normalized = code.upper()
    s = SessionLocal()
    try:
        card = s.query(GiftCard).filter(func.upper(GiftCard.code) == normalized).first()
        card_meta = _access_key_meta_from_card_type(s=s, card_type=str(getattr(card, "card_type", "") or "")) if card else None
        payment_claim_exists = bool(
            card
            and s.query(PaymentEntitlementClaim.id)
            .filter(PaymentEntitlementClaim.fallback_gift_card_id == int(card.id))
            .first()
        )
        promo = s.query(PromoCode).filter(func.upper(PromoCode.code) == normalized).first()
    finally:
        s.close()

    if _is_legacy_gift_card_for_unified_redeem(card=card, meta=card_meta):
        result = await gift_redeem(
            GiftRedeemIn(code=normalized),
            request,
            x_telegram_init_data,
        )
        s2 = SessionLocal()
        try:
            user = s2.query(User).filter_by(tg_id=tg_id).first()
            summary = _bonus_summary_payload(s=s2, user=user, tg_id=tg_id) if user else None
        finally:
            s2.close()
        payload_out: dict[str, Any] = {
            "ok": True,
            "kind": "gift",
            **_access_key_safe_meta(normalized),
            "result": result,
        }
        if summary:
            payload_out["summary"] = summary
        return payload_out

    if card and (card_meta or payment_claim_exists):
        result = await _redeem_access_key_for_auth_user(
            key=normalized,
            request=request,
            auth_user=auth_user,
            event_source="app",
            enforce_rate_limit=False,
        )
        return {
            "ok": True,
            "kind": "access_key",
            **_access_key_safe_meta(normalized),
            "result": result,
        }

    if promo:
        result = await promo_redeem(
            PromoRedeemIn(code=normalized),
            request,
            x_telegram_init_data,
        )
        return {
            "ok": True,
            "kind": "promo",
            **_access_key_safe_meta(normalized),
            "result": result,
        }

    raise HTTPException(
        status_code=404,
        detail={
            "code": "redeem_code_not_supported",
            "message": "This activation code is not supported by the unified app endpoint yet.",
            "supported_kinds": ["access_key", "gift", "promo"],
            **_access_key_safe_meta(normalized),
        },
    )


@app.post("/api/client/cabinet-token")
async def client_cabinet_token(
    payload: ClientCabinetTokenIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    _enforce_beta_rate_limit("cabinet_token", request, identity=f"tg:{tg_id}")
    target_path = _normalize_cabinet_target_path(payload.target_path)
    now = _utcnow()
    handoff_token = create_web_session_token(
        tg_id=tg_id,
        username=str(auth_user.get("username") or "").strip() or None,
        auth_type=str(auth_user.get("auth_type") or "app").strip() or "app",
        auth_origin="app_cabinet_handoff",
        email=str(auth_user.get("email") or "").strip() or None,
        ttl_seconds=CABINET_HANDOFF_TTL_SECONDS,
        purpose="cabinet_handoff",
        account_id=str(auth_user.get("account_id") or "").strip() or None,
        session_id=str(auth_user.get("session_id") or "").strip() or None,
        device_id=str(auth_user.get("device_id") or "").strip() or None,
        auth_epoch=auth_user.get("auth_epoch"),
        device_credential_version=auth_user.get("device_credential_version"),
        scope=str(auth_user.get("scope") or "").strip() or None,
        token_id=secrets.token_urlsafe(16),
    )
    if not handoff_token:
        raise HTTPException(status_code=500, detail="Cabinet handoff session is not configured")
    s = SessionLocal()
    try:
        _cleanup_expired_cabinet_handoff_tokens(s, now=now)
        s.add(
            WebCabinetHandoffToken(
                tg_id=tg_id,
                token_hash=_cabinet_handoff_token_hash(handoff_token),
                target_path=target_path,
                expires_at=now + timedelta(seconds=int(CABINET_HANDOFF_TTL_SECONDS)),
                created_at=now,
            )
        )
        s.commit()
    except IntegrityError:
        s.rollback()
        raise HTTPException(status_code=500, detail="Cabinet handoff token collision")
    finally:
        s.close()
    return {
        "ok": True,
        "token": handoff_token,
        "handoff_token": handoff_token,
        "expires_in": int(CABINET_HANDOFF_TTL_SECONDS),
        "target_path": target_path,
        "handoff_url": _build_cabinet_handoff_url(token=handoff_token, target_path=target_path),
        "auth_origin": "app_cabinet_handoff",
        "scope": "cabinet_handoff",
    }


@app.post("/api/auth/cabinet-handoff/exchange")
async def auth_cabinet_handoff_exchange(payload: CabinetHandoffExchangeIn, request: Request, response: Response) -> dict[str, Any]:
    handoff_token = str(payload.handoff_token or payload.token or "").strip()
    _enforce_beta_rate_limit("cabinet_handoff_exchange", request)
    if not handoff_token:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "cabinet_handoff_token_required",
                "message": "Cabinet handoff token is required.",
            },
        )
    handoff_auth_user, reason = inspect_web_session_token(handoff_token)
    if not handoff_auth_user:
        raise HTTPException(
            status_code=401 if reason != "expired" else 410,
            detail={
                "code": "cabinet_handoff_expired" if reason == "expired" else "cabinet_handoff_invalid",
                "message": "Cabinet handoff token is invalid or expired.",
            },
        )
    if str(handoff_auth_user.get("purpose") or "").strip() != "cabinet_handoff":
        raise HTTPException(
            status_code=400,
            detail={
                "code": "cabinet_handoff_wrong_purpose",
                "message": "This token is not a cabinet handoff token.",
            },
        )

    token_hash = _cabinet_handoff_token_hash(handoff_token)
    now = _utcnow()
    s = SessionLocal()
    try:
        row = (
            s.query(WebCabinetHandoffToken)
            .filter(WebCabinetHandoffToken.token_hash == token_hash)
            .with_for_update()
            .first()
        )
        if not row:
            raise HTTPException(
                status_code=401,
                detail={
                    "code": "cabinet_handoff_invalid",
                    "message": "Cabinet handoff token was not issued by this backend.",
                },
            )
        if int(row.tg_id or 0) != int(handoff_auth_user.get("id") or 0):
            raise HTTPException(
                status_code=401,
                detail={
                    "code": "cabinet_handoff_invalid",
                    "message": "Cabinet handoff token does not match the session user.",
                },
            )
        if row.used_at is not None:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "cabinet_handoff_already_used",
                    "message": "Cabinet handoff token was already used.",
                },
            )
        if row.expires_at <= now:
            raise HTTPException(
                status_code=410,
                detail={
                    "code": "cabinet_handoff_expired",
                    "message": "Cabinet handoff token has expired.",
                },
            )
        if str(handoff_auth_user.get("session_id") or "").strip():
            try:
                auth_session_service.validate_access_session(
                    s,
                    payload=handoff_auth_user,
                    now=now,
                )
            except auth_session_service.AuthSessionError as exc:
                raise _auth_session_http_exception(exc) from exc
        session_token = create_web_session_token(
            tg_id=int(handoff_auth_user.get("id") or 0),
            username=str(handoff_auth_user.get("username") or "").strip() or None,
            auth_type=str(handoff_auth_user.get("auth_type") or "app").strip() or "app",
            auth_origin="app_cabinet_handoff",
            email=str(handoff_auth_user.get("email") or "").strip() or None,
            purpose="cabinet_session",
            account_id=str(handoff_auth_user.get("account_id") or "").strip() or None,
            session_id=str(handoff_auth_user.get("session_id") or "").strip() or None,
            device_id=str(handoff_auth_user.get("device_id") or "").strip() or None,
            auth_epoch=handoff_auth_user.get("auth_epoch"),
            device_credential_version=handoff_auth_user.get("device_credential_version"),
            scope=(
                "cabinet_session"
                if str(handoff_auth_user.get("session_id") or "").strip()
                else None
            ),
        )
        if not session_token:
            raise HTTPException(status_code=500, detail="Cabinet session is not configured")
        row.used_at = now
        s.commit()
        _set_web_session_cookie(response, session_token)
        return {
            "ok": True,
            "token": session_token,
            "token_transport": "cookie_and_legacy_bearer",
            "cookie_bound": True,
            "expires_in": int(SESSION_TTL_SECONDS),
            "target_path": _normalize_cabinet_target_path(str(row.target_path or "/")),
            "auth_origin": "app_cabinet_handoff",
            "scope": "cabinet_session",
        }
    except HTTPException:
        s.rollback()
        raise
    finally:
        s.close()


@app.post("/api/reviews")
async def create_review(payload: ReviewCreateIn, request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        db_user = s.query(User).filter_by(tg_id=tg_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        review_text = _normalize_feedback_text(payload.text, max_len=500)
        if len(review_text) < 3:
            raise HTTPException(status_code=400, detail="Review text is too short")
        row = Review(
            tg_id=tg_id,
            username=db_user.username or db_user.linked_telegram_username or auth_user.get("username"),
            rating=int(payload.rating),
            text=review_text,
            is_featured=False,
        )
        s.add(row)
        s.commit()
        return {"ok": True, "review_id": row.id}
    finally:
        s.close()


@app.post("/api/feedback")
async def create_feedback(payload: FeedbackCreateIn, request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    s = SessionLocal()
    try:
        db_user = s.query(User).filter_by(tg_id=tg_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        feedback_text = _normalize_feedback_text(payload.text, max_len=1000)
        if len(feedback_text) < 5:
            raise HTTPException(status_code=400, detail="Feedback text is too short")

        review_id = int(payload.review_id or 0) or None
        if review_id is not None:
            review_row = s.query(Review).filter_by(id=review_id, tg_id=tg_id).first()
            if not review_row:
                raise HTTPException(status_code=404, detail="Review not found")

        row = FeedbackEntry(
            tg_id=tg_id,
            username=db_user.username or db_user.linked_telegram_username or auth_user.get("username"),
            category=_normalize_feedback_category(payload.category),
            text=feedback_text,
            status="new",
            source=_normalize_feedback_source(payload.source),
            review_id=review_id,
        )
        s.add(row)
        s.commit()
        return {"ok": True, "feedback_id": row.id, "status": row.status}
    finally:
        s.close()


@app.get("/api/tickets")
async def get_tickets(request: Request, x_telegram_init_data: str = Header(default=""), limit: int = 20) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    include_media = not _auth_user_is_recovery_scope(auth_user)
    s = SessionLocal()
    try:
        account_id = resolve_support_account_id(
            s,
            account_id=str(auth_user.get("account_id") or "").strip() or None,
            user_tg_id=tg_id,
        )
        items = list_user_tickets(
            s,
            tg_id,
            limit=max(1, min(int(limit), 50)),
            account_id=account_id,
        )
        data = []
        for t in items:
            msgs = list_ticket_messages(s, t.id, limit=1)
            data.append(_ticket_row(t, msgs, include_media=include_media))
        return {"tickets": data}
    finally:
        s.close()


@app.post("/api/tickets/uploads")
async def upload_ticket_attachment(
    request: Request,
    x_telegram_init_data: str = Header(default=""),
    x_upload_filename: str = Header(default=""),
) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    tg_id = int(auth_user.get("id", 0))
    _enforce_beta_rate_limit("ticket_upload", request, identity=f"tg:{tg_id}")
    try:
        raw_bytes = await _read_limited_request_body(
            request,
            max_bytes=SUPPORT_UPLOAD_MAX_BYTES,
            scope="Attachment",
        )
        s = SessionLocal()
        try:
            account_id = resolve_support_account_id(
                s,
                account_id=str(auth_user.get("account_id") or "").strip() or None,
                user_tg_id=tg_id,
            )
        finally:
            s.close()
        uploaded = _store_support_upload(
            owner_tg_id=tg_id,
            owner_account_id=account_id,
            filename=x_upload_filename,
            content_type=request.headers.get("content-type"),
            raw_bytes=raw_bytes,
        )
    except HTTPException as exc:
        _record_security_event(
            "support_upload_reject",
            scope="ticket_upload",
            client_ip=_request_client_ip(request),
            subject=f"tg:{tg_id}",
            reason=_support_upload_reject_reason(exc),
            meta={"status_code": int(exc.status_code)},
        )
        raise
    logger.info(
        "ticket_attachment_uploaded",
        extra={
            "user_id": tg_id,
            "media_type": uploaded["attachment"].get("media_type"),
            "media_file_id": uploaded["attachment"].get("media_file_id"),
            "size": uploaded["attachment_payload"].get("size"),
        },
    )
    return {"ok": True, **uploaded}


@app.get("/api/tickets/attachments/{stored_name}")
async def download_ticket_attachment(
    stored_name: str,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> FileResponse:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    if _auth_user_is_recovery_scope(auth_user):
        raise _auth_http_exception(
            detail="Recovery-сессия не открывает вложения.",
            code="recovery_scope_forbidden",
            status_code=403,
        )
    actor = int(auth_user.get("id", 0))
    clean_name = Path(str(stored_name or "")).name
    if clean_name != stored_name or not re.fullmatch(r"\d{8}-[A-Za-z0-9]{8,64}\.(png|jpg|jpeg|webp|pdf|txt)", clean_name):
        raise HTTPException(status_code=404, detail="Attachment not found")
    _enforce_beta_rate_limit("ticket_attachment_download", request, identity=f"tg:{actor}")
    s = SessionLocal()
    try:
        account_id = resolve_support_account_id(
            s,
            account_id=str(auth_user.get("account_id") or "").strip() or None,
            user_tg_id=actor,
        )
        row = s.query(SupportAttachment).filter(SupportAttachment.stored_name == clean_name).first()
        if not row:
            raise HTTPException(status_code=404, detail="Attachment not found")
        if (
            row.ticket_id is None
            and row.message_id is None
            and row.expires_at is not None
            and row.expires_at <= _utcnow()
        ):
            raise HTTPException(status_code=404, detail="Attachment not found")
        bound_ticket = get_ticket_by_id(s, int(row.ticket_id)) if row.ticket_id is not None else None
        allowed = (
            can_access_ticket(
                bound_ticket,
                actor,
                int(Settings.ADMIN_ID or 0),
                account_id=account_id,
            )
            if bound_ticket is not None
            else row.ticket_id is None
            and can_access_support_attachment(
                row,
                actor,
                int(Settings.ADMIN_ID or 0),
                account_id=account_id,
            )
        )
        if not allowed:
            _record_security_event(
                "support_attachment_denied",
                scope="ticket_attachment_download",
                client_ip=_request_client_ip(request),
                subject=f"tg:{actor}",
                reason="owner_mismatch",
                meta={"stored_name": clean_name},
            )
            raise HTTPException(status_code=403, detail="Access denied")
        upload_root = SUPPORT_UPLOAD_DIR.resolve()
        file_path = (upload_root / clean_name).resolve()
        try:
            file_path.relative_to(upload_root)
        except ValueError:
            raise HTTPException(status_code=404, detail="Attachment not found")
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="Attachment not found")
        headers = {
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
            "Content-Disposition": f'attachment; filename="{_sanitize_ticket_upload_name(row.original_name)}"',
        }
        return FileResponse(
            path=str(file_path),
            media_type=str(row.content_type or "application/octet-stream"),
            headers=headers,
            filename=_sanitize_ticket_upload_name(row.original_name),
        )
    finally:
        s.close()


@app.post("/api/tickets")
async def create_user_ticket(payload: TicketCreateIn, request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    _reject_recovery_ticket_media(auth_user=auth_user, payload=payload)
    tg_id = int(auth_user.get("id", 0))
    _enforce_beta_rate_limit("ticket_create", request, identity=f"tg:{tg_id}")
    reference = _support_attachment_reference(payload)
    with _support_attachment_bind_lock(reference):
        s = SessionLocal()
        try:
            account_id = resolve_support_account_id(
                s,
                account_id=str(auth_user.get("account_id") or "").strip() or None,
                user_tg_id=tg_id,
            )
            attachment, media = _resolve_ticket_attachment(
                s,
                payload=payload,
                actor_tg_id=tg_id,
                account_id=account_id,
            )
            ticket = get_user_active_ticket(s, tg_id, account_id=account_id)
            if not ticket:
                ticket = create_ticket(s, user_tg_id=tg_id, subject=payload.subject, account_id=account_id)
            else:
                claim_legacy_ticket(ticket, actor_tg_id=tg_id, account_id=account_id)
            message = add_ticket_message(
                s,
                ticket_id=ticket.id,
                sender_tg_id=tg_id,
                sender_role="user",
                body=payload.body,
                **media,
            )
            if attachment is not None:
                _bind_ticket_attachment(
                    s,
                    row=attachment,
                    ticket_id=int(ticket.id),
                    message_id=int(message.id),
                )
            set_ticket_status(s, ticket=ticket, status=STATUS_OPEN)
            s.commit()
            ticket_id = int(ticket.id)
            has_attachment = bool(attachment is not None or media.get("media_type") or media.get("media_file_id"))
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()

    if Settings.ADMIN_ID:
        await _telegram_send_message(int(Settings.ADMIN_ID), f"🆕 Новое обращение #{ticket_id} от пользователя {tg_id}.")
    track_event(tg_id=tg_id, event_name="ticket_created", source="webapp", meta={"ticket_id": ticket_id})
    await _maybe_append_support_ai_reply(
        ticket_id=ticket_id,
        user_tg_id=tg_id,
        text=payload.body,
        has_attachment=has_attachment,
    )
    return {
        "ticket": _load_ticket_row(
            ticket_id,
            message_limit=20,
            include_media=not _auth_user_is_recovery_scope(auth_user),
        )
    }


@app.get("/api/tickets/{ticket_id}")
async def get_ticket(ticket_id: int, request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    actor = int(auth_user.get("id", 0))
    recovery_scope = _auth_user_is_recovery_scope(auth_user)
    admin_bypass_tg_id = 0 if recovery_scope else int(Settings.ADMIN_ID or 0)
    s = SessionLocal()
    try:
        account_id = resolve_support_account_id(
            s,
            account_id=str(auth_user.get("account_id") or "").strip() or None,
            user_tg_id=actor,
        )
        ticket = get_ticket_by_id(s, ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        if not can_access_ticket(
            ticket,
            actor,
            admin_bypass_tg_id,
            account_id=account_id,
        ):
            raise HTTPException(status_code=403, detail="Access denied")
        msgs = list_ticket_messages(s, ticket.id, limit=100)
        return {
            "ticket": _ticket_row(
                ticket,
                msgs,
                include_media=not recovery_scope,
            )
        }
    finally:
        s.close()


@app.post("/api/tickets/{ticket_id}/messages")
async def add_ticket_user_message(ticket_id: int, payload: TicketMessageIn, request: Request, x_telegram_init_data: str = Header(default="")) -> dict:
    auth_user = _require_auth_user(x_telegram_init_data, request=request)
    _reject_recovery_ticket_media(auth_user=auth_user, payload=payload)
    actor = int(auth_user.get("id", 0))
    recovery_scope = _auth_user_is_recovery_scope(auth_user)
    admin_actor = bool(_is_admin_tg(actor) and not recovery_scope)
    admin_bypass_tg_id = 0 if recovery_scope else int(Settings.ADMIN_ID or 0)
    reference = _support_attachment_reference(payload)
    with _support_attachment_bind_lock(reference):
        s = SessionLocal()
        try:
            account_id = resolve_support_account_id(
                s,
                account_id=str(auth_user.get("account_id") or "").strip() or None,
                user_tg_id=actor,
            )
            ticket = get_ticket_by_id(s, ticket_id)
            if not ticket:
                raise HTTPException(status_code=404, detail="Ticket not found")
            if not can_access_ticket(
                ticket,
                actor,
                admin_bypass_tg_id,
                account_id=account_id,
            ):
                raise HTTPException(status_code=403, detail="Access denied")
            attachment, media = _resolve_ticket_attachment(
                s,
                payload=payload,
                actor_tg_id=actor,
                account_id=account_id,
            )
            role = "admin" if admin_actor else "user"
            if role == "user":
                claim_legacy_ticket(ticket, actor_tg_id=actor, account_id=account_id)
            message = add_ticket_message(
                s,
                ticket_id=ticket.id,
                sender_tg_id=actor,
                sender_role=role,
                body=payload.body,
                **media,
            )
            if attachment is not None:
                _bind_ticket_attachment(
                    s,
                    row=attachment,
                    ticket_id=int(ticket.id),
                    message_id=int(message.id),
                )
            set_ticket_status(
                s,
                ticket=ticket,
                status=STATUS_IN_PROGRESS if role == "admin" else STATUS_OPEN,
                assigned_admin_tg_id=int(Settings.ADMIN_ID) if role == "admin" and Settings.ADMIN_ID else None,
            )
            s.commit()
            ticket_user_tg_id = resolve_ticket_notification_tg_id(s, ticket)
            has_attachment = bool(attachment is not None or media.get("media_type") or media.get("media_file_id"))
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()

    if role == "admin":
        if ticket_user_tg_id is None:
            logger.warning(
                "support ticket notification skipped ticket=%s reason=no_telegram_target",
                ticket_id,
            )
        else:
            await _telegram_send_message(ticket_user_tg_id, f"💬 Новый ответ оператора в обращении #{ticket_id}.")
    elif Settings.ADMIN_ID:
        await _telegram_send_message(int(Settings.ADMIN_ID), f"🆕 Новое сообщение в обращении #{ticket_id} от {actor}.")
    if role == "user":
        await _maybe_append_support_ai_reply(
            ticket_id=ticket_id,
            user_tg_id=actor,
            text=payload.body,
            has_attachment=has_attachment,
        )
    return {
        "ticket": _load_ticket_row(
            ticket_id,
            message_limit=100,
            include_media=not recovery_scope,
        )
    }
