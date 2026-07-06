# POKROV Redesign — Sub-Project 2: Web Cabinet Rebuild

- Date: 2026-07-06
- Status: Approved by owner 2026-07-06 (blanket approval; open questions go back to the owner via menu)
- Parent effort: global redesign wave `0 → 1 → 2 → 3`; foundation (sub-project 0) landed in `fbe332e`, marketing landing (sub-project 1) landed in `27105ac..0908242`
- Foundation spec: `docs/superpowers/specs/2026-07-04-design-foundation-redesign-design.md`
- Marketing spec: `docs/superpowers/specs/2026-07-04-marketing-landing-redesign-design.md`

## 1. Context And Goal

The cabinet works but feels slow and looks like a different, older product than the rebuilt landing. The root perceived-performance cause is architectural: `app-route-link.tsx` forces `window.location.assign` for **every** internal navigation (a beta-stabilization workaround from `43b18f4` / `26dee66`, 2026-05-15), so each click reloads the document, re-runs the session bootstrap, and shows the full-screen `InitialCabinetSkeleton` (`cabinet-shell.tsx:328`). Visually, `globals.css` carries 1358 lines with two component generations (`.glass-card`/`.stat-card`/`.btn-*` era and the `.cab-*` era) plus dead root variables, and icons go through a legacy material-symbols name shim (`cabinet/icon.tsx`) that DESIGN.md marks as a sub-project-2 retirement target.

The goal: the cabinet becomes a fast, persistent-shell app surface on the `pokrov-clear` foundation — same family as the landing, higher density, light + dark. A user answers four questions in five seconds: is my access active, until when, what do I do next, how do I connect a device. Honest states everywhere: no fake progress, no full-screen loaders after the shell exists.

Good news from grounding: the session layer already fetches dashboard+user in parallel and keeps a last-good in-memory snapshot; there is no mojibake; `webapp.*` copy keys exist for most page titles; 60+ Playwright e2e tests cover cabinet and admin flows.

## 2. Owner Decisions (locked)

| # | Question | Decision |
|---|---|---|
| 1 | Wave scope | **A. User cabinet + entry/auth** — shell, entry, and all `(dashboard)` pages in this wave; admin gets a short separate wave 2b (it already has density mode and direct lucide) |
| 2 | Navigation model | **A. Restore SPA navigation** — persistent shell, client-side transitions, content-region skeletons; the hard-reload workaround is retired with e2e coverage as the safety net |
| 3 | CSS approach | **A. Tailwind utility-first** — TSX primitives on tokens (marketing pattern); both legacy CSS generations die; `globals.css` shrinks to bridge + base |
| 4 | Theme | Light + dark with manual toggle (foundation decision); toggle becomes the canonical iOS switch component |
| 5 | Iconography | Direct `lucide-react` imports; the material-symbols name shim is deleted (DESIGN.md migration target); brand marks via `simple-icons` per the 2026-07-06 canon addition |

## 3. Scope

In scope (all inside `webapp/`, plus shared copy files):

- SPA navigation restoration: `app-route-link.tsx`, `cabinet-shell.tsx` loading model, route activity indicator, per-page skeletons
- Full rebuild of shell (desktop sidebar, mobile header + bottom tab bar, theme toggle) and all user pages: `/dashboard`, `/dashboard/downloads`, `/subscription`, `/subscription/checkout`, `/downloads`, `/devices`, `/statistics`, `/profile`, `/settings`, `/redeem`, `/support`, `/support/thread`, `/support/legal`
- Entry/auth surfaces: `/` (entry + `CabinetEntryAuth`), `verify`, `recover` (logic-only pages get the new minimal wait surface), error/not-found boundaries
- New `ui/` primitive set on Tailwind utilities + tokens; iOS switch component (`component.switch` tokens)
- Icon migration to direct lucide imports; shim deletion
- `globals.css` reduction: Tailwind bridge (`@theme` → `--pokrov-*`), base styles, the few keyframes utilities cannot express
- Copy: extend `webapp.*` keys in `copy/catalog.ru.json` for all new user-visible strings
- Docs same-wave: `webapp/README.md`, DESIGN.md shim-retirement note

Out of scope:

