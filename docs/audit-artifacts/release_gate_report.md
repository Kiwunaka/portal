# Release Gate Report

- Generated at: `2026-08-04 20:45:51`
- Status: `PASS`
- Gate set: `default`
- Brain IP supplied: `no`
- Client platform gates: `none`
- Android audit required by selected gates: `no`

## Summary

| Gate | Exit code | Duration (s) |
|---|---:|---:|
| Release pytest matrix | 0 | 1375.10 |
| Admin/auth regressions | 0 | 270.25 |
| Client security smoke | 0 | 0.46 |
| Client Flutter tests | 0 | 59.22 |
| API lifecycle smoke | 0 | 10.41 |
| Public link checks | 0 | 0.11 |
| Marketing production build | 0 | 18.55 |
| AdminApp production build | 0 | 20.49 |
| Admin webapp smoke | 0 | 0.21 |
| WebApp production build | 0 | 23.29 |
| WebApp Playwright E2E | 0 | 86.73 |
| UI visual smoke | 0 | 0.11 |

## Evidence Classification

| Evidence | Scope | Status | Notes |
|---|---|---|---|
| current-origin check | local default gate set | PASS | Runs on the operator workstation; does not prove brain-origin or RU-origin reachability. |
| brain-origin check | `scripts/verify_brain_ready.py` / predeploy readiness | BLOCKED_BY_ACCESS | Requires `--brain-ip` and live SSH/API access; keep separate from current-origin results. |
| RU-origin check | external RU probe (`mini` or replacement) | BLOCKED_BY_ACCESS | Not run by this local gate; requires an external RU probe host and redacted report. |
| Android physical audit | release-build localhost/control-surface audit | BLOCKED_BY_ACCESS | Public Android remains blocked unless this is run on physical hardware with the release build. |
| Runtime app-download smoke | `/api/client/apps` and provider checks | SKIPPED_NO_LIVE_TOKEN | Requires `TELEGRAM_INIT_DATA`; omit raw token values from evidence. |
| Client platform builds | none requested | NOT_REQUESTED | Repo/static gates alone do not create Android or Windows beta artifacts. |

## Command Tails

### Release pytest matrix

- Command: `C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe -m pytest tests/test_account_foundation.py tests/test_antiabuse_privacy.py tests/test_antiabuse_retention_script.py tests/test_sqlite_postgres_rehearsal.py tests/test_account_recovery.py tests/test_auth_sessions.py portal_bot/tests/test_app_first_service.py portal_bot/tests/test_app_first_api.py portal_bot/tests/test_email_auth.py portal_bot/tests/test_economy_bonus_referral_service.py portal_bot/tests/test_economy_trial_service.py portal_bot/tests/test_channel_bonus_service.py tests/test_free_soft_profile_contract.py tests/test_free_soft_profile_migrations.py tests/test_node_provisioning_service.py tests/test_panel_client_free_profiles.py tests/test_free_soft_inbound_shaper.py tests/test_free_cycle_service.py tests/test_key_pressure_scoring.py tests/test_admin_ops_api.py tests/test_plan_policies.py tests/test_bot_paywall.py tests/test_api_payments_callbacks.py tests/test_portal_api.py tests/test_worker_retention.py tests/test_observer_service.py tests/test_observer_api.py tests/test_collect_xray_observer.py tests/test_predeploy_node_readiness.py tests/test_admin_webapp_smoke.py tests/test_public_copy_guardrails.py tests/test_reviews_username_masking.py -q --basetemp C:\Users\kiwun\Documents\ai\VPN\.tmp\pytest-basetemp\release-gate-4iejv2pa`
- Exit: `0`

