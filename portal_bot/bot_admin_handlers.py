"""Interactive administrator panels and guarded maintenance handlers.

Loaded by the bot composition root in source order. Public symbols are
re-exported for backwards compatibility.
"""

try:
    from .module_slices import bootstrap_slice
except ImportError:
    from module_slices import bootstrap_slice

bootstrap_slice(globals())

@router.callback_query(F.data == "admin")
async def show_admin_panel(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔️ Доступ запрещён")
        return

    stats = get_stats()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 Найти юзера", callback_data="admin_search_prompt"),
            InlineKeyboardButton(text="👥 Все юзеры", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton(text="🎫 Промокоды", callback_data="admin_promos"),
            InlineKeyboardButton(text="Отзывы", callback_data="admin_reviews")
        ],
        [
            InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast_menu"),
            InlineKeyboardButton(text="🎰 Рулетка", callback_data="admin_wheel")
        ],
        [
            InlineKeyboardButton(text="📊 Групповые действия", callback_data="admin_mass"),
            InlineKeyboardButton(text="❤️ Health", callback_data="admin_health")
        ],
        [
            InlineKeyboardButton(text="Sync usernames", callback_data="admin_sync"),
            InlineKeyboardButton(text="🎁 Подарки", callback_data="admin_gift_menu")
        ],
        [
            InlineKeyboardButton(text="📰 Последние обновления", callback_data="admin_live_updates"),
            InlineKeyboardButton(text="🔗 Launch ссылки", callback_data="admin_start_links"),
        ],
        [
            InlineKeyboardButton(text="🎫 Очередь обращений", callback_data="admin_tickets"),
        ],
        [
            InlineKeyboardButton(text="Ноды", callback_data="admin_nodes"),
            InlineKeyboardButton(text="Sync Free pool", callback_data="admin_sync_free_pl"),
        ],
        [
            InlineKeyboardButton(text="🧩 Manual users", callback_data="admin_manual_menu"),
        ],
        [InlineKeyboardButton(text="Back", callback_data="back")],
    ])

    await callback.message.edit_text(
        bot_text(
            "bot.admin.stats",
            total=stats["total"],
            active=stats["active"],
            stars=stats["stars"]
        ),
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "admin_manual_menu")
async def admin_manual_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать manual user", callback_data="admin_manual_create_prompt")],
        [InlineKeyboardButton(text="📋 Список manual users", callback_data="admin_manual_list")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")],
    ])
    await callback.message.edit_text(
        "🧩 *Manual users*\n\n"
        "Создавайте пользователей без Telegram аккаунта.\n"
        "Они будут подключаться ко всем paid-нодам.",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data == "admin_manual_create_prompt")
async def admin_manual_create_prompt(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    admin_pending_actions[ADMIN_ID] = {"action": "manual_create"}
    await callback.message.edit_text(
        "➕ *Создание manual user*\n\n"
        "Отправьте: `DisplayName|days`\n"
        "Пример: `Family Router|30`",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Отмена", callback_data="admin_manual_menu")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_manual_list")
async def admin_manual_list(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    rows = list_manual_users(limit=40)
    if not rows:
        await callback.message.edit_text(
            "Manual users пока не созданы.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_manual_menu")],
            ]),
        )
        await callback.answer()
        return

    buttons: list[list[InlineKeyboardButton]] = []
    for u in rows:
        name = (u.display_name or u.email or f"manual_{abs(u.tg_id)}").strip()
        status_icon = "🧪"
        buttons.append([
            InlineKeyboardButton(text=f"{status_icon} {name} ({u.tg_id})", callback_data=f"adm_user_{u.tg_id}"),
        ])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_manual_menu")])
    await callback.message.edit_text(
        "📋 *Manual/Test users*",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()

@router.callback_query(F.data == "admin_search_prompt")
async def admin_search_prompt(callback: CallbackQuery):
    """Prompt admin to search for user"""
    if callback.from_user.id != ADMIN_ID:
        return

    admin_pending_actions[ADMIN_ID] = {"action": "search_user"}

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="admin")]
    ])

    await callback.message.edit_text(
        "🔍 *Поиск пользователя*\n\n"
        "Введи @username или tg\\_id:",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "admin_promos")
async def admin_promos_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    session = Session()
    promos = session.query(PromoCode).order_by(PromoCode.created_at.desc()).limit(20).all()
    session.close()

    if promos:
        lines = []
        for p in promos:
            type_text = f"{p.value}%" if p.promo_type == "discount" else f"+{p.value} дн."
            uses_text = "∞" if p.uses_left == -1 else str(p.uses_left)
            lines.append(f"`{p.code}` — {type_text}, ×{uses_text}")
        promo_text = "\n".join(lines)
    else:
        promo_text = "_Нет активных промокодов_"

    kb_rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="➕ Создать промокод", callback_data="admin_promo_create")],
    ]
    for p in promos[:8]:
        kb_rows.append(
            [InlineKeyboardButton(text=f"🗑 Удалить {p.code}", callback_data=f"admin_promo_delete_{p.code}")]
        )
    kb_rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin")])

    await callback.message.edit_text(
        f"🎫 *Промокоды*\n\n{promo_text}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows),
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "admin_promo_create")
async def admin_promo_create(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    admin_pending_actions[ADMIN_ID] = {"action": "admin_promo_create_form"}
    await callback.message.edit_text(
        "➕ *Создать промокод*\n\n"
        "Формат:\n"
        "`CODE|days|14|100`\n"
        "или\n"
        "`CODE|discount|20|50|2026-03-01T00:00:00`\n\n"
        "Последнее поле `expires_at` необязательное.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_promos")]]),
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_promo_delete_"))
async def admin_promo_delete(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    code = str(callback.data or "").replace("admin_promo_delete_", "", 1).strip().upper()[:20]
    if not code:
        await callback.answer("Некорректный код", show_alert=True)
        return

    s = Session()
    try:
        row = s.query(PromoCode).filter(func.upper(PromoCode.code) == code).first()
        if not row:
            await callback.answer("Промокод не найден", show_alert=True)
            return
        s.delete(row)
        s.commit()
    finally:
        s.close()
    audit_admin(ADMIN_ID, "admin_promo_delete", meta=f"code={code}")
    await admin_promos_menu(callback)

@router.callback_query(F.data == "admin_reviews")
async def admin_reviews_menu(callback: CallbackQuery):
    """Show reviews moderation"""
    if callback.from_user.id != ADMIN_ID:
        return

    session = Session()
    reviews = session.query(Review).order_by(Review.created_at.desc()).limit(5).all()
    total = session.query(Review).count()
    featured = session.query(Review).filter_by(is_featured=True).count()
    session.close()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Все отзывы", callback_data="admin_reviews_all")],
        [InlineKeyboardButton(text="На главной", callback_data="admin_reviews_featured")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")]
    ])

    await callback.message.edit_text(
        f"*Отзывы*\n\n"
        f"Всего: {total}\n"
        f"Избранных: {featured}\n\n"
        f"_Команда: /reviews_",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "admin_health")
async def admin_health_check(callback: CallbackQuery, bot: Bot):
    """Quick health check from admin panel"""
    if callback.from_user.id != ADMIN_ID:
        return

    import time
    start_time = time.time()
    status = ["✅ Бот: работает"]

    try:
        session = Session()
        user_count = session.query(User).count()
        active_count = session.query(User).filter_by(is_active=True).count()
        session.close()
        status.append(f"✅ БД: {user_count} юзеров ({active_count} активных)")
    except Exception as e:
        status.append(f"❌ БД: ошибка")

    try:
        clients = await panel.get_clients_list()
        if clients is not None:
            status.append(f"✅ Панель: {len(clients)} клиентов")
        else:
            status.append("⚠️ Панель: нет ответа")
    except:
        status.append("❌ Панель: ошибка")

    elapsed = round((time.time() - start_time) * 1000)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_health")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")]
    ])

    await callback.message.edit_text(
        f"❤️ *Health Check*\n\n" +
        "\n".join(status) +
        f"\n\n⏱️ {elapsed}мс",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "admin_broadcast_menu")
