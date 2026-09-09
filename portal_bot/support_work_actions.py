"""Guarded action-intent policies for the server-owned Support Inbox."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Mapping

try:
    from .models import ServiceIncident, SupportBundleUpload, SupportModePolicy, SupportTicket, SupportTicketMessage
    from . import support_mode_service
    from .support_work_service import TICKET_PRIORITIES, TICKET_QUEUES, TICKET_WAITING_ON, attempt_explorer, support_bundle_upload_id_for_ref, ticket_view
except ImportError:
    from models import ServiceIncident, SupportBundleUpload, SupportModePolicy, SupportTicket, SupportTicketMessage
    import support_mode_service
    from support_work_service import TICKET_PRIORITIES, TICKET_QUEUES, TICKET_WAITING_ON, attempt_explorer, support_bundle_upload_id_for_ref, ticket_view


_ENV_RE = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
_ATTEMPT_RE = re.compile(r"^attempt_[0-9a-f]{20}$")
_MACRO_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,47}$")


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def _error(error_type, code: str, message: str, *, status_code: int = 422):
    raise error_type(code, status_code=status_code, message=message)


def _reject_extra(error_type, payload: Mapping[str, Any], allowed: set[str]) -> None:
    extra = sorted(set(payload) - allowed)
    if extra:
        _error(error_type, "invalid_payload", f"Unsupported payload fields: {', '.join(extra)}")


def _base(error_type, payload: Mapping[str, Any]) -> dict[str, Any]:
    environment = str(payload.get("_environment") or "").strip().lower()
    if _ENV_RE.fullmatch(environment) is None:
        _error(error_type, "invalid_payload", "Operator environment is invalid.")
    operator_id = str(payload.get("_operator_id") or "").strip().lower()
    if _UUID_RE.fullmatch(operator_id) is None:
        _error(error_type, "invalid_payload", "Operator id is invalid.")
    try:
        actor_tg_id = int(payload.get("_actor_tg_id"))
        expected_version = int(payload.get("expected_version"))
    except (TypeError, ValueError):
        _error(error_type, "invalid_payload", "Actor or ticket version is invalid.")
    if actor_tg_id <= 0 or expected_version < 1:
        _error(error_type, "invalid_payload", "Actor or ticket version is invalid.")
    return {
        "_environment": environment,
        "_operator_id": operator_id,
        "_actor_tg_id": actor_tg_id,
        "expected_version": expected_version,
    }


def _text(error_type, value: object, field: str, maximum: int, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    normalized = " ".join(str(value or "").strip().split())
    if not normalized or len(normalized) > maximum or any(ord(char) < 32 for char in normalized):
        _error(error_type, "invalid_payload", f"Field {field} is invalid.")
    return normalized


def _claim_payload(error_type, payload: Mapping[str, Any]) -> dict[str, Any]:
    allowed = {"_environment", "_operator_id", "_actor_tg_id", "expected_version"}
    _reject_extra(error_type, payload, allowed)
    return _base(error_type, payload)


def _assign_payload(error_type, payload: Mapping[str, Any]) -> dict[str, Any]:
    allowed = {"_environment", "_operator_id", "_actor_tg_id", "expected_version", "assignee_admin_tg_id", "assigned_team"}
    _reject_extra(error_type, payload, allowed)
    out = _base(error_type, payload)
    assignee = payload.get("assignee_admin_tg_id")
    if assignee is None:
        out["assignee_admin_tg_id"] = None
    else:
        try:
            parsed = int(assignee)
        except (TypeError, ValueError):
            _error(error_type, "invalid_payload", "Assignee is invalid.")
        if parsed <= 0:
            _error(error_type, "invalid_payload", "Assignee is invalid.")
        out["assignee_admin_tg_id"] = parsed
    out["assigned_team"] = _text(error_type, payload.get("assigned_team"), "assigned_team", 48, nullable=True)
    return out


def _parse_time(error_type, value: object, field: str) -> str | None:
    if value is None:
        return None
    normalized = str(value or "").strip()
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError:
        _error(error_type, "invalid_payload", f"Field {field} must be RFC3339.")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _update_payload(error_type, payload: Mapping[str, Any]) -> dict[str, Any]:
    allowed = {
        "_environment", "_operator_id", "_actor_tg_id", "expected_version",
        "priority", "queue", "waiting_on", "sla_due_at", "escalated",
        "incident_id", "attempt_ref", "status", "bundle_ref",
    }
    _reject_extra(error_type, payload, allowed)
    out = _base(error_type, payload)
    changed = False
    if "bundle_ref" in payload:
        bundle_ref = str(payload.get("bundle_ref") or "").strip().lower()
        if re.fullmatch(r"bundle_[0-9a-f]{20}", bundle_ref) is None or "attempt_ref" not in payload:
            _error(error_type, "invalid_payload", "Bundle link requires a bundle and attempt reference.")
        _reject_extra(error_type, payload, {
            "_environment", "_operator_id", "_actor_tg_id", "expected_version", "bundle_ref", "attempt_ref",
        })
        out["bundle_ref"] = bundle_ref
    if "priority" in payload:
        value = str(payload.get("priority") or "").strip().lower()
        if value not in TICKET_PRIORITIES:
            _error(error_type, "invalid_payload", "Ticket priority is invalid.")
        out["priority"] = value
        changed = True
    if "queue" in payload:
        value = str(payload.get("queue") or "").strip().lower()
        if value not in TICKET_QUEUES:
            _error(error_type, "invalid_payload", "Ticket queue is invalid.")
        out["queue"] = value
        changed = True
    if "waiting_on" in payload:
        value = payload.get("waiting_on")
        normalized = None if value is None else str(value or "").strip().lower()
        if normalized is not None and normalized not in TICKET_WAITING_ON:
            _error(error_type, "invalid_payload", "Waiting state is invalid.")
        out["waiting_on"] = normalized
        changed = True
    if "sla_due_at" in payload:
        out["sla_due_at"] = _parse_time(error_type, payload.get("sla_due_at"), "sla_due_at")
        changed = True
    if "escalated" in payload:
        if type(payload.get("escalated")) is not bool:
            _error(error_type, "invalid_payload", "Escalated must be boolean.")
        out["escalated"] = bool(payload["escalated"])
        changed = True
    if "incident_id" in payload:
        value = payload.get("incident_id")
        normalized = None if value is None else str(value or "").strip().lower()
        if normalized is not None and _UUID_RE.fullmatch(normalized) is None:
            _error(error_type, "invalid_payload", "Incident id is invalid.")
        out["incident_id"] = normalized
        changed = True
    if "attempt_ref" in payload:
        value = payload.get("attempt_ref")
        normalized = None if value is None else str(value or "").strip().lower()
        if normalized is not None and _ATTEMPT_RE.fullmatch(normalized) is None:
            _error(error_type, "invalid_payload", "Attempt reference is invalid.")
        out["attempt_ref"] = normalized
        changed = True
    if "status" in payload:
        value = str(payload.get("status") or "").strip().lower()
        if value not in {"open", "in_progress", "closed"}:
            _error(error_type, "invalid_payload", "Ticket status is invalid.")
        out["status"] = value
        changed = True
    if not changed:
        _error(error_type, "invalid_payload", "At least one ticket field must change.")
    return out


def _note_runtime(error_type, payload: Mapping[str, Any]) -> dict[str, Any]:
    allowed = {"_environment", "_operator_id", "_actor_tg_id", "expected_version", "body", "macro_code"}
    _reject_extra(error_type, payload, allowed)
    try:
        expected_version = int(payload.get("expected_version"))
    except (TypeError, ValueError):
        _error(error_type, "invalid_payload", "Ticket version is invalid.")
    if expected_version < 1:
        _error(error_type, "invalid_payload", "Ticket version is invalid.")
    out: dict[str, Any] = {"expected_version": expected_version}
    if payload.get("_environment") is not None:
        out.update(_base(error_type, payload))
    body = str(payload.get("body") or "").strip()
    if not 1 <= len(body) <= 2000:
        _error(error_type, "invalid_payload", "Internal note body is invalid.")
    macro = str(payload.get("macro_code") or "").strip().lower()
    if macro and _MACRO_RE.fullmatch(macro) is None:
        _error(error_type, "invalid_payload", "Macro code is invalid.")
    out.update({"body": body, "macro_code": macro or None})
    return out


def _note_payload(error_type, payload: Mapping[str, Any]) -> dict[str, Any]:
    runtime = _note_runtime(error_type, payload)
    body = str(runtime.pop("body"))
    runtime["body"] = {
        "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "length": len(body),
    }
    return runtime


def _support_mode_payload(error_type, payload: Mapping[str, Any]) -> dict[str, Any]:
    issue_fields = {
        "allowed_categories",
        "allowed_collectors",
        "app_version",
        "build_number",
        "maximum_bundle_bytes",
        "maximum_bundles",
        "maximum_total_bytes",
        "platform",
        "ttl_minutes",
    }
    _reject_extra(
        error_type,
        payload,
        {"_environment", "_operator_id", "_actor_tg_id", "expected_version"} | issue_fields,
    )
    base = _base(error_type, payload)
    try:
        spec = support_mode_service.normalize_issue_spec(
            {field: payload.get(field) for field in issue_fields}
        )
    except support_mode_service.SupportModeError as error:
        _error(
            error_type,
            error.code,
            "Параметры временного режима поддержки недействительны.",
            status_code=error.status_code,
        )
    return {
        **base,
        "allowed_categories": list(spec.allowed_categories),
        "allowed_collectors": list(spec.allowed_collectors),
        "app_version": spec.app_version,
        "build_number": spec.build_number,
        "maximum_bundle_bytes": spec.maximum_bundle_bytes,
        "maximum_bundles": spec.maximum_bundles,
        "maximum_total_bytes": spec.maximum_total_bytes,
        "platform": spec.platform,
        "ttl_minutes": spec.ttl_minutes,
    }


def _ticket_state(EntityState, error_type, session, target_id, payload, for_update):
    try:
        ticket_id = int(str(target_id))
    except (TypeError, ValueError):
        _error(error_type, "invalid_target", "Ticket id is invalid.")
    query = session.query(SupportTicket).filter(SupportTicket.id == ticket_id)
    if for_update and str(session.get_bind().dialect.name) == "postgresql":
        query = query.with_for_update()
    row = query.first()
    if row is None:
        _error(error_type, "target_not_found", "Ticket not found.", status_code=404)
    if payload.get("_environment") is not None and str(row.environment or "production") != str(payload["_environment"]):
        _error(error_type, "target_not_found", "Ticket not found.", status_code=404)
    current_version = max(1, int(row.version or 1))
    if current_version != int(payload["expected_version"]):
        _error(error_type, "stale_version", "Ticket changed; reload it before continuing.", status_code=409)
    context = {"ticket_id": ticket_id, "actor_tg_id": int(payload.get("_actor_tg_id") or 0)}
    bundle_snapshot = {}
    if payload.get("attempt_ref"):
        explored = attempt_explorer(session, environment=row.environment, ticket_id=ticket_id,
                                    attempt_ref=payload["attempt_ref"])
        if not explored or explored["selected"] is None:
            _error(error_type, "attempt_not_found", "Attempt is not available for this ticket.", status_code=404)
    if "bundle_ref" in payload:
        upload_id = support_bundle_upload_id_for_ref(session, environment=row.environment,
                                                     ticket_id=ticket_id, bundle_ref=payload["bundle_ref"])
        if upload_id is None:
            _error(error_type, "support_bundle_not_found", "Bundle is not available for this ticket.", status_code=404)
        context["bundle_upload_id"] = upload_id
        bundle = session.query(SupportBundleUpload).filter_by(upload_id=upload_id).one()
        bundle_snapshot = {"bundle": {"bundle_ref": payload["bundle_ref"], "attempt_ref": bundle.attempt_ref}}
    message_count = session.query(SupportTicketMessage.id).filter(SupportTicketMessage.ticket_id == ticket_id).count()
    return EntityState(
        entity=row,
        version_snapshot={"ticket_id": ticket_id, "version": current_version, "updated_at": str(row.updated_at), "messages": int(message_count), **bundle_snapshot},
        public_snapshot={**ticket_view(row), "message_count": int(message_count), **bundle_snapshot},
        context=context,
    )


def _preview(title: str, state, after: Mapping[str, Any], warnings: list[str] | None = None) -> dict[str, Any]:
    return {
        "title": title,
        "summary": "Server version and assignment are checked again at execution.",
        "before": state.public_snapshot,
        "after": dict(after),
        "warnings": list(warnings or []),
    }


def _claim_preview(state, payload):
    return _preview("Взять тикет в работу", state, {**state.public_snapshot, "assigned_admin_tg_id": payload["_actor_tg_id"], "status": "in_progress"})


def _assign_preview(state, payload):
    return _preview("Изменить назначение тикета", state, {**state.public_snapshot, "assigned_admin_tg_id": payload["assignee_admin_tg_id"], "assigned_team": payload["assigned_team"]})


def _update_preview(state, payload):
    after = dict(state.public_snapshot)
    if "bundle_ref" in payload:
        after["bundle"] = {"bundle_ref": payload["bundle_ref"], "attempt_ref": payload["attempt_ref"]}
        return _preview("Связать пакет поддержки с попыткой", state, after,
                        ["Связь указана оператором; она не подтверждает содержимое зашифрованного пакета."])
    after.update({key: value for key, value in payload.items() if not key.startswith("_") and key != "expected_version"})
    return _preview("Обновить операционный контекст тикета", state, after)


def _note_preview(state, payload):
    return _preview(
        "Добавить внутреннюю заметку",
        state,
        {**state.public_snapshot, "internal_note_length": int(payload["body"]["length"])},
        ["Текст заметки не сохраняется в intent или audit и не отправляется пользователю."],
    )


def _support_mode_preview(state, payload):
    return _preview(
        "Выдать одноразовый код временного режима поддержки",
        state,
        {
            **state.public_snapshot,
            "support_mode": {
                "platform": payload["platform"],
                "app_version": payload["app_version"],
                "build_number": payload["build_number"],
                "ttl_minutes": payload["ttl_minutes"],
                "allowed_categories": payload["allowed_categories"],
                "allowed_collectors": payload["allowed_collectors"],
                "maximum_bundle_bytes": payload["maximum_bundle_bytes"],
                "maximum_total_bytes": payload["maximum_total_bytes"],
                "maximum_bundles": payload["maximum_bundles"],
            },
        },
        [
            "Код одноразовый; клиент сверит подпись, сборку, платформу, TTL и nonce.",
            "Политика разрешает только закрытый список диагностических коллекторов и не содержит команд.",
        ],
    )


def _bump(row: SupportTicket) -> None:
    row.version = max(1, int(row.version or 1)) + 1
    row.updated_at = _now()


def _execute_claim(session, state, payload):
    row = state.entity
    actor = int(payload["_actor_tg_id"])
    if row.assigned_admin_tg_id not in {None, actor}:
        raise ValueError("ticket is already assigned to another operator")
    row.assigned_admin_tg_id = actor
    row.status = "in_progress"
    row.waiting_on = None
    _bump(row)
    session.flush()
    return {"ticket": ticket_view(row)}


def _execute_assign(session, state, payload):
    row = state.entity
    row.assigned_admin_tg_id = payload["assignee_admin_tg_id"]
    row.assigned_team = payload["assigned_team"]
    _bump(row)
    session.flush()
    return {"ticket": ticket_view(row)}


def _execute_update(session, state, payload):
    row = state.entity
    if "bundle_ref" in payload:
        bundle = session.query(SupportBundleUpload).filter_by(upload_id=state.context["bundle_upload_id"]).one()
        bundle.attempt_ref = payload["attempt_ref"]
        bundle.updated_at = _now()
        _bump(row)
        session.flush()
        return {"ticket": ticket_view(row), "bundle_ref": payload["bundle_ref"],
                "attempt_ref": bundle.attempt_ref, "attempt_link_source": "operator" if bundle.attempt_ref else None}
    if payload.get("incident_id"):
        incident = session.query(ServiceIncident).filter(
            ServiceIncident.id == payload["incident_id"],
            ServiceIncident.environment == row.environment,
        ).first()
        if incident is None:
            raise ValueError("incident is not available in this environment")
    for field in ("priority", "queue", "waiting_on", "incident_id", "attempt_ref", "status"):
        if field in payload:
            setattr(row, field, payload[field])
    if "sla_due_at" in payload:
        value = payload["sla_due_at"]
        row.sla_due_at = None if value is None else datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)
    if "escalated" in payload:
        row.escalated_at = _now() if payload["escalated"] else None
    if payload.get("status") == "closed":
        row.closed_at = _now()
    elif "status" in payload:
        row.closed_at = None
    _bump(row)
    session.flush()
    return {"ticket": ticket_view(row)}


def _execute_support_mode_issue(session, state, payload):
    spec = support_mode_service.normalize_issue_spec(
        {
            key: payload[key]
            for key in (
                "allowed_categories",
                "allowed_collectors",
                "app_version",
                "build_number",
                "maximum_bundle_bytes",
                "maximum_bundles",
                "maximum_total_bytes",
                "platform",
                "ttl_minutes",
            )
        }
    )
    issued = support_mode_service.issue_support_mode(
        session,
        ticket=state.entity,
        spec=spec,
        actor_tg_id=int(payload["_actor_tg_id"]),
    )
    return {
        "support_mode": support_mode_service.support_mode_public_view(issued.row),
        "activation_code": issued.activation_code,
    }


def _sanitize_support_mode_result(result):
    sanitized = dict(result)
    sanitized["activation_code"] = None
    return sanitized


def _replay_support_mode_result(session, _intent, stored):
    result = dict(stored)
    support_mode = result.get("support_mode")
    policy_id = str(support_mode.get("policy_id") or "") if isinstance(support_mode, Mapping) else ""
    row = session.query(SupportModePolicy).filter(SupportModePolicy.policy_id == policy_id).one_or_none()
    if row is None or str(row.status) != "issued" or row.expires_at <= _now():
        result["activation_code"] = None
        return result
    try:
        result["activation_code"] = support_mode_service.activation_code_for_policy_id(policy_id)
    except support_mode_service.SupportModeError:
        result["activation_code"] = None
    return result


def _note_external_context(state, payload):
    return {
        "ticket_id": int(state.context["ticket_id"]),
        "expected_version": int(payload["expected_version"]),
    }


def _audit_meta(state, payload):
    result = {
        "ticket_id": int(state.context["ticket_id"]),
        "expected_version": int(payload["expected_version"]),
    }
    for key in ("priority", "queue", "waiting_on", "incident_id", "attempt_ref", "bundle_ref", "status", "assignee_admin_tg_id", "assigned_team", "escalated"):
        if key in payload:
            result[key] = payload[key]
    if isinstance(payload.get("body"), Mapping):
        result["body_sha256"] = str(payload["body"].get("sha256") or "")
        result["body_length"] = int(payload["body"].get("length") or 0)
    if payload.get("macro_code"):
        result["macro_code"] = payload["macro_code"]
    if "ttl_minutes" in payload:
        result["support_mode"] = {
            "platform": payload["platform"],
            "app_version": payload["app_version"],
            "build_number": payload["build_number"],
            "ttl_minutes": payload["ttl_minutes"],
            "maximum_bundle_bytes": payload["maximum_bundle_bytes"],
            "maximum_total_bytes": payload["maximum_total_bytes"],
            "maximum_bundles": payload["maximum_bundles"],
            "allowed_categories": payload["allowed_categories"],
            "allowed_collectors": payload["allowed_collectors"],
        }
    return result


def build_support_action_policies(*, ActionPolicy, EntityState, ActionIntentError) -> dict[str, Any]:
    l2 = lambda _state, _payload: "ПОДТВЕРДИТЬ"

    def guarded(executor):
        def run(session, state, payload):
            try:
                return executor(session, state, payload)
            except ValueError as exc:
                _error(ActionIntentError, "domain_transition_rejected", str(exc), status_code=409)
        return run

    def issue_support_mode(session, state, payload):
        try:
            return _execute_support_mode_issue(session, state, payload)
        except support_mode_service.SupportModeError as error:
            _error(
                ActionIntentError,
                error.code,
                "Подписанная политика временного режима поддержки недоступна.",
                status_code=error.status_code,
            )

    state = lambda s, t, p, f: _ticket_state(EntityState, ActionIntentError, s, t, p, f)
    return {
        "ticket.claim": ActionPolicy(
            action="ticket.claim", target_type="ticket", risk_level="L2",
            payload_normalizer=lambda p: _claim_payload(ActionIntentError, p), entity_state_builder=state,
            preview_builder=_claim_preview, challenge_kind="exact_phrase", challenge_builder=l2,
            executor_kind="db", audit_action="ticket.claim", db_executor=guarded(_execute_claim), audit_meta_builder=_audit_meta,
        ),
        "ticket.assign": ActionPolicy(
            action="ticket.assign", target_type="ticket", risk_level="L2",
            payload_normalizer=lambda p: _assign_payload(ActionIntentError, p), entity_state_builder=state,
            preview_builder=_assign_preview, challenge_kind="exact_phrase", challenge_builder=l2,
            executor_kind="db", audit_action="ticket.assign", db_executor=guarded(_execute_assign), audit_meta_builder=_audit_meta,
        ),
        "ticket.update": ActionPolicy(
            action="ticket.update", target_type="ticket", risk_level="L2",
            payload_normalizer=lambda p: _update_payload(ActionIntentError, p), entity_state_builder=state,
            preview_builder=_update_preview, challenge_kind="exact_phrase", challenge_builder=l2,
            executor_kind="db", audit_action="ticket.update", db_executor=guarded(_execute_update), audit_meta_builder=_audit_meta,
        ),
        "ticket.note": ActionPolicy(
            action="ticket.note", target_type="ticket", risk_level="L2",
            payload_normalizer=lambda p: _note_payload(ActionIntentError, p),
            runtime_payload_normalizer=lambda p: _note_runtime(ActionIntentError, p),
            entity_state_builder=state, preview_builder=_note_preview,
            challenge_kind="exact_phrase", challenge_builder=l2,
            executor_kind="external", audit_action="ticket.note",
            external_context_builder=_note_external_context, audit_meta_builder=_audit_meta,
        ),
        "support.mode.issue": ActionPolicy(
            action="support.mode.issue", target_type="ticket", risk_level="L2",
            payload_normalizer=lambda p: _support_mode_payload(ActionIntentError, p),
            entity_state_builder=state, preview_builder=_support_mode_preview,
            challenge_kind="exact_phrase", challenge_builder=lambda _s, _p: "ВКЛЮЧИТЬ SUPPORT MODE",
            executor_kind="db", audit_action="support.mode.issue",
            db_executor=issue_support_mode, audit_meta_builder=_audit_meta,
            result_sanitizer=_sanitize_support_mode_result,
            replay_result_builder=_replay_support_mode_result,
        ),
    }


__all__ = ["build_support_action_policies"]
