from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import aiohttp
from fastapi import HTTPException

from outbound_http import OutboundHttpError, PaymentHttpRegistry


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
    "lavatop": PaymentProviderMeta(
        code="lavatop",
        label="Lava.top",
        accent="Cards and SBP",
        checkout_hint="Primary Open Beta checkout candidate; requires authenticated webhooks.",
    ),
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

PUBLIC_BETA_PROVIDER_CODES = ("lavatop",)


async def _post_payment_object(
    http_registry: PaymentHttpRegistry | None,
    *,
    provider: str,
    operation: str,
    url: str,
    headers: dict[str, str],
    json_body: dict[str, Any] | None = None,
    form_body: Any | None = None,
) -> dict[str, Any]:
    if http_registry is None:
        raise HTTPException(status_code=503, detail="payment HTTP client unavailable")
    try:
        result = await http_registry.post_object(
            provider=provider,
            operation=operation,
            url=url,
            headers=headers,
            json_body=json_body,
            form_body=form_body,
        )
    except OutboundHttpError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"{provider} API error: {exc.code}",
        ) from exc
    if result.status >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"{provider} API error: {result.status}",
        )
    return result.body


def normalize_provider(value: str | None) -> str:
    raw = str(value or "").strip().lower()
    return raw if raw in PROVIDER_META else ""


def _csv_env(name: str, default: str = "") -> list[str]:
    return [
        item.strip().lower()
        for item in (os.getenv(name) or default).split(",")
        if item.strip()
    ]


def provider_is_configured(code: str) -> bool:
    provider = normalize_provider(code)
    if not provider:
        return False
    if provider == "lavatop":
        has_invoice_config = bool(
            (os.getenv("LAVATOP_API_KEY") or "").strip()
            and _lavatop_any_offer_configured()
        )
        has_webhook_config = bool(
            (os.getenv("LAVATOP_WEBHOOK_API_KEY") or "").strip()
            or (
                (os.getenv("LAVATOP_WEBHOOK_BASIC_USERNAME") or "").strip()
                and (os.getenv("LAVATOP_WEBHOOK_BASIC_PASSWORD") or "").strip()
            )
        )
        return bool(has_invoice_config and has_webhook_config)
    if provider == "cardlink":
        return bool(
            (os.getenv("CARDLINK_API_TOKEN") or "").strip()
            and (os.getenv("CARDLINK_SHOP_ID") or "").strip()
        )
    if provider == "pally":
        return bool(
            (os.getenv("PALLY_API_TOKEN") or "").strip()
            and (os.getenv("PALLY_SHOP_ID") or "").strip()
        )
    if provider == "platima":
        return bool(
            (os.getenv("PLATIMA_PROJECT_ID") or "").strip()
            and (os.getenv("PLATIMA_API_KEY_PROJECT") or "").strip()
        )
    if provider == "freekassa":
        return bool(
            (os.getenv("FK_SITE_SHOP_ID") or "").strip()
            or (os.getenv("FK_BOT_SHOP_ID") or "").strip()
        )
    return False


def enabled_rub_provider_codes() -> list[str]:
    preferred = _csv_env("RUB_PAYMENT_PROVIDER_ORDER", "lavatop")
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


def public_provider_is_configured_for_plan(
    code: str, plan_code: str | None = None
) -> bool:
    """Fail-closed readiness for a new public-beta order.

    Historical provider adapters remain available for callbacks and replay, but
    new public checkout is Lava-only. A universal offer is safe for every plan
    only when dynamic amounts are explicitly enabled; otherwise an exact
    per-plan offer is required.
    """
    provider = normalize_provider(code)
    if provider not in PUBLIC_BETA_PROVIDER_CODES or not provider_is_configured(
        provider
    ):
        return False
    normalized_plan = str(plan_code or "").strip().lower()
    global_offer = bool((os.getenv("LAVATOP_OFFER_ID") or "").strip())
    if global_offer and _env_bool("LAVATOP_DYNAMIC_AMOUNT_ENABLED", default=False):
        return True
    if not normalized_plan:
        return any(
            key.startswith("LAVATOP_OFFER_ID_") and bool(str(value or "").strip())
            for key, value in os.environ.items()
        )
    return bool(
        (os.getenv(f"LAVATOP_OFFER_ID_{_env_suffix(normalized_plan)}") or "").strip()
    )


