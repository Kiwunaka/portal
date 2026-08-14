from __future__ import annotations

from datetime import datetime, timedelta, timezone

from db import SessionLocal
from models import AcquisitionSession, PayAttempt


STATUS_STARTED = "started"
STATUS_INVOICE_SENT = "invoice_sent"
STATUS_PAID = "paid"
STATUS_ABANDONED = "abandoned"
STATUS_FAILED = "failed"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def start_attempt(
    *,
    tg_id: int,
    source: str,
    plan_code: str,
    amount_stars: int,
    currency: str = "XTR",
    offer_id: int | None = None,
    invoice_payload: str | None = None,
) -> PayAttempt | None:
    now = _utcnow()
    s = SessionLocal()
    try:
        acquisition = (
            s.query(AcquisitionSession)
            .filter(AcquisitionSession.bound_tg_id == int(tg_id))
            .filter(AcquisitionSession.first_touch_at <= now)
            .filter(AcquisitionSession.expires_at > now)
            .order_by(AcquisitionSession.last_touch_at.desc(), AcquisitionSession.id.desc())
            .first()
        )
        row = PayAttempt(
            tg_id=int(tg_id),
            source=(source or "bot")[:32],
            plan_code=(plan_code or "").strip()[:32],
            amount_stars=max(0, int(amount_stars)),
            currency=(currency or "XTR")[:12],
            status=STATUS_STARTED,
            invoice_payload=(invoice_payload[:255] if invoice_payload else None),
            offer_id=offer_id,
            acquisition_session_id=(str(acquisition.id) if acquisition is not None else None),
            started_at=now,
            updated_at=now,
        )
        s.add(row)
        s.commit()
        s.refresh(row)
        return row
    except Exception:
        s.rollback()
        return None
    finally:
        s.close()


def mark_invoice_sent(
    *,
    attempt_id: int | None = None,
    invoice_payload: str | None = None,
    set_invoice_payload: str | None = None,
) -> bool:
    return _set_status(
        attempt_id=attempt_id,
        invoice_payload=invoice_payload,
        status=STATUS_INVOICE_SENT,
        set_invoice_payload=set_invoice_payload,
    )


def mark_paid(*, attempt_id: int | None = None, invoice_payload: str | None = None) -> bool:
    now = _utcnow()
    s = SessionLocal()
    try:
        q = s.query(PayAttempt)
        if attempt_id:
            q = q.filter(PayAttempt.id == int(attempt_id))
        elif invoice_payload:
            q = q.filter(PayAttempt.invoice_payload == str(invoice_payload))
        else:
            return False
        row = q.order_by(PayAttempt.id.desc()).first()
        if not row:
            return False
        row.status = STATUS_PAID
        row.paid_at = row.paid_at or now
        row.updated_at = now
        s.commit()
        return True
    except Exception:
        s.rollback()
        return False
    finally:
        s.close()


def mark_abandoned(*, attempt_id: int) -> bool:
    now = _utcnow()
    s = SessionLocal()
    try:
        row = s.query(PayAttempt).filter(PayAttempt.id == int(attempt_id)).first()
        if not row:
            return False
        row.status = STATUS_ABANDONED
        row.updated_at = now
        if not row.abandoned_notified_at:
            row.abandoned_notified_at = now
        s.commit()
        return True
    except Exception:
        s.rollback()
        return False
    finally:
        s.close()


def mark_abandoned_notified(*, attempt_id: int) -> bool:
    now = _utcnow()
    s = SessionLocal()
    try:
        row = s.query(PayAttempt).filter(PayAttempt.id == int(attempt_id)).first()
        if not row:
            return False
        row.abandoned_notified_at = now
        row.updated_at = now
        s.commit()
        return True
    except Exception:
        s.rollback()
        return False
    finally:
        s.close()


def get_attempt_by_payload(*, invoice_payload: str) -> PayAttempt | None:
    s = SessionLocal()
    try:
        return s.query(PayAttempt).filter(PayAttempt.invoice_payload == str(invoice_payload)).first()
    finally:
        s.close()


def resolve_pending_attempt_for_payment(
    *,
    tg_id: int,
    amount_stars: int,
    currency: str = "XTR",
    within_hours: int = 24,
) -> PayAttempt | None:
    """
    Best-effort resolver for payments where invoice payload is not recognized.
    Picks the newest pending attempt for the user with the same amount/currency.
    """
    cutoff = _utcnow() - timedelta(hours=max(1, int(within_hours)))
    s = SessionLocal()
    try:
        row = (
            s.query(PayAttempt)
            .filter(PayAttempt.tg_id == int(tg_id))
            .filter(PayAttempt.amount_stars == max(0, int(amount_stars)))
            .filter(PayAttempt.currency == (currency or "XTR")[:12])
            .filter(PayAttempt.status.in_([STATUS_STARTED, STATUS_INVOICE_SENT]))
            .filter(PayAttempt.started_at >= cutoff)
            .order_by(PayAttempt.id.desc())
            .first()
        )
        if not row:
            return None
        # Materialize immutable snapshot to avoid detached-session surprises.
        out = PayAttempt(
            id=row.id,
            tg_id=row.tg_id,
            source=row.source,
            plan_code=row.plan_code,
            amount_stars=row.amount_stars,
            currency=row.currency,
            status=row.status,
            invoice_payload=row.invoice_payload,
            offer_id=row.offer_id,
            started_at=row.started_at,
            updated_at=row.updated_at,
            paid_at=row.paid_at,
            abandoned_notified_at=row.abandoned_notified_at,
        )
        return out
    finally:
        s.close()


def find_abandoned_candidates(*, older_than_minutes: int = 60, limit: int = 500) -> list[PayAttempt]:
    cutoff = _utcnow() - timedelta(minutes=max(1, int(older_than_minutes)))
    s = SessionLocal()
    try:
        rows = (
            s.query(PayAttempt)
            .filter(PayAttempt.status.in_([STATUS_STARTED, STATUS_INVOICE_SENT]))
            .filter(PayAttempt.started_at <= cutoff)
            .filter(PayAttempt.abandoned_notified_at.is_(None))
            .order_by(PayAttempt.started_at.asc())
            .limit(max(1, int(limit)))
            .all()
        )
        return rows
    finally:
        s.close()


def _set_status(
    *,
    attempt_id: int | None,
    invoice_payload: str | None,
    status: str,
    set_invoice_payload: str | None = None,
) -> bool:
    now = _utcnow()
    s = SessionLocal()
    try:
        q = s.query(PayAttempt)
        if attempt_id:
            q = q.filter(PayAttempt.id == int(attempt_id))
        elif invoice_payload:
            q = q.filter(PayAttempt.invoice_payload == str(invoice_payload))
        else:
            return False
        row = q.order_by(PayAttempt.id.desc()).first()
        if not row:
            return False
        row.status = status
        if set_invoice_payload:
            row.invoice_payload = str(set_invoice_payload)[:255]
        row.updated_at = now
        s.commit()
        return True
    except Exception:
        s.rollback()
        return False
    finally:
        s.close()
