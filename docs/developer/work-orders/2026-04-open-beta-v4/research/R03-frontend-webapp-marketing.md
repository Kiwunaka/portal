# R03 Frontend Webapp Marketing Audit

Date: 2026-04-26
Role: R03, POKROV Open Beta v4 research wave
Scope: `marketing/`, `webapp/`, `webapp/README.md`, Playwright tests, shared copy/catalog, build scripts
Write scope: this file only

## Executive Summary

No confirmed P0 frontend implementation defect was found from static inspection, but the current release confidence is not yet strong enough for Open Beta v4 because the required responsive matrix is only partially enforced. The webapp has a 390px Playwright overflow check for core cabinet routes and selected admin routes; it does not cover 320, 360, 768, 1024, 1440, or 1920, and it does not take deliberate screenshots for visual review.

Marketing has solid static SEO primitives: metadata, canonical URLs, JSON-LD helpers, robots, sitemap, manifest, share images, legal pages, and legacy SEO redirects. The biggest SEO/product gap is that `/checkout/` is explicitly indexable and is the primary public acquisition route, but it is absent from `MARKETING_SITEMAP_ROUTES`.

Checkout has a useful local catalog fallback and canonical hosted-checkout handoff, but degradation is not browser-tested: API catalog outage, key-status failure, bad plan query, promo handling, and external checkout availability are not covered by e2e. Admin narrow viewport work exists, but the admin shell stacks a full navigation/sidebar before the working surface on narrow screens; it is technically non-overflowing in one 390px test, but not ergonomic for an operator in a mobile or Telegram WebView-like viewport.

## Evidence Table

| Label | Evidence | Finding | Confidence |
| --- | --- | --- | --- |
| E01 | `webapp/README.md` | Webapp role, route map, export build, and e2e commands are documented; admin narrow viewport is called out as required. | High |
| E02 | `webapp/playwright.config.ts` | Playwright has one Chromium-like config, failure-only screenshots, no named viewport projects. | High |
| E03 | `webapp/e2e/cabinet-flow.spec.ts` | Cabinet overflow test covers only 390x844 and only `/dashboard/`, `/subscription/`, `/devices/`, `/support/`. | High |
| E04 | `webapp/e2e/admin-gate.spec.ts` | Admin mobile overflow test covers only 390x844 and selected admin pages (`users`, `nodes`, `tickets`). | High |
| E05 | `webapp/src/app/(admin)/admin/layout.tsx` | Admin layout uses full stacked sidebar/content/rail below 2xl; no compact admin drawer or mobile-first category nav. | High |
| E06 | `webapp/src/app/(admin)/admin/users/page.tsx` | Users admin page has table/detail split at xl and table horizontal scroll; usable but not optimized for 320/360. | Medium |
| E07 | `webapp/src/components/cabinet-shell.tsx` | Consumer cabinet has an xl sidebar, mobile drawer, Telegram-context bottom nav, and `overflow-x-hidden`. | High |
| E08 | `marketing/src/app/globals.css` | Marketing has responsive breakpoints at 1180/980/780/560 and checkout grid collapses below 1180. | High |
| E09 | `marketing/src/components/home/homepage.module.css` | Home v3 has breakpoints at 1280/960/720; no explicit 320/360 visual proof. | High |
| E10 | `marketing/src/app/checkout/checkout-client.tsx` | Checkout fetches public catalog with fallback plans and links to canonical hosted checkout; no e2e degradation coverage found. | High |
| E11 | `marketing/src/lib/marketing-site.ts` | Sitemap includes home, SEO landing pages, offer, privacy; excludes `/checkout/` and `/install/`. | High |
| E12 | `marketing/src/app/checkout/page.tsx` | Checkout metadata is indexable (`noIndex: false`) and canonicalizes `/checkout/`. | High |
| E13 | `marketing/scripts/check-marketing-seo.mjs` | Static guard checks canonical SEO routes, redirects, and direct public `VPN` wording in marketing source/catalog. | High |
| E14 | `shared/copy.ts` | Shared copy validator allowlists legacy `@pokrov_vpn`/`POKROV VPN` exceptions and blocks direct public `VPN` wording. | High |
| E15 | `webapp/src/components/route-transition.tsx` | Route transition uses `framer-motion` with `useReducedMotion`; animation is light but globally applied. | Medium |
| E16 | `marketing/package.json` | Marketing declares `framer-motion` and `gsap`; no source imports were found during static scan, so build output should confirm no route bundle impact. | Medium |
| E17 | `marketing/public/_redirects` | Legacy SEO slugs containing `vpn` redirect permanently to canonical non-`VPN` routes; this is compatibility, not new public copy. | High |
| E18 | `webapp/src/app/layout.tsx` | Webapp is `noindex,nofollow`, loads Telegram WebApp script and Material Symbols font; expected for cabinet/admin, but affects first-load budget. | High |