def enabled_public_provider_catalog(
    *, plan_code: str | None = None
) -> list[dict[str, Any]]:
    enabled = set(enabled_rub_provider_codes())
    rows: list[dict[str, Any]] = []
    for code in PUBLIC_BETA_PROVIDER_CODES:
        if code not in enabled or not public_provider_is_configured_for_plan(
            code, plan_code
        ):
            continue
        meta = PROVIDER_META[code]
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


def payment_method_capabilities(code: str) -> list[dict[str, Any]]:
    """Return the server-owned checkout method availability for one provider."""

    provider = normalize_provider(code)
    if provider == "lavatop":
        rows = (
            ("sbp", "СБП", "Через приложение банка", "LAVATOP_SBP_ENABLED"),
            ("card", "Карта", "Банковская карта", "LAVATOP_CARD_ENABLED"),
        )
        return [
            {
                "code": method,
                "label": label,
                "hint": hint,
                "available": _env_bool(env_name, default=True),
                "unavailable_reason": (
                    None
                    if _env_bool(env_name, default=True)
                    else "temporarily_unavailable"
                ),
            }
            for method, label, hint, env_name in rows
        ]
    return []


def _bool_int(value: bool) -> int:
    return 1 if bool(value) else 0


def _stringify_amount(amount: float | int) -> str:
    return f"{float(amount or 0):.2f}"


def _env_bool(name: str, default: bool = False) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    if not raw:
        return bool(default)
    return raw in {"1", "true", "yes", "on"}


def _nested_value(payload: dict[str, Any], *path: str) -> str:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict):
            return ""
        current = current.get(key)
    return str(current or "").strip()


