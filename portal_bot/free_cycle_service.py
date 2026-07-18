from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from control_panel import ControlPanel  # Retained as a compatibility/test seam; scheduler never instantiates it.
from db import SessionLocal
from models import Node, NodeProvisioningJob, User
from node_policy import FREE_SOFT_ROLE, FREE_STANDARD_QUOTA_BYTES, PAID_ROLE, node_access_role


FREE_CYCLE_DAYS = 30
_PREMIUM_FREE_PLAN_CODES = frozenset({"trial", "channel_bonus", "start_99"})


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _is_free(user: User) -> bool:
    return (getattr(user, "sub_type", "") or "").upper().strip() == "FREE"


def _locked_free_profile_user_query(session, *, tg_id: int):
    return session.query(User).filter(User.tg_id == int(tg_id)).with_for_update()


def _lock_free_profile_user(session, user: User) -> User:
    locked = _locked_free_profile_user_query(session, tg_id=int(user.tg_id)).one_or_none()
    return locked or user


def _is_free_standard_eligible(user: User) -> bool:
    plan_code = str(getattr(user, "current_plan_code", "") or "").strip().lower()
    return _is_free(user) and plan_code not in _PREMIUM_FREE_PLAN_CODES


def _cycle_marker(user: User) -> str:
    marker = getattr(user, "free_cycle_last_reset_at", None) or getattr(user, "free_cycle_anchor_at", None)
    if isinstance(marker, datetime):
        return marker.replace(microsecond=0).isoformat()
    return "uninitialized"


def _next_cycle_at(*, anchor: datetime, now: datetime) -> datetime:
    nxt = anchor + timedelta(days=FREE_CYCLE_DAYS)
    while nxt <= now:
        nxt += timedelta(days=FREE_CYCLE_DAYS)
    return nxt


def mark_user_became_free(user: User, *, now: datetime | None = None) -> None:
    """
    Reset FREE cycle anchor for a user who has just switched to FREE.
    """
    ts = now or _utcnow()
    user.free_cycle_anchor_at = ts
    user.free_cycle_last_reset_at = ts
    user.free_cycle_next_reset_at = ts + timedelta(days=FREE_CYCLE_DAYS)
    user.free_profile_state = "standard"
    user.free_profile_active_role = "free_standard"
    user.free_profile_source = "became_free"
    user.free_profile_state_changed_at = ts
    user.free_profile_job_id = None
    user.free_profile_error_code = None
    user.free_profile_observed_bytes = 0
    user.free_profile_observed_at = ts
    user.free_profile_observation_source = "cycle_start"


def ensure_user_free_cycle_state(user: User, *, now: datetime | None = None) -> bool:
    """
    Ensure FREE cycle fields are initialized.
    Returns True when any field was changed.
    """
    if not _is_free(user):
        return False

    ts = now or _utcnow()
    changed = False

    anchor = getattr(user, "free_cycle_anchor_at", None)
    if not anchor:
        anchor = ts
        user.free_cycle_anchor_at = anchor
        changed = True

    if not getattr(user, "free_cycle_last_reset_at", None):
        user.free_cycle_last_reset_at = anchor
        changed = True

    nxt = getattr(user, "free_cycle_next_reset_at", None)
    if not nxt:
        user.free_cycle_next_reset_at = anchor + timedelta(days=FREE_CYCLE_DAYS)
        changed = True
    elif nxt <= anchor:
        user.free_cycle_next_reset_at = _next_cycle_at(anchor=anchor, now=ts)
        changed = True

    if not str(getattr(user, "free_profile_state", "") or "").strip():
        user.free_profile_state = "standard"
        changed = True
    if not str(getattr(user, "free_profile_active_role", "") or "").strip():
        user.free_profile_active_role = "free_standard"
        changed = True
    if not str(getattr(user, "free_profile_source", "") or "").strip():
        user.free_profile_source = "legacy_backfill"
        changed = True
    if getattr(user, "free_profile_state_changed_at", None) is None:
        user.free_profile_state_changed_at = anchor
        changed = True

    return changed


