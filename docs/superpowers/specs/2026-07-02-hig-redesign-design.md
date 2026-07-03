# POKROV HIG Redesign — Design Spec

Date: 2026-07-02
Status: approved by owner (chat), phase 1 implemented
Scope: marketing, webapp (cabinet + admin), Telegram bots copy, Flutter client

## Goal

Move every POKROV surface to a calm Apple-HIG style: grouped boxes with
breathing room, thin separators, restrained emerald accent, a real
token-driven dark mode, transform/opacity-only motion, and warm, direct,
selling Russian copy with step-by-step instructions.

## Root-cause findings (audit 2026-07-02)

1. Tokens emitted light and dark values side by side (`--pokrov-bg` +
   `--pokrov-bg-dark`), forcing every surface to hand-write dark selectors.
   This was the root cause of patchy dark mode everywhere.
2. Webapp Tailwind v4 `dark:` utilities followed the OS media query while the
   manual toggle set the `.dark` class — mixed-theme screens.
3. Marketing homepage had no theme toggle; 10 secondary pages sit on a legacy
   2,400-line `lp-*` stylesheet with ~60 ad-hoc dark override selectors.
4. Webapp mixed three styling generations and two primitive sets; copy
   hardcoded per page.
5. Bots: ~300-400 messages, 90% inline in `bot.py`; three competing copy
   systems; duplicated help menus.
6. Flutter app: solid theming, but no l10n layer and hand-duplicated palette.

## Phase plan

1. **Foundation (done)** — theme-switched tokens, type/spacing scales,
   webapp dark variant fix, homepage theme toggle.
2. **Cabinet (webapp)** — one primitive set, box-to-box screens, centralized
   copy, retire grain/gradient noise.
3. **Admin** — same primitives, cleanup of raw-Tailwind pages.
4. **Marketing** — migrate 10 legacy pages onto the homepage module pattern,
   kill `lp-*` legacy CSS, copy pass.
5. **Bots** — centralize texts into `copy/catalog.ru.json` via
   `portal_bot/copy_catalog.py`, rewrite tone, merge duplicate help flows.
6. **Flutter** — extract strings, tone pass (design already closest to goal).

## Phase 1 implementation (done)

Token changes (`shared/design-tokens.json`, version `2026-07-hig-w01`):

- palette: added `surface_subtle_dark`, `surface_muted_dark`;
- typography: added HIG-like type scale (`size_display`, `size_title`,
  `size_title_2`, `size_title_3`, `size_body`, `size_callout`,
  `size_footnote`, `size_caption`) and weights 400/500/600/700, plus
  `display_letter_spacing: -0.02em`;
- new top-level `spacing` scale (`2xs`..`3xl`), schema updated;
- motion: added `easing_spring`.

Adapter changes (`shared/design-tokens.ts`):

- `getDesignTokenDarkCssVariables()` — dark remap for the adaptive set
  (bg, surfaces, text, lines, focus, accent, statuses, shadows, button, nav,
  card, table, skeleton, progress);
- `getDesignTokenThemeCss(density)` — full theme stylesheet: light on
  `:root`, dark under `:root.dark` and `:root[data-theme="dark"]`, with
  `color-scheme`;
- `getDesignTokenDensityCssVariables(density)` — density-only subset for
  scoped overrides (admin);
- new adaptive accent group: `--pokrov-accent`, `--pokrov-accent-hover`,
  `--pokrov-accent-contrast`, `--pokrov-accent-soft`;
- legacy `-dark`-suffixed variables remain emitted and static for
  compatibility during migration.

Surface wiring:

- webapp `layout.tsx`: token `<style>` tag instead of inline body style;
- webapp `globals.css`: `@custom-variant dark (&:where(.dark, .dark *))` —
  compiled CSS now has 0 `prefers-color-scheme: dark` utility blocks;
- admin `layout.tsx`: density-only inline vars (colors stay adaptive);
- marketing `layout.tsx`: token `<style>` in head, inline body style removed;
- marketing homepage topbar: theme toggle (`[data-theme-toggle]`, sun/moon)
  in desktop topbar and mobile menu, handled by the existing pre-hydration
  delegated click script; persists under `pokrov-theme`.

