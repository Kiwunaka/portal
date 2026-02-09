# WebApp (Telegram LK)

This is a Vite + React app meant to be served as static files.

## Dev

```bash
cd webapp
npm install
npm run dev
```

## Build

```bash
cd webapp
npm install
npm run build
```

Build output is in `webapp/dist/`.

## Environment

Optionally set:
- `VITE_PUBLIC_API_BASE_URL` (default: tries same-origin first, then falls back to `https://<host>:2096`)
- `VITE_WEBAPP_ENABLE_HAPTIC` (`true|false`, fallback from backend feature flags)
- `VITE_WEBAPP_ENABLE_LOTTIE` (`true|false`, fallback from backend feature flags)