def reconcile_free_profile_usage(
    session,
    *,
    user: User,
    used_bytes: int,
    source: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Persist observed usage and queue one standard-to-soft transition per cycle."""
    ts = now or _utcnow()
    observed = max(0, int(used_bytes or 0))
    user = _lock_free_profile_user(session, user)

    if not _is_free_standard_eligible(user) or not bool(getattr(user, "is_active", False)):
        return {"queued": False, "job_id": None, "reason": "not_free_standard"}

    ensure_user_free_cycle_state(user, now=ts)
    state = str(getattr(user, "free_profile_state", "") or "standard").strip().lower()
    active_role = str(getattr(user, "free_profile_active_role", "") or "free_standard").strip().lower()
    if active_role != "free_standard" or state in {"soft_active", "reset_pending"}:
        return {"queued": False, "job_id": getattr(user, "free_profile_job_id", None), "reason": "not_standard"}

    user.free_profile_observed_bytes = observed
    user.free_profile_observed_at = ts
    user.free_profile_observation_source = str(source or "unknown").strip()[:64] or "unknown"
    if observed < FREE_STANDARD_QUOTA_BYTES:
        return {"queued": False, "job_id": None, "reason": "below_threshold"}

    idempotency_key = f"free-profile:{int(user.tg_id)}:{_cycle_marker(user)}:free_soft"
    existing = (
        session.query(NodeProvisioningJob)
        .filter(NodeProvisioningJob.idempotency_key == idempotency_key)
        .first()
    )
    if existing is not None:
        user.free_profile_job_id = int(existing.id)
        return {"queued": False, "job_id": int(existing.id), "reason": "already_queued"}

    job = NodeProvisioningJob(
        tg_id=int(user.tg_id),
        job_type="free_to_soft",
        status="queued",
        idempotency_key=idempotency_key,
        desired_state_json=json.dumps(
            {
                "target_role": "free_soft",
                "source_role": "free_standard",
                "quota_threshold_bytes": FREE_STANDARD_QUOTA_BYTES,
                "cycle_marker": _cycle_marker(user),
            },
            ensure_ascii=True,
            separators=(",", ":"),
        ),
        created_at=ts,
        updated_at=ts,
    )
    session.add(job)
    session.flush()
    user.free_profile_state = "soft_transition_pending"
    user.free_profile_active_role = "free_standard"
    user.free_profile_source = str(source or "usage_threshold").strip()[:64] or "usage_threshold"
    user.free_profile_state_changed_at = ts
    user.free_profile_job_id = int(job.id)
    user.free_profile_error_code = None
    return {"queued": True, "job_id": int(job.id), "reason": "threshold_reached"}


def queue_free_profile_reset(
    session,
    *,
    user: User,
    source: str,
    now: datetime | None = None,
    source_bindings: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    ts = now or _utcnow()
    user = _lock_free_profile_user(session, user)
    if not _is_free_standard_eligible(user) or not bool(getattr(user, "is_active", False)):
        return {"queued": False, "job_id": None, "reason": "not_free_standard"}
    ensure_user_free_cycle_state(user, now=ts)
    due_at = getattr(user, "free_cycle_next_reset_at", None) or ts
    due_marker = due_at.replace(microsecond=0).isoformat() if isinstance(due_at, datetime) else str(due_at)
    idempotency_key = f"free-profile:{int(user.tg_id)}:{due_marker}:free_standard_reset"
    existing = (
        session.query(NodeProvisioningJob)
        .filter(NodeProvisioningJob.idempotency_key == idempotency_key)
        .first()
    )
    if existing is not None:
        user.free_profile_job_id = int(existing.id)
        return {"queued": False, "job_id": int(existing.id), "reason": "already_queued"}

    source_role = str(getattr(user, "free_profile_active_role", "") or "free_standard").strip().lower()
    normalized_bindings: list[dict[str, str]] = []
    for binding in source_bindings or []:
        code = str((binding or {}).get("node_code") or "").strip()
        role = str((binding or {}).get("access_role") or "").strip().lower()
        if code and role in {"free_standard", "free_soft", "paid"}:
            item = {"node_code": code[:32], "access_role": role}
            if item not in normalized_bindings:
                normalized_bindings.append(item)
    job = NodeProvisioningJob(
        tg_id=int(user.tg_id),
        job_type="free_to_standard",
        status="queued",
        idempotency_key=idempotency_key,
        desired_state_json=json.dumps(
            {
                "target_role": "free_standard",
                "source_role": source_role,
                "reset_traffic": True,
                "cycle_due_at": due_marker,
                "source_bindings": normalized_bindings,
            },
            ensure_ascii=True,
            separators=(",", ":"),
        ),
        created_at=ts,
        updated_at=ts,
    )
    session.add(job)
    session.flush()
    user.free_profile_state = "reset_pending"
    user.free_profile_source = str(source or "cycle_due").strip()[:64] or "cycle_due"
    user.free_profile_state_changed_at = ts
    user.free_profile_job_id = int(job.id)
    user.free_profile_error_code = None
    return {"queued": True, "job_id": int(job.id), "reason": "cycle_reset_due"}


def queue_free_profile_reentry(
    session,
    *,
    user: User,
    source: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Project expired premium access to free and durably reconcile panel roles."""
    ts = now or _utcnow()
    user = _lock_free_profile_user(session, user)
    already_projected_free = (
        str(getattr(user, "sub_type", "") or "").strip().upper() == "FREE"
        and str(getattr(user, "current_plan_code", "") or "").strip().lower() == "free_monthly"
    )
    current_job_id = int(getattr(user, "free_profile_job_id", 0) or 0)
    if already_projected_free and current_job_id > 0:
        current_job = session.query(NodeProvisioningJob).filter(NodeProvisioningJob.id == current_job_id).first()
        if current_job is not None and current_job.job_type == "free_to_standard":
            return {
                "queued": False,
                "job_id": int(current_job.id),
                "reason": "reentry_already_projected",
            }
    previous_role = str(getattr(user, "free_profile_active_role", "") or "free_standard").strip().lower()
    bindings: list[dict[str, str]] = []
    nodes = session.query(Node).filter(Node.enabled == True).order_by(Node.code.asc()).all()
    for node in nodes:
        role = node_access_role(node)
        if role == PAID_ROLE or (previous_role == FREE_SOFT_ROLE and role == FREE_SOFT_ROLE):
            bindings.append({"node_code": str(node.code or ""), "access_role": role})

    user.sub_type = "FREE"
    user.current_plan_code = "free_monthly"
    user.is_active = True
    mark_user_became_free(user, now=ts)
    if previous_role == FREE_SOFT_ROLE:
        user.free_profile_active_role = FREE_SOFT_ROLE
    return queue_free_profile_reset(
        session,
        user=user,
        source=source,
        now=ts,
        source_bindings=bindings,
    )


def bootstrap_free_cycle_for_existing_users(*, now: datetime | None = None) -> dict[str, Any]:
    """
    One-time migration helper:
    - Existing FREE users get anchor at migration timestamp.
    """
    ts = now or _utcnow()
    s = SessionLocal()
    scanned = 0
    initialized = 0
    try:
        rows = s.query(User).filter(User.sub_type == "FREE").all()
        for u in rows:
            scanned += 1
            if getattr(u, "free_cycle_anchor_at", None):
                continue
            u.free_cycle_anchor_at = ts
            u.free_cycle_last_reset_at = ts
            u.free_cycle_next_reset_at = ts + timedelta(days=FREE_CYCLE_DAYS)
            initialized += 1
        if initialized:
            s.commit()
        return {"scanned": scanned, "initialized": initialized}
    except Exception:
        s.rollback()
        return {"scanned": scanned, "initialized": initialized, "error": "bootstrap_failed"}
    finally:
        s.close()


async def process_due_free_cycle_resets(*, max_users: int = 300) -> dict[str, Any]:
    """
    Queue durable monthly resets for FREE users whose cycle reached next_reset_at.
    The provisioning worker advances cycle timestamps only after panel proof.
    """
    now = _utcnow()
    s = SessionLocal()
    changed = 0
    queued = 0
    due = 0
    batch_limit = max(1, int(max_users))
    try:
        # Keep fields initialized for freshly migrated DB rows.
        all_free = (
            s.query(User)
            .filter(User.sub_type == "FREE")
            .filter(User.is_active == True)
            .filter(
                User.free_cycle_anchor_at.is_(None)
                | User.free_cycle_last_reset_at.is_(None)
                | User.free_cycle_next_reset_at.is_(None)
            )
            .order_by(User.tg_id.asc())
            .limit(batch_limit)
            .all()
        )
        for u in all_free:
            if ensure_user_free_cycle_state(u, now=now):
                changed += 1
        users = (
            s.query(User)
            .filter(User.sub_type == "FREE")
            .filter(User.is_active == True)
            .filter(User.free_cycle_next_reset_at.isnot(None))
            .filter(User.free_cycle_next_reset_at <= now)
            .order_by(User.free_cycle_next_reset_at.asc())
            .limit(batch_limit)
            .all()
        )
        due = len(users)
        for user in users:
            result = queue_free_profile_reset(s, user=user, source="cycle_due", now=now)
            if bool(result.get("queued")):
                queued += 1
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()

    return {
        "ok": True,
        "due": due,
        "queued": queued,
        "reset_ok": 0,
        "reset_failed": 0,
        "bootstrapped": changed,
    }
