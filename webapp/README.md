# POKROV WebApp

Last updated: 2026-04-25

## Document Status

This file is the local authority for `webapp/` and the browser cabinet/admin surface at `https://app.pokrov.space/`.

## Purpose

`webapp/` is the continuation-first cabinet and admin surface for:

- browser entry and web-login continuation from app handoff and Telegram today, with public email continuation marked `soon`
- personal cabinet flows with top-level IA `Dashboard`, `Subscription`, `Devices`, `Statistics`, and `Support`
- task routes for downloads, redeem, and hosted-checkout continuation inside that same cabinet model
- hosted key-first checkout continuation
- the primary admin operator surface

It is not the public marketing or SEO surface, and it must not become a second landing page. Public acquisition pages live in `marketing/` at `https://pokrov.space/`.

## Current Surface Map

Current user-facing route families in `webapp/src/app/`:

- `/` for browser entry, Telegram web-login, and bot handoff continuation
- `/dashboard/` for the main cabinet snapshot
- `/subscription/` for subscription state, renewal entry, and the main `Тарифы и оплата` surface
- `/devices/` for device visibility
- `/statistics/` only as a compatibility redirect to `/dashboard/`, where usage and account visibility summaries now live
- `/downloads/` for app-download continuation and install handoff
- `/support/` plus support thread/legal routes
- `/settings/` for account links, Telegram bonus actions, and safe continuation settings
- `/profile/` only as a compatibility redirect to `/settings/`
- `/dashboard/downloads/` only as a compatibility redirect to `/downloads/`
- `/redeem/` for activation-key lookup and redeem inside the cabinet
- `/subscription/checkout/` for renewal continuation into the hosted activation-key checkout flow
- `/pricing/` only as a compatibility continuation alias redirecting to `/subscription/`

Current operator routes:

- `/admin/`
- `/admin/dashboard/`
- `/admin/users/`
- `/admin/network/`
- `/admin/nodes/`
- `/admin/tickets/`
- `/admin/bonuses/`
- `/admin/promos/`
- `/admin/referrals/`
- `/admin/broadcast/`

## Surface Boundary

Keep the public/browser split explicit:

- `marketing/` owns the homepage, public `/checkout/`, offer/privacy pages, and indexable SEO landing pages
- `marketing/` keeps checkout-first CTA priority for public traffic; install help and cabinet-open links are secondary intent-driven exits
- `webapp/` starts when the user needs session continuation, cabinet actions, redeem, support, renewal, statistics, or admin tooling
- browser entry should route known or newly verified users into the same cabinet session model whether they arrived from app handoff, Telegram, or the future marked-`soon` email lane
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
- cabinet entry is continuation-first and must not be documented or styled like a second acquisition surface
- user-facing cabinet copy should show one public `ссылка подключения` and one QR built from the same URL
- `?format=plain` remains hidden compatibility-only behavior and must stay out of normal cabinet UX
- `connect.pokrov.space` is for config delivery, not for public acquisition or payment entry
- cabinet checkout must not drift into a second public paywall or direct raw-link delivery story
- public email continuation must stay explicitly marked `soon` until sender readiness, delivery confirmation, and public launch are live
- marketing and cabinet copy should inherit governed text from `shared/copy.ts`, `copy/catalog.ru.json`, and `shared/design-tokens.json` instead of inventing separate public messaging

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
- compatibility aliases such as `/pricing/`, `/statistics/`, and `/dashboard/downloads/` should resolve through a server redirect when the export server supports it, with fast client-side `router.replace` fallback pages for plain static hosting

## Auth Continuation

Current supported auth paths:

- inside Telegram: authorization through `initData`
- in browser: Telegram Login Widget -> `POST /api/auth/telegram/web-login`
- in browser: additive email continuation remains a marked-`soon` lane until delivery readiness and launch are live
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
- `npm.cmd run test:e2e` now builds the static export and serves `webapp/out` on port `3102` through `webapp/scripts/serve_export.py`, so the full browser pack runs against the same export-style surface that deploy uses
- `npm.cmd run test:e2e:admin` uses the same build-plus-export-server flow on port `3101`, which removes the standalone admin flake that came from `next dev` cold-start and HMR reload noise
- both release-style Playwright scripts clear a stale port owner first and disable server reuse so local browser checks do not inherit an old process or stale session bootstrap

## Related Canonical Docs

- [Product Overview](C:/Users/kiwun/Documents/ai/VPN/docs/product/portal-vpn-product.md)
- [System Overview](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/system-overview.md)
- [App-First And Bonus Flows](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/app-first-and-bonus-flows.md)
- [Developer Guide](C:/Users/kiwun/Documents/ai/VPN/docs/developer/developer-guide.md)