## P0 Issues

None confirmed from static inspection.

P0 remains possible until browser screenshots are captured at 320/360/390/768/1024/1440/1920 for marketing checkout, cabinet flows, and admin workflows. The current evidence proves only a narrow slice of horizontal overflow behavior at 390px.

## P1 Issues

### R03-P1-01 Required Responsive Matrix Is Not Enforced

Required widths are 320/360/390/768/1024/1440/1920. Existing e2e coverage checks 390 only, and only for a subset of cabinet/admin routes. Marketing has no Playwright viewport matrix. This can let 320/360 CTA wrapping, 768 tablet layouts, and 1440/1920 wide layout regressions ship unseen.

Implementation work:

- Add viewport projects or a dedicated responsive matrix spec for both `marketing` and `webapp`.
- Assert no document-level horizontal overflow.
- Capture screenshots for manual review at all required widths.
- Include checkout, install, legal, SEO landing, cabinet entry, dashboard, subscription, downloads, redeem, support, admin dashboard, users, network, nodes, tickets, payments, broadcast.

### R03-P1-02 Primary Checkout Is Indexable But Missing From Sitemap

`/checkout/` is the primary public acquisition/pricing route and has indexable metadata, but `MARKETING_SITEMAP_ROUTES` excludes it. This creates a mismatch between product strategy and SEO discovery.

Implementation work:

- Add `/checkout/` to `MARKETING_SITEMAP_ROUTES` with high priority.
- Decide whether `/install/` should remain `noindex` and absent from sitemap; current state is coherent because install is help/task-oriented.
- Extend `check-marketing-seo.mjs` to require `/checkout/` in sitemap routes.

### R03-P1-03 Checkout Degradation Is Not Browser-Tested

Checkout has static fallback plans, but no e2e covers catalog API failure, malformed plan query, hosted checkout URL correctness, key-status failure, promo code state, or support/cabinet fallback visibility. This is payment-adjacent and should be verified before beta traffic.

Implementation work:

- Add marketing Playwright tests for `/checkout/?plan=start_99`, bad plan aliases, catalog API 500/offline, access-key 404/500, and promo code updates.
- Assert CTA never points to `connect.pokrov.space`.
- Assert hosted checkout link uses `https://pay.pokrov.space/checkout/` with plan/promo params.
- Assert failure states keep visible cabinet/support fallback and do not expose raw subscription links.

### R03-P1-04 Admin Narrow Viewport Is Technically Non-Overflowing But Not Operator-Usable Enough

The admin shell stacks full sidebar, content, and right rail on narrow screens. The current 390px test checks clickability and overflow for selected pages, but the operator must scroll through a long nav before the working surface. At 320/360 this is likely slow and brittle for incident use.

Implementation work:

- Add a compact admin topbar/drawer for widths below 768.
- Move active category tabs before the full section descriptions.
- Keep destructive actions and dialogs reachable without relying on long horizontal table interactions.
- Add mobile checks for admin `/dashboard/`, `/users/`, `/network/`, `/nodes/`, `/tickets/`, `/payments/`, `/broadcast/`.

## P2 Issues

### R03-P2-01 Animation And Motion Budget Needs Tightening

Webapp route transitions respect reduced motion, and global CSS includes reduced-motion rules. Still, every route passes through a `framer-motion` wrapper, and the QA overlay also imports `framer-motion` when enabled. Marketing declares `framer-motion` and `gsap` dependencies without static source imports found in this pass.

Implementation work:

- Confirm build output does not include unused marketing animation libraries.
- Consider removing unused marketing animation deps if build confirms no imports.
- Keep route transition duration at or below the current 220ms.
- Avoid large scroll-linked animations and any animation that affects layout.

### R03-P2-02 Wide View Layout Budgets Are Informal

