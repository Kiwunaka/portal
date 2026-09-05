# ruff: noqa: F821
"""Payment transport routes.

Loaded after the general public slice and before observability/admin slices.
Business rules remain in focused payment application/provider/outbox modules;
this file binds HTTP inputs, authentication and response projections only.
"""

try:
    from .module_slices import bootstrap_slice
except ImportError:
    from module_slices import bootstrap_slice

bootstrap_slice(globals())


@app.api_route("/pay/success", methods=["GET", "POST"])
async def pay_success(request: Request):
    if request.method == "POST":
        return {"ok": True, "status": "unverified"}
    return HTMLResponse(
        content=_payment_page_html(
            title="Статус платежа",
            message="Проверьте оплату в личном кабинете. Доступ обновится после подтверждения платежа.",
            action_url=_public_webapp_url(),
            action_label="Открыть кабинет",
        )
    )


@app.api_route("/pay/fail", methods=["GET", "POST"])
async def pay_fail(request: Request):
    if request.method == "POST":
        return {"ok": False, "status": "failed"}
    action = _public_checkout_url() or (f"https://t.me/{BOT_USERNAME}" if BOT_USERNAME else "/")
    return HTMLResponse(
        content=_payment_page_html(
            title="Платеж не завершен",
            message="Платеж не прошел. Можно повторить попытку или обратиться в службу заботы через Telegram.",
            action_url=action,
            action_label="Повторить оплату",
        )
    )


@app.api_route("/api/payments/result/{provider}", methods=["POST", "GET"])
async def payment_result(provider: str, request: Request) -> dict:
    return await _handle_payment_callback(provider=provider, event_type="result", request=request)


@app.api_route("/api/payments/refund/{provider}", methods=["POST", "GET"])
async def payment_refund(provider: str, request: Request) -> dict:
    return await _handle_payment_callback(provider=provider, event_type="refund", request=request)


@app.api_route("/api/payments/chargeback/{provider}", methods=["POST", "GET"])
async def payment_chargeback(provider: str, request: Request) -> dict:
    return await _handle_payment_callback(provider=provider, event_type="chargeback", request=request)


@app.api_route("/api/payments/freekassa/notify", methods=["POST", "GET"])
async def payment_freekassa_notify(request: Request):
    result = await _handle_payment_callback(provider="freekassa", event_type="result", request=request)
    if request.method == "POST" and bool(result.get("ok")):
        return PlainTextResponse("YES")
    return result


@app.get("/api/payments/providers", response_model=RubProvidersOut)
async def rub_payment_providers() -> RubProvidersOut:
    return _public_checkout_provider_state()


@app.post("/api/payments/orders/status", response_model=PaymentReturnStatusOut)
async def rub_order_return_status(
    payload: PaymentReturnStatusIn,
    request: Request,
    response: Response,
) -> PaymentReturnStatusOut:
    return_token = str(payload.return_token or "").strip()
    await run_payment_db_use_case(
        "payment_return_rate_limit",
        _enforce_beta_rate_limit,
        "payment_return_status",
        request,
        identity=hashlib.sha256(return_token.encode("utf-8")).hexdigest()[:32],
    )
    try:
        result = await run_payment_db_use_case(
            "payment_return_status",
            _payment_return_status_db,
            return_token=return_token,
        )
    except PaymentReturnTokenError as exc:
        code = str(exc)
        status_code = 404 if code == "payment_return_order_missing" else 401
        raise HTTPException(status_code=status_code, detail=code) from exc
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    return PaymentReturnStatusOut(**result)


