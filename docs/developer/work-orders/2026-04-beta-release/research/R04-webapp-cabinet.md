# R04 WebApp Cabinet

Status: complete

## Scope

Continuation-first user cabinet: overview, tariffs/payment, devices/downloads, support/diagnostics, profile/settings.

## Files/docs inspected

- [confirmed] `webapp/README.md`
- [confirmed] `webapp/src/app/**`
- [confirmed] `webapp/src/components/**`
- [confirmed] `webapp/src/lib/api.ts`
- [confirmed] `webapp/src/lib/session.tsx`
- [confirmed] `webapp/e2e/**`
- [confirmed] static webapp design references under `ПРИМЕРЫ ДИЗАЙНА ПРИЛОЖЕНИЯ И ЛК/вебапп/`:
  - `лк главная.png`
  - `лк тарифы.png`
  - `лк устройства.png`
  - `лк поддержка.png`
  - `лк админка.png`
  - `лк админка 2.png`
- [confirmed] canonical context from root docs required by `AGENTS.md`: docs index, product overview, system overview, app-first/bonus flows, deployment/access, monitoring/visibility, developer guide, repository map.
- [confirmed] Did not read or print never-touch secret files.
- [needs local run] No browser, build, or Playwright execution was run because this was assigned as a read-only research task with a single markdown edit scope.

## Current state

- [confirmed] `webapp` is positioned correctly in docs as continuation-first, not acquisition-first. `webapp/README.md` says `/` is browser entry, `/pricing/` is compatibility-only, `/dashboard/downloads/` redirects to `/downloads/`, and acquisition/pricing ownership stays in `marketing/`.
- [confirmed] The root `/` page is continuation-first in current source. It explicitly says it is not a second POKROV storefront, routes known sessions to `/dashboard/`, and marks email continuation as not ready.
- [confirmed] Active browser continuation paths are Telegram OIDC/widget and web session token. `PortalSessionProvider` consumes OIDC callbacks, `web_session_token`, Telegram init data, then loads `/api/auth/session`, `/api/dashboard`, and `/api/user/{tg_id}` for cabinet pages.
- [confirmed] Russian-first top-level cabinet pages exist for `/dashboard/`, `/subscription/`, `/devices/`, `/downloads/`, `/support/`, `/profile/`, and `/redeem/`.
- [confirmed] `/pricing/` redirects to `/subscription/`; `/dashboard/downloads/` redirects to `/downloads/`.
- [confirmed] `/statistics/` redirects to `/dashboard/`.
- [confirmed] `/settings/` has no route directory or page under `webapp/src/app/(dashboard)/`.
- [confirmed] Current sidebar IA is `Главная`, `Тарифы и оплата`, `Устройства`, `Загрузки`, `Поддержка`, `Профиль`. It does not include `Statistics` or `Settings`.
- [confirmed] Dashboard uses safe summaries: status, plan, traffic, devices, active connections, active user estimate, and node readiness counts. It avoids raw subscription token, QR, and `?format=plain` in the consumer dashboard.
- [confirmed] Subscription page is mostly continuation-first: current access mode, expiry, traffic, device limit, plan options, checkout handoff, redeem, and support. It does not show raw connection links.
- [confirmed] Checkout continuation builds a URL to the canonical hosted checkout host with `plan`, `from=webapp`, and optional `promo`. It does not create an internal payment order itself.
- [confirmed] Downloads page fetches runtime app links from `/api/client/apps` and falls back to configured Android/Windows/docs URLs.
- [confirmed] Support page uses real ticket endpoints: list, create, attachment upload. Thread page loads a ticket, renders messages, supports replies, and supports attachment upload.
- [confirmed] Profile page shows linked Telegram/email/access state, quick actions, referral info, and channel-bonus status.
- [confirmed] API client has live wrappers for dashboard, user, client apps, access-key status/redeem, tickets, ticket uploads, Telegram auth, email auth, bonuses, payment providers, and admin flows.
- [confirmed] Attached design refs expect a calmer dense cabinet with left nav, status cards, traffic/device/payment history, Telegram bonus card, device/session management, downloads, diagnostics, and real support/admin surfaces. Current code implements the broad direction but not all specific beta surfaces.

