from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass
from typing import Any

import aiohttp
from fastapi import HTTPException


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PaymentProviderMeta:
    code: str
    label: str
    accent: str
    checkout_hint: str
    supports_bot: bool = True
    supports_webapp: bool = True
    supports_public: bool = True


PROVIDER_META: dict[str, PaymentProviderMeta] = {
    "cardlink": PaymentProviderMeta(
        code="cardlink",
        label="Cardlink",
        accent="Карты и СБП",
        checkout_hint="Прямой платёжный линк без FKWallet.",
    ),
    "pally": PaymentProviderMeta(
        code="pally",
        label="Paypalich",
        accent="Карты и СБП",
        checkout_hint="Резервная касса для быстрой оплаты.",
    ),
    "platima": PaymentProviderMeta(
        code="platima",
        label="Platima",
        accent="Карты и СБП",
        checkout_hint="Отдельный проект со своим callback-контуром.",
    ),
    "freekassa": PaymentProviderMeta(
        code="freekassa",
        label="FreeKassa",
        accent="Legacy fallback",
        checkout_hint="Оставлено как обратная совместимость.",
    ),
}


def normalize_provider(value: str | None) -> str:
    raw = str(value or "").strip().lower()
    return raw if raw in PROVIDER_META else ""


def _csv_env(name: str, default: str = "") -> list[str]:
    return [item.strip().lower() for item in (os.getenv(name) or default).split(",") if item.strip()]


def provider_is_configured(code: str) -> bool:
    provider = normalize_provider(code)
    if not provider:
        return False
    if provider == "cardlink":
        return bool((os.getenv("CARDLINK_API_TOKEN") or "").strip() and (os.getenv("CARDLINK_SHOP_ID") or "").strip())
    if provider == "pally":
        return bool((os.getenv("PALLY_API_TOKEN") or "").strip() and (os.getenv("PALLY_SHOP_ID") or "").strip())
    if provider == "platima":
        return bool((os.getenv("PLATIMA_PROJECT_ID") or "").strip() and (os.getenv("PLATIMA_API_KEY_PROJECT") or "").strip())
    if provider == "freekassa":
        return bool((os.getenv("FK_SITE_SHOP_ID") or "").strip() or (os.getenv("FK_BOT_SHOP_ID") or "").strip())
    return False


def enabled_rub_provider_codes() -> list[str]:
    preferred = _csv_env("RUB_PAYMENT_PROVIDER_ORDER", "cardlink,pally,platima,freekassa")
    allowed = set(_csv_env("RUB_PAYMENT_PROVIDER_ENABLED", ",".join(preferred)))
    out: list[str] = []
    for code in preferred:
        if code in allowed and provider_is_configured(code):
            out.append(code)
    return out


def enabled_provider_catalog() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for code in enabled_rub_provider_codes():
        meta = PROVIDER_META.get(code)
        if not meta:
            continue
        rows.append(
            {
                "code": meta.code,
                "label": meta.label,
                "accent": meta.accent,
                "checkout_hint": meta.checkout_hint,
                "supports_bot": meta.supports_bot,
                "supports_webapp": meta.supports_webapp,
                "supports_public": meta.supports_public,
            }
        )
    return rows


def _bool_int(value: bool) -> int:
    return 1 if bool(value) else 0


def _stringify_amount(amount: float | int) -> str:
    return f"{float(amount or 0):.2f}"


def _cardlink_like_base(provider: str) -> str:
    if provider == "cardlink":
        return (os.getenv("CARDLINK_API_BASE_URL") or "https://cardlink.link/api/v1").strip().rstrip("/")
    return (os.getenv("PALLY_API_BASE_URL") or "https://pally.info/api/v1").strip().rstrip("/")


def _cardlink_like_token(provider: str) -> str:
    return (os.getenv("CARDLINK_API_TOKEN") or "").strip() if provider == "cardlink" else (os.getenv("PALLY_API_TOKEN") or "").strip()


def _cardlink_like_shop_id(provider: str) -> str:
    return (os.getenv("CARDLINK_SHOP_ID") or "").strip() if provider == "cardlink" else (os.getenv("PALLY_SHOP_ID") or "").strip()