async def admin_broadcast_menu(callback: CallbackQuery):
    """Broadcast menu with custom messages and templates"""
    if callback.from_user.id != ADMIN_ID:
        return

    session = Session()
    active = session.query(User).filter_by(is_active=True).count()
    templates = session.query(Template).all()
    session.close()

    template_btns = []
    if templates:
        for t in templates[:5]:  # Show max 5 templates
            template_btns.append([InlineKeyboardButton(
                text=f"📝 {t.key}",
                callback_data=f"send_tpl_{t.key}"
            )])

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧩 Конструктор рассылки", callback_data="admin_bcast_compose")],
        [InlineKeyboardButton(text="🔄 Уведомить об обновлении", callback_data="admin_broadcast_links")],
        *template_btns,
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")]
    ])

    tpl_hint = f"\n📝 Шаблонов: {len(templates)}" if templates else "\n_Нет шаблонов_"

    await callback.message.edit_text(
        f"📢 *Рассылка*\n\n"
        f"Активных юзеров: {active}{tpl_hint}\n\n"
        f"_Сообщение одному пользователю:_ открой карточку юзера → `✉️ Сообщение`.\n\n"
        f"_Шаблоны и команды:_\n"
        f"`/template add key текст` — создать\n"
        f"`/template list` — список\n"
        f"`/template send key` — всем\n"
        f"`/template send key @user` — юзеру",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()


@router.callback_query(F.data == "admin_nodes")
async def admin_nodes(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    s = Session()
    try:
        nodes = enabled_nodes(s)
    finally:
        s.close()

    lines = ["🗺 *Ноды (enabled)*\n"]
    for n in nodes:
        code = (getattr(n, "code", "") or "").strip()
        name = (getattr(n, "name", "") or "").strip()
        host = (getattr(n, "host", "") or "").strip()
        port = int(getattr(n, "vless_port", 0) or 0)
        inb = int(getattr(n, "inbound_id", 0) or 0)
        pbase = (getattr(n, "panel_base_url", "") or "").strip()

        lines.append(f"✅ `{code}` {name} — `{host}:{port}` (inb `{inb}`)")
        if pbase:
            lines.append(f"    panel: `{pbase}`")

    free_codes = [((getattr(n, "code", "") or "").strip()) for n in nodes if node_is_free(n)]
    if free_codes:
        lines.append(f"\nFree pool: `{', '.join(free_codes)}`.")
    else:
        lines.append("\nFree pool: `not configured`.")

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_nodes")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")],
        ]
    )
    await callback.message.edit_text("\n".join(lines), reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    await callback.answer()


@router.callback_query(F.data == "admin_sync_free_pl")
async def admin_sync_free_pl(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    await callback.answer("⏳ Sync Free pool...")
    await callback.message.edit_text(
        "🆓 *Sync Free pool*\n\nЗапускаю. Это может занять 10–60 секунд.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin")]]),
        parse_mode=ParseMode.MARKDOWN,
    )

    s = Session()
    try:
        nodes = enabled_nodes(s)
        if not any(node_is_free(node) for node in nodes):
            await callback.message.edit_text(
                "🆓 *Sync Free pool*\n\n❌ Free-ноды не найдены в `nodes`.\nДобавь отдельную free-ноду (code с `free`).",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin")]]),
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        now = _utcnow()
        users = (
            s.query(User)
            .filter(func.upper(User.sub_type).in_(["FREE", "TRIAL", "BONUS"]))
            .filter(User.is_active == True)
            .filter((User.expiry_at.is_(None)) | (User.expiry_at > now))
            .order_by(User.created_at.asc())
            .all()
        )
    finally:
        s.close()

    sem = asyncio.Semaphore(6)
    passes = 2
    async def sync_one(u: User) -> bool:
        async with sem:
            sub_id = u.sub_token or str(u.tg_id)
            try:
                only_codes = _bot_resync_node_codes(u, nodes=nodes)
            except ValueError:
                return False
            res = await panel.ensure_user_on_all_nodes(
                tg_id=u.tg_id,
                client_uuid=u.uuid,
                email=u.email,
                sub_id=sub_id,
                enable=True,
                only_node_codes=only_codes,
            )
            return any(res.values())

    pending = list(users)
    ok = 0
    for attempt in range(1, passes + 1):
        if not pending:
            break
        results = await asyncio.gather(*(sync_one(u) for u in pending))
        next_pending: list[User] = []
        for u, r in zip(pending, results):
            if r:
                ok += 1
            else:
                next_pending.append(u)
        pending = next_pending
        if pending and attempt < passes:
            await asyncio.sleep(1.0)

    fail = len(pending)

    await callback.message.edit_text(
        "🆓 *Sync Free pool*\n\n"
        f"✅ OK: {ok}\n"
        f"❌ Fail: {fail}\n\n"
        "После этого Free-пользователи будут получать только выделенный free-pool после обновления подписки в приложении.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin")]]),
        parse_mode=ParseMode.MARKDOWN,
    )


async def _render_reviews_page(*, callback: CallbackQuery, featured_only: bool, page: int) -> None:
    if callback.from_user.id != ADMIN_ID:
        return

    page = max(0, int(page))
    per_page = 8
    offset = page * per_page

    session = Session()
    q = session.query(Review)
    if featured_only:
        q = q.filter_by(is_featured=True)
    total = q.count()
    rows = q.order_by(Review.created_at.desc()).offset(offset).limit(per_page).all()
    session.close()

    pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, pages - 1)

    title = "Отзывы на главной" if featured_only else "Все отзывы"
    if not rows:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Все", callback_data="admin_reviews_all:0"),
                    InlineKeyboardButton(text="На главной", callback_data="admin_reviews_featured:0"),
                ],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")],
            ]
        )
        await callback.message.edit_text(f"{title}\n\nПусто.", reply_markup=kb)
        return

    lines = [f"{title}\nВсего: {total} | Стр {page+1}/{pages}\n"]
    kb_rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(text="Все", callback_data="admin_reviews_all:0"),
            InlineKeyboardButton(text="На главной", callback_data="admin_reviews_featured:0"),
        ]
    ]

    for r in rows:
        masked = _mask_review_username(r.username)
        u = f"@{masked}" if masked != "Пользователь" else masked
        rating = f"{int(r.rating or 0)}/5"
        txt = (r.text or "").strip()
        if len(txt) > 120:
            txt = txt[:120] + "…"
        lines.append(f"ID {r.id} | {u} | оценка {rating}\n{txt or '—'}\n")
        kb_rows.append(
            [
                InlineKeyboardButton(
                    text="На сайт" if not r.is_featured else "Снять",
                    callback_data=f"review_toggle_{r.id}",
                ),
                InlineKeyboardButton(text="🗑", callback_data=f"review_delete_{r.id}"),
            ]
        )

    nav: list[InlineKeyboardButton] = []
    prefix = "admin_reviews_featured" if featured_only else "admin_reviews_all"
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"{prefix}:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{pages}", callback_data="noop"))
    if (page + 1) < pages:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"{prefix}:{page+1}"))
    kb_rows.append(nav)
    kb_rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin")])

    await callback.message.edit_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows))


@router.callback_query(F.data.startswith("admin_reviews_all"))
async def admin_reviews_all(callback: CallbackQuery):
    page = 0
    parts = (callback.data or "").split(":")
    if len(parts) >= 2 and parts[1].isdigit():
        page = int(parts[1])
    await _render_reviews_page(callback=callback, featured_only=False, page=page)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_reviews_featured"))
async def admin_reviews_featured(callback: CallbackQuery):
    page = 0
    parts = (callback.data or "").split(":")
    if len(parts) >= 2 and parts[1].isdigit():
        page = int(parts[1])
    await _render_reviews_page(callback=callback, featured_only=True, page=page)
    await callback.answer()


def _broadcast_segment_cycle(cur: str) -> str:
    order = ["active", "all", "expired", "trial"]
    try:
        i = order.index(cur)
    except ValueError:
        return "active"
    return order[(i + 1) % len(order)]


def _broadcast_segment_label(seg: str) -> str:
    return {
        "active": "Активные",
        "all": "Все",
        "expired": "Неактивные",
        "trial": "Пробные",
    }.get(seg, seg)


def _bulk_subscription_update_text() -> str:
    return (
        "🔄 *Обновление подключения*\n\n"
        "Мы обновили профиль подключения. Чтобы всё продолжило работать, откройте POKROV или кабинет и обновите профиль в приложении.\n\n"
        "Если приложение пока не под рукой, ручной вариант доступен отдельной кнопкой ниже. Открывайте его только для личного восстановления."
    )


def _bulk_subscription_update_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌐 Открыть кабинет", web_app=WebAppInfo(url=WEBAPP_URL))],
            [InlineKeyboardButton(text="🔗 Ручная ссылка / QR", callback_data="show_key")],
            [InlineKeyboardButton(text="💬 Поддержка", url=f"https://t.me/{SUPPORT_USERNAME}?start=ticket_new")],
        ]
    )


def _render_broadcast_draft(draft: dict) -> str:
    seg = _broadcast_segment_label(draft.get("segment", "active"))
    btn = draft.get("button")
    btn_txt = "нет" if not btn else f"{btn.get('text','')}"
    return (
        "📢 *Конструктор рассылки*\n\n"
        f"🎯 Аудитория: *{seg}*\n"
        f"🔗 Кнопка: *{btn_txt or 'нет'}*\n\n"
        "_Сообщение будет отправлено как копия (с сохранением форматирования/медиа)._"
    )


def _broadcast_controls(draft: dict) -> InlineKeyboardMarkup:
    seg = _broadcast_segment_label(draft.get("segment", "active"))
    btn = draft.get("button")
    btn_label = "Кнопка: нет" if not btn else f"Кнопка: {btn.get('text','')[:16]}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"🎯 {seg}", callback_data="admin_bcast_seg"),
                InlineKeyboardButton(text=f"🔗 {btn_label}", callback_data="admin_bcast_btn"),
            ],
            [
                InlineKeyboardButton(text="✅ Отправить", callback_data="admin_bcast_send"),
                InlineKeyboardButton(text="🗑 Отмена", callback_data="admin_bcast_cancel"),
            ],
        ]
    )


@router.callback_query(F.data == "admin_bcast_compose")
async def admin_bcast_compose(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    admin_pending_actions[ADMIN_ID] = {"action": "broadcast_capture"}
    admin_broadcast_drafts.pop(ADMIN_ID, None)

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_broadcast_menu")]])
    await callback.message.edit_text(
        "🧩 *Конструктор рассылки*\n\n"
        "1. Отправь сюда сообщение, которое нужно разослать.\n"
        "Можно: текст, фото, видео, документ, с форматированием.\n\n"
        "2. Я сохраню его как черновик и покажу кнопки управления.",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data == "admin_bcast_seg")
async def admin_bcast_seg(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    draft = admin_broadcast_drafts.get(ADMIN_ID)
    if not draft:
        await callback.answer("Черновик не найден. Создай рассылку заново.", show_alert=True)
        return
    draft["segment"] = _broadcast_segment_cycle(draft.get("segment", "active"))
    await callback.message.edit_text(_render_broadcast_draft(draft), reply_markup=_broadcast_controls(draft), parse_mode=ParseMode.MARKDOWN)
    await callback.answer()


@router.callback_query(F.data == "admin_bcast_btn")
async def admin_bcast_btn(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    draft = admin_broadcast_drafts.get(ADMIN_ID)
    if not draft:
        await callback.answer("Черновик не найден. Создай рассылку заново.", show_alert=True)
        return
    admin_pending_actions[ADMIN_ID] = {"action": "broadcast_set_button"}
    await callback.message.edit_text(
        "🔗 *Кнопка для рассылки*\n\n"
        "Пришли одной строкой:\n"
        "`Текст кнопки|https://example.com`\n\n"
        "Или пришли `нет`, чтобы убрать кнопку.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_broadcast_menu")]]),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data == "admin_bcast_cancel")
