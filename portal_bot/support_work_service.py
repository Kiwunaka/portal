"""Server-owned Support Inbox and privacy-bounded User 360 projections."""

from __future__ import annotations

import hashlib
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Iterable

from sqlalchemy import String, and_, func, or_
from client_network_diagnostics import recent_network_context
from client_connectivity import project_connectivity

try:
    from .models import (
        Event,
        ObserverUserState,
        ServiceIncident,
        SupportBundleAccessAudit,
        SupportBundleUpload,
        SupportTicket,
        SupportTicketMessage,
        User,
    )
except ImportError:
    from models import (
        Event,
        ObserverUserState,
        ServiceIncident,
        SupportBundleAccessAudit,
        SupportBundleUpload,
        SupportTicket,
        SupportTicketMessage,
        User,
    )


TICKET_PRIORITIES = frozenset({"critical", "high", "normal", "low"})
TICKET_QUEUES = frozenset({"general", "billing", "connection", "account", "release"})
TICKET_WAITING_ON = frozenset({"customer", "operator", "engineering", "provider"})
SUPPORT_MACROS: tuple[dict[str, str], ...] = (
    {
        "code": "request_diagnostics",
        "title": "Запросить диагностику",
        "body": "Пришлите диагностический пакет из приложения и укажите примерное время последней неудачной попытки.",
    },
    {
        "code": "acknowledge_investigation",
        "title": "Подтвердить разбор",
        "body": "Обращение принято в работу. Проверяем доступные серверные сигналы и вернёмся с результатом.",
    },
    {
        "code": "request_retry",
        "title": "Попросить повторить",
        "body": "Повторите действие один раз и сообщите время попытки. Не присылайте ключи, токены или конфигурацию подключения.",
    },
)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _event_time(row: Event) -> datetime:
    return row.occurred_at or row.received_at or row.created_at or _now()


def _opaque_ref(kind: str, *values: object) -> str:
    material = "\x1f".join(["pokrov-support-v1", kind, *(str(value or "") for value in values)])
    return f"{kind}_{hashlib.sha256(material.encode('utf-8')).hexdigest()[:20]}"


def _clean(value: object, maximum: int) -> str | None:
    normalized = " ".join(str(value or "").strip().split())
    if not normalized:
        return None
    return normalized[:maximum]


def _sla_status(ticket: SupportTicket, now: datetime | None = None) -> str:
    if str(ticket.status or "").lower() == "closed":
        return "stopped"
    due_at = ticket.sla_due_at
    if due_at is None:
        return "missing"
    current = now or _now()
    remaining = (due_at - current).total_seconds()
    if remaining < 0:
        return "breached"
    if remaining <= 60 * 60:
        return "at_risk"
    return "ok"


def ticket_message_view(row: SupportTicketMessage) -> dict[str, Any]:
    return {
        "id": int(row.id),
        "sender_role": str(row.sender_role or "unknown")[:20],
        "sender_tg_id": int(row.sender_tg_id),
        "visibility": str(getattr(row, "visibility", "public") or "public")[:16],
        "macro_code": _clean(getattr(row, "macro_code", None), 48),
        "body": str(row.body or "")[:12500 if row.sender_role == "assistant" else 2000],
        "has_attachment": bool(row.media_type or row.media_file_id),
        "media_type": _clean(row.media_type, 32),
        "created_at": _iso(row.created_at),
    }


