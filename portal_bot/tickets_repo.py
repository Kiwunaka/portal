from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from account_foundation_service import SYNTHETIC_EMAIL_ACCOUNT_MIN
from models import Account, AccountIdentity, SupportAttachment, SupportTicket, SupportTicketMessage, User
from support_account_service import (
    MAX_ACCOUNT_MERGE_HOPS,
    canonicalize_support_account_id,
    resolve_canonical_support_account_id,
)


STATUS_OPEN = "open"
STATUS_IN_PROGRESS = "in_progress"
STATUS_CLOSED = "closed"
VALID_STATUSES = {STATUS_OPEN, STATUS_IN_PROGRESS, STATUS_CLOSED}
DEFAULT_SUPPORT_SLA_HOURS = 24
MAX_SUPPORT_NOTIFICATION_ACCOUNT_IDS = 64
MAX_SUPPORT_NOTIFICATION_TARGETS = 64


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _support_environment() -> str:
    value = str(os.getenv("POKROV_ENVIRONMENT") or "production").strip().lower()
    return value if re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", value) else "production"


def normalize_status(value: str | None) -> str:
    raw = (value or "").strip().lower()
    if raw in VALID_STATUSES:
        return raw
    return STATUS_OPEN


def resolve_support_account_id(
    session: Session,
    *,
    account_id: str | None = None,
    user_tg_id: int | None = None,
) -> str | None:
    return resolve_canonical_support_account_id(
        session,
        account_id=account_id,
        legacy_tg_id=user_tg_id,
    )


def can_access_ticket(
    ticket: SupportTicket,
    tg_id: int,
    admin_tg_id: int,
    *,
    account_id: str | None = None,
) -> bool:
    if int(tg_id) == int(admin_tg_id):
        return True
    ticket_account_id = str(ticket.account_id or "").strip()
    actor_account_id = str(account_id or "").strip()
    if ticket_account_id:
        return bool(actor_account_id and ticket_account_id == actor_account_id)
    return int(ticket.user_tg_id) == int(tg_id)


def can_access_support_attachment(
    attachment: SupportAttachment,
    tg_id: int,
    admin_tg_id: int,
    *,
    account_id: str | None = None,
) -> bool:
    if int(tg_id) == int(admin_tg_id):
        return True
    owner_account_id = str(attachment.owner_account_id or "").strip()
    actor_account_id = str(account_id or "").strip()
    if owner_account_id:
        return bool(actor_account_id and owner_account_id == actor_account_id)
    return int(attachment.owner_tg_id) == int(tg_id)


def create_ticket(
    session: Session,
    *,
    user_tg_id: int,
    subject: str | None = None,
    account_id: str | None = None,
) -> SupportTicket:
    now = _utcnow()
    subj = (subject or "").strip()
    resolved_account_id = resolve_support_account_id(
        session,
        account_id=account_id,
        user_tg_id=int(user_tg_id),
    )
    ticket = SupportTicket(
        user_tg_id=int(user_tg_id),
        account_id=resolved_account_id,
        environment=_support_environment(),
        status=STATUS_OPEN,
        subject=subj[:200] if subj else None,
        priority="normal",
        queue="general",
        sla_due_at=now + timedelta(hours=DEFAULT_SUPPORT_SLA_HOURS),
        version=1,
        created_at=now,
        updated_at=now,
    )
    session.add(ticket)
    session.flush()
    return ticket


def get_ticket_by_id(session: Session, ticket_id: int) -> SupportTicket | None:
    return session.query(SupportTicket).filter_by(id=int(ticket_id)).first()


def _user_ownership_filter(*, user_tg_id: int, account_id: str | None):
    legacy_fallback = and_(
        SupportTicket.account_id.is_(None),
        SupportTicket.user_tg_id == int(user_tg_id),
    )
    canonical_id = str(account_id or "").strip()
    if canonical_id:
        return or_(SupportTicket.account_id == canonical_id, legacy_fallback)
    return legacy_fallback