- Admin visual redesign (wave 2b); mechanical-only touches where admin imports cabinet primitives (`(admin)/not-found.tsx`)
- `lib/api.ts` endpoints/contracts, auth flows, payment logic — behavior preserved; only navigation touchpoints and presentation change
- Client app (sub-project 3); marketing; backend
- Dashboard payload/API changes (no new endpoints)

## 4. Hard Constraints (from AGENTS.md / canon)

- Static export (`output: "export"`, `trailingSlash: true`) must survive; deep links keep working on direct load.
- Design tokens are the only color/type/motion source; no hand-written hex; utilities consume adaptive `--pokrov-*` names only — never legacy `-dark`-suffixed variables, never per-component `.dark` color overrides (theme model, DESIGN.md).
- Dashboard/user snapshots stay in React memory only; browser storage holds theme choice and the session token — nothing else (design-system-sync canon).
- Consumer-first layering: QR codes, raw config links, transport acronyms, node internals never appear on the first layer; manual/recovery paths live behind explicit fallback states.
- Wording: formal «вы», calm and practical; beta honesty for Android/Windows downloads; no store/1.0.0/signing/RU-origin/auto-update claims; `status_green` only for the connected state and switch fills, never text.
- Accessibility: WCAG AA, 44px touch targets, visible `:focus-visible`, `aria-busy`/`aria-live="polite"` on loading regions, `prefers-reduced-motion` collapses motion to opacity/static.
- Telegram WebApp integration (`telegram-webapp-init.tsx`, haptics, viewport/theme sync) keeps working; covered by `settings-email-link.spec.ts`.
- e2e truth: `webapp/e2e/*` suites are the regression net; they must pass at the end of every phase.

## 5. Navigation, Loading, And Perceived Performance

The core behavioral change of the wave, done before any visual work:

1. **Archaeology first**: reproduce the original bug class that motivated hard navigation (commits `43b18f4`, `26dee66`) against a static-export serve; record findings in the plan-phase notes. Expected classes: stale session state across client transitions, scroll restoration, or handoff-token URLs.
2. **`AppRouteLink` becomes a real `next/link`**: client-side navigation by default; `hardNavigate` stays as an explicit escape hatch only for auth-boundary flows (login/logout, OIDC start/finish, cabinet-handoff and `clear_web_session` URLs — flows that intentionally re-bootstrap the document).
3. **Persistent shell**: `PortalSessionProvider` + shell live in `(dashboard)/layout.tsx` and survive transitions. The full-screen skeleton renders only when there is no usable session state at all (true cold start). With a last-good snapshot present, the shell always stays; content regions swap.
4. **Honest indicators**: 2px indeterminate top bar during route/refresh activity (no percentages); nav item shows pending intent immediately; «Обновляем данные» chip when showing last-good data during refresh.
5. **Page-shaped skeletons**: each rebuilt page ships a skeleton matching its real layout (hero + tiles for dashboard, rows for lists, form block for redeem); minimum-delay-free, reduced-motion static.
6. **Prefetch**: default `next/link` prefetch for sidebar/tab-bar routes; no prefetch of admin routes from the cabinet.
7. **Budgets** (from atlas-glass loading audit): route feedback < 150ms, LCP < 2.5s, INP < 200ms, CLS < 0.1.

## 6. Component Architecture

```
webapp/src/components/
  ui/        Button, Badge, Chip, Input, Field, Switch (iOS, component.switch tokens),
             Card, PageHeader, Meter, SkeletonBlock, EmptyState, ErrorState, Toast —
             Tailwind utilities + tokens, cva-style variants, no CSS classes
  shell/     CabinetShell (persistent), Sidebar, MobileTabBar, TopActivityBar,
             ThemeToggle (iOS switch), BootstrapScreen (cold start)
  cabinet/   one section = one file, grouped per route:
             dashboard/ (StatusHero, NextAction, RunwayMeter, QuickTiles)
             subscription/ (PlanCard, RenewOptions, HistoryList)
             devices/ (DeviceCard, LimitMeter), downloads/ (PlatformCard, InstallSteps)
             support/ (IssueCards, TicketThread), redeem/, settings/, statistics/
  icons: direct lucide-react imports (single family); BrandIcon (simple-icons) if a
         real service logo is ever needed; POKROV mark stays custom SVG
```

Rules: sections compose primitives; no section imports another section; `lib/api.ts`, `lib/session.tsx` (minus navigation touchpoints), `telegram-webapp-init.tsx`, `qa-overlay.tsx` are reused as-is. Legacy `shell-primitives.tsx`, `cabinet/surface.tsx`, `cabinet/ui.tsx`, `cabinet/icon.tsx` are deleted once the last consumer migrates.