```text
........................................................................ [ 23%]
........................................................................ [ 35%]
........................................................................ [ 46%]
........................................................................ [ 58%]
......................................................... [ 68%]
.................................................................. [ 78%]
.................................................................. [ 89%]
............................................................. [ 99%]
...                                                                      [100%]
============================== warnings summary ===============================
tests/test_api_payments_callbacks.py::ApiPaymentCallbacksTests::test_admin_plan_key_then_real_payment_still_starts_first_referral_hold
  C:\Users\kiwun\Documents\ai\VPN\tests\test_api_payments_callbacks.py:1033: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    ref_expiry = datetime.utcnow() + timedelta(days=20)

tests/test_api_payments_callbacks.py::ApiPaymentCallbacksTests::test_admin_plan_key_then_real_payment_still_starts_first_referral_hold
  C:\Users\kiwun\Documents\ai\VPN\tests\test_api_payments_callbacks.py:1047: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    invited_expiry = datetime.utcnow() + timedelta(days=5)

tests/test_api_payments_callbacks.py::ApiPaymentCallbacksTests::test_admin_plan_key_then_real_payment_still_starts_first_referral_hold
  C:\Users\kiwun\Documents\ai\VPN\tests\test_api_payments_callbacks.py:1063: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    now=datetime.utcnow(),

tests/test_api_payments_callbacks.py::ApiPaymentCallbacksTests::test_admin_plan_key_then_real_payment_still_starts_first_referral_hold
  C:\Users\kiwun\Documents\ai\VPN\tests\test_api_payments_callbacks.py:1135: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    self.assertTrue(bool(referrer.expiry_at and referrer.expiry_at < datetime.utcnow() + timedelta(days=30)))

tests/test_api_payments_callbacks.py: 13 warnings
  C:\Users\kiwun\Documents\ai\VPN\.venv\Lib\site-packages\httpx\_models.py:408: DeprecationWarning: Use 'content=<...>' to upload raw bytes/text content.
    headers, stream = encode_request(

tests/test_api_payments_callbacks.py::ApiPaymentCallbacksTests::test_create_public_order_applies_referral_first_purchase_discount
  C:\Users\kiwun\Documents\ai\VPN\tests\test_api_payments_callbacks.py:1334: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    expiry_at=datetime.utcnow() + timedelta(days=30),

tests/test_api_payments_callbacks.py::ApiPaymentCallbacksTests::test_start99_public_order_ignores_referral_and_pending_discounts
  C:\Users\kiwun\Documents\ai\VPN\tests\test_api_payments_callbacks.py:1523: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    expiry_at=datetime.utcnow() + timedelta(days=30),

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
613 passed, 19 warnings, 38 subtests passed in 1370.21s (0:22:50)
```

### Admin/auth regressions

- Command: `C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe -m pytest tests/test_api_auth_and_tickets.py -q --basetemp C:\Users\kiwun\Documents\ai\VPN\.tmp\pytest-basetemp\release-gate-8p9qk6nl`
- Exit: `0`

```text
................................................................ [ 68%]
.............................                                            [100%]
93 passed, 8 subtests passed in 268.71s (0:04:28)
```

### Client security smoke

- Command: `C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe scripts/client_security_smoke.py`
- Exit: `0`

```text
[check] product contract: C:\Users\kiwun\Documents\ai\POKROV-app\config\product-contract.seed.json
[check] runtime profile: C:\Users\kiwun\Documents\ai\POKROV-app\config\runtime-profile.seed.json
[check] runtime artifacts: C:\Users\kiwun\Documents\ai\POKROV-app\config\runtime-artifacts.seed.json
[check] Android manifest: C:\Users\kiwun\Documents\ai\POKROV-app\apps\android_shell\android\app\src\main\AndroidManifest.xml
[check] Android build.gradle: C:\Users\kiwun\Documents\ai\POKROV-app\apps\android_shell\android\app\build.gradle
[check] Windows release seed: C:\Users\kiwun\Documents\ai\POKROV-app\config\windows-release.seed.json
[pass] client security smoke checks passed
```

### Client Flutter tests

- Command: `C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe scripts/run_client_release_gate.py test --suite full`
- Exit: `0`

