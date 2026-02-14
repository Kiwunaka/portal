from __future__ import annotations

from datetime import datetime

import db
from models import Offer


STATUS_ACTIVE = "active"
STATUS_ACCEPTED = "accepted"
STATUS_EXPIRED = "expired"


def _session():
    # Resolve SessionLocal dynamically to stay aligned with reloaded db module in tests/workers.
    return db.SessionLocal()


def create_offer(
    *,
    tg_id: int,
    offer_type: str,
    plan_code: str,
    price_stars: int,
    trigger_reason: str = "",
    expires_at: datetime | None = None,
) -> Offer | None:
    s = _session()
    try:
        row = Offer(
            tg_id=int(tg_id),
            offer_type=(offer_type or "generic")[:32],
            plan_code=(plan_code or "")[:32],
            price_stars=max(0, int(price_stars)),
            status=STATUS_ACTIVE,
            trigger_reason=(trigger_reason or "")[:64],
            expires_at=expires_at,
            created_at=datetime.utcnow(),
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


def get_active_offer(*, tg_id: int, offer_type: str | None = None) -> Offer | None:
    now = datetime.utcnow()
    s = _session()
    try:
        q = s.query(Offer).filter(Offer.tg_id == int(tg_id), Offer.status == STATUS_ACTIVE)
        if offer_type:
            q = q.filter(Offer.offer_type == str(offer_type))
        q = q.filter((Offer.expires_at.is_(None)) | (Offer.expires_at > now))
        return q.order_by(Offer.created_at.desc()).first()
    finally:
        s.close()


def accept_offer(*, offer_id: int, tg_id: int) -> bool:
    now = datetime.utcnow()
    s = _session()
    try:
        row = s.query(Offer).filter(Offer.id == int(offer_id), Offer.tg_id == int(tg_id)).first()
        if not row:
            return False
        row.status = STATUS_ACCEPTED
        row.accepted_at = now
        s.commit()
        return True
    except Exception:
        s.rollback()
        return False
    finally:
        s.close()


def expire_stale_offers() -> int:
    now = datetime.utcnow()
    s = _session()
    try:
        rows = (
            s.query(Offer)
            .filter(Offer.status == STATUS_ACTIVE)
            .filter(Offer.expires_at.isnot(None))
            .filter(Offer.expires_at <= now)
            .all()
        )
        for row in rows:
            row.status = STATUS_EXPIRED
        s.commit()
        return len(rows)
    except Exception:
        s.rollback()
        return 0
    finally:
        s.close()
