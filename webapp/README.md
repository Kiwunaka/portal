# POKROV WebApp (Next App Router)

Личный кабинет POKROV собран как Next static app для `https://app.pokrov.space/`.

## Локальный запуск

```bash
npm.cmd install
npm.cmd run dev
```

## Прод-сборка

```bash
npm.cmd run build
npm.cmd run test:e2e:admin
```

`next.config.ts` настроен на:

- `output: "export"`
- `trailingSlash: true`
- `basePath` не используется
- `assetPrefix` не используется

Готовые статик-файлы появляются в `webapp/out`.

## Ключевые ENV (frontend)

- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_TELEGRAM_BOT_URL`
- `NEXT_PUBLIC_TELEGRAM_LOGIN_BOT` (optional override)

Для плавного перехода поддерживаются fallback-переменные `VITE_*`.
Если `NEXT_PUBLIC_TELEGRAM_LOGIN_BOT` не задан, Telegram Login Widget берёт username из `NEXT_PUBLIC_TELEGRAM_BOT_URL`.

Канонический API для браузерного кабинета:

- `https://api.pokrov.space`

Важно:

- фронтенд не должен считать `https://app.pokrov.space/api/*` валидным API fallback
- если с app origin приходит HTML вместо JSON, это считается ошибкой auth/runtime wiring, а не успешным ответом

## Auth flows

- Внутри Telegram: авторизация через `initData`.
- В браузере: Telegram Login Widget -> `POST /api/auth/telegram/web-login`.
- Из бота: `web_session_token` handoff должен открывать кабинет без ручного копирования токена.
