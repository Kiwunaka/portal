"""Read models and audit helpers for Operator Center shift and incident work."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Iterable

from models import (
    AdminActionIntent,
    AdminAudit,
    ExternalOrder,
    OperatorIncidentEvent,
    OperatorIncidentLink,
    OperatorTask,
    OpsAlert,
    ReleaseKnownIssue,
    ServiceIncident,
    SupportTicket,
)


OPEN_TASK_STATUSES = frozenset({"open", "in_progress", "blocked"})
OPEN_INCIDENT_STATUSES = frozenset({"investigating", "identified", "monitoring"})


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def add_admin_audit(
    *,
    session,
    actor_tg_id: int,
    action: str,
    target_tg_id: int | None = None,
    meta: dict[str, Any] | None = None,
) -> AdminAudit:
    row = AdminAudit(
        actor_tg_id=int(actor_tg_id),
        action=str(action or "").strip()[:64],
        target_tg_id=int(target_tg_id) if target_tg_id is not None else None,
        meta=json.dumps(meta or {}, ensure_ascii=False, separators=(",", ":"))[:2000],
    )
    session.add(row)
    session.flush()
    return row


def task_payload(row: OperatorTask) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "environment": str(row.environment),
        "title": str(row.title),
        "owner_operator_id": str(row.owner_operator_id) if row.owner_operator_id else None,
        "owner_team": str(row.owner_team) if row.owner_team else None,
        "status": str(row.status),
        "priority": str(row.priority),
        "due_at": _iso(row.due_at),
        "next_action": str(row.next_action) if row.next_action else None,
        "source": str(row.source),
        "linked_entity": (
            {
                "type": str(row.linked_entity_type),
                "id": str(row.linked_entity_id),
            }
            if row.linked_entity_type and row.linked_entity_id
            else None
        ),
        "version": int(row.version or 1),
        "completed_at": _iso(row.completed_at),
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


def incident_summary_payload(row: ServiceIncident) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "key": str(row.incident_key),
        "environment": str(row.environment or "production"),
        "title": str(row.title),
        "summary": str(row.summary),
        "severity": str(row.severity),
        "public_status": str(row.status),
        "workflow_status": str(row.workflow_status or "investigating"),
        "version": int(row.workflow_version or 1),
        "owner_operator_id": str(row.owner_operator_id) if row.owner_operator_id else None,
        "owner_team": str(row.owner_team) if row.owner_team else None,
        "impact": str(row.impact) if row.impact else None,
        "started_at": _iso(row.started_at),
        "ended_at": _iso(row.ended_at),
        "next_update_at": _iso(row.next_update_at),
        "runbook_url": str(row.runbook_url) if row.runbook_url else None,
        "communications_summary": (
            str(row.communications_summary) if row.communications_summary else None
        ),
        "postmortem_status": str(row.postmortem_status or "not_required"),
        "postmortem_url": str(row.postmortem_url) if row.postmortem_url else None,
        "affected_node_codes": _json_string_list(row.affected_node_codes_json),
        "compensation": {
            "days": int(row.compensation_days or 0),
            "impacted_accounts": int(row.impacted_accounts_count or 0),
            "granted_accounts": int(row.granted_accounts_count or 0),
            "started_at": _iso(row.compensation_started_at),
            "completed_at": _iso(row.compensation_completed_at),
        },
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


def _json_string_list(value: str | None) -> list[str]:
    try:
        raw = json.loads(str(value or "[]"))
    except (TypeError, ValueError):
        return []
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw if str(item or "").strip()]


def list_tasks(
    session,
    *,
    environment: str,
    statuses: Iterable[str] | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    query = session.query(OperatorTask).filter(OperatorTask.environment == str(environment))
    selected = tuple(str(value) for value in (statuses or ()))
    if selected:
        query = query.filter(OperatorTask.status.in_(selected))
    rows = (
        query.order_by(
            OperatorTask.due_at.asc(),
            OperatorTask.created_at.asc(),
            OperatorTask.id.asc(),
        )
        .limit(max(1, min(500, int(limit))))
        .all()
    )
    return [task_payload(row) for row in rows]


def list_incidents(
    session,
    *,
    environment: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    rows = (
        session.query(ServiceIncident)
        .filter(ServiceIncident.environment == str(environment))
        .order_by(ServiceIncident.started_at.desc(), ServiceIncident.created_at.desc())
        .limit(max(1, min(300, int(limit))))
        .all()
    )
    return [incident_summary_payload(row) for row in rows]


def incident_detail(
    session,
    *,
    environment: str,
    incident_id: str,
) -> dict[str, Any] | None:
    incident = (
        session.query(ServiceIncident)
        .filter(
            ServiceIncident.id == str(incident_id),
            ServiceIncident.environment == str(environment),
        )
        .one_or_none()
    )
    if incident is None:
        return None
    events = (
        session.query(OperatorIncidentEvent)
        .filter(OperatorIncidentEvent.incident_id == str(incident.id))
        .order_by(OperatorIncidentEvent.incident_version.asc())
        .all()
    )
    links = (
        session.query(OperatorIncidentLink)
        .filter(OperatorIncidentLink.incident_id == str(incident.id))
        .order_by(OperatorIncidentLink.created_at.asc(), OperatorIncidentLink.id.asc())
        .all()
    )
    alerts = (
        session.query(OpsAlert)
        .filter(
            OpsAlert.environment == str(environment),
            OpsAlert.incident_id == str(incident.id),
        )
        .order_by(OpsAlert.last_seen_at.desc(), OpsAlert.id.desc())
        .all()
    )
    follow_ups = (
        session.query(OperatorTask)
        .filter(
            OperatorTask.environment == str(environment),
            OperatorTask.linked_entity_type == "incident",
            OperatorTask.linked_entity_id == str(incident.id),
        )
        .order_by(OperatorTask.created_at.asc(), OperatorTask.id.asc())
        .all()
    )
    return {
        **incident_summary_payload(incident),
        "timeline": [
            {
                "id": str(row.id),
                "version": int(row.incident_version),
                "event_type": str(row.event_type),
                "from_status": str(row.from_status) if row.from_status else None,
                "to_status": str(row.to_status) if row.to_status else None,
                "note": str(row.note) if row.note else None,
                "actor_operator_id": str(row.actor_operator_id) if row.actor_operator_id else None,
                "created_at": _iso(row.created_at),
            }
            for row in events
        ],
        "linked_entities": [
            {
                "id": str(row.id),
                "type": str(row.entity_type),
                "entity_id": str(row.entity_id),
                "label": str(row.label) if row.label else None,
                "created_at": _iso(row.created_at),
            }
            for row in links
        ],
        "alerts": [_alert_payload(row) for row in alerts],
        "follow_up_tasks": [task_payload(row) for row in follow_ups],
    }


def _alert_payload(row: OpsAlert) -> dict[str, Any]:
    return {
        "id": int(row.id),
        "source": str(row.source),
        "severity": str(row.severity),
        "status": str(row.status),
        "title": str(row.title),
        "node_code": str(row.node_code) if row.node_code else None,
        "incident_id": str(row.incident_id) if row.incident_id else None,
        "version": int(row.version or 1),
        "first_seen_at": _iso(row.first_seen_at),
        "last_seen_at": _iso(row.last_seen_at),
        "acknowledged_at": _iso(row.acknowledged_at),
    }


def build_shift_read_model(
    session,
    *,
    environment: str,
    operator_id: str,
    actor_tg_id: int,
    teams: Iterable[str],
    limit: int = 100,
) -> dict[str, Any]:
    cap = max(1, min(200, int(limit)))
    open_tasks = (
        session.query(OperatorTask)
        .filter(
            OperatorTask.environment == str(environment),
            OperatorTask.status.in_(tuple(OPEN_TASK_STATUSES)),
        )
        .order_by(OperatorTask.due_at.asc(), OperatorTask.created_at.asc())
        .limit(cap * 3)
        .all()
    )
    team_set = {str(value) for value in teams if str(value or "").strip()}

    failed_commands = (
        session.query(AdminActionIntent)
        .filter(
            AdminActionIntent.actor_tg_id == int(actor_tg_id),
            AdminActionIntent.status.in_(("failed", "uncertain")),
        )
        .order_by(AdminActionIntent.updated_at.desc())
        .limit(cap)
        .all()
    )
    tickets = (
        session.query(SupportTicket)
        .filter(SupportTicket.status.in_(("open", "in_progress")))
        .order_by(SupportTicket.updated_at.asc(), SupportTicket.id.asc())
        .limit(cap)
        .all()
    )
    incidents = (
        session.query(ServiceIncident)
        .filter(
            ServiceIncident.environment == str(environment),
            ServiceIncident.workflow_status.in_(tuple(OPEN_INCIDENT_STATUSES)),
        )
        .order_by(ServiceIncident.started_at.asc())
        .limit(cap)
        .all()
    )
    payments = (
        session.query(ExternalOrder)
        .filter(
            ExternalOrder.status.in_(
                ("manual_review", "pending_verification", "failed", "chargeback")
            )
        )
        .order_by(ExternalOrder.created_at.asc(), ExternalOrder.id.asc())
        .limit(cap)
        .all()
    )
    release_blockers = (
        session.query(ReleaseKnownIssue)
        .filter(
            ReleaseKnownIssue.status.notin_(("resolved", "closed", "cancelled")),
            ReleaseKnownIssue.severity.in_(("critical", "major", "high")),
        )
        .order_by(ReleaseKnownIssue.created_at.asc(), ReleaseKnownIssue.id.asc())
        .limit(cap)
        .all()
    )
    source_failures = (
        session.query(OpsAlert)
        .filter(
            OpsAlert.environment == str(environment),
            OpsAlert.status.in_(("active", "acknowledged")),
        )
        .order_by(OpsAlert.last_seen_at.desc(), OpsAlert.id.desc())
        .limit(cap)
        .all()
    )

    return {
        "environment": str(environment),
        "operator_id": str(operator_id),
        "teams": sorted(team_set),
        "mine": [task_payload(row) for row in open_tasks if row.owner_operator_id == operator_id][:cap],
        "team": [task_payload(row) for row in open_tasks if row.owner_team in team_set][:cap],
        "unassigned": [
            task_payload(row)
            for row in open_tasks
            if row.owner_operator_id is None and row.owner_team is None
        ][:cap],
        "failed_commands": [
            {
                "intent_id": str(row.id),
                "action": str(row.action),
                "target": {"type": str(row.target_type), "id": str(row.target_id)},
                "status": str(row.status),
                "result_code": str(row.result_code) if row.result_code else None,
                "updated_at": _iso(row.updated_at),
            }
            for row in failed_commands
        ],
        "tickets": [
            {
                "id": int(row.id),
                "subject": str(row.subject) if row.subject else "Без темы",
                "status": str(row.status),
                "assigned_to_me": int(row.assigned_admin_tg_id or 0) == int(actor_tg_id),
                "updated_at": _iso(row.updated_at),
            }
            for row in tickets
        ],
        "incident_work": [incident_summary_payload(row) for row in incidents],
        "payment_review": [
            {
                "id": int(row.id),
                "provider": str(row.provider),
                "order_id": str(row.order_id),
                "status": str(row.status),
                "created_at": _iso(row.created_at),
            }
            for row in payments
        ],
        "release_blockers": [
            {
                "id": int(row.id),
                "candidate": str(row.candidate_label),
                "issue_code": str(row.issue_code),
                "severity": str(row.severity),
                "status": str(row.status),
                "title": str(row.title),
            }
            for row in release_blockers
        ],
        "source_failures": [_alert_payload(row) for row in source_failures],
    }


__all__ = [
    "OPEN_INCIDENT_STATUSES",
    "OPEN_TASK_STATUSES",
    "add_admin_audit",
    "build_shift_read_model",
    "incident_detail",
    "incident_summary_payload",
    "list_incidents",
    "list_tasks",
    "task_payload",
]
