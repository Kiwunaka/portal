# R02 Design System, Brand, Visual Audit

Status: research complete - implementation owners required
Last researched: 2026-04-26
Scope guard: read-only audit plus this assigned research file. No source, token, asset, screenshot, or client files were edited.

Claim labels used below: `confirmed`, `probable`, `unknown`, `needs local run`, `blocked by missing access`, `deferred`.

## Executive Summary

POKROV has the right strategic design direction for Open Beta v4: calm, premium, white/mint/deep-green, app-first, and operationally honest. The current implementation is not yet release-coherent because the design truth is split across `shared/design-tokens.json`, local marketing CSS variables, webapp globals, hard-coded Flutter colors, and draft client `DESIGN.md` files. The platform root `DESIGN.md` and `shared/design-tokens.schema.json` are missing in this worktree, so there is no single enforceable design contract for web and Flutter.

The highest release risk is visible text integrity. Marketing and cabinet source currently contain mojibake in user-facing Russian copy. Cabinet downloads and loading states are affected, and marketing homepage copy is affected as well. That blocks meaningful visual signoff because screenshots cannot prove a polished public beta while labels are unreadable.

The second major risk is false visual evidence. Marketing still uses rendered product mockups, and the app/client shell includes English-first beta UI labels. Generated imagery may be useful for neutral illustrations and empty states, but implementation screenshots must come from real code and real states; generated images must never be treated as proof of app readiness, payment readiness, node status, or Android release safety.

## Evidence Table

| Label | Surface | Evidence | Finding | Severity |
| --- | --- | --- | --- | --- |
| confirmed | Platform docs | `docs/developer/work-orders/2026-04-open-beta-v4/00-orchestrator-context.md` | Findings must use the required labels above; Open Beta v4 must not claim public Android or `1.0.0` while P0 gates are blocked. | P0 |
| confirmed | Design truth | `shared/design-tokens.json` | Theme exists as `quiet-core-luminous-edge` with warm canvas, deep emerald, mint/sage, density bands, icons, motion, and accessibility fields. | P1 |
| confirmed | Design governance | root platform worktree | Platform root `DESIGN.md` is absent. The design release brief requires it. | P0 |
| confirmed | Token governance | `shared/` listing | `shared/design-tokens.schema.json` is absent. The WO acceptance requires it. | P1 |
| confirmed | Web token bridge | `marketing/src/app/layout.tsx`, `webapp/src/app/layout.tsx` | Both marketing and webapp inject `getDesignTokenCssVariables(...)`. | P1 |
| confirmed | Token drift | `marketing/src/app/globals.css`, `webapp/src/app/globals.css` | Both surfaces still carry local fallback token layers and hard-coded colors/radii. | P1 |
| confirmed | Client token drift | `POKROV-app/packages/app_shell/lib/app_shell.dart` | Flutter shell hard-codes `_SeedPalette` instead of consuming generated tokens from platform shared truth. | P1 |
| confirmed | Client docs | `POKROV-app/DESIGN.md`, `POKROV-app/docs/design/DESIGN.md` | Client design docs exist but are draft and defer token alignment until a generated Flutter export exists. | P1 |
| confirmed | Brand assets | `shared/design-tokens.json`, `logo/logoclear.svg`, `logo/pokrov-wordmark.svg`, `external/logogo.png` | Approved masters are declared; legacy subtitle wordmark is blocked for public use. | P0 |
| confirmed | Web public assets | `marketing/public/favicon.ico`, `apple-icon.png`, `opengraph-image.png`, `twitter-image.png` | Derived assets exist, but this pass did not decode them visually, so subtitle-free derivation is unproven. | P1 |
| confirmed | Public copy integrity | `marketing/src/components/home/homepage.tsx` | Homepage contains mojibake in visible Russian strings. | P0 |
| confirmed | Cabinet copy integrity | `webapp/src/components/cabinet-downloads-page.tsx`, `webapp/src/app/loading.tsx` | Downloads and loading copy contain visible mojibake. | P0 |
| confirmed | Admin copy integrity | `webapp/src/app/(admin)/admin/network/page.tsx` | Admin network page includes mojibake; operator-only but still a visual QA and credibility issue. | P1 |
| confirmed | Product scope | Canonical docs and client cutover docs | Public target remains Android + Windows; Apple is readiness-only. Android public release is blocked pending physical audit and signing. | P0 |
| confirmed | Client visual language | `POKROV-app/packages/app_shell/lib/app_shell.dart` | App shell is English-first (`Protection`, `Locations`, `Rules`, `Profile`, `One tap`, `Protected`) while consumer beta copy is Russian-first. | P1 |
| probable | Icon system | `webapp` package and globals | Webapp mixes `lucide-react` with Material Symbols; marketing has no icon library and relies on custom visuals/CSS. | P1 |
| confirmed | Motion | `webapp/src/components/route-transition.tsx`, `webapp/src/app/globals.css` | Reduced motion exists in webapp. Marketing uses `prefers-reduced-motion: no-preference`, but homepage module still has `min-height: 100vh`. | P1 |
| confirmed | Responsive risk | `marketing/src/components/home/homepage.module.css` | Homepage `.page` uses `min-height: 100vh`; mobile browser viewport stability should use `100dvh` or content-driven min-height. | P2 |
| confirmed | QA overlay | `webapp/src/app/layout.tsx`, `webapp/src/app/qa-overlay.tsx` | QA overlay is env-gated by `NEXT_PUBLIC_ENABLE_QA_OVERLAY === "true"` and must be proven off in production screenshots. | P0 |
| blocked by missing access | Search tooling | local shell | `rg.exe` fails with `Access is denied`; audit used PowerShell enumeration and `Select-String`. | P2 |