Marketing and cabinet cap content widths, but there are no explicit 1440/1920 screenshot gates. Wide desktop can regress into sparse, overly stretched, or hidden-next-section layouts without detection.

Implementation work:

- Add screenshots at 1440 and 1920 for home, checkout, install, dashboard, subscription, admin users, admin network.
- Include first viewport and mid-page screenshots for marketing home/checkout.

### R03-P2-03 POKROV Network Remains In Non-Public Retention Catalog Entries

`copy/catalog.ru.json` still contains `POKROV Network` in non-public retention entries. This is not a direct public marketing/webapp blocker because `allowed_public` is false and marketing checks focus public copy, but it is brand debt.

Implementation work:

- Replace non-public retention `POKROV Network` with `POKROV` in a separate copy cleanup task.
- Keep `POKROV VPN` only for legacy compatibility labels where unavoidable.

## Proposed Implementation Work

1. Add responsive screenshot and overflow coverage for marketing and webapp.
2. Add checkout degradation e2e for catalog fallback, key lookup failure, promo plan links, hosted checkout URL, and fallback CTAs.
3. Add `/checkout/` to marketing sitemap and SEO guard.
4. Add a compact admin mobile shell for operator routes below 768px.
5. Add route bundle budget capture to CI output and fail only on agreed thresholds.
6. Audit/remove unused marketing animation dependencies after build-size confirmation.
7. Add screenshot tasks to the release checklist and store artifacts outside source docs unless intentionally retained.

## Exact Verification Commands

Note: I did not run build/test/screenshot commands in this research pass because the assigned write scope allows only this file, and these commands generate `.next/`, `out/`, screenshots, traces, or temp artifacts.

Marketing:

```powershell
cd C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4\marketing
npm.cmd run check:seo
npm.cmd run build
python ..\scripts\check-links.py
python ..\scripts\ui_visual_smoke.py
```

Webapp:

```powershell
cd C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4\webapp
npm.cmd run build
npm.cmd run test:e2e
npm.cmd run test:e2e:admin
```

Focused existing responsive checks:

```powershell
cd C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4\webapp
npm.cmd run build
set E2E_PORT=3102&& set PLAYWRIGHT_FRESH_SERVER=1&& set PLAYWRIGHT_SERVER_MODE=start&& npx playwright test e2e/cabinet-flow.spec.ts --grep "narrow mobile viewport"
set E2E_PORT=3101&& set PLAYWRIGHT_FRESH_SERVER=1&& set PLAYWRIGHT_SERVER_MODE=start&& npx playwright test e2e/admin-gate.spec.ts --grep "inside the viewport on mobile"
```

New verification command after adding R03 responsive specs:

```powershell
cd C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4\webapp
npm.cmd run build
set E2E_PORT=3103&& set PLAYWRIGHT_FRESH_SERVER=1&& set PLAYWRIGHT_SERVER_MODE=start&& npx playwright test e2e/responsive-matrix.spec.ts --reporter=list
```

```powershell
cd C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4\marketing
npm.cmd run build
set E2E_PORT=3104&& set PLAYWRIGHT_FRESH_SERVER=1&& set PLAYWRIGHT_SERVER_MODE=start&& npx playwright test e2e/responsive-marketing.spec.ts --reporter=list
```

Bundle budget capture:

```powershell
cd C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4\marketing
npm.cmd run build
```

```powershell
cd C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4\webapp
npm.cmd run build
```

Record the Next.js route-size table from stdout in the work-order handoff or CI artifact. Do not commit `.next/` or `out/`.

## Route-By-Route Responsive Matrix

Legend: `S` = static responsive code found, `T390` = existing 390px e2e overflow check, `GAP` = required screenshot/overflow proof missing for that width, `NA` = not indexable/intent-only but still needs usability proof.

