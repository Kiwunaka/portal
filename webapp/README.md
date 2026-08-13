# POKROV WebApp

Last updated: 2026-08-13

## Document Status

Document class: CANONICAL. This file is the local authority for `webapp/`, the browser cabinet, and its retained admin parity fallback at `https://app.pokrov.space/`.

## Purpose

`webapp/` owns the continuation-first cabinet plus the retained admin parity fallback. The cabinet serves:

- browser entry and web-login continuation from app handoff, Telegram, and email when the runtime email delivery gate is fully ready
- personal cabinet flows with visible IA `Главная`, `Доступ`, `Помощь`, and `Аккаунт`
- task/detail routes for devices, statistics, downloads, redeem, support threads/legal docs, and hosted-checkout continuation inside that same compact cabinet model
- hosted key-first checkout continuation
- retained legacy admin routes while the dedicated `adminapp/` reaches full parity

It is not the public marketing or SEO surface, and it must not become a second landing page. Public acquisition pages live in `marketing/` at `https://pokrov.space/`.

## Current Surface Map

Current user-facing route families in `webapp/src/app/`:

- `/` for browser entry, Telegram web-login, and bot handoff continuation
- visible cabinet nav:
  - `Главная` -> `/dashboard/`
  - `Доступ` -> `/subscription/`
  - `Помощь` -> `/support/`
  - `Аккаунт` -> `/settings/`
- `/devices/` for device visibility as a `Главная` detail route
- `/statistics/` for usage and account visibility summaries as a `Главная` detail route
- `/downloads/` for app-download continuation and install handoff as a `Доступ` task route
- `/support/` plus support thread/legal routes for ticket continuation and documents
- `/settings/` for account links, Telegram bonus actions, and safe continuation settings
- `/rewards/` for the paid weekly wheel, activity calendar, and reward history as an `Аккаунт` detail route
- `/profile/` only as a compatibility redirect to `/settings/`
- `/dashboard/downloads/` only as a compatibility redirect to `/downloads/`
- `/redeem/` for activation-key lookup and redeem inside the cabinet
- `/subscription/checkout/` for renewal continuation into the hosted activation-key checkout flow
- `/pricing/` only as a compatibility continuation alias redirecting to `/subscription/`

Cabinet routes live under `webapp/src/app/(dashboard)/`. The route group is URL-invisible and owns the `CabinetShell`.

Current retained operator routes:

- `/admin/`
- `/admin/dashboard/`
- `/admin/users/`
- `/admin/network/`
- `/admin/nodes/`
- `/admin/tickets/`
- `/admin/bonuses/`
- `/admin/promos/`
- `/admin/referrals/`
- `/admin/payments/`
- `/admin/release/`
- `/admin/broadcast/`

Operator routes live under `webapp/src/app/(admin)/admin/`. The route group is URL-invisible and remains a parity fallback only. New primary operator work belongs in `adminapp/` for `https://admin.pokrov.space/`; delete these routes only after the dedicated panel covers every workflow and passes the parity checklist.

## Surface Boundary

Keep the public/browser split explicit:

