# -*- coding: utf-8 -*-
"""
Dedicated support intake bot.

Users create tickets here, while operator can continue responses
from the main bot admin queue (shared DB tables).
"""

from __future__ import annotations

import logging
import html
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import BotCommand, CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message
from dotenv import load_dotenv

# Load env from repo-local file first to avoid cwd-dependent startup behavior.
load_dotenv(dotenv_path=Path(__file__).resolve().with_name(".env"))
load_dotenv()

from copy_catalog import get_copy_text
from db import SessionLocal, init_db
from telegram_buttons import modern_inline_button
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
from support_ai_service import SupportAIConfig, generate_support_reply

# Keep existing helpbot keyboard construction while routing every button through
# the Bot API 9.4/9.5 style and custom-emoji helper.
InlineKeyboardButton = modern_inline_button


HELP_BOT_TOKEN = (os.getenv("HELP_BOT_TOKEN") or "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
MAIN_BOT_USERNAME = (os.getenv("BOT_USERNAME") or "pokrov_vpnbot").lstrip("@")
HELPBOT_START_MEDIA_PATH = (os.getenv("HELPBOT_START_MEDIA_PATH") or "").strip()
HELPBOT_START_MEDIA_TYPE = (os.getenv("HELPBOT_START_MEDIA_TYPE") or "photo").strip().lower()
SUPPORT_AI_CONFIG = SupportAIConfig.from_env()

if not HELP_BOT_TOKEN:
    raise SystemExit("HELP_BOT_TOKEN is empty")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ticket_id that expects next text message from tg_id
pending_ticket_replies: dict[int, int] = {}
support_ai_last_reply_at: dict[int, float] = {}

router = Router()

# Ensure schema/migrations are applied before polling.
init_db()

_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_INLINE_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")


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


def _ticket_sender_title(sender_role: str | None) -> str:
    role = (sender_role or "").lower().strip()
    if role == "admin":
        return "Оператор"
    if role == "assistant":
        return "AI-помощник"
    return "Пользователь"


def _support_reply_html(text: str) -> str:
    escaped = html.escape(str(text or "").strip())
    escaped = _INLINE_CODE_RE.sub(r"<code>\1</code>", escaped)
    escaped = _INLINE_BOLD_RE.sub(r"<b>\1</b>", escaped)
    return escaped


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


def _support_ai_reply_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Не получилось", callback_data=f"hb_aiq_no_{ticket_id}"),
                InlineKeyboardButton(text="Дайте шаги", callback_data=f"hb_aiq_steps_{ticket_id}"),
            ],
            [
                InlineKeyboardButton(text="Оператор", callback_data=f"hb_aiq_operator_{ticket_id}"),
                InlineKeyboardButton(text="Открыть обращение", callback_data=f"hb_ticket_view_{ticket_id}"),
            ],
        ]
    )


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


async def _maybe_generate_support_ai_reply(message: Message, *, ticket_id: int, text: str) -> str | None:
    tg_id = int(message.from_user.id)
    if tg_id == ADMIN_ID or not SUPPORT_AI_CONFIG.enabled or not SUPPORT_AI_CONFIG.api_key:
        return None

    now = time.monotonic()
    min_interval = max(0.0, float(SUPPORT_AI_CONFIG.min_interval_seconds))
    last = support_ai_last_reply_at.get(tg_id, 0.0)
    if min_interval and now - last < min_interval:
        return None
    support_ai_last_reply_at[tg_id] = now

    reply = await generate_support_reply(
        text,
        ticket_id=ticket_id,
        user_tg_id=tg_id,
        config=SUPPORT_AI_CONFIG,
    )
    if not reply:
        return None

    session = SessionLocal()
    try:
        add_ticket_message(
            session,
            ticket_id=ticket_id,
            sender_tg_id=0,
            sender_role="assistant",
            body=reply,
        )
        session.commit()
    except Exception:
        try:
            session.rollback()
        except Exception:
            pass
        logger.warning("support AI ticket append failed code=support_reply_persist_error")
        return None
    finally:
        try:
            session.close()
        except Exception:
            logger.warning("support AI ticket session cleanup failed code=support_reply_cleanup_error")
    return reply


def _main_bot_hint() -> str:
    if not MAIN_BOT_USERNAME:
        return "Ответить можно из очереди обращений в основном боте."
    return f"Ответ из админки: https://t.me/{MAIN_BOT_USERNAME}"


async def _configure_support_bot_commands(bot: Bot) -> None:
    try:
        await bot.set_my_commands([BotCommand(command="start", description="Открыть поддержку")])
    except Exception as e:
        logger.warning("helpbot command menu setup failed: %s", e)


def _telegram_attachment_payload(message: Message) -> tuple[str | None, str | None, dict]:
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
            role = _ticket_sender_title(msg.sender_role)
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
        f"Ответ для обращения #{ticket_id}: отправьте текст, скриншот или файл, и мы сразу добавим его в диалог.",
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


