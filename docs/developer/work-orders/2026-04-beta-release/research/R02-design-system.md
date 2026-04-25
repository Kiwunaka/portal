# R02 Design System

Status: research complete - implementation work orders required

Last researched: 2026-04-25

Scope guard: read-only research. Only this file was edited. Secret paths were not opened or printed.

Claim labels used below: `confirmed`, `probable`, `unknown`, `needs local run`, `blocked by missing access`.

## Scope

Design system, brand assets, visual audit, attached refs, token acceptance spec.

Attached/reference visuals override the current token file when they conflict. Visible `Premium VPN` / direct `VPN` wording in logo and UI refs is legacy/reference material only and is not allowed as new public copy.

## Files/docs inspected

- confirmed: Canonical root docs were read in required order: `docs/README.md`, `docs/product/portal-vpn-product.md`, `docs/architecture/system-overview.md`, `docs/architecture/app-first-and-bonus-flows.md`, `docs/operations/deployment-and-access.md`, `docs/operations/monitoring-and-visibility.md`, `docs/developer/developer-guide.md`, `docs/developer/repository-map.md`.
- confirmed: Active client docs were read: `C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md`, `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md`, `docs/operations/publishing-and-signing-guide.md`.
- confirmed: Design-token and brand files inspected: `shared/design-tokens.json`, `shared/design-tokens.ts`, `logo/logoclear.svg`, `logo/logowithtext.svg`, `external/logogo.png`, `C:/Users/kiwun/Documents/ai/POKROV-app/assets/branding/pokrov-mark.png`, `C:/Users/kiwun/Documents/ai/POKROV-app/assets/branding/README.md`.
- confirmed: Reference folder inspected: `ПРИМЕРЫ ДИЗАЙНА ПРИЛОЖЕНИЯ И ЛК/` including `вебапп/`, `лендинг/`, `приложение/`, PNG dimensions, and `.7z` presence.
- confirmed: Marketing UI inspected under `marketing/src/**`, including `marketing/src/app/layout.tsx`, `marketing/src/app/globals.css`, `marketing/src/components/home/homepage.tsx`, `marketing/src/components/home/homepage.module.css`, `marketing/src/components/marketing-landing.tsx`, and route pages.
- confirmed: Cabinet/admin UI inspected under `webapp/src/**`, including `webapp/src/app/layout.tsx`, `webapp/src/app/globals.css`, `webapp/src/app/pokrov-logo.tsx`, `webapp/src/app/branding.ts`, `webapp/src/components/**`, and dashboard/admin routes.
- confirmed: Active client UI inspected under `C:/Users/kiwun/Documents/ai/POKROV-app`, especially `packages/app_shell/lib/app_shell.dart`, branding assets, package metadata, and platform resource references.
- blocked by missing access: `rg` could not run in this shell session with `Access is denied`; PowerShell `Get-ChildItem` / `Select-String` searches were used instead.

## Current state

- confirmed: Public brand/product canon is `POKROV`; `POKROV VPN` and direct `VPN` product wording are legacy-only exceptions, not a public product description.
- confirmed: `shared/design-tokens.json` defines the current shared theme `pokrov-calm-premium` with warm canvas, white translucent surfaces, deep emerald accents, muted gold support color, soft shadows, and large card/panel radii.
- confirmed: `shared/design-tokens.ts` exposes the JSON theme as CSS variables for `public`, `cabinet`, `admin`, and `product` density contexts.
- confirmed: `marketing/src/app/layout.tsx` and `webapp/src/app/layout.tsx` consume shared token CSS variables, so both web surfaces have a shared-token entrypoint.
- probable: Marketing and webapp still have duplicated hard-coded CSS token layers in their global CSS. This can drift from `shared/design-tokens.json` even though the layout entrypoints import the shared variables.
- confirmed: `POKROV-app/packages/app_shell/lib/app_shell.dart` uses a hard-coded Flutter palette rather than importing or generating from `shared/design-tokens.json`.
- confirmed: Reference PNGs show a coherent target direction: off-white/warm canvas, deep emerald navigation and CTAs, soft mint/sage cards, low-contrast dividers, rounded app controls, quiet dense cabinet/admin tables, and minimal decorative noise.
- confirmed: Reference PNGs also include legacy/publicly unsafe text such as `PREMIUM VPN`, app labels including direct `VPN`, raw protocol terms, and technical controls. These refs are visual direction only, not copy approval.
- needs local run: Browser and Flutter screenshots are still required to prove the implemented surfaces match the refs at current runtime sizes.

