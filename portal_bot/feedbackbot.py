from __future__ import annotations

import asyncio
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().with_name(".env"))
load_dotenv()

from copy_catalog import get_copy_text
from db import SessionLocal, init_db
from models import FeedbackEntry, Review


FEEDBACK_BOT_TOKEN = (os.getenv("FEEDBACK_BOT_TOKEN") or "").strip()
FEEDBACK_USERNAME = (os.getenv("FEEDBACK_USERNAME") or os.getenv("FEEDBACK_BOT_USERNAME") or "pokrov_feedbackbot").lstrip("@")
SUPPORT_USERNAME = (os.getenv("SUPPORT_USERNAME") or os.getenv("SUPPORT_BOT_USERNAME") or "pokrov_supportbot").lstrip("@")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not FEEDBACK_BOT_TOKEN:
    raise SystemExit("FEEDBACK_BOT_TOKEN is empty")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
router = Router()

pending_feedback: set[int] = set()

init_db()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _normalize_feedback_text(text: str | None, *, limit: int = 1000) -> str:
    value = re.sub(r"\s+", " ", str(text or "").strip())
    return value[:limit]


def _mask_username(username: str | None) -> str:
    raw = re.sub(r"\s+", "", str(username or "").strip())
    if raw.startswith("@"):
        raw = raw[1:].strip()
    if not raw:
        return "Пользователь"
    return f"{raw[:4]}****"


def _display_username(username: str | None) -> str:
    masked = _mask_username(username)
    if masked == "Пользователь":
        return masked
    return f"@{masked}"


def upsert_feedback_entry(
    session,
    *,
    tg_id: int,
    username: str | None,
    text: str,
    category: str = "general",
    source: str = "feedbackbot",
) -> FeedbackEntry:
    normalized_text = _normalize_feedback_text(text, limit=1000)
    if len(normalized_text) < 5:
        raise ValueError("feedback text is too short")

    entry = (
        session.query(FeedbackEntry)
        .filter(FeedbackEntry.tg_id == int(tg_id))
        .filter(FeedbackEntry.status == "new")
        .order_by(FeedbackEntry.created_at.desc())
        .first()
    )
    if entry is None:
        entry = FeedbackEntry(
            tg_id=int(tg_id),
            username=(username or "").strip() or None,
            category=(category or "general").strip() or "general",
            text=normalized_text,
            status="new",
            source=(source or "feedbackbot").strip() or "feedbackbot",
        )
        session.add(entry)
    else:
        entry.username = (username or "").strip() or entry.username
        entry.category = (category or entry.category or "general").strip() or "general"
        entry.text = normalized_text
        entry.source = (source or entry.source or "feedbackbot").strip() or "feedbackbot"
        entry.reviewed_at = None

    session.commit()
    session.refresh(entry)
    return entry


def publish_feedback_entry(session, entry_id: int, *, rating: int = 5) -> tuple[FeedbackEntry | None, Review | None]:
    entry = session.query(FeedbackEntry).filter_by(id=int(entry_id)).first()
    if entry is None:
        return None, None

    review_text = _normalize_feedback_text(entry.text, limit=500)
    if len(review_text) < 5:
        raise ValueError("feedback text is too short for publishing")

    review = None
    if entry.review_id:
        review = session.query(Review).filter_by(id=int(entry.review_id)).first()

    if review is None:
        review = Review(
            tg_id=-abs(int(entry.tg_id)),
            username=entry.username,
            rating=max(1, min(int(rating or 5), 5)),
            text=review_text,
            is_featured=True,
        )
        session.add(review)
        session.flush()
        entry.review_id = int(review.id)
    else:
        review.username = entry.username
        review.rating = max(1, min(int(rating or review.rating or 5), 5))
        review.text = review_text
        review.is_featured = True

    entry.status = "published"
    entry.reviewed_at = _utcnow()
    session.commit()
    session.refresh(entry)
    session.refresh(review)
    return entry, review


def delete_feedback_entry(session, entry_id: int) -> bool:
    entry = session.query(FeedbackEntry).filter_by(id=int(entry_id)).first()
    if entry is None:
        return False

    if entry.review_id:
        review = session.query(Review).filter_by(id=int(entry.review_id)).first()
        if review is not None:
            session.delete(review)
    session.delete(entry)
    session.commit()
    return True


def _menu_markup(*, is_admin: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="✍️ Оставить отзыв", callback_data="fb_new")],
        [InlineKeyboardButton(text="💬 В поддержку", url=f"https://t.me/{SUPPORT_USERNAME}?start=ticket_new")],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton(text="🧑‍💼 Очередь модерации", callback_data="fb_admin_queue")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _welcome_text(is_admin: bool) -> str:
    headline = get_copy_text(
        "bot.feedback.welcome",
        "Сюда можно отправить отзыв, идею или короткое замечание о POKROV. Мы всё читаем и лучшие отзывы публикуем после модерации.",
    )
    prompt = get_copy_text(
        "bot.feedback.prompt",
        "Напишите, что понравилось, что хотелось бы улучшить или какой момент запомнился сильнее всего. Достаточно пары честных предложений.",
    )
    text = f"💌 *{headline}*\n\n{prompt}"
    if is_admin:
        text += "\n\nРежим оператора: ниже доступна очередь новых отзывов."
    return text


def _entry_keyboard(entry_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⭐ На сайт", callback_data=f"fb_feature_{entry_id}"),
                InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"fb_delete_{entry_id}"),
            ],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="fb_admin_queue")],
        ]
    )


def _format_entry(entry: FeedbackEntry) -> str:
    category = (entry.category or "general").strip()
    source = (entry.source or "feedbackbot").strip()
    return (
        f"💌 Отзыв #{entry.id}\n"
        f"Пользователь: {_display_username(entry.username)}\n"
        f"Категория: {category}\n"
        f"Источник: {source}\n\n"
        f"{entry.text or '—'}"
    )