## Phase 1 verification

- `npm run build` green in `webapp/` and `marketing/`;
- Playwright smoke against static exports:
  - marketing: `--pokrov-bg` `#f7f3eb` -> `#111715`, accent `#20674f` ->
    `#8ac4ab` on toggle; choice persists across reload; toggle visible;
  - webapp: `.dark` class remaps `--pokrov-bg` identically;
  - compiled webapp CSS: `dark:` utilities are class-driven (385 `.dark`
    selectors, 0 media-query dark blocks);
  - light/dark homepage screenshots reviewed.

## Phase 2 implementation (webapp visual layer — done)

`webapp/src/app/globals.css` consolidated (1,970 -> ~1,460 lines):

- deleted dead classes: `signal-grid`, `typing-dot`, `float-slow`,
  `pulse-glow`, `marquee*`, `tg-bottom-nav`, `shield-status`, `bento-*`,
  `connection-row*`, `quick-action-*`, `alert-card`, `location-pill`,
  `stat-value-lg`, `compact-nav-item`, `.grain` (usage census: 0 TSX refs);
- merged the three styling generations: gen-1 definitions + "Atlas
  flattening overrides" collapsed into single token-driven definitions
  (`glass-card`, `stat-card`, `node-card`, `btn-primary`, `outline-btn`,
  `skeleton`, `badge*`, `progress*`, `stat-icon*`, `chat-bubble*`,
  `empty-state`, `gradient-text` -> flat accent);
- deleted the whole `.dark body { --atlas-* }` remap block (~50 lines) and
  all per-class `.dark` color overrides — adaptive `--pokrov-*` variables
  now drive the `--atlas-*` bridge in both themes from one definition;
- body background: one calm token gradient, no stacked white overlays, no
  grain/noise overlay, no fixed decorative gradient div in `layout.tsx`;
- body className simplified (dropped redundant `dark:bg-*`/`dark:text-*`).

Verified: build green; entry page light/dark screenshots coherent (no
mixed-theme artifacts).

Remaining phase 2 follow-ups (not done): consolidate `shell-primitives.tsx`
vs `cabinet/ui.tsx` into one primitive set; centralize hardcoded RU copy;
per-screen box-to-box pass for cabinet pages.

## Phase 4 partial implementation (marketing legacy shell — calm pass)

- `marketing/src/app/globals.css`: removed `body::before` grid pattern (both
  themes), `background-attachment: fixed`, and multi-radial body gradient
  stacks; body is now one calm `--lp-bg -> --lp-bg-2` gradient per theme;
- fixed legacy light-theme bug: `.lp-stage-steps` chips were
  white-on-white inside flattened light cards; now adaptive
  (`color-mix` on `--lp-text`), dark override selectors removed.

Verified: build green; `/install` and `/vpn` screenshots in both themes.

Remaining phase 4 follow-ups: migrate 10 legacy pages off
`marketing-landing.tsx` / `lp-*` onto the homepage module pattern; retire the
remaining ~50 `[data-theme="dark"] .lp-*` patch selectors; copy pass.

## Phase 4b implementation (marketing lp-* layer rewrite — done)

Instead of rewriting 10 page files, the shared `lp-*` class vocabulary was
kept and its stylesheet layer rebuilt token-first
(`marketing/src/app/globals.css`, 2,393 -> 1,819 lines):

- one adaptive `:root { --lp-* }` block mapped to adaptive `--pokrov-*`
  variables; the `[data-theme="dark"] { --lp-* }` remap block deleted;
- the entire `[data-theme="dark"] .lp-*` patch section (~50 selectors)
  deleted; only the toggle-thumb transform and `color-scheme` remain;
- the trailing "flattening" override section deleted; values folded into
  base definitions; unused `.home-v2-*` selectors and `.lp-bg-blobs`
  removed;
- hardcoded light-only colors replaced with `--lp-*` vars across all
  `lp-*` / `checkout-*` / legal rules; primary buttons flat
  `--lp-primary` / `--lp-primary-contrast`; decorative multi-layer
  gradients replaced with calm adaptive surfaces; gold accent retained
  only for warning/fallback checkout chips;
- `backdrop-filter` kept only on sticky nav shells (overlay planes).