```text
UrlLauncherTest > openWebView_opensUrlInCustomTabs PASSED

UrlLauncherTest > canLaunch_returnsFalseForEmulatorFallbackComponent PASSED

UrlLauncherTest > openWebView_handlesEnableJavaScript PASSED

UrlLauncherTest > canLaunch_createsIntentWithPassedUrl PASSED

UrlLauncherTest > launch_returnsTrue PASSED

UrlLauncherTest > openWebView_handlesEnableDomStorage PASSED

UrlLauncherTest > openWebView_handlesEnableShowTitle PASSED

UrlLauncherTest > canLaunch_returnsFalse PASSED

UrlLauncherTest > launch_throwsForNoCurrentActivity PASSED

UrlLauncherTest > openWebView_returnsFalse PASSED

UrlLauncherTest > closeWebView_closes PASSED

UrlLauncherTest > canLaunch_returnsTrue PASSED

UrlLauncherTest > openWebView_handlesHeaders PASSED

UrlLauncherTest > openWebView_opensUrlInCustomTabsWithCORSAllowedHeader PASSED

UrlLauncherTest > launch_returnsFalse PASSED

UrlLauncherTest > openWebView_opensUrlInWebViewIfRequested PASSED

UrlLauncherTest > launch_createsIntentWithPassedUrl PASSED

WebViewActivityTest > extractHeaders_returnsEmptyMapWhenHeadersBundleNull PASSED

BUILD SUCCESSFUL in 8s
137 actionable tasks: 5 executed, 132 up-to-date
Workspace Flutter and Android unit tests passed.
[client-gate] C:\Program Files\PowerShell\7\pwsh.EXE -NoProfile -ExecutionPolicy Bypass -File C:\Users\kiwun\Documents\ai\POKROV-app\scripts\run-tests.ps1 (cwd=C:\Users\kiwun\Documents\ai\POKROV-app)
```

### API lifecycle smoke

- Command: `C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe scripts/api_lifecycle_smoke.py`
- Exit: `0`

```text
.
----------------------------------------------------------------------
Ran 1 test in 9.573s

OK
```

### Public link checks

- Command: `C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe scripts/check-links.py`
- Exit: `0`

```text
[PASS] marketing\src\app\robots.ts: Marketing SEO route is present
[PASS] marketing\src\app\sitemap.ts: Marketing SEO route is present
[PASS] marketing\src\app\manifest.ts: Marketing SEO route is present
[PASS] marketing\public\opengraph-image.png: Marketing SEO route is present
[PASS] marketing\public\twitter-image.png: Marketing SEO route is present
[PASS] marketing\public\favicon.ico: Marketing SEO route is present
[PASS] marketing\public\apple-icon.png: Marketing SEO route is present
[PASS] marketing\src\app\page.tsx: Public marketing CTA no longer routes to connect host
[PASS] marketing\src\components\layout\page-shell.tsx: Public cabinet CTA points to webapp host
[PASS] marketing\src\components\home\pricing.tsx: Pricing CTA routes through public checkout gateway
[PASS] marketing\src\components\layout\footer.tsx: Marketing footer exposes canonical news channel
[PASS] marketing\src\app\layout.tsx: Layout includes `metadataBase` metadata wiring
[PASS] marketing\src\app\layout.tsx: Layout includes `manifest` metadata wiring
[PASS] marketing\src\app\layout.tsx: Layout includes `icons` metadata wiring
[PASS] marketing\src\app\layout.tsx: Layout includes `apple` metadata wiring
[PASS] marketing\src\app\layout.tsx: Layout includes `/favicon.ico` metadata wiring
[PASS] marketing\src\app\layout.tsx: Layout includes `/apple-icon.png` metadata wiring
[PASS] marketing\src\lib\marketing-site.ts: Marketing metadata declares `alternates`
[PASS] marketing\src\lib\marketing-site.ts: Marketing metadata declares `canonical`
[PASS] marketing\src\lib\marketing-site.ts: Marketing metadata declares `twitter`
[PASS] marketing\src\lib\marketing-site.ts: Marketing metadata declares `images`
[PASS] marketing\src\app\page.tsx: Home page wires `buildMarketingMetadata`
[PASS] marketing\src\app\page.tsx: Home page wires `buildSoftwareApplicationJsonLd`
[PASS] marketing\src\app\page.tsx: Home page wires `buildFaqJsonLd`
[PASS] marketing\src\app\checkout\checkout-client.tsx: Checkout gateway uses cabinet-safe fallback instead of connect host
[PASS] marketing\src\app\offer\page.tsx: Legal page avoids direct checkout CTA
[PASS] marketing\src\app\privacy\page.tsx: Legal page avoids direct checkout CTA
[PASS] webapp\src\app\(dashboard)\support\legal\page.tsx: Webapp legal links use absolute marketing URLs
[PASS] portal_bot\api_admin_routes.py: Admin campaign link builder marks public checkout as safe fallback
[PASS] portal_bot\api.py: Numeric subscription fallback is explicit compatibility and defaults off

Link check passed.
```

