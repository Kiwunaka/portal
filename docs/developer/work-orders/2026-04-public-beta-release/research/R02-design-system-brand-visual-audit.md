# R02 Design System Brand Visual Audit

Status: research complete - implementation owners required

Last researched: 2026-04-25

Scope guard: read-only audit plus this assigned research file. I did not edit product, source, token, or evidence files. No secrets were opened or copied.

Claim labels used below: `confirmed`, `probable`, `unknown`, `needs local run`, `blocked by missing access`.

## Scope

Design system, brand, and visual readiness for the public beta release wave, focused on:

- public beta visual parity across marketing and webapp
- forbidden direct `VPN` wording
- fake claims, fake counters, fake live status, and decorative operational claims
- Android / Windows / Apple availability copy
- required visual and browser evidence before signoff

Inherited evidence consulted only from `docs/developer/work-orders/2026-04-beta-release`: prior `R02-design-system.md`, `WO-001-design-system-brand-assets.md`, `WO-001-design-system-brand-assets` work order, and the release gate plan.

## What I Checked

- confirmed: Canonical root docs were read in the required order: `docs/README.md`, `docs/product/portal-vpn-product.md`, `docs/architecture/system-overview.md`, `docs/architecture/app-first-and-bonus-flows.md`, `docs/operations/deployment-and-access.md`, `docs/operations/monitoring-and-visibility.md`, `docs/developer/developer-guide.md`, and `docs/developer/repository-map.md`.
- confirmed: Active client/public release docs were read: `C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md`, `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md`, and `docs/operations/publishing-and-signing-guide.md`.
- confirmed: Shared public governance inspected: `shared/design-tokens.json`, `shared/design-tokens.ts`, `shared/copy.ts`, `shared/product-facts.json`, `shared/public-urls.json`, and `copy/catalog.ru.json`.
- confirmed: Marketing surfaces inspected under `marketing/src`, especially layout, homepage, install, offer, route pages, metadata helpers, and public assets.
- confirmed: Webapp surfaces inspected under `webapp/src`, especially layout, loading, cabinet downloads, subscription checkout, QA overlay, admin network, and shared logo/mark components.
- confirmed: Brand assets inspected: `logo/logoclear.svg`, `logo/logowithtext.svg`, `logo/pokrov-wordmark.svg`, `marketing/public/pokrov-logo.svg`, and `webapp/src/app/icon.svg`.
- confirmed: `git status --short` shows many pre-existing dirty/untracked files in the shared worktree. I did not revert or modify them.
- blocked by missing access: `rg.exe` still fails with `Access is denied`, so searches used PowerShell `Get-ChildItem` / `Select-String`.

## Canonical Constraints

- confirmed: Public brand/product name is `POKROV`; direct public `VPN` product wording is forbidden except legacy identifiers, compatibility labels, and unavoidable technical IDs.
- confirmed: Public release scope is `Android + Windows`. Apple surfaces are readiness-only and must not read as shipped.
- confirmed: Android is not public-release-ready until signing plus physical release-build localhost/control-surface audit are green.
- confirmed: Windows remains unsigned-gated beta unless trusted signing and public handoff are approved; public copy must warn about unknown-publisher / SmartScreen-style friction while unsigned.
- confirmed: Marketing is checkout-first public acquisition; webapp is continuation-first cabinet/admin and must not become a second landing page.
- confirmed: Brand assets must derive from approved masters, and legacy subtitle lockups must not ship visibly.

## Findings

### Public Copy / Forbidden Wording

- confirmed: Current `marketing/src` public copy no longer shows the inherited public `AES-256 / WireGuard` homepage claim found in prior R02. The current homepage uses calmer route/access language.
- confirmed: PowerShell scan of `shared`, `copy`, `marketing/src`, and `webapp/src` found no direct public `VPN` product copy in those active source folders except intentional allowlist/control code in `shared/copy.ts` and Telegram handles such as `@pokrov_vpn`.
- confirmed: `marketing/scripts/check-marketing-seo.mjs` still keeps legacy redirect slugs such as `/vpn-dlya-tiktok/` and a built-artifact `VPN` scanner. This is compatible with canonical redirect history if those slugs do not appear as visible public copy.
- probable: E2E fixtures still use artifact URLs like `pokrov-vpn-android.apk` / `pokrov-vpn-windows.exe`; that is not public UI by itself, but it can pollute screenshots or test expectations if visual evidence captures fixtures without redaction.

### Brand Assets

