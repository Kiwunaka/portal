# POKROV Atlas Glass Route Map

Last updated: 2026-05-26

Primary user flow: 5-day trial -> install application -> first connection.

Tone: formal Russian `вы`, calm and practical.

## Marketing

- `/`: primary CTA should lead to application start/install; payment remains secondary to app-first trial even though Lava.top is beta-ready.
- `/checkout/`: keep Lava.top-only beta copy explicit; degraded/payment-unavailable copy appears only when the live provider catalog is blocked.
- `/install/`, `/devices/`, `/mobile/`: installation-first routes with cabinet/support continuation, not fake public download claims.
- `/telegram/`, `/youtube/`, `/tiktok/`, `/offer/`: intent pages must avoid performance guarantees such as “без пауз” when they read as absolute promises.
- `/privacy/`: legal page with simple links back to cabinet, support, and offer/privacy cross-links.

## Cabinet

- `/`: login/continue state, no theatrical progress.
- `/dashboard/`: status, remaining time, next action, install/device path, support path.
- `/subscription/`: trial, renewal, Telegram +10 days, Lava.top beta payment or temporary provider-unavailable state.
- `/subscription/checkout/`: Russian Lava.top beta copy, temporary provider-unavailable copy, and native cabinet continuation.
- `/downloads/` and `/dashboard/downloads/`: honest Android/Windows outside-store beta or account-gated state.
- `/devices/`: current device status and app-first connection path.
- `/statistics/`: useful status/activity without fake precision or raw transport jargon.
- `/settings/` and `/profile/`: identity, automatic username sync, recovery/manual sync, theme preference.
- `/redeem/`: simple key/code entry with clear success/failure.
- `/support/`, `/support/thread/`, `/support/legal/`: clear support route, issue state, retry/help.

## Admin

Routes: `/admin/`, `/admin/dashboard/`, `/admin/users/`, `/admin/network/`, `/admin/nodes/`, `/admin/tickets/`, `/admin/bonuses/`, `/admin/promos/`, `/admin/referrals/`, `/admin/broadcast/`, `/admin/payments/`, `/admin/release/`.

Admin should be dense and operational: tables, filters, status badges, risk indicators, retry states, and audit/context panels. Admin copy may be technical.

## Phrase Bank

- Primary: “Начать с приложения”, “Установить приложение”, “Запустить 5 дней бесплатно”, “Открыть загрузки в кабинете”, “Подключиться на этом устройстве”.
- Secondary: “Открыть кабинет”, “Выбрать срок”, “Применить ключ”, “Написать в поддержку”, “Забрать +10 дней в Telegram”.
- Loading: “Открываем кабинет”, “Проверяем доступ”, “Загружаем ваши данные”, “Подтягиваем доступные сборки”.
- Empty: “Пока здесь пусто”, “Устройства появятся после первого входа в приложение”, “Обращений пока нет”.
- Error/blocked: “Не удалось обновить данные”, “Повторить”, “Открыть поддержку”, “Оплата временно недоступна”, “Загрузка недоступна для этого аккаунта”.

## Forbidden Direction

Avoid public “VPN-сервис”, unsupported platform release claims, `1.0.0`, production payment maturity claims, app-store claims, trusted Windows signing claims, raw Android audit claims, RU-origin readiness claims, informal `ты/твой`, and hype such as “магия скорости” or absolute “без пауз” guarantees.
