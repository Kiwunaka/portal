from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from dotenv import load_dotenv


load_dotenv(dotenv_path=Path(__file__).resolve().with_name(".env"))
load_dotenv()

LEGACY_BOT_TOKEN = (os.getenv("LEGACY_BOT_TOKEN") or "").strip()
TARGET_URL = (os.getenv("BOT_MIGRATION_TARGET_URL") or "https://t.me/portal_service_bot").strip()

if not LEGACY_BOT_TOKEN:
    raise SystemExit("LEGACY_BOT_TOKEN is empty")

if not TARGET_URL.startswith("https://t.me/"):
    raise SystemExit("BOT_MIGRATION_TARGET_URL must be a Telegram URL (https://t.me/...)")


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
router = Router()


def _redirect_text() -> str:
    return (
        "ℹ️ Этот бот переехал.\n\n"
        "Пожалуйста, используйте новый бот:\n"
        f"{TARGET_URL}"
    )


def _redirect_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Открыть новый бот", url=TARGET_URL)]]
    )


@router.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(_redirect_text(), reply_markup=_redirect_kb(), disable_web_page_preview=True)


@router.callback_query()
async def any_callback(callback: CallbackQuery) -> None:
    await callback.answer("Бот переехал", show_alert=False)
    await callback.message.answer(_redirect_text(), reply_markup=_redirect_kb(), disable_web_page_preview=True)


@router.message(F.text)
async def any_text(message: Message) -> None:
    await message.answer(_redirect_text(), reply_markup=_redirect_kb(), disable_web_page_preview=True)


async def main() -> None:
    bot = Bot(token=LEGACY_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    logger.info("Legacy redirect bot started")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
