# Portal WebApp (Next App Router)

Личный кабинет PORTAL собран как Next static app.

## Локальный запуск

```bash
npm install
npm run dev
```

## Прод-сборка

```bash
npm run build
```

`next.config.ts` настроен на:
- `output: "export"`
- `trailingSlash: true`
- `basePath: "/webapp"`
- `assetPrefix: "/webapp"`

Готовые статик-файлы появляются в `webapp/out`.

## Ключевые ENV (frontend)

- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_TELEGRAM_BOT_URL`
- `NEXT_PUBLIC_TELEGRAM_LOGIN_BOT` (optional override)

Для плавного перехода поддерживаются fallback-переменные `VITE_*`.
Если `NEXT_PUBLIC_TELEGRAM_LOGIN_BOT` не задан, Telegram Login Widget берёт username из `NEXT_PUBLIC_TELEGRAM_BOT_URL`.

## Auth flows

- Внутри Telegram: авторизация через `initData`.
- В браузере: Telegram Login Widget -> `POST /api/auth/telegram/web-login`.