## Gaps against beta

- [confirmed] `/settings/` is absent even though the requested audit includes it and design refs show `Настройки` in the cabinet nav.
- [confirmed] `/statistics/` is only a redirect to `/dashboard/`, despite canonical docs naming Statistics as a top-level cabinet IA item and the requested route list including `/statistics/`.
- [confirmed] Consumer payment history is missing. The design ref `лк тарифы.png` includes `История платежей`; current consumer `/subscription/` and `/subscription/checkout/` show plan/checkout/redeem paths but no payment-history table or receipt links.
- [confirmed] Telegram bonus is visible only as status in `/profile/`; no consumer UI calls `claimChannelBonus()` or `checkChannelSubscriberStatus()`. A user who is eligible for `+10 days` can see a message/card, but cannot claim from the cabinet.
- [confirmed] `/subscription/checkout/` is not Russian-first/polished enough for paid beta. It exposes implementation copy such as `renewal continuation`, `Hosted checkout`, `payment-витрина`, `canonical hosted checkout`, `activation key`, `Free fallback`, raw `accessState`, `Email signup`, `premium trial`, `recovery`, `restore premium`, `fallback commerce/support`, and `managed profile`.
- [confirmed] `/subscription/checkout/` visually diverges from the newer cabinet primitives. It uses `glass-card`, violet accents, and older marketing/debug wording instead of the current green continuation cabinet design.
- [confirmed] Top-level IA diverges from product canon. Current nav includes `Загрузки` and `Профиль`, but omits `Статистика`; product docs say current top-level cabinet IA is `Dashboard / Subscription / Devices / Statistics / Support`, with downloads/redeem/checkout as task routes.
- [probable] `/profile/` partly covers settings/account needs, but it is not a substitute for `/settings/` if beta expects a visible settings route, language/account/security controls, or route-mode recovery affordances.
- [probable] Device management is visibility-first, not management-first. It shows device count and known devices, but there is no consumer action to remove a stale device, sign out other sessions, or request a slot reset directly from `/devices/`.
- [probable] The current dashboard/device pages show `Людей онлайн`, active connections, active nodes, and node readiness. These are safe enough as aggregates, but need browser review to ensure they do not feel like operator telemetry in the consumer cabinet.
- [needs local run] `webapp/e2e/cabinet-flow.spec.ts` appears stale against current root-entry copy. The spec expects headings/text like `Telegram уже работает`, `Скоро подключим`, and `Пока недоступно`; current source says `Telegram подтверждает кабинет`, `Готовим аккуратно`, and `Скоро`. This is a probable Playwright failure, but needs an actual local run.
- [needs local run] Mobile layout and visual parity with the attached refs need a screenshot/browser pass. Static source suggests responsive handling exists, but no rendered proof was produced in this research task.
- [blocked by missing access] Live production session behavior, real hosted checkout redirect, real ticket upload storage, and live Telegram auth cannot be confirmed without a live account/session and external service access.

## P0 blockers

- [confirmed] Build a real `/settings/` route or add an intentional redirect/handoff that satisfies the beta route contract. Current `/settings/` is missing.
- [confirmed] Implement `/statistics/` as a real safe-summary cabinet page or formally downgrade the route in canonical docs/work order. Current redirect conflicts with the top-level IA contract.
- [confirmed] Replace `/subscription/checkout/` beta-facing copy and styling. The route currently leaks internal/English/operator terms in the paid conversion path.
- [confirmed] Add consumer payment history to `/subscription/` or a task route reachable from it. Paid beta users need to see payment/renewal history without asking support.
- [confirmed] Add a real Telegram bonus claim/check card in the cabinet, using existing API wrappers, or explicitly route the user to the app/bot with truthful copy. Current profile-only status is not enough for the requested Telegram bonus card.
- [needs local run] Refresh and run `npm.cmd run build` plus `npm.cmd run test:e2e:cabinet` after the route/copy fixes. Current E2E expectations likely no longer match source.

## P1 beta polish

