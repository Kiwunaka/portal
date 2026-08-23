"""Stored action-intent policy for program review and entitlement rewards."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

try:
    from .models import ProgramApplication
    from .operator_money_service import program_view
    from .program_application_service import ProgramApplicationError, review_application
except ImportError:
    from models import ProgramApplication
    from operator_money_service import program_view
    from program_application_service import ProgramApplicationError, review_application


PROGRAM_REVIEW_STATUSES = frozenset({"under_review", "approved", "rejected"})
PROGRAM_REWARD_DAYS = frozenset({0, 1, 3, 7})


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def _error(error_type, code: str, message: str, *, status_code: int = 422):
    raise error_type(code, status_code=status_code, message=message)


def _payload(error_type, payload: Mapping[str, Any]) -> dict[str, Any]:
    allowed = {
        "_environment",
        "_operator_id",
        "_actor_tg_id",
        "status",
        "operator_note",
        "reward_days",
    }
    extra = sorted(set(payload) - allowed)
    if extra:
        _error(error_type, "invalid_payload", f"Unsupported payload fields: {', '.join(extra)}")
    environment = str(payload.get("_environment") or "").strip().lower()
    if environment != "production":
        _error(error_type, "money_environment_unavailable", "Money actions are unavailable in this environment.", status_code=409)
    try:
        actor_tg_id = int(payload.get("_actor_tg_id"))
        reward_days = int(payload.get("reward_days") or 0)
    except (TypeError, ValueError):
        _error(error_type, "invalid_payload", "Actor or reward is invalid.")
    if actor_tg_id <= 0 or reward_days not in PROGRAM_REWARD_DAYS:
        _error(error_type, "invalid_payload", "Actor or reward is invalid.")
    status = str(payload.get("status") or "").strip().lower()
    if status not in PROGRAM_REVIEW_STATUSES:
        _error(error_type, "invalid_payload", "Review status is invalid.")
    if reward_days and status != "approved":
        _error(error_type, "invalid_payload", "A reward requires approval.")
    note = " ".join(str(payload.get("operator_note") or "").strip().split())[:1000] or None
    return {
        "_environment": environment,
        "_actor_tg_id": actor_tg_id,
        "status": status,
        "operator_note": note,
        "reward_days": reward_days,
    }


def _state(EntityState, error_type, session, target_id: str, payload, for_update: bool):
    application_id = str(target_id or "").strip()
    if not application_id or len(application_id) > 64:
        _error(error_type, "invalid_target", "Application id is invalid.")
    query = session.query(ProgramApplication).filter(ProgramApplication.id == application_id)
    if for_update and str(session.get_bind().dialect.name) == "postgresql":
        query = query.with_for_update()
    row = query.one_or_none()
    if row is None:
        _error(error_type, "target_not_found", "Application was not found.", status_code=404)
    if row.kind == "team_pack" and int(payload["reward_days"]):
        _error(error_type, "program_reward_invalid", "Team-pack requests do not grant bonus days.", status_code=409)
    before = program_view(row)
    version = {
        "id": str(row.id),
        "status": str(row.status),
        "reward_days": int(row.reward_days or 0),
        "reward_grant_id": str(row.reward_grant_id or "") or None,
        "updated_at": before["updated_at"],
    }
    return EntityState(
        entity=row,
        version_snapshot=version,
        public_snapshot=before,
        context={"application_id": application_id, "legacy_tg_id": row.legacy_tg_id},
    )


def _preview(state, payload):
    rewarded = int(payload["reward_days"]) > 0
    return {
        "title": "Решение по заявке программы",
        "summary": "Статус и entitlement reward изменятся атомарно только при совпадении версии заявки.",
        "before": state.public_snapshot,
        "after": {
            "status": "rewarded" if rewarded else str(payload["status"]),
            "reward_days": int(payload["reward_days"]),
            "operator_note_present": bool(payload.get("operator_note")),
        },
        "warnings": (
            ["Команда создаёт идемпотентный entitlement grant."]
            if rewarded
            else []
        ),
    }


def _execute(error_type, session, state, payload):
    try:
        row = review_application(
            session,
            application_id=str(state.context["application_id"]),
            status=str(payload["status"]),
            operator_note=payload.get("operator_note"),
            reward_days=int(payload["reward_days"]),
            reviewed_by=int(payload["_actor_tg_id"]),
            now=_now(),
        )
    except ProgramApplicationError as exc:
        _error(error_type, str(exc.code), str(exc.message), status_code=409)
    return {"application": program_view(row)}


def build_money_action_policies(*, ActionPolicy, EntityState, ActionIntentError) -> dict[str, Any]:
    return {
        "program_application.review": ActionPolicy(
            action="program_application.review",
            target_type="program_application",
            risk_level="L3",
            payload_normalizer=lambda payload: _payload(ActionIntentError, payload),
            entity_state_builder=lambda session, target_id, payload, for_update: _state(
                EntityState,
                ActionIntentError,
                session,
                target_id,
                payload,
                for_update,
            ),
            preview_builder=_preview,
            challenge_kind="exact_application_id",
            challenge_builder=lambda state, _payload: str(state.context["application_id"]),
            executor_kind="db",
            audit_action="program_application.review",
            db_executor=lambda session, state, payload: _execute(
                ActionIntentError,
                session,
                state,
                payload,
            ),
            audit_target_builder=lambda state, _payload: (
                int(state.context["legacy_tg_id"])
                if state.context.get("legacy_tg_id") is not None
                else None
            ),
            audit_meta_builder=lambda state, payload: {
                "application_ref": str(state.context["application_id"]),
                "status": str(payload["status"]),
                "reward_days": int(payload["reward_days"]),
                "operator_note_present": bool(payload.get("operator_note")),
            },
        )
    }


__all__ = ["build_money_action_policies"]