Verified: build green (17 pages); light+dark screenshots of `/`,
`/install`, `/vpn`, `/devices`, `/checkout`, `/offer`, `/youtube` reviewed —
no mixed-theme artifacts, homepage untouched; zero page errors in console.

Remaining phase 4 follow-ups: deeper selling-copy pass per page (current
copy is acceptable); optional later migration of secondary pages onto the
homepage module pattern is no longer blocking since the legacy layer is now
token-driven.

## Phase 5 implementation (bot copy centralization — core done)

New module `portal_bot/bot_texts.py`: `bot_text(key, **variables)` resolves
through `copy/catalog.ru.json` at call time (fixes the import-time freeze the
old `TEXTS` dict had), with in-code fallbacks mirroring catalog values.
Catalog bumped to `2026-07-02-bot-core`; +18 `bot.*` items (29 total), tone
`warm`, `allowed_public: false`. Admin copy (`bot.admin.stats`) stays
fallback-only so operator wording (Stars revenue) never enters the governed
public catalog.

- `TEXTS` dict deleted (6 of 11 keys were dead); all 9 live call sites moved
  to `bot_text()`: home menu, returning/new-user start, status card,
  status-none, long tariffs, payment success, admin stats.
- Help surface unified: `support` callback and `/support` now share
  `_support_hub_keyboard()` + `bot.support.hub` (previously two drifting
  texts/keyboards). `confused_help` stays as the no-jargon triage screen.
- Device wizards merged: `instruction` (`_render_device_select` +
  `_render_platform_screen`) is the single path; platform screens gained the
  "✅ Приложение уже стоит" funnel button into the access-check step
  (`simple_step3`). `mode_simple` / `simple_*` callbacks kept as aliases for
  old chat messages; duplicate step texts deleted.
- Tone pass (warm, direct, no emoji spam) on all moved texts; test-pinned
  phrases ("Давайте без терминов", trial wording, keyboard labels) preserved.

Verified: `test_bot_paywall` (43 passed, 1 skipped), story contracts,
public-copy guardrails, app-bot parity, helpbot/feedbackbot lifecycle — all
green. `test_brain_telegram_bot_menu_check` fails on clean master too
(missing `puttykeys` dep in venv — pre-existing, unrelated).

Remaining phase 5 follow-ups: FAQ_ANSWERS + toast texts still inline in
bot.py (light polish candidates); helpbot/feedbackbot inline texts untouched
(they already read `bot.support.welcome` / `bot.feedback.*` for headlines).

## Phase 2b implementation (webapp primitive consolidation — done)

`cabinet/ui.tsx` (`cab-*` classes) is the canonical primitive set;
`shell-primitives.tsx` shrank to layout-level pieces only:

- deleted duplicate exports: `StatusBadge` (use `Badge` from cabinet/ui),
  `FormField` (use `Field`), `shellButtonClass`/`shellLinkClass`/
  `shellButtonProps`/`shellLinkProps` (use `Button`), public `Surface`
  (kept as internal impl detail of `DialogShell`);
- kept: `SectionHeader`, `MetricCard`, `DialogShell`, `EmptyState`,
  `Timeline` — now typed against cabinet `Tone` and free of per-selector
  `dark:` overrides (adaptive atlas vars only);
- `shell-boundary.tsx` and all four `not-found.tsx` boundary pages moved
  from raw `btn-primary`/`outline-btn` + utility soup to `<Button>`;
  decorative radial-gradient underlays removed from boundary screens.

Verified: webapp build green (34 pages); 404 screenshot light+dark —
calm surfaces, emerald/mint primary, no mixed-theme artifacts.

## Phase 2c implementation (webapp copy wiring — done)

The copy catalog (`copy/catalog.ru.json`) is now live on webapp user
surfaces; catalog version `2026-07-02-webapp-wire`:

- 15 keys wired via `getCopyText(key, fallback)` (entry title/subtitle/CTA,
  dashboard support CTA, subscription/checkout/support/devices/statistics/
  downloads titles+subtitles); `cabinet.handoff.*` (5) were already wired in
  `lib/api.ts`;
- catalog `ru` values synced byte-identical to current on-page copy first
  (stale April values replaced), so rendered output is unchanged;
