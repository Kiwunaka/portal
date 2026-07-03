# POKROV Design System

Last updated: 2026-07-02

This file is the root design contract for public, cabinet, admin, and release-support surfaces in this repository.

## Source Of Truth

- Canonical tokens: `shared/design-tokens.json`
- Token schema: `shared/design-tokens.schema.json`
- Token TypeScript adapter: `shared/design-tokens.ts`
- Product facts and public URLs remain in `shared/product-facts.json`, `shared/public-urls.json`, and `shared/portal-config.ts`.
- Active client design docs live in `C:/Users/kiwun/Documents/ai/POKROV-app/DESIGN.md` and `C:/Users/kiwun/Documents/ai/POKROV-app/docs/design/DESIGN.md`.

## Theme Model (2026-07 HIG wave)

Dark mode is token-remap based, not selector-patch based:

- `getDesignTokenThemeCss(density)` from `shared/design-tokens.ts` emits the full theme stylesheet: light values on `:root`, dark values under `:root.dark` (webapp) and `:root[data-theme="dark"]` (marketing), plus `color-scheme`.
- Both web layouts inject this CSS as a `<style>` tag. Do not inject the full token set as inline `style` attributes: inline custom properties cannot be remapped by the dark selector.
- Adaptive variables keep one name in both themes (`--pokrov-bg`, `--pokrov-surface`, `--pokrov-text`, `--pokrov-accent`, status/button/nav/card/table/skeleton/progress groups). Consume them directly; never hand-write per-component `.dark` overrides for colors that already have a token pair.
- Legacy `-dark`-suffixed variables stay emitted and static for backward compatibility during migration; new work must not reference them.
- Scoped density overrides (for example the admin subtree) must use `getDesignTokenDensityCssVariables(density)` so inline styles never freeze adaptive colors.
- Webapp Tailwind v4 binds the `dark:` variant to the `.dark` class via `@custom-variant dark` in `webapp/src/app/globals.css`; the manual toggle and utilities can no longer disagree.
- Theme choice persists under the `pokrov-theme` localStorage key on both web surfaces and falls back to `prefers-color-scheme`.

Type and spacing scales live in tokens: `--pokrov-font-size-*` (display, title, title-2, title-3, body, callout, footnote, caption), `--pokrov-font-weight-*`, and `--pokrov-space-*` (2xs..3xl). Motion adds `--pokrov-easing-spring` for gentle overshoot; transform/opacity-only animation and `prefers-reduced-motion` fallbacks remain mandatory.

## Brand Direction

POKROV should feel calm, premium, reliable, and practical. The interface should help a user start in the app, understand account state, and recover through the cabinet or support without needing transport-layer knowledge.

Use:

- light canvas, white surfaces, mint status accents, and deep green primary actions;
- an elevation-aware dark theme on off-black greens (never pure black), with the mint accent `#8ac4ab` as the dark-mode primary;
- grouped boxes with breathing room, thin separators, and restrained motion with clear focus states;
- dense but readable admin surfaces;
- app-first language for onboarding, trial, renewal, support, and downloads.

Avoid:

- hidden, cloaked, or stuffed `VPN` wording in public copy (visible SEO/search-intent `VPN` wording on dedicated surfaces is owner-approved per `AGENTS.md`);
- legacy subtitle lockups as visible public branding;
- decorative visual noise that competes with account, payment, or safety state: stacked gradients, grain/noise overlays, and glass blur on content planes are being retired in the HIG wave;
- unsupported public safety claims for Android, Windows, paid checkout, or downloads.

## Surface Rules

| Surface | Density | Primary job |
| --- | --- | --- |
| Marketing | `public` | Explain POKROV and route users to app-first start, cabinet, checkout, or support. |
| Checkout | `public` | Show plans and payment availability truthfully; hide or disable unavailable providers. |
| Cabinet | `cabinet` | Keep subscription, devices, downloads, support, and profile state scannable. |
| Admin | `admin` | Prioritize operational truth, filters, warnings, and auditability over promotion. |
| Client docs | `product` | Keep Android/Windows beta limitations precise and aligned with release gates. |

## Generated Assets

Generated images, icons, screenshots, app-store graphics, and social preview derivatives must have:

- prompt or source-reference note;
- source asset or approved master reference;
- final dimensions and file path;
- reviewer/date note;
- explicit statement that the asset does not contain legacy public `VPN` wording unless it is an unavoidable compatibility label.

Do not ship generated release assets from scratch without checking them against the current brand master and token palette.