## 7. Page Blueprints

### 7.1 Shell

Desktop: white sidebar on `canvas_alt`, grouped nav (Главная · Доступ · Помощь · Аккаунт, + Управление for admins), active pill, user summary with access badge at the bottom, theme toggle. Mobile: compact header + the existing bottom tab bar pattern rebuilt on tokens (app-like, always present, not Telegram-only). Route meta (title/subtitle) moves into `PageHeader` per page instead of the shell ROUTE_META map.

### 7.2 Dashboard — Access Cockpit

1. **StatusHero** — access state in one glance: «Доступ активен» / «Доступ заканчивается» / «Доступ истёк» / «Пробный период», expiry date + days left, subtle status ring (`status_green` only when connected-state semantics apply), primary CTA per state (продлить / скачать приложение / активировать ключ).
2. **NextAction** — one card, one action, chosen from real state (no app yet → install; expiring → renew; no devices → connect; open ticket → reply waiting).
3. **RunwayMeter** — days-left meter on `progress` tokens with renewal CTA.
4. **QuickTiles** — Устройства · Загрузки · Продление · Помощь (icon, one-line state, link).
5. No raw API states, no transport jargon, no metric dump.

### 7.3 Subscription + Checkout

Current plan card (plan label, expiry, device limit from shared tariff catalog), renewal options with honest per-month math (same rules as landing pricing), one-time-key honesty («ничего не продлевается само»), Telegram +10 reminder when unclaimed, payment history when available. Checkout continuation keeps existing logic/provider truth — presentation moves to primitives; escape hatches (redeem, support) keep routes.

### 7.4 Downloads (`/downloads`, `/dashboard/downloads`)

Platform cards from `/api/client/apps` (existing `downloads-surface` data flow): version, channel, honest beta status, split-APK explanation, SmartScreen/unknown-sources honesty aligned with the landing install page; account-gated and unavailable states stay truthful («Загрузка недоступна для этого аккаунта», «Сборка готовится»).

### 7.5 Devices

Limit meter (`device_limit` from dashboard payload), device cards (platform icon, name, last seen, status dot), add-device CTA routing to downloads/connect flow, empty state «Устройства появятся после первого входа в приложение». Details behind a drawer/accordion, not first layer.

### 7.6 Statistics

Honest summary only: last connection, active sessions, traffic summary when the policy exposes it (`traffic_policy.kind`), «что значит этот показатель» helper; no fake precision, no graphs for their own sake.

### 7.7 Support (+thread, +legal)

Quick issue cards (не подключается / оплата / устройство / другое), ticket list + thread on the existing API, Telegram support CTA from the registry, «что приложить» helper. Thread keeps `support-message-body` rendering. Legal page gets typography-only reskin.

### 7.8 Settings + Profile

Grouped iOS-style lists (grouped-box canon): identity + linked accounts (Telegram/email link flows preserved), Telegram bonus claim state, theme (iOS switch), session management (logout web session), danger zone collapsed.

### 7.9 Redeem

One big input, one CTA, clear valid/invalid/success states with next action; no technical error dumps (map API errors to human copy).

### 7.10 Entry / auth surfaces

`/` entry: brand panel + auth card on the new primitives (Telegram primary, email secondary — existing `CabinetEntryAuth` logic reskinned); button-level loading, field-level errors. `verify`/`recover`: minimal branded wait surface («Проверяем ссылку…») on `BootstrapScreen` styling. Error/not-found boundaries move to `ErrorState`/`EmptyState` primitives.

## 8. Motion Spec

- Tokens only: 160/220/320ms, `--pokrov-easing`, `--pokrov-easing-spring`; transform/opacity exclusively.
- Route content enter: fade + `translateY(6px)`, 220ms; shell never animates on route change; no exit animations that delay input.
- Switch: `component.switch.transition` spring (220ms, overshoot) — the only playful motion in the cabinet.
- Card hover: ≤1px lift + border/shadow shift; tap scale 0.98 on primary CTAs.
- Skeleton shimmer 1200–1600ms, static under reduced motion; top activity bar is opacity/scaleX-only.
- Drawers/dialogs/toasts: opacity + small translate, focus trap, Escape, focus return.
- `prefers-reduced-motion`: everything collapses to opacity or instant; framer-motion via `useReducedMotion()`.

