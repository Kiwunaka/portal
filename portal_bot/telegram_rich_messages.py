from __future__ import annotations

import html
import os
from dataclasses import dataclass
from urllib.parse import urlsplit

from telegram_emoji import rich_emoji


@dataclass(frozen=True)
class RichMessageCopy:
    rich_html: str
    fallback_html: str


def _safe_media_urls(values: list[str] | tuple[str, ...] | None = None) -> list[str]:
    raw_values = list(values or [])
    if not raw_values:
        raw_values = (os.getenv("TG_RICH_ONBOARDING_MEDIA_URLS") or "").split(",")

    result: list[str] = []
    for raw in raw_values:
        value = str(raw or "").strip()
        parsed = urlsplit(value)
        if parsed.scheme != "https" or not parsed.netloc or value in result:
            continue
        result.append(value)
        if len(result) == 10:
            break
    return result if len(result) >= 2 else []


def _slideshow_html(media_urls: list[str] | tuple[str, ...] | None = None) -> str:
    urls = _safe_media_urls(media_urls)
    if not urls:
        return ""
    slides = "".join(f'<img src="{html.escape(url, quote=True)}"/>' for url in urls)
    return (
        f"<tg-slideshow>{slides}"
        "<figcaption>Как выглядит подключение в POKROV</figcaption>"
        "</tg-slideshow>"
    )


def home_copy(
    *,
    returning: bool = False,
    new_user: bool = False,
    show_trial: bool = True,
) -> RichMessageCopy:
    if new_user:
        return RichMessageCopy(
            rich_html=(
                f"<h2>{rich_emoji('brand')} POKROV VPN</h2>"
                "<p><b>YouTube, TikTok и ChatGPT — одной кнопкой.</b></p>"
                "<p>Для Android и Windows. 5 дней бесплатно, карта не нужна.</p>"
                "<footer>Выберите своё устройство.</footer>"
            ),
            fallback_html=(
                "🛡 <b>POKROV VPN</b>\n\n"
                "<b>YouTube, TikTok и ChatGPT — одной кнопкой.</b>\n\n"
                "Для Android и Windows. 5 дней бесплатно, карта не нужна.\n\n"
                "Выберите своё устройство."
            ),
        )
    elif returning:
        title = "С возвращением в POKROV"
        lead = "Продолжите с главного действия или проверьте свой доступ."
    else:
        title = "POKROV"
        lead = "Выберите один следующий шаг."

    access_note = (
        "5 дней бесплатно, карта не нужна."
        if show_trial
        else "Срок и продление доступны в приложении и кабинете."
    )
    return RichMessageCopy(
        rich_html=(
            f"<h2>{rich_emoji('brand')} {html.escape(title)}</h2>"
            f"<p><b>{html.escape(lead)}</b></p>"
            f"<footer>{html.escape(access_note)}</footer>"
        ),
        fallback_html=(
            f"🛡 <b>{html.escape(title)}</b>\n\n"
            f"{html.escape(lead)}\n\n"
            f"{html.escape(access_note)}"
        ),
    )


def tariff_choice_copy(
    *,
    show_trial: bool,
    paid_count: int,
    paid_list: str,
    trial_days: int,
    paid_device_limit: int,
    savings: list[str] | tuple[str, ...] = (),
) -> RichMessageCopy:
    paid_locations = max(1, int(paid_count or 0))
    paid_list_safe = html.escape(str(paid_list or "доступные локации"))
    savings_safe = ", ".join(html.escape(str(item)) for item in savings if str(item).strip())
    trial_rich = ""
    trial_fallback = ""
    if show_trial:
        trial_rich = (
            f"<p><mark>{rich_emoji('free')} {int(trial_days)} дней бесплатно в приложении</mark><br/>"
            "Безлимитный трафик · 1 устройство · без карты</p>"
        )
        trial_fallback = (
            f"🆓 <b>{int(trial_days)} дней бесплатно в приложении</b>\n"
            "Безлимитный трафик · 1 устройство · без карты\n\n"
        )

    savings_rich = (
        f"<p><b>Экономия на длинных сроках:</b> {savings_safe}</p>"
        if savings_safe
        else ""
    )
    savings_fallback = (
        f"\n<b>Экономия на длинных сроках:</b> {savings_safe}\n"
        if savings_safe
        else ""
    )
    return RichMessageCopy(
        rich_html=(
            f"<h2>{rich_emoji('payment')} Выберите срок</h2>"
            "<p><b>Цена сразу указана на кнопке.</b> Чем длиннее срок, тем выгоднее месяц.</p>"
            f"{trial_rich}"
            "<table bordered striped>"
            "<tr><th>Доступ</th><th>Что входит</th></tr>"
            f"<tr><td>Платный</td><td>{paid_locations} локаций · до {int(paid_device_limit)} устройств</td></tr>"
            f"<tr><td>Локации</td><td>{paid_list_safe}</td></tr>"
            "</table>"
            f"{savings_rich}"
            "<details><summary>Что произойдёт после выбора</summary>"
            "<ol><li>Покажем доступный способ оплаты</li>"
            "<li>Включим срок на этом аккаунте</li>"
            "<li>Останется открыть POKROV и нажать «Подключить»</li></ol>"
            "</details>"
            "<footer>Выберите вариант ниже.</footer>"
        ),
        fallback_html=(
            "💳 <b>Выберите срок</b>\n\n"
            "<b>Цена сразу указана на кнопке.</b> Чем длиннее срок, тем выгоднее месяц.\n\n"
            f"{trial_fallback}"
            f"🌐 Платный доступ: {paid_locations} локаций · до {int(paid_device_limit)} устройств\n"
            f"Локации: {paid_list_safe}\n"
            f"{savings_fallback}\n"
            "<blockquote expandable><b>Что произойдёт после выбора</b>\n"
            "1. Покажем доступный способ оплаты\n"
            "2. Включим срок на этом аккаунте\n"
            "3. Останется открыть POKROV и нажать «Подключить»</blockquote>\n\n"
            "Выберите вариант ниже."
        ),
    )


