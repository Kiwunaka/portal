# POKROV WebApp

Last updated: 2026-04-22

## Document Status

This file is the local authority for `webapp/` and the browser cabinet/admin surface at `https://app.pokrov.space/`.

## Purpose

`webapp/` is the continuation surface for:

- browser entry and web-login continuation
- personal cabinet flows for status, subscription, devices, downloads, and support
- hosted key-first checkout continuation
- the primary admin operator surface

It is not the public marketing or SEO surface. Public acquisition pages live in `marketing/` at `https://pokrov.space/`.

## Current Surface Map

Current user-facing route families in `webapp/src/app/`:

- `/` for browser entry, Telegram web-login, and bot handoff continuation
- `/dashboard/` for the main cabinet snapshot
- `/subscription/` for subscription state and renewal entry
- `/subscription/checkout/` for renewal continuation into the hosted activation-key checkout flow
- `/redeem/` for activation-key lookup and redeem inside the cabinet
- `/devices/` for device visibility
- `/dashboard/downloads/` for app-download continuation
- `/support/` plus support thread/legal routes
- `/pricing/` only as a compatibility continuation alias; it must not become a public pricing surface again

Current operator routes:

- `/admin/`
- `/admin/dashboard/`
- `/admin/users/`
- `/admin/nodes/`
- `/admin/tickets/`
- `/admin/bonuses/`
- `/admin/promos/`
- `/admin/referrals/`
- `/admin/broadcast/`

## Surface Boundary

Keep the public/browser split explicit:

- `marketing/` owns the homepage, public `/checkout/`, offer/privacy pages, and indexable SEO landing pages
- `webapp/` starts when the user needs session continuation, cabinet actions, redeem, support, renewal, or admin tooling
- public `Open cabinet` CTA should point to `https://app.pokrov.space/`
- public pricing and acquisition belong to `marketing/`; cabinet checkout is continuation-only and should defer to the hosted key-first flow

## Runtime Contract

Canonical browser/runtime wiring:

- API base: `https://api.pokrov.space`
- browser cabinet URL: `https://app.pokrov.space`
- public config delivery host: `https://connect.pokrov.space`
- hosted checkout host: `https://pay.pokrov.space/checkout/`

Rules:

- frontend must not treat `https://app.pokrov.space/api/*` HTML fallback as valid API success
- user-facing cabinet copy should show one public `ссылка подключения` and one QR built from the same URL
- `?format=plain` remains hidden compatibility-only behavior and must stay out of normal cabinet UX
- `connect.pokrov.space` is for config delivery, not for public acquisition or payment entry
- cabinet checkout must not drift into a second public paywall or direct raw-link delivery story

## Frontend Environment

Primary public env keys:

- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_TELEGRAM_BOT_URL`
- `NEXT_PUBLIC_TELEGRAM_LOGIN_BOT`
- `NEXT_PUBLIC_WEBAPP_URL`
- `NEXT_PUBLIC_CONNECT_URL`
- `NEXT_PUBLIC_CHECKOUT_PAGE_URL`
- `NEXT_PUBLIC_APP_ANDROID_PLAY_URL`
- `NEXT_PUBLIC_APP_ANDROID_APK_URL`
- `NEXT_PUBLIC_APP_WINDOWS_EXE_URL`
- `NEXT_PUBLIC_APP_DOCS_URL`

Compatibility note:

- `VITE_*` fallback env names still exist for smoother migration, but new work should prefer the `NEXT_PUBLIC_*` names

## Build Output

Current Next.js export expectations:

- `next.config.ts` uses `output: "export"`
- `trailingSlash: true`
- `basePath` is not used
- `assetPrefix` is not used
- generated static files are emitted to `webapp/out`

## Auth Continuation

Current supported auth paths:

- inside Telegram: authorization through `initData`
- in browser: Telegram Login Widget -> `POST /api/auth/telegram/web-login`
- from bot handoff: `web_session_token` should open the cabinet without manual token copy/paste

## Local Run

```powershell
npm.cmd install
npm.cmd run dev
```

## Verification

```powershell
npm.cmd run build
npm.cmd run test:e2e
npm.cmd run test:e2e:admin
```

Verification rule:

- run `npm.cmd run build` on every webapp task
- run `npm.cmd run test:e2e` when cabinet, pricing, renewal, downloads, support, or login flows change
- run `npm.cmd run test:e2e:admin` when admin routes, permissions, dashboards, or operator actions change
- `npm.cmd run test:e2e` starts an isolated Playwright dev server on port `3102`, and `npm.cmd run test:e2e:admin` uses port `3101`; both scripts clear a stale port owner first so browser checks do not reuse a stale local `next dev` session

## Related Canonical Docs

- [Product Overview](C:/Users/kiwun/Documents/ai/VPN/docs/product/portal-vpn-product.md)
- [System Overview](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/system-overview.md)
- [App-First And Bonus Flows](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/app-first-and-bonus-flows.md)
- [Developer Guide](C:/Users/kiwun/Documents/ai/VPN/docs/developer/developer-guide.md)