def ticket_view(ticket: SupportTicket, *, last_message: SupportTicketMessage | None = None) -> dict[str, Any]:
    return {
        "id": int(ticket.id),
        "environment": str(getattr(ticket, "environment", "production") or "production")[:32],
        "user_tg_id": int(ticket.user_tg_id),
        "status": str(ticket.status or "open")[:20],
        "subject": _clean(ticket.subject, 200) or "Без темы",
        "priority": str(getattr(ticket, "priority", "normal") or "normal")[:16],
        "queue": str(getattr(ticket, "queue", "general") or "general")[:48],
        "assigned_admin_tg_id": int(ticket.assigned_admin_tg_id) if ticket.assigned_admin_tg_id is not None else None,
        "assigned_team": _clean(getattr(ticket, "assigned_team", None), 48),
        "waiting_on": _clean(getattr(ticket, "waiting_on", None), 24),
        "sla_due_at": _iso(getattr(ticket, "sla_due_at", None)),
        "sla_status": _sla_status(ticket),
        "escalated_at": _iso(getattr(ticket, "escalated_at", None)),
        "incident_id": _clean(getattr(ticket, "incident_id", None), 36),
        "attempt_ref": _clean(getattr(ticket, "attempt_ref", None), 64),
        "version": max(1, int(getattr(ticket, "version", 1) or 1)),
        "created_at": _iso(ticket.created_at),
        "updated_at": _iso(ticket.updated_at),
        "closed_at": _iso(ticket.closed_at),
        "last_message_preview": str(last_message.body or "")[:200] if last_message is not None else "",
        "last_message_visibility": str(getattr(last_message, "visibility", "public") or "public") if last_message is not None else None,
    }


def _last_messages(session, ticket_ids: Iterable[int]) -> dict[int, SupportTicketMessage]:
    result: dict[int, SupportTicketMessage] = {}
    ids = sorted({int(value) for value in ticket_ids})
    if not ids:
        return result
    rows = (
        session.query(SupportTicketMessage)
        .filter(SupportTicketMessage.ticket_id.in_(ids))
        .order_by(SupportTicketMessage.ticket_id.asc(), SupportTicketMessage.id.desc())
        .all()
    )
    for row in rows:
        result.setdefault(int(row.ticket_id), row)
    return result