def _env_suffix(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", str(value or "").upper()).strip("_")


def _lavatop_offer_id(custom: dict[str, Any]) -> str:
    plan_code = _env_suffix(str((custom or {}).get("plan_code") or ""))
    if plan_code:
        plan_offer = (os.getenv(f"LAVATOP_OFFER_ID_{plan_code}") or "").strip()
        if plan_offer:
            return plan_offer
    return (os.getenv("LAVATOP_OFFER_ID") or "").strip()


def _lavatop_any_offer_configured() -> bool:
    if (os.getenv("LAVATOP_OFFER_ID") or "").strip():
        return True
    return any(
        key.startswith("LAVATOP_OFFER_ID_") and bool(str(value or "").strip())
        for key, value in os.environ.items()
    )


def _lavatop_base() -> str:
    return (
        (os.getenv("LAVATOP_API_BASE_URL") or "https://gate.lava.top")
        .strip()
        .rstrip("/")
    )


def _lavatop_email(*, order_id: str, custom: dict[str, Any]) -> str:
    direct = str(
        (custom or {}).get("email") or os.getenv("LAVATOP_DEFAULT_BUYER_EMAIL") or ""
    ).strip()
    if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", direct):
        return direct
    domain = re.sub(
        r"[^a-zA-Z0-9.-]",
        "",
        (os.getenv("LAVATOP_BUYER_EMAIL_DOMAIN") or "pokrov.space").strip(),
    )
    if not domain or "." not in domain:
        domain = "pokrov.space"
    local = (
        re.sub(r"[^a-zA-Z0-9._+-]", "_", str(order_id or "order").strip())[:64]
        or "order"
    )
    return f"pokrov+{local}@{domain}"


def _extract_payment_url(body: dict[str, Any]) -> str:
    for key in (
        "location",
        "paymentUrl",
        "payment_url",
        "paymentURL",
        "url",
        "redirect_url",
        "link",
    ):
        value = body.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for container_key in ("data", "invoice", "contract", "result"):
        nested = body.get(container_key)
        if isinstance(nested, dict):
            url = _extract_payment_url(nested)
            if url:
                return url
    return ""


def parse_freekassa_payment_url(
    body: dict[str, Any],
    fallback_order_id: str = "",
    source: str = "site",
) -> str:
    """Return only a provider-supplied checkout URL on the configured HTTPS host.

    The compatibility arguments remain for legacy callers. They are never used
    to manufacture a local checkout URL: the signed local SCI builder owns that
    separate path and has the authoritative positive amount.
    """

    del fallback_order_id, source
    if not isinstance(body, dict):
        raise HTTPException(status_code=502, detail="freekassa payment URL missing")
    raw_url = _extract_payment_url(body)
    if not raw_url:
        raise HTTPException(status_code=502, detail="freekassa payment URL missing")

    configured = (
        str(os.getenv("FREEKASSA_PAY_HOST") or "pay.fk.money").strip().strip("/")
    )
    configured_url = configured if "://" in configured else f"https://{configured}"
    expected = urlparse(configured_url)
    parsed = urlparse(raw_url)
    try:
        expected_port = expected.port
        parsed_port = parsed.port
    except ValueError:
        raise HTTPException(
            status_code=502, detail="freekassa payment URL invalid"
        ) from None
    if (
        any(ord(char) < 33 for char in raw_url)
        or expected.scheme != "https"
        or parsed.scheme != "https"
        or not expected.hostname
        or parsed.hostname != expected.hostname
        or parsed_port != expected_port
        or parsed.username is not None
        or parsed.password is not None
        or not parsed.path
    ):
        raise HTTPException(status_code=502, detail="freekassa payment URL invalid")
    return raw_url


async def _lavatop_create(
    *,
    http_registry: PaymentHttpRegistry | None,
    order_id: str,
    amount_rub: float,
    currency: str,
    description: str,
    custom: dict[str, Any],
) -> dict[str, Any]:
    api_key = (os.getenv("LAVATOP_API_KEY") or "").strip()
    offer_id = _lavatop_offer_id(custom)
    if not api_key or not offer_id:
        raise HTTPException(status_code=500, detail="lavatop shop is not configured")
    currency_code = str(currency or "RUB").strip().upper() or "RUB"
    source = (
        str((custom or {}).get("source") or "checkout").strip().lower()[:64]
        or "checkout"
    )
    plan_code = str((custom or {}).get("plan_code") or "").strip().lower()[:64]
    payload: dict[str, Any] = {
        "email": _lavatop_email(order_id=order_id, custom=custom or {}),
        "offerId": offer_id,
        "currency": currency_code,
        "buyerLanguage": (os.getenv("LAVATOP_BUYER_LANGUAGE") or "RU")
        .strip()
        .upper()[:2]
        or "RU",
        "clientUtm": {
            "utm_source": "pokrov",
            "utm_medium": source,
            "utm_campaign": str((custom or {}).get("campaign") or "").strip()[:255],
            "utm_term": plan_code,
            "utm_content": str(order_id or "").strip()[:255],
        },
    }
    payment_provider = (
        str(
            (custom or {}).get("lavatop_payment_provider")
            or os.getenv("LAVATOP_PAYMENT_PROVIDER")
            or ""
        )
        .strip()
        .upper()
    )
    payment_method = (
        str(
            (custom or {}).get("lavatop_payment_method")
            or os.getenv("LAVATOP_PAYMENT_METHOD")
            or ""
        )
        .strip()
        .upper()
    )
    periodicity = (os.getenv("LAVATOP_PERIODICITY") or "").strip().upper()
    if payment_provider:
        payload["paymentProvider"] = payment_provider
    if payment_method:
        payload["paymentMethod"] = payment_method
    if periodicity:
        payload["periodicity"] = periodicity
    if _env_bool("LAVATOP_DYNAMIC_AMOUNT_ENABLED", default=False):
        payload["amount"] = float(amount_rub or 0)
    promo_code = str((custom or {}).get("promo_code") or "").strip()[:64]
    if promo_code:
        payload["clientUtm"]["utm_campaign"] = (
            payload["clientUtm"]["utm_campaign"] or promo_code
        )

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Api-Key": api_key,
    }
    body = await _post_payment_object(
        http_registry,
        provider="lavatop",
        operation="create_invoice",
        url=f"{_lavatop_base()}/api/v3/invoice",
        headers=headers,
        json_body=payload,
    )
    url = _extract_payment_url(body)
    if not url:
        raise HTTPException(status_code=502, detail="lavatop payment URL missing")
    remote = dict(body)
    remote.setdefault("request", payload)
    return {"payment_url": url, "remote": remote}


