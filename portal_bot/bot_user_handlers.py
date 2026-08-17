"""Customer entry, account, rewards and support Telegram handlers.

Loaded by the bot composition root in source order. Public symbols are
re-exported for backwards compatibility.
"""

try:
    from .module_slices import bootstrap_slice
except ImportError:
    from module_slices import bootstrap_slice

bootstrap_slice(globals())

@router.message(CommandStart())
async def cmd_start(message: Message):
    tg_id = message.from_user.id
    username = message.from_user.username
    _set_support_context(tg_id, enabled=False)

    start_arg = ""
    referral_code = None
    deeplink_promo_code = ""
    deeplink_campaign_key = ""
    friend_gift_referral_code = ""
    opening_bonus_requested = False
    app_link_account_id = 0
    if message.text:
        parts = message.text.split()
        if len(parts) > 1:
            code_part = parts[1].strip()
            start_arg = code_part
            reserved_payment_start = code_part.lower() in {"pay", "renew"}
            if code_part.startswith("ref_"):
                code_part = code_part[4:]
            if code_part.upper().startswith("SWAZ") and len(code_part) == 8:
                referral_code = code_part.upper()
            deeplink_promo_code, deeplink_campaign_key = _parse_start_deeplink_context(start_arg)
            friend_gift_referral_code = _parse_friend_gift_ref_code(start_arg)
            start_link_action = (
                {"promo_code": "", "campaign_key": "", "opening_bonus": False, "app_link_account_id": 0}
                if reserved_payment_start
                else _resolve_start_link_action(start_arg)
            )
            if str(start_link_action.get("promo_code") or "").strip():
                deeplink_promo_code = str(start_link_action.get("promo_code") or "").strip().upper()[:20]
            if str(start_link_action.get("campaign_key") or "").strip():
                deeplink_campaign_key = str(start_link_action.get("campaign_key") or "").strip()[:64]
            opening_bonus_requested = bool(start_link_action.get("opening_bonus"))
            app_link_account_id = int(start_link_action.get("app_link_account_id") or 0)

    try:
        await message.delete()
    except Exception:
        pass

    if tg_id in last_bot_message:
        try:
            await message.bot.delete_message(tg_id, last_bot_message[tg_id])
        except Exception:
            pass

    user = get_user(tg_id)
    panel_client = await panel.get_existing_client(tg_id)
    created_new = False

    if panel_client and not user:
        user = create_user(
            tg_id=tg_id,
            user_uuid=panel_client.get("id", str(uuid.uuid4())),
            email=panel_client.get("email", f"User_{tg_id}"),
            sub_type="PAID",
            days=365,
            gb=1000,
            stars=0,
            username=username,
        )
    elif not user:
        user, created_new = ensure_pending_user(tg_id, username=username)

    if referral_code:
        set_referrer_by_code(tg_id, referral_code)
    if friend_gift_referral_code:
        set_referrer_by_code(tg_id, friend_gift_referral_code)
    update_user_username(tg_id, username)
    _consume_bot_acquisition_handoff(
        tg_id=int(tg_id),
        user=user,
        start_arg=start_arg,
    )
    if deeplink_promo_code or deeplink_campaign_key:
        checkout_context_by_user[int(tg_id)] = {
            "promo_code": str(deeplink_promo_code or "").upper()[:20],
            "campaign_key": str(deeplink_campaign_key or "")[:64],
        }
    _track_bot_entry(
        tg_id=int(tg_id),
        entrypoint="start",
        meta={
            "created_new": bool(created_new),
            "start_arg_present": bool(start_arg),
            "start_arg_kind": _classify_start_arg_for_analytics(
                start_arg=start_arg,
                referral_code=referral_code,
                deeplink_promo_code=deeplink_promo_code,
                deeplink_campaign_key=deeplink_campaign_key,
                friend_gift_referral_code=friend_gift_referral_code,
                opening_bonus_requested=opening_bonus_requested,
                app_link_account_id=app_link_account_id,
            ),
        },
    )

    if start_arg.strip().lower() == "pair_device":
        await _send_device_pairing_code_message(
            bot=message.bot,
            chat_id=int(tg_id),
            tg_id=int(tg_id),
            entrypoint="start",
        )
        return

    if app_link_account_id > 0:
        track_event(
            tg_id=int(tg_id),
            event_name="app_telegram_link_bot_started",
            source="bot",
            meta={"handoff": "app_link"},
        )
        bind_status = _bind_app_account_to_telegram(
            account_tg_id=int(app_link_account_id),
            telegram_id=int(tg_id),
            telegram_username=username,
            start_code=start_arg,
        )
        track_event(
            tg_id=int(tg_id),
            event_name="app_telegram_link_start",
            source="bot",
            meta={"status": str(bind_status or "")},
        )
        if bind_status in {"linked", "already_linked"}:
            track_event(
                tg_id=int(tg_id),
                event_name="app_telegram_link_bound",
                source="bot",
                meta={"status": str(bind_status)},
            )
        messages = {
            "linked": (
                "✅ *Telegram уже привязан к POKROV.*\n\n"
                "Дальше вернитесь в приложение и нажмите «Проверить подписку»."
            ),
            "already_linked": (
                "✅ *Этот Telegram уже привязан к вашему аккаунту POKROV.*\n\n"
                "Дальше вернитесь в приложение и нажмите «Проверить подписку»."
            ),
            "telegram_already_linked": (
                "⚠️ Этот Telegram уже привязан к другому аккаунту POKROV.\n\n"
                "Если это не ваш случай, напишите в поддержку."
            ),
            "account_linked_elsewhere": (
                "⚠️ Этот аккаунт POKROV уже привязан к другому Telegram.\n\n"
                "Если нужно переназначить привязку, напишите в поддержку."
            ),
            "transitive_link_not_supported": (
                "⚠️ Эта ссылка затрагивает уже связанную учётную запись.\n\n"
                "Автоматически объединять цепочку небезопасно. Напишите в поддержку."
            ),
            "not_found": (
                "⚠️ Не удалось найти аккаунт POKROV для этой ссылки.\n\n"
                "Дальше откройте приложение и запросите новую ссылку привязки."
            ),
            "expired": (
                "⌛ Ссылка привязки устарела.\n\n"
                "Дальше откройте приложение POKROV и запросите новую ссылку."
            ),
            "invalid": (
                "⚠️ Ссылка привязки некорректна.\n\n"
                "Дальше откройте приложение POKROV и создайте новую ссылку."
            ),
            "error": (
                "⚠️ Не удалось завершить привязку прямо сейчас.\n\n"
                "Попробуйте ещё раз через минуту или напишите в службу заботы."
            ),
        }
        await message.answer(
            messages.get(
                str(bind_status or ""),
                "⚠️ Не удалось обработать ссылку привязки.\n\nСледующий шаг: откройте приложение POKROV и запросите новую ссылку.",
            ),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📢 Канал POKROV", url=f"https://t.me/{_channel_name_for_url()}")],
                ]
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if str(start_arg or "").strip().lower() in {"weblogin", "web_login", "login_web"}:
        token = create_web_session_token(tg_id=int(tg_id), username=username)
        if not token:
            await message.answer(
                "⚠️ Не получилось открыть вход прямо сейчас. Попробуйте ещё раз через минуту или откройте кабинет из меню бота.",
                reply_markup=main_keyboard(tg_id),
            )
            return
        login_url = _web_login_url_with_token(token)
        await message.answer(
            "✅ Вход подтверждён.\n\nСледующий шаг: откройте кабинет по кнопке ниже.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🌐 Открыть кабинет", url=login_url)],
                    [InlineKeyboardButton(text="◀️ В меню", callback_data="back")],
                ]
            ),
        )
        track_event(
            tg_id=int(tg_id),
            event_name="web_login_ticket_issued",
            source="bot",
            meta={"start_arg": str(start_arg or "").lower()},
        )
        return

    if str(start_arg or "").strip().lower() in {"pay", "renew"}:
        track_event(
            tg_id=int(tg_id),
            event_name="deep_link_opened",
            source="bot",
            meta={"kind": "payment", "start_arg": str(start_arg or "").strip().lower()},
        )
        if not check_tos_accepted(tg_id):
            await message.answer(
                _tos_offer_text(),
                reply_markup=_tos_offer_keyboard(back_callback="back"),
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        fresh_user = get_user(tg_id)
        show_trial = _trial_offer_available(fresh_user)
        ok = await _send_rich_copy(
            message=message,
            bot=message.bot,
            chat_id=tg_id,
            copy=build_choose_tariff_rich_copy(show_trial=show_trial),
            rows=tariff_keyboard_specs(
                tg_id,
                show_trial=show_trial,
                show_gb_only=False,
                include_long_plans=False,
            ),
        )
        if not ok:
            await message.answer(
                build_choose_tariff_text(show_trial=show_trial),
                reply_markup=tariff_keyboard(
                    tg_id,
                    show_trial=show_trial,
                    show_gb_only=False,
                    include_long_plans=False,
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
        return

    promo_requested = bool(
        OPENING_PREMIUM_ENABLED
        and OPENING_PREMIUM_START_CODE
        and start_arg
        and start_arg.strip().lower() == OPENING_PREMIUM_START_CODE
    )
    promo_requested = bool(promo_requested or opening_bonus_requested)
    if promo_requested:
        activated, reason = await _try_activate_opening_premium_bonus(
            message=message,
            bot=message.bot,
            tg_id=tg_id,
            username=username,
        )
        if activated:
            return
        if reason == "already_claimed":
            await message.answer(
                "🎁 Бонус по ссылке уже был активирован для вашего аккаунта.\n\n"
                "Открываю главное меню.",
                reply_markup=main_keyboard(tg_id),
            )
            return
        if reason == "already_paid_active":
            await message.answer(
                "✅ У вас уже есть платный доступ.\n\n"
                "Открываю главное меню.",
                reply_markup=main_keyboard(tg_id),
            )
            return
        if reason == "tos_required":
            await message.answer(
                "⚠️ Сначала примите условия, и я сразу продолжу.",
                reply_markup=_tos_offer_keyboard(back_callback="back"),
                parse_mode=ParseMode.MARKDOWN,
            )
            return

    if friend_gift_referral_code:
        if check_tos_accepted(tg_id):
            activated, reason = await _try_activate_friend_gift_bonus(
                message=message,
                bot=message.bot,
                tg_id=tg_id,
                username=username,
                referral_code=friend_gift_referral_code,
            )
            if activated:
                await message.answer(
                    f"🎁 Приглашение принято. +{FRIEND_GIFT_DAYS} дней добавятся после первого подтверждённого подключения.",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return
            if reason == "already_linked":
                await message.answer(
                    "🎁 Приглашение уже привязано к вашему аккаунту. Бонус ждёт первого подтверждённого подключения.\n\n"
                    "Открываю главное меню.",
                    reply_markup=main_keyboard(tg_id),
                )
                return
            if reason == "already_paid_active":
                await message.answer(
                    "✅ У вас уже есть платный доступ.\n\n"
                    "Открываю главное меню.",
                    reply_markup=main_keyboard(tg_id),
                )
                return
            if reason == "invalid_ref":
                await message.answer("⚠️ Подарочная ссылка недействительна или устарела.")
        else:
            pending_auto_friend_gift_referrals[int(tg_id)] = str(friend_gift_referral_code).upper()[:10]
            await message.answer(
                "🎁 Подарок сохранён.\n"
                "Сначала примите условия, затем я активирую его автоматически.",
                parse_mode=ParseMode.MARKDOWN,
            )

    if deeplink_promo_code:
        if check_tos_accepted(tg_id):
            ok, result = activate_promo_code_for_user(tg_id, deeplink_promo_code)
            await message.answer(result, parse_mode=ParseMode.MARKDOWN)
            track_event(
                tg_id=int(tg_id),
                event_name="deep_link_opened",
                source="bot",
                meta={
                    "kind": "promo",
                    "promo_code": str(deeplink_promo_code).upper()[:20],
                    "campaign_key": str(deeplink_campaign_key or "")[:64] or None,
                    "applied": bool(ok),
                },
            )
        else:
            pending_auto_promo_codes[int(tg_id)] = str(deeplink_promo_code).upper()[:20]
            await message.answer(
                "🎟️ Промокод сохранён.\n"
                "Сначала примите условия, затем я применю его автоматически.",
                parse_mode=ParseMode.MARKDOWN,
            )

    if not created_new:
        returning_text = bot_text("bot.menu.returning")
        ok = await _send_rich_copy(
            message=message,
            bot=message.bot,
            chat_id=tg_id,
            copy=home_copy(
                returning=True,
                show_trial=_trial_offer_available(get_user(tg_id)),
            ),
            rows=main_keyboard_specs(tg_id),
        )
        if not ok:
            await message.answer(
                returning_text,
                reply_markup=main_keyboard(tg_id),
                parse_mode=ParseMode.MARKDOWN,
            )
        return

    text = bot_text("bot.menu.new_user")
    rows = new_user_keyboard_specs()
    ok = await _send_rich_copy(
        message=message,
        bot=message.bot,
        chat_id=tg_id,
        copy=home_copy(new_user=True),
        rows=rows,
    )
    if not ok:
        sent = await message.answer(
            text,
            reply_markup=_keyboard_from_specs(rows),
            parse_mode=ParseMode.MARKDOWN,
        )
        last_bot_message[tg_id] = sent.message_id

@router.callback_query(F.data == "back")
async def back_to_main(callback: CallbackQuery):
    tg_id = callback.from_user.id
    pending_redeem_codes.discard(tg_id)
    pending_promo_codes.discard(tg_id)
    pending_auto_promo_codes.pop(int(tg_id), None)
    pending_auto_friend_gift_referrals.pop(int(tg_id), None)

    home_text = bot_text("bot.menu.home")
    ok = await _edit_rich_copy(
        callback=callback,
        copy=home_copy(show_trial=_trial_offer_available(get_user(tg_id))),
        rows=main_keyboard_specs(tg_id),
    )
    if not ok:
        await callback.message.edit_text(
            home_text,
            reply_markup=main_keyboard(tg_id),
            parse_mode=ParseMode.MARKDOWN,
        )
    await callback.answer()

@router.callback_query(F.data == "charge")
async def show_tariffs(callback: CallbackQuery):
    tg_id = callback.from_user.id
    user = get_user(tg_id)

    # Check if user has accepted TOS
    if not check_tos_accepted(tg_id):
        await callback.message.edit_text(
            _tos_offer_text(),
            reply_markup=_tos_offer_keyboard(back_callback="back"),
            parse_mode=ParseMode.MARKDOWN,
        )
        await callback.answer()
        return

    # Do not advertise a second trial or a downgrade to an active paid user.
    show_trial = _trial_offer_available(user)

    await _edit_rich_copy(
        callback=callback,
        copy=build_choose_tariff_rich_copy(show_trial=show_trial),
        rows=tariff_keyboard_specs(
            tg_id,
            show_trial=show_trial,
            show_gb_only=False,
            include_long_plans=False,
        ),
    )
    await callback.answer()


@router.callback_query(F.data == "charge_stars")
async def show_tariffs_stars(callback: CallbackQuery):
    tg_id = callback.from_user.id
    user = get_user(tg_id)
    show_trial = _trial_offer_available(user)
    await _edit_rich_copy(
        callback=callback,
        copy=build_choose_tariff_rich_copy(show_trial=show_trial),
        rows=tariff_keyboard_specs(
            tg_id,
            show_trial=show_trial,
            show_gb_only=False,
            include_long_plans=False,
        ),
    )
    await callback.answer()


@router.callback_query(F.data == "charge_long")
async def show_long_tariffs(callback: CallbackQuery):
    tg_id = callback.from_user.id
    if not check_tos_accepted(tg_id):
        await callback.message.edit_text(
            _tos_offer_text(),
            reply_markup=_tos_offer_keyboard(back_callback="back"),
            parse_mode=ParseMode.MARKDOWN,
        )
        await callback.answer()
        return

    await _edit_rich_copy(
        callback=callback,
        copy=long_tariffs_copy(),
        rows=tariff_keyboard_specs(
            tg_id,
            show_trial=False,
            show_gb_only=False,
            include_long_plans=True,
        ),
    )
    await callback.answer()

@router.callback_query(F.data == "accept_tos")
async def accept_tos(callback: CallbackQuery):
    tg_id = callback.from_user.id

    # Mark TOS as accepted
    set_tos_accepted(tg_id)

    auto_promo = (pending_auto_promo_codes.pop(int(tg_id), "") or "").strip().upper()
    if auto_promo:
        ok, result = activate_promo_code_for_user(tg_id, auto_promo)
        await callback.message.answer(result, parse_mode=ParseMode.MARKDOWN)
        track_event(
            tg_id=int(tg_id),
            event_name="deep_link_opened",
            source="bot",
            meta={"kind": "promo_after_tos", "promo_code": auto_promo, "applied": bool(ok)},
        )

    auto_friend_ref = (pending_auto_friend_gift_referrals.pop(int(tg_id), "") or "").strip().upper()
    if auto_friend_ref:
        activated, reason = await _try_activate_friend_gift_bonus(
            message=callback.message,
            bot=callback.message.bot,
            tg_id=tg_id,
            username=callback.from_user.username,
            referral_code=auto_friend_ref,
        )
        if activated:
            await callback.answer("✅ Условия приняты. Подарок активирован!", show_alert=True)
            return
        if reason == "already_claimed":
            await callback.message.answer(
                "🎁 Подарок по ссылке уже был активирован ранее.",
                parse_mode=ParseMode.MARKDOWN,
            )
        elif reason == "invalid_ref":
            await callback.message.answer(
                "⚠️ Подарочная ссылка недействительна.",
                parse_mode=ParseMode.MARKDOWN,
            )

    # Now show tariffs
    user = get_user(tg_id)

    show_trial = _trial_offer_available(user)
    await _edit_rich_copy(
        callback=callback,
        copy=build_choose_tariff_rich_copy(show_trial=show_trial),
        rows=tariff_keyboard_specs(
            tg_id,
            show_trial=show_trial,
            show_gb_only=False,
            include_long_plans=False,
        ),
    )
    await callback.answer("✅ Условия приняты!")

@router.callback_query(F.data == "status")
async def show_status(callback: CallbackQuery):
    tg_id = callback.from_user.id
    user = get_user(tg_id)

    if not user:
        none_text = bot_text("bot.status.none")
        ok = await _edit_text_with_specs(
            bot=callback.message.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=none_text,
            rows=main_keyboard_specs(tg_id),
            parse_mode=ParseMode.MARKDOWN,
        )
        if not ok:
            await callback.message.edit_text(
                none_text,
                reply_markup=main_keyboard(tg_id),
                parse_mode=ParseMode.MARKDOWN,
            )
        await callback.answer()
        return

    expiry_dt = _naive_utc(user.expiry_at) if user else None
    if expiry_dt:
        expiry = expiry_dt.strftime("%d.%m.%Y")
    else:
        expiry = "—"

    stars = user.stars_paid if user else 0
    is_active = bool(user and user.is_active and expiry_dt and expiry_dt > _utcnow())
    status_icon = "🟢" if is_active else "🔴"
    status_name = "Активен" if is_active else "Не активен"
    status_text = bot_text(
        "bot.status.card",
        tg_id=tg_id,
        expiry=expiry,
        stars=stars,
        status_icon=status_icon,
        status_text=status_name,
        plan_label=_plan_label_ru(user.sub_type if user else ""),
    )
    base_limit = FREE_LIMIT_IP if _is_freemium_sub_type(user.sub_type) else PAID_LIMIT_IP
    extra_slots = active_family_slots(tg_id)
    status_text += f"\n📱 Устройства: до `{base_limit + extra_slots}`"
    if extra_slots:
        status_text += f" (Family: +{extra_slots})"
    if user_uses_free_pool(user):
        remaining_gb, total_gb = await _free_remaining_gb(tg_id, user=user)
        if remaining_gb is None:
            status_text += f"\n📊 Бесплатный лимит: до `{int(total_gb)}` ГБ\n⏳ Остаток: `н/д`"
        else:
            status_text += f"\n📊 Бесплатный остаток: `{remaining_gb}` из `{int(total_gb)}` ГБ"
        status_text += f"\n📡 Скорость режима: до `{_free_speed_mbit_for_user(user)}` Мбит/с"
        is_subscriber = await check_subscription(tg_id, callback.message.bot)
        if is_subscriber:
            status_text += "\n📢 Канал подтверждён — бонусный режим доступен."
        else:
            status_text += "\n📢 Канал не подтверждён — бонусный доступ не активен."
    panel_snapshot = await _panel_online_snapshot(tg_id)
    status_text += f"\n🌐 Онлайн: `{_panel_online_text(panel_snapshot)}`"
    status_text += f"\n🕓 Последний онлайн: `{_panel_last_online_text(panel_snapshot)}`"

    ok = await _edit_text_with_specs(
        bot=callback.message.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=status_text,
        rows=main_keyboard_specs(tg_id),
        parse_mode=ParseMode.MARKDOWN,
    )
    if not ok:
        await callback.message.edit_text(
            status_text,
            reply_markup=main_keyboard(tg_id),
            parse_mode=ParseMode.MARKDOWN,
        )
    await callback.answer()

@router.callback_query(F.data == "show_key")
async def show_key(callback: CallbackQuery):
    if not await _require_private_callback(callback):
        return
    try:
        await callback.answer()
    except Exception:
        pass

    tg_id = callback.from_user.id
    track_event(tg_id=tg_id, event_name="clicked_connect", source="bot")
    user = get_user(tg_id)

    if not check_tos_accepted(tg_id):
        await _edit_or_answer_callback_text(
            callback,
            _tos_offer_text(),
            reply_markup=_tos_offer_keyboard(back_callback="back"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if not user:
        rows = [
            [_main_menu_cta_spec(tg_id)],
            [
                _btn_spec(text="◀️ Назад", callback_data="back")
            ],
        ]
        ok = await _edit_text_with_specs(
            bot=callback.message.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="⚠️ *Ручной ссылки пока нет.*\n\nСначала запустите доступ, и я сразу подготовлю запасной вариант.",
            rows=rows,
            parse_mode=ParseMode.MARKDOWN,
        )
        if not ok:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=_main_connect_cta_text(tg_id), callback_data="charge")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
            ])
            await _edit_or_answer_callback_text(
                callback,
                "⚠️ *Ручной ссылки пока нет.*\n\nСначала запустите доступ, и я сразу подготовлю запасной вариант.",
                reply_markup=kb,
                parse_mode=ParseMode.MARKDOWN
            )
        return

    expiry = _naive_utc(user.expiry_at)
    if not bool(user.is_active and expiry and expiry > _utcnow()):
        rows = [
            [_main_menu_cta_spec(tg_id)],
            [_btn_spec(text="◀️ Назад", callback_data="back")],
        ]
        await _edit_text_with_specs(
            bot=callback.message.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="⚠️ *Активного доступа пока нет.*\n\nВыберите вариант старта, и я подготовлю приложение и запасную ручную ссылку.",
            rows=rows,
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    await _edit_or_answer_callback_text(callback, "🔄 `Формирую ссылку и QR...`", parse_mode=ParseMode.MARKDOWN)

    sub_link = build_subscription_link(tg_id)
    happ_link = _subscription_link_for_format(sub_link, "happ")

    is_free = bool(user and user_uses_free_pool(user))
    free_note = ""
    if is_free:
        free_note = _free_access_note(user)
        free_note += f" Платный доступ откроет платные локации и до {PAID_LIMIT_IP} устройств."

    copy_button = _subscription_copy_button(
        label="📋 Скопировать ссылку",
        value=sub_link,
        fallback_callback="copy_key",
    )
    happ_copy_button = _subscription_copy_button(
        label="📋 Скопировать для Happ",
        value=happ_link,
        fallback_callback="copy_happ_key",
    )
    fallback_rows = (
        [[InlineKeyboardButton(text="📝 Показать ссылки текстом", callback_data="copy_key")]]
        if SUPPORTS_BTN_COPY_TEXT
        else []
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [copy_button],
            [happ_copy_button],
            *fallback_rows,
            [InlineKeyboardButton(text="📱 QR для Hiddify", callback_data="show_qr")],
            [InlineKeyboardButton(text="📱 QR для Happ", callback_data="show_happ_qr")],
            [InlineKeyboardButton(text="📲 Как подключить вручную", callback_data="instruction")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")],
        ]
    )

    await _edit_or_answer_callback_text(
        callback,
        f"🔗 *Ручное подключение*\n\n"
        "Это запасной способ, если POKROV не подключился сам. Сначала попробуйте приложение; ссылку используйте только для ручного подключения.\n\n"
        "Это личная ссылка для подключения. Не пересылайте её: по ней можно пользоваться вашим доступом.\n\n"
        f"`{sub_link}`\n\n"
        "Если приложения POKROV пока нет на устройстве, начните с Hiddify. Для Happ используйте отдельную кнопку или QR — вручную менять ссылку не нужно.\n"
        f"{free_note}",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )

@router.callback_query(F.data == "copy_key")
async def copy_key_callback(callback: CallbackQuery):
    if not await _require_private_callback(callback):
        return
    tg_id = callback.from_user.id
    sub_link = build_subscription_link(tg_id)
    track_event(tg_id=tg_id, event_name="copied_key", source="bot")
    await callback.message.answer(
        f"📋 <b>Обычная ссылка для Hiddify</b>\n<code>{html.escape(sub_link)}</code>",
        parse_mode=ParseMode.HTML,
    )
    await callback.answer("Ссылка показана")


@router.callback_query(F.data == "copy_happ_key")
async def copy_happ_key_callback(callback: CallbackQuery):
    if not await _require_private_callback(callback):
        return
    tg_id = callback.from_user.id
    happ_link = _subscription_link_for_format(build_subscription_link(tg_id), "happ")
    track_event(tg_id=tg_id, event_name="copied_key", source="bot", meta={"format": "happ"})
    await callback.message.answer(
        f"📋 <b>Ссылка для Happ</b>\n<code>{html.escape(happ_link)}</code>",
        parse_mode=ParseMode.HTML,
    )
    await callback.answer("Ссылка Happ показана")


@router.callback_query(F.data == "show_qr")
async def show_qr_code(callback: CallbackQuery):
    await _show_subscription_qr(callback, format_name="")


@router.callback_query(F.data == "show_happ_qr")
async def show_happ_qr_code(callback: CallbackQuery):
    await _show_subscription_qr(callback, format_name="happ")


async def _show_subscription_qr(callback: CallbackQuery, *, format_name: str) -> None:
    if not await _require_private_callback(callback):
        return
    tg_id = callback.from_user.id
    sub_link = build_subscription_link(tg_id)
    if format_name:
        sub_link = _subscription_link_for_format(sub_link, format_name)

    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(sub_link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    bio = BytesIO()
    img.save(bio, "PNG")
    bio.seek(0)
    file = BufferedInputFile(bio.read(), filename="pokrov-key.png")

    sent = await callback.message.bot.send_photo(
        chat_id=int(callback.message.chat.id),
        photo=file,
        caption=(
            f"📱 *QR для {'Happ' if format_name == 'happ' else 'Hiddify'}*\n\n"
            "QR содержит личную ссылку подключения - не пересылайте его посторонним."
        ),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    _subscription_copy_button(
                        label="📋 Скопировать ссылку",
                        value=sub_link,
                        fallback_callback="copy_happ_key" if format_name == "happ" else "copy_key",
                    )
                ],
                [InlineKeyboardButton(text="✕ Закрыть QR", callback_data="qr_close")],
            ]
        ),
        track_context=False,
    )
    qr_message_id = int(getattr(sent, "message_id", 0) or 0)
    if qr_message_id:
        await _schedule_auto_delete(
            callback.message.bot,
            chat_id=int(callback.message.chat.id),
            message_id=qr_message_id,
        )
    await callback.answer("QR для подключения готов")


@router.callback_query(F.data == "qr_close")
async def qr_close(callback: CallbackQuery):
    if not await _require_private_callback(callback):
        return
    chat_id = int(callback.message.chat.id)
    message_id = int(callback.message.message_id)
    _cancel_auto_delete(chat_id, message_id)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.answer("QR закрыт")


@router.callback_query(F.data == "share_access")
async def share_family_access(callback: CallbackQuery):
    await callback.message.answer(
        "🔒 *Личную ссылку лучше не пересылать.*\n\n"
        "Для своего нового устройства откройте POKROV и войдите в тот же аккаунт. "
        "Если нужен семейный слот или перенос доступа, напишите в поддержку.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать в поддержку", url=f"https://t.me/{SUPPORT_USERNAME}?start=ticket_new")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="show_key")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "panic_menu")