async def admin_bcast_cancel(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    admin_pending_actions.pop(ADMIN_ID, None)
    admin_broadcast_drafts.pop(ADMIN_ID, None)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_broadcast_menu")]])
    await callback.message.edit_text("🗑 Черновик удален.", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "admin_bcast_send")
async def admin_bcast_send(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        return
    draft = admin_broadcast_drafts.get(ADMIN_ID)
    if not draft:
        await callback.answer("Черновик не найден. Создай рассылку заново.", show_alert=True)
        return

    segment = draft.get("segment", "active")
    from_chat_id = draft.get("from_chat_id", ADMIN_ID)
    message_id = draft.get("message_id")
    if not message_id:
        await callback.answer("Черновик поврежден (нет message_id).", show_alert=True)
        return

    button = draft.get("button")
    reply_markup = None
    if button:
        try:
            reply_markup = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text=button["text"], url=button["url"])]]
            )
        except Exception:
            reply_markup = None

    s = Session()
    try:
        q = s.query(User)
        if segment == "active":
            q = q.filter_by(is_active=True)
        elif segment == "expired":
            q = q.filter_by(is_active=False)
        elif segment == "trial":
            q = q.filter(User.sub_type == "TRIAL")
        users = q.all()
    finally:
        s.close()

    total = len(users)
    await callback.message.edit_text(
        f"📤 *Рассылка запущена*\n\nАудитория: *{_broadcast_segment_label(segment)}*\nВсего: *{total}*",
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()

    sent = 0
    failed = 0
    for i, u in enumerate(users, start=1):
        if u.tg_id in PROTECTED_USERS or u.tg_id == ADMIN_ID:
            continue
        try:
            await bot.copy_message(
                chat_id=u.tg_id,
                from_chat_id=from_chat_id,
                message_id=message_id,
                reply_markup=reply_markup,
            )
            sent += 1
        except Exception:
            failed += 1
        if i % 40 == 0:
            try:
                await callback.message.edit_text(
                    f"📤 *Рассылка идет*\n\nОтправлено: *{sent}*\nОшибок: *{failed}*",
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception:
                pass
        await asyncio.sleep(0.04)

    audit_admin(ADMIN_ID, "admin_broadcast_v2", meta=f"segment={segment}; sent={sent}; failed={failed}")
    admin_broadcast_drafts.pop(ADMIN_ID, None)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_broadcast_menu")]])
    await callback.message.edit_text(
        f"✅ *Рассылка завершена*\n\nОтправлено: *{sent}*\nОшибок: *{failed}*",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
    )

@router.callback_query(F.data == "admin_custom_msg")
async def admin_custom_msg_prompt(callback: CallbackQuery):
    """Prompt for custom message with optional URL button"""
    if callback.from_user.id != ADMIN_ID:
        return

    admin_pending_actions[ADMIN_ID] = {"action": "custom_broadcast"}

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="admin_broadcast_menu")]
    ])

    await callback.message.edit_text(
        "✍️ *Кастомная рассылка*\n\n"
        "Введи текст сообщения.\n\n"
        "*Формат с кнопкой URL:*\n"
        "`Текст сообщения\n---\nТекст кнопки|https://ссылка.com`\n\n"
        "_Пример:_\n"
        "`Привет! Новое обновление!\n---\n🌐 Подробнее|https://pokrov.space/`",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "admin_broadcast_links")
async def admin_broadcast_links(callback: CallbackQuery, bot: Bot):
    """Trigger app-first subscription update notice from button."""
    if callback.from_user.id != ADMIN_ID:
        return

    await callback.answer("🔄 Рассылка уведомления запущена...")

    # Call existing broadcast logic
    session = Session()
    users = session.query(User).filter_by(is_active=True).all()
    session.close()

    sent = 0
    for user in users:
        if user.tg_id in PROTECTED_USERS or user.tg_id == ADMIN_ID:
            continue
        try:
            await bot.send_message(
                user.tg_id,
                _bulk_subscription_update_text(),
                reply_markup=_bulk_subscription_update_keyboard(),
                parse_mode=ParseMode.MARKDOWN,
            )
            sent += 1
        except:
            pass

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_broadcast_menu")]
    ])

    await callback.message.edit_text(
        f"✅ *Рассылка завершена*\n\n"
        f"Отправлено: {sent} сообщений",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )

@router.callback_query(F.data.startswith("send_tpl_"))
async def send_template_to_all(callback: CallbackQuery, bot: Bot):
    """Send template to all users from button"""
    if callback.from_user.id != ADMIN_ID:
        return

    key = callback.data.replace("send_tpl_", "")

    session = Session()
    template = session.query(Template).filter_by(key=key).first()
    users = session.query(User).filter_by(is_active=True).all()
    session.close()

    if not template:
        await callback.answer("❌ Шаблон не найден", show_alert=True)
        return

    await callback.answer(f"📤 Отправка шаблона '{key}'...")

    sent = 0
    for user in users:
        if user.tg_id in PROTECTED_USERS or user.tg_id == ADMIN_ID:
            continue
        try:
            await bot.send_message(user.tg_id, template.text, parse_mode=ParseMode.MARKDOWN)
            sent += 1
        except:
            pass

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_broadcast_menu")]
    ])

    await callback.message.edit_text(
        f"✅ *Шаблон '{key}' отправлен*\n\n"
        f"Получили: {sent} юзеров",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )

# ==========================================
#         WHEEL SETTINGS
# ==========================================

@router.callback_query(F.data == "admin_wheel")
async def admin_wheel_settings(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    cfg = _load_wheel_config()
    outcomes = list(cfg.get("outcomes") or [])
    cooldown_hours = int(cfg.get("cooldown_hours") or WHEEL_DEFAULT_COOLDOWN_HOURS)
    cooldown_days = _cooldown_days_from_hours(cooldown_hours)
    preset = str(cfg.get("preset") or "invalid")
    total_weight = sum(weight for _, _, weight in outcomes) or 1
    prizes_text = []
    for kind, value, weight in outcomes:
        pct = (weight / total_weight) * 100
        label = f"{value} дней" if kind == "days" else f"скидка {value}%"
        prizes_text.append(f"• {label} — {weight}/10000 ({pct:.2f}%)")
    if preset == "invalid":
        prizes_text = ["⚠️ Сохранённая конфигурация не прошла валидацию."]

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")],
        ]
    )

    await callback.message.edit_text(
        "🎰 <b>Настройки рулетки</b>\n\n"
        + f"<b>Preset:</b> {html.escape(preset)}\n\n"
        "<b>Шансы выигрыша:</b>\n"
        + "\n".join(prizes_text)
        + "\n\n"
        + f"<b>Кулдаун:</b> {cooldown_days} дней ({cooldown_hours}ч)\n"
        + "Конфигурация фиксирована контрактом PAID_WEEKLY_DISCOUNTS_V2.",
        reply_markup=kb,
        parse_mode=ParseMode.HTML,
    )
    await callback.answer()


def _live_update_public_link(row: LiveUpdate) -> str:
    channel = str(getattr(row, "channel_username", "") or "").strip().lstrip("@")
    post_id = int(getattr(row, "post_id", 0) or 0)
    if channel and post_id > 0:
        return f"https://t.me/{channel}/{post_id}"
    return str(getattr(row, "link", "") or "").strip()


@router.callback_query(F.data == "admin_live_updates")
async def admin_live_updates_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    s = Session()
    try:
        rows = (
            s.query(LiveUpdate)
            .order_by(LiveUpdate.sort_order.asc(), LiveUpdate.id.desc())
            .limit(15)
            .all()
        )
    finally:
        s.close()

    lines = ["📰 *Последние обновления*\n"]
    kb_rows: list[list[InlineKeyboardButton]] = []
    if not rows:
        lines.append("_Пока пусто_")
    for row in rows:
        status = "🟢" if bool(getattr(row, "is_active", False)) else "⚪"
        lines.append(
            f"{status} `{int(row.id)}` {row.title}\n"
            f"↳ {(_live_update_public_link(row) or '—')}"
        )
        kb_rows.append(
            [
                InlineKeyboardButton(
                    text=f"{'Выключить' if bool(row.is_active) else 'Включить'} #{int(row.id)}",
                    callback_data=f"admin_live_toggle_{int(row.id)}",
                )
            ]
        )

    kb_rows.extend(
        [
            [InlineKeyboardButton(text="➕ Добавить обновление", callback_data="admin_live_create")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")],
        ]
    )
    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data == "admin_live_create")
async def admin_live_create_prompt(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    admin_pending_actions[ADMIN_ID] = {"action": "admin_live_create"}
    await callback.message.edit_text(
        "➕ *Новое обновление*\n\n"
        "Формат:\n"
        "`Заголовок|Краткое описание|@channel|123`\n\n"
        "Либо legacy-формат:\n"
        "`Заголовок|Краткое описание|https://t.me/...`",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_live_updates")]]),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_live_toggle_"))