| Surface / route | 320 | 360 | 390 | 768 | 1024 | 1440 | 1920 | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Marketing `/` | GAP | GAP | GAP | GAP | GAP | GAP | GAP | Static breakpoints exist in home CSS, no e2e screenshots. |
| Marketing `/checkout/` | GAP | GAP | GAP | GAP | GAP | GAP | GAP | Primary acquisition route; degradation tests missing. |
| Marketing `/install/` | GAP | GAP | GAP | GAP | GAP | GAP | GAP | `noindex` help route; still user-facing after purchase/known intent. |
| Marketing `/mobile/` | GAP | GAP | GAP | GAP | GAP | GAP | GAP | Uses shared `MarketingLanding`; needs SEO landing proof. |
| Marketing `/tiktok/` | GAP | GAP | GAP | GAP | GAP | GAP | GAP | Uses shared landing shell; needs route screenshot. |
| Marketing `/youtube/` | GAP | GAP | GAP | GAP | GAP | GAP | GAP | Uses shared landing shell; needs route screenshot. |
| Marketing `/devices/` | GAP | GAP | GAP | GAP | GAP | GAP | GAP | Uses shared landing shell; important Android/Windows scope proof. |
| Marketing `/telegram/` | GAP | GAP | GAP | GAP | GAP | GAP | GAP | Uses shared landing shell; Telegram must stay secondary. |
| Marketing `/offer/` | GAP | GAP | GAP | GAP | GAP | GAP | GAP | Legal route; verify contacts and no overflow. |
| Marketing `/privacy/` | GAP | GAP | GAP | GAP | GAP | GAP | GAP | Legal route; verify contacts and no overflow. |
| Webapp `/` entry | GAP | GAP | GAP | GAP | GAP | GAP | GAP | Auth/cabinet continuation tested functionally, not in viewport matrix. |
| Webapp `/dashboard/` | GAP | GAP | T390 | GAP | GAP | GAP | GAP | Existing 390 overflow check only. |
| Webapp `/subscription/` | GAP | GAP | T390 | GAP | GAP | GAP | GAP | Existing 390 overflow check only. |
| Webapp `/subscription/checkout/` | GAP | GAP | GAP | GAP | GAP | GAP | GAP | Functional copy test exists, no viewport proof. |
| Webapp `/devices/` | GAP | GAP | T390 | GAP | GAP | GAP | GAP | Existing 390 overflow check only. |
| Webapp `/statistics/` | GAP | GAP | GAP | GAP | GAP | GAP | GAP | Functional safety test exists, no viewport proof. |
| Webapp `/downloads/` | GAP | GAP | GAP | GAP | GAP | GAP | GAP | Functional downloads test exists, no viewport proof. |
| Webapp `/redeem/` | GAP | GAP | GAP | GAP | GAP | GAP | GAP | Activation-key task route needs narrow form proof. |
| Webapp `/support/` | GAP | GAP | T390 | GAP | GAP | GAP | GAP | Existing 390 overflow check only. |
| Webapp `/support/thread/` | GAP | GAP | GAP | GAP | GAP | GAP | GAP | Ticket detail and message composer need proof. |
| Webapp `/settings/` | GAP | GAP | GAP | GAP | GAP | GAP | GAP | Bonus actions tested functionally, no viewport proof. |
| Webapp `/pricing/` | NA | NA | NA | NA | NA | NA | NA | Compatibility redirect; verify redirect in link checks. |
| Admin `/admin/` | GAP | GAP | GAP | GAP | GAP | GAP | GAP | Entry/admin home not in mobile matrix. |
| Admin `/admin/dashboard/` | GAP | GAP | GAP | GAP | GAP | GAP | GAP | Summary dashboard not in mobile matrix. |
| Admin `/admin/users/` | GAP | GAP | T390 | GAP | GAP | GAP | GAP | Existing 390 overflow/clickability only; 320/360 risky. |
| Admin `/admin/network/` | GAP | GAP | GAP | GAP | GAP | GAP | GAP | JSON editor route needs narrow proof. |
| Admin `/admin/nodes/` | GAP | GAP | T390 | GAP | GAP | GAP | GAP | Existing 390 overflow only. |
| Admin `/admin/tickets/` | GAP | GAP | T390 | GAP | GAP | GAP | GAP | Existing 390 composer clickability only. |
| Admin `/admin/payments/` | GAP | GAP | GAP | GAP | GAP | GAP | GAP | Payment reconciliation needs narrow proof. |
| Admin `/admin/bonuses/` | GAP | GAP | GAP | GAP | GAP | GAP | GAP | Operator action route needs proof. |
| Admin `/admin/promos/` | GAP | GAP | GAP | GAP | GAP | GAP | GAP | Promo slot editor needs proof. |
| Admin `/admin/referrals/` | GAP | GAP | GAP | GAP | GAP | GAP | GAP | Referral ops route needs proof. |
| Admin `/admin/broadcast/` | GAP | GAP | GAP | GAP | GAP | GAP | GAP | Messaging route needs proof before beta use. |