def get_user_active_ticket(
    session: Session,
    user_tg_id: int,
    *,
    account_id: str | None = None,
) -> SupportTicket | None:
    resolved_account_id = resolve_support_account_id(
        session,
        account_id=account_id,
        user_tg_id=int(user_tg_id),
    )
    return (
        session.query(SupportTicket)
        .filter(_user_ownership_filter(user_tg_id=int(user_tg_id), account_id=resolved_account_id))
        .filter(SupportTicket.status.in_([STATUS_OPEN, STATUS_IN_PROGRESS]))
        .order_by(SupportTicket.updated_at.desc(), SupportTicket.id.desc())
        .first()
    )


def list_user_tickets(
    session: Session,
    user_tg_id: int,
    limit: int = 10,
    *,
    account_id: str | None = None,
) -> list[SupportTicket]:
    resolved_account_id = resolve_support_account_id(
        session,
        account_id=account_id,
        user_tg_id=int(user_tg_id),
    )
    return (
        session.query(SupportTicket)
        .filter(_user_ownership_filter(user_tg_id=int(user_tg_id), account_id=resolved_account_id))
        .order_by(SupportTicket.updated_at.desc(), SupportTicket.id.desc())
        .limit(int(limit))
        .all()
    )


def claim_legacy_ticket(
    ticket: SupportTicket,
    *,
    actor_tg_id: int,
    account_id: str | None,
) -> bool:
    canonical_id = str(account_id or "").strip()
    if ticket.account_id is not None or not canonical_id:
        return False
    if int(ticket.user_tg_id) != int(actor_tg_id):
        return False
    ticket.account_id = canonical_id
    return True


def _real_telegram_target(value: object) -> int | None:
    try:
        target = int(str(value or "").strip())
    except (TypeError, ValueError):
        return None
    if 0 < target < SYNTHETIC_EMAIL_ACCOUNT_MIN:
        return target
    return None


def _support_notification_account_ids(session: Session, account_id: str) -> list[str]:
    canonical_id = canonicalize_support_account_id(session, account_id)
    if not canonical_id:
        return []
    account_ids = {canonical_id}
    frontier = {canonical_id}
    for _hop in range(MAX_ACCOUNT_MERGE_HOPS):
        if not frontier or len(account_ids) >= MAX_SUPPORT_NOTIFICATION_ACCOUNT_IDS:
            break
        remaining = MAX_SUPPORT_NOTIFICATION_ACCOUNT_IDS - len(account_ids)
        rows = (
            session.query(Account.id)
            .filter(Account.merged_into_account_id.in_(sorted(frontier)))
            .order_by(Account.id.asc())
            .limit(remaining)
            .all()
        )
        next_frontier = {str(row[0]) for row in rows if str(row[0]) not in account_ids}
        account_ids.update(next_frontier)
        frontier = next_frontier
    return sorted(account_ids)


def resolve_ticket_notification_tg_id(session: Session, ticket: SupportTicket) -> int | None:
    account_ids = _support_notification_account_ids(session, str(ticket.account_id or "").strip())
    if account_ids:
        linked_users = (
            session.query(User.linked_telegram_id)
            .filter(
                User.account_id.in_(account_ids),
                User.linked_telegram_id.isnot(None),
                User.linked_telegram_id > 0,
                User.linked_telegram_id < SYNTHETIC_EMAIL_ACCOUNT_MIN,
            )
            .order_by(
                User.linked_telegram_linked_at.is_(None).asc(),
                User.linked_telegram_linked_at.desc(),
                User.tg_id.asc(),
            )
            .limit(MAX_SUPPORT_NOTIFICATION_TARGETS)
            .all()
        )
        for row in linked_users:
            target = _real_telegram_target(row[0])
            if target is not None:
                return target

        identities = (
            session.query(AccountIdentity.subject_norm)
            .filter(
                AccountIdentity.account_id.in_(account_ids),
                AccountIdentity.kind == "telegram",
                AccountIdentity.provider == "telegram",
                AccountIdentity.disabled_at.is_(None),
            )
            .order_by(
                AccountIdentity.verified_at.is_(None).asc(),
                AccountIdentity.verified_at.desc(),
                AccountIdentity.updated_at.desc(),
                AccountIdentity.id.asc(),
            )
            .limit(MAX_SUPPORT_NOTIFICATION_TARGETS)
            .all()
        )
        for row in identities:
            target = _real_telegram_target(row[0])
            if target is not None:
                return target

    return _real_telegram_target(ticket.user_tg_id)