- 28 keys intentionally left unwired: slots removed in redesigns
  (entry steps/note/card, cabinet.entry.*), dynamic conditional slots
  (dashboard primary CTA, subscription/support subtitles, cabinet dashboard
  hero), and `cabinet.*` duplicates of the same slot (wired `webapp.*`).

Admin copy (~1,160 RU lines) deliberately stays out of the catalog: it is
operator-facing, has no catalog namespace, and already has local pockets
(`admin/nav.ts`, `admin-format.ts`).

Verified: build 34/34 pages; text-integrity + public-copy guardrails +
marketing readiness — 19 passed.

## Phase 3 implementation (webapp dark: purge — done)

All per-selector `dark:` Tailwind utilities removed from webapp TSX
(~170 occurrences across 20 files: admin pages nodes/promos/broadcast/
referrals/bonuses/tickets/funnel, entry auth, loading shell, entry page,
double-bezel, preloader, logo, misc):

- `dark:` restatements of adaptive `--atlas-*` bases deleted outright;
- hardcoded light-only literals (`border-white/20`, `border-violet-200/50`,
  `bg-black/[0.03]`, `ring-emerald-900/10`, hex canvas colors) replaced
  with adaptive atlas vars (`--atlas-border`, `--atlas-canvas-alt`,
  `--atlas-status-*-bg`, `--atlas-progress-fill`);
- tickets selected-row inversion mapped to `--atlas-text`/`--atlas-canvas`;
- only leftover `dark` token is the `qrcode` lib's `color.dark` option.

Theme-agnostic alpha accents (modal scrims, tone tints over adaptive
backgrounds) intentionally kept. Structural decomposition of the large
admin pages (nodes 1,097 lines) deferred — no longer a theming risk.

Verified: build 34/34; light+dark screenshots of entry, dashboard shell,
admin gate — no mixed-theme artifacts, zero page errors.

## Phase 6 implementation (Flutter client copy pass — done)

Repo `C:\Users\kiwun\Documents\ai\POKROV-app` (Melos monorepo; all UI copy
in `packages/app_shell`, single library with part-files). No ARB/l10n infra
introduced — extended the existing per-feature `*_labels.dart` pattern:

- new `src/shared/ru_plural.dart`: `ruDays()` with correct Russian plural
  rules (11–14 exception); 19 call sites replaced the hardcoded
  `'$n дней'` bug class (access_labels, seed_shell, profile, onboarding,
  rewards) + unit tests;
- raw `$error` interpolation removed from all user-facing snackbars in
  `seed_shell.dart` (8 sites) — calm "what happened + next step" messages,
  error detail moved to `debugPrint`;
- jargon fixes: "триал" → "пробный период", "подготовьте устройство" →
  "активируйте доступ на этом устройстве", "системный модуль не ответил" →
  "система не ответила вовремя", "приложите диагностику" → phrasing that
  matches the actual opt-in diagnostics flow; `'Недоступно'` →
  `'Пока недоступно'`;
- copy contract strengthened: `ui_copy_contract_test.dart` now also forbids
  `триал`, `системный модуль`, `подготовьте устройство` and asserts no
  user-facing `$error` interpolation in seed_shell.

Verified: `flutter test` in app_shell — 136 passed; `flutter analyze` clean.

## Polish pass (instructions everywhere — done)

Goal: step-by-step instructions and FAQ on every "stuck" surface, with
token-driven SVG pictograms (no binary assets — inline SVG on adaptive
`--atlas-*` vars, follows light/dark automatically; generated-assets
policy does not apply to code-drawn vectors).

Bot (`portal_bot/bot.py`, catalog `2026-07-02-instructions`):
- `FAQ_ANSWERS` expanded 5 → 9 topics (+payment-not-applied, +codes,
  +speed, +login/account, +manual-connection with safety note about the
  personal link);
- new `faqmenu` screen (`show_faq_menu` + `FAQ_MENU_ITEMS`, text key
  `bot.faq.menu`) listing all 9 topics + escalation to support; FAQ answers
  now return to the menu, not the hub;
