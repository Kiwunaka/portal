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
- `NEXT_PUBLIC_TELEGRAM_LOGIN_BOT`
- `NEXT_PUBLIC_TELEGRAM_BOT_URL`

Для плавного перехода поддерживаются fallback-переменные `VITE_*`.

## Auth flows

- Внутри Telegram: авторизация через `initData`.
- В браузере: Telegram Login Widget -> `POST /api/auth/telegram/web-login`.
