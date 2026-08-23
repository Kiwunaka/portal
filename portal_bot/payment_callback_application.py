from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Callable

from fastapi import HTTPException, Request

from payment_db_runtime import run_payment_db_use_case


@dataclass(frozen=True)
class PaymentCallbackDependencies:
    normalize_provider: Callable[..., Any]
    payment_provider_whitelist: set[str] | frozenset[str]
    enforce_beta_rate_limit: Callable[..., Any]
    read_callback_payload: Callable[..., Any]
    fk_client_ip: Callable[..., Any]
    is_ip_allowed: Callable[..., Any]
    fk_notify_ip_allowlist: tuple[str, ...] | list[str]
    lavatop_webhook_auth_configured: Callable[..., Any]
    request_client_ip: Callable[..., Any]
    is_loopback_ip: Callable[..., Any]
    callback_ids: Callable[..., Any]
    verify_callback_signature: Callable[..., Any]
    status_from_event: Callable[..., Any]
    validate_paid_callback_against_order: Callable[..., Any]
    record_external_payment_event: Callable[..., Any]
    record_security_event: Callable[..., Any]
    payment_callback_tolerant_mode: bool
    record_payment_reversal_operator_action: Callable[..., Any]
    terminal_payment_reversal_codes: set[str] | frozenset[str]
    complete_external_payment_event: Callable[..., Any]
    payment_order_correlation: Callable[..., Any]
    fulfill_external_paid_order: Callable[..., Any]
    safe_payment_processing_error: Callable[..., Any]
    terminal_payment_fulfillment_codes: set[str] | frozenset[str]
    record_payment_entitlement_retry_error: Callable[..., Any]
    deliver_payment_access_key: Callable[..., Any]
    record_access_key_delivery_result: Callable[..., Any]
    finalize_paid_event_after_delivery: Callable[..., Any]
    sync_user_after_paid_purchase: Callable[..., Any]
    notify_telegram_paid_access_ready: Callable[..., Any]
    logger: logging.Logger


