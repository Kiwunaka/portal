# POKROV Web Cabinet UX Reset Plan

Last updated: 2026-06-06

## Status

Implemented design plan after read-only consilium review of the current `webapp/` personal cabinet.

This plan covers the personal cabinet only. It does not cover admin, marketing, backend deploy, or native client UX.

Implementation status as of `2026-06-06`:

- Phase 1: implemented in `CabinetShell` and compact cabinet primitives.
- Phase 2: implemented on `/dashboard/`.
- Phase 3: implemented on `/subscription/`; manual link and QR are explicit fallback only.
- Phase 4: implemented on `/support/`; ticket creation and uploads remain wired.
- Phase 5: implemented on `/settings/`; email, Telegram linking, and bonus flows remain wired.
- Phase 6: completed locally with build/export, focused e2e, copy guards, Browser smoke, and responsive screenshots. Release deploy/signing/manual visual approval are outside this plan.
- Follow-up detail-route compact pass: completed for `/devices/`, `/statistics/`, `/downloads/`, and `/redeem/`; these task/detail routes now use the same row-first compact surface instead of `CabinetHero`/card-grid-first layouts.
- Follow-up continuation-route compact pass: completed for `/subscription/checkout/`, `/support/thread/`, and `/support/legal/`; checkout, ticket thread, and legal docs now use compact status/group/row surfaces instead of hero/card-grid prose.

Verification snapshot:

- `npm.cmd run test:e2e:cabinet`: `26 passed`
- `npm.cmd run test:e2e:cabinet -- --grep "checkout continuation|support thread attachments|legal documents"`: `3 passed`
- `npx.cmd playwright test e2e/settings-email-link.spec.ts --config=playwright.config.ts`: `5 passed`
- `python -m pytest tests/test_frontend_text_integrity.py tests/test_public_copy_guardrails.py -q`: `10 passed`
- responsive screenshots: `C:/Users/kiwun/Documents/ai/VPN/.tmp/webapp-responsive-2026-06-06/`
- checked widths: `360`, `390`, `700`, `900`, `1024`, `1180`, `1440`
- maximum measured horizontal overflow on `/dashboard/`, `/subscription/`, `/support/`, `/settings/`: `0px`
- maximum measured horizontal overflow on `/devices/`, `/statistics/`, `/downloads/`, `/redeem/`: `0px`

## Consilium Input

Reviewed by OpenCode `opencode-go` models:

- `deepseek-v4-pro`
- `qwen3.7-max`
- `minimax-m3`
- `glm-5.1`
- `mimo-v2.5-pro`
- `kimi-k2.6`

Local context supplied:

- POKROV product canon
- current `webapp` route map
- current owner feedback
- current cabinet shell and page code excerpts
- Playwright screenshots for mobile and desktop cabinet routes
- first-viewport density metrics

All model feedback converged on the same conclusion: the current cabinet problem is structural density and repeated hierarchy, not just colors or radius.

## Current Problem

The cabinet is a continuation surface, but current screens behave like long product documentation pages.

Observed current metrics from local Playwright screenshots:

- mobile `dashboard`: about `2050` first-viewport text chars, `12` card-like blocks
- mobile `subscription`: about `5084` first-viewport text chars, `10` card-like blocks, page height about `6837px`
- mobile `settings`: about `2898` first-viewport text chars, `14` card-like blocks
- mobile `support`: about `4046` first-viewport text chars, `13` card-like blocks, page height about `6633px`
- desktop first view can show `22-30` card-like blocks and `13-16` actions

There is no meaningful horizontal overflow in the sampled views. The real problem is cognitive overflow: too many sections, repeated actions, too much explanatory copy, and too many card styles.

## Design Goal

The web cabinet should feel like a high-class utility, closer to iOS Settings plus a compact account cockpit:

- one screen, one primary job
- one primary action per screen
- short rows instead of card grids
- progressive disclosure for recovery, manual setup, QR, forms, and explainers
- no repeated CTAs across hero, alert, quick actions, and cards
- mobile first, desktop calm and sparse
- fast-feeling motion, no scroll-triggered drift

