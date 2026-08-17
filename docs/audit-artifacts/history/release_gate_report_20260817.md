# Weekly Release Gate Snapshot (20260817)

- Exported UTC: `2026-08-17T05:01:29.481955+00:00`
- Source report: `/home/runner/work/portal/portal/docs/audit-artifacts/release_gate_report.md`

# Release Gate Report

- Generated at: `2026-08-17 05:01:29`
- Status: `PASS`
- Gate set: `quick`
- Brain IP supplied: `no`
- Client platform gates: `none`
- Android audit required by selected gates: `no`

## Summary

| Gate | Exit code | Duration (s) |
|---|---:|---:|
| Critical worker regression | 0 | 17.30 |
| API lifecycle smoke | 0 | 4.69 |
| Public link checks | 0 | 0.05 |
| Marketing production build | 0 | 20.67 |
| AdminApp production build | 0 | 21.11 |
| Admin webapp smoke | 0 | 0.11 |
| WebApp production build | 0 | 27.34 |
| WebApp Playwright E2E | 0 | 149.27 |
| UI visual smoke | 0 | 0.05 |
| Client workspace preflight (skipped) | 0 | 0.01 |

## Evidence Classification

| Evidence | Scope | Status | Notes |
|---|---|---|---|
| current-origin check | local quick gate set | PASS | Runs on the operator workstation; does not prove brain-origin or RU-origin reachability. |
| brain-origin check | `scripts/verify_brain_ready.py` / predeploy readiness | BLOCKED_BY_ACCESS | Requires `--brain-ip` and live SSH/API access; keep separate from current-origin results. |
| RU-origin check | external RU probe (`mini` or replacement) | BLOCKED_BY_ACCESS | Not run by this local gate; requires an external RU probe host and redacted report. |
| Android physical audit | release-build localhost/control-surface audit | BLOCKED_BY_ACCESS | Public Android remains blocked unless this is run on physical hardware with the release build. |
| Runtime app-download smoke | `/api/client/apps` and provider checks | SKIPPED_NO_LIVE_TOKEN | Requires `TELEGRAM_INIT_DATA`; omit raw token values from evidence. |
| Client platform builds | none requested | NOT_REQUESTED | Repo/static gates alone do not create Android or Windows beta artifacts. |

## Command Tails

### Critical worker regression

- Command: `/opt/hostedtoolcache/Python/3.12.13/x64/bin/python -m pytest tests/test_worker_retention.py -q --basetemp /home/runner/work/portal/portal/.tmp/pytest-basetemp/release-gate-dpa9hdjb`
- Exit: `0`

```text
.........................                                                [100%]
25 passed in 16.21s
```

### API lifecycle smoke

- Command: `/opt/hostedtoolcache/Python/3.12.13/x64/bin/python scripts/api_lifecycle_smoke.py`
- Exit: `0`

```text
.
----------------------------------------------------------------------
Ran 1 test in 3.928s

OK
```

### Public link checks

- Command: `/opt/hostedtoolcache/Python/3.12.13/x64/bin/python scripts/check-links.py`
- Exit: `0`