async def panic_menu(callback: CallbackQuery):
    if not await _require_private_callback(callback):
        return
    text = (
        "🛡 *Обновить ссылку подключения*\n\n"
        "Действие меняет только URL подписки. Уже импортированные конфигурации могут продолжить работать.\n\n"
        "Если нужно отозвать доступ с потерянного или чужого устройства, сначала напишите в поддержку — требуется отдельная проверка и отзыв устройства."
    )
    rows = [
        [
            _btn_spec(
                text="Выпустить новую ссылку",
                callback_data="panic_execute",
                style=BTN_STYLE_DANGER,
                emoji_key="warning",
            )
        ],
        [
            _btn_spec(text="◀️ Отмена", callback_data="show_key")
        ],
    ]
    ok = await _edit_text_with_specs(
        bot=callback.message.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        rows=rows,
        parse_mode=ParseMode.MARKDOWN,
    )
    if not ok:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="♻️ Выпустить новую ссылку", callback_data="panic_execute")],
            [InlineKeyboardButton(text="◀️ Отмена", callback_data="show_key")],
        ])
        await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    await callback.answer()


@router.callback_query(F.data == "panic_execute")
async def panic_execute(callback: CallbackQuery, bot: Bot):
    if not await _require_private_callback(callback):
        return
    user_id = callback.from_user.id
    user = get_user(user_id)
    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    await callback.message.edit_text("🔄 *Готовлю новую ссылку...*", parse_mode=ParseMode.MARKDOWN)

    new_token = generate_sub_token()
    session = Session()
    user_uuid = ""
    is_active = True
    try:
        db_user = session.query(User).filter_by(tg_id=user_id).first()
        if db_user:
            db_user.sub_token = new_token
            user_uuid = str(db_user.uuid or "")
            is_active = bool(db_user.is_active)
            session.commit()
    finally:
        session.close()

    panel_sync_ok = False
    if user_uuid:
        try:
            panel_sync_ok = bool(await panel.enable_client(user_uuid, enable=is_active))
        except Exception:
            panel_sync_ok = False

    try:
        await bot.send_message(
            ADMIN_ID,
            f"🚨 <b>PANIC BUTTON PRESSED</b>\nUser: {user_id}\nAction: token rotated and requires review.\nPanel sync: {'ok' if panel_sync_ok else 'failed'}",
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass

    await callback.message.edit_text(
        "✅ *Ссылка обновлена.*\n\n"
        "Откройте ручное подключение, чтобы скопировать новый URL. Уже импортированные конфигурации могли сохранить доступ. "
        "Для отзыва потерянного или чужого устройства напишите в поддержку.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Ручное подключение", callback_data="show_key")],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="back")],
        ]),
    )
    await callback.answer("Новая ссылка выпущена")