async def _cardlink_like_create(
    *,
    provider: str,
    order_id: str,
    amount_rub: float,
    currency: str,
    description: str,
    success_url: str,
    fail_url: str,
    result_url: str,
    refund_url: str,
    chargeback_url: str,
    custom: dict[str, Any],
) -> dict[str, Any]:
    token = _cardlink_like_token(provider)
    shop_id = _cardlink_like_shop_id(provider)
    if not token or not shop_id:
        raise HTTPException(status_code=500, detail=f"{provider} shop is not configured")
    base = _cardlink_like_base(provider)
    form = aiohttp.FormData()
    form.add_field("amount", _stringify_amount(amount_rub))
    form.add_field("order_id", str(order_id))
    form.add_field("shop_id", str(shop_id))
    form.add_field("currency_in", str(currency or "RUB").upper())
    form.add_field("description", str(description or order_id)[:255])
    form.add_field("name", str(description or order_id)[:120])
    form.add_field("type", "normal")
    form.add_field("payer_pays_commission", str(_bool_int(False)))
    form.add_field("success_url", success_url)
    form.add_field("fail_url", fail_url)
    form.add_field("result_url", result_url)
    form.add_field("refund_url", refund_url)
    form.add_field("chargeback_url", chargeback_url)
    form.add_field("custom", json.dumps(custom, ensure_ascii=False, separators=(",", ":")))

    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        async with session.post(f"{base}/bill/create", headers=headers, data=form) as resp:
            raw = await resp.text()
            try:
                body = json.loads(raw) if raw else {}
            except Exception:
                body = {"raw": raw}
            if resp.status >= 400:
                logger.error("%s create error status=%s body=%s", provider, resp.status, raw[:800])
                raise HTTPException(status_code=502, detail=f"{provider} API error: {resp.status}")
            url = ""
            if isinstance(body, dict):
                for key in ("link_page_url", "link_url", "url", "payment_url"):
                    value = body.get(key)
                    if isinstance(value, str) and value.strip():
                        url = value.strip()
                        break
                data = body.get("data")
                if not url and isinstance(data, dict):
                    for key in ("link_page_url", "link_url", "url", "payment_url"):
                        value = data.get(key)
                        if isinstance(value, str) and value.strip():
                            url = value.strip()
                            break
            if not url:
                raise HTTPException(status_code=502, detail=f"{provider} payment URL missing")
            return {"payment_url": url, "remote": body}


def _platima_signature(api_key_project: str, *, order_id: str, project_id: str, amount_rub: float, currency: str) -> str:
    base = f"{api_key_project}{order_id}{project_id}{_stringify_amount(amount_rub)}{str(currency or 'RUB').upper()}"
    return hashlib.sha512(base.encode("utf-8")).hexdigest()


async def _platima_create(
    *,
    order_id: str,
    amount_rub: float,
    currency: str,
    description: str,
    success_url: str,
    fail_url: str,
    result_url: str,
    logo_url: str,
) -> dict[str, Any]:
    project_id = (os.getenv("PLATIMA_PROJECT_ID") or "").strip()
    api_key_project = (os.getenv("PLATIMA_API_KEY_PROJECT") or "").strip()
    if not project_id or not api_key_project:
        raise HTTPException(status_code=500, detail="platima shop is not configured")
    base = (os.getenv("PLATIMA_API_BASE_URL") or "https://platima.com/api/v1").strip().rstrip("/")
    payload = {
        "project_id": project_id,
        "order_id": str(order_id),
        "amount": _stringify_amount(amount_rub),
        "currency": str(currency or "RUB").upper(),
        "description": str(description or order_id)[:255],
        "success_url": success_url,
        "fail_url": fail_url,
        "callback_url": result_url,
    }
    if logo_url:
        payload["logo_url"] = logo_url
    auth = _platima_signature(
        api_key_project,
        order_id=str(order_id),
        project_id=project_id,
        amount_rub=amount_rub,
        currency=currency,
    )
    headers = {"Accept": "application/json", "Content-Type": "application/json", "Authorization": auth}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        async with session.post(f"{base}/acquiring/create-payment-link", headers=headers, json=payload) as resp:
            raw = await resp.text()
            try:
                body = json.loads(raw) if raw else {}
            except Exception:
                body = {"raw": raw}
            if resp.status >= 400:
                logger.error("platima create error status=%s body=%s", resp.status, raw[:800])
                raise HTTPException(status_code=502, detail=f"platima API error: {resp.status}")
            url = ""
            if isinstance(body, dict):
                for key in ("payment_link", "url", "payment_url", "link"):
                    value = body.get(key)
                    if isinstance(value, str) and value.strip():
                        url = value.strip()
                        break
                data = body.get("data")
                if not url and isinstance(data, dict):
                    for key in ("payment_link", "url", "payment_url", "link"):
                        value = data.get(key)
                        if isinstance(value, str) and value.strip():
                            url = value.strip()
                            break
            if not url:
                raise HTTPException(status_code=502, detail="platima payment URL missing")
            return {"payment_url": url, "remote": body}


