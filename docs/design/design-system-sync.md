# Design System Sync

Last updated: 2026-07-03

`DESIGN.md` is the root design contract for this repository. `shared/design-tokens.json` is the machine-readable token source for marketing, cabinet, admin, and release-support UI.

## Required Sync Points

| Area | Source | Consumer |
| --- | --- | --- |
| Palette, radius, shadows, type, density | `shared/design-tokens.json` | `shared/design-tokens.ts`, marketing, webapp |
| Token shape | `shared/design-tokens.schema.json` | tests, review, token generation |
| Historical Atlas Glass research | `docs/design/atlas-glass/` | reference only when investigating prior web/admin redesign choices |
| Client design | `C:/Users/kiwun/Documents/ai/POKROV-app/DESIGN.md` | Android and Windows shell work |
| Generated assets | `docs/design/generated-assets-policy.md` | launch, store, social, app assets |

## Atlas Glass Notes

- The current web direction is the `2026-07 HIG wave` recorded in `DESIGN.md`: token-remapped light/dark themes, calmer HIG-style surfaces, and app-first onboarding around `trial -> install -> first connection`.
- `shared/design-tokens.json` remains the authority for light/dark palette, glass surfaces, shadows, density, focus, status color, skeleton, progress, and navigation tokens.
- `shared/design-tokens.schema.json` must require every token field consumed by `shared/design-tokens.ts`; optional schema fields are allowed only when the adapter does not dereference them directly.
- `product`, `public`, `cabinet`, and `admin` are separate density modes. `product` is no longer an alias for `public`.
- Marketing, cabinet, and admin may use different density, but should feel like the same product family: public pages are acquisition-oriented, cabinet screens guide the next action, and admin screens favor compact evidence.
- Theme defaults to the system preference; explicit user choice belongs in browser UI state only. Dashboard/user snapshots must not be persisted to browser storage.
- QR codes, raw config links, transport acronyms, and node internals are not first-layer consumer UI. Show manual connection only in explicit recovery or fallback states.
- Text integrity checks cover active frontend, shared copy/token sources, and `docs/design/`; retained archive and audit folders are intentionally skipped to avoid false release blockers from historical mojibake.

## Open Beta v4 Notes

- Marketing, checkout, cabinet, admin, and client docs must stay visually aligned around the `2026-07 HIG wave` direction and the retained `quiet-core-luminous-edge` product truth.
- Android and Windows public visuals must not imply public readiness until signing, handoff, and audit gates pass.
- Admin views should use the `admin` density and favor compact evidence over large promotional layouts.
- The completed June cabinet and web/admin/site density plans are archived under `docs/archive/design-plans/`. Current work should start from `DESIGN.md`, `shared/design-tokens.json`, and implemented UI, not from those completed plans.
- Public surfaces may link to `/install/` as gated help, but public download claims require runtime handoff evidence.
- Admin route layout applies the `admin` density token set to the admin subtree.
  Shared admin helpers should use token-backed radius, padding, and shadow
  variables; new arbitrary numeric radii in shared admin helpers should fail
  `tests/test_admin_design_guardrails.py`.
- Marketing `--lp-*` variables should bridge through `--pokrov-*` variables
  emitted by `getDesignTokenCssVariables("public")`; hard-coded route
  exceptions need a route-local reason.

## Review Checklist

- Token changes include schema-compatible JSON.
- Public copy uses `POKROV` as the product line and avoids direct public `VPN` wording.
- Any new generated image includes source prompt, dimensions, intended use, and review note.
- Screenshots used for launch or store work are fresh and match the current beta limitations.
- Reduced-motion, keyboard focus, text integrity, and light/dark screenshots are part of frontend Definition of Done when visible surfaces change.
