from __future__ import annotations

import os
from typing import Any

from aiogram.types import InlineKeyboardButton as AiogramInlineKeyboardButton


BTN_STYLE_PRIMARY = "primary"
BTN_STYLE_SUCCESS = "success"
BTN_STYLE_DANGER = "danger"

BTN_EMOJI_PRIMARY_ID = (os.getenv("TG_BTN_EMOJI_PRIMARY_ID") or "").strip()
BTN_EMOJI_SUCCESS_ID = (os.getenv("TG_BTN_EMOJI_SUCCESS_ID") or "").strip()
BTN_EMOJI_DANGER_ID = (os.getenv("TG_BTN_EMOJI_DANGER_ID") or "").strip()


def _inline_button_supported_fields() -> set[str]:
    fields = getattr(AiogramInlineKeyboardButton, "model_fields", None)
    if isinstance(fields, dict):
        return set(fields.keys())
    fields = getattr(AiogramInlineKeyboardButton, "__fields__", None)
    if isinstance(fields, dict):
        return set(fields.keys())
    return {"text", "callback_data", "url", "web_app"}


INLINE_BUTTON_FIELDS = _inline_button_supported_fields()
SUPPORTS_BTN_STYLE = "style" in INLINE_BUTTON_FIELDS
SUPPORTS_BTN_ICON = "icon_custom_emoji_id" in INLINE_BUTTON_FIELDS
SUPPORTS_BTN_COPY_TEXT = "copy_text" in INLINE_BUTTON_FIELDS


def _emoji_for_style(style: str | None) -> str | None:
    if style == BTN_STYLE_SUCCESS:
        return BTN_EMOJI_SUCCESS_ID or None
    if style == BTN_STYLE_DANGER:
        return BTN_EMOJI_DANGER_ID or None
    if style == BTN_STYLE_PRIMARY:
        return BTN_EMOJI_PRIMARY_ID or None
    return None


def infer_button_style(text: str, callback_data: str | None = None, url: str | None = None) -> str | None:
    del url
    label = (text or "").strip().lower()
    data = (callback_data or "").strip().lower()

    if any(token in label for token in ("назад", "отмена", "закрыть")):
        return None

    if (
        "delete" in data
        or "panic" in data
        or "ban" in data
        or "revoke" in data
        or "ticket_close" in data
        or data.startswith("adm_del_")
        or data.startswith("adm_regen_token_")
        or any(token in label for token in ("удалить", "сбросить", "отозвать", "заблокировать"))
    ):
        return BTN_STYLE_DANGER

    if "back" in data or "cancel" in data or data in {"close", "dismiss"}:
        return None

    if (
        "new" in data
        or "reopen" in data
        or "feature" in data
        or "publish" in data
        or "create" in data
        or "claim" in data
    ):
        return BTN_STYLE_SUCCESS

    return BTN_STYLE_PRIMARY


def modern_inline_button(
    *,
    text: str,
    callback_data: str | None = None,
    url: str | None = None,
    copy_text: str | None = None,
    style: str | None = None,
    icon_custom_emoji_id: str | None = None,
    **kwargs: Any,
) -> AiogramInlineKeyboardButton:
    payload: dict[str, Any] = {"text": text, **kwargs}
    if callback_data is not None:
        payload["callback_data"] = callback_data
    if url is not None:
        payload["url"] = url
    if copy_text and SUPPORTS_BTN_COPY_TEXT:
        payload["copy_text"] = {"text": copy_text}

    resolved_style = style or infer_button_style(text, callback_data=callback_data, url=url)
    if resolved_style and SUPPORTS_BTN_STYLE:
        payload["style"] = resolved_style

    resolved_icon = icon_custom_emoji_id
    if resolved_icon is None:
        resolved_icon = _emoji_for_style(resolved_style)
    if resolved_icon and SUPPORTS_BTN_ICON:
        payload["icon_custom_emoji_id"] = resolved_icon

    return AiogramInlineKeyboardButton(**payload)