## Token / Acceptance Spec

### Palette

- acceptance: Base canvas should stay in the warm off-white family close to `#f7f3eb` / `#f4f0e7`; avoid beige-heavy or monochrome tan pages.
- acceptance: Primary action and brand accent should be deep emerald close to `#20674f` / `#1b5a45`; darker emerald is acceptable for sidebars, bottom nav, and active chrome.
- acceptance: Support colors should be soft mint/sage and restrained muted gold; blue, violet, rose, amber, and red should be reserved for status, charts, alerts, or admin semantics.
- acceptance: Text should stay near deep ink `#1f2636` / `#12261b`; secondary copy should be muted but readable.
- acceptance: Public, cabinet, admin, Android, and Windows surfaces should expose the same named design decisions even if implementation-specific token formats differ.

### Surfaces, Radius, And Density

- acceptance: Marketing pages can use broader visual rhythm, but the first screen must show the real POKROV product/brand and hint at the next section.
- acceptance: Cabinet and admin should be dense, scan-first, and operational. They should not feel like marketing hero pages.
- acceptance: Avoid nested card stacks and arbitrary floating cards. Use cards for repeated items, modals, and genuinely framed tools.
- acceptance: Keep stable dimensions for nav items, icon buttons, tiles, status counters, device mocks, tables, and app controls so hover/loading states do not shift layout.
- acceptance: Use controlled radius tokens by surface. The app connect affordance can remain circular/ref-like; dense web/admin cards should avoid uncontrolled oversized rounding.

### Typography

- acceptance: Manrope or an equivalent geometric sans is the web default; monospace should be reserved for machine values, keys, IDs, and operator diagnostics.
- acceptance: Do not rely on negative letter spacing in compact UI. Text should fit buttons, pills, sidebar items, and mobile nav without overlap.
- acceptance: Russian copy is first-class for consumer/cabinet beta surfaces; English technical labels are acceptable only in operator-only contexts where they are deliberate.

### Motion

- acceptance: Motion should be subtle: fade, small lift, and state transitions. No distracting decorative background movement.
- acceptance: Reduced-motion mode should degrade to fade-only or static state changes.

### Icons

- acceptance: Pick one icon policy per surface. Web buttons should use the chosen icon library consistently, preferably `lucide-react` where available.
- acceptance: Custom SVGs are acceptable for the POKROV mark and unavoidable product graphics, not for common actions that already have library icons.
- acceptance: App icons may remain Flutter Material icons if the app shell standardizes on them, but the style should match the reference line-weight and calm visual language.

### Copy And Data

- acceptance: Public and first-layer product UI must not use `VPN` as direct product description. Allowed exceptions are legacy names, compatibility labels, unavoidable technical identifiers, and operator diagnostics.
- acceptance: Public and first-layer consumer UI must not expose raw protocol/security claims such as `WireGuard`, `AES-256`, `Kill Switch`, `Hiddify`, or fallback engine names as decorative trust badges.
- acceptance: `Premium VPN` subtitle from refs/logos is legacy reference only. Public wordmarks must be subtitle-free unless a separately approved non-`VPN` descriptor is created.
- acceptance: Marketing/device/dashboard mockups must not show fake live operational data, false statuses, sample user identities, or unsupported capabilities. Illustrations must be policy-safe and visibly product-relevant.
- acceptance: Dev/local labels must not appear in production public, cabinet, or paid beta screenshots.

## Logo findings

- confirmed: `external/logogo.png` is a 2048x2048 raster master with the POKROV mark.
- confirmed: `logo/logoclear.svg` is a 200x200 vector mark with deep emerald gradient stops and no visible text.
- confirmed: `logo/logowithtext.svg` is a 200x200 vector logo containing the POKROV wordmark plus a visible subtitle rendered as paths. The subtitle reads as legacy `PREMIUM VPN` in the reference set.
- confirmed: `C:/Users/kiwun/Documents/ai/POKROV-app/assets/branding/pokrov-mark.png` is a 1024x1024 active client branding asset derived from the mark.
- confirmed: `C:/Users/kiwun/Documents/ai/POKROV-app/assets/branding/README.md` identifies `pokrov-mark.png` as the client source asset and lists the root raster/vector files as upstream references.
- P0 blocker: Any public/cabinet/app use of the `logowithtext.svg` subtitle variant would ship forbidden direct `VPN` copy. Use mark-only or subtitle-free wordmark exports for beta.
- P1 polish: Regenerate and inventory favicon, app icon, splash, tray, store, social preview, and web manifest assets from the approved subtitle-free mark/wordmark before release.

