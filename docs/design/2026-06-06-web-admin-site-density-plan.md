# Web, Admin, And Site Density Plan

Last updated: 2026-06-07

## Status

Active implementation plan for the next web/admin/site pass after the
personal cabinet reset.

This plan was synthesized from a read-only OpenCode `opencode-go` consilium:

- `deepseek-v4-pro`
- `qwen3.7-max`
- `minimax-m3`
- `glm-5.1`
- `mimo-v2.5-pro`
- `kimi-k2.6`

The consilium was constrained to `marketing/`, the `webapp` cabinet boundary,
and the admin operator surface. It was explicitly told not to inspect secrets,
archives, deploy state, native client code, signing, store gates, RU-origin
claims, or backend rewrites.

## Verdict

The highest-impact next stage is not another cabinet pass. The cabinet reset is
implemented and verified.

The next product-quality problem is visible density:

- the public homepage repeats the same story across too many sections and
  card grids;
- mobile marketing pages can feel like a long stack of blocks instead of one
  clear path;
- admin is structurally useful, but still keeps too much permanent prose and
  can stack awkwardly before the `2xl` breakpoint;
- the webapp entry route still uses older heavy entrance motion.

## Surface Priorities

### P0: Marketing Homepage

Goal: make the first public path feel simple, expensive, and direct.

Implementation rules:

- one hero with one primary action;
- no card-grid proof wall above the fold;
- no repeated `5 дней бесплатно` explanation across header, hero, sections,
  pricing, and final CTA;
- no `FadeUp` cascade on every section;
- no hover-lift on non-interactive marketing cards;
- mobile first viewport should show the hero, not a stack of proof cards;
- public beta honesty stays visible where it matters.

Acceptance metrics:

- homepage first viewport at `390px` shows one primary story and no horizontal
  overflow;
- total homepage section count is reduced from the old long stack;
- first mobile viewport has one primary CTA;
- scroll depth to pricing is shorter than the old page;
- no store, trusted signing, stable `1.0.0`, RU-origin, raw Android audit, or
  production WARP claim is added.

### P0: Admin Trim

Goal: keep admin as an operator cockpit, not a prose-heavy dashboard.

Implementation rules:

- sidebar groups show labels and items, not repeated descriptions;
- the topbar carries current context and actions, not breadcrumb/prose
  duplication;
- right rail keeps status and quick links, not permanent operator training
  paragraphs;
- at `xl` widths, admin should not become a pure vertical stack before `2xl`.

Acceptance metrics:

- at `1440px`, sidebar and main content can sit side by side;
- persistent sidebar prose is reduced;
- the right rail has status and quick transitions only;
- admin e2e remains green.

### P0: Webapp Entry

Goal: keep browser entry continuation-first and visually aligned with the
compact cabinet without reopening the implemented cabinet screens.

Implementation rules:

- remove old `FadeUp` cascades from the entry page;
- keep one compact sign-in surface;
- do not turn entry into marketing;
- authenticated users still redirect into `/dashboard/`.

Acceptance metrics:

- entry build and cabinet e2e remain green;
- no cabinet IA change;
- no raw subscription or QR content appears on the first entry layer.

## P1 Follow-Up

- Decide and document the long-term split between the homepage-specific
  `MarketingHomePage` and reusable `MarketingLanding` template.
- Apply the same density rules to `/mobile/`, `/devices/`, `/telegram/`,
  `/youtube/`, `/tiktok/`, and `/vpn/`.
- Trim secondary admin dashboard cells if first-paint screenshots still feel
  like nested card walls.
- Add a dedicated responsive screenshot pass for marketing routes.

### P1 Implementation Notes

Status as of `2026-06-07`:

- `/` remains owned by the homepage-specific `MarketingHomePage`.
- `/mobile/`, `/devices/`, `/telegram/`, `/youtube/`, and `/tiktok/` remain on
  `MarketingLanding`, but the template is now compressed around hero,
  scenarios, pricing, FAQ, related links, and a final CTA.
- `/vpn/` remains a separate longform search-intent surface because it is the
  only public page intentionally using explicit `VPN` / `ВПН` SEO wording.
- The old secondary-page proof wall, downloads block, review/default feedback
  block, related card grid, and oversized footer rail are no longer part of
  the reusable secondary landing template.
- `marketing/scripts/check-marketing-responsive.mjs` is the dedicated
  responsive smoke/screenshot pass for `/`, secondary landing pages, and
  `/vpn/` at `390`, `700`, and `1180` px widths.

## P2 Follow-Up

- Move remaining marketing/admin style constants closer to
  `shared/design-tokens.json`.
- Add doc or test guardrails for admin arbitrary radius drift.
- Add a marketing density README that records which component owns `/` and
  which template owns SEO landing pages.

### P2 Implementation Notes

Status as of `2026-06-07`:

- Admin route layout now applies `getDesignTokenCssVariables("admin")` to the
  admin subtree, so shared admin helpers use admin density rather than cabinet
  density.
- Shared admin shell helpers now use token-backed radius, padding, and shadow
  classes such as `--pokrov-radius-panel`, `--pokrov-radius-card`,
  `--pokrov-radius-control`, `--pokrov-panel-padding`, and
  `--pokrov-card-padding`.
- Marketing `--lp-*` CSS variables now bridge through `--pokrov-*` design
  token variables with local fallbacks instead of standalone first-choice
  constants.
- `tests/test_admin_design_guardrails.py` protects the shared admin helper
  layer from new arbitrary-radius drift and checks the marketing token bridge.
- `marketing/README.md` records route-density ownership for `/`, reusable SEO
  landing pages, `/vpn/`, checkout/install, and legal pages.

## Verification

Required for this pass:

- `npm.cmd run build` in `marketing/`
- `npm.cmd run check:seo` in `marketing/`
- `npm.cmd run check:responsive` in `marketing/` for marketing route layout
  changes
- `npm.cmd run build` in `webapp/`
- `npm.cmd run test:e2e:admin` in `webapp/` when admin shell changes
- `npm.cmd run test:e2e:cabinet` in `webapp/` when entry/cabinet boundary
  changes
- root copy guards when visible Russian copy changes:
  `python -m pytest tests/test_frontend_text_integrity.py tests/test_public_copy_guardrails.py -q`
