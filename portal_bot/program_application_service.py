from __future__ import annotations

import uuid
from datetime import datetime

from economy_service import grant_internal_bonus_days, rebuild_account_entitlement_projection
from models import ProgramApplication, User


PROGRAM_KINDS = {"competitor_switch", "research", "team_pack"}
PROGRAM_STATUSES = {"submitted", "under_review", "approved", "rejected", "rewarded", "cancelled"}


class ProgramApplicationError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = str(code)
        self.message = str(message)


def _clean_text(value: str | None, *, max_len: int) -> str:
    return " ".join(str(value or "").strip().split())[:max_len]


def application_payload(row: ProgramApplication, *, include_operator_note: bool = False) -> dict[str, object | None]:
    payload: dict[str, object | None] = {
        "id": str(row.id),
        "kind": str(row.kind),
        "status": str(row.status),
        "source_name": str(row.source_name or "") or None,
        "seats": int(row.seats) if row.seats is not None else None,
        "summary": str(row.summary or ""),
        "contact": str(row.contact or "") or None,
        "reward_days": int(row.reward_days or 0),
        "rewarded": bool(row.reward_grant_id),
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "reviewed_at": row.reviewed_at.isoformat() if row.reviewed_at else None,
        "decision_note": str(row.operator_note or "") or None,
    }
    if include_operator_note:
        payload.update(
            {
                "account_id": str(row.account_id),
                "legacy_tg_id": int(row.legacy_tg_id) if row.legacy_tg_id is not None else None,
                "operator_note": str(row.operator_note or "") or None,
                "reviewed_by": int(row.reviewed_by) if row.reviewed_by is not None else None,
                "reward_grant_id": str(row.reward_grant_id or "") or None,
            }
        )
    return payload


def submit_application(
    session,
    *,
    user: User,
    kind: str,
    source_name: str | None,
    seats: int | None,
    summary: str,
    contact: str | None,
    now: datetime,
) -> ProgramApplication:
    normalized_kind = str(kind or "").strip().lower()
    if normalized_kind not in PROGRAM_KINDS:
        raise ProgramApplicationError("program_kind_invalid", "Unknown program.")
    account_id = str(user.account_id or "").strip()
    if not account_id:
        raise ProgramApplicationError("account_not_found", "Account is unavailable.")
    clean_summary = _clean_text(summary, max_len=2000)
    if len(clean_summary) < 20:
        raise ProgramApplicationError("program_summary_too_short", "Add at least 20 characters.")
    clean_source = _clean_text(source_name, max_len=100)
    clean_contact = _clean_text(contact, max_len=160)
    resolved_seats = int(seats) if seats is not None else None
    if normalized_kind == "competitor_switch" and len(clean_source) < 2:
        raise ProgramApplicationError("competitor_required", "Name the service you are switching from.")
    if normalized_kind == "team_pack":
        if resolved_seats is None or resolved_seats < 2 or resolved_seats > 50:
            raise ProgramApplicationError("team_seats_invalid", "Team size must be from 2 to 50.")
    else:
        resolved_seats = None

    existing = (
        session.query(ProgramApplication)
        .filter(
            ProgramApplication.account_id == account_id,
            ProgramApplication.kind == normalized_kind,
            ProgramApplication.status.in_(["submitted", "under_review"]),
        )
        .order_by(ProgramApplication.created_at.desc())
        .first()
    )
    if existing is not None:
        raise ProgramApplicationError("program_application_pending", "An application is already under review.")

    row = ProgramApplication(
        id=str(uuid.uuid4()),
        account_id=account_id,
        legacy_tg_id=int(user.tg_id),
        kind=normalized_kind,
        status="submitted",
        source_name=clean_source or None,
        seats=resolved_seats,
        summary=clean_summary,
        contact=clean_contact or None,
        reward_days=0,
        created_at=now,
        updated_at=now,
    )
    session.add(row)
    session.flush()
    return row


def list_account_applications(session, *, account_id: str, limit: int = 20) -> list[ProgramApplication]:
    return (
        session.query(ProgramApplication)
        .filter(ProgramApplication.account_id == str(account_id))
        .order_by(ProgramApplication.created_at.desc())
        .limit(max(1, min(int(limit), 50)))
        .all()
    )


def cancel_application(session, *, account_id: str, application_id: str, now: datetime) -> ProgramApplication:
    row = (
        session.query(ProgramApplication)
        .filter(
            ProgramApplication.id == str(application_id),
            ProgramApplication.account_id == str(account_id),
        )
        .with_for_update()
        .one_or_none()
    )
    if row is None:
        raise ProgramApplicationError("program_application_not_found", "Application was not found.")
    if row.status in {"submitted", "under_review"}:
        row.status = "cancelled"
        row.updated_at = now
    session.flush()
    return row


def review_application(
    session,
    *,
    application_id: str,
    status: str,
    operator_note: str | None,
    reward_days: int,
    reviewed_by: int,
    now: datetime,
) -> ProgramApplication:
    normalized_status = str(status or "").strip().lower()
    if normalized_status not in {"under_review", "approved", "rejected"}:
        raise ProgramApplicationError("program_status_invalid", "Review status is invalid.")
    days = int(reward_days or 0)
    if days not in {0, 1, 3, 7}:
        raise ProgramApplicationError("program_reward_invalid", "Reward must be 0, 1, 3 or 7 days.")
    row = (
        session.query(ProgramApplication)
        .filter(ProgramApplication.id == str(application_id))
        .with_for_update()
        .one_or_none()
    )
    if row is None:
        raise ProgramApplicationError("program_application_not_found", "Application was not found.")
    if row.status == "rewarded" and days > 0 and int(row.reward_days or 0) == days:
        return row
    if row.status in {"cancelled", "rewarded"}:
        raise ProgramApplicationError("program_application_closed", "Application is already closed.")
    if row.kind == "team_pack" and days:
        raise ProgramApplicationError("program_reward_invalid", "Team-pack requests do not grant bonus days.")
    if days and normalized_status != "approved":
        raise ProgramApplicationError("program_reward_invalid", "A reward requires an approved application.")

    row.status = normalized_status
    row.operator_note = _clean_text(operator_note, max_len=1000) or None
    row.reviewed_by = int(reviewed_by)
    row.reviewed_at = now
    row.updated_at = now
    row.reward_days = days
    if days:
        source = "research_reward" if row.kind == "research" else "competitor_switch"
        grant = grant_internal_bonus_days(
            session,
            account_id=str(row.account_id),
            source=source,
            plan_code=source,
            idempotency_key=f"program-application:v1:{row.id}",
            days=days,
            legacy_tg_id=int(row.legacy_tg_id) if row.legacy_tg_id is not None else None,
            metadata={
                "application_id": str(row.id),
                "program_kind": str(row.kind),
                "reviewed_by": int(reviewed_by),
            },
            now=now,
        )
        row.reward_grant_id = str(grant.id)
        row.status = "rewarded"
        owner = (
            session.query(User)
            .filter(User.account_id == str(row.account_id))
            .order_by(User.tg_id.asc())
            .first()
        )
        if owner is not None:
            rebuild_account_entitlement_projection(session, account_id=str(row.account_id), now=now)
    session.flush()
    return row