@router.callback_query(F.data == "mtproto")
async def show_mtproto(callback: CallbackQuery):
    await callback.message.edit_text(
        "ℹ️ Этот раздел отключен.\n\nСледующий шаг: используйте «🌐 Открыть кабинет» для подключения.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="back")]]),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()

def _device_select_rows() -> list[list[dict[str, str]]]:
    return [
        [
            _btn_spec(
                text="Android",
                callback_data="instr_android",
                style=BTN_STYLE_PRIMARY,
                emoji_key="phone",
            ),
            _btn_spec(text="Windows", callback_data="instr_win", emoji_key="device"),
        ],
        [
            _btn_spec(
                text="Код для входа в POKROV",
                callback_data="device_pairing_code",
                style=BTN_STYLE_SUCCESS,
                emoji_key="key",
            )
        ],
        [_btn_spec(text="Помощь с выбором", callback_data="confused_help", emoji_key="support")],
        [_btn_spec(text="◀️ Назад", callback_data="back")],
    ]


def _device_select_keyboard() -> InlineKeyboardMarkup:
    return _keyboard_from_specs(_device_select_rows())


async def _render_device_select(callback: CallbackQuery) -> None:
    """Single device-selection screen shared by instruction and mode_simple."""
    await _edit_rich_copy(
        callback=callback,
        copy=device_picker_copy(),
        rows=_device_select_rows(),
    )
    await callback.answer()


@router.callback_query(F.data == "instruction")
async def show_instruction(callback: CallbackQuery):
    await _render_device_select(callback)


@router.callback_query(F.data == "confused_help")
async def confused_help(callback: CallbackQuery):
    rows = [
        [
            _btn_spec(
                text="📲 Подключить это устройство",
                callback_data="instruction",
                style=BTN_STYLE_PRIMARY,
            )
        ],
        [_btn_spec(text="🎫 Есть код оплаты или подарок", callback_data="menu_more")],
        [_btn_spec(text="Есть личная ссылка", callback_data="show_key", emoji_key="link")],
        [_btn_spec(text="Подключение не работает", callback_data="support", emoji_key="warning")],
        [_btn_spec(text="Частые вопросы", callback_data="faqmenu", emoji_key="faq")],
        [_btn_spec(text="◀️ Назад", callback_data="back")],
    ]
    await _edit_rich_copy(
        callback=callback,
        copy=help_triage_copy(),
        rows=rows,
    )
    await callback.answer()


def _issue_bot_device_pairing_code(tg_id: int) -> str:
    session = Session()
    try:
        user = (
            session.query(User)
            .filter(User.tg_id == int(tg_id))
            .with_for_update()
            .one_or_none()
        )
        if user is None:
            raise device_pairing_service.DevicePairingError(
                "account_not_found",
                "Account is unavailable.",
            )
        ensure_user_account_foundation(session, user, now=_utcnow())
        issued = device_pairing_service.issue_pairing_code(
            session,
            account_id=str(user.account_id or ""),
            issued_by_session_id=None,
            now=_utcnow(),
        )
        session.commit()
        return str(issued.code)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _device_pairing_code_text(code: str) -> str:
    return (
        "🔑 *Код для входа в POKROV*\n\n"
        f"`{code}`\n\n"
        "Откройте POKROV → «Уже пользуюсь» и введите этот код. "
        "Он одноразовый и действует 10 минут."
    )


def _device_pairing_code_rows() -> list[list[dict[str, str]]]:
    return [
        [_btn_spec(text="Обновить код", callback_data="device_pairing_code")],
        [_btn_spec(text="Скачать приложение", callback_data="instruction", emoji_key="download")],
        [_btn_spec(text="◀️ Назад", callback_data="instruction")],
    ]


async def _send_device_pairing_code_message(
    *,
    bot: Bot,
    chat_id: int,
    tg_id: int,
    entrypoint: str,
) -> None:
    try:
        code = _issue_bot_device_pairing_code(tg_id)
        sent = await bot.send_message(
            chat_id,
            _device_pairing_code_text(code),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=_keyboard_from_specs(_device_pairing_code_rows()),
        )
        last_bot_message[int(tg_id)] = sent.message_id
        track_event(
            tg_id=int(tg_id),
            event_name="device_pairing_code_issued",
            source="bot",
            meta={"entrypoint": str(entrypoint or "bot")[:32]},
        )
    except Exception as exc:
        logger.warning(
            "device pairing code issue failed tg_id=%s error=%s",
            tg_id,
            type(exc).__name__,
        )
        sent = await bot.send_message(
            chat_id,
            "Не удалось создать код входа. Попробуйте еще раз через минуту.",
        )
        last_bot_message[int(tg_id)] = sent.message_id


@router.callback_query(F.data == "device_pairing_code")
async def show_device_pairing_code(callback: CallbackQuery):
    try:
        code = _issue_bot_device_pairing_code(callback.from_user.id)
        await callback.message.edit_text(
            _device_pairing_code_text(code),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=_keyboard_from_specs(_device_pairing_code_rows()),
        )
        track_event(
            tg_id=int(callback.from_user.id),
            event_name="device_pairing_code_issued",
            source="bot",
            meta={"entrypoint": "device_picker"},
        )
        await callback.answer("Код действует 10 минут")
    except Exception as exc:
        logger.warning(
            "device pairing code issue failed tg_id=%s error=%s",
            callback.from_user.id,
            type(exc).__name__,
        )
        await callback.answer("Не удалось создать код. Попробуйте еще раз.", show_alert=True)


@router.callback_query(F.data == "verify_pokrov")
async def verify_pokrov(callback: CallbackQuery):
    rows = [
        [
            _btn_spec(text="Android", callback_data="instr_android", emoji_key="phone"),
            _btn_spec(text="Windows", callback_data="instr_win", emoji_key="device"),
        ],
        [_btn_spec(text="Тарифы", callback_data="charge", emoji_key="payment")],
        [_btn_spec(text="◀️ Назад", callback_data="back")],
    ]
    await _edit_text_with_specs(
        bot=callback.message.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=bot_text("bot.instruction.verify"),
        rows=rows,
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data == "settings")
async def show_settings(callback: CallbackQuery):
    await _edit_text_with_specs(
        bot=callback.message.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=(
            "*Меню POKROV обновилось.*\n\n"
            "Загрузка, вход и помощь теперь находятся на одном коротком экране. "
            "Подробный аккаунт открывается в кабинете."
        ),
        rows=main_keyboard_specs(int(callback.from_user.id)),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


_PLATFORM_SCREENS = {
    "ios": ("bot.instruction.platform_ios", IOS_APP_LINK, "Открыть страницу для iPhone"),
    "android": (
        "bot.instruction.platform_android",
        ANDROID_APP_LINK,
        "Скачать ARM64 · основной" if APP_ANDROID_APK_ARM64_URL else "Скачать POKROV",
    ),
    "win": ("bot.instruction.platform_windows", WINDOWS_APP_LINK, "Скачать POKROV"),
    "mac": ("bot.instruction.platform_macos", MAC_APP_LINK, "Открыть страницу для macOS"),
}


def _platform_download_rows(platform: str, url: str, button_text: str) -> list[list[dict]]:
    rows = [
        [
            _btn_spec(
                text=button_text,
                url=url,
                style=BTN_STYLE_PRIMARY,
                emoji_key="download",
            )
        ]
    ]
    if platform != "android":
        return rows

    seen_urls = {str(url or "").strip()}
    variants = (
        (
            "ARMv7 · старый телефон",
            f"{PUBLIC_API_BASE_URL.rstrip('/')}/api/public/downloads/android-armv7"
            if APP_ANDROID_APK_ARMEABI_V7A_URL
            else "",
        ),
        (
            "Universal · запасной",
            f"{PUBLIC_API_BASE_URL.rstrip('/')}/api/public/downloads/android-universal"
            if APP_ANDROID_APK_UNIVERSAL_URL
            else "",
        ),
    )
    for label, variant_url in variants:
        clean_url = str(variant_url or "").strip()
        if not clean_url or clean_url in seen_urls:
            continue
        seen_urls.add(clean_url)
        rows.append([_btn_spec(text=label, url=clean_url, emoji_key="download")])
    return rows


def _installed_app_action_spec(tg_id: int) -> dict[str, str]:
    del tg_id
    return _btn_spec(
        text="Код для входа в POKROV",
        callback_data="device_pairing_code",
        style=BTN_STYLE_SUCCESS,
        emoji_key="key",
    )


async def _render_platform_screen(callback: CallbackQuery, platform: str) -> None:
    """Per-platform install screen: download, funnel to access check, manual fallback."""
    copy_key, url, btn = _PLATFORM_SCREENS.get(platform, _PLATFORM_SCREENS["android"])
    rows = _platform_download_rows(platform, url, btn) + [
        [_installed_app_action_spec(callback.from_user.id)],
        [_btn_spec(text="Ручное подключение", callback_data="show_key", emoji_key="link")],
        [_btn_spec(text="◀️ Устройства", callback_data="instruction")],
    ]
    await _edit_text_with_specs(
        bot=callback.message.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=bot_text(copy_key),
        rows=rows,
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data.in_({"instr_ios", "instr_android", "instr_win", "instr_mac"}))
async def instruction_platform(callback: CallbackQuery):
    await _render_platform_screen(callback, (callback.data or "").replace("instr_", ""))

# ==========================================
#         SUB-MENUS
# ==========================================

@router.callback_query(F.data == "menu_bonuses")
async def menu_bonuses(callback: CallbackQuery):
    """Bonuses submenu: referral, wheel, streak, achievements"""
    tg_id = int(callback.from_user.id)
    user = get_user(tg_id)
    if not _is_paid_active_user(user):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"🎁 {CHANNEL_PREMIUM_DAYS} дней премиум за канал", callback_data="bonus_offer_main")],
            [InlineKeyboardButton(text=_main_connect_cta_text(tg_id), callback_data="charge")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")],
        ])
        await callback.message.edit_text(
            "🎁 *Бонусы*\n\n"
            "Можно взять бонус за канал или сразу перейти к выбору доступа.\n\n"
            "Выберите действие.",
            reply_markup=kb,
            parse_mode=ParseMode.MARKDOWN,
        )
        await callback.answer()
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎁 Пригласить друга", callback_data="referral"),
            InlineKeyboardButton(text="🏆 Ачивки", callback_data="achievements")
        ],
        [
            InlineKeyboardButton(text="🎰 Колесо Фортуны", callback_data="wheel"),
            InlineKeyboardButton(text="🔥 Streak", callback_data="streak")
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
    ])

    await callback.message.edit_text(
        "🎁 *Бонусы*\n\n"
        "Здесь собраны бонусы и полезные плюсы: друзья, streak, рулетка и достижения.\n\n"
        "Выберите нужный раздел.",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "menu_more")
