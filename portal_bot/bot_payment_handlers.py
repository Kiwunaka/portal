"""Checkout, payment fulfillment and subscription delivery handlers.

Loaded by the bot composition root in source order. Public symbols are
re-exported for backwards compatibility.
"""

try:
    from .module_slices import bootstrap_slice
except ImportError:
    from module_slices import bootstrap_slice

bootstrap_slice(globals())

@router.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: CallbackQuery, bot: Bot):
    raw_key = callback.data.replace("buy_", "")
    tariff_key = normalize_tariff_key(raw_key)
    tariff = TARIFFS.get(tariff_key)

    if not tariff:
        await callback.answer("❌ Тариф не найден")
        return

    tg_id = callback.from_user.id
    user = get_user(tg_id)

    if tariff_key == "trial":
        await _activate_trial_tariff(callback, bot, retry_callback_data="buy_trial")
        return

    await callback.message.edit_text(
        _build_tariff_payment_choice_text(tariff_key=tariff_key, tg_id=tg_id),
        reply_markup=_build_tariff_payment_choice_keyboard(tg_id=tg_id, tariff_key=tariff_key),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()
    return


@router.callback_query(F.data.startswith("pay_stars_"))
async def process_buy_stars(callback: CallbackQuery, bot: Bot):
    if not _stars_checkout_creation_enabled():
        await callback.answer("Оплата через Stars сейчас не используется. Выберите оплату в ₽ или напишите в поддержку, если уже оплатили.", show_alert=True)
        return
    raw_key = callback.data.replace("pay_stars_", "")
    tariff_key = normalize_tariff_key(raw_key)
    tariff = TARIFFS.get(tariff_key)
    if not tariff:
        await callback.answer("❌ Тариф не найден")
        return

    tg_id = callback.from_user.id
    pricing = _tariff_pricing_for_user(tg_id, tariff_key)
    use_discount = bool(pricing["use_discount"])
    pending_discount_pct = int(pricing["pending_discount_pct"])
    base_price = int(pricing["base_price"])
    actual_stars = int(pricing["actual_stars"])
    points_to_use = int(pricing["points_to_use"])
    final_stars = int(pricing["final_stars"])

    mode_label = "disc" if use_discount else "full"
    attempt = start_attempt(
        tg_id=tg_id,
        source="bot",
        plan_code=tariff_key,
        amount_stars=final_stars,
        currency="XTR",
    )
    if not attempt:
        await callback.message.answer("Не смог подготовить оплату. Попробуйте ещё раз через минуту; если повторится, напишите в поддержку.")
        return

    invoice_payload = f"portal_{tariff_key}_{tg_id}_{mode_label}_a{int(attempt.id)}_p{int(points_to_use)}"
    mark_invoice_sent(attempt_id=int(attempt.id), set_invoice_payload=invoice_payload)

    discount_chunks = []
    if use_discount:
        discount_chunks.append("-20% реф")
    if pending_discount_pct > 0:
        discount_chunks.append(f"-{pending_discount_pct}% промо")
    discount_note = f" ({', '.join(discount_chunks)})" if discount_chunks else ""
    points_note = f" + points -{points_to_use} Stars" if points_to_use > 0 else ""
    prices = [LabeledPrice(label=tariff["name"] + discount_note + points_note, amount=int(final_stars))]
    description = f"Безлимит на {tariff['days']} дней{discount_note}{points_note}"
    track_event(
        tg_id=tg_id,
        event_name="clicked_pay",
        source="bot",
        meta={
            "attempt_id": int(attempt.id),
            "plan_code": tariff_key,
            "base_price": int(base_price),
            "discounted_price": int(actual_stars),
            "promo_discount_pct": int(pending_discount_pct),
            "points_used": int(points_to_use),
            "final_price": int(final_stars),
        },
    )
    await bot.send_invoice(
        chat_id=tg_id,
        title=f"POKROV: {tariff['name']}",
        description=description,
        payload=invoice_payload,
        provider_token="",
        currency="XTR",
        prices=prices
    )
    await callback.message.answer(
        "💳 Счёт готов. После оплаты я автоматически включу доступ.\n\n"
        "Если окно закрылось, нажмите «Проверить оплату».",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Проверить оплату", callback_data="status")],
                [InlineKeyboardButton(text="◀️ К тарифам", callback_data="charge")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back")],
            ]
        ),
    )


