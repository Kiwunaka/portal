# POKROV Design System

Last updated: 2026-08-13

Document class: CANONICAL

This file is the sole current design owner and root design contract for public, cabinet, admin, and release-support surfaces in this repository.

## Source Of Truth

- Canonical tokens: `shared/design-tokens.json` (theme `pokrov-clear`, version `2026-07-redesign-w01`)
- Token schema: `shared/design-tokens.schema.json`
- Token TypeScript adapter: `shared/design-tokens.ts`
- Retained history: `docs/superpowers/specs/2026-07-04-design-foundation-redesign-design.md` is a historical redesign spec, not current authority.
- Product facts and public URLs remain in `shared/product-facts.json`, `shared/public-urls.json`, and `shared/portal-config.ts`.
- Active client design docs live in `C:/Users/kiwun/Documents/ai/POKROV-app/DESIGN.md` and `C:/Users/kiwun/Documents/ai/POKROV-app/docs/design/DESIGN.md`.

## Theme Model

Dark mode is token-remap based, not selector-patch based:

- `getDesignTokenThemeCss(density)` from `shared/design-tokens.ts` emits the full theme stylesheet: light values on `:root`, dark values under `:root.dark` (webapp) and `:root[data-theme="dark"]` (marketing), plus `color-scheme`.
- Both web layouts inject this CSS as a `<style>` tag. Do not inject the full token set as inline `style` attributes: inline custom properties cannot be remapped by the dark selector.
- Adaptive variables keep one name in both themes (`--pokrov-bg`, `--pokrov-surface`, `--pokrov-text`, `--pokrov-accent`, status/button/nav/card/table/skeleton/progress/switch groups). Consume them directly; never hand-write per-component `.dark` overrides for colors that already have a token pair.
- Legacy `-dark`-suffixed variables stay emitted and static for backward compatibility during migration; new work must not reference them.
- Scoped density overrides (for example the admin subtree) must use `getDesignTokenDensityCssVariables(density)` so inline styles never freeze adaptive colors.
- Webapp Tailwind v4 binds the `dark:` variant to the `.dark` class via `@custom-variant dark` in `webapp/src/app/globals.css`; the manual toggle and utilities can no longer disagree.
- Theme choice persists under the `pokrov-theme` localStorage key and falls back to `prefers-color-scheme`.

Theme availability by surface (2026-07 redesign decision):

- Marketing/landing is **light-only** by policy. The dual-theme token emission stays (shared code path), but the landing ships without a theme toggle once the sub-project 1 rebuild lands.
- Cabinet, admin, and the client app keep light + dark with a manual toggle.

Type and spacing scales live in tokens: `--pokrov-font-size-*` (display, title, title-2, title-3, body, callout, footnote, caption), `--pokrov-font-weight-*`, and `--pokrov-space-*` (2xs..3xl). Motion adds `--pokrov-easing-spring` for gentle overshoot; transform/opacity-only animation and `prefers-reduced-motion` fallbacks remain mandatory.

## Typography

- Brand family: **Golos Text** (display + body), Cyrillic-first. Mono: JetBrains Mono for technical strings.
- Marketing loads Golos through `next/font/google` with `latin` + `cyrillic` subsets and self-hosts it at build time. The cabinet imports pinned `@fontsource-variable` packages for Golos and JetBrains Mono, which bundle the files with the static application. CSS-only font-family references without a bundled font source are forbidden.
- Consume the `--font-body` / `--font-display` variables (which resolve from the `next/font` `--font-golos` variable). Never consume the raw `--pokrov-font-body` / `--pokrov-font-display` family strings directly: `next/font` uses hashed family names, so the raw string will not resolve to the self-hosted face.
- Display letter-spacing is `-0.01em`; Golos needs less negative tracking than the retired Manrope.
- Golos supports weights 400–900; surfaces may use up to 800 for display headlines without a new token.

## Brand Direction

POKROV should feel calm, premium, reliable, and practical. The interface should help a user start in the app, understand account state, and recover through the cabinet or support without needing transport-layer knowledge.

Use:

- pure white canvas (`#ffffff`), solid white surfaces with hairline borders, and the fresh emerald primary `#12805a` (hover `#0f6b47`, tint `#e6f4ed`) for actions;
- the iOS system green `status_green` (`#34c759` light / `#30d158` dark) **only** for the "connected" state and switch fills — never for text or generic accents;
- an elevation-aware dark theme on off-black greens (never pure black) with solid surfaces and the mint accent `#8ac4ab` as the dark-mode primary;
- grouped boxes with breathing room, thin separators, light tight shadows, and restrained motion with clear focus states;
- dense but readable admin surfaces;
- app-first language for onboarding, trial, renewal, support, and downloads.

Text roles: `text` (`#16181d`, 17.8:1) for primary, `text_soft` (`#5e6772`, 5.7:1) for secondary. `text_muted` (`#9aa1a9`, ~2.6:1) is decorative-only — placeholders, disabled states, ornament; anything a user must read uses `text_soft` or stronger.

Deprecated (keep tokens for compatibility, no new usage): `sage`, `gold_soft`, legacy `-dark`-suffixed variables, card `inner_edge` / `inner_edge_dark` (both now `none`).

## Public Wording Boundary

Visible `VPN` / `ВПН` wording is allowed on dedicated SEO/search-intent
surfaces when it is useful to users and tied to the real POKROV app flow.


## Control Canon (iOS-style, 2026-07 redesign)

The control vocabulary for cabinet, admin, and client surfaces (implemented per surface in sub-projects 1–3):

- **Switch:** 51×31px pill, 27px thumb, `status_green` fill when on, `rgba(120,120,128,0.16)` track when off (`0.32` dark), spring transition from `component.switch.transition`. Emitted as `--pokrov-switch-*` variables.
- **Grouped lists:** white (or `surface_raised_dark`) grouped boxes on `canvas_alt`, inset separators from `line`, chevron affordance for navigation rows.
- **Buttons:** marketing CTAs use `pill` radius; cabinet/app controls use `control` radius (`0.875rem`); minimum touch target 44px.
- **Tooltips, popovers, banners:** translucent overlay planes are allowed (glass policy: overlays only, max blur 16px); content planes stay solid.

## Iconography

- Web surfaces: `lucide-react` is the single icon family, imported directly (the legacy material-symbols naming shim was retired with the sub-project 2 cabinet rebuild).
- Third-party service logos (YouTube, TikTok, Instagram, Discord, …) come from `simple-icons` in the brand's official color; never redraw brand marks by hand. If a brand is absent from simple-icons (e.g. OpenAI, removed at the brand's request), fall back to a semantic lucide icon — do not hand-roll the logo.
- Glyph characters (▶ ♪ ⌘ ✦ and similar) are not icons; they are banned in UI.
- Custom SVG is reserved for the POKROV mark and product graphics.
- Client: flutter-material per client-repo canon.

## Surface Rules

| Surface | Density | Primary job |
| --- | --- | --- |
| Marketing | `public` | Explain POKROV and route users to app-first start, cabinet, checkout, or support. Light-only. |
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
- explicit statement that any visible `VPN` / `ВПН` wording follows the scoped SEO/search-intent boundary above.

Do not ship generated release assets from scratch without checking them against the current brand master and token palette.