## Primary Information Architecture

Keep all existing routes working, but collapse first-layer navigation.

Primary visible cabinet nav:

1. `Главная`
   - route: `/dashboard/`
   - owns access state, next action, compact traffic/device summary
2. `Доступ`
   - route: `/subscription/`
   - owns renewal, plan picker, activation code, downloads, manual fallback disclosure
3. `Помощь`
   - route: `/support/`
   - owns ticket list, new ticket, attachments, Telegram fallback
4. `Аккаунт`
   - route: `/settings/`
   - owns identity, Telegram, email, bonus, theme/session/logout

Compatibility/detail routes remain live:

- `/devices/` becomes a detail route linked from `Главная`
- `/statistics/` becomes a detail route linked from `Главная` only when it has useful data
- `/downloads/` becomes a task/detail route linked from `Доступ`
- `/redeem/` remains a task route linked from `Доступ`
- `/profile/` remains a compatibility redirect to `Аккаунт`

Admin links remain conditional for admins and are not part of the consumer nav count.

## Screen Rules

### Главная

First viewport target:

- one compact status block
- one context-aware primary action
- up to three row metrics
- optional warning only when action is required
- no all-good alert banner
- no quick-action grid
- no full install block
- no bento KPI grid

Context-aware primary action examples:

- active access and no app/device context: `Скачать приложение`
- active access and known app context: `Открыть приложение`
- expiring soon: `Продлить`
- inactive: `Вернуть доступ`

Device and traffic summaries should be rows:

- `Трафик` -> value
- `Устройства` -> `2 из 5`
- `Доступ до` -> date

### Доступ

First viewport target:

- current plan and expiry
- plan picker or selected renewal option
- one payment CTA
- compact `Активировать код` row

Move below fold or disclosure:

- manual setup
- QR
- raw subscription link
- compatible client recommendations
- long explanations of modes or payment behavior

Do not show payment-history placeholders until real history exists.

### Помощь

First viewport target:

- latest open ticket, if present
- `Новый вопрос` primary action
- ticket list rows
- Telegram fallback as a secondary row

Move into the compose flow:

- category guidance
- diagnostic checklist
- file/log guidance
- warnings about what to attach

Support should remain a real ticket thread with uploads, not a fake chat promise.

### Аккаунт

Use grouped rows:

- `Аккаунт`: current identity, session, logout
- `Связки`: Telegram, email
- `Бонус`: Telegram `+10 дней`, history/claim state
- `Дополнительно`: theme, language, safe preferences

Email linking, Telegram linking, and bonus claim should open progressive flows instead of large inline forms.

## Copy Rules

Delete or hide:

- section eyebrows that duplicate the route title
- section descriptions that restate the title
- generic lines like `что нужно сейчас`, `следующий шаг`, `как это работает`, unless they carry a real action
- repeated explanations of install, renewal, support, or bonus mechanics
- all-good alert copy
- internal diagnostic prose on the first layer

Keep copy short:

- nav labels: 1-2 words
- row labels: 1-4 words
- row values: 1 line
- alerts: one reason plus one action
- button labels: verb-first and direct

Preferred words:

- `Доступ`
- `Продлить`
- `Скачать`
- `Активировать код`
- `Новый вопрос`
- `Привязать Telegram`
- `Добавить email`

Avoid first-layer raw terms:

- raw hostnames
- raw subscription links
- QR/manual import wording unless inside recovery disclosure
- unsupported store, stable, signing, RU-readiness, or production-proof claims

## Component Rules

Introduce or refocus primitives:

- `CabinetRow`: iOS Settings-style row with optional icon, label, value, chevron/action
- `CabinetGroup`: compact group label plus rows, no card wrapper by default
- `CabinetStatus`: one compact status surface with optional primary action
- `CabinetSheet`: bottom sheet on mobile, centered modal/side panel on desktop
- `CabinetSkeleton`: shape-matched skeleton rows and status blocks