def _list_pending_entries(limit: int = 10) -> list[FeedbackEntry]:
    session = SessionLocal()
    try:
        return (
            session.query(FeedbackEntry)
            .filter(FeedbackEntry.status == "new")
            .order_by(FeedbackEntry.created_at.desc())
            .limit(limit)
            .all()
        )
    finally:
        session.close()


async def _notify_admin(bot: Bot, entry: FeedbackEntry) -> None:
    if ADMIN_ID <= 0:
        return
    try:
        await bot.send_message(ADMIN_ID, _format_entry(entry), reply_markup=_entry_keyboard(entry.id))
    except Exception as exc:
        logger.warning("feedbackbot admin notify failed: %s", exc)


async def _show_queue(message: Message) -> None:
    entries = _list_pending_entries()
    if not entries:
        await message.answer("Новых отзывов в очереди пока нет.", reply_markup=_menu_markup(is_admin=True))
        return

    rows: list[list[InlineKeyboardButton]] = []
    for entry in entries:
        masked = _mask_username(entry.username)
        timestamp = entry.created_at.strftime("%d.%m %H:%M") if entry.created_at else "только что"
        rows.append([InlineKeyboardButton(text=f"{masked} • {timestamp}", callback_data=f"fb_review_{entry.id}")])

    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="fb_back_home")])
    await message.answer(
        f"Очередь модерации: {len(entries)}\nСледующий шаг: выберите отзыв, который хотите проверить.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )


@router.message(CommandStart())
async def start(message: Message) -> None:
    is_admin = message.from_user.id == ADMIN_ID
    await message.answer(
        _welcome_text(is_admin),
        reply_markup=_menu_markup(is_admin=is_admin),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "fb_new")
async def fb_new(callback: CallbackQuery) -> None:
    pending_feedback.add(callback.from_user.id)
    await callback.message.edit_text(
        "💌 *Напишите отзыв одним сообщением*\n\n"
        "Коротко расскажите, что помогло, что было неудобно и что стоит улучшить. Затем мы передадим текст на модерацию.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="fb_back_home")]]
        ),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "fb_back_home")
async def fb_back_home(callback: CallbackQuery) -> None:
    is_admin = callback.from_user.id == ADMIN_ID
    await callback.message.edit_text(
        _welcome_text(is_admin),
        reply_markup=_menu_markup(is_admin=is_admin),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(F.text & ~F.text.startswith("/"))
async def capture_feedback(message: Message) -> None:
    tg_id = message.from_user.id
    if tg_id not in pending_feedback:
        return

    pending_feedback.discard(tg_id)

    try:
        session = SessionLocal()
        try:
            entry = upsert_feedback_entry(
                session,
                tg_id=tg_id,
                username=message.from_user.username,
                text=message.text or "",
            )
        finally:
            session.close()
    except ValueError:
        pending_feedback.add(tg_id)
        await message.answer("Напишите пару слов, чтобы мы поняли контекст и спокойно передали отзыв на модерацию.")
        return

    await _notify_admin(message.bot, entry)
    await message.answer(
        get_copy_text(
            "bot.feedback.thanks",
            "Спасибо! Мы сохранили отзыв и передали его на модерацию. Если он подойдёт для публикации, покажем его на сайте.",
        ),
        reply_markup=_menu_markup(),
    )


@router.callback_query(F.data.startswith("fb_review_"))
async def fb_review_open(callback: CallbackQuery) -> None:
    entry_id = int(callback.data.replace("fb_review_", ""))
    session = SessionLocal()
    try:
        entry = session.query(FeedbackEntry).filter_by(id=entry_id).first()
    finally:
        session.close()

    if not entry:
        await callback.answer("Отзыв не найден.", show_alert=True)
        return

    await callback.message.edit_text(_format_entry(entry), reply_markup=_entry_keyboard(entry.id))
    await callback.answer()


@router.callback_query(F.data == "fb_admin_queue")
async def fb_admin_queue(callback: CallbackQuery) -> None:
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа.", show_alert=True)
        return
    await _show_queue(callback.message)
    await callback.answer()


@router.callback_query(F.data.startswith("fb_feature_"))
async def fb_feature(callback: CallbackQuery) -> None:
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа.", show_alert=True)
        return

    entry_id = int(callback.data.replace("fb_feature_", ""))
    session = SessionLocal()
    try:
        entry, _review = publish_feedback_entry(session, entry_id)
    except ValueError:
        entry = None
    finally:
        session.close()

    if entry is None:
        await callback.answer("Не удалось опубликовать отзыв.", show_alert=True)
        return

    try:
        await callback.bot.send_message(
            int(entry.tg_id),
            "✅ Спасибо. Отзыв прошёл модерацию и теперь опубликован на сайте POKROV.",
        )
    except Exception:
        pass

    await callback.answer("Отзыв опубликован.")
    await _show_queue(callback.message)


@router.callback_query(F.data.startswith("fb_delete_"))
async def fb_delete(callback: CallbackQuery) -> None:
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа.", show_alert=True)
        return

    entry_id = int(callback.data.replace("fb_delete_", ""))
    session = SessionLocal()
    try:
        deleted = delete_feedback_entry(session, entry_id)
    finally:
        session.close()

    if not deleted:
        await callback.answer("Отзыв уже удалён.", show_alert=True)
        return

    await callback.answer("Отзыв удалён.")
    await _show_queue(callback.message)


async def main() -> None:
    dp = Dispatcher()
    dp.include_router(router)
    bot = Bot(token=FEEDBACK_BOT_TOKEN)
    logger.info("Feedback bot starting...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
