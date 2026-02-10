from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import func

from db import SessionLocal
from models import PointsLedger


MONTHLY_CAP = 300
EXPIRY_DAYS = 90
REFERRAL_PERCENT = 0.10
POINTS_PLAN_CAP_RATIO = 0.50
TOTAL_DISCOUNT_CAP_RATIO = 0.70


@dataclass
class PointsPreview:
    available_points: int
    max_points_by_plan_cap: int
    max_points_by_total_cap: int
    redeemable_points: int


def _now() -> datetime:
    return datetime.utcnow()


def _month_start_utc(now: datetime | None = None) -> datetime:
    n = now or _now()
    return datetime(n.year, n.month, 1)


def get_balance(*, tg_id: int, now: datetime | None = None) -> int:
    n = now or _now()
    s = SessionLocal()
    try:
        bal = (
            s.query(func.coalesce(func.sum(PointsLedger.delta_points), 0))
            .filter(PointsLedger.tg_id == int(tg_id))
            .filter((PointsLedger.expires_at.is_(None)) | (PointsLedger.expires_at > n))
            .scalar()
            or 0
        )
        return int(bal)
    finally:
        s.close()


def available_points(*, tg_id: int, now: datetime | None = None) -> tuple[int, int]:
    n = now or _now()
    s = SessionLocal()
    try:
        total = (
            s.query(func.coalesce(func.sum(PointsLedger.delta_points), 0))
            .filter(PointsLedger.tg_id == int(tg_id))
            .filter((PointsLedger.expires_at.is_(None)) | (PointsLedger.expires_at > n))
            .scalar()
            or 0
        )
        expiring_soon = (
            s.query(func.coalesce(func.sum(PointsLedger.delta_points), 0))
            .filter(PointsLedger.tg_id == int(tg_id))
            .filter(PointsLedger.delta_points > 0)
            .filter(PointsLedger.expires_at.isnot(None))
            .filter(PointsLedger.expires_at <= n + timedelta(days=14))
            .filter(PointsLedger.expires_at > n)
            .scalar()
            or 0
        )
        return int(total), int(expiring_soon)
    finally:
        s.close()


def award_referral_points(
    *,
    tg_id: int,
    paid_stars: int,
    ref_tg_id: int | None = None,
    pay_attempt_id: int | None = None,
) -> int:
    stars = max(0, int(paid_stars))
    if stars <= 0:
        return 0
    raw_points = int(stars * REFERRAL_PERCENT)
    if raw_points <= 0:
        return 0

    now = _now()
    month_start = _month_start_utc(now)
    s = SessionLocal()
    try:
        earned_month = (
            s.query(func.coalesce(func.sum(PointsLedger.delta_points), 0))
            .filter(PointsLedger.tg_id == int(tg_id))
            .filter(PointsLedger.reason == "referral_earned")
            .filter(PointsLedger.created_at >= month_start)
            .scalar()
            or 0
        )
        room = max(0, MONTHLY_CAP - int(earned_month))
        grant = min(raw_points, room)
        if grant <= 0:
            return 0
        row = PointsLedger(
            tg_id=int(tg_id),
            delta_points=int(grant),
            reason="referral_earned",
            ref_tg_id=int(ref_tg_id) if ref_tg_id is not None else None,
            pay_attempt_id=int(pay_attempt_id) if pay_attempt_id is not None else None,
            expires_at=now + timedelta(days=EXPIRY_DAYS),
            created_at=now,
        )
        s.add(row)
        s.commit()
        return int(grant)
    except Exception:
        s.rollback()
        return 0
    finally:
        s.close()


def spend_points(*, tg_id: int, amount: int, pay_attempt_id: int | None = None, reason: str = "payment_redeem") -> int:
    want = max(0, int(amount))
    if want <= 0:
        return 0
    now = _now()
    cur = get_balance(tg_id=int(tg_id), now=now)
    used = min(want, cur)
    if used <= 0:
        return 0
    s = SessionLocal()
    try:
        row = PointsLedger(
            tg_id=int(tg_id),
            delta_points=-int(used),
            reason=(reason or "payment_redeem")[:64],
            pay_attempt_id=int(pay_attempt_id) if pay_attempt_id is not None else None,
            expires_at=None,
            created_at=now,
        )
        s.add(row)
        s.commit()
        return int(used)
    except Exception:
        s.rollback()
        return 0
    finally:
        s.close()


def preview_redeemable_points(
    *,
    tg_id: int,
    plan_price_stars: int,
    first_purchase_discount_pct: float = 0.0,
) -> PointsPreview:
    price = max(0, int(plan_price_stars))
    available = max(0, get_balance(tg_id=int(tg_id)))
    if price <= 0 or available <= 0:
        return PointsPreview(
            available_points=available,
            max_points_by_plan_cap=0,
            max_points_by_total_cap=0,
            redeemable_points=0,
        )

    effective_after_first_discount = int(round(price * (1.0 - max(0.0, float(first_purchase_discount_pct)))))
    effective_after_first_discount = max(0, effective_after_first_discount)
    by_plan_cap = int(effective_after_first_discount * POINTS_PLAN_CAP_RATIO)
    by_total_cap = int(price * TOTAL_DISCOUNT_CAP_RATIO) - int(round(price * max(0.0, float(first_purchase_discount_pct))))
    by_total_cap = max(0, by_total_cap)
    redeemable = max(0, min(available, by_plan_cap, by_total_cap))
    return PointsPreview(
        available_points=available,
        max_points_by_plan_cap=by_plan_cap,
        max_points_by_total_cap=by_total_cap,
        redeemable_points=redeemable,
    )