```text
[PASS] marketing/src/app/robots.ts: Marketing SEO route is present
[PASS] marketing/src/app/sitemap.ts: Marketing SEO route is present
[PASS] marketing/src/app/manifest.ts: Marketing SEO route is present
[PASS] marketing/public/opengraph-image.png: Marketing SEO route is present
[PASS] marketing/public/twitter-image.png: Marketing SEO route is present
[PASS] marketing/public/favicon.ico: Marketing SEO route is present
[PASS] marketing/public/apple-icon.png: Marketing SEO route is present
[PASS] marketing/src/app/page.tsx: Public marketing CTA no longer routes to connect host
[PASS] marketing/src/components/layout/page-shell.tsx: Public cabinet CTA points to webapp host
[PASS] marketing/src/components/home/pricing.tsx: Pricing CTA routes through public checkout gateway
[PASS] marketing/src/components/layout/footer.tsx: Marketing footer exposes canonical news channel
[PASS] marketing/src/app/layout.tsx: Layout includes `metadataBase` metadata wiring
[PASS] marketing/src/app/layout.tsx: Layout includes `manifest` metadata wiring
[PASS] marketing/src/app/layout.tsx: Layout includes `icons` metadata wiring
[PASS] marketing/src/app/layout.tsx: Layout includes `apple` metadata wiring
[PASS] marketing/src/app/layout.tsx: Layout includes `/favicon.ico` metadata wiring
[PASS] marketing/src/app/layout.tsx: Layout includes `/apple-icon.png` metadata wiring
[PASS] marketing/src/lib/marketing-site.ts: Marketing metadata declares `alternates`
[PASS] marketing/src/lib/marketing-site.ts: Marketing metadata declares `canonical`
[PASS] marketing/src/lib/marketing-site.ts: Marketing metadata declares `twitter`
[PASS] marketing/src/lib/marketing-site.ts: Marketing metadata declares `images`
[PASS] marketing/src/app/page.tsx: Home page wires `buildMarketingMetadata`
[PASS] marketing/src/app/page.tsx: Home page wires `buildSoftwareApplicationJsonLd`
[PASS] marketing/src/app/page.tsx: Home page wires `buildFaqJsonLd`
[PASS] marketing/src/app/checkout/checkout-client.tsx: Checkout gateway uses cabinet-safe fallback instead of connect host
[PASS] marketing/src/app/offer/page.tsx: Legal page avoids direct checkout CTA
[PASS] marketing/src/app/privacy/page.tsx: Legal page avoids direct checkout CTA
[PASS] webapp/src/app/(dashboard)/support/legal/page.tsx: Webapp legal links use absolute marketing URLs
[PASS] portal_bot/api_admin_routes.py: Admin campaign link builder marks public checkout as safe fallback
[PASS] portal_bot/api.py: Numeric subscription fallback is explicit compatibility and defaults off

Link check passed.
```

### Marketing production build

- Command: `npm run build`
- Exit: `0`

```text
  Generating static pages using 1 worker (16/32)
  Generating static pages using 1 worker (24/32)
✓ Generating static pages using 1 worker (32/32) in 956.5ms
  Finalizing page optimization ...

Route (app)
┌ ○ /
├ ○ /_not-found
├ ○ /android
├ ○ /best-vpn
├ ○ /billing/no-autosubscription
├ ○ /checkout
├ ○ /compare/free-vpn
├ ○ /devices
├ ○ /fallback
├ ○ /guides
├ ○ /guides/pokrov-app
├ ○ /install
├ ○ /install/android
├ ○ /install/windows
├ ○ /manifest.webmanifest
├ ○ /mobile
├ ○ /offer
├ ○ /privacy
├ ○ /programs
├ ○ /robots.txt
├ ○ /sitemap.xml
├ ○ /status
├ ○ /support/install
├ ○ /telegram
├ ○ /tiktok
├ ○ /transparency
├ ○ /trial/no-card
├ ○ /trust/github-releases
├ ○ /vpn
├ ○ /windows
└ ○ /youtube


○  (Static)  prerendered as static content
```

### AdminApp production build

- Command: `npm run build`
- Exit: `0`

```text
> pokrov-adminapp@0.1.0 build
> next build

⚠ No build cache found. Please configure build caching for faster rebuilds. Read more: https://nextjs.org/docs/messages/no-cache
Attention: Next.js now collects completely anonymous telemetry regarding usage.
This information is used to shape Next.js' roadmap and prioritize features.
You can learn more, including how to opt-out if you'd not like to participate in this anonymous program, by visiting the following URL:
https://nextjs.org/telemetry

▲ Next.js 16.2.10 (Turbopack)
- Experiments (use with caution):
  ✓ externalDir

  Creating an optimized production build ...
✓ Compiled successfully in 8.6s
  Running TypeScript ...
  Finished TypeScript in 9.6s ...
  Collecting page data using 1 worker ...
  Generating static pages using 1 worker (0/18) ...
  Generating static pages using 1 worker (4/18)
  Generating static pages using 1 worker (8/18)
  Generating static pages using 1 worker (13/18)
✓ Generating static pages using 1 worker (18/18) in 503ms
  Finalizing page optimization ...

Route (app)
┌ ○ /
├ ○ /_not-found
└ ● /[section]
  ├ /nodes
  ├ /traffic
  ├ /alerts
  └ [+12 more paths]


○  (Static)  prerendered as static content
●  (SSG)     prerendered as static HTML (uses generateStaticParams)
```