## 9. Copy Plan

- Every new user-visible string gets a `webapp.*` key in `copy/catalog.ru.json` via `shared/copy.ts`; existing keys reused where semantics match; orphans pruned in the same change.
- Tone contract: formal «вы», calm, concrete, next-action-first. Phrase bank from `docs/design/atlas-glass/route-map.md` (loading «Открываем кабинет» / «Проверяем доступ», empty «Пока здесь пусто», error «Не удалось обновить данные» + «Повторить»). Forbidden: fake progress wording («почти готово»), transport jargon on first layer, unsupported release/payment claims, alarm tone for expiring access.
- Draft flow: local draft → consilium pass (Kimi for warmth, DeepSeek for contradiction/claims per AGENTS.md routing) → local synthesis.
- Claims checklist per surface: 5-day trial, +10 Telegram, one-time keys, per-plan device limits, GitHub beta delivery — all from shared facts.

## 10. Risks

| Risk | Handling |
|---|---|
| SPA restore reintroduces the May bug class | Phase 0 archaeology reproduces the original failure before the fix lands; `hardNavigate` escape hatch stays for auth-boundary flows; full e2e suite after every phase |
| Static export + client nav edge cases (trailingSlash, deep links) | e2e covers direct-URL entry for every route; export route list compared before/after |
| Dark theme drift when moving to utilities | Utilities consume adaptive `--pokrov-*` only; light+dark screenshot pass per page; text-integrity + guardrail tests |
| Admin breakage from shared-code changes | Admin imports of cabinet primitives migrated mechanically (no visual change); `admin-gate.spec.ts` green is a phase gate; `.cab-*`/legacy classes deleted only after the last consumer (including admin) is off them |
| Session provider behavior change during shell refactor | `lib/session.tsx` fetch logic untouched; only the consumer (shell) changes its render branches; cabinet-flow e2e covers handoff/email/OIDC paths |
| Telegram WebApp regressions | `telegram-webapp-init` untouched; `settings-email-link.spec.ts` in the phase gate |
| Perceived-performance regression on low-end devices | No blur animation, transform/opacity only; skeletons are static boxes under reduced motion; manual slow-network pass |

## 11. Verification And DoD

1. `npm.cmd run build` in `webapp/` (static export; route set unchanged) — green after every phase.
2. `node ./scripts/run-e2e.mjs full` — cabinet, admin-gate, settings-email-link, telegram-login-refresh, oidc-fallback, qa-overlay all green.
3. Python guardrails: `tests/test_frontend_text_integrity.py`, `tests/test_admin_design_guardrails.py`, `tests/test_ui_visual_smoke.py` (+ refreshed `scripts/ui_visual_smoke.py` expectations where they encode old markup) — green.
4. `rg` cleanliness: no `material-symbols` name map, no `.glass-card|.stat-card|.btn-primary|.skeleton `-era classes, no `cab-` classes left in `webapp/src` (bridge/base only in globals.css), no raw hex in components, no legacy `-dark` variable references.
5. Browser smoke (my pass): entry, dashboard, subscription, checkout, downloads, devices, support, settings, redeem at 375px and 1280px, light + dark, reduced-motion pass, console-error-free; navigation between all sidebar routes without document reload (verify via DevTools).
6. Contrast spot-check per foundation table; `status_green` never on text; `text_muted` decorative-only.
7. Owner visual review of the built cabinet before deploy (webapp deploy was deliberately held since sub-project 0 — this wave is the webapp deploy trigger).
8. Same-wave docs: `webapp/README.md` (architecture/nav model), DESIGN.md iconography note (shim retired), `docs/design/design-system-sync.md` if token consumption rules change.

## Appendix: Session Decision Log

- Scope, navigation, and CSS decisions answered in terminal on 2026-07-06 (options A/A/A, recommended set).
- Grounding facts recorded in this session: hard-navigation origin `43b18f4`/`26dee66`; `cabinet-shell.tsx:328` full-screen loading branch; globals.css 1358 lines with two component generations; session already parallel + last-good snapshot; no mojibake in webapp/src.
- Icon canon addition (same day, pre-wave): simple-icons for brand marks, glyph pseudo-icons banned — landed in DESIGN.md with the marketing icon fix.
