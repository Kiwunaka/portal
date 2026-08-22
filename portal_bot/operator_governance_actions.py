"""Guarded action-intent policies for operator governance changes."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from sqlalchemy import or_

try:
    from .admin_v2.roles import ROLE_REGISTRY
    from .models import AdminOperator, AdminOperatorRole, AdminOperatorSession
    from .operator_governance_service import role_is_active, role_payload
except ImportError:
    from admin_v2.roles import ROLE_REGISTRY
    from models import AdminOperator, AdminOperatorRole, AdminOperatorSession
    from operator_governance_service import role_is_active, role_payload


GOVERNANCE_ACTIONS = frozenset(
    {
        "operator.role.grant",
        "operator.role.revoke",
        "operator.suspend",
        "operator.activate",
        "operator.session.revoke",
        "operator.access.review",
    }
)
_TEMPORAL_LIMITS = {
    "jit": (15, 1440),
    "break_glass": (5, 60),
}


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except (TypeError, ValueError, OverflowError):
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed.replace(microsecond=0)


def _fail(error_type, code: str, message: str, *, status_code: int = 422):
    raise error_type(code, status_code=status_code, message=message)


def _base_payload(error_type, payload: Mapping[str, Any], *, allowed: set[str]) -> dict[str, Any]:
    internal = {"_environment", "_operator_id", "_actor_tg_id"}
    extra = sorted(set(payload) - allowed - internal)
    if extra:
        _fail(error_type, "invalid_payload", f"Unsupported payload fields: {', '.join(extra)}")
    environment = str(payload.get("_environment") or "").strip().lower()
    operator_id = str(payload.get("_operator_id") or "").strip()
    try:
        actor_tg_id = int(payload.get("_actor_tg_id"))
    except (TypeError, ValueError):
        actor_tg_id = 0
    if not environment or not operator_id or actor_tg_id <= 0:
        _fail(error_type, "operator_context_invalid", "Authenticated operator context is invalid.", status_code=403)
    return {
        "_environment": environment[:32],
        "_operator_id": operator_id[:36],
        "_actor_tg_id": actor_tg_id,
    }


def _reason(error_type, value: object) -> str:
    reason = str(value or "").strip()
    if not 8 <= len(reason) <= 240:
        _fail(error_type, "invalid_payload", "Reason must contain 8-240 characters.")
    return reason


def _payload(error_type, action: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    fields = {
        "operator.role.grant": {"role_code", "grant_kind", "expires_at", "reason"},
        "operator.role.revoke": {"role_code", "reason"},
        "operator.suspend": {"reason"},
        "operator.activate": {"reason"},
        "operator.session.revoke": {"reason"},
        "operator.access.review": {"note"},
    }
    result = _base_payload(error_type, payload, allowed=fields[action])
    if action == "operator.role.grant":
        role_code = str(payload.get("role_code") or "").strip().lower()
        grant_kind = str(payload.get("grant_kind") or "standing").strip().lower()
        if role_code not in ROLE_REGISTRY:
            _fail(error_type, "invalid_payload", "Role code is unknown.")
        if grant_kind not in {"standing", "jit", "break_glass"}:
            _fail(error_type, "invalid_payload", "Grant kind is invalid.")
        expires_at = _parse_time(payload.get("expires_at"))
        if grant_kind == "standing":
            if expires_at is not None:
                _fail(error_type, "invalid_payload", "Standing grant cannot expire.")
        else:
            if role_code == "superadmin":
                _fail(error_type, "invalid_payload", "Temporal superadmin grants are forbidden.")
            if expires_at is None:
                _fail(error_type, "invalid_payload", "Temporal grant requires expires_at.")
            minutes = int((expires_at - _now()).total_seconds() // 60)
            minimum, maximum = _TEMPORAL_LIMITS[grant_kind]
            if not minimum <= minutes <= maximum:
                _fail(error_type, "invalid_payload", f"{grant_kind} lifetime must be {minimum}-{maximum} minutes.")
        result.update(
            {
                "role_code": role_code,
                "grant_kind": grant_kind,
                "expires_at": _iso(expires_at),
                "reason": _reason(error_type, payload.get("reason")),
            }
        )
    elif action == "operator.role.revoke":
        role_code = str(payload.get("role_code") or "").strip().lower()
        if role_code not in ROLE_REGISTRY:
            _fail(error_type, "invalid_payload", "Role code is unknown.")
        result.update({"role_code": role_code, "reason": _reason(error_type, payload.get("reason"))})
    elif action in {"operator.suspend", "operator.activate", "operator.session.revoke"}:
        result["reason"] = _reason(error_type, payload.get("reason"))
    else:
        result["note"] = _reason(error_type, payload.get("note"))
    return result


def _locked(query, session, for_update: bool):
    if for_update and str(session.get_bind().dialect.name) == "postgresql":
        return query.with_for_update()
    return query


def _other_active_superadmins(session, *, operator_id: str, environment: str) -> int:
    current = _now()
    return int(
        session.query(AdminOperatorRole)
        .join(AdminOperator, AdminOperator.id == AdminOperatorRole.operator_id)
        .filter(
            AdminOperatorRole.role_code == "superadmin",
            AdminOperatorRole.environment_scope == str(environment),
            AdminOperatorRole.operator_id != str(operator_id),
            AdminOperatorRole.revoked_at.is_(None),
            or_(AdminOperatorRole.expires_at.is_(None), AdminOperatorRole.expires_at > current),
            AdminOperator.status == "active",
        )
        .count()
    )


def _protect_superadmin_suspension(error_type, session, *, operator_id: str) -> None:
    current = _now()
    environments = {
        str(row.environment_scope)
        for row in session.query(AdminOperatorRole)
        .filter(
            AdminOperatorRole.operator_id == str(operator_id),
            AdminOperatorRole.role_code == "superadmin",
            AdminOperatorRole.revoked_at.is_(None),
            or_(AdminOperatorRole.expires_at.is_(None), AdminOperatorRole.expires_at > current),
        )
        .all()
    }
    blocked = sorted(
        environment
        for environment in environments
        if _other_active_superadmins(
            session,
            operator_id=operator_id,
            environment=environment,
        )
        < 1
    )
    if blocked:
        _fail(
            error_type,
            "last_superadmin_protected",
            "The last active superadmin cannot be suspended.",
            status_code=409,
        )


def _operator_state(EntityState, error_type, action: str, session, target_id: str, payload, for_update: bool):
    operator = _locked(
        session.query(AdminOperator).filter(AdminOperator.id == str(target_id)),
        session,
        for_update,
    ).one_or_none()
    if operator is None:
        _fail(error_type, "target_not_found", "Operator was not found.", status_code=404)
    if str(operator.id) == str(payload["_operator_id"]):
        _fail(error_type, "self_governance_denied", "Self role/status changes are forbidden.", status_code=409)
    role_row = None
    if action in {"operator.role.grant", "operator.role.revoke"}:
        role_row = _locked(
            session.query(AdminOperatorRole).filter(
                AdminOperatorRole.operator_id == str(operator.id),
                AdminOperatorRole.environment_scope == str(payload["_environment"]),
                AdminOperatorRole.role_code == str(payload["role_code"]),
            ),
            session,
            for_update,
        ).one_or_none()
        if action == "operator.role.grant":
            if role_row is not None and role_is_active(role_row):
                _fail(error_type, "role_already_active", "Operator already has this active role.", status_code=409)
            if role_row is not None and str(role_row.review_status or "") == "pending_review":
                _fail(error_type, "access_review_required", "Previous temporal grant requires review before re-grant.", status_code=409)
        elif role_row is None or not role_is_active(role_row):
            _fail(error_type, "role_not_active", "Operator does not have this active role.", status_code=409)
        if action == "operator.role.revoke" and str(payload["role_code"]) == "superadmin":
            if _other_active_superadmins(
                session,
                operator_id=str(operator.id),
                environment=str(payload["_environment"]),
            ) < 1:
                _fail(error_type, "last_superadmin_protected", "The last active superadmin cannot be revoked.", status_code=409)
    expected = "suspended" if action == "operator.activate" else "active"
    if action in {"operator.suspend", "operator.activate"} and str(operator.status) != expected:
        _fail(error_type, "operator_state_conflict", f"Operator must be {expected} for this action.", status_code=409)
    if action == "operator.suspend":
        _protect_superadmin_suspension(error_type, session, operator_id=str(operator.id))
    snapshot = {
        "operator_id": str(operator.id),
        "display_name": str(operator.display_name or "") or None,
        "status": str(operator.status),
        "updated_at": _iso(operator.updated_at),
        "role": role_payload(role_row) if role_row is not None else None,
    }
    return EntityState(
        entity=operator,
        version_snapshot=snapshot,
        public_snapshot=snapshot,
        context={"action": action, "operator": operator, "role": role_row},
    )


def _session_state(EntityState, error_type, session, target_id: str, payload, for_update: bool):
    row = _locked(
        session.query(AdminOperatorSession).filter(
            AdminOperatorSession.id == str(target_id),
            AdminOperatorSession.environment_scope == str(payload["_environment"]),
        ),
        session,
        for_update,
    ).one_or_none()
    if row is None:
        _fail(error_type, "target_not_found", "Operator session was not found.", status_code=404)
    if row.revoked_at is not None:
        _fail(error_type, "session_already_revoked", "Operator session is already revoked.", status_code=409)
    snapshot = {
        "session_id": str(row.id),
        "operator_id": str(row.operator_id),
        "last_seen_at": _iso(row.last_seen_at),
        "absolute_expires_at": _iso(row.absolute_expires_at),
        "revoked_at": _iso(row.revoked_at),
    }
    return EntityState(entity=row, version_snapshot=snapshot, public_snapshot=snapshot, context={"action": "operator.session.revoke", "session": row})


def _review_state(EntityState, error_type, session, target_id: str, payload, for_update: bool):
    row = _locked(
        session.query(AdminOperatorRole).filter(
            AdminOperatorRole.id == str(target_id),
            AdminOperatorRole.environment_scope == str(payload["_environment"]),
        ),
        session,
        for_update,
    ).one_or_none()
    if row is None:
        _fail(error_type, "target_not_found", "Temporal role grant was not found.", status_code=404)
    if str(row.grant_kind or "standing") not in _TEMPORAL_LIMITS:
        _fail(error_type, "review_not_required", "Standing grants do not require temporal review.", status_code=409)
    if str(row.review_status or "") != "pending_review":
        _fail(error_type, "review_already_closed", "Temporal grant review is already closed.", status_code=409)
    snapshot = role_payload(row)
    return EntityState(entity=row, version_snapshot=snapshot, public_snapshot=snapshot, context={"action": "operator.access.review", "role": row})


def _state(EntityState, error_type, action: str, session, target_id: str, payload, for_update: bool):
    if action == "operator.session.revoke":
        return _session_state(EntityState, error_type, session, target_id, payload, for_update)
    if action == "operator.access.review":
        return _review_state(EntityState, error_type, session, target_id, payload, for_update)
    return _operator_state(EntityState, error_type, action, session, target_id, payload, for_update)


def _after(state, payload) -> dict[str, Any]:
    action = str(state.context["action"])
    if action == "operator.role.grant":
        return {
            **state.public_snapshot,
            "role": {
                "role_code": str(payload["role_code"]),
                "grant_kind": str(payload["grant_kind"]),
                "expires_at": payload.get("expires_at"),
                "active": True,
                "review_status": "pending_review" if str(payload["grant_kind"]) != "standing" else "not_required",
            },
        }
    if action == "operator.role.revoke":
        return {**state.public_snapshot, "role": {**(state.public_snapshot.get("role") or {}), "active": False, "revoke_reason": str(payload["reason"])}}
    if action == "operator.suspend":
        return {**state.public_snapshot, "status": "suspended", "sessions": "all_active_revoked"}
    if action == "operator.activate":
        return {**state.public_snapshot, "status": "active"}
    if action == "operator.session.revoke":
        return {**state.public_snapshot, "revoked": True, "revoke_reason": str(payload["reason"])}
    return {**state.public_snapshot, "review_status": "reviewed", "review_note": str(payload["note"])}


def _preview(state, payload) -> dict[str, Any]:
    action = str(state.context["action"])
    warnings = []
    if action == "operator.role.grant":
        warnings.append("Новая роль начнёт действовать для следующей аутентифицированной проверки.")
        if str(payload["grant_kind"]) != "standing":
            warnings.append("Временная выдача требует постревью даже после истечения или отзыва.")
    elif action == "operator.suspend":
        warnings.append("Все активные сессии оператора будут отозваны атомарно.")
    return {
        "title": "Управление доступом оператора",
        "summary": "Изменение применится только при совпадении сохранённого operator/role/session snapshot.",
        "before": state.public_snapshot,
        "after": _after(state, payload),
        "warnings": warnings,
    }


def _execute(error_type, session, state, payload) -> dict[str, Any]:
    current = _now()
    action = str(state.context["action"])
    if action == "operator.role.grant":
        row = state.context.get("role")
        if row is None:
            row = AdminOperatorRole(
                id=str(uuid.uuid4()),
                operator_id=str(state.context["operator"].id),
                role_code=str(payload["role_code"]),
                environment_scope=str(payload["_environment"]),
            )
            session.add(row)
        row.granted_by_operator_id = str(payload["_operator_id"])
        row.granted_at = current
        row.grant_kind = str(payload["grant_kind"])
        row.grant_reason = str(payload["reason"])
        row.expires_at = _parse_time(payload.get("expires_at"))
        row.review_status = "pending_review" if str(payload["grant_kind"]) != "standing" else "not_required"
        row.reviewed_by_operator_id = None
        row.reviewed_at = None
        row.review_note = None
        row.revoked_at = None
        row.revoke_reason = None
        session.flush()
        return {"operator_id": str(row.operator_id), "role": role_payload(row, now=current)}
    if action == "operator.role.revoke":
        row = state.context["role"]
        row.revoked_at = current
        row.revoke_reason = str(payload["reason"])[:96]
        return {"operator_id": str(row.operator_id), "role": role_payload(row, now=current)}
    if action in {"operator.suspend", "operator.activate"}:
        operator = state.context["operator"]
        operator.status = "suspended" if action == "operator.suspend" else "active"
        operator.suspended_at = current if action == "operator.suspend" else None
        operator.updated_at = current
        revoked_sessions = 0
        if action == "operator.suspend":
            sessions = session.query(AdminOperatorSession).filter(
                AdminOperatorSession.operator_id == str(operator.id),
                AdminOperatorSession.revoked_at.is_(None),
            ).all()
            for row in sessions:
                row.revoked_at = current
                row.revoke_reason = "operator_suspended"
                revoked_sessions += 1
        return {"operator_id": str(operator.id), "status": str(operator.status), "revoked_sessions": revoked_sessions}
    if action == "operator.session.revoke":
        row = state.context["session"]
        row.revoked_at = current
        row.revoke_reason = str(payload["reason"])[:96]
        return {"session_id": str(row.id), "operator_id": str(row.operator_id), "revoked": True}
    row = state.context["role"]
    row.review_status = "reviewed"
    row.reviewed_by_operator_id = str(payload["_operator_id"])
    row.reviewed_at = current
    row.review_note = str(payload["note"])
    return {"operator_id": str(row.operator_id), "role": role_payload(row, now=current)}


def _audit_meta(state, payload) -> dict[str, Any]:
    action = str(state.context["action"])
    operator_id = None
    if state.context.get("operator") is not None:
        operator_id = str(state.context["operator"].id)
    elif state.context.get("role") is not None:
        operator_id = str(state.context["role"].operator_id)
    elif state.context.get("session") is not None:
        operator_id = str(state.context["session"].operator_id)
    return {
        "environment": str(payload["_environment"]),
        "operator_id": operator_id,
        "role_code": payload.get("role_code") or getattr(state.context.get("role"), "role_code", None),
        "grant_kind": payload.get("grant_kind") or getattr(state.context.get("role"), "grant_kind", None),
        "expires_at": payload.get("expires_at") or _iso(getattr(state.context.get("role"), "expires_at", None)),
        "reason": payload.get("reason") or payload.get("note"),
        "review_status": "reviewed" if action == "operator.access.review" else None,
    }


def build_governance_action_policies(*, ActionPolicy, EntityState, ActionIntentError) -> dict[str, Any]:
    target_types = {
        "operator.role.grant": "operator",
        "operator.role.revoke": "operator",
        "operator.suspend": "operator",
        "operator.activate": "operator",
        "operator.session.revoke": "operator_session",
        "operator.access.review": "operator_role",
    }
    policies: dict[str, Any] = {}
    for action in sorted(GOVERNANCE_ACTIONS):
        high_risk = action != "operator.access.review"
        policies[action] = ActionPolicy(
            action=action,
            target_type=target_types[action],
            risk_level="L3" if high_risk else "L2",
            payload_normalizer=lambda payload, selected=action: _payload(ActionIntentError, selected, payload),
            entity_state_builder=lambda session, target_id, payload, for_update, selected=action: _state(
                EntityState, ActionIntentError, selected, session, target_id, payload, for_update
            ),
            preview_builder=_preview,
            challenge_kind="exact_target_id" if high_risk else "exact_phrase",
            challenge_builder=(
                (lambda state, _payload: str(state.entity.id))
                if high_risk
                else (lambda _state, _payload: "ПОДТВЕРДИТЬ")
            ),
            executor_kind="db",
            audit_action=action,
            db_executor=lambda session, state, payload: _execute(ActionIntentError, session, state, payload),
            audit_meta_builder=_audit_meta,
        )
    return policies


__all__ = ["GOVERNANCE_ACTIONS", "build_governance_action_policies"]
