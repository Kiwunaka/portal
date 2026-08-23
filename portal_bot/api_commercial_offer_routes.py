# ruff: noqa: F821
"""Public commercial-offer preview transport.

The route resolves an already server-issued subject and delegates all campaign,
price, audience, deadline and token decisions to the commercial offer service.
"""

try:
    from .module_slices import bootstrap_slice
except ImportError:
    from module_slices import bootstrap_slice

bootstrap_slice(globals())


def _commercial_offer_terms_url() -> str:
    legal_urls = dict(_PUBLIC_URL_FACTS.get("legal") or {})
    return str(legal_urls.get("offer") or "https://pokrov.space/offer/").strip()


def _commercial_offer_preview_db(
    *,
    plan_code: str,
    promo_code: str,
    offer_public_id: str,
    channel: str,
    checkout_ticket: str,
    acquisition_handle: str,
    telegram_init_data: str,
    authenticated_tg_id: int = 0,
) -> dict[str, Any]:
    session = SessionLocal()
    try:
        subject_sources = sum(
            1
            for value in (checkout_ticket, acquisition_handle, telegram_init_data)
            if str(value or "").strip()
        )
        subject_kind: str | None = None
        subject_value: str | None = None
        subject_error: str | None = None
        impression_public_id: str | None = None
        click_public_id: str | None = None
        if subject_sources > 1:
            subject_error = "subject_conflict"
        elif checkout_ticket:
            ticket = _parse_checkout_ticket(checkout_ticket)
            tg_id = int((ticket or {}).get("tg_id") or 0)
            if ticket is None or tg_id <= 0:
                subject_error = "subject_invalid"
            else:
                subject_kind, subject_value = "telegram", str(tg_id)
                impression_public_id = str((ticket or {}).get("impression_public_id") or "") or None
                click_public_id = str((ticket or {}).get("click_public_id") or "") or None
        elif acquisition_handle:
            try:
                subject_kind, subject_value, handoff = resolve_acquisition_offer_context(
                    session,
                    raw_handle=acquisition_handle,
                    now=_utcnow(),
                )
                impression_public_id = str(handoff.impression_public_id)
                click_public_id = str(handoff.click_public_id)
            except CommercialOfferPreviewError:
                subject_error = "subject_invalid"
        elif telegram_init_data:
            auth_user = _optional_auth_user(telegram_init_data)
            tg_id = int((auth_user or {}).get("id") or 0)
            if tg_id <= 0:
                subject_error = "subject_invalid"
            else:
                subject_kind, subject_value = "telegram", str(tg_id)
        elif int(authenticated_tg_id or 0) > 0:
            subject_kind, subject_value = "telegram", str(authenticated_tg_id)

        result = preview_commercial_offer(
            session,
            plan_code=plan_code,
            promo_code=promo_code,
            offer_public_id=offer_public_id,
            channel=channel,
            subject_kind=subject_kind,
            subject_value=subject_value,
            subject_error=subject_error,
            impression_public_id=impression_public_id,
            click_public_id=click_public_id,
            terms_url=_commercial_offer_terms_url(),
            now=_utcnow(),
        )
        session.commit()
        return result
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@app.post("/api/public/offers/preview", response_model=CommercialOfferPreviewOut)
async def commercial_offer_preview_route(
    payload: CommercialOfferPreviewIn,
    request: Request,
    response: Response,
    x_telegram_init_data: str = Header(default=""),
) -> CommercialOfferPreviewOut:
    checkout_ticket = str(payload.checkout_ticket or "").strip()
    acquisition_handle = str(payload.acquisition_handle or "").strip()
    telegram_init_data = str(x_telegram_init_data or "").strip()
    authenticated_tg_id = 0
    if not (checkout_ticket or acquisition_handle or telegram_init_data):
        authenticated = _optional_auth_user("", request=request)
        authenticated_tg_id = int((authenticated or {}).get("id") or 0)
    rate_identity_raw = (
        checkout_ticket
        or acquisition_handle
        or telegram_init_data
        or (f"authenticated:{authenticated_tg_id}" if authenticated_tg_id > 0 else "")
    )
    rate_identity = (
        hashlib.sha256(rate_identity_raw.encode("utf-8")).hexdigest()[:32]
        if rate_identity_raw
        else "anonymous"
    )
    await run_payment_db_use_case(
        "offer_preview_rate_limit",
        _enforce_beta_rate_limit,
        "public_offer_preview",
        request,
        identity=rate_identity,
    )
    result = await run_payment_db_use_case(
        "offer_preview",
        _commercial_offer_preview_db,
        plan_code=str(payload.plan_code or "").strip().lower(),
        promo_code=str(payload.promo_code or "").strip().upper(),
        offer_public_id=str(payload.offer_id or "").strip().lower(),
        channel=str(payload.channel or "").strip().lower(),
        checkout_ticket=checkout_ticket,
        acquisition_handle=acquisition_handle,
        telegram_init_data=telegram_init_data,
        authenticated_tg_id=authenticated_tg_id,
    )
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    return CommercialOfferPreviewOut(**result)