## Reference pack inventory

- confirmed: `ПРИМЕРЫ ДИЗАЙНА ПРИЛОЖЕНИЯ И ЛК/вебапп/` contains 6 PNG refs, each 1536x1024, covering main cabinet, tariff, devices, support, and admin views.
- confirmed: `ПРИМЕРЫ ДИЗАЙНА ПРИЛОЖЕНИЯ И ЛК/лендинг/` contains 10 PNG refs, split across 1536x1024 and 1448x1086 landing compositions.
- confirmed: `ПРИМЕРЫ ДИЗАЙНА ПРИЛОЖЕНИЯ И ЛК/приложение/` contains 20 PNG refs across mobile and desktop-ish app aspect ratios.
- confirmed: `ПРИМЕРЫ ДИЗАЙНА ПРИЛОЖЕНИЯ И ЛК/лендинг.7z` and `ПРИМЕРЫ ДИЗАЙНА ПРИЛОЖЕНИЯ И ЛК/приложение.7z` are present.
- unknown: The `.7z` archives were not unpacked during this read-only pass, so their internal file lists and any additional source layers remain unknown.

## Old colors/icons/fake dashboards/dev labels/old subtitle findings

- confirmed: The logo/reference subtitle `PREMIUM VPN` is legacy/reference only and must not be used as beta public copy.
- confirmed: App refs include visual labels such as direct `VPN`, `WireGuard`, `Kill Switch`, and `Premium`; these should be treated as layout/style references, not final copy.
- confirmed: `marketing/src/components/home/homepage.tsx` contains a visible hero mock metric with `AES-256 / WireGuard`. This is public-facing protocol/security copy and should be removed or replaced before paid beta.
- confirmed: `marketing/src/components/home/homepage.tsx` uses rendered device/dashboard mock UI. This can remain only if it is clearly illustrative, policy-safe, and does not imply unsupported live state.
- confirmed: `marketing/src/components/marketing-landing.tsx` contains older mixed English/internal labels such as device/trial/free-cycle phrasing. This component should be audited before any route uses it for beta traffic.
- confirmed: `webapp/src/app/(dashboard)/subscription/checkout/page.tsx` contains user-visible English/dev-like labels including `Preview discount`, `Free fallback`, `activation key`, and `redeem` in otherwise Russian flows.
- confirmed: Local/admin development entry screens include development wording such as local login. This is acceptable only when gated to local/dev environments.
- confirmed: `webapp/src/app/layout.tsx` includes a QA overlay switch controlled by `NEXT_PUBLIC_ENABLE_QA_OVERLAY`. Production must verify this flag is off.
- confirmed: `webapp/src/app/globals.css` includes status icon color classes such as violet, blue, amber, and rose. These are acceptable only as semantic status colors and should not become the dominant theme.
- probable: Current web icon usage mixes Material Symbols for shell/nav and `lucide-react` in admin routes. This is a visual-consistency risk unless intentionally documented by surface.
- confirmed: `POKROV-app/packages/app_shell/lib/app_shell.dart` currently presents app shell strings in English while the beta refs and public product lane are Russian-first.
- probable: Active client runtime/package references still include Hiddify-related internal names in some runtime resources. They may be compatibility-only, but they are a release identity risk if surfaced in binaries, windows, process names, logs, or crash reports.

## Component inventory

### Marketing

- confirmed: Route/app primitives live in `marketing/src/app/**`, including home, checkout, install, mobile, offer, privacy, Telegram, TikTok, YouTube, manifest, robots, and sitemap surfaces.
- confirmed: Main visual homepage lives in `marketing/src/components/home/homepage.tsx` with CSS module styling in `homepage.module.css`.
- confirmed: Older/general landing component lives in `marketing/src/components/marketing-landing.tsx`.
- confirmed: Structured data helper lives in `marketing/src/components/json-ld.tsx`.
- confirmed: Marketing package uses animated/custom visual systems but does not currently depend on `lucide-react`.

### Webapp Cabinet/Admin

- confirmed: Shell and shared primitives live in `webapp/src/components/cabinet-shell.tsx`, `cabinet-primitives.tsx`, `shell-primitives.tsx`, `cabinet-page.tsx`, `route-transition.tsx`, and `pokrov-mark.tsx`.
- confirmed: User routes include dashboard, subscription, checkout, devices, downloads, statistics, support, support legal/thread, profile, and redeem.
- confirmed: Admin routes include dashboard, users, tickets, network, nodes, bonuses, broadcast, promos, and referrals.
- confirmed: Admin component inventory includes `admin-shell` and users subcomponents for history, key policy editor, overview, side panel, formatting, query panel/state, and results table.
- confirmed: Webapp package depends on `lucide-react` and also loads Google Material Symbols.

