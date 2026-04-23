# -*- coding: utf-8 -*-
"""
Dedicated support intake bot.

Users create tickets here, while operator can continue responses
from the main bot admin queue (shared DB tables).
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message
from dotenv import load_dotenv

# Load env from repo-local file first to avoid cwd-dependent startup behavior.
load_dotenv(dotenv_path=Path(__file__).resolve().with_name(".env"))
load_dotenv()

from copy_catalog import get_copy_text
from db import SessionLocal, init_db
from tickets_repo import (
    STATUS_CLOSED,
    STATUS_IN_PROGRESS,
    STATUS_OPEN,
    add_ticket_message,
    can_access_ticket,
    create_ticket,
    get_ticket_by_id,
    get_user_active_ticket,
    list_active_tickets,
    list_ticket_messages,
    list_user_tickets,
    set_ticket_status,
)


HELP_BOT_TOKEN = (os.getenv("HELP_BOT_TOKEN") or "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
MAIN_BOT_USERNAME = (os.getenv("BOT_USERNAME") or "pokrov_vpnbot").lstrip("@")
HELPBOT_START_MEDIA_PATH = (os.getenv("HELPBOT_START_MEDIA_PATH") or "").strip()
HELPBOT_START_MEDIA_TYPE = (os.getenv("HELPBOT_START_MEDIA_TYPE") or "photo").strip().lower()

if not HELP_BOT_TOKEN:
    raise SystemExit("HELP_BOT_TOKEN is empty")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ticket_id that expects next text message from tg_id
pending_ticket_replies: dict[int, int] = {}

router = Router()

# Ensure schema/migrations are applied before polling.
init_db()


def _now_str(dt: datetime | None) -> str:
    if dt is None:
        return "-"
    try:
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    except Exception:
        pass
    return dt.strftime("%d.%m %H:%M")


def _ticket_status_title(status: str) -> str:
    st = (status or "").lower().strip()
    if st == STATUS_OPEN:
        return "🟡 Открыто"
    if st == STATUS_IN_PROGRESS:
        return "🟡 В работе"
    if st == STATUS_CLOSED:
        return "⚪ Закрыто"
    return st or "Неизвестно"


def _ticket_message_preview(text: str, limit: int = 200) -> str:
    t = (text or "").strip().replace("\n", " ")
    if not t:
        return "(без текста)"
    return t if len(t) <= limit else t[: max(0, limit - 1)] + "…"


def _main_menu(is_admin: bool) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="➕ Новое обращение", callback_data="hb_ticket_new")],
        [InlineKeyboardButton(text="📂 Мои обращения", callback_data="hb_ticket_my")],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton(text="🧑‍💼 Очередь поддержки", callback_data="hb_admin_queue")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _welcome_text(is_admin: bool) -> str:
    headline = get_copy_text(
        "bot.support.welcome",
        "Служба поддержки POKROV на связи. Здесь можно открыть новое обращение или продолжить уже начатый диалог.",
    )
    text = (
        f"👨‍💻 *{headline}*\n\n"
        "Опишите вопрос одним сообщением — так мы быстрее поймём ситуацию.\n"
        "Если диалог уже начат, откройте своё обращение и продолжайте там.\n\n"
        "👇 *Выберите действие:*"
    )
    if is_admin:
        text += "\n\nРежим оператора: доступна очередь обращений и ответы пользователям вручную."
    return text


async def _send_welcome(message: Message, *, is_admin: bool) -> None:
    text = _welcome_text(is_admin)
    kb = _main_menu(is_admin)

    media_path = HELPBOT_START_MEDIA_PATH
    if media_path:
        try:
            p = Path(media_path)
            if p.exists() and p.is_file():
                media = FSInputFile(str(p))
                mtype = HELPBOT_START_MEDIA_TYPE
                if mtype == "animation":
                    await message.answer_animation(animation=media, caption=text, reply_markup=kb, parse_mode="Markdown")
                    return
                if mtype == "video":
                    await message.answer_video(video=media, caption=text, reply_markup=kb, parse_mode="Markdown")
                    return
                await message.answer_photo(photo=media, caption=text, reply_markup=kb, parse_mode="Markdown")
                return
        except Exception as e:
            logger.warning("helpbot start media failed, fallback to text: %s", e)

    await message.answer(text, reply_markup=kb, parse_mode="Markdown")


def _ticket_view_keyboard(ticket_id: int, status: str, *, is_admin: bool) -> InlineKeyboardMarkup:
    rows = []
    if status != STATUS_CLOSED:
        rows.append([InlineKeyboardButton(text="✍️ Ответить", callback_data=f"hb_ticket_reply_{ticket_id}")])
        rows.append([InlineKeyboardButton(text="✅ Закрыть", callback_data=f"hb_ticket_close_{ticket_id}")])
    else:
        rows.append([InlineKeyboardButton(text="♻️ Переоткрыть", callback_data=f"hb_ticket_reopen_{ticket_id}")])
    if is_admin:
        rows.append([InlineKeyboardButton(text="◀️ Назад к очереди", callback_data="hb_admin_queue")])
    else:
        rows.append([InlineKeyboardButton(text="📂 Мои обращения", callback_data="hb_ticket_my")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _safe_answer(callback: CallbackQuery, text: str | None = None, *, show_alert: bool = False) -> None:
    try:
        await callback.answer(text=text, show_alert=show_alert)
    except Exception:
        pass


async def _notify_admin(bot: Bot, text: str) -> None:
    if ADMIN_ID <= 0:
        return
    try:
        await bot.send_message(ADMIN_ID, text)
    except Exception as e:
        logger.warning("helpbot admin notify failed: %s", e)


def _main_bot_hint() -> str:
    if not MAIN_BOT_USERNAME:
        return "Ответить можно из очереди обращений в основном боте."
    return f"Ответ из админки: https://t.me/{MAIN_BOT_USERNAME}"


def _get_or_create_user_ticket(session, tg_id: int):
    ticket = get_user_active_ticket(session, tg_id)
    created = False
    if not ticket:
        ticket = create_ticket(session, user_tg_id=tg_id)
        session.commit()
        session.refresh(ticket)
        created = True
    return ticket, created


async def _render_ticket(callback: CallbackQuery, ticket_id: int) -> None:
    tg_id = callback.from_user.id
    is_admin = tg_id == ADMIN_ID
    session = SessionLocal()
    try:
        ticket = get_ticket_by_id(session, ticket_id)
        if not ticket:
            await _safe_answer(callback, "Обращение не найдено.", show_alert=True)
            return
        if not can_access_ticket(ticket, tg_id, ADMIN_ID):
            await _safe_answer(callback, "Нет доступа.", show_alert=True)
            return

        msgs = list_ticket_messages(session, ticket_id=ticket.id, limit=20)
        lines = []
        for msg in msgs:
            role = "Оператор" if (msg.sender_role or "").lower() == "admin" else "Пользователь"
            lines.append(f"[{_now_str(msg.created_at)}] {role}: {_ticket_message_preview(msg.body)}")
        history = "\n".join(lines) if lines else "Сообщений пока нет."

        text = (
            f"🎫 Обращение #{ticket.id}\n"
            f"Статус: {_ticket_status_title(ticket.status)}\n"
            f"Пользователь: {ticket.user_tg_id}\n"
            f"Создано: {_now_str(ticket.created_at)}\n"
            f"Обновлено: {_now_str(ticket.updated_at)}\n\n"
            f"{history}"
        )
        await callback.message.edit_text(
            text,
            reply_markup=_ticket_view_keyboard(ticket.id, ticket.status, is_admin=is_admin),
        )
        await _safe_answer(callback)
    finally:
        session.close()


@router.message(CommandStart())
async def start(message: Message) -> None:
    tg_id = message.from_user.id
    is_admin = tg_id == ADMIN_ID
    start_arg = ""
    raw = (message.text or "").strip()
    if " " in raw:
        start_arg = raw.split(" ", 1)[1].strip().lower()

    if start_arg in {"ticket_new", "new", "support"}:
        session = SessionLocal()
        try:
            ticket, created = _get_or_create_user_ticket(session, tg_id)
            pending_ticket_replies[tg_id] = ticket.id
        finally:
            session.close()
        if created:
            await _notify_admin(
                message.bot,
                f"🆕 Новое обращение #{ticket.id} от пользователя {tg_id} (helpbot).\n{_main_bot_hint()}",
            )
        await message.answer(
            f"Обращение #{ticket.id} открыто.\nСледующий шаг: опишите вопрос одним сообщением.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🎫 Открыть обращение", callback_data=f"hb_ticket_view_{ticket.id}")],
                    [InlineKeyboardButton(text="🏠 В меню", callback_data="hb_back_home")],
                ]
            ),
        )
        return

    if start_arg in {"ticket_my", "my", "tickets"}:
        session = SessionLocal()
        try:
            tickets = list_user_tickets(session, tg_id, limit=10)
        finally:
            session.close()
        if not tickets:
            await message.answer(
                "Обращений пока нет.\nСледующий шаг — создайте новое, если нужна помощь.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="➕ Новое обращение", callback_data="hb_ticket_new")],
                        [InlineKeyboardButton(text="◀️ Назад", callback_data="hb_back_home")],
                    ]
                ),
            )
            return
        rows = []
        for t in tickets:
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"#{t.id} {_ticket_status_title(t.status)}",
                        callback_data=f"hb_ticket_view_{t.id}",
                    )
                ]
            )
        rows.append([InlineKeyboardButton(text="➕ Новое обращение", callback_data="hb_ticket_new")])
        rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="hb_back_home")])
        await message.answer("Мои обращения:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
        return

    await _send_welcome(message, is_admin=is_admin)


@router.callback_query(F.data == "hb_ticket_new")
async def ticket_new(callback: CallbackQuery) -> None:
    await _safe_answer(callback)
    tg_id = callback.from_user.id
    session = SessionLocal()
    try:
        ticket, created = _get_or_create_user_ticket(session, tg_id)
        if created:
            await _notify_admin(
                callback.bot,
                f"🆕 Новое обращение #{ticket.id} от пользователя {tg_id} (helpbot).\n{_main_bot_hint()}",
            )
        pending_ticket_replies[tg_id] = ticket.id
        await callback.message.edit_text(
            f"Обращение #{ticket.id} открыто.\nСледующий шаг: одним сообщением опишите, что случилось и на каком шаге возникла проблема.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🎫 Открыть обращение", callback_data=f"hb_ticket_view_{ticket.id}")],
                    [InlineKeyboardButton(text="📂 Мои обращения", callback_data="hb_ticket_my")],
                ]
            ),
        )
    finally:
        session.close()


@router.callback_query(F.data == "hb_ticket_my")
async def ticket_my(callback: CallbackQuery) -> None:
    await _safe_answer(callback)
    tg_id = callback.from_user.id
    session = SessionLocal()
    try:
        tickets = list_user_tickets(session, tg_id, limit=10)
    finally:
        session.close()

    if not tickets:
        await callback.message.edit_text(
            "Обращений пока нет. Когда вы напишете в поддержку, они появятся здесь.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="➕ Новое обращение", callback_data="hb_ticket_new")],
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="hb_back_home")],
                ]
            ),
        )
        return

    rows = []
    for t in tickets:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"#{t.id} {_ticket_status_title(t.status)}",
                    callback_data=f"hb_ticket_view_{t.id}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text="➕ Новое обращение", callback_data="hb_ticket_new")])
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="hb_back_home")])
    await callback.message.edit_text("Мои обращения:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data.startswith("hb_ticket_view_"))
async def ticket_view(callback: CallbackQuery) -> None:
    ticket_id = int(callback.data.replace("hb_ticket_view_", ""))
    await _render_ticket(callback, ticket_id)


@router.callback_query(F.data.startswith("hb_ticket_reply_"))
async def ticket_reply(callback: CallbackQuery) -> None:
    await _safe_answer(callback)
    ticket_id = int(callback.data.replace("hb_ticket_reply_", ""))
    session = SessionLocal()
    try:
        ticket = get_ticket_by_id(session, ticket_id)
        if not ticket:
            await callback.message.edit_text("Обращение не найдено.", reply_markup=_main_menu(callback.from_user.id == ADMIN_ID))
            return
        if not can_access_ticket(ticket, callback.from_user.id, ADMIN_ID):
            await callback.message.edit_text("Нет доступа.", reply_markup=_main_menu(callback.from_user.id == ADMIN_ID))
            return
        if callback.from_user.id == ADMIN_ID:
            set_ticket_status(session, ticket=ticket, status=STATUS_IN_PROGRESS, assigned_admin_tg_id=ADMIN_ID)
        elif ticket.status == STATUS_CLOSED:
            set_ticket_status(session, ticket=ticket, status=STATUS_OPEN)
        session.commit()
    finally:
        session.close()

    pending_ticket_replies[callback.from_user.id] = ticket_id
    await callback.message.edit_text(
        f"Ответ для обращения #{ticket_id}: отправьте одно текстовое сообщение, и мы сразу добавим его в диалог.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data=f"hb_ticket_view_{ticket_id}")]]
        ),
    )


@router.callback_query(F.data.startswith("hb_ticket_close_"))
async def ticket_close(callback: CallbackQuery) -> None:
    await _safe_answer(callback)
    ticket_id = int(callback.data.replace("hb_ticket_close_", ""))
    session = SessionLocal()
    try:
        ticket = get_ticket_by_id(session, ticket_id)
        if not ticket:
            await callback.message.edit_text("Обращение не найдено.", reply_markup=_main_menu(callback.from_user.id == ADMIN_ID))
            return
        if not can_access_ticket(ticket, callback.from_user.id, ADMIN_ID):
            await callback.message.edit_text("Нет доступа.", reply_markup=_main_menu(callback.from_user.id == ADMIN_ID))
            return
        set_ticket_status(session, ticket=ticket, status=STATUS_CLOSED)
        session.commit()
    finally:
        session.close()

    await _notify_admin(callback.bot, f"Обращение #{ticket_id} закрыто пользователем {callback.from_user.id}.")
    await _render_ticket(callback, ticket_id)


@router.callback_query(F.data.startswith("hb_ticket_reopen_"))
async def ticket_reopen(callback: CallbackQuery) -> None:
    await _safe_answer(callback)
    ticket_id = int(callback.data.replace("hb_ticket_reopen_", ""))
    session = SessionLocal()
    try:
        ticket = get_ticket_by_id(session, ticket_id)
        if not ticket:
            await callback.message.edit_text("Обращение не найдено.", reply_markup=_main_menu(callback.from_user.id == ADMIN_ID))
            return
        if not can_access_ticket(ticket, callback.from_user.id, ADMIN_ID):
            await callback.message.edit_text("Нет доступа.", reply_markup=_main_menu(callback.from_user.id == ADMIN_ID))
            return
        set_ticket_status(session, ticket=ticket, status=STATUS_OPEN)
        session.commit()
    finally:
        session.close()

    await _notify_admin(callback.bot, f"Обращение #{ticket_id} снова открыто пользователем {callback.from_user.id}.")
    await _render_ticket(callback, ticket_id)


@router.callback_query(F.data == "hb_admin_queue")
async def admin_queue(callback: CallbackQuery) -> None:
    await _safe_answer(callback)
    if callback.from_user.id != ADMIN_ID:
        await callback.message.edit_text("Доступ запрещён.", reply_markup=_main_menu(False))
        return

    session = SessionLocal()
    try:
        tickets = list_active_tickets(session, limit=20)
    finally:
        session.close()

    if not tickets:
        await callback.message.edit_text(
            "В очереди пока нет активных обращений.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Обновить", callback_data="hb_admin_queue")],
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="hb_back_home")],
                ]
            ),
        )
        return

    rows = []
    for t in tickets:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"#{t.id} u:{t.user_tg_id} {_ticket_status_title(t.status)}",
                    callback_data=f"hb_ticket_view_{t.id}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text="🔄 Обновить", callback_data="hb_admin_queue")])
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="hb_back_home")])
    await callback.message.edit_text("Активные обращения:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data == "hb_back_home")
async def back_home(callback: CallbackQuery) -> None:
    await _safe_answer(callback)
    await callback.message.edit_text(
        "Меню поддержки POKROV.",
        reply_markup=_main_menu(callback.from_user.id == ADMIN_ID),
    )


@router.message(F.text)
async def capture_ticket_reply(message: Message) -> None:
    tg_id = message.from_user.id
    text = (message.text or "").strip()
    if not text:
        return
    ticket_id = pending_ticket_replies.get(tg_id, 0)
    session = SessionLocal()
    try:
        ticket = None
        created = False
        if ticket_id > 0:
            ticket = get_ticket_by_id(session, ticket_id)
        if not ticket and tg_id != ADMIN_ID:
            ticket, created = _get_or_create_user_ticket(session, tg_id)
            ticket_id = ticket.id
        if not ticket and tg_id == ADMIN_ID:
            await message.answer("Выберите обращение в очереди и нажмите «Ответить».", reply_markup=_main_menu(True))
            return
        if not ticket:
            await message.answer("Обращение не найдено.", reply_markup=_main_menu(tg_id == ADMIN_ID))
            return
        if not can_access_ticket(ticket, tg_id, ADMIN_ID):
            await message.answer("Нет доступа к обращению.", reply_markup=_main_menu(tg_id == ADMIN_ID))
            return

        role = "admin" if tg_id == ADMIN_ID else "user"
        add_ticket_message(
            session,
            ticket_id=ticket.id,
            sender_tg_id=tg_id,
            sender_role=role,
            body=text,
        )
        if tg_id == ADMIN_ID:
            set_ticket_status(session, ticket=ticket, status=STATUS_IN_PROGRESS, assigned_admin_tg_id=ADMIN_ID)
            try:
                await message.bot.send_message(ticket.user_tg_id, f"💬 Новый ответ команды POKROV по обращению #{ticket.id}:\n{text}")
            except Exception as e:
                logger.warning("helpbot reply to user failed ticket=%s err=%s", ticket.id, e)
        else:
            set_ticket_status(session, ticket=ticket, status=STATUS_OPEN)
            await _notify_admin(
                message.bot,
                f"🆕 Новое сообщение в обращении #{ticket.id} от пользователя {tg_id} (helpbot).\n{text}\n\n{_main_bot_hint()}",
            )
            if created:
                await _notify_admin(
                    message.bot,
                    f"🆕 Новое обращение #{ticket.id} от пользователя {tg_id} (helpbot).\n{_main_bot_hint()}",
                )
        session.commit()
        pending_ticket_replies.pop(tg_id, None)
    finally:
        session.close()

    await message.answer(
        f"Сообщение добавлено в обращение #{ticket_id}.\nСледующий шаг: откройте обращение, если хотите продолжить диалог.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🎫 Открыть обращение", callback_data=f"hb_ticket_view_{ticket_id}")],
                [InlineKeyboardButton(text="🏠 В меню", callback_data="hb_back_home")],
            ]
        ),
    )


async def main() -> None:
    dp = Dispatcher()
    dp.include_router(router)
    bot = Bot(token=HELP_BOT_TOKEN)
    logger.info("Support helpbot starting...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
