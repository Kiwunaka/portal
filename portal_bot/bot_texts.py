"""Central access point for the main bot's user-facing copy.

Keys resolve through copy/catalog.ru.json at call time (no import-time
freezing), so catalog edits apply on restart without touching handlers.
The fallbacks below are the safety net when the catalog file is missing
or a key is absent; keep them in sync with the catalog values.

Admin-only keys stay fallback-only on purpose: the public copy guardrail
tests scan catalog `ru` values, and operator texts (e.g. Stars revenue)
must not leak into governed public copy.
"""

from copy_catalog import get_copy_text

_FALLBACKS: dict[str, str] = {
    # --- Main menu / start ---
    "bot.menu.home": (
        "🛡 *POKROV VPN*\n\n"
        "YouTube, TikTok, ChatGPT, соцсети и нужные сайты — на Android и Windows. "
        "Управляйте подключением, тарифом и устройствами прямо здесь.\n\n"
        "Выберите действие:"
    ),
    "bot.menu.returning": (
        "👋 *POKROV готов к работе*\n\n"
        "Подключайтесь, проверьте доступ или выберите выгодный срок продления:"
    ),
    "bot.menu.new_user": (
        "🚀 *POKROV VPN — интернет без ограничений*\n\n"
        "YouTube, TikTok, ChatGPT, соцсети и сайты — на Android и Windows.\n\n"
        "✅ 5 дней бесплатно, без карты\n"
        "✅ Безлимитный трафик на платных тарифах\n"
        "✅ До 5 устройств\n"
        "✅ От 99 ₽, без автосписаний\n\n"
        "Попробуйте прямо сейчас:"
    ),
    "bot.menu.all_actions": (
        "⚙️ *Все действия*\n\n"
        "Выберите ближайший шаг:"
    ),
    "bot.settings.more": (
        "⚙️ *Ещё*\n\n"
        "Запасные инструменты: ручное подключение, бонусы, коды и сброс личной ссылки."
    ),
    # --- Access status ---
    "bot.status.card": (
        "👤 *Ваш доступ*\n\n"
        "Статус: {status_icon} *{status_text}*\n"
        "Тариф: {plan_label}\n"
        "Действует до: {expiry}\n\n"
        "Продлить можно в кабинете или прямо здесь.\n"
        "Номер для поддержки: `{tg_id}`"
    ),
    "bot.status.none": (
        "🔥 *Включите POKROV бесплатно*\n\n"
        "5 дней за 0 ₽ — без карты. YouTube, TikTok, ChatGPT и другие сервисы уже ждут.\n\n"
        "После теста — безлимитный трафик от 99 ₽ и никаких автосписаний."
    ),
    # --- Tariffs / payment ---
    "bot.tariffs.long": (
        "💎 *Максимум выгоды на длинном сроке*\n\n"
        "Чем дольше доступ, тем ниже цена месяца. Годовой план экономит 45% против помесячной оплаты: "
        "платите один раз и пользуетесь без постоянных продлений."
    ),
    "bot.payment.success": (
        "✅ *Готово — доступ оплачен.* Мы уже обновляем ваш аккаунт. "
        "Откройте POKROV, нажмите «Подключить» и пользуйтесь."
    ),
    # --- Onboarding / instructions ---
    "bot.instruction.pick_device": (
        "🚀 *Выберите устройство — и переходите к подключению*\n\n"
        "Android или Windows: официальный файл, вход и одна кнопка. После установки заберите 5 дней бесплатно."
    ),
    "bot.instruction.platform_ios": (
        "🍏 *iPhone / iPad*\n\n"
        "1. Откройте страницу приложений\n"
        "2. Установите подходящее приложение для iPhone\n"
        "3. Если профиль не подтянулся сам, вернитесь сюда за ручной ссылкой"
    ),
    "bot.instruction.platform_android": (
        "🤖 *Android*\n\n"
        "1. Скачайте приложение POKROV\n"
        "2. Войдите через почту или Telegram\n"
        "3. Нажмите «Подключить»\n\n"
        "Если приложение недоступно, есть запасной путь: установите Hiddify "
        "и добавьте личную ссылку из кабинета POKROV. Для Happ используйте отдельную готовую кнопку или QR в ручной настройке."
    ),
    "bot.instruction.platform_windows": (
        "💻 *Windows*\n\n"
        "1. Скачайте POKROV для Windows\n"
        "2. Войдите через почту или Telegram\n"
        "3. Нажмите «Подключить»\n\n"
        "Если приложение недоступно, есть запасной путь: установите Hiddify "
        "и добавьте личную ссылку из кабинета POKROV. Для Happ используйте отдельную готовую кнопку или QR в ручной настройке."
    ),
    "bot.instruction.platform_macos": (
        "🍎 *macOS*\n\n"
        "1. Откройте страницу приложений\n"
        "2. Посмотрите актуальный статус macOS\n"
        "3. Для подключения прямо сейчас используйте ручную ссылку в совместимом приложении"
    ),
    "bot.instruction.step_access": (
        "🔥 *Остался один шаг до подключения*\n\n"
        "Заберите 5 дней бесплатно — без карты и обязательств. Или сразу выберите выгодный срок: "
        "после оплаты доступ обновится автоматически.\n\n"
        "Войдите в POKROV, нажмите «Подключить» и проверьте любимые сервисы."
    ),
    # --- Help / support ---
    "bot.help.triage": (
        "🧭 *Давайте без терминов.*\n\n"
        "Выберите, что у вас сейчас, — покажу один следующий шаг и не буду грузить настройками."
    ),
    "bot.support.hub": (
        "🆘 *Поддержка POKROV*\n\n"
        "Опишите, что случилось, одним сообщением — разберёмся и доведём до решения. "
        "Частые вопросы уже собраны ниже."
    ),
    "bot.faq.menu": (
        "❓ *Частые вопросы*\n\n"
        "Собрали пошаговые ответы на всё, с чем обычно приходят. "
        "Выберите тему — покажу короткую инструкцию."
    ),
    "bot.cabinet.intro": (
        "🌐 *Весь POKROV в одном кабинете*\n\n"
        "Доступ, устройства, тарифы, загрузки и поддержка — в одном месте. "
        "Войдите в приложении в тот же аккаунт, и данные подтянутся автоматически."
    ),
    # --- Admin (fallback-only, never in the public catalog) ---
    "bot.admin.stats": (
        "📊 *Центр управления*\n\n"
        "👥 Пользователей: `{total}`\n"
        "🟢 Активных: `{active}`\n"
        "💰 Оборот: `{stars}` Stars"
    ),
}


def bot_text(key: str, **variables) -> str:
    """Resolve bot copy by catalog key with local fallback and formatting."""
    return get_copy_text(key, _FALLBACKS.get(key, ""), variables=variables or None)