def _cardlink_like_base(provider: str) -> str:
    if provider == "cardlink":
        return (
            (os.getenv("CARDLINK_API_BASE_URL") or "https://cardlink.link/api/v1")
            .strip()
            .rstrip("/")
        )
    return (
        (os.getenv("PALLY_API_BASE_URL") or "https://pally.info/api/v1")
        .strip()
        .rstrip("/")
    )


def _cardlink_like_token(provider: str) -> str:
    return (
        (os.getenv("CARDLINK_API_TOKEN") or "").strip()
        if provider == "cardlink"
        else (os.getenv("PALLY_API_TOKEN") or "").strip()
    )


def _cardlink_like_shop_id(provider: str) -> str:
    return (
        (os.getenv("CARDLINK_SHOP_ID") or "").strip()
        if provider == "cardlink"
        else (os.getenv("PALLY_SHOP_ID") or "").strip()
    )


async def _cardlink_like_create(
    *,
    http_registry: PaymentHttpRegistry | None,
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
        raise HTTPException(
            status_code=500, detail=f"{provider} shop is not configured"
        )
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
    form.add_field(
        "custom", json.dumps(custom, ensure_ascii=False, separators=(",", ":"))
    )

    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    body = await _post_payment_object(
        http_registry,
        provider=provider,
        operation="create_bill",
        url=f"{base}/bill/create",
        headers=headers,
        form_body=form,
    )
    url = ""
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


def _platima_signature(
    api_key_project: str,
    *,
    order_id: str,
    project_id: str,
    amount_rub: float,
    currency: str,
) -> str:
    base = f"{api_key_project}{order_id}{project_id}{_stringify_amount(amount_rub)}{str(currency or 'RUB').upper()}"
    return hashlib.sha512(base.encode("utf-8")).hexdigest()


async def _platima_create(
    *,
    http_registry: PaymentHttpRegistry | None,
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
    base = (
        (os.getenv("PLATIMA_API_BASE_URL") or "https://platima.com/api/v1")
        .strip()
        .rstrip("/")
    )
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
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": auth,
    }
    body = await _post_payment_object(
        http_registry,
        provider="platima",
        operation="create_payment_link",
        url=f"{base}/acquiring/create-payment-link",
        headers=headers,
        json_body=payload,
    )
    url = ""
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
    http_registry: PaymentHttpRegistry | None = None,
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
            http_registry=http_registry,
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
            http_registry=http_registry,
            order_id=order_id,
            amount_rub=amount_rub,
            currency=currency,
            description=description,
            success_url=success_url,
            fail_url=fail_url,
            result_url=result_url,
            logo_url=logo_url,
        )
    if provider == "lavatop":
        return await _lavatop_create(
            http_registry=http_registry,
            order_id=order_id,
            amount_rub=amount_rub,
            currency=currency,
            description=description,
            custom=custom,
        )
    raise HTTPException(status_code=400, detail=f"Unsupported RUB provider: {provider}")