async def menu_more(callback: CallbackQuery):
    """Compact code activation menu retained for existing purchases and promos."""
    tg_id = int(callback.from_user.id)
    pending_redeem_codes.discard(tg_id)
    pending_promo_codes.discard(tg_id)
    rows = [
        [
            InlineKeyboardButton(text="🎁 Код доступа или подарок", callback_data="gift_redeem_prompt"),
            InlineKeyboardButton(text="🎟️ Промокод", callback_data="promo_activate_prompt"),
        ],
        [InlineKeyboardButton(text="ℹ️ Как работают коды", callback_data="promo_help")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")],
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=rows)

    await callback.message.edit_text(
        "🎟️ *Активировать код*\n\n"
        "Выберите тип кода. Оплата, устройства и история остаются в приложении и кабинете.",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "promo_help")
async def promo_help(callback: CallbackQuery):
    """Show promo command help"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_more")]
    ])
    await callback.message.edit_text(
        "🎟️ *Активация промокода*\n\n"
        "Нажмите «Ввести промокод», затем отправьте код следующим сообщением.\n\n"
        "Пример: `NEWYEAR`",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()


@router.callback_query(F.data == "gift_redeem_prompt")
async def gift_redeem_prompt(callback: CallbackQuery):
    pending_redeem_codes.add(callback.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")],
    ])
    await callback.message.edit_text(
        "🎁 *Активация подарка*\n\n"
        "Отправьте код следующим сообщением.\n"
        "_Если у вас старый код `SWAZ-...`, он тоже пока принимается._",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data == "promo_activate_prompt")
async def promo_activate_prompt(callback: CallbackQuery):
    pending_promo_codes.add(callback.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")],
    ])
    await callback.message.edit_text(
        "🎟️ *Активация промокода*\n\n"
        "Отправьте код следующим сообщением, без `/promo`.\n"
        "Пример: `NEWYEAR`",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()

@router.callback_query(F.data == "review_start")
async def review_start(callback: CallbackQuery):
    """Start review flow from button"""
    tg_id = callback.from_user.id
    user = get_user(tg_id)

    if not user or not user.is_active:
        await callback.answer("❌ Сначала включите доступ, потом можно оставить отзыв для сайта.", show_alert=True)
        return

    if has_user_review(tg_id):
        await callback.answer("❌ Отзыв уже сохранён. Спасибо!", show_alert=True)
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1", callback_data="rate_1"),
            InlineKeyboardButton(text="2", callback_data="rate_2"),
            InlineKeyboardButton(text="3", callback_data="rate_3"),
            InlineKeyboardButton(text="4", callback_data="rate_4"),
            InlineKeyboardButton(text="5", callback_data="rate_5"),
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_more")]
    ])

    await callback.message.edit_text(
        "*Поделитесь впечатлением*\n\n"
        "Выберите оценку от 1 до 5. Потом можно добавить короткий текст для сайта.",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "referral")
async def show_referral(callback: CallbackQuery):
    tg_id = callback.from_user.id
    user = get_user(tg_id)
    if not _is_paid_active_user(user):
        await callback.answer("⚠️ Реферальные бонусы доступны только при активном платном доступе.", show_alert=True)
        return

    # Get or create unique referral code
    stats = get_referral_stats(tg_id)
    ref_code = stats.get('code') or get_or_create_referral_code(tg_id)

    if not ref_code:
        await callback.answer("⚠️ Сначала активируйте доступ", show_alert=True)
        return

    # Generate referral link with SWAZ code
    invite_link = f"https://t.me/{BOT_USERNAME}?start={ref_code}"
    ref_count = stats['count']
    bonus_earned = stats['bonus_earned']

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Поделиться реферальной ссылкой", url=f"https://t.me/share/url?url={invite_link}&text=🛡 POKROV — приглашение в защищённую связь")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
    ])

    await callback.message.edit_text(
        f"🎁 *Пригласите друга по своей ссылке*\n\n"
        "Друг получит *+5 дней* после своей первой успешной оплаты.\n"
        f"Вы получите *+{REFERRAL_BONUS_DAYS} дней* после его первой оплаты и проверки 72 часа.\n\n"
        f"👇 *Ваша ссылка для приглашения:*\n`{invite_link}`\n\n"
        f"Активировано по ссылке: {ref_count}\n"
        f"Бонусных дней начислено: {bonus_earned}",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "wheel")
async def show_wheel(callback: CallbackQuery):
    """Render the shared account-level wheel state without exposing weights."""
    tg_id = callback.from_user.id
    now = _utcnow()
    session = Session()
    try:
        user = session.query(User).filter_by(tg_id=int(tg_id)).first()
        if not user:
            await callback.answer("⚠️ Сначала активируй аккаунт.", show_alert=True)
            return
        if not str(user.account_id or "").strip():
            ensure_user_account_foundation(session, user, now=now)
            session.flush()
        state = get_wheel_state(
            session,
            account_id=str(user.account_id or ""),
            enabled=bool(BONUS_WHEEL_ENABLED),
            config_payload=_load_wheel_config_payload(session),
            now=now,
        )
    except RewardDomainError:
        session.rollback()
        await callback.answer("⚠️ Рулетка временно недоступна.", show_alert=True)
        return
    finally:
        session.close()

    if not BONUS_WHEEL_ENABLED:
        status_text = "⏸ *Рулетка временно недоступна.*"
        buttons = [[InlineKeyboardButton(text="◀️ Назад", callback_data="menu_bonuses")]]
    elif state.reason == "wheel_config_invalid":
        await callback.answer("⚠️ Рулетка временно недоступна.", show_alert=True)
        return
    elif not state.eligible:
        await callback.answer(
            "⚠️ Рулетка доступна только при активном платном доступе.",
            show_alert=True,
        )
        return
    elif state.can_spin:
        status_text = "✅ *Можно крутить!*"
        buttons = [
            [InlineKeyboardButton(text="🎰 КРУТИТЬ!", callback_data="wheel_spin")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_bonuses")],
        ]
    else:
        next_spin_at = state.next_spin_at or now
        seconds_left = max(0, int((next_spin_at - now).total_seconds()))
        days = seconds_left // 86400
        hours = (seconds_left % 86400) // 3600
        mins = (seconds_left % 3600) // 60
        if days > 0:
            time_str = f"{days}д {hours}ч"
        elif hours > 0:
            time_str = f"{hours}ч {mins}м"
        else:
            time_str = f"{mins} мин"
        status_text = f"⏳ Следующий спин через: *{time_str}*"
        buttons = [[InlineKeyboardButton(text="◀️ Назад", callback_data="menu_bonuses")]]

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    sectors = [int(days) for days in state.sectors]
    prizes_text = "\n".join(f"• +{days} дней" for days in sectors) or "Секторы скрыты до включения"

    await callback.message.edit_text(
        "🎰 *Колесо Фортуны!*\n\n"
        "Крути раз в 14 дней и получай бонусные дни или скидку.\n\n"
        f"🎁 *Секторы:*\n{prizes_text}\n\n"
        f"{status_text}",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()

@router.callback_query(F.data == "wheel_spin")
async def do_wheel_spin(callback: CallbackQuery):
    """Commit one shared reward-service mutation for the canonical account."""
    tg_id = callback.from_user.id
    if not BONUS_WHEEL_ENABLED:
        await callback.answer("⚠️ Рулетка временно недоступна.", show_alert=True)
        return

    await callback.message.edit_text(
        "🎰 *Крутим колесо...*\n\n"
        "🔄 ▓▓▓▓▓▓▓▓▓▓ 🔄",
        parse_mode=ParseMode.MARKDOWN,
    )
    await asyncio.sleep(1.5)

    now = _utcnow()
    session = Session()
    try:
        user = session.query(User).filter_by(tg_id=int(tg_id)).first()
        if not user:
            raise RewardForbidden("account_not_found")
        if not str(user.account_id or "").strip():
            ensure_user_account_foundation(session, user, now=now)
            session.flush()
        mutation = spin_wheel(
            session,
            account_id=str(user.account_id or ""),
            enabled=bool(BONUS_WHEEL_ENABLED),
            config_payload=_load_wheel_config_payload(session),
            now=now,
        )
        _ensure_reward_achievement(
            session,
            tg_id=int(tg_id),
            achievement_id="first_wheel",
            now=now,
        )
        if int(mutation.reward_days) >= 30:
            _ensure_reward_achievement(
                session,
                tg_id=int(tg_id),
                achievement_id="jackpot",
                now=now,
            )
        session.commit()
    except RewardDisabled:
        session.rollback()
        await callback.answer("⚠️ Рулетка временно недоступна.", show_alert=True)
        return
    except RewardForbidden:
        session.rollback()
        await callback.answer(
            "⚠️ Рулетка доступна только при активном платном доступе.",
            show_alert=True,
        )
        return
    except RewardConflict as exc:
        session.rollback()
        seconds_left = max(0, int((exc.next_allowed_at - now).total_seconds()))
        days = max(1, (seconds_left + 86399) // 86400)
        await callback.message.edit_text(
            f"⏳ Следующий спин будет доступен примерно через {days} дней.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_bonuses")],
            ]),
        )
        await callback.answer("Рулетка ещё на перезарядке.", show_alert=True)
        return
    except RewardDomainError:
        session.rollback()
        await callback.answer("⚠️ Рулетка временно недоступна.", show_alert=True)
        return
    except Exception as exc:
        session.rollback()
        logger.warning("wheel reward failed tg_id=%s err=%s", tg_id, exc)
        await callback.answer("⚠️ Не удалось прокрутить рулетку.", show_alert=True)
        return
    finally:
        session.close()

    prize = int(mutation.reward_days)
    # Keep the handler compatible with older ledger/test adapters while the
    # richer wheel outcome is rolled out across every entrypoint.
    discount_pct = int(getattr(mutation, "discount_pct", 0) or 0)
    if discount_pct > 0:
        emoji = "🎁"
        title = "Скидка на продление"
        achievement_id = ""
    elif prize >= 30:
        emoji = "🎉🎉🎉"
        title = "ДЖЕКПОТ!!!"
        achievement_id = "jackpot"
    elif prize >= 7:
        emoji = "✨"
        title = "Отлично!"
        achievement_id = ""
    else:
        emoji = "🎁"
        title = "Поздравляем!"
        achievement_id = ""

    next_spin_at = mutation.wheel_next_spin_at or now + timedelta(days=7)
    cooldown_seconds = max(0, int((next_spin_at - now).total_seconds()))
    cooldown_days = max(1, (cooldown_seconds + 86399) // 86400)
    track_event(
        tg_id=int(tg_id),
        event_name="wheel_spin",
        source="bot",
        meta={
            "prize_days": int(prize),
            "reward_kind": str(getattr(mutation, "reward_kind", "days") or "days"),
            "discount_pct": discount_pct,
            "achievement_id": achievement_id or None,
            "cooldown_days": int(cooldown_days),
            "grant_id": mutation.grant_id,
            "sync_state": str(mutation.sync_state),
        },
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ В бонусы", callback_data="menu_bonuses")],
    ])

    reward_copy = (
        f"Тебе выпала скидка *−{discount_pct}%* на одно следующее продление.\n\n"
        "Скидка применится автоматически, не складывается с другой скидкой."
        if discount_pct > 0
        else f"Тебе выпало: *+{prize} Дней*!\n\nПодписка продлена."
    )
    await callback.message.edit_text(
        f"{emoji} *{title}*\n\n"
        f"{reward_copy}\n"
        f"Приходи через {cooldown_days} дней за новым призом!",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer(
        f"🎁 −{discount_pct}% на продление!"
        if discount_pct > 0
        else f"🎉 +{prize} Дней!",
        show_alert=True,
    )

@router.callback_query(F.data == "achievements")
async def show_achievements(callback: CallbackQuery):
    """Show user's achievements"""
    tg_id = callback.from_user.id
    user = get_user(tg_id)
    if not _is_paid_active_user(user):
        await callback.answer("⚠️ Достижения доступны только при активном платном доступе.", show_alert=True)
        return

    # Check for new achievements
    await check_achievements(tg_id, callback.bot)

    # Get user's unlocked achievements
    unlocked = get_user_achievements(tg_id)

    # Build achievements grid (all rewards are days).
    lines = []
    total_days = 0
    for ach_id, ach in ACHIEVEMENTS.items():
        unlocked_now = ach_id in unlocked
        status = "✅" if unlocked_now else "🔒"

        bonus_days = int(ach.get("days", 0) or 0)
        if unlocked_now:
            total_days += bonus_days

        bonus = f" (+{bonus_days} дн.)" if bonus_days > 0 else ""
        lines.append(f"{status} {ach['icon']} *{ach['name']}*{bonus}\n   _{ach['desc']}_")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
    ])

    await callback.message.edit_text(
        f"🏆 *Твои достижения*\n\n"
        f"Открыто: *{len(unlocked)}/{len(ACHIEVEMENTS)}*\n"
        f"Бонусом начислено: *{total_days} дней*\n\n"
        + "\n\n".join(lines),
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "streak")
async def show_streak(callback: CallbackQuery):
    """Show user's streak info"""
    tg_id = callback.from_user.id
    user = get_user(tg_id)
    if not _is_paid_active_user(user):
        await callback.answer("⚠️ Streak доступен только при активном платном доступе.", show_alert=True)
        return

    info = get_streak_info(tg_id)

    months = info["months"]
    next_m = info["next_milestone"]
    bonus_days_next = info["bonus_days_next"]

    # Build progress bar
    if next_m:
        progress = min(months / next_m, 1.0)
        filled = int(progress * 10)
        bar = "▓" * filled + "░" * (10 - filled)
        progress_text = f"До *{next_m} мес* (+{bonus_days_next} дней): [{bar}]"
    else:
        bar = "▓" * 10
        progress_text = f"🏆 *Все вехи пройдены!* [{bar}]"

    # Milestone list
    milestones = "\n".join([
        f"{'✅' if months >= m else '⬜'} {m} мес = +{d} Дней"
        for m, d in sorted(STREAK_REWARDS.items())
    ])

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
    ])

    await callback.message.edit_text(
        f"🔥 *Твой Streak: {months} мес*\n\n"
        f"Каждый месяц активной подписки увеличивает streak.\n"
        f"За вехи получаешь бонусные дни подписки!\n\n"
        f"📊 {progress_text}\n\n"
        f"*Вехи:*\n{milestones}\n\n"
        f"⚠️ _Если подписка истечёт > 7 дней — streak сбросится!_",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()


@router.callback_query(F.data == "buy_family_slot")
async def buy_family_slot(callback: CallbackQuery, bot: Bot):
    if not _stars_checkout_creation_enabled():
        await callback.answer("Family-слоты в боте пока закрыты. Напишите в поддержку, если нужен ручной перенос.", show_alert=True)
        return
    tg_id = callback.from_user.id
    current = active_family_slots(tg_id)
    if current >= FAMILY_SLOT_MAX:
        await callback.answer(f"Лимит family-слотов: +{FAMILY_SLOT_MAX}", show_alert=True)
        return
    try:
        await callback.answer()
        await bot.send_invoice(
            chat_id=tg_id,
            title="Family slot +1",
            description=f"+1 устройство на {FAMILY_SLOT_DAYS} дней (макс +{FAMILY_SLOT_MAX})",
            payload=f"familyslot_{tg_id}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label="Family slot", amount=FAMILY_SLOT_STARS)],
        )
        track_event(tg_id=tg_id, event_name="clicked_pay", source="bot", meta={"plan_code": "family_slot"})
    except Exception:
        await callback.message.answer("❌ Не удалось выставить счёт на family-слот.")


# ==========================================
#         SMART SUPPORT
# ==========================================

FAQ_ANSWERS = {
    "connect": (
        "📱 *Как подключиться?*\n\n"
        f"1. Скачайте POKROV для [Android]({ANDROID_APP_LINK}) или [Windows]({WINDOWS_APP_LINK})\n"
        "2. Войдите через почту или Telegram\n"
        "3. Нажмите «Подключить»\n\n"
        f"iPhone / iPad: [инструкция и статус релиза]({IOS_APP_LINK}).\n"
        f"macOS: [инструкция и статус релиза]({MAC_APP_LINK}).\n\n"
        "Если приложение недоступно или профиль не подтянулся, откройте *Ручное подключение* в кабинете POKROV. Для начала используйте Hiddify: добавьте туда личную ссылку из кабинета. Для Happ используйте отдельную готовую кнопку или QR. Если запутались, напишите в поддержку."
    ),
    "notwork": (
        "⚠️ *Не работает?*\n\n"
        "Попробуйте по порядку:\n\n"
        "1. Обновите доступ в приложении\n\n"
        "2. Полностью перезапустите приложение\n\n"
        "3. Проверьте обычный интернет без прокси\n\n"
        "4. Если есть выбор, смените локацию\n\n"
        "5. Перезагрузите устройство\n\n"
        "Если не помогло, напишите в поддержку 👇"
    ),
    "renew": (
        "💳 *Как продлить доступ?*\n\n"
        f"1️⃣ Откройте бота @{BOT_USERNAME_MD}\n\n"
        "2️⃣ Нажмите *💳 Продлить или начать*\n\n"
        "3️⃣ Выберите нужный план\n\n"
        "4️⃣ Откройте оплату в ₽\n\n"
        "После успешной оплаты доступ обновится автоматически."
    ),
    "payment": (
        "🧾 *Оплатил, но доступ не обновился*\n\n"
        "Обычно доступ включается сам за пару минут после оплаты.\n\n"
        "Если прошло больше:\n"
        "1. Проверьте статус кнопкой «Проверить доступ» в меню\n"
        "2. Загляните в кабинет — там виден срок и последняя оплата\n"
        "3. Если через 15 минут ничего не изменилось, напишите в поддержку и приложите чек или скрин оплаты\n\n"
        "Деньги не теряются: по чеку мы находим платёж и включаем доступ вручную."
    ),
    "codes": (
        "🎫 *Промокоды и подарочные коды*\n\n"
        "• Промокод — команда /promo, затем отправьте код сообщением\n"
        "• Ключ доступа или подарочный код — команда /redeem\n\n"
        "Если код не сработал:\n"
        "1. Проверьте, нет ли опечатки — коды не зависят от регистра\n"
        "2. У кода мог закончиться срок или лимит активаций\n"
        "3. Некоторые коды действуют только для новых аккаунтов\n\n"
        "Не получилось — напишите в поддержку, разберёмся с конкретным кодом."
    ),
    "referral": (
        "🎁 *Реферальная программа*\n\n"
        "• Пригласите друга по своей ссылке\n"
        "• Друг получает *+5 дней* после своей первой успешной оплаты\n"
        f"• Вы получаете *+{REFERRAL_BONUS_DAYS} дней* после его первой оплаты и проверки 72 часа\n\n"
        "Откройте меню → *🎁 Пригласить друга*"
    ),
    "device": (
        "📲 *Смена устройства*\n\n"
        "Скачайте приложение на новое устройство и войдите в тот же аккаунт POKROV.\n\n"
        "Если профиль не подтянулся автоматически, откройте кабинет POKROV и раздел *Ручное подключение*. Для начала используйте Hiddify и добавьте туда личную ссылку из кабинета. Для Happ используйте отдельную готовую кнопку или QR.\n\n"
        f"Лимит устройств зависит от плана: до *{PAID_LIMIT_IP}* в платных режимах."
    ),
    "speed": (
        "🚀 *Медленно работает*\n\n"
        "Что помогает чаще всего:\n\n"
        "1. Смените локацию, если в приложении есть выбор\n"
        "2. Проверьте скорость обычного интернета без POKROV — если он медленный, дело в сети\n"
        "3. Перезапустите приложение и подключитесь заново\n"
        f"4. На бесплатном старте после {TRIAL_LIMIT_GB} ГБ скорость снижается — в платных режимах в обычном режиме снижения нет\n\n"
        "Если скорость упала резко и не восстанавливается, напишите в поддержку и укажите локацию."
    ),
    "login": (
        "🔑 *Вход в приложение и кабинет*\n\n"
        "Войти можно через почту или Telegram — главное, использовать *один и тот же способ* на всех устройствах, тогда доступ подтянется сам.\n\n"
        "Частые ситуации:\n"
        "• Код на почту не пришёл — проверьте «Спам» и подождите пару минут\n"
        "• Вошли, а доступа нет — вероятно, это другой аккаунт; выйдите и войдите тем способом, которым оплачивали\n"
        "• Кабинет просит вход заново — это нормально после долгого перерыва\n\n"
        "Запутались в аккаунтах — поддержка поможет найти ваш по номеру для поддержки из «Проверить доступ»."
    ),
    "manual": (
        "🔗 *Ручное подключение*\n\n"
        "Запасной способ, если приложение POKROV недоступно на вашем устройстве.\n\n"
        "1. Откройте кабинет POKROV → раздел «Ручное подключение» и скопируйте личную ссылку\n"
        "2. Установите совместимое приложение: Hiddify; для Happ используйте отдельную готовую кнопку или QR\n"
        "3. Добавьте ссылку в приложение — обычно через «Добавить профиль» или вставку из буфера\n"
        "4. Нажмите «Подключить» уже там\n\n"
        "Личная ссылка — как ключ от квартиры: не публикуйте её. Если ссылка попала не в те руки, сбросьте её в меню «⚙️ Ещё» → «🛡 Сбросить ссылку»."
    ),
}

# Order and labels for the FAQ menu screen.
FAQ_MENU_ITEMS: list[tuple[str, str]] = [
    ("connect", "📱 Как подключиться"),
    ("notwork", "⚠️ Не работает"),
    ("payment", "🧾 Оплата не отобразилась"),
    ("renew", "💳 Как продлить"),
    ("codes", "🎫 Промокоды и коды"),
    ("referral", "🎁 Пригласить друга"),
    ("device", "📲 Смена устройства"),
    ("speed", "🚀 Медленно работает"),
    ("login", "🔑 Вход и аккаунт"),
    ("manual", "🔗 Ручное подключение"),
]

# ==========================================
#         GIFT CARDS HANDLERS
# ==========================================

@router.callback_query(F.data == "gift_cards")
async def show_gift_cards(callback: CallbackQuery):
    """Show gift card purchase menu"""
    if not _stars_checkout_creation_enabled():
        await callback.message.edit_text(
            "🎁 *Подарки*\n\n"
            "Покупка подарков прямо в боте пока закрыта. Если у вас уже есть ключ или подарок, активируйте его здесь; если нужен новый подарок, напишите в поддержку.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🎁 Активировать подарок", callback_data="gift_redeem_prompt")],
                    [InlineKeyboardButton(text="💬 Поддержка", url=f"https://t.me/{SUPPORT_USERNAME}?start=ticket_new")],
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_more")],
                ]
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
        await callback.answer()
        return
    buttons = []
    for key, card in GIFT_CARD_TYPES.items():
        text = f"{card['name']} — {card['days']} дн. — {card['stars']} Stars"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"buy_giftcard_{key}")])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(
        "🎁 *Подарочные карты*\n\n"
        "Купите карту → получите код → отправьте другу!\n"
        "Друг активирует код в меню «Дополнительно» → «Активировать подарок»\n\n"
        "Выберите карту:",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data.startswith("buy_giftcard_"))