def long_tariffs_copy() -> RichMessageCopy:
    return RichMessageCopy(
        rich_html=(
            f"<h2>{rich_emoji('crown')} Доступ надолго</h2>"
            "<p><b>Один платёж — и реже вспоминать о продлении.</b></p>"
            "<ul><li>6 месяцев — уверенный выбор</li>"
            "<li>9 месяцев — большой запас</li>"
            "<li>12 месяцев — максимальная выгода</li></ul>"
            "<footer>Точная цена и скидка указаны на кнопках.</footer>"
        ),
        fallback_html=(
            "👑 <b>Доступ надолго</b>\n\n"
            "<b>Один платёж — и реже вспоминать о продлении.</b>\n\n"
            "• 6 месяцев — уверенный выбор\n"
            "• 9 месяцев — большой запас\n"
            "• 12 месяцев — максимальная выгода\n\n"
            "Точная цена и скидка указаны на кнопках."
        ),
    )


def device_picker_copy(
    media_urls: list[str] | tuple[str, ...] | None = None,
) -> RichMessageCopy:
    return RichMessageCopy(
        rich_html=(
            f"<h2>{rich_emoji('device')} С какого устройства начинаем?</h2>"
            "<p><b>Выберите платформу — покажем только нужные шаги.</b></p>"
            "<ol><li>Установить POKROV</li>"
            "<li>Войти через почту или Telegram</li>"
            "<li>Нажать «Подключить»</li></ol>"
            f"{_slideshow_html(media_urls)}"
            "<footer>Ручная ссылка остаётся запасным вариантом.</footer>"
        ),
        fallback_html=(
            "💻 <b>С какого устройства начинаем?</b>\n\n"
            "Выберите платформу — покажем только нужные шаги.\n\n"
            "1. Установить POKROV\n"
            "2. Войти через почту или Telegram\n"
            "3. Нажать «Подключить»\n\n"
            "Ручная ссылка остаётся запасным вариантом."
        ),
    )


def help_triage_copy() -> RichMessageCopy:
    return RichMessageCopy(
        rich_html=(
            f"<h2>{rich_emoji('support')} Чем помочь?</h2>"
            "<p><b>Выберите ситуацию — покажем один следующий шаг.</b></p>"
            "<ul><li>Подключить устройство</li>"
            "<li>Активировать код или открыть личную ссылку</li>"
            "<li>Разобраться, почему подключение не работает</li></ul>"
            "<footer>Давайте без терминов — только следующий шаг.</footer>"
        ),
        fallback_html=(
            "🆘 <b>Чем помочь?</b>\n\n"
            "Выберите ситуацию — покажем один следующий шаг.\n\n"
            "• Подключить устройство\n"
            "• Активировать код или открыть личную ссылку\n"
            "• Разобраться, почему подключение не работает\n\n"
            "Давайте без терминов — только следующий шаг."
        ),
    )


def settings_copy() -> RichMessageCopy:
    return RichMessageCopy(
        rich_html=(
            f"<h2>{rich_emoji('settings')} Ещё</h2>"
            "<p>Здесь находятся запасные и редкие действия.</p>"
            "<ul><li>Ручное подключение и инструкции</li>"
            "<li>Бонусы, подарки и промокоды</li>"
            "<li>Сброс личной ссылки при необходимости</li></ul>"
            "<details><summary>Когда нужен сброс ссылки?</summary>"
            "Только если ссылка попала к постороннему или перестала работать после обращения в поддержку."
            "</details>"
        ),
        fallback_html=(
            "⚙️ <b>Ещё</b>\n\n"
            "Здесь находятся запасные и редкие действия.\n\n"
            "• Ручное подключение и инструкции\n"
            "• Бонусы, подарки и промокоды\n"
            "• Сброс личной ссылки при необходимости\n\n"
            "<blockquote expandable><b>Когда нужен сброс ссылки?</b>\n"
            "Только если ссылка попала к постороннему или перестала работать после обращения в поддержку."
            "</blockquote>"
        ),
    )


def support_hub_copy() -> RichMessageCopy:
    return RichMessageCopy(
        rich_html=(
            f"<h2>{rich_emoji('message')} Поддержка POKROV</h2>"
            "<p><b>Опишите проблему одним сообщением.</b> "
            "Если есть ошибка — приложите скриншот.</p>"
            "<ul><li>Сначала можно открыть частые вопросы</li>"
            "<li>Диагностика покажет статус доступа</li>"
            "<li>Обращение продолжится в службе заботы</li></ul>"
        ),
        fallback_html=(
            "💬 <b>Поддержка POKROV</b>\n\n"
            "<b>Опишите проблему одним сообщением.</b> Если есть ошибка — приложите скриншот.\n\n"
            "• Сначала можно открыть частые вопросы\n"
            "• Диагностика покажет статус доступа\n"
            "• Обращение продолжится в службе заботы"
        ),
    )


def help_copy() -> RichMessageCopy:
    return RichMessageCopy(
        rich_html=(
            f"<h3>{rich_emoji('faq')} Помощь. Частые вопросы</h3>"
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
            f"<h3>{rich_emoji('success')} Оплата прошла — доступ включён</h3>"
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