@router.callback_query(F.data.startswith("pay_rub_"))
@router.callback_query(F.data.startswith("pay_rub:"))
async def process_buy_rub(callback: CallbackQuery, bot: Bot):
    provider_code, tariff_key = _parse_pay_rub_callback(callback.data)
    tariff = TARIFFS.get(tariff_key)
    if not tariff:
        await callback.answer("❌ Тариф не найден")
        return
    provider_row = _rub_provider_by_code(provider_code, plan_code=tariff_key)
    if not provider_row:
        await callback.answer("⚠️ Рублёвая оплата сейчас временно недоступна", show_alert=True)
        return
    provider_label = str((provider_row or {}).get("label") or "кассу").strip()

    tg_id = callback.from_user.id
    pricing = _tariff_pricing_for_user(tg_id, tariff_key)

    try:
        data = await _create_rub_payment_link_for_bot(
            provider=provider_code,
            tg_id=tg_id,
            tariff_key=tariff_key,
        )
    except Exception as exc:
        logger.warning("direct rub checkout failed provider=%s tg_id=%s plan=%s err=%s", provider_code, tg_id, tariff_key, exc)
        await callback.message.edit_text(
            "⚠️ Не получилось сразу открыть оплату.\n\n"
            "Попробуйте ещё раз через минуту или откройте оплату через сайт из этого же тарифа.",
            reply_markup=_build_tariff_payment_choice_keyboard(tg_id=tg_id, tariff_key=tariff_key),
        )
        await callback.answer("Не удалось подготовить оплату", show_alert=True)
        return

    payment_url = str(data.get("payment_url") or "").strip()
    order_id = str(data.get("order_id") or "").strip()
    rub_price = int(pricing["base_price"])
    track_event(
        tg_id=tg_id,
        event_name="clicked_pay",
        source="bot",
        meta={
            "provider": provider_code,
            "plan_code": tariff_key,
            "amount_rub": rub_price,
            "order_id": order_id,
            "flow": "direct_bot_rub",
        },
    )
    await callback.message.edit_text(
        f"💳 *{tariff['name']}*\n\n"
        f"Сумма: *{rub_price} ₽*\n"
        f"Способ оплаты: *{provider_label}*.\n\n"
        "Следующий шаг: откройте оплату по кнопке ниже.\n"
        "Если банк не откроется внутри Telegram, используйте кнопку «Открыть через сайт» "
        "или обычный браузер.\n\n"
        "Ссылка действует около *15 минут*.",
        reply_markup=_build_direct_rub_payment_keyboard(
            tg_id=tg_id,
            tariff_key=tariff_key,
            payment_url=payment_url,
            provider_label=provider_label,
        ),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer("Ссылка на оплату готова")

@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(
        pre_checkout.id,
        ok=False,
        error_message="Оплата через Telegram Stars сейчас закрыта. Выберите Lava.top или напишите в поддержку.",
    )


def _payment_amount_display(*, total_amount: int, currency: str) -> str:
    amount = int(total_amount or 0)
    normalized = str(currency or "").strip().upper()
    if normalized == "XTR":
        return f"{amount} Telegram Stars"
    if normalized in {"RUB", "RUR"}:
        return f"{amount // 100} ₽" if amount % 100 == 0 else f"{amount / 100:.2f} ₽"
    return f"{amount} {normalized}".strip()


async def _send_payment_success_summary(
    *,
    message: Message,
    bot: Bot,
    tg_id: int,
    tariff: dict,
    payment: object,
    transaction_id: str,
) -> bool:
    user = get_user(int(tg_id))
    expiry_dt = _naive_utc(user.expiry_at) if user and user.expiry_at else None
    copy = payment_success_copy(
        tariff_name=str(tariff.get("name") or "Доступ POKROV"),
        expiry=expiry_dt.strftime("%d.%m.%Y") if expiry_dt else "—",
        amount_display=_payment_amount_display(
            total_amount=int(getattr(payment, "total_amount", 0) or 0),
            currency=str(getattr(payment, "currency", "") or ""),
        ),
        paid_at=_utcnow().strftime("%d.%m.%Y %H:%M"),
        transaction_id=str(transaction_id or "")[:160],
    )
    rows = [
        [
            _btn_spec(
                text="Подключить устройство",
                callback_data="instruction",
                style=BTN_STYLE_SUCCESS,
                emoji_key="device",
            )
        ],
        [_btn_spec(text="Открыть кабинет", web_app_url=WEBAPP_URL, emoji_key="cabinet")],
        [_btn_spec(text="Ручная ссылка / QR", callback_data="show_key", emoji_key="link")],
    ]
    return await _send_rich_copy(
        message=message,
        bot=bot,
        chat_id=int(tg_id),
        copy=copy,
        rows=rows,
        preserve=True,
    )


@router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def payment_success(message: Message, bot: Bot):
    payment = message.successful_payment
    payload = payment.invoice_payload
    payment_fingerprint = _telegram_payment_fingerprint(payment)
    logger.info(
        "payment_success: from_tg=%s amount=%s currency=%s payload=%s",
        message.from_user.id if message.from_user else None,
        payment.total_amount,
        payment.currency,
        payload,
    )
    if payment_fingerprint and _stars_payment_already_processed(payment_fingerprint):
        if not payload.startswith("portal_") or _stars_entitlement_projection_applied(payment_fingerprint):
            logger.info("payment_success duplicate ignored payload=%s fp=%s", payload, payment_fingerprint)
            return
        logger.warning("payment_success resuming incomplete Stars fulfillment payload=%s", payload)

    # Handle gift card purchase
    if payload.startswith("giftcard_"):
        gift_raw = payload[len("giftcard_"):]
        try:
            card_type, buyer_raw = gift_raw.rsplit("_", 1)
            buyer_tg_id = int(buyer_raw)
        except Exception:
            logger.warning("payment_success giftcard parse error payload=%s", payload)
            await message.answer("❌ Ошибка обработки оплаты. Напишите в службу заботы.")
            return

        code = create_gift_card(buyer_tg_id, card_type)
        if code:
            card_info = GIFT_CARD_TYPES.get(card_type, {})
            _mark_stars_payment_processed(
                payment_fingerprint=payment_fingerprint,
                invoice_payload=payload,
                tg_id=buyer_tg_id,
            )
            await message.answer(
                f"🎁 *Подарочная карта куплена!*\n\n"
                f"Код: `{code}`\n\n"
                f"📦 {card_info.get('days', 0)} дней (Безлимит)\n\n"
                f"Отправьте этот код другу!\n"
                f"Он активирует его командой `/redeem {code}`",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            logger.warning("payment_success giftcard create failed buyer_tg_id=%s card_type=%s", buyer_tg_id, card_type)
            await message.answer("❌ Ошибка создания карты. Напишите в службу заботы.")
        return

    # Handle family-slot purchase
    if payload.startswith("familyslot_"):
        try:
            buyer_tg_id = int(payload.replace("familyslot_", "", 1))
        except Exception:
            await message.answer("❌ Ошибка обработки family-слота.")
            return
        ok, total = add_family_slot_pack(buyer_tg_id, slots=1, days=FAMILY_SLOT_DAYS)
        if not ok:
            await message.answer(f"⚠️ Лимит family-слотов достигнут (+{FAMILY_SLOT_MAX}).")
            return
        _mark_stars_payment_processed(
            payment_fingerprint=payment_fingerprint,
            invoice_payload=payload,
            tg_id=buyer_tg_id,
        )
        await message.answer(
            f"✅ Family-слот активирован.\n\n"
            f"Добавлено: +1 устройство на {FAMILY_SLOT_DAYS} дней\n"
            f"Текущий доп.лимит: +{total}",
        )
        track_event(
            tg_id=buyer_tg_id,
            event_name="paid",
            source="bot",
            meta={"plan_code": "family_slot", "amount_stars": int(payment.total_amount), "family_slots": int(total)},
        )
        return

    # Handle regular tariff purchase
    if payload.startswith("portal_"):
        portal_raw = payload[len("portal_"):]
        try:
            # Backward-compatible payload parser:
            # portal_{tariff}_{tg_id}_{mode}
            # portal_{tariff}_{tg_id}_{mode}_a{attempt_id}_p{points_used}
            match = re.match(
                r"^(?P<tariff>.+)_(?P<tg_id>\d+)_(?P<mode>[a-z]+)(?:_a(?P<attempt_id>\d+))?(?:_p(?P<points>\d+))?$",
                portal_raw,
            )
            if not match:
                raise ValueError("bad payload")
            tariff_key = normalize_tariff_key(str(match.group("tariff") or ""))
            tg_id = int(match.group("tg_id"))
            attempt_id = int(match.group("attempt_id")) if match.group("attempt_id") else None
            points_used = max(0, int(match.group("points"))) if match.group("points") else 0
        except Exception:
            logger.warning("payment_success portal parse error payload=%s", payload)
            await message.answer("❌ Ошибка обработки оплаты. Напишите в службу заботы.")
            return

        tariff = TARIFFS.get(tariff_key)

        if tariff:
            logger.info("payment_success portal parsed: tg_id=%s tariff_key=%s stars=%s", tg_id, tariff_key, tariff.get("stars"))
            mark_paid(attempt_id=attempt_id, invoice_payload=payload)
            if points_used > 0:
                spend_points(tg_id=tg_id, amount=int(points_used), pay_attempt_id=attempt_id, reason="payment_redeem")
            track_event(
                tg_id=tg_id,
                event_name="paid",
                source="bot",
                meta={
                    "attempt_id": attempt_id,
                    "plan_code": tariff_key,
                    "invoice_payload": payload,
                    "amount_stars": int(payment.total_amount),
                    "points_used": int(points_used),
                },
            )
            fulfilled = await create_subscription(
                message,
                tg_id,
                tariff,
                bot,
                paid_amount_stars=int(payment.total_amount),
                pay_attempt_id=attempt_id,
                provider_order_id=str(getattr(payment, "telegram_payment_charge_id", "") or payment_fingerprint),
                send_completion_message=False,
            )
            if not fulfilled:
                return
            _mark_stars_payment_processed(
                payment_fingerprint=payment_fingerprint,
                invoice_payload=payload,
                tg_id=tg_id,
            )
            summary_sent = await _send_payment_success_summary(
                message=message,
                bot=bot,
                tg_id=tg_id,
                tariff=tariff,
                payment=payment,
                transaction_id=str(getattr(payment, "telegram_payment_charge_id", "") or payload),
            )
            if not summary_sent:
                logger.warning("payment_success summary delivery failed tg_id=%s", tg_id)
        else:
            logger.warning("payment_success unknown tariff_key=%s payload=%s", tariff_key, payload)
        return

    # Fallback for legacy/non-standard payloads:
    # resolve the newest pending pay attempt by user + amount.
    payer_tg_id = message.from_user.id if message.from_user else 0
    fallback_attempt = resolve_pending_attempt_for_payment(
        tg_id=int(payer_tg_id),
        amount_stars=int(payment.total_amount),
        currency=str(payment.currency or "XTR"),
        within_hours=24,
    )
    if fallback_attempt:
        tariff_key = normalize_tariff_key(str(fallback_attempt.plan_code or ""))
        tariff = TARIFFS.get(tariff_key)
        if tariff:
            logger.info(
                "payment_success fallback resolved: tg_id=%s attempt_id=%s plan=%s payload=%s",
                payer_tg_id,
                fallback_attempt.id,
                tariff_key,
                payload,
            )
            # Persist real payload to the attempt for traceability, then mark as paid.
            mark_invoice_sent(attempt_id=int(fallback_attempt.id), set_invoice_payload=payload)
            mark_paid(attempt_id=int(fallback_attempt.id), invoice_payload=payload)
            track_event(
                tg_id=int(payer_tg_id),
                event_name="paid",
                source="bot",
                meta={
                    "attempt_id": int(fallback_attempt.id),
                    "plan_code": tariff_key,
                    "invoice_payload": payload,
                    "amount_stars": int(payment.total_amount),
                    "recovered_by_fallback": True,
                },
            )
            fulfilled = await create_subscription(
                message,
                int(payer_tg_id),
                tariff,
                bot,
                paid_amount_stars=int(payment.total_amount),
                pay_attempt_id=int(fallback_attempt.id),
                provider_order_id=str(getattr(payment, "telegram_payment_charge_id", "") or payment_fingerprint),
                send_completion_message=False,
            )
            if not fulfilled:
                return
            _mark_stars_payment_processed(
                payment_fingerprint=payment_fingerprint,
                invoice_payload=payload,
                tg_id=int(payer_tg_id),
            )
            summary_sent = await _send_payment_success_summary(
                message=message,
                bot=bot,
                tg_id=int(payer_tg_id),
                tariff=tariff,
                payment=payment,
                transaction_id=str(getattr(payment, "telegram_payment_charge_id", "") or payload),
            )
            if not summary_sent:
                logger.warning("payment_success fallback summary delivery failed tg_id=%s", payer_tg_id)
            return

    logger.warning(
        "payment_success unhandled payload=%s from_tg=%s amount=%s currency=%s",
        payload,
        payer_tg_id,
        payment.total_amount,
        payment.currency,
    )
    await message.answer("✅ Оплата получена. Откройте POKROV и нажмите «Подключить». Если доступ не обновился, напишите в поддержку.")


@router.callback_query(F.data.startswith("retry_stars:"))
async def retry_stars_fulfillment(callback: CallbackQuery, bot: Bot) -> None:
    grant_id = str(callback.data or "").replace("retry_stars:", "", 1).strip()
    if not grant_id:
        await callback.answer("Не удалось найти оплату", show_alert=True)
        return

    session = Session()
    try:
        grant = session.query(EntitlementGrant).filter_by(id=grant_id).one_or_none()
        if (
            grant is None
            or int(grant.legacy_tg_id or 0) != int(callback.from_user.id)
            or str(grant.provider or "").lower() != "stars"
            or str(grant.grant_kind or "") != "paid_access"
            or str(grant.status or "").lower() not in {"active", "grace"}
            or not str(grant.external_order_id or "").strip()
        ):
            await callback.answer("Эта оплата недоступна для повторной выдачи", show_alert=True)
            return
        external_order_id = str(grant.external_order_id)
        plan_code = str(grant.plan_code or "").strip().lower()
        duration_days = int(grant.duration_days or 0)
    finally:
        session.close()

    if _stars_payment_already_processed(external_order_id):
        await callback.answer("Доступ уже выдан", show_alert=False)
        return
    tariff = next(
        (
            value
            for value in TARIFFS.values()
            if int(value.get("stars") or 0) > 0
            and str(value.get("subId") or "").strip().lower() == plan_code
            and int(value.get("days") or 0) == duration_days
        ),
        None,
    )
    if tariff is None:
        await callback.answer("Тариф не найден — напишите в поддержку", show_alert=True)
        return

    await callback.answer("Повторяю выдачу доступа…", show_alert=False)
    fulfilled = await create_subscription(
        callback.message,
        int(callback.from_user.id),
        tariff,
        bot,
        provider_order_id=external_order_id,
    )
    if not fulfilled:
        return
    _mark_stars_payment_processed(
        payment_fingerprint=external_order_id,
        invoice_payload=f"retry_grant:{grant_id}",
        tg_id=int(callback.from_user.id),
    )

async def create_subscription(
    message: Message,
    tg_id: int,
    tariff: dict,
    bot: Bot,
    paid_amount_stars: int | None = None,
    pay_attempt_id: int | None = None,
    provider_order_id: str | None = None,
    send_completion_message: bool = True,
):
    """Create or extend subscription"""
    # Check if this is a PAID purchase (for referral bonus)
    is_paid_purchase = tariff["stars"] > 0
    first_paid_purchase = False
    referral_tg_id = 0
    stable_order_id = ""
    payment_grant_id = ""

    # Account entitlement is the durable fulfillment authority. Persist it before
    # retryable panel/provisioning work so a provider-confirmed payment cannot be lost.
    if is_paid_purchase:
        ensure_pending_user(int(tg_id))
        session = Session()
        try:
            db_user = session.query(User).filter_by(tg_id=int(tg_id)).one()
            ensure_user_account_foundation(session, db_user, now=_utcnow())
            session.flush()
            referral_tg_id = int(db_user.referrer_id or 0)
            if referral_tg_id > 0:
                referrer = session.query(User).filter_by(tg_id=referral_tg_id).one_or_none()
                if referrer is not None:
                    ensure_user_account_foundation(session, referrer, now=_utcnow())
                    session.flush()
                    create_referral_relationship(
                        session,
                        referred_account_id=str(db_user.account_id),
                        referrer_account_id=str(referrer.account_id),
                        source="legacy_referrer_projection",
                        now=_utcnow(),
                    )
            stable_order_id = str(provider_order_id or f"pay-attempt:{int(pay_attempt_id or 0)}:{int(tg_id)}")
            payment_result = record_successful_payment_grant(
                session,
                account_id=str(db_user.account_id),
                legacy_tg_id=int(tg_id),
                provider="stars",
                order_id=stable_order_id,
                plan_code=str(tariff.get("subId") or tariff.get("sub_type") or "stars_paid").lower(),
                duration_days=int(tariff["days"]),
                paid_at=_utcnow(),
            )
            payment_grant_id = str(payment_result.grant.id)
            first_paid_purchase = bool(payment_result.is_first_payment)
            try:
                grant_metadata = json.loads(str(payment_result.grant.metadata_json or "{}"))
            except (TypeError, ValueError):
                grant_metadata = {}
            if not isinstance(grant_metadata, dict):
                grant_metadata = {}
            if not bool(grant_metadata.get("stars_amount_recorded")):
                db_user.stars_paid = int(db_user.stars_paid or 0) + int(tariff["stars"] or 0)
                grant_metadata["stars_amount_recorded"] = True
                grant_metadata["stars_amount"] = int(tariff["stars"] or 0)
                payment_result.grant.metadata_json = json.dumps(
                    grant_metadata,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
            db_user.pending_discount_pct = None
            db_user.pending_discount_code = None
            db_user.pending_discount_set_at = None
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    user = get_user(tg_id)
    try:
        panel_client = await panel.get_existing_client(tg_id)
    except Exception:
        if is_paid_purchase:
            await _send_stars_fulfillment_retry(message, payment_grant_id=payment_grant_id)
            return False
        raise

    if panel_client:
        if is_paid_purchase:
            try:
                _reconcile_owned_panel_client(
                    tg_id=int(tg_id),
                    panel_client=panel_client,
                    provider_order_id=stable_order_id,
                )
            except Exception as exc:
                logger.warning(
                    "Stars panel credential reconciliation failed tg_id=%s order_id=%s error_type=%s",
                    int(tg_id),
                    stable_order_id,
                    type(exc).__name__,
                )
                await _send_stars_fulfillment_retry(message, payment_grant_id=payment_grant_id)
                return False
        # User exists in panel - update DB and add traffic
        client_uuid = panel_client.get("id")
        if user:
            if not is_paid_purchase:
                extend_user(tg_id, tariff["days"], tariff["stars"])
                # Keep current plan label in DB for non-payment flows.
                session = Session()
                db_user = session.query(User).filter_by(tg_id=tg_id).first()
                if db_user:
                    db_user.sub_type = tariff.get("sub_type") or db_user.sub_type
                    if not str(db_user.sub_token or "").strip():
                        db_user.sub_token = generate_sub_token()
                        logger.info("generated missing sub_token for existing user tg_id=%s", int(tg_id))
                    if _is_freemium_sub_type(db_user.sub_type):
                        mark_user_became_free(db_user)
                    session.commit()
                session.close()
        else:
            create_user(tg_id, panel_client.get("id"), panel_client.get("email"),
                       tariff.get("sub_type") or tariff["subId"], tariff["days"], tariff["gb"], tariff["stars"])

        # Add traffic to existing client. A false result is a retryable panel failure.
        try:
            traffic_updated = bool(await panel.update_client_traffic(tg_id, tariff["gb"]))
        except Exception:
            traffic_updated = False
        if not traffic_updated:
            if is_paid_purchase:
                await _send_stars_fulfillment_retry(message, payment_grant_id=payment_grant_id)
            else:
                await message.answer("❌ Не получилось обновить доступ. Попробуйте ещё раз или напишите в поддержку.")
            return False
    else:
        # Create new in panel
        user_uuid = str(uuid.uuid4())
        email = f"User_{tg_id}"

        # Generate sub_token BEFORE creating in panel
        sub_token = generate_sub_token()

        # 3x-ui "subId" in this project is the per-user subscription token, not the tariff.
        # The 3rd argument here is our internal plan marker to decide which nodes to provision.
        try:
            success = await panel.add_client(user_uuid, email, tariff.get("sub_type") or tariff["subId"], tariff["gb"], tg_id, sub_token)
        except Exception:
            success = False

        if not success:
            if is_paid_purchase:
                await _send_stars_fulfillment_retry(message, payment_grant_id=payment_grant_id)
            else:
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="💬 Написать в поддержку", url=f"https://t.me/{SUPPORT_USERNAME}?start=ticket_new")],
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
                ])
                await message.answer("❌ Не получилось включить доступ.\n\nНажмите кнопку ниже, и поддержка подскажет, что делать дальше.", reply_markup=kb)
            return False

        if is_paid_purchase:
            try:
                created_panel_client = await panel.get_existing_client(tg_id)
                _reconcile_owned_panel_client(
                    tg_id=int(tg_id),
                    panel_client=created_panel_client,
                    provider_order_id=stable_order_id,
                )
            except Exception as exc:
                logger.warning(
                    "Stars panel credential reconciliation failed after create tg_id=%s order_id=%s error_type=%s",
                    int(tg_id),
                    stable_order_id,
                    type(exc).__name__,
                )
                await _send_stars_fulfillment_retry(message, payment_grant_id=payment_grant_id)
                return False
        else:
            create_user(
                tg_id,
                user_uuid,
                email,
                tariff.get("sub_type") or tariff["subId"],
                tariff["days"],
                tariff["gb"],
                tariff["stars"],
            )
            # create_user generates a token; keep the one provisioned in panel.
            session = Session()
            db_user = session.query(User).filter_by(tg_id=tg_id).first()
            if db_user:
                db_user.sub_token = sub_token
                session.commit()
            session.close()

    # Keep legacy trial flag only for actual TRIAL plans (not used by default).
    sub_type = (tariff.get("sub_type") or "").upper()
    if tariff["stars"] == 0 and sub_type.startswith("TRIAL"):
        mark_trial_used(tg_id)

    if is_paid_purchase and first_paid_purchase and referral_tg_id > 0 and paid_amount_stars and int(paid_amount_stars) > 0:
        award_referral_points(
            tg_id=referral_tg_id,
            paid_stars=int(paid_amount_stars),
            ref_tg_id=int(tg_id),
            pay_attempt_id=pay_attempt_id,
        )

    # 🔥 Update streak and bonus only for paid purchases.
    if is_paid_purchase:
        new_streak, streak_bonus = update_streak(tg_id)
        if streak_bonus > 0:
            try:
                await panel.update_client_traffic(tg_id, streak_bonus)
                await message.answer(
                    f"🔥 *Streak бонус!*\n\n"
                    f"Вы на волне уже *{new_streak} месяцев*!\n"
                    f"Вам начислено *+{streak_bonus} дней*!",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass

    user = get_user(tg_id)
    expiry = user.expiry_at.strftime("%d.%m.%Y") if user and user.expiry_at else "—"
    is_free = bool(user and user_uses_free_pool(user))
    free_note = ""
    if is_free:
        free_note = _free_access_note(user)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📲 Подключить устройство", callback_data="instruction")],
        [InlineKeyboardButton(text="🌐 Открыть кабинет", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="🔗 Ручная ссылка / QR", callback_data="show_key")],
        [InlineKeyboardButton(text="◀️ В меню", callback_data="back")]
    ])

    if send_completion_message:
        await message.answer(
            f"✅ *Доступ готов!*\n\n"
            f"📅 До: `{expiry}`\n\n"
            "Лучший путь: откройте POKROV, войдите тем же способом и нажмите «Подключить».\n\n"
            "Если приложения нет под рукой, нажмите «Ручная ссылка / QR» ниже. Я покажу ссылку отдельно и напомню, как использовать её безопасно."
            f"{free_note}",
            reply_markup=kb,
            parse_mode=ParseMode.MARKDOWN
        )
    return True