async def buy_gift_card(callback: CallbackQuery, bot: Bot):
    """Buy a gift card"""
    if not _stars_checkout_creation_enabled():
        await callback.answer("Покупка подарков в боте пока закрыта", show_alert=True)
        return
    card_type = callback.data.replace("buy_giftcard_", "")
    card_info = GIFT_CARD_TYPES.get(card_type)

    if not card_info:
        await callback.answer("❌ Неизвестный тип карты", show_alert=True)
        return

    tg_id = callback.from_user.id

    # Create payment
    await bot.send_invoice(
        chat_id=tg_id,
        title=f"Подарочная карта {card_info['name']}",
        description=f"{card_info['days']} дней",
        payload=f"giftcard_{card_type}_{tg_id}",
        currency="XTR",
        prices=[LabeledPrice(label="Gift Card", amount=card_info["stars"])],
        start_parameter=f"giftcard_{card_type}"
    )
    await callback.answer()

@router.message(Command("redeem"))
async def redeem_command(message: Message, bot: Bot):
    """Redeem a gift card code"""
    pending_redeem_codes.discard(message.from_user.id)
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        await message.answer(
            "📥 *Активация подарочной карты*\n\n"
            "Использование: `/redeem POKROV-XXXX-XXXX`\n\n"
            "_Старые коды `SWAZ-...` тоже работают._\n\n"
            "_Введите код карты, которую вам подарили_",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    code = args[1].strip().upper()
    tg_id = message.from_user.id

    # Check TOS first
    if not check_tos_accepted(tg_id):
        await message.answer(
            "⚠️ Сначала примите условия использования.\n"
            "Нажмите /start и примите оферту."
        )
        return

    success, result_msg = await redeem_gift_card(code, tg_id, bot)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Открыть кабинет", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="◀️ В меню", callback_data="back")]
    ]) if success else None

    await message.answer(result_msg, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

# ==========================================
#           SHARE (DISABLED)
# ==========================================

@router.message(Command("share"))
async def share_traffic(message: Message, bot: Bot):
    await message.answer(
        "ℹ️ Функция передачи трафика отключена.\n"
        "В сервисе нет лимитов по трафику: доступ считается по сроку (дням)."
    )

# ==========================================
#           REVIEWS
# ==========================================

def _mask_review_username(username: str | None) -> str:
    raw = (username or "").strip()
    if raw.startswith("@"):
        raw = raw[1:].strip()
    if not raw:
        return "Пользователь"
    return f"{raw[:4]}****"


def has_user_review(tg_id: int) -> bool:
    """Check if user already left a review"""
    session = Session()
    exists = session.query(Review).filter_by(tg_id=tg_id).first() is not None
    session.close()
    return exists

def create_review(tg_id: int, username: str, rating: int, text: str = None) -> bool:
    """Create a new review"""
    session = Session()
    # Check if exists
    existing = session.query(Review).filter_by(tg_id=tg_id).first()
    if existing:
        session.close()
        return False

    review = Review(
        tg_id=tg_id,
        username=username,
        rating=rating,
        text=text
    )
    session.add(review)
    session.commit()
    session.close()
    return True

def get_featured_reviews(limit: int = 5) -> list:
    """Get top featured reviews for display"""
    session = Session()
    reviews = session.query(Review).filter_by(is_featured=True).order_by(Review.created_at.desc()).limit(limit).all()
    result = [{
        "username": _mask_review_username(r.username),
        "rating": r.rating,
        "text": r.text,
        "date": r.created_at.strftime("%d.%m.%Y") if r.created_at else ""
    } for r in reviews]
    session.close()
    return result

# Store pending review ratings
pending_reviews = {}
# Stores pending support ticket replies: tg_id -> ticket_id
pending_ticket_replies: dict[int, int] = {}
pending_ticket_reply_media_groups: dict[tuple[int, str], int] = {}
# Pending one-shot inputs from buttons in "More" menu.
pending_redeem_codes: set[int] = set()
pending_promo_codes: set[int] = set()
pending_auto_promo_codes: dict[int, str] = {}
pending_auto_friend_gift_referrals: dict[int, str] = {}
checkout_context_by_user: dict[int, dict[str, str]] = {}


def _telegram_attachment_payload(message: Message) -> tuple[str | None, str | None, dict[str, Any]]:
    photo = list(getattr(message, "photo", None) or [])
    if photo:
        item = photo[-1]
        payload = {
            "source": "telegram",
            "kind": "photo",
            "name": "Скриншот из Telegram",
        }
        for key in ("file_unique_id", "width", "height", "file_size"):
            value = getattr(item, key, None)
            if value is not None:
                payload[key] = value
        return "photo", getattr(item, "file_id", None), payload

    document = getattr(message, "document", None)
    if document is not None:
        payload = {
            "source": "telegram",
            "kind": "file",
            "name": getattr(document, "file_name", None) or "Файл из Telegram",
            "content_type": getattr(document, "mime_type", None) or "application/octet-stream",
        }
        for key in ("file_unique_id", "file_size"):
            value = getattr(document, key, None)
            if value is not None:
                payload[key] = value
        return "file", getattr(document, "file_id", None), payload

    video = getattr(message, "video", None)
    if video is not None:
        payload = {
            "source": "telegram",
            "kind": "video",
            "name": getattr(video, "file_name", None) or "Видео из Telegram",
            "content_type": getattr(video, "mime_type", None) or "video/mp4",
        }
        for key in ("file_unique_id", "width", "height", "duration", "file_size"):
            value = getattr(video, key, None)
            if value is not None:
                payload[key] = value
        return "video", getattr(video, "file_id", None), payload

    return None, None, {}


def _ticket_reply_media_group_id(message: Message) -> str:
    return str(getattr(message, "media_group_id", "") or "").strip()


def _ticket_reply_id_for_message(tg_id: int, message: Message) -> int:
    ticket_id = int(pending_ticket_replies.get(tg_id, 0) or 0)
    media_group_id = _ticket_reply_media_group_id(message)
    if not ticket_id and media_group_id:
        ticket_id = int(pending_ticket_reply_media_groups.get((int(tg_id), media_group_id), 0) or 0)
    return ticket_id


def _finish_ticket_reply_input(tg_id: int, message: Message, ticket_id: int) -> None:
    media_group_id = _ticket_reply_media_group_id(message)
    if media_group_id and int(ticket_id or 0) > 0:
        pending_ticket_reply_media_groups[(int(tg_id), media_group_id)] = int(ticket_id)
    pending_ticket_replies.pop(int(tg_id), None)


def _ticket_delivery_text(prefix: str, body: str, *, limit: int = 950) -> str:
    text = f"{prefix}\n{body}".strip()
    if len(text) > limit:
        return text[: limit - 1].rstrip() + "…"
    return text


def _support_actor_account_id(session, tg_id: int) -> str | None:
    return resolve_support_account_id(session, user_tg_id=int(tg_id))


def _can_access_support_ticket(session, ticket: SupportTicket, tg_id: int) -> bool:
    return can_access_ticket(
        ticket,
        int(tg_id),
        ADMIN_ID,
        account_id=_support_actor_account_id(session, int(tg_id)),
    )


async def _capture_ticket_reply_message(
    message: Message,
    *,
    body: str,
    media_type: str | None = None,
    media_file_id: str | None = None,
    media_payload: dict[str, Any] | None = None,
) -> bool:
    tg_id = int(message.from_user.id)
    ticket_id = _ticket_reply_id_for_message(tg_id, message)
    if ticket_id <= 0:
        return False

    body = (body or "").strip()
    if not body:
        await message.answer("❌ Отправь текст или файл для обращения.")
        return True

    session = Session()
    try:
        ticket = get_ticket_by_id(session, ticket_id)
        if not ticket:
            await message.answer("❌ Обращение не найдено.")
            return True
        if not _can_access_support_ticket(session, ticket, tg_id):
            await message.answer("⛔ Нет доступа к обращению.")
            return True

        role = "admin" if tg_id == ADMIN_ID else "user"
        actor_account_id = _support_actor_account_id(session, tg_id)
        if role == "user":
            claim_legacy_ticket(ticket, actor_tg_id=tg_id, account_id=actor_account_id)
        add_ticket_message(
            session,
            ticket_id=ticket.id,
            sender_tg_id=tg_id,
            sender_role=role,
            body=body,
            media_type=media_type,
            media_file_id=str(media_file_id or "").strip() or None,
            media_payload=(
                json.dumps(media_payload, ensure_ascii=False, separators=(",", ":"))
                if media_payload
                else None
            ),
        )
        if tg_id == ADMIN_ID:
            set_ticket_status(
                session,
                ticket=ticket,
                status=STATUS_IN_PROGRESS,
                assigned_admin_tg_id=ADMIN_ID,
            )
        else:
            set_ticket_status(session, ticket=ticket, status=STATUS_OPEN)
        delivery_tg_id = resolve_ticket_notification_tg_id(session, ticket)
        session.commit()

        await message.answer(f"✅ Ответ добавлен в обращение #{ticket.id}.")

        if tg_id == ADMIN_ID:
            delivery = _ticket_delivery_text(f"💬 Новый ответ команды POKROV по обращению #{ticket.id}:", body)
            if delivery_tg_id is None:
                logger.warning(
                    "main bot ticket notification skipped ticket=%s reason=no_telegram_target",
                    ticket.id,
                )
            else:
                try:
                    if media_type and media_file_id:
                        await message.copy_to(delivery_tg_id, caption=delivery)
                    else:
                        await message.bot.send_message(delivery_tg_id, delivery)
                except Exception as exc:
                    logger.warning("main bot ticket reply to user failed ticket=%s err=%s", ticket.id, exc)
        else:
            delivery = _ticket_delivery_text(f"🆕 Новое сообщение в обращении #{ticket.id} от пользователя {ticket.user_tg_id}:", body)
            try:
                if media_type and media_file_id:
                    await message.copy_to(ADMIN_ID, caption=delivery)
                else:
                    await message.bot.send_message(ADMIN_ID, delivery)
            except Exception as exc:
                logger.warning("main bot ticket reply to admin failed ticket=%s err=%s", ticket.id, exc)

        _finish_ticket_reply_input(tg_id, message, ticket.id)
        return True
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

@router.message(Command("review"))
async def review_command(message: Message):
    """Leave a review"""
    tg_id = message.from_user.id

    # Check if can review (has active sub, used for 7+ days, no existing review)
    user = get_user(tg_id)
    if not user or not user.is_active:
        await message.answer("❌ Сначала включите доступ, потом можно оставить отзыв для сайта.")
        return

    if has_user_review(tg_id):
        await message.answer("❌ Отзыв уже сохранён. Спасибо!")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1", callback_data="rate_1"),
            InlineKeyboardButton(text="2", callback_data="rate_2"),
            InlineKeyboardButton(text="3", callback_data="rate_3"),
            InlineKeyboardButton(text="4", callback_data="rate_4"),
            InlineKeyboardButton(text="5", callback_data="rate_5"),
        ],
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="back")]
    ])

    await message.answer(
        "*Поделитесь впечатлением*\n\n"
        "Выберите оценку от 1 до 5. Потом можно добавить короткий текст для сайта.",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )

@router.callback_query(F.data.startswith("rate_"))
async def rate_review(callback: CallbackQuery):
    """Handle rating selection"""
    tg_id = callback.from_user.id
    rating = int(callback.data.replace("rate_", ""))

    # Save rating, ask for text
    pending_reviews[tg_id] = rating

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="review_skip_text")],
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="back")]
    ])

    await callback.message.edit_text(
        f"Твоя оценка: {rating}/5\n\n"
        "Следующий шаг: напишите короткий отзыв (до 200 символов).\n\n"
        "_Или нажмите «Пропустить», чтобы оставить только оценку._",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "review_skip_text")
async def skip_review_text(callback: CallbackQuery):
    """Skip text and submit review with just rating"""
    tg_id = callback.from_user.id
    rating = pending_reviews.pop(tg_id, 5)
    username = callback.from_user.username

    success = create_review(tg_id, username, rating)

    if success:
        await callback.message.edit_text(
            f"✅ *Спасибо за отзыв!*\n\n"
            f"Оценка: {rating}/5\n"
            "Если отзыв подойдёт для сайта, мы покажем его после модерации.",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await callback.message.edit_text("❌ Отзыв уже сохранён.")

    await callback.answer()

@router.message()
async def admin_broadcast_capture_any(message: Message):
    """
    Capture any message from admin as broadcast draft (text/media/formatting).
    Uses Telegram copy_message/copy_to so admin doesn't have to write templates.
    """
    if message.from_user.id != ADMIN_ID:
        raise SkipHandler()
    info = admin_pending_actions.get(ADMIN_ID)
    if not info:
        raise SkipHandler()
    action = info.get("action")
    if action == "broadcast_capture":
        admin_pending_actions.pop(ADMIN_ID, None)
        draft = {
            "from_chat_id": message.chat.id,
            "message_id": message.message_id,
            "segment": "active",
            "button": None,
        }
        admin_broadcast_drafts[ADMIN_ID] = draft

        ctrl = await message.answer(
            _render_broadcast_draft(draft),
            reply_markup=_broadcast_controls(draft),
            parse_mode=ParseMode.MARKDOWN,
        )
        draft["control_message_id"] = ctrl.message_id
        audit_admin(ADMIN_ID, "admin_broadcast_v2_capture", meta=f"message_id={message.message_id}")
        return

    if action == "admin_dm_capture":
        target_tg_id = int(info.get("target_tg_id") or 0)
        admin_pending_actions.pop(ADMIN_ID, None)
        if target_tg_id <= 0:
            await message.answer("❌ Не найден получатель.")
            return
        try:
            await message.copy_to(chat_id=target_tg_id)
            await message.answer(f"✅ Сообщение отправлено пользователю `{target_tg_id}`.", parse_mode=ParseMode.MARKDOWN)
            audit_admin(ADMIN_ID, "admin_dm_send", target_tg_id=target_tg_id, meta=f"source_msg={message.message_id}")
        except Exception:
            await message.answer("❌ Не удалось отправить. Возможно, пользователь заблокировал бота.")
        return

    raise SkipHandler()


@router.message(F.photo | F.document | F.video)
async def capture_ticket_attachment(message: Message):
    media_type, media_file_id, media_payload = _telegram_attachment_payload(message)
    if not media_type or not media_file_id:
        raise SkipHandler()

    body = (getattr(message, "caption", None) or "").strip()
    if not body:
        body = str(media_payload.get("name") or "Вложение из Telegram").strip()

    handled = await _capture_ticket_reply_message(
        message,
        body=body,
        media_type=media_type,
        media_file_id=media_file_id,
        media_payload=media_payload,
    )
    if not handled:
        raise SkipHandler()


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text_input(message: Message):
    """Handle text inputs for reviews and admin actions"""
    tg_id = message.from_user.id

    # Support ticket reply capture (user/admin).
    if tg_id in pending_ticket_replies:
        _set_support_context(tg_id, enabled=True)
        body = (message.text or "").strip()
        await _capture_ticket_reply_message(message, body=body)
        return

    if tg_id in pending_redeem_codes:
        pending_redeem_codes.discard(tg_id)
        code = (message.text or "").strip().upper()
        if not code:
            await message.answer("❌ Код пустой. Нажмите «🎁 Активировать подарок» и попробуйте снова.")
            return
        if not check_tos_accepted(tg_id):
            await message.answer("⚠️ Сначала примите условия. Нажмите /start и подтвердите оферту.")
            return
        success, result_msg = await redeem_gift_card(code, tg_id, message.bot)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌐 Открыть кабинет", web_app=WebAppInfo(url=WEBAPP_URL))],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="back")],
        ]) if success else InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔁 Ввести код снова", callback_data="gift_redeem_prompt")],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="back")],
        ])
        await message.answer(result_msg, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        return

    if tg_id in pending_promo_codes:
        pending_promo_codes.discard(tg_id)
        code = (message.text or "").strip().upper()
        if not code:
            await message.answer("❌ Код пустой. Нажмите «🎟️ Ввести промокод» и попробуйте снова.")
            return
        ok, result = activate_promo_code_for_user(tg_id, code)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔁 Ввести другой код", callback_data="promo_activate_prompt")],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="back")],
        ])
        await message.answer(result, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        return

    # Check for admin pending actions first
    if tg_id == ADMIN_ID and tg_id in admin_pending_actions:
        action_info = admin_pending_actions.pop(tg_id)
        action = action_info["action"]

        # Handle search_user action
        if action == "search_user":
            query = message.text.strip()
            session = Session()

            if query.startswith("@"):
                username = query.lstrip("@")
                user = session.query(User).filter(User.username.ilike(username)).first()
            else:
                try:
                    uid = int(query)
                    user = session.query(User).filter_by(tg_id=uid).first()
                except ValueError:
                    user = session.query(User).filter(User.username.ilike(query)).first()

            if not user:
                session.close()
                await message.answer(f"❌ Пользователь `{query}` не найден", parse_mode=ParseMode.MARKDOWN)
                return

            ach_count = session.query(Achievement).filter_by(tg_id=user.tg_id).count()
            session.close()

            status = "✅ Активен" if user.is_active else "❌ Неактивен"
            expiry = user.expiry_at.strftime("%d.%m.%Y") if user.expiry_at else "—"

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="👤 Открыть", callback_data=f"adm_user_{user.tg_id}"),
                    InlineKeyboardButton(text="🚫 Бан" if user.is_active else "✅ Разбан", callback_data=f"admin_ban_{user.tg_id}"),
                ],
                [InlineKeyboardButton(text="◀️ Админка", callback_data="admin")]
            ])

            safe_username = (user.username or "—").replace("_", "\\_")
            await message.answer(
                f"👤 `{user.tg_id}` @{safe_username}\n"
                f"{status} | До: {expiry}\n"
                f"Stars: {user.stars_paid or 0}\n"
                f"🔥 Streak: {user.streak_months or 0} | 🏆 {ach_count}",
                reply_markup=kb,
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Handle custom_broadcast action with optional URL button
        if action == "custom_broadcast":
            raw_text = message.text.strip()

            # Parse for URL button: text---ButtonText|URL
            msg_text = raw_text
            url_button = None

            if "---" in raw_text:
                parts = raw_text.split("---", 1)
                msg_text = parts[0].strip()
                button_part = parts[1].strip()
                if "|" in button_part:
                    btn_text, btn_url = button_part.split("|", 1)
                    url_button = (btn_text.strip(), btn_url.strip())

            session = Session()
            users = session.query(User).filter_by(is_active=True).all()
            session.close()

            sent = 0
            for user in users:
                if user.tg_id in PROTECTED_USERS or user.tg_id == ADMIN_ID:
                    continue
                try:
                    if url_button:
                        kb = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text=url_button[0], url=url_button[1])]
                        ])
                        await message.bot.send_message(user.tg_id, msg_text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
                    else:
                        await message.bot.send_message(user.tg_id, msg_text, parse_mode=ParseMode.MARKDOWN)
                    sent += 1
                except:
                    pass

            btn_info = f" с кнопкой" if url_button else ""
            await message.answer(f"✅ Сообщение{btn_info} отправлено {sent} юзерам")
            return

        if action == "admin_promo_create_form":
            raw = (message.text or "").strip()
            parts = [p.strip() for p in raw.split("|")]
            if len(parts) < 4:
                await message.answer(
                    "Формат: `CODE|days|14|100` или `CODE|discount|20|50|2026-03-01T00:00:00`",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return
            code = re.sub(r"[^A-Z0-9_]+", "", parts[0].upper())[:20]
            promo_type = parts[1].lower()
            if promo_type not in {"days", "discount"}:
                await message.answer("Тип должен быть `days` или `discount`.", parse_mode=ParseMode.MARKDOWN)
                return
            try:
                value = int(parts[2])
                uses = int(parts[3])
            except Exception:
                await message.answer("value и uses должны быть числами.", parse_mode=ParseMode.MARKDOWN)
                return
            expires_at = None
            if len(parts) >= 5 and parts[4]:
                try:
                    expires_at = datetime.fromisoformat(parts[4])
                except Exception:
                    await message.answer("Неверный expires_at. Используйте ISO формат.", parse_mode=ParseMode.MARKDOWN)
                    return

            s = Session()
            try:
                exists = s.query(PromoCode.id).filter(func.upper(PromoCode.code) == code).first()
                if exists:
                    await message.answer("Промокод уже существует.")
                    return
                row = PromoCode(code=code, promo_type=promo_type, value=value, uses_left=uses, expires_at=expires_at)
                s.add(row)
                s.commit()
            finally:
                s.close()
            await message.answer(f"✅ Промокод `{code}` создан.", parse_mode=ParseMode.MARKDOWN)
            return

        if action == "admin_live_create":
            raw = (message.text or "").strip()
            parts = [p.strip() for p in raw.split("|")]
            if len(parts) < 3:
                await message.answer(
                    "Формат: `Заголовок|Кратко|@channel|123` или `Заголовок|Кратко|https://...`",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return
            title = parts[0][:160]
            summary = parts[1][:600]
            channel_username = None
            post_id = None
            link = ""
            if len(parts) >= 4 and parts[2].startswith("@"):
                channel_username = parts[2].lstrip("@")[:64]
                try:
                    post_id = int(parts[3])
                except Exception:
                    await message.answer("post_id должен быть числом.", parse_mode=ParseMode.MARKDOWN)
                    return
                link = f"https://t.me/{channel_username}/{post_id}"
            else:
                link = parts[2][:600]
            if not link:
                await message.answer("Ссылка не заполнена.")
                return

            s = Session()
            try:
                now = _utcnow()
                row = LiveUpdate(
                    title=title,
                    summary=summary,
                    link=link,
                    channel_username=channel_username,
                    post_id=post_id,
                    is_active=True,
                    sort_order=100,
                    created_at=now,
                    updated_at=now,
                )
                s.add(row)
                s.commit()
            finally:
                s.close()
            await message.answer("✅ Обновление сохранено.")
            return

        if action == "admin_start_create":
            raw = (message.text or "").strip()
            parts = [p.strip() for p in raw.split("|")]
            if len(parts) < 3:
                await message.answer(
                    "Формат: `code|Описание|target_action`",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return
            code = re.sub(r"[^a-z0-9_-]+", "", parts[0].lower())[:64]
            if len(code) < 2:
                await message.answer("Некорректный code.")
                return
            description = parts[1][:240]
            target_action = parts[2][:64]

            s = Session()
            try:
                exists = s.query(StartLink.id).filter(func.lower(StartLink.code) == code).first()
                if exists:
                    await message.answer("Такой code уже существует.")
                    return
                now = _utcnow()
                row = StartLink(
                    code=code,
                    description=description or None,
                    target_action=target_action or None,
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                )
                s.add(row)
                s.commit()
            finally:
                s.close()
            await message.answer(
                f"✅ Ссылка создана:\n`https://t.me/{BOT_USERNAME}?start={code}`",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        if action == "admin_start_edit":
            link_id = int(action_info.get("link_id") or 0)
            if link_id <= 0:
                await message.answer("Некорректный link_id.")
                return
            raw = (message.text or "").strip()
            parts = [p.strip() for p in raw.split("|")]
            if len(parts) < 3:
                await message.answer(
                    "Формат: `code|Описание|target_action`",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return

            code = re.sub(r"[^a-z0-9_-]+", "", parts[0].lower())[:64]
            if len(code) < 2:
                await message.answer("Некорректный code.")
                return
            description = parts[1][:240]
            target_action = parts[2][:64]

            s = Session()
            try:
                row = s.query(StartLink).filter(StartLink.id == link_id).first()
                if not row:
                    await message.answer("Ссылка не найдена.")
                    return
                exists = (
                    s.query(StartLink.id)
                    .filter(func.lower(StartLink.code) == code)
                    .filter(StartLink.id != link_id)
                    .first()
                )
                if exists:
                    await message.answer("Такой code уже занят.")
                    return
                row.code = code
                row.description = description or None
                row.target_action = target_action or None
                row.updated_at = _utcnow()
                s.commit()
            finally:
                s.close()

            await message.answer(
                f"✅ Ссылка обновлена:\n`https://t.me/{BOT_USERNAME}?start={code}`",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        if action == "broadcast_set_button":
            draft = admin_broadcast_drafts.get(ADMIN_ID)
            if not draft:
                await message.answer("Черновик не найден. Сначала создай рассылку заново.")
                return

            raw = (message.text or "").strip()
            if raw.lower() in {"нет", "no", "none", "-"}:
                draft["button"] = None
            else:
                if "|" not in raw:
                    await message.answer("Формат: `Текст кнопки|https://example.com` или `нет`", parse_mode=ParseMode.MARKDOWN)
                    return
                btn_text, btn_url = [x.strip() for x in raw.split("|", 1)]
                if not btn_text or not btn_url.startswith(("http://", "https://")):
                    await message.answer("Проверь текст кнопки и URL (должен начинаться с http/https).")
                    return
                draft["button"] = {"text": btn_text[:64], "url": btn_url}

            # Update controls message if we have it.
            ctrl_id = draft.get("control_message_id")
            if ctrl_id:
                try:
                    await message.bot.edit_message_text(
                        chat_id=ADMIN_ID,
                        message_id=ctrl_id,
                        text=_render_broadcast_draft(draft),
                        reply_markup=_broadcast_controls(draft),
                        parse_mode=ParseMode.MARKDOWN,
                    )
                except Exception:
                    pass
            await message.answer("✅ Обновил кнопку. Можно отправлять.")
            return

        if action == "wheel_cd":
            await message.answer("Конфигурация PAID_FORTNIGHTLY_DISCOUNTS_V3 фиксирована: кулдаун 14 дней.")
            return

        if action == "wheel_weights":
            await message.answer("Ручные веса отключены: действует фиксированный PAID_FORTNIGHTLY_DISCOUNTS_V3.")
            return

        if action == "manual_create":
            raw = (message.text or "").strip()
            if "|" not in raw:
                await message.answer("Формат: `DisplayName|days`", parse_mode=ParseMode.MARKDOWN)
                return
            name_raw, days_raw = [p.strip() for p in raw.split("|", 1)]
            try:
                days = int(days_raw)
            except Exception:
                await message.answer("Количество дней должно быть числом.", parse_mode=ParseMode.MARKDOWN)
                return
            if days < 1 or days > 3650:
                await message.answer("Диапазон дней: 1..3650", parse_mode=ParseMode.MARKDOWN)
                return

            manual_user = create_manual_user_record(
                display_name=name_raw or "Manual Client",
                days=days,
                created_by_admin=ADMIN_ID,
            )
            sub_id = manual_user.sub_token or str(manual_user.tg_id)
            try:
                res = await panel.ensure_user_on_all_nodes(
                    tg_id=manual_user.tg_id,
                    client_uuid=manual_user.uuid,
                    email=manual_user.email,
                    sub_id=sub_id,
                    enable=True,
                    only_node_codes=None,
                )
                ok = sum(1 for v in res.values() if v)
                fail = sum(1 for v in res.values() if not v)
            except Exception:
                ok = 0
                fail = 1

            link = build_subscription_link(manual_user.tg_id)
            qr = qrcode.QRCode(box_size=7, border=3)
            qr.add_data(link)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            bio = BytesIO()
            img.save(bio, "PNG")
            bio.seek(0)
            photo = BufferedInputFile(bio.read(), filename=f"manual-{abs(manual_user.tg_id)}.png")

            await message.answer_photo(
                photo=photo,
                caption=(
                    "✅ *Manual user создан*\n\n"
                    f"ID: `{manual_user.tg_id}`\n"
                    f"Name: `{(manual_user.display_name or manual_user.email)}`\n"
                    f"Sub: `{manual_user.sub_type}`\n"
                    f"Nodes sync: OK `{ok}`, fail `{fail}`\n\n"
                    f"Link:\n`{link}`"
                ),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="👤 Открыть карточку", callback_data=f"adm_user_{manual_user.tg_id}")],
                    [InlineKeyboardButton(text="🧩 Manual меню", callback_data="admin_manual_menu")],
                ]),
            )
            audit_admin(ADMIN_ID, "admin_manual_create", target_tg_id=manual_user.tg_id, meta=f"days={days}; ok={ok}; fail={fail}")
            return

        target_id = action_info.get("target")

        try:
            value = int(message.text.strip())
        except ValueError:
            await message.answer("❌ Введи число")
            return

        if action == "addgb":
            await message.answer(
                "ℹ️ Лимиты по трафику не используются.\n"
                "Используй продление по дням или смену тарифа.",
                parse_mode=ParseMode.MARKDOWN,
            )

        elif action == "extend":
            extend_user(target_id, value, 0)
            await message.answer(f"✅ Подписка юзера `{target_id}` продлена на {value} дней", parse_mode=ParseMode.MARKDOWN)

        elif action == "mass_addgb":
            await message.answer(
                "ℹ️ Массовое управление трафиком отключено (используются тарифные политики).\n"
                "Используй массовое продление по дням.",
                parse_mode=ParseMode.MARKDOWN,
            )

        elif action == "mass_extend":
            session = Session()
            now = _utcnow()
            try:
                count = (
                    session.query(User)
                    .filter(User.is_active == True)
                    .filter(User.expiry_at.isnot(None))
                    .filter(User.expiry_at > now)
                    .filter(User.tg_id != ADMIN_ID)
                    .count()
                )
            finally:
                session.close()

            await message.answer(
                f"⚠️ *Подтверждение действия*\n\n"
                f"Добавить *{value}* дней активному сегменту.\n"
                f"Будет затронуто: *{count}* пользователей.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=_bulk_confirm_kb(f"mass_extend_run_{value}"),
            )

        return

    # Handle review text
    if tg_id in pending_reviews:
        rating = pending_reviews.pop(tg_id)
        text = message.text[:200]
        username = message.from_user.username

        success = create_review(tg_id, username, rating, text)

        if success:
            await message.answer(
                f"✅ *Спасибо за отзыв!*\n\n"
                f"Оценка: {rating}/5\n"
                f"_{text}_\n\n"
                "Если отзыв подойдёт для сайта, мы покажем его после модерации.",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await message.answer("❌ Отзыв уже сохранён.")


@router.callback_query(F.data == "network_status")
async def network_status(callback: CallbackQuery):
    nodes = _bot_enabled_nodes()
    if not nodes:
        await callback.message.edit_text(
            "📡 *Состояние узлов сети*\n\n"
            "Нет данных по узлам. Проверьте конфигурацию control-plane.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="back")]]),
            parse_mode=ParseMode.MARKDOWN,
        )
        await callback.answer()
        return

    ping_values = await asyncio.gather(*[_node_ping_ms(n) for n in nodes])

    lines: list[str] = ["📡 *Состояние узлов сети*\n"]
    loads: list[int] = []
    for n, ping in zip(nodes, ping_values):
        code = _node_code_base(getattr(n, "code", ""))
        label = _node_label_ru_bot(getattr(n, "code", ""), getattr(n, "name", ""))
        healthy = bool(getattr(n, "is_healthy", True))
        ping_text = f"{ping}ms" if isinstance(ping, int) else "n/a"
        load = int(getattr(n, "active_clients", 0) or 0)
        loads.append(max(load, 0))
        dns_sni = "OK" if healthy else "WARN"
        node_kind = "Control" if code in {"brain", "de"} else "Node"
        lines.append(f"{label}: {'🟢' if healthy else '🔴'} Online ({node_kind}, Ping: {ping_text}, DNS/SNI: {dns_sni})")

    avg_load = int(sum(loads) / max(1, len(loads))) if loads else 0
    lines.append(f"\n⚡️ Нагрузка системы: {avg_load}%")
    lines.append("\nДля детальной диагностики откройте WebApp → Nodes.")

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Проверить доступность", callback_data="network_status_scan")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")],
        ]),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data == "network_status_scan")
