from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import db
from models import GiftCard, User
from shared_surface_facts import get_tariff_catalog


GIFT_CARD_TYPES: dict[str, dict[str, Any]] = {
    "mini": {"days": 7, "stars": 59, "name": "Mini"},
    "standard": {"days": 30, "stars": 249, "name": "Standard"},
    "premium": {"days": 90, "stars": 699, "name": "Premium"},
}


def _plan_card_types() -> dict[str, dict[str, Any]]:
    try:
        catalog = get_tariff_catalog()
    except Exception:
        return {}
    rows: dict[str, dict[str, Any]] = {}
    for plan in list((catalog or {}).get("plans") or []):
        if not isinstance(plan, dict):
            continue
        code = str(plan.get("code") or "").strip().lower()
        days = int(plan.get("duration_days") or plan.get("days") or 0)
        if not code or days <= 0:
            continue
        rows[code] = {
            "days": days,
            "stars": int(plan.get("amount_stars") or 0),
            "name": str(plan.get("label") or code),
            "plan_code": code,
        }
    return rows


def _card_type_info(card_type: str) -> dict[str, Any] | None:
    normalized = str(card_type or "").strip().lower()
    if not normalized:
        return None
    legacy = GIFT_CARD_TYPES.get(normalized)
    if legacy:
        return {**legacy, "legacy_type": normalized}
    plan = _plan_card_types().get(normalized)
    if plan:
        return {**plan, "plan_code": normalized}
    return None


def _session():
    # Resolve SessionLocal dynamically to avoid stale DB bindings after module reloads.
    return db.SessionLocal()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _generate_sub_token() -> str:
    return secrets.token_urlsafe(32)


def _generate_gift_code() -> str:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    token = "".join(secrets.choice(alphabet) for _ in range(8))
    return f"POKROV-{token[:4]}-{token[4:]}"


def create_gift_card(*, buyer_tg_id: int, card_type: str) -> str | None:
    ctype = (card_type or "").strip().lower()
    if ctype not in GIFT_CARD_TYPES:
        return None

    s = _session()
    try:
        code = ""
        for _ in range(30):
            candidate = _generate_gift_code()
            exists = s.query(GiftCard.id).filter(GiftCard.code == candidate).first()
            if not exists:
                code = candidate
                break
        if not code:
            return None

        row = GiftCard(code=code, card_type=ctype, created_by=int(buyer_tg_id))
        s.add(row)
        s.commit()
        return code
    except Exception:
        s.rollback()
        return None
    finally:
        s.close()


def get_gift_card(code: str) -> dict[str, Any] | None:
    norm = (code or "").strip().upper()
    if not norm:
        return None

    s = _session()
    try:
        row = s.query(GiftCard).filter(GiftCard.code == norm).first()
        if not row:
            return None
        meta = _card_type_info(str(row.card_type or "")) or {}
        return {
            "code": str(row.code),
            "type": str(row.card_type or ""),
            "days": int(meta.get("days") or 0),
            "stars": int(meta.get("stars") or 0),
            "created_by": int(row.created_by or 0),
            "redeemed": bool(row.redeemed_by),
            "redeemed_by": int(row.redeemed_by) if row.redeemed_by is not None else None,
            "redeemed_at": row.redeemed_at.isoformat() if row.redeemed_at else None,
        }
    finally:
        s.close()


async def redeem_gift_card(*, code: str, recipient_tg_id: int, require_tos: bool = True) -> dict[str, Any]:
    norm = (code or "").strip().upper()
    if not norm:
        return {"ok": False, "error": "invalid_code", "message": "Код не указан"}

    s = _session()
    try:
        card = s.query(GiftCard).filter(GiftCard.code == norm).first()
        if not card:
            return {"ok": False, "error": "not_found", "message": "Код не найден"}
        if card.redeemed_by is not None:
            return {"ok": False, "error": "already_redeemed", "message": "Код уже активирован"}
        if int(card.created_by or 0) == int(recipient_tg_id):
            return {"ok": False, "error": "self_redeem", "message": "Нельзя активировать собственный код"}

        card_info = _card_type_info(str(card.card_type or ""))
        if not card_info:
            return {"ok": False, "error": "unknown_type", "message": "Тип кода не поддерживается"}

        now = _utcnow()
        user = s.query(User).filter(User.tg_id == int(recipient_tg_id)).first()
        if not user:
            user = User(
                tg_id=int(recipient_tg_id),
                uuid=str(uuid.uuid4()),
                email=f"User_{int(recipient_tg_id)}",
                sub_type="PAID",
                created_at=now,
                expiry_at=now,
                is_active=True,
                stars_paid=0,
                total_gb=0,
                trial_used=False,
                sub_token=_generate_sub_token(),
                tos_accepted=False,
            )
            s.add(user)
            s.flush()

        if require_tos and not bool(getattr(user, "tos_accepted", False)):
            return {"ok": False, "error": "tos_required", "message": "Сначала примите оферту"}

        days = int(card_info.get("days") or 0)
        if days <= 0:
            return {"ok": False, "error": "invalid_days", "message": "Некорректный срок действия"}

        current_expiry = user.expiry_at if (user.expiry_at and user.expiry_at > now) else now
        # FREE -> PAID gift should start from now.
        if (user.sub_type or "").upper().strip() == "FREE":
            current_expiry = now

        user.expiry_at = current_expiry + timedelta(days=days)
        user.sub_type = "PAID"
        user.is_active = True
        if str(card_info.get("plan_code") or "").strip():
            user.current_plan_code = str(card_info.get("plan_code") or "").strip().lower()
        if not user.sub_token:
            user.sub_token = _generate_sub_token()

        updated = (
            s.query(GiftCard)
            .filter(GiftCard.id == card.id, GiftCard.redeemed_by.is_(None))
            .update(
                {
                    GiftCard.redeemed_by: int(recipient_tg_id),
                    GiftCard.redeemed_at: now,
                },
                synchronize_session=False,
            )
        )
        if int(updated or 0) != 1:
            s.rollback()
            return {"ok": False, "error": "already_redeemed", "message": "Код уже активирован"}
        redeemed_card_type = str(card.card_type or "")
        s.commit()

        user_uuid = str(user.uuid or "")
        user_email = str(user.email or f"User_{int(recipient_tg_id)}")
        sub_token = str(user.sub_token or "")
        expiry_at_iso = user.expiry_at.isoformat() if user.expiry_at else None
    except Exception:
        s.rollback()
        return {"ok": False, "error": "db_error", "message": "Не удалось применить код"}
    finally:
        s.close()

    sync_ok = False
    try:
        from control_panel import ControlPanel

        panel = ControlPanel()
        try:
            await panel.login()
            existing = await panel.get_existing_client(int(recipient_tg_id))
            if existing:
                sync_ok = await panel.update_client_traffic(int(recipient_tg_id), 0)
            else:
                sync_ok = await panel.add_client(
                    user_uuid,
                    user_email,
                    "PAID",
                    0,
                    int(recipient_tg_id),
                    sub_token,
                )
        finally:
            await panel.close()
    except Exception:
        sync_ok = False

    return {
        "ok": True,
        "code": norm,
        "days": int((_card_type_info(redeemed_card_type) or {}).get("days") or 0),
        "card_type": redeemed_card_type,
        "expiry_at": expiry_at_iso,
        "sync_ok": bool(sync_ok),
    }