def list_active_tickets(session: Session, limit: int = 20) -> list[SupportTicket]:
    return (
        session.query(SupportTicket)
        .filter(SupportTicket.status != STATUS_CLOSED)
        .order_by(SupportTicket.updated_at.desc(), SupportTicket.id.desc())
        .limit(int(limit))
        .all()
    )


def list_ticket_messages(
    session: Session,
    ticket_id: int,
    limit: int = 20,
    *,
    include_internal: bool = False,
) -> list[SupportTicketMessage]:
    query = session.query(SupportTicketMessage).filter(SupportTicketMessage.ticket_id == int(ticket_id))
    if not include_internal:
        query = query.filter(SupportTicketMessage.visibility != "internal")
    rows = (
        query
        .order_by(SupportTicketMessage.created_at.desc(), SupportTicketMessage.id.desc())
        .limit(int(limit))
        .all()
    )
    rows.reverse()
    return rows


def add_ticket_message(
    session: Session,
    *,
    ticket_id: int,
    sender_tg_id: int,
    sender_role: str,
    body: str,
    media_type: str | None = None,
    media_file_id: str | None = None,
    media_payload: str | None = None,
    visibility: str = "public",
    macro_code: str | None = None,
) -> SupportTicketMessage:
    ticket = get_ticket_by_id(session, int(ticket_id))
    if not ticket:
        raise ValueError(f"ticket {ticket_id} not found")

    msg_body = (body or "").strip()
    if not msg_body:
        raise ValueError("ticket message body cannot be empty")
    raw_role = (sender_role or "").strip().lower()
    role = raw_role if raw_role in {"admin", "assistant"} else "user"
    normalized_visibility = str(visibility or "public").strip().lower()
    if normalized_visibility not in {"public", "internal"}:
        raise ValueError("ticket message visibility is invalid")
    if normalized_visibility == "internal" and role not in {"admin", "assistant"}:
        raise ValueError("internal ticket notes require an operator role")
    normalized_macro = str(macro_code or "").strip().lower()
    if normalized_macro and re.fullmatch(r"[a-z0-9][a-z0-9._-]{1,47}", normalized_macro) is None:
        raise ValueError("ticket macro code is invalid")

    now = _utcnow()
    msg = SupportTicketMessage(
        ticket_id=int(ticket_id),
        sender_tg_id=int(sender_tg_id),
        sender_role=role,
        visibility=normalized_visibility,
        macro_code=normalized_macro or None,
        body=msg_body[:2000],
        media_type=(media_type or "").strip()[:32] or None,
        media_file_id=(media_file_id or "").strip()[:256] or None,
        media_payload=(media_payload or "").strip()[:2000] or None,
        created_at=now,
    )
    session.add(msg)
    ticket.updated_at = now
    ticket.version = max(1, int(getattr(ticket, "version", 1) or 1)) + 1
    session.flush()
    return msg


def set_ticket_status(
    session: Session,
    *,
    ticket: SupportTicket,
    status: str,
    assigned_admin_tg_id: int | None = None,
) -> SupportTicket:
    new_status = normalize_status(status)
    now = _utcnow()
    changed = str(ticket.status or "") != new_status
    ticket.status = new_status
    ticket.updated_at = now
    if new_status == STATUS_CLOSED:
        ticket.closed_at = now
    else:
        ticket.closed_at = None
    if assigned_admin_tg_id is not None:
        changed = changed or int(ticket.assigned_admin_tg_id or 0) != int(assigned_admin_tg_id)
        ticket.assigned_admin_tg_id = int(assigned_admin_tg_id)
    if changed:
        ticket.version = max(1, int(getattr(ticket, "version", 1) or 1)) + 1
    session.flush()
    return ticket
