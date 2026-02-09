from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models import SupportTicket, SupportTicketMessage


STATUS_OPEN = "open"
STATUS_IN_PROGRESS = "in_progress"
STATUS_CLOSED = "closed"
VALID_STATUSES = {STATUS_OPEN, STATUS_IN_PROGRESS, STATUS_CLOSED}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def normalize_status(value: str | None) -> str:
    raw = (value or "").strip().lower()
    if raw in VALID_STATUSES:
        return raw
    return STATUS_OPEN


def can_access_ticket(ticket: SupportTicket, tg_id: int, admin_tg_id: int) -> bool:
    return tg_id == admin_tg_id or int(ticket.user_tg_id) == int(tg_id)


def create_ticket(session: Session, *, user_tg_id: int, subject: str | None = None) -> SupportTicket:
    now = _utcnow()
    subj = (subject or "").strip()
    ticket = SupportTicket(
        user_tg_id=int(user_tg_id),
        status=STATUS_OPEN,
        subject=subj[:200] if subj else None,
        created_at=now,
        updated_at=now,
    )
    session.add(ticket)
    session.flush()
    return ticket


def get_ticket_by_id(session: Session, ticket_id: int) -> SupportTicket | None:
    return session.query(SupportTicket).filter_by(id=int(ticket_id)).first()


def get_user_active_ticket(session: Session, user_tg_id: int) -> SupportTicket | None:
    return (
        session.query(SupportTicket)
        .filter(SupportTicket.user_tg_id == int(user_tg_id))
        .filter(SupportTicket.status.in_([STATUS_OPEN, STATUS_IN_PROGRESS]))
        .order_by(SupportTicket.updated_at.desc(), SupportTicket.id.desc())
        .first()
    )


def list_user_tickets(session: Session, user_tg_id: int, limit: int = 10) -> list[SupportTicket]:
    return (
        session.query(SupportTicket)
        .filter(SupportTicket.user_tg_id == int(user_tg_id))
        .order_by(SupportTicket.updated_at.desc(), SupportTicket.id.desc())
        .limit(int(limit))
        .all()
    )


def list_active_tickets(session: Session, limit: int = 20) -> list[SupportTicket]:
    return (
        session.query(SupportTicket)
        .filter(SupportTicket.status != STATUS_CLOSED)
        .order_by(SupportTicket.updated_at.desc(), SupportTicket.id.desc())
        .limit(int(limit))
        .all()
    )


def list_ticket_messages(session: Session, ticket_id: int, limit: int = 20) -> list[SupportTicketMessage]:
    rows = (
        session.query(SupportTicketMessage)
        .filter(SupportTicketMessage.ticket_id == int(ticket_id))
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
) -> SupportTicketMessage:
    ticket = get_ticket_by_id(session, int(ticket_id))
    if not ticket:
        raise ValueError(f"ticket {ticket_id} not found")

    msg_body = (body or "").strip()
    if not msg_body:
        raise ValueError("ticket message body cannot be empty")
    role = "admin" if (sender_role or "").strip().lower() == "admin" else "user"

    now = _utcnow()
    msg = SupportTicketMessage(
        ticket_id=int(ticket_id),
        sender_tg_id=int(sender_tg_id),
        sender_role=role,
        body=msg_body[:2000],
        media_type=(media_type or "").strip()[:32] or None,
        media_file_id=(media_file_id or "").strip()[:256] or None,
        media_payload=(media_payload or "").strip()[:2000] or None,
        created_at=now,
    )
    session.add(msg)
    ticket.updated_at = now
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
    ticket.status = new_status
    ticket.updated_at = now
    if new_status == STATUS_CLOSED:
        ticket.closed_at = now
    else:
        ticket.closed_at = None
    if assigned_admin_tg_id is not None:
        ticket.assigned_admin_tg_id = int(assigned_admin_tg_id)
    session.flush()
    return ticket