@router.callback_query(F.data.startswith("hb_aiq_"))
async def support_ai_quick_reply(callback: CallbackQuery) -> None:
    raw = str(callback.data or "")
    try:
        action, ticket_id_raw = raw.replace("hb_aiq_", "", 1).rsplit("_", 1)
        ticket_id = int(ticket_id_raw)
    except Exception:
        await _safe_answer(callback, "Кнопка устарела.", show_alert=True)
        return

    tg_id = int(callback.from_user.id)
    if tg_id == ADMIN_ID:
        await _safe_answer(callback, "Эти кнопки доступны пользователю.", show_alert=True)
        return

    session = SessionLocal()
    try:
        ticket = get_ticket_by_id(session, ticket_id)
        if not ticket:
            await _safe_answer(callback, "Обращение не найдено.", show_alert=True)
            return
        if not can_access_ticket(ticket, tg_id, ADMIN_ID):
            await _safe_answer(callback, "Нет доступа.", show_alert=True)
            return

        if action == "operator":
            body = "Нужна ручная проверка оператором."
            add_ticket_message(
                session,
                ticket_id=ticket.id,
                sender_tg_id=tg_id,
                sender_role="user",
                body=body,
            )
            set_ticket_status(session, ticket=ticket, status=STATUS_OPEN)
            session.commit()
            await _notify_admin(
                callback.bot,
                f"🆕 Пользователь {tg_id} попросил оператора в обращении #{ticket.id} (helpbot).\n{_main_bot_hint()}",
            )
            await callback.message.answer(
                f"Ок, позвал оператора в обращение #{ticket.id}. Можно дописать детали одним сообщением.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="🎫 Открыть обращение", callback_data=f"hb_ticket_view_{ticket.id}")]]
                ),
            )
            await _safe_answer(callback)
            return
    finally:
        session.close()

    pending_ticket_replies[tg_id] = ticket_id
    if action == "steps":
        prompt = (
            "Напишите одним сообщением устройство и клиент — я дам более точные шаги.\n\n"
            "Устройство:\n"
            "Клиент, если уже установлен:\n"
            "Что хотите сделать:"
        )
    else:
        prompt = (
            "Ок, напишите что именно не получилось — добавлю это в обращение.\n\n"
            "Устройство:\n"
            "Клиент:\n"
            "На каком шаге остановилось:\n"
            "Что видно на экране:"
        )
    await callback.message.answer(
        prompt,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🎫 Открыть обращение", callback_data=f"hb_ticket_view_{ticket_id}")]]
        ),
    )
    await _safe_answer(callback)


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


@router.message(F.photo)
@router.message(F.document)
@router.message(F.video)
async def capture_ticket_attachment(message: Message) -> None:
    tg_id = message.from_user.id
    media_type, media_file_id, media_payload = _telegram_attachment_payload(message)
    if not media_type or not media_file_id:
        return

    body = (getattr(message, "caption", None) or "").strip()
    if not body:
        body = str(media_payload.get("name") or "Вложение из Telegram").strip()

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
            body=body,
            media_type=media_type,
            media_file_id=str(media_file_id),
            media_payload=json.dumps(media_payload, ensure_ascii=False, separators=(",", ":")),
        )
        if tg_id == ADMIN_ID:
            set_ticket_status(session, ticket=ticket, status=STATUS_IN_PROGRESS, assigned_admin_tg_id=ADMIN_ID)
            caption = f"💬 Новый ответ команды POKROV по обращению #{ticket.id}:\n{body}"
            try:
                await message.copy_to(ticket.user_tg_id, caption=caption)
            except Exception as e:
                logger.warning("helpbot attachment copy to user failed ticket=%s err=%s", ticket.id, e)
                try:
                    await message.bot.send_message(ticket.user_tg_id, caption)
                except Exception as inner:
                    logger.warning("helpbot attachment fallback to user failed ticket=%s err=%s", ticket.id, inner)
        else:
            set_ticket_status(session, ticket=ticket, status=STATUS_OPEN)
            caption = f"🆕 Новое сообщение в обращении #{ticket.id} от пользователя {tg_id} (helpbot).\n{body}\n\n{_main_bot_hint()}"
            if ADMIN_ID > 0:
                try:
                    await message.copy_to(ADMIN_ID, caption=caption)
                except Exception as e:
                    logger.warning("helpbot attachment copy to admin failed ticket=%s err=%s", ticket.id, e)
                    await _notify_admin(message.bot, caption)
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
        f"Вложение добавлено в обращение #{ticket_id}.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🎫 Открыть обращение", callback_data=f"hb_ticket_view_{ticket_id}")],
                [InlineKeyboardButton(text="🏠 В меню", callback_data="hb_back_home")],
            ]
        ),
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

    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎫 Открыть обращение", callback_data=f"hb_ticket_view_{ticket_id}")],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="hb_back_home")],
        ]
    )
    assistant_reply = None
    if tg_id != ADMIN_ID:
        assistant_reply = await _maybe_generate_support_ai_reply(message, ticket_id=ticket_id, text=text)

    if assistant_reply:
        await message.answer(
            (
                f"<b>AI-подсказка по обращению #{ticket_id}</b>\n\n"
                f"{_support_reply_html(assistant_reply)}\n\n"
                "<i>Обращение осталось открытым: оператор увидит историю и сможет дополнить ответ.</i>"
            ),
            reply_markup=_support_ai_reply_keyboard(ticket_id),
            parse_mode="HTML",
        )
        return

    await message.answer(
        f"Сообщение добавлено в обращение #{ticket_id}.\nСледующий шаг: откройте обращение, если хотите продолжить диалог.",
        reply_markup=reply_markup,
    )


async def main() -> None:
    dp = Dispatcher()
    dp.include_router(router)
    bot = Bot(token=HELP_BOT_TOKEN)
    await _configure_support_bot_commands(bot)
    logger.info("Support helpbot starting...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