## P0 Issues

1. confirmed: Platform root `DESIGN.md` is missing even though Open Beta v4 design truth requires it. Without it, web and Flutter implementers have no single canonical design contract.
2. confirmed: Visible mojibake exists in public/cabinet copy, including `marketing/src/components/home/homepage.tsx`, `webapp/src/components/cabinet-downloads-page.tsx`, and `webapp/src/app/loading.tsx`. This blocks public visual signoff.
3. confirmed: The release wording and visual system must keep Android public-blocked and Windows unsigned-gated status visible where app downloads are offered. Cabinet download cards need parity with marketing install/offer disclaimers before screenshots can be trusted.
4. confirmed: Legacy subtitle/wordmark usage must remain blocked. `logo/logowithtext.svg` may exist as retained reference only; release-facing favicon, social preview, launcher, splash, tray, and installer assets must be proven derived from subtitle-free masters.
5. confirmed: Production screenshots must prove the QA overlay and local/dev affordances are not visible.

## P1 Issues

1. confirmed: `shared/design-tokens.schema.json` is missing, so token shape is not enforceable.
2. confirmed: Marketing and webapp use shared token injection but also keep local token/fallback layers, making drift likely.
3. confirmed: Flutter uses hard-coded palette/radius/motion values rather than a generated token export.
4. probable: Icon policy is not unified. Webapp uses both Lucide and Material Symbols; marketing mostly uses custom CSS shapes; Flutter uses Material icons.
5. confirmed: Client shell is English-first and should either become Russian-first for consumer beta screenshots or get a documented beta exception.
6. unknown: Derived web and client raster assets were not visually decoded in this pass, so stale subtitle or old mark residue is unproven.

## P2 Issues

1. confirmed: Some web surfaces still use `100vh`/`min-h-screen`; migrate primary shell/hero surfaces to `100dvh` or content-driven layouts where mobile browser stability matters.
2. deferred: Exact source-layer recovery from any old design archives is not required unless implementation needs pixel-level recreation.
3. deferred: Full dark-mode refinement can wait if beta does not expose a public dark-mode toggle, but status colors and contrast still need AA verification.

## Desired Visual System

POKROV should read as quiet, direct, and premium: warm off-white canvas, white/surface panels, deep emerald primary action, mint/sage support surfaces, restrained muted gold only as secondary warmth, and status colors only for semantic feedback. Marketing can be more spacious and image-led; cabinet should be continuation-first and task-oriented; admin should be dense, scan-first, and low-drama; app should center one large connect affordance with `Protection / Locations / Rules / Profile`.