- `marketing/` owns the homepage, public `/checkout/`, offer/privacy pages, and indexable SEO landing pages
- `marketing/` keeps trial, install, and first connection as the primary public path; checkout stays an honest continuation after the user has checked the product or when plan context is explicit
- `webapp/` starts when the user needs session continuation, cabinet actions, redeem, support, renewal, or statistics
- `adminapp/` starts when the operator needs admin tooling at `https://admin.pokrov.space/`
- browser entry should route known or newly verified users into the same cabinet session model whether they arrived from app handoff, Telegram, or the public email lane when delivery is fully ready
- browser entry heading and subtitle follow the active email action (`Вход`, `Регистрация`, confirmation, or recovery) instead of retaining login copy after a mode switch
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
- first-layer cabinet UI should guide users through app install, device connection, renewal, and support before exposing manual connection details
- the single public `ссылка подключения` and matching QR may appear only behind an explicit manual/recovery fallback or after a fulfilled commerce/support path that truly needs manual import
- `?format=plain` remains hidden compatibility-only behavior and must stay out of normal cabinet UX
- `connect.pokrov.space` is for config delivery, not for public acquisition or payment entry
- cabinet checkout must not drift into a second public paywall or direct raw-link delivery story
- cabinet renewal and checkout keep the shared six-plan catalog (`99`, `239`, `669`, `1199`, `1699`, and `1999` RUB) as the complete local fail-safe; a failed or partial catalog request must not collapse the surface to a stale subset
- download rows and their secondary APK/file actions keep at least a 44 px touch target on mobile
- downloads instructions and the six-plan renewal grid stay behind explicit disclosures on narrow screens; the main download or checkout action remains visible first
- an active trial's `5 days` entitlement links to the compact `start_99` checkout continuation without changing the public `от 99 ₽ за полный месяц` price fact
- public email continuation must stay hidden/marked `soon` unless sender readiness, delivery confirmation, public mode, and debug-echo-off checks are live
- marketing and cabinet copy should inherit governed text from `shared/copy.ts`, `copy/catalog.ru.json`, and `shared/design-tokens.json` instead of inventing separate public messaging
- support upload responses expose `attachment_id`; preferred create/reply requests send only that ID and never resend the server-private media triplet
- support thread media accepts only canonical `/api/tickets/attachments/*` paths and rewrites retained `/uploads/support/*` history to that endpoint; arbitrary external attachment URLs are not rendered
- attachment preview/download is user-triggered rather than fetched on thread mount; it uses an authenticated blob request with the same API-base candidates, bearer/init-data headers, and `credentials: include` behavior as normal API calls, then a revocable object URL, and aborts in-flight retrieval on path change or unmount
- the support picker is limited to PNG, JPEG, WebP, PDF, and UTF-8 TXT; video, SVG, HTML, log aliases, and arbitrary files are not offered
- client preflight rejects files above the shared 20 MiB constant before reading TXT bytes; the backend `SUPPORT_UPLOAD_MAX_BYTES` check remains authoritative

## Rewards Surface

`/rewards/` is a detail route inside the existing `Аккаунт` lane, not a fifth primary cabinet tab. Its runtime rules are:

- wheel and activity-calendar mutations are available only to an account with active `PAID` access
- `BONUS_WHEEL_ENABLED` and `BONUS_CALENDAR_ENABLED` are independent rollout guards; a disabled, malformed, or unavailable feature fails closed without blocking the other feature
- wheel sectors are a display allowlist only; equal visual geometry does not describe probability, and the UI never receives or invents server weights
- the committed mutation response is authoritative for awarded days; the UI animates only when that exact result exists in the validated current sector list
- an unknown committed reward remains visible, triggers a wheel-state and entitlement refresh, and never falls back to the first visual sector
- calendar check-in treats the server's same-day response as successful idempotency and does not attempt a second grant
- every successful mutation refreshes feature state, in-memory cabinet entitlement, and reward history independently

## Shell, Theme, And Loading

- Full-screen loading is reserved for true cold start when no useful session state exists.
- Internal cabinet navigation keeps the shell mounted, shows page-shaped skeleton or route activity feedback, and must not reset the product frame.
- Internal links warm their static route payload on hover/focus intent (`app-route-link.tsx`, deduplicated per session); hard-navigation auth flows and external links never prefetch.
- Dashboard and user snapshots may be kept only in React memory as last-good state during warm refresh; do not persist dashboard cache to browser storage.
- Theme follows the system preference by default. Manual light/dark choice is a browser UI preference and should not store account or dashboard data.
- Mobile cabinet navigation uses the shell drawer as its only navigation surface;
  a second bottom-tab system must not be added.
- Sidebar theme and account actions share one grouped shell card, and hidden
  route activity collapses without retaining an empty layout gap.
- Retained admin navigation uses its own route group and must not depend on `CabinetShell` or dashboard path checks; new primary admin navigation lives in `adminapp/`.

## Account Onboarding And Motion

- The dashboard reads `experience` from `GET /api/user/*`. First-run display,
  version, completion, and skip state belong to the account; they are never
  stored in `localStorage`.
- Completion and skip use `POST /api/account/experience/onboarding`; a failed
  write keeps the tour open and presents the error inside the dialog.
- The tour is an app-first four-screen handoff: welcome, download, same-account
  login, and connect. It does not claim store availability or trusted signing.