@app.post("/api/payments/orders/create", response_model=RubOrderActionOut)
async def rub_order_create(
    payload: RubOrderCreateIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> RubOrderActionOut:
    _ensure_checkout_runtime_ready()
    auth_user = await run_payment_db_use_case(
        "order_authenticate",
        _require_auth_user,
        x_telegram_init_data,
        request=request,
    )
    actor_tg_id = int(auth_user.get("id", 0))
    source = (payload.source or "site").strip().lower()
    if source not in {"site", "bot"}:
        source = "site"
    tg_id = int(payload.tg_id or actor_tg_id)
    if tg_id != actor_tg_id and not _is_admin_tg(actor_tg_id):
        raise HTTPException(status_code=403, detail="Access denied")
    return await _rub_create_order_internal(
        request=request,
        provider=_normalize_provider(payload.provider),
        tg_id=int(tg_id),
        source=source,
        plan_code=(payload.plan_code or "").strip().lower(),
        campaign=_sanitize_deeplink_token(payload.campaign, max_len=64, uppercase=False),
        promo_code=_sanitize_deeplink_token(payload.promo_code, max_len=20, uppercase=True),
        currency=(payload.currency or "RUB").strip().upper(),
        payment_method=payload.payment_method,
        consume_pending_discount=False,
        acquisition_handle=payload.acquisition_handle,
        offer_token=payload.offer_token,
        return_surface="cabinet",
    )


@app.post("/api/payments/orders/create-public", response_model=RubOrderActionOut)
async def rub_order_create_public(
    payload: RubPublicOrderCreateIn,
    request: Request,
) -> RubOrderActionOut:
    _ensure_checkout_runtime_ready()
    ticket_raw = str(payload.checkout_ticket or "").strip()
    public_subject = ticket_raw or str(payload.buyer_email or payload.source or "").strip()[:96]
    public_identity = hashlib.sha256(public_subject.encode("utf-8")).hexdigest()[:32] if public_subject else ""
    await run_payment_db_use_case(
        "order_public_rate_limit",
        _enforce_beta_rate_limit,
        "public_order_create",
        request,
        identity=public_identity,
    )
    ticket_payload = _parse_checkout_ticket(ticket_raw) if ticket_raw else None
    request_plan_code = (payload.plan_code or "").strip().lower()
    if ticket_raw and not ticket_payload:
        raise HTTPException(status_code=401, detail="Invalid or expired checkout ticket")

    if ticket_payload:
        tg_id = int(ticket_payload.get("tg_id") or 0)
        if tg_id <= 0:
            raise HTTPException(status_code=400, detail="Checkout ticket has no user binding")
        source = str(ticket_payload.get("source") or "bot").strip().lower()
        if source not in {"site", "bot"}:
            source = "bot"
        ticket_plan_code = str(ticket_payload.get("plan_code") or "").strip().lower()
        if ticket_plan_code and request_plan_code and request_plan_code != ticket_plan_code:
            raise HTTPException(status_code=400, detail="Plan code does not match checkout ticket")
        plan_code = (ticket_plan_code or request_plan_code or "").strip().lower()
        campaign = _sanitize_deeplink_token(
            str(ticket_payload.get("campaign_key") or ""), max_len=64, uppercase=False
        )
        promo_code = _sanitize_deeplink_token(
            str(ticket_payload.get("promo_code") or ""), max_len=20, uppercase=True
        )
        buyer_email = None
    else:
        tg_id = None
        source = str(payload.source or "site").strip().lower()
        if source != "site":
            source = "site"
        plan_code = request_plan_code
        campaign = _sanitize_deeplink_token(payload.campaign, max_len=64, uppercase=False)
        promo_code = _sanitize_deeplink_token(payload.promo_code, max_len=20, uppercase=True)
        buyer_email = str(payload.buyer_email or "").strip()

    return await _rub_create_order_internal(
        request=request,
        provider=_normalize_provider(payload.provider),
        tg_id=tg_id,
        source=source,
        plan_code=plan_code,
        campaign=campaign,
        promo_code=promo_code,
        currency=(payload.currency or "RUB").strip().upper(),
        buyer_email=buyer_email,
        payment_method=payload.payment_method,
        consume_pending_discount=False,
        acquisition_handle=payload.acquisition_handle,
        offer_token=payload.offer_token,
        return_surface="marketing",
        intent_id=payload.intent_id,
    )


@app.post("/api/payments/start-99-eligibility")
async def start99_eligibility(
    payload: Start99EligibilityIn,
    request: Request,
) -> dict[str, Any]:
    ticket_raw = str(payload.checkout_ticket or "").strip()
    identity = hashlib.sha256(ticket_raw.encode("utf-8")).hexdigest()[:32]
    await run_payment_db_use_case(
        "start99_rate_limit",
        _enforce_beta_rate_limit,
        "start99_eligibility",
        request,
        identity=identity,
    )
    ticket_payload = _parse_checkout_ticket(ticket_raw)
    if not ticket_payload:
        raise HTTPException(status_code=401, detail="Invalid or expired checkout ticket")
    tg_id = int(ticket_payload.get("tg_id") or 0)
    if tg_id <= 0:
        raise HTTPException(status_code=400, detail="Checkout ticket has no user binding")
    return await run_payment_db_use_case(
        "start99_read",
        _start99_eligibility_db,
        tg_id=tg_id,
        ticket_payload=dict(ticket_payload),
    )


@app.post("/api/payments/freekassa/orders/create", response_model=RubOrderActionOut)
async def freekassa_order_create(
    payload: FreekassaOrderCreateIn,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> RubOrderActionOut:
    generic = RubOrderCreateIn(
        provider="freekassa",
        plan_code=payload.plan_code,
        source=payload.source,
        tg_id=payload.tg_id,
        campaign=payload.campaign,
        promo_code=payload.promo_code,
        currency=payload.currency,
        payment_method=payload.payment_method,
        acquisition_handle=payload.acquisition_handle,
        offer_token=payload.offer_token,
    )
    return await rub_order_create(generic, request=request, x_telegram_init_data=x_telegram_init_data)


@app.post("/api/payments/freekassa/orders/create-public", response_model=RubOrderActionOut)
async def freekassa_order_create_public(
    payload: FreekassaPublicOrderCreateIn,
    request: Request,
) -> RubOrderActionOut:
    generic = RubPublicOrderCreateIn(
        provider="freekassa",
        plan_code=payload.plan_code,
        checkout_ticket=payload.checkout_ticket,
        currency=payload.currency,
        payment_method=payload.payment_method,
        acquisition_handle=payload.acquisition_handle,
        offer_token=payload.offer_token,
    )
    return await rub_order_create_public(generic, request=request)


@app.get("/api/payments/freekassa/orders/{order_id}")
async def freekassa_order_get(
    order_id: str,
    request: Request,
    source: str = "site",
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    auth_user = await run_payment_db_use_case(
        "freekassa_order_authenticate",
        _require_auth_user,
        x_telegram_init_data,
        request=request,
    )
    actor_tg_id = int(auth_user.get("id", 0))
    request_source = (source or "").strip().lower() or "site"
    local_status, request_source = await run_payment_db_use_case(
        "freekassa_order_read",
        _freekassa_order_context_db,
        order_id=order_id,
        actor_tg_id=actor_tg_id,
        request_source=request_source,
    )
    remote = await _freekassa_api_request(
        source=request_source,
        method="orders",
        data={"orderId": order_id},
        http_registry=getattr(request.app.state, "payment_http_registry", None),
    )
    return {
        "ok": True,
        "provider": "freekassa",
        "order_id": order_id,
        "status_local": local_status,
        "remote": remote,
    }


@app.post("/api/payments/freekassa/orders/{order_id}/refund")
async def freekassa_order_refund(
    order_id: str,
    request: Request,
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    await run_payment_db_use_case(
        "freekassa_refund_authorize",
        _require_admin,
        x_telegram_init_data,
        request=request,
    )
    amount, source = await run_payment_db_use_case(
        "freekassa_refund_read",
        _freekassa_refund_context_db,
        order_id=order_id,
    )
    remote = await _freekassa_api_request(
        source=source,
        method="orders/refund",
        data={"orderId": order_id, "amount": amount},
        http_registry=getattr(request.app.state, "payment_http_registry", None),
    )
    return {"ok": True, "provider": "freekassa", "order_id": order_id, "remote": remote}


@app.get("/api/payments/freekassa/currencies")
async def freekassa_currencies(
    request: Request,
    source: str = "site",
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    await run_payment_db_use_case(
        "freekassa_currency_authenticate",
        _require_auth_user,
        x_telegram_init_data,
        request=request,
    )
    remote = await _freekassa_api_request(
        source=source,
        method="currencies",
        data={},
        http_registry=getattr(request.app.state, "payment_http_registry", None),
    )
    return {"ok": True, "provider": "freekassa", "remote": remote}


@app.get("/api/payments/freekassa/currencies/{currency}/status")
async def freekassa_currency_status(
    currency: str,
    request: Request,
    source: str = "site",
    x_telegram_init_data: str = Header(default=""),
) -> dict[str, Any]:
    await run_payment_db_use_case(
        "freekassa_currency_authenticate",
        _require_auth_user,
        x_telegram_init_data,
        request=request,
    )
    remote = await _freekassa_api_request(
        source=source,
        method="currencies/status",
        data={"currency": str(currency or "").strip().upper()},
        http_registry=getattr(request.app.state, "payment_http_registry", None),
    )
    return {
        "ok": True,
        "provider": "freekassa",
        "currency": str(currency or "").upper(),
        "remote": remote,
    }