## JS Bundle / Route Budget

These are proposed Open Beta v4 budgets until measured Next.js route-size output is captured. Treat gzip/First Load JS as the release-facing metric from `next build` stdout.

| Route family | Proposed first-load JS budget | Risk notes |
| --- | ---: | --- |
| Marketing static landing routes (`/`, `/mobile/`, `/tiktok/`, `/youtube/`, `/devices/`, `/telegram/`) | <= 130 KB | Should stay mostly static; shared landing shell should not import client-only motion libraries. |
| Marketing `/checkout/` | <= 170 KB | Client state, catalog fetch, key lookup, and promo handling justify a higher budget. |
| Marketing legal/help (`/offer/`, `/privacy/`, `/install/`) | <= 120 KB | Should stay static/help-oriented. |
| Webapp entry/cabinet shell | <= 220 KB | Session provider, Telegram script, Material Symbols, and route transition add cost. |
| Webapp consumer task routes | <= 260 KB | QR, downloads, tickets, and forms may add weight; raw-link UI must stay hidden. |
| Webapp admin shell | <= 300 KB | Admin API surface and tables are heavier; keep route-specific chunks from pulling every admin page at once. |
| Admin users/network heavy routes | <= 360 KB | User detail, policy editor, JSON editor, and tables are expected heavy routes. |

Budget tasks:

- Capture actual `next build` route-size output for both apps.
- Fail CI only after current measured baseline is known.
- Confirm marketing `framer-motion` and `gsap` are absent from route chunks or remove them.
- Keep QA overlay disabled in production unless explicitly requested with `NEXT_PUBLIC_ENABLE_QA_OVERLAY=true`.

## Animation Backlog

| Item | Current state | Backlog action |
| --- | --- | --- |
| Webapp route transition | Global `framer-motion` wrapper with `useReducedMotion` and 220ms duration. | Keep, but add screenshot/video smoke at reduced motion and normal motion. |
| Webapp QA overlay | `framer-motion` panel, gated by env host. | Ensure production env leaves overlay disabled. |
| Webapp CSS animations | Reduced-motion CSS disables animation/transition duration globally. | Keep. Add e2e reduced-motion context check. |
| Marketing CSS transitions | Hover/transition rules wrapped by `prefers-reduced-motion: no-preference`; responsive CSS is mostly static. | Keep; avoid adding scroll-linked or layout-affecting motion. |
| Marketing deps | `framer-motion` and `gsap` declared, no static source imports found. | Confirm build chunks; remove if unused. |
| Loading skeletons | `animate-pulse` in webapp loading/auth states. | Acceptable; verify reduced motion does not create distracting loops. |

## SEO / Legal / Link Checklist

| Check | Current state | Action |
| --- | --- | --- |
| Canonical marketing host | `CANONICAL_MARKETING_SITE_URL` and `metadataBase` used. | Keep. |
| Webapp indexing | `webapp` root metadata sets `index:false, follow:false`. | Keep; cabinet/admin should not become acquisition SEO. |
| Marketing canonical routes | `/mobile/`, `/tiktok/`, `/youtube/`, `/devices/`, `/telegram/` exist. | Keep. |
| Legacy SEO redirects | `_redirects` maps old `vpn` slugs to canonical routes. | Keep as compatibility. |
| Checkout sitemap | `/checkout/` is indexable but absent from sitemap. | Add to `MARKETING_SITEMAP_ROUTES` and SEO check. |
| Install sitemap | `/install/` is `noIndex:true` and absent from sitemap. | Coherent; keep unless product wants install indexed. |
| Robots | Allows `/`, disallows `/api/` and `/_next/`, declares sitemap/host. | Keep; verify built `robots.txt`. |
| Manifest | POKROV name, icons, categories, start URL present. | Keep; verify asset links. |
| JSON-LD | Organization, WebSite, SoftwareApplication, Breadcrumb, FAQ helpers present. | Keep; validate rendered JSON-LD in built output. |
| Legal pages | `/offer/` and `/privacy/` have metadata, breadcrumbs, contacts, responsive classes. | Add viewport screenshots. |
| Public `VPN` wording | Marketing guard blocks direct public `VPN`; shared validator allowlists legacy Telegram/channel identifiers. | Keep guard; expand to rendered output after build. |
| Canonical checkout host | Checkout uses `pay.pokrov.space/checkout/` via shared public URL. | Add e2e assertion for plan/promo params. |
| Config host exposure | Marketing CTAs should not route to `connect.pokrov.space`; cabinet hides raw links in first-layer UX. | Keep tests and add checkout-specific assertion. |
| External links | Telegram/support/cabinet links use canonical shared URLs. | Verify with link checker and screenshot tasks. |