Deprecate as default cabinet patterns:

- `CabinetHero`
- `CabinetCardGrid` for navigation or ordinary settings
- `CabinetKpiRow` as a four-card grid
- `DoubleBezel` on every section
- `FadeUp` on every section
- `bento-card`
- `quick-action-btn`
- all-good `alert-card`

Cards remain allowed only for true choice comparison, such as plan selection.

Design-system constraints:

- one panel radius family, preferably `16px`
- one row radius family, preferably `12px`
- one modal/sheet radius family, preferably `24px`
- no nested cards
- no hover-lift on ordinary utility rows
- no viewport-scaled cabinet type
- no large hero typography inside compact panels

## Motion Rules

Use motion to make the cabinet responsive, not theatrical.

Allowed:

- route crossfade `120-180ms`
- row press scale/opacity `80-120ms`
- sheet open/close transform `180-240ms`
- status value crossfade `160-220ms`
- skeleton shimmer only when it matches final layout

Avoid:

- scroll-triggered FadeUp cascades
- blur-heavy entrance effects
- hover lifting on utility cards
- animated decorative backgrounds
- progress bars that reserve layout space or create jumps

## Implementation Phases

### Phase 1: Shell And Primitives

- collapse visible consumer nav to `Главная / Доступ / Помощь / Аккаунт`
- keep all old routes working
- simplify desktop sidebar
- remove duplicate status/account from desktop top header
- reduce mobile bottom nav to four first-layer items
- add row/group/status/sheet primitives
- simplify skeletons to match the new layout

### Phase 2: Главная

- remove quick actions
- remove all-good alert
- remove large install block
- replace KPI bento with compact rows
- show only one context-aware primary action
- move device/stat detail to rows and detail links

### Phase 3: Доступ

- rebuild subscription around current plan, plan selection, pay CTA, activation code
- move downloads into a compact install group
- keep `/downloads/` available as a direct task route
- hide manual setup, QR, and compatible clients behind explicit recovery disclosure
- remove history placeholder and mode explainer

### Phase 4: Помощь

- keep ticket list and compose flow
- keep upload support
- move diagnostic/checklist content into compose modal
- remove guide/help/diagnostic card grids from the first layer
- keep Telegram fallback as a row

### Phase 5: Аккаунт

- rebuild settings as grouped rows
- move email link form into a sheet
- move Telegram bonus claim into a compact flow
- keep session/logout/theme discoverable but secondary
- remove quick-action cards

### Phase 6: Cleanup And Verification

- remove unused cabinet card classes and old primitives only after pages no longer use them
- run build
- run focused cabinet e2e
- run copy guard if visible Russian copy changed
- capture screenshots at `360`, `390`, `700`, `900`, `1024`, `1180`, and `1440`
- verify no horizontal overflow and no fixed nav overlap

## Acceptance Metrics

Mobile first viewport targets:

- `<= 500` visible text characters on `Главная`
- `<= 700` visible text characters on `Доступ`
- `<= 600` visible text characters on `Помощь`
- `<= 600` visible text characters on `Аккаунт`
- `<= 4` card-like blocks in first viewport
- `<= 2` visible primary/secondary actions per first viewport
- no horizontal overflow at `360px`
- bottom nav never overlaps actionable content

Desktop targets:

- first viewport shows one primary action
- no more than `10` card-like/panel blocks in first viewport
- main content max width is constrained and does not become a full-width card wall
- sidebar and top header do not repeat the same status/account content

## Canon Checks

- Cabinet stays continuation-first and does not become marketing.
- Existing task routes remain available for deep links and bots.
- Raw subscription link and QR stay behind explicit manual/recovery disclosure.
- Telegram `+10 days` reward remains visible and accessible.
- Email continuation remains gated by runtime readiness.
- No store availability, trusted Windows signing, stable `1.0.0`, RU-origin readiness, or production WARP proof is implied.
- Admin surface remains separate and conditional.