def verify_callback_signature(provider: str, payload: dict[str, Any]) -> bool:
    provider = normalize_provider(provider)
    if provider in {"cardlink", "pally"}:
        token = _cardlink_like_token(provider)
        amount = str(
            payload.get("OutSum")
            or payload.get("out_sum")
            or payload.get("amount")
            or ""
        ).strip()
        inv_id = str(
            payload.get("InvId")
            or payload.get("inv_id")
            or payload.get("order_id")
            or ""
        ).strip()
        sign = (
            str(
                payload.get("SignatureValue")
                or payload.get("signature")
                or payload.get("sign")
                or ""
            )
            .strip()
            .upper()
        )
        if not token or not amount or not inv_id or not sign:
            return False
        expected = (
            hashlib.md5(f"{amount}:{inv_id}:{token}".encode("utf-8"))
            .hexdigest()
            .upper()
        )
        return expected == sign
    if provider == "platima":
        api_key_project = (os.getenv("PLATIMA_API_KEY_PROJECT") or "").strip()
        project_id = str(payload.get("project_id") or "").strip()
        payment_id = str(payload.get("id") or payload.get("payment_id") or "").strip()
        order_id = str(payload.get("order_id") or "").strip()
        amount = str(payload.get("amount") or "").strip()
        currency = str(payload.get("currency") or "RUB").strip().upper()
        sign = (
            str(payload.get("sign") or payload.get("signature") or "").strip().lower()
        )
        if (
            not api_key_project
            or not payment_id
            or not order_id
            or not project_id
            or not amount
            or not sign
        ):
            return False
        expected = hashlib.sha256(
            f"{api_key_project}{payment_id}{order_id}{project_id}{amount}{currency}".encode(
                "utf-8"
            )
        ).hexdigest()
        return expected == sign
    return False


def callback_ids(provider: str, payload: dict[str, Any]) -> tuple[str, str]:
    provider = normalize_provider(provider)
    if provider == "lavatop":
        order_id = (
            str(payload.get("order_id") or "").strip()
            or _nested_value(payload, "clientUtm", "utm_content")
            or _nested_value(payload, "client_utm", "utm_content")
        )
        external_id = str(
            payload.get("contractId")
            or payload.get("contract_id")
            or payload.get("id")
            or order_id
        ).strip()
        return order_id, external_id
    if provider in {"cardlink", "pally"}:
        order_id = str(
            payload.get("InvId")
            or payload.get("inv_id")
            or payload.get("order_id")
            or ""
        ).strip()
        external_id = str(
            payload.get("TrsId") or payload.get("trs_id") or order_id
        ).strip()
        return order_id, external_id
    if provider == "platima":
        order_id = str(payload.get("order_id") or "").strip()
        external_id = str(
            payload.get("id") or payload.get("payment_id") or order_id
        ).strip()
        return order_id, external_id
    return "", ""


def callback_status(provider: str, payload: dict[str, Any]) -> str:
    provider = normalize_provider(provider)
    if provider == "lavatop":
        event_type = (
            str(payload.get("eventType") or payload.get("event_type") or "")
            .strip()
            .lower()
        )
        if event_type in {"payment.success", "subscription.recurring.payment.success"}:
            return str(payload.get("status") or "completed").strip().lower()
        if event_type in {"payment.failed", "subscription.recurring.payment.failed"}:
            return str(payload.get("status") or "failed").strip().lower()
        if event_type == "subscription.cancelled":
            return "cancelled"
        return (
            str(payload.get("status") or payload.get("payment_status") or "")
            .strip()
            .lower()
        )
    if provider in {"cardlink", "pally"}:
        return str(payload.get("Status") or payload.get("status") or "").strip().lower()
    if provider == "platima":
        return (
            str(payload.get("status") or payload.get("payment_status") or "")
            .strip()
            .lower()
        )
    return ""
