"""Operator Center read models for guarded messaging and news publication."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func

try:
    from .models import (
        AdminActionIntent,
        AdminBroadcastDeliveryAttempt,
        LiveUpdate,
        NewsDraft,
        NewsDraftRun,
    )
    from .news_draft_service import (
        NewsDraftConfigError,
        configured_news_feeds,
        news_draft_interval_seconds,
        news_draft_worker_enabled,
    )
except ImportError:
    from models import (
        AdminActionIntent,
        AdminBroadcastDeliveryAttempt,
        LiveUpdate,
        NewsDraft,
        NewsDraftRun,
    )
    from news_draft_service import (
        NewsDraftConfigError,
        configured_news_feeds,
        news_draft_interval_seconds,
        news_draft_worker_enabled,
    )


class OperatorGrowthError(ValueError):
    def __init__(self, code: str, *, status_code: int = 422, message: str | None = None) -> None:
        super().__init__(code)
        self.code = str(code)
        self.status_code = int(status_code)
        self.message = str(message or code)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def _naive(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def _iso(value: datetime | None) -> str | None:
    normalized = _naive(value)
    if normalized is None:
        return None
    return normalized.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def broadcast_delivery(session, *, intent_id: str) -> dict[str, Any]:
    try:
        normalized_intent_id = str(uuid.UUID(str(intent_id)))
    except ValueError:
        raise OperatorGrowthError(
            "broadcast_not_found", status_code=404, message="Broadcast was not found."
        ) from None
    intent = (
        session.query(AdminActionIntent)
        .filter(AdminActionIntent.id == normalized_intent_id)
        .one_or_none()
    )
    if intent is None or str(intent.action) != "broadcast.send":
        raise OperatorGrowthError(
            "broadcast_not_found", status_code=404, message="Broadcast was not found."
        )
    campaign_row = (
        session.query(AdminBroadcastDeliveryAttempt.campaign_intent_id)
        .filter(AdminBroadcastDeliveryAttempt.intent_id == normalized_intent_id)
        .order_by(AdminBroadcastDeliveryAttempt.id.asc())
        .first()
    )
    campaign_intent_id = str(campaign_row[0]) if campaign_row is not None else normalized_intent_id
    rows = (
        session.query(AdminBroadcastDeliveryAttempt)
        .filter(AdminBroadcastDeliveryAttempt.campaign_intent_id == campaign_intent_id)
        .order_by(
            AdminBroadcastDeliveryAttempt.tg_id.asc(),
            AdminBroadcastDeliveryAttempt.attempt_number.asc(),
        )
        .limit(20_000)
        .all()
    )
    by_recipient: dict[int, list[AdminBroadcastDeliveryAttempt]] = {}
    for row in rows:
        by_recipient.setdefault(int(row.tg_id), []).append(row)
    reason_counts: dict[str, int] = {}
    delivered = 0
    retryable_failed = 0
    terminal_failed = 0
    attempts_total = 0
    duration_total_ms = 0
    first_started_at: datetime | None = None
    last_finished_at: datetime | None = None
    for attempts in by_recipient.values():
        attempts_total += len(attempts)
        duration_total_ms += sum(max(0, int(row.duration_ms or 0)) for row in attempts)
        starts = [_naive(row.started_at) for row in attempts if row.started_at is not None]
        finishes = [_naive(row.finished_at) for row in attempts if row.finished_at is not None]
        if starts:
            candidate = min(value for value in starts if value is not None)
            first_started_at = candidate if first_started_at is None else min(first_started_at, candidate)
        if finishes:
            candidate = max(value for value in finishes if value is not None)
            last_finished_at = candidate if last_finished_at is None else max(last_finished_at, candidate)
        if any(str(row.status) == "sent" for row in attempts):
            delivered += 1
            continue
        latest = attempts[-1]
        reason = str(latest.reason_code or "unknown_safe")
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
        if bool(latest.retryable):
            retryable_failed += 1
        else:
            terminal_failed += 1
    return {
        "campaign_intent_id": campaign_intent_id,
        "recipients": len(by_recipient),
        "delivered": delivered,
        "failed": max(0, len(by_recipient) - delivered),
        "retryable_failed": retryable_failed,
        "terminal_failed": terminal_failed,
        "attempts": attempts_total,
        "reason_counts": dict(sorted(reason_counts.items())),
        "average_duration_ms": (
            int(round(duration_total_ms / attempts_total)) if attempts_total else None
        ),
        "first_started_at": _iso(first_started_at),
        "last_finished_at": _iso(last_finished_at),
        "freshness_seconds": (
            max(0, int((_utcnow() - last_finished_at).total_seconds()))
            if last_finished_at is not None
            else None
        ),
        "retry_scope": "failed_retryable_only",
    }


def news_drafts(session, *, status: str = "all", limit: int = 100) -> dict[str, Any]:
    normalized_status = str(status or "all").strip().lower()
    if normalized_status not in {"all", "pending", "approved"}:
        raise OperatorGrowthError("invalid_news_status", message="News draft status is invalid.")
    normalized_limit = max(1, min(int(limit), 200))
    configuration_state = "ready"
    try:
        feeds = configured_news_feeds()
        interval_seconds = news_draft_interval_seconds()
    except NewsDraftConfigError:
        feeds = ()
        interval_seconds = None
        configuration_state = "invalid"
    query = session.query(NewsDraft)
    if normalized_status != "all":
        query = query.filter(NewsDraft.status == normalized_status)
    rows = (
        query.order_by(NewsDraft.discovered_at.desc(), NewsDraft.id.desc())
        .limit(normalized_limit)
        .all()
    )
    latest_run = (
        session.query(NewsDraftRun)
        .order_by(NewsDraftRun.started_at.desc(), NewsDraftRun.id.desc())
        .first()
    )
    counts = dict(
        session.query(NewsDraft.status, func.count(NewsDraft.id))
        .group_by(NewsDraft.status)
        .all()
    )
    return {
        "worker": {
            "enabled": news_draft_worker_enabled(),
            "configuration_state": configuration_state,
            "interval_seconds": interval_seconds,
            "sources": [feed.name for feed in feeds],
        },
        "counts": {str(key): int(value or 0) for key, value in counts.items()},
        "latest_run": None
        if latest_run is None
        else {
            "run_id": str(latest_run.run_id),
            "status": str(latest_run.status),
            "sources_total": int(latest_run.sources_total or 0),
            "sources_succeeded": int(latest_run.sources_succeeded or 0),
            "sources_failed": int(latest_run.sources_failed or 0),
            "candidates_seen": int(latest_run.candidates_seen or 0),
            "drafts_created": int(latest_run.drafts_created or 0),
            "duplicates_skipped": int(latest_run.duplicates_skipped or 0),
            "duration_ms": int(latest_run.duration_ms) if latest_run.duration_ms is not None else None,
            "failure_code": str(latest_run.failure_code or "") or None,
            "started_at": _iso(latest_run.started_at),
            "finished_at": _iso(latest_run.finished_at),
        },
        "drafts": [
            {
                "id": int(row.id),
                "source_name": str(row.source_name),
                "source_url": str(row.source_url),
                "source_title": str(row.source_title),
                "source_published_at": _iso(row.source_published_at),
                "status": str(row.status),
                "live_update_id": int(row.live_update_id) if row.live_update_id is not None else None,
                "discovered_at": _iso(row.discovered_at),
                "reviewed_at": _iso(row.reviewed_at),
            }
            for row in rows
        ],
        "freshness_at": _iso(latest_run.finished_at if latest_run is not None else None),
    }


def live_updates(session, *, include_inactive: bool = True) -> dict[str, Any]:
    query = session.query(LiveUpdate)
    if not include_inactive:
        query = query.filter(LiveUpdate.is_active.is_(True))
    rows = query.order_by(LiveUpdate.sort_order.asc(), LiveUpdate.id.desc()).limit(300).all()
    draft_by_update_id = {
        int(live_update_id): int(draft_id)
        for live_update_id, draft_id in session.query(NewsDraft.live_update_id, NewsDraft.id)
        .filter(NewsDraft.live_update_id.isnot(None))
        .all()
    }
    return {
        "updates": [
            {
                "id": int(row.id),
                "title": str(row.title),
                "summary": str(row.summary),
                "link": str(row.link or "").strip(),
                "channel_username": str(row.channel_username or "").strip().lstrip("@") or None,
                "post_id": int(row.post_id or 0) or None,
                "published_at": _iso(row.published_at),
                "is_active": bool(row.is_active),
                "sort_order": int(row.sort_order or 0),
                "source_draft_id": draft_by_update_id.get(int(row.id)),
                "created_at": _iso(row.created_at),
                "updated_at": _iso(row.updated_at),
            }
            for row in rows
        ]
    }


__all__ = [
    "OperatorGrowthError",
    "broadcast_delivery",
    "live_updates",
    "news_drafts",
]