async def create_rub_payment(
    *,
    provider: str,
    order_id: str,
    amount_rub: float,
    currency: str,
    description: str,
    success_url: str,
    fail_url: str,
    result_url: str,
    refund_url: str,
    chargeback_url: str,
    logo_url: str,
    custom: dict[str, Any],
) -> dict[str, Any]:
    provider = normalize_provider(provider)
    if provider in {"cardlink", "pally"}:
        return await _cardlink_like_create(
            provider=provider,
            order_id=order_id,
            amount_rub=amount_rub,
            currency=currency,
            description=description,
            success_url=success_url,
            fail_url=fail_url,
            result_url=result_url,
            refund_url=refund_url,
            chargeback_url=chargeback_url,
            custom=custom,
        )
    if provider == "platima":
        return await _platima_create(
            order_id=order_id,
            amount_rub=amount_rub,
            currency=currency,
            description=description,
            success_url=success_url,
            fail_url=fail_url,
            result_url=result_url,
            logo_url=logo_url,
        )
    raise HTTPException(status_code=400, detail=f"Unsupported RUB provider: {provider}")


def verify_callback_signature(provider: str, payload: dict[str, Any]) -> bool:
    provider = normalize_provider(provider)
    if provider in {"cardlink", "pally"}:
        token = _cardlink_like_token(provider)
        amount = str(payload.get("OutSum") or payload.get("out_sum") or payload.get("amount") or "").strip()
        inv_id = str(payload.get("InvId") or payload.get("inv_id") or payload.get("order_id") or "").strip()
        sign = str(payload.get("SignatureValue") or payload.get("signature") or payload.get("sign") or "").strip().upper()
        if not token or not amount or not inv_id or not sign:
            return False
        expected = hashlib.md5(f"{amount}:{inv_id}:{token}".encode("utf-8")).hexdigest().upper()
        return expected == sign
    if provider == "platima":
        api_key_project = (os.getenv("PLATIMA_API_KEY_PROJECT") or "").strip()
        project_id = str(payload.get("project_id") or "").strip()
        payment_id = str(payload.get("id") or payload.get("payment_id") or "").strip()
        order_id = str(payload.get("order_id") or "").strip()
        amount = str(payload.get("amount") or "").strip()
        currency = str(payload.get("currency") or "RUB").strip().upper()
        sign = str(payload.get("sign") or payload.get("signature") or "").strip().lower()
        if not api_key_project or not payment_id or not order_id or not project_id or not amount or not sign:
            return False
        expected = hashlib.sha256(f"{api_key_project}{payment_id}{order_id}{project_id}{amount}{currency}".encode("utf-8")).hexdigest()
        return expected == sign
    return False


def callback_ids(provider: str, payload: dict[str, Any]) -> tuple[str, str]:
    provider = normalize_provider(provider)
    if provider in {"cardlink", "pally"}:
        order_id = str(payload.get("InvId") or payload.get("inv_id") or payload.get("order_id") or "").strip()
        external_id = str(payload.get("TrsId") or payload.get("trs_id") or order_id).strip()
        return order_id, external_id
    if provider == "platima":
        order_id = str(payload.get("order_id") or "").strip()
        external_id = str(payload.get("id") or payload.get("payment_id") or order_id).strip()
        return order_id, external_id
    return "", ""


def callback_status(provider: str, payload: dict[str, Any]) -> str:
    provider = normalize_provider(provider)
    if provider in {"cardlink", "pally"}:
        return str(payload.get("Status") or payload.get("status") or "").strip().lower()
    if provider == "platima":
        return str(payload.get("status") or payload.get("payment_status") or "").strip().lower()
    return ""