Avoid direct public `VPN` wording, raw transport badges, fake operational counters, network jargon in first-layer consumer UI, decorative dashboards that look like live proof, purple/blue AI gradients, heavy glass, nested cards, and generated screenshots masquerading as evidence.

## Token Proposal

Keep `shared/design-tokens.json` as the canonical source and add a schema plus generated web/Flutter outputs.

Required additions:

```json
{
  "theme": {
    "version": "2026-04-open-beta-v4",
    "breakpoints": {
      "xs": "320px",
      "sm": "360px",
      "md": "390px",
      "tablet": "768px",
      "desktop": "1180px",
      "wide": "1440px"
    },
    "zIndex": {
      "base": "0",
      "sticky": "20",
      "overlay": "40",
      "modal": "60",
      "qa": "80"
    },
    "state": {
      "beta": { "bg": "#f7efd9", "text": "#765d23" },
      "blocked": { "bg": "#f8e7e3", "text": "#8d352e" },
      "unsigned": { "bg": "#f7efd9", "text": "#765d23" },
      "soon": { "bg": "#e7eef2", "text": "#315c70" }
    },
    "focus": {
      "ring": "0 0 0 3px rgba(32, 103, 79, 0.22)",
      "outline": "2px solid #20674f"
    }
  },
  "asset": {
    "forbiddenPublicSources": ["logo/logowithtext.svg"],
    "requiredDerivatives": ["favicon", "apple-icon", "opengraph", "twitter", "android-launcher", "windows-ico", "tray", "splash"]
  }
}
```

Generated outputs:

- Web: keep `shared/design-tokens.ts` and emit CSS variables for `public`, `cabinet`, `admin`, and `product`.
- Flutter: generate `packages/app_shell/lib/design/pokrov_tokens.dart` with `Color`, `BorderRadius`, spacing, duration, and text constants.
- Docs: root `DESIGN.md` becomes canonical; `POKROV-app/DESIGN.md` mirrors client-specific implementation rules and links back to root token truth.

## Component Inventory

Marketing:

- Homepage shell, hero, proof strip, how-it-works steps, surface cards, pricing cards, final CTA.
- Install/help pages, offer/legal pages, checkout entry route, SEO landings.
- Required shared components: `BrandHeader`, `PrimaryCta`, `SecondaryCta`, `BetaAvailabilityNotice`, `ProductIllustration`, `PlanCard`, `SupportLinkBand`, `FooterLegal`.

Cabinet:

- Cabinet shell/sidebar/mobile nav, dashboard summary, subscription/checkout continuation, devices, downloads, statistics, support/ticket thread, redeem, loading/not-found/error states.
- Required shared components: `CabinetPageHeader`, `ActionList`, `AvailabilityCard`, `StatusBadge`, `EmptyState`, `InlineWarning`, `SupportTicketComposer`, `DeviceSummary`.

Admin:

- Admin shell, dashboard, users, payments, tickets, network rollout, nodes, bonuses, broadcast, promos, referrals.
- Required shared components: `AdminTable`, `AdminFilterBar`, `AdminMetricStrip`, `AdminStatusBadge`, `AdminJsonEditor`, `AdminDrawer`, `AdminEmptyState`, `AdminErrorPanel`.

Client:

- Protection connect surface, location list, route-mode picker, profile hub, subscription/devices/support/settings, warning/blocked panels, runtime loading/error states.
- Required shared components: `ConnectControl`, `RouteModeCard`, `LocationCard`, `ProfileHubTile`, `BetaStatusBanner`, `SupportEntry`, `RuntimeErrorPanel`.

## Responsive Breakpoints

Use these as verification, not merely CSS names:

- `320px`: smallest supported Android/WebView width; no horizontal overflow, CTA text wraps cleanly.
- `360px`: common Android small phone; connect affordance and bottom nav must fit.
- `390px`: common modern phone; Telegram WebView-safe height check.
- `430px`: large phone; no extra hero whitespace or clipped card grids.
- `768px`: tablet/small desktop transition; navigation should not become cramped.
- `1180px`: desktop baseline for marketing/cabinet/admin.
- `1440px`: wide desktop release screenshot baseline.
- `1536px`: reference-pack comparison width.

