from __future__ import annotations

import sys
from pathlib import Path


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1]
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

from telegram_emoji import (  # noqa: E402
    button_label,
    curated_emoji_manifest,
    custom_emoji_id,
    rich_emoji,
)


def test_curated_manifest_has_valid_unique_ids_and_pack_provenance() -> None:
    manifest = curated_emoji_manifest()
    ids = [item["custom_emoji_id"] for item in manifest.values()]

    assert {"FinanceEmoji", "NewsEmoji", "Decoration_Pack", "TONEmoji"} <= {
        item["pack"] for item in manifest.values()
    }
    assert all(value.isdigit() for value in ids)
    assert len(ids) == len(set(ids))
    assert manifest["payment"]["fallback"] == "💳"


def test_custom_emoji_can_be_disabled_without_losing_unicode(monkeypatch) -> None:
    monkeypatch.setenv("TG_CUSTOM_EMOJI_ENABLED", "0")

    assert custom_emoji_id("payment") is None
    assert button_label("payment", "Оплатить", icon_supported=True) == "💳 Оплатить"
    assert rich_emoji("payment") == "💳"


def test_per_icon_override_is_validated(monkeypatch) -> None:
    monkeypatch.setenv("TG_CUSTOM_EMOJI_ENABLED", "1")
    monkeypatch.setenv("TG_EMOJI_PAYMENT_ID", "not-an-id")
    assert custom_emoji_id("payment") is None

    monkeypatch.setenv("TG_EMOJI_PAYMENT_ID", "1234567890123456789")
    assert custom_emoji_id("payment") == "1234567890123456789"
    assert 'emoji-id="1234567890123456789"' in rich_emoji("payment")
