from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from account_foundation_service import (
    ACCOUNT_FOUNDATION_BACKFILL_LOCK,
    _acquire_postgres_advisory_lock,
)
from models import (
    Account,
    AccountIdentity,
    AccountMergeReview,
    AppSetting,
    SupportAttachment,
    SupportTicket,
    User,
)


SUPPORT_ACCOUNT_OWNERSHIP_BACKFILL_KEY = "migration.support_account_ownership.v1"
SUPPORT_ACCOUNT_OWNERSHIP_BACKFILL_LOCK = "pokrov_support_account_ownership_backfill_v1"
SUPPORT_ACCOUNT_OWNERSHIP_STARTUP_LOCK = "pokrov_support_account_ownership_startup_v1"
SUPPORT_ACCOUNT_REVIEW_NAMESPACE = uuid.UUID("b192ff3f-e8b7-4524-80db-507cc28d0e87")
MAX_ACCOUNT_MERGE_HOPS = 32


@dataclass(frozen=True)
class SupportAccountBackfillReport:
    tickets_seen: int = 0
    attachments_seen: int = 0
    ticket_assignments: int = 0
    attachment_assignments: int = 0
    unresolved: int = 0
    conflicts: int = 0
    reviews_created: int = 0


class _Counter:
    def __init__(self) -> None:
        self.tickets_seen = 0
        self.attachments_seen = 0
        self.ticket_assignments = 0
        self.attachment_assignments = 0
        self.unresolved = 0
        self.conflicts = 0
        self.reviews_created = 0

    def freeze(self) -> SupportAccountBackfillReport:
        return SupportAccountBackfillReport(
            tickets_seen=self.tickets_seen,
            attachments_seen=self.attachments_seen,
            ticket_assignments=self.ticket_assignments,
            attachment_assignments=self.attachment_assignments,
            unresolved=self.unresolved,
            conflicts=self.conflicts,
            reviews_created=self.reviews_created,
        )


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def canonicalize_support_account_id(session: Session, account_id: str | None) -> str | None:
    current = str(account_id or "").strip()
    visited: set[str] = set()
    for _hop in range(MAX_ACCOUNT_MERGE_HOPS):
        if not current or current in visited:
            return None
        visited.add(current)
        account = session.query(Account).filter(Account.id == current).first()
        if account is None:
            return None
        target = str(account.merged_into_account_id or "").strip()
        if str(account.status or "").strip().lower() != "merged" or not target:
            return current
        current = target
    return None


def support_account_candidates(session: Session, legacy_id: int) -> dict[str, list[str]]:
    legacy_key = int(legacy_id)
    raw_candidates: list[tuple[str, str]] = []
    for row in session.query(User.account_id).filter(User.tg_id == legacy_key, User.account_id.isnot(None)).all():
        raw_candidates.append((str(row[0]), "user.tg_id"))
    for row in (
        session.query(User.account_id)
        .filter(User.linked_telegram_id == legacy_key, User.account_id.isnot(None))
        .all()
    ):
        raw_candidates.append((str(row[0]), "user.linked_telegram_id"))
    for row in (
        session.query(AccountIdentity.account_id)
        .filter(
            AccountIdentity.kind == "telegram",
            AccountIdentity.provider == "telegram",
            AccountIdentity.subject_norm == str(legacy_key),
            AccountIdentity.disabled_at.is_(None),
        )
        .all()
    ):
        raw_candidates.append((str(row[0]), "account_identity.telegram"))

    candidates: dict[str, set[str]] = {}
    for raw_account_id, source in raw_candidates:
        canonical_id = canonicalize_support_account_id(session, raw_account_id)
        if canonical_id:
            candidates.setdefault(canonical_id, set()).add(source)
    return {
        account_id: sorted(sources)
        for account_id, sources in sorted(candidates.items())
    }


def resolve_canonical_support_account_id(
    session: Session,
    *,
    account_id: str | None = None,
    legacy_tg_id: int | None = None,
) -> str | None:
    explicit = str(account_id or "").strip()
    if explicit:
        return canonicalize_support_account_id(session, explicit)
    if legacy_tg_id is None:
        return None
    candidates = support_account_candidates(session, int(legacy_tg_id))
    return next(iter(candidates)) if len(candidates) == 1 else None


def _create_review(
    session: Session,
    counter: _Counter,
    *,
    entity_type: str,
    entity_id: int,
    legacy_id: int,
    reason: str,
    candidates: dict[str, list[str]],
    now: datetime,
) -> None:
    fingerprint = hashlib.sha256(
        f"support-account-ownership|{entity_type}|{int(entity_id)}|{reason}".encode("utf-8")
    ).hexdigest()
    details = {
        "candidate_ids": sorted(candidates),
        "candidate_sources": [
            {"account_id": candidate_id, "sources": candidates[candidate_id]}
            for candidate_id in sorted(candidates)
        ],
        "entity_id": int(entity_id),
        "entity_type": entity_type,
        "legacy_id": int(legacy_id),
        "reason": reason,
    }
    details_json = _json(details)
    existing = session.query(AccountMergeReview).filter_by(fingerprint=fingerprint).first()
    if existing is not None:
        if str(existing.details_json or "") != details_json:
            existing.details_json = details_json
            existing.updated_at = now
        return
    candidate_ids = sorted(candidates)
    session.add(
        AccountMergeReview(
            id=str(uuid.uuid5(SUPPORT_ACCOUNT_REVIEW_NAMESPACE, fingerprint)),
            fingerprint=fingerprint,
            account_id=candidate_ids[0] if candidate_ids else None,
            conflicting_account_id=candidate_ids[1] if len(candidate_ids) > 1 else None,
            reason_code=reason,
            status="open",
            subject_hint=f"{entity_type}:{int(entity_id)}",
            details_json=details_json,
            created_at=now,
            updated_at=now,
        )
    )
    counter.reviews_created += 1