CSS rule: public and cabinet layouts may be asymmetric at desktop, but must collapse to one column below `768px`. Avoid `h-screen`; use `min-height: 100dvh`, `min-height: var(--tg-viewport-height, 100dvh)`, or content-driven section sizing.

## Motion Rules

- Use motion only for state change, route transition, loading skeletons, and tactile press feedback.
- Default durations: fast `120ms`, base `180ms`, slow `280ms`.
- Easing: `cubic-bezier(0.2, 0.7, 0.2, 1)`.
- Animate only `transform` and `opacity`; avoid layout property animation.
- Reduced motion must remove route movement, shimmer loops, pulsing status dots, and decorative motion.
- Marketing image/illustration motion must be `prefers-reduced-motion: no-preference`.
- Admin motion should be nearly static: hover/active only, plus explicit loading indicators.
- Generated video/animated art is not release evidence and must not be used in verification screenshots.

## Accessibility Checklist

- WCAG AA contrast for body text, CTAs, status badges, and disabled states.
- Minimum touch target `44px` for mobile buttons, nav, checkboxes, segmented controls, and app bottom tabs.
- Visible focus ring from token source on every interactive control.
- Keyboard path through marketing CTAs, cabinet auth, downloads, support tickets, admin filters, tables, modals, and JSON editor.
- Skip link present and visible on focus for web surfaces.
- No text overlap or clipping at `320`, `360`, `390`, `430`, `768`, `1180`, and `1440`.
- Motion disabled or reduced under `prefers-reduced-motion`.
- Screen-reader labels for icon-only buttons; icons are decorative only when adjacent text already labels the action.
- Status must not be color-only; include text labels such as `blocked`, `unsigned beta`, `soon`, `stale`, `missing`.
- No screenshots or prompts may include secrets, QR payloads, raw configs, personal connection links, payment IDs, full Telegram IDs, or private node topology.

## Image Generation Prompt Pack

Use image tools for brand-safe illustration assets only. Do not generate logos, UI proof, QR codes, app screenshots, node maps, payment proof, or operational dashboards.

Prompt 1 - public hero illustration:

```text
Create a premium calm product illustration for POKROV, a consumer connectivity app. Warm off-white canvas, deep emerald and soft mint, subtle white surfaces, one abstract circular connect affordance, Android phone and Windows laptop silhouettes without readable UI text, no VPN wording, no protocol labels, no fake counters, no maps with real locations, no QR codes. 16:9, clean editorial lighting, high trust, restrained motion feel.
```

Prompt 2 - cabinet empty state:

```text
Create a small empty-state illustration for a user cabinet downloads/support panel. White and mint surfaces, deep emerald accent, simple device outlines, calm premium style, no readable text, no logos except abstract shield-like mark, no QR codes, no personal data, no network nodes. Transparent or off-white background, 4:3.
```

Prompt 3 - support illustration:

```text
Create a quiet support illustration for POKROV: abstract chat cards, device context, safe diagnostic checklist, warm off-white background, emerald and sage accents, no real usernames, no Telegram IDs, no payment data, no network topology, no VPN wording, no fake live status. 1:1.
```

Prompt 4 - social preview background:

```text
Create an Open Graph background for POKROV. Warm off-white, deep emerald mark area, soft mint edge lighting, premium calm technology feel, no text rendered in the image, no VPN wording, no device screenshots, no counters. Leave safe negative space for code-rendered wordmark and headline. 1200x630.
```

Generate with image tools:

- Neutral hero backgrounds and product illustrations.
- Empty-state illustrations.
- Social preview background art with text rendered by code.
- Non-proof decorative app/device silhouettes.

Generate with code:

- Logos, wordmarks, favicon/manifest derivatives from approved masters.
- Real UI components, icons for actions, status badges, charts, tables, QR rendering, and screenshots.
- Before/after visual evidence from Playwright/Flutter/device runs.

## Before/After Screenshot Plan