- confirmed: `shared/design-tokens.json` now declares `quiet-core-luminous-edge`, approved `logo/pokrov-wordmark.svg`, mark-only `logo/logoclear.svg`, raster master `external/logogo.png`, and blocks visible public use of `logo/logowithtext.svg`.
- confirmed: `marketing/public/pokrov-logo.svg` and `webapp/src/app/icon.svg` are mark-only assets with no visible subtitle.
- confirmed: `webapp/src/app/pokrov-logo.tsx` renders only POKROV wordmark paths when `showWordmark` is true; no subtitle path is rendered there.
- confirmed: `logo/logowithtext.svg` still exists as legacy reference and contains the old subtitle lockup. It must remain blocked from visible public/cabinet/app usage.
- unknown: `marketing/public/favicon.ico`, `apple-icon.png`, `opengraph-image.png`, and `twitter-image.png` were not visually decoded in this pass, so their derivation from subtitle-free masters is unproven.

### Design Tokens / Visual Parity

- confirmed: Marketing and webapp layouts both inject `getDesignTokenCssVariables(...)`, so the shared token bridge exists for public/cabinet contexts.
- confirmed: The W01 evidence says token JSON/TS were expanded and `marketing`/`webapp` builds passed after that pass.
- probable: Visual parity is still not proven because hard-coded CSS/classes remain across marketing/webapp, and active client token sync was inherited as unresolved.
- needs local run: Browser screenshots are still required at release breakpoints for marketing home, install, checkout, cabinet entry, dashboard, downloads/devices, support, admin dashboard/users/network/nodes/tickets, plus Android and Windows shells.
- needs local run: A visual pass must verify text fit, no overlap, no off-brand dominant colors, no dev labels, no fake live data, no forbidden wording, and no stale logo derivatives.

### Fake Claims / Counters / Demo States

- confirmed: `marketing/src/components/home/homepage.tsx` still renders an aria-hidden product visual with a fake connected state and timer `00:12:34`, plus route/status cards. Even though it is illustrative and hidden from assistive tech, it is visually public and can read as a live product screenshot.
- confirmed: Homepage proof items show `До 5 устройств` and `Ответ до 24 часов`; these align with current product/beta support limits only if the paid plan/device-limit and best-effort support wording stay visible and unchanged.
- probable: Mock support/device/routing panels in the marketing homepage are acceptable only as neutral illustration. They should not be used as evidence that real dashboard/device/support flows were visually verified.
- confirmed: `webapp/src/app/(dashboard)/admin/payments/page.tsx` explicitly labels an empty state as not a fake revenue counter, which is good guardrail copy.

### Availability Copy

- confirmed: `marketing/src/app/install/page.tsx` correctly avoids direct public downloads and routes Android/Windows beta artifacts through cabinet/help; Android is described as internal beta and Windows as possibly unsigned.
- confirmed: `marketing/src/app/offer/page.tsx` explicitly says Android APK is internal beta until signing, handoff, and physical localhost/control-surface audit; Windows beta may be unsigned; support is best-effort rather than production SLA.
- confirmed: Apple install copy is readiness/upcoming-only and does not promise a shipped iOS/macOS app.
- confirmed: `copy/catalog.ru.json` contains Apple copy as “скоро” / readiness style and cabinet email continuation as “Email скоро подключим”, matching canonical soon-state rules.
- probable: `webapp/src/components/cabinet-downloads-page.tsx` is the weakest availability surface: when `APP_*`/API URLs exist, it exposes Android Play/APK and Windows EXE cards as live download paths without repeating Android internal-only/public-blocked status or Windows unsigned warning.

### Encoding / Public Text Integrity

- confirmed: `webapp/src/components/cabinet-downloads-page.tsx` contains many mojibake literals such as `РЈС‚РѕС‡РЅРёРј...`, `Android В· APK`, and `РЎРєР°С‡Р°С‚СЊ`. This is visible cabinet copy and a public beta blocker for the downloads route.
- confirmed: `webapp/src/app/loading.tsx` contains mojibake visible loading copy, including the loading eyebrow and headline/body.
- confirmed: `webapp/src/app/(dashboard)/admin/network/page.tsx` contains mojibake in visible admin copy and separators (`вЂ”`, `В·`). It is operator-only, but it harms visual QA and release confidence.
- probable: More mojibake may exist outside the inspected high-risk files; the PowerShell scan found at least these three active webapp surfaces.

### QA / Dev Visibility