- [confirmed] Align user nav with continuation-first IA: keep downloads/redeem/checkout as task routes, and decide whether `Профиль` remains top-level or `Настройки` becomes the account/settings destination.
- [confirmed] Localize remaining public-facing English/implementation terms in consumer cabinet routes, especially `checkout`, `redeem`, `hosted checkout`, `activation key`, `premium trial`, and `managed profile`.
- [confirmed] Add direct support escalation affordances near payment-history failures, bonus claim failures, and device-limit friction.
- [confirmed] Bring support thread page onto the same `CabinetRoute`/green cabinet primitives as the rest of the user cabinet; it currently still uses older `glass-card`/violet styling.
- [confirmed] Review route labels against public wording rules. The attached design refs still show `Premium VPN`, but current canon says not to use `VPN` as direct public product description.
- [probable] Add device-slot actions or guided support flows from `/devices/`: remove old device, request reset, or continue a support case with device context.
- [probable] Add a safer `diagnostics` summary to support/profile if beta expects support diagnostics from the design refs. Current support collects user-described categories and attachments but does not expose a prepared diagnostic bundle in the consumer UI.

## P2 defer

- [confirmed] Full email login UI should remain deferred/marked soon until delivery is ready. Current source follows this.
- [confirmed] Raw subscription link/QR recovery should remain out of first-layer consumer cabinet. Current source mostly follows this for user routes.
- [confirmed] Admin visual parity with the attached refs is outside the user-cabinet P0 path, but admin already has broad coverage in source and E2E.
- [probable] A richer settings surface for language, theme, notification preferences, and linked identities can be phased after route-contract compliance if `/settings/` initially redirects to `/profile/` with clear IA.

## Technical debt

- [confirmed] There are two download components: `webapp/src/components/cabinet-downloads-page.tsx` and `webapp/src/components/cabinet/downloads-surface.tsx`; active route uses `downloads-surface.tsx`. The older component should be checked for stale duplication before implementation work.
- [confirmed] There are two cabinet primitive families: `cabinet-page.tsx` and `components/cabinet/surface.tsx`. Newer route pages use `surface.tsx`, while `/redeem/` still uses `cabinet-page.tsx`.
- [confirmed] Consumer checkout and support thread still use older `glass-card`/violet styling while dashboard/subscription/devices/downloads/profile use the newer cabinet primitives.
- [confirmed] `webapp/e2e/cabinet-flow.spec.ts` likely contains stale copy assertions for the root entry.
- [confirmed] `api.ts` still carries older payment/order wrappers that are not used by the current checkout continuation route. That may be fine for compatibility, but it increases audit noise.
- [probable] The product/README route map says `/statistics/` is current, while code redirects it away. This doc-code divergence will keep reappearing until resolved.

## Security/privacy risks

- [confirmed] Consumer dashboard/subscription/devices tests and source avoid showing raw `subscription_url`, raw token, QR, and `?format=plain` on first-layer consumer pages.
- [confirmed] Admin user detail still exposes/copies `subscription_url` for operator/manual recovery. That is an admin-only risk surface, not consumer-facing, but should stay permission-gated and audited.
- [confirmed] Ticket thread attachment renderer only accepts `/uploads/support/` through API URL resolution or absolute `http/https` URLs; it rejects empty/non-http protocols.
- [probable] `/subscription/checkout/` exposes raw internal state labels (`accessState`, free fallback constants) to users. This is more UX/privacy/confusion risk than a secret leak, but it should be removed before paid beta.
- [blocked by missing access] Could not confirm production auth/session cookie behavior, hosted checkout domain behavior, real file-upload storage paths, or live Telegram OIDC callback handling.

## Required implementation WOs

- R04-WO1: Route-contract fix for `/settings/` and `/statistics/`.
  - Add real pages or intentional redirects.
  - Update nav and canonical docs consistently.
  - Add route-level E2E assertions.
- R04-WO2: Paid checkout continuation polish.
  - Rebuild `/subscription/checkout/` with cabinet primitives.
  - Replace internal/English copy with Russian-first user copy.
  - Keep hosted checkout handoff and key-first model.
