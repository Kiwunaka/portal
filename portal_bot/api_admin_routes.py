"""Administrative operations, safety controls and action-intent routes.

Loaded by the api composition root in source order. Public symbols are
re-exported for backwards compatibility.
"""

try:
    from .module_slices import bootstrap_slice
except ImportError:
    from module_slices import bootstrap_slice

bootstrap_slice(globals())

@app.get("/api/admin/summary")
async def admin_summary(x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    stale_after_seconds = max(300, int(os.getenv("NODE_METRICS_STALE_AFTER_SECONDS", "900")))
    now = _utcnow()
    since_24h = now - timedelta(hours=24)
    since_7d = now - timedelta(days=7)
    s = SessionLocal()
    try:
        active_user_filter = _effective_active_user_filter(now=now)
        user_sub_type = func.upper(func.coalesce(User.sub_type, ""))
        user_counts = (
            s.query(
                func.count(User.tg_id).label("total_users"),
                func.sum(case((active_user_filter, 1), else_=0)).label("active_users"),
                func.sum(case((user_sub_type == "FREE", 1), else_=0)).label("free_users"),
                func.sum(case((user_sub_type == "PAID", 1), else_=0)).label("paid_users"),
                func.sum(case((and_(active_user_filter, _premium_entitlement_filter()), 1), else_=0)).label("active_nonfree_accounts"),
                func.sum(case((and_(active_user_filter, _trial_entitlement_filter()), 1), else_=0)).label("trial_accounts"),
                func.sum(case((and_(active_user_filter, _bonus_entitlement_filter()), 1), else_=0)).label("bonus_accounts"),
            )
            .one()
        )
        total_users = int(getattr(user_counts, "total_users", 0) or 0)
        active_users = int(getattr(user_counts, "active_users", 0) or 0)
        free_users = int(getattr(user_counts, "free_users", 0) or 0)
        paid_users = int(getattr(user_counts, "paid_users", 0) or 0)
        active_nonfree_accounts = int(getattr(user_counts, "active_nonfree_accounts", 0) or 0)
        trial_accounts = int(getattr(user_counts, "trial_accounts", 0) or 0)
        bonus_accounts = int(getattr(user_counts, "bonus_accounts", 0) or 0)
        unique_install_ids_total = (
            s.query(func.count(func.distinct(User.app_install_id)))
            .filter(User.tg_id > 0)
            .filter(~_manual_test_user_filter())
            .filter(User.app_install_id.isnot(None))
            .scalar()
            or 0
        )
        unique_install_ids_24h = (
            s.query(func.count(func.distinct(User.app_install_id)))
            .filter(User.tg_id > 0)
            .filter(~_manual_test_user_filter())
            .filter(User.app_install_id.isnot(None))
            .filter(User.app_last_seen_at.isnot(None))
            .filter(User.app_last_seen_at >= since_24h)
            .scalar()
            or 0
        )
        unique_install_ids_7d = (
            s.query(func.count(func.distinct(User.app_install_id)))
            .filter(User.tg_id > 0)
            .filter(~_manual_test_user_filter())
            .filter(User.app_install_id.isnot(None))
            .filter(User.app_last_seen_at.isnot(None))
            .filter(User.app_last_seen_at >= since_7d)
            .scalar()
            or 0
        )
        open_tickets = s.query(func.count(SupportTicket.id)).filter(SupportTicket.status != STATUS_CLOSED).scalar() or 0
        total_nodes = s.query(func.count(Node.id)).filter(Node.enabled == True).scalar() or 0
        healthy_nodes = s.query(func.count(Node.id)).filter(Node.enabled == True, Node.is_healthy == True).scalar() or 0
        free_node_enabled = bool(
            s.query(Node.id).filter(Node.enabled == True, func.lower(func.coalesce(Node.code, "")) == "free").first()
        )
        observer_counts = (
            s.query(
                func.count(ObserverUserState.tg_id).label("total_rows"),
                func.sum(case((ObserverUserState.state == "watch", 1), else_=0)).label("watch_users"),
                func.sum(case((ObserverUserState.state == "suspicious", 1), else_=0)).label("suspicious_users"),
                func.sum(
                    case(
                        (and_(ObserverUserState.last_observed_at.isnot(None), ObserverUserState.last_observed_at >= since_24h), 1),
                        else_=0,
                    )
                ).label("seen_24h"),
            )
            .one()
        )
        observer_watch_users = int(getattr(observer_counts, "watch_users", 0) or 0)
        observer_suspicious_users = int(getattr(observer_counts, "suspicious_users", 0) or 0)
        observer_seen_accounts_24h = int(getattr(observer_counts, "seen_24h", 0) or 0)
        observer_total_rows = int(getattr(observer_counts, "total_rows", 0) or 0)
        observer_secret_filter = func.length(func.trim(func.coalesce(Node.observer_push_secret, ""))) > 0
        observer_configured_nodes = (
            s.query(func.count(Node.id))
            .filter(Node.enabled == True)
            .filter(observer_secret_filter)
            .scalar()
            or 0
        )
        observer_fresh_nodes = (
            s.query(func.count(Node.id))
            .filter(Node.enabled == True)
            .filter(observer_secret_filter)
            .filter(Node.observer_last_push_at.isnot(None))
            .filter(Node.observer_last_push_at >= now - timedelta(seconds=observer_stale_after_seconds()))
            .scalar()
            or 0
        )
        metrics_status = _ops_build_admin_metrics_status_snapshot(
            s=s,
            now=now,
            stale_after_seconds=stale_after_seconds,
        )
        metrics_age_seconds = metrics_status.get("age_seconds")
        metrics_quality_status = "missing" if not metrics_status.get("nodes") else str(metrics_status.get("status") or "stale")
        if unique_install_ids_7d > 0:
            app_installs_quality_status = "ok"
        elif int(unique_install_ids_total or 0) > 0:
            app_installs_quality_status = "stale"
        else:
            app_installs_quality_status = "missing"
        if observer_fresh_nodes > 0 or observer_seen_accounts_24h > 0:
            observer_quality_status = "ok"
        elif observer_configured_nodes > 0 or observer_total_rows > 0:
            observer_quality_status = "stale"
        else:
            observer_quality_status = "missing"
        payment_callback_failures_24h = (
            s.query(func.count(ExternalPaymentEvent.id))
            .filter(
                ExternalPaymentEvent.created_at >= since_24h,
                or_(
                    ExternalPaymentEvent.signature_ok == False,
                    ExternalPaymentEvent.processed_ok == False,
                ),
            )
            .scalar()
            or 0
        )
        subscription_numeric_fallbacks_24h = (
            s.query(func.count(Event.id))
            .filter(
                Event.created_at >= since_24h,
                Event.event_name == "subscription_numeric_fallback",
            )
            .scalar()
            or 0
        )
        expiring_3d = (
            s.query(func.count(User.tg_id))
            .filter(User.tg_id > 0)
            .filter(func.upper(func.coalesce(User.sub_type, "")) != "MANUAL")
            .filter(User.is_active == True)
            .filter(User.expiry_at.isnot(None))
            .filter(User.expiry_at >= now, User.expiry_at <= now + timedelta(days=3))
            .scalar()
            or 0
        )
        expired_7d = (
            s.query(func.count(func.distinct(Event.tg_id)))
            .filter(Event.created_at >= since_7d, Event.event_name == "expired")
            .scalar()
            or 0
        )
        reactivation_candidates = (
            s.query(func.count(User.tg_id))
            .filter(User.tg_id > 0)
            .filter(func.upper(func.coalesce(User.sub_type, "")) != "MANUAL")
            .filter(
                or_(
                    User.expiry_at <= now,
                    and_(func.upper(func.coalesce(User.sub_type, "")) == "FREE", User.is_active == False),
                )
            )
            .scalar()
            or 0
        )
        bonus_event_rows = (
            s.query(Event.event_name, func.count(Event.id))
            .filter(Event.created_at >= since_24h)
            .filter(
                Event.event_name.in_(
                    [
                        "promo_channel_activated",
                        "promo_channel_denied",
                        "promo_redeemed",
                        "promo_redeem_denied",
                        "gift_redeemed",
                        "gift_redeem_denied",
                    ]
                )
            )
            .group_by(Event.event_name)
            .all()
        )
        bonus_event_map = {str(name or ""): int(count or 0) for name, count in bonus_event_rows}
        retention_ping_rows = (
            s.query(Event.meta_json)
            .filter(Event.created_at >= since_24h, Event.event_name == "retention_ping")
            .all()
        )
        retention_ping_map = {
            "welcome": 0,
            "t3": 0,
            "t1": 0,
            "t0": 0,
            "reactivation": 0,
            "start99_offer": 0,
        }
        for row in retention_ping_rows:
            meta = _json_obj(getattr(row, "meta_json", None))
            flow_key = _normalize_retention_flow(meta.get("flow"))
            if flow_key:
                retention_ping_map[flow_key] = int(retention_ping_map.get(flow_key, 0)) + 1
        last_samples = (
            s.query(Node.code, Node.health_score, Node.panel_latency_ms, Node.active_clients, Node.last_health_at)
            .filter(Node.enabled == True)
            .order_by(Node.health_score.desc(), Node.weight.desc())
            .limit(10)
            .all()
        )
        return {
            "actor_tg_id": actor,
            "users": {
                "total": int(total_users),
                "active": int(active_users),
                "free": int(free_users),
                "paid": int(paid_users),
                "active_nonfree_accounts": int(active_nonfree_accounts),
                "trial_accounts": int(trial_accounts),
                "bonus_accounts": int(bonus_accounts),
                "unique_install_ids_24h": int(unique_install_ids_24h),
                "unique_install_ids_7d": int(unique_install_ids_7d),
                "observer_seen_accounts_24h": int(observer_seen_accounts_24h),
            },
            "data_quality": {
                "metrics": {
                    "status": metrics_quality_status,
                    "badge": _quality_badge(metrics_quality_status),
                    "missing": bool(metrics_quality_status == "missing"),
                    "age_seconds": metrics_age_seconds,
                },
                "app_installs": {
                    "status": app_installs_quality_status,
                    "badge": _quality_badge(app_installs_quality_status),
                    "missing": bool(app_installs_quality_status == "missing"),
                    "unique_install_ids_total": int(unique_install_ids_total),
                    "unique_install_ids_24h": int(unique_install_ids_24h),
                    "unique_install_ids_7d": int(unique_install_ids_7d),
                },
                "observer": {
                    "status": observer_quality_status,
                    "badge": _quality_badge(observer_quality_status),
                    "missing": bool(observer_quality_status == "missing"),
                    "configured_nodes": int(observer_configured_nodes),
                    "fresh_nodes": int(observer_fresh_nodes),
                    "seen_accounts_24h": int(observer_seen_accounts_24h),
                },
            },
            "retention": {
                "expiring_3d": int(expiring_3d),
                "expired_7d": int(expired_7d),
                "reactivation_candidates": int(reactivation_candidates),
                "pings_24h": {
                    "welcome": int(retention_ping_map.get("welcome", 0)),
                    "t3": int(retention_ping_map.get("t3", 0)),
                    "t1": int(retention_ping_map.get("t1", 0)),
                    "t0": int(retention_ping_map.get("t0", 0)),
                    "reactivation": int(retention_ping_map.get("reactivation", 0)),
                    "start99_offer": int(retention_ping_map.get("start99_offer", 0)),
                },
            },
            "tickets": {"open": int(open_tickets)},
            "nodes": {"total": int(total_nodes), "healthy": int(healthy_nodes)},
            "observer": {
                "watch_users": int(observer_watch_users),
                "suspicious_users": int(observer_suspicious_users),
            },
            "errors": {
                "stale_metrics": bool(metrics_status.get("status") != "fresh"),
                "unhealthy_nodes": max(0, int(total_nodes) - int(healthy_nodes)),
                "open_tickets": int(open_tickets),
                "payment_callback_failures_24h": int(payment_callback_failures_24h),
                "subscription_numeric_fallbacks_24h": int(subscription_numeric_fallbacks_24h),
            },
            "resilience": {
                "single_point_risk": bool(int(healthy_nodes) < 2),
                "free_node_enabled": bool(free_node_enabled),
            },
            "bonus_events_24h": {
                "channel_activated": int(bonus_event_map.get("promo_channel_activated", 0)),
                "channel_denied": int(bonus_event_map.get("promo_channel_denied", 0)),
                "promo_redeemed": int(bonus_event_map.get("promo_redeemed", 0)),
                "promo_denied": int(bonus_event_map.get("promo_redeem_denied", 0)),
                "gift_redeemed": int(bonus_event_map.get("gift_redeemed", 0)),
                "gift_denied": int(bonus_event_map.get("gift_redeem_denied", 0)),
            },
            "top_nodes": [
                {
                    "code": n.code,
                    "health_score": float(n.health_score or 0.0),
                    "panel_latency_ms": n.panel_latency_ms,
                    "active_clients": int(n.active_clients or 0),
                    "last_health_at": _safe_iso(n.last_health_at),
                }
                for n in last_samples
            ],
        }
    finally:
        s.close()


ADMIN_PAYMENT_RECONCILE_STATUSES = {
    "created",
    "pending",
    "paid",
    "failed",
    "cancelled",
    "refunded",
    "chargeback",
    "manual_review",
    "pending_verification",
}


def _admin_payment_event_payload(event: ExternalPaymentEvent | None) -> dict[str, Any] | None:
    if not event:
        return None
    return {
        "id": int(event.id),
        "provider": str(event.provider or ""),
        "event_type": str(event.event_type or ""),
        "external_id": str(event.external_id or ""),
        "order_id": str(event.order_id or "") or None,
        "signature_ok": bool(event.signature_ok),
        "processed_ok": bool(event.processed_ok),
        "created_at": _safe_iso(event.created_at),
    }


def _admin_payment_order_payload(*, s, order: ExternalOrder) -> dict[str, Any]:
    events_q = s.query(ExternalPaymentEvent).filter(
        ExternalPaymentEvent.provider == str(order.provider or ""),
        ExternalPaymentEvent.order_id == str(order.order_id or ""),
    )
    last_event = events_q.order_by(ExternalPaymentEvent.created_at.desc(), ExternalPaymentEvent.id.desc()).first()
    event_count = events_q.count()
    user = None
    if getattr(order, "tg_id", None) is not None:
        user = s.query(User).filter(User.tg_id == int(order.tg_id)).first()
    return {
        "id": int(order.id),
        "order_id": str(order.order_id or ""),
        "provider": str(order.provider or ""),
        "tg_id": int(order.tg_id) if getattr(order, "tg_id", None) is not None else None,
        "user": {
            "tg_id": int(user.tg_id),
            "username": user.username,
            "display_name": getattr(user, "display_name", None),
            "status": _user_effective_status(user),
        }
        if user
        else None,
        "plan_code": str(order.plan_code or "") or None,
        "amount": float(order.amount or 0),
        "currency": str(order.currency or "RUB"),
        "status": str(order.status or "created"),
        "source": str(order.source or "") or None,
        "campaign": str(order.campaign or "") or None,
        "promo_code": str(order.promo_code or "") or None,
        "created_at": _safe_iso(order.created_at),
        "paid_at": _safe_iso(order.paid_at),
        "event_count": int(event_count or 0),
        "last_event": _admin_payment_event_payload(last_event),
    }


def _payment_reversal_needs_operator(order: ExternalOrder) -> bool:
    if str(order.status or "").strip().lower() not in {"refunded", "chargeback"}:
        return False
    meta = _external_order_meta(order)
    reversal = meta.get("reversal") if isinstance(meta.get("reversal"), dict) else {}
    fulfillment = meta.get("fulfillment") if isinstance(meta.get("fulfillment"), dict) else {}
    reconciliation_status = str(reversal.get("reconciliation_status") or "").strip().lower()
    fulfillment_status = str(fulfillment.get("status") or "").strip().lower()
    return not bool(
        reversal.get("operator_action_required") is False
        and reconciliation_status in {"reversed", "already_reversed"}
        and fulfillment_status == "reversed"
    )


def _payment_reversal_problem_time(order: ExternalOrder) -> datetime:
    meta = _external_order_meta(order)
    reversal = meta.get("reversal") if isinstance(meta.get("reversal"), dict) else {}
    raw = str(reversal.get("recorded_at") or "").strip()[:128]
    if raw:
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if parsed.tzinfo is not None:
                parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
            return parsed
        except (TypeError, ValueError, OverflowError):
            pass
    return order.created_at or datetime.min


def _admin_payment_period_bounds(period: str) -> tuple[str, datetime, datetime]:
    period_norm = str(period or "7d").strip().lower()
    now = _utcnow()
    if period_norm in {"today", "day", "1d"}:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        label = "today"
    elif period_norm in {"30d", "month"}:
        start = now - timedelta(days=30)
        label = "30d"
    else:
        start = now - timedelta(days=7)
        label = "7d"
    return label, start, now


def _count_funnel_sessions(
    s,
    *,
    from_dt: datetime,
    to_dt: datetime,
    stages: set[str] | None = None,
    event_names: set[str] | None = None,
) -> int:
    query = (
        s.query(func.count(func.distinct(FunnelEvent.session_id)))
        .filter(FunnelEvent.created_at >= from_dt, FunnelEvent.created_at <= to_dt)
    )
    if stages:
        query = query.filter(FunnelEvent.stage.in_(sorted(stages)))
    if event_names:
        query = query.filter(FunnelEvent.event_name.in_(sorted(event_names)))
    return int(query.scalar() or 0)


def _count_known_event_users(
    s,
    *,
    from_dt: datetime,
    to_dt: datetime,
    event_names: set[str],
) -> int:
    return int(
        s.query(func.count(func.distinct(Event.tg_id)))
        .filter(Event.created_at >= from_dt, Event.created_at <= to_dt)
        .filter(Event.event_name.in_(sorted(event_names)))
        .scalar()
        or 0
    )


def _count_pay_attempt_users(
    s,
    *,
    from_dt: datetime,
    to_dt: datetime,
    statuses: set[str] | None = None,
) -> int:
    query = (
        s.query(func.count(func.distinct(PayAttempt.tg_id)))
        .filter(PayAttempt.started_at >= from_dt, PayAttempt.started_at <= to_dt)
    )
    if statuses:
        query = query.filter(
            func.lower(func.coalesce(PayAttempt.status, "")).in_(sorted(statuses))
        )
    return int(query.scalar() or 0)


def _admin_payments_summary_payload(*, s, period: str) -> dict[str, Any]:
    label, from_dt, to_dt = _admin_payment_period_bounds(period)
    paid_time = func.coalesce(ExternalOrder.paid_at, ExternalOrder.created_at)
    paid_rows = (
        s.query(
            ExternalOrder.currency,
            func.count(ExternalOrder.id),
            func.sum(func.coalesce(ExternalOrder.amount, 0.0)),
        )
        .filter(func.lower(func.coalesce(ExternalOrder.status, "")) == "paid")
        .filter(paid_time >= from_dt, paid_time <= to_dt)
        .group_by(ExternalOrder.currency)
        .all()
    )
    revenue_by_currency = [
        {
            "currency": str(currency or "RUB"),
            "paid_count": int(count or 0),
            "revenue": round(float(total or 0.0), 2),
        }
        for currency, count, total in paid_rows
    ]
    primary_revenue = next((row for row in revenue_by_currency if row["currency"].upper() == "RUB"), None)
    if not primary_revenue and revenue_by_currency:
        primary_revenue = revenue_by_currency[0]
    if not primary_revenue:
        primary_revenue = {"currency": "RUB", "paid_count": 0, "revenue": 0.0}

    status_counts = {
        str(status or "created"): int(count or 0)
        for status, count in (
            s.query(ExternalOrder.status, func.count(ExternalOrder.id))
            .filter(ExternalOrder.created_at >= from_dt, ExternalOrder.created_at <= to_dt)
            .group_by(ExternalOrder.status)
            .all()
        )
    }
    pending_count = sum(int(status_counts.get(status, 0)) for status in ("created", "pending", "pending_verification"))
    manual_review_count = int(status_counts.get("manual_review", 0))
    reversal_rows = (
        s.query(ExternalOrder)
        .filter(ExternalOrder.status.in_(["refunded", "chargeback"]))
        .all()
    )
    reversal_problem_rows = [row for row in reversal_rows if _payment_reversal_needs_operator(row)]
    reversal_problem_count = len(reversal_problem_rows)
    failed_count = (
        sum(int(status_counts.get(status, 0)) for status in ("failed", "cancelled"))
        + reversal_problem_count
    )

    site_checkout_intent = _count_funnel_sessions(
        s,
        from_dt=from_dt,
        to_dt=to_dt,
        stages={"checkout_view", "checkout_start"},
    )
    known_buy_clicks = _count_known_event_users(s, from_dt=from_dt, to_dt=to_dt, event_names={"clicked_pay"})
    known_checkout_events = _count_known_event_users(s, from_dt=from_dt, to_dt=to_dt, event_names={"pay_started"})
    pay_attempts_started = _count_pay_attempt_users(s, from_dt=from_dt, to_dt=to_dt)
    buy_clicks = site_checkout_intent + known_buy_clicks
    checkout_started = site_checkout_intent + max(known_checkout_events, pay_attempts_started)
    paid_count = int(primary_revenue.get("paid_count") or 0)

    ordinary_problem_rows = (
        s.query(ExternalOrder)
        .filter(ExternalOrder.created_at >= from_dt, ExternalOrder.created_at <= to_dt)
        .filter(ExternalOrder.status.in_([
            "created",
            "pending",
            "pending_verification",
            "manual_review",
            "failed",
            "cancelled",
        ]))
        .order_by(ExternalOrder.created_at.desc(), ExternalOrder.id.desc())
        .limit(25)
        .all()
    )
    recent_problem_orders = [
        row
        for _problem_at, row in sorted(
            [
                *((row.created_at or datetime.min, row) for row in ordinary_problem_rows),
                *((_payment_reversal_problem_time(row), row) for row in reversal_problem_rows),
            ],
            key=lambda item: (item[0], int(item[1].id or 0)),
            reverse=True,
        )[:25]
    ]

    return {
        "ok": True,
        "period": {
            "key": label,
            "from": _safe_iso(from_dt),
            "to": _safe_iso(to_dt),
        },
        "revenue": {
            "currency": primary_revenue["currency"],
            "paid_count": paid_count,
            "amount": float(primary_revenue["revenue"]),
            "by_currency": revenue_by_currency,
        },
        "status_counts": status_counts,
        "attention": {
            "pending_count": int(pending_count),
            "manual_review_count": int(manual_review_count),
            "failed_count": int(failed_count),
            "problem_count": int(pending_count + manual_review_count + failed_count),
        },
        "abandoned": {
            "buy_clicks": int(buy_clicks),
            "checkout_started": int(checkout_started),
            "paid": int(paid_count),
            "buy_click_not_paid": max(0, int(buy_clicks) - int(paid_count)),
            "checkout_not_paid": max(0, int(checkout_started) - int(paid_count)),
            "note": "Диагностический funnel-счетчик; бухгалтерская правда остается в signed payment callbacks и external_orders.",
        },
        "problem_orders": [_admin_payment_order_payload(s=s, order=row) for row in recent_problem_orders],
    }


@app.get("/api/admin/payments/summary")
async def admin_payments_summary(
    x_telegram_init_data: str = Header(default=""),
    period: str = Query(default="7d"),
) -> dict[str, Any]:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        return _admin_payments_summary_payload(s=s, period=period)
    finally:
        s.close()


@app.get("/api/admin/payments/orders")
async def admin_payment_orders(
    x_telegram_init_data: str = Header(default=""),
    status: str = "",
    provider: str = "",
    q: str = "",
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    _require_admin(x_telegram_init_data)
    lim = max(1, min(int(limit), 250))
    off = max(0, int(offset))
    status_norm = str(status or "").strip().lower()
    provider_norm = _normalize_provider(provider) if provider else ""
    q_norm = str(q or "").strip()
    s = SessionLocal()
    try:
        query = s.query(ExternalOrder)
        if status_norm:
            query = query.filter(func.lower(func.coalesce(ExternalOrder.status, "")) == status_norm)
        if provider_norm:
            query = query.filter(func.lower(func.coalesce(ExternalOrder.provider, "")) == provider_norm)
        if q_norm:
            filters = [
                ExternalOrder.order_id.ilike(f"%{q_norm}%"),
                ExternalOrder.provider.ilike(f"%{q_norm}%"),
                ExternalOrder.plan_code.ilike(f"%{q_norm}%"),
                ExternalOrder.source.ilike(f"%{q_norm}%"),
                ExternalOrder.campaign.ilike(f"%{q_norm}%"),
                ExternalOrder.promo_code.ilike(f"%{q_norm}%"),
            ]
            if q_norm.lstrip("-").isdigit():
                filters.append(ExternalOrder.tg_id == int(q_norm))
            query = query.filter(or_(*filters))
        total = query.count()
        rows = query.order_by(ExternalOrder.created_at.desc(), ExternalOrder.id.desc()).offset(off).limit(lim).all()
        return {
            "orders": [_admin_payment_order_payload(s=s, order=row) for row in rows],
            "total": int(total or 0),
            "limit": lim,
            "offset": off,
        }
    finally:
        s.close()


@app.get("/api/admin/payments/orders/{provider}/{order_id}")
async def admin_payment_order_detail(
    provider: str,
    order_id: str,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    _require_admin(x_telegram_init_data)
    provider_norm = _normalize_provider(provider)
    order_norm = str(order_id or "").strip()
    s = SessionLocal()
    try:
        order = (
            s.query(ExternalOrder)
            .filter(
                ExternalOrder.provider == provider_norm,
                ExternalOrder.order_id == order_norm,
            )
            .first()
        )
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return {"order": _admin_payment_order_payload(s=s, order=order)}
    finally:
        s.close()


@app.post("/api/admin/payments/orders/{provider}/{order_id}/reconcile")
async def admin_payment_order_reconcile(
    provider: str,
    order_id: str,
    payload: AdminPaymentReconcileIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    provider_norm = _normalize_provider(provider)
    order_norm = str(order_id or "").strip()
    if not provider_norm or not order_norm:
        raise HTTPException(status_code=400, detail="Provider and order_id are required")
    guarded_payload = {"note": str(payload.note or ""), "status": payload.status}
    if not str(request.headers.get("X-Admin-Intent-Id") or "").strip():
        return await _execute_admin_guarded_action(
            actor_tg_id=actor,
            action="payment.reconcile",
            target_type="payment",
            target_id="0",
            payload=guarded_payload,
            request=request,
        )
    s = SessionLocal()
    try:
        order = (
            s.query(ExternalOrder)
            .filter(ExternalOrder.provider == provider_norm, ExternalOrder.order_id == order_norm)
            .first()
        )
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        target_id = str(int(order.id))
    finally:
        s.close()
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="payment.reconcile",
        target_type="payment",
        target_id=target_id,
        payload=guarded_payload,
        request=request,
    )


@app.get("/api/admin/users")
async def admin_users(
    x_telegram_init_data: str = Header(default=""),
    q: str = "",
    status: str = "",
    origin: str = "",
    observer_state: str = "",
    sort: str = "created_desc",
    limit: int = 50,
    offset: int = 0,
    page: int = 0,
    page_size: int = 0,
) -> dict:
    _require_admin(x_telegram_init_data)
    now = _utcnow()
    page_size_value = max(1, min(int(page_size or limit or 50), 200))
    if int(page or 0) > 0:
        offset_value = max(0, (int(page) - 1) * page_size_value)
        page_value = int(page)
    else:
        offset_value = max(0, int(offset))
        page_value = (offset_value // page_size_value) + 1
    s = SessionLocal()
    try:
        query = s.query(User)
        status_filter = _admin_user_status_filter(status, now=now)
        if status_filter is not None:
            query = query.filter(status_filter)
        origin_filter = _admin_user_origin_filter(origin)
        if origin_filter is not None:
            query = query.filter(origin_filter)
        observer_state_norm = _normalize_observer_state_filter(observer_state)
        if observer_state_norm == "ok":
            query = query.outerjoin(ObserverUserState, ObserverUserState.tg_id == User.tg_id).filter(
                or_(ObserverUserState.tg_id.is_(None), ObserverUserState.state == "ok")
            )
        elif observer_state_norm in {"watch", "suspicious"}:
            query = query.join(ObserverUserState, ObserverUserState.tg_id == User.tg_id).filter(
                ObserverUserState.state == observer_state_norm
            )
        query = _apply_admin_user_search(query, q)
        sort_norm = str(sort or "created_desc").strip().lower()
        if sort_norm == "created_asc":
            query = query.order_by(User.created_at.asc(), User.tg_id.asc())
        elif sort_norm == "expiry_asc":
            query = query.order_by(User.expiry_at.asc(), User.tg_id.asc())
        elif sort_norm == "expiry_desc":
            query = query.order_by(User.expiry_at.desc(), User.tg_id.desc())
        elif sort_norm == "name_asc":
            query = query.order_by(
                func.lower(func.coalesce(User.display_name, User.username, User.email, "")),
                User.tg_id.asc(),
            )
        elif sort_norm == "name_desc":
            query = query.order_by(
                func.lower(func.coalesce(User.display_name, User.username, User.email, "")).desc(),
                User.tg_id.desc(),
            )
        else:
            sort_norm = "created_desc"
            query = query.order_by(User.created_at.desc(), User.tg_id.desc())
        total = int(query.count() or 0)
        rows = (
            query.offset(offset_value)
            .limit(page_size_value)
            .all()
        )
        observer_map = get_observer_state_map(
            s=s,
            tg_ids=[int(getattr(row, "tg_id", 0) or 0) for row in rows],
        )
        return {
            "page": int(page_value),
            "page_size": int(page_size_value),
            "total": int(total),
            "sort": sort_norm,
            "users": [
                _serialize_admin_user_row(
                    u,
                    now=now,
                    observer_snapshot=observer_map.get(int(getattr(u, "tg_id", 0) or 0)),
                )
                for u in rows
            ],
        }
    finally:
        s.close()


def _admin_select_users_for_segment(
    *,
    s,
    segment: str,
    q: str = "",
    tg_ids: list[int] | None = None,
    limit: int = 100,
) -> list[User]:
    seg = str(segment or "active").strip().lower()
    now = _utcnow()
    query = s.query(User)
    if seg in {"all_active"}:
        seg = "active"
    if seg in {"manual"}:
        seg = "manual_test"

    if seg == "all":
        query = query.filter(User.tg_id > 0).filter(~_manual_test_user_filter())
    elif seg == "active":
        query = query.filter(_admin_user_status_filter("active", now=now))
    elif seg == "inactive":
        query = query.filter(_admin_user_status_filter("inactive", now=now))
    elif seg == "expired":
        query = query.filter(_admin_user_status_filter("expired", now=now))
    elif seg == "blocked":
        query = query.filter(_admin_user_status_filter("blocked", now=now))
    elif seg == "paid":
        query = query.filter(User.tg_id > 0).filter(~_manual_test_user_filter()).filter(func.upper(User.sub_type) == "PAID")
    elif seg == "free":
        query = query.filter(User.tg_id > 0).filter(~_manual_test_user_filter()).filter(func.upper(User.sub_type) == "FREE")
    elif seg == "manual_test":
        query = query.filter(_manual_test_user_filter())
    elif seg == "custom":
        picked = sorted({int(x) for x in (tg_ids or [])})
        if not picked:
            return []
        query = query.filter(User.tg_id.in_(picked))
    else:
        raise HTTPException(status_code=400, detail="Unsupported segment")

    query = _apply_admin_user_search(query, q)

    rows = (
        query.order_by(User.created_at.desc(), User.tg_id.desc())
        .limit(max(1, min(int(limit), 500)))
        .all()
    )
    return rows


def _admin_subscription_url(user: User) -> str:
    token = str(getattr(user, "sub_token", "") or "").strip()
    token_or_id = token or str(int(user.tg_id))
    return build_subscription_url(token_or_id)


def _bytes_to_gb(value: int) -> float:
    return round(float(max(0, int(value or 0))) / float(1024**3), 3)


async def _admin_user_keys_state(user: User, *, nodes: list) -> dict[str, Any]:
    allowed_nodes = _nodes_for_user(user, nodes)
    allowed_by_code = {str(getattr(n, "code", "") or ""): n for n in allowed_nodes}
    expected_sub_id = str(getattr(user, "sub_token", "") or user.tg_id)
    policy_by_code: dict[str, dict[str, Any]] = {}
    observed_ip_count_24h = 0
    s = SessionLocal()
    try:
        policy_rows = s.query(UserKeyPolicy).filter(UserKeyPolicy.tg_id == int(user.tg_id)).all()
        for row in policy_rows:
            policy_by_code[str(row.node_code or "").strip().lower()] = _serialize_key_policy(row)
        observer_row = s.query(ObserverUserState).filter(ObserverUserState.tg_id == int(user.tg_id)).first()
        observed_ip_count_24h = int(getattr(observer_row, "observed_ip_count_24h", 0) or 0)
    finally:
        s.close()
    panel_rows: list[dict] = []
    panel_error = ""

    panel = ControlPanel()
    try:
        await panel.login()
        panel_rows = await panel.get_user_key_snapshots(
            tg_id=int(user.tg_id),
            node_codes=[str(code) for code in allowed_by_code.keys() if str(code).strip()],
        )
    except Exception as exc:
        panel_error = str(exc)[:200]
    finally:
        await panel.close()

    keys: list[dict[str, Any]] = []
    online_count = 0
    online_connections_now = 0
    enabled_count = 0
    total_up = 0
    total_down = 0
    mismatch_count = 0
    online_node_codes_now: list[str] = []
    saw_ip_count = False

    for row in panel_rows:
        code = str(row.get("node_code") or "").strip()
        node = allowed_by_code.get(code)
        client = row.get("client") or {}
        runtime = row.get("runtime") or {}
        exists = bool(client)
        current_sub_id = str(client.get("subId", "") or "")
        sub_id_match = bool(exists and current_sub_id == expected_sub_id)
        enabled = bool(runtime.get("enable", client.get("enable", False))) if exists else False
        online_raw = runtime.get("online") if isinstance(runtime, dict) else None
        online = bool(online_raw) if online_raw is not None else None
        up = int((runtime or {}).get("up", 0) or 0)
        down = int((runtime or {}).get("down", 0) or 0)
        total = int((runtime or {}).get("total", up + down) or (up + down))
        last_online_at = str((runtime or {}).get("last_online_at") or "") or None
        last_online_age_seconds = (runtime or {}).get("last_online_age_seconds")
        ip_count_raw = (runtime or {}).get("ip_count")
        current_connections = 0
        if ip_count_raw is not None:
            try:
                current_connections = max(0, int(ip_count_raw))
                saw_ip_count = True
            except Exception:
                current_connections = 0
        elif online is True:
            current_connections = 1
        policy = policy_by_code.get(code.lower(), {})
        link = (
            _generate_vless_link(user_uuid=str(user.uuid or ""), node=node, name=_node_label_ru(node.code, node.name))
            if node and str(user.uuid or "").strip()
            else ""
        )
        if online is True:
            online_count += 1
            online_connections_now += current_connections
            if code:
                online_node_codes_now.append(code)
        if enabled:
            enabled_count += 1
        if exists and not sub_id_match:
            mismatch_count += 1
        total_up += up
        total_down += down
        keys.append(
            {
                "node_code": code,
                "node_name": str(getattr(node, "name", row.get("node_name", "")) or ""),
                "node_host": str(getattr(node, "host", row.get("node_host", "")) or ""),
                "exists": exists,
                "client_uuid": str(client.get("id", "") or ""),
                "panel_email": str(client.get("email", "") or ""),
                "enabled": enabled,
                "online": online,
                "current_connections": int(current_connections),
                "sub_id": current_sub_id,
                "expected_sub_id": expected_sub_id,
                "sub_id_match": sub_id_match,
                "up_bytes": up,
                "down_bytes": down,
                "total_bytes": total,
                "total_gb": _bytes_to_gb(total),
                "last_online_at": last_online_at,
                "last_online_age_seconds": int(last_online_age_seconds) if last_online_age_seconds is not None else None,
                "vless_link": link,
                "panel_error": str(row.get("error", "") or "")[:200] or None,
                "policy": policy or None,
            }
        )

    keys.sort(key=lambda item: str(item.get("node_code") or ""))
    failed_panel_rows = [row for row in panel_rows if str(row.get("error") or "").strip()]
    usable_panel_rows = [row for row in panel_rows if not str(row.get("error") or "").strip()]
    if panel_error or (allowed_by_code and not panel_rows) or (failed_panel_rows and not usable_panel_rows):
        panel_state = "error"
    elif failed_panel_rows:
        panel_state = "partial"
    else:
        panel_state = "ok"
    active_users_estimate, active_users_source = _estimate_active_users_proxy(
        live_connections=online_connections_now,
        live_nodes=online_count,
        saw_ip_count=saw_ip_count,
        observed_ip_count_24h=observed_ip_count_24h,
    )
    return {
        "keys": keys,
        "summary": {
            "nodes_total": int(len(keys)),
            "nodes_with_client": int(sum(1 for k in keys if bool(k.get("exists")))),
            "nodes_online": int(online_count),
            "online_keys_now": int(online_count),
            "online_connections_now": int(online_connections_now),
            "active_users_estimate": int(active_users_estimate),
            "active_users_source": active_users_source,
            "online_node_codes_now": sorted(set(online_node_codes_now)),
            "nodes_enabled": int(enabled_count),
            "subid_mismatch_count": int(mismatch_count),
            "traffic_up_bytes": int(total_up),
            "traffic_down_bytes": int(total_down),
            "traffic_total_bytes": int(total_up + total_down),
            "traffic_total_gb": _bytes_to_gb(total_up + total_down),
            "panel_state": panel_state,
            "panel_error": panel_error or None,
            "policies_total": int(len(policy_by_code)),
        },
    }


@app.get("/api/admin/users/{tg_id}")
async def admin_user_card(tg_id: int, x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        tickets = list_user_tickets(s, tg_id, limit=20)
        nodes = enabled_nodes(s)
        policies = (
            s.query(UserKeyPolicy)
            .filter(UserKeyPolicy.tg_id == int(tg_id))
            .order_by(UserKeyPolicy.node_code.asc())
            .all()
        )
        history_rows = (
            s.query(KeyActionHistory)
            .filter(KeyActionHistory.tg_id == int(tg_id))
            .order_by(KeyActionHistory.created_at.desc(), KeyActionHistory.id.desc())
            .limit(100)
            .all()
        )
        recent_admin_rows = (
            s.query(AdminAudit)
            .filter(or_(AdminAudit.target_tg_id == int(tg_id), AdminAudit.actor_tg_id == int(tg_id)))
            .order_by(AdminAudit.created_at.desc(), AdminAudit.id.desc())
            .limit(100)
            .all()
        )
        payment_order_rows = (
            s.query(ExternalOrder)
            .filter(ExternalOrder.tg_id == int(tg_id))
            .order_by(ExternalOrder.created_at.desc(), ExternalOrder.id.desc())
            .limit(20)
            .all()
        )
        loyalty_snapshot = _user_loyalty_snapshot(s=s, user=user)
        observer_payload = build_admin_observer_block(s=s, tg_id=int(tg_id))
        observer_summary_payload = {
            key: value
            for key, value in observer_payload.items()
            if key != "recent_ips"
        }
        user_status = _user_effective_status(user)
        user_origin = _user_origin(user)
        user_payload = {
            "tg_id": int(user.tg_id),
            "username": user.username,
            "display_name": getattr(user, "display_name", None),
            "sub_type": user.sub_type,
            "is_active": bool(user.is_active),
            "effective_active": bool(user_status == "active"),
            "status": user_status,
            "origin": user_origin,
            "is_manual": bool(_is_manual_test_user(user)),
            "expiry_at": _safe_iso(user.expiry_at),
            "stars_paid": int(user.stars_paid or 0),
            "total_gb": int(user.total_gb or 0),
            "trial_used": bool(user.trial_used),
            "referral_count": int(user.referral_count or 0),
            "streak_months": int(user.streak_months or 0),
            "created_at": _safe_iso(user.created_at),
            "linked_telegram_id": int(user.linked_telegram_id) if getattr(user, "linked_telegram_id", None) is not None else None,
            "linked_telegram_username": getattr(user, "linked_telegram_username", None),
            "app_install_id": getattr(user, "app_install_id", None),
            "app_device_name": getattr(user, "app_device_name", None),
            "app_platform": getattr(user, "app_platform", None),
            "app_last_seen_at": _safe_iso(getattr(user, "app_last_seen_at", None)),
            "observer_state": observer_payload.get("state", "ok"),
            "observer_updated_at": observer_payload.get("updated_at"),
        }
        ticket_payload = [_ticket_summary_row(t, list_ticket_messages(s, t.id, limit=1)) for t in tickets]
        policy_payload = [_serialize_key_policy(row) for row in policies]
        history_payload = [
            {
                "id": int(row.id),
                "action": str(row.action or ""),
                "node_code": str(row.node_code or "") or None,
                "actor_tg_id": int(row.actor_tg_id) if row.actor_tg_id is not None else None,
                "source": str(row.source or ""),
                "created_at": _safe_iso(row.created_at),
            }
            for row in history_rows
        ]
        recent_admin_payload = [
            {
                "id": int(row.id),
                "actor_tg_id": int(row.actor_tg_id),
                "action": str(row.action or ""),
                "target_tg_id": int(row.target_tg_id) if row.target_tg_id is not None else None,
                "created_at": _safe_iso(row.created_at),
            }
            for row in recent_admin_rows
        ]
        payment_order_payload = [_admin_payment_order_payload(s=s, order=row) for row in payment_order_rows]
    finally:
        s.close()

    keys_state = await _admin_user_keys_state(user, nodes=nodes)
    s2 = SessionLocal()
    try:
        risk = _compute_user_risk(s=s2, user=user, keys_summary=(keys_state or {}).get("summary") or {})
    finally:
        s2.close()
    keys_summary = dict((keys_state or {}).get("summary") or {})
    raw_panel_state = str(keys_summary.get("panel_state") or "").strip().lower()
    panel_state = raw_panel_state if raw_panel_state in {"ok", "partial", "error"} else "error"

    def panel_value(key: str) -> Any:
        return keys_summary.get(key) if panel_state == "ok" else None

    def safe_key_row(row: dict[str, Any]) -> dict[str, Any]:
        row_panel_state = "error" if row.get("panel_error") else "ok"
        panel_ok = row_panel_state == "ok"
        return {
            "node_code": row.get("node_code"),
            "node_name": row.get("node_name"),
            "exists": bool(row.get("exists")) if panel_ok else None,
            "enabled": bool(row.get("enabled")) if panel_ok else None,
            "online": row.get("online") if panel_ok and isinstance(row.get("online"), bool) else None,
            "current_connections": int(row.get("current_connections") or 0) if panel_ok else None,
            "sub_id_match": bool(row.get("sub_id_match")) if panel_ok else None,
            "up_bytes": int(row.get("up_bytes") or 0) if panel_ok else None,
            "down_bytes": int(row.get("down_bytes") or 0) if panel_ok else None,
            "total_bytes": int(row.get("total_bytes") or 0) if panel_ok else None,
            "total_gb": float(row.get("total_gb") or 0.0) if panel_ok else None,
            "last_online_at": row.get("last_online_at") if panel_ok else None,
            "last_online_age_seconds": row.get("last_online_age_seconds") if panel_ok else None,
            "panel_state": row_panel_state,
            "policy": row.get("policy"),
        }

    safe_keys_state = {
        "summary": {
            "nodes_total": panel_value("nodes_total"),
            "nodes_with_client": panel_value("nodes_with_client"),
            "nodes_online": panel_value("nodes_online"),
            "online_keys_now": panel_value("online_keys_now"),
            "online_connections_now": panel_value("online_connections_now"),
            "active_users_estimate": panel_value("active_users_estimate"),
            "active_users_source": panel_value("active_users_source"),
            "online_node_codes_now": (
                list(keys_summary.get("online_node_codes_now") or [])
                if panel_state == "ok"
                else None
            ),
            "nodes_enabled": panel_value("nodes_enabled"),
            "subid_mismatch_count": panel_value("subid_mismatch_count"),
            "traffic_up_bytes": panel_value("traffic_up_bytes"),
            "traffic_down_bytes": panel_value("traffic_down_bytes"),
            "traffic_total_bytes": panel_value("traffic_total_bytes"),
            "traffic_total_gb": panel_value("traffic_total_gb"),
            "panel_state": panel_state,
            "policies_total": keys_summary.get("policies_total"),
        },
        "keys": [
            safe_key_row(row)
            for row in list((keys_state or {}).get("keys") or [])
            if isinstance(row, dict)
        ],
    }
    return {
        "user": user_payload,
        "tickets": ticket_payload,
        "key_policies": policy_payload,
        "key_history": history_payload,
        "admin_actions": recent_admin_payload,
        "payment_orders": payment_order_payload,
        "risk": risk,
        "observer": observer_summary_payload,
        "loyalty": loyalty_snapshot,
        **safe_keys_state,
    }


@app.get("/api/admin/users/{tg_id}/investigation")
async def admin_user_investigation(tg_id: int, x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(tg_id=int(tg_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "tg_id": int(tg_id),
            "generated_at": _safe_iso(_utcnow()),
            "observer": build_admin_observer_block(s=s, tg_id=int(tg_id)),
        }
    finally:
        s.close()


@app.post("/api/admin/users/manual")
async def admin_create_manual_user(
    payload: ManualUserCreateRequest,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="user.manual_create",
        target_type="user",
        target_id="manual",
        payload={"display_name": payload.display_name, "days": int(payload.days)},
        request=request,
    )


@app.post("/api/admin/users/{tg_id}/manual/extend")
@app.post("/api/admin/users/{tg_id}/manual-extend")
async def admin_extend_manual_user(
    tg_id: int,
    payload: ManualUserExtendRequest,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="user.extend",
        target_type="user",
        target_id=str(tg_id),
        payload={
            "days": payload.days,
            "delta_days": payload.delta_days,
            "allow_deactivate": bool(payload.allow_deactivate),
        },
        request=request,
    )


@app.post("/api/admin/users/{tg_id}/manual/block")
async def admin_block_manual_user(
    tg_id: int,
    payload: ManualUserBlockRequest,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="user.block",
        target_type="user",
        target_id=str(tg_id),
        payload={"blocked": bool(payload.blocked)},
        request=request,
    )


@app.post("/api/admin/users/{tg_id}/manual/regenerate-token")
async def admin_regenerate_manual_token(
    tg_id: int,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="user.regenerate_token",
        target_type="user",
        target_id=str(tg_id),
        payload={},
        request=request,
    )


@app.post("/api/admin/users/{tg_id}/safe-delete")
async def admin_safe_delete_test_user(
    tg_id: int,
    payload: AdminUserSafeDeleteIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="user.safe_delete",
        target_type="user",
        target_id=str(tg_id),
        payload={"confirm": bool(payload.confirm)},
        request=request,
    )


@app.post("/api/admin/users/{tg_id}/delete-test-user")
async def admin_delete_test_user_compat(
    tg_id: int,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="user.delete_test",
        target_type="user",
        target_id=str(tg_id),
        payload={},
        request=request,
    )


@app.post("/api/admin/users/{tg_id}/keys/{node_code}/toggle")
async def admin_user_key_toggle(
    tg_id: int,
    node_code: str,
    payload: AdminUserKeyToggleIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="user.key_toggle",
        target_type="user",
        target_id=str(tg_id),
        payload={"node_code": node_code, "enable": bool(payload.enable)},
        request=request,
    )


@app.post("/api/admin/users/{tg_id}/keys/{node_code}/reset-traffic")
async def admin_user_key_reset_traffic(
    tg_id: int,
    node_code: str,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="user.key_reset_traffic",
        target_type="user",
        target_id=str(tg_id),
        payload={"node_code": node_code},
        request=request,
    )


@app.post("/api/admin/users/{tg_id}/keys/{node_code}/resync-subid")
async def admin_user_key_resync_subid(
    tg_id: int,
    node_code: str,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="user.key_resync_subid",
        target_type="user",
        target_id=str(tg_id),
        payload={"node_code": node_code},
        request=request,
    )


@app.get("/api/admin/users/{tg_id}/key-history")
async def admin_user_key_history(tg_id: int, x_telegram_init_data: str = Header(default=""), limit: int = 100) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        rows = (
            s.query(KeyActionHistory)
            .filter(KeyActionHistory.tg_id == int(tg_id))
            .order_by(KeyActionHistory.created_at.desc(), KeyActionHistory.id.desc())
            .limit(max(1, min(int(limit), 500)))
            .all()
        )
        return {
            "rows": [
                {
                    "id": int(r.id),
                    "tg_id": int(r.tg_id),
                    "node_code": str(r.node_code or "") or None,
                    "action": str(r.action or ""),
                    "actor_tg_id": int(r.actor_tg_id) if r.actor_tg_id is not None else None,
                    "source": str(r.source or ""),
                    "meta": _json_obj(getattr(r, "meta", None)),
                    "created_at": _safe_iso(r.created_at),
                }
                for r in rows
            ]
        }
    finally:
        s.close()


@app.get("/api/admin/users/{tg_id}/key-limits")
async def admin_user_key_limits_get(tg_id: int, x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        rows = (
            s.query(UserKeyPolicy)
            .filter(UserKeyPolicy.tg_id == int(tg_id))
            .order_by(UserKeyPolicy.node_code.asc())
            .all()
        )
        return {"limits": [_serialize_key_policy(r) for r in rows]}
    finally:
        s.close()


@app.put("/api/admin/users/{tg_id}/key-limits/{node_code}")
async def admin_user_key_limits_put(
    tg_id: int,
    node_code: str,
    payload: AdminUserKeyLimitsIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="user.key_limits",
        target_type="user",
        target_id=str(tg_id),
        payload={
            "node_code": node_code,
            "burst_mbps": payload.burst_mbps,
            "soft_cap_gb": payload.soft_cap_gb,
            "hard_cap_gb": payload.hard_cap_gb,
            "notify_soft": bool(payload.notify_soft),
            "notify_hard": bool(payload.notify_hard),
            "auto_disable_on_hard": bool(payload.auto_disable_on_hard),
            "apply_now": bool(payload.apply_now),
        },
        request=request,
    )


@app.get("/api/admin/users/{tg_id}/risk")
async def admin_user_risk_get(tg_id: int, x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        nodes = enabled_nodes(s)
    finally:
        s.close()
    keys_state = await _admin_user_keys_state(user, nodes=nodes)
    s2 = SessionLocal()
    try:
        risk = _compute_user_risk(s=s2, user=user, keys_summary=(keys_state or {}).get("summary") or {})
    finally:
        s2.close()
    return {"risk": risk}


@app.get("/api/admin/users/{tg_id}/loyalty")
async def admin_user_loyalty_get(tg_id: int, x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        user = s.query(User).filter(User.tg_id == int(tg_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"loyalty": _user_loyalty_snapshot(s=s, user=user)}
    finally:
        s.close()


@app.post("/api/admin/users/{tg_id}/loyalty/grant")
async def admin_user_loyalty_grant(
    tg_id: int,
    payload: AdminLoyaltyGrantIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="user.loyalty_grant",
        target_type="user",
        target_id=str(tg_id),
        payload={"tier_days": int(payload.tier_days)},
        request=request,
    )


@app.post("/api/admin/users/{tg_id}/presets/run")
async def admin_user_preset_run(
    tg_id: int,
    payload: AdminUserPresetRunIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="user.preset_run",
        target_type="user",
        target_id=str(tg_id),
        payload={"preset": payload.preset},
        request=request,
    )


@app.post("/api/admin/users/keys/bulk-action")
async def admin_users_keys_bulk_action(
    payload: AdminUserKeysBulkActionIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="user.bulk_key_action",
        target_type="users",
        target_id="bulk",
        payload={
            "action": payload.action,
            "segment": payload.segment,
            "node_codes": list(payload.node_codes),
            "tg_ids": list(payload.tg_ids),
            "q": payload.q,
            "limit": int(payload.limit),
            "dry_run": bool(payload.dry_run),
            "force": bool(payload.force),
        },
        request=request,
    )


@app.get("/api/admin/audit")
async def admin_audit_log(
    x_telegram_init_data: str = Header(default=""),
    limit: int = 200,
    offset: int = 0,
    action: str = "",
    target_tg_id: int | None = None,
) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        q = s.query(AdminAudit)
        if target_tg_id is not None:
            q = q.filter(AdminAudit.target_tg_id == int(target_tg_id))
        action_norm = str(action or "").strip()
        if action_norm:
            q = q.filter(AdminAudit.action == action_norm)
        rows = (
            q.order_by(AdminAudit.created_at.desc(), AdminAudit.id.desc())
            .offset(max(0, int(offset)))
            .limit(max(1, min(int(limit), 1000)))
            .all()
        )
        return {
            "rows": [
                {
                    "id": int(r.id),
                    "actor_tg_id": int(r.actor_tg_id),
                    "action": str(r.action or ""),
                    "target_tg_id": int(r.target_tg_id) if r.target_tg_id is not None else None,
                    "meta": _json_obj(getattr(r, "meta", None)),
                    "created_at": _safe_iso(r.created_at),
                }
                for r in rows
            ]
        }
    finally:
        s.close()


@app.post("/api/admin/users/{tg_id}/message")
async def admin_user_message(
    tg_id: int,
    payload: AdminMessageIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="user.message",
        target_type="user",
        target_id=str(tg_id),
        payload={"text": payload.text},
        request=request,
    )


@app.post("/api/admin/broadcast")
async def admin_broadcast(
    payload: AdminBroadcastIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    segment = (payload.segment or "all_active").strip().lower()
    limit = max(1, min(int(payload.limit), MAX_BROADCAST_LIMIT))

    if not bool(payload.dry_run):
        return await _execute_admin_guarded_action(
            actor_tg_id=actor,
            action="broadcast.send",
            target_type="broadcast",
            target_id="broadcast",
            payload={
                "text": payload.text,
                "segment": segment,
                "limit": limit,
                "tg_ids": list(payload.tg_ids),
            },
            request=request,
        )

    s = SessionLocal()
    try:
        target_ids: list[int] = []
        if segment == "custom":
            target_ids = sorted({int(v) for v in payload.tg_ids if int(v) > 0})
        else:
            query = s.query(User.tg_id).filter(User.tg_id > 0)
            if segment == "all_active":
                query = query.filter(User.is_active == True)
            elif segment == "free":
                query = query.filter(func.upper(User.sub_type) == "FREE")
            elif segment == "paid":
                query = query.filter(func.upper(User.sub_type) == "PAID")
            elif segment == "expired":
                query = query.filter(User.expiry_at.isnot(None), User.expiry_at < _utcnow())
            else:
                raise HTTPException(status_code=400, detail="Unsupported segment")
            target_ids = [int(r[0]) for r in query.order_by(User.tg_id.asc()).limit(limit).all()]
    finally:
        s.close()

    _audit_admin(
        actor_tg_id=actor,
        action="admin_broadcast_preview",
        meta={"segment": segment, "attempted": len(target_ids), "limit": limit},
    )
    return {
        "ok": True,
        "dry_run": True,
        "segment": segment,
        "attempted": len(target_ids),
        "sent": 0,
        "failed": 0,
    }


@app.get("/api/admin/promos")
async def admin_promos(x_telegram_init_data: str = Header(default=""), limit: int = 200) -> dict:
    _require_admin(x_telegram_init_data)
    lim = max(1, min(int(limit), 500))
    s = SessionLocal()
    try:
        rows = s.query(PromoCode).order_by(PromoCode.created_at.desc(), PromoCode.id.desc()).limit(lim).all()
        usage_rows = (
            s.query(PromoUsage.promo_code, func.count(PromoUsage.id))
            .group_by(PromoUsage.promo_code)
            .all()
        )
        usage_map = {str(code or "").upper(): int(cnt or 0) for code, cnt in usage_rows}
        return {
            "promos": [
                {
                    "code": p.code,
                    "promo_type": p.promo_type,
                    "value": int(p.value or 0),
                    "uses_left": int(p.uses_left or 0),
                    "used_count": int(usage_map.get(str(p.code or "").upper(), 0)),
                    "expires_at": _safe_iso(p.expires_at),
                    "created_at": _safe_iso(p.created_at),
                }
                for p in rows
            ]
        }
    finally:
        s.close()


@app.post("/api/admin/promos")
async def admin_promos_create(
    payload: AdminPromoCreateIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    code = (payload.code or "").strip().upper()
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="promo.create",
        target_type="promo",
        target_id=code,
        payload=payload.model_dump(),
        request=request,
    )


@app.patch("/api/admin/promos/{code}")
async def admin_promos_update(
    code: str,
    payload: AdminPromoUpdateIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    src_code = (code or "").strip().upper()
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="promo.update",
        target_type="promo",
        target_id=src_code,
        payload=payload.model_dump(exclude_unset=True),
        request=request,
    )


@app.delete("/api/admin/promos/{code}")
async def admin_promos_delete(
    code: str,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    src_code = (code or "").strip().upper()
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="promo.delete",
        target_type="promo",
        target_id=src_code,
        payload={},
        request=request,
    )


@app.get("/api/admin/plans")
async def admin_plans(x_telegram_init_data: str = Header(default=""), include_inactive: bool = True) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        rows = _plan_catalog_payload(s=s, only_active=not bool(include_inactive))
        return {"plans": rows}
    finally:
        s.close()


@app.post("/api/admin/plans")
async def admin_plans_create(
    payload: AdminPlanCreateIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    code = (payload.code or "").strip().lower()
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="plan.create",
        target_type="plan",
        target_id=code,
        payload=payload.model_dump(),
        request=request,
    )


@app.patch("/api/admin/plans/{code}")
async def admin_plans_update(
    code: str,
    payload: AdminPlanUpdateIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    target = (code or "").strip().lower()
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="plan.update",
        target_type="plan",
        target_id=target,
        payload=payload.model_dump(exclude_unset=True),
        request=request,
    )


@app.delete("/api/admin/plans/{code}")
async def admin_plans_delete(
    code: str,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    target = (code or "").strip().lower()
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="plan.delete",
        target_type="plan",
        target_id=target,
        payload={},
        request=request,
    )


@app.get("/api/admin/service-incidents")
async def admin_service_incidents(
    x_telegram_init_data: str = Header(default=""),
    limit: int = Query(default=100, ge=1, le=300),
) -> dict[str, Any]:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        rows = (
            s.query(ServiceIncident)
            .order_by(ServiceIncident.started_at.desc(), ServiceIncident.created_at.desc())
            .limit(int(limit))
            .all()
        )
        return {"incidents": [incident_service.incident_payload(row) for row in rows]}
    finally:
        s.close()


@app.post("/api/admin/service-incidents")
async def admin_service_incident_create(
    payload: AdminServiceIncidentCreateIn,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    incident_key = str(payload.incident_key or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,79}", incident_key):
        raise HTTPException(status_code=422, detail="Invalid incident key")
    severity = str(payload.severity or "").strip().lower()
    if severity not in {"minor", "degraded", "major", "critical"}:
        raise HTTPException(status_code=422, detail="Invalid incident severity")
    if int(payload.compensation_days) not in incident_service.ALLOWED_COMPENSATION_DAYS:
        raise HTTPException(status_code=422, detail="Invalid compensation days")
    started_at = _parse_admin_datetime(payload.started_at)
    if started_at is None or started_at > _utcnow() + timedelta(minutes=5):
        raise HTTPException(status_code=422, detail="Invalid incident start")
    node_codes = incident_service.normalize_node_codes(payload.affected_node_codes)
    now = _utcnow()
    s = SessionLocal()
    try:
        if s.query(ServiceIncident.id).filter(ServiceIncident.incident_key == incident_key).first():
            raise HTTPException(status_code=409, detail="Incident key already exists")
        row = ServiceIncident(
            id=str(uuid.uuid4()),
            incident_key=incident_key,
            title=str(payload.title).strip(),
            summary=str(payload.summary).strip(),
            severity=severity,
            status="confirmed",
            started_at=started_at,
            affected_node_codes_json=json.dumps(list(node_codes), separators=(",", ":")),
            compensation_days=int(payload.compensation_days),
            confirmed_by=actor,
            confirmed_at=now,
            created_at=now,
            updated_at=now,
        )
        s.add(row)
        s.flush()
        _add_admin_audit(
            s,
            actor_tg_id=actor,
            action="service_incident.confirm",
            meta={
                "incident_id": str(row.id),
                "incident_key": incident_key,
                "affected_node_codes": list(node_codes),
                "compensation_days": int(payload.compensation_days),
            },
        )
        s.commit()
        return {"incident": incident_service.incident_payload(row)}
    except HTTPException:
        s.rollback()
        raise
    except IntegrityError as exc:
        s.rollback()
        raise HTTPException(status_code=409, detail="Incident key already exists") from exc
    finally:
        s.close()


@app.post("/api/admin/service-incidents/{incident_id}/resolve")
async def admin_service_incident_resolve(
    incident_id: str,
    payload: AdminServiceIncidentResolveIn,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    ended_at = _parse_admin_datetime(payload.ended_at)
    if ended_at is None or ended_at > _utcnow() + timedelta(minutes=5):
        raise HTTPException(status_code=422, detail="Invalid incident end")
    now = _utcnow()
    s = SessionLocal()
    try:
        row = (
            s.query(ServiceIncident)
            .filter(ServiceIncident.id == str(incident_id))
            .with_for_update()
            .one_or_none()
        )
        if row is None:
            raise HTTPException(status_code=404, detail="Incident not found")
        if str(row.status) == "cancelled":
            raise HTTPException(status_code=409, detail="Cancelled incident cannot be resolved")
        if ended_at < row.started_at:
            raise HTTPException(status_code=422, detail="Incident end precedes start")
        if str(row.status) == "confirmed":
            row.status = "resolved"
            row.ended_at = ended_at
            row.resolved_by = actor
            row.resolved_at = now
            row.updated_at = now
        elif row.ended_at != ended_at:
            raise HTTPException(status_code=409, detail="Resolved incident window is immutable")
        _add_admin_audit(
            s,
            actor_tg_id=actor,
            action="service_incident.resolve",
            meta={
                "incident_id": str(row.id),
                "incident_key": str(row.incident_key),
                "ended_at": _safe_iso(row.ended_at),
            },
        )
        s.commit()
        return {
            "incident": incident_service.incident_payload(row),
            "compensationQueued": int(row.compensation_days or 0) > 0
                and row.compensation_completed_at is None,
        }
    except HTTPException:
        s.rollback()
        raise
    finally:
        s.close()


@app.post("/api/admin/service-incidents/{incident_id}/compensate")
async def admin_service_incident_compensate(
    incident_id: str,
    payload: AdminServiceIncidentCompensateIn,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    s = SessionLocal()
    try:
        row = s.query(ServiceIncident).filter(ServiceIncident.id == str(incident_id)).one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Incident not found")
        try:
            preview = incident_service.preview_incident_compensation(s, incident=row)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        preview_payload = {
            "incidentId": preview.incident_id,
            "incidentKey": preview.incident_key,
            "impactedAccounts": preview.impacted_accounts,
            "compensationDays": preview.compensation_days,
        }
        if payload.dry_run:
            return {"applied": False, "dryRun": True, "preview": preview_payload}
        if not secrets.compare_digest(
            str(payload.confirm_incident_key or "").strip().lower(),
            str(row.incident_key),
        ):
            raise HTTPException(status_code=409, detail="Incident confirmation key mismatch")
        result = incident_service.apply_incident_compensation(
            s,
            incident_id=str(row.id),
            now=_utcnow(),
        )
        _add_admin_audit(
            s,
            actor_tg_id=actor,
            action="service_incident.compensate",
            meta={
                **preview_payload,
                "granted_accounts": result.granted_accounts,
                "existing_grants": result.existing_grants,
            },
        )
        s.commit()
        return {
            "applied": True,
            "dryRun": False,
            "preview": preview_payload,
            "grantedAccounts": result.granted_accounts,
            "existingGrants": result.existing_grants,
            "completedAt": _safe_iso(result.completed_at),
        }
    except HTTPException:
        s.rollback()
        raise
    except ValueError as exc:
        s.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    finally:
        s.close()


@app.get("/api/admin/program-applications")
async def admin_program_applications(
    x_telegram_init_data: str = Header(default=""),
    status: str = Query(default="", max_length=24),
    kind: str = Query(default="", max_length=32),
    limit: int = Query(default=100, ge=1, le=300),
) -> dict[str, Any]:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        query = s.query(ProgramApplication)
        normalized_status = str(status or "").strip().lower()
        normalized_kind = str(kind or "").strip().lower()
        if normalized_status:
            query = query.filter(ProgramApplication.status == normalized_status)
        if normalized_kind:
            query = query.filter(ProgramApplication.kind == normalized_kind)
        rows = query.order_by(ProgramApplication.created_at.desc()).limit(int(limit)).all()
        return {
            "ok": True,
            "applications": [
                program_application_service.application_payload(row, include_operator_note=True)
                for row in rows
            ],
        }
    finally:
        s.close()


@app.post("/api/admin/program-applications/{application_id}/review")
async def admin_program_application_review(
    application_id: str,
    payload: AdminProgramApplicationReviewIn,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    if int(payload.reward_days or 0) > 0 and not secrets.compare_digest(
        str(payload.confirm_application_id or "").strip(),
        str(application_id),
    ):
        raise HTTPException(status_code=409, detail="Application confirmation id mismatch")
    s = SessionLocal()
    try:
        row = program_application_service.review_application(
            s,
            application_id=application_id,
            status=payload.status,
            operator_note=payload.operator_note,
            reward_days=payload.reward_days,
            reviewed_by=actor,
            now=_utcnow(),
        )
        _add_admin_audit(
            s,
            actor_tg_id=actor,
            action="program_application.review",
            target_tg_id=int(row.legacy_tg_id) if row.legacy_tg_id is not None else None,
            meta={
                "application_id": str(row.id),
                "kind": str(row.kind),
                "status": str(row.status),
                "reward_days": int(row.reward_days or 0),
                "reward_grant_id": str(row.reward_grant_id or "") or None,
            },
        )
        s.commit()
        return {
            "ok": True,
            "application": program_application_service.application_payload(row, include_operator_note=True),
        }
    except program_application_service.ProgramApplicationError as exc:
        s.rollback()
        status_code = 404 if exc.code == "program_application_not_found" else 409
        raise HTTPException(status_code=status_code, detail={"code": exc.code, "message": exc.message}) from exc
    except ValueError as exc:
        s.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    finally:
        s.close()


@app.get("/api/admin/live-updates")
async def admin_live_updates(x_telegram_init_data: str = Header(default=""), include_inactive: bool = True) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        q = s.query(LiveUpdate)
        if not include_inactive:
            q = q.filter(LiveUpdate.is_active == True)
        rows = q.order_by(LiveUpdate.sort_order.asc(), LiveUpdate.id.desc()).limit(300).all()
        return {
            "updates": [
                {
                    "id": int(r.id),
                    "title": r.title,
                    "summary": r.summary,
                    "link": str(r.link or "").strip(),
                    "tg_link": _build_tg_post_link(
                        channel_username=getattr(r, "channel_username", None),
                        post_id=getattr(r, "post_id", None),
                        fallback_link=str(r.link or "").strip(),
                    ),
                    "channel_username": str(getattr(r, "channel_username", "") or "").strip().lstrip("@") or None,
                    "post_id": int(getattr(r, "post_id", 0) or 0) or None,
                    "published_at": _safe_iso(r.published_at),
                    "is_active": bool(r.is_active),
                    "sort_order": int(r.sort_order or 0),
                    "created_at": _safe_iso(r.created_at),
                    "updated_at": _safe_iso(r.updated_at),
                }
                for r in rows
            ]
        }
    finally:
        s.close()


@app.post("/api/admin/live-updates")
async def admin_live_updates_create(
    payload: AdminLiveUpdateCreateIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="live_update.create",
        target_type="live_update",
        target_id="new",
        payload=payload.model_dump(),
        request=request,
    )


@app.patch("/api/admin/live-updates/{update_id}")
async def admin_live_updates_update(
    update_id: int,
    payload: AdminLiveUpdateUpdateIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="live_update.update",
        target_type="live_update",
        target_id=str(update_id),
        payload=payload.model_dump(exclude_unset=True),
        request=request,
    )


@app.delete("/api/admin/live-updates/{update_id}")
async def admin_live_updates_delete(
    update_id: int,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="live_update.delete",
        target_type="live_update",
        target_id=str(update_id),
        payload={},
        request=request,
    )


@app.get("/api/admin/start-links")
async def admin_start_links(x_telegram_init_data: str = Header(default=""), include_inactive: bool = True) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        q = s.query(StartLink)
        if not include_inactive:
            q = q.filter(StartLink.is_active == True)
        rows = q.order_by(StartLink.updated_at.desc(), StartLink.id.desc()).limit(500).all()
        bot_username = (BOT_USERNAME or "pokrov_vpnbot").lstrip("@")
        return {
            "start_links": [
                {
                    "id": int(r.id),
                    "code": str(r.code or "").strip().lower(),
                    "description": str(r.description or "").strip() or None,
                    "target_action": str(r.target_action or "").strip() or None,
                    "is_active": bool(r.is_active),
                    "bot_start_link": f"https://t.me/{bot_username}?start={str(r.code or '').strip()}",
                    "created_at": _safe_iso(getattr(r, "created_at", None)),
                    "updated_at": _safe_iso(getattr(r, "updated_at", None)),
                }
                for r in rows
            ]
        }
    finally:
        s.close()


@app.post("/api/admin/start-links")
async def admin_start_links_create(
    payload: AdminStartLinkCreateIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    code = re.sub(r"[^a-z0-9_-]+", "", str(payload.code or "").strip().lower())[:64]
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="start_link.create",
        target_type="start_link",
        target_id=code,
        payload=payload.model_dump(),
        request=request,
    )


@app.patch("/api/admin/start-links/{link_id}")
async def admin_start_links_update(
    link_id: int,
    payload: AdminStartLinkUpdateIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="start_link.update",
        target_type="start_link",
        target_id=str(link_id),
        payload=payload.model_dump(exclude_unset=True),
        request=request,
    )


@app.delete("/api/admin/start-links/{link_id}")
async def admin_start_links_delete(
    link_id: int,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="start_link.delete",
        target_type="start_link",
        target_id=str(link_id),
        payload={},
        request=request,
    )


@app.get("/api/admin/wheel-config")
async def admin_wheel_config_get(x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        cfg = _normalized_wheel_config(_get_app_setting_json(s=s, key="wheel_config", default=DEFAULT_WHEEL_CONFIG))
        return {"wheel_config": cfg}
    finally:
        s.close()


@app.put("/api/admin/wheel-config")
async def admin_wheel_config_put(
    payload: AdminWheelConfigIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="wheel_config.update",
        target_type="config",
        target_id="wheel",
        payload=payload.model_dump(),
        request=request,
    )


@app.get("/api/admin/network-rollout-config")
async def admin_network_rollout_config_get(x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        return {"network_rollout_config": load_network_rollout_config(session=s)}
    finally:
        s.close()


@app.put("/api/admin/network-rollout-config")
async def admin_network_rollout_config_put(
    payload: dict[str, Any],
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="network_rollout_config.update",
        target_type="config",
        target_id="network-rollout",
        payload=payload if isinstance(payload, dict) else {},
        request=request,
    )


@app.put("/api/admin/client/warp/material")
async def admin_client_warp_material_put(
    payload: AdminWarpMaterialPutIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="warp_material.replace",
        target_type="warp_material",
        target_id=str(payload.tg_id),
        payload=payload.model_dump(),
        request=request,
    )


@app.get("/api/admin/client/warp/summary")
async def admin_client_warp_summary(x_telegram_init_data: str = Header(default="")) -> dict[str, Any]:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        return build_warp_admin_summary(s)
    finally:
        s.close()


@app.get("/api/admin/promo-slots")
async def admin_promo_slots_get(x_telegram_init_data: str = Header(default="")) -> dict[str, Any]:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        config = _normalized_promo_slots_config(
            _get_app_setting_json(s=s, key=PROMO_SLOTS_CONFIG_KEY, default={}),
            strict=False,
        )
        slot_map, content_map = _promo_slot_catalog_maps()
        return {
            "promo_slots": {
                **config,
                "catalog": {
                    "version": str(_PROMO_SLOTS.get("version") or ""),
                    "mode": str(_PROMO_SLOTS.get("mode") or "whitelist_slots"),
                    "fallback_behavior": str(_PROMO_SLOTS.get("fallback_behavior") or "contextual_only_when_remote_unavailable"),
                    "slots": list(slot_map.values()),
                    "content_catalog": list(content_map.values()),
                },
            }
        }
    finally:
        s.close()


@app.put("/api/admin/promo-slots")
async def admin_promo_slots_put(
    payload: AdminPromoSlotsPutIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="promo_slots.update",
        target_type="config",
        target_id="promo-slots",
        payload=payload.model_dump(),
        request=request,
    )


@app.post("/api/admin/campaign-links/build")
async def admin_campaign_links_build(payload: AdminCampaignLinksBuildIn, x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    promo = _sanitize_deeplink_token(payload.promo_code, max_len=20, uppercase=True)
    campaign = _sanitize_deeplink_token(payload.campaign_key, max_len=64, uppercase=False)
    plan = (payload.plan_code or "").strip().lower()[:32]
    source = (payload.source or "bot").strip().lower()[:16]
    start_payload = ""
    if campaign and promo:
        start_payload = f"campaign_{campaign}__promo_{promo}"
    elif promo:
        start_payload = f"promo_{promo}"
    elif campaign:
        start_payload = f"campaign_{campaign}"
    if start_payload and len(start_payload) > 64:
        raise HTTPException(status_code=400, detail="Telegram start payload exceeds 64 chars")
    bot_username = (BOT_USERNAME or "pokrov_vpnbot").lstrip("@")
    bot_start_link = f"https://t.me/{bot_username}" + (f"?start={start_payload}" if start_payload else "")

    base_checkout = _public_checkout_url() or "https://pay.pokrov.space/checkout/"
    parsed = urlparse(base_checkout)
    q = dict(parse_qsl(parsed.query, keep_blank_values=True))
    q["source"] = source or "bot"
    if plan:
        q["plan"] = plan
    if promo:
        q["promo"] = promo
    if campaign:
        q["campaign"] = campaign
    # Public campaign links cannot mint a valid checkout ticket without a bound user,
    # so the "checkout" action must stay in a safe bot-first flow.
    checkout_link = bot_start_link

    webapp_base = _safe_public_url(Settings.WEBAPP_URL) or "https://app.pokrov.space/"
    wp = urlparse(webapp_base)
    wq = dict(parse_qsl(wp.query, keep_blank_values=True))
    if promo:
        wq["promo"] = promo
    if campaign:
        wq["campaign"] = campaign
    if plan:
        wq["plan"] = plan
    webapp_link = f"{wp.scheme}://{wp.netloc}{wp.path or '/'}?{urlencode(wq)}" if wp.scheme and wp.netloc else f"/?{urlencode(wq)}"
    return {
        "ok": True,
        "bot_start_link": bot_start_link,
        "checkout_link": checkout_link,
        "checkout_mode": "bot_fallback",
        "checkout_reason": "checkout_ticket_requires_bound_user",
        "webapp_link": webapp_link,
    }


def _admin_referral_basis(session, row: ReferralBonusQueue, *, now: datetime) -> str:
    status = str(row.status or "").strip().lower()
    if status != "pending":
        return status or "unknown"
    if row.ready_at and row.ready_at > now:
        return "waiting_ready_at"
    referred = session.query(User).filter(User.tg_id == int(row.referred_tg_id)).first()
    referrer = session.query(User).filter(User.tg_id == int(row.referrer_tg_id)).first()
    if referred is None or referrer is None:
        return "rejected_missing_user"
    has_activity = (
        session.query(Event.id)
        .filter(
            Event.tg_id == int(referred.tg_id),
            Event.created_at >= (row.queued_at or (now - timedelta(days=1))),
            Event.event_name.in_(["connected_ok", "clicked_connect"]),
        )
        .first()
        is not None
    )
    if not has_activity:
        queued_at = row.queued_at or now
        age_hours = max(0, int((now - queued_at).total_seconds() // 3600))
        return (
            "rejected_no_activity"
            if age_hours >= int(REFERRAL_ANTIFRAUD_MAX_WAIT_HOURS)
            else "waiting_for_activity"
        )
    if not (
        bool(referrer.is_active)
        and str(referrer.sub_type or "").strip().upper() == "PAID"
        and referrer.expiry_at is not None
        and referrer.expiry_at > now
    ):
        return "rejected_referrer_inactive"
    return "reward_ready"


@app.get("/api/admin/referrals/pending")
async def admin_referrals_pending(
    x_telegram_init_data: str = Header(default=""),
    limit: int = 200,
    status: str = "",
) -> dict:
    _require_admin(x_telegram_init_data)
    now = _utcnow()
    s = SessionLocal()
    try:
        q = s.query(ReferralBonusQueue)
        status_norm = str(status or "").strip().lower()
        if status_norm:
            q = q.filter(func.lower(ReferralBonusQueue.status) == status_norm)
        rows = (
            q.order_by(ReferralBonusQueue.ready_at.asc(), ReferralBonusQueue.id.asc())
            .limit(max(1, min(int(limit), 1000)))
            .all()
        )
        return {
            "rows": [
                {
                    "id": int(r.id),
                    "order_id": str(r.order_id or ""),
                    "referrer_tg_id": int(r.referrer_tg_id),
                    "referred_tg_id": int(r.referred_tg_id),
                    "queued_at": _safe_iso(r.queued_at),
                    "ready_at": _safe_iso(r.ready_at),
                    "status": str(r.status or ""),
                    "processed_at": _safe_iso(r.processed_at),
                    "basis": _admin_referral_basis(s, r, now=now),
                    "meta_present": bool(str(getattr(r, "meta", "") or "").strip()),
                    "meta_sha256": hashlib.sha256(
                        str(getattr(r, "meta", "") or "").encode("utf-8")
                    ).hexdigest(),
                }
                for r in rows
            ]
        }
    finally:
        s.close()


@app.post("/api/admin/referrals/process")
async def admin_referrals_process(
    payload: AdminReferralQueueProcessIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="referral.process",
        target_type="referral_queue",
        target_id="ready",
        payload=payload.model_dump(),
        request=request,
    )


@app.get("/api/admin/loyalty-config")
async def admin_loyalty_config_get(x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        return {"loyalty_config": _loyalty_config(s=s)}
    finally:
        s.close()


@app.put("/api/admin/loyalty-config")
async def admin_loyalty_config_put(
    payload: dict[str, Any],
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="loyalty_config.update",
        target_type="config",
        target_id="loyalty",
        payload=payload if isinstance(payload, dict) else {},
        request=request,
    )


@app.get("/api/admin/campaigns")
async def admin_campaigns_get(x_telegram_init_data: str = Header(default=""), limit: int = 200) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        rows = (
            s.query(IncentiveCampaign)
            .order_by(IncentiveCampaign.updated_at.desc(), IncentiveCampaign.id.desc())
            .limit(max(1, min(int(limit), 1000)))
            .all()
        )
        return {
            "campaigns": [
                {
                    "id": int(r.id),
                    "name": str(r.name or ""),
                    "campaign_type": str(r.campaign_type or ""),
                    "target_value": str(r.target_value or ""),
                    "segment": str(r.segment or ""),
                    "starts_at": _safe_iso(r.starts_at),
                    "ends_at": _safe_iso(r.ends_at),
                    "max_activations": int(r.max_activations or -1),
                    "activations_count": int(r.activations_count or 0),
                    "auto_disable": bool(r.auto_disable),
                    "is_active": bool(r.is_active),
                    "created_by": int(r.created_by) if r.created_by is not None else None,
                    "metadata": _json_obj(getattr(r, "metadata_json", None)),
                    "created_at": _safe_iso(r.created_at),
                    "updated_at": _safe_iso(r.updated_at),
                }
                for r in rows
            ]
        }
    finally:
        s.close()


@app.post("/api/admin/campaigns")
async def admin_campaigns_create(
    payload: AdminCampaignCreateIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="campaign.create",
        target_type="campaign",
        target_id="new",
        payload=payload.model_dump(),
        request=request,
    )


@app.patch("/api/admin/campaigns/{campaign_id}")
async def admin_campaigns_patch(
    campaign_id: int,
    payload: AdminCampaignUpdateIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="campaign.update",
        target_type="campaign",
        target_id=str(campaign_id),
        payload=payload.model_dump(exclude_unset=True),
        request=request,
    )


@app.delete("/api/admin/campaigns/{campaign_id}")
async def admin_campaigns_delete(
    campaign_id: int,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="campaign.delete",
        target_type="campaign",
        target_id=str(campaign_id),
        payload={},
        request=request,
    )


@app.get("/api/admin/templates")
async def admin_templates(x_telegram_init_data: str = Header(default=""), limit: int = 200) -> dict:
    _require_admin(x_telegram_init_data)
    lim = max(1, min(int(limit), 500))
    s = SessionLocal()
    try:
        rows = s.query(Template).order_by(Template.created_at.desc(), Template.id.desc()).limit(lim).all()
        return {
            "templates": [
                {"key": t.key, "text": t.text, "created_at": _safe_iso(t.created_at)}
                for t in rows
            ]
        }
    finally:
        s.close()


@app.post("/api/admin/templates")
async def admin_templates_create(
    payload: AdminTemplateCreateIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    key = (payload.key or "").strip().lower()
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="template.create",
        target_type="template",
        target_id=key,
        payload=payload.model_dump(),
        request=request,
    )
@app.patch("/api/admin/templates/{key}")
async def admin_templates_update(
    key: str,
    payload: AdminTemplateUpdateIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    src_key = (key or "").strip().lower()
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="template.update",
        target_type="template",
        target_id=src_key,
        payload=payload.model_dump(exclude_unset=True),
        request=request,
    )


@app.delete("/api/admin/templates/{key}")
async def admin_templates_delete(
    key: str,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    src_key = (key or "").strip().lower()
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="template.delete",
        target_type="template",
        target_id=src_key,
        payload={},
        request=request,
    )


@app.get("/api/admin/gift-codes")
async def admin_gift_codes(x_telegram_init_data: str = Header(default=""), limit: int = 100) -> dict:
    _require_admin(x_telegram_init_data)
    lim = max(1, min(int(limit), 500))
    s = SessionLocal()
    try:
        rows = s.query(GiftCard).order_by(GiftCard.created_at.desc(), GiftCard.id.desc()).limit(lim).all()
        return {
            "gift_codes": [
                {
                    "code": g.code,
                    "card_type": g.card_type,
                    "days": int((GIFT_CARD_TYPES.get(g.card_type or "", {}) or {}).get("days", 0)),
                    "stars": int((GIFT_CARD_TYPES.get(g.card_type or "", {}) or {}).get("stars", 0)),
                    "created_by": int(g.created_by or 0),
                    "created_at": _safe_iso(g.created_at),
                    "redeemed_by": int(g.redeemed_by) if g.redeemed_by is not None else None,
                    "redeemed_at": _safe_iso(g.redeemed_at),
                }
                for g in rows
            ]
        }
    finally:
        s.close()


@app.post("/api/admin/access-keys/issue")
async def admin_access_keys_issue(
    payload: AdminAccessKeyIssueIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    plan_code = str(payload.plan_code or "").strip().lower()
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="access_key.issue",
        target_type="access_key_batch",
        target_id=plan_code,
        payload=payload.model_dump(),
        request=request,
    )


@app.post("/api/admin/gift-codes")
async def admin_gift_codes_create(
    payload: AdminGiftCodeCreateIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    card_type = (payload.card_type or "").strip().lower()
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="gift_code.create",
        target_type="gift_code",
        target_id=card_type,
        payload=payload.model_dump(),
        request=request,
    )


@app.get("/api/admin/tickets")
async def admin_tickets(x_telegram_init_data: str = Header(default=""), status: str = "", limit: int = 30) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        lim = max(1, min(int(limit), 100))
        st = (status or "").strip().lower()
        if st:
            rows = (
                s.query(SupportTicket)
                .filter(SupportTicket.status == st)
                .order_by(SupportTicket.updated_at.desc(), SupportTicket.id.desc())
                .limit(lim)
                .all()
            )
        else:
            rows = list_active_tickets(s, limit=lim)
        return {"tickets": [_ticket_summary_row(t, list_ticket_messages(s, t.id, limit=1)) for t in rows]}
    finally:
        s.close()


@app.get("/api/admin/tickets/{ticket_id}")
async def admin_ticket_detail(ticket_id: int, x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        ticket = get_ticket_by_id(s, int(ticket_id))
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        messages = list_ticket_messages(s, ticket.id, limit=100)
        return {"ticket": _ticket_detail_row(ticket, messages)}
    finally:
        s.close()


@app.post("/api/admin/tickets/{ticket_id}/reply")
async def admin_ticket_reply(
    ticket_id: int,
    payload: AdminTicketReplyIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="ticket.reply",
        target_type="ticket",
        target_id=str(ticket_id),
        payload={
            "body": payload.body,
            "attachment_id": payload.attachment_id,
            "media_type": payload.media_type,
            "media_file_id": payload.media_file_id,
            "media_payload": payload.media_payload,
        },
        request=request,
    )


@app.post("/api/admin/tickets/{ticket_id}/status")
async def admin_ticket_status(
    ticket_id: int,
    payload: AdminTicketStatusIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="ticket.status",
        target_type="ticket",
        target_id=str(ticket_id),
        payload={"status": payload.status},
        request=request,
    )


@app.get("/api/admin/nodes/health")
async def admin_nodes_health(x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    now = _utcnow()
    stale_after_seconds = max(300, int(os.getenv("NODE_METRICS_STALE_AFTER_SECONDS", "900")))
    s = SessionLocal()
    try:
        rows = s.query(Node).order_by(Node.enabled.desc(), Node.health_score.desc(), Node.weight.desc(), Node.code.asc()).all()
        metrics_snapshot = _ops_build_admin_metrics_status_snapshot(
            s=s,
            now=now,
            stale_after_seconds=stale_after_seconds,
        )
        alert_kinds_by_code = {
            str(item.get("node_code") or item.get("code") or "").strip().lower(): list(
                item.get("display_alert_kinds") or item.get("alert_kinds") or []
            )
            for item in list(metrics_snapshot.get("nodes") or [])
        }
        window_start = now - timedelta(hours=24)
        peak_by_code = {
            str(node_code or ""): (float(peak_mbps) if peak_mbps is not None else None)
            for node_code, peak_mbps in (
                s.query(
                    NodeHealthSample.node_code,
                    func.max(NodeHealthSample.network_total_mbps),
                )
                .filter(NodeHealthSample.sampled_at >= window_start)
                .group_by(NodeHealthSample.node_code)
                .all()
            )
        }
        mapped_counts = {
            int(node_id): int(count or 0)
            for node_id, count in (
                s.query(UserNode.node_id, func.count(func.distinct(UserNode.tg_id)))
                .group_by(UserNode.node_id)
                .all()
            )
        }
    finally:
        s.close()

    online_summary_by_code: dict[str, dict[str, Any]] = {}
    panel = ControlPanel()
    try:
        await panel.login()
        online_summary_by_code = await panel.get_node_online_summaries(
            node_codes=[str(getattr(n, "code", "") or "").strip() for n in rows if str(getattr(n, "code", "") or "").strip()]
        )
    except Exception:
        online_summary_by_code = {}
    finally:
        await panel.close()

    return {
        "nodes": [
            _serialize_admin_node(
                n,
                mapped_users=mapped_counts.get(int(n.id), 0),
                network_peak_mbps_24h=peak_by_code.get(str(n.code or ""), None),
                online_keys_now=int((online_summary_by_code.get(str(n.code or ""), {}) or {}).get("online_keys_now") or 0),
                online_connections_now=int((online_summary_by_code.get(str(n.code or ""), {}) or {}).get("online_connections_now") or 0),
                alert_kinds=alert_kinds_by_code.get(str(n.code or "").strip().lower(), []),
                now=now,
            )
            for n in rows
        ]
    }


@app.get("/api/admin/nodes/capacity")
async def admin_nodes_capacity(x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        return _ops_admin_nodes_capacity_payload(s=s, now=_utcnow())
    finally:
        s.close()


def _provider_quota_bytes_from_payload(payload: AdminProviderQuotaIn | AdminProviderQuotaPatchIn, existing: int = 0) -> int:
    data = payload.model_dump(exclude_unset=True)
    if data.get("included_bytes") is not None:
        return max(0, int(data.get("included_bytes") or 0))
    if data.get("included_gb") is not None:
        return _ops_gb_to_bytes(float(data.get("included_gb") or 0.0))
    return max(0, int(existing or 0))


def _provider_quota_safe_payload(row: ProviderTrafficQuota | None) -> dict[str, Any] | None:
    if not row:
        return None
    payload = _ops_provider_quota_payload(row)
    notes = str(payload.pop("notes", "") or "")
    payload.update(
        {
            "notes_present": bool(notes),
            "notes_length": len(notes),
            "notes_sha256": hashlib.sha256(notes.encode("utf-8")).hexdigest(),
        }
    )
    return payload


def _provider_quota_audit_payload(row: ProviderTrafficQuota | None) -> dict[str, Any] | None:
    return _provider_quota_safe_payload(row)


def _add_provider_quota_audit(
    *,
    s,
    quota: ProviderTrafficQuota | None,
    node_code: str,
    actor: int,
    action: str,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> None:
    s.add(
        ProviderTrafficQuotaAudit(
            quota_id=int(quota.id) if quota and quota.id is not None else None,
            node_code=str(node_code or "").strip().lower()[:32],
            actor_tg_id=int(actor) if actor else None,
            action=str(action or "")[:32],
            before_json=json.dumps(before, ensure_ascii=False, separators=(",", ":"))[:4000] if before is not None else None,
            after_json=json.dumps(after, ensure_ascii=False, separators=(",", ":"))[:4000] if after is not None else None,
            created_at=_utcnow(),
        )
    )


async def _deliver_ops_alert_notifications(notifications: list[dict[str, Any]]) -> None:
    if not notifications or not int(Settings.ADMIN_ID or 0):
        return
    delivered: dict[str, str] = {}
    for batch in _ops_alert_notification_batches(notifications):
        ok = await _telegram_send_message(
            int(Settings.ADMIN_ID),
            str(batch.get("text") or ""),
            disable_web_page_preview=True,
        )
        for fingerprint in batch.get("fingerprints") or []:
            delivered[str(fingerprint)] = "sent" if ok else "send_failed"
    if not delivered:
        return
    s = SessionLocal()
    try:
        now = _utcnow()
        for fingerprint, status in delivered.items():
            row = s.query(OpsAlert).filter(OpsAlert.fingerprint == fingerprint).first()
            if not row:
                continue
            row.last_delivery_at = now
            row.last_delivery_status = status
            row.updated_at = now
        s.commit()
    except Exception:
        s.rollback()
    finally:
        s.close()


async def _refresh_ops_alerts_for_payload(*, s, now: datetime) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    stale_after_seconds = max(300, int(os.getenv("NODE_METRICS_STALE_AFTER_SECONDS", "900")))
    rows, notifications, _metrics_status, _capacity_payload = _ops_refresh_alerts_for_current_state(
        s=s,
        now=now,
        free_limit_gb=FREE_STANDARD_QUOTA_GB,
        cycle_days=int(_FREE_TIER_FACTS.get("cycle_days") or 30),
        stale_after_seconds=stale_after_seconds,
    )
    return rows, notifications


def _admin_ops_compact_summary_payload(*, s, now: datetime, metrics_status: dict[str, Any]) -> dict[str, Any]:
    active_user_filter = _effective_active_user_filter(now=now)
    user_sub_type = func.upper(func.coalesce(User.sub_type, ""))
    user_counts = (
        s.query(
            func.count(User.tg_id).label("total"),
            func.sum(case((active_user_filter, 1), else_=0)).label("active"),
            func.sum(case((user_sub_type == "FREE", 1), else_=0)).label("free"),
            func.sum(case((user_sub_type == "PAID", 1), else_=0)).label("paid"),
        )
        .one()
    )
    node_counts = (
        s.query(
            func.count(Node.id).label("total"),
            func.sum(case((Node.is_healthy == True, 1), else_=0)).label("healthy"),
        )
        .filter(Node.enabled == True)
        .one()
    )
    open_tickets = int(
        s.query(func.count(SupportTicket.id))
        .filter(SupportTicket.status != STATUS_CLOSED)
        .scalar()
        or 0
    )
    total_nodes = int(getattr(node_counts, "total", 0) or 0)
    healthy_nodes = int(getattr(node_counts, "healthy", 0) or 0)
    return {
        "users": {
            "total": int(getattr(user_counts, "total", 0) or 0),
            "active": int(getattr(user_counts, "active", 0) or 0),
            "free": int(getattr(user_counts, "free", 0) or 0),
            "paid": int(getattr(user_counts, "paid", 0) or 0),
        },
        "tickets": {"open": open_tickets},
        "nodes": {"total": total_nodes, "healthy": healthy_nodes},
        "errors": {
            "stale_metrics": bool(metrics_status.get("status") != "fresh"),
            "unhealthy_nodes": max(0, total_nodes - healthy_nodes),
            "open_tickets": open_tickets,
        },
    }


@app.get("/api/admin/provider-quotas")
async def admin_provider_quotas(x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        rows = s.query(ProviderTrafficQuota).order_by(ProviderTrafficQuota.node_code.asc()).all()
        return {"ok": True, "quotas": [_provider_quota_safe_payload(row) for row in rows]}
    finally:
        s.close()


@app.post("/api/admin/provider-quotas")
async def admin_provider_quota_create(
    payload: AdminProviderQuotaIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    node_code = str(payload.node_code or "").strip().lower()
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="provider_quota.create",
        target_type="provider_quota",
        target_id=node_code,
        payload=payload.model_dump(),
        request=request,
    )


@app.patch("/api/admin/provider-quotas/{node_code}")
async def admin_provider_quota_update(
    node_code: str,
    payload: AdminProviderQuotaPatchIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    wanted = str(node_code or "").strip().lower()
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="provider_quota.update",
        target_type="provider_quota",
        target_id=wanted,
        payload=payload.model_dump(exclude_unset=True),
        request=request,
    )


@app.delete("/api/admin/provider-quotas/{node_code}")
async def admin_provider_quota_delete(
    node_code: str,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    wanted = str(node_code or "").strip().lower()
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="provider_quota.delete",
        target_type="provider_quota",
        target_id=wanted,
        payload={},
        request=request,
    )


@app.get("/api/admin/provider-quotas/status")
async def admin_provider_quota_status(x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        now = _utcnow()
        return {"ok": True, "generated_at": _safe_iso(now), "nodes": _ops_provider_quota_status_rows(s=s, now=now)}
    finally:
        s.close()


def _admin_free_tier_facts_payload() -> dict[str, Any]:
    enabled = bool(_FREE_TIER_FACTS.get("enabled", False)) and free_tier_enabled()
    return {
        "enabled": enabled,
        "status": str(_FREE_TIER_FACTS.get("status") or "retired_pending_replacement"),
        "node_pool": str(_FREE_TIER_FACTS.get("location_code") or "NL-free") if enabled else None,
        "traffic_limit_gb": FREE_STANDARD_QUOTA_GB,
        "traffic_limit_bytes": int(FREE_STANDARD_QUOTA_BYTES),
        "cycle_days": int(_FREE_TIER_FACTS.get("cycle_days") or 30),
        "speed_limit_mbps": int(_FREE_TIER_FACTS.get("speed_limit_mbps") or 50),
        "soft_mode_speed_limit_mbps": int(_FREE_TIER_FACTS.get("soft_mode_speed_limit_mbps") or 2),
        "device_limit": int(_FREE_TIER_FACTS.get("device_limit") or 1),
        "standard_access_role": str(_FREE_TIER_FACTS.get("standard_access_role") or "free_standard"),
        "soft_access_role": str(_FREE_TIER_FACTS.get("soft_access_role") or "free_soft"),
        "monthly_reset": enabled and bool(_FREE_TIER_FACTS.get("monthly_reset", True)),
        "source": "shared_product_facts",
    }


@app.get("/api/admin/free-tier/summary")
async def admin_free_tier_summary(x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        now = _utcnow()
        return {
            "ok": True,
            "summary": _ops_free_tier_summary(
                s=s,
                now=now,
                free_limit_gb=FREE_STANDARD_QUOTA_GB,
                cycle_days=int(_FREE_TIER_FACTS.get("cycle_days") or 30),
            ),
            "facts": _admin_free_tier_facts_payload(),
        }
    finally:
        s.close()


@app.get("/api/admin/free-tier/users")
async def admin_free_tier_users(
    x_telegram_init_data: str = Header(default=""),
    q: str = Query(default=""),
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        now = _utcnow()
        rows, total = _ops_free_tier_user_rows(
            s=s,
            now=now,
            free_limit_gb=FREE_STANDARD_QUOTA_GB,
            cycle_days=int(_FREE_TIER_FACTS.get("cycle_days") or 30),
            limit=int(limit),
            offset=int(offset),
            q=q,
        )
        return {"ok": True, "generated_at": _safe_iso(now), "total": total, "facts": _admin_free_tier_facts_payload(), "users": rows}
    finally:
        s.close()


@app.get("/api/admin/nodes/timeseries")
async def admin_nodes_timeseries(
    x_telegram_init_data: str = Header(default=""),
    node_code: str = Query(default=""),
    from_: str = Query(default="", alias="from"),
    to: str = Query(default="", alias="to"),
) -> dict:
    _require_admin(x_telegram_init_data)
    from_dt, to_dt = _admin_metrics_range(from_, to, max_days=90)
    s = SessionLocal()
    try:
        return {
            "ok": True,
            "from": from_dt.isoformat(),
            "to": to_dt.isoformat(),
            "node_code": str(node_code or "").strip().lower() or None,
            "rows": _ops_node_timeseries_rows(s=s, from_dt=from_dt, to_dt=to_dt, node_code=node_code),
        }
    finally:
        s.close()


@app.get("/api/admin/traffic/summary")
async def admin_traffic_summary(
    x_telegram_init_data: str = Header(default=""),
    from_: str = Query(default="", alias="from"),
    to: str = Query(default="", alias="to"),
) -> dict:
    _require_admin(x_telegram_init_data)
    from_dt, to_dt = _admin_metrics_range(from_, to, max_days=120)
    s = SessionLocal()
    try:
        rows = _ops_traffic_summary_rows(s=s, from_dt=from_dt, to_dt=to_dt)
        totals_by_pool: dict[str, int] = {}
        for row in rows:
            pool = str(row.get("pool_code") or "unknown")
            totals_by_pool[pool] = int(totals_by_pool.get(pool, 0)) + int(row.get("traffic_bytes") or 0)
        return {
            "ok": True,
            "from": from_dt.date().isoformat(),
            "to": to_dt.date().isoformat(),
            "rows": rows,
            "totals_by_pool": {pool: {"traffic_bytes": value, "traffic_gb": _ops_bytes_to_gb(value)} for pool, value in sorted(totals_by_pool.items())},
        }
    finally:
        s.close()


def _parse_ru_history_datetime(raw: str, *, field: str) -> datetime | None:
    value = str(raw or "").strip()
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, OverflowError) as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid RU history {field}",
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _ru_read_model_http_error(error: RuProbeReadModelError) -> HTTPException:
    messages = {
        "invalid_cursor": "Invalid RU history cursor",
        "invalid_limit": "Invalid RU history limit",
        "invalid_from": "Invalid RU history from",
        "invalid_to": "Invalid RU history to",
        "invalid_range": "Invalid RU history range",
        "invalid_verdict": "Invalid RU history verdict",
        "invalid_node_code": "Invalid RU history node_code",
        "invalid_now": "Invalid RU read timestamp",
    }
    return HTTPException(
        status_code=400,
        detail=messages.get(error.code, "Invalid RU read request"),
    )


@app.get("/api/admin/probes/ru-origin/latest")
async def admin_ru_probe_latest(
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        return get_latest_ru_status(s, now=_utcnow())
    finally:
        s.close()


@app.get("/api/admin/probes/ru-origin/runs")
async def admin_ru_probe_runs(
    x_telegram_init_data: str = Header(default=""),
    node_code: str = Query(default=""),
    from_: str = Query(default="", alias="from"),
    to: str = Query(default=""),
    verdict: str = Query(default=""),
    limit: int = Query(default=50),
    cursor: str = Query(default=""),
) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        try:
            return get_ru_run_history(
                s,
                node_code=node_code or None,
                from_at=_parse_ru_history_datetime(from_, field="from"),
                to_at=_parse_ru_history_datetime(to, field="to"),
                verdict=verdict or None,
                limit=limit,
                cursor=cursor or None,
            )
        except RuProbeReadModelError as exc:
            raise _ru_read_model_http_error(exc) from exc
    finally:
        s.close()


@app.get("/api/admin/probes/ru-origin/uploader-status")
async def admin_ru_probe_uploader_status(
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        return get_ru_uploader_status(s, now=_utcnow())
    finally:
        s.close()


def _release_read_http_error(error: ReleaseEvidenceReadError) -> HTTPException:
    return HTTPException(
        status_code=400,
        detail={
            "code": error.code,
            "message": "Invalid release evidence read request",
        },
    )


@app.get("/api/admin/releases/candidates")
async def admin_release_candidates(
    x_telegram_init_data: str = Header(default=""),
    limit: int = Query(default=50),
    cursor: str = Query(default=""),
) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        try:
            return list_release_candidates(
                s,
                limit=limit,
                cursor=cursor or None,
                now=_utcnow(),
            )
        except ReleaseEvidenceReadError as exc:
            raise _release_read_http_error(exc) from exc
    finally:
        s.close()


@app.get("/api/admin/releases/{candidate_id}/readiness")
async def admin_release_candidate_readiness(
    candidate_id: str,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        try:
            return get_release_readiness(s, candidate_id, now=_utcnow())
        except ReleaseEvidenceNotFound as exc:
            raise HTTPException(
                status_code=404,
                detail={"code": exc.code, "message": "Release candidate not found"},
            ) from exc
        except ReleaseEvidenceReadError as exc:
            raise _release_read_http_error(exc) from exc
    finally:
        s.close()


@app.get("/api/admin/nodes/{node_code}/observability")
async def admin_node_observability(
    node_code: str,
    include_ru_history: bool = Query(default=True),
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    _require_admin(x_telegram_init_data)
    s = SessionLocal()
    try:
        payload = _ops_build_node_observability(
            s=s,
            node_code=node_code,
            now=_utcnow(),
            metrics_stale_after_seconds=max(
                300,
                int(os.getenv("NODE_METRICS_STALE_AFTER_SECONDS", "900")),
            ),
            include_ru_history=include_ru_history,
        )
        if payload is None:
            raise HTTPException(status_code=404, detail="Node not found")
        return payload
    finally:
        s.close()


@app.get("/api/admin/search")
async def admin_global_search(
    q: str = Query(default=""),
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    _require_admin(x_telegram_init_data)
    normalized = str(q or "").strip()
    if len(normalized) < 2:
        raise HTTPException(
            status_code=400,
            detail="Search query must contain at least 2 characters",
        )
    if len(normalized) > 128:
        raise HTTPException(status_code=400, detail="Search query is too long")
    s = SessionLocal()
    try:
        return {
            "ok": True,
            "results": _ops_admin_search_results(
                s=s,
                q=normalized,
                limit=20,
            ),
        }
    finally:
        s.close()


@app.get("/api/admin/alerts")
async def admin_ops_alerts(x_telegram_init_data: str = Header(default=""), status: str = Query(default="active")) -> dict:
    _require_admin(x_telegram_init_data)
    wanted = str(status or "active").strip().lower()
    now = _utcnow()
    s = SessionLocal()
    try:
        refreshed, notifications = await _refresh_ops_alerts_for_payload(s=s, now=now)
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
    await _deliver_ops_alert_notifications(notifications)
    if wanted in {"active", "open"}:
        rows = [row for row in refreshed if row["status"] in {"active", "silenced"}]
    elif wanted in {"all", "*"}:
        rows = refreshed
    else:
        rows = [row for row in refreshed if row["status"] == wanted or row.get("raw_status") == wanted]
    return {"ok": True, "generated_at": _safe_iso(now), "alerts": rows, "notifications": len(notifications)}


@app.post("/api/admin/alerts/{alert_id}/ack")
async def admin_ops_alert_ack(alert_id: int, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    s = SessionLocal()
    try:
        row = s.query(OpsAlert).filter(OpsAlert.id == int(alert_id)).first()
        if not row:
            raise HTTPException(status_code=404, detail="Alert not found")
        row.acknowledged_at = _utcnow()
        row.acknowledged_by = int(actor)
        row.updated_at = _utcnow()
        s.commit()
        payload = _ops_alert_payload(row)
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
    _audit_admin(actor_tg_id=actor, action="admin_ops_alert_ack", meta={"alert_id": int(alert_id)})
    return {"ok": True, "alert": payload}


@app.post("/api/admin/alerts/{alert_id}/silence")
async def admin_ops_alert_silence(alert_id: int, payload: AdminAlertSilenceIn, x_telegram_init_data: str = Header(default="")) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    s = SessionLocal()
    try:
        row = s.query(OpsAlert).filter(OpsAlert.id == int(alert_id)).first()
        if not row:
            raise HTTPException(status_code=404, detail="Alert not found")
        row.silence_until = _utcnow() + timedelta(minutes=int(payload.minutes))
        row.acknowledged_at = row.acknowledged_at or _utcnow()
        row.acknowledged_by = row.acknowledged_by or int(actor)
        row.updated_at = _utcnow()
        meta = _json_obj(row.metadata_json)
        if payload.note:
            meta["silence_note"] = str(payload.note or "")[:300]
            row.metadata_json = json.dumps(meta, ensure_ascii=False, separators=(",", ":"))[:4000]
        s.commit()
        alert_out = _ops_alert_payload(row)
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
    _audit_admin(actor_tg_id=actor, action="admin_ops_alert_silence", meta={"alert_id": int(alert_id), "minutes": int(payload.minutes)})
    return {"ok": True, "alert": alert_out}


@app.get("/api/admin/ops/overview")
async def admin_ops_overview(x_telegram_init_data: str = Header(default="")) -> dict:
    _require_admin(x_telegram_init_data)
    now = _utcnow()
    stale_after_seconds = max(300, int(os.getenv("NODE_METRICS_STALE_AFTER_SECONDS", "900")))
    s = SessionLocal()
    try:
        metrics_status = _ops_build_admin_metrics_status_snapshot(s=s, now=now, stale_after_seconds=stale_after_seconds)
        summary_payload = _admin_ops_compact_summary_payload(
            s=s,
            now=now,
            metrics_status=metrics_status,
        )
        capacity_payload = _ops_admin_nodes_capacity_payload(s=s, now=now)
        provider_status = _ops_provider_quota_status_rows(s=s, now=now)
        free_summary = _ops_free_tier_summary(
            s=s,
            now=now,
            free_limit_gb=FREE_STANDARD_QUOTA_GB,
            cycle_days=int(_FREE_TIER_FACTS.get("cycle_days") or 30),
        )
        alert_rows = [
            _ops_alert_payload(row, now=now)
            for row in (
                s.query(OpsAlert)
                .filter(OpsAlert.source.in_(sorted(_OPS_MANAGED_ALERT_SOURCES)))
                .order_by(OpsAlert.status.asc(), OpsAlert.severity.asc(), OpsAlert.last_seen_at.desc())
                .all()
            )
        ]
    finally:
        s.close()
    active_alerts = [row for row in alert_rows if row["status"] in {"active", "silenced"}]
    return {
        "ok": True,
        "generated_at": _safe_iso(now),
        "summary": summary_payload,
        "metrics": metrics_status,
        "capacity": capacity_payload,
        "free_tier": free_summary,
        "provider_quotas": provider_status,
        "alerts": {
            "active": active_alerts,
            "active_count": len(active_alerts),
            "critical_count": sum(1 for row in active_alerts if row.get("severity") == "critical"),
            "warning_count": sum(1 for row in active_alerts if row.get("severity") == "warning"),
        },
    }


@app.get("/api/admin/keys/pressure")
async def admin_keys_pressure(
    x_telegram_init_data: str = Header(default=""),
    state: str = Query(default=""),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    _require_admin(x_telegram_init_data)
    wanted_state = str(state or "").strip().lower()
    s = SessionLocal()
    try:
        query = s.query(KeyPressureState)
        if wanted_state:
            query = query.filter(KeyPressureState.state == wanted_state)
        rows = query.order_by(KeyPressureState.pressure_score.desc(), KeyPressureState.updated_at.desc()).limit(int(limit)).all()
        keys = []
        for row in rows:
            try:
                reasons = json.loads(str(row.reasons_json or "[]"))
            except Exception:
                reasons = []
            keys.append(
                {
                    "key_id": int(row.key_id),
                    "tg_id": int(row.tg_id) if row.tg_id is not None else None,
                    "node_code": str(row.node_code or "") or None,
                    "panel_email": str(row.panel_email or "") or None,
                    "state": str(row.state or "ok"),
                    "pressure_score": float(row.pressure_score or 0.0),
                    "reasons": reasons if isinstance(reasons, list) else [],
                    "distinct_source_ips_1h": int(row.distinct_source_ips_1h or 0),
                    "distinct_source_ips_24h": int(row.distinct_source_ips_24h or 0),
                    "node_count_24h": int(row.node_count_24h or 0),
                    "traffic_gb_24h": float(row.traffic_gb_24h or 0.0),
                    "manual_review_required": bool(row.manual_review_required),
                    "updated_at": _safe_iso(row.updated_at),
                }
            )
        return {"ok": True, "keys": keys}
    finally:
        s.close()


def _parse_panel_datetime(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed
    except Exception:
        return None


def _pressure_reasons(row: KeyPressureState) -> list[str]:
    try:
        parsed = json.loads(str(row.reasons_json or "[]"))
    except Exception:
        parsed = []
    return [str(item) for item in parsed if str(item or "").strip()] if isinstance(parsed, list) else []


def _admin_online_row_id(*, tg_id: int | None, panel_email: str, client_uuid: str, node_code: str) -> str:
    if tg_id is not None:
        return f"user:{int(tg_id)}"
    subject = str(panel_email or "").strip().lower() or str(client_uuid or "").strip() or str(node_code or "").strip().lower()
    digest = hashlib.sha256(f"admin-online-row-v1\0{subject}".encode("utf-8")).hexdigest()[:24]
    return f"panel:{digest}"


def _safe_admin_online_panel_errors(errors: list[dict]) -> list[dict[str, str | None]]:
    allowed_codes = {"missing_node_code", "panel_request_failed", "panel_unavailable"}
    safe: list[dict[str, str | None]] = []
    for item in errors:
        raw_node_code = str((item or {}).get("node_code") or "").strip().lower()
        node_code = raw_node_code if re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,31}", raw_node_code) else None
        raw_code = str((item or {}).get("evidence_code") or (item or {}).get("error_code") or "").strip().lower()
        evidence_code = raw_code if raw_code in allowed_codes else "panel_request_failed"
        safe.append({"node_code": node_code, "evidence_code": evidence_code})
    return safe


def _admin_online_users_payload(*, s, live_rows: list[dict], errors: list[dict], limit: int) -> dict[str, Any]:
    tg_ids = sorted(
        {
            int(row.get("tg_id"))
            for row in live_rows
            if row.get("tg_id") is not None and str(row.get("tg_id")).lstrip("-").isdigit()
        }
    )
    panel_emails = sorted({str(row.get("panel_email") or "").strip().lower() for row in live_rows if str(row.get("panel_email") or "").strip()})

    users_by_tg: dict[int, User] = {}
    users_by_email: dict[str, User] = {}
    if tg_ids:
        for user in s.query(User).filter(User.tg_id.in_(tg_ids)).all():
            users_by_tg[int(user.tg_id)] = user
            email = str(getattr(user, "email", "") or "").strip().lower()
            if email:
                users_by_email[email] = user
    if panel_emails:
        for user in s.query(User).filter(func.lower(func.coalesce(User.email, "")).in_(panel_emails)).all():
            users_by_tg[int(user.tg_id)] = user
            email = str(getattr(user, "email", "") or "").strip().lower()
            if email:
                users_by_email[email] = user

    pressure_rows: list[KeyPressureState] = []
    pressure_filters = []
    if tg_ids:
        pressure_filters.append(KeyPressureState.tg_id.in_(tg_ids))
    if panel_emails:
        pressure_filters.append(func.lower(func.coalesce(KeyPressureState.panel_email, "")).in_(panel_emails))
    if pressure_filters:
        pressure_rows = s.query(KeyPressureState).filter(or_(*pressure_filters)).all()
    pressure_by_tg: dict[int, list[KeyPressureState]] = {}
    pressure_by_email: dict[str, list[KeyPressureState]] = {}
    for row in pressure_rows:
        if row.tg_id is not None:
            pressure_by_tg.setdefault(int(row.tg_id), []).append(row)
        email = str(row.panel_email or "").strip().lower()
        if email:
            pressure_by_email.setdefault(email, []).append(row)

    observer_by_tg: dict[int, ObserverUserState] = {}
    if tg_ids:
        for row in s.query(ObserverUserState).filter(ObserverUserState.tg_id.in_(tg_ids)).all():
            observer_by_tg[int(row.tg_id)] = row

    aggregates: dict[str, dict[str, Any]] = {}
    for live in live_rows:
        raw_tg_id = live.get("tg_id")
        tg_id = int(raw_tg_id) if raw_tg_id is not None and str(raw_tg_id).lstrip("-").isdigit() else None
        panel_email = str(live.get("panel_email") or "").strip()
        email_key = panel_email.lower()
        user = users_by_tg.get(int(tg_id)) if tg_id is not None else None
        if user is None and email_key:
            user = users_by_email.get(email_key)
        effective_tg_id = int(user.tg_id) if user else tg_id
        row_id = _admin_online_row_id(
            tg_id=effective_tg_id,
            panel_email=email_key,
            client_uuid=str(live.get("client_uuid") or ""),
            node_code=str(live.get("node_code") or ""),
        )
        agg = aggregates.setdefault(
            row_id,
            {
                "row_id": row_id,
                "tg_id": effective_tg_id,
                "username": getattr(user, "username", None) if user else None,
                "display_name": getattr(user, "display_name", None) if user else None,
                "sub_type": getattr(user, "sub_type", None) if user else None,
                "status": _user_effective_status(user) if user else "unknown",
                "origin": _user_origin(user) if user else "unknown",
                "nodes_online_set": set(),
                "online_keys_now": 0,
                "online_connections_now": 0,
                "ip_count": 0,
                "panel_email_set": set(),
                "last_online_dt": None,
                "last_online_at": None,
                "risk_flags": set(),
                "pressure_score": 0.0,
                "traffic_gb_24h": 0.0,
            },
        )
        if user and agg.get("username") is None:
            agg["username"] = getattr(user, "username", None)
            agg["display_name"] = getattr(user, "display_name", None)
            agg["sub_type"] = getattr(user, "sub_type", None)
            agg["status"] = _user_effective_status(user)
            agg["origin"] = _user_origin(user)
        node_code = str(live.get("node_code") or "").strip()
        if node_code:
            agg["nodes_online_set"].add(node_code)
        if panel_email:
            agg["panel_email_set"].add(panel_email)
        ip_count = max(1, int(live.get("ip_count") or 1))
        agg["online_keys_now"] += 1
        agg["online_connections_now"] += ip_count
        agg["ip_count"] += ip_count
        last_dt = _parse_panel_datetime(live.get("last_online_at"))
        if last_dt is not None and (agg["last_online_dt"] is None or last_dt > agg["last_online_dt"]):
            agg["last_online_dt"] = last_dt
            agg["last_online_at"] = _safe_iso(last_dt)

    for agg in aggregates.values():
        tg_id = agg.get("tg_id")
        panel_email_values = {str(email).strip().lower() for email in (agg.get("panel_email_set") or set()) if str(email).strip()}
        pressure_matches: list[KeyPressureState] = []
        if tg_id is not None:
            pressure_matches.extend(pressure_by_tg.get(int(tg_id), []))
        for email in panel_email_values:
            pressure_matches.extend(pressure_by_email.get(email, []))
        seen_pressure_keys: set[int] = set()
        for pressure in pressure_matches:
            key_id = int(pressure.key_id)
            if key_id in seen_pressure_keys:
                continue
            seen_pressure_keys.add(key_id)
            state = str(pressure.state or "ok")
            if state != "ok":
                agg["risk_flags"].add(f"key_pressure:{state}")
            if bool(pressure.manual_review_required):
                agg["risk_flags"].add("manual_review")
            for reason in _pressure_reasons(pressure):
                agg["risk_flags"].add(str(reason))
            agg["pressure_score"] = max(float(agg.get("pressure_score") or 0.0), float(pressure.pressure_score or 0.0))
            agg["traffic_gb_24h"] += float(pressure.traffic_gb_24h or 0.0)
        if int(agg.get("ip_count") or 0) > 1:
            agg["risk_flags"].add("multi_ip")
        if tg_id is None:
            agg["risk_flags"].add("unknown_identity")
        elif int(tg_id) in observer_by_tg:
            observer = observer_by_tg[int(tg_id)]
            state = str(observer.state or "ok")
            if state != "ok":
                agg["risk_flags"].add(f"observer:{state}")

    rows: list[dict[str, Any]] = []
    for agg in aggregates.values():
        agg.pop("panel_email_set", None)
        nodes_online = sorted({str(code) for code in agg.pop("nodes_online_set", set()) if str(code).strip()})
        agg.pop("last_online_dt", None)
        risk_flags = sorted({str(flag) for flag in agg.pop("risk_flags", set()) if str(flag).strip()})
        rows.append(
            {
                **agg,
                "nodes_online": nodes_online,
                "nodes_online_count": len(nodes_online),
                "risk_flags": risk_flags,
                "traffic_gb_24h": round(float(agg.get("traffic_gb_24h") or 0.0), 3),
                "pressure_score": round(float(agg.get("pressure_score") or 0.0), 1),
            }
        )
    rows.sort(
        key=lambda row: (
            "manual_review" not in set(row.get("risk_flags") or []),
            -float(row.get("pressure_score") or 0.0),
            -int(row.get("ip_count") or 0),
            str(row.get("last_online_at") or ""),
        )
    )
    bounded = rows[: max(1, min(int(limit), 500))]
    safe_errors = _safe_admin_online_panel_errors(errors)
    return {
        "ok": True,
        "generated_at": _safe_iso(_utcnow()),
        "rows": bounded,
        "total": len(rows),
        "limit": max(1, min(int(limit), 500)),
        "summary": {
            "online_identities": len(rows),
            "known_users_online": sum(1 for row in rows if row.get("tg_id") is not None),
            "unknown_online_keys": sum(1 for row in rows if row.get("tg_id") is None),
            "online_keys_now": sum(int(row.get("online_keys_now") or 0) for row in rows),
            "online_connections_now": sum(int(row.get("online_connections_now") or 0) for row in rows),
            "nodes_with_panel_errors": len(safe_errors),
            "raw_ip_exposed": False,
        },
        "panel_errors": safe_errors,
        "notes": [
            "Список построен по оперативному состоянию панели.",
            "IP-адреса здесь не возвращаются; исходные IP-адреса доступны только через отдельный запрос расследования пользователя.",
        ],
    }


@app.get("/api/admin/online/users")
async def admin_online_users(
    x_telegram_init_data: str = Header(default=""),
    limit: int = Query(default=200, ge=1, le=500),
    only: str = Query(default=""),
) -> dict[str, Any]:
    _require_admin(x_telegram_init_data)
    only_codes = [part.strip().lower() for part in str(only or "").split(",") if part.strip()]
    panel = ControlPanel()
    try:
        live = await panel.get_node_online_clients(node_codes=only_codes or None)
    finally:
        await panel.close()
    s = SessionLocal()
    try:
        return _admin_online_users_payload(
            s=s,
            live_rows=list(live.get("rows") or []),
            errors=list(live.get("errors") or []),
            limit=int(limit),
        )
    finally:
        s.close()


@app.post("/api/admin/keys/{key_id}/rotate")
async def admin_key_rotate_request(
    key_id: int,
    payload: AdminKeyRotateIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="key.rotate",
        target_type="key",
        target_id=str(key_id),
        payload={"reason": payload.reason, "dry_run": bool(payload.dry_run)},
        request=request,
    )


@app.get("/api/admin/nodes/runtime")
async def admin_nodes_runtime(
    x_telegram_init_data: str = Header(default=""),
    only: str = Query(default=""),
) -> dict:
    _require_admin(x_telegram_init_data)
    only_codes = [part.strip().lower() for part in str(only or "").split(",") if part.strip()]
    panel = ControlPanel()
    try:
        rows = await panel.get_node_runtime_snapshots(node_codes=only_codes or None)
    finally:
        await panel.close()
    return {
        "ok": True,
        "updated_at": _utcnow().isoformat(),
        "nodes": [rows[key] for key in sorted(rows.keys())],
    }


async def _build_admin_node_drift_report(*, only_codes: list[str] | None = None) -> dict:
    panel = ControlPanel()
    try:
        await panel.login()
        return await panel.get_node_drift_report(node_codes=only_codes or [])
    finally:
        await panel.close()


@app.get("/api/admin/nodes/drift")
async def admin_nodes_drift(
    x_telegram_init_data: str = Header(default=""),
    only: str = Query(default=""),
) -> dict:
    _require_admin(x_telegram_init_data)
    only_codes = [part.strip().lower() for part in str(only or "").split(",") if part.strip()]
    result = _build_admin_node_drift_report(only_codes=only_codes)
    if inspect.isawaitable(result):
        return await result
    return result


@app.post("/api/admin/nodes/sync")
async def admin_nodes_sync(
    payload: AdminNodeSyncIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    return await _execute_admin_guarded_action(
        actor_tg_id=actor,
        action="node.sync_global",
        target_type="node_sync",
        target_id="global",
        payload=payload.model_dump(),
        request=request,
    )


@app.post("/api/admin/nodes/{node_code}/drain")
async def admin_node_drain(
    node_code: str,
    payload: AdminNodeLifecycleIn,
    x_telegram_init_data: str = Header(default=""),
    x_admin_intent_id: str = Header(default="", alias="X-Admin-Intent-Id"),
    x_admin_idempotency_key: str = Header(
        default="",
        alias="X-Admin-Idempotency-Key",
    ),
    x_admin_confirmation_sha256: str = Header(
        default="",
        alias="X-Admin-Confirmation-SHA256",
    ),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    wanted = str(node_code or "").strip().lower()
    return await _execute_admin_node_action(
        actor_tg_id=actor,
        action="node.drain",
        node_code=wanted,
        payload={"force": bool(payload.force)},
        intent_id=x_admin_intent_id,
        idempotency_key=x_admin_idempotency_key,
        confirmation_sha256=x_admin_confirmation_sha256,
    )


@app.post("/api/admin/nodes/{node_code}/enable")
async def admin_node_enable(
    node_code: str,
    payload: AdminNodeLifecycleIn,
    x_telegram_init_data: str = Header(default=""),
    x_admin_intent_id: str = Header(default="", alias="X-Admin-Intent-Id"),
    x_admin_idempotency_key: str = Header(
        default="",
        alias="X-Admin-Idempotency-Key",
    ),
    x_admin_confirmation_sha256: str = Header(
        default="",
        alias="X-Admin-Confirmation-SHA256",
    ),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    wanted = str(node_code or "").strip().lower()
    return await _execute_admin_node_action(
        actor_tg_id=actor,
        action="node.enable",
        node_code=wanted,
        payload={"force": bool(payload.force)},
        intent_id=x_admin_intent_id,
        idempotency_key=x_admin_idempotency_key,
        confirmation_sha256=x_admin_confirmation_sha256,
    )


@app.post("/api/admin/nodes/{node_code}/undrain")
async def admin_node_undrain(
    node_code: str,
    payload: AdminNodeLifecycleIn,
    x_telegram_init_data: str = Header(default=""),
    x_admin_intent_id: str = Header(default="", alias="X-Admin-Intent-Id"),
    x_admin_idempotency_key: str = Header(
        default="",
        alias="X-Admin-Idempotency-Key",
    ),
    x_admin_confirmation_sha256: str = Header(
        default="",
        alias="X-Admin-Confirmation-SHA256",
    ),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    wanted = str(node_code or "").strip().lower()
    return await _execute_admin_node_action(
        actor_tg_id=actor,
        action="node.undrain",
        node_code=wanted,
        payload={"force": bool(payload.force)},
        intent_id=x_admin_intent_id,
        idempotency_key=x_admin_idempotency_key,
        confirmation_sha256=x_admin_confirmation_sha256,
    )


def _raise_action_intent_http(error: ActionIntentError) -> None:
    detail: dict[str, Any] = {
        "code": str(error.code),
        "message": str(error.message),
    }
    if error.intent_id:
        detail["intent_id"] = str(error.intent_id)
    if error.audit_id is not None:
        detail["audit_id"] = int(error.audit_id)
    raise HTTPException(
        status_code=int(error.status_code),
        detail=detail,
    )


def _raise_action_intent_header_required(
    *,
    actor_tg_id: int,
    intent_id: str,
    code: str,
    message: str,
) -> None:
    owned_intent_id, audit_id = _action_intent_error_identifiers(
        session_factory=SessionLocal,
        actor_tg_id=actor_tg_id,
        intent_id=intent_id,
    )
    _raise_action_intent_http(
        ActionIntentError(
            code,
            status_code=428,
            message=message,
            intent_id=owned_intent_id,
            audit_id=audit_id,
        )
    )


async def _execute_node_resync_external(context: dict[str, Any]) -> dict[str, Any]:
    execution = context.get("execution")
    if not isinstance(execution, dict):
        raise RuntimeError("missing frozen resync execution context")
    source_node_id = int(execution.get("source_node_id") or 0)
    source_code = str(execution.get("source_node_code") or "").strip().lower()
    selection = execution.get("selection")
    dry_run = bool(execution.get("dry_run", False))
    if source_node_id <= 0 or not source_code or not isinstance(selection, list):
        raise RuntimeError("invalid frozen resync execution context")

    selected_count = len(selection)
    skipped = sum(
        1
        for item in selection
        if isinstance(item, dict) and not item.get("target_nodes")
    )
    if dry_run:
        return {
            "ok": True,
            "code": "resync_dry_run_completed",
            "count": selected_count,
            "changed": 0,
            "failed": 0,
            "skipped": skipped,
        }

    panel = ControlPanel()
    migrated = 0
    failed = 0
    try:
        await panel.login()
        for item in selection:
            if not isinstance(item, dict):
                raise RuntimeError("invalid frozen resync item")
            source_user_node_id = int(item.get("source_user_node_id") or 0)
            recipient_fingerprint = str(item.get("recipient_fingerprint") or "")
            raw_target_nodes = item.get("target_nodes")
            if not isinstance(raw_target_nodes, list):
                raise RuntimeError("invalid frozen target nodes")
            target_nodes: list[dict[str, Any]] = []
            seen_target_ids: set[int] = set()
            seen_target_codes: set[str] = set()
            for raw_target in raw_target_nodes:
                if not isinstance(raw_target, dict):
                    raise RuntimeError("invalid frozen target node")
                target_node_id = int(raw_target.get("id") or 0)
                target_code = str(raw_target.get("code") or "").strip().lower()
                if (
                    target_node_id <= 0
                    or not target_code
                    or target_node_id in seen_target_ids
                    or target_code in seen_target_codes
                ):
                    raise RuntimeError("invalid frozen target node")
                seen_target_ids.add(target_node_id)
                seen_target_codes.add(target_code)
                target_nodes.append({"id": target_node_id, "code": target_code})
            target_codes = [str(target["code"]) for target in target_nodes]
            if source_user_node_id <= 0:
                raise RuntimeError("invalid frozen source mapping")
            if not target_nodes:
                continue

            session = SessionLocal()
            try:
                row = (
                    session.query(UserNode, User)
                    .join(User, User.tg_id == UserNode.tg_id)
                    .filter(
                        UserNode.id == source_user_node_id,
                        UserNode.node_id == source_node_id,
                    )
                    .first()
                )
                if row is None:
                    failed += 1
                    continue
                source_mapping, user = row
                source_node = session.query(Node).filter(Node.id == source_node_id).first()
                if (
                    source_node is None
                    or str(source_node.code or "").strip().lower() != source_code
                ):
                    failed += 1
                    continue
                tg_id = int(user.tg_id)
                client_uuid = str(user.uuid)
                panel_email = str(user.email)
                sub_id = str(getattr(user, "sub_token", "") or user.tg_id)
                current_recipient_fingerprint = _node_resync_recipient_fingerprint(
                    tg_id=tg_id,
                    mapping_client_uuid=str(source_mapping.client_uuid or ""),
                    mapping_panel_email=str(source_mapping.panel_email or ""),
                    user_uuid=client_uuid,
                    user_email=panel_email,
                    sub_id=sub_id,
                )
                if not hmac.compare_digest(
                    recipient_fingerprint,
                    current_recipient_fingerprint,
                ):
                    failed += 1
                    continue
            finally:
                session.close()

            ensure_results = await panel.ensure_user_on_all_nodes(
                tg_id=tg_id,
                client_uuid=client_uuid,
                email=panel_email,
                sub_id=sub_id,
                enable=True,
                only_node_codes=target_codes,
            )
            successful_codes = {
                str(code or "").strip().lower()
                for code, value in ensure_results.items()
                if bool(value) and str(code or "").strip().lower() in seen_target_codes
            }
            if not successful_codes:
                failed += 1
                continue

            disable_results = await panel.set_existing_user_enabled_on_nodes(
                tg_id=tg_id,
                node_codes=[source_code],
                enable=False,
                sub_id=sub_id,
            )
            source_disabled = any(
                str(code or "").strip().lower() == source_code and bool(value)
                for code, value in disable_results.items()
            )
            if not source_disabled:
                failed += 1
                continue

            session = SessionLocal()
            try:
                target_ids = [int(target["id"]) for target in target_nodes]
                dialect = str(session.get_bind().dialect.name)
                if dialect == "postgresql":
                    for locked_node_id in sorted({source_node_id, *target_ids}):
                        session.execute(
                            sql_text(
                                "SELECT pg_advisory_xact_lock(:lock_namespace, :node_id)"
                            ),
                            {
                                "lock_namespace": NODE_MAPPING_LOCK_NAMESPACE,
                                "node_id": int(locked_node_id),
                            },
                        )
                source_query = session.query(Node).filter(Node.id == source_node_id)
                target_query = session.query(Node).filter(Node.id.in_(target_ids))
                if dialect == "postgresql":
                    source_query = source_query.with_for_update()
                    target_query = target_query.with_for_update()
                current_source = source_query.first()
                current_targets = target_query.all()
                current_by_id = {int(node.id): node for node in current_targets}
                frozen_targets_match = (
                    current_source is not None
                    and str(current_source.code or "").strip().lower() == source_code
                    and len(current_by_id) == len(target_nodes)
                    and all(
                        int(target["id"]) in current_by_id
                        and str(current_by_id[int(target["id"])].code or "").strip().lower()
                        == str(target["code"])
                        for target in target_nodes
                    )
                )
                if not frozen_targets_match:
                    session.rollback()
                    failed += 1
                    continue
                successful_targets = [
                    current_by_id[int(target["id"])]
                    for target in target_nodes
                    if str(target["code"]) in successful_codes
                ]
                successful_targets_valid = bool(successful_targets) and all(
                    bool(target.enabled)
                    and bool(target.accepting_new_clients)
                    and not bool(target.is_draining)
                    for target in successful_targets
                )
                if not successful_targets_valid:
                    session.rollback()
                    failed += 1
                    continue
                existing_node_ids = {
                    int(row.node_id)
                    for row in session.query(UserNode)
                    .filter(UserNode.tg_id == tg_id)
                    .all()
                }
                for target_node in successful_targets:
                    if int(target_node.id) in existing_node_ids:
                        continue
                    session.add(
                        UserNode(
                            tg_id=tg_id,
                            node_id=int(target_node.id),
                            client_uuid=client_uuid,
                            panel_email=panel_email,
                        )
                    )
                deleted = session.query(UserNode).filter(
                    UserNode.id == source_user_node_id,
                    UserNode.node_id == source_node_id,
                ).delete(synchronize_session=False)
                if deleted != 1:
                    session.rollback()
                    failed += 1
                    continue
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
            migrated += 1
    finally:
        await panel.close()

    return {
        "ok": failed == 0,
        "code": "resync_completed" if failed == 0 else "resync_partial",
        "count": selected_count,
        "changed": migrated,
        "failed": failed,
        "skipped": skipped,
    }


_TASK20_DB_ACTIONS = frozenset(
    {
        "plan.create",
        "plan.update",
        "plan.delete",
        "live_update.create",
        "live_update.update",
        "live_update.delete",
        "start_link.create",
        "start_link.update",
        "start_link.delete",
        "wheel_config.update",
        "network_rollout_config.update",
        "warp_material.replace",
        "promo_slots.update",
        "loyalty_config.update",
        "campaign.create",
        "campaign.update",
        "campaign.delete",
        "template.create",
        "template.update",
        "template.delete",
        "access_key.issue",
        "gift_code.create",
    }
)


def _execute_task20_admin_action_db(
    session,
    state,
    runtime: dict[str, Any],
    *,
    actor_tg_id: int,
    action: str,
) -> dict[str, Any]:
    now = _utcnow()

    if action in {"plan.create", "plan.update", "plan.delete"}:
        row = state.entity
        if action == "plan.delete":
            if row is None:
                raise ActionIntentError("target_not_found", status_code=404, message="План не найден.")
            code = str(row.code or "").strip().lower()
            session.delete(row)
            session.flush()
            return {"code": code, "deleted": True}
        if action == "plan.create":
            if row is not None:
                raise ActionIntentError("target_exists", status_code=409, message="План уже существует.")
            row = PlanCatalog(code=str(runtime["code"]), created_at=now)
            session.add(row)
        for field in (
            "label",
            "amount_rub",
            "amount_stars",
            "days",
            "device_limit",
            "node_policy",
            "badge",
            "is_active",
            "sort_order",
        ):
            if field in runtime:
                setattr(row, field, runtime[field])
        row.updated_at = now
        session.flush()
        return {"code": str(row.code or "").strip().lower()}

    if action in {"live_update.create", "live_update.update", "live_update.delete"}:
        row = state.entity
        if action == "live_update.delete":
            if row is None:
                raise ActionIntentError("target_not_found", status_code=404, message="Новость не найдена.")
            update_id = int(row.id)
            session.delete(row)
            session.flush()
            return {"id": update_id, "deleted": True}
        if action == "live_update.create":
            row = LiveUpdate(created_at=now, updated_at=now)
            session.add(row)
        for field in ("title", "summary", "is_active", "sort_order"):
            if field in runtime:
                setattr(row, field, runtime[field])
        if "link" in runtime and runtime["link"] is not None:
            row.link = str(runtime["link"])
        if "channel_username" in runtime:
            row.channel_username = runtime["channel_username"]
        if "post_id" in runtime:
            row.post_id = runtime["post_id"]
        if "published_at" in runtime:
            row.published_at = (
                datetime.fromisoformat(str(runtime["published_at"]))
                if runtime["published_at"]
                else None
            )
        row.link = _build_tg_post_link(
            channel_username=getattr(row, "channel_username", None),
            post_id=getattr(row, "post_id", None),
            fallback_link=str(getattr(row, "link", "") or "").strip(),
        )
        if not str(row.link or "").strip():
            raise ActionIntentError("invalid_payload", status_code=422, message="Нужна ссылка или Telegram post target.")
        row.updated_at = now
        session.flush()
        return {"id": int(row.id)}

    if action in {"start_link.create", "start_link.update", "start_link.delete"}:
        row = state.entity
        if action == "start_link.delete":
            if row is None:
                raise ActionIntentError("target_not_found", status_code=404, message="Start link не найден.")
            row.is_active = False
            row.updated_at = now
            session.flush()
            return {"id": int(row.id), "code": str(row.code or "").strip().lower(), "deleted": True}
        if action == "start_link.create":
            row = StartLink(code=str(runtime["code"]), created_at=now, updated_at=now)
            session.add(row)
        if "code" in runtime and str(runtime["code"]) != str(row.code or "").strip().lower():
            duplicate = session.query(StartLink.id).filter(
                func.lower(StartLink.code) == str(runtime["code"]),
                StartLink.id != int(row.id),
            ).first()
            if duplicate:
                raise ActionIntentError("target_exists", status_code=409, message="Start link уже существует.")
            row.code = str(runtime["code"])
        for field in ("description", "target_action", "is_active"):
            if field in runtime:
                setattr(row, field, runtime[field])
        row.updated_at = now
        session.flush()
        return {"id": int(row.id), "code": str(row.code or "").strip().lower()}

    if action == "wheel_config.update":
        try:
            config = parse_paid_weekly_config(runtime, explicit=True)
        except InvalidWheelConfig:
            raise ActionIntentError(
                "wheel_config_invalid",
                status_code=400,
                message="wheel_config_invalid",
            ) from None
        normalized = {
            "preset": config.preset,
            "weights": [
                (
                    {"days": int(outcome.value), "weight": int(outcome.weight)}
                    if config.preset == "paid_weekly_v1"
                    else {
                        "kind": outcome.kind,
                        "value": int(outcome.value),
                        "weight": int(outcome.weight),
                    }
                )
                for outcome in config.outcomes
            ],
            "cooldown_hours": int(config.cooldown_hours),
        }
        _set_app_setting_json(s=session, key="wheel_config", value=normalized)
        session.flush()
        return {"wheel_config": normalized}

    if action == "network_rollout_config.update":
        normalized = normalized_network_rollout_config(runtime)
        _set_app_setting_json(s=session, key=NETWORK_ROLLOUT_CONFIG_KEY, value=normalized)
        session.flush()
        return {"network_rollout_config": normalized}

    if action == "promo_slots.update":
        normalized = _normalized_promo_slots_config(runtime, strict=True)
        _set_app_setting_json(
            s=session,
            key=PROMO_SLOTS_CONFIG_KEY,
            value={"assignments": normalized.get("assignments") or []},
        )
        session.flush()
        return {"promo_slots": normalized}

    if action == "loyalty_config.update":
        normalized = _normalized_loyalty_config(runtime)
        _set_app_setting_json(s=session, key="loyalty_config", value=normalized)
        session.flush()
        return {"loyalty_config": normalized}

    if action == "warp_material.replace":
        user = state.entity
        install_id = str(runtime.get("install_id") or getattr(user, "app_install_id", "") or "").strip() or None
        limit, window_seconds = _warp_material_provision_limit()
        if limit and _warp_event_count(
            session,
            user=user,
            install_id=install_id,
            event_name="material_provisioned",
            window_seconds=window_seconds,
        ) >= limit:
            raise ActionIntentError(
                "warp_material_rate_limited",
                status_code=429,
                message="Лимит замены WARP material исчерпан.",
            )
        try:
            row = provision_warp_material(
                session,
                user=user,
                install_id=install_id,
                wireguard_config=dict(runtime["wireguard_config"]),
                account=dict(runtime.get("account") or {}),
                source=str(runtime["source"]),
                mode=str(runtime["mode"]),
            )
            session.flush()
            policy = public_warp_policy_for_user(
                session,
                user=user,
                install_id=install_id,
                rollout_config=load_network_rollout_config(session=session),
            )
            record_warp_event(
                session,
                user=user,
                install_id=install_id,
                policy=policy,
                event_name="material_provisioned",
                state="ready_to_consent",
                reason_code="admin_provisioned",
                consented=False,
                meta={"source": "admin", "actor_tg_id": int(actor_tg_id), "material_id": int(row.id or 0)},
            )
            session.flush()
        except ValueError:
            raise ActionIntentError("invalid_warp_material", status_code=422, message="WARP material не прошёл проверку.") from None
        except RuntimeError:
            raise ActionIntentError("warp_material_store_unavailable", status_code=503, message="Хранилище WARP material недоступно.") from None
        material = warp_material_public_payload(row, policy=policy)
        status = build_warp_status(session, user=user, install_id=install_id, policy=policy)
        return {"material": material, "warp_status": status}

    if action in {"campaign.create", "campaign.update", "campaign.delete"}:
        row = state.entity
        if action == "campaign.delete":
            if row is None:
                raise ActionIntentError("target_not_found", status_code=404, message="Кампания не найдена.")
            row.is_active = False
            row.updated_at = now
            session.flush()
            return {"id": int(row.id), "deleted": True}
        if action == "campaign.create":
            row = IncentiveCampaign(
                campaign_type=str(runtime["campaign_type"]),
                target_value=str(runtime["target_value"]),
                activations_count=0,
                created_by=int(actor_tg_id),
                created_at=now,
                updated_at=now,
            )
            session.add(row)
        for field in ("name", "segment", "max_activations", "auto_disable", "is_active"):
            if field in runtime:
                setattr(row, field, runtime[field])
        for field in ("starts_at", "ends_at"):
            if field in runtime:
                setattr(row, field, datetime.fromisoformat(str(runtime[field])) if runtime[field] else None)
        if row.starts_at and row.ends_at and row.starts_at > row.ends_at:
            raise ActionIntentError("invalid_payload", status_code=422, message="starts_at должен быть не позже ends_at.")
        if "metadata" in runtime:
            row.metadata_json = json.dumps(runtime["metadata"], ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        row.updated_at = now
        session.flush()
        return {"id": int(row.id)}

    if action in {"template.create", "template.update", "template.delete"}:
        row = state.entity
        if action == "template.delete":
            if row is None:
                raise ActionIntentError("target_not_found", status_code=404, message="Шаблон не найден.")
            key = str(row.key or "").strip().lower()
            session.delete(row)
            session.flush()
            return {"key": key, "deleted": True}
        if action == "template.create":
            row = Template(key=str(runtime["key"]), text=str(runtime["text"]), created_at=now)
            session.add(row)
        new_key = runtime.get("new_key")
        if new_key and str(new_key) != str(row.key or "").strip().lower():
            duplicate = session.query(Template.id).filter(
                func.lower(Template.key) == str(new_key),
                Template.id != int(row.id),
            ).first()
            if duplicate:
                raise ActionIntentError("target_exists", status_code=409, message="Ключ шаблона уже существует.")
            row.key = str(new_key)
        if "text" in runtime:
            row.text = str(runtime["text"])
        session.flush()
        return {"key": str(row.key or "").strip().lower()}

    if action == "access_key.issue":
        plan_code = str(runtime["plan_code"])
        plan = _resolve_plan_config(s=session, code=plan_code)
        normalized_plan = _normalized_plan_payload(plan, fallback_code=plan_code)
        if not normalized_plan:
            raise ActionIntentError("invalid_payload", status_code=422, message="plan_code не поддерживается.")
        issued: list[dict[str, Any]] = []
        issued_rows: list[GiftCard] = []
        for _ in range(int(runtime["quantity"])):
            code = _generate_gift_code_for_admin(session)
            row = GiftCard(
                code=code,
                card_type=normalized_plan["code"],
                created_by=int(actor_tg_id),
                created_at=now,
            )
            session.add(row)
            issued_rows.append(row)
            issued.append({"key": code, "plan": normalized_plan, "issued_at": _safe_iso(now)})
        session.flush()
        return {
            "plan": normalized_plan,
            "issued": issued,
            "_issued_card_ids": [int(row.id) for row in issued_rows],
        }

    if action == "gift_code.create":
        card_type = str(runtime["card_type"])
        card = GIFT_CARD_TYPES.get(card_type)
        if not card:
            raise ActionIntentError("invalid_payload", status_code=422, message="card_type не поддерживается.")
        code = _generate_gift_code_for_admin(session)
        row = GiftCard(
            code=code,
            card_type=card_type,
            created_by=int(actor_tg_id),
            created_at=now,
        )
        session.add(row)
        session.flush()
        return {
            "_issued_card_ids": [int(row.id)],
            "gift_code": {
                "code": code,
                "card_type": card_type,
                "days": int(card.get("days", 0)),
                "stars": int(card.get("stars", 0)),
            }
        }

    raise ActionIntentError("executor_unavailable", status_code=503, message="DB-исполнитель действия недоступен.")


def _execute_admin_client_action_db(
    session,
    state,
    payload: dict[str, Any],
    _runtime_payload: dict[str, Any],
    *,
    actor_tg_id: int,
    action: str,
) -> dict[str, Any]:
    if action in _TASK20_DB_ACTIONS:
        return _execute_task20_admin_action_db(
            session,
            state,
            dict(_runtime_payload),
            actor_tg_id=actor_tg_id,
            action=action,
        )

    if action == "payment.reconcile":
        order = state.entity
        next_status = str(state.context["to_status"])
        operator_note = str(_runtime_payload["note"])
        order_meta = _json_obj(order.meta_json)
        existing = order_meta.get("admin_reconciliations")
        reconciliations = [
            item
            for item in (existing[-49:] if isinstance(existing, list) else [])
            if isinstance(item, dict)
        ]
        reconciliations.append(
            {
                "at": _safe_iso(_utcnow()),
                "actor_tg_id": int(actor_tg_id),
                "from_status": str(state.context["from_status"]),
                "to_status": next_status,
                "note": operator_note,
            }
        )
        order_meta["admin_reconciliations"] = reconciliations
        order.meta_json = json.dumps(order_meta, ensure_ascii=False, separators=(",", ":"))
        order.status = next_status
        if next_status == "paid" and not order.paid_at:
            order.paid_at = _utcnow()
        session.flush()
        return {
            "order_db_id": int(order.id),
            "provider": str(order.provider or ""),
            "order_id": str(order.order_id or ""),
            "order_status": str(order.status or ""),
        }

    if action in {"promo.create", "promo.update", "promo.delete"}:
        promo = state.entity
        if action == "promo.delete":
            if promo is None:
                raise ActionIntentError(
                    "target_not_found",
                    status_code=404,
                    message="Промокод не найден.",
                )
            deleted_code = str(promo.code or "").upper()
            session.delete(promo)
            session.flush()
            return {"code": deleted_code, "deleted": True}

        after = dict(state.context["after_snapshot"])
        if action == "promo.create":
            if promo is not None:
                raise ActionIntentError(
                    "target_exists",
                    status_code=409,
                    message="Промокод уже существует.",
                )
            promo = PromoCode(created_at=_utcnow())
            session.add(promo)
        promo.code = str(after["promo_code"])
        promo.promo_type = str(after["promo_type"])
        promo.value = int(after["value"])
        promo.uses_left = int(after["uses_left"])
        promo.expires_at = (
            datetime.fromisoformat(str(after["expires_at"]))
            if after.get("expires_at")
            else None
        )
        session.flush()
        return {"code": str(promo.code or "").upper(), "deleted": False}

    if action == "referral.process":
        now = _utcnow()
        processed = 0
        rewarded = 0
        waiting = 0
        rejected = 0
        queue_ids: list[int] = []
        for row in list(state.entity):
            processed += 1
            queue_ids.append(int(row.id))
            referred = session.query(User).filter(User.tg_id == int(row.referred_tg_id)).first()
            referrer = session.query(User).filter(User.tg_id == int(row.referrer_tg_id)).first()
            if referred is None or referrer is None:
                row.status = "rejected_missing_user"
                row.processed_at = now
                rejected += 1
                continue
            has_activity = (
                session.query(Event.id)
                .filter(
                    Event.tg_id == int(referred.tg_id),
                    Event.created_at >= (row.queued_at or (now - timedelta(days=1))),
                    Event.event_name.in_(["connected_ok", "clicked_connect"]),
                )
                .first()
                is not None
            )
            age_hours = max(
                0,
                int((now - (row.queued_at or now)).total_seconds() // 3600),
            )
            if not has_activity and not bool(payload["force_without_activity"]):
                if age_hours >= int(REFERRAL_ANTIFRAUD_MAX_WAIT_HOURS):
                    row.status = "rejected_no_activity"
                    row.processed_at = now
                    rejected += 1
                else:
                    row.ready_at = now + timedelta(hours=6)
                    waiting += 1
                continue
            ref_sub = str(referrer.sub_type or "").upper().strip()
            ref_expiry = referrer.expiry_at if referrer.expiry_at and referrer.expiry_at > now else None
            if not (bool(referrer.is_active) and ref_sub == "PAID" and ref_expiry):
                row.status = "rejected_referrer_inactive"
                row.processed_at = now
                rejected += 1
                continue
            row_meta = _json_obj(getattr(row, "meta", None))
            if not bool(row_meta.get("counted")):
                referrer.referral_count = int(referrer.referral_count or 0) + 1
            referrer.expiry_at = ref_expiry + timedelta(days=max(1, int(REFERRAL_BONUS_DAYS)))
            referrer.is_active = True
            row.status = "rewarded"
            row.processed_at = now
            rewarded += 1
        session.flush()
        return {
            "processed": processed,
            "rewarded": rewarded,
            "waiting": waiting,
            "rejected": rejected,
            "queue_ids": queue_ids,
        }

    if action in {"provider_quota.create", "provider_quota.update"}:
        node_code = str(state.context["node_code"])
        row = state.entity
        before = _provider_quota_audit_payload(row)
        now = _utcnow()
        if action == "provider_quota.create":
            if row is not None:
                raise ActionIntentError(
                    "target_exists",
                    status_code=409,
                    message="Квота провайдера для этой ноды уже настроена.",
                )
            row = ProviderTrafficQuota(node_code=node_code, created_at=now)
            session.add(row)
            quota_action = "create"
        else:
            if row is None:
                raise ActionIntentError(
                    "target_not_found",
                    status_code=404,
                    message="Квота провайдера не найдена.",
                )
            quota_action = "update"
        proposed = dict(state.context.get("proposed_config") or {})
        row.included_bytes = int(proposed["included_bytes"])
        row.reset_day = int(proposed["reset_day"])
        row.timezone = str(proposed["timezone"])
        row.warning_ratio = float(proposed["warning_ratio"])
        row.critical_ratio = float(proposed["critical_ratio"])
        row.enabled = bool(proposed["enabled"])
        row.notes = proposed.get("notes")
        row.updated_by = int(actor_tg_id)
        row.updated_at = now
        session.flush()
        after = _provider_quota_safe_payload(row)
        assert after is not None
        _add_provider_quota_audit(
            s=session,
            quota=row,
            node_code=node_code,
            actor=actor_tg_id,
            action=quota_action,
            before=before,
            after=after,
        )
        return {"quota": after, "node_code": node_code}

    if action == "provider_quota.delete":
        row = state.entity
        node_code = str(state.context["node_code"])
        if row is None:
            raise ActionIntentError(
                "target_not_found",
                status_code=404,
                message="Квота провайдера не найдена.",
            )
        before = _provider_quota_audit_payload(row)
        _add_provider_quota_audit(
            s=session,
            quota=row,
            node_code=node_code,
            actor=actor_tg_id,
            action="delete",
            before=before,
            after=None,
        )
        session.delete(row)
        session.flush()
        return {"node_code": node_code, "deleted": True}

    if action == "user.extend":
        user = state.entity
        now = _utcnow()
        current = user.expiry_at if user.expiry_at and user.expiry_at > now else now
        candidate = current + timedelta(days=int(payload["delta_days"]))
        if candidate <= now:
            if not bool(payload["allow_deactivate"]):
                raise ActionIntentError(
                    "would_deactivate",
                    status_code=409,
                    message="Операция деактивирует пользователя; подтвердите allow_deactivate=true.",
                )
            user.expiry_at = now
            user.is_active = False
        else:
            user.expiry_at = candidate
            user.is_active = True
        session.flush()
        return {
            "expiry_at": _safe_iso(user.expiry_at),
            "is_active": bool(user.is_active),
            "delta_days": int(payload["delta_days"]),
        }

    if action == "user.key_limits":
        tg_id = int(state.context["tg_id"])
        node = str(payload["node_code"])
        row = (
            session.query(UserKeyPolicy)
            .filter(
                UserKeyPolicy.tg_id == tg_id,
                func.lower(UserKeyPolicy.node_code) == node,
            )
            .first()
        )
        if row is None:
            row = UserKeyPolicy(tg_id=tg_id, node_code=node)
            session.add(row)
        row.burst_mbps = payload["burst_mbps"]
        row.soft_cap_gb = payload["soft_cap_gb"]
        row.hard_cap_gb = payload["hard_cap_gb"]
        row.notify_soft = bool(payload["notify_soft"])
        row.notify_hard = bool(payload["notify_hard"])
        row.auto_disable_on_hard = bool(payload["auto_disable_on_hard"])
        row.updated_by = int(actor_tg_id)
        row.updated_at = _utcnow()
        session.flush()
        row_payload = _serialize_key_policy(row)
        session.add(
            KeyActionHistory(
                tg_id=tg_id,
                node_code=node,
                action="key_limits_update",
                actor_tg_id=int(actor_tg_id),
                source="admin",
                meta=json.dumps(
                    {"policy": row_payload, "apply_now": False, "applied": None},
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                created_at=_utcnow(),
            )
        )
        return {"policy": row_payload, "applied": None}

    if action == "user.preset_run" and payload["preset"] == "extend_1d":
        user = state.entity
        now = _utcnow()
        base = user.expiry_at if user.expiry_at and user.expiry_at > now else now
        user.expiry_at = base + timedelta(days=1)
        user.is_active = True
        session.flush()
        return {
            "preset": "extend_1d",
            "expiry_at": _safe_iso(user.expiry_at),
        }

    if action == "user.bulk_key_action" and bool(payload["dry_run"]):
        return {
            "action": str(payload["action"]),
            "dry_run": True,
            "users": int(state.context["selected_count"]),
            "selection_hash": str(state.context["selection_hash"]),
            "preview_tg_ids": [
                int(value)
                for value in list(state.context["selected_tg_ids"])[:50]
            ],
        }

    if action == "key.rotate":
        key_row = state.entity
        if bool(payload["dry_run"]):
            return {
                "dry_run": True,
                "key_id": int(key_row.id),
                "tg_id": int(key_row.tg_id),
                "node_code": str(key_row.node_code or "") or None,
                "planned_job_type": "rotate_access_key",
            }
        key_row.state = "rotation_requested"
        key_row.updated_at = _utcnow()
        job = NodeProvisioningJob(
            tg_id=int(key_row.tg_id),
            key_id=int(key_row.id),
            node_code=str(key_row.node_code or "") or None,
            job_type="rotate_access_key",
            status="queued",
            desired_state_json=json.dumps(
                {
                    "reason_sha256": str(payload["reason"]["sha256"]),
                    "reason_length": int(payload["reason"]["length"]),
                    "requested_by": int(actor_tg_id),
                    "pool_code": str(key_row.pool_code or ""),
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            created_at=_utcnow(),
            updated_at=_utcnow(),
        )
        session.add(job)
        session.flush()
        return {
            "key_id": int(key_row.id),
            "job_id": int(job.id),
            "job_status": "queued",
        }

    if action == "ticket.status":
        ticket = state.entity
        new_status = str(payload["status"])
        set_ticket_status(
            session,
            ticket=ticket,
            status=new_status,
            assigned_admin_tg_id=(
                int(actor_tg_id) if new_status == STATUS_IN_PROGRESS else None
            ),
        )
        session.flush()
        return {"ticket_id": int(ticket.id)}

    raise ActionIntentError(
        "executor_unavailable",
        status_code=503,
        message="DB-исполнитель действия недоступен.",
    )


async def _execute_admin_client_action_external(
    context: dict[str, Any],
) -> dict[str, Any]:
    action = str(context["action"])
    actor = int(context["actor_tg_id"])
    runtime = dict(context.get("runtime_payload") or {})
    execution = dict(context.get("execution") or {})

    if action == "user.manual_create":
        tg_id = int(execution["candidate_tg_id"])
        session = SessionLocal()
        try:
            if session.query(User).filter(User.tg_id == tg_id).first() is not None:
                return {"ok": False, "code": "manual_id_conflict", "tg_id": tg_id}
            now = _utcnow()
            user = User(
                tg_id=tg_id,
                username=None,
                uuid=str(uuid.uuid4()),
                email=f"MANUAL_{abs(tg_id)}",
                sub_type="MANUAL",
                current_plan_code="manual",
                created_at=now,
                expiry_at=now + timedelta(days=int(runtime["days"])),
                is_active=True,
                stars_paid=0,
                total_gb=0,
                trial_used=False,
                tos_accepted=True,
                first_purchase_done=True,
                sub_token=_generate_sub_token(),
                is_manual=True,
                created_by_admin=actor,
                display_name=str(runtime["display_name"]),
            )
            session.add(user)
            ensure_user_account_foundation(session, user, now=now)
            session.commit()
            session.refresh(user)
            user_uuid = str(user.uuid or "")
            email = str(user.email or "")
            sub_token = str(user.sub_token or "")
        except IntegrityError:
            session.rollback()
            return {"ok": False, "code": "manual_id_conflict", "tg_id": tg_id}
        finally:
            session.close()
        panel = ControlPanel()
        try:
            await panel.login()
            synced = await panel.ensure_user_on_all_nodes(
                tg_id=tg_id,
                client_uuid=user_uuid,
                email=email,
                sub_id=sub_token or str(tg_id),
                enable=True,
                only_node_codes=None,
            )
            sync_ok = bool(any(synced.values())) if synced else False
        finally:
            await panel.close()
        _key_history_log(
            tg_id=tg_id,
            action="manual_create",
            actor_tg_id=actor,
            meta={"days": int(runtime["days"]), "sync_ok": sync_ok},
        )
        return {
            "ok": True,
            "code": "manual_created",
            "tg_id": tg_id,
            "sync_ok": sync_ok,
        }

    if action == "user.block":
        tg_id = int(execution["tg_id"])
        active = not bool(runtime["blocked"])
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()
            if user is None:
                return {"ok": False, "code": "user_not_found", "tg_id": tg_id}
            user.is_active = active
            user_uuid = str(user.uuid or "")
            session.commit()
        finally:
            session.close()
        panel = ControlPanel()
        try:
            await panel.login()
            await panel.enable_client(user_uuid, enable=active)
        finally:
            await panel.close()
        _key_history_log(
            tg_id=tg_id,
            action="manual_block" if runtime["blocked"] else "manual_unblock",
            actor_tg_id=actor,
            meta={"blocked": bool(runtime["blocked"])},
        )
        return {
            "ok": True,
            "code": "user_block_updated",
            "tg_id": tg_id,
            "is_active": active,
        }

    if action == "user.regenerate_token":
        tg_id = int(execution["tg_id"])
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()
            if user is None:
                return {"ok": False, "code": "user_not_found", "tg_id": tg_id}
            user.sub_token = _generate_sub_token()
            user_uuid = str(user.uuid or "")
            active = bool(user.is_active)
            session.commit()
        finally:
            session.close()
        _process_referral_bonus_queue(limit=100, force_without_activity=False)
        sync_ok = False
        if user_uuid:
            panel = ControlPanel()
            try:
                await panel.login()
                sync_ok = bool(await panel.enable_client(user_uuid, enable=active))
            finally:
                await panel.close()
        _key_history_log(
            tg_id=tg_id,
            action="token_regenerate",
            actor_tg_id=actor,
            meta={"sync_ok": sync_ok},
        )
        return {
            "ok": True,
            "code": "token_regenerated",
            "tg_id": tg_id,
            "sync_ok": sync_ok,
        }

    if action in {"user.safe_delete", "user.delete_test"}:
        tg_id = int(execution["tg_id"])
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()
            if user is None:
                return {"ok": False, "code": "user_not_found", "tg_id": tg_id}
            if not _is_manual_test_user(user):
                return {"ok": False, "code": "user_not_deletable", "tg_id": tg_id}
            session.query(UserNode).filter(UserNode.tg_id == tg_id).delete(
                synchronize_session=False
            )
            session.query(UserKeyPolicy).filter(UserKeyPolicy.tg_id == tg_id).delete(
                synchronize_session=False
            )
            session.query(KeyActionHistory).filter(KeyActionHistory.tg_id == tg_id).delete(
                synchronize_session=False
            )
            session.query(Event).filter(Event.tg_id == tg_id).delete(
                synchronize_session=False
            )
            session.delete(user)
            session.commit()
        finally:
            session.close()
        panel_deleted = False
        panel = ControlPanel()
        try:
            await panel.login()
            panel_deleted = bool(await panel.delete_client(tg_id))
        except Exception as exc:
            logger.warning(
                "admin guarded delete panel cleanup failed tg_id=%s error_type=%s intent_id=%s",
                tg_id,
                type(exc).__name__,
                str(context.get("action_intent_id") or ""),
            )
        finally:
            await panel.close()
        return {
            "ok": True,
            "code": "user_deleted",
            "tg_id": tg_id,
            "panel_deleted": panel_deleted,
        }

    if action in {
        "user.key_toggle",
        "user.key_reset_traffic",
        "user.key_resync_subid",
    }:
        tg_id = int(execution["tg_id"])
        node_code = str(runtime["node_code"])
        hard_cap = dict(execution.get("hard_caps") or {}).get(node_code)
        sub_id = str(execution.get("sub_token") or tg_id)
        panel = ControlPanel()
        try:
            await panel.login()
            if action == "user.key_toggle":
                changed = await panel.set_user_key_enabled_on_node(
                    tg_id=tg_id,
                    node_code=node_code,
                    enable=bool(runtime["enable"]),
                    sub_id=sub_id,
                    hard_cap_gb=hard_cap,
                )
            elif action == "user.key_reset_traffic":
                changed = await panel.reset_user_key_traffic_on_node(
                    tg_id=tg_id,
                    node_code=node_code,
                )
            else:
                changed = await panel.resync_user_key_subid_on_node(
                    tg_id=tg_id,
                    node_code=node_code,
                    sub_id=sub_id,
                    hard_cap_gb=hard_cap,
                )
        finally:
            await panel.close()
        if changed is None:
            return {
                "ok": False,
                "code": "key_not_found",
                "tg_id": tg_id,
                "node_code": node_code,
            }
        if not changed:
            return {
                "ok": False,
                "code": "panel_update_failed",
                "tg_id": tg_id,
                "node_code": node_code,
            }
        history_action = {
            "user.key_toggle": "key_enable" if runtime["enable"] else "key_disable",
            "user.key_reset_traffic": "key_reset_traffic",
            "user.key_resync_subid": "key_resync_subid",
        }[action]
        _key_history_log(
            tg_id=tg_id,
            action=history_action,
            node_code=node_code,
            actor_tg_id=actor,
            meta=(
                {"enabled": bool(runtime["enable"])}
                if action == "user.key_toggle"
                else None
            ),
        )
        result: dict[str, Any] = {
            "ok": True,
            "code": "key_updated",
            "tg_id": tg_id,
            "node_code": node_code,
        }
        if action == "user.key_toggle":
            result["enabled"] = bool(runtime["enable"])
        return result

    if action == "user.key_limits":
        tg_id = int(execution["tg_id"])
        node_code = str(runtime["node_code"])
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()
            if user is None:
                return {"ok": False, "code": "user_not_found", "tg_id": tg_id}
            row = (
                session.query(UserKeyPolicy)
                .filter(
                    UserKeyPolicy.tg_id == tg_id,
                    func.lower(UserKeyPolicy.node_code) == node_code,
                )
                .first()
            )
            if row is None:
                row = UserKeyPolicy(tg_id=tg_id, node_code=node_code)
                session.add(row)
            row.burst_mbps = runtime["burst_mbps"]
            row.soft_cap_gb = runtime["soft_cap_gb"]
            row.hard_cap_gb = runtime["hard_cap_gb"]
            row.notify_soft = bool(runtime["notify_soft"])
            row.notify_hard = bool(runtime["notify_hard"])
            row.auto_disable_on_hard = bool(runtime["auto_disable_on_hard"])
            row.updated_by = actor
            row.updated_at = _utcnow()
            sub_id = str(user.sub_token or user.tg_id)
            row_payload = _serialize_key_policy(row)
            session.commit()
        finally:
            session.close()
        panel = ControlPanel()
        try:
            await panel.login()
            applied = await panel.apply_user_key_limits_on_node(
                tg_id=tg_id,
                node_code=node_code,
                hard_cap_gb=runtime["hard_cap_gb"],
                sub_id=sub_id,
            )
        finally:
            await panel.close()
        _key_history_log(
            tg_id=tg_id,
            action="key_limits_update",
            node_code=node_code,
            actor_tg_id=actor,
            meta={"policy": row_payload, "apply_now": True, "applied": applied},
        )
        return {
            "ok": True,
            "code": "key_limits_updated",
            "tg_id": tg_id,
            "node_code": node_code,
            "applied": applied,
        }

    if action == "user.loyalty_grant":
        tg_id = int(execution["tg_id"])
        tier_days = int(runtime["tier_days"])
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()
            if user is None:
                return {"ok": False, "code": "user_not_found", "tg_id": tg_id}
            loyalty = _user_loyalty_snapshot(s=session, user=user)
            tier = next(
                (
                    row
                    for row in loyalty.get("tiers", [])
                    if int(row.get("days") or 0) == tier_days
                ),
                None,
            )
            if tier is None:
                return {"ok": False, "code": "tier_not_found", "tg_id": tg_id}
            if not bool(tier.get("unlocked")):
                return {"ok": False, "code": "tier_locked", "tg_id": tg_id}
            if bool(tier.get("claimed")):
                return {"ok": False, "code": "tier_claimed", "tg_id": tg_id}
            now = _utcnow()
            base = user.expiry_at if user.expiry_at and user.expiry_at > now else now
            user.expiry_at = base + timedelta(days=max(1, int(tier.get("bonus_days") or 0)))
            user.is_active = True
            session.add(
                RewardClaim(
                    tg_id=tg_id,
                    reward_key=str(tier.get("reward_key") or ""),
                    meta=json.dumps({"tier": tier_days}, ensure_ascii=False),
                )
            )
            session.commit()
            try:
                sync_ok = bool(await _sync_user_after_paid_bonus(user))
            except Exception as exc:
                logger.warning(
                    "loyalty grant sync failed tg_id=%s error_type=%s intent_id=%s",
                    tg_id,
                    type(exc).__name__,
                    str(context.get("action_intent_id") or ""),
                )
                sync_ok = False
        except IntegrityError:
            session.rollback()
            return {"ok": False, "code": "tier_claimed", "tg_id": tg_id}
        finally:
            session.close()
        return {
            "ok": True,
            "code": "loyalty_granted",
            "tg_id": tg_id,
            "tier_days": tier_days,
            "sync_ok": sync_ok,
        }

    if action == "user.preset_run":
        tg_id = int(execution["tg_id"])
        preset = str(runtime["preset"])
        if preset == "send_guide":
            ok = await _telegram_send_message(
                tg_id,
                "Инструкция по подключению:\n"
                "1) Откройте раздел Устройства.\n"
                "2) Импортируйте ключ.\n"
                "3) Проверьте статус и перезапустите приложение.",
            )
            return {
                "ok": bool(ok),
                "code": "guide_sent" if ok else "telegram_failed",
                "tg_id": tg_id,
                "preset": preset,
            }
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()
            if user is None:
                return {"ok": False, "code": "user_not_found", "tg_id": tg_id}
            nodes = enabled_nodes(session)
        finally:
            session.close()
        keys_state = await _admin_user_keys_state(user, nodes=nodes)
        keys = [row for row in keys_state.get("keys", []) if bool(row.get("exists"))]
        expected_sub_id = str(user.sub_token or user.tg_id)
        changed = 0
        failed = 0
        panel = ControlPanel()
        try:
            await panel.login()
            if preset == "reset_key":
                for key in keys:
                    code = str(key.get("node_code") or "")
                    ok = await panel.reset_user_key_traffic_on_node(
                        tg_id=tg_id,
                        node_code=code,
                    )
                    if ok:
                        changed += 1
                        _key_history_log(
                            tg_id=tg_id,
                            action="key_reset_traffic",
                            node_code=code,
                            actor_tg_id=actor,
                            source="preset",
                        )
                    else:
                        failed += 1
            elif preset == "rotate_link":
                rotate_session = SessionLocal()
                try:
                    db_user = rotate_session.query(User).filter(User.tg_id == tg_id).first()
                    if db_user is None:
                        return {"ok": False, "code": "user_not_found", "tg_id": tg_id}
                    db_user.sub_token = _generate_sub_token()
                    rotate_session.commit()
                    expected_sub_id = str(db_user.sub_token or db_user.tg_id)
                finally:
                    rotate_session.close()
                for key in keys:
                    code = str(key.get("node_code") or "")
                    cap_session = SessionLocal()
                    try:
                        hard_cap = _get_user_node_hard_cap_gb(
                            s=cap_session,
                            tg_id=tg_id,
                            node_code=code,
                        )
                    finally:
                        cap_session.close()
                    ok = await panel.resync_user_key_subid_on_node(
                        tg_id=tg_id,
                        node_code=code,
                        sub_id=expected_sub_id,
                        hard_cap_gb=hard_cap,
                    )
                    if ok:
                        changed += 1
                        _key_history_log(
                            tg_id=tg_id,
                            action="key_resync_subid",
                            node_code=code,
                            actor_tg_id=actor,
                            source="preset",
                        )
                    else:
                        failed += 1
                _key_history_log(
                    tg_id=tg_id,
                    action="token_regenerate",
                    actor_tg_id=actor,
                    source="preset",
                )
        finally:
            await panel.close()
        return {
            "ok": failed == 0,
            "code": "preset_completed" if failed == 0 else "preset_partial",
            "tg_id": tg_id,
            "preset": preset,
            "changed": changed,
            "failed": failed,
        }

    if action == "user.bulk_key_action":
        selected = [int(value) for value in execution["selected_tg_ids"]]
        bulk_action = str(execution["action"])
        if len(selected) > 50 and not bool(execution["force"]):
            return {
                "ok": False,
                "code": "force_required",
                "action": bulk_action,
                "users": len(selected),
                "requires_force": True,
            }
        panel = ControlPanel()
        changed = 0
        failed = 0
        details: list[dict[str, int]] = []
        try:
            await panel.login()
            for tg_id in selected:
                user_changed = 0
                user_failed = 0
                session = SessionLocal()
                try:
                    user = session.query(User).filter(User.tg_id == tg_id).first()
                    if user is None:
                        failed += 1
                        user_failed += 1
                        details.append(
                            {"tg_id": tg_id, "changed": 0, "failed": user_failed}
                        )
                        continue
                    sub_id = str(user.sub_token or user.tg_id)
                finally:
                    session.close()
                node_codes = list(execution["node_codes"])
                if not node_codes:
                    snapshots = await panel.get_user_key_snapshots(tg_id=tg_id)
                    node_codes = [
                        str(row.get("node_code") or "").strip().lower()
                        for row in snapshots
                        if str(row.get("node_code") or "").strip()
                    ]
                for node_code in node_codes:
                    cap_session = SessionLocal()
                    try:
                        hard_cap = _get_user_node_hard_cap_gb(
                            s=cap_session,
                            tg_id=tg_id,
                            node_code=node_code,
                        )
                    finally:
                        cap_session.close()
                    if bulk_action == "disable":
                        ok = await panel.set_user_key_enabled_on_node(
                            tg_id=tg_id,
                            node_code=node_code,
                            enable=False,
                            sub_id=sub_id,
                            hard_cap_gb=hard_cap,
                        )
                    elif bulk_action == "enable":
                        ok = await panel.set_user_key_enabled_on_node(
                            tg_id=tg_id,
                            node_code=node_code,
                            enable=True,
                            sub_id=sub_id,
                            hard_cap_gb=hard_cap,
                        )
                    elif bulk_action == "reset":
                        ok = await panel.reset_user_key_traffic_on_node(
                            tg_id=tg_id,
                            node_code=node_code,
                        )
                    else:
                        ok = await panel.resync_user_key_subid_on_node(
                            tg_id=tg_id,
                            node_code=node_code,
                            sub_id=sub_id,
                            hard_cap_gb=hard_cap,
                        )
                    if ok:
                        changed += 1
                        user_changed += 1
                        _key_history_log(
                            tg_id=tg_id,
                            action={
                                "disable": "key_disable",
                                "enable": "key_enable",
                                "reset": "key_reset_traffic",
                                "resync": "key_resync_subid",
                            }[bulk_action],
                            node_code=node_code,
                            actor_tg_id=actor,
                            source="bulk",
                        )
                    else:
                        failed += 1
                        user_failed += 1
                details.append(
                    {
                        "tg_id": tg_id,
                        "changed": user_changed,
                        "failed": user_failed,
                    }
                )
        finally:
            await panel.close()
        return {
            "ok": failed == 0,
            "code": "bulk_completed" if failed == 0 else "bulk_partial",
            "action": bulk_action,
            "users": len(selected),
            "changed": changed,
            "failed": failed,
            "details": details,
        }

    if action == "node.sync_global":
        selection = [dict(item) for item in execution["selection"]]
        if len(selection) != int(execution["selected_count"]):
            raise RuntimeError("frozen global sync selection is unavailable")
        panel = ControlPanel()
        changed = 0
        failed = 0
        try:
            await panel.login()
            for item in selection:
                ok = await panel.enable_client(str(item["uuid"]), True)
                if ok:
                    changed += 1
                else:
                    failed += 1
        finally:
            await panel.close()
        return {
            "ok": failed == 0,
            "code": "global_sync_completed" if failed == 0 else "global_sync_partial",
            "count": len(selection),
            "changed": changed,
            "failed": failed,
        }

    if action == "broadcast.send":
        recipients = [int(value) for value in execution["selected_tg_ids"]]
        if (
            recipients != sorted(set(recipients))
            or len(recipients) != int(execution["recipient_count"])
        ):
            raise RuntimeError("frozen broadcast plan is unavailable")
        sent = 0
        failed = 0
        for tg_id in recipients:
            if await _telegram_send_message(tg_id, str(runtime["text"])):
                sent += 1
            else:
                failed += 1
        return {
            "ok": failed == 0,
            "code": "broadcast_sent" if failed == 0 else "broadcast_partial",
            "attempted": len(recipients),
            "sent": sent,
            "failed": failed,
        }

    if action == "user.message":
        tg_id = int(execution["tg_id"])
        ok = await _telegram_send_message(tg_id, str(runtime["text"]))
        return {
            "ok": bool(ok),
            "code": "message_sent" if ok else "telegram_failed",
            "tg_id": tg_id,
        }

    if action == "ticket.reply":
        ticket_id = int(execution["ticket_id"])
        user_tg_id = int(execution["user_tg_id"])
        message_payload = TicketMessageIn(
            body=str(runtime["body"]),
            attachment_id=runtime.get("attachment_id"),
            media_type=runtime.get("media_type"),
            media_file_id=runtime.get("media_file_id"),
            media_payload=runtime.get("media_payload"),
        )
        reference = _support_attachment_reference(message_payload)
        with _support_attachment_bind_lock(reference):
            session = SessionLocal()
            try:
                account_id = resolve_support_account_id(session, user_tg_id=actor)
                ticket = get_ticket_by_id(session, ticket_id)
                if ticket is None:
                    return {"ok": False, "code": "ticket_not_found", "ticket_id": ticket_id}
                attachment, media = _resolve_ticket_attachment(
                    session,
                    payload=message_payload,
                    actor_tg_id=actor,
                    account_id=account_id,
                )
                message = add_ticket_message(
                    session,
                    ticket_id=ticket_id,
                    sender_tg_id=actor,
                    sender_role="admin",
                    body=message_payload.body,
                    **media,
                )
                if attachment is not None:
                    _bind_ticket_attachment(
                        session,
                        row=attachment,
                        ticket_id=ticket_id,
                        message_id=int(message.id),
                    )
                set_ticket_status(
                    session,
                    ticket=ticket,
                    status=STATUS_IN_PROGRESS,
                    assigned_admin_tg_id=actor,
                )
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        sent = await _telegram_send_message(
            user_tg_id,
            f"💬 Ответ оператора в обращении #{ticket_id}.",
        )
        return {
            "ok": bool(sent),
            "code": "ticket_replied" if sent else "telegram_failed",
            "ticket_id": ticket_id,
        }

    raise RuntimeError("guarded external executor is unavailable")


async def _execute_admin_post_commit(context: dict[str, Any]) -> dict[str, Any]:
    if str(context.get("action") or "") != "ticket.status":
        return {"ok": True, "code": "post_commit_not_required"}
    execution = dict(context.get("execution") or {})
    ticket_id = int(execution["ticket_id"])
    user_tg_id = int(execution["user_tg_id"])
    sent = await _telegram_send_message(
        user_tg_id,
        f"✅ Обращение #{ticket_id} закрыто оператором.",
    )
    return {"ok": bool(sent), "code": "ticket_close_notified" if sent else "telegram_failed"}


def _saved_bulk_preview_ids(value: object) -> list[int]:
    if not isinstance(value, list) or len(value) > 50:
        return []
    ids: list[int] = []
    for item in value:
        if type(item) is not int or not -(2**63) <= item < 2**63:
            return []
        ids.append(int(item))
    return ids if len(set(ids)) == len(ids) else []


def _saved_bulk_details(value: object) -> list[dict[str, int]]:
    if not isinstance(value, list) or len(value) > 500:
        return []
    details: list[dict[str, int]] = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"tg_id", "changed", "failed"}:
            return []
        tg_id = item["tg_id"]
        changed = item["changed"]
        failed = item["failed"]
        if (
            type(tg_id) is not int
            or not -(2**63) <= tg_id < 2**63
            or type(changed) is not int
            or type(failed) is not int
            or not 0 <= changed <= 1_000_000
            or not 0 <= failed <= 1_000_000
        ):
            return []
        details.append(
            {"tg_id": int(tg_id), "changed": int(changed), "failed": int(failed)}
        )
    return (
        details
        if len({item["tg_id"] for item in details}) == len(details)
        else []
    )


def _admin_guarded_action_response(
    *,
    action: str,
    target_id: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    known_status = str(result.get("status") or "")
    if known_status not in {"completed", "failed"}:
        return result
    if known_status == "failed" and (
        action,
        str(result.get("result_code") or ""),
    ) not in {
        ("user.preset_run", "preset_partial"),
        ("user.bulk_key_action", "bulk_partial"),
        ("user.bulk_key_action", "force_required"),
        ("ticket.reply", "telegram_failed"),
        ("broadcast.send", "broadcast_partial"),
        ("node.sync_global", "global_sync_partial"),
    }:
        return result
    facts = result.get("result") if isinstance(result.get("result"), dict) else {}
    metadata = {
        "status": result.get("status"),
        "action_intent_id": result.get("action_intent_id"),
        "audit_id": result.get("audit_id"),
    }

    def merged(legacy: dict[str, Any]) -> dict[str, Any]:
        merged_result = {**result, **legacy, **metadata}
        merged_result["ok"] = bool(
            known_status == "completed" and legacy.get("ok", True)
        )
        return merged_result

    if action == "payment.reconcile":
        session = SessionLocal()
        try:
            order = session.query(ExternalOrder).filter(ExternalOrder.id == int(target_id)).first()
            if order is None:
                return result
            return merged(
                {
                    "ok": True,
                    "order": _admin_payment_order_payload(s=session, order=order),
                }
            )
        finally:
            session.close()

    if action == "user.manual_create":
        tg_id = int(facts["tg_id"])
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()
            if user is None:
                return result
            return merged(
                {
                    "ok": True,
                    "user": {
                        "tg_id": tg_id,
                        "display_name": str(user.display_name or ""),
                        "sub_type": str(user.sub_type or ""),
                        "is_active": bool(user.is_active),
                        "expiry_at": _safe_iso(user.expiry_at),
                        "subscription_url": build_subscription_url(str(user.sub_token or "")),
                    },
                    "sync_ok": bool(facts.get("sync_ok")),
                }
            )
        finally:
            session.close()

    if action == "user.block":
        return merged({"ok": True, "is_active": bool(facts.get("is_active"))})

    if action == "user.regenerate_token":
        tg_id = int(facts["tg_id"])
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()
            if user is None:
                return result
            return merged(
                {
                    "ok": True,
                    "subscription_url": build_subscription_url(str(user.sub_token or "")),
                    "sync_ok": bool(facts.get("sync_ok")),
                }
            )
        finally:
            session.close()

    if action in {"user.safe_delete", "user.delete_test"}:
        return merged(
            {
                "ok": True,
                "tg_id": int(facts["tg_id"]),
                "panel_deleted": bool(facts.get("panel_deleted")),
            }
        )

    if action == "user.key_toggle":
        return merged(
            {
                "ok": True,
                "tg_id": int(facts["tg_id"]),
                "node_code": str(facts["node_code"]),
                "enabled": bool(facts.get("enabled")),
            }
        )

    if action == "user.key_reset_traffic":
        return merged(
            {
                "ok": True,
                "tg_id": int(facts["tg_id"]),
                "node_code": str(facts["node_code"]),
            }
        )

    if action == "user.key_resync_subid":
        tg_id = int(facts["tg_id"])
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()
            if user is None:
                return result
            return merged(
                {
                    "ok": True,
                    "tg_id": tg_id,
                    "node_code": str(facts["node_code"]),
                    "expected_sub_id": str(user.sub_token or user.tg_id),
                }
            )
        finally:
            session.close()

    if action == "user.key_limits":
        tg_id = int(facts.get("tg_id") or target_id)
        node_code = str(facts.get("node_code") or "")
        session = SessionLocal()
        try:
            row = (
                session.query(UserKeyPolicy)
                .filter(
                    UserKeyPolicy.tg_id == tg_id,
                    func.lower(UserKeyPolicy.node_code) == node_code,
                )
                .first()
            )
            if row is None:
                return result
            return merged(
                {
                    "ok": True,
                    "policy": _serialize_key_policy(row),
                    "applied": facts.get("applied"),
                }
            )
        finally:
            session.close()

    if action == "user.loyalty_grant":
        tg_id = int(facts["tg_id"])
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.tg_id == tg_id).first()
            if user is None:
                return result
            return merged(
                {
                    "ok": True,
                    "tier_days": int(facts["tier_days"]),
                    "expiry_at": _safe_iso(user.expiry_at),
                    "sync_ok": bool(facts.get("sync_ok")),
                }
            )
        finally:
            session.close()

    if action == "user.preset_run" and facts:
        preset = str(facts["preset"])
        legacy: dict[str, Any] = {"ok": True, "preset": preset}
        if preset in {"reset_key", "rotate_link"}:
            tg_id = int(facts["tg_id"])
            session = SessionLocal()
            try:
                user = session.query(User).filter(User.tg_id == tg_id).first()
                if user is not None:
                    legacy["subscription_url"] = build_subscription_url(
                        str(user.sub_token or user.tg_id)
                    )
            finally:
                session.close()
            legacy["changed"] = int(facts.get("changed") or 0)
            legacy["failed"] = int(facts.get("failed") or 0)
        return merged(legacy)

    if action == "user.bulk_key_action":
        if facts:
            requires_force = bool(facts.get("requires_force"))
            return merged(
                {
                    "ok": not requires_force,
                    "requires_force": requires_force or None,
                    "action": str(facts.get("action") or ""),
                    "users": int(facts.get("users") or 0),
                    "changed": int(facts.get("changed") or 0),
                    "failed": int(facts.get("failed") or 0),
                    "details": _saved_bulk_details(facts.get("details")),
                    **(
                        {"message": "Для массового действия более чем над 50 пользователями нужен force=true"}
                        if requires_force
                        else {}
                    ),
                }
            )
        return merged(
            {
                "ok": True,
                "action": str(result.get("action") or ""),
                "dry_run": True,
                "users": int(result.get("users") or 0),
                "preview_tg_ids": _saved_bulk_preview_ids(
                    result.get("preview_tg_ids")
                ),
            }
        )

    if action == "user.message":
        return merged({"ok": True})

    if action == "broadcast.send":
        return merged(
            {
                "attempted": int(facts.get("attempted") or 0),
                "sent": int(facts.get("sent") or 0),
                "failed": int(facts.get("failed") or 0),
            }
        )

    if action == "node.sync_global":
        return merged(
            {
                "synced": int(facts.get("changed") or 0),
                "failed": int(facts.get("failed") or 0),
                "count": int(facts.get("count") or 0),
            }
        )

    if action in {"ticket.reply", "ticket.status"}:
        ticket_id = int(facts.get("ticket_id") or result.get("ticket_id") or target_id)
        session = SessionLocal()
        try:
            ticket = get_ticket_by_id(session, ticket_id)
            if ticket is None:
                return result
            messages = list_ticket_messages(session, ticket_id, limit=100)
            return merged({"ticket": _ticket_detail_row(ticket, messages)})
        finally:
            session.close()

    return result


async def _execute_admin_guarded_action(
    *,
    actor_tg_id: int,
    action: str,
    target_type: str,
    target_id: str,
    payload: dict[str, Any],
    request: Request,
) -> dict[str, Any]:
    intent_id = str(request.headers.get("X-Admin-Intent-Id") or "")
    idempotency_key = str(request.headers.get("X-Admin-Idempotency-Key") or "")
    confirmation = str(request.headers.get("X-Admin-Confirmation-SHA256") or "")
    if not intent_id.strip():
        raise HTTPException(
            status_code=428,
            detail={
                "code": "intent_required",
                "message": "Сначала создайте защищённое намерение через серверный предпросмотр.",
            },
        )
    if not idempotency_key.strip():
        _raise_action_intent_header_required(
            actor_tg_id=actor_tg_id,
            intent_id=intent_id,
            code="idempotency_required",
            message="Нужен клиентский ключ идемпотентности.",
        )
    if not confirmation.strip():
        _raise_action_intent_header_required(
            actor_tg_id=actor_tg_id,
            intent_id=intent_id,
            code="confirmation_required",
            message="Нужно подтверждение серверной проверочной фразы.",
        )
    try:
        execution_result = await _execute_action_intent(
            session_factory=SessionLocal,
            actor_tg_id=actor_tg_id,
            intent_id=intent_id,
            idempotency_key=idempotency_key,
            confirmation_sha256_header=confirmation,
            action=action,
            target={"type": target_type, "id": target_id},
            payload=payload,
            audit_writer=_add_admin_audit,
            db_executor=lambda session, state, normalized, runtime: (
                _execute_admin_client_action_db(
                    session,
                    state,
                    dict(normalized),
                    dict(runtime),
                    actor_tg_id=actor_tg_id,
                    action=action,
                )
            ),
            external_executor=_execute_admin_client_action_external,
            post_commit_executor=_execute_admin_post_commit,
            external_timeout_seconds=(
                300.0
                if action in {"user.bulk_key_action", "user.preset_run"}
                else 30.0
            ),
            return_replay_state=True,
        )
    except ActionIntentError as error:
        if (
            action == "warp_material.replace"
            and error.code == "warp_material_rate_limited"
        ):
            event_session = SessionLocal()
            try:
                user = (
                    event_session.query(User)
                    .filter(User.tg_id == int(payload.get("tg_id") or 0))
                    .first()
                )
                if user is not None:
                    install_id = (
                        str(
                            payload.get("install_id")
                            or getattr(user, "app_install_id", "")
                            or ""
                        ).strip()
                        or None
                    )
                    policy = public_warp_policy_for_user(
                        event_session,
                        user=user,
                        install_id=install_id,
                        rollout_config=load_network_rollout_config(session=event_session),
                    )
                    record_warp_event(
                        event_session,
                        user=user,
                        install_id=install_id,
                        policy=policy,
                        event_name="material_provision_rate_limited",
                        state="rate_limited",
                        reason_code="provision_limit",
                        consented=False,
                        meta={"source": "admin", "actor_tg_id": int(actor_tg_id)},
                    )
                    event_session.commit()
            except Exception:
                event_session.rollback()
            finally:
                event_session.close()
        _raise_action_intent_http(error)
        raise AssertionError("unreachable")
    result, replayed = execution_result
    if replayed and action != "broadcast.send":
        return result
    return _admin_guarded_action_response(
        action=action,
        target_id=target_id,
        result=result,
    )


async def _execute_admin_node_action(
    *,
    actor_tg_id: int,
    action: str,
    node_code: str,
    payload: dict[str, Any],
    intent_id: str,
    idempotency_key: str,
    confirmation_sha256: str,
) -> dict[str, Any]:
    if not str(intent_id or "").strip():
        raise HTTPException(
            status_code=428,
            detail={
                "code": "intent_required",
                "message": "Сначала создайте защищённое намерение через серверный предпросмотр.",
            },
        )
    if not str(idempotency_key or "").strip():
        _raise_action_intent_header_required(
            actor_tg_id=actor_tg_id,
            intent_id=intent_id,
            code="idempotency_required",
            message="Нужен клиентский ключ идемпотентности.",
        )
    if not str(confirmation_sha256 or "").strip():
        _raise_action_intent_header_required(
            actor_tg_id=actor_tg_id,
            intent_id=intent_id,
            code="confirmation_required",
            message="Нужно подтверждение серверной проверочной фразы.",
        )
    try:
        return await _execute_action_intent(
            session_factory=SessionLocal,
            actor_tg_id=actor_tg_id,
            intent_id=intent_id,
            idempotency_key=idempotency_key,
            confirmation_sha256_header=confirmation_sha256,
            action=action,
            target={"type": "node", "id": node_code},
            payload=payload,
            audit_writer=_add_admin_audit,
            external_executor=(
                _execute_node_resync_external
                if action == "node.resync"
                else None
            ),
        )
    except ActionIntentError as error:
        _raise_action_intent_http(error)
        raise AssertionError("unreachable")


@app.post("/api/admin/action-intents")
async def admin_action_intent_prepare(
    payload: AdminActionIntentPrepareIn,
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    session = SessionLocal()
    try:
        result = _prepare_action_intent(
            session=session,
            actor_tg_id=actor,
            action=payload.action,
            target={"type": payload.target.type, "id": payload.target.id},
            payload=dict(payload.payload),
        )
        session.commit()
        return result
    except ActionIntentError as error:
        session.rollback()
        _raise_action_intent_http(error)
        raise AssertionError("unreachable")
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "code": "intent_prepare_failed",
                "message": "Не удалось подготовить действие.",
            },
        ) from None
    finally:
        session.close()


@app.get("/api/admin/action-intents/{intent_id}")
async def admin_action_intent_status(
    intent_id: str,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    session = SessionLocal()
    try:
        return _get_action_intent_status(
            session=session,
            actor_tg_id=actor,
            intent_id=intent_id,
        )
    except ActionIntentError as error:
        _raise_action_intent_http(error)
        raise AssertionError("unreachable")
    finally:
        session.close()


@app.post("/api/admin/nodes/{node_code}/disable")
async def admin_node_disable(
    node_code: str,
    payload: AdminNodeLifecycleIn,
    x_telegram_init_data: str = Header(default=""),
    x_admin_intent_id: str = Header(default="", alias="X-Admin-Intent-Id"),
    x_admin_idempotency_key: str = Header(
        default="",
        alias="X-Admin-Idempotency-Key",
    ),
    x_admin_confirmation_sha256: str = Header(
        default="",
        alias="X-Admin-Confirmation-SHA256",
    ),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    wanted = str(node_code or "").strip().lower()
    return await _execute_admin_node_action(
        actor_tg_id=actor,
        action="node.disable",
        node_code=wanted,
        payload={"force": bool(payload.force)},
        intent_id=x_admin_intent_id,
        idempotency_key=x_admin_idempotency_key,
        confirmation_sha256=x_admin_confirmation_sha256,
    )


@app.post("/api/admin/nodes/{node_code}/resync")
async def admin_node_resync(
    node_code: str,
    payload: AdminNodeResyncIn,
    x_telegram_init_data: str = Header(default=""),
    x_admin_intent_id: str = Header(default="", alias="X-Admin-Intent-Id"),
    x_admin_idempotency_key: str = Header(
        default="",
        alias="X-Admin-Idempotency-Key",
    ),
    x_admin_confirmation_sha256: str = Header(
        default="",
        alias="X-Admin-Confirmation-SHA256",
    ),
) -> dict:
    actor = int(_require_admin(x_telegram_init_data).get("id", 0))
    wanted = str(node_code or "").strip().lower()
    return await _execute_admin_node_action(
        actor_tg_id=actor,
        action="node.resync",
        node_code=wanted,
        payload={"limit": int(payload.limit), "dry_run": bool(payload.dry_run)},
        intent_id=x_admin_intent_id,
        idempotency_key=x_admin_idempotency_key,
        confirmation_sha256=x_admin_confirmation_sha256,
    )