async def admin_live_toggle(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    raw_id = str(callback.data or "").replace("admin_live_toggle_", "", 1)
    try:
        update_id = int(raw_id)
    except Exception:
        await callback.answer("Некорректный id", show_alert=True)
        return

    s = Session()
    try:
        row = s.query(LiveUpdate).filter(LiveUpdate.id == update_id).first()
        if not row:
            await callback.answer("Обновление не найдено", show_alert=True)
            return
        row.is_active = not bool(row.is_active)
        row.updated_at = _utcnow()
        s.commit()
    finally:
        s.close()
    await admin_live_updates_menu(callback)


@router.callback_query(F.data == "admin_start_links")
async def admin_start_links_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    s = Session()
    try:
        rows = s.query(StartLink).order_by(StartLink.updated_at.desc(), StartLink.id.desc()).limit(20).all()
    finally:
        s.close()

    bot_username = (BOT_USERNAME or "pokrov_vpnbot").lstrip("@")
    lines = ["🔗 *Launch ссылки*\n"]
    kb_rows: list[list[InlineKeyboardButton]] = []
    if not rows:
        lines.append("_Пока пусто_")
    for row in rows:
        code = str(getattr(row, "code", "") or "").strip()
        state = "🟢" if bool(getattr(row, "is_active", False)) else "⚪"
        target = str(getattr(row, "target_action", "") or "").strip() or "—"
        lines.append(
            f"{state} `{int(row.id)}` `{code}` → `{target}`\n"
            f"↳ https://t.me/{bot_username}?start={code}"
        )
        kb_rows.append(
            [
                InlineKeyboardButton(
                    text=f"{'Деактивировать' if bool(row.is_active) else 'Активировать'} {code}",
                    callback_data=f"admin_start_toggle_{int(row.id)}",
                ),
                InlineKeyboardButton(
                    text=f"✏️ Изменить {code}",
                    callback_data=f"admin_start_edit_{int(row.id)}",
                ),
            ]
        )

    kb_rows.extend(
        [
            [InlineKeyboardButton(text="➕ Создать launch-ссылку", callback_data="admin_start_create")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")],
        ]
    )
    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data == "admin_start_create")
async def admin_start_create_prompt(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    admin_pending_actions[ADMIN_ID] = {"action": "admin_start_create"}
    await callback.message.edit_text(
        "➕ *Создать launch-ссылку*\n\n"
        "Формат:\n"
        "`code|Описание|target_action`\n\n"
        "Примеры `target_action`:\n"
        "• `opening_bonus`\n"
        "• `promo:WELCOME14`\n"
        "• `campaign:launch_week_1`\n"
        "• `campaign_promo:launch_week_1:WELCOME14`",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_start_links")]]),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_start_edit_"))
async def admin_start_edit_prompt(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    raw_id = str(callback.data or "").replace("admin_start_edit_", "", 1)
    try:
        link_id = int(raw_id)
    except Exception:
        await callback.answer("Некорректный id", show_alert=True)
        return

    s = Session()
    try:
        row = s.query(StartLink).filter(StartLink.id == link_id).first()
        if not row:
            await callback.answer("Ссылка не найдена", show_alert=True)
            return
        code = str(getattr(row, "code", "") or "").strip()
        description = str(getattr(row, "description", "") or "").strip()
        target_action = str(getattr(row, "target_action", "") or "").strip()
    finally:
        s.close()

    admin_pending_actions[ADMIN_ID] = {"action": "admin_start_edit", "link_id": link_id}
    await callback.message.edit_text(
        "✏️ *Редактировать launch-ссылку*\n\n"
        f"Текущие значения:\n`{code}|{description}|{target_action}`\n\n"
        "Новый формат:\n"
        "`code|Описание|target_action`",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_start_links")]]),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_start_toggle_"))
async def admin_start_toggle(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    raw_id = str(callback.data or "").replace("admin_start_toggle_", "", 1)
    try:
        link_id = int(raw_id)
    except Exception:
        await callback.answer("Некорректный id", show_alert=True)
        return

    s = Session()
    try:
        row = s.query(StartLink).filter(StartLink.id == link_id).first()
        if not row:
            await callback.answer("Ссылка не найдена", show_alert=True)
            return
        row.is_active = not bool(row.is_active)
        row.updated_at = _utcnow()
        s.commit()
    finally:
        s.close()
    await admin_start_links_menu(callback)

# ==========================================
#         MASS ACTIONS
# ==========================================

@router.callback_query(F.data == "admin_mass")
async def admin_mass_actions(callback: CallbackQuery):
    """Show grouped bulk actions menu with explicit target counts."""
    if callback.from_user.id != ADMIN_ID:
        return

    session = Session()
    total = session.query(User).count()
    now = _utcnow()
    active = (
        session.query(User)
        .filter(User.is_active == True)
        .filter(User.expiry_at.isnot(None))
        .filter(User.expiry_at > now)
        .count()
    )
    inactive = total - active
    plan_rows = session.query(User.sub_type, func.count(User.tg_id)).group_by(User.sub_type).all()

    # Find users with expiring subscriptions (within 3 days)
    soon = now + timedelta(days=3)
    expiring = session.query(User).filter(
        User.is_active == True,
        User.expiry_at <= soon,
        User.expiry_at > now
    ).count()
    session.close()

    plan_lines = []
    for st, cnt in sorted(plan_rows, key=lambda x: str(x[0] or "")):
        plan_lines.append(f"• `{(st or '—')}`: {cnt}")
    plans_txt = "\n".join(plan_lines) if plan_lines else "—"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить дни активным", callback_data="mass_extend_active"),
            InlineKeyboardButton(text=f"📨 Отправить напоминание ({expiring})", callback_data="mass_remind_expiring"),
        ],
        [
            InlineKeyboardButton(text="🎁 +14 дней сегменту", callback_data="mass_promo_14"),
            InlineKeyboardButton(text="🔄 Синхронизировать с нодами", callback_data="mass_sync_nodes"),
        ],
        [InlineKeyboardButton(text="🧹 Нормализовать сегменты", callback_data="mass_normalize_plans")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")]
    ])

    await callback.message.edit_text(
        f"📊 *Групповые действия*\n\n"
        f"Всего: {total}\n"
        f"✅ Активных сейчас: {active}\n"
        f"❌ Неактивных: {inactive}\n"
        f"⏳ Истекает в 3 дня: {expiring}\n\n"
        f"*Планы в БД:*\n{plans_txt}",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "mass_addgb_active")
async def mass_addgb_prompt(callback: CallbackQuery):
    """Legacy placeholder: traffic limits are not used."""
    if callback.from_user.id != ADMIN_ID:
        return

    await callback.answer("Лимиты по трафику не используются.", show_alert=True)

@router.callback_query(F.data == "mass_extend_active")
async def mass_extend_prompt(callback: CallbackQuery):
    """Prompt for mass extend"""
    if callback.from_user.id != ADMIN_ID:
        return

    admin_pending_actions[ADMIN_ID] = {"action": "mass_extend"}

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="admin_mass")]
    ])

    await callback.message.edit_text(
        "📅 *Продлить всем активным*\n\n"
        "Введи количество дней:",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "mass_remind_expiring")
async def mass_remind_expiring(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        return

    session = Session()
    now = _utcnow()
    soon = now + timedelta(days=3)
    try:
        users = session.query(User).filter(
            User.is_active == True,
            User.expiry_at <= soon,
            User.expiry_at > now
        ).all()
    finally:
        session.close()

    target = [u for u in users if u.tg_id not in PROTECTED_USERS and u.tg_id != ADMIN_ID]
    await callback.message.edit_text(
        f"⚠️ *Подтверждение действия*\n\n"
        f"Отправить напоминание об истечении.\n"
        f"Будет затронуто: *{len(target)}* пользователей.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=_bulk_confirm_kb("mass_remind_expiring_run"),
    )
    await callback.answer()


@router.callback_query(F.data == "mass_remind_expiring_run")
async def mass_remind_expiring_run(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        return

    await callback.answer("📤 Отправка...")

    session = Session()
    now = _utcnow()
    soon = now + timedelta(days=3)
    try:
        users = session.query(User).filter(
            User.is_active == True,
            User.expiry_at <= soon,
            User.expiry_at > now
        ).all()
    finally:
        session.close()

    sent = 0
    for user in users:
        if user.tg_id in PROTECTED_USERS or user.tg_id == ADMIN_ID:
            continue
        try:
            expiry = _naive_utc(user.expiry_at)
            days_left = (expiry - now).days if expiry and expiry > now else 0
            await bot.send_message(
                user.tg_id,
                f"⚠️ *Подписка истекает!*\n\n"
                f"Осталось {days_left} дней.\n\n"
                f"Продли сейчас, чтобы не потерять доступ!",
                parse_mode=ParseMode.MARKDOWN
            )
            sent += 1
        except:
            pass

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_mass")]
    ])

    await callback.message.edit_text(
        f"✅ *Готово*\n\n"
        f"Напоминание отправлено: *{sent}* пользователей.",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )


@router.callback_query(F.data == "mass_normalize_plans")
async def mass_normalize_plans(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    s = Session()
    try:
        users = s.query(User).order_by(User.created_at.asc()).all()
        preview_count = sum(
            1
            for u in users
            if u.tg_id not in PROTECTED_USERS
            and u.tg_id != ADMIN_ID
            and _normalize_sub_type((u.sub_type or "").strip()) != (u.sub_type or "").strip()
        )
    finally:
        s.close()

    if preview_count > 0:
        await callback.message.edit_text(
            f"⚠️ *Подтверждение действия*\n\n"
            f"Нормализовать сегменты (`sub_type`) по правилам.\n"
            f"Будет затронуто: *{preview_count}* пользователей.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=_bulk_confirm_kb("mass_normalize_plans_run"),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "ℹ️ Нечего нормализовать: все сегменты уже в консистентном формате.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_mass")]]),
    )
    await callback.answer()


@router.callback_query(F.data == "mass_normalize_plans_run")
async def mass_normalize_plans_run(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    await callback.answer("⏳ Выполняю...")
    s = Session()
    try:
        users = s.query(User).order_by(User.created_at.asc()).all()
        changed = 0
        by_to: dict[tuple[str, str], int] = {}
        for u in users:
            if u.tg_id in PROTECTED_USERS or u.tg_id == ADMIN_ID:
                continue
            old = (u.sub_type or "").strip()
            new = _normalize_sub_type(old)
            if new and new != old:
                u.sub_type = new
                changed += 1
                key = (old or "—", new)
                by_to[key] = by_to.get(key, 0) + 1
        s.commit()
    finally:
        s.close()

    lines = ["🧹 *Нормализация сегментов*\n", f"Изменено: *{changed}*"]
    if by_to:
        lines.append("\n*Что поменялось:*")
        for (old, new), cnt in sorted(by_to.items(), key=lambda x: (-x[1], x[0][0], x[0][1]))[:12]:
            lines.append(f"• `{old}` → `{new}`: {cnt}")

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_mass")]])
    await callback.message.edit_text("\n".join(lines), reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    await callback.answer()


@router.callback_query(F.data == "mass_promo_14")
async def mass_promo_14(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    s = Session()
    try:
        users = s.query(User).order_by(User.created_at.asc()).all()
        target_count = sum(
            1
            for u in users
            if u.tg_id not in PROTECTED_USERS
            and u.tg_id != ADMIN_ID
            and _normalize_sub_type((u.sub_type or "").strip()) != "MANUAL"
        )
    finally:
        s.close()

    await callback.message.edit_text(
        f"⚠️ *Подтверждение действия*\n\n"
        f"Добавить +14 дней сегменту (кроме MANUAL).\n"
        f"Будет затронуто: *{target_count}* пользователей.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=_bulk_confirm_kb("mass_promo_14_run"),
    )
    await callback.answer()


@router.callback_query(F.data == "mass_promo_14_run")
async def mass_promo_14_run(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    await callback.answer("🎁 Выполняю...")
    await callback.message.edit_text(
        "🎁 *Промо: +14 дней сегменту*\n\n"
        "Обновляю БД и синхронизирую пользователей на ноды. Это может занять 10–60 секунд.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_mass")]]),
        parse_mode=ParseMode.MARKDOWN,
    )

    now = _utcnow()
    new_expiry = now + timedelta(days=14)

    s = Session()
    try:
        users = s.query(User).order_by(User.created_at.asc()).all()
        target: list[User] = []
        for u in users:
            st = (u.sub_type or "").strip()
            if _normalize_sub_type(st) == "MANUAL":
                continue
            if u.tg_id in PROTECTED_USERS or u.tg_id == ADMIN_ID:
                continue
            u.is_active = True
            u.expiry_at = new_expiry
            u.sub_type = "BONUS"
            target.append(u)
        s.commit()
    finally:
        s.close()

    # Sync to paid nodes (exclude free nodes by ControlPanel default).
    ok_total = 0
    fail_total = 0
    sem = asyncio.Semaphore(6)

    async def sync_one(u: User) -> bool:
        async with sem:
            try:
                sub_id = u.sub_token or str(u.tg_id)
                res = await panel.ensure_user_on_all_nodes(
                    tg_id=u.tg_id,
                    client_uuid=u.uuid,
                    email=u.email,
                    sub_id=sub_id,
                    enable=True,
                )
                return all(res.values()) if res else False
            except Exception:
                return False

    # We need fresh objects after session close. Re-query minimal fields.
    s = Session()
    try:
        rows = (
            s.query(User)
            .filter(func.upper(User.sub_type).in_(["PAID", "BONUS", "TRIAL", "FREE"]))
            .filter(User.tg_id != ADMIN_ID)
            .order_by(User.created_at.asc())
            .all()
        )
    finally:
        s.close()

    results = await asyncio.gather(*(sync_one(u) for u in rows))
    ok_total = sum(1 for r in results if r)
    fail_total = sum(1 for r in results if not r)

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_mass")]])
    await callback.message.edit_text(
        "🎁 *Промо: +14 дней сегменту*\n\n"
        f"БД обновлена до: `{new_expiry.strftime('%Y-%m-%d')}`\n"
        f"✅ Sync OK: {ok_total}\n"
        f"❌ Sync Fail: {fail_total}\n"
        f"Сегмент после операции: `BONUS`",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
    )


@router.callback_query(F.data == "mass_sync_nodes")
async def mass_sync_nodes(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    s = Session()
    try:
        users = s.query(User).order_by(User.created_at.asc()).all()
    finally:
        s.close()
    target_count = sum(1 for u in users if u.tg_id not in PROTECTED_USERS and u.tg_id != ADMIN_ID)

    await callback.message.edit_text(
        f"⚠️ *Подтверждение действия*\n\n"
        f"Синхронизировать сегмент с нодами.\n"
        f"Будет затронуто: *{target_count}* пользователей.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=_bulk_confirm_kb("mass_sync_nodes_run"),
    )
    await callback.answer()


@router.callback_query(F.data == "mass_sync_nodes_run")
async def mass_sync_nodes_run(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    await callback.answer("🔄 Sync...")
    await callback.message.edit_text(
        "🔄 *Синхронизация пользователей с нодами*\n\nЗапускаю. Это может занять 10–60 секунд.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_mass")]]),
        parse_mode=ParseMode.MARKDOWN,
    )

    now = _utcnow()
    s = Session()
    try:
        users = s.query(User).order_by(User.created_at.asc()).all()
    finally:
        s.close()

    sem = asyncio.Semaphore(6)

    async def sync_one(u: User) -> bool:
        async with sem:
            try:
                st = _normalize_sub_type(u.sub_type)
                if st == "MANUAL":
                    return True
                expiry = _naive_utc(u.expiry_at)
                enable = bool(u.is_active and expiry and expiry > now)
                sub_id = u.sub_token or str(u.tg_id)
                try:
                    only_codes = _bot_resync_node_codes(u)
                except ValueError:
                    return False
                res = await panel.ensure_user_on_all_nodes(
                    tg_id=u.tg_id,
                    client_uuid=u.uuid,
                    email=u.email,
                    sub_id=sub_id,
                    enable=enable,
                    only_node_codes=only_codes,
                )
                return all(res.values()) if res else False
            except Exception:
                return False

    target = [u for u in users if u.tg_id not in PROTECTED_USERS and u.tg_id != ADMIN_ID]
    results = await asyncio.gather(*(sync_one(u) for u in target))
    ok = sum(1 for r in results if r)
    fail = sum(1 for r in results if not r)

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_mass")]])
    await callback.message.edit_text(
        "🔄 *Синхронизация пользователей с нодами*\n\n"
        f"✅ OK: {ok}\n"
        f"❌ Fail: {fail}",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
    )

@router.callback_query(F.data == "admin_sync")
async def admin_sync_callback(callback: CallbackQuery, bot: Bot):
    """Trigger sync from button"""
    if callback.from_user.id != ADMIN_ID:
        return

    await callback.answer("🔄 Синхронизация запущена...")

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
    for tg_id in sorted(tg_ids):
        try:
            chat = await bot.get_chat(tg_id)
            if sync_telegram_identity(tg_id, getattr(chat, "username", None)):
                updated += 1
        except Exception:
            pass

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")]
    ])

    await callback.message.edit_text(
        f"✅ *Синхронизация завершена*\n\n"
        f"Обновлено: {updated} username'ов",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )

@router.callback_query(F.data.startswith("admin_users"))
async def show_admin_users(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔️ Доступ запрещён")
        return

    page = 0
    segment = "all"  # all|active|expired|blocked|manual_test
    parts = (callback.data or "").split(":")
    if len(parts) >= 2 and parts[1].isdigit():
        page = max(0, int(parts[1]))
    if len(parts) >= 3 and parts[2]:
        segment = parts[2]
    if segment == "manual":
        segment = "manual_test"
    if segment == "inactive":
        segment = "expired"
    if segment not in {"all", "active", "expired", "blocked", "manual_test"}:
        segment = "all"

    segment_labels = {
        "all": "Все",
        "active": "Active",
        "expired": "Expired",
        "blocked": "Blocked",
        "manual_test": "Manual/Test",
    }
    segment_buttons = [
        [
            InlineKeyboardButton(text="Все", callback_data="admin_users:0:all"),
            InlineKeyboardButton(text="Active", callback_data="admin_users:0:active"),
            InlineKeyboardButton(text="Expired", callback_data="admin_users:0:expired"),
        ],
        [
            InlineKeyboardButton(text="Blocked", callback_data="admin_users:0:blocked"),
            InlineKeyboardButton(text="Manual/Test", callback_data="admin_users:0:manual_test"),
        ],
    ]

    now = _utcnow()
    per_page = 12
    offset = page * per_page

    session = Session()
    try:
        q = session.query(User)
        if segment == "active":
            q = q.filter(User.is_active == True).filter(User.expiry_at.isnot(None)).filter(User.expiry_at > now)
        elif segment == "expired":
            q = q.filter((User.expiry_at.is_(None)) | (User.expiry_at <= now))
            q = q.filter(~((User.tg_id < 0) | (func.upper(User.sub_type) == "MANUAL") | (User.is_manual == True)))
        elif segment == "blocked":
            q = q.filter(User.is_active == False).filter(User.expiry_at.isnot(None)).filter(User.expiry_at > now)
        elif segment == "manual_test":
            q = q.filter((User.tg_id < 0) | (func.upper(User.sub_type) == "MANUAL") | (User.is_manual == True))

        total = q.count()
        users = q.order_by(User.created_at.desc()).offset(offset).limit(per_page).all()
    finally:
        session.close()

    pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, pages - 1)

    if not users:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                *segment_buttons,
                [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")],
            ]
        )
        await callback.message.edit_text(
            "👥 Пользователи\n\n"
            "Telegram admin работает как safe fallback. "
            "Для выбранного статуса пользователей пока нет.",
            reply_markup=kb,
        )
        await callback.answer()
        return

    header = (
        f"👥 <b>Пользователи</b> — {html.escape(segment_labels.get(segment, 'Все'))}\n"
        f"Всего: {total} | Стр. {page+1}/{pages}\n"
        "Telegram admin: safe fallback, destructive cleanup только для manual/test.\n\n"
    )

    lines: list[str] = []
    buttons: list[list[InlineKeyboardButton]] = list(segment_buttons)
    for u in users:
        expiry = _naive_utc(u.expiry_at)
        effective_status = _admin_user_effective_status(u, now=now)
        status_label = _admin_user_status_label(effective_status)
        origin_label = _admin_user_origin_label(u)
        uname = f"@{u.username}" if u.username else f"ID:{u.tg_id}"
        days_left = (expiry - now).days if expiry and expiry > now else 0
        expiry_txt = expiry.strftime("%d.%m.%Y") if expiry else "—"
        plan = (u.sub_type or "—").upper()
        lines.append(
            f"{html.escape(status_label)} {html.escape(uname)} — "
            f"{html.escape(origin_label)} — до {html.escape(expiry_txt)} "
            f"({days_left} дн.) — {html.escape(plan)}"
        )

        status_icon = {
            "active": "✅",
            "expired": "⌛",
            "blocked": "⛔",
            "manual_test": "🧪",
        }.get(effective_status, "⌛")
        label = f"{status_icon} @{u.username}" if u.username else f"{status_icon} {u.tg_id}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"adm_user_{u.tg_id}")])

    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"admin_users:{page-1}:{segment}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{pages}", callback_data="noop"))
    if (page + 1) < pages:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"admin_users:{page+1}:{segment}"))
    buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin")])

    await callback.message.edit_text(
        header + "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode=ParseMode.HTML,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("wheel_preset_"))
async def admin_wheel_set_preset(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer("Preset фиксирован: PAID_WEEKLY_DISCOUNTS_V2.", show_alert=True)


@router.callback_query(F.data == "wheel_weights")
async def admin_wheel_set_weights_prompt(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer("Ручные веса отключены контрактом PAID_WEEKLY_DISCOUNTS_V2.", show_alert=True)


@router.callback_query(F.data.startswith("mass_extend_run_"))
async def mass_extend_run(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    raw_days = str(callback.data or "").replace("mass_extend_run_", "", 1).strip()
    try:
        days = int(raw_days)
    except Exception:
        await callback.answer("Некорректное число дней", show_alert=True)
        return
    if days < 1 or days > 3650:
        await callback.answer("Диапазон 1..3650", show_alert=True)
        return

    await callback.answer("⏳ Выполняю...")
    session = Session()
    now = _utcnow()
    try:
        users = (
            session.query(User)
            .filter(User.is_active == True)
            .filter(User.expiry_at.isnot(None))
            .filter(User.expiry_at > now)
            .all()
        )
        count = 0
        for user in users:
            if user.tg_id in PROTECTED_USERS or user.tg_id == ADMIN_ID:
                continue
            expiry = _naive_utc(user.expiry_at) or now
            user.expiry_at = expiry + timedelta(days=days)
            count += 1
        session.commit()
    finally:
        session.close()

    await callback.message.edit_text(
        f"✅ *Готово*\n\n"
        f"Добавлено по *{days}* дней.\n"
        f"Затронуто пользователей: *{count}*.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_mass")]]),
    )


def _bulk_confirm_kb(confirm_cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data=confirm_cb)],
            [InlineKeyboardButton(text="◀️ Отмена", callback_data="admin_mass")],
        ]
    )