- R04-WO3: Payment history and receipt visibility.
  - Add consumer payment-history API contract if absent.
  - Render history on `/subscription/` or a task route.
  - Add support escalation for missing/failed payments.
- R04-WO4: Telegram bonus cabinet action.
  - Add claim/check card wired to `/api/channel/subscriber/check` and `/api/bonuses/channel/claim`.
  - Reflect claimed, eligible, unavailable, and error states.
- R04-WO5: Cabinet E2E refresh.
  - Update stale copy assertions.
  - Cover `/settings/`, `/statistics/`, payment history, bonus claim states, checkout handoff, downloads, support thread, and mobile viewport.
- R04-WO6: Style debt cleanup.
  - Migrate support thread and redeem/checkout to the same cabinet primitive family.
  - Remove stale duplicate download component if unused.

## Validation commands

- [needs local run] From `webapp/`: `npm.cmd run build`
- [needs local run] From `webapp/`: `npm.cmd run test:e2e:cabinet`
- [needs local run] From `webapp/`: `npm.cmd run test:e2e`
- [needs local run] Browser screenshot pass for `/`, `/dashboard/`, `/subscription/`, `/subscription/checkout/`, `/devices/`, `/downloads/`, `/support/`, `/support/thread/?id=<ticket>`, `/profile/`, `/settings/`, `/statistics/`, and `/redeem/` at desktop and mobile widths.
- [needs local run] Hosted checkout click-through smoke with a non-production/test-safe plan and promo code, confirming handoff to `https://pay.pokrov.space/checkout/`.
- [blocked by missing access] Live Telegram OIDC/widget, live bonus claim, real payment history, and real attachment upload checks require valid beta credentials and external services.

## Evidence links

- [confirmed] `webapp/README.md` defines webapp as continuation-first and lists expected route families.
- [confirmed] `webapp/src/app/page.tsx` lines 42-45 route known sessions to `/dashboard/`; lines 125-130 explicitly say the cabinet is not a second storefront.
- [confirmed] `webapp/src/components/cabinet-entry-auth.tsx` lines 21-26 define Telegram as continuation, not new registration; lines 52-54 mark email as future/not ready.
- [confirmed] `webapp/src/components/cabinet-shell.tsx` lines 31-78 define current sidebar IA and omit `Statistics`/`Settings`; lines 306-311 show traffic/device summaries in the shell.
- [confirmed] `webapp/src/app/(dashboard)/statistics/page.tsx` redirects to `/dashboard`.
- [confirmed] `webapp/src/app/pricing/page.tsx` redirects to `/subscription`.
- [confirmed] `webapp/src/app/(dashboard)/dashboard/downloads/page.tsx` redirects to `/downloads`.
- [confirmed] `webapp/src/app/(dashboard)/subscription/page.tsx` lines 93-100 derive access/traffic/device state; lines 126-163 define checkout/redeem/support action cards.
- [confirmed] `webapp/src/app/(dashboard)/subscription/checkout/page.tsx` lines 47-54 build hosted checkout URL; lines 128-223 contain beta-facing internal/English copy that needs replacement.
- [confirmed] `webapp/src/components/cabinet/downloads-surface.tsx` lines 37-43 prefer runtime app URLs from `/api/client/apps`; lines 180-283 render the download handoff.
- [confirmed] `webapp/src/app/(dashboard)/support/page.tsx` uses `fetchTickets`, `createTicket`, and `uploadTicketAttachment`.
- [confirmed] `webapp/src/app/(dashboard)/support/thread/page.tsx` uses `getTicket`, `addTicketMessage`, and `uploadTicketAttachment`.
- [confirmed] `webapp/src/app/(dashboard)/profile/page.tsx` lines 41-43 read Telegram bonus state; no source usage of `claimChannelBonus()` was found outside `api.ts`.
- [confirmed] `webapp/src/lib/api.ts` lines 1566-1680 cover user/dashboard/catalog/apps/access-key wrappers; lines 1805-1842 cover ticket wrappers; lines 1645-1655 expose channel bonus claim wrapper.
- [confirmed] `webapp/e2e/cabinet-flow.spec.ts` lines 337-365 contain root-entry copy expectations that appear stale against current source.