### Active Client

- confirmed: Main app shell prototype lives in `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/lib/app_shell.dart`.
- confirmed: Active client top-level IA matches the documented direction: Protection, Locations, Rules, Profile.
- confirmed: Active client branding asset lives at `C:/Users/kiwun/Documents/ai/POKROV-app/assets/branding/pokrov-mark.png`.
- probable: Android/Windows package, icon, splash, and runtime identity still need a release-brand audit beyond the visual pass.

## Gaps against beta

- P0: Public/cabinet/app visuals must remove direct `VPN` product wording and the legacy `Premium VPN` subtitle before paid beta.
- P0: Public marketing must remove raw protocol/security trust badges from first-layer visuals, especially `AES-256 / WireGuard`.
- P0: Paid beta user-facing cabinet checkout copy must be localized and de-dev-labeled.
- P0: Active client shell needs Russian-first consumer copy or a documented beta exception before public release screenshots.
- P0: Production must prove local/dev login labels and QA overlay cannot appear on public/cabinet beta surfaces.
- P1: Token sources need consolidation so shared web tokens and Flutter/app tokens do not drift.
- P1: Icon-family policy needs cleanup across marketing, cabinet, admin, and app.
- P1: Mock dashboards/device visuals need either real data binding, neutral illustrative treatment, or replacement with approved product screenshots.
- P2: Archive `.7z` internals can remain unopened unless source-layer recovery or exact visual reproduction becomes necessary.

## P0 blockers

- confirmed: `Premium VPN` subtitle appears in brand refs/logo material; shipping it publicly violates the public wording rule.
- confirmed: `marketing/src/components/home/homepage.tsx` exposes `AES-256 / WireGuard` in a public visual.
- confirmed: `webapp/src/app/(dashboard)/subscription/checkout/page.tsx` includes user-visible English/dev-like labels that are not beta-ready.
- confirmed: `POKROV-app/packages/app_shell/lib/app_shell.dart` is English-first in the visible app shell while beta refs/product lane are Russian-first.
- needs local run: Production builds/screenshots must confirm QA overlay and local development login surfaces are not reachable in public/cabinet beta.

## P1 beta polish

- probable: Consolidate duplicated CSS variables in marketing/webapp around the shared token contract.
- probable: Generate client/web token artifacts from one source or document deliberate per-platform differences.
- probable: Normalize icon families and line weights by surface.
- probable: Replace fake device/dashboard visuals with approved screenshots or policy-safe illustrative states.
- probable: Regenerate all derived brand assets from subtitle-free logo masters.
- probable: Audit hard-coded old color classes, especially violet/blue/rose/amber, so they remain semantic only.

## P2 defer

- unknown: `.7z` contents may contain editable source layers. They can wait unless implementation needs exact layer extraction.
- probable: Full dark-mode refinement can defer if paid beta does not expose dark mode, but status colors and contrast still need verification.
- probable: Marketing animation refinements can defer after copy/brand blockers are cleared.

## Technical debt

- confirmed: `shared/design-tokens.json` is a source of truth for web variables, but marketing/webapp global CSS still carries local token definitions.
- confirmed: Active client palette is hard-coded in Flutter rather than derived from the shared tokens.
- probable: Current token names do not fully cover beta needs such as semantic statuses, plan badges, admin table density, app connect state, and release identity assets.
- probable: Mixed Material Symbols, Lucide, inline SVGs, and Flutter Material icons will make visual QA harder unless each surface has an explicit icon rule.
- probable: Runtime/legacy technical identifiers may be harmless internally, but they need a separate release identity gate to prevent accidental public surfacing.

## Security/privacy risks

- confirmed: Rendered fake dashboards, sample users, sample IP-like values, or artificial device states must not ship as production data surfaces.
- confirmed: Dev/local login labels and QA overlays must be gated away from production.
- probable: Branding/runtime residue from compatibility layers could leak through process names, logs, crash reports, or binary metadata if not audited.
- needs local run: Browser and client screenshots are needed to verify that no private operational values, debug labels, or local URLs appear in beta UI.

## Required implementation WOs