### Admin webapp smoke

- Command: `/opt/hostedtoolcache/Python/3.12.13/x64/bin/python scripts/admin_webapp_smoke.py`
- Exit: `0`

```text
Admin WebApp smoke passed.
```

### WebApp production build

- Command: `npm run build`
- Exit: `0`

```text
├ ○ /admin/bonuses
├ ○ /admin/broadcast
├ ○ /admin/dashboard
├ ○ /admin/funnel
├ ○ /admin/network
├ ○ /admin/nodes
├ ○ /admin/payments
├ ○ /admin/programs
├ ○ /admin/promos
├ ○ /admin/referrals
├ ○ /admin/release
├ ○ /admin/tickets
├ ○ /admin/users
├ ○ /dashboard
├ ○ /dashboard/downloads
├ ○ /devices
├ ○ /downloads
├ ○ /guides
├ ○ /guides/pokrov-app
├ ○ /icon.svg
├ ○ /pricing
├ ○ /profile
├ ○ /programs
├ ○ /protection
├ ○ /recover
├ ○ /redeem
├ ○ /rewards
├ ○ /settings
├ ○ /statistics
├ ○ /subscription
├ ○ /subscription/checkout
├ ○ /support
├ ○ /support/legal
├ ○ /support/thread
└ ○ /verify


○  (Static)  prerendered as static content

[fix-export-segment-paths] created 0 dot-joined segment payload copies
```

### WebApp Playwright E2E

- Command: `npm run test:e2e`
- Exit: `0`

```text
├ ○ /admin/nodes
├ ○ /admin/payments
├ ○ /admin/programs
├ ○ /admin/promos
├ ○ /admin/referrals
├ ○ /admin/release
├ ○ /admin/tickets
├ ○ /admin/users
├ ○ /dashboard
├ ○ /dashboard/downloads
├ ○ /devices
├ ○ /downloads
├ ○ /guides
├ ○ /guides/pokrov-app
├ ○ /icon.svg
├ ○ /pricing
├ ○ /profile
├ ○ /programs
├ ○ /protection
├ ○ /recover
├ ○ /redeem
├ ○ /rewards
├ ○ /settings
├ ○ /statistics
├ ○ /subscription
├ ○ /subscription/checkout
├ ○ /support
├ ○ /support/legal
├ ○ /support/thread
└ ○ /verify


○  (Static)  prerendered as static content

[fix-export-segment-paths] created 0 dot-joined segment payload copies

Running 77 tests using 1 worker
·············································································
  77 passed (2.0m)
::notice title=🎭 Playwright Run Summary::  77 passed (2.0m)
```

### UI visual smoke

- Command: `/opt/hostedtoolcache/Python/3.12.13/x64/bin/python scripts/ui_visual_smoke.py`
- Exit: `0`

```text
UI visual smoke passed.
```

### Client workspace preflight (skipped)

- Command: `/opt/hostedtoolcache/Python/3.12.13/x64/bin/python -c print('POKROV-app workspace is unavailable for this gate run: missing /home/runner/work/portal/POKROV-app/config/product-contract.seed.json, /home/runner/work/portal/POKROV-app/config/runtime-profile.seed.json, /home/runner/work/portal/POKROV-app/config/runtime-artifacts.seed.json (+2 more)'); print('BLOCKED_BY_ACCESS: client gates skipped for this CI guardrail run')`
- Exit: `0`

```text
POKROV-app workspace is unavailable for this gate run: missing /home/runner/work/portal/POKROV-app/config/product-contract.seed.json, /home/runner/work/portal/POKROV-app/config/runtime-profile.seed.json, /home/runner/work/portal/POKROV-app/config/runtime-artifacts.seed.json (+2 more)
BLOCKED_BY_ACCESS: client gates skipped for this CI guardrail run
```

