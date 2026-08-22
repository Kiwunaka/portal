"""Action-intent policies for operator tasks, incidents, and alert transitions."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping
from urllib.parse import urlparse

import incident_service
from models import (
    OperatorIncidentEvent,
    OperatorIncidentLink,
    OperatorTask,
    OpsAlert,
    ServiceIncident,
)


TASK_STATUSES = frozenset({"open", "in_progress", "blocked", "done", "cancelled"})
TASK_PRIORITIES = frozenset({"critical", "high", "normal", "low"})
INCIDENT_STATUSES = frozenset({"investigating", "identified", "monitoring", "resolved", "cancelled"})
INCIDENT_SEVERITIES = frozenset({"minor", "degraded", "major", "critical"})
POSTMORTEM_STATUSES = frozenset({"not_required", "pending", "in_progress", "published"})
_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
_ENV_RE = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def _error(error_type, code: str, message: str, *, status_code: int = 422):
    raise error_type(code, status_code=status_code, message=message)


def _reject_extra(error_type, payload: Mapping[str, Any], allowed: set[str]) -> None:
    extra = sorted(set(payload) - allowed)
    if extra:
        _error(error_type, "invalid_payload", f"Unsupported payload fields: {', '.join(extra)}")


def _text(
    error_type,
    value: Any,
    *,
    field: str,
    minimum: int = 1,
    maximum: int,
    required: bool = True,
) -> str | None:
    if value is None and not required:
        return None
    normalized = str(value or "").strip()
    if not minimum <= len(normalized) <= maximum:
        _error(error_type, "invalid_payload", f"Field {field} has invalid length.")
    return normalized


def _optional_text(error_type, payload: Mapping[str, Any], field: str, maximum: int) -> str | None:
    if field not in payload or payload.get(field) is None:
        return None
    return _text(error_type, payload.get(field), field=field, maximum=maximum)


def _identifier(error_type, value: Any, *, field: str, maximum: int = 128) -> str:
    normalized = str(value or "").strip()
    if not normalized or len(normalized) > maximum or any(ord(ch) < 32 for ch in normalized):
        _error(error_type, "invalid_payload", f"Field {field} is invalid.")
    return normalized


def _uuid(error_type, value: Any, *, field: str) -> str:
    normalized = str(value or "").strip().lower()
    if not _UUID_RE.fullmatch(normalized):
        _error(error_type, "invalid_payload", f"Field {field} must be a UUID.")
    return normalized


def _environment(error_type, payload: Mapping[str, Any]) -> str:
    value = str(payload.get("_environment") or "").strip().lower()
    if not _ENV_RE.fullmatch(value):
        _error(error_type, "invalid_payload", "Operator environment is invalid.")
    return value


def _actor(error_type, payload: Mapping[str, Any]) -> tuple[str, int]:
    operator_id = _uuid(error_type, payload.get("_operator_id"), field="_operator_id")
    try:
        actor_tg_id = int(payload.get("_actor_tg_id"))
    except (TypeError, ValueError):
        _error(error_type, "invalid_payload", "Operator actor is invalid.")
    if actor_tg_id <= 0:
        _error(error_type, "invalid_payload", "Operator actor is invalid.")
    return operator_id, actor_tg_id


def _version(error_type, payload: Mapping[str, Any], field: str = "expected_version") -> int:
    try:
        value = int(payload.get(field))
    except (TypeError, ValueError):
        _error(error_type, "invalid_payload", f"Field {field} is invalid.")
    if value < 1:
        _error(error_type, "invalid_payload", f"Field {field} is invalid.")
    return value


def _iso_datetime(error_type, value: Any, *, field: str, required: bool = False) -> str | None:
    if value is None and not required:
        return None
    raw = str(value or "").strip()
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        _error(error_type, "invalid_payload", f"Field {field} must be ISO-8601.")
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed.replace(microsecond=0).isoformat() + "Z"


def _to_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed.replace(microsecond=0)


def _url(error_type, payload: Mapping[str, Any], field: str) -> str | None:
    value = _optional_text(error_type, payload, field, 500)
    if value is None:
        return None
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        _error(error_type, "invalid_payload", f"Field {field} must be an HTTP(S) URL.")
    return value


def _target_uuid(error_type, target_id: str) -> str:
    return _uuid(error_type, target_id, field="target.id")


def _lock(query, session, for_update: bool):
    if for_update and str(session.get_bind().dialect.name) == "postgresql":
        query = query.with_for_update()
    return query


def _task_create_payload(error_type, payload: Mapping[str, Any]) -> dict[str, Any]:
    allowed = {
        "_environment", "_operator_id", "_actor_tg_id", "title", "owner_operator_id",
        "owner_team", "priority", "due_at", "next_action", "source",
        "linked_entity_type", "linked_entity_id",
    }
    _reject_extra(error_type, payload, allowed)
    environment = _environment(error_type, payload)
    operator_id, actor_tg_id = _actor(error_type, payload)
    owner_operator_id = (
        _uuid(error_type, payload.get("owner_operator_id"), field="owner_operator_id")
        if payload.get("owner_operator_id")
        else None
    )
    owner_team = _optional_text(error_type, payload, "owner_team", 48)
    priority = str(payload.get("priority") or "normal").strip().lower()
    if priority not in TASK_PRIORITIES:
        _error(error_type, "invalid_payload", "Task priority is unsupported.")
    linked_type = _optional_text(error_type, payload, "linked_entity_type", 64)
    linked_id = _optional_text(error_type, payload, "linked_entity_id", 128)
    if bool(linked_type) != bool(linked_id):
        _error(error_type, "invalid_payload", "Linked entity type and id must be supplied together.")
    return {
        "_environment": environment,
        "_operator_id": operator_id,
        "_actor_tg_id": actor_tg_id,
        "title": _text(error_type, payload.get("title"), field="title", maximum=180),
        "owner_operator_id": owner_operator_id,
        "owner_team": owner_team,
        "priority": priority,
        "due_at": _iso_datetime(error_type, payload.get("due_at"), field="due_at"),
        "next_action": _optional_text(error_type, payload, "next_action", 500),
        "source": _text(error_type, payload.get("source"), field="source", maximum=64),
        "linked_entity_type": linked_type,
        "linked_entity_id": linked_id,
    }


def _task_update_payload(error_type, payload: Mapping[str, Any]) -> dict[str, Any]:
    allowed = {
        "_environment", "_operator_id", "_actor_tg_id", "expected_version", "title",
        "owner_operator_id", "owner_team", "status", "priority", "due_at",
        "next_action", "linked_entity_type", "linked_entity_id",
    }
    _reject_extra(error_type, payload, allowed)
    result: dict[str, Any] = {
        "_environment": _environment(error_type, payload),
        "_operator_id": _actor(error_type, payload)[0],
        "_actor_tg_id": _actor(error_type, payload)[1],
        "expected_version": _version(error_type, payload),
    }
    if "title" in payload:
        result["title"] = _text(error_type, payload.get("title"), field="title", maximum=180)
    if "owner_operator_id" in payload:
        result["owner_operator_id"] = (
            _uuid(error_type, payload.get("owner_operator_id"), field="owner_operator_id")
            if payload.get("owner_operator_id")
            else None
        )
    if "owner_team" in payload:
        result["owner_team"] = _optional_text(error_type, payload, "owner_team", 48)
    if "status" in payload:
        status = str(payload.get("status") or "").strip().lower()
        if status not in TASK_STATUSES:
            _error(error_type, "invalid_payload", "Task status is unsupported.")
        result["status"] = status
    if "priority" in payload:
        priority = str(payload.get("priority") or "").strip().lower()
        if priority not in TASK_PRIORITIES:
            _error(error_type, "invalid_payload", "Task priority is unsupported.")
        result["priority"] = priority
    if "due_at" in payload:
        result["due_at"] = _iso_datetime(error_type, payload.get("due_at"), field="due_at")
    if "next_action" in payload:
        result["next_action"] = _optional_text(error_type, payload, "next_action", 500)
    if "linked_entity_type" in payload or "linked_entity_id" in payload:
        linked_type = _optional_text(error_type, payload, "linked_entity_type", 64)
        linked_id = _optional_text(error_type, payload, "linked_entity_id", 128)
        if bool(linked_type) != bool(linked_id):
            _error(error_type, "invalid_payload", "Linked entity type and id must be supplied together.")
        result["linked_entity_type"] = linked_type
        result["linked_entity_id"] = linked_id
    if set(result) == {"_environment", "_operator_id", "_actor_tg_id", "expected_version"}:
        _error(error_type, "invalid_payload", "Task update is empty.")
    return result


def _task_state(EntityState, error_type, session, target_id, payload, for_update, *, create: bool):
    task_id = _target_uuid(error_type, target_id)
    query = session.query(OperatorTask).filter(OperatorTask.id == task_id)
    row = _lock(query, session, for_update).one_or_none()
    if create and row is not None:
        _error(error_type, "target_exists", "Task already exists.", status_code=409)
    if not create and row is None:
        _error(error_type, "target_not_found", "Task not found.", status_code=404)
    if row is not None and str(row.environment) != str(payload["_environment"]):
        _error(error_type, "target_not_found", "Task not found.", status_code=404)
    if row is not None and int(row.version or 1) != int(payload["expected_version"]):
        _error(error_type, "state_changed", "Task version changed.", status_code=409)
    snapshot = (
        {"id": task_id, "exists": False}
        if row is None
        else {"id": task_id, "version": int(row.version), "status": str(row.status)}
    )
    return EntityState(entity=row, version_snapshot=snapshot, public_snapshot=snapshot, context={"task_id": task_id})


def _task_preview(state, payload):
    change = {key: value for key, value in payload.items() if not key.startswith("_") and key != "expected_version"}
    return {
        "title": "Изменение операторской задачи",
        "summary": f"Задача {state.context['task_id']} будет изменена только при совпадении версии.",
        "before": state.public_snapshot,
        "after": change,
        "warnings": [],
        "task_id": state.context["task_id"],
    }


def _execute_task_create(session, state, payload):
    now = _now()
    row = OperatorTask(
        id=state.context["task_id"], environment=payload["_environment"], title=payload["title"],
        owner_operator_id=payload["owner_operator_id"], owner_team=payload["owner_team"],
        status="open", priority=payload["priority"], due_at=_to_datetime(payload["due_at"]),
        next_action=payload["next_action"], source=payload["source"],
        linked_entity_type=payload["linked_entity_type"], linked_entity_id=payload["linked_entity_id"],
        version=1, created_by=payload["_actor_tg_id"], updated_by=payload["_actor_tg_id"],
        created_at=now, updated_at=now,
    )
    session.add(row)
    session.flush()
    return {"task_id": str(row.id), "task_version": 1, "task_status": "open"}


def _execute_task_update(session, state, payload):
    row = state.entity
    for field in ("title", "owner_operator_id", "owner_team", "status", "priority", "next_action", "linked_entity_type", "linked_entity_id"):
        if field in payload:
            setattr(row, field, payload[field])
    if "due_at" in payload:
        row.due_at = _to_datetime(payload["due_at"])
    now = _now()
    if "status" in payload:
        row.completed_at = now if payload["status"] == "done" else None
    row.version = int(row.version or 1) + 1
    row.updated_by = int(payload["_actor_tg_id"])
    row.updated_at = now
    session.flush()
    return {"task_id": str(row.id), "task_version": int(row.version), "task_status": str(row.status)}


def _incident_create_payload(error_type, payload: Mapping[str, Any]) -> dict[str, Any]:
    allowed = {
        "_environment", "_operator_id", "_actor_tg_id", "incident_key", "title", "summary",
        "severity", "started_at", "affected_node_codes", "compensation_days", "owner_operator_id",
        "owner_team", "impact", "next_update_at", "runbook_url",
    }
    _reject_extra(error_type, payload, allowed)
    environment = _environment(error_type, payload)
    operator_id, actor_tg_id = _actor(error_type, payload)
    incident_key = str(payload.get("incident_key") or "").strip().lower()
    if not _KEY_RE.fullmatch(incident_key):
        _error(error_type, "invalid_payload", "Incident key is invalid.")
    severity = str(payload.get("severity") or "degraded").strip().lower()
    if severity not in INCIDENT_SEVERITIES:
        _error(error_type, "invalid_payload", "Incident severity is unsupported.")
    try:
        compensation_days = int(payload.get("compensation_days") or 0)
    except (TypeError, ValueError):
        _error(error_type, "invalid_payload", "Compensation days are invalid.")
    if compensation_days not in incident_service.ALLOWED_COMPENSATION_DAYS:
        _error(error_type, "invalid_payload", "Compensation days are unsupported.")
    raw_nodes = payload.get("affected_node_codes") or []
    if not isinstance(raw_nodes, list):
        _error(error_type, "invalid_payload", "Affected node codes must be a list.")
    node_codes = list(incident_service.normalize_node_codes(raw_nodes))
    return {
        "_environment": environment, "_operator_id": operator_id, "_actor_tg_id": actor_tg_id,
        "incident_key": incident_key,
        "title": _text(error_type, payload.get("title"), field="title", maximum=160),
        "summary": _text(error_type, payload.get("summary"), field="summary", maximum=600),
        "severity": severity,
        "started_at": _iso_datetime(error_type, payload.get("started_at"), field="started_at", required=True),
        "affected_node_codes": node_codes,
        "compensation_days": compensation_days,
        "owner_operator_id": (
            _uuid(error_type, payload.get("owner_operator_id"), field="owner_operator_id")
            if payload.get("owner_operator_id") else operator_id
        ),
        "owner_team": _optional_text(error_type, payload, "owner_team", 48),
        "impact": _optional_text(error_type, payload, "impact", 1000),
        "next_update_at": _iso_datetime(error_type, payload.get("next_update_at"), field="next_update_at"),
        "runbook_url": _url(error_type, payload, "runbook_url"),
    }


def _incident_update_payload(error_type, payload: Mapping[str, Any]) -> dict[str, Any]:
    allowed = {
        "_environment", "_operator_id", "_actor_tg_id", "expected_version", "workflow_status",
        "owner_operator_id", "owner_team", "impact", "next_update_at", "runbook_url",
        "communications_summary", "postmortem_status", "postmortem_url", "note", "ended_at",
    }
    _reject_extra(error_type, payload, allowed)
    operator_id, actor_tg_id = _actor(error_type, payload)
    result: dict[str, Any] = {
        "_environment": _environment(error_type, payload), "_operator_id": operator_id,
        "_actor_tg_id": actor_tg_id, "expected_version": _version(error_type, payload),
    }
    if "workflow_status" in payload:
        status = str(payload.get("workflow_status") or "").strip().lower()
        if status not in INCIDENT_STATUSES:
            _error(error_type, "invalid_payload", "Incident status is unsupported.")
        result["workflow_status"] = status
    if "owner_operator_id" in payload:
        result["owner_operator_id"] = (
            _uuid(error_type, payload.get("owner_operator_id"), field="owner_operator_id")
            if payload.get("owner_operator_id") else None
        )
    if "owner_team" in payload:
        result["owner_team"] = _optional_text(error_type, payload, "owner_team", 48)
    for field, maximum in (("impact", 1000), ("communications_summary", 2000), ("note", 2000)):
        if field in payload:
            result[field] = _optional_text(error_type, payload, field, maximum)
    for field in ("next_update_at", "ended_at"):
        if field in payload:
            result[field] = _iso_datetime(error_type, payload.get(field), field=field)
    for field in ("runbook_url", "postmortem_url"):
        if field in payload:
            result[field] = _url(error_type, payload, field)
    if "postmortem_status" in payload:
        status = str(payload.get("postmortem_status") or "").strip().lower()
        if status not in POSTMORTEM_STATUSES:
            _error(error_type, "invalid_payload", "Postmortem status is unsupported.")
        result["postmortem_status"] = status
    if set(result) == {"_environment", "_operator_id", "_actor_tg_id", "expected_version"}:
        _error(error_type, "invalid_payload", "Incident update is empty.")
    return result


def _incident_link_payload(error_type, payload: Mapping[str, Any]) -> dict[str, Any]:
    allowed = {"_environment", "_operator_id", "_actor_tg_id", "expected_version", "entity_type", "entity_id", "label"}
    _reject_extra(error_type, payload, allowed)
    operator_id, actor_tg_id = _actor(error_type, payload)
    return {
        "_environment": _environment(error_type, payload), "_operator_id": operator_id,
        "_actor_tg_id": actor_tg_id, "expected_version": _version(error_type, payload),
        "entity_type": _identifier(error_type, payload.get("entity_type"), field="entity_type", maximum=64),
        "entity_id": _identifier(error_type, payload.get("entity_id"), field="entity_id"),
        "label": _optional_text(error_type, payload, "label", 180),
    }


def _incident_state(EntityState, error_type, session, target_id, payload, for_update, *, create=False):
    incident_id = _target_uuid(error_type, target_id)
    query = session.query(ServiceIncident).filter(ServiceIncident.id == incident_id)
    row = _lock(query, session, for_update).one_or_none()
    if create:
        duplicate = session.query(ServiceIncident.id).filter(ServiceIncident.incident_key == payload["incident_key"]).first()
        if row is not None or duplicate is not None:
            _error(error_type, "target_exists", "Incident already exists.", status_code=409)
    elif row is None or str(row.environment or "production") != str(payload["_environment"]):
        _error(error_type, "target_not_found", "Incident not found.", status_code=404)
    if row is not None and not create and int(row.workflow_version or 1) != int(payload["expected_version"]):
        _error(error_type, "state_changed", "Incident version changed.", status_code=409)
    snapshot = (
        {"id": incident_id, "exists": False}
        if row is None
        else {
            "id": incident_id, "version": int(row.workflow_version or 1),
            "workflow_status": str(row.workflow_status or "investigating"), "public_status": str(row.status),
        }
    )
    return EntityState(entity=row, version_snapshot=snapshot, public_snapshot=snapshot, context={"incident_id": incident_id})


def _incident_preview(state, payload):
    change = {key: value for key, value in payload.items() if not key.startswith("_") and key != "expected_version"}
    return {
        "title": "Изменение инцидента",
        "summary": f"Incident {state.context['incident_id']} останется единым источником статуса и компенсации.",
        "before": state.public_snapshot,
        "after": change,
        "warnings": [],
        "incident_id": state.context["incident_id"],
    }


def _append_event(session, row, payload, *, event_type: str, from_status=None, note=None):
    session.add(OperatorIncidentEvent(
        id=str(uuid.uuid4()), incident_id=str(row.id), environment=str(row.environment),
        incident_version=int(row.workflow_version), event_type=event_type, from_status=from_status,
        to_status=str(row.workflow_status), note=note, actor_operator_id=payload["_operator_id"],
        actor_tg_id=int(payload["_actor_tg_id"]), created_at=_now(),
    ))


def _execute_incident_create(session, state, payload):
    now = _now()
    started_at = _to_datetime(payload["started_at"])
    if started_at is None or started_at > now:
        raise ValueError("incident_start_invalid")
    row = ServiceIncident(
        id=state.context["incident_id"], incident_key=payload["incident_key"], title=payload["title"],
        summary=payload["summary"], severity=payload["severity"], status="confirmed", started_at=started_at,
        affected_node_codes_json=json.dumps(payload["affected_node_codes"], separators=(",", ":")),
        compensation_days=int(payload["compensation_days"]), confirmed_by=int(payload["_actor_tg_id"]),
        confirmed_at=now, environment=payload["_environment"], workflow_status="investigating",
        workflow_version=1, owner_operator_id=payload["owner_operator_id"], owner_team=payload["owner_team"],
        impact=payload["impact"], next_update_at=_to_datetime(payload["next_update_at"]),
        runbook_url=payload["runbook_url"], postmortem_status="not_required", created_at=now, updated_at=now,
    )
    session.add(row)
    session.flush()
    _append_event(session, row, payload, event_type="created", note=payload["summary"])
    session.flush()
    return {"incident_id": str(row.id), "incident_version": 1, "workflow_status": "investigating"}


def _execute_incident_update(session, state, payload):
    row = state.entity
    before = str(row.workflow_status or "investigating")
    wanted = str(payload.get("workflow_status") or before)
    if before in {"resolved", "cancelled"} and wanted != before:
        raise ValueError("incident_terminal")
    ended_at = _to_datetime(payload.get("ended_at")) if "ended_at" in payload else row.ended_at
    if wanted in {"resolved", "cancelled"}:
        if ended_at is None or ended_at < row.started_at:
            raise ValueError("incident_end_invalid")
        row.ended_at = ended_at
        row.status = wanted
        if wanted == "resolved":
            row.resolved_by = int(payload["_actor_tg_id"])
            row.resolved_at = _now()
    elif "ended_at" in payload:
        raise ValueError("incident_end_requires_terminal_status")
    for field in (
        "owner_operator_id", "owner_team", "impact", "runbook_url", "communications_summary",
        "postmortem_status", "postmortem_url",
    ):
        if field in payload:
            setattr(row, field, payload[field])
    if "next_update_at" in payload:
        row.next_update_at = _to_datetime(payload["next_update_at"])
    row.workflow_status = wanted
    row.workflow_version = int(row.workflow_version or 1) + 1
    row.updated_at = _now()
    event_type = "status" if wanted != before else "note" if payload.get("note") else "updated"
    _append_event(session, row, payload, event_type=event_type, from_status=before, note=payload.get("note"))
    session.flush()
    return {"incident_id": str(row.id), "incident_version": int(row.workflow_version), "workflow_status": wanted}


def _execute_incident_link(session, state, payload):
    row = state.entity
    existed = session.query(OperatorIncidentLink).filter(
        OperatorIncidentLink.incident_id == str(row.id),
        OperatorIncidentLink.entity_type == payload["entity_type"],
        OperatorIncidentLink.entity_id == payload["entity_id"],
    ).one_or_none()
    if existed is None:
        session.add(OperatorIncidentLink(
            id=str(uuid.uuid4()), incident_id=str(row.id), environment=str(row.environment),
            entity_type=payload["entity_type"], entity_id=payload["entity_id"], label=payload["label"],
            created_by=int(payload["_actor_tg_id"]), created_at=_now(),
        ))
    row.workflow_version = int(row.workflow_version or 1) + 1
    row.updated_at = _now()
    _append_event(
        session, row, payload, event_type="link",
        note=f"{payload['entity_type']}:{payload['entity_id']}",
    )
    session.flush()
    return {"incident_id": str(row.id), "incident_version": int(row.workflow_version), "linked": True, "existing": existed is not None}


def _alert_payload(error_type, payload: Mapping[str, Any], *, mode: str) -> dict[str, Any]:
    allowed = {"_environment", "_operator_id", "_actor_tg_id", "expected_version"}
    if mode == "link":
        allowed |= {"incident_id", "expected_incident_version"}
    _reject_extra(error_type, payload, allowed)
    operator_id, actor_tg_id = _actor(error_type, payload)
    result = {
        "_environment": _environment(error_type, payload), "_operator_id": operator_id,
        "_actor_tg_id": actor_tg_id, "expected_version": _version(error_type, payload),
    }
    if mode == "link":
        result["incident_id"] = _uuid(error_type, payload.get("incident_id"), field="incident_id")
        result["expected_incident_version"] = _version(error_type, payload, "expected_incident_version")
    return result


def _alert_create_incident_payload(error_type, payload: Mapping[str, Any]) -> dict[str, Any]:
    base = _incident_create_payload(error_type, payload)
    return base


def _alert_silence_payload(error_type, payload: Mapping[str, Any]) -> dict[str, Any]:
    allowed = {
        "_environment",
        "_operator_id",
        "_actor_tg_id",
        "expected_version",
        "minutes",
    }
    _reject_extra(error_type, payload, allowed)
    result = _alert_payload(
        error_type,
        {key: value for key, value in payload.items() if key != "minutes"},
        mode="ack",
    )
    try:
        minutes = int(payload.get("minutes"))
    except (TypeError, ValueError):
        _error(error_type, "invalid_payload", "Silence duration is invalid.")
    if not 1 <= minutes <= 1440:
        _error(error_type, "invalid_payload", "Silence duration is invalid.")
    result["minutes"] = minutes
    return result


def _alert_state(EntityState, error_type, session, target_id, payload, for_update, *, link=False):
    try:
        alert_id = int(target_id)
    except (TypeError, ValueError):
        _error(error_type, "invalid_target", "Alert id is invalid.")
    query = session.query(OpsAlert).filter(OpsAlert.id == alert_id)
    alert = _lock(query, session, for_update).one_or_none()
    if alert is None or str(alert.environment or "production") != str(payload["_environment"]):
        _error(error_type, "target_not_found", "Alert not found.", status_code=404)
    expected = int(payload.get("expected_version") or 0)
    if expected and int(alert.version or 1) != expected:
        _error(error_type, "state_changed", "Alert version changed.", status_code=409)
    incident = None
    if link:
        query = session.query(ServiceIncident).filter(
            ServiceIncident.id == payload["incident_id"],
            ServiceIncident.environment == payload["_environment"],
        )
        incident = _lock(query, session, for_update).one_or_none()
        if incident is None:
            _error(error_type, "target_not_found", "Incident not found.", status_code=404)
        if int(incident.workflow_version or 1) != int(payload["expected_incident_version"]):
            _error(error_type, "state_changed", "Incident version changed.", status_code=409)
    snapshot = {
        "alert_id": alert_id, "alert_version": int(alert.version or 1), "alert_status": str(alert.status),
        "incident_id": str(alert.incident_id) if alert.incident_id else None,
    }
    if incident is not None:
        snapshot["target_incident_version"] = int(incident.workflow_version or 1)
    return EntityState(entity=alert, version_snapshot=snapshot, public_snapshot=snapshot, context={"alert_id": alert_id, "incident": incident})


def _alert_preview(state, payload):
    change = {key: value for key, value in payload.items() if not key.startswith("_") and not key.startswith("expected_")}
    return {
        "title": "Переход алерта",
        "summary": f"Алерт {state.context['alert_id']} будет изменён только при совпадении версии.",
        "before": state.public_snapshot,
        "after": change,
        "warnings": [],
    }


def _execute_alert_ack(session, state, payload):
    alert = state.entity
    if str(alert.status) == "false_positive":
        raise ValueError("false_positive_alert_cannot_be_acknowledged")
    alert.status = "acknowledged"
    alert.acknowledged_at = alert.acknowledged_at or _now()
    alert.acknowledged_by = int(payload["_actor_tg_id"])
    alert.version = int(alert.version or 1) + 1
    alert.updated_at = _now()
    session.flush()
    return {"alert_id": int(alert.id), "alert_version": int(alert.version), "alert_status": str(alert.status)}


def _execute_alert_false_positive(session, state, payload):
    alert = state.entity
    if alert.incident_id:
        raise ValueError("linked_alert_cannot_be_false_positive")
    alert.status = "false_positive"
    alert.resolved_at = _now()
    alert.acknowledged_at = alert.acknowledged_at or _now()
    alert.acknowledged_by = int(payload["_actor_tg_id"])
    alert.version = int(alert.version or 1) + 1
    alert.updated_at = _now()
    session.flush()
    return {"alert_id": int(alert.id), "alert_version": int(alert.version), "alert_status": "false_positive"}


def _execute_alert_silence(session, state, payload):
    alert = state.entity
    if str(alert.status) in {"resolved", "false_positive"}:
        raise ValueError("closed_alert_cannot_be_silenced")
    alert.silence_until = _now() + timedelta(minutes=int(payload["minutes"]))
    alert.acknowledged_at = alert.acknowledged_at or _now()
    alert.acknowledged_by = int(payload["_actor_tg_id"])
    alert.version = int(alert.version or 1) + 1
    alert.updated_at = _now()
    session.flush()
    return {
        "alert_id": int(alert.id),
        "alert_version": int(alert.version),
        "alert_status": "silenced",
        "silence_until": alert.silence_until.isoformat() + "Z",
    }


def _execute_alert_link(session, state, payload):
    alert = state.entity
    incident = state.context["incident"]
    if alert.incident_id and str(alert.incident_id) != str(incident.id):
        raise ValueError("alert_already_linked")
    alert.incident_id = str(incident.id)
    alert.version = int(alert.version or 1) + 1
    alert.updated_at = _now()
    incident.workflow_version = int(incident.workflow_version or 1) + 1
    incident.updated_at = _now()
    _append_event(session, incident, payload, event_type="alert_link", note=f"alert:{alert.id}")
    session.flush()
    return {
        "alert_id": int(alert.id), "alert_version": int(alert.version),
        "incident_id": str(incident.id), "incident_version": int(incident.workflow_version),
    }


def _alert_create_state(EntityState, error_type, session, target_id, payload, for_update):
    state = _alert_state(EntityState, error_type, session, target_id, {**payload, "expected_version": payload.get("expected_version", 1)}, for_update)
    incident_id = _uuid(error_type, payload.get("incident_id"), field="incident_id")
    duplicate = session.query(ServiceIncident.id).filter(
        (ServiceIncident.id == incident_id) | (ServiceIncident.incident_key == payload["incident_key"])
    ).first()
    if duplicate is not None or state.entity.incident_id:
        _error(error_type, "target_exists", "Alert already has an incident or incident exists.", status_code=409)
    state.context["incident_id"] = incident_id
    return state


def _execute_alert_create_incident(session, state, payload):
    incident_state = type(state)(
        entity=None,
        version_snapshot={"id": state.context["incident_id"], "exists": False},
        public_snapshot={"id": state.context["incident_id"], "exists": False},
        context={"incident_id": state.context["incident_id"]},
    )
    result = _execute_incident_create(session, incident_state, payload)
    alert = state.entity
    alert.incident_id = state.context["incident_id"]
    alert.version = int(alert.version or 1) + 1
    alert.updated_at = _now()
    session.flush()
    return {**result, "alert_id": int(alert.id), "alert_version": int(alert.version)}


def _compensation_payload(error_type, payload: Mapping[str, Any]) -> dict[str, Any]:
    allowed = {"_environment", "_operator_id", "_actor_tg_id", "expected_version"}
    _reject_extra(error_type, payload, allowed)
    operator_id, actor_tg_id = _actor(error_type, payload)
    return {
        "_environment": _environment(error_type, payload), "_operator_id": operator_id,
        "_actor_tg_id": actor_tg_id, "expected_version": _version(error_type, payload),
    }


def _compensation_state(EntityState, error_type, session, target_id, payload, for_update):
    state = _incident_state(EntityState, error_type, session, target_id, payload, for_update)
    try:
        preview = incident_service.preview_incident_compensation(session, incident=state.entity)
    except ValueError as exc:
        _error(error_type, "incident_not_compensable", str(exc), status_code=409)
    state.context["compensation_preview"] = preview
    return state


def _compensation_preview(state, _payload):
    preview = state.context["compensation_preview"]
    return {
        "title": "Компенсация по инциденту",
        "summary": "Получатели зафиксированы сервером; повторное выполнение не создаёт второй grant.",
        "before": {
            "incident_key": preview.incident_key,
            "compensation_completed": state.entity.compensation_completed_at is not None,
        },
        "after": {
            "impacted_accounts": preview.impacted_accounts,
            "compensation_days": preview.compensation_days,
        },
        "warnings": ["Команда выдаёт entitlement grants и требует свежий step-up."],
        "incident_id": preview.incident_id, "incident_key": preview.incident_key,
        "impacted_accounts": preview.impacted_accounts, "compensation_days": preview.compensation_days,
        "already_completed": state.entity.compensation_completed_at is not None,
    }


def _execute_compensation(session, state, payload):
    result = incident_service.apply_incident_compensation(session, incident_id=str(state.entity.id), now=_now())
    row = state.entity
    row.workflow_version = int(row.workflow_version or 1) + 1
    row.updated_at = _now()
    _append_event(
        session, row, payload, event_type="compensation",
        note=f"granted={result.granted_accounts};existing={result.existing_grants}",
    )
    session.flush()
    return {
        "incident_id": result.incident_id, "incident_version": int(row.workflow_version),
        "impacted_accounts": result.impacted_accounts, "granted_accounts": result.granted_accounts,
        "existing_grants": result.existing_grants, "compensation_days": result.compensation_days,
    }


def build_operator_action_policies(*, ActionPolicy, EntityState, ActionIntentError) -> dict[str, Any]:
    task_create = lambda payload: _task_create_payload(ActionIntentError, payload)
    task_update = lambda payload: _task_update_payload(ActionIntentError, payload)
    incident_create = lambda payload: _incident_create_payload(ActionIntentError, payload)
    incident_update = lambda payload: _incident_update_payload(ActionIntentError, payload)
    incident_link = lambda payload: _incident_link_payload(ActionIntentError, payload)
    alert_ack = lambda payload: _alert_payload(ActionIntentError, payload, mode="ack")
    alert_silence = lambda payload: _alert_silence_payload(ActionIntentError, payload)
    alert_link = lambda payload: _alert_payload(ActionIntentError, payload, mode="link")
    compensate = lambda payload: _compensation_payload(ActionIntentError, payload)
    l2 = lambda _state, _payload: "ПОДТВЕРДИТЬ"

    def guarded(executor):
        def run(session, state, payload):
            try:
                return executor(session, state, payload)
            except ValueError as exc:
                _error(
                    ActionIntentError,
                    "domain_transition_rejected",
                    str(exc),
                    status_code=409,
                )

        return run

    policies = {
        "operator_task.create": ActionPolicy(
            action="operator_task.create", target_type="operator_task", risk_level="L2",
            payload_normalizer=task_create,
            entity_state_builder=lambda s, t, p, f: _task_state(EntityState, ActionIntentError, s, t, p, f, create=True),
            preview_builder=_task_preview, challenge_kind="exact_phrase", challenge_builder=l2,
            executor_kind="db", audit_action="operator_task.create", db_executor=guarded(_execute_task_create),
        ),
        "operator_task.update": ActionPolicy(
            action="operator_task.update", target_type="operator_task", risk_level="L2",
            payload_normalizer=task_update,
            entity_state_builder=lambda s, t, p, f: _task_state(EntityState, ActionIntentError, s, t, p, f, create=False),
            preview_builder=_task_preview, challenge_kind="exact_phrase", challenge_builder=l2,
            executor_kind="db", audit_action="operator_task.update", db_executor=guarded(_execute_task_update),
        ),
        "incident.create": ActionPolicy(
            action="incident.create", target_type="incident", risk_level="L2",
            payload_normalizer=incident_create,
            entity_state_builder=lambda s, t, p, f: _incident_state(EntityState, ActionIntentError, s, t, p, f, create=True),
            preview_builder=_incident_preview, challenge_kind="exact_phrase", challenge_builder=l2,
            executor_kind="db", audit_action="incident.create", db_executor=guarded(_execute_incident_create),
        ),
        "incident.update": ActionPolicy(
            action="incident.update", target_type="incident", risk_level="L2",
            payload_normalizer=incident_update,
            entity_state_builder=lambda s, t, p, f: _incident_state(EntityState, ActionIntentError, s, t, p, f),
            preview_builder=_incident_preview, challenge_kind="exact_phrase", challenge_builder=l2,
            executor_kind="db", audit_action="incident.update", db_executor=guarded(_execute_incident_update),
        ),
        "incident.link": ActionPolicy(
            action="incident.link", target_type="incident", risk_level="L2",
            payload_normalizer=incident_link,
            entity_state_builder=lambda s, t, p, f: _incident_state(EntityState, ActionIntentError, s, t, p, f),
            preview_builder=_incident_preview, challenge_kind="exact_phrase", challenge_builder=l2,
            executor_kind="db", audit_action="incident.link", db_executor=guarded(_execute_incident_link),
        ),
        "alert.ack": ActionPolicy(
            action="alert.ack", target_type="alert", risk_level="L2", payload_normalizer=alert_ack,
            entity_state_builder=lambda s, t, p, f: _alert_state(EntityState, ActionIntentError, s, t, p, f),
            preview_builder=_alert_preview, challenge_kind="exact_phrase", challenge_builder=l2,
            executor_kind="db", audit_action="alert.ack", db_executor=guarded(_execute_alert_ack),
        ),
        "alert.false_positive": ActionPolicy(
            action="alert.false_positive", target_type="alert", risk_level="L2", payload_normalizer=alert_ack,
            entity_state_builder=lambda s, t, p, f: _alert_state(EntityState, ActionIntentError, s, t, p, f),
            preview_builder=_alert_preview, challenge_kind="exact_phrase", challenge_builder=l2,
            executor_kind="db", audit_action="alert.false_positive", db_executor=guarded(_execute_alert_false_positive),
        ),
        "alert.silence": ActionPolicy(
            action="alert.silence", target_type="alert", risk_level="L2", payload_normalizer=alert_silence,
            entity_state_builder=lambda s, t, p, f: _alert_state(EntityState, ActionIntentError, s, t, p, f),
            preview_builder=_alert_preview, challenge_kind="exact_phrase", challenge_builder=l2,
            executor_kind="db", audit_action="alert.silence", db_executor=guarded(_execute_alert_silence),
        ),
        "alert.link_incident": ActionPolicy(
            action="alert.link_incident", target_type="alert", risk_level="L2", payload_normalizer=alert_link,
            entity_state_builder=lambda s, t, p, f: _alert_state(EntityState, ActionIntentError, s, t, p, f, link=True),
            preview_builder=_alert_preview, challenge_kind="exact_phrase", challenge_builder=l2,
            executor_kind="db", audit_action="alert.link_incident", db_executor=guarded(_execute_alert_link),
        ),
        "incident.compensate": ActionPolicy(
            action="incident.compensate", target_type="incident", risk_level="L3", payload_normalizer=compensate,
            entity_state_builder=lambda s, t, p, f: _compensation_state(EntityState, ActionIntentError, s, t, p, f),
            preview_builder=_compensation_preview, challenge_kind="exact_incident_key",
            challenge_builder=lambda state, _payload: str(state.entity.incident_key),
            executor_kind="db", audit_action="incident.compensate", db_executor=guarded(_execute_compensation),
        ),
    }

    # Alert -> incident needs an alert version plus the incident creation fields.
    create_allowed = {
        "_environment", "_operator_id", "_actor_tg_id", "expected_version", "incident_id",
        "incident_key", "title", "summary", "severity", "started_at", "affected_node_codes",
        "compensation_days", "owner_operator_id", "owner_team", "impact", "next_update_at", "runbook_url",
    }

    def normalize_alert_create(payload):
        _reject_extra(ActionIntentError, payload, create_allowed)
        base = _incident_create_payload(
            ActionIntentError,
            {key: value for key, value in payload.items() if key not in {"expected_version", "incident_id"}},
        )
        base["expected_version"] = _version(ActionIntentError, payload)
        base["incident_id"] = _uuid(ActionIntentError, payload.get("incident_id"), field="incident_id")
        return base

    policies["alert.create_incident"] = ActionPolicy(
        action="alert.create_incident", target_type="alert", risk_level="L2",
        payload_normalizer=normalize_alert_create,
        entity_state_builder=lambda s, t, p, f: _alert_create_state(EntityState, ActionIntentError, s, t, p, f),
        preview_builder=_alert_preview, challenge_kind="exact_phrase", challenge_builder=l2,
        executor_kind="db", audit_action="alert.create_incident", db_executor=guarded(_execute_alert_create_incident),
    )
    return policies


__all__ = [
    "INCIDENT_SEVERITIES",
    "INCIDENT_STATUSES",
    "POSTMORTEM_STATUSES",
    "TASK_PRIORITIES",
    "TASK_STATUSES",
    "build_operator_action_policies",
]