@router.callback_query(F.data == "wheel_cd")
async def admin_wheel_set_cooldown_prompt(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer("Кулдаун фиксирован: 7 дней.", show_alert=True)

@router.callback_query(F.data.startswith("adm_user_"))
async def admin_view_user(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔️ Доступ запрещён")
        return

    tg_id = int(callback.data.replace("adm_user_", ""))
    await render_admin_user_view(callback, tg_id)

@router.callback_query(F.data.startswith("adm_add_days_"))
async def admin_add_days(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    parts = callback.data.split("_")
    tg_id = int(parts[3])
    days = int(parts[4])

    extend_user(tg_id, days, 0)
    if days >= 0:
        await callback.answer(f"✅ Добавлено {days} дней!")
    else:
        await callback.answer(f"✅ Списано {abs(days)} дней.")

    # Refresh user view - re-render directly
    await render_admin_user_view(callback, tg_id)

@router.callback_query(F.data.startswith("adm_add_gb_"))
async def admin_add_gb(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    parts = callback.data.split("_")
    tg_id = int(parts[3])
    gb = int(parts[4])

    user = get_user(tg_id)
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return

    # Keep handler for backward compatibility; policy is managed by plan/env.
    await panel.update_client_traffic(tg_id, 0)
    await callback.answer("ℹ️ Управление трафиком через эту кнопку отключено.", show_alert=True)

    # Refresh user view - re-render directly
    await render_admin_user_view(callback, tg_id)

@router.callback_query(F.data.startswith("adm_sub_gb_"))
async def admin_sub_gb(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    parts = callback.data.split("_")
    tg_id = int(parts[3])
    gb = int(parts[4])

    user = get_user(tg_id)
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return

    await panel.subtract_client_traffic(tg_id, 0)
    await callback.answer("ℹ️ Управление трафиком через эту кнопку отключено.", show_alert=True)

    # Refresh user view
    await render_admin_user_view(callback, tg_id)

@router.callback_query(F.data.startswith("adm_toggle_"))
async def admin_toggle_user(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    tg_id = int(callback.data.replace("adm_toggle_", ""))
    user = get_user(tg_id)

    if not user:
        await callback.answer("❌ Пользователь не найден")
        return

    # Toggle status
    new_status = not user.is_active
    session = Session()
    db_user = session.query(User).filter_by(tg_id=tg_id).first()
    if db_user:
        db_user.is_active = new_status
        session.commit()
    session.close()

    # Toggle in panel
    await panel.enable_client(user.uuid, new_status)
    audit_admin(callback.from_user.id, "toggle_user", tg_id, meta=f"new_status={int(new_status)}")

    status_text = "активирован" if new_status else "отключен"
    await callback.answer(f"✅ Пользователь {status_text}!")

    # Refresh user view - re-render directly
    await render_admin_user_view(callback, tg_id)


@router.callback_query(F.data.startswith("adm_sync_nodes_"))
async def admin_sync_user_nodes(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    tg_id = int((callback.data or "").replace("adm_sync_nodes_", ""))
    s = Session()
    try:
        u = s.query(User).filter_by(tg_id=tg_id).first()
    finally:
        s.close()

    if not u:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    sub_id = u.sub_token or str(u.tg_id)
    try:
        only_codes = _bot_resync_node_codes(u)
    except ValueError:
        await callback.answer("❌ Переход free-профиля ещё не завершён", show_alert=True)
        return
    try:
        res = await panel.ensure_user_on_all_nodes(
            tg_id=u.tg_id,
            client_uuid=u.uuid,
            email=u.email,
            sub_id=sub_id,
            enable=bool(u.is_active),
            only_node_codes=only_codes,
        )
        ok = sum(1 for v in res.values() if v)
        fail = sum(1 for v in res.values() if not v)
        await callback.answer(f"🔁 Sync: OK {ok}, fail {fail}")
    except Exception:
        await callback.answer("❌ Ошибка sync (см. логи)", show_alert=True)

    await render_admin_user_view(callback, tg_id)


@router.callback_query(F.data.startswith("adm_send_link_"))
async def admin_send_user_link(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        return

    tg_id = int((callback.data or "").replace("adm_send_link_", ""))
    u = get_user(tg_id)
    if not u:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    try:
        sub_link = build_subscription_link(tg_id)
        await bot.send_message(
            tg_id,
            "🔗 *Ваша ссылка подписки*\n\n"
            f"`{sub_link}`\n\n"
            "_Если приложение просит обновить профиль, просто обновите подписку внутри приложения._",
            parse_mode=ParseMode.MARKDOWN,
        )
        await callback.answer("📨 Отправлено")
    except Exception:
        await callback.answer("❌ Не удалось отправить (юзер заблокировал?)", show_alert=True)

    await render_admin_user_view(callback, tg_id)


@router.callback_query(F.data.startswith("adm_regen_token_"))
async def admin_regen_token(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    tg_id = int((callback.data or "").replace("adm_regen_token_", ""))
    token = regenerate_user_sub_token(tg_id)
    if not token:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    panel_sync_ok = await sync_user_panel_sub_token(tg_id)
    link = build_subscription_link(tg_id)
    audit_admin(callback.from_user.id, "regen_sub_token", tg_id)
    await callback.answer("♻️ Токен перевыпущен")
    await callback.message.answer(
        f"♻️ Новый ключ пользователя `{tg_id}`:\n`{link}`\n\n"
        f"Sync с нодами: {'OK' if panel_sync_ok else 'WARN (проверьте adm_sync_nodes)'}",
        parse_mode=ParseMode.MARKDOWN,
    )
    await render_admin_user_view(callback, tg_id)


@router.callback_query(F.data.startswith("adm_msg_user_"))
async def admin_message_user_prompt(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    tg_id = int((callback.data or "").replace("adm_msg_user_", ""))
    u = get_user(tg_id)
    if not u:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    admin_pending_actions[ADMIN_ID] = {"action": "admin_dm_capture", "target_tg_id": tg_id}
    await callback.message.edit_text(
        f"✉️ *Сообщение пользователю* `{tg_id}`\n\n"
        "Отправь следующим сообщением текст, фото, видео или документ.\n"
        "Я перешлю его пользователю как есть.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="◀️ Отмена", callback_data=f"adm_user_{tg_id}")]]
        ),
    )
    await callback.answer()


@router.callback_query(F.data == "mode_pro")
async def mode_pro_start(callback: CallbackQuery):
    tg_id = callback.from_user.id
    user = get_user(tg_id)
    if _channel_bonus_eligible(tg_id=tg_id, user=user):
        await _show_channel_bonus_offer(callback, next_action="main")
        return

    await _edit_rich_copy(
        callback=callback,
        copy=home_copy(show_trial=_trial_offer_available(user)),
        rows=main_keyboard_specs(tg_id),
    )
    await callback.answer("Открываю действия", show_alert=False)


@router.callback_query(F.data == "mode_simple")
async def mode_simple_start(callback: CallbackQuery):
    """Compatibility entrypoint for the old simple-mode callback."""
    await _render_device_select(callback)


@router.callback_query(F.data.in_({"simple_ios", "simple_android", "simple_pc", "simple_win"}))
async def mode_simple_step2(callback: CallbackQuery):
    platform = {
        "simple_ios": "ios",
        "simple_android": "android",
        "simple_pc": "win",
        "simple_win": "win",
    }.get(callback.data or "", "android")
    await _render_platform_screen(callback, platform)


@router.callback_query(F.data == "simple_step3")
async def mode_simple_step3(callback: CallbackQuery):
    tg_id = callback.from_user.id
    user = get_user(tg_id)
    if _channel_bonus_eligible(tg_id=tg_id, user=user):
        await _show_channel_bonus_offer(callback, next_action="simple")
        return
    await _render_mode_simple_step3(callback)


async def _render_mode_simple_step3(callback: CallbackQuery) -> None:
    starter_price = int(TARIFFS["1_month"]["stars"])
    recommended_price = int(TARIFFS["6_months"]["stars"])
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Попробовать VPN бесплатно", callback_data="trial_direct")],
        [InlineKeyboardButton(text=f"💎 6 месяцев · {recommended_price} ₽", callback_data="buy_6_months")],
        [InlineKeyboardButton(text=f"🚀 1 месяц · {starter_price} ₽", callback_data="buy_1_month")],
        [InlineKeyboardButton(text="Сравнить все планы", callback_data="charge")],
        [InlineKeyboardButton(text=f"🎁 Ещё {CHANNEL_PREMIUM_DAYS} дней за Telegram", callback_data="bonus_offer_trial")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="instruction")],
    ])
    await callback.message.edit_text(
        bot_text("bot.instruction.step_access"),
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


async def _activate_trial_tariff(
    callback: CallbackQuery,
    bot: Bot,
    *,
    retry_callback_data: str = "buy_trial",
) -> None:
    del bot, retry_callback_data
    await callback.message.edit_text(
        "🔥 *Ваши 5 бесплатных дней ждут в POKROV*\n\n"
        "Установите приложение, войдите в аккаунт и подключитесь. Бесплатный доступ включится один раз "
        "после первого подтверждённого соединения — карта не нужна.\n\n"
        f"Хотите больше времени на проверку? После подписки на канал заберите ещё {CHANNEL_PREMIUM_DAYS} дней.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🚀 Скачать POKROV", callback_data="instruction")],
                [InlineKeyboardButton(text="💳 Выбрать тариф от 99 ₽", callback_data="charge")],
                [InlineKeyboardButton(text="◀️ В меню", callback_data="back")],
            ]
        ),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


def _parse_bonus_next_action(data: str, prefix: str) -> str | None:
    raw = (data or "").replace(prefix, "", 1).strip().lower()
    if raw in {"main", "simple", "trial"}:
        return raw
    return None


async def _resume_after_bonus_prompt(callback: CallbackQuery, bot: Bot, *, next_action: str) -> None:
    tg_id = callback.from_user.id
    if next_action == "trial":
        await _activate_trial_tariff(callback, bot, retry_callback_data="trial_direct")
        return
    if next_action == "simple":
        await _render_mode_simple_step3(callback)
        return

    await callback.message.edit_text(
        "✅ Продолжаем без бонуса.\n\nСледующий шаг — выбрать действие в главном меню.",
        reply_markup=main_keyboard(tg_id),
        parse_mode=ParseMode.MARKDOWN,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("bonus_offer_"))
async def channel_bonus_offer(callback: CallbackQuery):
    next_action = _parse_bonus_next_action(callback.data or "", "bonus_offer_")
    if not next_action:
        await callback.answer("Некорректный шаг", show_alert=True)
        return
    await _show_channel_bonus_offer(callback, next_action=next_action)


@router.callback_query(F.data.startswith("bonus_claim_"))
async def channel_bonus_claim(callback: CallbackQuery, bot: Bot):
    next_action = _parse_bonus_next_action(callback.data or "", "bonus_claim_")
    if not next_action:
        await callback.answer("Некорректный шаг", show_alert=True)
        return

    tg_id = callback.from_user.id
    user = get_user(tg_id)
    ineligible_reason = _channel_bonus_ineligible_reason(tg_id=tg_id, user=user)
    if ineligible_reason:
        await callback.answer(ineligible_reason, show_alert=True)
        await _resume_after_bonus_prompt(callback, bot, next_action=next_action)
        return

    activated, reason = await _activate_channel_bonus(message=callback.message, bot=bot, tg_id=tg_id)
    if activated:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔗 Ручная ссылка / QR", callback_data="show_key")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back")],
            ]
        )
        await callback.message.edit_text(
            f"✅ *Бонус включён*\n\nПлатный доступ добавлен на *{CHANNEL_PREMIUM_DAYS} дней*.\n\nСледующий шаг — открыть POKROV или запасную ручную ссылку.",
            reply_markup=kb,
            parse_mode=ParseMode.MARKDOWN,
        )
        await callback.answer("Готово")
        return

    if reason == "not_subscribed":
        await callback.message.edit_text(
            "⚠️ Сначала подпишитесь на канал, затем нажмите «Проверить и получить».",
            reply_markup=_channel_bonus_keyboard(next_action),
            parse_mode=ParseMode.MARKDOWN,
        )
        await callback.answer()
        return
    if reason == "tos_required":
        await callback.message.edit_text(
            "⚠️ Сначала примите условия, затем я активирую бонус.",
            reply_markup=_tos_offer_keyboard(back_callback=f"bonus_offer_{next_action}"),
            parse_mode=ParseMode.MARKDOWN,
        )
        await callback.answer()
        return

    await callback.answer("Не удалось включить бонус. Продолжаю без него.", show_alert=True)
    await _resume_after_bonus_prompt(callback, bot, next_action=next_action)


@router.callback_query(F.data.startswith("bonus_skip_"))
async def channel_bonus_skip(callback: CallbackQuery, bot: Bot):
    next_action = _parse_bonus_next_action(callback.data or "", "bonus_skip_")
    if not next_action:
        await callback.answer("Некорректный шаг", show_alert=True)
        return
    await _resume_after_bonus_prompt(callback, bot, next_action=next_action)


@router.callback_query(F.data == "trial_direct")
async def trial_direct(callback: CallbackQuery, bot: Bot):
    await _activate_trial_tariff(callback, bot, retry_callback_data="trial_direct")


async def render_admin_user_view(callback: CallbackQuery, tg_id: int):
    """Render admin user detail view - reusable helper"""
    user = get_user(tg_id)

    if not user:
        return

    uname = f"@{user.username}" if user.username else "—"
    now = _utcnow()
    expiry = _naive_utc(user.expiry_at)
    effective_status = _admin_user_effective_status(user, now=now)
    is_active = effective_status == "active"
    status = _admin_user_status_label(effective_status)
    expiry_txt = expiry.strftime("%d.%m.%Y") if expiry else "—"
    days_left = (expiry - now).days if expiry and expiry > now else 0
    plan = (user.sub_type or "—").upper()
    manual_name = (getattr(user, "display_name", None) or "").strip()
    is_manual = _is_manual_test_user(user)
    origin_label = _admin_user_origin_label(user)
    free_usage_line = ""
    if user_uses_free_pool(user):
        remaining_gb, total_gb = await _free_remaining_gb(tg_id, user=user)
        if remaining_gb is None:
            free_usage_line = f"\n📊 Бесплатный остаток: <b>н/д</b> из <b>{int(total_gb)} ГБ</b>"
        else:
            free_usage_line = f"\n📊 Бесплатный остаток: <b>{remaining_gb} ГБ</b> из <b>{int(total_gb)} ГБ</b>"
    panel_snapshot = await _panel_online_snapshot(tg_id)
    panel_online_line = html.escape(_panel_online_text(panel_snapshot))
    panel_last_online_line = html.escape(_panel_last_online_text(panel_snapshot))

    manual_line = f"🏷 Имя: <b>{html.escape(manual_name)}</b>\n" if manual_name else ""

    text = (
        f"<b>👤 Пользователь</b>\n\n"
        f"🆔 ID: <code>{tg_id}</code>\n"
        f"📝 Ник: {html.escape(uname)}\n"
        f"{manual_line}"
        f"📦 Тариф: <b>{html.escape(plan)}</b>\n"
        f"🧩 Origin: <b>{html.escape(origin_label)}</b>\n"
        f"🔋 Статус: {html.escape(status)}\n\n"
        f"📅 До: <b>{html.escape(expiry_txt)}</b> ({days_left} дн.)\n"
        f"📡 Режим: <b>{html.escape(_plan_mode_label(plan, user=user))}</b>\n"
        f"🌐 Онлайн: <b>{panel_online_line}</b>\n"
        f"🕓 Последний онлайн: <b>{panel_last_online_line}</b>\n"
        f"Stars: <b>{int(user.stars_paid or 0)}</b>"
        f"{free_usage_line}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ 7 дней", callback_data=f"adm_add_days_{tg_id}_7"),
            InlineKeyboardButton(text="➕ 30 дней", callback_data=f"adm_add_days_{tg_id}_30")
        ],
        [
            InlineKeyboardButton(text="➖ 7 дней", callback_data=f"adm_add_days_{tg_id}_-7"),
            InlineKeyboardButton(text="➖ 30 дней", callback_data=f"adm_add_days_{tg_id}_-30"),
        ],
        [InlineKeyboardButton(text="🔁 Sync на ноды", callback_data=f"adm_sync_nodes_{tg_id}")],
        [
            InlineKeyboardButton(text="📨 Отправить ссылку", callback_data=f"adm_send_link_{tg_id}"),
            InlineKeyboardButton(text="✉️ Сообщение", callback_data=f"adm_msg_user_{tg_id}"),
        ],
        [InlineKeyboardButton(text="🎫 Сменить тариф", callback_data=f"adm_tariff_{tg_id}")],
        [
            InlineKeyboardButton(
                text="🔓 Активировать" if not user.is_active else "🔒 Отключить",
                callback_data=f"adm_toggle_{tg_id}"
            )
        ],
        [InlineKeyboardButton(text="♻️ Перевыпустить токен", callback_data=f"adm_regen_token_{tg_id}")],
        *(
            [[InlineKeyboardButton(text="🗑️ Удалить manual/test", callback_data=f"adm_del_{tg_id}")]]
            if is_manual
            else []
        ),
        [InlineKeyboardButton(text="◀️ К списку", callback_data="admin_manual_list" if is_manual else "admin_users")]
    ])

    await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)