async def network_status_scan(callback: CallbackQuery):
    await callback.message.edit_text("🔄 *Сканирование узлов...*", parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(0.6)
    await callback.message.edit_text("🔄 *Проверка DNS / SNI...*", parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(0.6)
    await network_status(callback)

def _support_hub_rows() -> list[list[dict[str, str]]]:
    support_new_url = f"https://t.me/{SUPPORT_USERNAME}?start=ticket_new"
    support_my_url = f"https://t.me/{SUPPORT_USERNAME}?start=ticket_my"
    return [
        [
            _btn_spec(
                text="Создать обращение",
                url=support_new_url,
                style=BTN_STYLE_SUCCESS,
                emoji_key="message",
            )
        ],
        [_btn_spec(text="Мои обращения", url=support_my_url, emoji_key="cabinet")],
        [_btn_spec(text="Частые вопросы", callback_data="faqmenu", emoji_key="faq")],
        [_btn_spec(text="Диагностика", callback_data="support_diagnose", emoji_key="target")],
        [_btn_spec(text="◀️ Назад", callback_data="back")],
    ]


def _support_hub_keyboard() -> InlineKeyboardMarkup:
    return _keyboard_from_specs(_support_hub_rows())


@router.callback_query(F.data == "support")
async def show_support(callback: CallbackQuery):
    """Show support menu"""
    _set_support_context(callback.from_user.id, enabled=True)
    await _edit_rich_copy(
        callback=callback,
        copy=support_hub_copy(),
        rows=_support_hub_rows(),
    )
    await callback.answer()


@router.message(Command("cabinet"))
async def cabinet_command(message: Message):
    _set_support_context(message.from_user.id, enabled=False)
    _track_bot_entry(tg_id=int(message.from_user.id), entrypoint="cabinet", meta={"command": "cabinet"})
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌐 Открыть кабинет", web_app=WebAppInfo(url=PUBLIC_BOT_WEBAPP_MENU_URL))],
            [InlineKeyboardButton(text="📲 Как начать", callback_data="instruction")],
            [InlineKeyboardButton(text="💬 Поддержка", url=f"https://t.me/{SUPPORT_USERNAME}?start=ticket_new")],
        ]
    )
    await message.answer(
        bot_text("bot.cabinet.intro"),
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
    )