1. R02-WO1 Brand asset cleanup: create approved subtitle-free mark/wordmark exports; update favicon, manifest, splash, app launcher, tray, social preview, and store assets; ban `logowithtext.svg` subtitle variant from public use.
2. R02-WO2 Token consolidation: map `shared/design-tokens.json` into marketing/webapp CSS and active client token artifacts; remove duplicate drift-prone local values or document intentional overrides.
3. R02-WO3 Public copy scrub: remove direct `VPN`, `Premium VPN`, raw protocol/security labels, and English/dev labels from public/cabinet/app first-layer UI.
4. R02-WO4 Mock/data realism pass: replace fake dashboards/device panels with approved screenshots, neutral illustrations, or real API-backed states; include empty/loading/error states.
5. R02-WO5 Icon and component policy: define per-surface icon families, radii, density, button states, table states, modal states, and app navigation states.
6. R02-WO6 Visual QA gate: capture marketing, cabinet, admin, Android, and Windows screenshots at release breakpoints and compare against refs with copy/token acceptance checklist.

## Validation commands

- needs local run: `npm.cmd run build` in `marketing/`.
- needs local run: `npm.cmd run build` in `webapp/`.
- needs local run: `npm.cmd run test:e2e:admin` in `webapp/` if admin-visible surfaces are changed.
- needs local run: browser screenshot pass for marketing home, cabinet entry, checkout, dashboard, devices, support, admin dashboard, users, tickets, network, and nodes.
- needs local run: Flutter/widget or screenshot pass in `C:/Users/kiwun/Documents/ai/POKROV-app` for Protection, Locations, Rules, Profile, onboarding/activation, error, loading, and empty states.
- needs local run: production-env smoke confirming `NEXT_PUBLIC_ENABLE_QA_OVERLAY` is unset/false and local development login is not reachable.
- needs local run: brand/copy scan for forbidden first-layer strings: `Premium VPN`, direct public `VPN`, `WireGuard`, `AES-256`, `Kill Switch`, `Hiddify`, `Preview discount`, `Free fallback`.
- blocked by missing access: replace fallback PowerShell search with `rg` once the local `rg.exe` permission issue is fixed.

## Visual QA checklist

- confirmed: Use the PNG refs as visual acceptance direction, but reject their legacy/technical copy.
- needs local run: Desktop widths: 1440, 1536, and a wide desktop viewport for marketing/cabinet/admin.
- needs local run: Mobile widths: 360, 390, 430, and Telegram webview-safe height for public/cabinet flows.
- needs local run: Verify first viewport always shows POKROV brand/product signal and no forbidden direct `VPN` copy.
- needs local run: Verify text never overlaps, clips, or escapes buttons, pills, cards, tables, nav, modals, app bars, and bottom nav.
- needs local run: Verify real loading, empty, error, and offline states do not use fake sample users/dev labels.
- needs local run: Verify status colors remain semantic and do not dominate the palette.
- needs local run: Verify focus rings, keyboard nav, contrast, and reduced motion.
- needs local run: Verify image assets render crisply on high-DPI desktop and Android devices.
- needs local run: Verify production screenshots do not expose localhost, test tokens, QA overlays, internal hostnames, or operator-only debug values.

## Evidence links

- confirmed: `C:/Users/kiwun/Documents/ai/VPN/shared/design-tokens.json`
- confirmed: `C:/Users/kiwun/Documents/ai/VPN/shared/design-tokens.ts`
- confirmed: `C:/Users/kiwun/Documents/ai/VPN/logo/logoclear.svg`
- confirmed: `C:/Users/kiwun/Documents/ai/VPN/logo/logowithtext.svg`
- confirmed: `C:/Users/kiwun/Documents/ai/VPN/external/logogo.png`
- confirmed: `C:/Users/kiwun/Documents/ai/VPN/ПРИМЕРЫ ДИЗАЙНА ПРИЛОЖЕНИЯ И ЛК/`
- confirmed: `C:/Users/kiwun/Documents/ai/VPN/marketing/src/components/home/homepage.tsx`
- confirmed: `C:/Users/kiwun/Documents/ai/VPN/marketing/src/components/marketing-landing.tsx`
- confirmed: `C:/Users/kiwun/Documents/ai/VPN/webapp/src/app/(dashboard)/subscription/checkout/page.tsx`
- confirmed: `C:/Users/kiwun/Documents/ai/VPN/webapp/src/app/layout.tsx`
- confirmed: `C:/Users/kiwun/Documents/ai/VPN/webapp/src/app/globals.css`
- confirmed: `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/lib/app_shell.dart`
- confirmed: `C:/Users/kiwun/Documents/ai/POKROV-app/assets/branding/README.md`
