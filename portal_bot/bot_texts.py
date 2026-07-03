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
        "🛡 *POKROV*\n\n"
        "Я помогу подключить устройство, продлить доступ и ответить на вопросы.\n\n"
        "Выберите, что сделать:"
    ),
    "bot.menu.returning": (
        "👋 *С возвращением в POKROV!*\n\n"
        "Всё на месте. Выберите, что сделать:"
    ),
    "bot.menu.new_user": (
        "👋 *Добро пожаловать в POKROV*\n\n"
        "Настроим доступ за пару минут: установите приложение, войдите и нажмите «Подключить».\n\n"
        "С чего начнём?"
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
        "⛔️ *Сейчас доступа нет*\n\n"
        "Начните с 5 дней бесплатно — карту не просим. Понравится — выберите срок, длинные выходят выгоднее."
    ),
    # --- Tariffs / payment ---
    "bot.tariffs.long": (
        "💎 *Долгие планы*\n\n"
        "Чем длиннее срок, тем дешевле выходит месяц. Оплатили один раз — и надолго забыли о продлении."
    ),
    "bot.payment.success": (
        "✅ *Оплата прошла.* Доступ уже обновляется в этом аккаунте. "
        "Откройте POKROV и нажмите «Подключить» — на этом всё."
    ),
    # --- Onboarding / instructions ---
    "bot.instruction.pick_device": (
        "📱 *С какого устройства начинаем?*\n\n"
        "Выберите своё — покажу короткий путь: установить, войти, нажать «Подключить»."
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
        "Если приложение недоступно, есть запасной путь: установите Karing или Happ "
        "и добавьте личную ссылку из кабинета POKROV."
    ),
    "bot.instruction.platform_windows": (
        "💻 *Windows*\n\n"
        "1. Скачайте POKROV для Windows\n"
        "2. Войдите через почту или Telegram\n"
        "3. Нажмите «Подключить»\n\n"
        "Если приложение недоступно, есть запасной путь: установите Karing или Happ "
        "и добавьте личную ссылку из кабинета POKROV."
    ),
    "bot.instruction.platform_macos": (
        "🍎 *macOS*\n\n"
        "1. Откройте страницу приложений\n"
        "2. Посмотрите актуальный статус macOS\n"
        "3. Для подключения прямо сейчас используйте ручную ссылку в совместимом приложении"
    ),
    "bot.instruction.step_access": (
        "✅ *Приложение есть — включим доступ*\n\n"
        "Начните с 5 дней бесплатно, карту не просим. Хотите сразу надолго — "
        "выберите срок ниже, после оплаты всё включится само.\n\n"
        "Останется войти и нажать «Подключить»."
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
        "🌐 *Кабинет POKROV*\n\n"
        "Здесь аккаунт, оплата, загрузки и ссылки подключения. Подключаться удобнее "
        "из приложения: войдите в тот же аккаунт, и всё подтянется само."
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