@router.message(Command("support"))
async def support_command(message: Message):
    _set_support_context(message.from_user.id, enabled=True)
    _track_bot_entry(tg_id=int(message.from_user.id), entrypoint="support", meta={"command": "support"})
    await _send_rich_copy(
        message=message,
        bot=message.bot,
        chat_id=int(message.from_user.id),
        copy=support_hub_copy(),
        rows=_support_hub_rows(),
    )


@router.message(Command("help"))
async def help_command(message: Message):
    _set_support_context(message.from_user.id, enabled=True)
    _track_bot_entry(tg_id=int(message.from_user.id), entrypoint="help", meta={"command": "help"})
    await _send_rich_copy(
        message=message,
        bot=getattr(message, "bot", message),
        chat_id=int(getattr(getattr(message, "chat", None), "id", message.from_user.id)),
        copy=help_copy(),
        rows=_support_hub_rows(),
    )


def _faq_menu_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=label, callback_data=f"faq_{key}")]
        for key, label in FAQ_MENU_ITEMS
    ]
    rows.append([InlineKeyboardButton(text="💬 Написать в службу заботы", url=f"https://t.me/{SUPPORT_USERNAME}?start=ticket_new")])
    rows.append([InlineKeyboardButton(text="◀️ Назад в поддержку", callback_data="support")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data == "faqmenu")
async def show_faq_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        bot_text("bot.faq.menu"),
        reply_markup=_faq_menu_keyboard(),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("faq_"))
async def show_faq_answer(callback: CallbackQuery):
    """Show FAQ answer"""
    faq_key = callback.data.replace("faq_", "")
    answer = FAQ_ANSWERS.get(faq_key, "Ответ не найден")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад к вопросам", callback_data="faqmenu")],
        [InlineKeyboardButton(text="💬 Написать в службу заботы", url=f"https://t.me/{SUPPORT_USERNAME}?start=ticket_new")]
    ])

    await callback.message.edit_text(
        answer,
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )
    await callback.answer()

@router.callback_query(F.data == "support_diagnose")
async def support_diagnose(callback: CallbackQuery):
    """Run diagnostics and show user status"""
    _set_support_context(callback.from_user.id, enabled=True)
    tg_id = callback.from_user.id
    user = get_user(tg_id)

    if not user:
        status = "❌ Доступ не найден"
        details = "Запустите доступ через *💳 Продлить или начать*"
    else:
        # Status
        if user.is_active and user.expiry_at and user.expiry_at > _utcnow():
            days_left = (user.expiry_at - _utcnow()).days
            status = f"✅ Активна (ещё {days_left} дн.)"
        else:
            status = "❌ Истекла"

        # Details
        expiry = user.expiry_at.strftime("%d.%m.%Y") if user.expiry_at else "—"
        tariff = user.sub_type or "—"

        details = (
            f"📦 Тариф: *{tariff}*\n"
            f"📅 До: *{expiry}*\n"
            f"📡 Режим: *{_plan_mode_label(tariff, user=user)}*"
        )

    # Server check
    server_status = "✅ Онлайн"  # Simplified - we're running so server is up

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Моя ссылка", callback_data="show_key")],
        [InlineKeyboardButton(text="◀️ Назад к поддержке", callback_data="support")],
        [InlineKeyboardButton(text="💬 Написать в службу заботы", url=f"https://t.me/{SUPPORT_USERNAME}?start=ticket_new")]
    ])

    await callback.message.edit_text(
        f"🔧 *Диагностика*\n\n"
        f"*Ваш доступ:* {status}\n\n"
        f"{details}\n\n"
        f"*Сервер:* {server_status}",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()


def _ticket_status_title(status: str) -> str:
    if status == STATUS_IN_PROGRESS:
        return "В работе"
    if status == STATUS_CLOSED:
        return "Закрыто"
    return "Открыто"


def _ticket_message_preview(text: str, limit: int = 220) -> str:
    one_line = " ".join((text or "").split())
    if not one_line:
        return "(без текста)"
    if len(one_line) > limit:
        return one_line[: limit - 1] + "…"
    return one_line


def _ticket_view_keyboard(ticket_id: int, status: str, *, is_admin: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if status != STATUS_CLOSED:
        rows.append([InlineKeyboardButton(text="✍️ Ответить", callback_data=f"ticket_reply_{ticket_id}")])
        rows.append([InlineKeyboardButton(text="✅ Закрыть", callback_data=f"ticket_close_{ticket_id}")])
    else:
        rows.append([InlineKeyboardButton(text="♻️ Переоткрыть", callback_data=f"ticket_reopen_{ticket_id}")])

    if is_admin:
        rows.append([InlineKeyboardButton(text="🧑‍💼 Взять в работу", callback_data=f"ticket_claim_{ticket_id}")])
        rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_tickets")])
    else:
        rows.append([InlineKeyboardButton(text="📂 Мои обращения", callback_data="ticket_my")])
        rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="support")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _render_ticket(callback: CallbackQuery, ticket_id: int) -> None:
    tg_id = callback.from_user.id
    is_admin = tg_id == ADMIN_ID
    session = Session()
    try:
        ticket = get_ticket_by_id(session, ticket_id)
        if not ticket:
            await callback.answer("Обращение не найдено", show_alert=True)
            return
        if not _can_access_support_ticket(session, ticket, tg_id):
            await callback.answer("Нет доступа к этому обращению", show_alert=True)
            return

        msgs = list_ticket_messages(session, ticket_id=ticket.id, limit=20)
        status = _ticket_status_title(ticket.status)
        created = ticket.created_at.strftime("%d.%m %H:%M") if ticket.created_at else "-"
        updated = ticket.updated_at.strftime("%d.%m %H:%M") if ticket.updated_at else "-"
        assigned = str(ticket.assigned_admin_tg_id) if ticket.assigned_admin_tg_id else "-"
        lines = []
        for msg in msgs:
            ts = msg.created_at.strftime("%d.%m %H:%M") if msg.created_at else "-"
            role = "Оператор" if msg.sender_role == "admin" else "Пользователь"
            lines.append(f"[{ts}] {role}: {_ticket_message_preview(msg.body)}")
        history = "\n".join(lines) if lines else "Сообщений пока нет."

        text = (
            f"🎫 Обращение #{ticket.id}\n"
            f"Статус: {status}\n"
            f"Пользователь: {ticket.user_tg_id}\n"
            f"Оператор: {assigned}\n"
            f"Создано: {created}\n"
            f"Обновлено: {updated}\n\n"
            f"{history}"
        )
        await callback.message.edit_text(
            text,
            reply_markup=_ticket_view_keyboard(ticket.id, ticket.status, is_admin=is_admin),
        )
        await callback.answer()
    finally:
        session.close()


@router.callback_query(F.data == "ticket_new")
async def ticket_new(callback: CallbackQuery):
    tg_id = callback.from_user.id
    session = Session()
    try:
        ticket = get_user_active_ticket(session, tg_id)
        if ticket:
            await callback.message.edit_text(
                f"У вас уже есть активное обращение #{ticket.id}.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🎫 Открыть обращение", callback_data=f"ticket_view_{ticket.id}")],
                        [InlineKeyboardButton(text="📂 Мои обращения", callback_data="ticket_my")],
                        [InlineKeyboardButton(text="◀️ Назад", callback_data="support")],
                    ]
                ),
            )
            await callback.answer()
            return

        ticket = create_ticket(session, user_tg_id=tg_id)
        session.commit()
        pending_ticket_replies[tg_id] = ticket.id

        await callback.message.edit_text(
            f"Обращение #{ticket.id} создано.\nОтправьте одним сообщением описание проблемы.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Отмена", callback_data="support")]]
            ),
        )
        await callback.answer()

        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🎫 Открыть обращение", callback_data=f"ticket_view_{ticket.id}")]]
        )
        try:
            await callback.bot.send_message(
                ADMIN_ID,
                f"🆕 Новое обращение #{ticket.id} от пользователя `{tg_id}`",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=kb,
            )
        except Exception:
            pass
    finally:
        session.close()


@router.callback_query(F.data == "ticket_my")
async def ticket_my(callback: CallbackQuery):
    tg_id = callback.from_user.id
    session = Session()
    try:
        tickets = list_user_tickets(session, tg_id, limit=10)
    finally:
        session.close()

    if not tickets:
        await callback.message.edit_text(
            "Обращений пока нет.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🎫 Создать обращение", callback_data="ticket_new")],
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="support")],
                ]
            ),
        )
        await callback.answer()
        return

    rows: list[list[InlineKeyboardButton]] = []
    for ticket in tickets:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"#{ticket.id} {_ticket_status_title(ticket.status)}",
                    callback_data=f"ticket_view_{ticket.id}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text="🎫 Создать обращение", callback_data="ticket_new")])
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="support")])

    await callback.message.edit_text(
        "Мои обращения:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ticket_view_"))
async def ticket_view(callback: CallbackQuery):
    ticket_id = int(callback.data.replace("ticket_view_", ""))
    await _render_ticket(callback, ticket_id)


@router.callback_query(F.data.startswith("ticket_reply_"))
async def ticket_reply(callback: CallbackQuery):
    ticket_id = int(callback.data.replace("ticket_reply_", ""))
    session = Session()
    try:
        ticket = get_ticket_by_id(session, ticket_id)
        if not ticket:
            await callback.answer("Обращение не найдено", show_alert=True)
            return
        if not _can_access_support_ticket(session, ticket, callback.from_user.id):
            await callback.answer("Нет доступа", show_alert=True)
            return
        if callback.from_user.id == ADMIN_ID:
            set_ticket_status(
                session,
                ticket=ticket,
                status=STATUS_IN_PROGRESS,
                assigned_admin_tg_id=ADMIN_ID,
            )
        elif ticket.status == STATUS_CLOSED:
            claim_legacy_ticket(
                ticket,
                actor_tg_id=callback.from_user.id,
                account_id=_support_actor_account_id(session, callback.from_user.id),
            )
            set_ticket_status(session, ticket=ticket, status=STATUS_OPEN)
        session.commit()
    finally:
        session.close()

    pending_ticket_replies[callback.from_user.id] = ticket_id
    await callback.message.edit_text(
        f"Ответ в обращение #{ticket_id}: отправьте текст, скриншот или файл одним сообщением.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data=f"ticket_view_{ticket_id}")]]
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ticket_close_"))
async def ticket_close(callback: CallbackQuery):
    ticket_id = int(callback.data.replace("ticket_close_", ""))
    session = Session()
    try:
        ticket = get_ticket_by_id(session, ticket_id)
        if not ticket:
            await callback.answer("Обращение не найдено", show_alert=True)
            return
        if not _can_access_support_ticket(session, ticket, callback.from_user.id):
            await callback.answer("Нет доступа", show_alert=True)
            return
        if callback.from_user.id != ADMIN_ID:
            claim_legacy_ticket(
                ticket,
                actor_tg_id=callback.from_user.id,
                account_id=_support_actor_account_id(session, callback.from_user.id),
            )
        set_ticket_status(session, ticket=ticket, status=STATUS_CLOSED)
        delivery_tg_id = resolve_ticket_notification_tg_id(session, ticket)
        session.commit()

        # Notify opposite side.
        if callback.from_user.id == ADMIN_ID:
            if delivery_tg_id is None:
                logger.warning(
                    "main bot ticket close notification skipped ticket=%s reason=no_telegram_target",
                    ticket.id,
                )
            else:
                try:
                    await callback.bot.send_message(delivery_tg_id, f"Обращение #{ticket.id} закрыто оператором.")
                except Exception:
                    pass
        else:
            try:
                await callback.bot.send_message(
                    ADMIN_ID,
                    f"Пользователь `{ticket.user_tg_id}` закрыл обращение #{ticket.id}.",
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception:
                pass
    finally:
        session.close()
    await _render_ticket(callback, ticket_id)


@router.callback_query(F.data.startswith("ticket_reopen_"))
async def ticket_reopen(callback: CallbackQuery):
    ticket_id = int(callback.data.replace("ticket_reopen_", ""))
    session = Session()
    try:
        ticket = get_ticket_by_id(session, ticket_id)
        if not ticket:
            await callback.answer("Обращение не найдено", show_alert=True)
            return
        if not _can_access_support_ticket(session, ticket, callback.from_user.id):
            await callback.answer("Нет доступа", show_alert=True)
            return
        if callback.from_user.id != ADMIN_ID:
            claim_legacy_ticket(
                ticket,
                actor_tg_id=callback.from_user.id,
                account_id=_support_actor_account_id(session, callback.from_user.id),
            )
        set_ticket_status(session, ticket=ticket, status=STATUS_OPEN)
        session.commit()

        if callback.from_user.id != ADMIN_ID:
            try:
                await callback.bot.send_message(
                    ADMIN_ID,
                    f"Обращение #{ticket.id} переоткрыто пользователем `{ticket.user_tg_id}`.",
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception:
                pass
    finally:
        session.close()
    await _render_ticket(callback, ticket_id)


@router.callback_query(F.data.startswith("ticket_claim_"))
async def ticket_claim(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Только для админа", show_alert=True)
        return
    ticket_id = int(callback.data.replace("ticket_claim_", ""))
    session = Session()
    try:
        ticket = get_ticket_by_id(session, ticket_id)
        if not ticket:
            await callback.answer("Обращение не найдено", show_alert=True)
            return
        set_ticket_status(
            session,
            ticket=ticket,
            status=STATUS_IN_PROGRESS,
            assigned_admin_tg_id=ADMIN_ID,
        )
        session.commit()
    finally:
        session.close()
    await _render_ticket(callback, ticket_id)


@router.callback_query(F.data == "admin_tickets")
async def admin_tickets(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Только для админа", show_alert=True)
        return

    session = Session()
    try:
        tickets = list_active_tickets(session, limit=20)
    finally:
        session.close()

    if not tickets:
        await callback.message.edit_text(
            "В очереди нет активных обращений.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin")]]
            ),
        )
        await callback.answer()
        return

    rows: list[list[InlineKeyboardButton]] = []
    for ticket in tickets:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"#{ticket.id} u:{ticket.user_tg_id} {_ticket_status_title(ticket.status)}",
                    callback_data=f"ticket_view_{ticket.id}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_tickets")])
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin")])

    await callback.message.edit_text(
        "Активные обращения:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await callback.answer()