## E2E Screenshot Tasks

Add screenshots as deterministic release artifacts, not committed source files unless the orchestrator requests retained evidence.

| Task | Routes | Viewports | Assertions |
| --- | --- | --- | --- |
| S01 Marketing home | `/` | 320, 360, 390, 768, 1024, 1440, 1920 | No horizontal overflow; hero CTA visible; next section hinted; no direct `VPN` copy. |
| S02 Marketing checkout | `/checkout/?plan=start_99&promo=POKROV10`, `/checkout/?plan=bad` | 320, 360, 390, 768, 1024, 1440, 1920 | Plan cards usable; total visible; hosted checkout link canonical; fallback CTAs visible. |
| S03 Marketing checkout degraded | `/checkout/` with `/api/public/catalog` 500/offline and key status 404/500 | 320, 390, 768 | Fallback plans render; error text fits; no raw subscription link. |
| S04 SEO landing shell | `/mobile/`, `/devices/`, `/telegram/`, `/youtube/`, `/tiktok/` | 320, 390, 768, 1440 | Shared shell responsive; route-specific title visible; CTA priority coherent. |
| S05 Legal/help | `/install/`, `/offer/`, `/privacy/` | 320, 390, 768, 1440 | Contacts and legal text readable; no overflow; no fake download promise. |
| S06 Cabinet entry | `/` unauthenticated and authenticated redirect | 320, 360, 390, 768, 1024 | Email marked soon; Telegram continuation visible; no second landing-page pitch. |
| S07 Cabinet core | `/dashboard/`, `/subscription/`, `/devices/`, `/statistics/`, `/support/`, `/settings/` | 320, 360, 390, 768, 1024, 1440 | Drawer/top nav usable; no raw token/QR on first layer; no overflow. |
| S08 Cabinet tasks | `/downloads/`, `/redeem/?key=POKROV-XXXX`, `/subscription/checkout/?plan=1_month` | 320, 390, 768, 1440 | Forms/buttons fit; checkout continuation stays hosted/key-first. |
| S09 Admin shell | `/admin/`, `/admin/dashboard/`, `/admin/users/`, `/admin/network/`, `/admin/nodes/`, `/admin/tickets/` | 320, 360, 390, 768, 1024, 1440, 1920 | Active category visible quickly; tables/editors usable; dialogs fit; no overflow. |
| S10 Admin operator actions | users delete dialog, extend dialog, network save panel, ticket reply, broadcast compose | 320, 390, 768 | Destructive and save actions reachable; modal max height fits; keyboard focus visible. |
| S11 Reduced motion | Marketing home/checkout, webapp dashboard/admin users | 390, 1440 | Motion disabled or minimal under `prefers-reduced-motion: reduce`. |
| S12 Bundle budget | All built routes | N/A | Record route-size table; compare to proposed budget after baseline. |

## Handoff Notes

What I checked:

- Canonical product/system/developer docs required by the root contract.
- `webapp/README.md`, `webapp/package.json`, `webapp/playwright.config.ts`, e2e specs, shell/admin/cabinet components.
- `marketing/package.json`, marketing layout/pages/components, SEO helpers, redirects, global/home CSS, checkout client.
- Shared public URL/product/copy/tariff facts relevant to branding and checkout.

What I found:

- Existing responsive proof is too narrow for the requested Open Beta v4 matrix.
- Checkout is product-aligned but lacks degradation e2e.
- Admin mobile has non-overflow checks at 390px, but the layout is not yet a compact operator surface.
- `/checkout/` should be added to the sitemap if it remains indexable and primary acquisition.

What I changed:

- Created this R03 research artifact only.

How I verified:

- Static inspection with PowerShell file reads and targeted `Select-String` searches.
- No build/test/screenshot commands were run because the task allowed writing only this file.

What remains / risk:

- Browser proof at 320/360/390/768/1024/1440/1920 remains required.
- Build route-size budgets are proposed, not measured.
- Any final release decision should wait for generated screenshots and exact build output.
