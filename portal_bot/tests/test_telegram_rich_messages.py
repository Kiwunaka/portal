from __future__ import annotations

import sys
from pathlib import Path


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1]
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

from telegram_rich_messages import help_copy, payment_success_copy  # noqa: E402


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