def _backfill_row(
    session: Session,
    counter: _Counter,
    *,
    row: SupportTicket | SupportAttachment,
    entity_type: str,
    owner_attribute: str,
    legacy_id: int,
    unresolved_reason: str,
    conflict_reason: str,
    now: datetime,
) -> None:
    candidates = support_account_candidates(session, int(legacy_id))
    if len(candidates) == 1:
        setattr(row, owner_attribute, next(iter(candidates)))
        if entity_type == "support_ticket":
            counter.ticket_assignments += 1
        else:
            counter.attachment_assignments += 1
        return
    reason = unresolved_reason if not candidates else conflict_reason
    if candidates:
        counter.conflicts += 1
    else:
        counter.unresolved += 1
    _create_review(
        session,
        counter,
        entity_type=entity_type,
        entity_id=int(row.id),
        legacy_id=int(legacy_id),
        reason=reason,
        candidates=candidates,
        now=now,
    )


def backfill_support_account_ownership(
    session: Session,
    *,
    now: datetime | None = None,
) -> SupportAccountBackfillReport:
    effective_now = now or _utcnow()
    _acquire_postgres_advisory_lock(session, ACCOUNT_FOUNDATION_BACKFILL_LOCK, shared=True)
    _acquire_postgres_advisory_lock(session, SUPPORT_ACCOUNT_OWNERSHIP_BACKFILL_LOCK)
    counter = _Counter()

    tickets = (
        session.query(SupportTicket)
        .filter(SupportTicket.account_id.is_(None))
        .order_by(SupportTicket.id.asc())
        .with_for_update()
        .all()
    )
    counter.tickets_seen = len(tickets)
    for ticket in tickets:
        _backfill_row(
            session,
            counter,
            row=ticket,
            entity_type="support_ticket",
            owner_attribute="account_id",
            legacy_id=int(ticket.user_tg_id),
            unresolved_reason="support_ticket_account_unresolved",
            conflict_reason="support_ticket_account_conflict",
            now=effective_now,
        )

    attachments = (
        session.query(SupportAttachment)
        .filter(SupportAttachment.owner_account_id.is_(None))
        .order_by(SupportAttachment.id.asc())
        .with_for_update()
        .all()
    )
    counter.attachments_seen = len(attachments)
    for attachment in attachments:
        _backfill_row(
            session,
            counter,
            row=attachment,
            entity_type="support_attachment",
            owner_attribute="owner_account_id",
            legacy_id=int(attachment.owner_tg_id),
            unresolved_reason="support_attachment_owner_unresolved",
            conflict_reason="support_attachment_owner_conflict",
            now=effective_now,
        )
    session.flush()
    return counter.freeze()


def run_support_account_ownership_backfill_once(
    session: Session,
    *,
    now: datetime | None = None,
) -> SupportAccountBackfillReport:
    effective_now = now or _utcnow()
    _acquire_postgres_advisory_lock(session, SUPPORT_ACCOUNT_OWNERSHIP_STARTUP_LOCK)
    marker = session.query(AppSetting).filter_by(key=SUPPORT_ACCOUNT_OWNERSHIP_BACKFILL_KEY).first()
    if marker is not None:
        try:
            payload = json.loads(str(marker.value_json or "{}"))
        except (TypeError, ValueError, json.JSONDecodeError):
            payload = {}
        if payload.get("status") == "complete" and int(payload.get("version") or 0) == 1:
            return SupportAccountBackfillReport()

    report = backfill_support_account_ownership(session, now=effective_now)
    marker_payload = _json(
        {
            "completed_at": effective_now.isoformat(),
            "report": {
                "attachment_assignments": report.attachment_assignments,
                "attachments_seen": report.attachments_seen,
                "conflicts": report.conflicts,
                "reviews_created": report.reviews_created,
                "ticket_assignments": report.ticket_assignments,
                "tickets_seen": report.tickets_seen,
                "unresolved": report.unresolved,
            },
            "status": "complete",
            "version": 1,
        }
    )
    if marker is None:
        session.add(
            AppSetting(
                key=SUPPORT_ACCOUNT_OWNERSHIP_BACKFILL_KEY,
                value_json=marker_payload,
                updated_at=effective_now,
            )
        )
    else:
        marker.value_json = marker_payload
        marker.updated_at = effective_now
    session.flush()
    return report