- The main dashboard CTA follows server state: renew inactive access, download
  before app identity exists, reopen connection guidance before first connect,
  and open devices after connection.
- `reported` connection state is app-authored UX progress. Only `verified`
  means signed observer evidence exists.
- Onboarding transitions, counters, status pulses, and route activity honor
  reduced-motion preferences. Animated numbers use tabular figures and spring
  only when their value changes; they are not continuous decorative loops.

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

Authenticated task routes added in the selected-feature pass:

- `/protection/` — read-only protection/status explanation and recovery path;
- `/guides/` — the shared searchable 46-task catalog with category filters;
  every task includes the client, platform, screen and highlighted click
  target, while fallback guides additionally expose recommended setup,
  button-by-button behavior, warnings and 18 real screens across seven clients;
- `/guides/pokrov-app/` — the separate searchable 20-screen Android atlas with
  real redacted screenshots and numbered, non-obscuring target outlines;
- `/devices/` — device list plus one-time pairing-code controls;
- `/programs/` — switch, research, and team-pack application state;
- `/rewards/` — wheel discounts, anonymized referral conversion/history,
  achievements, and useful quests.

These cabinet pages explain or mutate account-owned server state. They do not
claim direct control of an Android/Windows tunnel running on another device.

## Auth Continuation

Current supported auth paths:

- inside Telegram: authorization through `initData`
- in browser: Telegram Login Widget -> `POST /api/auth/telegram/web-login`
- expired or deprecated Telegram widget/OIDC/session tokens must clear the stale web token and return the user to the cabinet entry with a human repeat-login CTA
- in browser: additive email continuation is available only when delivery readiness is live; settings can link email to the current Telegram-backed account without leaving the cabinet
- in settings: email-backed sessions can start Telegram linking through `/api/client/telegram/link`, then finish the link in the bot using the returned start code
- from bot handoff: `web_session_token` should open the cabinet without manual token copy/paste
- from app handoff: `handoff_token` is exchanged through `/api/auth/cabinet-handoff/exchange`, then removed from the URL before normal cabinet API calls; successful exchange honors the returned safe `target_path`, while expired/replayed handoffs show localized cabinet copy

## Local Run

```powershell
npm.cmd install
npm.cmd run dev
```

## Verification

```powershell
npm.cmd run build
npm.cmd run test:e2e:cabinet
npm.cmd run test:e2e
npm.cmd run test:e2e:admin  # retained admin parity fallback only
```

From the repository root, run the shared text guard when visible copy changes:

```powershell
python -m pytest tests/test_frontend_text_integrity.py tests/test_public_copy_guardrails.py -q
```

Verification rule:

- run `npm.cmd run build` on every webapp task
- run `python -m pytest tests/test_frontend_text_integrity.py tests/test_public_copy_guardrails.py -q` from the repository root when Russian copy, shared copy, or visible frontend text changes
- run `npm.cmd run test:e2e:cabinet` for focused cabinet route work
- run `npm.cmd run test:e2e` when cabinet, pricing, renewal, downloads, support, or login flows change
- run `npm.cmd run test:e2e:admin` only when retained `webapp` admin parity routes, permissions, dashboards, or operator actions change
- `npm.cmd run test:e2e` now builds the static export and serves `webapp/out` on port `3102` through `webapp/scripts/serve_export.py`, so the full browser pack runs against the same export-style surface that deploy uses
- `npm.cmd run test:e2e:cabinet` uses the same build-plus-export-server flow on port `3103` for the focused cabinet spec
- `npm.cmd run test:e2e:admin` uses the same build-plus-export-server flow on port `3101`, which removes the standalone admin flake that came from `next dev` cold-start and HMR reload noise
- both release-style Playwright scripts clear a stale port owner first and disable server reuse so local browser checks do not inherit an old process or stale session bootstrap

## Related Canonical Docs

- [Product Overview](C:/Users/kiwun/Documents/ai/VPN/docs/product/portal-vpn-product.md)
- [System Overview](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/system-overview.md)
- [App-First And Bonus Flows](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/app-first-and-bonus-flows.md)
- [Developer Guide](C:/Users/kiwun/Documents/ai/VPN/docs/developer/developer-guide.md)