- confirmed: `webapp/src/app/layout.tsx` gates the QA overlay on `NEXT_PUBLIC_ENABLE_QA_OVERLAY === "true"`.
- needs local run: Production/build-time env must prove `NEXT_PUBLIC_ENABLE_QA_OVERLAY` is unset or false for beta. Source-level gating alone does not prove the deployed artifact lacks the overlay.
- needs local run: Browser evidence must verify local/dev login labels and QA overlay controls are not visible on public/cabinet beta surfaces.

## Highest-Risk Findings

1. confirmed: Cabinet downloads route has mojibake visible copy in `webapp/src/components/cabinet-downloads-page.tsx`, including download card labels and CTAs. This is high-risk because downloads are central to Android/Windows beta handoff.
2. probable: Cabinet downloads can show Android APK/Play and Windows EXE as available without the same Android public-blocked and Windows unsigned-warning clarity present on marketing install/offer pages.
3. confirmed: Marketing homepage still uses a visually public fake connected timer/status mock (`00:12:34`, connected route cards). It needs either replacement with approved neutral illustration or screenshot evidence proving it cannot be mistaken for real runtime proof.
4. needs local run: No current browser/screenshot evidence in this pass proves public beta visual parity, text fit, absence of QA overlay, or absence of stale logo/share-preview assets across marketing, cabinet, admin, Android, and Windows.
5. unknown: Derived favicon/share-preview/apple-icon assets were not visually decoded, so release-facing raster/social assets are not proven regenerated from subtitle-free approved masters.

## Required Visual / Browser Evidence Before Signoff

- needs local run: `npm.cmd run build` in `marketing/`.
- needs local run: `npm.cmd run build` in `webapp/`.
- needs local run: `npm.cmd run test:e2e` and `npm.cmd run test:e2e:admin` in `webapp/` after copy/visual fixes.
- needs local run: `python scripts/check-links.py` and `python scripts/ui_visual_smoke.py`.
- needs local run: Browser screenshots for `pokrov.space` home, `/checkout/`, `/install/`, `/offer/`, cabinet entry, dashboard, subscription/checkout, downloads, devices, support, admin users/payments/network/nodes/tickets.
- needs local run: Mobile screenshots at 360/390/430 widths and Telegram WebView-like height for public/cabinet flows.
- needs local run: Android and Windows shell screenshots proving Russian-first copy, POKROV identity, no direct public `VPN` wording, no Hiddify residue, and clear beta limitations.
- needs local run: Production-env smoke proving `NEXT_PUBLIC_ENABLE_QA_OVERLAY` is false/unset.
- needs local run: Visual asset audit for `favicon.ico`, `apple-icon.png`, Open Graph/Twitter images, launcher/splash/tray/installer/store assets.

## Implementation Follow-Ups

- confirmed: Fix mojibake in active webapp visible strings before public beta screenshots.
- confirmed: Make cabinet downloads availability copy match marketing install/offer limitations: Android internal-only/public-blocked until audit/signing; Windows unsigned warning until signing/handoff.
- probable: Replace the public fake connected timer/status visual with neutral product illustration, a labeled mock, or approved real screenshot evidence.
- probable: Regenerate and inventory derived brand assets from approved subtitle-free masters.
- probable: Keep `logowithtext.svg` as legacy reference only and add/keep guardrails that prevent import into active public/cabinet/client surfaces.

## Evidence Paths

- confirmed: `shared/design-tokens.json`
- confirmed: `shared/design-tokens.ts`
- confirmed: `shared/copy.ts`
- confirmed: `copy/catalog.ru.json`
- confirmed: `shared/product-facts.json`
- confirmed: `shared/public-urls.json`
- confirmed: `logo/logoclear.svg`
- confirmed: `logo/logowithtext.svg`
- confirmed: `logo/pokrov-wordmark.svg`
- confirmed: `marketing/public/pokrov-logo.svg`
- confirmed: `marketing/src/components/home/homepage.tsx`
- confirmed: `marketing/src/app/install/page.tsx`
- confirmed: `marketing/src/app/offer/page.tsx`
- confirmed: `webapp/src/app/layout.tsx`
- confirmed: `webapp/src/app/loading.tsx`
- confirmed: `webapp/src/components/cabinet-downloads-page.tsx`
- confirmed: `webapp/src/app/(dashboard)/admin/network/page.tsx`
- confirmed: `docs/developer/work-orders/2026-04-beta-release/research/R02-design-system.md`
- confirmed: `docs/developer/work-orders/2026-04-beta-release/evidence/visual-audit/WO-001-design-system-brand-assets.md`
