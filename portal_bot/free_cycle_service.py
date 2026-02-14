from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any

from control_panel import ControlPanel
from db import SessionLocal
from models import User


FREE_CYCLE_DAYS = max(1, int(os.getenv("FREE_CYCLE_DAYS", "30")))


def _utcnow() -> datetime:
    return datetime.utcnow()


def _is_free(user: User) -> bool:
    return (getattr(user, "sub_type", "") or "").upper().strip() == "FREE"


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

    return changed


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
    Apply monthly reset for FREE users whose cycle reached next_reset_at.
    """
    now = _utcnow()
    s = SessionLocal()
    users: list[User] = []
    changed = 0
    try:
        # Keep fields initialized for freshly migrated DB rows.
        all_free = (
            s.query(User)
            .filter(User.sub_type == "FREE")
            .filter(User.is_active == True)
            .all()
        )
        for u in all_free:
            if ensure_user_free_cycle_state(u, now=now):
                changed += 1
        if changed:
            s.commit()

        users = (
            s.query(User)
            .filter(User.sub_type == "FREE")
            .filter(User.is_active == True)
            .filter(User.free_cycle_next_reset_at.isnot(None))
            .filter(User.free_cycle_next_reset_at <= now)
            .order_by(User.free_cycle_next_reset_at.asc())
            .limit(max(1, int(max_users)))
            .all()
        )
    finally:
        s.close()

    if not users:
        return {"ok": True, "due": 0, "reset_ok": 0, "reset_failed": 0, "bootstrapped": changed}

    panel = ControlPanel()
    reset_ok = 0
    reset_failed = 0
    try:
        await panel.login()
        s2 = SessionLocal()
        try:
            for u in users:
                db_user = s2.query(User).filter(User.tg_id == int(u.tg_id)).first()
                if not db_user:
                    continue
                ok = await panel.reset_client_traffic(int(db_user.tg_id), only_free=True)
                if not ok:
                    reset_failed += 1
                    continue
                db_user.free_cycle_last_reset_at = now
                anchor = db_user.free_cycle_anchor_at or now
                db_user.free_cycle_next_reset_at = _next_cycle_at(anchor=anchor, now=now)
                reset_ok += 1
            s2.commit()
        except Exception:
            s2.rollback()
            raise
        finally:
            s2.close()
    finally:
        await panel.close()

    return {
        "ok": True,
        "due": len(users),
        "reset_ok": reset_ok,
        "reset_failed": reset_failed,
        "bootstrapped": changed,
    }
