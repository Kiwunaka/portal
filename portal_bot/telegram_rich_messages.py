from __future__ import annotations

import html
from dataclasses import dataclass


@dataclass(frozen=True)
class RichMessageCopy:
    rich_html: str
    fallback_html: str


def help_copy() -> RichMessageCopy:
    return RichMessageCopy(
        rich_html=(
            "<h3>🧭 Помощь. Частые вопросы</h3>"
            "<p>Главное действие — открыть приложение POKROV и нажать «Подключить».</p>"
            "<ul>"
            "<li><b>/start</b> — главное меню, доступ и оплата</li>"
            "<li><b>/cabinet</b> — кабинет, устройства и загрузки</li>"
            "<li><b>/support</b> — обращение в поддержку</li>"
            "</ul>"
            "<footer>Ручная ссылка и QR остаются запасным способом подключения.</footer>"
        ),
        fallback_html=(
            "🧭 <b>Помощь. Частые вопросы</b>\n\n"
            "Главное действие — открыть приложение POKROV и нажать «Подключить».\n\n"
            "• <b>/start</b> — главное меню, доступ и оплата\n"
            "• <b>/cabinet</b> — кабинет, устройства и загрузки\n"
            "• <b>/support</b> — обращение в поддержку\n\n"
            "Ручная ссылка и QR остаются запасным способом подключения."
        ),
    )


def payment_success_copy(
    *,
    tariff_name: str,
    expiry: str,
    amount_display: str,
    paid_at: str,
    transaction_id: str,
) -> RichMessageCopy:
    tariff = html.escape(str(tariff_name or "Доступ POKROV"))
    expires = html.escape(str(expiry or "—"))
    amount = html.escape(str(amount_display or "—"))
    timestamp = html.escape(str(paid_at or "—"))
    transaction = html.escape(str(transaction_id or "—"))
    return RichMessageCopy(
        rich_html=(
            "<h3>✅ Оплата прошла — доступ включён</h3>"
            f"<p>Тариф: <b>{tariff}</b><br/>Действует до: <b>{expires}</b></p>"
            "<p>Откройте приложение POKROV, войдите в свой аккаунт и нажмите «Подключить».</p>"
            "<details><summary>🧾 Квитанция</summary>"
            f"<p>Товар: {tariff}<br/>Сумма: {amount}<br/>Дата: {timestamp} UTC<br/>ID: <code>{transaction}</code></p>"
            "</details>"
        ),
        fallback_html=(
            "✅ <b>Оплата прошла — доступ включён</b>\n\n"
            f"Тариф: <b>{tariff}</b>\n"
            f"Действует до: <b>{expires}</b>\n\n"
            "Откройте приложение POKROV, войдите в свой аккаунт и нажмите «Подключить».\n\n"
            "<blockquote expandable>🧾 Квитанция\n"
            f"Товар: {tariff}\n"
            f"Сумма: {amount}\n"
            f"Дата: {timestamp} UTC\n"
            f"ID: <code>{transaction}</code></blockquote>"
        ),
    )