- support hub keyboard slimmed (3 hardcoded FAQ buttons → one "Частые
  вопросы" entry); triage screen (`confused_help`) also links the FAQ;
- tests: `test_faq_menu_lists_every_answer_topic` (menu ⇄ answers
  bijection), `test_faq_answers_do_not_leak_raw_links_or_stars`, extended
  confused-help labels test.

Webapp (`components/cabinet/instructions.tsx` + `cab-steps`/`cab-faq` CSS):
- `InstructionSteps`: illustrated step cards (6 pictogram kinds: download,
  login, connect, shield, link, refresh) with numbered badges; wired into
  downloads page as "Как подключиться за 3 шага";
- `FaqAccordion`: native `<details>` accordion on cab-panel; support page
  gained a 7-entry "Частые вопросы" section (connect, payment, not-working,
  speed, device transfer, codes, manual link + safety);
- reduced-motion respected (chevron transition disabled).

Verified: bot matrix 54 passed; webapp build 34/34; light+dark screenshots
of steps + accordion — clean in both themes, zero page errors.

## Premium interaction uplift (app + webapp — done)

### Flutter app (`POKROV-app/packages/app_shell`, 136 → 142 tests)
- **Bug fix**: busy sweep on the connect orb froze after one 1250ms pass —
  now `repeat()` while `runsSweep`, clean stop on settle; connected orb
  breathes (`breathPeriod` 1800ms, repeat-reverse). Reduced motion keeps
  static behavior. `PokrovLoopingMotion` gate collapses infinite loops
  under `flutter test` (pumpAndSettle safety) with `debugLoopingOverride`.
- **Dead curves wired**: `spring` = release curve of HomeChip /
  SettingsRowPressSurface / new PokrovPressable; `emphasized` = home reveal
  + all sheet animations.
- **`PokrovPressable`** (design_system): press 0.97 quick/easeIn, spring
  release, hover 1.01; wraps primary CTAs (paywall, onboarding, rewards
  claim, warp confirm); `pokrov-pressable-motion` key.
- **`PokrovHaptics`** tiers (tap/impact/success/error, guarded): orb tap →
  impact, →connected → success, →error → error; snack tones wired.
- **`showPokrovSnack`** (tone icon success/danger/info): all 19 raw
  snackbar sites replaced, byte-identical messages; sheets got
  `sheetAnimationStyle` (280ms emphasized, zero when reduced).
- **Animated skeletons** (opacity pulse 1.0↔0.55, 1100ms), **tab content
  transition** (fade+6px over 180ms, state alive), **pull-to-refresh** on
  profile + rewards.
- Verified: `flutter analyze` clean; 142 tests green; contract test updated
  ("repeats while busy, settles when done") + 6 new contracts.

### Webapp (build 34/34, guardrails green)
- **Button loading state** (`loading` prop, cabSpin spinner, stable width):
  adopted on support submit, redeem, settings email actions, checkout.
- **Toast system** (`components/cabinet/toast.tsx`): ToastProvider +
  useToast; tones on --atlas-status-* vars; AnimatePresence enter/exit;
  auto-dismiss 3.5s, pause-on-hover; aria-live; Telegram
  `notificationOccurred` haptics (previously dead code) wired. Adopted:
  ticket created, redeem, settings saves, copy.
- **CopyButton** (icon morph copy→check, toast, `data-haptic="rigid"`) on
  subscription personal link, replacing copyStatus text-state.
- **Animated dialogs**: support compose modal (backdrop fade + slide-up,
  role=dialog, Escape, autofocus, modal-open) and mobile drawer (slide-in)
  via AnimatePresence; reduced-motion aware.
- **Live status**: .cab-status tone crossfade + success glow breathing
  (3s, motion-safe); pulsing status dot on connections tile; `useCountUp`
  on numeric dashboard tiles.
- **Polish**: `.cab-btn--primary` → medium haptic mapping; duration-var
  fallbacks (27 sites); focus-visible rings on icon buttons / mobile nav /
  FAQ summary; desktop warm-refresh bar (2px).

## Non-goals / constraints

- No public copy that violates the wording rule from `AGENTS.md`.
- No silent-auto-update or store/stable claims in any copy.
- Legacy `-dark` variables are not removed until all consumers migrate.