Do not store generated proof in this research file. Implementation owners should capture redacted before/after screenshots after fixing P0 copy and token issues.

Marketing:

- `/` at `390x844`, `430x932`, `1440x1000`, `1536x1024`.
- `/checkout/`, `/install/`, `/offer/` at `390x844` and `1440x1000`.
- Check: POKROV first viewport signal, no mojibake, no direct public `VPN`, no fake live proof, CTA priority checkout-first, text fit.

Cabinet:

- Entry, dashboard, subscription, downloads, devices, support, redeem at `360x800`, `390x844`, `1180x900`, `1440x1000`.
- Check: continuation-first tone, no mojibake, Android/Windows status clarity, no raw links/configs in first-layer UI, no QA overlay.

Admin:

- Dashboard, users, payments, tickets, network, nodes at `390x844`, `1180x900`, `1440x1000`.
- Check: dense scan-first layout, no mojibake in operator copy, table overflow handling, missing/stale/failed status distinctions, keyboard focus.

Client:

- Android: Protection, Locations, Rules, Profile, support, subscription, route-mode choice, loading/error at small and common phone sizes.
- Windows: compact window, wide window, Protection, Rules, Profile/support, beta unsigned notice.
- Check: one-tap affordance, Russian-first or documented exception, no raw config/topology, no Hiddify visible residue, no direct public `VPN` wording except OS permission/technical compatibility contexts.

## Proposed Implementation Work

1. Create platform root `DESIGN.md` as the canonical Open Beta v4 design system, then sync `POKROV-app/DESIGN.md` and `POKROV-app/docs/design/DESIGN.md` to it.
2. Add `shared/design-tokens.schema.json` and validate `shared/design-tokens.json` against it.
3. Generate Flutter token output from `shared/design-tokens.json` and replace `_SeedPalette` hard-coded constants with generated constants.
4. Collapse marketing and webapp local CSS token fallbacks into the shared token variables or document intentional local aliases.
5. Fix mojibake in public/cabinet/admin visible strings before any screenshot signoff.
6. Normalize download availability notices across marketing and cabinet: Android internal/public-blocked until signing plus physical audit; Windows unsigned-gated until trusted signing.
7. Inventory and regenerate derived brand assets from subtitle-free masters; explicitly ban `logo/logowithtext.svg` imports in public/cabinet/client code.
8. Define icon policy by surface: marketing minimal custom/product graphics, cabinet/admin Lucide for actions, Flutter Material icons for app until a custom icon package exists.
9. Replace or label public mock visuals so they cannot be mistaken for live operational proof.
10. Add screenshot and visual smoke gates for the before/after plan above.

## Exact Verification Commands

Platform root:

```powershell
Set-Location C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4
Test-Path .\DESIGN.md
Test-Path .\shared\design-tokens.schema.json
python scripts\client_security_smoke.py
python scripts\run_client_release_gate.py preflight
python scripts\run_client_release_gate.py test --suite portal
python scripts\check-links.py
python scripts\ui_visual_smoke.py
```

Design lint after root `DESIGN.md` exists:

```powershell
Set-Location C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4
npx --yes @google/design.md lint DESIGN.md
```

Marketing:

```powershell
Set-Location C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4\marketing
npm.cmd run check:seo
npm.cmd run build
```

Webapp:

```powershell
Set-Location C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4\webapp
npm.cmd run build
npm.cmd run test:e2e
npm.cmd run test:e2e:admin
```

Client:

```powershell
Set-Location C:\Users\kiwun\.config\superpowers\worktrees\POKROV-app\open-beta-v4
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1
flutter test packages\app_shell
flutter test apps\android_shell
flutter test apps\windows_shell
```

Screenshot gate commands should be added by implementation owners once the screenshot harness paths are finalized. Any Android public-release evidence still requires the separate physical-device localhost/control-surface audit and must not be inferred from visual QA.

## Remaining Risk

This pass did not run browser builds, Playwright, Flutter tests, screenshot capture, image decoding, or asset regeneration. Findings are based on source/docs inspection only. Because the assigned output is research-only, all P0/P1 fixes remain open for implementation work orders.