@router.callback_query(F.data.startswith("adm_tariff_"))
async def admin_tariff_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    tg_id = int(callback.data.replace("adm_tariff_", ""))

    p1 = int(TARIFFS["1_month"]["stars"])
    p3 = int(TARIFFS["3_months"]["stars"])
    p6 = int(TARIFFS["6_months"]["stars"])
    p9 = int(TARIFFS["9_months"]["stars"])
    p12 = int(TARIFFS["12_months"]["stars"])
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆓 Бесплатный (соцсети + AI)", callback_data=f"adm_set_{tg_id}_trial")],
        [InlineKeyboardButton(text=f"📅 1 Месяц ({p1} Stars)", callback_data=f"adm_set_{tg_id}_1_month")],
        [InlineKeyboardButton(text=f"📅 3 Месяца ({p3} Stars)", callback_data=f"adm_set_{tg_id}_3_months")],
        [InlineKeyboardButton(text=f"📅 6 Месяцев ({p6} Stars)", callback_data=f"adm_set_{tg_id}_6_months")],
        [InlineKeyboardButton(text=f"📅 9 Месяцев ({p9} Stars)", callback_data=f"adm_set_{tg_id}_9_months")],
        [InlineKeyboardButton(text=f"📅 12 Месяцев ({p12} Stars)", callback_data=f"adm_set_{tg_id}_12_months")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"adm_user_{tg_id}")]
    ])

    await callback.message.edit_text(
        f"🎫 *Выберите тариф для пользователя* `{tg_id}`:",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data == "admin_gift_menu")
async def admin_gift_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    mini_price = int(GIFT_CARD_TYPES["mini"]["stars"])
    standard_price = int(GIFT_CARD_TYPES["standard"]["stars"])
    premium_price = int(GIFT_CARD_TYPES["premium"]["stars"])
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🎫 Создать Mini (7д / {mini_price} Stars)", callback_data="admin_giftcode_mini")],
        [InlineKeyboardButton(text=f"🎫 Создать Standard (30д / {standard_price} Stars)", callback_data="admin_giftcode_standard")],
        [InlineKeyboardButton(text=f"🎫 Создать Premium (90д / {premium_price} Stars)", callback_data="admin_giftcode_premium")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin")]
    ])

    await callback.message.edit_text(
        "🎁 *Подарки для пользователей*\n\n"
        "Основной поток: *gift-коды* (удобно и безопасно).\n"
        "Создайте код кнопками выше или командой:\n"
        "`/giftcode mini`\n"
        "`/giftcode standard`\n"
        "`/giftcode premium`\n"
        "`/giftcode standard 5` _(пакет 5 кодов)_\n\n"
        "Прямая выдача `/gift` остаётся как резервный ручной инструмент.",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_giftcode_"))
async def admin_giftcode_create_from_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    card_type = (callback.data or "").replace("admin_giftcode_", "", 1).strip().lower()
    if card_type not in GIFT_CARD_TYPES:
        await callback.answer("Неизвестный тип gift-кода", show_alert=True)
        return
    code = create_gift_card(ADMIN_ID, card_type)
    if not code:
        await callback.answer("Не удалось создать код", show_alert=True)
        return
    card = GIFT_CARD_TYPES.get(card_type, {})
    await callback.message.answer(
        f"🎫 *Новый gift-код*\n\n"
        f"Код: `{code}`\n"
        f"Тип: {card.get('name', card_type)}\n"
        f"Срок: {int(card.get('days', 0))} дн.\n\n"
        f"Для активации: `/redeem {code}`",
        parse_mode=ParseMode.MARKDOWN,
    )
    audit_admin(ADMIN_ID, "admin_gift_code_create", meta=f"card_type={card_type}; code={code}")
    await callback.answer("Gift-код создан")

@router.callback_query(F.data.startswith("adm_set_"))
async def admin_set_tariff(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        return

    parts = callback.data.split("_")
    tg_id = int(parts[2])
    # Handle keys with underscores like 1_month (parts[3] + parts[4]?)
    # callback data: adm_set_{tg_id}_{key}
    # split("_"): ["adm", "set", "123", "1", "month"] -> len 5
    # trial -> len 4

    if len(parts) >= 5:
        tariff_key = f"{parts[3]}_{parts[4]}"
    else:
        tariff_key = parts[3]

    # Pre-defined presets logic based on TARIFFS constant to avoid duplication
    preset = None
    if tariff_key in TARIFFS:
        t = TARIFFS[tariff_key]
        preset = {"days": t["days"], "gb": t["gb"], "name": t["name"]}

    if not preset:
        await callback.answer("❌ Тариф не найден")
        return

    user = get_user(tg_id)
    if user:
        target_sub = _normalize_sub_type(t.get("sub_type") or tariff_key)
        old_sub = _normalize_sub_type(user.sub_type)
        if _is_freemium_sub_type(old_sub) and target_sub == "PAID":
            reset_user_expiry_from_now(tg_id, preset["days"], 0)
        else:
            # Default behavior: extend from current expiry.
            extend_user(tg_id, preset["days"], 0)

        # Update plan in DB (keep internal sub_type consistent with TARIFFS, so wheel/logic works).
        session = Session()
        db_user = session.query(User).filter_by(tg_id=tg_id).first()
        if db_user:
            db_user.sub_type = t.get("sub_type") or tariff_key.upper()
            db_user.total_gb = preset["gb"]
            if _is_freemium_sub_type(db_user.sub_type):
                mark_user_became_free(db_user)
            session.commit()
        session.close()

        # SET traffic on panel (not add) - this resets used to 0 and sets new limit
        await panel.set_tariff_traffic(tg_id, preset["gb"])

        await callback.answer(f"✅ Установлен тариф: {preset['name']}")
    else:
        await callback.answer("❌ Пользователь не найден")
        return

    # Refresh user view
    await render_admin_user_view(callback, tg_id)

@router.callback_query(F.data.startswith("adm_reset_"))
async def admin_reset_traffic(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    tg_id = int(callback.data.replace("adm_reset_", ""))

    # Legacy: traffic limits are not used anymore (kept to avoid breaking older callback links).
    await panel.reset_client_traffic(tg_id)
    await callback.answer("ℹ️ Лимиты по трафику отключены.", show_alert=True)

    # Refresh user view
    await render_admin_user_view(callback, tg_id)


def _delete_legacy_support_history_for_test_user(session, *, tg_id: int) -> None:
    ticket_ids = [
        row[0]
        for row in session.query(SupportTicket.id)
        .filter(
            SupportTicket.user_tg_id == int(tg_id),
            SupportTicket.account_id.is_(None),
        )
        .all()
    ]
    if not ticket_ids:
        return
    session.query(SupportTicketMessage).filter(
        SupportTicketMessage.ticket_id.in_(ticket_ids)
    ).delete(synchronize_session=False)
    session.query(SupportTicket).filter(SupportTicket.id.in_(ticket_ids)).delete(
        synchronize_session=False
    )

@router.callback_query(F.data.startswith("adm_del_"))
async def admin_delete_user(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    tg_id = int(callback.data.replace("adm_del_", ""))

    session = Session()
    try:
        user = session.query(User).filter_by(tg_id=tg_id).first()
        if not _is_manual_test_user(user):
            await callback.answer("Удаление доступно только для manual/test пользователей", show_alert=True)
            return

        try:
            await panel.delete_client(tg_id)
        except Exception:
            pass

        session.query(UserNode).filter_by(tg_id=tg_id).delete(synchronize_session=False)
        session.query(UserKeyPolicy).filter_by(tg_id=tg_id).delete(synchronize_session=False)
        session.query(KeyActionHistory).filter_by(tg_id=tg_id).delete(synchronize_session=False)
        session.query(Event).filter_by(tg_id=tg_id).delete(synchronize_session=False)
        _delete_legacy_support_history_for_test_user(session, tg_id=tg_id)
        session.query(PointsLedger).filter_by(tg_id=tg_id).delete(synchronize_session=False)
        session.query(AdminAudit).filter_by(target_tg_id=tg_id).delete(synchronize_session=False)
        if user:
            session.delete(user)
        session.commit()
    finally:
        session.close()

    audit_admin(callback.from_user.id, "admin_safe_delete_test_user", tg_id)

    await callback.answer(f"✅ Manual/test пользователь {tg_id} удалён!")

    callback_copy = callback
    callback_copy._data = "admin_users:0:all"
    await show_admin_users(callback_copy)