### Marketing production build

- Command: `npm.cmd run build`
- Exit: `0`

```text
  Generating static pages using 19 workers (16/32)
  Generating static pages using 19 workers (24/32)
✓ Generating static pages using 19 workers (32/32) in 557.2ms
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

- Command: `npm.cmd run build`
- Exit: `0`

```text
> pokrov-adminapp@0.1.0 build
> next build

▲ Next.js 16.2.10 (Turbopack)
- Experiments (use with caution):
  ✓ externalDir

  Creating an optimized production build ...
✓ Compiled successfully in 3.0s
  Running TypeScript ...
  Finished TypeScript in 5.1s ...
  Collecting page data using 5 workers ...
  Generating static pages using 5 workers (0/17) ...
  Generating static pages using 5 workers (4/17)
  Generating static pages using 5 workers (8/17)
  Generating static pages using 5 workers (12/17)
✓ Generating static pages using 5 workers (17/17) in 759ms
  Finalizing page optimization ...

Route (app)
┌ ○ /
├ ○ /_not-found
└ ● /[section]
  ├ /nodes
  ├ /traffic
  ├ /alerts
  └ [+11 more paths]


○  (Static)  prerendered as static content
●  (SSG)     prerendered as static HTML (uses generateStaticParams)
```

### Admin webapp smoke

- Command: `C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe scripts/admin_webapp_smoke.py`
- Exit: `0`

```text
Admin WebApp smoke passed.
```

### WebApp production build

- Command: `npm.cmd run build`
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

[fix-export-segment-paths] created 86 dot-joined segment payload copies
```

### WebApp Playwright E2E

- Command: `npm.cmd run test:e2e`
- Exit: `0`

