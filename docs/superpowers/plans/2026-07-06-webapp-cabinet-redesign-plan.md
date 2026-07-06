# POKROV Redesign — Sub-Project 2: Implementation Plan

- Date: 2026-07-06
- Spec: `docs/superpowers/specs/2026-07-06-webapp-cabinet-redesign-design.md` (approved)
- Rule: every phase ends with a green `webapp` build **and** green e2e (`run-e2e.mjs full`); commits land per phase.

## Phase 0 — Archaeology & baseline (no behavior change)

- 0.1 Reproduce the 2026-05-15 hard-navigation bug class (`43b18f4`, `26dee66`) on a static-export serve; record findings + the exact flows that still need `hardNavigate` (§5.1–5.2).
- 0.2 Run full e2e + build as baseline; capture route list of the export and screenshots (light/dark) of dashboard, subscription, downloads, devices, support, settings, entry.

### Phase 0 findings (2026-07-06)

- History: original `AppRouteLink` used client nav (`hardNavigate=false`); `43b18f4` (May 15) flipped the default to hard; `43433be` (May 19) tried `router.push` with trailing-slash-stripped paths; `26dee66` (May 22) gave up and made even the soft path use `window.location.assign`. Suspected bug class: Next 14-era client-router vs `trailingSlash: true` static export path normalization.
- Reproduction on Next 16.1.6 export (`serve_export.py`, port 3105): `window.next.router.push('/devices/')` **and** `push('/subscription')` (no slash) both performed true client-side transitions — a `window` marker survived, URLs normalized to trailing-slash form. The May bug class does not reproduce on Next 16.
- Baseline: build green (30-route export), e2e **46/46 green**, 18 screenshots (9 routes × light/dark) in `.playwright-mcp/baseline-cabinet/`; reusable mock QA script in `.tmp/redesign-w2/pokrov-cabinet-baseline.js`.
- Flows that keep `hardNavigate`/full reload semantics: logout (`clear_web_session`), OIDC start/finish redirects, cabinet-handoff token URLs, external links.

## Phase 1 — SPA navigation & loading model (old visuals intact)

- 1.1 `app-route-link.tsx`: default to `next/link` client navigation; keep `hardNavigate` only for auth-boundary flows identified in 0.1 (§5.2).
- 1.2 `cabinet-shell.tsx`: full-screen skeleton only on true cold start; shell persists whenever a last-good session snapshot exists (§5.3).
- 1.3 Route activity: 2px indeterminate top bar + pending nav state + «Обновляем данные» chip (§5.4); wire prefetch for sidebar/tab-bar routes (§5.6).
- 1.4 Verify budgets manually (route feedback <150ms) and no document reload between sidebar routes; full e2e.

### Phase 1 findings (2026-07-06)

- `AppRouteLink` soft path now lets `next/link` run true client transitions; `hardNavigate` prop unchanged for auth-boundary/external callers.
- New export bug found and fixed: Next 16 static export writes route-group RSC segment payloads as nested dirs (`__next.!<group>/page.txt`) while the client requests dot-joined paths (`__next.!<group>.page.txt`) — 404 on every transition/prefetch, silent full-payload fallback. Fix: `webapp/scripts/fix-export-segment-paths.mjs` post-build creates dot-joined copies (72 files); wired into `npm run build`. Marketing is unaffected (no route groups).
- Next 16.2.10 upgrade attempt REVERTED: it does not fix the export layout and regresses `router.replace` with query params on static export (admin users URL-filter e2e fails). Stay pinned to `16.1.6`; re-test the segment-path workaround on any future Next upgrade.
- Shell loading branch needed no change: `PortalSessionProvider` persists in `(dashboard)/layout.tsx` across client transitions, so `loading=true` (full skeleton) now happens only on true cold start; warm navigation swaps content only (verified: 1 page-data API call on nav, no session re-bootstrap).
- Gates: e2e 46/46 green (export mode), SPA nav check clean (marker survives 3 transitions, 0 console errors), build green. Visible «Обновляем данные» chip moves to the Phase 2 shell reskin.

## Phase 2 — Foundation primitives & shell reskin

- 2.1 `globals.css`: add Tailwind `@theme` bridge to adaptive `--pokrov-*` (marketing pattern); keep legacy classes alive during migration.
- 2.2 Build `ui/` primitives (Button, Badge, Chip, Input, Field, Switch iOS, Card, PageHeader, Meter, SkeletonBlock, EmptyState, ErrorState, Toast port) per §6.
- 2.3 Rebuild shell: Sidebar, MobileTabBar, TopActivityBar, ThemeToggle (iOS switch), BootstrapScreen (§7.1); migrate shell icons to direct lucide.
- 2.4 Light+dark screenshot pass of the shell; full e2e.

### Phase 2 findings (2026-07-06)

- Bridge + `ui/` set landed (button, badge, chip, input/field, iOS switch, card/panel, page-header, meter, skeleton, empty/error state, toast). `cabinet/toast.tsx` is a re-export shim so the single toast context survives until pages migrate.
- Shell rebuilt on utilities + direct lucide; `.mobile-nav-*` CSS block replaced by utilities (class kept as e2e marker); desktop sidebar gained the «Тёмная тема» iOS-switch row and the «Обновляем данные» chip landed next to the activity bar. Gates: build green, e2e 46/46, light/dark screenshots in `.playwright-mcp/phase2/`.

## Phase 3 — Page rebuilds (each page replaces legacy on completion)

- 3.1 `/dashboard` — Access Cockpit: StatusHero, NextAction, RunwayMeter, QuickTiles + page skeleton (§7.2).
- 3.2 `/downloads` + `/dashboard/downloads` — platform cards, honest beta states (§7.4).
- 3.3 `/subscription` + `/subscription/checkout` — plan card, renewal math, checkout reskin (logic untouched) (§7.3).
- 3.4 `/devices` — limit meter, device cards, empty state (§7.5).
- 3.5 `/support` + `/support/thread` + `/support/legal` — issue cards, thread, typography reskin (§7.7).
- 3.6 `/redeem` (§7.9), `/settings` + `/profile` — grouped lists, iOS switch theme row (§7.8).
- 3.7 `/statistics` — honest summary (§7.6).
- 3.8 Entry `/` + `verify` + `recover` + error/not-found boundaries (§7.10).
- 3.9 Migrate `(admin)/not-found.tsx` and any admin imports of retired primitives mechanically (no visual change).

## Phase 4 — Copy pass

- 4.1 Sweep inline strings into `webapp.*` keys in `copy/catalog.ru.json`; prune orphans; claims checklist per §9.
- 4.2 Consilium pass (Kimi warmth / DeepSeek claims) on new strings; local synthesis; catalog version bump.

## Phase 5 — Legacy retirement, verification, ship

- 5.1 Delete `shell-primitives.tsx`, `cabinet/surface.tsx`, `cabinet/ui.tsx`, `cabinet/icon.tsx` (shim), legacy CSS generations; `globals.css` = bridge + base + keyframes only.
- 5.2 `rg` cleanliness checks per §11.4; refresh `scripts/ui_visual_smoke.py` expectations; run python guardrails.
- 5.3 Full e2e + build + browser smoke (375/1280, light/dark, reduced-motion) per §11.5–11.6.
- 5.4 Same-wave docs: `webapp/README.md`, DESIGN.md shim note, design-system-sync if needed.
- 5.5 Owner visual review → push → webapp deploy on owner go (§11.7).
