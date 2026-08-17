from __future__ import annotations

import sys
from pathlib import Path


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1]
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

from telegram_rich_messages import (  # noqa: E402
    device_picker_copy,
    help_copy,
    home_copy,
    payment_success_copy,
    tariff_choice_copy,
)


def test_help_copy_has_rich_structure_and_plain_html_fallback() -> None:
    copy = help_copy()
    assert "<h3>" in copy.rich_html
    assert "<ul>" in copy.rich_html
    assert "/cabinet" in copy.rich_html
    assert "<h3>" not in copy.fallback_html
    assert "Частые вопросы" in copy.fallback_html


def test_payment_copy_escapes_receipt_fields_and_keeps_details_collapsed() -> None:
    copy = payment_success_copy(
        tariff_name="Месяц <test>",
        expiry="31.08.2026",
        amount_display="299 Telegram Stars",
        paid_at="22.07.2026 12:00",
        transaction_id="portal_<unsafe>",
    )
    assert "<details>" in copy.rich_html
    assert "Месяц &lt;test&gt;" in copy.rich_html
    assert "portal_&lt;unsafe&gt;" in copy.rich_html
    assert "<blockquote expandable>" in copy.fallback_html
    assert "<details>" not in copy.fallback_html


def test_home_copy_uses_native_rich_structure_and_custom_emoji() -> None:
    copy = home_copy(new_user=True)
    returning_copy = home_copy(returning=True, show_trial=False)
    assert "<h2>" in copy.rich_html
    assert "<tg-emoji emoji-id=" in copy.rich_html
    assert "YouTube, TikTok и ChatGPT — одной кнопкой" in copy.rich_html
    assert "<ul>" not in copy.rich_html
    assert "<h2>" not in copy.fallback_html
    assert "POKROV VPN" in copy.fallback_html
    assert "карта не нужна" in copy.fallback_html
    assert "5 дней" not in returning_copy.fallback_html
    assert "приложении и кабинете" in returning_copy.fallback_html


def test_device_picker_only_adds_slideshow_for_two_safe_https_urls() -> None:
    without_media = device_picker_copy(
        ["https://cdn.example/one.png", "http://cdn.example/two.png"]
    )
    with_media = device_picker_copy(
        [
            "https://cdn.example/one.png",
            "https://cdn.example/two.png?size=large&kind=step",
        ]
    )

    assert "<tg-slideshow>" not in without_media.rich_html
    assert "<tg-slideshow>" in with_media.rich_html
    assert "size=large&amp;kind=step" in with_media.rich_html
    assert "<tg-slideshow>" not in with_media.fallback_html


def test_tariff_copy_is_native_text_and_escapes_runtime_values() -> None:
    copy = tariff_choice_copy(
        show_trial=True,
        paid_count=3,
        paid_list="Москва <fast>, NL & DE",
        free_label="NL <free>",
        trial_limit_gb=5,
        trial_device_limit=2,
        paid_device_limit=5,
        savings=["3 мес: -10%", "12 мес: -45%"],
    )

    assert "<table bordered striped>" in copy.rich_html
    assert "<details>" in copy.rich_html
    assert "Москва &lt;fast&gt;, NL &amp; DE" in copy.rich_html
    assert "NL &lt;free&gt;" in copy.rich_html
    assert "<table" not in copy.fallback_html
    assert "<blockquote expandable>" in copy.fallback_html