def list_support_tickets(
    session,
    *,
    environment: str,
    status: str | None = None,
    priority: str | None = None,
    queue: str | None = None,
    assignment: str | None = None,
    actor_tg_id: int | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    query = session.query(SupportTicket).filter(SupportTicket.environment == str(environment))
    if status and status != "active":
        query = query.filter(SupportTicket.status == str(status))
    elif status == "active" or not status:
        query = query.filter(SupportTicket.status != "closed")
    if priority:
        query = query.filter(SupportTicket.priority == str(priority))
    if queue:
        query = query.filter(SupportTicket.queue == str(queue))
    if assignment == "unassigned":
        query = query.filter(SupportTicket.assigned_admin_tg_id.is_(None))
    elif assignment == "mine" and actor_tg_id is not None:
        query = query.filter(SupportTicket.assigned_admin_tg_id == int(actor_tg_id))
    rows = query.order_by(
        SupportTicket.escalated_at.is_(None).asc(),
        SupportTicket.sla_due_at.asc(),
        SupportTicket.updated_at.asc(),
        SupportTicket.id.asc(),
    ).limit(max(1, min(int(limit), 300))).all()
    last = _last_messages(session, [row.id for row in rows])
    return [ticket_view(row, last_message=last.get(int(row.id))) for row in rows]


def _bundle_views(session, ticket_id: int) -> list[dict[str, Any]]:
    rows = (
        session.query(SupportBundleUpload)
        .filter(SupportBundleUpload.ticket_id == int(ticket_id))
        .order_by(SupportBundleUpload.created_at.desc(), SupportBundleUpload.id.desc())
        .limit(20)
        .all()
    )
    audits = (
        session.query(SupportBundleAccessAudit)
        .filter(SupportBundleAccessAudit.ticket_id == int(ticket_id))
        .order_by(SupportBundleAccessAudit.created_at.desc(), SupportBundleAccessAudit.id.desc())
        .limit(100)
        .all()
    )
    by_upload: dict[str, list[SupportBundleAccessAudit]] = {}
    for audit in audits:
        by_upload.setdefault(str(audit.upload_id), []).append(audit)
    return [
        {
            "bundle_ref": _opaque_ref("bundle", row.upload_id),
            "attempt_ref": _clean(row.attempt_ref, 64),
            "attempt_link_source": "operator" if row.attempt_ref else None,
            "status": str(row.status or "unknown")[:24],
            "diagnostic_profile": _clean(row.diagnostic_profile, 16),
            "app_version": _clean(row.app_version, 64),
            "build_number": _clean(row.build_number, 80),
            "platform": _clean(row.platform, 16),
            "architecture": _clean(row.architecture, 16),
            "last_phase": _clean(row.last_phase, 32),
            "last_error_code": _clean(row.last_error_code, 32),
            "proof_outcome": _clean(row.proof_outcome, 24),
            "expires_at": _iso(row.expires_at),
            "retention_hold": bool(row.retention_hold),
            "access_audit": {
                "count": len(by_upload.get(str(row.upload_id), [])),
                "last_action": _clean(by_upload[str(row.upload_id)][0].action, 24) if by_upload.get(str(row.upload_id)) else None,
                "last_at": _iso(by_upload[str(row.upload_id)][0].created_at) if by_upload.get(str(row.upload_id)) else None,
            },
        }
        for row in rows
    ]


def support_bundle_upload_id_for_ref(
    session, *, environment: str, ticket_id: int, bundle_ref: str
) -> str | None:
    normalized_ref = str(bundle_ref or "").strip().lower()
    if not normalized_ref.startswith("bundle_") or len(normalized_ref) != 27:
        return None
    rows = (
        session.query(SupportBundleUpload)
        .join(SupportTicket, SupportTicket.id == SupportBundleUpload.ticket_id)
        .filter(
            SupportBundleUpload.ticket_id == int(ticket_id),
            SupportTicket.environment == str(environment),
        )
        .order_by(SupportBundleUpload.created_at.desc(), SupportBundleUpload.id.desc())
        .limit(20)
        .all()
    )
    for row in rows:
        if _opaque_ref("bundle", row.upload_id) == normalized_ref:
            return str(row.upload_id)
    return None


def search_support_cases(
    session, *, environment: str, query: str, limit: int = 12
) -> list[dict[str, str]]:
    normalized = " ".join(str(query or "").strip().split())
    if not 2 <= len(normalized) <= 128:
        raise ValueError("support_search_query_invalid")
    bounded_limit = max(1, min(int(limit), 20))
    escaped = normalized.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    like = f"%{escaped.lower()}%"
    results: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(item: dict[str, str]) -> None:
        key = (item["kind"], item["id"])
        if key in seen or len(results) >= bounded_limit:
            return
        seen.add(key)
        results.append(item)

    case_query = normalized.removeprefix("#")
    if case_query.isdigit():
        tickets = (
            session.query(SupportTicket)
            .filter(
                SupportTicket.environment == str(environment),
                func.cast(SupportTicket.id, String).like(f"%{case_query}%"),
            )
            .order_by(SupportTicket.updated_at.desc(), SupportTicket.id.desc())
            .limit(bounded_limit)
            .all()
        )
        for ticket in tickets:
            ticket_id = int(ticket.id)
            add(
                {
                    "kind": "case",
                    "id": str(ticket_id),
                    "title": f"Тикет #{ticket_id}",
                    "subtitle": f"Статус {str(ticket.status or 'unknown')}, очередь {str(ticket.queue or 'general')}",
                    "href": f"/tickets?selected={ticket_id}",
                }
            )

    bundle_rows: list[tuple[SupportBundleUpload, SupportTicket]] = []
    if normalized.lower().startswith("bundle_") and len(normalized) == 27:
        recent_bundles = (
            session.query(SupportBundleUpload, SupportTicket)
            .join(SupportTicket, SupportTicket.id == SupportBundleUpload.ticket_id)
            .filter(SupportTicket.environment == str(environment))
            .order_by(SupportBundleUpload.updated_at.desc(), SupportBundleUpload.id.desc())
            .limit(200)
            .all()
        )
        bundle_rows.extend(
            (bundle, ticket)
            for bundle, ticket in recent_bundles
            if _opaque_ref("bundle", bundle.upload_id) == normalized.lower()
        )
    bundle_rows.extend(
        session.query(SupportBundleUpload, SupportTicket)
        .join(SupportTicket, SupportTicket.id == SupportBundleUpload.ticket_id)
        .filter(
            SupportTicket.environment == str(environment),
            or_(
                func.lower(SupportBundleUpload.upload_id).like(like, escape="\\"),
                func.lower(SupportBundleUpload.bundle_id).like(like, escape="\\"),
            ),
        )
        .order_by(SupportBundleUpload.updated_at.desc(), SupportBundleUpload.id.desc())
        .limit(bounded_limit)
        .all()
    )
    seen_uploads: set[str] = set()
    for bundle, ticket in bundle_rows:
        if str(bundle.upload_id) in seen_uploads:
            continue
        seen_uploads.add(str(bundle.upload_id))
        ticket_id = int(ticket.id)
        bundle_ref = _opaque_ref("bundle", bundle.upload_id)
        add(
            {
                "kind": "support_bundle",
                "id": bundle_ref,
                "title": f"Пакет поддержки · тикет #{ticket_id}",
                "subtitle": f"Статус {str(bundle.status or 'unknown')}, профиль {str(bundle.diagnostic_profile or 'unknown')}",
                "href": f"/tickets?selected={ticket_id}",
            }
        )

    correlation = normalized.lower()
    if all(character.isalnum() or character in "._:-" for character in correlation):
        events = (
            session.query(Event)
            .filter(func.lower(Event.trace_id) == correlation)
            .order_by(Event.received_at.desc(), Event.id.desc())
            .limit(bounded_limit)
            .all()
        )
        for event in events:
            owner_filter = SupportTicket.user_tg_id == int(event.tg_id)
            account_id = str(event.account_id or "").strip()
            if account_id:
                owner_filter = or_(owner_filter, SupportTicket.account_id == account_id)
            ticket = (
                session.query(SupportTicket)
                .filter(
                    SupportTicket.environment == str(environment),
                    owner_filter,
                )
                .order_by(SupportTicket.updated_at.desc(), SupportTicket.id.desc())
                .first()
            )
            if ticket is None:
                continue
            ticket_id = int(ticket.id)
            add(
                {
                    "kind": "correlation",
                    "id": correlation,
                    "title": f"Корреляция · тикет #{ticket_id}",
                    "subtitle": f"Этап {str(event.stage or 'unknown')}, код {str(event.error_code or 'нет')}",
                    "href": f"/tickets?selected={ticket_id}",
                }
            )
    return results


def support_ticket_detail(session, *, environment: str, ticket_id: int) -> dict[str, Any] | None:
    ticket = (
        session.query(SupportTicket)
        .filter(SupportTicket.id == int(ticket_id), SupportTicket.environment == str(environment))
        .first()
    )
    if ticket is None:
        return None
    messages = (
        session.query(SupportTicketMessage)
        .filter(SupportTicketMessage.ticket_id == int(ticket.id))
        .order_by(SupportTicketMessage.created_at.asc(), SupportTicketMessage.id.asc())
        .limit(300)
        .all()
    )
    incident = None
    if ticket.incident_id:
        incident = session.query(ServiceIncident).filter(
            ServiceIncident.id == str(ticket.incident_id),
            ServiceIncident.environment == str(environment),
        ).first()
    return {
        **ticket_view(ticket, last_message=messages[-1] if messages else None),
        "messages": [ticket_message_view(row) for row in messages],
        "incident": None if incident is None else {
            "id": str(incident.id),
            "incident_key": str(incident.incident_key or "")[:80],
            "title": str(incident.title or "")[:240],
            "status": str(getattr(incident, "workflow_status", "investigating") or "investigating")[:24],
        },
        "support_bundles": _bundle_views(session, int(ticket.id)),
        "evidence_policy": {
            "client_events": "allowlist_projection_only",
            "support_bundles": "ttl_and_access_audit_enforced",
            "observer": "trusted_server_observer",
        },
    }


def _event_rows(session, *, tg_id: int, account_id: str | None, limit: int = 500) -> list[Event]:
    filters = [Event.tg_id == int(tg_id)]
    if account_id:
        filters.append(Event.account_id == str(account_id))
    return (
        session.query(Event)
        .filter(or_(*filters))
        .filter(
            or_(
                Event.platform.isnot(None),
                Event.source.in_(["app", "client", "android", "windows", "app_shell", "android_shell", "windows_shell"]),
                Event.surface.in_(["app", "client"]),
            )
        )
        .order_by(Event.occurred_at.desc(), Event.received_at.desc(), Event.id.desc())
        .limit(max(1, min(int(limit), 500)))
        .all()
    )


def _adapt_event(row: Event, *, fallback_install: str | None) -> dict[str, Any]:
    install_raw = str(row.device_id or fallback_install or "unknown")
    session_raw = str(row.session_id or f"event:{row.id}")
    if row.trace_id:
        attempt_raw = str(row.trace_id)
    elif row.session_id and row.attempt_number is not None:
        attempt_raw = f"{session_raw}:attempt:{row.attempt_number}"
    else:
        attempt_raw = f"event:{row.id}"
    fingerprint_parts = (
        row.platform,
        row.app_version,
        row.build_number,
        row.subsystem,
        row.stage,
        row.result,
        row.error_category,
        row.error_code,
        row.network_class,
    )
    return {
        "event_id": int(row.id),
        "connectivity": project_connectivity(row.meta_json, received_at=row.received_at or row.created_at, now=_now()),
        "installation_ref": _opaque_ref("install", install_raw),
        "session_ref": _opaque_ref("session", install_raw, session_raw),
        "attempt_ref": _opaque_ref("attempt", install_raw, attempt_raw),
        "fingerprint": _opaque_ref("fp", *fingerprint_parts),
        "event_name": str(row.event_name or "unknown")[:64],
        "source": str(row.source or "unknown")[:32],
        "platform": _clean(row.platform, 24),
        "app_version": _clean(row.app_version, 32),
        "build_number": _clean(row.build_number, 24),
        "subsystem": _clean(row.subsystem, 32),
        "stage": _clean(row.stage, 64),
        "result": _clean(row.result, 24),
        "error_category": _clean(row.error_category, 32),
        "error_code": _clean(row.error_code, 64),
        "retryable": bool(row.retryable) if row.retryable is not None else None,
        "attempt_number": int(row.attempt_number) if row.attempt_number is not None else None,
        "duration_ms": int(row.duration_ms) if row.duration_ms is not None else None,
        "network_class": _clean(row.network_class, 24),
        "clock_skew_state": _clean(row.clock_skew_state, 24),
        "occurred_at": _iso(row.occurred_at),
        "received_at": _iso(row.received_at or row.created_at),
    }


def _group_attempts(events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    attempts: dict[str, dict[str, Any]] = {}
    fingerprint_counts: Counter[str] = Counter()
    fingerprint_sample: dict[str, dict[str, Any]] = {}
    for event in sorted(events, key=lambda item: str(item.get("occurred_at") or item.get("received_at") or "")):
        ref = str(event["attempt_ref"])
        attempt = attempts.setdefault(ref, {
            "attempt_ref": ref,
            "installation_ref": event["installation_ref"],
            "session_ref": event["session_ref"],
            "started_at": event.get("occurred_at") or event.get("received_at"),
            "ended_at": event.get("occurred_at") or event.get("received_at"),
            "outcome": event.get("result"),
            "event_count": 0,
            "fingerprints": [],
            "events": [],
            "connectivity": None,
        })
        attempt["ended_at"] = event.get("occurred_at") or event.get("received_at") or attempt["ended_at"]
        # A status self-report does not replace the connection result.
        if event.get("result") != "reported" or not attempt["outcome"]:
            attempt["outcome"] = event.get("result") or attempt["outcome"]
        attempt["event_count"] += 1
        connectivity = event.get("connectivity")
        if connectivity is not None and (
            attempt["connectivity"] is None
            or connectivity["sequence"] > attempt["connectivity"]["sequence"]
        ):
            attempt["connectivity"] = connectivity
        if len(attempt["events"]) < 50:
            attempt["events"].append(event)
        fingerprint = str(event["fingerprint"])
        fingerprint_counts[fingerprint] += 1
        fingerprint_sample.setdefault(fingerprint, event)
        if fingerprint not in attempt["fingerprints"]:
            attempt["fingerprints"].append(fingerprint)
    attempt_rows = sorted(attempts.values(), key=lambda item: str(item.get("ended_at") or ""), reverse=True)
    fingerprints = [
        {
            "fingerprint": ref,
            "count": count,
            "platform": fingerprint_sample[ref].get("platform"),
            "app_version": fingerprint_sample[ref].get("app_version"),
            "subsystem": fingerprint_sample[ref].get("subsystem"),
            "stage": fingerprint_sample[ref].get("stage"),
            "result": fingerprint_sample[ref].get("result"),
            "error_code": fingerprint_sample[ref].get("error_code"),
        }
        for ref, count in fingerprint_counts.most_common(50)
    ]
    return attempt_rows, fingerprints


def user_360(
    session,
    *,
    environment: str,
    tg_id: int,
    include_sensitive_diagnostics: bool,
) -> dict[str, Any] | None:
    user = session.query(User).filter(User.tg_id == int(tg_id)).first()
    if user is None:
        return None
    adapted = []
    if include_sensitive_diagnostics:
        adapted = [
            _adapt_event(row, fallback_install=user.app_install_id)
            for row in _event_rows(
                session,
                tg_id=int(tg_id),
                account_id=str(user.account_id or "") or None,
            )
        ]
    attempts, fingerprints = _group_attempts(adapted)
    network_context = []
    if include_sensitive_diagnostics:
        for observation in recent_network_context(session, account_id=str(user.account_id or "")):
            device_id = observation.pop("device_id", None)
            network_context.append({
                **observation, "device_ref": _opaque_ref("network-device", device_id),
            })
    installations: dict[str, dict[str, Any]] = {}
    sessions: dict[str, dict[str, Any]] = {}
    for attempt in attempts:
        install = installations.setdefault(str(attempt["installation_ref"]), {
            "installation_ref": attempt["installation_ref"], "attempts": 0, "sessions": set(), "last_seen_at": None,
        })
        install["attempts"] += 1
        install["sessions"].add(str(attempt["session_ref"]))
        install["last_seen_at"] = max(str(install["last_seen_at"] or ""), str(attempt.get("ended_at") or "")) or None
        session_row = sessions.setdefault(str(attempt["session_ref"]), {
            "session_ref": attempt["session_ref"], "installation_ref": attempt["installation_ref"], "attempts": 0, "last_seen_at": None,
        })
        session_row["attempts"] += 1
        session_row["last_seen_at"] = max(str(session_row["last_seen_at"] or ""), str(attempt.get("ended_at") or "")) or None
    observer = session.query(ObserverUserState).filter(ObserverUserState.tg_id == int(tg_id)).first()
    ticket_owner = and_(
        SupportTicket.account_id.is_(None),
        SupportTicket.user_tg_id == int(tg_id),
    )
    if user.account_id:
        ticket_owner = or_(
            SupportTicket.account_id == str(user.account_id),
            ticket_owner,
        )
    ticket_rows = (
        session.query(SupportTicket)
        .filter(
            SupportTicket.environment == str(environment),
            ticket_owner,
        )
        .order_by(SupportTicket.updated_at.desc(), SupportTicket.id.desc())
        .limit(100)
        .all()
    )
    ticket_last = _last_messages(session, [row.id for row in ticket_rows])
    tickets = [
        ticket_view(row, last_message=ticket_last.get(int(row.id)))
        for row in ticket_rows
    ]
    return {
        "entity": {
            "tg_id": int(user.tg_id),
            "account_ref": _opaque_ref("account", user.account_id or user.tg_id),
            "username": _clean(user.username, 128),
            "display_name": _clean(getattr(user, "display_name", None), 160),
            "status": "active" if bool(user.is_active) else "inactive",
            "plan": _clean(user.sub_type, 32),
            "platform": _clean(user.app_platform, 32),
            "app_version": _clean(getattr(user, "app_version", None), 32),
            "last_seen_at": _iso(getattr(user, "app_last_seen_at", None)),
        },
        "installations": [
            {**row, "sessions": len(row["sessions"])} for row in installations.values()
        ],
        "sessions": list(sessions.values()),
        "attempts": attempts[:100],
        "fingerprints": fingerprints,
        "network_context": network_context,
        "tickets": tickets,
        "field_access": {
            "support_diagnostics": {
                "state": "visible" if include_sensitive_diagnostics else "redacted",
                "required_permission": "support.sensitive.read",
                "classification": "sensitive_support_diagnostics",
            }
        },
        "observer": {
            "authority": "trusted_server_observer",
            "state": str(getattr(observer, "state", "missing") or "missing")[:24],
            "observed_ip_count_24h": int(getattr(observer, "observed_ip_count_24h", 0) or 0),
            "observed_node_count_24h": int(getattr(observer, "observed_node_count_24h", 0) or 0),
            "last_observed_at": _iso(getattr(observer, "last_observed_at", None)),
        },
        "privacy": {
            "adapter": "event_allowlist_v1",
            "excluded": ["meta_json", "raw identifiers", "ip", "url", "token", "configuration"],
            "network_context_exception": "support.sensitive.read; access-network IP and coarse context up to 72h",
        },
    }


def attempt_explorer(
    session,
    *,
    environment: str,
    ticket_id: int | None = None,
    tg_id: int | None = None,
    attempt_ref: str | None = None,
) -> dict[str, Any] | None:
    ticket = None
    if ticket_id is not None:
        ticket = session.query(SupportTicket).filter(
            SupportTicket.id == int(ticket_id), SupportTicket.environment == str(environment)
        ).first()
        if ticket is None:
            return None
        tg_id = int(ticket.user_tg_id)
        attempt_ref = attempt_ref or ticket.attempt_ref
    if tg_id is None:
        return None
    projection = user_360(
        session,
        environment=environment,
        tg_id=int(tg_id),
        include_sensitive_diagnostics=True,
    )
    if projection is None:
        return None
    selected = None
    if attempt_ref:
        selected = next((row for row in projection["attempts"] if row["attempt_ref"] == attempt_ref), None)
    return {
        "tg_id": int(tg_id),
        "ticket_id": int(ticket.id) if ticket is not None else None,
        "linked_attempt_ref": attempt_ref,
        "selected": selected,
        "attempts": projection["attempts"],
        "fingerprints": projection["fingerprints"],
        "privacy": projection["privacy"],
    }


__all__ = [
    "SUPPORT_MACROS",
    "TICKET_PRIORITIES",
    "TICKET_QUEUES",
    "TICKET_WAITING_ON",
    "attempt_explorer",
    "list_support_tickets",
    "search_support_cases",
    "support_bundle_upload_id_for_ref",
    "support_ticket_detail",
    "ticket_view",
    "user_360",
]