```text
  ok 36 e2e\cabinet-flow.spec.ts:856:7 › Cabinet flow › uses the side drawer as the only mobile cabinet navigation (1.3s)
  ok 37 e2e\cabinet-flow.spec.ts:895:7 › Cabinet flow › keeps cabinet navigation usable with left-click browser routing (875ms)
  ok 38 e2e\cabinet-flow.spec.ts:909:7 › Cabinet flow › shows branded root and cabinet not-found recovery screens (511ms)
  ok 39 e2e\cabinet-flow.spec.ts:921:7 › Cabinet flow › shows subscription manual connection only as an explicit fallback (733ms)
  ok 40 e2e\cabinet-flow.spec.ts:942:7 › Cabinet flow › builds the Happ URL without leaking it to third parties (649ms)
  ok 41 e2e\cabinet-flow.spec.ts:970:7 › Cabinet flow › keeps manual setup closed from a direct hash when no active link exists (505ms)
  ok 42 e2e\cabinet-flow.spec.ts:984:7 › Cabinet flow › keeps paid plan cards selectable for a free monthly account (488ms)
  ok 43 e2e\cabinet-flow.spec.ts:1047:7 › Cabinet flow › renders runtime connections on devices and keeps statistics as its own safe-summary page (964ms)
  ok 44 e2e\cabinet-flow.spec.ts:1068:7 › Cabinet flow › issues a one-time device code without exposing the subscription URL (735ms)
  ok 45 e2e\cabinet-flow.spec.ts:1077:7 › Cabinet flow › searches fallback guides and the POKROV screen atlas on mobile (1.3s)
  ok 46 e2e\cabinet-flow.spec.ts:1110:7 › Cabinet flow › submits a competitor-switch application without automatic reward (1.3s)
  ok 47 e2e\cabinet-flow.spec.ts:1132:7 › Cabinet flow › keeps redeem as a compact activation task (650ms)
  ok 48 e2e\cabinet-flow.spec.ts:1146:7 › Cabinet flow › keeps cabinet copy human and hides node internals (869ms)
  ok 49 e2e\cabinet-flow.spec.ts:1160:7 › Cabinet flow › settings exposes clear Telegram bonus actions without raw account details (2.0s)
  ok 50 e2e\cabinet-flow.spec.ts:1178:7 › Cabinet flow › shows honest payment history and Russian checkout continuation copy (784ms)
  ok 51 e2e\cabinet-flow.spec.ts:1216:7 › Cabinet flow › keeps downloads and support flows usable without the app (1.6s)
  ok 52 e2e\cabinet-flow.spec.ts:1250:7 › Cabinet flow › renders support thread attachments without exposing private access data (1.8s)
  ok 53 e2e\cabinet-flow.spec.ts:1307:7 › Cabinet flow › sends staged attachment id without the private media triplet (3.6s)
  ok 54 e2e\cabinet-flow.spec.ts:1389:7 › Cabinet flow › keeps legal documents as compact support rows (664ms)
  ok 55 e2e\cabinet-flow.spec.ts:1402:7 › Cabinet flow › stays inside a narrow mobile viewport for core cabinet pages (920ms)
  ok 56 e2e\rewards.spec.ts:268:7 › rewards fail-closed cabinet surface › shows anonymized referral conversion and history (726ms)
  ok 57 e2e\rewards.spec.ts:286:7 › rewards fail-closed cabinet surface › keeps calendar usable when wheel state fails (484ms)
  ok 58 e2e\rewards.spec.ts:294:7 › rewards fail-closed cabinet surface › keeps wheel usable when calendar state fails (475ms)
  ok 59 e2e\rewards.spec.ts:302:7 › rewards fail-closed cabinet surface › does not invent sectors or animate an unknown committed reward (714ms)
  ok 60 e2e\rewards.spec.ts:312:7 › rewards fail-closed cabinet surface › renders one sector as a guaranteed reward card (488ms)
  ok 61 e2e\rewards.spec.ts:327:9 › rewards fail-closed cabinet surface › fails closed for missing sectors (494ms)
  ok 62 e2e\rewards.spec.ts:327:9 › rewards fail-closed cabinet surface › fails closed for duplicate sectors (478ms)
  ok 63 e2e\rewards.spec.ts:327:9 › rewards fail-closed cabinet surface › fails closed for non-positive sectors (494ms)
  ok 64 e2e\rewards.spec.ts:327:9 › rewards fail-closed cabinet surface › fails closed for too many sectors (479ms)
  ok 65 e2e\rewards.spec.ts:327:9 › rewards fail-closed cabinet surface › fails closed for excessive reward (493ms)
  ok 66 e2e\rewards.spec.ts:337:9 › rewards fail-closed cabinet surface › keeps FREE rewards ineligible (472ms)
  ok 67 e2e\rewards.spec.ts:337:9 › rewards fail-closed cabinet surface › keeps TRIAL rewards ineligible (551ms)
  ok 68 e2e\rewards.spec.ts:337:9 › rewards fail-closed cabinet surface › keeps BONUS rewards ineligible (523ms)
  ok 69 e2e\rewards.spec.ts:347:7 › rewards fail-closed cabinet surface › keeps expired rewards ineligible (498ms)
  ok 70 e2e\rewards.spec.ts:355:7 › rewards fail-closed cabinet surface › renders disabled features without mutation controls (526ms)
  ok 71 e2e\rewards.spec.ts:365:7 › rewards fail-closed cabinet surface › accepts the server same-day calendar response (727ms)
  ok 72 e2e\rewards.spec.ts:374:7 › rewards fail-closed cabinet surface › refetches wheel state and entitlement after committed reward (731ms)
  ok 73 e2e\rewards.spec.ts:387:7 › rewards fail-closed cabinet surface › refetches calendar state and entitlement after check-in (702ms)

  73 passed (1.1m)
```

### UI visual smoke

- Command: `C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe scripts/ui_visual_smoke.py`
- Exit: `0`

```text
UI visual smoke passed.
```
