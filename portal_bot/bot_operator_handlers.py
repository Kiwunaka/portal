"""Operator commands, moderation, expiry monitoring and bot startup.

Loaded by the bot composition root in source order. Public symbols are
re-exported for backwards compatibility.
"""

try:
    from .module_slices import bootstrap_slice
except ImportError:
    from module_slices import bootstrap_slice

bootstrap_slice(globals())

# ==========================================
#           ADMIN COMMANDS
# ==========================================
@router.message(Command("admin"))
async def admin_stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    # 🧹 Delete command message
    try:
        await message.delete()
    except:
        pass

    stats = get_stats()

    await message.answer(
        bot_text(
            "bot.admin.stats",
            total=stats["total"],
            active=stats["active"],
            stars=stats["stars"]
        ),
        parse_mode=ParseMode.MARKDOWN
    )

@router.message(Command("user"))
async def admin_user_search(message: Message):
    """Search user by @username or tg_id: /user @name or /user 123456"""
    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "🔍 *Поиск пользователя*\n\n"
            "Использование:\n"
            "`/user @username`\n"
            "`/user 123456789`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    query = args[1].strip()
    session = Session()

    if query.startswith("@"):
        # Search by username
        username = query.lstrip("@")
        user = session.query(User).filter(User.username.ilike(username)).first()
    else:
        # Search by tg_id
        try:
            tg_id = int(query)
            user = session.query(User).filter_by(tg_id=tg_id).first()
        except ValueError:
            user = session.query(User).filter(User.username.ilike(query)).first()

    if not user:
        session.close()
        await message.answer(f"❌ Пользователь `{query}` не найден", parse_mode=ParseMode.MARKDOWN)
        return

    # Get achievements count
    ach_count = session.query(Achievement).filter_by(tg_id=user.tg_id).count()

    session.close()



    # Format user info
    status = "✅ Активен" if user.is_active else "❌ Неактивен"
    expiry = user.expiry_at.strftime("%d.%m.%Y") if user.expiry_at else "—"
    created = user.created_at.strftime("%d.%m.%Y") if user.created_at else "—"

    safe_username = (user.username or '—').replace('_', '\\_')
    text = (
        f"👤 *Пользователь*\n\n"
        f"ID: `{user.tg_id}`\n"
        f"Username: @{safe_username}\n"
        f"Статус: {status}\n\n"
        f"📦 Тариф: `{user.sub_type or '—'}`\n"
        f"📅 До: `{expiry}`\n"
        f"📡 Режим: `{_plan_mode_label(user.sub_type, user=user)}`\n"
        f"Оплачено: `{user.stars_paid or 0}` Stars\n\n"
        f"🔥 Streak: `{user.streak_months or 0}` мес\n"
        f"🏆 Ачивки: `{ach_count}`\n"
        f"👥 Рефералы: `{user.referral_count or 0}`\n\n"
        f"📆 Создан: `{created}`"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 Открыть", callback_data=f"adm_user_{user.tg_id}"),
            InlineKeyboardButton(text="📋 Логи", callback_data=f"admin_logs_{user.tg_id}"),
        ],
        [
            InlineKeyboardButton(text="📅 Продлить", callback_data=f"admin_extend_{user.tg_id}")
        ],
        [InlineKeyboardButton(text="🚫 Заблокировать" if user.is_active else "✅ Разблокировать",
                              callback_data=f"admin_ban_{user.tg_id}")]
    ])

    await message.answer(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

# Admin action states
admin_pending_actions = {}
# In-memory draft for the broadcast composer (admin only).
admin_broadcast_drafts: dict[int, dict] = {}

@router.callback_query(F.data.startswith("admin_logs_"))
async def admin_view_logs(callback: CallbackQuery):
    """View user activity logs"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔️ Доступ запрещён")
        return

    tg_id = int(callback.data.replace("admin_logs_", ""))
    session = Session()

    user = session.query(User).filter_by(tg_id=tg_id).first()
    if not user:
        session.close()
        await callback.answer("Юзер не найден")
        return

    # Get achievements
    achievements = session.query(Achievement).filter_by(tg_id=tg_id).all()
    ach_text = "\n".join([f"  • {ACHIEVEMENTS.get(a.achievement_id, {}).get('name', a.achievement_id)}"
                          for a in achievements[:5]]) or "  Нет"

    # Get gift cards redeemed/created
    cards_created = session.query(GiftCard).filter_by(created_by=tg_id).count()
    cards_redeemed = session.query(GiftCard).filter_by(redeemed_by=tg_id).count()

    # Get reviews
    review = session.query(Review).filter_by(tg_id=tg_id).first()
    review_text = f"  Оценка {review.rating}/5 {review.text[:50] if review.text else ''}" if review else "  Нет"

    session.close()

    # Wheel info
    wheel_text = user.last_wheel_spin.strftime("%d.%m.%Y %H:%M") if user.last_wheel_spin else "Никогда"

    text = (
        f"📋 *Логи пользователя* `{tg_id}`\n\n"
        f"*Последняя активность:*\n"
        f"  🎰 Рулетка: {wheel_text}\n"
        f"  🔥 Streak check: {user.streak_last_check.strftime('%d.%m.%Y') if user.streak_last_check else 'Нет'}\n\n"
        f"*Ачивки ({len(achievements)}):*\n{ach_text}\n\n"
        f"*Подарочные карты:*\n"
        f"  Создано: {cards_created}\n"
        f"  Активировано: {cards_redeemed}\n\n"
        f"*Отзыв:*\n{review_text}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад к профилю", callback_data=f"admin_profile_{tg_id}")]
    ])

    await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    await callback.answer()

@router.callback_query(F.data.startswith("admin_profile_"))
async def admin_back_to_profile(callback: CallbackQuery):
    """Return to user profile from logs"""
    if callback.from_user.id != ADMIN_ID:
        return

    tg_id = int(callback.data.replace("admin_profile_", ""))
    # Reuse search logic
    from aiogram.types import Message as FakeMessage

    session = Session()
    user = session.query(User).filter_by(tg_id=tg_id).first()
    ach_count = session.query(Achievement).filter_by(tg_id=tg_id).count() if user else 0
    session.close()

    if not user:
        await callback.answer("Юзер не найден")
        return

    status = "✅ Активен" if user.is_active else "❌ Неактивен"
    expiry = user.expiry_at.strftime("%d.%m.%Y") if user.expiry_at else "—"
    created = user.created_at.strftime("%d.%m.%Y") if user.created_at else "—"

    safe_username = (user.username or '—').replace('_', '\\_')
    text = (
        f"👤 *Пользователь*\n\n"
        f"ID: `{user.tg_id}`\n"
        f"Username: @{safe_username}\n"
        f"Статус: {status}\n\n"
        f"📦 Тариф: `{user.sub_type or '—'}`\n"
        f"📅 До: `{expiry}`\n"
        f"Оплачено: `{user.stars_paid or 0}` Stars\n\n"
        f"🔥 Streak: `{user.streak_months or 0}` мес\n"
        f"🏆 Ачивки: `{ach_count}`\n"
        f"👥 Рефералы: `{user.referral_count or 0}`\n\n"
        f"📆 Создан: `{created}`"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 Открыть", callback_data=f"adm_user_{user.tg_id}"),
            InlineKeyboardButton(text="📋 Логи", callback_data=f"admin_logs_{user.tg_id}"),
        ],
        [
            InlineKeyboardButton(text="📅 Продлить", callback_data=f"admin_extend_{user.tg_id}")
        ],
        [InlineKeyboardButton(text="🚫 Заблокировать" if user.is_active else "✅ Разблокировать",
                              callback_data=f"admin_ban_{user.tg_id}")]
    ])

    await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    await callback.answer()

    # Handler removed
    # await callback.answer("🚫 Лимиты по трафику не поддерживаются. Используйте 'Продлить'.", show_alert=True)

@router.callback_query(F.data.startswith("admin_extend_"))
async def admin_extend_prompt(callback: CallbackQuery):
    """Prompt to extend subscription"""
    if callback.from_user.id != ADMIN_ID:
        return

    tg_id = int(callback.data.replace("admin_extend_", ""))
    admin_pending_actions[callback.from_user.id] = {"action": "extend", "target": tg_id}

    await callback.message.edit_text(
        f"📅 *Продлить подписку*\n\n"
        f"Юзер: `{tg_id}`\n\n"
        f"Отправь количество дней (число):",
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_ban_"))
async def admin_toggle_ban(callback: CallbackQuery):
    """Ban/unban user"""
    if callback.from_user.id != ADMIN_ID:
        return

    tg_id = int(callback.data.replace("admin_ban_", ""))
    session = Session()
    user = session.query(User).filter_by(tg_id=tg_id).first()

    if user:
        user.is_active = not user.is_active
        new_status = "заблокирован" if not user.is_active else "разблокирован"
        session.commit()
        await callback.answer(f"✅ Юзер {new_status}")

    session.close()
    # Return to profile
    await admin_back_to_profile(callback)

# ==========================================
#           PROMO CODES
# ==========================================

@router.message(Command("template"))
async def template_command(message: Message, bot: Bot):
    """
    /template add KEY text - create template
    /template list - show all
    /template send KEY - send to all
    /template send KEY @user - send to user
    /template delete KEY - delete
    """
    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split(maxsplit=3)

    if len(args) < 2:
        await message.answer(
            "📝 *Шаблоны сообщений*\n\n"
            "`/template add key текст` — создать\n"
            "`/template list` — список\n"
            "`/template send key` — всем\n"
            "`/template send key @user` — юзеру\n"
            "`/template delete key` — удалить",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    subcmd = args[1].lower()

    if subcmd == "add" and len(args) >= 4:
        key = args[2].lower()
        text = args[3]

        session = Session()
        existing = session.query(Template).filter_by(key=key).first()
        if existing:
            existing.text = text
            action = "обновлён"
        else:
            session.add(Template(key=key, text=text))
            action = "создан"
        session.commit()
        session.close()

        await message.answer(f"✅ Шаблон `{key}` {action}", parse_mode=ParseMode.MARKDOWN)

    elif subcmd == "list":
        session = Session()
        templates = session.query(Template).all()
        session.close()

        if not templates:
            await message.answer("📝 _Нет шаблонов_", parse_mode=ParseMode.MARKDOWN)
            return

        lines = [f"`{t.key}` — {t.text[:50]}..." if len(t.text) > 50 else f"`{t.key}` — {t.text}" for t in templates]
        await message.answer("📝 *Шаблоны:*\n\n" + "\n".join(lines), parse_mode=ParseMode.MARKDOWN)

    elif subcmd == "send" and len(args) >= 3:
        key = args[2].lower()
        target_user = args[3] if len(args) >= 4 else None

        session = Session()
        template = session.query(Template).filter_by(key=key).first()

        if not template:
            session.close()
            await message.answer(f"❌ Шаблон `{key}` не найден", parse_mode=ParseMode.MARKDOWN)
            return

        if target_user:
            # Send to specific user
            username = target_user.lstrip("@")
            user = session.query(User).filter(User.username.ilike(username)).first()
            if not user:
                try:
                    uid = int(target_user)
                    user = session.query(User).filter_by(tg_id=uid).first()
                except:
                    pass
            session.close()

            if not user:
                await message.answer(f"❌ Юзер `{target_user}` не найден", parse_mode=ParseMode.MARKDOWN)
                return

            try:
                await bot.send_message(user.tg_id, template.text, parse_mode=ParseMode.MARKDOWN)
                await message.answer(f"✅ Шаблон `{key}` отправлен @{user.username or user.tg_id}", parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                await message.answer(f"❌ Ошибка: {e}")
        else:
            # Send to all
            users = session.query(User).filter_by(is_active=True).all()
            session.close()

            sent = 0
            for user in users:
                if user.tg_id in PROTECTED_USERS or user.tg_id == ADMIN_ID:
                    continue
                try:
                    await bot.send_message(user.tg_id, template.text, parse_mode=ParseMode.MARKDOWN)
                    sent += 1
                except:
                    pass

            await message.answer(f"✅ Шаблон `{key}` отправлен {sent} юзерам", parse_mode=ParseMode.MARKDOWN)

    elif subcmd == "delete" and len(args) >= 3:
        key = args[2].lower()

        session = Session()
        template = session.query(Template).filter_by(key=key).first()
        if template:
            session.delete(template)
            session.commit()
            await message.answer(f"✅ Шаблон `{key}` удалён", parse_mode=ParseMode.MARKDOWN)
        else:
            await message.answer(f"❌ Шаблон `{key}` не найден", parse_mode=ParseMode.MARKDOWN)
        session.close()

    else:
        await message.answer("❌ Неверный формат команды")


def activate_promo_code_for_user(tg_id: int, code: str) -> tuple[bool, str]:
    code = (code or "").strip().upper()
    if not code:
        _track_bonus_event(tg_id=int(tg_id), event_name="promo_redeem_denied", meta={"reason": "empty_code"})
        return False, "❌ Промокод пустой"
    if not check_tos_accepted(int(tg_id)):
        _track_bonus_event(tg_id=int(tg_id), event_name="promo_redeem_denied", meta={"code": code, "reason": "tos_required"})
        return False, "⚠️ Сначала примите оферту через /start."

    session = Session()
    try:
        promo = session.query(PromoCode).filter_by(code=code).first()
        if not promo:
            _track_bonus_event(tg_id=int(tg_id), event_name="promo_redeem_denied", meta={"code": code, "reason": "not_found"})
            return False, "❌ Промокод не найден"
        if promo.expires_at and promo.expires_at < _utcnow():
            _track_bonus_event(tg_id=int(tg_id), event_name="promo_redeem_denied", meta={"code": code, "reason": "expired"})
            return False, "❌ Срок действия промокода истёк"

        if promo.uses_left == 0:
            _track_bonus_event(tg_id=int(tg_id), event_name="promo_redeem_denied", meta={"code": code, "reason": "exhausted"})
            return False, "❌ Промокод больше не активен"

        usage = session.query(PromoUsage).filter_by(tg_id=tg_id, promo_code=code).first()
        if usage:
            _track_bonus_event(tg_id=int(tg_id), event_name="promo_redeem_denied", meta={"code": code, "reason": "already_redeemed"})
            return False, "❌ Вы уже использовали этот промокод"

        user = session.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            _track_bonus_event(tg_id=int(tg_id), event_name="promo_redeem_denied", meta={"code": code, "reason": "user_not_found"})
            return False, "❌ Пользователь не найден"

        active_campaigns_for_code = (
            session.query(func.count(IncentiveCampaign.id))
            .filter(func.lower(IncentiveCampaign.campaign_type) == "promo")
            .filter(func.upper(IncentiveCampaign.target_value) == code)
            .filter(IncentiveCampaign.is_active == True)
            .scalar()
            or 0
        )
        campaign = _campaign_lookup(
            session=session,
            campaign_type="promo",
            target_value=code,
            user=user,
            now=_utcnow(),
        )
        if int(active_campaigns_for_code) > 0 and campaign is None:
            _track_bonus_event(
                tg_id=int(tg_id),
                event_name="promo_redeem_denied",
                meta={"code": code, "reason": "campaign_restriction_mismatch"},
            )
            session.flush()
            return False, "❌ Промокод недоступен для этого аккаунта"

        promo_type = str(promo.promo_type or "").strip().lower()
        promo_value = int(promo.value or 0)
        if promo_type not in {"days", "discount"} or promo_value <= 0:
            _track_bonus_event(tg_id=int(tg_id), event_name="promo_redeem_denied", meta={"code": code, "reason": "invalid_value"})
            return False, "❌ Промокод некорректен"

        if promo_type == "days":
            now = _utcnow()
            if user:
                expiry = _naive_utc(user.expiry_at)
                if expiry and expiry > now:
                    user.expiry_at = expiry + timedelta(days=promo_value)
                else:
                    user.expiry_at = now + timedelta(days=promo_value)
                user.is_active = True
            result_text = f"🎁 Вам добавлено *+{promo_value} дней!*"
        elif promo_type == "discount":
            user = session.query(User).filter_by(tg_id=tg_id).first()
            if user:
                user.pending_discount_pct = max(1, min(95, int(promo_value or 0)))
                user.pending_discount_code = str(code).upper()[:20]
                user.pending_discount_set_at = _utcnow()
            result_text = (
                f"🎉 Скидка *{promo_value}%* активирована.\n"
                "Она применится к следующей оплате в ₽."
            )
        else:
            result_text = f"🎉 Скидка *{promo_value}%* будет применена к следующей покупке!"

        session.add(PromoUsage(tg_id=tg_id, promo_code=code))
        _campaign_consume(row=campaign)
        if promo.uses_left > 0:
            promo.uses_left -= 1
        session.commit()
        _track_bonus_event(
            tg_id=int(tg_id),
            event_name="promo_redeemed",
            meta={
                "code": code,
                "promo_type": promo_type,
                "value": int(promo_value),
                "applied_days": int(promo_value if promo_type == "days" else 0),
                "pending_discount_pct": int(user.pending_discount_pct or 0) if promo_type == "discount" and user else 0,
            },
        )
        return True, f"✅ *Промокод активирован!*\n\n{result_text}"
    finally:
        session.close()


def _is_manual_test_user(user: User | None) -> bool:
    if not user:
        return False
    return bool(
        getattr(user, "is_manual", False)
        or int(getattr(user, "tg_id", 0) or 0) < 0
        or str(getattr(user, "sub_type", "") or "").upper() == "MANUAL"
        or getattr(user, "created_by_admin", None) is not None
    )


def _admin_user_effective_status(user: User | None, *, now: datetime | None = None) -> str:
    if not user:
        return "expired"
    if _is_manual_test_user(user):
        return "manual_test"
    current = now or _utcnow()
    expiry = _naive_utc(getattr(user, "expiry_at", None))
    if not bool(getattr(user, "is_active", False)):
        return "blocked"
    if not expiry or expiry <= current:
        return "expired"
    return "active"


def _admin_user_status_label(status: str) -> str:
    if status == "active":
        return "✅ Активен"
    if status == "blocked":
        return "⛔ Заблокирован"
    if status == "manual_test":
        return "🧪 Manual/Test"
    return "⌛ Истёк"


def _admin_user_origin_label(user: User | None) -> str:
    if not user:
        return "—"
    if _is_manual_test_user(user):
        return "MANUAL/TEST"
    has_app = bool(getattr(user, "app_install_id", None) or getattr(user, "is_app_user", False))
    has_telegram = bool(getattr(user, "linked_telegram_id", None) or getattr(user, "username", None) or int(getattr(user, "tg_id", 0) or 0) > 0)
    if has_app and has_telegram:
        return "APP + TELEGRAM"
    if has_app:
        return "APP"
    return "TELEGRAM"


@router.message(Command("promo"))
async def promo_command(message: Message, bot: Bot):
    """
    Admin: /promo create CODE TYPE VALUE [USES]
    Admin: /promo list
    User: /promo CODE
    """
    tg_id = message.from_user.id
    pending_promo_codes.discard(tg_id)
    args = message.text.split()

    # Admin commands
    if tg_id == ADMIN_ID and len(args) >= 2:
        subcmd = args[1].lower()

        if subcmd == "create" and len(args) >= 5:
            # /promo create NEWYEAR discount 20 100
            # /promo create BONUS10 gb 10 50
            code = args[2].upper()
            promo_type = args[3].lower()
            try:
                value = int(args[4])
                uses = int(args[5]) if len(args) > 5 else -1
            except:
                await message.answer("❌ Неверный формат. Пример:\n`/promo create NEWYEAR discount 20 100`", parse_mode=ParseMode.MARKDOWN)
                return

            if promo_type not in ["discount", "days"]:
                await message.answer("❌ Тип: `discount` или `days`", parse_mode=ParseMode.MARKDOWN)
                return

            session = Session()
            existing = session.query(PromoCode).filter_by(code=code).first()
            if existing:
                session.close()
                await message.answer(f"❌ Код `{code}` уже существует", parse_mode=ParseMode.MARKDOWN)
                return

            promo = PromoCode(code=code, promo_type=promo_type, value=value, uses_left=uses)
            session.add(promo)
            session.commit()
            session.close()

            type_text = f"{value}%" if promo_type == "discount" else f"+{value} Дней"
            uses_text = "∞" if uses == -1 else str(uses)
            await message.answer(
                f"✅ *Промокод создан!*\n\n"
                f"Код: `{code}`\n"
                f"Тип: {type_text}\n"
                f"Лимит: {uses_text}",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        elif subcmd == "list":
            session = Session()
            promos = session.query(PromoCode).filter(PromoCode.uses_left != 0).all()
            session.close()

            if not promos:
                await message.answer("📭 Нет активных промокодов")
                return

            lines = []
            for p in promos:
                type_text = f"{p.value}%" if p.promo_type == "discount" else f"+{p.value} Дн."
                uses_text = "∞" if p.uses_left == -1 else str(p.uses_left)
                lines.append(f"`{p.code}` — {type_text}, осталось: {uses_text}")

            await message.answer(
                "🎫 *Активные промокоды:*\n\n" + "\n".join(lines),
                parse_mode=ParseMode.MARKDOWN
            )
            return

        elif subcmd == "delete" and len(args) >= 3:
            code = args[2].upper()
            session = Session()
            promo = session.query(PromoCode).filter_by(code=code).first()
            if promo:
                session.delete(promo)
                session.commit()
                await message.answer(f"✅ Промокод `{code}` удалён", parse_mode=ParseMode.MARKDOWN)
            else:
                await message.answer(f"❌ Промокод `{code}` не найден", parse_mode=ParseMode.MARKDOWN)
            session.close()
            return

    # User activation: /promo CODE
    if len(args) >= 2:
        code = args[1].upper()
        ok, result = activate_promo_code_for_user(tg_id, code)
        await message.answer(result, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer(
            "🎫 *Активация промокода*\n\n"
            "Использование: `/promo КОД`\n\n"
            "Пример: `/promo NEWYEAR`",
            parse_mode=ParseMode.MARKDOWN
        )

# ==========================================
#           HEALTH CHECK
# ==========================================

@router.message(Command("health"))
async def health_check(message: Message, bot: Bot):
    """Check system health"""
    if message.from_user.id != ADMIN_ID:
        return

    import time
    start_time = time.time()

    status = []

    # Bot status (always OK if we're running)
    status.append("✅ Бот: работает")

    # Database check
    try:
        session = Session()
        user_count = session.query(User).count()
        active_count = session.query(User).filter_by(is_active=True).count()
        session.close()
        status.append(f"✅ БД: {user_count} юзеров ({active_count} активных)")
    except Exception as e:
        status.append(f"❌ БД: {str(e)[:50]}")

    # Panel check
    try:
        clients = await panel.get_clients_list()
        if clients is not None:
            status.append(f"✅ Панель: {len(clients)} клиентов")
        else:
            status.append("⚠️ Панель: нет ответа")
    except Exception as e:
        status.append(f"❌ Панель: {str(e)[:50]}")

    # API check (self-ping)
    try:
        import aiohttp
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{WEBAPP_URL}", timeout=aiohttp.ClientTimeout(total=5)) as r:
                if r.status == 200:
                    status.append("✅ WebApp: доступен")
                else:
                    status.append(f"⚠️ WebApp: код {r.status}")
    except Exception as e:
        status.append(f"❌ WebApp: {str(e)[:30]}")

    elapsed = round((time.time() - start_time) * 1000)

    await message.answer(
        f"❤️ *Health Check*\n\n" +
        "\n".join(status) +
        f"\n\n⏱️ Проверка: {elapsed}мс",
        parse_mode=ParseMode.MARKDOWN
    )

# ==========================================
#           REVIEWS MODERATION
# ==========================================

@router.message(Command("reviews"))
async def reviews_moderation(message: Message):
    """List reviews for moderation: /reviews [featured|all]"""
    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()
    show_featured = len(args) > 1 and args[1].lower() == "featured"

    session = Session()
    if show_featured:
        reviews = session.query(Review).filter_by(is_featured=True).order_by(Review.created_at.desc()).limit(10).all()
        title = "Отзывы на главной"
    else:
        reviews = session.query(Review).order_by(Review.created_at.desc()).limit(10).all()
        title = "Последние отзывы"

    session.close()

    if not reviews:
        await message.answer("📭 Отзывов пока нет")
        return

    for r in reviews:
        featured = "На главной · " if r.is_featured else ""
        masked = _mask_review_username(r.username)
        label = f"@{masked}" if masked != "Пользователь" else masked
        text = r.text[:100] if r.text else "—"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="На главную" if not r.is_featured else "Снять с главной",
                                     callback_data=f"review_toggle_{r.id}"),
                InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"review_delete_{r.id}")
            ]
        ])
        await message.answer(
            f"{featured}*{label}* · оценка {r.rating}/5\n"
            f"_{text}_\n"
            f"`ID:{r.id}`",
            reply_markup=kb,
            parse_mode=ParseMode.MARKDOWN
        )

@router.callback_query(F.data.startswith("review_toggle_"))
async def toggle_review_featured(callback: CallbackQuery):
    """Toggle featured status"""
    if callback.from_user.id != ADMIN_ID:
        return

    review_id = int(callback.data.replace("review_toggle_", ""))
    session = Session()
    review = session.query(Review).filter_by(id=review_id).first()
    if review:
        review.is_featured = not review.is_featured
        status = "добавлен на главную" if review.is_featured else "убран с главной"
        session.commit()
        await callback.answer(f"✅ Отзыв {status}")
    session.close()

    # If this toggle was triggered from the admin list view, refresh the list.
    try:
        txt = (callback.message.text or "").strip()
        if ("Стр " in txt) and ("Все отзывы" in txt or "Отзывы на главной" in txt):
            featured_only = txt.startswith("Отзывы на главной")
            import re

            m = re.search(r"Стр\\s+(\\d+)/(\\d+)", txt)
            page = int(m.group(1)) - 1 if m else 0
            await _render_reviews_page(callback=callback, featured_only=featured_only, page=page)
    except Exception:
        pass

@router.callback_query(F.data.startswith("review_delete_"))
async def delete_review(callback: CallbackQuery):
    """Delete review"""
    if callback.from_user.id != ADMIN_ID:
        return

    review_id = int(callback.data.replace("review_delete_", ""))
    session = Session()
    review = session.query(Review).filter_by(id=review_id).first()
    if review:
        session.delete(review)
        session.commit()
    session.close()

    # Refresh admin list view if this action came from it; otherwise just confirm.
    try:
        txt = (callback.message.text or "").strip()
        if ("Стр " in txt) and ("Все отзывы" in txt or "Отзывы на главной" in txt):
            featured_only = txt.startswith("Отзывы на главной")
            import re

            m = re.search(r"Стр\\s+(\\d+)/(\\d+)", txt)
            page = int(m.group(1)) - 1 if m else 0
            await _render_reviews_page(callback=callback, featured_only=featured_only, page=page)
        else:
            await callback.answer("🗑️ Удалено")
    except Exception:
        await callback.answer("🗑️ Удалено")

@router.message(Command("sync"))
async def sync_usernames(message: Message, bot: Bot):
    """Sync usernames from Telegram API for all users and update panel comments"""
    if message.from_user.id != ADMIN_ID:
        return

    # 🧹 Delete command message
    try:
        await message.delete()
    except:
        pass

    await message.answer("🔄 Синхронизирую никнеймы и обновляю панель...")

    session = Session()
    try:
        tg_ids: set[int] = set()
        for user in session.query(User).all():
            tg_id = int(getattr(user, "tg_id", 0) or 0)
            linked_id = int(getattr(user, "linked_telegram_id", 0) or 0)
            if 0 < tg_id < 9_000_000_000_000 and tg_id not in PROTECTED_USERS and tg_id != ADMIN_ID:
                tg_ids.add(tg_id)
            if linked_id > 0 and linked_id not in PROTECTED_USERS and linked_id != ADMIN_ID:
                tg_ids.add(linked_id)
    finally:
        session.close()

    updated = 0
    panel_updated = 0
    errors = 0

    for tg_id in sorted(tg_ids):
        try:
            chat = await bot.get_chat(tg_id)
            username = getattr(chat, "username", None)
            if sync_telegram_identity(tg_id, username):
                updated += 1
            if username and await panel.update_client_comment(tg_id, f"@{username}"):
                panel_updated += 1
        except Exception:
            errors += 1

    await message.answer(
        f"✅ Синхронизация завершена!\n\n"
        f"📊 Обновлено в БД: {updated}\n"
        f"📋 Обновлено в панели: {panel_updated}\n"
        f"❌ Ошибок: {errors}\n"
        f"👥 Всего: {len(tg_ids)}"
    )


# Backwards compat from old const
BROADCAST_EXCLUDE = PROTECTED_USERS

@router.message(Command("broadcast"))
async def admin_broadcast(message: Message, bot: Bot):
    """Send an app-first subscription update notice to all active users."""
    if message.from_user.id != ADMIN_ID:
        return

    try:
        await message.delete()
    except:
        pass

    session = Session()
    users = session.query(User).filter(User.is_active == True).all()
    session.close()

    sent = 0
    failed = 0
    skipped = 0

    status_msg = await message.answer(f"📤 Отправляю рассылку...\n👥 Всего: {len(users)}")

    for user in users:
        # Skip excluded users and admin
        if user.tg_id in BROADCAST_EXCLUDE or user.tg_id == ADMIN_ID:
            skipped += 1
            continue

        try:
            await bot.send_message(
                user.tg_id,
                _bulk_subscription_update_text(),
                reply_markup=_bulk_subscription_update_keyboard(),
                parse_mode=ParseMode.MARKDOWN,
            )
            sent += 1
            await asyncio.sleep(0.1)  # Rate limit
        except Exception as e:
            failed += 1

    await status_msg.edit_text(
        f"✅ *Рассылка завершена!*\n\n"
        f"📨 Отправлено: {sent}\n"
        f"⏭️ Пропущено: {skipped}\n"
        f"❌ Ошибок: {failed}",
        parse_mode=ParseMode.MARKDOWN
    )

    audit_admin(
        actor_tg_id=message.from_user.id,
        action="admin_broadcast",
        meta=json.dumps(
            {"sent": sent, "failed": failed, "skipped": skipped, "total": len(users)},
            ensure_ascii=True,
            separators=(",", ":"),
        ),
    )


@router.message(Command("giftcode"))
async def admin_giftcode(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(
            "🎫 *Формат /giftcode*\n\n"
            "`/giftcode mini`\n"
            "`/giftcode standard`\n"
            "`/giftcode premium`\n"
            "`/giftcode standard 5` _(создать сразу 5 кодов)_",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    card_type = (parts[1] or "").strip().lower()
    if card_type not in GIFT_CARD_TYPES:
        await message.answer("❌ Неизвестный тип. Используйте: mini / standard / premium")
        return

    try:
        count = int(parts[2]) if len(parts) > 2 else 1
    except Exception:
        await message.answer("❌ Количество должно быть числом.")
        return
    count = max(1, min(20, count))

    created: list[str] = []
    for _ in range(count):
        code = create_gift_card(ADMIN_ID, card_type)
        if code:
            created.append(code)

    if not created:
        await message.answer("❌ Не удалось создать gift-коды.")
        return

    card = GIFT_CARD_TYPES.get(card_type, {})
    lines = "\n".join(f"`{c}`" for c in created[:20])
    await message.answer(
        f"✅ Создано кодов: *{len(created)}*\n"
        f"Тип: *{card.get('name', card_type)}*\n"
        f"Срок: *{int(card.get('days', 0))} дн.*\n\n"
        f"{lines}",
        parse_mode=ParseMode.MARKDOWN,
    )
    audit_admin(
        ADMIN_ID,
        "admin_gift_code_batch",
        meta=f"card_type={card_type}; requested={count}; created={len(created)}",
    )


@router.message(Command("gift"))
async def admin_gift(message: Message, bot: Bot):
    if message.from_user.id != ADMIN_ID:
        return

    # 🧹 Delete command message
    try:
        await message.delete()
    except:
        pass

    parts = message.text.split()
    if len(parts) < 3:
        await message.answer(
            "📦 *Формат команды /gift:*\n\n"
            "`/gift [tg_id] trial` — Пробный (5 дней)\n"
            "`/gift [tg_id] basic` — Стандарт (30 дней)\n"
            "`/gift [tg_id] pro` — Турбо (30 дней)\n"
            "`/gift [tg_id] vip` — VIP (365 дней)\n"
            "`/gift [tg_id] [days]` — Кастом\n\n"
            "_Примеры:_\n"
            "`/gift 123456789 vip`\n"
            "`/gift 123456789 90`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    try:
        gift_tg_id = int(parts[1])
    except ValueError:
        await message.answer("❌ Неверный tg_id")
        return
    if gift_tg_id > 0 and not check_tos_accepted(gift_tg_id):
        await message.answer(
            "⚠️ Этот пользователь ещё не принял оферту.\n"
            "Сначала пусть нажмёт /start и подтвердит условия, затем выдавайте подарок."
        )
        return

    # Preset tariffs for gifts
    gift_presets = {
        "trial": {"days": 5, "name": "🎁 Пробный"},
        "basic": {"days": 30, "name": "⚡ Стандарт"},
        "pro": {"days": 30, "name": "🚀 Турбо"},
        "vip": {"days": 365, "name": "👑 VIP"},
    }

    # Check if preset or custom
    preset_key = parts[2].lower()
    if preset_key in gift_presets:
        preset = gift_presets[preset_key]
        days = preset["days"]
        name = preset["name"]
    else:
        # Custom: /gift tg_id days
        try:
            days = int(parts[2])
            name = f"🎁 Подарок ({days} дней)"
        except ValueError:
            await message.answer("❌ Неверные параметры")
            return

    panel_client = await panel.get_existing_client(gift_tg_id)

    user = get_user(gift_tg_id)
    if user:
        # EXISTING USER - extend
        extend_user(gift_tg_id, days, 0)

        # Update sub_type to GIFT
        session = Session()
        db_user = session.query(User).filter_by(tg_id=gift_tg_id).first()
        if db_user:
            db_user.sub_type = "PAID"
            db_user.total_gb = 0
            ensure_user_account_foundation(session, db_user, now=_utcnow())
            session.commit()
        session.close()
    else:
        # NEW USER - generate sub_token FIRST before adding to panel
        sub_token = generate_sub_token()
        user_uuid = str(uuid.uuid4())
        email = f"User_{gift_tg_id}"

        if not panel_client:
            # Pass sub_token to add_client so panel uses secure subscription ID
            await panel.add_client(user_uuid, email, "PAID", 0, gift_tg_id, sub_token)
        else:
            user_uuid = panel_client.get("id")
            email = panel_client.get("email")

        # Create user in DB with generated sub_token
        session = Session()
        new_user = User(
            tg_id=gift_tg_id,
            uuid=user_uuid,
            email=email,
            sub_type="PAID",
            expiry_at=_utcnow() + timedelta(days=days),
            is_active=True,
            stars_paid=0,
            total_gb=0,
            sub_token=sub_token
        )
        session.add(new_user)
        ensure_user_account_foundation(session, new_user, now=_utcnow())
        session.commit()
        session.close()

    await message.answer(
        f"✅ Подарок отправлен!\n\n👤 ID: `{gift_tg_id}`\n📦 Тариф: {name}\n📅 Дней: {days}",
        parse_mode=ParseMode.MARKDOWN,
    )

    audit_admin(
        actor_tg_id=message.from_user.id,
        action="admin_gift",
        target_tg_id=gift_tg_id,
        meta=json.dumps(
            {"days": days, "preset": preset_key, "name": name},
            ensure_ascii=True,
            separators=(",", ":"),
        ),
    )

    try:
        await bot.send_message(
            gift_tg_id,
            f"🎁 *Вам подарили доступ к POKROV!*\n\n"
            f"📦 Тариф: {name}\n"
            f"📅 Дней: {days}\n"
            f"📡 Режим: платный доступ\n\n"
            "Следующий шаг: откройте кабинет или бот, выберите «Подключить устройство» и войдите тем же способом. "
            "Ручная ссылка доступна отдельно, если приложение пока не подходит.",
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        pass

# ==========================================
#               BACKGROUND TASKS
# ==========================================
def _queue_expired_user_reentry(session, *, user: User, now: datetime) -> dict:
    result = queue_free_profile_reentry(
        session,
        user=user,
        source="bot_expiry_monitor",
        now=now,
    )
    if str(result.get("reason") or "") == "free_tier_disabled":
        return result
    auto_free_days = max(30, int(os.getenv("AUTO_FREE_DAYS", "3650")))
    user.expiry_at = now + timedelta(days=auto_free_days)
    user.is_active = True
    return result


async def monitor_expiry(bot: Bot) -> None:
    """
    Background task to enforce expiry.

    Important: we DO NOT enforce traffic limits in this project.
    Traffic-based deactivation is dangerous because legacy/manual clients may have old totalGB limits in panels.
    """
    while True:
        try:
            await asyncio.sleep(3600)  # hourly
            now = _utcnow()

            session = Session()
            try:
                users = session.query(User).filter(User.is_active == True).all()
                for user in users:
                    try:
                        # Manual users are special (static accounts). Don't auto-disable them.
                        if _normalize_sub_type(user.sub_type) == "MANUAL":
                            continue

                        expiry = _naive_utc(user.expiry_at)
                        if expiry and now > expiry:
                            _queue_expired_user_reentry(session, user=user, now=now)
                            session.commit()

                            if user.tg_id > 0 and user.tg_id not in PROTECTED_USERS:
                                kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Продлить", callback_data="charge")]])
                                try:
                                    await bot.send_message(
                                        chat_id=user.tg_id,
                                        text=(
                                            "*Платный срок закончился*\n\n"
                                            "Перевожу вас в бесплатный режим; профиль обновится после подтверждения сервера.\n"
                                            "Если хотите вернуть все доступные локации и лимит устройств, нажмите кнопку ниже."
                                        ),
                                        reply_markup=kb,
                                        parse_mode=ParseMode.MARKDOWN,
                                    )
                                    track_event(
                                        tg_id=int(user.tg_id),
                                        event_name="expired",
                                        source="bot",
                                        meta={"flow": "monitor_expiry"},
                                    )
                                except Exception:
                                    pass
                    except Exception as e:
                        logger.error("Expiry monitor error user=%s: %s", getattr(user, "tg_id", "?"), e)
            finally:
                session.close()
        except Exception as e:
            logger.error("Expiry monitor loop error: %s", e)
            await asyncio.sleep(60)


async def _configure_public_bot_menu(bot: Bot) -> None:
    try:
        await bot.set_my_commands(
            [BotCommand(command=item["command"], description=item["description"]) for item in expected_public_command_payload()]
        )
    except Exception as e:
        logger.warning("set_my_commands failed: %s", e)

    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text=TELEGRAM_PROFILE_WEBAPP_MENU_TEXT,
                web_app=WebAppInfo(url=PUBLIC_BOT_WEBAPP_MENU_URL),
            )
        )
    except Exception as e:
        logger.warning("set_chat_menu_button failed: %s", e)

# ==========================================
#               MAIN
# ==========================================
async def main():
    bot = Bot(token=BOT_TOKEN)
    _patch_outgoing_message_methods(bot)
    dp = Dispatcher()
    try:
        dp.message.middleware(TelegramIdentitySyncMiddleware())
    except Exception:
        pass
    try:
        dp.callback_query.middleware(TelegramIdentitySyncMiddleware())
    except Exception:
        pass
    try:
        dp.callback_query.middleware(CallbackContextMiddleware())
    except Exception:
        pass
    dp.include_router(router)

    logger.info("🌐 POKROV Bot v2 starting...")

    await panel.login()
    await _configure_public_bot_menu(bot)

    # Start background expiry monitor (no traffic limits).
    asyncio.create_task(monitor_expiry(bot))
    logger.info("⏳ Expiry monitor started")
    if os.getenv("WORKER_EMBEDDED", "false").strip().lower() in {"1", "true", "yes", "on"}:
        try:
            from worker import main as worker_main

            asyncio.create_task(worker_main())
            logger.info("🧰 Embedded worker started")
        except Exception as e:
            logger.error("Failed to start embedded worker: %s", e)

    try:
        await dp.start_polling(bot)
    finally:
        await panel.close()
        await bot.session.close()
