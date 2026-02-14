from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import os

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

import db
from models import PointsLedger


MONTHLY_CAP = int(os.getenv("POINTS_MONTHLY_CAP", "300"))
EXPIRY_DAYS = int(os.getenv("POINTS_EXPIRY_DAYS", "90"))
POINTS_PLAN_CAP_RATIO = float(os.getenv("POINTS_PLAN_CAP_RATIO", "0.50"))
TOTAL_DISCOUNT_CAP_RATIO = float(os.getenv("TOTAL_DISCOUNT_CAP_RATIO", "0.70"))

# Format: "bronze:0:10,silver:5:15,gold:15:20,platinum:40:25"
REFERRAL_TIERS_RAW = (
    os.getenv("REFERRAL_TIERS", "bronze:0:10,silver:5:15,gold:15:20,platinum:40:25")
    .strip()
)


@dataclass
class PointsPreview:
    available_points: int
    max_points_by_plan_cap: int
    max_points_by_total_cap: int
    redeemable_points: int


@dataclass
class ReferralTier:
    key: str
    min_paid_referrals: int
    percent: float


def _now() -> datetime:
    return datetime.utcnow()


def _month_start_utc(now: datetime | None = None) -> datetime:
    n = now or _now()
    return datetime(n.year, n.month, 1)


def _parse_referral_tiers(raw: str) -> list[ReferralTier]:
    tiers: list[ReferralTier] = []
    for chunk in (raw or "").split(","):
        item = chunk.strip()
        if not item:
            continue
        parts = [p.strip() for p in item.split(":")]
        if len(parts) != 3:
            continue
        key, min_count_raw, pct_raw = parts
        try:
            min_count = max(0, int(min_count_raw))
            pct = max(0.0, min(100.0, float(pct_raw)))
        except Exception:
            continue
        tiers.append(ReferralTier(key=(key or "tier").lower(), min_paid_referrals=min_count, percent=pct / 100.0))
    if not tiers:
        tiers = [ReferralTier(key="bronze", min_paid_referrals=0, percent=0.10)]
    tiers.sort(key=lambda t: (t.min_paid_referrals, t.percent))
    return tiers


REFERRAL_TIERS = _parse_referral_tiers(REFERRAL_TIERS_RAW)


def _session():
    # Resolve SessionLocal dynamically to avoid stale DB bindings after module reloads.
    return db.SessionLocal()


def _paid_referrals_count(*, tg_id: int) -> int:
    s = _session()
    try:
        # Distinct referred users that produced at least one positive referral-earn event.
        rows = (
            s.query(PointsLedger.ref_tg_id)
            .filter(PointsLedger.tg_id == int(tg_id))
            .filter(PointsLedger.delta_points > 0)
            .filter(PointsLedger.reason.like("referral_earned%"))
            .filter(PointsLedger.ref_tg_id.isnot(None))
            .distinct()
            .all()
        )
        return int(len(rows))
    except SQLAlchemyError:
        # Backward compatibility for DBs/tests where points tables are not present yet.
        return 0
    finally:
        s.close()


def _tier_for_referrals_count(count: int) -> ReferralTier:
    current = REFERRAL_TIERS[0]
    for tier in REFERRAL_TIERS:
        if int(count) >= int(tier.min_paid_referrals):
            current = tier
    return current


def referral_tier_snapshot(*, tg_id: int) -> dict[str, int | float | str | None]:
    paid_referrals = _paid_referrals_count(tg_id=int(tg_id))
    current = _tier_for_referrals_count(paid_referrals)
    nxt = next((t for t in REFERRAL_TIERS if t.min_paid_referrals > paid_referrals), None)
    return {
        "tier_key": current.key,
        "percent": round(float(current.percent) * 100, 2),
        "paid_referrals": int(paid_referrals),
        "next_tier_key": (nxt.key if nxt else None),
        "next_tier_at": (int(nxt.min_paid_referrals) if nxt else None),
    }


def get_balance(*, tg_id: int, now: datetime | None = None) -> int:
    n = now or _now()
    s = _session()
    try:
        bal = (
            s.query(func.coalesce(func.sum(PointsLedger.delta_points), 0))
            .filter(PointsLedger.tg_id == int(tg_id))
            .filter((PointsLedger.expires_at.is_(None)) | (PointsLedger.expires_at > n))
            .scalar()
            or 0
        )
        return int(bal)
    except SQLAlchemyError:
        # Graceful fallback for partially migrated/test databases.
        return 0
    finally:
        s.close()


def available_points(*, tg_id: int, now: datetime | None = None) -> tuple[int, int]:
    n = now or _now()
    s = _session()
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
    except SQLAlchemyError:
        # Graceful fallback for partially migrated/test databases.
        return 0, 0
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
    tier = referral_tier_snapshot(tg_id=int(tg_id))
    pct = max(0.0, float(tier.get("percent") or 0.0) / 100.0)
    raw_points = int(stars * pct)
    if raw_points <= 0:
        return 0

    now = _now()
    month_start = _month_start_utc(now)
    s = _session()
    try:
        earned_month = (
            s.query(func.coalesce(func.sum(PointsLedger.delta_points), 0))
            .filter(PointsLedger.tg_id == int(tg_id))
            .filter(PointsLedger.reason.like("referral_earned%"))
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
            reason=f"referral_earned:{str(tier.get('tier_key') or 'tier')[:24]}",
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
    s = _session()
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