async def handle_payment_callback(
    *,
    dependencies: PaymentCallbackDependencies,
    provider: str,
    event_type: str,
    request: Request,
) -> dict[str, Any]:
    deps = dependencies
    _normalize_provider = deps.normalize_provider
    PAYMENT_PROVIDER_WHITELIST = deps.payment_provider_whitelist
    _enforce_beta_rate_limit = deps.enforce_beta_rate_limit
    _read_callback_payload = deps.read_callback_payload
    _fk_client_ip = deps.fk_client_ip
    _is_ip_allowed = deps.is_ip_allowed
    FK_NOTIFY_IP_ALLOWLIST = deps.fk_notify_ip_allowlist
    _lavatop_webhook_auth_configured = deps.lavatop_webhook_auth_configured
    _request_client_ip = deps.request_client_ip
    _is_loopback_ip = deps.is_loopback_ip
    _callback_ids = deps.callback_ids
    _verify_callback_signature = deps.verify_callback_signature
    _status_from_event = deps.status_from_event
    _validate_paid_callback_against_order = deps.validate_paid_callback_against_order
    _record_external_payment_event = deps.record_external_payment_event
    _record_security_event = deps.record_security_event
    PAYMENT_CALLBACK_TOLERANT_MODE = deps.payment_callback_tolerant_mode
    _record_payment_reversal_operator_action = deps.record_payment_reversal_operator_action
    _TERMINAL_PAYMENT_REVERSAL_CODES = deps.terminal_payment_reversal_codes
    _complete_external_payment_event = deps.complete_external_payment_event
    _payment_order_correlation = deps.payment_order_correlation
    _fulfill_external_paid_order = deps.fulfill_external_paid_order
    _safe_payment_processing_error = deps.safe_payment_processing_error
    _TERMINAL_PAYMENT_FULFILLMENT_CODES = deps.terminal_payment_fulfillment_codes
    _record_payment_entitlement_retry_error = deps.record_payment_entitlement_retry_error
    deliver_payment_access_key = deps.deliver_payment_access_key
    _record_access_key_delivery_result = deps.record_access_key_delivery_result
    _finalize_paid_event_after_delivery = deps.finalize_paid_event_after_delivery
    _sync_user_after_paid_purchase = deps.sync_user_after_paid_purchase
    _notify_telegram_paid_access_ready = deps.notify_telegram_paid_access_ready
    logger = deps.logger
    p = _normalize_provider(provider)
    et = re.sub(r"[^a-z_]", "", str(event_type or "").strip().lower())
    if p not in PAYMENT_PROVIDER_WHITELIST:
        raise HTTPException(status_code=404, detail="Unsupported provider")
    if et not in {"result", "refund", "chargeback"}:
        raise HTTPException(status_code=400, detail="Unsupported event type")
    await run_payment_db_use_case(
        "callback_rate_limit",
        _enforce_beta_rate_limit,
        "payment_callback",
        request,
        identity=f"{p}:{et}",
    )

    payload, raw = await _read_callback_payload(request)
    if p == "freekassa":
        client_ip = _fk_client_ip(request)
        if not _is_ip_allowed(client_ip, FK_NOTIFY_IP_ALLOWLIST):
            logger.warning("freekassa callback blocked by ip allowlist: ip=%s", client_ip)
            raise HTTPException(status_code=403, detail="Callback IP is not allowed")
    if p == "lavatop":
        allowlist = [item.strip() for item in (os.getenv("LAVATOP_WEBHOOK_IP_ALLOWLIST") or "").split(",") if item.strip()]
        client_ip = _request_client_ip(request)
        if allowlist and not _is_ip_allowed(client_ip, allowlist):
            if _is_loopback_ip(client_ip) and _lavatop_webhook_auth_configured():
                logger.warning(
                    "lavatop callback arrived through local reverse proxy; relying on webhook auth after allowlist miss: ip=%s",
                    client_ip,
                )
            else:
                logger.warning("lavatop callback blocked by ip allowlist: ip=%s", client_ip)
                raise HTTPException(status_code=403, detail="Callback IP is not allowed")
    order_id, external_id = _callback_ids(p, payload, raw)
    signature_ok, signature_reason = _verify_callback_signature(provider=p, payload=payload, raw=raw, request=request)
    callback_status = _status_from_event(et, payload, signature_ok=signature_ok, provider=p)
    validation_reason = ""
    if signature_ok and et == "result" and callback_status == "paid":
        callback_valid, validation_reason = await run_payment_db_use_case(
            "callback_validate_order",
            _validate_paid_callback_against_order,
            provider=p,
            order_id=order_id,
            payload=payload,
        )
        if not callback_valid:
            payload = dict(payload)
            payload["_pokrov_validation_error"] = validation_reason
            callback_status = "manual_review"
    requires_durable_completion = bool(
        signature_ok
        and (
            (et == "result" and callback_status == "paid")
            or et in {"refund", "chargeback"}
        )
    )
    processed_ok = bool(
        signature_ok
        and callback_status != "pending_verification"
        and not requires_durable_completion
    )
    duplicate, persist_ok = await run_payment_db_use_case(
        "callback_record_event",
        _record_external_payment_event,
        provider=p,
        event_type=et,
        external_id=external_id,
        order_id=order_id,
        payload=payload,
        signature_ok=signature_ok,
        processed_ok=processed_ok,
        status=callback_status,
    )
    if not persist_ok:
        raise HTTPException(status_code=503, detail="Payment callback persistence is retryable")

    if not signature_ok:
        await run_payment_db_use_case(
            "callback_security_event",
            _record_security_event,
            "payment_callback_invalid_signature",
            scope="payment_callback",
            client_ip=_request_client_ip(request),
            subject=f"{p}:{et}",
            reason=signature_reason,
            meta={"order_id": order_id, "external_id": external_id},
        )
        await run_payment_db_use_case(
            "callback_invalid_rate_limit",
            _enforce_beta_rate_limit,
            "payment_callback_invalid",
            request,
            identity=f"{p}:{signature_reason}",
        )
        logger.warning(
            "payment callback signature invalid: provider=%s event=%s reason=%s order_id=%s external_id=%s",
            p,
            et,
            signature_reason,
            order_id,
            external_id,
        )
        if not PAYMENT_CALLBACK_TOLERANT_MODE:
            raise HTTPException(status_code=400, detail=f"Invalid signature: {signature_reason}")

    activated = False
    activation_reason = ""
    sync_ok = None
    if (not duplicate) and signature_ok and et in {"refund", "chargeback"}:
        try:
            reversed_ok, reversal_code = await run_payment_db_use_case(
                "callback_reverse_payment",
                _record_payment_reversal_operator_action,
                provider=p,
                order_id=order_id,
                event_type=et,
                payload=payload,
                reason=callback_status,
            )
        except Exception:
            logger.error(
                "payment reversal failed code=reversal_persistence_failed correlation=%s",
                _payment_order_correlation(provider=p, order_id=order_id),
            )
            reversed_ok, reversal_code = False, "reversal_persistence_failed"
        if not reversed_ok:
            if reversal_code in _TERMINAL_PAYMENT_REVERSAL_CODES:
                completion_ok = await run_payment_db_use_case(
                    "callback_complete_reversal",
                    _complete_external_payment_event,
                    provider=p,
                    event_type=et,
                    external_id=external_id,
                    processed_ok=True,
                    error_code=reversal_code,
                )
                if not completion_ok:
                    raise HTTPException(status_code=503, detail="Payment callback completion is retryable")
                activation_reason = reversal_code
            else:
                await run_payment_db_use_case(
                    "callback_fail_reversal",
                    _complete_external_payment_event,
                    provider=p,
                    event_type=et,
                    external_id=external_id,
                    processed_ok=False,
                    error_code=reversal_code,
                )
                raise HTTPException(status_code=503, detail="Payment reversal is retryable")
        else:
            completion_ok = await run_payment_db_use_case(
                "callback_complete_reversal",
                _complete_external_payment_event,
                provider=p,
                event_type=et,
                external_id=external_id,
                processed_ok=True,
            )
            if not completion_ok:
                raise HTTPException(status_code=503, detail="Payment callback completion is retryable")

    if (not duplicate) and signature_ok and et == "result" and callback_status == "paid":
        activated, activation_reason, fulfillment = await run_payment_db_use_case(
            "callback_fulfill_order",
            _fulfill_external_paid_order,
            provider=p,
            order_id=order_id,
            payload=payload,
        )
        if not activated:
            safe_reason = _safe_payment_processing_error(activation_reason or "durable_fulfillment_failed")
            if safe_reason in _TERMINAL_PAYMENT_FULFILLMENT_CODES:
                completion_ok = await run_payment_db_use_case(
                    "callback_complete_terminal",
                    _complete_external_payment_event,
                    provider=p,
                    event_type=et,
                    external_id=external_id,
                    processed_ok=True,
                    error_code=safe_reason,
                )
                if not completion_ok:
                    raise HTTPException(status_code=503, detail="Payment callback completion is retryable")
                activation_reason = safe_reason
            else:
                await run_payment_db_use_case(
                    "callback_record_retry",
                    _record_payment_entitlement_retry_error,
                    provider=p,
                    order_id=order_id,
                    error_code=safe_reason,
                )
                await run_payment_db_use_case(
                    "callback_fail_fulfillment",
                    _complete_external_payment_event,
                    provider=p,
                    event_type=et,
                    external_id=external_id,
                    processed_ok=False,
                    error_code=safe_reason,
                )
                raise HTTPException(status_code=503, detail="Payment fulfillment is retryable")
        else:
            delivery_finalized = False
            if fulfillment.get("access_key") and fulfillment.get("buyer_email"):
                try:
                    delivery = await deliver_payment_access_key(
                        email=str(fulfillment["buyer_email"]),
                        access_key=str(fulfillment["access_key"]),
                        order_id=str(fulfillment.get("order_id") or order_id),
                        plan_code=str(fulfillment.get("plan_code") or ""),
                        plan_label=str(fulfillment.get("plan_label") or ""),
                        days=int(fulfillment.get("days") or 0),
                    )
                except Exception:
                    delivery = {"status": "delivery_error", "mode": "webhook"}
                evidence_ok = await run_payment_db_use_case(
                    "callback_record_delivery",
                    _record_access_key_delivery_result,
                    provider=p,
                    order_id=order_id,
                    delivery=delivery,
                )
                if not evidence_ok:
                    await run_payment_db_use_case(
                        "callback_fail_delivery",
                        _complete_external_payment_event,
                        provider=p,
                        event_type=et,
                        external_id=external_id,
                        processed_ok=False,
                        error_code="delivery_evidence_failed",
                    )
                    raise HTTPException(status_code=503, detail="Payment delivery evidence is retryable")
                delivery_ok = str(delivery.get("status") or "").strip().lower() in {"sent", "debug_echo"}
                completion_ok, completion_reason = await run_payment_db_use_case(
                    "callback_finalize_delivery",
                    _finalize_paid_event_after_delivery,
                    provider=p,
                    order_id=order_id,
                    event_type=et,
                    external_id=external_id,
                    delivery_succeeded=delivery_ok,
                )
                if not completion_ok:
                    raise HTTPException(status_code=503, detail="Payment callback completion is retryable")
                delivery_finalized = True
                if completion_reason == "claim_reversed":
                    activated = False
                    activation_reason = completion_reason
                    fulfillment = {}
                elif completion_reason:
                    raise HTTPException(status_code=503, detail="Payment access delivery is retryable")
            if not delivery_finalized:
                completion_ok = await run_payment_db_use_case(
                    "callback_complete_paid",
                    _complete_external_payment_event,
                    provider=p,
                    event_type=et,
                    external_id=external_id,
                    processed_ok=True,
                )
                if not completion_ok:
                    raise HTTPException(status_code=503, detail="Payment callback completion is retryable")
            if activated and fulfillment.get("access_key") and fulfillment.get("buyer_email"):
                activation_reason = activation_reason or "access_key_email_sent"
            tg_id = fulfillment.get("tg_id")
            if tg_id is not None:
                try:
                    sync_ok = bool(await _sync_user_after_paid_purchase(int(tg_id)))
                except Exception:
                    sync_ok = False
                try:
                    await _notify_telegram_paid_access_ready(
                        tg_id=int(tg_id),
                        sync_ok=bool(sync_ok),
                    )
                except Exception:
                    logger.warning(
                        "telegram paid access notification failed code=telegram_notification_failed correlation=%s",
                        _payment_order_correlation(provider=p, order_id=order_id),
                    )
    elif (not duplicate) and signature_ok and et == "result":
        activation_reason = validation_reason or callback_status

    return {
        "ok": bool(signature_ok and persist_ok),
        "provider": p,
        "event_type": et,
        "order_id": order_id or None,
        "external_id": external_id,
        "status": callback_status,
        "signature_ok": bool(signature_ok),
        "duplicate": bool(duplicate),
        "activated": bool(activated),
        "activation_reason": activation_reason or None,
        "sync_ok": sync_ok,
    }
